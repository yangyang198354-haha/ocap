"""GROUP_D（回流 1，续）：公众号适配器 + 补缺用例（TC-INT-373~394）。

只经 apps/integrations/fakes.py 的替身，不触网。
- 公众号适配器：令牌类错误刷新重发至多一次、超时不重发、40164 分类且不标失效、auth_errcodes 命中标失效并写审计、
  覆盖凭据恢复 NORMAL（AC-127-04）、响应/日志/审计不含 appsecret 与令牌、上传开关缺省关闭。
- 补缺：导出内容包不遗留临时文件、视频多片段全有或全无、worker 心跳频率与 --concurrency、
  默认标题发布被拒、草稿重试再次失败。
依据：module_design IFC-239/240/184/189、ADR-060/063。
"""
import os
import tempfile
import zipfile
import io
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.core.management import CommandError, call_command
from django.utils import timezone

from apps.content.ai_jobs import VideoJobHandler
from apps.content.conf import ContentSettings
from apps.content.drafts import DraftPushHandler
from apps.content.export_pack import ExportPackService
from apps.content.jobs import JobContext, JobService
from apps.content.media import set_remote_fetcher
from apps.content.models import ContentJob, ContentPost, DraftPush, MediaItem, PlatformAccount
from apps.content.wechat_token import WechatTokenService
from apps.core.models import AuditLog, JobRun
from apps.integrations.fakes import FakeRemoteFetcher, FakeVideoGenClient, FakeWechatMpApi
from apps.integrations.videogen import VideoTaskStatus, set_videogen_client
from apps.integrations.wechat_mp import TokenResponse, WechatMpApiError, set_wechat_mp_api
from tests.content_support import ContentRoundBase, audit_dump, capture_logs
from tests.integration.test_content_api import MP4, PNG

APPID = "wxadapt0001"
APPSECRET = "APPSECRET-ADAPTER-VERYSECRET"
CREDS = {"appid": APPID, "appsecret": APPSECRET}
EXPIRED_AUDIT = "CONTENT_PLATFORM_AUTH_EXPIRED"


def ops(api, name):
    return [c for c in api.calls if c["op"] == name]


class AdapterBase(ContentRoundBase):
    def setUp(self):
        super().setUp()
        self.mp_api = FakeWechatMpApi()
        set_wechat_mp_api(self.mp_api)
        self.addCleanup(set_wechat_mp_api, None)
        image = self.upload_media(PNG, "cover.png", "封面图").data["id"]
        self.post_id = self.create_post("公众号内容", content=[
            {"type": "paragraph", "content": [{"type": "text", "text": "正文"}]},
            {"type": "image", "attrs": {"mediaId": image}}]).data["id"]
        self.publish(self.post_id)
        created = self.api("post", "/admin/content/platform-accounts",
                           {"platform": "wechat_mp", "display_name": "公众号",
                            "credentials": CREDS}, token=self.admin_token)
        self.assert_ok(created, 201)
        self.account_id = created.data["id"]

    def prime_cache(self, token="cached-token", age_seconds=3600):
        """让令牌缓存在"age_seconds 秒前"写入：仍有效（7200-age > 提前量），且已过刷新冷却。"""
        self.mp_api.token_results = [TokenResponse(token, 7200)]
        got = WechatTokenService.get_token(
            self.account_id, CREDS, now=timezone.now() - timedelta(seconds=age_seconds))
        self.assertEqual(got, token)
        self.mp_api.calls.clear()
        self.mp_api._cursor["token"] = 0

    def push(self):
        resp = self.api("post", f"/admin/content/posts/{self.post_id}/drafts",
                        {"account_ids": [self.account_id]}, token=self.admin_token)
        self.assert_ok(resp, 202)
        job = ContentJob.objects.get(id=resp.data["job_id"])
        DraftPushHandler().run(JobContext(job, timezone.now()))
        return DraftPush.objects.get(batch_id=resp.data["batch_id"])

    def account_row(self):
        return PlatformAccount.objects.get(id=self.account_id)


