# MOD-076 / implements IFC-272 / depends core.config
"""规则限制常量与当前生效值（行为不变，仅集中）。"""
from .config import SystemConfigService

POLL_OPTIONS_MIN: int = 2
POLL_OPTIONS_MAX: int = 10
INCOME_IMPORT_MAX_ROWS: int = 5000
INCOME_MANUAL_MAX_RECORDS: int = 500


def current_limits() -> dict[str, object]:
    return {
        "claim_amount_max": f"{SystemConfigService.amount_max():.2f}",
        "poll_max_questions": int(SystemConfigService.get("poll.max_questions") or 50),
        "poll_options_min": POLL_OPTIONS_MIN,
        "poll_options_max": POLL_OPTIONS_MAX,
        "vote_min_window_minutes": int(SystemConfigService.get("vote.min_window_minutes") or 60),
        "income_import_max_rows": INCOME_IMPORT_MAX_ROWS,
        "income_manual_max_records": INCOME_MANUAL_MAX_RECORDS,
    }
