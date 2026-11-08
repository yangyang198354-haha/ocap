"""账号视图（MOD-003）。"""
from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.attachments import AttachmentService
from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, RateLimited
from apps.core.masking import EMAIL_RE, PHONE_RE, mask_email, mask_phone
from apps.core.models import Attachment
from apps.core.permissions import IsAdmin, IsMember
from apps.core.ratelimit import RateLimiter, client_ip
from apps.core.serializers import page_response
from apps.integrations.wechat import WeChatError, get_wechat_client

from .models import AdminAccount, User
from .services import (
    AccountService, consume_wechat_state, create_login_ticket, create_wechat_state,
    map_wechat_error, verify_login_ticket,
)
from .serializers import AdminAccountSerializer, AdminUserSerializer


def user_brief(user: User) -> dict:
    return {"id": user.id, "account_no": user.account_no, "nickname": user.nickname,
            "avatar_url": user.avatar_url, "status": user.status}


def auth_result(user: User, token: str, *, is_new: bool = False) -> dict:
    return {"token": token, "user": user_brief(user), "is_new": is_new}


def _session_kind(payload, *, default: str = "IDLE") -> str:
    return "EXTENDED" if bool(payload.get("remember_me")) else default


class CodeRequestView(APIView):
    def post(self, request):
        data = request.data or {}
        target = str(data.get("target", ""))
        target_type = data.get("target_type", "PHONE")
        purpose = data.get("purpose", "")
        if purpose not in {"REGISTER", "LOGIN", "EMAIL_LOGIN"}:
            raise ApiError("INVALID_VALUE", "purpose 不合法")
        if purpose == "EMAIL_LOGIN" and target_type != "EMAIL":
            raise ApiError("INVALID_VALUE", "邮箱登录验证码须发往邮箱")
        if purpose != "EMAIL_LOGIN" and target_type != "PHONE":
            raise ApiError("INVALID_VALUE", "该用途验证码须发往手机号")
        if purpose == "REGISTER" and User.objects.filter(phone=target).exists():
            raise ApiError("PHONE_ALREADY_REGISTERED", "该手机号已注册", 409)
        result = AccountService.send_code(target=target, target_type=target_type,
                                          purpose=purpose, ip=client_ip(request))
        return Response(result, status=status.HTTP_202_ACCEPTED)


class MeCodeRequestView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        data = request.data or {}
        purpose = data.get("purpose", "")
        if purpose not in {"BIND_PHONE", "CHANGE_PHONE", "CANCEL", "EMAIL_VERIFY"}:
            raise ApiError("INVALID_VALUE", "purpose 不合法")
        user: User = request.user
        if purpose == "CANCEL":
            if not user.phone:
                raise ApiError("PHONE_REQUIRED", "请先绑定手机号", 409)
            target, target_type = user.phone, "PHONE"
        elif purpose == "EMAIL_VERIFY":
            target = data.get("target") or user.email
            if not target or target != user.email:
                raise ApiError("EMAIL_MISMATCH", "邮箱与当前填写的邮箱不一致")
            target_type = "EMAIL"
        else:
            target = str(data.get("target", ""))
            target_type = "PHONE"
        result = AccountService.send_code(target=target, target_type=target_type,
                                          purpose=purpose, ip=client_ip(request))
        return Response(result, status=status.HTTP_202_ACCEPTED)


class RegisterView(APIView):
    def post(self, request):
        data = request.data or {}
        phone = str(data.get("phone", ""))
        code = str(data.get("code", ""))
        if not PHONE_RE.match(phone):
            raise ApiError("INVALID_TARGET", "手机号格式不正确")
        if not (len(code) == int(6) and code.isdigit()):
            raise ApiError("CODE_INVALID", "验证码错误")
        user = AccountService.register_by_phone(phone=phone, code=code, email=data.get("email"))
        token = AccountService.issue_token(user)
        return Response(auth_result(user, token, is_new=True), status=status.HTTP_201_CREATED)


class LoginByCodeView(APIView):
    def post(self, request):
        data = request.data or {}
        user = AccountService.login_by_phone_code(phone=str(data.get("phone", "")),
                                                  code=str(data.get("code", "")))
        token = AccountService.issue_token(user, session_kind=_session_kind(data))
        return Response(auth_result(user, token))


class LoginByPasswordView(APIView):
    def post(self, request):
        data = request.data or {}
        identifier = str(data.get("identifier", ""))
        password = str(data.get("password", ""))
        if len(identifier) > 32 or len(password) > 128:
            raise ApiError("LOGIN_FAILED", "账号或密码错误；若从未设置过密码，请使用验证码登录")
        user = AccountService.login_by_password(identifier=identifier, password=password)
        token = AccountService.issue_token(user, session_kind=_session_kind(data))
        return Response(auth_result(user, token))


