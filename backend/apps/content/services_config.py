"""MOD-051：服务配置（IFC-182）。"""
from dataclasses import dataclass
from typing import Mapping

from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, NotFound
from apps.integrations.llm import get_llm_client

from .models import ServiceConfig
from .vault import CredentialVault, CredentialVaultError, SecretRedactor


@dataclass(frozen=True)
class ServiceSpec:
    service_type: str
    label: str
    secret_fields: tuple[str, ...]
    default_params: dict
    model_hints: tuple[str, ...]
    testable: bool


SERVICE_SPECS = {
    "LLM_DEEPSEEK": ServiceSpec("LLM_DEEPSEEK", "DeepSeek", ("api_key",),
                                {"model": "deepseek-chat"},
                                ("deepseek-chat", "deepseek-reasoner"), True),
    "LLM_VOLCANO": ServiceSpec("LLM_VOLCANO", "火山方舟", ("api_key",),
                               {"model": "doubao-pro-4k"},
                               ("doubao-pro-4k", "doubao-pro-32k"), True),
    "IMAGE_ARK": ServiceSpec("IMAGE_ARK", "火山方舟图像生成", ("api_key",),
                             {"model": "doubao-seedream-4-5-251128"},
                             ("doubao-seedream-5-0-260128", "doubao-seedream-4-5-251128",
                              "doubao-seedream-4-0-250828"), False),
    "VIDEO_JIMENG": ServiceSpec("VIDEO_JIMENG", "即梦视频生成",
                                ("access_key", "secret_key"), {}, (), False),
}


def _actor(admin):
    return AuditActor("ADMIN", getattr(admin, "id", None),
                      getattr(admin, "username", "") or "")


def _out(spec: ServiceSpec, row: ServiceConfig | None) -> dict:
    saved = {key: bool((row.secret_keys if row else []) and key in (row.secret_keys or []))
             for key in spec.secret_fields}
    return {
        "service_type": spec.service_type, "label": spec.label,
        "configured": bool(row and row.secret_keys), "params": {**spec.default_params, **((row.params if row else {}) or {})},
        "secret_saved": saved, "is_default": bool(row and row.is_default),
        "last_test_ok": row.last_test_ok if row else None,
        "last_tested_at": row.last_tested_at if row else None,
        "last_test_error": row.last_test_error if row else "",
        "updated_at": row.updated_at if row else None,
        "testable": spec.testable, "model_hints": list(spec.model_hints),
        "secret_fields": list(spec.secret_fields),
    }


