"""账号服务（MOD-003 / IFC-038）。"""
import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from apps.core.config import SystemConfig
from apps.core.errors import ApiError, NotFound, RateLimited
from apps.core.masking import EMAIL_RE, PHONE_RE
from apps.core.ratelimit import RateLimiter
from apps.integrations.email import EmailSendError, get_email_gateway
from apps.integrations.sms import SmsSendError, get_sms_gateway
from apps.integrations.wechat import WeChatError

from .models import AuthToken, LoginTicket, User, VerificationCode, WeChatIdentity, WeChatLoginState

WEAK_PASSWORDS = {"12345678", "password", "password1", "abc12345", "11111111", "00000000", "qwerty123"}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _code_hmac(target: str, purpose: str, code: str) -> str:
    message = f"{target}:{purpose}:{code}".encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _new_account_no() -> str:
    for _ in range(20):
        candidate = f"{secrets.randbelow(9_000_000_000) + 1_000_000_000}"
        if not User.objects.filter(account_no=candidate).exists():
            return candidate
    raise RuntimeError("无法生成账号编号")


def validate_password(password: str, *, user: User | None = None) -> None:
    min_len = int(SystemConfig.get("password.min_len"))
    max_len = int(SystemConfig.get("password.max_len"))
    errors: list[str] = []
    if not (min_len <= len(password) <= max_len):
        errors.append(f"长度须为 {min_len}~{max_len} 位")
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        errors.append("须同时包含字母和数字")
    if password.isdigit():
        errors.append("不能是纯数字")
    if password.lower() in WEAK_PASSWORDS:
        errors.append("不能是常见弱口令")
    if user is not None and password in {user.username if hasattr(user, "username") else "",
                                        user.account_no if hasattr(user, "account_no") else "",
                                        user.phone if hasattr(user, "phone") else ""}:
        errors.append("不能与账号或手机号相同")
    if errors:
        raise ApiError("PASSWORD_RULE_VIOLATION", "密码不符合规则", 400, {"password": errors})


