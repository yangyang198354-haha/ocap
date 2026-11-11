"""GROUP_D（回流 1）：富文本宽容校验 / 渲染口径单元测试（TC-UNIT-348~367）。

依据 module_design 1.1.0 IFC-169/170/171 的规则表与共享测试向量（ADR-062/063）。
期望值取自设计文档的规则与向量，不由被测代码输出反推。
"""
import json
import re
import unittest
from pathlib import Path

from apps.content.richtext import (
    DocValidationError, extract_media_ids, extract_paragraphs, normalize_color, render_blocks,
    render_html, validate_doc, validate_doc_ex,
)
from apps.content.richtext.render import StyleTokens

VECTORS = json.loads((Path(__file__).resolve().parents[1] / "data" / "color_vectors.json")
                     .read_text(encoding="utf-8"))["vectors"]
BIG = 10 ** 9
MID_A = "00000000-0000-0000-0000-0000000000a1"
MID_B = "00000000-0000-0000-0000-0000000000b2"
MID_C = "00000000-0000-0000-0000-0000000000c3"


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


def style(**attrs):
    return [{"type": "textStyle", "attrs": attrs}]


def marks_of(result, block=0, node=0):
    return result.doc["content"][block]["content"][node].get("marks", [])


def resolver(table):
    def resolve(media_id):
        return table.get(str(media_id))
    return resolve


REFS = {
    MID_A: {"url": "https://cdn.test/a.png", "media_type": "IMAGE", "title": "图A"},
    MID_B: {"url": "https://cdn.test/b.mp4", "media_type": "VIDEO", "title": "视频B"},
    MID_C: {"url": "https://cdn.test/c.png", "media_type": "IMAGE", "title": "图C"},
}


