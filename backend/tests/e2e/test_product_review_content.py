"""ocap_product_review GROUP_D：content_publish 批次的补充 E2E（TC-E2E-318 起）：
US-113 分页阅读（既有用例无 US/AC 编号引用），并验证本批新增的自定义版式模板（US-162）驱动页长与样式。
"""
from tests.integration.test_content_api import ContentTestBase, doc, para


class ContentPagingWithTemplateJourneyTests(ContentTestBase):
    def _publish(self, blocks, style="builtin:classic"):
        post = self.assert_ok(self.create_post("e2e_分页", content=blocks, style=style), 201).data
        self.assert_ok(self.publish(post["id"]))
        return post["id"]

    def test_tc_e2e_318_us_113_pagination_by_marker_by_page_chars_and_single_page(self):
        """TC-E2E-318 / US-113（AC-113-01、03、04）、US-162（AC-162-02）：分页标记把正文分两页（第 1 页只含标记前内容）；
        自定义模板 page_chars=200 时长文自动分页且最后一页显示剩余内容；短文只有 1 页；blocks 输出的 theme 与保存的样式值逐项一致。"""
        marker = self._publish([para("第一部分"), {"type": "pageBreak"}, para("第二部分")])
        web = self.assert_ok(self.api("get", f"/info/posts/{marker}", token=self.member_token)).data
        self.assertEqual(web["page_count"], 2)
        self.assertIn("第一部分", web["pages"][0]["html"])
        self.assertNotIn("第二部分", web["pages"][0]["html"])
        self.assertIn("第二部分", web["pages"][1]["html"])
        tokens = {"page_chars": 200, "font_size": 18, "text_color": "#223344", "line_height": 1.8}
        tpl = self.assert_ok(self.api("post", "/admin/content/style-templates", {"name": "e2e_短页", "tokens": tokens},
                                      token=self.admin_token), 201).data
        long_blocks = [para(f"第{i}段：" + "文" * 120) for i in range(6)]
        long_id = self._publish(long_blocks, style=tpl["key"])
        pages = self.assert_ok(self.api("get", f"/info/posts/{long_id}", token=self.member_token)).data
        self.assertGreaterEqual(pages["page_count"], 3)
        self.assertIn("第5段", pages["pages"][-1]["html"])
        all_html = "".join(p["html"] for p in pages["pages"])
        self.assertEqual(all_html.count("第0段"), 1)
        for i in range(6):
            self.assertIn(f"第{i}段", all_html)
        blocks = self.assert_ok(self.api("get", f"/info/posts/{long_id}?fmt=blocks", token=self.member_token)).data
        for key, value in tokens.items():
            self.assertEqual(blocks["theme"][key], value, key)
        short = self._publish([para("很短")], style=tpl["key"])
        self.assertEqual(self.api("get", f"/info/posts/{short}", token=self.member_token).data["page_count"], 1)
        mini = self.api("get", f"/info/posts/{marker}?fmt=blocks", token=self.member_token).data
        self.assertEqual(mini["page_count"], web["page_count"])  # AC-113-02：小程序与 Web 分页位置一致

    def test_tc_e2e_319_us_162_edit_template_changes_published_rendering_and_delete_blocked_until_unused(self):
        """TC-E2E-319 / US-162（AC-162-02、03、04）：修改自定义模板后，已发布内容立即按新样式值渲染；被引用时不能删除，内容删除后可删除。"""
        tpl = self.assert_ok(self.api("post", "/admin/content/style-templates", {"name": "e2e_改样式", "tokens": {"font_size": 16}},
                                      token=self.admin_token), 201).data
        post_id = self._publish([para("样式正文")], style=tpl["key"])
        first = self.api("get", f"/info/posts/{post_id}", token=self.member_token).data["pages"][0]["html"]
        self.assertIn("font-size:16px", first)
        self.assert_ok(self.api("put", f"/admin/content/style-templates/{tpl['id']}",
                                {"name": "e2e_改样式2", "tokens": {"font_size": 22}}, token=self.admin_token))
        second = self.api("get", f"/info/posts/{post_id}", token=self.member_token).data["pages"][0]["html"]
        self.assertIn("font-size:22px", second)
        self.assertIn("样式正文", second)
        self.assert_error(self.api("delete", f"/admin/content/style-templates/{tpl['id']}", token=self.admin_token), 409, "STYLE_IN_USE")
        self.assert_ok(self.api("delete", f"/admin/content/posts/{post_id}", token=self.admin_token), 204)
        self.assert_ok(self.api("delete", f"/admin/content/style-templates/{tpl['id']}", token=self.admin_token), 204)
