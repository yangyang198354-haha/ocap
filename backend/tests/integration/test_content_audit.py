"""GROUP_D（回流 1）：内容中心审计断言（TC-INT-346~362）。

对应 GR-C-002 / GR-C-003 条件 2：逐 AC 断言"恰好新增 1 条审计，含操作人、对象、时间、结果"，
并断言凭据原文在审计、接口响应、日志中出现 0 次（AC-117-02、AC-125-02、AC-127-02）。
依据：module_design 1.1.0 审计落点表。
"""
import io
import os
import zipfile
from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone

from apps.content.ai_jobs import VideoJobHandler
from apps.content.drafts import DraftPushHandler, DraftPushService
from apps.content.jobs import JobContext
from apps.content.media import set_remote_fetcher
from apps.content.models import ContentJob, DraftPush, MediaItem
from apps.core.audit import AuditActor
from apps.integrations.fakes import (
    FakeLlmClient, FakeRemoteFetcher, FakeVideoGenClient, FakeWechatMpApi,
)
from apps.integrations.llm import set_llm_client
from apps.integrations.videogen import VideoTaskStatus, set_videogen_client
from apps.integrations.wechat_mp import WechatMpApiError, set_wechat_mp_api
from tests.content_support import ContentRoundBase, audit_dump, capture_logs
from tests.integration.test_content_api import MP4, PNG

SECRET_LLM = "sk-LLM-SECRET-117-ABCDEF"
SECRET_VIDEO_AK = "AK-VIDEO-SECRET-125-001"
SECRET_VIDEO_SK = "SK-VIDEO-SECRET-125-002"
APPID = "wxaudit0001"
APPSECRET = "APPSECRET-127-VERYSECRET"


class PostAuditTests(ContentRoundBase):
    def test_tc_int_346_publish_writes_one_audit_and_incomplete_writes_none(self):
        """AC-105-02：发布 → 状态已发布，审计恰新增 1 条（操作人/对象/时间/结果）；AC-105-03 被拒不写。"""
        empty = self.create_post(title="", content=[]).data["id"]
        before = self.audit_count("CONTENT_POST_PUBLISHED")
        self.assert_error(self.publish(empty), 400, "POST_INCOMPLETE")
        self.assertEqual(self.audit_count("CONTENT_POST_PUBLISHED"), before)
        self.assertEqual(self.api("get", f"/admin/content/posts/{empty}",
                                  token=self.admin_token).data["status"], "DRAFT")

        post_id = self.create_post("公告").data["id"]
        self.assert_ok(self.publish(post_id))
        row = self.assert_new_audit("CONTENT_POST_PUBLISHED", before, object_type="content_post",
                                    object_id=post_id)
        self.assertEqual(row.detail, {"title": "公告"})

    def test_tc_int_347_update_published_writes_one_audit_draft_writes_none(self):
        """AC-106-01：已发布内容修改正文 → 门户展示新正文，审计新增 1 条"修改"。"""
        post_id = self.create_post("公告").data["id"]
        before = self.audit_count("CONTENT_POST_UPDATED")
        self.assert_ok(self.api("patch", f"/admin/content/posts/{post_id}",
                                {"title": "草稿阶段改名"}, token=self.admin_token))
        self.assertEqual(self.audit_count("CONTENT_POST_UPDATED"), before)   # 草稿阶段不写
        self.assert_ok(self.publish(post_id))
        new_doc = {"type": "doc", "content": [{"type": "paragraph", "content": [
            {"type": "text", "text": "修改后的正文"}]}]}
        self.assert_ok(self.api("patch", f"/admin/content/posts/{post_id}", {"doc": new_doc},
                                token=self.admin_token))
        self.assert_new_audit("CONTENT_POST_UPDATED", before, object_type="content_post",
                              object_id=post_id)
        self.assert_ok(self.publish(post_id))
        shown = self.api("get", f"/info/posts/{post_id}", token=self.member_token)
        self.assertIn("修改后的正文", shown.data["pages"][0]["html"])
        self.assertNotIn(">正文<", shown.data["pages"][0]["html"])

    def test_tc_int_348_offline_writes_one_audit_and_hides_from_members(self):
        """AC-106-02。"""
        post_id = self.create_post("公告").data["id"]
        self.publish(post_id)
        before = self.audit_count("CONTENT_POST_OFFLINED")
        self.assert_ok(self.api("post", f"/admin/content/posts/{post_id}/offline", {},
                                token=self.admin_token))
        self.assert_new_audit("CONTENT_POST_OFFLINED", before, object_type="content_post",
                              object_id=post_id)
        self.assert_error(self.api("post", f"/admin/content/posts/{post_id}/offline", {},
                                   token=self.admin_token), 409, "POST_STATE_INVALID")
        self.assertEqual(self.audit_count("CONTENT_POST_OFFLINED"), before + 1)
        self.assertEqual(self.api("get", "/info/posts", token=self.member_token).data["count"], 0)
        self.assert_error(self.api("get", f"/info/posts/{post_id}", token=self.member_token),
                          404, "NOT_FOUND")

    def test_tc_int_349_delete_writes_one_audit_missing_writes_none(self):
        """AC-106-04（AC-106-03 的取消路径属前端，见 vitest）。"""
        post_id = self.create_post("待删除").data["id"]
        self.publish(post_id)
        before = self.audit_count("CONTENT_POST_DELETED")
        self.assert_error(self.api("delete", "/admin/content/posts/987654", token=self.admin_token),
                          404, "NOT_FOUND")
        self.assertEqual(self.audit_count("CONTENT_POST_DELETED"), before)
        self.assert_ok(self.api("delete", f"/admin/content/posts/{post_id}", token=self.admin_token), 204)
        row = self.assert_new_audit("CONTENT_POST_DELETED", before, object_type="content_post",
                                    object_id=post_id)
        self.assertEqual(row.detail, {"title": "待删除"})
        listing = self.api("get", "/admin/content/posts", token=self.admin_token)
        self.assertEqual(listing.data["count"], 0)
        self.assert_error(self.api("get", f"/info/posts/{post_id}", token=self.member_token),
                          404, "NOT_FOUND")


