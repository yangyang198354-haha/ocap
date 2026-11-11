"""MOD-042：富文本文档白名单校验（IFC-169）。

严格模式 validate_doc：1.0.0 行为不变（非法即抛 DocValidationError）。
宽容模式 validate_doc_ex（1.1.0，ADR-062）：样式类与可丢弃类问题丢弃/归一化并返回 warnings，
结构类与资源类问题仍抛 DocValidationError。
"""
import json
import math
import re
import uuid
from dataclasses import dataclass
from typing import Any

MAX_DEPTH = 12
MAX_NODES = 20000
MAX_CHARS = 100000
MAX_WARNINGS = 50

COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
SIZE_RE = re.compile(r"^(\d{2}(\.\d)?)px$")
LINK_RE = re.compile(r"^(https?://|mailto:|tel:)", re.I)
WHITESPACE_RE = re.compile(r"[\s\x00-\x1f\x7f]")
# rgb()/rgba() 逗号形式（IFC-169；前端 colors.js 使用同一规则）
RGB_RE = re.compile(
    r"^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*"
    r"(?:,\s*(\d(?:\.\d+)?|\.\d+)\s*)?\)$")

ALLOWED_TYPES = {
    "doc", "paragraph", "heading", "bulletList", "orderedList", "listItem",
    "blockquote", "horizontalRule", "hardBreak", "image", "video", "pageBreak", "text",
}
ALIGN = {"left", "center", "right", "justify"}


class DocValidationError(ValueError):
    def __init__(self, path: str, reason: str, block_index: int | None = None,
                 block_type: str | None = None):
        super().__init__(reason)
        self.path = path
        self.reason = reason
        self.block_index = block_index   # 1.1.0：顶层块序号（从 0 起）；doc 级错误为 None
        self.block_type = block_type     # 1.1.0：该顶层块的节点类型


@dataclass(frozen=True)
class ValidationResult:
    doc: dict
    warnings: tuple
    warning_total: int


class _Ctx:
    """宽容模式上下文：收集 warnings。严格模式传 None。"""

    def __init__(self) -> None:
        self.warnings: list[dict] = []
        self.total = 0
        self.block_index: int | None = None

    def warn(self, path: str, reason: str, action: str) -> None:
        self.total += 1
        if len(self.warnings) < MAX_WARNINGS:
            self.warnings.append({"path": path, "block_index": self.block_index,
                                  "reason": reason, "action": action})


def _absent(value: Any, ctx: "_Ctx | None") -> bool:
    """宽容模式下 null/空串视为"未设置"（编辑器对没有该属性的 textStyle 标记会输出 null 或空串），不产生警告。

    严格模式（ctx 为 None）保持 1.0.0 行为。
    """
    return ctx is not None and (value is None or value == "")


def normalize_color(value: Any) -> str | None:
    """#hex 原样；rgb()/rgba() → #rrggbb[aa]；其余 None（IFC-169 共享测试向量）。"""
    if not isinstance(value, str):
        return None
    if COLOR_RE.fullmatch(value):
        return value
    match = RGB_RE.fullmatch(value)
    if not match:
        return None
    channels = [int(match.group(i)) for i in (1, 2, 3)]
    if any(c > 255 for c in channels):
        return None
    alpha_text = match.group(4)
    out = "#%02x%02x%02x" % tuple(channels)
    if alpha_text is not None:
        alpha = float(alpha_text)
        if alpha > 1:
            return None
        if alpha < 1:
            # 四舍五入取半向上（不用 Python round），与前端 Math.floor(a*255+0.5) 一致
            out += "%02x" % int(math.floor(alpha * 255 + 0.5))
    assert COLOR_RE.fullmatch(out)
    return out


def _check_color(value: Any, path: str) -> str:
    if not isinstance(value, str) or not COLOR_RE.match(value):
        raise DocValidationError(path, "COLOR")
    return value