class WechatAdapterTests(AdapterBase):
    def test_tc_int_373_upload_switches_default_off_no_upload_requests(self):
        """AC-128-01 / ADR-061：封面与正文图片上传开关缺省关闭；默认只发 取令牌 + draft/add，不发任何上传请求。"""
        for key in ("content.wechat_mp.upload_cover", "content.wechat_mp.upload_content_images",
                    "content.wechat_mp.require_cover"):
            self.assertIs(ContentSettings.get(key), False, key)
        row = self.push()
        self.assertEqual((row.status, row.remote_ref, row.error_code), ("SAVED", "fake-media-id", ""))
        self.assertEqual([c["op"] for c in self.mp_api.calls], ["fetch_token", "add_draft"])
        self.assertEqual(ops(self.mp_api, "upload_cover"), [])
        self.assertEqual(ops(self.mp_api, "upload_content_image"), [])

    def test_tc_int_374_token_error_refreshes_and_resends_exactly_once(self):
        """令牌类错误（缓存令牌 + 非零 errcode / HTTP 401）→ 强制刷新并重发一次成功；
        连续两次失败也只重发这一次（add_draft 共 2 次，不会第 3 次）。"""
        for label, first_error in (("ERRCODE", WechatMpApiError("ERRCODE", errcode=40001, errmsg="bad token")),
                                   ("HTTP401", WechatMpApiError("HTTP", http_status=401))):
            with self.subTest(label):
                PlatformAccount.objects.filter(id=self.account_id).update(
                    token_blob=None, token_expires_at=None, token_refreshed_at=None, token_lock_until=None)
                self.prime_cache()
                self.mp_api.token_results = [TokenResponse("renewed-token", 7200)]
                self.mp_api._cursor["token"] = 0
                self.mp_api.draft_results = [first_error, "media-after-refresh"]
                self.mp_api._cursor["draft"] = 0
                row = self.push()
                self.assertEqual((row.status, row.remote_ref), ("SAVED", "media-after-refresh"))
                self.assertEqual([c["op"] for c in self.mp_api.calls],
                                 ["add_draft", "fetch_token", "add_draft"])
                self.assertEqual(len(ops(self.mp_api, "fetch_token")), 1)

        PlatformAccount.objects.filter(id=self.account_id).update(
            token_blob=None, token_expires_at=None, token_refreshed_at=None, token_lock_until=None)
        self.prime_cache()
        self.mp_api.token_results = [TokenResponse("renewed-2", 7200)]
        self.mp_api._cursor["token"] = 0
        self.mp_api.draft_results = [WechatMpApiError("ERRCODE", errcode=40001),
                                     WechatMpApiError("ERRCODE", errcode=40002, errmsg="still bad"),
                                     "never-reached"]
        self.mp_api._cursor["draft"] = 0
        row = self.push()
        self.assertEqual((row.status, row.error_code), ("FAILED", "UPSTREAM"))
        self.assertIn("40002", row.error_message)
        self.assertEqual(len(ops(self.mp_api, "add_draft")), 2)
        self.assertEqual(len(ops(self.mp_api, "fetch_token")), 1)

    def test_tc_int_375_timeout_is_not_resent(self):
        """超时 / 连接中断（NETWORK）不重发，避免重复草稿：add_draft 恰 1 次、不再取令牌；结果 FAILED/NETWORK。"""
        self.prime_cache()
        self.mp_api.draft_results = [WechatMpApiError("NETWORK", errmsg="read timed out")]
        row = self.push()
        self.assertEqual((row.status, row.error_code), ("FAILED", "NETWORK"))
        self.assertEqual([c["op"] for c in self.mp_api.calls], ["add_draft"])
        self.assertEqual(self.account_row().auth_status, "NORMAL")
        self.assertEqual(self.audit_count(EXPIRED_AUDIT), 0)

    def test_tc_int_376_ip_whitelist_error_classified_and_not_marked_expired(self):
        """40164：无论发生在取令牌还是 draft/add，都分类为 IP_NOT_WHITELISTED，账户保持 NORMAL，不写失效审计，不重发。"""
        # 1) 取令牌时
        self.mp_api.token_results = [WechatMpApiError("ERRCODE", errcode=40164, errmsg="invalid ip")]
        row = self.push()
        self.assertEqual((row.status, row.error_code), ("FAILED", "IP_NOT_WHITELISTED"))
        self.assertEqual(self.account_row().auth_status, "NORMAL")
        self.assertEqual(self.audit_count(EXPIRED_AUDIT), 0)
        self.assertEqual(len(ops(self.mp_api, "add_draft")), 0)

        # 2) draft/add 时（令牌来自缓存，且 token_errcodes 为空的兜底也不会把 IP 错误当令牌错误）
        self.mp_api.reset()
        self.prime_cache()
        self.mp_api.draft_results = [WechatMpApiError("ERRCODE", errcode=40164, errmsg="invalid ip")]
        row = self.push()
        self.assertEqual((row.status, row.error_code), ("FAILED", "IP_NOT_WHITELISTED"))
        self.assertEqual(self.account_row().auth_status, "NORMAL")
        self.assertEqual(self.audit_count(EXPIRED_AUDIT), 0)
        self.assertEqual([c["op"] for c in self.mp_api.calls], ["add_draft"])

    def test_tc_int_377_auth_errcode_marks_expired_and_audits_once(self):
        """AC-127-03：auth_errcodes 命中 → 推送 FAILED/AUTH_EXPIRED（中文提示），账户标 EXPIRED，
        写 1 条 CONTENT_PLATFORM_AUTH_EXPIRED；再次推送不重复写。"""
        ContentSettings.update({"content.wechat_mp.auth_errcodes": [40013]}, admin_id=self.admin.id)
        self.mp_api.token_results = [WechatMpApiError("ERRCODE", errcode=40013, errmsg="invalid appid")]
        row = self.push()
        self.assertEqual((row.status, row.error_code, row.error_message),
                         ("FAILED", "AUTH_EXPIRED", "认证已失效，请重新认证"))
        self.assertEqual(self.account_row().auth_status, "EXPIRED")
        audit = self.assert_new_audit(EXPIRED_AUDIT, 0, object_type="platform_account",
                                      object_id=self.account_id)
        self.assertEqual(audit.detail, {"platform": "wechat_mp", "reason": "AUTH_REJECTED"})
        listing = self.api("get", "/admin/content/platform-accounts", token=self.admin_token)
        wechat = [i for i in listing.data if i["platform"] == "wechat_mp"][0]
        self.assertEqual(wechat["account"]["auth_status"], "EXPIRED")
        # 再次推送：仍失败，但账户已非 NORMAL，不再写第二条失效审计
        again = self.push()
        self.assertEqual(again.error_code, "AUTH_EXPIRED")
        self.assertEqual(self.audit_count(EXPIRED_AUDIT), 1)

    def test_tc_int_378_overwriting_credentials_clears_cache_and_restores_normal(self):
        """AC-127-04：已失效账户覆盖更新认证信息 → 恢复 NORMAL，令牌缓存列清空，下次推送重新取令牌并成功。"""
        ContentSettings.update({"content.wechat_mp.auth_errcodes": [40013]}, admin_id=self.admin.id)
        self.prime_cache()
        self.assertIsNotNone(self.account_row().token_blob)
        self.mp_api.token_results = [WechatMpApiError("ERRCODE", errcode=40013)]
        self.mp_api._cursor["token"] = 0
        PlatformAccount.objects.filter(id=self.account_id).update(
            token_blob=None, token_expires_at=None, token_refreshed_at=None)
        self.push()
        self.assertEqual(self.account_row().auth_status, "EXPIRED")
        # 缓存里放一个令牌，证明覆盖凭据会清缓存
        self.mp_api.token_results = [TokenResponse("stale-token", 7200)]
        self.mp_api._cursor["token"] = 0
        WechatTokenService.get_token(self.account_id, CREDS)
        self.assertIsNotNone(self.account_row().token_blob)

        updated = self.api("patch", f"/admin/content/platform-accounts/{self.account_id}",
                           {"credentials": {"appid": APPID, "appsecret": APPSECRET + "-NEW"}},
                           token=self.admin_token)
        self.assert_ok(updated)
        self.assertEqual(updated.data["auth_status"], "NORMAL")
        row = self.account_row()
        self.assertEqual((row.auth_status, row.token_blob, row.token_expires_at,
                          row.token_refreshed_at, row.token_lock_until), ("NORMAL", None, None, None, None))
        self.mp_api.calls.clear()
        self.mp_api.token_results = [TokenResponse("fresh-after-overwrite", 7200)]
        self.mp_api._cursor["token"] = 0
        pushed = self.push()
        self.assertEqual(pushed.status, "SAVED")
        self.assertEqual([c["op"] for c in self.mp_api.calls], ["fetch_token", "add_draft"])

    def test_tc_int_379_responses_audit_logs_never_contain_secret_or_token(self):
        """AC-127-02 / 125 系列：整条链路（保存、推送、失败、历史、账户列表）的响应、日志、审计、
        推送记录中 appsecret 与访问令牌出现 0 次。"""
        token = "ACCESS-TOKEN-LEAKCHECK-001"
        self.mp_api.token_results = [TokenResponse(token, 7200)]
        self.mp_api.draft_results = [WechatMpApiError("ERRCODE", errcode=99999,
                                                      errmsg=f"bad {APPSECRET} {token}")]
        with capture_logs() as logs:
            row = self.push()
            history = self.api("get", f"/admin/content/posts/{self.post_id}/drafts/history",
                               token=self.admin_token)
            listing = self.api("get", "/admin/content/platform-accounts", token=self.admin_token)
        self.assertEqual(row.status, "FAILED")
        texts = {"history": history.content.decode(), "accounts": listing.content.decode(),
                 "audit": audit_dump(), "logs": "\n".join(logs),
                 "push": f"{row.error_message}|{row.error_code}|{row.remote_ref}"}
        for name, text in texts.items():
            self.assertNotIn(APPSECRET, text, name)
            self.assertNotIn(token, text, name)
        cached = self.account_row()
        self.assertNotIn(token.encode(), bytes(cached.token_blob))   # 缓存是密文
        self.assertNotIn(APPSECRET.encode(), bytes(cached.secret_blob))


