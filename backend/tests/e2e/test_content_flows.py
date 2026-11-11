"""GROUP_D：内容中心端到端 API 旅程（TC-E2E-301~303）。"""
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
        self.assert_ok(self.api("delete", f"/admin/content/media/{media_id}",
                                token=self.admin_token), 204)

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
