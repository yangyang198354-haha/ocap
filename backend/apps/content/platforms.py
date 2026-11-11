"""MOD-053：第三方平台账户（IFC-185）。"""
import re
from typing import Mapping

from django.db import transaction

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, NotFound
from apps.integrations.draft import PLATFORMS, get_draft_adapter

from .models import PlatformAccount
from .vault import CredentialVault, CredentialVaultError
from .wechat_token import WechatTokenService

APPID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
APPSECRET_RE = re.compile(r"^[\x21-\x7e]{1,128}$")   # 可见 ASCII，无空白


def _actor(admin):
    return AuditActor("ADMIN", getattr(admin, "id", None),
                      getattr(admin, "username", "") or "")


def _out(row: PlatformAccount | None) -> dict | None:
    if row is None:
        return None
    return {"id": row.id, "platform": row.platform, "display_name": row.display_name,
            "auth_status": row.auth_status,
            "secret_saved": {key: key in (row.secret_keys or []) for key in
                             [field.key for field in get_draft_adapter(row.platform).credential_fields]},
            "updated_at": row.updated_at}


class PlatformAccountService:
    @staticmethod
    def list_platforms() -> list[dict]:
        rows = {row.platform: row for row in PlatformAccount.objects.all()}
        result = []
        for platform in PLATFORMS:
            adapter = get_draft_adapter(platform)
            result.append({
                "platform": platform, "label": adapter.label,
                "capability": adapter.capability,
                "credential_fields": [
                    {"key": field.key, "label": field.label,
                     "secret": field.secret, "required": field.required}
                    for field in adapter.credential_fields],
                "account": _out(rows.get(platform)),
            })
        return result

    @staticmethod
    def _validate_name(name) -> str:
        clean = str(name or "").strip()
        if not 1 <= len(clean) <= 64:
            raise ApiError("INVALID_VALUE", "账户名称长度不合法", 400)
        return clean

    @staticmethod
    def _validate_credentials(platform: str, credentials: Mapping | None) -> dict:
        if credentials is None:
            return {}
        adapter = get_draft_adapter(platform)
        allowed = {field.key for field in adapter.credential_fields}
        clean = {}
        for key, value in credentials.items():
            if key not in allowed:
                raise ApiError("INVALID_VALUE", "未知的认证字段", 400, {"key": key})
            text = str(value).strip()
            if text and not 1 <= len(text) <= 4096:
                raise ApiError("INVALID_VALUE", "认证信息长度不合法", 400, {"key": key})
            if text and platform == "wechat_mp":
                # 1.1.0：仅字符集/长度约束，不断言微信 AppID 格式 [ASSUMPTION]；消息不回显值
                if key == "appid" and not APPID_RE.match(text):
                    raise ApiError("INVALID_VALUE", "AppID 格式不合法", 400, {"key": key})
                if key == "appsecret" and not APPSECRET_RE.match(text):
                    raise ApiError("INVALID_VALUE", "AppSecret 格式不合法", 400, {"key": key})
            if text:
                clean[key] = text
        return clean

    @staticmethod
    def create(*, platform: str, display_name: str, credentials=None, admin) -> dict:
        if platform not in PLATFORMS:
            raise ApiError("PLATFORM_NOT_SUPPORTED", "不支持的平台", 400)
        if PlatformAccount.objects.filter(platform=platform).exists():
            raise ApiError("PLATFORM_ACCOUNT_EXISTS", "每个平台只能有 1 个账户", 409)
        clean_name = PlatformAccountService._validate_name(display_name)
        clean_creds = PlatformAccountService._validate_credentials(platform, credentials)
        adapter = get_draft_adapter(platform)
        required = {field.key for field in adapter.credential_fields if field.required}
        if clean_creds and not CredentialVault.is_configured():
            raise ApiError("CREDENTIAL_VAULT_NOT_CONFIGURED", "凭据加密密钥未配置", 503)
        blob = None
        if clean_creds:
            blob = CredentialVault.encrypt(clean_creds, context=f"content_platformaccount|new")
        row = PlatformAccount.objects.create(
            platform=platform, display_name=clean_name, secret_blob=blob,
            secret_keys=sorted(clean_creds), created_by_admin_id=getattr(admin, "id", 0),
            auth_status="NORMAL" if required <= set(clean_creds) else "UNSET",
        )
        if blob is not None:
            row.secret_blob = CredentialVault.encrypt(
                clean_creds, context=f"content_platformaccount|{row.id}")
            row.save(update_fields=["secret_blob"])
        AuditService.record(actor=_actor(admin), action="CONTENT_PLATFORM_ACCOUNT_CHANGED",
                            object_type="platform_account", object_id=str(row.id),
                            result="SUCCESS", detail={"platform": platform, "action": "create"})
        return _out(row)

    @staticmethod
    def update(account_id: int, *, display_name=None, credentials=None, admin) -> dict:
        row = PlatformAccount.objects.filter(id=account_id).first()
        if row is None:
            raise NotFound("平台账户不存在")
        if display_name is None and credentials is None:
            raise ApiError("INVALID_VALUE", "至少需要修改一项", 400)
        action = "rename"
        update_fields = ["updated_at"]
        credentials_replaced = False
        if display_name is not None:
            row.display_name = PlatformAccountService._validate_name(display_name)
            update_fields.append("display_name")
        if credentials is not None:
            clean_creds = PlatformAccountService._validate_credentials(row.platform, credentials)
            if clean_creds and not CredentialVault.is_configured():
                raise ApiError("CREDENTIAL_VAULT_NOT_CONFIGURED", "凭据加密密钥未配置", 503)
            if clean_creds:
                context = f"content_platformaccount|{row.id}"
                current = {}
                if row.secret_blob:
                    try:
                        current = CredentialVault.decrypt(row.secret_blob, context=context)
                    except CredentialVaultError:
                        current = {}
                merged = {**current, **clean_creds}
                row.secret_blob = CredentialVault.encrypt(merged, context=context)
                row.secret_keys = sorted(merged)
                adapter = get_draft_adapter(row.platform)
                required = {field.key for field in adapter.credential_fields if field.required}
                row.auth_status = "NORMAL" if required <= set(merged) else "UNSET"
                action = "credentials_updated"
                credentials_replaced = True
                update_fields += ["secret_blob", "secret_keys", "auth_status"]
        with transaction.atomic():
            # 只写本次改动的列：令牌缓存列由 worker 并发更新，不能被整行 save 覆盖
            row.save(update_fields=update_fields)
            if credentials_replaced:
                # ADR-060：凭据有任何覆盖即清空令牌缓存（含单飞锁），与凭据写入同一事务
                WechatTokenService.invalidate(row.id)
            AuditService.record(actor=_actor(admin), action="CONTENT_PLATFORM_ACCOUNT_CHANGED",
                                object_type="platform_account", object_id=str(row.id),
                                result="SUCCESS", detail={"platform": row.platform, "action": action})
        return _out(row)

    @staticmethod
    def delete(account_id: int, admin) -> None:
        row = PlatformAccount.objects.filter(id=account_id).first()
        if row is None:
            raise NotFound("平台账户不存在")
        platform = row.platform
        row.delete()
        AuditService.record(actor=_actor(admin), action="CONTENT_PLATFORM_ACCOUNT_CHANGED",
                            object_type="platform_account", object_id=str(account_id),
                            result="SUCCESS", detail={"platform": platform, "action": "delete"})

    @staticmethod
    def credentials_of(account_id: int) -> dict:
        row = PlatformAccount.objects.filter(id=account_id).first()
        if row is None:
            raise NotFound("平台账户不存在")
        if not row.secret_blob:
            return {}
        try:
            return CredentialVault.decrypt(
                row.secret_blob, context=f"content_platformaccount|{row.id}")
        except CredentialVaultError:
            return {}

    @staticmethod
    def mark_expired(account_id: int, *, actor: AuditActor, reason: str) -> bool:
        """仅当 auth_status 为 NORMAL 时置 EXPIRED 并写审计 CONTENT_PLATFORM_AUTH_EXPIRED（ADR-063 第 3 条）。

        返回是否发生了变更；已是 EXPIRED/UNSET 不重复写。
        """
        row = PlatformAccount.objects.filter(id=account_id).first()
        if row is None:
            return False
        with transaction.atomic():
            changed = PlatformAccount.objects.filter(id=account_id, auth_status="NORMAL").update(
                auth_status="EXPIRED")
            if changed:
                AuditService.record(actor=actor, action="CONTENT_PLATFORM_AUTH_EXPIRED",
                                    object_type="platform_account", object_id=str(account_id),
                                    result="SUCCESS",
                                    detail={"platform": row.platform, "reason": reason})
        return bool(changed)
