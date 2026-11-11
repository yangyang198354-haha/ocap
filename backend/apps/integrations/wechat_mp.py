"""MOD-063：公众号接口客户端（IFC-239，1.1.0 新增）。

仅封装取令牌与 draft/add 两个有出处的调用；封面/正文图片上传只有签名占位（[UNSOURCED]，Q-B1）。
测试只经 FakeWechatMpApi，不得走 HttpWechatMpApi。
"""
from dataclasses import dataclass
from typing import Literal, Protocol

import requests

from apps.content.vault import SecretRedactor, redact_url

TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"          # [CODE: backend/apps/integrations/wechat.py:98]
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"  # [P11: publisher/publishers.py:76]
ERRMSG_MAX = 200


@dataclass(frozen=True)
class TokenResponse:
    access_token: str
    expires_in: int = 7200   # 响应缺失时由调用方按 7200 处理 [CODE: wechat.py:103]


class WechatMpApiError(Exception):
    def __init__(self, kind: Literal["NETWORK", "HTTP", "BAD_RESPONSE", "ERRCODE"], *,
                 errcode: int | None = None, http_status: int | None = None, errmsg: str = ""):
        super().__init__(f"{kind}:{errcode if errcode is not None else http_status or ''}")
        self.kind = kind
        self.errcode = errcode
        self.http_status = http_status
        # 已脱敏、≤200 字符；错误描述字段名无出处 [UNSOURCED]（Q-B1 第 4 项），按 errmsg 读取，读不到为空串
        self.errmsg = (errmsg or "")[:ERRMSG_MAX]


@dataclass(frozen=True)
class DraftArticle:
    title: str
    content: str
    author: str = ""
    # TODO(IFC-239): [UNSOURCED] 封面字段名与是否必填（Q-B1 第 1 项）；None 时请求体不含该键，当前不会被发送
    thumb_media_id: str | None = None


class WechatMpApi(Protocol):
    def fetch_token(self, *, appid: str, secret: str, timeout_seconds: int) -> TokenResponse: ...

    def add_draft(self, *, access_token: str, article: DraftArticle, timeout_seconds: int) -> str: ...

    def upload_cover(self, *, access_token: str, file_path: str, content_type: str,
                     timeout_seconds: int) -> str: ...

    def upload_content_image(self, *, access_token: str, file_path: str, content_type: str,
                             timeout_seconds: int) -> str: ...


def _int_or_none(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class HttpWechatMpApi:
    @staticmethod
    def _error_from(data: dict, redactor: SecretRedactor) -> WechatMpApiError | None:
        errcode = _int_or_none(data.get("errcode")) or 0
        if not errcode:
            return None
        return WechatMpApiError("ERRCODE", errcode=errcode,
                                errmsg=redactor.redact(str(data.get("errmsg") or ""),
                                                       max_len=ERRMSG_MAX))

    @staticmethod
    def _network_error(url: str, exc: Exception, redactor: SecretRedactor) -> WechatMpApiError:
        return WechatMpApiError(
            "NETWORK", errmsg=redactor.redact(f"{redact_url(url)} {exc}", max_len=ERRMSG_MAX))

    def fetch_token(self, *, appid: str, secret: str, timeout_seconds: int) -> TokenResponse:
        redactor = SecretRedactor([secret])
        try:
            # [CODE: backend/apps/integrations/wechat.py:97-98] grant_type=client_credential、appid、secret
            response = requests.get(
                TOKEN_URL,
                params={"grant_type": "client_credential", "appid": appid, "secret": secret},
                timeout=timeout_seconds)
        except requests.RequestException as exc:
            raise self._network_error(TOKEN_URL, exc, redactor) from None
        try:
            data = response.json()
        except ValueError:
            data = None
        if not isinstance(data, dict):
            if response.status_code >= 400:
                raise WechatMpApiError("HTTP", http_status=response.status_code)
            raise WechatMpApiError("BAD_RESPONSE")
        error = self._error_from(data, redactor)
        if error is not None:
            raise error
        if response.status_code >= 400:
            raise WechatMpApiError("HTTP", http_status=response.status_code)
        token = data.get("access_token")   # [CODE: wechat.py:100]
        if not token or not isinstance(token, str):
            raise WechatMpApiError("BAD_RESPONSE")
        expires = _int_or_none(data.get("expires_in"))   # [CODE: wechat.py:103]
        return TokenResponse(token, expires if expires and expires > 0 else 7200)

    def add_draft(self, *, access_token: str, article: DraftArticle, timeout_seconds: int) -> str:
        redactor = SecretRedactor([access_token])
        item = {"title": article.title, "content": article.content, "author": article.author}
        # thumb_media_id 的请求字段名无出处（[UNSOURCED]，Q-B1），不发送
        try:
            # [P11: publisher/publishers.py:76-79] POST draft/add?access_token=…，JSON {"articles":[…]}
            response = requests.post(DRAFT_ADD_URL, params={"access_token": access_token},
                                     json={"articles": [item]}, timeout=timeout_seconds)
        except requests.RequestException as exc:
            raise self._network_error(DRAFT_ADD_URL, exc, redactor) from None
        try:
            data = response.json()
        except ValueError:
            data = None
        if response.status_code >= 400:   # [P11: publishers.py:81] HTTP 错误状态视为失败
            raise WechatMpApiError("HTTP", http_status=response.status_code)
        if not isinstance(data, dict):
            raise WechatMpApiError("BAD_RESPONSE")
        media_id = data.get("media_id")   # [P11: publishers.py:83-87] 含非空 media_id 即成功
        if media_id:
            return str(media_id)
        error = self._error_from(data, redactor)
        if error is not None:
            raise error
        raise WechatMpApiError("BAD_RESPONSE")

    def upload_cover(self, *, access_token: str, file_path: str, content_type: str,
                     timeout_seconds: int) -> str:
        # TODO(IFC-239): [UNSOURCED] 封面上传端点、请求/响应字段、格式与大小限制无出处（Q-B1 第 1 项）
        raise NotImplementedError("UNSOURCED: Q-B1")

    def upload_content_image(self, *, access_token: str, file_path: str, content_type: str,
                             timeout_seconds: int) -> str:
        # TODO(IFC-239): [UNSOURCED] 正文图片上传端点与响应图片地址字段无出处（Q-B1 第 2 项）
        raise NotImplementedError("UNSOURCED: Q-B1")


_api: WechatMpApi | None = None


def get_wechat_mp_api() -> WechatMpApi:
    global _api
    if _api is None:
        _api = HttpWechatMpApi()
    return _api


def set_wechat_mp_api(api: WechatMpApi | None) -> None:
    global _api
    _api = api
