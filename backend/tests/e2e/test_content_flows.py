"""GROUP_D：内容中心端到端 API 旅程（TC-E2E-301~308）。"""
import io
import zipfile

from django.utils import timezone

from apps.content.drafts import DraftPushHandler
from apps.content.jobs import JobContext
from apps.content.models import ContentJob
from apps.integrations.draft import DraftOutcome, get_draft_adapter, set_draft_adapter
from apps.integrations.fakes import FakeDraftAdapter, FakeLlmClient
from apps.integrations.llm import set_llm_client
from apps.content.ai_jobs import ImageJobHandler, TextJobHandler, VideoJobHandler
from apps.content.media import set_remote_fetcher
from apps.integrations.fakes import (
    FakeDraftAdapter, FakeImageGenClient, FakeLlmClient, FakeRemoteFetcher, FakeVideoGenClient,
)
from apps.integrations.imagegen import set_imagegen_client
from apps.integrations.videogen import set_videogen_client
from tests.integration.test_content_api import ContentTestBase, MP4, PNG, doc, para


class ContentJourneyTests(ContentTestBase):
    def test_tc_e2e_301_edit_publish_web_and_miniprogram(self):
        """管理员编辑富文本→发布→Web 分页阅读→小程序 blocks→下线后不可见。"""
        style = self.api("post", "/admin/content/style-templates",
                         {"name": "E2E 模板", "tokens": {"font_size": 20, "text_color": "#222222"}},
                         token=self.admin_token)
        self.assert_ok(style, 201)
        media_id = self.upload_media(PNG, "a.png").data["id"]
        created = self.create_post("小区公告", content=[
            para("第一段", marks=[{"type": "bold"}], attrs={"textAlign": "center"}),
            {"type": "image", "attrs": {"mediaId": media_id}},
            {"type": "pageBreak"},
            para("第二页"),
        ], style=style.data["key"])
        post_id = created.data["id"]
        self.assert_ok(self.publish(post_id))

        web = self.api("get", f"/info/posts/{post_id}", token=self.member_token)
        self.assert_ok(web)
        self.assertEqual(web.data["page_count"], 2)
        self.assertIn("text-align:center", web.data["pages"][0]["html"])
        self.assertIn("font-size:20px", web.data["pages"][0]["html"])
        self.assertIn("<img", web.data["pages"][0]["html"])

        blocks = self.api("get", f"/info/posts/{post_id}?fmt=blocks", token=self.member_token)
        self.assert_ok(blocks)
        self.assertEqual(blocks.data["page_count"], 2)
        image_block = blocks.data["pages"][0]["blocks"][1]
        self.assertEqual(image_block["type"], "image")
        self.assertTrue(image_block["src"].startswith("/content/media/"))
        self.assertIn("theme", blocks.data)

        self.assert_ok(self.api("post", f"/admin/content/posts/{post_id}/offline", {},
                                token=self.admin_token))
        self.assert_error(self.api("get", f"/info/posts/{post_id}", token=self.member_token),
                          404, "NOT_FOUND")

    def test_tc_e2e_305_edit_save_with_warnings_publish_portal_and_miniprogram_read(self):
        """critical path（US-105/107/108/109/111）：编辑（粘贴来的 rgb 颜色、javascript: 链接、引用内图片）
        → 保存（返回 warnings，文档已规范化）→ 发布 → 门户 HTML / 小程序 blocks 读取，
        XSS 不回退（任何输出都不含 javascript:），格式与图片保留。"""
        media_id = self.upload_media(PNG, "nested.png", "引用内图").data["id"]
        dirty = [
            para("红字", marks=[{"type": "textStyle", "attrs": {"color": "rgb(255, 0, 0)"}}]),
            {"type": "paragraph", "content": [{"type": "text", "text": "坏链接", "marks": [
                {"type": "link", "attrs": {"href": "javascript:alert(1)"}}]}]},
            {"type": "blockquote", "content": [para("引文"), {"type": "image", "attrs": {"mediaId": media_id}}]},
            {"type": "image", "attrs": {"src": "https://evil.example/x.png"}},   # 无 mediaId：外链图片丢弃
        ]
        created = self.create_post("热点公告", content=dirty)
        self.assert_ok(created, 201)
        post_id = created.data["id"]
        reasons = sorted((w["reason"], w["action"]) for w in created.data["warnings"])
        self.assertIn(("COLOR", "NORMALIZED"), reasons)
        self.assertIn(("LINK", "DROPPED"), reasons)
        self.assertEqual(created.data["warning_total"], len(created.data["warnings"]))
        self.assertTrue(all("block_index" in w for w in created.data["warnings"]))
        self.assertNotIn("javascript", str(created.data["doc"]))
        self.assertIn("#ff0000", str(created.data["doc"]))

        # 保存已发布前再改一次（编辑→保存），仍带 warnings，随后发布
        updated = self.api("patch", f"/admin/content/posts/{post_id}",
                           {"doc": created.data["doc"], "title": "热点公告（改）"}, token=self.admin_token)
        self.assert_ok(updated)
        self.assertEqual(updated.data["warnings"], [])
        self.assert_ok(self.publish(post_id))

        web = self.api("get", f"/info/posts/{post_id}", token=self.member_token)
        self.assert_ok(web)
        html = web.data["pages"][0]["html"]
        self.assertNotIn("javascript:", html)
        self.assertIn("color:#ff0000", html)
        self.assertIn("坏链接", html)           # 文字保留，链接标记丢弃
        self.assertNotIn("evil.example", html)
        quote = html[html.index("<blockquote"):html.index("</blockquote>")]
        self.assertIn("<img", quote)             # 引用内图片在 HTML 中渲染

        blocks = self.api("get", f"/info/posts/{post_id}?fmt=blocks", token=self.member_token)
        self.assert_ok(blocks)
        self.assertNotIn("javascript:", str(blocks.data))
        quote_block = [b for b in blocks.data["pages"][0]["blocks"] if b["type"] == "quote"
                       or b.get("children")][0]
        image = [c for c in quote_block["children"] if c["type"] == "image"][0]
        self.assertIn("/content/media/%s/file?sig=" % media_id, image["src"])   # 前缀一致性见 TC-INT-388
        # 管理端详情与成员端同源：标题已更新
        self.assertEqual(self.api("get", "/info/posts", token=self.member_token).data["results"][0]["title"],
                         "热点公告（改）")

    def test_tc_e2e_302_generate_confirm_and_push_drafts(self):
        """配置模型→生成文案→确认→一键保存（自动 + 人工）→导出内容包。"""
        fake_llm = FakeLlmClient()
        fake_llm.responses = ["AI 文案第一段\n\nAI 文案第二段"]
        set_llm_client(fake_llm)
        self.addCleanup(set_llm_client, None)
        self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                 {"secrets": {"api_key": "sk-test"}}, token=self.admin_token)
        tested = self.api("post", "/admin/content/services/LLM_DEEPSEEK/test", {},
                          token=self.admin_token)
        self.assertTrue(tested.data["ok"])
        options = self.api("get", "/admin/content/llm/options", token=self.admin_token)
        self.assertEqual(len(options.data), 1)

        job = self.api("post", "/admin/content/ai/text", {"prompt": "写公告"}, token=self.admin_token)
        row = ContentJob.objects.get(id=job.data["id"])
        from apps.content.ai_jobs import TextJobHandler
        result = TextJobHandler().run(JobContext(row, timezone.now()))
        self.assertIn("AI 文案第二段", result.result["text"])

        post_id = self.create_post("AI 公告", content=[]).data["id"]
        self.api("patch", f"/admin/content/posts/{post_id}",
                 {"doc": result.result["doc"]}, token=self.admin_token)
        self.assert_ok(self.api("post", f"/admin/content/posts/{post_id}/confirm-text", {},
                                token=self.admin_token))
        self.assert_ok(self.publish(post_id))

        manual = self.api("post", "/admin/content/platform-accounts",
                          {"platform": "xiaohongshu", "display_name": "小红书"},
                          token=self.admin_token).data
        original = get_draft_adapter("wechat_mp")
        fake = FakeDraftAdapter("wechat_mp", outcomes=[DraftOutcome("SAVED", remote_ref="wx-1")])
        set_draft_adapter("wechat_mp", fake)
        self.addCleanup(set_draft_adapter, "wechat_mp", original)
        wechat = self.api("post", "/admin/content/platform-accounts",
                          {"platform": "wechat_mp", "display_name": "公众号",
                           "credentials": {"access_token": "tok-abcdef"}},
                          token=self.admin_token).data

        batch = self.api("post", f"/admin/content/posts/{post_id}/drafts",
                         {"account_ids": [manual["id"], wechat["id"]]}, token=self.admin_token)
        self.assert_ok(batch, 202)
        DraftPushHandler().run(JobContext(ContentJob.objects.get(id=batch.data["job_id"]),
                                          timezone.now()))
        history = self.api("get", f"/admin/content/posts/{post_id}/drafts/history",
                           token=self.admin_token)
        statuses = {row["platform"]: row["status"] for row in history.data["results"]}
        self.assertEqual(statuses["wechat_mp"], "SAVED")
        self.assertEqual(statuses["xiaohongshu"], "MANUAL_REQUIRED")

        pack = self.client_for(self.admin_token).get(
            f"/api/v1/admin/content/posts/{post_id}/export-pack?platform=xiaohongshu")
        payload = b"".join(pack.streaming_content)
        archive = zipfile.ZipFile(io.BytesIO(payload))
        self.assertIn("AI 文案第二段", archive.read("content.txt").decode("utf-8"))

    def test_tc_e2e_303_media_reuse_and_delete_protection(self):
        """上传素材→复用到两条内容→已发布引用时禁止删除→下线后允许删除。"""
        media_id = self.upload_media(PNG, "reuse.png").data["id"]
        first = self.create_post("内容一", content=[
            {"type": "image", "attrs": {"mediaId": media_id}}]).data["id"]
        second = self.create_post("内容二", content=[
            {"type": "image", "attrs": {"mediaId": media_id}}]).data["id"]
        self.publish(first)
        self.publish(second)
        usage = self.api("get", "/admin/content/media", token=self.admin_token)
        self.assertEqual(len(usage.data["results"]), 1)

        refused = self.api("delete", f"/admin/content/media/{media_id}", token=self.admin_token)
        self.assert_error(refused, 409, "MEDIA_IN_USE")
        self.assertEqual(len(refused.data["details"]["posts"]), 2)

        self.api("post", f"/admin/content/posts/{first}/offline", {}, token=self.admin_token)
        self.assert_error(self.api("delete", f"/admin/content/media/{media_id}",
                                   token=self.admin_token), 409, "MEDIA_IN_USE")
        self.api("post", f"/admin/content/posts/{second}/offline", {}, token=self.admin_token)
        import os
        from django.conf import settings
        from apps.content.models import MediaItem
        path = os.path.join(settings.MEDIA_ROOT, MediaItem.objects.get(id=media_id).storage_path)
        self.assertTrue(os.path.exists(path))
        # 文件在事务提交后删除（GR-C-003 CR-010），TestCase 内需显式执行 on_commit 回调
        with self.captureOnCommitCallbacks(execute=True):
            self.assert_ok(self.api("delete", f"/admin/content/media/{media_id}",
                                    token=self.admin_token), 204)
        self.assertFalse(os.path.exists(path))
        self.assertFalse(MediaItem.objects.filter(id=media_id).exists())

    def test_tc_e2e_304_ai_image_and_video_assets(self):
        """配置图像/视频服务→文生图入库→确认文案→视频生成入库（全部替身）。"""
        image_client = FakeImageGenClient()
        fetcher = FakeRemoteFetcher()
        fetcher.payloads = {
            "https://example.com/image.png": PNG,
            "https://example.com/clip.mp4": MP4,
        }
        set_imagegen_client(image_client)
        set_remote_fetcher(fetcher)
        self.addCleanup(set_imagegen_client, None)
        self.addCleanup(set_remote_fetcher, None)
        self.api("put", "/admin/content/services/IMAGE_ARK",
                 {"secrets": {"api_key": "sk-image"}}, token=self.admin_token)

        image_job = self.api("post", "/admin/content/ai/image",
                             {"prompt": "一张公告配图"}, token=self.admin_token)
        self.assert_ok(image_job, 202)
        row = ContentJob.objects.get(id=image_job.data["id"])
        outcome = ImageJobHandler().run(JobContext(row, timezone.now()))
        self.assertEqual(len(outcome.result["media"]), 1)
        media_id = outcome.result["media"][0]["id"]
        self.assert_ok(self.api("post", f"/admin/content/media/{media_id}/save", {},
                                token=self.admin_token))

        post_id = self.create_post("视频内容").data["id"]
        self.assert_ok(self.api("post", f"/admin/content/posts/{post_id}/confirm-text", {},
                                token=self.admin_token))
        self.api("put", "/admin/content/services/VIDEO_JIMENG",
                 {"secrets": {"access_key": "ak", "secret_key": "sk"}},
                 token=self.admin_token)
        video_client = FakeVideoGenClient()
        set_videogen_client(video_client)
        self.addCleanup(set_videogen_client, None)
        video_job = self.api("post", "/admin/content/ai/video", {"post_id": post_id},
                             token=self.admin_token)
        self.assert_ok(video_job, 202)
        row = ContentJob.objects.get(id=video_job.data["id"])
        first = VideoJobHandler().run(JobContext(row, timezone.now()))
        self.assertEqual(first.__class__.__name__, "Wait")
        row.refresh_from_db()
        outcome = VideoJobHandler().run(JobContext(row, timezone.now()))
        self.assertEqual(len(outcome.result["media"]), 1)
        self.assertEqual(outcome.result["media"][0]["media_type"], "VIDEO")

    def test_tc_e2e_306_upload_video_insert_publish_and_play_url(self):
        """US-123（critical path）：上传视频→插入正文→发布→门户 HTML / 小程序 blocks 都含视频，
        签名地址可取回文件（200）并支持 Range（206）。"""
        uploaded = self.upload_media(MP4, "clip.mp4", "宣传片")
        self.assert_ok(uploaded, 201)
        self.assertEqual((uploaded.data["media_type"], uploaded.data["source"]), ("VIDEO", "UPLOAD"))
        video_id = uploaded.data["id"]
        post_id = self.create_post("含视频公告", content=[
            para("请观看"), {"type": "video", "attrs": {"mediaId": video_id}}]).data["id"]
        self.assert_ok(self.publish(post_id))

        web = self.api("get", f"/info/posts/{post_id}", token=self.member_token)
        self.assert_ok(web)
        html = web.data["pages"][0]["html"]
        self.assertIn("<video", html)
        self.assertIn(f"/content/media/{video_id}/file?sig=", html)

        blocks = self.api("get", f"/info/posts/{post_id}?fmt=blocks", token=self.member_token)
        video = [b for b in blocks.data["pages"][0]["blocks"] if b["type"] == "video"][0]
        self.assertEqual(video["media_id"], video_id)
        self.assertTrue(video["src"].startswith("/content/media/%s/file?sig=" % video_id))

        client = self.client_for()   # 媒体地址靠签名鉴权，无需登录头
        signed = "/api/v1" + video["src"]
        full = client.get(signed)
        self.assertEqual(full.status_code, 200)
        self.assertEqual(b"".join(full.streaming_content), MP4)
        partial = client.get(signed, HTTP_RANGE="bytes=0-3")
        self.assertEqual(partial.status_code, 206)
        self.assertEqual(partial.content, MP4[:4])

    def test_tc_e2e_307_only_admin_can_manage_member_and_anonymous_rejected_end_to_end(self):
        """US-131（critical path）：未登录 / 业主 / 游客在整条管理链路（建稿→上传→发布→服务配置→平台账户）上
        全部被拒且无任何写入；管理员同一链路全部成功。"""
        from apps.content.models import ContentPost, MediaItem, PlatformAccount
        from apps.core.models import SystemConfig
        _owner, owner_token, _unit = self.make_owner()
        post_id = self.create_post("管理员稿").data["id"]
        counts = lambda: (ContentPost.objects.count(), MediaItem.objects.count(),  # noqa: E731
                          PlatformAccount.objects.count(), SystemConfig.objects.count())
        before = counts()
        steps = [
            ("post", "/admin/content/posts", {"title": "越权", "doc": doc(para("x"))}),
            ("patch", f"/admin/content/posts/{post_id}", {"title": "被篡改"}),
            ("post", f"/admin/content/posts/{post_id}/publish", {}),
            ("delete", f"/admin/content/posts/{post_id}", None),
            ("put", "/admin/content/services/LLM_DEEPSEEK", {"secrets": {"api_key": "sk-evil"}}),
            ("post", "/admin/content/platform-accounts", {"platform": "toutiao", "display_name": "越权"}),
            ("post", "/admin/content/ai/text", {"prompt": "x"}),
            ("get", f"/admin/content/posts/{post_id}/export-pack?platform=toutiao", None),
        ]
        for who, token, expected in (("未登录", None, 401), ("游客", self.member_token, 403),
                                     ("业主", owner_token, 403)):
            for method, path, body in steps:
                resp = self.api(method, path, body, token=token) if body is not None \
                    else self.api(method, path, token=token)
                self.assertEqual(resp.status_code, expected, (who, method, path))
        self.assertEqual(counts(), before)
        self.assertEqual(ContentPost.objects.get(id=post_id).title, "管理员稿")

        # 管理员（任一账号，无额外权限）同链路全部成功
        _other, other_token = self.make_admin()
        created = self.api("post", "/admin/content/posts", {"title": "二号管理员稿", "doc": doc(para("正文"))},
                           token=other_token)
        self.assert_ok(created, 201)
        self.assert_ok(self.api("post", f"/admin/content/posts/{created.data['id']}/publish", {},
                                token=other_token))
        self.assert_ok(self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                                {"secrets": {"api_key": "sk-ok"}}, token=other_token))
        self.assert_ok(self.api("post", "/admin/content/platform-accounts",
                                {"platform": "toutiao", "display_name": "头条"}, token=other_token), 201)
        self.assert_ok(self.api("get", "/info/posts", token=self.member_token))

    def test_tc_e2e_308_full_basic_format_list_survives_save_publish_and_render(self):
        """US-110 / US-109（critical path）：基础格式清单的每一项经 保存（无 warnings）→ 发布 → 门户渲染 保持：
        标题 1/4、加粗斜体下划线删除线、对齐、字号、文字色/背景色、行距、超链接、有序/无序列表、引用、分割线、分页。"""
        blocks = [
            {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "一级标题"}]},
            {"type": "heading", "attrs": {"level": 4}, "content": [{"type": "text", "text": "四级标题"}]},
            para("粗斜下删", marks=[{"type": "bold"}, {"type": "italic"}, {"type": "underline"}, {"type": "strike"}]),
            para("样式", marks=[{"type": "textStyle", "attrs": {
                "color": "#ff0000", "backgroundColor": "#ffff00", "fontSize": "20px", "lineHeight": 1.5}}],
                attrs={"textAlign": "right"}),
            para("链接", marks=[{"type": "link", "attrs": {"href": "https://example.com"}}]),
            {"type": "bulletList", "content": [{"type": "listItem", "content": [para("无序项")]}]},
            {"type": "orderedList", "content": [{"type": "listItem", "content": [para("有序项")]}]},
            {"type": "blockquote", "content": [para("引用段")]},
            {"type": "horizontalRule"},
            {"type": "pageBreak"},
            para("第二页"),
        ]
        created = self.create_post("全格式", content=blocks)
        self.assert_ok(created, 201)
        self.assertEqual(created.data["warnings"], [])
        post_id = created.data["id"]
        self.assert_ok(self.publish(post_id))
        web = self.api("get", f"/info/posts/{post_id}", token=self.member_token)
        self.assertEqual(web.data["page_count"], 2)
        first = web.data["pages"][0]["html"]
        for expected in ("<h1>一级标题</h1>", "<h4>四级标题</h4>",
                         "font-weight:700;font-style:italic;text-decoration:underline line-through",
                         '<p style="text-align:right">', "color:#ff0000", "background-color:#ffff00",
                         "font-size:20px", "line-height:1.5", 'href="https://example.com"',
                         "<ul><li><p>无序项</p></li></ul>", "<ol><li><p>有序项</p></li></ol>",
                         "<blockquote", "<hr "):
            self.assertIn(expected, first)
        self.assertIn("第二页", web.data["pages"][1]["html"])
        self.assertNotIn("<table", first)

