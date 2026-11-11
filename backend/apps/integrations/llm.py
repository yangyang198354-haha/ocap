"""MOD-047：LLM 客户端（IFC-177）。测试一律替换为 FakeLlmClient。"""
import json
from dataclasses import dataclass
from typing import Literal, Protocol, Sequence

import requests

from apps.content.vault import SecretRedactor, redact_url

BASES = {
    "LLM_DEEPSEEK": "https://api.deepseek.com/v1",
    "LLM_VOLCANO": "https://ark.cn-beijing.volces.com/api/v3",
}


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


class LlmError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class LlmTestResult:
    ok: bool
    error_code: str = ""


class LlmClient(Protocol):
    def test(self, *, service_type: str, api_key: str) -> LlmTestResult: ...
    def generate(self, *, service_type: str, api_key: str, model: str,
                 messages: Sequence[ChatMessage], max_tokens: int,
                 temperature: float, timeout_seconds: int) -> str: ...


class HttpLlmClient:
    def test(self, *, service_type: str, api_key: str) -> LlmTestResult:
        try:
            response = requests.get(f"{BASES[service_type]}/models",
                                    headers={"Authorization": f"Bearer {api_key}"},
                                    timeout=10)
        except requests.RequestException:
            return LlmTestResult(False, "UNREACHABLE")
        if response.status_code == 200:
            return LlmTestResult(True, "")
        if response.status_code == 401:
            return LlmTestResult(False, "KEY_INVALID")
        if response.status_code == 429:
            return LlmTestResult(False, "QUOTA_EXCEEDED")
        return LlmTestResult(False, "UNREACHABLE")

    def generate(self, *, service_type: str, api_key: str, model: str,
                 messages: Sequence[ChatMessage], max_tokens: int,
                 temperature: float, timeout_seconds: int) -> str:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        redact = SecretRedactor([api_key])
        parts: list[str] = []
        try:
            response = requests.post(
                f"{BASES[service_type]}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload, stream=True, timeout=(5, timeout_seconds),
            )
        except requests.RequestException as exc:
            raise LlmError("UNREACHABLE", redact.redact(f"{redact_url(BASES[service_type])} {exc}"))
        if response.status_code == 401:
            raise LlmError("KEY_INVALID", "API 密钥无效")
        if response.status_code == 429:
            raise LlmError("QUOTA_EXCEEDED", "模型配额不足")
        if response.status_code >= 400:
            raise LlmError("UPSTREAM_ERROR", f"上游返回 {response.status_code}")
        try:
            for raw in response.iter_lines(decode_unicode=True):
                if not raw or not raw.startswith("data:"):
                    continue
                data = raw[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content") or ""
                except (KeyError, IndexError, json.JSONDecodeError):
                    continue
                parts.append(delta)
        except requests.RequestException as exc:
            raise LlmError("UNREACHABLE", redact.redact(str(exc)))
        text = "".join(parts).strip()
        if not text:
            raise LlmError("EMPTY_RESPONSE", "模型返回空内容")
        return text


_client = None


def get_llm_client() -> LlmClient:
    return _client or HttpLlmClient()


def set_llm_client(client: LlmClient | None) -> None:
    global _client
    _client = client
