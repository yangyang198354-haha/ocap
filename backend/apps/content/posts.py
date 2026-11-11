"""MOD-045：信息公开内容服务（IFC-175）。"""
import hashlib
from typing import Mapping

from django.db import transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, NotFound

from .conf import ContentSettings
from .media import sign_media_url
from .models import ContentPost, ContentPostMedia, MediaItem
from .richtext import (
    DocValidationError, extract_media_ids, render_html, render_pages, render_text, validate_doc,
)
from .styles import StyleService


def _actor(admin) -> AuditActor:
    return AuditActor("ADMIN", getattr(admin, "id", None),
                      getattr(admin, "username", "") or getattr(admin, "label", ""))


def _validate_style_key(style_key: str) -> str:
    if style_key in {"builtin:classic", "builtin:notice", "builtin:formal"}:
        return style_key
    if style_key.startswith("custom:"):
        from .models import StyleTemplate
        try:
            StyleTemplate.objects.get(id=int(style_key.split(":", 1)[1]))
            return style_key
        except (ValueError, StyleTemplate.DoesNotExist):
            pass
    raise ApiError("STYLE_INVALID", "样式模板不存在", 400, {"field": "style_key"})


def _validate_doc(doc) -> dict:
    try:
        return validate_doc(doc, max_bytes=int(ContentSettings.get("content.post.max_doc_bytes")))
    except DocValidationError as exc:
        raise ApiError("CONTENT_INVALID_DOC", "正文格式不合法", 400,
                       {"path": exc.path, "reason": exc.reason}) from exc


def _resolver(ttl: int | None = None):
    def resolve(media_id):
        row = MediaItem.objects.filter(id=media_id).first()
        if row is None:
            return None
        return {"url": sign_media_url(row.id, ttl_seconds=ttl, absolute=True),
                "media_type": row.media_type, "title": row.title}
    return resolve


