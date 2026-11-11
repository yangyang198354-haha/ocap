"""GROUP_D：内容中心集成测试（TC-INT-301~340）。"""
import io
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.content.ai_jobs import TextJobHandler
from apps.content.drafts import DraftPushHandler
from apps.content.jobs import JobContext
from apps.integrations.draft import DraftOutcome, set_draft_adapter
from apps.integrations.fakes import FakeDraftAdapter, FakeLlmClient
from apps.integrations.llm import set_llm_client
from apps.content.models import ContentJob, DraftPush, MediaItem, PlatformAccount
from tests.support import ApiTestBase

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 128
JPG = b"\xff\xd8\xff" + b"0" * 128
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"0" * 128


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


class ContentTestBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()
        self.member, self.member_token = self.make_user()

    def create_post(self, title="测试公告", content=None, style="builtin:classic"):
        blocks = content if content is not None else [para("正文")]
        return self.api("post", "/admin/content/posts",
                        {"title": title, "doc": doc(*blocks),
                         "style_key": style}, token=self.admin_token)

    def publish(self, post_id):
        return self.api("post", f"/admin/content/posts/{post_id}/publish", {}, token=self.admin_token)

    def upload_media(self, data, name="a.png", title=None):
        upload = SimpleUploadedFile(name, data,
                                    content_type="image/png" if not name.endswith(".mp4")
                                    else "video/mp4")
        return self.upload("/admin/content/media", {"file": upload},
                           data={"title": title} if title else None, token=self.admin_token)