class AccountService:
    @staticmethod
    def send_code(*, target: str, target_type: str, purpose: str, ip: str) -> dict:
        if target_type == "PHONE" and not PHONE_RE.match(target):
            raise ApiError("INVALID_TARGET", "手机号格式不正确")
        if target_type == "EMAIL" and (len(target) > 254 or not EMAIL_RE.match(target)):
            raise ApiError("INVALID_TARGET", "邮箱格式不正确")
        resend = int(SystemConfig.get("code.resend_interval_seconds"))
        checks = [
            (f"code:int:{target}", 1, resend),
            (f"code:hour:{target}", int(SystemConfig.get("code.target_per_hour")), 3600),
            (f"code:day:{target}", int(SystemConfig.get("code.target_per_day")), 86400),
            (f"code:ip:{ip}", int(SystemConfig.get("code.ip_per_hour")), 3600),
        ]
        for key, limit, window in checks:
            decision = RateLimiter.hit(key, limit=limit, window_seconds=window)
            if not decision.allowed:
                raise RateLimited(decision.retry_after)
        locked = RateLimiter.is_locked(f"codefail:{target}")
        if not locked.allowed:
            raise ApiError("CODE_LOCKED", "验证码尝试过多，请稍后再试", 429,
                           {"retry_after": locked.retry_after})
        length = int(SystemConfig.get("code.sms.length"))
        code = "".join(str(secrets.randbelow(10)) for _ in range(length))
        ttl = int(SystemConfig.get("code.sms.ttl_seconds" if target_type == "PHONE" else "code.email.ttl_seconds"))
        expires_at = timezone.now() + timedelta(seconds=ttl)
        VerificationCode.objects.create(
            target=target, target_type=target_type, purpose=purpose,
            code_hmac=_code_hmac(target, purpose, code), expires_at=expires_at, ip=ip,
        )
        try:
            if target_type == "PHONE":
                get_sms_gateway().send_code(target, code, purpose)
            else:
                get_email_gateway().send_code(target, code, purpose, ttl // 60)
        except SmsSendError as exc:
            mapping = {
                "RATE_LIMITED": ("CODE_RATE_LIMITED", 429),
                "INVALID_NUMBER": ("INVALID_TARGET", 400),
                "QUOTA_OR_BALANCE": ("SMS_UNAVAILABLE", 503),
                "CONFIG": ("SMS_UNAVAILABLE", 503),
                "UPSTREAM": ("SMS_SEND_FAILED", 502),
            }
            code_name, http_status = mapping.get(exc.kind, ("SMS_SEND_FAILED", 502))
            raise ApiError(code_name, "短信发送失败", http_status)
        except EmailSendError as exc:
            raise ApiError("EMAIL_SEND_FAILED", "邮件发送失败", 502) from exc
        return {"resend_after": resend, "expires_in": ttl}

    @staticmethod
    def verify_code(*, target: str, purpose: str, code: str) -> None:
        locked = RateLimiter.is_locked(f"codefail:{target}")
        if not locked.allowed:
            raise ApiError("CODE_LOCKED", "验证码尝试过多，请稍后再试", 429,
                           {"retry_after": locked.retry_after})
        row = (VerificationCode.objects
               .filter(target=target, purpose=purpose, consumed_at__isnull=True)
               .order_by("-created_at").first())
        if row is None:
            raise ApiError("CODE_INVALID", "验证码错误")
        if row.expires_at <= timezone.now():
            raise ApiError("CODE_EXPIRED", "验证码已过期")
        if not hmac.compare_digest(row.code_hmac, _code_hmac(target, purpose, code)):
            row.attempts += 1
            row.save(update_fields=["attempts"])
            decision = RateLimiter.register_failure(
                f"codefail:{target}",
                limit=int(SystemConfig.get("code.target_lock_after_wrong")),
                window_seconds=int(SystemConfig.get("code.target_lock_seconds")),
                lock_seconds=int(SystemConfig.get("code.target_lock_seconds")),
            )
            if not decision.allowed or row.attempts >= int(SystemConfig.get("code.max_wrong_per_code")):
                raise ApiError("CODE_LOCKED", "验证码尝试过多，请稍后再试", 429,
                               {"retry_after": decision.retry_after or 1})
            raise ApiError("CODE_INVALID", "验证码错误")
        row.consumed_at = timezone.now()
        row.save(update_fields=["consumed_at"])
        RateLimiter.reset(f"codefail:{target}")

    @staticmethod
    def _check_phone_available(phone: str) -> None:
        if User.objects.filter(phone=phone).exists():
            raise ApiError("PHONE_ALREADY_REGISTERED", "该手机号已注册", 409)

    @classmethod
    def register_by_phone(cls, *, phone: str, code: str, email: str | None = None) -> User:
        if not PHONE_RE.match(phone):
            raise ApiError("INVALID_TARGET", "手机号格式不正确")
        cls._check_phone_available(phone)
        if email is not None and email != "" and (len(email) > 254 or not EMAIL_RE.match(email)):
            raise ApiError("INVALID_TARGET", "邮箱格式不正确")
        cls.verify_code(target=phone, purpose="REGISTER", code=code)
        user = User.objects.create(
            account_no=_new_account_no(), phone=phone,
            email=email or None,
            email_state="UNVERIFIED_REG" if email else "NONE",
        )
        from apps.core.audit import AuditActor, AuditService

        AuditService.record(actor=AuditActor("MEMBER", user.id, user.identity_label), action="REGISTER",
                            object_type="user", object_id=str(user.id), result="SUCCESS")
        return user

    @classmethod
    def login_by_phone_code(cls, *, phone: str, code: str) -> User:
        cls.verify_code(target=phone, purpose="LOGIN", code=code)
        user = User.objects.filter(phone=phone, status="ACTIVE").first()
        if user is None:
            raise ApiError("PHONE_NOT_REGISTERED", "该手机号尚未注册", 404)
        _touch_login(user)
        return user

    @classmethod
    def login_by_password(cls, *, identifier: str, password: str) -> User:
        key = f"pwfail:{identifier}"
        locked = RateLimiter.is_locked(key)
        if not locked.allowed:
            raise ApiError("LOGIN_LOCKED", "登录失败次数过多，请稍后再试", 429,
                           {"retry_after": locked.retry_after})
        user = (User.objects.filter(account_no=identifier, status="ACTIVE").first()
                or User.objects.filter(phone=identifier, status="ACTIVE").first())
        if user is None or not user.password or not check_password(password, user.password):
            decision = RateLimiter.register_failure(
                key, limit=int(SystemConfig.get("login.password_fail_limit")),
                window_seconds=int(SystemConfig.get("login.password_lock_seconds")),
                lock_seconds=int(SystemConfig.get("login.password_lock_seconds")),
            )
            if not decision.allowed:
                raise ApiError("LOGIN_LOCKED", "登录失败次数过多，请稍后再试", 429,
                               {"retry_after": decision.retry_after})
            raise ApiError("LOGIN_FAILED", "账号或密码错误；若从未设置过密码，请使用验证码登录")
        RateLimiter.reset(key)
        _touch_login(user)
        return user

    @classmethod
    def login_by_email_code(cls, *, email: str, code: str) -> User:
        if not EMAIL_RE.match(email):
            raise ApiError("INVALID_TARGET", "邮箱格式不正确")
        cls.verify_code(target=email, purpose="EMAIL_LOGIN", code=code)
        verified = User.objects.filter(verified_email=email, status="ACTIVE").first()
        if verified is not None:
            _touch_login(verified)
            return verified
        candidates = list(User.objects.filter(email=email, status="ACTIVE"))
        if not candidates:
            raise ApiError("EMAIL_NOT_LINKED", "该邮箱未关联任何账号", 404)
        if len(candidates) > 1 or any(u.email_state != "UNVERIFIED_REG" for u in candidates):
            raise ApiError("EMAIL_LOGIN_NOT_ALLOWED", "该邮箱须在登录后验证", 403)
        user = candidates[0]
        with transaction.atomic():
            User.objects.filter(verified_email=email).exclude(id=user.id).update(verified_email=None)
            user.verified_email = email
            user.email_state = "VERIFIED"
            user.save(update_fields=["verified_email", "email_state"])
        _touch_login(user)
        return user

    @staticmethod
    def get_or_create_wechat_user(*, channel: str, openid: str, unionid: str | None,
                                  nickname: str | None = None, avatar_url: str | None = None) -> tuple[User, bool]:
        with transaction.atomic():
            identity = WeChatIdentity.objects.filter(channel=channel, openid=openid).first()
            if identity is not None:
                return identity.user, False
            if unionid:
                sibling = WeChatIdentity.objects.filter(unionid=unionid).select_related("user").first()
                if sibling is not None:
                    WeChatIdentity.objects.create(user=sibling.user, channel=channel,
                                                  openid=openid, unionid=unionid)
                    return sibling.user, False
            user = User.objects.create(account_no=_new_account_no())
            WeChatIdentity.objects.create(user=user, channel=channel, openid=openid, unionid=unionid)
            return user, True

    @staticmethod
    def issue_token(principal, *, session_kind: str = "IDLE") -> str:
        is_admin = getattr(principal, "is_admin_principal", False)
        if is_admin and session_kind != "IDLE":
            session_kind = "IDLE"
        key = secrets.token_urlsafe(32)
        AuthToken.objects.create(
            key_hash=_sha256(key),
            principal="ADMIN" if is_admin else "MEMBER",
            user=None if is_admin else principal,
            admin=principal if is_admin else None,
            session_kind=session_kind,
            last_active_at=timezone.now(),
        )
        return key

    @staticmethod
    def authenticate_token(key: str, *, now=None):
        now = now or timezone.now()
        row = (AuthToken.objects.select_related("user", "admin")
               .filter(key_hash=_sha256(key)).first())
        if row is None:
            raise AuthenticationFailed("无效令牌")
        if row.session_kind == "EXTENDED":
            if now - row.created_at >= timedelta(seconds=int(SystemConfig.get("session.extended_seconds"))):
                row.delete()
                raise AuthenticationFailed("登录已过期")
        else:
            idle = int(SystemConfig.get("session.admin_idle_seconds" if row.principal == "ADMIN"
                                       else "session.idle_seconds"))
            if now - row.last_active_at >= timedelta(seconds=idle):
                row.delete()
                raise AuthenticationFailed("登录已过期")
            if (now - row.last_active_at).total_seconds() > 300:
                row.last_active_at = now
                row.save(update_fields=["last_active_at"])
        principal = row.admin if row.principal == "ADMIN" else row.user
        if principal is None:
            raise AuthenticationFailed("无效令牌")
        if row.principal == "ADMIN" and not principal.is_active:
            raise AuthenticationFailed("账号已停用")
        if row.principal == "MEMBER" and principal.status != "ACTIVE":
            raise AuthenticationFailed("账号不可用")
        return principal

    @staticmethod
    def revoke_current(key: str) -> None:
        AuthToken.objects.filter(key_hash=_sha256(key)).delete()

    @staticmethod
    def revoke_tokens(user_id: int) -> int:
        return AuthToken.objects.filter(user_id=user_id).delete()[0]

    @staticmethod
    def set_password(user: User, password: str, confirm: str | None = None,
                     current_password: str | None = None) -> None:
        if confirm is None:
            raise ApiError("PASSWORD_CONFIRM_REQUIRED", "请再次输入密码")
        if password != confirm:
            raise ApiError("PASSWORD_MISMATCH", "两次输入的密码不一致")
        if user.password:
            if not current_password:
                raise ApiError("CURRENT_PASSWORD_REQUIRED", "请输入当前密码")
            if not check_password(current_password, user.password):
                raise ApiError("LOGIN_FAILED", "当前密码错误")
        validate_password(password, user=user)
        user.password = make_password(password)
        user.save(update_fields=["password"])

    @staticmethod
    def update_profile(user: User, data: dict) -> User:
        editable = {"nickname", "gender", "birthday", "email", "avatar_attachment_id"}
        forbidden = set(data) - editable
        if forbidden:
            raise ApiError("FIELD_NOT_EDITABLE", "该字段不可编辑")
        if "nickname" in data:
            nickname = data["nickname"]
            if nickname is not None and not (1 <= len(str(nickname)) <= 30):
                raise ApiError("INVALID_VALUE", "昵称长度须为 1~30 字符")
            user.nickname = nickname
        if "gender" in data:
            if data["gender"] not in (0, 1, 2, None):
                raise ApiError("INVALID_VALUE", "性别取值不合法")
            user.gender = data["gender"]
        if "birthday" in data:
            birthday = data["birthday"]
            if birthday is not None and birthday > timezone.localdate():
                raise ApiError("INVALID_VALUE", "生日不得晚于今天")
            user.birthday = birthday
        if "email" in data:
            email = data["email"]
            if email:
                if not EMAIL_RE.match(str(email)) or len(str(email)) > 254:
                    raise ApiError("INVALID_VALUE", "邮箱格式不正确")
                if email != user.email:
                    user.email = email
                    user.email_state = "UNVERIFIED_CHANGED"
                    user.verified_email = None
            else:
                user.email = None
                user.email_state = "NONE"
                user.verified_email = None
        if "avatar_attachment_id" in data:
            from apps.core.models import Attachment

            attachment_id = data["avatar_attachment_id"]
            if attachment_id is not None:
                row = Attachment.objects.filter(id=attachment_id, owner_id=user.id,
                                                purpose="AVATAR").first()
                if row is None:
                    raise ApiError("INVALID_VALUE", "头像附件不存在")
            user.avatar_attachment_id = attachment_id
        user.save()
        return user

    @staticmethod
    def verify_email(user: User, email: str, code: str) -> None:
        if not user.email or user.email != email:
            raise ApiError("EMAIL_MISMATCH", "邮箱与当前填写的邮箱不一致")
        AccountService.verify_code(target=email, purpose="EMAIL_VERIFY", code=code)
        with transaction.atomic():
            cleared = User.objects.filter(verified_email=email).exclude(id=user.id)
            cleared_ids = list(cleared.values_list("id", flat=True))
            cleared.update(verified_email=None)
            user.email_state = "VERIFIED"
            user.verified_email = email
            user.save(update_fields=["email_state", "verified_email"])
            if cleared_ids:
                from apps.core.audit import AuditActor, AuditService

                AuditService.record(actor=AuditActor("MEMBER", user.id, user.identity_label),
                                    action="EMAIL_OWNERSHIP_CHANGED", object_type="user",
                                    object_id=str(user.id), result="SUCCESS",
                                    detail={"cleared_user_ids": cleared_ids})

    @staticmethod
    def tombstone(user: User) -> None:
        with transaction.atomic():
            WeChatIdentity.objects.filter(user=user).delete()
            user.phone = None
            user.email = None
            user.verified_email = None
            user.email_state = "NONE"
            user.nickname = None
            user.avatar_attachment_id = None
            user.password = None
            user.gender = None
            user.birthday = None
            user.status = "CANCELLED"
            user.cancelled_at = timezone.now()
            user.save()
            AccountService.revoke_tokens(user.id)

    @staticmethod
    def fill_empty_profile_from(primary: User, secondary: User) -> None:
        fields = ["email", "verified_email", "password", "nickname", "avatar_attachment_id",
                  "gender", "birthday"]
        for field in fields:
            if not getattr(primary, field) and getattr(secondary, field):
                setattr(primary, field, getattr(secondary, field))
        if primary.email_state == "NONE" and secondary.email_state != "NONE":
            primary.email_state = secondary.email_state
        primary.save()


def _touch_login(user: User) -> None:
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])


