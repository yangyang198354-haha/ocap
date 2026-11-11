"""账号主体与凭据（MOD-003）。"""
import uuid

from django.db import models


class User(models.Model):
    EMAIL_STATES = [
        ("NONE", "无"), ("UNVERIFIED_REG", "注册未验证"),
        ("UNVERIFIED_CHANGED", "修改未验证"), ("VERIFIED", "已验证"),
    ]
    STATUSES = [("ACTIVE", "正常"), ("CANCELLED", "已注销")]

    account_no = models.CharField(max_length=10, unique=True)
    phone = models.CharField(max_length=11, unique=True, null=True, blank=True)
    email = models.CharField(max_length=254, null=True, blank=True)
    email_state = models.CharField(max_length=20, choices=EMAIL_STATES, default="NONE")
    verified_email = models.CharField(max_length=254, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    nickname = models.CharField(max_length=30, null=True, blank=True)
    avatar_attachment_id = models.UUIDField(null=True, blank=True)
    gender = models.SmallIntegerField(null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    # MOD-023：界面风格偏好；NULL = 未选择（客户端按默认风格 bento 解释）
    theme_key = models.CharField(max_length=32, null=True, blank=True)

    is_admin_principal = False
    is_authenticated = True

    @property
    def identity_label(self) -> str:
        return f"用户{self.account_no}"

    @property
    def avatar_url(self) -> str | None:
        if not self.avatar_attachment_id:
            return None
        return f"/api/v1/attachments/{self.avatar_attachment_id}/download"


class AdminAccount(models.Model):
    username = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_admin_id = models.IntegerField(null=True, blank=True)
    # MOD-068：管理端界面风格偏好；NULL = 未选择（客户端按默认风格 bento 解释）
    theme_key = models.CharField(max_length=32, null=True, blank=True)

    is_admin_principal = True
    is_authenticated = True

    @property
    def identity_label(self) -> str:
        return f"管理员{self.username}"


class WeChatIdentity(models.Model):
    CHANNELS = [("MINIAPP", "小程序"), ("WEB", "网站")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wechat_identities")
    channel = models.CharField(max_length=8, choices=CHANNELS)
    openid = models.CharField(max_length=64)
    unionid = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["channel", "openid"], name="uniq_wechat_channel_openid")]


class AuthToken(models.Model):
    PRINCIPALS = [("MEMBER", "用户"), ("ADMIN", "管理员")]
    KINDS = [("IDLE", "闲置"), ("EXTENDED", "延长")]

    key_hash = models.CharField(max_length=64, unique=True)
    principal = models.CharField(max_length=8, choices=PRINCIPALS)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="tokens")
    admin = models.ForeignKey(AdminAccount, on_delete=models.CASCADE, null=True, blank=True, related_name="tokens")
    session_kind = models.CharField(max_length=8, choices=KINDS, default="IDLE")
    created_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField()


class VerificationCode(models.Model):
    TARGET_TYPES = [("PHONE", "手机号"), ("EMAIL", "邮箱")]

    target = models.CharField(max_length=254)
    target_type = models.CharField(max_length=8, choices=TARGET_TYPES)
    purpose = models.CharField(max_length=20)
    code_hmac = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.SmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["target", "purpose", "created_at"])]


class WeChatLoginState(models.Model):
    state_hash = models.CharField(max_length=64, primary_key=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)


class LoginTicket(models.Model):
    ticket_hash = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_tickets")
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)


def _uuid_default():
    return uuid.uuid4()
