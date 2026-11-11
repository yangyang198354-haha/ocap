"""MOD-042：富文本渲染（IFC-170），输出 HTML / 块 / 纯文本。"""
import html
from dataclasses import dataclass
from typing import Callable, TypedDict
from uuid import UUID

FONT_FAMILIES = {
    "sans": "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif",
    "serif": "Georgia,'Songti SC',serif",
}


class MediaRef(TypedDict):
    url: str
    media_type: str
    title: str


MediaResolver = Callable[[UUID], MediaRef | None]


@dataclass(frozen=True)
class StyleTokens:
    font_family_key: str = "sans"
    font_size: int = 16
    line_height: float = 1.8
    paragraph_spacing: int = 12
    text_color: str = "#333333"
    heading_color: str = "#111111"
    link_color: str = "#1a73e8"
    quote_border_color: str = "#d0d7de"
    accent_color: str = "#1a73e8"
    page_chars: int = 1500


def _esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _normalize(tokens) -> StyleTokens:
    if isinstance(tokens, StyleTokens):
        return tokens
    data = dict(tokens or {})
    allowed = {key: data[key] for key in StyleTokens.__dataclass_fields__ if key in data}
    return StyleTokens(**allowed)


def _font(tokens: StyleTokens) -> str:
    return FONT_FAMILIES.get(tokens.font_family_key, FONT_FAMILIES["sans"])


def _merge_marks(node: dict) -> dict:
    inline: dict = {}
    for mark in node.get("marks") or []:
        mtype = mark.get("type")
        attrs = mark.get("attrs") or {}
        if mtype in {"bold", "italic", "underline", "strike"}:
            inline[mtype] = True
        elif mtype == "link":
            inline["href"] = attrs.get("href")
        elif mtype == "textStyle":
            if attrs.get("color"):
                inline["color"] = attrs["color"]
            if attrs.get("backgroundColor"):
                inline["bg"] = attrs["backgroundColor"]
            if attrs.get("fontSize"):
                inline["size"] = int(float(attrs["fontSize"].replace("px", "")))
            if attrs.get("lineHeight"):
                inline["lh"] = attrs["lineHeight"]
    return inline


def _inline_of(node: dict) -> list[dict]:
    inlines = []
    if node.get("type") == "text" and node.get("text"):
        inlines.append({"text": node["text"], **_merge_marks(node)})
    for child in node.get("content") or []:
        if child.get("type") == "text":
            text = child.get("text") or ""
            if text:
                inlines.append({"text": text, **_merge_marks(child)})
        elif child.get("type") == "hardBreak":
            inlines.append({"text": "\n"})
    return inlines


def _children(node: dict) -> list[dict]:
    return list(node.get("content") or [])


def _list_items(node: dict) -> list[list[dict]]:
    items = []
    for item in _children(node):
        blocks = []
        for child in _children(item):
            blocks.extend(_node_to_blocks(child))
        items.append(blocks)
    return items


def _node_to_blocks(node: dict) -> list[dict]:
    ntype = node.get("type")
    attrs = node.get("attrs") or {}
    if ntype == "paragraph":
        block = {"type": "paragraph", "inlines": _inline_of(node)}
        if attrs.get("textAlign"):
            block["align"] = attrs["textAlign"]
        if attrs.get("lineHeight"):
            block["lh"] = attrs["lineHeight"]   # 1.1.0：块级行距（ADR-063 第 7 条）
        return [block]
    if ntype == "heading":
        block = {"type": "heading", "level": attrs.get("level", 1), "inlines": _inline_of(node)}
        if attrs.get("textAlign"):
            block["align"] = attrs["textAlign"]
        if attrs.get("lineHeight"):
            block["lh"] = attrs["lineHeight"]
        return [block]
    if ntype == "bulletList":
        return [{"type": "bullet_list", "items": _list_items(node)}]
    if ntype == "orderedList":
        return [{"type": "ordered_list", "start": attrs.get("start", 1), "items": _list_items(node)}]
    if ntype == "blockquote":
        children = []
        for child in _children(node):
            children.extend(_node_to_blocks(child))
        return [{"type": "quote", "children": children}]
    if ntype == "horizontalRule":
        return [{"type": "hr"}]
    if ntype == "image":
        return [{"type": "image", "media_id": attrs.get("mediaId"), "alt": attrs.get("alt", "")}]
    if ntype == "video":
        return [{"type": "video", "media_id": attrs.get("mediaId")}]
    if ntype == "pageBreak":
        return [{"type": "page_break"}]
    return []


def _resolve_media(blocks: list[dict], resolve: MediaResolver) -> None:
    """任意深度（顶层、引用、列表项）解析图片/视频的 src；素材不存在则原位替换为提示段落。"""
    for block in blocks:
        kind = block.get("type")
        if kind in {"image", "video"}:
            ref = resolve(UUID(block["media_id"])) if block.get("media_id") else None
            if ref is None:
                block.clear()
                block.update({"type": "paragraph", "inlines": [{"text": "[素材已删除]"}]})
            else:
                block["src"] = ref["url"]
        elif kind == "quote":
            _resolve_media(block.get("children", []), resolve)
        elif kind in {"bullet_list", "ordered_list"}:
            for item in block.get("items", []):
                _resolve_media(item, resolve)


def render_blocks(doc: dict, resolve: MediaResolver) -> list[dict]:
    blocks = []
    for node in _children(doc):
        blocks.extend(_node_to_blocks(node))
    _resolve_media(blocks, resolve)
    return blocks