def _norm_marks(marks: Any, path: str, ctx: _Ctx | None = None) -> list[dict]:
    if not isinstance(marks, list):
        raise DocValidationError(path, "ATTR")
    result = []
    for i, mark in enumerate(marks):
        if not isinstance(mark, dict):
            raise DocValidationError(f"{path}[{i}]", "ATTR")
        mtype = mark.get("type")
        attrs = mark.get("attrs") or {}
        if not isinstance(attrs, dict):
            raise DocValidationError(f"{path}[{i}].attrs", "ATTR")
        if mtype in {"bold", "italic", "underline", "strike"}:
            result.append({"type": mtype})
        elif mtype == "link":
            href = attrs.get("href")
            if not isinstance(href, str) or len(href) > 2048 or WHITESPACE_RE.search(href) \
                    or not LINK_RE.match(href):
                if ctx is None:
                    raise DocValidationError(f"{path}[{i}].attrs.href", "LINK")
                ctx.warn(f"{path}[{i}].attrs.href", "LINK", "DROPPED")
                continue
            result.append({"type": "link", "attrs": {"href": href}})
        elif mtype == "textStyle":
            clean = {}
            for key in ("color", "backgroundColor"):
                if key not in attrs or _absent(attrs[key], ctx):
                    continue
                attr_path = f"{path}[{i}].attrs.{key}"
                if ctx is None:
                    clean[key] = _check_color(attrs[key], attr_path)
                    continue
                normalized = normalize_color(attrs[key])
                if normalized is None:
                    ctx.warn(attr_path, "COLOR", "DROPPED")
                    continue
                if normalized != attrs[key]:
                    ctx.warn(attr_path, "COLOR", "NORMALIZED")
                clean[key] = normalized
            if "fontSize" in attrs and not _absent(attrs["fontSize"], ctx):
                text = attrs["fontSize"]
                match = SIZE_RE.match(text) if isinstance(text, str) else None
                if not match or not 10 <= float(match.group(1)) <= 48:
                    if ctx is None:
                        raise DocValidationError(f"{path}[{i}].attrs.fontSize", "SIZE")
                    ctx.warn(f"{path}[{i}].attrs.fontSize", "SIZE", "DROPPED")
                else:
                    clean["fontSize"] = text
            if "lineHeight" in attrs and not _absent(attrs["lineHeight"], ctx):
                lh_path = f"{path}[{i}].attrs.lineHeight"
                lh = _to_line_height(attrs["lineHeight"])
                if lh is None:
                    if ctx is None:
                        raise DocValidationError(lh_path, "SIZE")
                    ctx.warn(lh_path, "SIZE", "DROPPED")
                else:
                    clean["lineHeight"] = lh
            if clean:
                result.append({"type": "textStyle", "attrs": clean})
    return result


def _to_line_height(value: Any) -> float | None:
    """合法行距（1.0~3.0 的有限数）返回浮点，否则 None。"""
    try:
        lh = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(lh) or not 1.0 <= lh <= 3.0:
        return None
    return lh


def _media_id(attrs: dict) -> str | None:
    try:
        return str(uuid.UUID(str(attrs.get("mediaId"))))
    except (TypeError, ValueError):
        return None


