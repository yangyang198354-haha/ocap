"""系统配置与默认值（IFC-007）。"""
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, TypeVar

from .errors import ApiError
from .models import SystemConfig as SystemConfigModel

T = TypeVar("T")

EDITABLE_KEYS = {"audit.retention_months", "claim.amount_max"}
AMOUNT_MAX_DEFAULT = Decimal("1000000.00")
AMOUNT_MAX_CEILING = Decimal("999999999999.99")  # 金额列 max_digits=14, decimal_places=2

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
    "session.remember_seconds": 15 * 24 * 3600,
    "session.admin_idle_seconds": 1800,
    "session.miniapp_extended": True,
    "claim.amount_max": "1000000.00",
    "poll.max_questions": 50,
    "vote.min_window_minutes": 60,
    "vote.denominator_mode": "ACTIVE",
    "report.show_expense_reason": True,
    "wechat.phone_quick_verify_enabled": False,
}


def validate_retention_months(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ApiError("INVALID_VALUE", "保留期限必须为整数")
    if value < 6:
        raise ApiError("RETENTION_TOO_SHORT", "保留期限不得低于 6 个月")
    if value > 120:
        raise ApiError("RETENTION_TOO_LONG", "保留期限不得高于 120 个月")
    return value


def validate_amount_max(value: object) -> str:
    """金额上限：正数、最多两位小数、不超过金额列范围；规范化为两位小数字符串。"""
    invalid = ApiError("INVALID_VALUE", "上限须为正数且最多两位小数")
    if isinstance(value, bool) or value is None or not isinstance(value, (int, str, float, Decimal)):
        raise invalid
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise invalid from exc
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        raise invalid
    if amount > AMOUNT_MAX_CEILING:
        raise ApiError("INVALID_VALUE", "上限超出金额范围（最大 999999999999.99）")
    return f"{amount:.2f}"


EDITABLE_VALIDATORS: dict[str, Callable[[object], object]] = {
    "audit.retention_months": validate_retention_months,
    "claim.amount_max": validate_amount_max,
}


class SystemConfigService:
    @staticmethod
    def get(key: str, default: T | None = None) -> Any:
        row = SystemConfigModel.objects.filter(key=key).first()
        if row is not None:
            return row.value
        return DEFAULTS.get(key, default)

    @staticmethod
    def amount_max() -> Decimal:
        """报销/备用金/收入共用的单笔金额上限；缺失或损坏时回退默认值。"""
        raw = SystemConfigService.get("claim.amount_max")
        try:
            value = Decimal(str(raw))
        except (InvalidOperation, ValueError):
            return AMOUNT_MAX_DEFAULT
        if not value.is_finite() or value <= 0:
            return AMOUNT_MAX_DEFAULT
        return value

    @staticmethod
    def set(key: str, value: Any, admin_id: int | None) -> None:
        SystemConfigModel.objects.update_or_create(
            key=key, defaults={"value": value, "updated_by_admin_id": admin_id}
        )

    @staticmethod
    def all_editable() -> dict[str, Any]:
        return {key: SystemConfigService.get(key) for key in sorted(EDITABLE_KEYS)}


SystemConfig = SystemConfigService  # 兼容 IFC 命名
