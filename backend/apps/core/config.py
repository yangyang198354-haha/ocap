"""系统配置与默认值（IFC-007）。"""
from typing import Any, TypeVar

from .models import SystemConfig as SystemConfigModel

T = TypeVar("T")

EDITABLE_KEYS = {"audit.retention_months"}

DEFAULTS: dict[str, Any] = {
    "code.sms.length": 6,
    "code.sms.ttl_seconds": 300,
    "code.email.ttl_seconds": 600,
    "code.resend_interval_seconds": 60,
    "code.target_per_hour": 5,
    "code.target_per_day": 10,
    "code.ip_per_hour": 30,
    "code.max_wrong_per_code": 5,
    "code.target_lock_after_wrong": 10,
    "code.target_lock_seconds": 1800,
    "login.password_fail_limit": 5,
    "login.password_lock_seconds": 900,
    "password.min_len": 8,
    "password.max_len": 64,
    "audit.retention_months": 24,
    "attachment.max_count.resolution": 10,
    "attachment.max_bytes": 10485760,
    "attachment.max_total_bytes.resolution": 52428800,
    "attachment.max_count.appeal": 5,
    "attachment.max_count.invoice": 10,
    "attachment.max_count.voucher": 10,
    "attachment.avatar_max_bytes": 2097152,
    "session.idle_seconds": 1800,
    "session.extended_seconds": 604800,
    "session.admin_idle_seconds": 1800,
    "session.miniapp_extended": True,
    "claim.amount_max": None,
    "poll.max_questions": 50,
    "vote.min_window_minutes": 60,
    "vote.denominator_mode": "ACTIVE",
    "report.show_expense_reason": False,
    "wechat.phone_quick_verify_enabled": False,
}


class SystemConfigService:
    @staticmethod
    def get(key: str, default: T | None = None) -> Any:
        row = SystemConfigModel.objects.filter(key=key).first()
        if row is not None:
            return row.value
        return DEFAULTS.get(key, default)

    @staticmethod
    def set(key: str, value: Any, admin_id: int | None) -> None:
        SystemConfigModel.objects.update_or_create(
            key=key, defaults={"value": value, "updated_by_admin_id": admin_id}
        )

    @staticmethod
    def all_editable() -> dict[str, Any]:
        return {key: SystemConfigService.get(key) for key in sorted(EDITABLE_KEYS)}


SystemConfig = SystemConfigService  # 兼容 IFC 命名
