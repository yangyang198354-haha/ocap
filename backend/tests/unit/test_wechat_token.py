"""GROUP_D（回流 1）：公众号令牌服务 MOD-062 单元测试（TC-UNIT-368~382）。

只经 apps/integrations/fakes.py 的 FakeWechatMpApi，不触网。SQLite 内存库无法并发，
"单飞"用预置的 token_lock_until（另一个 worker 持锁）模拟。
依据：module_design IFC-240 行为契约 1~7；ADR-060。
"""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from apps.content.conf import ContentSettings
from apps.content.models import PlatformAccount
from apps.content.vault import CredentialVault
from apps.content.wechat_token import WechatTokenError, WechatTokenService
from apps.integrations.fakes import FakeWechatMpApi
from apps.integrations.wechat_mp import TokenResponse, WechatMpApiError, set_wechat_mp_api

CREDS = {"appid": "wxtest0001", "appsecret": "SECRET-xyz-001"}


def calls(api, op):
    return [c for c in api.calls if c["op"] == op]


class TokenServiceBase(TestCase):
    def setUp(self):
        super().setUp()
        self.api = FakeWechatMpApi()
        set_wechat_mp_api(self.api)
        self.addCleanup(set_wechat_mp_api, None)
        self.account = PlatformAccount.objects.create(
            platform="wechat_mp", display_name="公众号", secret_keys=["appid", "appsecret"],
            auth_status="NORMAL", created_by_admin_id=1)
        self.t0 = timezone.now()

    def fresh(self):
        return PlatformAccount.objects.get(id=self.account.id)

    def get(self, **kwargs):
        return WechatTokenService.get_token(self.account.id, CREDS, **kwargs)


class CacheTests(TokenServiceBase):
    def test_tc_unit_368_cache_hit_avoids_second_fetch(self):
        """AC-128-01 / ADR-060：首次取令牌后加密入库，再次获取命中缓存、不再请求。"""
        self.assertEqual(self.get(now=self.t0), "fake-mp-token")
        self.assertEqual(self.get(now=self.t0 + timedelta(seconds=60)), "fake-mp-token")
        self.assertEqual(len(calls(self.api, "fetch_token")), 1)
        row = self.fresh()
        self.assertEqual(row.token_expires_at, self.t0 + timedelta(seconds=7200))
        self.assertEqual(row.token_refreshed_at, self.t0)
        self.assertIsNone(row.token_lock_until)
        # 缓存是密文，且能用保险库解回
        blob = bytes(row.token_blob)
        self.assertNotIn(b"fake-mp-token", blob)
        self.assertEqual(CredentialVault.decrypt(
            blob, context=f"content_platformaccount_token|{row.id}"), {"access_token": "fake-mp-token"})

    def test_tc_unit_369_refresh_inside_margin(self):
        """提前量 300 秒：距过期 ≤300 秒视为需要刷新；>300 秒仍命中缓存。"""
        self.assertEqual(ContentSettings.get("content.wechat_mp.token_margin_seconds"), 300)
        self.api.token_results = [TokenResponse("t1", 7200), TokenResponse("t2", 7200)]
        self.assertEqual(self.get(now=self.t0), "t1")
        self.assertEqual(self.get(now=self.t0 + timedelta(seconds=7200 - 301)), "t1")
        self.assertEqual(len(calls(self.api, "fetch_token")), 1)
        self.assertEqual(self.get(now=self.t0 + timedelta(seconds=7200 - 299)), "t2")
        self.assertEqual(len(calls(self.api, "fetch_token")), 2)
        self.assertEqual(self.fresh().token_expires_at,
                         self.t0 + timedelta(seconds=7200 - 299) + timedelta(seconds=7200))

    def test_tc_unit_370_expires_in_missing_defaults_to_7200(self):
        for expires_in in (0, -5):
            PlatformAccountReset(self.account)
            self.api.token_results = [TokenResponse("tok", expires_in)]
            self.api._cursor["token"] = 0
            self.get(now=self.t0)
            self.assertEqual(self.fresh().token_expires_at, self.t0 + timedelta(seconds=7200))

    def test_tc_unit_371_invalidate_clears_all_cache_columns(self):
        self.get(now=self.t0)
        PlatformAccount.objects.filter(id=self.account.id).update(
            token_lock_until=self.t0 + timedelta(seconds=30))
        WechatTokenService.invalidate(self.account.id)
        row = self.fresh()
        self.assertIsNone(row.token_blob)
        self.assertIsNone(row.token_expires_at)
        self.assertIsNone(row.token_refreshed_at)
        self.assertIsNone(row.token_lock_until)
        self.get(now=self.t0)   # 清空后重新取
        self.assertEqual(len(calls(self.api, "fetch_token")), 2)

    def test_tc_unit_372_missing_credentials_no_network(self):
        for creds in ({}, {"appid": "wx"}, {"appsecret": "s"}, {"appid": "", "appsecret": ""}):
            with self.assertRaises(WechatTokenError) as ctx:
                WechatTokenService.get_token(self.account.id, creds)
            self.assertEqual(ctx.exception.code, "NO_CREDENTIALS")
        self.assertEqual(self.api.calls, [])

    def test_tc_unit_373_wrong_platform_account_is_value_error(self):
        other = PlatformAccount.objects.create(platform="toutiao", display_name="头条",
                                               created_by_admin_id=1)
        with self.assertRaises(ValueError):
            WechatTokenService.get_token(other.id, CREDS)
        with self.assertRaises(ValueError):
            WechatTokenService.get_token(999999, CREDS)