class ServiceAuditTests(ContentRoundBase):
    def test_tc_int_350_service_config_audit_and_no_secret_leak(self):
        """AC-117-04 / AC-117-02：保存配置新增 1 条；凭据原文在审计、响应、日志中出现 0 次。"""
        before = self.audit_count("CONTENT_SERVICE_CONFIG_CHANGED")
        with capture_logs() as logs:
            saved = self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                             {"params": {"model": "deepseek-chat"},
                              "secrets": {"api_key": SECRET_LLM}}, token=self.admin_token)
            self.assert_ok(saved)
            row = self.assert_new_audit("CONTENT_SERVICE_CONFIG_CHANGED", before,
                                        object_type="content_service", object_id="LLM_DEEPSEEK")
            self.assertEqual(row.detail, {"changed_fields": ["api_key", "model"]})
            # 只改模型：再新增 1 条
            self.assert_ok(self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                                    {"params": {"model": "deepseek-reasoner"}}, token=self.admin_token))
            self.assertEqual(self.audit_count("CONTENT_SERVICE_CONFIG_CHANGED"), before + 2)
            listing = self.api("get", "/admin/content/services", token=self.admin_token)
            options = self.api("get", "/admin/content/llm/options", token=self.admin_token)
            self.assert_ok(listing)
        self.assertTrue(saved.data["secret_saved"]["api_key"])
        for name, text in (("save response", saved.content.decode()),
                           ("list response", listing.content.decode()),
                           ("options response", options.content.decode()),
                           ("audit", audit_dump()), ("logs", "\n".join(logs))):
            self.assertNotIn(SECRET_LLM, text, name)
            self.assertNotIn("SECRET-117", text, name)

    def test_tc_int_351_service_test_audit_success_and_failure(self):
        """AC-118-04 / AC-118-01~03：连通测试各新增 1 条；失败的配置不进可选列表。"""
        fake = FakeLlmClient()
        set_llm_client(fake)
        self.addCleanup(set_llm_client, None)
        self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                 {"secrets": {"api_key": "sk-t"}}, token=self.admin_token)
        # 从未测试 → 不可选（AC-118-03）
        self.assertEqual(self.api("get", "/admin/content/llm/options", token=self.admin_token).data, [])
        before = self.audit_count("CONTENT_SERVICE_TESTED")
        ok = self.api("post", "/admin/content/services/LLM_DEEPSEEK/test", {}, token=self.admin_token)
        self.assertTrue(ok.data["ok"])
        row = self.assert_new_audit("CONTENT_SERVICE_TESTED", before, object_type="content_service",
                                    object_id="LLM_DEEPSEEK")
        self.assertEqual(row.detail, {"error_code": ""})
        self.assertEqual(len(self.api("get", "/admin/content/llm/options", token=self.admin_token).data), 1)

        fake.fail_code = "UPSTREAM"
        bad = self.api("post", "/admin/content/services/LLM_DEEPSEEK/test", {}, token=self.admin_token)
        self.assertFalse(bad.data["ok"])
        self.assertEqual(bad.data["error_code"], "UPSTREAM")
        row = self.assert_new_audit("CONTENT_SERVICE_TESTED", before + 1,
                                    object_type="content_service", object_id="LLM_DEEPSEEK",
                                    result="FAILURE")
        self.assertEqual(row.detail, {"error_code": "UPSTREAM"})
        self.assertEqual(self.api("get", "/admin/content/llm/options", token=self.admin_token).data, [])

    def test_tc_int_352_video_service_credentials_not_echoed(self):
        """AC-125-02 / AC-125-03：视频服务账号不回显，审计 / 响应 / 日志 0 次；必填缺失不改动已有配置。"""
        with capture_logs() as logs:
            saved = self.api("put", "/admin/content/services/VIDEO_JIMENG",
                             {"secrets": {"access_key": SECRET_VIDEO_AK, "secret_key": SECRET_VIDEO_SK}},
                             token=self.admin_token)
            self.assert_ok(saved)
            again = self.api("get", "/admin/content/services", token=self.admin_token)
            # 另一位管理员看到同一份配置（AC-125-01）
            other_admin, other_token = self.make_admin()
            seen = self.api("get", "/admin/content/services", token=other_token)
            missing = self.api("put", "/admin/content/services/VIDEO_JIMENG",
                               {"secrets": {"access_key": ""}}, token=self.admin_token)
        self.assertEqual(saved.data["secret_saved"], {"access_key": True, "secret_key": True})
        video = next(item for item in seen.data if item["service_type"] == "VIDEO_JIMENG")
        self.assertTrue(video["configured"])
        self.assertEqual(missing.status_code, 400)
        still = next(item for item in self.api("get", "/admin/content/services",
                                               token=self.admin_token).data
                     if item["service_type"] == "VIDEO_JIMENG")
        self.assertTrue(still["configured"])
        for name, text in (("save", saved.content.decode()), ("list", again.content.decode()),
                           ("other admin list", seen.content.decode()), ("audit", audit_dump()),
                           ("logs", "\n".join(logs))):
            self.assertNotIn(SECRET_VIDEO_AK, text, name)
            self.assertNotIn(SECRET_VIDEO_SK, text, name)