class PostApiTests(ContentTestBase):
    def test_tc_int_301_create_and_list_excludes_doc(self):
        created = self.create_post()
        self.assert_ok(created, 201)
        listing = self.api("get", "/admin/content/posts", token=self.admin_token)
        self.assert_ok(listing)
        self.assertEqual(listing.data["results"][0]["title"], "测试公告")
        self.assertNotIn("doc", listing.data["results"][0])

    def test_tc_int_302_permissions_401_403(self):
        self.assertEqual(self.api("get", "/admin/content/posts").status_code, 401)
        self.assertEqual(self.api("get", "/admin/content/posts", token=self.member_token).status_code, 403)
        self.assertEqual(self.api("get", "/info/posts").status_code, 401)

    def test_tc_int_303_publish_requires_title_and_body(self):
        created = self.create_post(title="", content=[])
        self.assert_ok(created, 201)
        resp = self.publish(created.data["id"])
        self.assert_error(resp, 400, "POST_INCOMPLETE")
        self.assertEqual(resp.data["details"]["missing"], ["title", "body"])

    def test_tc_int_304_publish_offline_and_audit(self):
        created = self.create_post()
        post_id = created.data["id"]
        self.assert_ok(self.publish(post_id))
        detail = self.api("get", f"/admin/content/posts/{post_id}", token=self.admin_token)
        self.assertEqual(detail.data["status"], "PUBLISHED")
        self.assertIsNotNone(detail.data["published_at"])
        self.assert_ok(self.api("post", f"/admin/content/posts/{post_id}/offline", {},
                                token=self.admin_token))
        self.assert_error(self.api("post", f"/admin/content/posts/{post_id}/offline", {},
                                   token=self.admin_token), 409, "POST_STATE_INVALID")
        from apps.core.models import AuditLog
        actions = set(AuditLog.objects.values_list("action", flat=True))
        self.assertTrue({"CONTENT_POST_PUBLISHED", "CONTENT_POST_OFFLINED"} <= actions)

    def test_tc_int_305_update_published_writes_audit(self):
        created = self.create_post()
        post_id = created.data["id"]
        self.publish(post_id)
        resp = self.api("patch", f"/admin/content/posts/{post_id}",
                        {"title": "已修改"}, token=self.admin_token)
        self.assert_ok(resp)
        from apps.core.models import AuditLog
        self.assertTrue(AuditLog.objects.filter(action="CONTENT_POST_UPDATED",
                                                object_id=str(post_id)).exists())

    def test_tc_int_306_confirm_text_and_member_visibility(self):
        created = self.create_post()
        post_id = created.data["id"]
        self.assert_error(self.api("get", f"/info/posts/{post_id}", token=self.member_token),
                          404, "NOT_FOUND")
        confirmed = self.api("post", f"/admin/content/posts/{post_id}/confirm-text", {},
                             token=self.admin_token)
        self.assert_ok(confirmed)
        self.assertTrue(confirmed.data["text_confirmed"])
        self.assert_ok(self.publish(post_id))
        detail = self.api("get", f"/info/posts/{post_id}", token=self.member_token)
        self.assert_ok(detail)
        self.assertEqual(detail.data["page_count"], 1)
        listing = self.api("get", "/info/posts", token=self.member_token)
        self.assertEqual(listing.data["count"], 1)

    def test_tc_int_307_member_list_only_published(self):
        first = self.create_post("已发布").data["id"]
        self.publish(first)
        self.create_post("草稿")
        listing = self.api("get", "/info/posts", token=self.member_token)
        self.assertEqual([row["title"] for row in listing.data["results"]], ["已发布"])

    def test_tc_int_308_delete_and_not_found(self):
        post_id = self.create_post().data["id"]
        self.assert_ok(self.api("delete", f"/admin/content/posts/{post_id}", token=self.admin_token), 204)
        self.assert_error(self.api("get", f"/admin/content/posts/{post_id}", token=self.admin_token),
                          404, "NOT_FOUND")

    def test_tc_int_309_invalid_doc_rejected(self):
        resp = self.api("post", "/admin/content/posts",
                        {"title": "x", "doc": doc(para("x", marks=[
                            {"type": "link", "attrs": {"href": "javascript:alert(1)"}}]))},
                        token=self.admin_token)
        self.assert_error(resp, 400, "CONTENT_INVALID_DOC")
        self.assertEqual(resp.data["details"]["reason"], "LINK")

    def test_tc_int_310_preview_does_not_persist(self):
        before = MediaItem.objects.count()
        resp = self.api("post", "/admin/content/preview",
                        {"doc": doc(para("预览"), {"type": "pageBreak"}, para("第二页"))},
                        token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["page_count"], 2)
        self.assertEqual(MediaItem.objects.count(), before)

    def test_tc_int_311_member_blocks_relative_media_src(self):
        media_id = self.upload_media(PNG, "a.png").data["id"]
        created = self.create_post(content=[
            {"type": "image", "attrs": {"mediaId": media_id}}, para("图")])
        post_id = created.data["id"]
        self.publish(post_id)
        detail = self.api("get", f"/info/posts/{post_id}?fmt=blocks", token=self.member_token)
        self.assert_ok(detail)
        src = detail.data["pages"][0]["blocks"][0]["src"]
        self.assertTrue(src.startswith("/content/media/"))

    def test_tc_int_312_invalid_status_query(self):
        resp = self.api("get", "/admin/content/posts?status=BAD", token=self.admin_token)
        self.assert_error(resp, 400, "INVALID_QUERY")

    # ---- media ----
    def test_tc_int_313_upload_png_and_filter(self):
        resp = self.upload_media(PNG, "a.png", "公告图")
        self.assert_ok(resp, 201)
        self.assertEqual((resp.data["media_type"], resp.data["source"]), ("IMAGE", "UPLOAD"))
        listing = self.api("get", "/admin/content/media?media_type=IMAGE&source=UPLOAD",
                           token=self.admin_token)
        self.assertEqual(len(listing.data["results"]), 1)

    def test_tc_int_314_reject_svg_and_bad_magic(self):
        self.assert_error(self.upload_media(PNG, "a.svg"), 400, "FILE_TYPE_NOT_ALLOWED")
        self.assert_error(self.upload_media(b"not-a-png", "b.png"), 400, "FILE_TYPE_NOT_ALLOWED")

    def test_tc_int_315_upload_video(self):
        resp = self.upload_media(MP4, "a.mp4")
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["media_type"], "VIDEO")

    def test_tc_int_316_rename_save_candidate_delete(self):
        media_id = self.upload_media(PNG).data["id"]
        renamed = self.api("patch", f"/admin/content/media/{media_id}", {"title": "新名称"},
                           token=self.admin_token)
        self.assertEqual(renamed.data["title"], "新名称")
        self.assert_ok(self.api("delete", f"/admin/content/media/{media_id}",
                                token=self.admin_token), 204)

    def test_tc_int_317_published_media_cannot_delete(self):
        media_id = self.upload_media(PNG).data["id"]
        created = self.create_post(content=[{"type": "image", "attrs": {"mediaId": media_id}}])
        self.publish(created.data["id"])
        resp = self.api("delete", f"/admin/content/media/{media_id}", token=self.admin_token)
        self.assert_error(resp, 409, "MEDIA_IN_USE")
        self.assertEqual(resp.data["details"]["posts"][0]["title"], "测试公告")

    def test_tc_int_318_media_signature_required(self):
        media_id = self.upload_media(PNG).data["id"]
        self.assertEqual(self.client_for().get(f"/api/v1/content/media/{media_id}/file").status_code, 403)
        listing = self.api("get", "/admin/content/media", token=self.admin_token)
        signed = listing.data["results"][0]["url"]
        resp = self.client_for().get(signed)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["X-Content-Type-Options"], "nosniff")

    # ---- services / prompts ----
    def test_tc_int_319_service_save_masks_secret_and_test(self):
        fake = FakeLlmClient()
        set_llm_client(fake)
        self.addCleanup(set_llm_client, None)
        resp = self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                        {"params": {"model": "deepseek-chat"},
                         "secrets": {"api_key": "sk-test-123456"}}, token=self.admin_token)
        self.assert_ok(resp)
        self.assertTrue(resp.data["secret_saved"]["api_key"])
        self.assertNotIn("sk-test-123456", str(resp.data))
        tested = self.api("post", "/admin/content/services/LLM_DEEPSEEK/test", {},
                          token=self.admin_token)
        self.assertTrue(tested.data["ok"])
        options = self.api("get", "/admin/content/llm/options", token=self.admin_token)
        self.assertEqual(options.data[0]["service_type"], "LLM_DEEPSEEK")

    def test_tc_int_320_service_missing_fields(self):
        resp = self.api("put", "/admin/content/services/VIDEO_JIMENG",
                        {"params": {}}, token=self.admin_token)
        self.assert_error(resp, 400, "MISSING_FIELDS")

    def test_tc_int_321_test_non_llm_not_allowed(self):
        self.assert_ok(self.api("put", "/admin/content/services/IMAGE_ARK",
                                {"secrets": {"api_key": "sk-image"}}, token=self.admin_token))
        resp = self.api("post", "/admin/content/services/IMAGE_ARK/test", {},
                        token=self.admin_token)
        self.assert_error(resp, 400, "NOT_TESTABLE")

    def test_tc_int_322_prompt_template_crud(self):
        created = self.api("post", "/admin/content/prompt-templates",
                           {"name": "公告模板", "prompt": "写一段公告"}, token=self.admin_token)
        self.assert_ok(created, 201)
        self.assert_error(self.api("post", "/admin/content/prompt-templates",
                                   {"name": "公告模板", "prompt": "x"}, token=self.admin_token),
                          409, "PROMPT_NAME_EXISTS")
        updated = self.api("put", f"/admin/content/prompt-templates/{created.data['id']}",
                           {"prompt": "改写"}, token=self.admin_token)
        self.assertEqual(updated.data["prompt"], "改写")
        self.assert_ok(self.api("delete", f"/admin/content/prompt-templates/{created.data['id']}",
                                token=self.admin_token), 204)

    # ---- settings ----
    def test_tc_int_323_settings_get_and_update(self):
        items = self.api("get", "/admin/content/settings", token=self.admin_token)
        self.assert_ok(items)
        self.assertGreaterEqual(len(items.data), 20)
        updated = self.api("put", "/admin/content/settings",
                           {"values": {"content.page.default_chars": 800}}, token=self.admin_token)
        self.assert_ok(updated)
        self.assertEqual(next(i for i in updated.data if i["key"] == "content.page.default_chars")["value"], 800)

    def test_tc_int_324_settings_invalid_key(self):
        self.assert_error(self.api("put", "/admin/content/settings",
                                   {"values": {"bad.key": 1}}, token=self.admin_token),
                          400, "INVALID_VALUE")


