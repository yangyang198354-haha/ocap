"""MOD-042：按分页标记与页长分页（IFC-171）。"""
from .render import render_text


def _char_count(node: dict) -> int:
    return len(render_text({"type": "doc", "content": [node]}))


def paginate(doc: dict, page_chars: int) -> list[dict]:
    """先按 pageBreak 切，再按顶层块累计字数换页；不拆分单个块。"""
    groups: list[list[dict]] = [[]]
    for node in doc.get("content") or []:
        if node.get("type") == "pageBreak":
            if groups[-1]:
                groups.append([])
            continue
        groups[-1].append(node)

    pages: list[list[dict]] = []
    for group in groups:
        current: list[dict] = []
        count = 0
        for node in group:
            size = _char_count(node)
            if current and count + size > page_chars:
                pages.append(current)
                current = []
                count = 0
            current.append(node)
            count += size
        if current:
            pages.append(current)
    if not pages:
        pages = [[]]
    return [{"type": "doc", "content": page} for page in pages]
