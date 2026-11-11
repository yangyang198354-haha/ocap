"""MOD-048：即梦视频生成客户端（IFC-179）。"""
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, Sequence
from urllib.parse import urlencode

import requests

from apps.content.vault import SecretRedactor

HOST = "visual.volcengineapi.com"
SERVICE = "visual"
REGION = "cn-north-1"
VERSION = "2024-05-01"


@dataclass(frozen=True)
class VideoScene:
    scene_index: int
    scene_prompt: str
    narration: str
    duration_sec: int
    transition: str


@dataclass(frozen=True)
class VideoTaskStatus:
    task_id: str
    status: str
    progress: int
    clip_urls: tuple[str, ...]
    error: str | None = None


class VideoGenError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class VideoGenClient(Protocol):
    def submit(self, *, access_key: str, secret_key: str, scenes: Sequence[VideoScene]) -> str: ...
    def poll(self, *, access_key: str, secret_key: str, task_id: str) -> VideoTaskStatus: ...


def _sign(secret_key: str, date_stamp: str) -> bytes:
    k_date = hmac.new(secret_key.encode(), date_stamp.encode(), hashlib.sha256).digest()
    k_region = hmac.new(k_date, REGION.encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, SERVICE.encode(), hashlib.sha256).digest()
    return hmac.new(k_service, b"request", hashlib.sha256).digest()


def _request(access_key: str, secret_key: str, action: str, body: dict, timeout: int) -> dict:
    now = datetime.now(timezone.utc)
    x_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    query = urlencode({"Action": action, "Version": VERSION})
    canonical_headers = f"content-type:application/json\nhost:{HOST}\nx-date:{x_date}\n"
    signed_headers = "content-type;host;x-date"
    canonical = "\n".join([
        "POST", "/", query, canonical_headers, signed_headers,
        hashlib.sha256(payload).hexdigest(),
    ])
    scope = f"{date_stamp}/{REGION}/{SERVICE}/request"
    string_to_sign = "\n".join([
        "HMAC-SHA256", x_date, scope, hashlib.sha256(canonical.encode()).hexdigest(),
    ])
    signature = hmac.new(_sign(secret_key, date_stamp), string_to_sign.encode(), hashlib.sha256).hexdigest()
    authorization = (f"HMAC-SHA256 Credential={access_key}/{scope}, "
                     f"SignedHeaders={signed_headers}, Signature={signature}")
    redact = SecretRedactor([secret_key, access_key])
    try:
        response = requests.post(
            f"https://{HOST}/?{query}",
            data=payload,
            headers={"Content-Type": "application/json", "Host": HOST,
                     "X-Date": x_date, "Authorization": authorization},
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise VideoGenError("TIMEOUT", redact.redact(str(exc)))
    except requests.RequestException as exc:
        raise VideoGenError("UPSTREAM", redact.redact(str(exc)))
    if response.status_code in {401, 403}:
        raise VideoGenError("AUTH", "认证失败")
    if response.status_code >= 400:
        raise VideoGenError("UPSTREAM", f"上游返回 {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise VideoGenError("BAD_RESPONSE", "返回格式不正确") from exc


class HttpVideoGenClient:
    def submit(self, *, access_key: str, secret_key: str, scenes: Sequence[VideoScene]) -> str:
        body = {
            "req_key": "i2v_multi_scene",
            "scenes": [{"prompt": s.scene_prompt, "narration": s.narration,
                        "duration": s.duration_sec, "transition": s.transition} for s in scenes],
        }
        data = _request(access_key, secret_key, "CVSubmitTask", body, 30)
        task_id = (data.get("data") or {}).get("task_id") or data.get("task_id")
        if not task_id:
            raise VideoGenError("BAD_RESPONSE", "未返回任务号")
        return str(task_id)

    def poll(self, *, access_key: str, secret_key: str, task_id: str) -> VideoTaskStatus:
        data = _request(access_key, secret_key, "CVQueryTask", {"task_id": task_id}, 30)
        payload = data.get("data") or {}
        raw = str(payload.get("status") or "pending")
        mapping = {"queue": "pending", "processing": "processing",
                   "succeed": "completed", "failed": "failed"}
        status = mapping.get(raw, "pending")
        urls = tuple(payload.get("video_urls") or ())
        try:
            progress = int(payload.get("progress") or 0)
        except (TypeError, ValueError):
            progress = 0
        return VideoTaskStatus(task_id=task_id, status=status, progress=progress,
                               clip_urls=urls, error=payload.get("error_message"))


_client = None


def get_videogen_client() -> VideoGenClient:
    return _client or HttpVideoGenClient()


def set_videogen_client(client: VideoGenClient | None) -> None:
    global _client
    _client = client
