"""GROUP_D：富文本引擎单元测试（TC-UNIT-301~320）。"""
import unittest

from apps.content.richtext import (
    DocValidationError, extract_media_ids, paginate, render_blocks, render_html,
    render_text, text_to_doc, unsupported_features, validate_doc,
)
from apps.content.richtext.render import StyleTokens


def doc(*blocks):
    return {"type": "doc", "content": list(blocks)}


def para(text, marks=None, attrs=None):
    node = {"type": "text", "text": text}
    if marks:
        node["marks"] = marks
    block = {"type": "paragraph", "content": [node]}
    if attrs:
        block["attrs"] = attrs
    return block


class ValidateDocTests(unittest.TestCase):
    def test_tc_unit_301_empty_doc_allowed(self):
        self.assertEqual(validate_doc(None, max_bytes=1024)["content"], [])

    def test_tc_unit_302_unknown_node_dropped_and_attrs_normalized(self):
        raw = doc({"type": "paragraph", "attrs": {"textAlign": "center", "foo": "bar"},
                   "content": [{"type": "text", "text": "正文", "marks": [{"type": "bold"}]}]})
        clean = validate_doc(raw, max_bytes=4096)
        self.assertEqual(clean["content"][0]["attrs"], {"textAlign": "center"})
        self.assertEqual(clean["content"][0]["content"][0]["marks"], [{"type": "bold"}])

    def test_tc_unit_303_script_link_rejected(self):
        raw = doc(para("x", marks=[{"type": "link", "attrs": {"href": "javascript:alert(1)"}}]))
        with self.assertRaises(DocValidationError) as ctx:
            validate_doc(raw, max_bytes=4096)
        self.assertEqual(ctx.exception.reason, "LINK")

    def test_tc_unit_304_allowed_link_kept(self):
        raw = doc(para("官网", marks=[{"type": "link", "attrs": {"href": "https://example.com/a"}}]))
        clean = validate_doc(raw, max_bytes=4096)
        self.assertEqual(clean["content"][0]["content"][0]["marks"][0]["attrs"]["href"],
                         "https://example.com/a")

    def test_tc_unit_305_invalid_color_and_font_size(self):
        for attrs, reason in (({"color": "red"}, "COLOR"),
                              ({"fontSize": "100px"}, "SIZE"),
                              ({"lineHeight": 9}, "SIZE")):
            raw = doc(para("x", marks=[{"type": "textStyle", "attrs": attrs}]))
            with self.assertRaises(DocValidationError) as ctx:
                validate_doc(raw, max_bytes=4096)
            self.assertEqual(ctx.exception.reason, reason)

    def test_tc_unit_306_media_id_invalid(self):
        raw = doc({"type": "image", "attrs": {"mediaId": "not-a-uuid"}})
        with self.assertRaises(DocValidationError) as ctx:
            validate_doc(raw, max_bytes=4096)
        self.assertEqual(ctx.exception.reason, "MEDIA_ID")

    def test_tc_unit_307_doc_bytes_limit(self):
        raw = doc(para("x" * 500))
        with self.assertRaises(DocValidationError):
            validate_doc(raw, max_bytes=100)

    def test_tc_unit_308_heading_level_range(self):
        raw = doc({"type": "heading", "attrs": {"level": 9}, "content": []})
        with self.assertRaises(DocValidationError):
            validate_doc(raw, max_bytes=4096)