def PlatformAccountReset(account):
    PlatformAccount.objects.filter(id=account.id).update(
        token_blob=None, token_expires_at=None, token_refreshed_at=None, token_lock_until=None)


class SingleFlightAndCooldownTests(TokenServiceBase):
    def test_tc_unit_374_lock_held_times_out_as_token_busy_without_fetch(self):
        """单飞：他人持锁且始终没写出缓存 → 等待上限后 TOKEN_BUSY，本进程不发请求。"""
        PlatformAccount.objects.filter(id=self.account.id).update(
            token_lock_until=timezone.now() + timedelta(seconds=60))
        fake_time = MagicMock()
        ticks = iter(range(0, 1000, 3))
        fake_time.monotonic.side_effect = lambda: next(ticks)
        with patch("apps.content.wechat_token.time", fake_time):
            with self.assertRaises(WechatTokenError) as ctx:
                self.get()
        self.assertEqual(ctx.exception.code, "TOKEN_BUSY")
        self.assertEqual(calls(self.api, "fetch_token"), [])
        self.assertTrue(fake_time.sleep.called)
        self.assertTrue(all(call.args == (0.5,) for call in fake_time.sleep.call_args_list))
        self.assertIsNotNone(self.fresh().token_lock_until)   # 不能释放别人的锁

    def test_tc_unit_375_lock_held_then_other_worker_cached_token_is_reused(self):
        PlatformAccount.objects.filter(id=self.account.id).update(
            token_lock_until=timezone.now() + timedelta(seconds=60))
        blob = CredentialVault.encrypt({"access_token": "from-other-worker"},
                                       context=f"content_platformaccount_token|{self.account.id}")

        def other_worker_finishes(_seconds):
            PlatformAccount.objects.filter(id=self.account.id).update(
                token_blob=blob, token_expires_at=timezone.now() + timedelta(seconds=7000),
                token_refreshed_at=timezone.now(), token_lock_until=None)

        fake_time = MagicMock()
        fake_time.monotonic.side_effect = iter(range(0, 100)).__next__
        fake_time.sleep.side_effect = other_worker_finishes
        with patch("apps.content.wechat_token.time", fake_time):
            self.assertEqual(self.get(), "from-other-worker")
        self.assertEqual(calls(self.api, "fetch_token"), [])

    def test_tc_unit_376_expired_lock_can_be_taken_and_is_released(self):
        PlatformAccount.objects.filter(id=self.account.id).update(
            token_lock_until=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.get(), "fake-mp-token")
        self.assertEqual(len(calls(self.api, "fetch_token")), 1)
        self.assertIsNone(self.fresh().token_lock_until)

    def test_tc_unit_377_lock_released_when_fetch_fails(self):
        self.api.token_results = [WechatMpApiError("NETWORK", errmsg="boom")]
        with self.assertRaises(WechatTokenError) as ctx:
            self.get()
        self.assertEqual(ctx.exception.code, "NETWORK")
        row = self.fresh()
        self.assertIsNone(row.token_lock_until)
        self.assertIsNone(row.token_blob)

    def test_tc_unit_378_force_refresh_cooldown_and_after(self):
        """冷却：缓存令牌 == stale 且刷新不足 60 秒 → TOKEN_BUSY；超过后重取；他人已刷新则直接复用。"""
        self.api.token_results = [TokenResponse("t1", 7200), TokenResponse("t2", 7200)]
        self.assertEqual(self.get(now=self.t0), "t1")
        with self.assertRaises(WechatTokenError) as ctx:
            self.get(force=True, stale_token="t1", now=self.t0 + timedelta(seconds=59))
        self.assertEqual(ctx.exception.code, "TOKEN_BUSY")
        self.assertEqual(len(calls(self.api, "fetch_token")), 1)
        # 缓存令牌与 stale 不同 = 他人已刷新：无需请求，直接返回缓存
        self.assertEqual(self.get(force=True, stale_token="old-token",
                                  now=self.t0 + timedelta(seconds=10)), "t1")
        self.assertEqual(len(calls(self.api, "fetch_token")), 1)
        # 冷却过后强制刷新
        self.assertEqual(self.get(force=True, stale_token="t1",
                                  now=self.t0 + timedelta(seconds=61)), "t2")
        self.assertEqual(len(calls(self.api, "fetch_token")), 2)
        self.assertEqual(self.fresh().token_refreshed_at, self.t0 + timedelta(seconds=61))

    def test_tc_unit_379_credentials_overwritten_during_fetch_discards_result(self):
        """凭据在取令牌期间被覆盖（invalidate）：结果仅供本次调用，不入库。"""
        account_id = self.account.id

        class Racing(FakeWechatMpApi):
            def fetch_token(inner, **kwargs):
                WechatTokenService.invalidate(account_id)
                return TokenResponse("stale-from-old-secret", 7200)

        set_wechat_mp_api(Racing())
        self.assertEqual(self.get(), "stale-from-old-secret")
        row = self.fresh()
        self.assertIsNone(row.token_blob)
        self.assertIsNone(row.token_expires_at)
        self.assertIsNone(row.token_lock_until)