def _norm_node(node: Any, depth: int, counter: list[int], path: str,
               ctx: _Ctx | None = None) -> dict | None:
    """返回规范化节点；宽容模式下被丢弃的节点返回 None。"""
    if depth > MAX_DEPTH:
        raise DocValidationError(path, "LIMIT")
    if not isinstance(node, dict):
        raise DocValidationError(path, "TYPE")
    ntype = node.get("type")
    if not isinstance(ntype, str) or ntype not in ALLOWED_TYPES:
        if ctx is None or depth == 0:
            raise DocValidationError(path, "TYPE")
        ctx.warn(path, "TYPE", "DROPPED")
        return None
    counter[0] += 1
    if counter[0] > MAX_NODES:
        raise DocValidationError(path, "LIMIT")

    clean: dict = {"type": ntype}
    attrs = node.get("attrs") or {}
    if not isinstance(attrs, dict):
        raise DocValidationError(path + ".attrs", "ATTR")

    if ntype in {"paragraph", "heading"}:
        out = {}
        if attrs.get("textAlign") in ALIGN:
            out["textAlign"] = attrs["textAlign"]
        if ntype == "heading":
            level_path = path + ".attrs.level"
            try:
                level = int(attrs.get("level", 1))
            except (TypeError, ValueError, OverflowError):
                if ctx is None:
                    raise DocValidationError(level_path, "ATTR")
                ctx.warn(level_path, "LEVEL", "DROPPED")
                level = 1
            if not 1 <= level <= 4:
                if ctx is None:
                    raise DocValidationError(level_path, "ATTR")
                if level > 4:
                    ctx.warn(level_path, "LEVEL", "CLAMPED")
                    level = 4
                else:
                    ctx.warn(level_path, "LEVEL", "DROPPED")
                    level = 1
            out["level"] = level
        if "lineHeight" in attrs and not _absent(attrs["lineHeight"], ctx):
            lh_path = path + ".attrs.lineHeight"
            lh = _to_line_height(attrs["lineHeight"])
            if lh is not None:
                out["lineHeight"] = lh
            elif ctx is not None:
                ctx.warn(lh_path, "SIZE", "DROPPED")
            else:
                # 严格模式（1.0.0 行为）：非数字抛错，数值越界静默丢弃
                try:
                    float(attrs["lineHeight"])
                except (TypeError, ValueError):
                    raise DocValidationError(lh_path, "SIZE")
        if out:
            clean["attrs"] = out
    elif ntype == "orderedList":
        try:
            start = int(attrs.get("start", 1))
        except (TypeError, ValueError, OverflowError):
            raise DocValidationError(path + ".attrs.start", "ATTR")
        clean["attrs"] = {"start": min(max(start, 1), 9999)}
    elif ntype in {"image", "video"}:
        media_id = _media_id(attrs)
        if media_id is None:
            if ctx is None:
                raise DocValidationError(path + ".attrs.mediaId", "MEDIA_ID")
            # 外链/data: 图片等无有效 mediaId 的节点：丢弃，不下载不转存（ADR-062）
            ctx.warn(path + ".attrs.mediaId", "MEDIA_ID", "DROPPED")
            return None
        if ntype == "image":
            alt = attrs.get("alt") or ""
            if not isinstance(alt, str):
                raise DocValidationError(path + ".attrs.alt", "ATTR")
            clean["attrs"] = {"mediaId": media_id, "alt": alt[:200]}
        else:
            clean["attrs"] = {"mediaId": media_id}
    elif ntype == "text":
        text = node.get("text")
        if not isinstance(text, str):
            raise DocValidationError(path + ".text", "TYPE")
        clean["text"] = text
        marks = node.get("marks")
        if marks:
            clean["marks"] = _norm_marks(marks, path + ".marks", ctx)

    content = node.get("content")
    if content is not None:
        if not isinstance(content, list):
            raise DocValidationError(path + ".content", "ATTR")
        children = []
        for i, child in enumerate(content):
            if depth == 0 and ctx is not None:
                ctx.block_index = i
            try:
                normalized = _norm_node(child, depth + 1, counter, f"{path}.content[{i}]", ctx)
            except DocValidationError as exc:
                if depth == 0 and exc.block_index is None:
                    exc.block_index = i
                    exc.block_type = child.get("type") if isinstance(child, dict) \
                        and isinstance(child.get("type"), str) else None
                raise
            if normalized is None:
                continue
            if normalized["type"] == "text" and not normalized.get("text"):
                continue
            children.append(normalized)
        clean["content"] = children

    if ntype == "doc" and clean.get("content") is None:
        clean["content"] = []
    return clean


def _finish(doc: Any, max_bytes: int, ctx: _Ctx | None) -> dict:
    if doc is None:
        doc = {"type": "doc", "content": []}
    if not isinstance(doc, dict) or doc.get("type") != "doc":
        raise DocValidationError("", "TYPE")
    counter = [0]
    clean = _norm_node(doc, 0, counter, "", ctx)
    if _count_chars(clean) > MAX_CHARS:
        raise DocValidationError("", "LIMIT")
    try:
        size = len(json.dumps(clean, ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError):
        raise DocValidationError("", "TYPE")
    if size > max_bytes:
        raise DocValidationError("", "LIMIT")
    return clean


def validate_doc(doc: Any, *, max_bytes: int) -> dict:
    """严格模式（1.0.0 行为不变）。"""
    return _finish(doc, max_bytes, None)


def validate_doc_ex(doc: Any, *, max_bytes: int) -> ValidationResult:
    """宽容模式（ADR-062）：HTTP 视图一律使用本函数。"""
    ctx = _Ctx()
    clean = _finish(doc, max_bytes, ctx)
    return ValidationResult(doc=clean, warnings=tuple(ctx.warnings), warning_total=ctx.total)


def _count_chars(node: dict) -> int:
    total = len(node.get("text") or "")
    for child in node.get("content") or []:
        total += _count_chars(child)
    return total
