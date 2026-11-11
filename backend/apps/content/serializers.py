"""MOD-054：响应映射（IFC-190~231）。"""
from .media import sign_media_url
from .models import ContentPost, MediaItem
from .posts import PostService


def post_out(post: ContentPost, *, include_doc: bool = False) -> dict:
    data = {
        "id": post.id, "title": post.title, "status": post.status,
        "style_key": post.style_key, "published_at": post.published_at,
        "created_at": post.created_at, "updated_at": post.updated_at,
        "created_by_label": post.created_by_label,
        "text_confirmed": PostService.is_confirmed(post),
    }
    if include_doc:
        data["doc"] = post.doc
        data["media_urls"] = PostService.media_url_map(post.doc)
    return data


def media_out(row: MediaItem) -> dict:
    return {
        "id": str(row.id), "media_type": row.media_type, "source": row.source,
        "state": row.state, "title": row.title, "original_name": row.original_name,
        "size": row.size, "content_type": row.content_type,
        "url": sign_media_url(row.id), "created_at": row.created_at,
        "in_use": row.post_links.filter(post__status="PUBLISHED").exists(),
    }
