"""MOD-041：内容中心参数（IFC-168）。"""
from typing import Any, Mapping

from apps.core.config import SystemConfig
from apps.core.errors import ApiError

# key: (default, type, min, max, confirmed, note)
SPEC: dict[str, tuple] = {
    "content.media.image_max_bytes": (10485760, "int", 1048576, 52428800, True, "C-29"),
    "content.media.image_exts": (["jpg", "jpeg", "png"], "list", None, None, True, "C-29"),
    "content.media.video_max_bytes": (10485760, "int", 1048576, 209715200, False, "OQ-6"),
    "content.media.video_exts": (["mp4"], "list", None, None, False, "OQ-6"),
    "content.media.ai_image_max_bytes": (10485760, "int", 1048576, 52428800, False, ""),
    "content.media.ai_video_max_bytes": (52428800, "int", 1048576, 524288000, False, "[ESTIMATE]"),
    "content.media.total_quota_bytes": (1073741824, "int", 0, None, False, "OQ-6 [ESTIMATE]"),
    "content.media.min_free_bytes": (536870912, "int", 0, None, False, "[ESTIMATE]"),
    "content.media.candidate_ttl_hours": (24, "int", 1, 720, False, ""),
    "content.media.url_ttl_seconds": (3600, "int", 60, 86400, False, ""),
    "content.media.push_url_ttl_seconds": (86400, "int", 3600, 604800, False, ""),
    "content.post.max_doc_bytes": (1048576, "int", 65536, 8388608, False, "OQ-2"),
    "content.page.default_chars": (1500, "int", 200, 20000, False, "OQ-2"),
    "content.ai.rate_limit_per_hour": (30, "int", 1, 600, False, ""),
    "content.ai.max_prompt_chars": (4000, "int", 100, 20000, False, ""),
    "content.job.retention_days": (30, "int", 1, 365, False, ""),
    "content.job.lease_seconds": (300, "int", 60, 1800, True, "ADR-049"),
    "content.llm.timeout_seconds": (120, "int", 10, 300, True, "P11"),
    "content.image.timeout_seconds": (120, "int", 10, 300, True, "P11"),
    "content.image.default_size": ("2048x2048", "str", None, None, True, "P11"),
    "content.video.max_scenes": (5, "int", 1, 10, False, "A-6"),
    "content.video.scene_seconds": (5, "int", 2, 10, False, "A-6"),
    "content.video.transition": ("cut", "str", None, None, False, "A-6"),
    "content.video.poll_interval_seconds": (15, "int", 5, 120, False, ""),
    "content.video.max_wait_seconds": (1800, "int", 120, 7200, False, ""),
    "content.video.max_text_chars": (2000, "int", 50, 10000, False, ""),
    "content.wechat_mp.timeout_seconds": (30, "int", 5, 120, True, "P11"),
    "content.wechat_mp.auth_errcodes": ([], "list", None, None, False, "Q-A3"),
}


def _valid(key: str, value: Any) -> bool:
    default, typ, low, high, _, _ = SPEC[key]
    if typ == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            return False
        if low is not None and value < low:
            return False
        if high is not None and value > high:
            return False
        if key == "content.media.total_quota_bytes" and value not in (0,) and value < 67108864:
            return False
        if key == "content.media.image_exts":
            return False
        return True
    if typ == "str":
        if not isinstance(value, str):
            return False
        if key == "content.image.default_size":
            import re
            return bool(re.match(r"^\d{3,4}x\d{3,4}$", value))
        if key == "content.video.transition":
            import re
            return bool(re.match(r"^[a-z_]{1,16}$", value))
        return True
    if typ == "list":
        if not isinstance(value, list):
            return False
        if key == "content.media.image_exts":
            return set(map(str, value)) <= {"jpg", "jpeg", "png"}
        if key == "content.media.video_exts":
            return set(map(str, value)) <= {"mp4", "mov"}
        if key == "content.wechat_mp.auth_errcodes":
            return all(isinstance(v, int) and not isinstance(v, bool) for v in value)
        return True
    return isinstance(value, bool)


class ContentSettings:
    @staticmethod
    def get(key: str) -> Any:
        if key not in SPEC:
            return None
        default = SPEC[key][0]
        value = SystemConfig.get(key, default)
        return value if _valid(key, value) else default

    @staticmethod
    def all_items() -> list[dict]:
        items = []
        for key, (default, typ, low, high, confirmed, note) in SPEC.items():
            value = ContentSettings.get(key)
            items.append({"key": key, "value": value, "default": default, "type": typ,
                          "min": low, "max": high, "confirmed": confirmed, "note": note})
        return items

    @staticmethod
    def update(values: Mapping[str, Any], *, admin_id: int) -> list[str]:
        changed = []
        for key, value in values.items():
            if key not in SPEC or not str(key).startswith("content."):
                raise ApiError("INVALID_VALUE", "不支持的参数键", 400, {"key": key})
            if not _valid(key, value):
                raise ApiError("INVALID_VALUE", "参数取值不合法", 400, {"key": key})
        for key, value in values.items():
            SystemConfig.set(key, value, admin_id)
            changed.append(key)
        return changed