class MediaAuditTests(ContentRoundBase):
    def test_tc_int_353_media_delete_writes_one_audit_and_removes_file(self):
        """AC-122-03：删除未被引用素材 → 素材消失、文件被删、审计新增 1 条；被引用拒绝时不写。"""
        used = self.upload_media(PNG, "used.png", "在用").data["id"]
        free = self.upload_media(PNG, "free.png", "闲置").data["id"]
        post_id = self.create_post(content=[{"type": "image", "attrs": {"mediaId": used}}]).data["id"]
        self.publish(post_id)
        before = self.audit_count("CONTENT_MEDIA_DELETED")
        refused = self.api("delete", f"/admin/content/media/{used}", token=self.admin_token)
        self.assert_error(refused, 409, "MEDIA_IN_USE")
        self.assertEqual(self.audit_count("CONTENT_MEDIA_DELETED"), before)
        self.assertTrue(MediaItem.objects.filter(id=used).exists())

        path = os.path.join(self.media_root, MediaItem.objects.get(id=free).storage_path)
        self.assertTrue(os.path.exists(path))
        with self.captureOnCommitCallbacks(execute=True):
            self.assert_ok(self.api("delete", f"/admin/content/media/{free}", token=self.admin_token), 204)
        row = self.assert_new_audit("CONTENT_MEDIA_DELETED", before, object_type="content_media",
                                    object_id=free)
        self.assertEqual(row.detail, {"title": "闲置", "media_type": "IMAGE", "source": "UPLOAD",
                                      "size": len(PNG)})
        self.assertFalse(os.path.exists(path))
        self.assertFalse(MediaItem.objects.filter(id=free).exists())
        titles = [item["title"] for item in
                  self.api("get", "/admin/content/media", token=self.admin_token).data["results"]]
        self.assertEqual(titles, ["在用"])

    def test_tc_int_354_media_delete_rolled_back_keeps_file(self):
        """删除事务回滚（如审计写入失败）时，文件保持不动、素材行仍在（on_commit 语义）。"""
        media_id = self.upload_media(PNG, "keep.png").data["id"]
        path = os.path.join(self.media_root, MediaItem.objects.get(id=media_id).storage_path)
        with patch("apps.content.media.AuditService.record", side_effect=RuntimeError("audit down")):
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                from rest_framework.test import APIClient
                client = APIClient(raise_request_exception=False)
                client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
                response = client.delete(f"/api/v1/admin/content/media/{media_id}")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(callbacks, [])
        self.assertTrue(os.path.exists(path))
        self.assertTrue(MediaItem.objects.filter(id=media_id).exists())
        self.assertEqual(self.audit_count("CONTENT_MEDIA_DELETED"), 0)


