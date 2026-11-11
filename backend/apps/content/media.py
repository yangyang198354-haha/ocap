"""MOD-044：素材库（IFC-173/174）。"""
import hashlib
import ipaddress
import os
import shutil
import socket
import uuid
from datetime import datetime, timedelta
from typing import Iterable, Iterator, Protocol
from urllib.parse import urlparse

from django.conf import settings
from django.core import signing
from django.http import FileResponse, HttpResponse
from django.utils import timezone

from apps.core.errors import ApiError, NotFound

from .conf import ContentSettings
from .models import ContentPost, ContentPostMedia, MediaItem

MAGIC = {"jpg": [b"\xff\xd8\xff"], "jpeg": [b"\xff\xd8\xff"],
         "png": [b"\x89PNG\r\n\x1a\n"]}
SIGN_SALT = "ocap.content.media"


class MediaFetchError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class RemoteFetcher(Protocol):
    def fetch(self, url: str, *, max_bytes: int, timeout_seconds: int) -> Iterator[bytes]: ...


class HttpRemoteFetcher:
    def fetch(self, url: str, *, max_bytes: int, timeout_seconds: int) -> Iterator[bytes]:
        import requests

        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise MediaFetchError("SCHEME")
        try:
            addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, 443)}
        except OSError as exc:
            raise MediaFetchError("HTTP") from exc
        for addr in addresses:
            ip = ipaddress.ip_address(addr)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise MediaFetchError("PRIVATE_ADDRESS")
        try:
            response = requests.get(url, timeout=timeout_seconds, stream=True, allow_redirects=False)
        except requests.Timeout as exc:
            raise MediaFetchError("TIMEOUT") from exc
        except requests.RequestException as exc:
            raise MediaFetchError("HTTP") from exc
        if response.status_code >= 300:
            raise MediaFetchError("HTTP")
        total = 0
        try:
            for chunk in response.iter_content(65536):
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    raise MediaFetchError("TOO_LARGE")
                yield chunk
        finally:
            response.close()


_fetcher: RemoteFetcher | None = None


def get_remote_fetcher() -> RemoteFetcher:
    return _fetcher or HttpRemoteFetcher()


def set_remote_fetcher(fetcher: RemoteFetcher | None) -> None:
    global _fetcher
    _fetcher = fetcher


