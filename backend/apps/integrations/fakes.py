"""测试替身（画像 P11-3）：内存记录发送内容、可编程失败。"""
from .email import EmailSendError
from .sms import SmsSendError
from .wechat import MiniappSession, WebAuthToken, WebUserInfo, WeChatError


class FakeSmsGateway:
    _shared: "FakeSmsGateway | None" = None

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []
        self.fail_kind: str | None = None

    @classmethod
    def shared(cls) -> "FakeSmsGateway":
        if cls._shared is None:
            cls._shared = cls()
        return cls._shared

    def reset(self) -> None:
        self.sent.clear()
        self.fail_kind = None

    def send_code(self, phone: str, code: str, purpose: str) -> None:
        if self.fail_kind:
            raise SmsSendError(self.fail_kind, "FAKE", retryable=self.fail_kind == "UPSTREAM")
        self.sent.append((phone, code, purpose))


class FakeEmailGateway:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str, int]] = []
        self.fail = False
        self.reset()

    def reset(self) -> None:
        self.sent.clear()
        self.fail = False

    def send_code(self, email: str, code: str, purpose: str, ttl_minutes: int) -> None:
        if self.fail:
            raise EmailSendError("fake failure")
        self.sent.append((email, code, purpose, ttl_minutes))


class FakeWeChatClient:
    def __init__(self) -> None:
        self.sessions: dict[str, MiniappSession] = {}
        self.phones: dict[str, str] = {}
        self.fail_kind: str | None = None

    def miniapp_code2session(self, js_code: str) -> MiniappSession:
        if self.fail_kind:
            raise WeChatError(self.fail_kind)
        if js_code in self.sessions:
            return self.sessions[js_code]
        return MiniappSession(openid=f"openid_{js_code}", unionid=None, session_key="session")

    def stable_access_token(self) -> str:
        return "fake-token"

    def miniapp_phone_by_code(self, code: str, openid: str | None = None) -> str:
        if self.fail_kind:
            raise WeChatError(self.fail_kind)
        return self.phones.get(code, "13800000000")

    def web_exchange_code(self, code: str) -> WebAuthToken:
        if self.fail_kind:
            raise WeChatError(self.fail_kind)
        return WebAuthToken(access_token="fake", openid=f"webopenid_{code}", unionid=None)

    def web_userinfo(self, access_token: str, openid: str) -> WebUserInfo:
        return WebUserInfo(nickname="微信用户", headimgurl=None)