class AiAndDraftTests(ContentTestBase):
    def test_tc_int_325_ai_text_job_success(self):
        fake = FakeLlmClient()
        fake.responses = ["生成的第一段\n\n生成的第二段"]
        set_llm_client(fake)
        self.addCleanup(set_llm_client, None)
        self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                 {"secrets": {"api_key": "sk-test"}}, token=self.admin_token)
        self.api("post", "/admin/content/services/LLM_DEEPSEEK/test", {}, token=self.admin_token)
        resp = self.api("post", "/admin/content/ai/text", {"prompt": "写公告"}, token=self.admin_token)
        self.assert_ok(resp, 202)
        job = self.api("get", f"/admin/content/jobs/{resp.data['id']}", token=self.admin_token)
        self.assertEqual(job.data["status"], "QUEUED")
        from apps.content.models import ContentJob
        row = ContentJob.objects.get(id=resp.data["id"])
        result = TextJobHandler().run(JobContext(row, timezone.now()))
        self.assertIn("生成的第二段", result.result["text"])

    def test_tc_int_326_ai_text_requires_prompt_and_config(self):
        self.assert_error(self.api("post", "/admin/content/ai/text", {"prompt": " "},
                                   token=self.admin_token), 400, "PROMPT_EMPTY")
        self.assert_error(self.api("post", "/admin/content/ai/text", {"prompt": "写"},
                                   token=self.admin_token), 409, "LLM_NOT_CONFIGURED")

    def test_tc_int_327_platform_account_crud_and_mask(self):
        created = self.api("post", "/admin/content/platform-accounts",
                           {"platform": "wechat_mp", "display_name": "小区公众号",
                            "credentials": {"access_token": "tok-123456"}},
                           token=self.admin_token)
        self.assert_ok(created, 201)
        self.assertEqual(created.data["auth_status"], "NORMAL")
        self.assertNotIn("tok-123456", str(created.data))
        self.assert_error(self.api("post", "/admin/content/platform-accounts",
                                   {"platform": "wechat_mp", "display_name": "第二个"},
                                   token=self.admin_token), 409, "PLATFORM_ACCOUNT_EXISTS")
        account_id = created.data["id"]
        updated = self.api("patch", f"/admin/content/platform-accounts/{account_id}",
                           {"display_name": "新名称"}, token=self.admin_token)
        self.assertEqual(updated.data["display_name"], "新名称")
        listing = self.api("get", "/admin/content/platform-accounts", token=self.admin_token)
        self.assertEqual(len(listing.data), 3)

    def test_tc_int_328_manual_platform_and_no_credentials(self):
        self.api("post", "/admin/content/platform-accounts",
                 {"platform": "xiaohongshu", "display_name": "小红书"},
                 token=self.admin_token)
        self.api("post", "/admin/content/platform-accounts",
                 {"platform": "toutiao", "display_name": "头条"},
                 token=self.admin_token)
        post_id = self.create_post().data["id"]
        self.publish(post_id)
        accounts = self.api("get", "/admin/content/platform-accounts", token=self.admin_token).data
        manual = next(a for a in accounts if a["platform"] == "xiaohongshu")
        resp = self.api("post", f"/admin/content/posts/{post_id}/drafts",
                        {"account_ids": [manual["account"]["id"]]}, token=self.admin_token)
        self.assert_ok(resp, 202)
        self.assertEqual(resp.data["pushes"][0]["status"], "MANUAL_REQUIRED")
        self.assertIn("style_not_carried", resp.data["pushes"][0]["unsupported"])

        wechat = self.api("post", "/admin/content/platform-accounts",
                          {"platform": "wechat_mp", "display_name": "公众号"},
                          token=self.admin_token)
        resp2 = self.api("post", f"/admin/content/posts/{post_id}/drafts",
                         {"account_ids": [wechat.data["id"]]}, token=self.admin_token)
        self.assertEqual(resp2.data["pushes"][0]["status"], "FAILED")
        self.assertEqual(resp2.data["pushes"][0]["error_code"], "NO_CREDENTIALS")

    def test_tc_int_329_draft_push_success_and_auth_expired(self):
        from apps.integrations.draft import get_draft_adapter
        original = get_draft_adapter("wechat_mp")
        fake = FakeDraftAdapter("wechat_mp", outcomes=[DraftOutcome("SAVED", remote_ref="ref-1")])
        set_draft_adapter("wechat_mp", fake)
        self.addCleanup(set_draft_adapter, "wechat_mp", original)
        account = self.api("post", "/admin/content/platform-accounts",
                           {"platform": "wechat_mp", "display_name": "公众号",
                            "credentials": {"access_token": "tok-abcdef"}},
                           token=self.admin_token).data
        post_id = self.create_post().data["id"]
        self.publish(post_id)
        batch = self.api("post", f"/admin/content/posts/{post_id}/drafts",
                         {"account_ids": [account["id"]]}, token=self.admin_token)
        self.assert_ok(batch, 202)
        job = self.api("get", f"/admin/content/jobs/{batch.data['job_id']}", token=self.admin_token)
        from apps.content.models import ContentJob
        row = ContentJob.objects.get(id=batch.data["job_id"])
        DraftPushHandler().run(JobContext(row, timezone.now()))
        push = DraftPush.objects.get(id=batch.data["pushes"][0]["id"])
        self.assertEqual((push.status, push.remote_ref), ("SAVED", "ref-1"))

        fake2 = FakeDraftAdapter("wechat_mp", outcomes=[DraftOutcome("AUTH_EXPIRED")])
        set_draft_adapter("wechat_mp", fake2)
        post2 = self.create_post("第二条").data["id"]
        self.publish(post2)
        batch2 = self.api("post", f"/admin/content/posts/{post2}/drafts",
                          {"account_ids": [account["id"]]}, token=self.admin_token)
        DraftPushHandler().run(JobContext(ContentJob.objects.get(id=batch2.data["job_id"]),
                                          timezone.now()))
        self.assertEqual(DraftPush.objects.get(id=batch2.data["pushes"][0]["id"]).status, "FAILED")
        self.assertEqual(PlatformAccount.objects.get(id=account["id"]).auth_status, "EXPIRED")

    def test_tc_int_330_draft_requires_confirmed_and_selection(self):
        post_id = self.create_post().data["id"]
        self.assert_error(self.api("post", f"/admin/content/posts/{post_id}/drafts",
                                   {"account_ids": []}, token=self.admin_token),
                          400, "NO_PLATFORM_SELECTED")
        account = self.api("post", "/admin/content/platform-accounts",
                           {"platform": "wechat_mp", "display_name": "公众号",
                            "credentials": {"access_token": "tok"}},
                           token=self.admin_token).data
        resp = self.api("post", f"/admin/content/posts/{post_id}/drafts",
                        {"account_ids": [account["id"]]}, token=self.admin_token)
        self.assert_error(resp, 409, "POST_NOT_CONFIRMED")

    def test_tc_int_331_export_pack_contains_text_and_html(self):
        post_id = self.create_post().data["id"]
        self.publish(post_id)
        resp = self.client_for(self.admin_token).get(
            f"/api/v1/admin/content/posts/{post_id}/export-pack?platform=xiaohongshu")
        self.assertEqual(resp.status_code, 200)
        payload = b"".join(resp.streaming_content)
        archive = zipfile.ZipFile(io.BytesIO(payload))
        self.assertEqual(set(archive.namelist()) >= {"content.txt", "content.html", "README.txt"}, True)
        self.assertIn("正文", archive.read("content.txt").decode("utf-8"))

    def test_tc_int_332_copy_payload(self):
        post_id = self.create_post().data["id"]
        self.publish(post_id)
        resp = self.api("get", f"/admin/content/posts/{post_id}/copy?platform=toutiao",
                        token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["text"], "正文")
        self.assertIn("style_not_carried", resp.data["unsupported"])

    def test_tc_int_333_ai_video_requires_confirmation_and_config(self):
        post_id = self.create_post().data["id"]
        self.assert_error(self.api("post", "/admin/content/ai/video", {"post_id": post_id},
                                   token=self.admin_token), 409, "VIDEO_NOT_CONFIGURED")
        self.api("put", "/admin/content/services/VIDEO_JIMENG",
                 {"secrets": {"access_key": "ak", "secret_key": "sk"}},
                 token=self.admin_token)
        self.assert_error(self.api("post", "/admin/content/ai/video", {"post_id": post_id},
                                   token=self.admin_token), 409, "TEXT_NOT_CONFIRMED")
        self.api("post", f"/admin/content/posts/{post_id}/confirm-text", {},
                 token=self.admin_token)
        resp = self.api("post", "/admin/content/ai/video", {"post_id": post_id},
                        token=self.admin_token)
        self.assert_ok(resp, 202)
        from apps.content.models import ContentJob
        job = ContentJob.objects.get(id=resp.data["id"])
        self.assertEqual(job.kind, "VIDEO_GEN")
        self.assertTrue(job.payload["scenes"])

    def test_tc_int_334_job_list_filters(self):
        fake = FakeLlmClient()
        set_llm_client(fake)
        self.addCleanup(set_llm_client, None)
        self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                 {"secrets": {"api_key": "sk"}}, token=self.admin_token)
        self.api("post", "/admin/content/services/LLM_DEEPSEEK/test", {}, token=self.admin_token)
        self.api("post", "/admin/content/ai/text", {"prompt": "写"}, token=self.admin_token)
        listing = self.api("get", "/admin/content/jobs?kind=LLM_TEXT", token=self.admin_token)
        self.assertEqual(listing.data["count"], 1)
        self.assert_error(self.api("get", "/admin/content/jobs?kind=BAD", token=self.admin_token),
                          400, "INVALID_QUERY")

    def test_tc_int_335_draft_history_pagination(self):
        post_id = self.create_post().data["id"]
        self.publish(post_id)
        listing = self.api("get", f"/admin/content/posts/{post_id}/drafts/history",
                           token=self.admin_token)
        self.assert_ok(listing)
        self.assertEqual(listing.data["count"], 0)