def verify_login_ticket(ticket: str) -> User:
    row = LoginTicket.objects.select_related("user").filter(ticket_hash=_sha256(ticket)).first()
    if row is None or row.consumed_at is not None or row.expires_at <= timezone.now():
        raise ApiError("TICKET_INVALID", "票据无效或已过期")
    row.consumed_at = timezone.now()
    row.save(update_fields=["consumed_at"])
    return row.user


def create_login_ticket(user: User) -> str:
    ticket = secrets.token_urlsafe(24)
    LoginTicket.objects.update_or_create(
        ticket_hash=_sha256(ticket),
        defaults={"user": user, "expires_at": timezone.now() + timedelta(seconds=60), "consumed_at": None},
    )
    return ticket


def create_wechat_state() -> str:
    state = secrets.token_urlsafe(24)
    WeChatLoginState.objects.create(state_hash=_sha256(state),
                                    expires_at=timezone.now() + timedelta(minutes=10))
    return state


def consume_wechat_state(state: str) -> bool:
    row = WeChatLoginState.objects.filter(state_hash=_sha256(state)).first()
    if row is None or row.consumed_at is not None or row.expires_at <= timezone.now():
        return False
    row.consumed_at = timezone.now()
    row.save(update_fields=["consumed_at"])
    return True


def map_wechat_error(exc: WeChatError) -> ApiError:
    mapping = {
        "INVALID_CODE": ("WECHAT_CODE_INVALID", 400),
        "RATE_LIMITED": ("CODE_RATE_LIMITED", 429),
        "BLOCKED": ("WECHAT_LOGIN_BLOCKED", 403),
        "UPSTREAM_DOWN": ("WECHAT_UNAVAILABLE", 503),
        "NOT_CONFIGURED": ("WECHAT_UNAVAILABLE", 503),
        "IP_NOT_WHITELISTED": ("WECHAT_UNAVAILABLE", 503),
    }
    code, http_status = mapping.get(exc.kind, ("WECHAT_UNAVAILABLE", 503))
    return ApiError(code, "微信服务暂不可用", http_status)


def get_user_or_404(user_id: int) -> User:
    user = User.objects.filter(id=user_id).first()
    if user is None:
        raise NotFound("用户不存在")
    return user