class RetryAndTitleTests(AdapterBase):
    def test_tc_int_380_retry_fails_again_keeps_failed_with_latest_reason_and_one_more_history(self):
        """AC-129-04：重试再次失败 → 仍 FAILED 且显示最新失败原因；历史新增 1 条，原记录不变。"""
        self.mp_api.draft_results = [WechatMpApiError("NETWORK", errmsg="first failure 91001"),
                                     WechatMpApiError("NETWORK", errmsg="second failure 91002")]
        first = self.push()
        self.assertEqual((first.status, first.error_code), ("FAILED", "NETWORK"))
        self.assertIn("91001", first.error_message)
        history_url = f"/admin/content/posts/{self.post_id}/drafts/history"
        before = self.api("get", history_url, token=self.admin_token).data
        before_total = len(before["results"] if isinstance(before, dict) else before)

        retry = self.api("post", f"/admin/content/drafts/{first.id}/retry", {}, token=self.admin_token)
        self.assert_ok(retry, 202)
        job = ContentJob.objects.get(id=retry.data["job_id"])
        DraftPushHandler().run(JobContext(job, timezone.now()))
        second = DraftPush.objects.get(id=retry.data["push"]["id"])
        self.assertEqual((second.status, second.error_code), ("FAILED", "NETWORK"))
        self.assertIn("91002", second.error_message)
        self.assertNotIn("91001", second.error_message)
        self.assertEqual(second.retry_of_id, first.id)
        first.refresh_from_db()
        self.assertIn("91001", first.error_message)

        after = self.api("get", history_url, token=self.admin_token).data
        results = after["results"] if isinstance(after, dict) else after
        self.assertEqual(len(results), before_total + 1)
        self.assertEqual(results[0]["id"], second.id)   # 时间倒序，最新在前
        self.assertEqual(results[0]["status"], "FAILED")
        self.assertIn("91002", results[0]["error_message"])

    def test_tc_int_381_default_title_cannot_be_published(self):
        """AC-105-03：默认标题"未命名内容"（含首尾空白）视为标题缺失，发布被拒 400 POST_INCOMPLETE，状态仍为草稿；
        仅以它开头的真实标题可发布。"""
        for title in ("未命名内容", "  未命名内容  "):
            with self.subTest(title=title):
                post_id = self.create_post(title).data["id"]
                resp = self.publish(post_id)
                self.assert_error(resp, 400, "POST_INCOMPLETE")
                self.assertEqual(resp.data["details"]["missing"], ["title"])
                self.assertEqual(ContentPost.objects.get(id=post_id).status, "DRAFT")
        ok_id = self.create_post("未命名内容补充说明").data["id"]
        self.assert_ok(self.publish(ok_id))
        self.assertEqual(ContentPost.objects.get(id=ok_id).status, "PUBLISHED")


