"""MOD-043：样式模板（IFC-172）。"""
import re
from typing import Mapping

from apps.core.errors import ApiError

from .conf import ContentSettings
from .models import StyleTemplate

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

BUILTIN_TEMPLATES = {
    "builtin:classic": {
        "key": "builtin:classic", "name": "经典", "builtin": True,
        "tokens": {"font_family_key": "sans", "font_size": 16, "line_height": 1.8,
                   "paragraph_spacing": 12, "text_color": "#333333",
                   "heading_color": "#111111", "link_color": "#1a73e8",
                   "quote_border_color": "#d0d7de", "accent_color": "#1a73e8"},
    },
    "builtin:notice": {
        "key": "builtin:notice", "name": "公告", "builtin": True,
        "tokens": {"font_family_key": "serif", "font_size": 18, "line_height": 2.0,
                   "paragraph_spacing": 16, "text_color": "#1f2937",
                   "heading_color": "#111827", "link_color": "#b45309",
                   "quote_border_color": "#f59e0b", "accent_color": "#b45309"},
    },
    "builtin:formal": {
        "key": "builtin:formal", "name": "正式", "builtin": True,
        "tokens": {"font_family_key": "serif", "font_size": 17, "line_height": 1.9,
                   "paragraph_spacing": 14, "text_color": "#222222",
                   "heading_color": "#000000", "link_color": "#0f4c81",
                   "quote_border_color": "#9ca3af", "accent_color": "#0f4c81"},
    },
}

TOKEN_RULES = {
    "font_size": (12, 24), "line_height": (1.2, 2.4), "paragraph_spacing": (0, 32),
    "page_chars": (200, 20000),
}


class StyleService:
    @staticmethod
    def list_all() -> list[dict]:
        items = [dict(item) for item in BUILTIN_TEMPLATES.values()]
        for row in StyleTemplate.objects.order_by("id"):
            items.append({"key": f"custom:{row.id}", "name": row.name,
                          "builtin": False, "tokens": row.tokens})
        return items

    @staticmethod
    def resolve_tokens(style_key: str) -> dict:
        if style_key in BUILTIN_TEMPLATES:
            tokens = dict(BUILTIN_TEMPLATES[style_key]["tokens"])
        elif style_key.startswith("custom:"):
            try:
                row = StyleTemplate.objects.get(id=int(style_key.split(":", 1)[1]))
            except (ValueError, StyleTemplate.DoesNotExist):
                return StyleService.resolve_tokens("builtin:classic")
            tokens = dict(row.tokens)
        else:
            return StyleService.resolve_tokens("builtin:classic")
        tokens.setdefault("page_chars", ContentSettings.get("content.page.default_chars"))
        return tokens

    @staticmethod
    def validate_tokens(tokens: Mapping) -> dict:
        if not isinstance(tokens, Mapping):
            raise ApiError("STYLE_INVALID", "样式定义格式不正确", 400, {"field": "tokens"})
        clean: dict = {}
        for key, value in tokens.items():
            if key in {"font_family_key"}:
                if value not in {"sans", "serif"}:
                    raise ApiError("STYLE_INVALID", "字体取值不合法", 400, {"field": key})
                clean[key] = value
            elif key in TOKEN_RULES:
                low, high = TOKEN_RULES[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
                    raise ApiError("STYLE_INVALID", "样式数值越界", 400, {"field": key})
                clean[key] = value
            elif key in {"text_color", "heading_color", "link_color",
                         "quote_border_color", "accent_color"}:
                if not isinstance(value, str) or not COLOR_RE.match(value):
                    raise ApiError("STYLE_INVALID", "颜色格式不正确", 400, {"field": key})
                clean[key] = value
        return clean

    @staticmethod
    def create(*, name: str, tokens: Mapping, admin_id: int) -> dict:
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ApiError("STYLE_NAME_REQUIRED", "模板名称不能为空", 400)
        if len(clean_name) > 64:
            raise ApiError("INVALID_VALUE", "模板名称过长", 400)
        if StyleTemplate.objects.filter(name=clean_name).exists():
            raise ApiError("STYLE_NAME_EXISTS", "模板名称已存在", 409)
        row = StyleTemplate.objects.create(name=clean_name,
                                           tokens=StyleService.validate_tokens(tokens),
                                           created_by_admin_id=admin_id)
        return {"key": f"custom:{row.id}", "name": row.name, "builtin": False, "tokens": row.tokens}

    @staticmethod
    def update(template_id: int, *, name: str | None, tokens: Mapping | None) -> dict:
        row = StyleTemplate.objects.filter(id=template_id).first()
        if row is None:
            from apps.core.errors import NotFound
            raise NotFound("样式模板不存在")
        if name is not None:
            clean_name = str(name).strip()
            if not clean_name:
                raise ApiError("STYLE_NAME_REQUIRED", "模板名称不能为空", 400)
            if StyleTemplate.objects.exclude(id=row.id).filter(name=clean_name).exists():
                raise ApiError("STYLE_NAME_EXISTS", "模板名称已存在", 409)
            row.name = clean_name
        if tokens is not None:
            row.tokens = StyleService.validate_tokens(tokens)
        row.save()
        return {"key": f"custom:{row.id}", "name": row.name, "builtin": False, "tokens": row.tokens}

    @staticmethod
    def delete(template_id: int) -> None:
        from apps.core.errors import NotFound
        deleted, _ = StyleTemplate.objects.filter(id=template_id).delete()
        if not deleted:
            raise NotFound("样式模板不存在")
