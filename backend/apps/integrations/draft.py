"""MOD-049：草稿箱适配器（IFC-180）。

1.1.0（ADR-060/061）：公众号适配器凭据改为 AppID/AppSecret，令牌由 WechatTokenService 获取并缓存，
所有 HTTP 经 WechatMpApi（不再直接 import requests）。封面/正文图片上传依赖 [UNSOURCED] 接口（Q-B1），
开关缺省关闭。
"""
import os
from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Protocol

from django.conf import settings

from apps.content.conf import ContentSettings
from apps.content.vault import SecretRedactor
from apps.content.wechat_token import WechatTokenError, WechatTokenService
from apps.integrations.wechat_mp import DraftArticle, WechatMpApiError, get_wechat_mp_api

Capability = Literal["AUTO_DRAFT", "MANUAL_EXPORT"]
PLATFORMS = ("wechat_mp", "xiaohongshu", "toutiao")


@dataclass(frozen=True)
class CredentialField:
    key: str
    label: str
    secret: bool = True
    required: bool = True


@dataclass(frozen=True)
class MediaFile:
    media_id: str
    path: str
    content_type: str
    media_type: str
    name: str


@dataclass(frozen=True)
class DraftPayload:
    title: str
    html: str
    text: str
    media: tuple[MediaFile, ...] = ()
    # 1.1.0（ADR-061）：以 {mediaId: 替换后的图片地址} 重新渲染 inline HTML，仅 upload_content_images 开启时使用
    html_for: Callable[[Mapping[str, str]], str] | None = None
    # 1.1.0：封面候选 = 文档中按出现顺序的第一张图片；无图片为 None
    cover: MediaFile | None = None


@dataclass(frozen=True)
class DraftOutcome:
    status: str
    remote_ref: str = ""
    # 空串=成功；NO_CREDENTIALS | AUTH_EXPIRED | IP_NOT_WHITELISTED | TOKEN_BUSY | UPSTREAM | NETWORK
    #   | COVER_REQUIRED | IMAGE_UPLOAD_FAILED（后两项依赖 Q-B1，开关关闭时不会产生）
    error_code: str = ""
    message: str = ""


class DraftAdapter(Protocol):
    platform: str
    label: str
    capability: Capability
    credential_fields: tuple[CredentialField, ...]
    unsupported_features: frozenset[str]

    def save_draft(self, payload: DraftPayload, credentials: Mapping[str, str], *,
                   account_id: int | None = None) -> DraftOutcome: ...


def _abs_path(media: MediaFile) -> str:
    return os.path.join(settings.MEDIA_ROOT, media.path)