class BranchCoverageTests(ContentTestBase):
    def test_tc_int_336_media_too_large(self):
        from apps.content.conf import ContentSettings
        ContentSettings.update({"content.media.image_max_bytes": 1048576}, admin_id=1)
        resp = self.upload_media(PNG + b"0" * (1048576 + 1), "big.png")
        self.assert_error(resp, 413, "FILE_TOO_LARGE")

    def test_tc_int_337_media_quota_exceeded(self):
        from apps.content.conf import ContentSettings
        from apps.content.models import MediaItem
        ContentSettings.update({"content.media.total_quota_bytes": 67108864}, admin_id=1)
        MediaItem.objects.create(media_type="IMAGE", source="UPLOAD", state="SAVED",
                                 title="占位", original_name="a.png", content_type="image/png",
                                 size=67108864 - 1, sha256="x", storage_path="content/a.png",
                                 created_by_admin_id=self.admin.id)
        resp = self.upload_media(PNG, "b.png")
        self.assert_error(resp, 413, "MEDIA_QUOTA_EXCEEDED")

    def test_tc_int_338_ai_rate_limited(self):
        from apps.content.conf import ContentSettings
        from apps.integrations.fakes import FakeLlmClient
        from apps.integrations.llm import set_llm_client
        ContentSettings.update({"content.ai.rate_limit_per_hour": 1}, admin_id=1)
        fake = FakeLlmClient()
        set_llm_client(fake)
        self.addCleanup(set_llm_client, None)
        self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                 {"secrets": {"api_key": "sk"}}, token=self.admin_token)
        self.api("post", "/admin/content/services/LLM_DEEPSEEK/test", {}, token=self.admin_token)
        first = self.api("post", "/admin/content/ai/text", {"prompt": "一"}, token=self.admin_token)
        self.assert_ok(first, 202)
        second = self.api("post", "/admin/content/ai/text", {"prompt": "二"}, token=self.admin_token)
        self.assert_error(second, 429, "CODE_RATE_LIMITED")

    def test_tc_int_339_media_range_and_invalid(self):
        media_id = self.upload_media(PNG, "range.png").data["id"]
        signed = self.api("get", "/admin/content/media", token=self.admin_token).data["results"][0]["url"]
        partial = self.client_for().get(signed, HTTP_RANGE="bytes=0-3")
        self.assertEqual(partial.status_code, 206)
        self.assertTrue(partial["Content-Range"].startswith("bytes 0-3/"))
        invalid = self.client_for().get(signed, HTTP_RANGE="bytes=99999-100000")
        self.assertEqual(invalid.status_code, 416)

    def test_tc_int_340_style_template_update_delete_api(self):
        created = self.api("post", "/admin/content/style-templates",
                           {"name": "接口模板", "tokens": {"font_size": 18}},
                           token=self.admin_token)
        self.assert_ok(created, 201)
        template_id = int(created.data["key"].split(":")[1])
        updated = self.api("put", f"/admin/content/style-templates/{template_id}",
                           {"name": "接口模板2", "tokens": {"font_size": 20}},
                           token=self.admin_token)
        self.assertEqual(updated.data["name"], "接口模板2")
        self.assertEqual(updated.data["tokens"]["font_size"], 20)
        self.assert_ok(self.api("delete", f"/admin/content/style-templates/{template_id}",
                                token=self.admin_token), 204)
        keys = [item["key"] for item in self.api("get", "/admin/content/style-templates",
                                                token=self.admin_token).data]
        self.assertNotIn(created.data["key"], keys)

    def test_tc_int_341_platform_account_delete(self):
        created = self.api("post", "/admin/content/platform-accounts",
                           {"platform": "wechat_mp", "display_name": "公众号",
                            "credentials": {"access_token": "tok"}},
                           token=self.admin_token)
        self.assert_ok(created, 201)
        self.assert_ok(self.api("delete", f"/admin/content/platform-accounts/{created.data['id']}",
                                token=self.admin_token), 204)
        listing = self.api("get", "/admin/content/platform-accounts", token=self.admin_token).data
        wechat = next(item for item in listing if item["platform"] == "wechat_mp")
        self.assertIsNone(wechat["account"])
        again = self.api("post", "/admin/content/platform-accounts",
                         {"platform": "wechat_mp", "display_name": "新公众号"},
                         token=self.admin_token)
        self.assert_ok(again, 201)

    def test_tc_int_342_draft_retry(self):
        post_id = self.create_post().data["id"]
        self.publish(post_id)
        account = self.api("post", "/admin/content/platform-accounts",
                           {"platform": "wechat_mp", "display_name": "公众号"},
                           token=self.admin_token).data
        batch = self.api("post", f"/admin/content/posts/{post_id}/drafts",
                         {"account_ids": [account["id"]]}, token=self.admin_token)
        self.assertEqual(batch.data["pushes"][0]["status"], "FAILED")
        retry = self.api("post", f"/admin/content/drafts/{batch.data['pushes'][0]['id']}/retry",
                         {}, token=self.admin_token)
        self.assert_ok(retry, 202)
        self.assertEqual(retry.data["push"]["status"], "PENDING")
        again = self.api("post", f"/admin/content/drafts/{retry.data['push']['id']}/retry",
                         {}, token=self.admin_token)
        self.assert_error(again, 409, "DRAFT_PUSH_STATE_INVALID")

    def test_tc_int_343_draft_interrupted_marks_unknown(self):
        from apps.content.models import DraftPush
        from apps.content.drafts import DraftPushHandler
        post_id = self.create_post().data["id"]
        job = ContentJob.objects.create(kind="DRAFT_PUSH", payload={}, status="RUNNING",
                                        next_run_at=timezone.now(),
                                        created_by_admin_id=self.admin.id)
        sending = DraftPush.objects.create(post_id=post_id, platform="wechat_mp", mode="AUTO",
                                           status="SENDING", job=job,
                                           created_by_admin_id=self.admin.id)
        pending = DraftPush.objects.create(post_id=post_id, platform="wechat_mp", mode="AUTO",
                                           status="PENDING", job=job,
                                           created_by_admin_id=self.admin.id)
        DraftPushHandler().on_interrupted(job)
        sending.refresh_from_db()
        pending.refresh_from_db()
        self.assertEqual(sending.status, "UNKNOWN")
        self.assertEqual(pending.status, "FAILED")
        self.assertEqual(pending.error_code, "INTERRUPTED")

    def test_tc_int_344_candidate_ttl_housekeeping(self):
        from datetime import timedelta
        from apps.content.media import MediaService
        from apps.content.models import ContentPost, ContentPostMedia, MediaItem
        old = timezone.now() - timedelta(hours=48)
        row = MediaItem.objects.create(media_type="IMAGE", source="AI_GENERATED",
                                       state="CANDIDATE", title="旧候选", original_name="a.png",
                                       content_type="image/png", size=1, sha256="x",
                                       storage_path="content/missing.png",
                                       created_by_admin_id=self.admin.id)
        MediaItem.objects.filter(id=row.id).update(created_at=old)
        referenced = MediaItem.objects.create(media_type="IMAGE", source="AI_GENERATED",
                                              state="CANDIDATE", title="被引用", original_name="b.png",
                                              content_type="image/png", size=1, sha256="x",
                                              storage_path="content/missing2.png",
                                              created_by_admin_id=self.admin.id)
        MediaItem.objects.filter(id=referenced.id).update(created_at=old)
        post = ContentPost.objects.create(title="引用", doc={"type": "doc", "content": []},
                                          created_by_admin_id=self.admin.id)
        ContentPostMedia.objects.create(post=post, media=referenced)
        deleted = MediaService.housekeeping(timezone.now())
        self.assertGreaterEqual(deleted, 1)
        self.assertFalse(MediaItem.objects.filter(id=row.id).exists())
        self.assertTrue(MediaItem.objects.filter(id=referenced.id).exists())

    def test_tc_int_345_video_failure_branch(self):
        from apps.content.ai_jobs import VideoJobHandler
        from apps.integrations.fakes import FakeVideoGenClient
        from apps.integrations.videogen import set_videogen_client
        client = FakeVideoGenClient()
        set_videogen_client(client)
        self.addCleanup(set_videogen_client, None)
        self.api("put", "/admin/content/services/VIDEO_JIMENG",
                 {"secrets": {"access_key": "ak", "secret_key": "sk"}},
                 token=self.admin_token)
        post_id = self.create_post().data["id"]
        self.api("post", f"/admin/content/posts/{post_id}/confirm-text", {},
                 token=self.admin_token)
        resp = self.api("post", "/admin/content/ai/video", {"post_id": post_id},
                        token=self.admin_token)
        job = ContentJob.objects.get(id=resp.data["id"])
        first = VideoJobHandler().run(JobContext(job, timezone.now()))
        self.assertEqual(first.__class__.__name__, "Wait")
        job.refresh_from_db()
        from apps.integrations.videogen import VideoTaskStatus
        client.statuses = [VideoTaskStatus(task_id="fake-task", status="failed",
                                           progress=10, clip_urls=(), error="远端失败")]
        outcome = VideoJobHandler().run(JobContext(job, timezone.now()))
        self.assertEqual(outcome.code, "REMOTE_FAILED")
