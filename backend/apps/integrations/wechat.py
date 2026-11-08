"""微信开放接口适配（MOD-002 / IFC-010）。"""
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Literal, Protocol

from django.conf import settings

KIND = Literal["INVALID_CODE", "RATE_LIMITED", "BLOCKED", "UPSTREAM_DOWN", "NOT_CONFIGURED", "IP_NOT_WHITELISTED"]

ERRCODE_MAP = {40029: "INVALID_CODE", 45011: "RATE_LIMITED", 40226: "BLOCKED", 40164: "IP_NOT_WHITELISTED"}


class WeChatError(Exception):
    def __init__(self, kind: KIND, errcode: int | None = None, message: str = ""):
        self.kind = kind
        self.errcode = errcode
        super().__init__(message or kind)


@dataclass
class MiniappSession:
    openid: str
    unionid: str | None
    session_key: str


@dataclass
class WebAuthToken:
    access_token: str
    openid: str
    unionid: str | None


@dataclass
class WebUserInfo:
    nickname: str | None
    headimgurl: str | None


class WeChatClient(Protocol):
    def miniapp_code2session(self, js_code: str) -> MiniappSession: ...
    def stable_access_token(self) -> str: ...
    def miniapp_phone_by_code(self, code: str, openid: str | None = None) -> str: ...
    def web_exchange_code(self, code: str) -> WebAuthToken: ...
    def web_userinfo(self, access_token: str, openid: str) -> WebUserInfo: ...


def _get_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=settings.WECHAT_API_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # 网络错误统一映射
        raise WeChatError("UPSTREAM_DOWN", message=str(exc)) from exc


def _raise_for_errcode(data: dict) -> None:
    errcode = data.get("errcode") or 0
    if errcode:
        raise WeChatError(ERRCODE_MAP.get(int(errcode), "UPSTREAM_DOWN"), int(errcode))


class HttpWeChatClient:
    def __init__(self) -> None:
        self._token_cache: tuple[str, float] | None = None

    def _miniapp_credentials(self) -> tuple[str, str]:
        appid, secret = settings.WECHAT_MINIAPP_APPID, settings.WECHAT_MINIAPP_SECRET
        if not appid or not secret:
            raise WeChatError("NOT_CONFIGURED")
        return appid, secret

    def _web_credentials(self) -> tuple[str, str]:
        appid, secret = settings.WECHAT_WEB_APPID, settings.WECHAT_WEB_SECRET
        if not appid or not secret:
            raise WeChatError("NOT_CONFIGURED")
        return appid, secret

    def miniapp_code2session(self, js_code: str) -> MiniappSession:
        appid, secret = self._miniapp_credentials()
        query = urllib.parse.urlencode(
            {"appid": appid, "secret": secret, "js_code": js_code, "grant_type": "authorization_code"}
        )
        data = _get_json(f"https://api.weixin.qq.com/sns/jscode2session?{query}")
        _raise_for_errcode(data)
        if not data.get("openid"):
            raise WeChatError("UPSTREAM_DOWN")
        return MiniappSession(data["openid"], data.get("unionid"), data.get("session_key", ""))

    def stable_access_token(self) -> str:
        now = time.time()
        if self._token_cache and self._token_cache[1] > now + 300:
            return self._token_cache[0]
        appid, secret = self._miniapp_credentials()
        query = urllib.parse.urlencode({"grant_type": "client_credential", "appid": appid, "secret": secret})
        data = _get_json(f"https://api.weixin.qq.com/cgi-bin/token?{query}")
        _raise_for_errcode(data)
        token = data.get("access_token", "")
        if not token:
            raise WeChatError("UPSTREAM_DOWN")
        self._token_cache = (token, now + int(data.get("expires_in", 7200)))
        return token

    def miniapp_phone_by_code(self, code: str, openid: str | None = None) -> str:
        token = self.stable_access_token()
        body = json.dumps({"code": code}).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={urllib.parse.quote(token)}",
            data=body, headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=settings.WECHAT_API_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise WeChatError("UPSTREAM_DOWN", message=str(exc)) from exc
        _raise_for_errcode(data)
        phone = (data.get("phone_info") or {}).get("purePhoneNumber", "")
        if not phone:
            raise WeChatError("UPSTREAM_DOWN")
        return phone

    def web_exchange_code(self, code: str) -> WebAuthToken:
        appid, secret = self._web_credentials()
        query = urllib.parse.urlencode(
            {"appid": appid, "secret": secret, "code": code, "grant_type": "authorization_code"}
        )
        data = _get_json(f"https://api.weixin.qq.com/sns/oauth2/access_token?{query}")
        _raise_for_errcode(data)
        return WebAuthToken(data.get("access_token", ""), data.get("openid", ""), data.get("unionid"))

    def web_userinfo(self, access_token: str, openid: str) -> WebUserInfo:
        query = urllib.parse.urlencode({"access_token": access_token, "openid": openid})
        data = _get_json(f"https://api.weixin.qq.com/sns/userinfo?{query}")
        _raise_for_errcode(data)
        return WebUserInfo(data.get("nickname"), data.get("headimgurl"))


_client: WeChatClient | None = None


def get_wechat_client() -> WeChatClient:
    global _client
    if _client is None:
        _client = HttpWeChatClient()
    return _client


def set_wechat_client(client: WeChatClient | None) -> None:
    global _client
    _client = client