class ExportTempFileTests(ContentRoundBase):
    def listing(self):
        return set(os.listdir(tempfile.gettempdir()))

    def test_tc_int_382_export_pack_leaves_no_temp_files_on_success_and_error(self):
        """GR-C-002-F05 / AC-130-02：导出内容包前后 tempfile.gettempdir() 无新增文件（成功、客户端中断、构建异常）。"""
        img = self.upload_media(PNG, "p.png", "图").data["id"]
        vid = self.upload_media(MP4, "v.mp4", "视频").data["id"]
        post_id = self.create_post("导出", content=[
            {"type": "paragraph", "content": [{"type": "text", "text": "文"}]},
            {"type": "image", "attrs": {"mediaId": img}}, {"type": "video", "attrs": {"mediaId": vid}},
        ]).data["id"]
        self.publish(post_id)
        client = self.client_for(self.admin_token)

        before = self.listing()
        resp = client.get(f"/api/v1/admin/content/posts/{post_id}/export-pack?platform=toutiao")
        self.assertEqual(resp.status_code, 200)
        data = b"".join(resp.streaming_content)
        resp.close()
        self.assertEqual(len([n for n in zipfile.ZipFile(io.BytesIO(data)).namelist()
                              if n.startswith("media/")]), 2)
        self.assertEqual(self.listing() - before, set(), "成功路径遗留了临时文件")

        resp = client.get(f"/api/v1/admin/content/posts/{post_id}/export-pack?platform=toutiao")
        resp.close()   # 客户端未读完就断开
        self.assertEqual(self.listing() - before, set(), "客户端中断路径遗留了临时文件")

        post = ContentPost.objects.get(id=post_id)
        with patch("zipfile.ZipFile.write", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                ExportPackService.build_zip(post, "toutiao", self.admin)
        with patch("apps.content.export_pack.AuditService.record", side_effect=RuntimeError("audit down")):
            with self.assertRaises(RuntimeError):
                ExportPackService.build_zip(post, "toutiao", self.admin)
        self.assertEqual(self.listing() - before, set(), "异常路径遗留了临时文件")


class VideoAllOrNothingTests(ContentRoundBase):
    def setUp(self):
        super().setUp()
        self.client_ = FakeVideoGenClient()
        self.fetcher = FakeRemoteFetcher()
        set_videogen_client(self.client_)
        set_remote_fetcher(self.fetcher)
        self.addCleanup(set_videogen_client, None)
        self.addCleanup(set_remote_fetcher, None)
        self.api("put", "/admin/content/services/VIDEO_JIMENG",
                 {"secrets": {"access_key": "ak", "secret_key": "sk"}}, token=self.admin_token)
        self.post_id = self.create_post("多段视频").data["id"]
        self.api("post", f"/admin/content/posts/{self.post_id}/confirm-text", {}, token=self.admin_token)
        resp = self.api("post", "/admin/content/ai/video", {"post_id": self.post_id}, token=self.admin_token)
        self.assert_ok(resp, 202)
        self.job_id = resp.data["id"]
        job = ContentJob.objects.get(id=self.job_id)
        self.assertEqual(VideoJobHandler().run(JobContext(job, timezone.now())).__class__.__name__, "Wait")

    def media_files(self):
        found = []
        for root, _dirs, files in os.walk(self.media_root):
            found += files
        return found

    def complete(self, urls):
        self.client_.statuses = [VideoTaskStatus(task_id="fake-task", status="completed", progress=100,
                                                 clip_urls=tuple(urls))]
        job = ContentJob.objects.get(id=self.job_id)
        return VideoJobHandler().run(JobContext(job, timezone.now()))

    def test_tc_int_383_one_segment_download_failure_adds_nothing_to_library(self):
        """AC-124-03 / GR-C-002-F07：多片段中第 2 段下载失败 → 任务失败，素材库无新增（已入库的第 1 段被回收，文件也删除）。"""
        self.fetcher.payloads = {"https://example.com/a.mp4": MP4}   # b.mp4 缺失 → 下载失败
        before_rows = MediaItem.objects.count()
        before_files = self.media_files()
        outcome = self.complete(["https://example.com/a.mp4", "https://example.com/b.mp4"])
        self.assertEqual((outcome.__class__.__name__, outcome.code), ("Fail", "DOWNLOAD_FAILED"))
        self.assertEqual(MediaItem.objects.count(), before_rows)
        self.assertEqual(MediaItem.objects.filter(source="AI_GENERATED").count(), 0)
        self.assertEqual(self.media_files(), before_files)
        self.assertEqual(self.audit_count("CONTENT_VIDEO_COMPLETED"), 0)
        listing = self.api("get", "/admin/content/media?media_type=VIDEO&source=AI_GENERATED",
                           token=self.admin_token)
        self.assertEqual(listing.data["count"] if "count" in listing.data else len(listing.data["results"]), 0)

    def test_tc_int_384_all_segments_succeed_become_saved_together(self):
        """正例（配对 383）：两段都成功 → 素材库恰新增 2 条 VIDEO/AI_GENERATED/SAVED，写 1 条完成审计。"""
        self.fetcher.payloads = {"https://example.com/a.mp4": MP4, "https://example.com/b.mp4": MP4 + b"1"}
        outcome = self.complete(["https://example.com/a.mp4", "https://example.com/b.mp4"])
        self.assertEqual(outcome.__class__.__name__, "Done")
        rows = list(MediaItem.objects.filter(source="AI_GENERATED"))
        self.assertEqual([(r.media_type, r.state) for r in rows], [("VIDEO", "SAVED")] * 2)
        self.assertEqual(self.audit_count("CONTENT_VIDEO_COMPLETED"), 1)

    def test_tc_int_385_remote_failure_marks_job_failed_and_library_unchanged(self):
        """AC-124-03：服务返回失败 → 任务 FAILED 并显示失败原因，素材库无新增（经 run_one 落库）。"""
        from apps.content.handlers import register_all_handlers
        register_all_handlers()
        self.client_.statuses = [VideoTaskStatus(task_id="fake-task", status="failed", progress=10,
                                                 clip_urls=(), error="远端失败原因X")]
        before = MediaItem.objects.count()
        ContentJob.objects.filter(id=self.job_id).update(status="RUNNING")
        job = JobService.run_one(self.job_id)
        self.assertEqual((job.status, job.error_code), ("FAILED", "REMOTE_FAILED"))
        self.assertIn("远端失败原因X", job.error_message)
        self.assertEqual(MediaItem.objects.count(), before)
        shown = self.api("get", f"/admin/content/jobs/{self.job_id}", token=self.admin_token)
        self.assertEqual(shown.data["status"], "FAILED")
        self.assertIn("远端失败原因X", shown.data["error_message"])


class StopLoop(Exception):
    pass


class WorkerTests(ContentRoundBase):
    MODULE = "apps.content.management.commands.run_content_worker"

    def run_loop(self, iterations, step_seconds=2.0):
        """让 worker 空转 iterations 个轮询周期（每周期单调时钟 +step_seconds），返回 JobRun 写入次数。"""
        clock = {"now": 1000.0}
        fake_time = MagicMock()
        fake_time.monotonic.side_effect = lambda: clock["now"]
        fake_time.time.return_value = 1.7e9
        counter = {"sleeps": 0}

        def sleep(_seconds):
            clock["now"] += step_seconds
            counter["sleeps"] += 1
            if counter["sleeps"] >= iterations:
                raise StopLoop()

        fake_time.sleep.side_effect = sleep
        job_run = MagicMock()
        with patch(f"{self.MODULE}.time", fake_time), patch(f"{self.MODULE}.JobRun", job_run):
            with self.assertRaises(StopLoop):
                call_command("run_content_worker", "--poll-interval", "2")
        return job_run.objects.update_or_create.call_count

    def test_tc_int_386_jobrun_written_at_most_once_per_60_seconds(self):
        """GR-C-002-F07：心跳（JobRun）至多每 60 秒 1 次（启动时 1 次）；不再每个 2 秒轮询周期写一次。"""
        self.assertEqual(self.run_loop(29), 1)    # 58 秒：仅启动时 1 次
        self.assertEqual(self.run_loop(31), 2)    # 62 秒：+1
        self.assertEqual(self.run_loop(61), 3)    # 122 秒：+1（每 60 秒一次，不会每周期一次）

    def test_tc_int_387_concurrency_removed_and_once_writes_running_then_stopped(self):
        """--concurrency 已移除（传入即报错，帮助中不出现）；--once 在启动 / 停止各写一次，最终状态 STOPPED。"""
        with self.assertRaises(CommandError):
            call_command("run_content_worker", "--once", "--concurrency=2")
        from django.core.management import load_command_class
        self.assertNotIn("concurrency", load_command_class("apps.content", "run_content_worker")
                         .create_parser("manage.py", "run_content_worker").format_help())
        call_command("run_content_worker", "--once")
        row = JobRun.objects.get(job_name="content_worker")
        self.assertEqual(row.last_status, "STOPPED")


class NestedMediaBlocksContractTests(ContentRoundBase):
    def test_tc_int_388_blocks_media_src_prefix_consistent_at_any_depth(self):
        """AC-108-01 / AC-123-01 / F07：小程序 blocks 的媒体 src 在任意深度都应与顶层一致地去掉 API 前缀
        （小程序 mediaUrl 会再拼接 BASE=/api/v1，否则嵌套媒体 URL 变成 /api/v1/api/v1/...）。"""
        img = self.upload_media(PNG, "n.png", "图").data["id"]
        vid = self.upload_media(MP4, "n.mp4", "视频").data["id"]
        post_id = self.create_post("嵌套媒体", content=[
            {"type": "image", "attrs": {"mediaId": img}},
            {"type": "blockquote", "content": [{"type": "image", "attrs": {"mediaId": img}}]},
            {"type": "bulletList", "content": [{"type": "listItem", "content": [
                {"type": "video", "attrs": {"mediaId": vid}}]}]},
        ]).data["id"]
        self.publish(post_id)
        resp = self.api("get", f"/info/posts/{post_id}?fmt=blocks", token=self.member_token)
        self.assert_ok(resp)
        blocks = resp.data["pages"][0]["blocks"]

        def srcs(items):
            for block in items:
                if block.get("src"):
                    yield block["src"]
                yield from srcs(block.get("children") or [])
                for item in block.get("items") or []:
                    yield from srcs(item)

        found = list(srcs(blocks))
        self.assertEqual(len(found), 3)
        for src in found:
            self.assertTrue(src.startswith("/content/media/"), src)
            self.assertNotIn("/api/v1", src)


class RetrySuccessAndFailureBranchTests(AdapterBase):
    def test_tc_int_389_retry_success_changes_only_that_platform(self):
        """AC-129-02：失败平台重试且平台返回成功 → 该平台结果变为成功（新记录 SAVED），其他平台结果不变。"""
        xhs = self.api("post", "/admin/content/platform-accounts",
                       {"platform": "xiaohongshu", "display_name": "小红书"}, token=self.admin_token).data["id"]
        self.mp_api.draft_results = [WechatMpApiError("NETWORK", errmsg="boom"), "media-retried"]
        batch = self.api("post", f"/admin/content/posts/{self.post_id}/drafts",
                         {"account_ids": [self.account_id, xhs]}, token=self.admin_token).data
        DraftPushHandler().run(JobContext(ContentJob.objects.get(id=batch["job_id"]), timezone.now()))
        rows = {r.platform: r for r in DraftPush.objects.filter(batch_id=batch["batch_id"])}
        self.assertEqual((rows["wechat_mp"].status, rows["xiaohongshu"].status), ("FAILED", "MANUAL_REQUIRED"))

        retry = self.api("post", f"/admin/content/drafts/{rows['wechat_mp'].id}/retry", {}, token=self.admin_token)
        self.assert_ok(retry, 202)
        DraftPushHandler().run(JobContext(ContentJob.objects.get(id=retry.data["job_id"]), timezone.now()))
        again = DraftPush.objects.get(id=retry.data["push"]["id"])
        self.assertEqual((again.status, again.remote_ref, again.error_code), ("SAVED", "media-retried", ""))
        self.assertEqual(again.retry_of_id, rows["wechat_mp"].id)
        # 其他平台与原失败记录均不变
        self.assertEqual(DraftPush.objects.get(id=rows["xiaohongshu"].id).status, "MANUAL_REQUIRED")
        self.assertEqual(DraftPush.objects.get(id=rows["wechat_mp"].id).status, "FAILED")


class AiFailureAndMediaBoundaryTests(ContentRoundBase):
    def test_tc_int_390_llm_failure_leaves_no_post_and_reports_reason(self):
        """AC-114-04：模型服务返回失败 → 任务 FAILED 带失败原因，不产生内容草稿。"""
        from apps.content.handlers import register_all_handlers
        from apps.integrations.fakes import FakeLlmClient
        from apps.integrations.llm import set_llm_client
        register_all_handlers()
        fake = FakeLlmClient()
        set_llm_client(fake)
        self.addCleanup(set_llm_client, None)
        self.api("put", "/admin/content/services/LLM_DEEPSEEK", {"secrets": {"api_key": "sk-f"}},
                 token=self.admin_token)
        self.api("post", "/admin/content/services/LLM_DEEPSEEK/test", {}, token=self.admin_token)
        posts_before = ContentPost.objects.count()
        job = self.api("post", "/admin/content/ai/text", {"prompt": "写公告"}, token=self.admin_token)
        self.assert_ok(job, 202)
        fake.fail_code = "UPSTREAM"
        ContentJob.objects.filter(id=job.data["id"]).update(status="RUNNING")
        done = JobService.run_one(job.data["id"])
        self.assertEqual((done.status, done.error_code), ("FAILED", "UPSTREAM"))
        self.assertTrue(done.error_message)
        shown = self.api("get", f"/admin/content/jobs/{job.data['id']}", token=self.admin_token)
        self.assertEqual(shown.data["status"], "FAILED")
        self.assertEqual(ContentPost.objects.count(), posts_before)

    def test_tc_int_391_image_failure_leaves_library_and_posts_unchanged(self):
        """AC-116-04 / AC-120-03：文生图失败 → 任务 FAILED 带原因；素材库与正文不变。"""
        from apps.content.handlers import register_all_handlers
        from apps.integrations.fakes import FakeImageGenClient
        from apps.integrations.imagegen import set_imagegen_client
        register_all_handlers()
        client = FakeImageGenClient()
        client.fail_code = "UPSTREAM"
        set_imagegen_client(client)
        self.addCleanup(set_imagegen_client, None)
        self.api("put", "/admin/content/services/IMAGE_ARK", {"secrets": {"api_key": "sk-i"}},
                 token=self.admin_token)
        post_id = self.create_post("配图").data["id"]
        doc_before = ContentPost.objects.get(id=post_id).doc
        media_before = MediaItem.objects.count()
        job = self.api("post", "/admin/content/ai/image", {"prompt": "配图"}, token=self.admin_token)
        self.assert_ok(job, 202)
        ContentJob.objects.filter(id=job.data["id"]).update(status="RUNNING")
        done = JobService.run_one(job.data["id"])
        self.assertEqual((done.status, done.error_code), ("FAILED", "UPSTREAM"))
        self.assertEqual(MediaItem.objects.count(), media_before)
        self.assertEqual(ContentPost.objects.get(id=post_id).doc, doc_before)

    def test_tc_int_392_media_filters_by_type_and_source_combined(self):
        """AC-120-02 / AC-122-01：类型 + 来源同时筛选只返回同时满足者；AI 来源筛选不含上传素材。"""
        self.upload_media(PNG, "up.png", "上传图")
        self.upload_media(MP4, "up.mp4", "上传视频")
        for media_type, name in (("IMAGE", "ai.png"), ("VIDEO", "ai.mp4")):
            MediaItem.objects.create(media_type=media_type, source="AI_GENERATED", state="SAVED",
                                     title=f"AI {media_type}", original_name=name,
                                     content_type="image/png" if media_type == "IMAGE" else "video/mp4",
                                     size=10, sha256=name, storage_path=f"content/{name}",
                                     created_by_admin_id=self.admin.id)

        def titles(query):
            resp = self.api("get", f"/admin/content/media?{query}", token=self.admin_token)
            self.assert_ok(resp)
            return sorted(item["title"] for item in resp.data["results"])

        self.assertEqual(titles("source=AI_GENERATED"), ["AI IMAGE", "AI VIDEO"])
        self.assertEqual(titles("media_type=VIDEO&source=AI_GENERATED"), ["AI VIDEO"])
        self.assertEqual(titles("media_type=IMAGE&source=UPLOAD"), ["上传图"])
        self.assertEqual(titles("media_type=VIDEO&source=UPLOAD"), ["上传视频"])

    def test_tc_int_393_eleven_mb_image_and_video_rejected_library_unchanged(self):
        """AC-119-03 / AC-119-04 / AC-123-03 / AC-111-03：11 MB 的图片与视频被拒（413），素材库无新增；
        边界内的 5 MB 图片、8 MB 视频可上传（AC-119-01 / AC-119-02）。"""
        mb = 1024 * 1024
        self.assert_error(self.upload_media(PNG + b"0" * (11 * mb), "big.png"), 413, "FILE_TOO_LARGE")
        self.assert_error(self.upload_media(MP4 + b"0" * (11 * mb), "big.mp4"), 413, "FILE_TOO_LARGE")
        self.assertEqual(MediaItem.objects.count(), 0)
        ok_img = self.upload_media(PNG + b"0" * (5 * mb), "five.png", "五兆")
        ok_vid = self.upload_media(MP4 + b"0" * (8 * mb), "eight.mp4", "八兆")
        self.assert_ok(ok_img, 201)
        self.assert_ok(ok_vid, 201)
        self.assertEqual([(r.media_type, r.source) for r in MediaItem.objects.order_by("created_at")],
                         [("IMAGE", "UPLOAD"), ("VIDEO", "UPLOAD")])

    def test_tc_int_394_empty_style_template_name_rejected_existing_unchanged(self):
        """AC-112-04：自定义样式名称为空（或全空白）→ 400 STYLE_NAME_REQUIRED（"模板名称不能为空"），不新增模板。"""
        before = self.api("get", "/admin/content/style-templates", token=self.admin_token).data
        for name in ("", "   "):
            resp = self.api("post", "/admin/content/style-templates",
                            {"name": name, "tokens": {"font_size": 18}}, token=self.admin_token)
            self.assert_error(resp, 400, "STYLE_NAME_REQUIRED")
            self.assertIn("模板名称不能为空", resp.data["message"])
        self.assertEqual(self.api("get", "/admin/content/style-templates", token=self.admin_token).data, before)