def _inline_html(inline: dict, tokens: StyleTokens) -> str:
    text = _esc(inline.get("text", "")).replace("\n", "<br/>")
    styles = []
    if inline.get("bold"):
        styles.append("font-weight:700")
    if inline.get("italic"):
        styles.append("font-style:italic")
    if inline.get("underline") and inline.get("strike"):
        # 合并为单个声明，避免两个 text-decoration 互相覆盖（ADR-063 第 7 条）
        styles.append("text-decoration:underline line-through")
    elif inline.get("underline"):
        styles.append("text-decoration:underline")
    elif inline.get("strike"):
        styles.append("text-decoration:line-through")
    if inline.get("color"):
        styles.append(f"color:{inline['color']}")
    if inline.get("bg"):
        styles.append(f"background-color:{inline['bg']}")
    if inline.get("size"):
        styles.append(f"font-size:{inline['size']}px")
    if inline.get("lh"):
        styles.append(f"line-height:{inline['lh']}")
    if styles:
        text = f'<span style="{";".join(styles)}">{text}</span>'
    if inline.get("href"):
        text = (f'<a href="{_esc(inline["href"])}" target="_blank" '
                f'rel="noopener noreferrer nofollow" style="color:{tokens.link_color}">{text}</a>')
    return text


def _block_html(block: dict, tokens: StyleTokens, resolve: MediaResolver) -> str:
    block_styles = []
    if block.get("align"):
        block_styles.append(f'text-align:{_esc(block["align"])}')
    if block.get("lh"):
        block_styles.append(f'line-height:{_esc(block["lh"])}')
    align = f' style="{";".join(block_styles)}"' if block_styles else ""
    kind = block.get("type")
    if kind == "paragraph":
        content = "".join(_inline_html(i, tokens) for i in block.get("inlines", []))
        return f"<p{align}>{content}</p>"
    if kind == "heading":
        level = min(max(int(block.get("level", 1)), 1), 4)
        content = "".join(_inline_html(i, tokens) for i in block.get("inlines", []))
        return f"<h{level}{align}>{content}</h{level}>"
    if kind == "bullet_list":
        items = "".join("<li>" + _nested_html(blocks, tokens, resolve) + "</li>"
                        for blocks in block.get("items", []))
        return f"<ul>{items}</ul>"
    if kind == "ordered_list":
        start = int(block.get("start", 1))
        attr = f' start="{start}"' if start != 1 else ""
        items = "".join("<li>" + _nested_html(blocks, tokens, resolve) + "</li>"
                        for blocks in block.get("items", []))
        return f"<ol{attr}>{items}</ol>"
    if kind == "quote":
        inner = "".join(_block_html(b, tokens, resolve) for b in block.get("children", []))
        return f'<blockquote style="border-left:3px solid {tokens.quote_border_color};padding-left:12px">{inner}</blockquote>'
    if kind == "hr":
        return '<hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0"/>'
    if kind == "image":
        # src 已由 render_blocks 在任意深度解析；缺失即素材不存在
        if not block.get("src"):
            return "<p>[素材已删除]</p>"
        return (f'<figure><img src="{_esc(block["src"])}" alt="{_esc(block.get("alt", ""))}" '
                f'style="max-width:100%;height:auto"/></figure>')
    if kind == "video":
        if not block.get("src"):
            return "<p>[素材已删除]</p>"
        return f'<video controls src="{_esc(block["src"])}" style="max-width:100%"></video>'
    if kind == "page_break":
        return '<hr class="rt-page-break" style="border:none;border-top:1px dashed #cbd5e1;margin:24px 0"/>'
    return ""


def _nested_html(blocks: list[dict], tokens: StyleTokens, resolve: MediaResolver) -> str:
    return "".join(_block_html(b, tokens, resolve) for b in blocks)


def render_html(doc: dict, tokens: StyleTokens, *, mode: str, resolve: MediaResolver) -> str:
    tokens = _normalize(tokens)
    body = "".join(_block_html(b, tokens, resolve) for b in render_blocks(doc, resolve))
    if mode == "inline":
        return (f'<div style="font-family:{_font(tokens)};font-size:{tokens.font_size}px;'
                f'line-height:{tokens.line_height};color:{tokens.text_color}">{body}</div>')
    style = (f'font-family:{_font(tokens)};font-size:{tokens.font_size}px;'
             f'line-height:{tokens.line_height};color:{tokens.text_color};'
             f'--rt-font:{_font(tokens)};--rt-size:{tokens.font_size}px;'
             f'--rt-line:{tokens.line_height};--rt-spacing:{tokens.paragraph_spacing}px;'
             f'--rt-color:{tokens.text_color};--rt-heading:{tokens.heading_color};'
             f'--rt-link:{tokens.link_color};--rt-accent:{tokens.accent_color}')
    return f'<article class="rt-article" style="{style}">{body}</article>'


def render_text(doc: dict) -> str:
    lines: list[str] = []

    def walk(node: dict) -> None:
        ntype = node.get("type")
        if ntype == "text":
            if lines:
                lines[-1] += node.get("text") or ""
            else:
                lines.append(node.get("text") or "")
        elif ntype == "hardBreak":
            if lines:
                lines[-1] += "\n"
        elif ntype in {"paragraph", "heading"}:
            lines.append("")
            for child in node.get("content") or []:
                walk(child)
        elif ntype in {"bulletList", "orderedList", "listItem", "blockquote"}:
            for child in node.get("content") or []:
                walk(child)
        elif ntype in {"image", "video"}:
            lines.append("[图片]" if ntype == "image" else "[视频]")
        elif ntype == "horizontalRule":
            lines.append("———")
        elif ntype == "pageBreak":
            lines.append("")
        elif ntype == "doc":
            for child in node.get("content") or []:
                walk(child)
            lines.append("")

    walk(doc)
    return "\n".join(line for line in lines if line is not None).strip()