class ServiceConfigService:
    @staticmethod
    def list_all() -> list[dict]:
        rows = {row.service_type: row for row in ServiceConfig.objects.all()}
        return [_out(spec, rows.get(key)) for key, spec in SERVICE_SPECS.items()]

    @staticmethod
    def save(service_type: str, *, params=None, secrets=None, is_default=None, admin) -> dict:
        spec = SERVICE_SPECS.get(service_type)
        if spec is None:
            raise NotFound("服务类型不存在")
        row = ServiceConfig.objects.filter(service_type=service_type).first()
        clean_params = dict((row.params if row else {}) or {})
        if params is not None:
            model = params.get("model")
            if model is not None:
                import re
                if not isinstance(model, str) or not re.match(r"^[A-Za-z0-9._:/-]{1,64}$", model):
                    raise ApiError("INVALID_VALUE", "模型名不合法", 400)
                clean_params["model"] = model
        clean_secrets = dict()
        if secrets is not None:
            for key, value in secrets.items():
                if key not in spec.secret_fields:
                    raise ApiError("INVALID_VALUE", "未知的凭据字段", 400, {"key": key})
                text = str(value).strip()
                if not 1 <= len(text) <= 4096:
                    raise ApiError("INVALID_VALUE", "凭据长度不合法", 400, {"key": key})
                clean_secrets[key] = text
        existing_keys = set((row.secret_keys if row else []) or [])
        missing = [key for key in spec.secret_fields
                   if key not in existing_keys and key not in clean_secrets]
        if missing and (row is None or not existing_keys):
            raise ApiError("MISSING_FIELDS", "缺少必填凭据", 400, {"fields": missing})
        if row is None:
            row = ServiceConfig(service_type=service_type)
        merged_keys = existing_keys | set(clean_secrets)
        if clean_secrets:
            if not CredentialVault.is_configured():
                raise ApiError("CREDENTIAL_VAULT_NOT_CONFIGURED", "凭据加密密钥未配置", 503)
            context = f"content_serviceconfig|{service_type}"
            current = {}
            if row.secret_blob:
                try:
                    current = CredentialVault.decrypt(row.secret_blob, context=context)
                except CredentialVaultError:
                    current = {}
            current.update(clean_secrets)
            row.secret_blob = CredentialVault.encrypt(current, context=context)
            row.secret_keys = sorted(merged_keys)
            row.last_test_ok = None
        if params is not None and "model" in (params or {}):
            row.last_test_ok = None
            row.last_test_error = ""
        row.params = clean_params
        if is_default is not None:
            row.is_default = bool(is_default)
            if is_default:
                ServiceConfig.objects.filter(
                    service_type__startswith="LLM_").exclude(id=row.id if row.id else -1
                ).update(is_default=False)
        row.updated_by_admin_id = getattr(admin, "id", None)
        row.save()
        AuditService.record(actor=_actor(admin), action="CONTENT_SERVICE_CONFIG_CHANGED",
                            object_type="content_service", object_id=service_type,
                            result="SUCCESS",
                            detail={"changed_fields": sorted(list(clean_params) + list(clean_secrets))})
        return _out(spec, row)

    @staticmethod
    def test(service_type: str, admin) -> dict:
        spec = SERVICE_SPECS.get(service_type)
        if spec is None:
            raise NotFound("服务类型不存在")
        if not spec.testable:
            raise ApiError("NOT_TESTABLE", "该服务不支持连通测试", 400)
        row = ServiceConfig.objects.filter(service_type=service_type).first()
        if row is None or not row.secret_blob:
            raise ApiError("LLM_NOT_CONFIGURED", "尚未配置该模型", 409)
        try:
            secrets = CredentialVault.decrypt(
                row.secret_blob, context=f"content_serviceconfig|{service_type}")
        except CredentialVaultError:
            raise ApiError("CREDENTIAL_VAULT_NOT_CONFIGURED", "凭据解密失败", 503)
        result = get_llm_client().test(service_type=service_type,
                                       api_key=secrets.get("api_key", ""))
        row.last_test_ok = result.ok
        row.last_tested_at = timezone.now()
        row.last_test_error = result.error_code
        row.save(update_fields=["last_test_ok", "last_tested_at", "last_test_error"])
        AuditService.record(actor=_actor(admin), action="CONTENT_SERVICE_TESTED",
                            object_type="content_service", object_id=service_type,
                            result="SUCCESS" if result.ok else "FAILURE",
                            detail={"error_code": result.error_code})
        return {"ok": result.ok, "error_code": result.error_code,
                "message": "" if result.ok else result.error_code}

    @staticmethod
    def llm_options() -> list[dict]:
        rows = ServiceConfig.objects.filter(service_type__startswith="LLM_", last_test_ok=True)
        return [{"service_type": row.service_type,
                 "label": SERVICE_SPECS[row.service_type].label,
                 "model": (row.params or {}).get("model", SERVICE_SPECS[row.service_type].default_params.get("model", "")),
                 "is_default": row.is_default} for row in rows]

    @staticmethod
    def resolve_llm(service_type: str | None) -> tuple[str, str]:
        rows = ServiceConfig.objects.filter(service_type__startswith="LLM_", last_test_ok=True)
        if service_type:
            row = rows.filter(service_type=service_type).first()
        else:
            row = rows.filter(is_default=True).first() or rows.order_by("id").first()
        if row is None:
            raise ApiError("LLM_NOT_CONFIGURED", "请先配置大语言模型", 409)
        spec = SERVICE_SPECS[row.service_type]
        return row.service_type, (row.params or {}).get("model", spec.default_params["model"])

    @staticmethod
    def secrets_for(service_type: str) -> dict[str, str]:
        row = ServiceConfig.objects.filter(service_type=service_type).first()
        if row is None or not row.secret_blob:
            raise ApiError(f"{service_type}_NOT_CONFIGURED", "服务未配置", 409)
        try:
            return CredentialVault.decrypt(row.secret_blob,
                                           context=f"content_serviceconfig|{service_type}")
        except CredentialVaultError:
            raise ApiError("CREDENTIAL_VAULT_NOT_CONFIGURED", "凭据解密失败", 503)