class VideoAuditTests(ContentRoundBase):
    def _setup_video(self, post_title="视频内容"):
        client = FakeVideoGenClient()
        fetcher = FakeRemoteFetcher()
        set_videogen_client(client)
        set_remote_fetcher(fetcher)
        self.addCleanup(set_videogen_client, None)
        self.addCleanup(set_remote_fetcher, None)
        self.api("put", "/admin/content/services/VIDEO_JIMENG",
                 {"secrets": {"access_key": "ak", "secret_key": "sk"}}, token=self.admin_token)
        post_id = self.create_post(post_title).data["id"]
        return client, fetcher, post_id

    def test_tc_int_355_video_request_and_completion_audit(self):
        """AC-124-06：发起视频生成新增 1 条（请求）；完成时补记 1 条；拒绝（未确认文案）不记成功。"""
        client, fetcher, post_id = self._setup_video()
        before = self.audit_count("CONTENT_VIDEO_REQUESTED")
        denied = self.api("post", "/admin/content/ai/video", {"post_id": post_id}, token=self.admin_token)
        self.assert_error(denied, 409, "TEXT_NOT_CONFIRMED")
        self.assertEqual(AuditLogCount("CONTENT_VIDEO_REQUESTED", "SUCCESS"), 0)

        self.api("post", f"/admin/content/posts/{post_id}/confirm-text", {}, token=self.admin_token)
        mark = self.audit_count("CONTENT_VIDEO_REQUESTED")
        resp = self.api("post", "/admin/content/ai/video", {"post_id": post_id}, token=self.admin_token)
        self.assert_ok(resp, 202)
        self.assertEqual(resp.data["status"], "QUEUED")
        row = self.assert_new_audit("CONTENT_VIDEO_REQUESTED", mark, object_type="content_post",
                                    object_id=post_id)
        self.assertEqual(row.detail, {"job_id": resp.data["id"], "scenes": 1})
        self.assertEqual(self.audit_count("CONTENT_VIDEO_COMPLETED"), 0)

        fetcher.payloads = {"https://example.com/clip.mp4": MP4}
        job = ContentJob.objects.get(id=resp.data["id"])
        self.assertEqual(VideoJobHandler().run(JobContext(job, timezone.now())).__class__.__name__, "Wait")
        job.refresh_from_db()
        outcome = VideoJobHandler().run(JobContext(job, timezone.now()))
        self.assertEqual(len(outcome.result["media"]), 1)
        done = self.assert_new_audit("CONTENT_VIDEO_COMPLETED", 0, object_type="content_job",
                                     object_id=job.id)
        self.assertEqual(done.detail, {"media": 1, "post_id": post_id})


