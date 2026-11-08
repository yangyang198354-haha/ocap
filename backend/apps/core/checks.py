"""启动检查（module_design MOD-001 配置项清单）。"""
from django.conf import settings
from django.core.checks import register, Error, Warning
from django.db.utils import OperationalError, ProgrammingError

from .config import SystemConfig
from .user_refs import assert_all_user_fks_registered


def _config_int(key: str, default: int) -> int:
    try:
        return int(SystemConfig.get(key))
    except (OperationalError, ProgrammingError):
        from .config import DEFAULTS

        return int(DEFAULTS.get(key, default))


@register()
def check_sms_template_ttl(app_configs, **kwargs):
    if settings.ALIYUN_SMS_TEMPLATE_TTL_MINUTES * 60 != _config_int("code.sms.ttl_seconds", 300):
        return [Error("短信模板有效期与 code.sms.ttl_seconds 不一致", id="core.E001")]
    return []


@register()
def check_sms_code_length(app_configs, **kwargs):
    length = _config_int("code.sms.length", 6)
    if not 4 <= length <= 6:
        return [Error("验证码位数须在 4..6", id="core.E002")]
    return []


@register()
def check_retention(app_configs, **kwargs):
    try:
        months = int(SystemConfig.get("audit.retention_months"))
    except (OperationalError, ProgrammingError):
        months = 24
    if months < 6:
        return [Error("审计保留期限不得低于 6 个月", id="core.E003")]
    return []


@register()
def check_user_refs(app_configs, **kwargs):
    try:
        assert_all_user_fks_registered()
    except AssertionError as exc:
        return [Warning(str(exc), id="core.W001")]
    except (OperationalError, ProgrammingError):
        return []
    return []