class PostService:
    @staticmethod
    def create(*, title: str, doc: Mapping, style_key: str, admin) -> ContentPost:
        clean_doc = _validate_doc(doc)
        key = _validate_style_key(style_key or "builtin:classic")
        clean_title = str(title or "").strip()
        if len(clean_title) > 200:
            raise ApiError("INVALID_VALUE", "标题过长", 400)
        post = ContentPost.objects.create(
            title=clean_title, doc=clean_doc, style_key=key, status="DRAFT",
            created_by_admin_id=getattr(admin, "id", 0),
            created_by_label=getattr(admin, "username", "")[:64],
            updated_by_admin_id=getattr(admin, "id", 0),
        )
        PostService._sync_media(post)
        return post

    @staticmethod
    def update(post_id: int, *, title=None, doc=None, style_key=None, admin) -> ContentPost:
        post = PostService.get(post_id)
        changed = False
        if title is not None:
            clean_title = str(title).strip()
            if len(clean_title) > 200:
                raise ApiError("INVALID_VALUE", "标题过长", 400)
            post.title = clean_title
            changed = True
        if doc is not None:
            post.doc = _validate_doc(doc)
            changed = True
        if style_key is not None:
            post.style_key = _validate_style_key(style_key)
            changed = True
        if not changed:
            raise ApiError("INVALID_VALUE", "至少需要修改一项", 400)
        post.updated_by_admin_id = getattr(admin, "id", 0)
        post.save()
        PostService._sync_media(post)
        if post.status == "PUBLISHED":
            AuditService.record(actor=_actor(admin), action="CONTENT_POST_UPDATED",
                                object_type="content_post", object_id=str(post.id),
                                result="SUCCESS", detail={"title": post.title})
        return post

    @staticmethod
    def _sync_media(post: ContentPost) -> None:
        ids = extract_media_ids(post.doc)
        existing = set(MediaItem.objects.filter(id__in=ids).values_list("id", flat=True)) if ids else set()
        ContentPostMedia.objects.filter(post=post).exclude(media_id__in=existing).delete()
        for media_id in existing:
            ContentPostMedia.objects.get_or_create(post=post, media_id=media_id)
            MediaItem.objects.filter(id=media_id, state="CANDIDATE").update(state="SAVED")

    @staticmethod
    def publish(post_id: int, admin) -> ContentPost:
        post = PostService.get(post_id)
        missing = []
        if not post.title.strip():
            missing.append("title")
        text = render_text(post.doc).strip()
        has_media = bool(extract_media_ids(post.doc))
        if not text and not has_media:
            missing.append("body")
        if missing:
            raise ApiError("POST_INCOMPLETE", "内容不完整", 400, {"missing": missing})
        ids = extract_media_ids(post.doc)
        found = set(MediaItem.objects.filter(id__in=ids).values_list("id", flat=True)) if ids else set()
        if len(found) != len(ids):
            raise ApiError("POST_MEDIA_MISSING", "引用的素材不存在", 400)
        post.status = "PUBLISHED"
        post.published_at = timezone.now()
        post.updated_by_admin_id = getattr(admin, "id", 0)
        post.save()
        AuditService.record(actor=_actor(admin), action="CONTENT_POST_PUBLISHED",
                            object_type="content_post", object_id=str(post.id),
                            result="SUCCESS", detail={"title": post.title})
        return post

    @staticmethod
    def offline(post_id: int, admin) -> ContentPost:
        post = PostService.get(post_id)
        if post.status != "PUBLISHED":
            raise ApiError("POST_STATE_INVALID", "仅已发布内容可下线", 409)
        post.status = "OFFLINE"
        post.save(update_fields=["status", "updated_at"])
        AuditService.record(actor=_actor(admin), action="CONTENT_POST_OFFLINED",
                            object_type="content_post", object_id=str(post.id),
                            result="SUCCESS", detail={"title": post.title})
        return post

    @staticmethod
    def delete(post_id: int, admin) -> None:
        post = PostService.get(post_id)
        title = post.title
        post.delete()
        AuditService.record(actor=_actor(admin), action="CONTENT_POST_DELETED",
                            object_type="content_post", object_id=str(post_id),
                            result="SUCCESS", detail={"title": title})

    @staticmethod
    def confirm_text(post_id: int, admin) -> ContentPost:
        post = PostService.get(post_id)
        text = render_text(post.doc).strip()
        if not text:
            raise ApiError("POST_INCOMPLETE", "文案为空", 400, {"missing": ["body"]})
        post.text_confirmed_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        post.text_confirmed_at = timezone.now()
        post.save(update_fields=["text_confirmed_hash", "text_confirmed_at", "updated_at"])
        return post

    @staticmethod
    def is_text_confirmed(post: ContentPost) -> bool:
        text = render_text(post.doc).strip()
        if not text:
            return False
        return post.text_confirmed_hash == hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def is_confirmed(post: ContentPost) -> bool:
        return post.status in {"PUBLISHED", "OFFLINE"} or PostService.is_text_confirmed(post)

    @staticmethod
    def admin_queryset(status=None, q=None):
        qs = ContentPost.objects.all()
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    @staticmethod
    def get(post_id: int) -> ContentPost:
        post = ContentPost.objects.filter(id=post_id).first()
        if post is None:
            raise NotFound("内容不存在")
        return post

    @staticmethod
    def member_queryset():
        return ContentPost.objects.filter(status="PUBLISHED").order_by("-published_at", "-id")

    @staticmethod
    def render_for_member(post: ContentPost, fmt: str) -> dict:
        tokens = StyleService.resolve_tokens(post.style_key)
        pages = render_pages(post.doc, tokens, fmt=fmt, resolve=_resolver(),
                             page_chars=int(tokens.get("page_chars") or 1500))
        if fmt == "blocks":
            from django.conf import settings
            prefix = (settings.CONTENT_MEDIA_PATH_PREFIX or "").rstrip("/")
            for page in pages:
                for block in page.get("blocks", []):
                    src = block.get("src") or ""
                    if prefix and src.startswith(prefix):
                        block["src"] = src[len(prefix):]
        result = {"id": post.id, "title": post.title,
                  "published_at": post.published_at, "page_count": len(pages), "pages": pages}
        if fmt == "blocks":
            result["theme"] = tokens
        return result

    @staticmethod
    def render_preview(*, doc: Mapping, style_key: str, fmt: str = "html") -> dict:
        clean = _validate_doc(doc)
        tokens = StyleService.resolve_tokens(_validate_style_key(style_key or "builtin:classic"))
        pages = render_pages(clean, tokens, fmt=fmt, resolve=_resolver(),
                             page_chars=int(tokens.get("page_chars") or 1500))
        media = {}
        for media_id in extract_media_ids(clean):
            media[str(media_id)] = sign_media_url(media_id, absolute=True)
        return {"page_count": len(pages), "pages": pages, "media_urls": media,
                "theme": tokens if fmt == "blocks" else None}

    @staticmethod
    def media_url_map(doc: Mapping, *, ttl_seconds: int | None = None) -> dict[str, str]:
        result = {}
        for media_id in extract_media_ids(doc):
            result[str(media_id)] = sign_media_url(media_id, ttl_seconds=ttl_seconds)
        return result

    @staticmethod
    def summary(post: ContentPost, n: int = 80) -> str:
        return render_text(post.doc).replace("\n", " ")[:n]