def _ext(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def _media_dir() -> str:
    path = os.path.join(settings.MEDIA_ROOT, "content")
    os.makedirs(path, exist_ok=True)
    return path


def _store(*, chunks: Iterable[bytes], media_type: str, source: str, state: str,
           title: str, original_name: str, max_bytes: int, ai_job_id: int | None,
           admin_id: int) -> MediaItem:
    ext = _ext(original_name)
    allowed = ContentSettings.get("content.media.image_exts" if media_type == "IMAGE"
                                  else "content.media.video_exts")
    if ext not in allowed:
        raise ApiError("FILE_TYPE_NOT_ALLOWED", "文件类型不允许")
    used = sum(MediaItem.objects.values_list("size", flat=True))
    quota = int(ContentSettings.get("content.media.total_quota_bytes"))
    if quota and used + max_bytes > quota:
        raise ApiError("MEDIA_QUOTA_EXCEEDED", "素材库配额不足", 413)
    usage = shutil.disk_usage(_media_dir())
    if usage.free < int(ContentSettings.get("content.media.min_free_bytes")):
        raise ApiError("MEDIA_QUOTA_EXCEEDED", "磁盘剩余空间不足", 413)

    temp_name = f".tmp-{uuid.uuid4().hex}"
    temp_path = os.path.join(_media_dir(), temp_name)
    digest = hashlib.sha256()
    size = 0
    header = b""
    try:
        with open(temp_path, "wb") as fh:
            for chunk in chunks:
                size += len(chunk)
                if size > max_bytes:
                    raise ApiError("FILE_TOO_LARGE", "文件超过大小上限", 413)
                if len(header) < 16:
                    header += chunk[: 16 - len(header)]
                digest.update(chunk)
                fh.write(chunk)
        if media_type == "IMAGE":
            signatures = MAGIC.get(ext, [])
            if source == "AI_GENERATED":
                signatures = [sig for group in MAGIC.values() for sig in group]
            if not any(header.startswith(sig) for sig in signatures):
                raise ApiError("FILE_TYPE_NOT_ALLOWED", "文件内容与扩展名不一致")
        else:
            if header[4:8] != b"ftyp":
                raise ApiError("FILE_TYPE_NOT_ALLOWED", "文件内容与扩展名不一致")
        storage = f"{uuid.uuid4().hex}.{ext}"
        os.replace(temp_path, os.path.join(_media_dir(), storage))
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

    return MediaItem.objects.create(
        media_type=media_type, source=source, state=state,
        title=(title or original_name)[:255], original_name=original_name[:255],
        content_type=f"{media_type.lower()}/{'jpeg' if ext in {'jpg', 'jpeg'} else ext}",
        size=size, sha256=digest.hexdigest(), storage_path=f"content/{storage}",
        ai_job_id=ai_job_id, created_by_admin_id=admin_id,
    )


class MediaService:
    @staticmethod
    def upload(*, file, title: str | None, admin_id: int) -> MediaItem:
        name = os.path.basename(getattr(file, "name", "upload"))
        ext = _ext(name)
        if ext in ContentSettings.get("content.media.image_exts"):
            media_type, limit = "IMAGE", int(ContentSettings.get("content.media.image_max_bytes"))
        elif ext in ContentSettings.get("content.media.video_exts"):
            media_type, limit = "VIDEO", int(ContentSettings.get("content.media.video_max_bytes"))
        else:
            raise ApiError("FILE_TYPE_NOT_ALLOWED", "文件类型不允许")
        return _store(chunks=file.chunks(), media_type=media_type, source="UPLOAD",
                      state="SAVED", title=title or name, original_name=name,
                      max_bytes=limit, ai_job_id=None, admin_id=admin_id)

    @staticmethod
    def store_stream(*, chunks, media_type: str, source: str, state: str, title: str,
                     original_name: str, max_bytes: int, ai_job_id: int | None,
                     admin_id: int) -> MediaItem:
        return _store(chunks=chunks, media_type=media_type, source=source, state=state,
                      title=title, original_name=original_name, max_bytes=max_bytes,
                      ai_job_id=ai_job_id, admin_id=admin_id)

    @staticmethod
    def fetch_remote(url: str, *, max_bytes: int, timeout_seconds: int) -> Iterator[bytes]:
        return get_remote_fetcher().fetch(url, max_bytes=max_bytes, timeout_seconds=timeout_seconds)

    @staticmethod
    def list(*, media_type=None, source=None, q=None):
        qs = MediaItem.objects.filter(state="SAVED")
        if media_type:
            qs = qs.filter(media_type=media_type)
        if source:
            qs = qs.filter(source=source)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    @staticmethod
    def rename(media_id, title: str) -> MediaItem:
        clean = str(title or "").strip()
        if not clean or len(clean) > 255:
            raise ApiError("INVALID_VALUE", "素材名称不合法", 400)
        row = MediaItem.objects.filter(id=media_id).first()
        if row is None:
            raise NotFound("素材不存在")
        row.title = clean
        row.save(update_fields=["title", "updated_at"])
        return row

    @staticmethod
    def save_candidate(media_id) -> MediaItem:
        row = MediaItem.objects.filter(id=media_id).first()
        if row is None:
            raise NotFound("素材不存在")
        if row.state != "SAVED":
            row.state = "SAVED"
            row.save(update_fields=["state", "updated_at"])
        return row

    @staticmethod
    def published_usage(media_id) -> list[tuple[int, str]]:
        return list(
            ContentPost.objects.filter(
                media_links__media_id=media_id, status="PUBLISHED"
            ).values_list("id", "title")[:10]
        )

    @staticmethod
    def delete(media_id, *, admin_id: int) -> None:
        row = MediaItem.objects.filter(id=media_id).first()
        if row is None:
            raise NotFound("素材不存在")
        posts = MediaService.published_usage(media_id)
        if posts:
            raise ApiError("MEDIA_IN_USE", "素材正在被已发布内容使用", 409,
                           {"posts": [{"id": pid, "title": title} for pid, title in posts]})
        path = os.path.join(settings.MEDIA_ROOT, row.storage_path)
        ContentPostMedia.objects.filter(media_id=media_id).delete()
        row.delete()
        if os.path.exists(path):
            os.remove(path)

    @staticmethod
    def housekeeping(now: datetime) -> int:
        ttl = int(ContentSettings.get("content.media.candidate_ttl_hours"))
        cutoff = now - timedelta(hours=ttl)
        rows = MediaItem.objects.filter(state="CANDIDATE", created_at__lt=cutoff)
        count = 0
        for row in rows:
            if ContentPostMedia.objects.filter(media_id=row.id).exists():
                continue
            path = os.path.join(settings.MEDIA_ROOT, row.storage_path)
            row.delete()
            if os.path.exists(path):
                os.remove(path)
            count += 1
        return count


def sign_media_url(media_id, *, ttl_seconds: int | None = None, absolute: bool = False) -> str:
    ttl = int(ttl_seconds or ContentSettings.get("content.media.url_ttl_seconds"))
    expiry = int(timezone.now().timestamp()) + ttl
    sig = signing.dumps({"m": str(media_id), "e": expiry}, salt=SIGN_SALT, compress=True)
    prefix = settings.CONTENT_MEDIA_PATH_PREFIX.rstrip("/") or ""
    if absolute:
        base = (settings.CONTENT_PUBLIC_BASE_URL or "").rstrip("/")
        prefix = f"{base}/api/v1"
    return f"{prefix}/content/media/{media_id}/file?sig={sig}"


def verify_media_sig(media_id, sig: str, *, now: float | None = None) -> bool:
    if not sig or len(sig) > 512:
        return False
    try:
        payload = signing.loads(sig, salt=SIGN_SALT)
    except signing.BadSignature:
        return False
    if str(payload.get("m")) != str(media_id):
        return False
    return float(payload.get("e", 0)) >= (now if now is not None else timezone.now().timestamp())


def _parse_range(header: str, size: int) -> tuple[int, int] | None:
    if not header or not header.startswith("bytes=") or "," in header:
        return None
    spec = header[6:].strip()
    try:
        start_text, end_text = spec.split("-", 1)
        if start_text == "":
            length = int(end_text)
            if length <= 0:
                return None
            start = max(size - length, 0)
            end = size - 1
        else:
            start = int(start_text)
            end = int(end_text) if end_text else size - 1
    except (ValueError, TypeError):
        return None
    if start < 0 or start >= size or end < start:
        return None
    return start, min(end, size - 1)


def serve_media_file(request, media: MediaItem):
    path = os.path.join(settings.MEDIA_ROOT, media.storage_path)
    if not os.path.exists(path):
        raise NotFound("文件不存在")
    size = os.path.getsize(path)
    range_header = request.headers.get("Range")
    if range_header:
        parsed = _parse_range(range_header, size)
        if parsed is None:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{size}"
            return response
        start, end = parsed
        with open(path, "rb") as fh:
            fh.seek(start)
            data = fh.read(end - start + 1)
        response = HttpResponse(data, status=206, content_type=media.content_type)
        response["Content-Range"] = f"bytes {start}-{end}/{size}"
        response["Content-Length"] = str(len(data))
    else:
        response = FileResponse(open(path, "rb"), content_type=media.content_type)
    response["Accept-Ranges"] = "bytes"
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, max-age=300"
    response["Content-Disposition"] = "inline"
    return response