def AuditLogCount(action, result):
    from apps.core.models import AuditLog
    return AuditLog.objects.filter(action=action, result=result).count()


class PlatformAuditTests(ContentRoundBase):
    def test_tc_int_356_account_create_rename_delete_each_one_audit(self):
        """AC-126-01 / AC-126-03：增、改名、删各新增 1 条，detail.action 区分。"""
        name = "CONTENT_PLATFORM_ACCOUNT_CHANGED"
        before = self.audit_count(name)
        created = self.api("post", "/admin/content/platform-accounts",
                           {"platform": "xiaohongshu", "display_name": "小红书号"}, token=self.admin_token)
        self.assert_ok(created, 201)
        account_id = created.data["id"]
        row = self.assert_new_audit(name, before, object_type="platform_account", object_id=account_id)
        self.assertEqual(row.detail, {"platform": "xiaohongshu", "action": "create"})

        self.assert_ok(self.api("patch", f"/admin/content/platform-accounts/{account_id}",
                                {"display_name": "新名"}, token=self.admin_token))
        row = self.assert_new_audit(name, before + 1, object_type="platform_account", object_id=account_id)
        self.assertEqual(row.detail, {"platform": "xiaohongshu", "action": "rename"})

        # 重复添加被拒绝（AC-126-02），不写审计
        self.assert_error(self.api("post", "/admin/content/platform-accounts",
                                   {"platform": "xiaohongshu", "display_name": "第二个"},
                                   token=self.admin_token), 409, "PLATFORM_ACCOUNT_EXISTS")
        self.assertEqual(self.audit_count(name), before + 2)

        self.assert_ok(self.api("delete", f"/admin/content/platform-accounts/{account_id}",
                                token=self.admin_token), 204)
        row = self.assert_new_audit(name, before + 2, object_type="platform_account", object_id=account_id)
        self.assertEqual(row.detail, {"platform": "xiaohongshu", "action": "delete"})
        listing = self.api("get", "/admin/content/platform-accounts", token=self.admin_token).data
        self.assertEqual([item["platform"] for item in listing], ["wechat_mp", "xiaohongshu", "toutiao"])
        self.assertTrue(all(item["account"] is None for item in listing if item["platform"] == "xiaohongshu"))

    def test_tc_int_357_credentials_update_audit_and_no_secret_leak(self):
        """AC-127-01 / AC-127-02：认证信息更新新增 1 条且不含原文；响应 / 日志 / 审计 0 次。"""
        name = "CONTENT_PLATFORM_ACCOUNT_CHANGED"
        with capture_logs() as logs:
            created = self.api("post", "/admin/content/platform-accounts",
                               {"platform": "wechat_mp", "display_name": "公众号"}, token=self.admin_token)
            self.assertEqual(created.data["auth_status"], "UNSET")
            before = self.audit_count(name)
            updated = self.api("patch", f"/admin/content/platform-accounts/{created.data['id']}",
                               {"credentials": {"appid": APPID, "appsecret": APPSECRET}},
                               token=self.admin_token)
            self.assert_ok(updated)
            row = self.assert_new_audit(name, before, object_type="platform_account",
                                        object_id=created.data["id"])
            self.assertEqual(row.detail, {"platform": "wechat_mp", "action": "credentials_updated"})
            listing = self.api("get", "/admin/content/platform-accounts", token=self.admin_token)
        self.assertEqual(updated.data["auth_status"], "NORMAL")
        self.assertEqual(updated.data["secret_saved"], {"appid": True, "appsecret": True})
        for name_, text in (("update response", updated.content.decode()),
                            ("list response", listing.content.decode()),
                            ("audit", audit_dump()), ("logs", "\n".join(logs))):
            self.assertNotIn(APPSECRET, text, name_)
            self.assertNotIn(APPID, text, name_)

    def test_tc_int_358_no_independent_validity_check_endpoint(self):
        """AC-127-05：平台账户没有独立的"检测账户有效性"接口 / 功能项。"""
        listing = self.api("get", "/admin/content/platform-accounts", token=self.admin_token).data
        for item in listing:
            self.assertEqual(set(item), {"platform", "label", "capability", "credential_fields", "account"})
        account = self.api("post", "/admin/content/platform-accounts",
                           {"platform": "wechat_mp", "display_name": "号"}, token=self.admin_token).data
        for suffix in ("check", "verify", "test", "validate", "status"):
            resp = self.api("post", f"/admin/content/platform-accounts/{account['id']}/{suffix}", {},
                            token=self.admin_token)
            self.assertEqual(resp.status_code, 404, suffix)


