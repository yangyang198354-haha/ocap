"""MOD-040：凭据保险库与脱敏（IFC-166/167）。"""
import base64
import json
import re
from typing import Iterable, Mapping

from django.conf import settings

try:  # cryptography 为新增依赖；缺失时视为未配置，不影响其他功能
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception:  # noqa: BLE001 - 部署缺依赖时降级为 NOT_CONFIGURED
    AESGCM = None
    InvalidTag = Exception


class CredentialVaultError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


_KEY_RE = re.compile(r"^[a-z_]{1,32}$")
_REDACT_QUERY_RE = re.compile(
    r"(?i)(access_token|api_key|secret|signature|authorization)=([^&\s\"']+)")
_BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+")
_TOKEN_PAIR_RE = re.compile(r"(?i)(access_token|api_key|secret|signature|authorization)=([^&\s\"']+)")


def _decode_key(value: str) -> bytes | None:
    if not value:
        return None
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception:  # noqa: BLE001
        return None
    return raw if len(raw) == 32 else None


class CredentialVault:
    @staticmethod
    def is_configured() -> bool:
        return _decode_key(settings.CONTENT_CRED_ENC_KEY) is not None and AESGCM is not None

    @staticmethod
    def encrypt(values: Mapping[str, str], *, context: str) -> bytes:
        key = _decode_key(settings.CONTENT_CRED_ENC_KEY)
        if key is None or AESGCM is None:
            raise CredentialVaultError("NOT_CONFIGURED")
        cleaned: dict[str, str] = {}
        for name, value in values.items():
            if not _KEY_RE.match(str(name)):
                raise ValueError("invalid key name")
            text = str(value)
            if not 1 <= len(text) <= 4096:
                raise ValueError("invalid value length")
            cleaned[str(name)] = text
        aad = ("ocap.content|" + context).encode("utf-8")
        nonce = __import__("os").urandom(12)
        ct = AESGCM(key).encrypt(nonce, json.dumps(cleaned, ensure_ascii=False).encode("utf-8"), aad)
        return b"\x01" + nonce + ct

    @staticmethod
    def decrypt(blob: bytes, *, context: str) -> dict[str, str]:
        if AESGCM is None or not blob or blob[:1] != b"\x01":
            raise CredentialVaultError("DECRYPT_FAILED")
        aad = ("ocap.content|" + context).encode("utf-8")
        for candidate in (settings.CONTENT_CRED_ENC_KEY, getattr(settings, "CONTENT_CRED_ENC_KEY_PREV", "")):
            key = _decode_key(candidate)
            if key is None:
                continue
            try:
                plain = AESGCM(key).decrypt(blob[1:13], blob[13:], aad)
                return json.loads(plain.decode("utf-8"))
            except (InvalidTag, ValueError, json.JSONDecodeError):
                continue
        raise CredentialVaultError("DECRYPT_FAILED")


class SecretRedactor:
    def __init__(self, secrets: Iterable[str]) -> None:
        self._secrets = [s for s in secrets if s and len(s) >= 6]

    def redact(self, text: str, *, max_len: int = 500) -> str:
        result = str(text or "")
        for secret in self._secrets:
            result = result.replace(secret, "***")
        result = _REDACT_QUERY_RE.sub(lambda m: f"{m.group(1)}=***", result)
        result = _BEARER_RE.sub("Bearer ***", result)
        return result[:max_len]


def redact_url(url: str) -> str:
    match = re.match(r"^([a-z]+)://([^/?#]+)([^?#]*)", str(url), re.I)
    if not match:
        return "***"
    return f"{match.group(1)}://{match.group(2)}{match.group(3)}"
