"""MOD-055：用户端信息公开 API（IFC-232~234）。"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.errors import ApiError, NotFound
from apps.core.permissions import IsMember

from .media import serve_media_file, verify_media_sig
from .models import MediaItem
from .posts import PostService


class InfoListView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
            page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
        except (TypeError, ValueError):
            page, page_size = 1, 20
        qs = PostService.member_queryset()
        rows = qs[(page - 1) * page_size: page * page_size]
        return Response({
            "count": qs.count(), "page": page, "page_size": page_size,
            "results": [{"id": row.id, "title": row.title,
                         "published_at": row.published_at,
                         "summary": PostService.summary(row)} for row in rows],
        })


class InfoDetailView(APIView):
    permission_classes = [IsMember]

    def get(self, request, post_id):
        fmt = request.query_params.get("fmt", "html")
        if fmt not in {"html", "blocks"}:
            raise ApiError("INVALID_QUERY", "fmt 不合法", 400)
        post = PostService.member_queryset().filter(id=post_id).first()
        if post is None:
            raise NotFound("内容不存在")
        return Response(PostService.render_for_member(post, fmt))


class MediaFileView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, media_id):
        sig = request.query_params.get("sig", "")
        if not verify_media_sig(media_id, sig):
            raise ApiError("MEDIA_SIGNATURE_INVALID", "链接无效或已过期", 403)
        row = MediaItem.objects.filter(id=media_id).first()
        if row is None:
            raise NotFound("素材不存在")
        return serve_media_file(request, row)