class LoginByEmailView(APIView):
    def post(self, request):
        data = request.data or {}
        if "password" in data:
            raise ApiError("PASSWORD_NOT_SUPPORTED_FOR_EMAIL", "邮箱登录不支持密码")
        user = AccountService.login_by_email_code(email=str(data.get("email", "")),
                                                  code=str(data.get("code", "")))
        token = AccountService.issue_token(user, session_kind=_session_kind(data))
        return Response(auth_result(user, token))


class LogoutView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        AccountService.revoke_current(request.auth)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MiniappLoginView(APIView):
    def post(self, request):
        data = request.data or {}
        code = str(data.get("code", ""))
        if not code or len(code) > 128:
            raise ApiError("WECHAT_CODE_INVALID", "微信登录凭证无效")
        try:
            session = get_wechat_client().miniapp_code2session(code)
        except WeChatError as exc:
            raise map_wechat_error(exc) from exc
        user, is_new = AccountService.get_or_create_wechat_user(
            channel="MINIAPP", openid=session.openid, unionid=session.unionid,
        )
        token = AccountService.issue_token(user, session_kind="EXTENDED")
        return Response(auth_result(user, token, is_new=is_new))


class WebWechatParamsView(APIView):
    def get(self, request):
        appid = settings.WECHAT_WEB_APPID
        redirect_uri = settings.WECHAT_WEB_REDIRECT_URI
        if not appid or not redirect_uri:
            raise ApiError("WECHAT_UNAVAILABLE", "微信服务暂不可用", 503)
        return Response({"appid": appid, "scope": "snsapi_login", "redirect_uri": redirect_uri,
                         "state": create_wechat_state(), "fast_login": 1})


class WebWechatCallbackView(APIView):
    def get(self, request):
        frontend = settings.WECHAT_WEB_FRONTEND_URL
        state = request.query_params.get("state", "")
        code = request.query_params.get("code", "")
        if not state or not consume_wechat_state(state):
            return HttpResponseRedirect(f"{frontend}?error=STATE_INVALID")
        try:
            exchanged = get_wechat_client().web_exchange_code(code)
        except WeChatError as exc:
            return HttpResponseRedirect(f"{frontend}?error={map_wechat_error(exc).code}")
        user, _ = AccountService.get_or_create_wechat_user(
            channel="WEB", openid=exchanged.openid, unionid=exchanged.unionid,
        )
        return HttpResponseRedirect(f"{frontend}?ticket={create_login_ticket(user)}")


class WebWechatExchangeView(APIView):
    def post(self, request):
        data = request.data or {}
        user = verify_login_ticket(str(data.get("ticket", "")))
        token = AccountService.issue_token(user, session_kind=_session_kind(data))
        return Response(auth_result(user, token))