class RenderTests(unittest.TestCase):
    def test_tc_unit_309_renders_escaped_html_with_marks_and_align(self):
        raw = doc(para("<script>alert(1)</script>", marks=[{"type": "bold"}],
                       attrs={"textAlign": "center"}))
        html = render_html(raw, StyleTokens(), mode="web", resolve=lambda _: None)
        self.assertIn('text-align:center', html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("font-weight:700", html)

    def test_tc_unit_310_link_gets_security_attrs(self):
        raw = doc(para("链接", marks=[{"type": "link", "attrs": {"href": "https://a.b"}}]))
        html = render_html(raw, StyleTokens(), mode="inline", resolve=lambda _: None)
        self.assertIn('rel="noopener noreferrer nofollow"', html)
        self.assertIn('target="_blank"', html)

    def test_tc_unit_311_missing_media_degrades(self):
        raw = doc({"type": "image", "attrs": {"mediaId": "00000000-0000-0000-0000-000000000001"}})
        html = render_html(raw, StyleTokens(), mode="web", resolve=lambda _: None)
        self.assertIn("[素材已删除]", html)
        self.assertNotIn("<img", html)

    def test_tc_unit_312_media_resolved(self):
        media_id = "00000000-0000-0000-0000-000000000002"
        raw = doc({"type": "image", "attrs": {"mediaId": media_id}})
        ref = {"url": "https://cdn/x.png", "media_type": "IMAGE", "title": "图"}
        blocks = render_blocks(raw, lambda _: ref)
        self.assertEqual(blocks[0]["src"], "https://cdn/x.png")
        html = render_html(raw, StyleTokens(), mode="web", resolve=lambda _: ref)
        self.assertIn('src="https://cdn/x.png"', html)

    def test_tc_unit_313_render_text_paragraphs(self):
        raw = doc(para("第一段"), para("第二段"))
        self.assertEqual(render_text(raw), "第一段\n第二段")

    def test_tc_unit_314_blocks_keep_list_structure(self):
        raw = doc({"type": "bulletList", "content": [
            {"type": "listItem", "content": [para("甲")]},
            {"type": "listItem", "content": [para("乙")]},
        ]})
        blocks = render_blocks(raw, lambda _: None)
        self.assertEqual(blocks[0]["type"], "bullet_list")
        self.assertEqual(len(blocks[0]["items"]), 2)

    def test_tc_unit_315_blocks_include_attrs_whitelist(self):
        raw = doc(para("x", attrs={"textAlign": "right"}))
        self.assertEqual(render_blocks(raw, lambda _: None)[0]["align"], "right")


class PaginateConvertTests(unittest.TestCase):
    def test_tc_unit_316_page_break_splits(self):
        raw = doc(para("A"), {"type": "pageBreak"}, para("B"))
        pages = paginate(raw, 1500)
        self.assertEqual(len(pages), 2)
        self.assertEqual(render_text(pages[0]), "A")
        self.assertEqual(render_text(pages[1]), "B")

    def test_tc_unit_317_page_chars_splits_blocks(self):
        raw = doc(para("甲" * 10), para("乙" * 10), para("丙" * 10))
        pages = paginate(raw, 15)
        self.assertGreaterEqual(len(pages), 2)
        self.assertEqual(sum(len(p["content"]) for p in pages), 3)

    def test_tc_unit_318_single_page_when_short(self):
        self.assertEqual(len(paginate(doc(para("短")), 1500)), 1)

    def test_tc_unit_319_text_to_doc_headings_and_breaks(self):
        node = text_to_doc("# 标题\n正文\n第二行\n\n普通段")
        self.assertEqual(node["content"][0]["type"], "heading")
        self.assertEqual(node["content"][1]["content"][1]["type"], "hardBreak")
        self.assertEqual(node["content"][2]["type"], "paragraph")

    def test_tc_unit_320_extract_media_and_unsupported(self):
        media_id = "00000000-0000-0000-0000-000000000003"
        raw = doc({"type": "video", "attrs": {"mediaId": media_id}},
                  para("x", attrs={"textAlign": "center"}), {"type": "pageBreak"})
        self.assertEqual([str(i) for i in extract_media_ids(raw)], [media_id])
        names = unsupported_features(raw, platform_unsupported=frozenset(
            {"page_break", "video", "text_align"}))
        self.assertEqual(names, ["page_break", "video", "text_align"])