class BatchAuditTests(ContentRoundBase):
    """AC-128-07：每个批次恰 1 条 CONTENT_DRAFT_PUSHED，含逐平台结果（含人工 / 无凭据平台）。"""

    NAME = "CONTENT_DRAFT_PUSHED"

    def setUp(self):
        super().setUp()
        self.mp_api = FakeWechatMpApi()
        set_wechat_mp_api(self.mp_api)
        self.addCleanup(set_wechat_mp_api, None)
        self.post_id = self.create_post("批次内容").data["id"]
        self.publish(self.post_id)

    def account(self, platform, name, credentials=None):
        body = {"platform": platform, "display_name": name}
        if credentials:
            body["credentials"] = credentials
        resp = self.api("post", "/admin/content/platform-accounts", body, token=self.admin_token)
        self.assert_ok(resp, 201)
        return resp.data["id"]

    def start(self, account_ids):
        resp = self.api("post", f"/admin/content/posts/{self.post_id}/drafts",
                        {"account_ids": account_ids}, token=self.admin_token)
        self.assert_ok(resp, 202)
        return resp.data

    def run_job(self, job_id):
        return DraftPushHandler().run(JobContext(ContentJob.objects.get(id=job_id), timezone.now()))

    def test_tc_int_359_all_manual_batch_writes_exactly_one_audit_at_start(self):
        xhs = self.account("xiaohongshu", "小红书")
        toutiao = self.account("toutiao", "头条")
        batch = self.start([xhs, toutiao])
        self.assertIsNone(batch["job_id"])   # 没有自动行，不入队
        row = self.assert_new_audit(self.NAME, 0, object_type="content_draft_batch",
                                    object_id=batch["batch_id"])
        self.assertEqual(row.result, "SUCCESS")
        self.assertEqual(row.detail["post_id"], self.post_id)
        self.assertEqual(row.detail["results"], [
            {"platform": "xiaohongshu", "mode": "MANUAL", "status": "MANUAL_REQUIRED", "error_code": ""},
            {"platform": "toutiao", "mode": "MANUAL", "status": "MANUAL_REQUIRED", "error_code": ""},
        ])
        self.assertEqual(self.audit_count(self.NAME), 1)

    def test_tc_int_360_no_credentials_batch_writes_one_failure_audit(self):
        """AC-128-06 / AC-128-07：无凭据平台失败，批次审计 1 条且 result=FAILURE，不影响人工平台。"""
        wechat = self.account("wechat_mp", "公众号")
        xhs = self.account("xiaohongshu", "小红书")
        batch = self.start([wechat, xhs])
        statuses = {item["platform"]: (item["status"], item["error_code"]) for item in batch["pushes"]}
        self.assertEqual(statuses, {"wechat_mp": ("FAILED", "NO_CREDENTIALS"),
                                    "xiaohongshu": ("MANUAL_REQUIRED", "")})
        self.assertIsNone(batch["job_id"])
        row = self.assert_new_audit(self.NAME, 0, object_type="content_draft_batch",
                                    object_id=batch["batch_id"], result="FAILURE")
        self.assertEqual([(r["platform"], r["status"], r["error_code"]) for r in row.detail["results"]],
                         [("wechat_mp", "FAILED", "NO_CREDENTIALS"),
                          ("xiaohongshu", "MANUAL_REQUIRED", "")])
        self.assertEqual(self.mp_api.calls, [])   # 无凭据不触发任何外部调用

    def test_tc_int_361_mixed_batch_audit_written_once_after_handler_run(self):
        """有自动行：入队时不写，处理器结束时写 1 条，含全部行；重复汇总幂等。"""
        wechat = self.account("wechat_mp", "公众号", {"appid": APPID, "appsecret": APPSECRET})
        xhs = self.account("xiaohongshu", "小红书")
        batch = self.start([wechat, xhs])
        self.assertIsNotNone(batch["job_id"])
        self.assertEqual(self.audit_count(self.NAME), 0)
        result = self.run_job(batch["job_id"])
        self.assertEqual(result.result["results"], [{"platform": "wechat_mp", "status": "SAVED",
                                                     "error_code": ""}])
        row = self.assert_new_audit(self.NAME, 0, object_type="content_draft_batch",
                                    object_id=batch["batch_id"])
        self.assertEqual([(r["platform"], r["mode"], r["status"]) for r in row.detail["results"]],
                         [("wechat_mp", "AUTO", "SAVED"), ("xiaohongshu", "MANUAL", "MANUAL_REQUIRED")])
        actor = AuditActor("ADMIN", self.admin.id, self.admin.username)
        DraftPushService.audit_batch(batch["batch_id"], actor=actor)
        DraftPushService.audit_batch(batch["batch_id"], actor=actor)
        self.assertEqual(self.audit_count(self.NAME), 1)
        self.assertNotIn(APPSECRET, audit_dump())

    def test_tc_int_362_per_platform_result_failure_recorded(self):
        """AC-128-07 / AC-129-01：自动平台失败 → 批次审计 result=FAILURE，逐平台结果含 error_code。"""
        self.mp_api.draft_results = [WechatMpApiError("ERRCODE", errcode=99999, errmsg="rejected")]
        wechat = self.account("wechat_mp", "公众号", {"appid": APPID, "appsecret": APPSECRET})
        toutiao = self.account("toutiao", "头条")
        batch = self.start([wechat, toutiao])
        self.run_job(batch["job_id"])
        row = self.assert_new_audit(self.NAME, 0, object_type="content_draft_batch",
                                    object_id=batch["batch_id"], result="FAILURE")
        self.assertEqual([(r["platform"], r["status"], r["error_code"]) for r in row.detail["results"]],
                         [("wechat_mp", "FAILED", "UPSTREAM"), ("toutiao", "MANUAL_REQUIRED", "")])
        self.assertNotIn("rejected", str(row.detail))   # detail 不含 error_message

    def test_tc_int_363_interrupted_batch_audited_once(self):
        """worker 中断：SENDING→UNKNOWN、PENDING→FAILED 后，批次审计恰 1 条，含各行最终状态。"""
        wechat = self.account("wechat_mp", "公众号", {"appid": APPID, "appsecret": APPSECRET})
        batch = self.start([wechat])
        job = ContentJob.objects.get(id=batch["job_id"])
        push = DraftPush.objects.get(job=job)
        DraftPush.objects.filter(id=push.id).update(status="SENDING")
        ContentJob.objects.filter(id=job.id).update(status="RUNNING", attempts=1,
                                                    lease_until=timezone.now() - timedelta(seconds=5))
        from apps.content.handlers import register_all_handlers
        from apps.content.jobs import JobService
        register_all_handlers()
        self.assertEqual(JobService.requeue_expired(timezone.now()), {"requeued": 0, "failed": 1})
        row = self.assert_new_audit(self.NAME, 0, object_type="content_draft_batch",
                                    object_id=batch["batch_id"], result="FAILURE")
        self.assertEqual([(r["status"], r["error_code"]) for r in row.detail["results"]],
                         [("UNKNOWN", "UNKNOWN")])
        # 再次回收 / 汇总不重复写
        JobService.requeue_expired(timezone.now())
        self.assertEqual(self.audit_count(self.NAME), 1)

    def test_tc_int_364_worker_once_writes_one_audit_for_mixed_batch(self):
        """经 worker 入口（--once）端到端：混合批次恰 1 条审计，任务 SUCCEEDED。"""
        wechat = self.account("wechat_mp", "公众号", {"appid": APPID, "appsecret": APPSECRET})
        xhs = self.account("xiaohongshu", "小红书")
        batch = self.start([wechat, xhs])
        call_command("run_content_worker", "--once")
        job = ContentJob.objects.get(id=batch["job_id"])
        self.assertEqual(job.status, "SUCCEEDED")
        row = self.assert_new_audit(self.NAME, 0, object_type="content_draft_batch",
                                    object_id=batch["batch_id"])
        self.assertEqual(len(row.detail["results"]), 2)
        self.assertEqual(DraftPush.objects.get(job=job).status, "SAVED")


