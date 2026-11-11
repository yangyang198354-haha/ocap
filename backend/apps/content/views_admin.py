"""MOD-054：管理端内容中心 API（IFC-190~231）。"""
import os
import uuid

from django.http import FileResponse
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.errors import ApiError
from apps.core.permissions import IsAdmin

from .ai_jobs import AiGenerationService
from .conf import ContentSettings
from .drafts import DraftPushService, _out as push_out
from .jobs import JobService
from .media import MediaService
from .models import ContentPost, DraftPush, MediaItem
from .platforms import PlatformAccountService
from .posts import PostService
from .prompts import PromptTemplateService
from .serializers import media_out, post_out
from .services_config import ServiceConfigService
from .styles import StyleService
from .export_pack import ExportPackService

POST_STATUSES = {"DRAFT", "PUBLISHED", "OFFLINE"}
MEDIA_TYPES = {"IMAGE", "VIDEO"}
MEDIA_SOURCES = {"UPLOAD", "AI_GENERATED"}
JOB_KINDS = {"LLM_TEXT", "IMAGE_GEN", "VIDEO_GEN", "DRAFT_PUSH"}
JOB_STATUSES = {"QUEUED", "RUNNING", "WAITING_REMOTE", "SUCCEEDED", "FAILED"}


def _page(qs, request, mapper):
    try:
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
    except (TypeError, ValueError):
        page, page_size = 1, 20
    count = qs.count()
    rows = qs[(page - 1) * page_size: page * page_size]
    return Response({"count": count, "page": page, "page_size": page_size,
                     "results": [mapper(row) for row in rows]})


class AdminOnly(APIView):
    permission_classes = [IsAdmin]


class PostListView(AdminOnly):
    def get(self, request):
        status = request.query_params.get("status")
        if status and status not in POST_STATUSES:
            raise ApiError("INVALID_QUERY", "status 不合法", 400)
        q = request.query_params.get("q", "")[:100]
        qs = PostService.admin_queryset(status, q).order_by("-updated_at", "-id")
        return _page(qs, request, lambda row: post_out(row))

    def post(self, request):
        data = request.data or {}
        post = PostService.create(title=data.get("title", ""), doc=data.get("doc", {}),
                                  style_key=data.get("style_key", "builtin:classic"),
                                  admin=request.user)
        return Response(post_out(post, include_doc=True), status=201)


class PostDetailView(AdminOnly):
    def get(self, request, post_id):
        return Response(post_out(PostService.get(post_id), include_doc=True))

    def patch(self, request, post_id):
        data = request.data or {}
        if not any(key in data for key in ("title", "doc", "style_key")):
            raise ApiError("INVALID_VALUE", "至少需要修改一项", 400)
        post = PostService.update(post_id, title=data.get("title"), doc=data.get("doc"),
                                  style_key=data.get("style_key"), admin=request.user)
        return Response(post_out(post, include_doc=True))

    def delete(self, request, post_id):
        PostService.delete(post_id, request.user)
        return Response(status=204)


class PostPublishView(AdminOnly):
    def post(self, request, post_id):
        return Response(post_out(PostService.publish(post_id, request.user), include_doc=True))


class PostOfflineView(AdminOnly):
    def post(self, request, post_id):
        return Response(post_out(PostService.offline(post_id, request.user), include_doc=True))


class PostConfirmView(AdminOnly):
    def post(self, request, post_id):
        return Response(post_out(PostService.confirm_text(post_id, request.user), include_doc=True))


class PreviewView(AdminOnly):
    def post(self, request):
        data = request.data or {}
        return Response(PostService.render_preview(doc=data.get("doc", {}),
                                                   style_key=data.get("style_key", ""),
                                                   fmt="html"))


class StyleListView(AdminOnly):
    def get(self, request):
        return Response(StyleService.list_all())

    def post(self, request):
        data = request.data or {}
        return Response(StyleService.create(name=data.get("name", ""),
                                            tokens=data.get("tokens", {}),
                                            admin_id=request.user.id), status=201)


class StyleDetailView(AdminOnly):
    def put(self, request, template_id):
        data = request.data or {}
        return Response(StyleService.update(template_id, name=data.get("name"),
                                            tokens=data.get("tokens")))

    def delete(self, request, template_id):
        StyleService.delete(template_id)
        return Response(status=204)


class MediaListView(AdminOnly):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        media_type = request.query_params.get("media_type")
        source = request.query_params.get("source")
        if media_type and media_type not in MEDIA_TYPES:
            raise ApiError("INVALID_QUERY", "media_type 不合法", 400)
        if source and source not in MEDIA_SOURCES:
            raise ApiError("INVALID_QUERY", "source 不合法", 400)
        qs = MediaService.list(media_type=media_type, source=source,
                               q=request.query_params.get("q", "")[:100])
        return _page(qs, request, media_out)

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            raise ApiError("INVALID_VALUE", "缺少文件", 400)
        title = request.data.get("title")
        row = MediaService.upload(file=upload, title=title, admin_id=request.user.id)
        return Response(media_out(row), status=201)


class MediaDetailView(AdminOnly):
    def patch(self, request, media_id):
        return Response(media_out(MediaService.rename(media_id, (request.data or {}).get("title", ""))))

    def delete(self, request, media_id):
        MediaService.delete(media_id, admin_id=request.user.id)
        return Response(status=204)


