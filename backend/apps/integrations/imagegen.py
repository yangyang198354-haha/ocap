"""MOD-047：文生图客户端（IFC-178）。"""
import time
from typing import Protocol

import requests

from apps.content.vault import SecretRedactor, redact_url

URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"


class ImageGenError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class ImageGenClient(Protocol):
    def generate(self, *, api_key: str, model: str, prompt: str, n: int,
                 size: str, timeout_seconds: int) -> list[str]: ...


class HttpImageGenClient:
    def generate(self, *, api_key: str, model: str, prompt: str, n: int,
                 size: str, timeout_seconds: int) -> list[str]:
        redact = SecretRedactor([api_key])
        payload = {"model": model, "prompt": prompt, "n": n, "size": size,
                   "response_format": "url"}
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = requests.post(
                    URL, headers={"Authorization": f"Bearer {api_key}"},
                    json=payload, timeout=timeout_seconds)
            except requests.RequestException as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(5)
                    continue
                raise ImageGenError("UPSTREAM", redact.redact(f"{redact_url(URL)} {exc}"))
            break
        else:  # pragma: no cover
            raise ImageGenError("UPSTREAM", redact.redact(str(last_error)))
        if response.status_code == 401:
            raise ImageGenError("AUTH", "认证失败")
        if response.status_code == 429:
            raise ImageGenError("QUOTA", "配额不足")
        if response.status_code == 400:
            digest = response.text[:300]
            if any(word in digest for word in ("content_filter", "sensitive", "审核", "违规")):
                raise ImageGenError("CONTENT_FILTER", "内容被平台审核拒绝")
            raise ImageGenError("UPSTREAM", redact.redact(digest))
        if response.status_code >= 400:
            raise ImageGenError("UPSTREAM", f"上游返回 {response.status_code}")
        try:
            urls = [item["url"] for item in response.json().get("data", []) if item.get("url")]
        except (ValueError, KeyError, TypeError):
            raise ImageGenError("BAD_RESPONSE", "返回格式不正确")
        if not urls:
            raise ImageGenError("BAD_RESPONSE", "未返回图片")
        return urls


_client = None


def get_imagegen_client() -> ImageGenClient:
    return _client or HttpImageGenClient()


def set_imagegen_client(client: ImageGenClient | None) -> None:
    global _client
    _client = client