class PasswordUpdateView(APIView):
    permission_classes = [IsMember]

    def put(self, request):
        data = request.data or {}
        AccountService.set_password(request.user, str(data.get("password", "")),
                                    data.get("password_confirm"), data.get("current_password"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        return Response(profile_view(request.user))

    def patch(self, request):
        data = request.data or {}
        from django.utils.dateparse import parse_date

        patch = {}
        for key, value in data.items():
            if key == "birthday" and value is not None:
                value = parse_date(value)
                if value is None:
                    raise ApiError("INVALID_VALUE", "生日格式不正确")
            if key == "avatar_attachment_id" and value is not None:
                from uuid import UUID

                try:
                    value = UUID(str(value))
                except ValueError as exc:
                    raise ApiError("INVALID_VALUE", "头像附件 id 不合法") from exc
            patch[key] = value
        user = AccountService.update_profile(request.user, patch)
        return Response(profile_view(user))


def profile_view(user: User) -> dict:
    return {
        "account_no": user.account_no,
        "phone": mask_phone(user.phone) if user.phone else None,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "gender": user.gender,
        "birthday": user.birthday,
        "email": mask_email(user.email) if user.email else None,
        "email_state": user.email_state,
    }


class AvatarUploadView(APIView):
    permission_classes = [IsMember]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        decision = RateLimiter.hit(f"upload:{request.user.id}", limit=60, window_seconds=3600)
        if not decision.allowed:
            raise RateLimited(decision.retry_after)
        file = request.FILES.get("file")
        if file is None:
            raise ApiError("FILE_REQUIRED", "缺少文件")
        ref = AttachmentService.store(file=file, purpose="AVATAR", owner=request.user)
        request.user.avatar_attachment_id = ref.id
        request.user.save(update_fields=["avatar_attachment_id"])
        return Response({"id": str(ref.id), "name": ref.name, "size": ref.size,
                         "content_type": ref.content_type}, status=status.HTTP_201_CREATED)


class EmailVerifyView(APIView):
    permission_classes = [IsMember]

    def post(self, request):
        data = request.data or {}
        AccountService.verify_email(request.user, str(data.get("email", "")), str(data.get("code", "")))
        return Response({"email_state": "VERIFIED"})


class AdminLoginView(APIView):
    def post(self, request):
        data = request.data or {}
        if "remember_me" in data:
            raise ApiError("UNKNOWN_FIELD", "管理员登录不支持记住我")
        username = str(data.get("username", ""))
        password = str(data.get("password", ""))
        key = f"pwfail:admin:{username}"
        locked = RateLimiter.is_locked(key)
        if not locked.allowed:
            raise ApiError("LOGIN_LOCKED", "登录失败次数过多，请稍后再试", 429,
                           {"retry_after": locked.retry_after})
        from django.contrib.auth.hashers import check_password

        admin = AdminAccount.objects.filter(username=username, is_active=True).first()
        if admin is None or not check_password(password, admin.password):
            decision = RateLimiter.register_failure(key, limit=5, window_seconds=900, lock_seconds=900)
            AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="ADMIN_LOGIN_FAILED",
                                object_type="admin", object_id=username, result="FAILURE",
                                ip=client_ip(request))
            if not decision.allowed:
                raise ApiError("LOGIN_LOCKED", "登录失败次数过多，请稍后再试", 429,
                               {"retry_after": decision.retry_after})
            raise ApiError("LOGIN_FAILED", "账号或密码错误")
        RateLimiter.reset(key)
        token = AccountService.issue_token(admin, session_kind="IDLE")
        AuditService.record(actor=AuditActor("ADMIN", admin.id, admin.username), action="ADMIN_LOGIN",
                            object_type="admin", object_id=str(admin.id), result="SUCCESS",
                            ip=client_ip(request))
        return Response({"token": token, "admin": {"id": admin.id, "username": admin.username}})


class AdminAccountListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return page_response(AdminAccount.objects.order_by("id"), request, AdminAccountSerializer)

    def post(self, request):
        data = request.data or {}
        username = str(data.get("username", ""))
        import re

        if not re.match(r"^[A-Za-z0-9_-]{3,32}$", username):
            raise ApiError("INVALID_VALUE", "用户名须为 3~32 位字母数字_-")
        if AdminAccount.objects.filter(username=username).exists():
            raise ApiError("USERNAME_TAKEN", "用户名已存在", 409)
        from .services import validate_password

        validate_password(str(data.get("password", "")))
        from django.contrib.auth.hashers import make_password

        admin = AdminAccount.objects.create(username=username,
                                            password=make_password(str(data.get("password", ""))),
                                            created_by_admin_id=request.user.id)
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="ADMIN_CREATED", object_type="admin", object_id=str(admin.id),
                            result="SUCCESS")
        return Response({"id": admin.id, "username": admin.username, "is_active": admin.is_active,
                         "created_at": admin.created_at}, status=status.HTTP_201_CREATED)


class AdminPasswordResetView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, admin_id: int):
        if int(admin_id) == request.user.id:
            raise ApiError("CANNOT_RESET_SELF", "不能重置自己的密码")
        admin = AdminAccount.objects.filter(id=admin_id).first()
        if admin is None:
            raise ApiError("NOT_FOUND", "管理员不存在", 404)
        from django.contrib.auth.hashers import make_password

        from .services import validate_password

        password = str((request.data or {}).get("password", ""))
        validate_password(password)
        admin.password = make_password(password)
        admin.save(update_fields=["password"])
        from .models import AuthToken

        AuthToken.objects.filter(admin=admin).delete()
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="ADMIN_PASSWORD_RESET", object_type="admin",
                            object_id=str(admin.id), result="SUCCESS")
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        q = request.query_params.get("q", "")[:32]
        qs = User.objects.all()
        if q:
            from django.db.models import Q

            condition = Q(account_no__icontains=q) | Q(nickname__icontains=q)
            if PHONE_RE.match(q):
                condition |= Q(phone=q)
            elif q.isdigit() and len(q) == 4:
                condition |= Q(phone__endswith=q)
            qs = qs.filter(condition)
        return page_response(qs.order_by("id"), request, AdminUserSerializer)


_ = (EMAIL_RE, Attachment)