class ExportAuditTests(ContentRoundBase):
    def test_tc_int_365_export_pack_audit_and_pack_contents(self):
        """AC-130-04 / AC-130-02：导出新增 1 条审计；包含正文、2 张图片、1 个视频；未确认 409 不写审计。"""
        img1 = self.upload_media(PNG, "a.png", "图一").data["id"]
        img2 = self.upload_media(PNG + b"1", "b.png", "图二").data["id"]
        vid = self.upload_media(MP4, "v.mp4", "视频").data["id"]
        draft = self.create_post("未确认", content=[]).data["id"]
        before = self.audit_count("CONTENT_PACK_EXPORTED")
        client = self.client_for(self.admin_token)
        self.assertEqual(client.get(f"/api/v1/admin/content/posts/{draft}/export-pack?platform=toutiao")
                         .status_code, 409)
        self.assertEqual(self.audit_count("CONTENT_PACK_EXPORTED"), before)

        post_id = self.create_post("带素材", content=[
            {"type": "paragraph", "content": [{"type": "text", "text": "含图文视频的正文"}]},
            {"type": "image", "attrs": {"mediaId": img1}}, {"type": "image", "attrs": {"mediaId": img2}},
            {"type": "video", "attrs": {"mediaId": vid}}]).data["id"]
        self.publish(post_id)
        resp = client.get(f"/api/v1/admin/content/posts/{post_id}/export-pack?platform=toutiao")
        self.assertEqual(resp.status_code, 200)
        payload = b"".join(resp.streaming_content)
        resp.close()
        self.assert_new_audit("CONTENT_PACK_EXPORTED", before, object_type="content_pack",
                              object_id=post_id)
        archive = zipfile.ZipFile(io.BytesIO(payload))
        names = archive.namelist()
        media_names = sorted(n for n in names if n.startswith("media/"))
        self.assertEqual(len(media_names), 3)
        self.assertEqual(sorted(archive.read(n) for n in media_names), sorted([PNG, PNG + b"1", MP4]))
        self.assertIn("含图文视频的正文", archive.read("content.txt").decode())
        # 复制载荷不写审计（设计口径）
        copy = self.api("get", f"/admin/content/posts/{post_id}/copy?platform=toutiao", token=self.admin_token)
        self.assert_ok(copy)
        self.assertEqual(self.audit_count("CONTENT_PACK_EXPORTED"), before + 1)

    def test_tc_int_366_text_only_pack_and_build_failure_writes_no_audit(self):
        """AC-130-05：无图片视频只含正文，不报错；构建失败时不写审计。"""
        post_id = self.create_post("纯文字").data["id"]
        self.publish(post_id)
        client = self.client_for(self.admin_token)
        resp = client.get(f"/api/v1/admin/content/posts/{post_id}/export-pack?platform=xiaohongshu")
        self.assertEqual(resp.status_code, 200)
        archive = zipfile.ZipFile(io.BytesIO(b"".join(resp.streaming_content)))
        resp.close()
        self.assertEqual(sorted(archive.namelist()), ["README.txt", "content.html", "content.txt"])
        self.assertEqual(self.audit_count("CONTENT_PACK_EXPORTED"), 1)

        from apps.content.export_pack import ExportPackService
        from apps.content.models import ContentPost
        post = ContentPost.objects.get(id=post_id)
        with patch("zipfile.ZipFile.writestr", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                ExportPackService.build_zip(post, "xiaohongshu", self.admin)
        self.assertEqual(self.audit_count("CONTENT_PACK_EXPORTED"), 1)
