"""MOD-053：内容包导出与复制（IFC-187）。"""
import os
import tempfile
import zipfile

from django.conf import settings

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError
from apps.integrations.draft import PLATFORMS, get_draft_adapter

from .conf import ContentSettings
from .posts import PostService
from .richtext import render_html, render_text, unsupported_features
from .styles import StyleService


def _actor(admin):
    return AuditActor("ADMIN", getattr(admin, "id", None),
                      getattr(admin, "username", "") or "")


class ExportPackService:
    @staticmethod
    def _prepare(post, platform):
        if platform not in PLATFORMS:
            raise ApiError("PLATFORM_NOT_SUPPORTED", "不支持的平台", 400)
        if not PostService.is_confirmed(post):
            raise ApiError("POST_NOT_CONFIRMED", "请先确认内容", 409)
        adapter = get_draft_adapter(platform)
        ttl = int(ContentSettings.get("content.media.push_url_ttl_seconds"))

        def resolve(media_id):
            from .models import MediaItem
            from .media import sign_media_url
            row = MediaItem.objects.filter(id=media_id).first()
            if row is None:
                return None
            return {"url": sign_media_url(row.id, ttl_seconds=ttl, absolute=True),
                    "media_type": row.media_type, "title": row.title}

        tokens = StyleService.resolve_tokens(post.style_key)
        html = render_html(post.doc, tokens, mode="inline", resolve=resolve)
        unsupported = unsupported_features(post.doc,
                                           platform_unsupported=adapter.unsupported_features)
        if adapter.capability == "MANUAL_EXPORT":
            unsupported = unsupported + ["style_not_carried"]
        return html, unsupported

    @staticmethod
    def build_zip(post, platform: str, admin):
        html, _ = ExportPackService._prepare(post, platform)
        temp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        temp.close()
        name = f"content_{post.id}_{platform}.zip"
        with zipfile.ZipFile(temp.name, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("content.txt", render_text(post.doc))
            archive.writestr("content.html", html)
            for index, link in enumerate(post.media_links.select_related("media"), start=1):
                row = link.media
                path = os.path.join(settings.MEDIA_ROOT, row.storage_path)
                if not os.path.exists(path):
                    continue
                safe = (row.title or row.original_name or f"media_{index}").replace("/", "_")
                archive.write(path, f"media/{index:02d}_{safe}", compress_type=zipfile.ZIP_STORED)
            archive.writestr("README.txt", "内容包由 ocap 生成：正文见 content.txt / content.html，素材在 media/。")
        AuditService.record(actor=_actor(admin), action="CONTENT_PACK_EXPORTED",
                            object_type="content_pack", object_id=str(post.id),
                            result="SUCCESS", detail={"platform": platform})
        return open(temp.name, "rb"), name

    @staticmethod
    def copy_payload(post, platform: str) -> dict:
        html, unsupported = ExportPackService._prepare(post, platform)
        return {"text": render_text(post.doc), "html": html, "unsupported": unsupported}
