"""MOD-049：草稿箱适配器（IFC-180）。"""
from dataclasses import dataclass
from typing import Literal, Mapping, Protocol

import requests

from apps.content.conf import ContentSettings
from apps.content.vault import SecretRedactor, redact_url

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


@dataclass(frozen=True)
class DraftOutcome:
    status: str
    remote_ref: str = ""
    error_code: str = ""
    message: str = ""


class DraftAdapter(Protocol):
    platform: str
    label: str
    capability: Capability
    credential_fields: tuple[CredentialField, ...]
    unsupported_features: frozenset[str]

    def save_draft(self, payload: DraftPayload, credentials: Mapping[str, str]) -> DraftOutcome: ...


class WechatMpDraftAdapter:
    platform = "wechat_mp"
    label = "微信公众号"
    capability = "AUTO_DRAFT"
    credential_fields = (CredentialField("access_token", "访问令牌"),)
    unsupported_features = frozenset({"page_break", "video"})

    def save_draft(self, payload: DraftPayload, credentials: Mapping[str, str]) -> DraftOutcome:
        token = credentials.get("access_token", "")
        if not token:
            return DraftOutcome("FAILED", error_code="NO_CREDENTIALS", message="未配置访问令牌")
        timeout = int(ContentSettings.get("content.wechat_mp.timeout_seconds"))
        redact = SecretRedactor([token])
        url = "https://api.weixin.qq.com/cgi-bin/draft/add"
        try:
            response = requests.post(
                url, params={"access_token": token},
                json={"articles": [{"title": payload.title, "content": payload.html, "author": ""}]},
                timeout=timeout,
            )
        except requests.RequestException as exc:
            return DraftOutcome("FAILED", error_code="NETWORK",
                                message=redact.redact(f"{redact_url(url)} {exc}"))
        if response.status_code in {401, 403}:
            return DraftOutcome("AUTH_EXPIRED", error_code="AUTH_EXPIRED", message="认证已失效")
        try:
            data = response.json()
        except ValueError:
            return DraftOutcome("FAILED", error_code="UPSTREAM",
                                message=redact.redact(response.text[:200]))
        errcode = data.get("errcode") or 0
        auth_codes = set(ContentSettings.get("content.wechat_mp.auth_errcodes") or [])
        if errcode in auth_codes:
            return DraftOutcome("AUTH_EXPIRED", error_code="AUTH_EXPIRED", message="认证已失效")
        media_id = data.get("media_id")
        if media_id:
            return DraftOutcome("SAVED", remote_ref=str(media_id))
        message = redact.redact(str(data.get("errmsg") or "平台未返回草稿编号"))
        return DraftOutcome("FAILED", error_code="UPSTREAM", message=message[:200])


class ManualExportAdapter:
    capability = "MANUAL_EXPORT"
    credential_fields = (CredentialField("credential", "认证信息（预留）", required=False),)
    unsupported_features = frozenset()

    def __init__(self, platform: str, label: str):
        self.platform = platform
        self.label = label

    def save_draft(self, payload: DraftPayload, credentials: Mapping[str, str]) -> DraftOutcome:
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
