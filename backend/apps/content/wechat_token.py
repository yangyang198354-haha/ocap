"""MOD-062：公众号访问令牌服务（IFC-240，1.1.0 新增，ADR-060）。

用已保存的 AppID/AppSecret 换取令牌，加密缓存在 PlatformAccount，条件 UPDATE 单飞刷新，错误分类。
取令牌端点与字段 [CODE: backend/apps/integrations/wechat.py:97-103]（经 MOD-063）；
auth_errcodes / token_errcodes 取值无出处 [UNSOURCED]（Q-B1），缺省空。
"""
import time
from datetime import datetime, timedelta
from typing import Mapping

from django.db.models import Q
from django.utils import timezone

from apps.integrations.wechat_mp import WechatMpApiError, get_wechat_mp_api

from .conf import ContentSettings
from .models import PlatformAccount
from .vault import CredentialVault, CredentialVaultError, SecretRedactor

LOCK_EXTRA_SECONDS = 15      # 锁时长 = 请求超时 + 15 秒
LOCK_WAIT_SECONDS = 10.0     # 未抢到锁时最长等待
LOCK_POLL_SECONDS = 0.5
MESSAGE_MAX = 200


class WechatTokenError(Exception):
    def __init__(self, code: str, message: str = "", errcode: int | None = None):
        super().__init__(message or code)
        self.code = code            # NO_CREDENTIALS | AUTH_REJECTED | IP_NOT_WHITELISTED | UPSTREAM | NETWORK | TOKEN_BUSY
        self.errcode = errcode
        self.message = (message or code)[:MESSAGE_MAX]


def _context(account_id: int) -> str:
    return f"content_platformaccount_token|{account_id}"


def _cached(row: PlatformAccount, now: datetime, margin: int) -> tuple[str | None, bool]:
    """返回 (缓存令牌或 None, 是否仍有效)；解密失败按未命中处理，不抛错。"""
    if not row.token_blob:
        return None, False
    try:
        token = CredentialVault.decrypt(bytes(row.token_blob), context=_context(row.id)).get("access_token")
    except CredentialVaultError:
        return None, False
    if not token:
        return None, False
    valid = bool(row.token_expires_at and row.token_expires_at - timedelta(seconds=margin) > now)
    return token, valid