class ClassificationTests(TokenServiceBase):
    def test_tc_unit_380_classify_defaults_and_configured(self):
        """AC-127-03：40164（IP 不在白名单）单独分类，不当作认证失效；auth_errcodes 缺省为空。"""
        self.assertEqual(ContentSettings.get("content.wechat_mp.ip_errcodes"), [40164])
        self.assertEqual(ContentSettings.get("content.wechat_mp.auth_errcodes"), [])
        self.assertEqual(ContentSettings.get("content.wechat_mp.token_errcodes"), [])
        self.assertEqual(WechatTokenService.classify(40164), "IP_NOT_WHITELISTED")
        self.assertEqual(WechatTokenService.classify(88101), "UPSTREAM")
        self.assertEqual(WechatTokenService.classify(None), "UPSTREAM")
        ContentSettings.update({"content.wechat_mp.auth_errcodes": [88101]}, admin_id=1)
        self.assertEqual(WechatTokenService.classify(88101), "AUTH_REJECTED")
        self.assertEqual(WechatTokenService.classify(40164), "IP_NOT_WHITELISTED")
        # 同一 errcode 同时出现在两个清单时 IP 优先（设计：IP_NOT_WHITELISTED 优先）
        ContentSettings.update({"content.wechat_mp.auth_errcodes": [40164, 88101]}, admin_id=1)
        self.assertEqual(WechatTokenService.classify(40164), "IP_NOT_WHITELISTED")

    def test_tc_unit_381_fetch_errors_mapped_to_codes(self):
        ContentSettings.update({"content.wechat_mp.auth_errcodes": [88101]}, admin_id=1)
        cases = [
            (WechatMpApiError("ERRCODE", errcode=40164, errmsg="ip"), "IP_NOT_WHITELISTED", 40164),
            (WechatMpApiError("ERRCODE", errcode=88101, errmsg="auth"), "AUTH_REJECTED", 88101),
            (WechatMpApiError("ERRCODE", errcode=99999, errmsg="other"), "UPSTREAM", 99999),
            (WechatMpApiError("NETWORK", errmsg="timeout"), "NETWORK", None),
            (WechatMpApiError("HTTP", http_status=502), "UPSTREAM", None),
            (WechatMpApiError("BAD_RESPONSE"), "UPSTREAM", None),
        ]
        for error, code, errcode in cases:
            with self.subTest(code=code, kind=error.kind):
                self.api.reset()
                self.api.token_results = [error]
                with self.assertRaises(WechatTokenError) as ctx:
                    self.get()
                self.assertEqual((ctx.exception.code, ctx.exception.errcode), (code, errcode))
                self.assertIsNone(self.fresh().token_blob)   # 失败不写缓存
                self.assertIsNone(self.fresh().token_lock_until)

    def test_tc_unit_382_error_messages_never_contain_secret_or_token(self):
        """AC-127-02：错误消息 / 日志文本不含 appsecret 与令牌（SecretRedactor）。"""
        secret = CREDS["appsecret"]
        self.api.token_results = [WechatMpApiError(
            "ERRCODE", errcode=99999, errmsg=f"invalid secret={secret} appsecret {secret}")]
        with self.assertRaises(WechatTokenError) as ctx:
            self.get()
        self.assertNotIn(secret, ctx.exception.message)
        self.assertNotIn(secret, str(ctx.exception))
        self.assertLessEqual(len(ctx.exception.message), 200)
        # FakeWechatMpApi 自身也不记录 secret / 令牌值
        self.assertNotIn(secret, str(self.api.calls))