class ColorVectorTests(unittest.TestCase):
    def test_tc_unit_348_shared_color_vectors(self):
        """AC-109-01：颜色归一化的共享向量（与前端 colors.js 同一组）。"""
        self.assertEqual(len(VECTORS), 17)
        for raw, expected in VECTORS:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_color(raw), expected)

    def test_tc_unit_362_normalized_output_always_valid_hex(self):
        for raw, expected in VECTORS:
            out = normalize_color(raw)
            if out is not None:
                self.assertRegex(out, r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


class LenientStyleTests(unittest.TestCase):
    def test_tc_unit_349_color_normalized_dropped_with_warnings(self):
        """AC-109-01 / F04：rgb()/rgba() 归一化为 #hex，非法颜色丢弃，文字保留，均带 block_index。"""
        raw = doc(para("甲", marks=style(color="rgb(255, 0, 0)", backgroundColor="rgba(0, 0, 0, 0.5)")),
                  para("乙", marks=style(color="red", backgroundColor="url(javascript:alert(1))")),
                  para("丙", marks=style(color="rgb(300, 0, 0)")))
        result = validate_doc_ex(raw, max_bytes=BIG)
        self.assertEqual(marks_of(result, 0)[0]["attrs"],
                         {"color": "#ff0000", "backgroundColor": "#00000080"})
        # 乙、丙：属性全部丢弃，textStyle 标记随之消失；文字仍在
        self.assertEqual(marks_of(result, 1), [])
        self.assertEqual(marks_of(result, 2), [])
        self.assertEqual([b["content"][0]["text"] for b in result.doc["content"]], ["甲", "乙", "丙"])
        got = [(w["block_index"], w["reason"], w["action"]) for w in result.warnings]
        self.assertEqual(got, [(0, "COLOR", "NORMALIZED"), (0, "COLOR", "NORMALIZED"),
                               (1, "COLOR", "DROPPED"), (1, "COLOR", "DROPPED"),
                               (2, "COLOR", "DROPPED")])
        self.assertEqual(result.warning_total, 5)
        self.assertNotIn("javascript", json.dumps(result.doc))

    def test_tc_unit_363_hex_untouched_no_warning(self):
        result = validate_doc_ex(doc(para("x", marks=style(color="#F00", backgroundColor="#12345678"))),
                                 max_bytes=BIG)
        self.assertEqual(marks_of(result)[0]["attrs"], {"color": "#F00", "backgroundColor": "#12345678"})
        self.assertEqual((result.warnings, result.warning_total), ((), 0))

    def test_tc_unit_364_size_and_line_height_dropped(self):
        raw = doc(para("x", marks=style(fontSize="100px", lineHeight=9)),
                  para("y", marks=style(fontSize="9px")),
                  para("z", marks=style(fontSize="20px", lineHeight=1.5)),
                  para("w", attrs={"lineHeight": 5}))
        result = validate_doc_ex(raw, max_bytes=BIG)
        self.assertEqual(marks_of(result, 0), [])
        self.assertEqual(marks_of(result, 1), [])
        self.assertEqual(marks_of(result, 2)[0]["attrs"], {"fontSize": "20px", "lineHeight": 1.5})
        self.assertNotIn("attrs", result.doc["content"][3])
        self.assertEqual([(w["block_index"], w["reason"], w["action"]) for w in result.warnings],
                         [(0, "SIZE", "DROPPED"), (0, "SIZE", "DROPPED"),
                          (1, "SIZE", "DROPPED"), (3, "SIZE", "DROPPED")])

    def test_tc_unit_350_null_and_empty_style_values_are_not_warnings(self):
        """F04：编辑器对无该属性的 textStyle 输出 null / 空串，视为未设置，不告警、不 400。"""
        raw = doc(para("x", marks=style(color=None, backgroundColor="", fontSize="", lineHeight=None)),
                  para("y", marks=style(color="", fontSize=None)))
        result = validate_doc_ex(raw, max_bytes=BIG)
        self.assertEqual(result.warning_total, 0)
        self.assertEqual(result.warnings, ())
        self.assertEqual(marks_of(result, 0), [])
        self.assertEqual(result.doc["content"][1]["content"][0]["text"], "y")

    def test_tc_unit_351_heading_level_clamped_or_defaulted(self):
        """AC-110-01：标题级别 >4 钳为 4（CLAMPED），<1 或非数字缺省 1（DROPPED），1..4 不变。"""
        def heading(level):
            return {"type": "heading", "attrs": {"level": level},
                    "content": [{"type": "text", "text": "标题"}]}
        raw = doc(*[heading(level) for level in (5, 6, 100, 0, -1, "abc", 3, "2")])
        result = validate_doc_ex(raw, max_bytes=BIG)
        self.assertEqual([b["attrs"]["level"] for b in result.doc["content"]], [4, 4, 4, 1, 1, 1, 3, 2])
        self.assertEqual([(w["block_index"], w["action"]) for w in result.warnings],
                         [(0, "CLAMPED"), (1, "CLAMPED"), (2, "CLAMPED"),
                          (3, "DROPPED"), (4, "DROPPED"), (5, "DROPPED")])
        self.assertTrue(all(w["reason"] == "LEVEL" for w in result.warnings))

    def test_tc_unit_365_strict_mode_unchanged(self):
        """回归：严格模式 validate_doc 仍按 1.0.0 行为抛错。"""
        for node, reason in (
                (para("x", marks=style(color="rgb(255,0,0)")), "COLOR"),
                (para("x", marks=[{"type": "link", "attrs": {"href": "javascript:1"}}]), "LINK"),
                ({"type": "heading", "attrs": {"level": 5}, "content": []}, "ATTR"),
                ({"type": "image", "attrs": {"mediaId": "x"}}, "MEDIA_ID"),
                ({"type": "script"}, "TYPE")):
            with self.subTest(reason=reason):
                with self.assertRaises(DocValidationError) as ctx:
                    validate_doc(doc(node), max_bytes=BIG)
                self.assertEqual(ctx.exception.reason, reason)


class LenientNodeTests(unittest.TestCase):
    def test_tc_unit_352_media_without_media_id_is_dropped(self):
        """AC-111-03 / F04：缺 mediaId、外链 src、data: 图片被丢弃（不下载不转存），其余内容保留。"""
        raw = doc(para("前"),
                  {"type": "image", "attrs": {"src": "https://evil.test/x.png"}},
                  {"type": "image", "attrs": {"src": "data:image/png;base64,AAAA", "mediaId": "not-a-uuid"}},
                  {"type": "video", "attrs": {"src": "https://evil.test/v.mp4"}},
                  {"type": "image", "attrs": {"mediaId": MID_A, "alt": "有效"}},
                  {"type": "blockquote", "content": [{"type": "image", "attrs": {"href": "x"}}]},
                  para("后"))
        result = validate_doc_ex(raw, max_bytes=BIG)
        types = [b["type"] for b in result.doc["content"]]
        self.assertEqual(types, ["paragraph", "image", "blockquote", "paragraph"])
        self.assertEqual(result.doc["content"][1]["attrs"], {"mediaId": MID_A, "alt": "有效"})
        self.assertEqual(result.doc["content"][2]["content"], [])
        self.assertEqual([(w["block_index"], w["reason"], w["action"]) for w in result.warnings],
                         [(1, "MEDIA_ID", "DROPPED"), (2, "MEDIA_ID", "DROPPED"),
                          (3, "MEDIA_ID", "DROPPED"), (5, "MEDIA_ID", "DROPPED")])
        dumped = json.dumps(result.doc)
        for needle in ("evil.test", "data:image", "src"):
            self.assertNotIn(needle, dumped)

    def test_tc_unit_353_unsafe_links_dropped_text_kept(self):
        """AC-107-04 / AC-109-03：javascript:/data:/vbscript:/含空白或控制字符/超长的链接一律丢弃，文字保留。"""
        bad = ["javascript:alert(1)", "JaVaScRiPt:alert(1)", " javascript:alert(1)",
               "data:text/html;base64,PHNjcmlwdD4=", "vbscript:msgbox(1)", "java\tscript:alert(1)",
               "https://a.test/a b", "https://a.test/\x00", "ftp://a.test/f", "//evil.test", "",
               None, 123, "https://a.test/" + "a" * 2048]
        raw = doc(*[para(f"链接{i}", marks=[{"type": "link", "attrs": {"href": href}}])
                    for i, href in enumerate(bad)])
        result = validate_doc_ex(raw, max_bytes=BIG)
        self.assertEqual(result.warning_total, len(bad))
        for index in range(len(bad)):
            node = result.doc["content"][index]["content"][0]
            self.assertEqual(node["text"], f"链接{index}")
            self.assertEqual(node.get("marks", []), [])
        self.assertNotIn("javascript", json.dumps(result.doc).lower())

    def test_tc_unit_366_allowed_link_schemes_kept(self):
        good = ["https://a.test/x?y=1", "http://a.test", "mailto:a@b.test", "tel:+8613800000000"]
        raw = doc(*[para("t", marks=[{"type": "link", "attrs": {"href": href}}]) for href in good])
        result = validate_doc_ex(raw, max_bytes=BIG)
        self.assertEqual(result.warning_total, 0)
        self.assertEqual([marks_of(result, i)[0]["attrs"]["href"] for i in range(4)], good)

    def test_tc_unit_354_unknown_nodes_dropped_structure_errors_raise(self):
        result = validate_doc_ex(doc(para("a"), {"type": "table", "content": [para("单元格")]},
                                     {"type": "blockquote", "content": [{"type": "codeBlock"}, para("q")]}),
                                 max_bytes=BIG)
        self.assertEqual([b["type"] for b in result.doc["content"]], ["paragraph", "blockquote"])
        self.assertEqual([(w["block_index"], w["reason"], w["action"]) for w in result.warnings],
                         [(1, "TYPE", "DROPPED"), (2, "TYPE", "DROPPED")])
        self.assertNotIn("单元格", json.dumps(result.doc, ensure_ascii=False))
        # 结构类错误仍抛出，并带顶层块序号 / 类型
        cases = [
            (doc(para("ok"), {"type": "paragraph", "content": "oops"}), "ATTR", 1, "paragraph"),
            (doc(para("ok"), {"type": "paragraph", "attrs": "bad"}), "ATTR", 1, "paragraph"),
            (doc({"type": "paragraph", "content": [{"type": "text", "text": 5}]}), "TYPE", 0, "paragraph"),
            ({"type": "paragraph", "content": []}, "TYPE", None, None),
            ("not-a-doc", "TYPE", None, None),
        ]
        for raw, reason, index, btype in cases:
            with self.subTest(reason=reason, index=index):
                with self.assertRaises(DocValidationError) as ctx:
                    validate_doc_ex(raw, max_bytes=BIG)
                self.assertEqual((ctx.exception.reason, ctx.exception.block_index,
                                  ctx.exception.block_type), (reason, index, btype))

    def test_tc_unit_355_limits_still_raise(self):
        """超限（深度 / 节点数 / 字符数 / 字节数）在宽容模式下仍是错误，不静默截断。"""
        deep = para("x")
        for _ in range(13):
            deep = {"type": "blockquote", "content": [deep]}
        many = doc(*[{"type": "paragraph"} for _ in range(20001)])
        for name, raw, limit in (("depth", doc(deep), BIG), ("nodes", many, BIG),
                                 ("chars", doc(para("字" * 100001)), BIG),
                                 ("bytes", doc(para("x" * 500)), 100)):
            with self.subTest(limit=name):
                with self.assertRaises(DocValidationError) as ctx:
                    validate_doc_ex(raw, max_bytes=limit)
                self.assertEqual(ctx.exception.reason, "LIMIT")

    def test_tc_unit_356_warnings_capped_at_50_total_kept(self):
        raw = doc(*[para("x", marks=[{"type": "link", "attrs": {"href": "javascript:1"}}])
                    for _ in range(60)])
        result = validate_doc_ex(raw, max_bytes=BIG)
        self.assertEqual(len(result.warnings), 50)
        self.assertEqual(result.warning_total, 60)


class RenderRuleTests(unittest.TestCase):
    TOKENS = StyleTokens()

    def test_tc_unit_358_block_line_height_in_html_and_blocks(self):
        """F07：段落 / 标题的块级行距在 web、inline、blocks 三种输出中都不丢；行内行距不覆盖块级。"""
        raw = doc(para("段", attrs={"lineHeight": 2.0, "textAlign": "center"}),
                  {"type": "heading", "attrs": {"level": 2, "lineHeight": 1.5},
                   "content": [{"type": "text", "text": "题"}]},
                  para("行内", marks=style(lineHeight=3.0), attrs={"lineHeight": 1.2}))
        for mode in ("web", "inline"):
            html = render_html(raw, self.TOKENS, mode=mode, resolve=resolver({}))
            self.assertRegex(html, r'<p style="text-align:center;line-height:2(\.0)?">段</p>')
            self.assertRegex(html, r'<h2 style="line-height:1\.5">题</h2>')
            self.assertRegex(html, r'<p style="line-height:1\.2"><span style="line-height:3(\.0)?">行内</span></p>')
        blocks = render_blocks(raw, resolver({}))
        self.assertEqual([b.get("lh") for b in blocks], [2.0, 1.5, 1.2])
        self.assertEqual(blocks[2]["inlines"][0]["lh"], 3.0)

    def test_tc_unit_359_nested_media_rendered_at_any_depth(self):
        """F07 / AC-107-03：引用、列表项内（含多层嵌套）的图片 / 视频完整渲染，HTML 与 blocks 一致。"""
        raw = doc(
            {"type": "blockquote", "content": [para("引"), {"type": "image", "attrs": {"mediaId": MID_A, "alt": "图A"}}]},
            {"type": "bulletList", "content": [{"type": "listItem", "content": [
                para("项"), {"type": "video", "attrs": {"mediaId": MID_B}}]}]},
            {"type": "blockquote", "content": [{"type": "orderedList", "content": [{"type": "listItem", "content": [
                {"type": "blockquote", "content": [{"type": "image", "attrs": {"mediaId": MID_C}}]}]}]}]})
        resolve = resolver(REFS)
        html = render_html(raw, self.TOKENS, mode="inline", resolve=resolve)
        quote = re.search(r"<blockquote[^>]*>(.*?)</blockquote>", html, re.S).group(1)
        self.assertIn('<img src="https://cdn.test/a.png" alt="图A"', quote)
        self.assertRegex(html, r"<ul><li><p>项</p><video controls src=\"https://cdn\.test/b\.mp4\"")
        self.assertIn('https://cdn.test/c.png', html)
        self.assertNotIn("[素材已删除]", html)
        blocks = render_blocks(raw, resolve)
        self.assertEqual(blocks[0]["children"][1]["src"], "https://cdn.test/a.png")
        self.assertEqual(blocks[1]["items"][0][1], {"type": "video", "media_id": MID_B,
                                                    "src": "https://cdn.test/b.mp4"})
        deep = blocks[2]["children"][0]["items"][0][0]["children"][0]
        self.assertEqual((deep["type"], deep["src"]), ("image", "https://cdn.test/c.png"))

    def test_tc_unit_367_missing_media_at_depth_degrades_in_place(self):
        raw = doc({"type": "blockquote", "content": [{"type": "image", "attrs": {"mediaId": MID_A}}]},
                  {"type": "bulletList", "content": [{"type": "listItem", "content": [
                      {"type": "video", "attrs": {"mediaId": MID_B}}]}]})
        html = render_html(raw, self.TOKENS, mode="web", resolve=resolver({}))
        self.assertEqual(html.count("[素材已删除]"), 2)
        self.assertNotIn("<img", html)
        self.assertNotIn("<video", html)
        self.assertNotIn('src=""', html)

    def test_tc_unit_360_underline_and_strike_merged(self):
        """F07：下划线 + 删除线只输出一个 text-decoration 声明；单独使用保持原样。"""
        both = render_html(doc(para("同时", marks=[{"type": "underline"}, {"type": "strike"}])),
                           self.TOKENS, mode="inline", resolve=resolver({}))
        self.assertIn("text-decoration:underline line-through", both)
        self.assertEqual(both.count("text-decoration"), 1)
        for marks, expected in (([{"type": "underline"}], "text-decoration:underline"),
                                ([{"type": "strike"}], "text-decoration:line-through")):
            html = render_html(doc(para("单", marks=marks)), self.TOKENS, mode="web", resolve=resolver({}))
            self.assertIn(f'<span style="{expected}">单</span>', html)
        inlines = render_blocks(doc(para("同时", marks=[{"type": "underline"}, {"type": "strike"}])),
                                resolver({}))[0]["inlines"]
        self.assertTrue(inlines[0]["underline"] and inlines[0]["strike"])

    def test_tc_unit_361_extract_paragraphs_and_media_ids_any_depth(self):
        raw = doc(para("一"),
                  {"type": "paragraph", "content": [{"type": "text", "text": "二"}, {"type": "hardBreak"},
                                                    {"type": "text", "text": "三"}]},
                  para("   "),
                  {"type": "bulletList", "content": [{"type": "listItem", "content": [
                      para("列表项"), {"type": "image", "attrs": {"mediaId": MID_A}}]}]},
                  {"type": "blockquote", "content": [{"type": "video", "attrs": {"mediaId": MID_B}},
                                                     {"type": "heading", "attrs": {"level": 1},
                                                      "content": [{"type": "text", "text": "引用标题"}]}]},
                  {"type": "horizontalRule"}, {"type": "pageBreak"})
        self.assertEqual(extract_paragraphs(raw), ["一", "二\n三", "列表项", "引用标题"])
        self.assertEqual([str(i) for i in extract_media_ids(raw)], [MID_A, MID_B])
