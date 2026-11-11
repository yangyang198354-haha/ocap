"""MOD-042：文本转换、媒体提取、平台不支持特征（IFC-171）。"""
import re
import uuid

from .paginate import paginate
from .render import render_blocks, render_html

FEATURE_ORDER = ["page_break", "video", "text_align", "text_color", "background_color",
                 "font_size", "line_height", "blockquote"]


def text_to_doc(text: str) -> dict:
    blocks: list[dict] = []
    for raw in str(text or "").replace("\r\n", "\n").split("\n\n"):
        lines = raw.split("\n")
        heading = re.match(r"^(#{1,4})\s+(.*)$", lines[0])
        if heading:
            blocks.append({
                "type": "heading",
                "attrs": {"level": len(heading.group(1))},
                "content": [{"type": "text", "text": heading.group(2).strip()}],
            })
            lines = lines[1:]
            if lines:
                content = []
                for i, line in enumerate(lines):
                    if i:
                        content.append({"type": "hardBreak"})
                    content.append({"type": "text", "text": line})
                blocks.append({"type": "paragraph", "content": content})
            continue
        content = []
        for i, line in enumerate(lines):
            if i:
                content.append({"type": "hardBreak"})
            content.append({"type": "text", "text": line})
        blocks.append({"type": "paragraph", "content": content})
    return {"type": "doc", "content": blocks}


def extract_media_ids(doc: dict) -> list[uuid.UUID]:
    found: list[uuid.UUID] = []
    seen: set[str] = set()

    def walk(node: dict) -> None:
        if node.get("type") in {"image", "video"}:
            raw = (node.get("attrs") or {}).get("mediaId")
            try:
                value = str(uuid.UUID(str(raw)))
            except (TypeError, ValueError):
                return
            if value not in seen:
                seen.add(value)
                found.append(uuid.UUID(value))
        for child in node.get("content") or []:
            walk(child)

    walk(doc)
    return found


def _features(node: dict, found: set[str]) -> None:
    ntype = node.get("type")
    attrs = node.get("attrs") or {}
    if ntype == "pageBreak":
        found.add("page_break")
    if ntype == "video":
        found.add("video")
    if ntype == "blockquote":
        found.add("blockquote")
    if attrs.get("textAlign"):
        found.add("text_align")
    if attrs.get("lineHeight"):
        found.add("line_height")
    for mark in node.get("marks") or []:
        mark_attrs = mark.get("attrs") or {}
        if mark.get("type") == "textStyle":
            if mark_attrs.get("color"):
                found.add("text_color")
            if mark_attrs.get("backgroundColor"):
                found.add("background_color")
            if mark_attrs.get("fontSize"):
                found.add("font_size")
            if mark_attrs.get("lineHeight"):
                found.add("line_height")
    for child in node.get("content") or []:
        _features(child, found)


def unsupported_features(doc: dict, *, platform_unsupported: frozenset[str]) -> list[str]:
    present: set[str] = set()
    _features(doc, present)
    hits = present & set(platform_unsupported)
    return [name for name in FEATURE_ORDER if name in hits]


def render_pages(doc: dict, tokens, *, fmt: str, resolve, page_chars: int) -> list[dict]:
    pages = paginate(doc, page_chars)
    result = []
    for index, page in enumerate(pages):
        if fmt == "blocks":
            result.append({"index": index, "blocks": render_blocks(page, resolve)})
        else:
            result.append({"index": index, "html": render_html(page, tokens, mode="web", resolve=resolve)})
    return result
