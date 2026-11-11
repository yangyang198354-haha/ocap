"""MOD-042：富文本文档白名单校验（IFC-169）。"""
import json
import re
import uuid
from typing import Any

MAX_DEPTH = 12
MAX_NODES = 20000
MAX_CHARS = 100000

COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
SIZE_RE = re.compile(r"^(\d{2}(\.\d)?)px$")
LINK_RE = re.compile(r"^(https?://|mailto:|tel:)", re.I)
WHITESPACE_RE = re.compile(r"[\s\x00-\x1f\x7f]")

ALLOWED_TYPES = {
    "doc", "paragraph", "heading", "bulletList", "orderedList", "listItem",
    "blockquote", "horizontalRule", "hardBreak", "image", "video", "pageBreak", "text",
}
ALIGN = {"left", "center", "right", "justify"}


class DocValidationError(ValueError):
    def __init__(self, path: str, reason: str):
        super().__init__(reason)
        self.path = path
        self.reason = reason


def _check_color(value: Any, path: str) -> str:
    if not isinstance(value, str) or not COLOR_RE.match(value):
        raise DocValidationError(path, "COLOR")
    return value


def _norm_marks(marks: Any, path: str) -> list[dict]:
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
                raise DocValidationError(f"{path}[{i}].attrs.href", "LINK")
            result.append({"type": "link", "attrs": {"href": href}})
        elif mtype == "textStyle":
            clean = {}
            if "color" in attrs:
                clean["color"] = _check_color(attrs["color"], f"{path}[{i}].attrs.color")
            if "backgroundColor" in attrs:
                clean["backgroundColor"] = _check_color(
                    attrs["backgroundColor"], f"{path}[{i}].attrs.backgroundColor")
            if "fontSize" in attrs:
                text = attrs["fontSize"]
                match = SIZE_RE.match(text) if isinstance(text, str) else None
                if not match or not 10 <= float(match.group(1)) <= 48:
                    raise DocValidationError(f"{path}[{i}].attrs.fontSize", "SIZE")
                clean["fontSize"] = text
            if "lineHeight" in attrs:
                try:
                    lh = float(attrs["lineHeight"])
                except (TypeError, ValueError):
                    raise DocValidationError(f"{path}[{i}].attrs.lineHeight", "SIZE")
                if not 1.0 <= lh <= 3.0:
                    raise DocValidationError(f"{path}[{i}].attrs.lineHeight", "SIZE")
                clean["lineHeight"] = lh
            if clean:
                result.append({"type": "textStyle", "attrs": clean})
    return result


def _norm_node(node: Any, depth: int, counter: list[int], path: str) -> dict:
    if depth > MAX_DEPTH:
        raise DocValidationError(path, "LIMIT")
    if not isinstance(node, dict):
        raise DocValidationError(path, "TYPE")
    ntype = node.get("type")
    if ntype not in ALLOWED_TYPES:
        raise DocValidationError(path, "TYPE")
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
            try:
                level = int(attrs.get("level", 1))
            except (TypeError, ValueError):
                raise DocValidationError(path + ".attrs.level", "ATTR")
            if not 1 <= level <= 4:
                raise DocValidationError(path + ".attrs.level", "ATTR")
            out["level"] = level
        if "lineHeight" in attrs:
            try:
                lh = float(attrs["lineHeight"])
            except (TypeError, ValueError):
                raise DocValidationError(path + ".attrs.lineHeight", "SIZE")
            if 1.0 <= lh <= 3.0:
                out["lineHeight"] = lh
        if out:
            clean["attrs"] = out
    elif ntype == "orderedList":
        try:
            start = int(attrs.get("start", 1))
        except (TypeError, ValueError):
            raise DocValidationError(path + ".attrs.start", "ATTR")
        clean["attrs"] = {"start": min(max(start, 1), 9999)}
    elif ntype == "image":
        try:
            media_id = str(uuid.UUID(str(attrs.get("mediaId"))))
        except (TypeError, ValueError):
            raise DocValidationError(path + ".attrs.mediaId", "MEDIA_ID")
        alt = attrs.get("alt") or ""
        if not isinstance(alt, str):
            raise DocValidationError(path + ".attrs.alt", "ATTR")
        clean["attrs"] = {"mediaId": media_id, "alt": alt[:200]}
    elif ntype == "video":
        try:
            media_id = str(uuid.UUID(str(attrs.get("mediaId"))))
        except (TypeError, ValueError):
            raise DocValidationError(path + ".attrs.mediaId", "MEDIA_ID")
        clean["attrs"] = {"mediaId": media_id}
    elif ntype == "text":
        text = node.get("text")
        if not isinstance(text, str):
            raise DocValidationError(path + ".text", "TYPE")
        clean["text"] = text
        marks = node.get("marks")
        if marks:
            clean["marks"] = _norm_marks(marks, path + ".marks")

    content = node.get("content")
    if content is not None:
        if not isinstance(content, list):
            raise DocValidationError(path + ".content", "ATTR")
        children = []
        for i, child in enumerate(content):
            normalized = _norm_node(child, depth + 1, counter, f"{path}.content[{i}]")
            if normalized["type"] == "text" and not normalized.get("text"):
                continue
            children.append(normalized)
        clean["content"] = children

    if ntype == "doc" and clean.get("content") is None:
        clean["content"] = []
    return clean


def validate_doc(doc: Any, *, max_bytes: int) -> dict:
    if doc is None:
        doc = {"type": "doc", "content": []}
    if not isinstance(doc, dict) or doc.get("type") != "doc":
        raise DocValidationError("", "TYPE")
    counter = [0]
    clean = _norm_node(doc, 0, counter, "")
    if _count_chars(clean) > MAX_CHARS:
        raise DocValidationError("", "LIMIT")
    try:
        size = len(json.dumps(clean, ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError):
        raise DocValidationError("", "TYPE")
    if size > max_bytes:
        raise DocValidationError("", "LIMIT")
    return clean


def _count_chars(node: dict) -> int:
    total = len(node.get("text") or "")
    for child in node.get("content") or []:
        total += _count_chars(child)
    return total