class WechatMpDraftAdapter:
    platform = "wechat_mp"
    label = "微信公众号"
    capability = "AUTO_DRAFT"
    credential_fields = (CredentialField("appid", "AppID"), CredentialField("appsecret", "AppSecret"))
    unsupported_features = frozenset({"page_break", "video"})

    # ---- 令牌 ----
    @staticmethod
    def _token(account_id, credentials, *, force=False, stale_token=None) -> tuple[str, bool]:
        if account_id is not None:
            return WechatTokenService.get_token_ex(
                account_id, credentials, force=force, stale_token=stale_token)
        # 无账户编号（直接调用）：不缓存，直接换取
        timeout = int(ContentSettings.get("content.wechat_mp.timeout_seconds"))
        try:
            response = get_wechat_mp_api().fetch_token(
                appid=credentials.get("appid", ""), secret=credentials.get("appsecret", ""),
                timeout_seconds=timeout)
        except WechatMpApiError as exc:
            raise WechatTokenService._map_error(exc, credentials.get("appsecret", "")) from None
        return response.access_token, True

    @staticmethod
    def _token_failure(exc: WechatTokenError) -> DraftOutcome:
        if exc.code == "AUTH_REJECTED":
            # 取令牌时凭据被拒（errcode ∈ auth_errcodes，取值无出处 [UNSOURCED]，Q-B1）→ 认证失效
            return DraftOutcome("AUTH_EXPIRED", error_code="AUTH_EXPIRED",
                                message="认证已失效，请重新认证")
        return DraftOutcome("FAILED", error_code=exc.code, message=exc.message)

    # ---- 草稿接口错误分类 ----
    @staticmethod
    def _is_token_error(exc: WechatMpApiError, *, token_was_fresh: bool) -> bool:
        if exc.kind == "HTTP" and exc.http_status in {401, 403}:
            return True
        if exc.kind != "ERRCODE":
            return False
        if WechatTokenService.classify(exc.errcode) == "IP_NOT_WHITELISTED":
            return False   # IP 白名单问题刷新令牌无法修复
        configured = set(ContentSettings.get("content.wechat_mp.token_errcodes") or [])
        if configured:
            return exc.errcode in configured
        # token_errcodes 为空（[UNSOURCED]，Q-B1）时的保守兜底（ADR-060 第 5 条）：
        # 令牌取自缓存（非本次新取）且响应为明确错误（有非零 errcode、无 media_id）才重取一次
        return not token_was_fresh

    @staticmethod
    def _failure(exc: WechatMpApiError, redactor: SecretRedactor) -> DraftOutcome:
        if exc.kind == "NETWORK":
            return DraftOutcome("FAILED", error_code="NETWORK",
                                message=redactor.redact(exc.errmsg or "网络错误", max_len=200))
        if exc.kind == "ERRCODE":
            if WechatTokenService.classify(exc.errcode) == "IP_NOT_WHITELISTED":
                return DraftOutcome("FAILED", error_code="IP_NOT_WHITELISTED",
                                    message="服务器出口 IP 未加入公众号 IP 白名单")
            text = f"errcode={exc.errcode}" + (f" {exc.errmsg}" if exc.errmsg else "")
            return DraftOutcome("FAILED", error_code="UPSTREAM", message=redactor.redact(text, max_len=200))
        if exc.kind == "HTTP":
            return DraftOutcome("FAILED", error_code="UPSTREAM", message=f"HTTP {exc.http_status}")
        return DraftOutcome("FAILED", error_code="UPSTREAM", message="平台未返回草稿编号")

    def save_draft(self, payload: DraftPayload, credentials: Mapping[str, str], *,
                   account_id: int | None = None) -> DraftOutcome:
        if not credentials.get("appid") or not credentials.get("appsecret"):
            return DraftOutcome("FAILED", error_code="NO_CREDENTIALS", message="未配置 AppID 或 AppSecret")
        timeout = int(ContentSettings.get("content.wechat_mp.timeout_seconds"))
        api = get_wechat_mp_api()
        try:
            token, fresh = self._token(account_id, credentials)
        except WechatTokenError as exc:
            return self._token_failure(exc)
        redactor = SecretRedactor([credentials.get("appsecret", ""), token])

        # ADR-061：两个开关缺省关闭；对应接口 [UNSOURCED]（Q-B1），HttpWechatMpApi 中未实现
        thumb = None
        if ContentSettings.get("content.wechat_mp.require_cover") and payload.cover is None:
            return DraftOutcome("FAILED", error_code="COVER_REQUIRED", message="内容中没有可用作封面的图片")
        if ContentSettings.get("content.wechat_mp.upload_cover") and payload.cover is not None:
            try:
                thumb = api.upload_cover(access_token=token, file_path=_abs_path(payload.cover),
                                         content_type=payload.cover.content_type,
                                         timeout_seconds=timeout)
            except (WechatMpApiError, NotImplementedError) as exc:
                return DraftOutcome("FAILED", error_code="IMAGE_UPLOAD_FAILED",
                                    message=redactor.redact(f"封面上传失败 {exc}", max_len=200))
        content = payload.html
        if ContentSettings.get("content.wechat_mp.upload_content_images"):
            mapping: dict[str, str] = {}
            for media in payload.media:
                if media.media_type != "IMAGE":
                    continue
                try:
                    mapping[media.media_id] = api.upload_content_image(
                        access_token=token, file_path=_abs_path(media),
                        content_type=media.content_type, timeout_seconds=timeout)
                except (WechatMpApiError, NotImplementedError) as exc:
                    return DraftOutcome("FAILED", error_code="IMAGE_UPLOAD_FAILED",
                                        message=redactor.redact(f"正文图片上传失败 {exc}", max_len=200))
            if payload.html_for is not None:
                content = payload.html_for(mapping)

        article = DraftArticle(title=payload.title, content=content, author="", thumb_media_id=thumb)
        try:
            media_id = api.add_draft(access_token=token, article=article, timeout_seconds=timeout)
            return DraftOutcome("SAVED", remote_ref=media_id)
        except WechatMpApiError as exc:
            first = exc
        # 令牌类错误：强制刷新并重发至多一次；超时/连接中断（NETWORK）不重发，避免重复草稿（ADR-054）
        if account_id is None or not self._is_token_error(first, token_was_fresh=fresh):
            return self._failure(first, redactor)
        try:
            token2, _ = self._token(account_id, credentials, force=True, stale_token=token)
        except WechatTokenError as exc:
            return self._token_failure(exc)
        redactor = SecretRedactor([credentials.get("appsecret", ""), token, token2])
        try:
            media_id = api.add_draft(access_token=token2, article=article, timeout_seconds=timeout)
            return DraftOutcome("SAVED", remote_ref=media_id)
        except WechatMpApiError as exc:
            return self._failure(exc, redactor)


class ManualExportAdapter:
    capability = "MANUAL_EXPORT"
    credential_fields = (CredentialField("credential", "认证信息（预留）", required=False),)
    unsupported_features = frozenset()

    def __init__(self, platform: str, label: str):
        self.platform = platform
        self.label = label

    def save_draft(self, payload: DraftPayload, credentials: Mapping[str, str], *,
                   account_id: int | None = None) -> DraftOutcome:
        raise NotImplementedError


_ADAPTERS: dict[str, DraftAdapter] = {
    "wechat_mp": WechatMpDraftAdapter(),
    "xiaohongshu": ManualExportAdapter("xiaohongshu", "小红书"),
    "toutiao": ManualExportAdapter("toutiao", "今日头条"),
}


def get_draft_adapter(platform: str) -> DraftAdapter:
    adapter = _ADAPTERS.get(platform)
    if adapter is None:
        raise KeyError(platform)
    return adapter


def set_draft_adapter(platform: str, adapter: DraftAdapter | None) -> None:
    if adapter is None:
        _ADAPTERS.pop(platform, None)
    else:
        _ADAPTERS[platform] = adapter
