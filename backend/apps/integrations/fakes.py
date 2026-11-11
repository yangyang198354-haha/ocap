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


class FakeLlmClient:
    def __init__(self) -> None:
        self.responses: list[str] = ["示例生成文案"]
        self.fail_code: str | None = None
        self.test_result = None
        self.calls: list[dict] = []

    def reset(self) -> None:
        self.responses = ["示例生成文案"]
        self.fail_code = None
        self.test_result = None
        self.calls.clear()

    def test(self, *, service_type, api_key):
        from .llm import LlmTestResult
        self.calls.append({"kind": "test", "service_type": service_type, "has_key": bool(api_key)})
        if self.test_result is not None:
            return self.test_result
        return LlmTestResult(self.fail_code is None, self.fail_code or "")

    def generate(self, *, service_type, api_key, model, messages,
                 max_tokens, temperature, timeout_seconds):
        from .llm import LlmError
        self.calls.append({"kind": "generate", "service_type": service_type,
                           "model": model, "has_key": bool(api_key),
                           "messages": [m.content for m in messages]})
        if self.fail_code:
            raise LlmError(self.fail_code, "模拟失败")
        if not self.responses:
            from .llm import LlmError as _Err
            raise _Err("EMPTY_RESPONSE", "模型返回空内容")
        return self.responses.pop(0)


class FakeImageGenClient:
    def __init__(self) -> None:
        self.urls: list[str] = ["https://example.com/image.png"]
        self.fail_code: str | None = None
        self.calls: list[dict] = []

    def reset(self) -> None:
        self.urls = ["https://example.com/image.png"]
        self.fail_code = None
        self.calls.clear()

    def generate(self, *, api_key, model, prompt, n, size, timeout_seconds):
        from .imagegen import ImageGenError
        self.calls.append({"model": model, "prompt": prompt, "n": n,
                           "size": size, "has_key": bool(api_key)})
        if self.fail_code:
            raise ImageGenError(self.fail_code, "模拟失败")
        return list(self.urls)


class FakeVideoGenClient:
    def __init__(self) -> None:
        self.submit_task_id = "fake-task"
        self.statuses: list = []
        self.fail_on: str | None = None
        self.calls: list[dict] = []

    def reset(self) -> None:
        self.submit_task_id = "fake-task"
        self.statuses = []
        self.fail_on = None
        self.calls.clear()

    def submit(self, *, access_key, secret_key, scenes):
        from .videogen import VideoGenError
        self.calls.append({"kind": "submit", "scenes": len(scenes),
                           "has_key": bool(access_key and secret_key)})
        if self.fail_on == "submit":
            raise VideoGenError("UPSTREAM", "模拟提交失败")
        return self.submit_task_id

    def poll(self, *, access_key, secret_key, task_id):
        from .videogen import VideoGenError, VideoTaskStatus
        self.calls.append({"kind": "poll", "task_id": task_id})
        if self.fail_on == "poll":
            raise VideoGenError("UPSTREAM", "模拟查询失败")
        if self.statuses:
            return self.statuses.pop(0)
        return VideoTaskStatus(task_id=task_id, status="completed", progress=100,
                               clip_urls=("https://example.com/clip.mp4",))


class FakeDraftAdapter:
    def __init__(self, platform: str, capability: str = "AUTO_DRAFT", outcomes=None,
                 label: str = ""):
        from .draft import CredentialField
        self.platform = platform
        self.label = label or platform
        self.capability = capability
        self.credential_fields = (CredentialField("access_token", "访问令牌"),)
        self.unsupported_features = frozenset()
        self.credentials_fields = ()
        self.outcomes = list(outcomes or [])
        self.received: list = []

    def reset(self) -> None:
        self.outcomes = []
        self.received = []

    def save_draft(self, payload, credentials):
        from .draft import DraftOutcome
        self.received.append(payload)
        if self.outcomes:
            return self.outcomes.pop(0)
        return DraftOutcome("SAVED", remote_ref="fake-ref")


class FakeRemoteFetcher:
    def __init__(self) -> None:
        self.payloads: dict[str, bytes] = {}
        self.reset()

    def reset(self) -> None:
        self.payloads = {}

    def fetch(self, url: str, *, max_bytes: int, timeout_seconds: int):
        from apps.content.media import MediaFetchError
        if url not in self.payloads:
            raise MediaFetchError("HTTP")
        data = self.payloads[url]
        if len(data) > max_bytes:
            raise MediaFetchError("TOO_LARGE")
        yield data