class MediaSaveView(AdminOnly):
    def post(self, request, media_id):
        return Response(media_out(MediaService.save_candidate(media_id)))


class ServiceListView(AdminOnly):
    def get(self, request):
        return Response(ServiceConfigService.list_all())


class ServiceDetailView(AdminOnly):
    def put(self, request, service_type):
        data = request.data or {}
        return Response(ServiceConfigService.save(
            service_type, params=data.get("params"), secrets=data.get("secrets"),
            is_default=data.get("is_default"), admin=request.user))


class ServiceTestView(AdminOnly):
    def post(self, request, service_type):
        return Response(ServiceConfigService.test(service_type, request.user))


class LlmOptionsView(AdminOnly):
    def get(self, request):
        return Response(ServiceConfigService.llm_options())


class PromptListView(AdminOnly):
    def get(self, request):
        return Response(PromptTemplateService.list_all())

    def post(self, request):
        data = request.data or {}
        return Response(PromptTemplateService.create(
            name=data.get("name", ""), prompt=data.get("prompt", ""),
            params=data.get("params"), admin_id=request.user.id), status=201)


class PromptDetailView(AdminOnly):
    def put(self, request, template_id):
        data = request.data or {}
        return Response(PromptTemplateService.update(
            template_id, name=data.get("name"), prompt=data.get("prompt"),
            params=data.get("params")))

    def delete(self, request, template_id):
        PromptTemplateService.delete(template_id)
        return Response(status=204)


class AiTextView(AdminOnly):
    def post(self, request):
        data = request.data or {}
        job = AiGenerationService.submit_text(
            prompt=data.get("prompt", ""), service_type=data.get("service_type"),
            template_id=data.get("template_id"), params=data.get("params"),
            admin=request.user)
        return Response(JobService.view(job), status=202)


class AiImageView(AdminOnly):
    def post(self, request):
        data = request.data or {}
        job = AiGenerationService.submit_image(
            prompt=data.get("prompt", ""), n=data.get("n", 1),
            size=data.get("size"), admin=request.user)
        return Response(JobService.view(job), status=202)


class AiVideoView(AdminOnly):
    def post(self, request):
        data = request.data or {}
        job = AiGenerationService.submit_video(post_id=data.get("post_id"), admin=request.user)
        return Response(JobService.view(job), status=202)


class JobListView(AdminOnly):
    def get(self, request):
        kind = request.query_params.get("kind")
        status = request.query_params.get("status")
        if kind and kind not in JOB_KINDS:
            raise ApiError("INVALID_QUERY", "kind 不合法", 400)
        if status and status not in JOB_STATUSES:
            raise ApiError("INVALID_QUERY", "status 不合法", 400)
        from .models import ContentJob
        qs = ContentJob.objects.all()
        if kind:
            qs = qs.filter(kind=kind)
        if status:
            qs = qs.filter(status=status)
        return _page(qs.order_by("-created_at", "-id"), request, JobService.view)


class JobDetailView(AdminOnly):
    def get(self, request, job_id):
        return Response(JobService.view(JobService.get(job_id)))


class PlatformListView(AdminOnly):
    def get(self, request):
        return Response(PlatformAccountService.list_platforms())

    def post(self, request):
        data = request.data or {}
        return Response(PlatformAccountService.create(
            platform=data.get("platform", ""), display_name=data.get("display_name", ""),
            credentials=data.get("credentials"), admin=request.user), status=201)


class PlatformDetailView(AdminOnly):
    def patch(self, request, account_id):
        data = request.data or {}
        return Response(PlatformAccountService.update(
            account_id, display_name=data.get("display_name"),
            credentials=data.get("credentials"), admin=request.user))

    def delete(self, request, account_id):
        PlatformAccountService.delete(account_id, request.user)
        return Response(status=204)


class DraftPushView(AdminOnly):
    def post(self, request, post_id):
        data = request.data or {}
        batch_id, job_id, pushes = DraftPushService.start_batch(
            post_id, data.get("account_ids") or [], request.user)
        return Response({"batch_id": batch_id, "job_id": job_id, "pushes": pushes}, status=202)


class DraftRetryView(AdminOnly):
    def post(self, request, push_id):
        job_id, push = DraftPushService.retry(push_id, request.user)
        return Response({"job_id": job_id, "push": push}, status=202)


class DraftHistoryView(AdminOnly):
    def get(self, request, post_id):
        qs = DraftPushService.history(post_id, batch_id=request.query_params.get("batch_id"))
        return _page(qs, request, push_out)


class ExportPackView(AdminOnly):
    def get(self, request, post_id):
        platform = request.query_params.get("platform", "")
        post = PostService.get(post_id)
        stream, name = ExportPackService.build_zip(post, platform, request.user)
        response = FileResponse(stream, as_attachment=True, filename=name,
                                content_type="application/zip")
        return response


class CopyPackView(AdminOnly):
    def get(self, request, post_id):
        platform = request.query_params.get("platform", "")
        return Response(ExportPackService.copy_payload(PostService.get(post_id), platform))


class SettingsView(AdminOnly):
    def get(self, request):
        return Response(ContentSettings.all_items())

    def put(self, request):
        values = (request.data or {}).get("values") or {}
        if not isinstance(values, dict):
            raise ApiError("INVALID_VALUE", "values 必须为对象", 400)
        ContentSettings.update(values, admin_id=request.user.id)
        return Response(ContentSettings.all_items())