class WechatTokenService:
    @staticmethod
    def classify(errcode: int | None) -> str:
        if errcode is not None:
            if errcode in set(ContentSettings.get("content.wechat_mp.ip_errcodes") or []):
                return "IP_NOT_WHITELISTED"
            if errcode in set(ContentSettings.get("content.wechat_mp.auth_errcodes") or []):
                return "AUTH_REJECTED"
        return "UPSTREAM"

    @staticmethod
    def invalidate(account_id: int) -> None:
        PlatformAccount.objects.filter(id=account_id).update(
            token_blob=None, token_expires_at=None, token_refreshed_at=None, token_lock_until=None)

    @staticmethod
    def get_token(account_id: int, credentials: Mapping[str, str], *, force: bool = False,
                  stale_token: str | None = None, now: datetime | None = None) -> str:
        return WechatTokenService.get_token_ex(
            account_id, credentials, force=force, stale_token=stale_token, now=now)[0]

    @staticmethod
    def get_token_ex(account_id: int, credentials: Mapping[str, str], *, force: bool = False,
                     stale_token: str | None = None,
                     now: datetime | None = None) -> tuple[str, bool]:
        """同 get_token，另返回"本次是否经网络新取"（适配器据此判断令牌类错误是否值得重取）。"""
        row = PlatformAccount.objects.filter(id=account_id).first()
        if row is None or row.platform != "wechat_mp":
            raise ValueError("account must exist and be a wechat_mp account")
        appid = (credentials or {}).get("appid") or ""
        secret = (credentials or {}).get("appsecret") or ""
        if not appid or not secret:
            raise WechatTokenError("NO_CREDENTIALS", "未配置 AppID 或 AppSecret")

        now = now or timezone.now()
        margin = int(ContentSettings.get("content.wechat_mp.token_margin_seconds"))
        cooldown = int(ContentSettings.get("content.wechat_mp.refresh_cooldown_seconds"))
        timeout = int(ContentSettings.get("content.wechat_mp.timeout_seconds"))

        def reusable(current: PlatformAccount) -> str | None:
            token, valid = _cached(current, now, margin)
            if token is None or not valid:
                return None
            if force and token == stale_token:
                return None
            return token

        # 命中缓存 / 强制刷新时他人已刷新
        token = reusable(row)
        if token is not None:
            return token, False
        if force and stale_token is not None:
            cached, _ = _cached(row, now, margin)
            if cached == stale_token and row.token_refreshed_at \
                    and (now - row.token_refreshed_at).total_seconds() < cooldown:
                raise WechatTokenError("TOKEN_BUSY", "令牌刷新冷却中，请稍后重试")

        # 抢锁：条件 UPDATE，影响行数 1 表示抢到
        lock_value = now + timedelta(seconds=timeout + LOCK_EXTRA_SECONDS)
        got = PlatformAccount.objects.filter(id=account_id).filter(
            Q(token_lock_until__isnull=True) | Q(token_lock_until__lt=now)
        ).update(token_lock_until=lock_value)
        if not got:
            deadline = time.monotonic() + LOCK_WAIT_SECONDS
            while time.monotonic() < deadline:
                time.sleep(LOCK_POLL_SECONDS)
                current = PlatformAccount.objects.filter(id=account_id).first()
                if current is None:
                    break
                token = reusable(current)
                if token is not None:
                    return token, False
            raise WechatTokenError("TOKEN_BUSY", "令牌正在被其他任务刷新，请稍后重试")

        try:
            # 持锁后再确认一次：他人可能已在我们读取与抢锁之间刷新
            current = PlatformAccount.objects.filter(id=account_id).first()
            if current is not None:
                token = reusable(current)
                if token is not None:
                    return token, False
            try:
                response = get_wechat_mp_api().fetch_token(
                    appid=appid, secret=secret, timeout_seconds=timeout)
            except WechatMpApiError as exc:
                raise WechatTokenService._map_error(exc, secret) from None
            WechatTokenService._store(account_id, lock_value, response.access_token,
                                      response.expires_in, now)
            return response.access_token, True
        finally:
            # 任何路径都释放锁；条件不成立（已被 invalidate 或已在 _store 中释放）时为 no-op
            PlatformAccount.objects.filter(id=account_id, token_lock_until=lock_value).update(
                token_lock_until=None)

    @staticmethod
    def _store(account_id: int, lock_value: datetime, access_token: str, expires_in: int,
               now: datetime) -> None:
        try:
            blob = CredentialVault.encrypt({"access_token": access_token},
                                           context=_context(account_id))
        except CredentialVaultError:
            return    # 无法加密则不缓存，令牌只供本次调用使用
        seconds = expires_in if expires_in and expires_in > 0 else 7200   # [CODE: wechat.py:103]
        # 条件不成立（凭据在取令牌期间被覆盖并 invalidate）时丢弃结果，不入库
        PlatformAccount.objects.filter(id=account_id, token_lock_until=lock_value).update(
            token_blob=blob, token_expires_at=now + timedelta(seconds=seconds),
            token_refreshed_at=now, token_lock_until=None)

    @staticmethod
    def _map_error(exc: WechatMpApiError, secret: str) -> WechatTokenError:
        redactor = SecretRedactor([secret])
        if exc.kind == "ERRCODE":
            code = WechatTokenService.classify(exc.errcode)
            text = f"errcode={exc.errcode}" + (f" {exc.errmsg}" if exc.errmsg else "")
            return WechatTokenError(code, redactor.redact(text, max_len=MESSAGE_MAX), exc.errcode)
        if exc.kind == "NETWORK":
            return WechatTokenError("NETWORK", redactor.redact(exc.errmsg or "网络错误",
                                                               max_len=MESSAGE_MAX))
        detail = f"HTTP {exc.http_status}" if exc.kind == "HTTP" else "响应格式异常"
        return WechatTokenError("UPSTREAM", detail)
