"""core 的 HTTP 端点（IFC-002/004/005/009）。"""
from django.http import FileResponse
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .attachments import AttachmentService
from .audit import AuditActor, AuditService
from .config import EDITABLE_KEYS, SystemConfig
from .errors import ApiError, NotFound
from .models import AuditLog
from .permissions import IsAdmin, IsMember, IsMemberOrAdmin
from .ratelimit import RateLimiter
from .serializers import page_response


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "occurred_at", "actor_type", "actor_id", "actor_label", "action",
                  "object_type", "object_id", "result", "detail", "ip"]


class AuditLogListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = AuditLog.objects.all()
        for param in ("action", "object_type", "object_id", "actor_id"):
            value = request.query_params.get(param)
            if value:
                qs = qs.filter(**{param: value})
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        if date_from:
            qs = qs.filter(occurred_at__gte=date_from)
        if date_to:
            qs = qs.filter(occurred_at__lte=date_to)
        return page_response(qs, request, AuditLogSerializer)


class SystemConfigView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(SystemConfig.all_editable())

    def put(self, request, key: str):
        if key not in EDITABLE_KEYS:
            raise NotFound("配置项不可编辑")
        value = (request.data or {}).get("value")
        if key == "audit.retention_months":
            if not isinstance(value, int) or isinstance(value, bool):
                raise ApiError("INVALID_VALUE", "保留期限必须为整数")
            if value < 6:
                raise ApiError("RETENTION_TOO_SHORT", "保留期限不得低于 6 个月")
            if value > 120:
                raise ApiError("RETENTION_TOO_LONG", "保留期限不得高于 120 个月")
        before = SystemConfig.get(key)
        SystemConfig.set(key, value, request.user.id)
        AuditService.record(
            actor=AuditActor("ADMIN", request.user.id, request.user.username),
            action="SYSTEM_CONFIG_CHANGED", object_type="system_config", object_id=key,
            result="SUCCESS", detail={"before": before, "after": value},
        )
        return Response({"key": key, "value": value})


class AttachmentUploadView(APIView):
    permission_classes = [IsMember]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        decision = RateLimiter.hit(f"upload:{request.user.id}", limit=60, window_seconds=3600)
        if not decision.allowed:
            raise ApiError("CODE_RATE_LIMITED", "上传过于频繁", 429, {"retry_after": decision.retry_after})
        file = request.FILES.get("file")
        purpose = request.data.get("purpose", "")
        if file is None:
            raise ApiError("FILE_REQUIRED", "缺少文件")
        ref = AttachmentService.store(file=file, purpose=purpose, owner=request.user)
        return Response({"id": str(ref.id), "name": ref.name, "size": ref.size,
                         "content_type": ref.content_type}, status=status.HTTP_201_CREATED)


class AttachmentDownloadView(APIView):
    permission_classes = [IsMemberOrAdmin]

    def get(self, request, attachment_id):
        return AttachmentService.open(attachment_id, request.user)


def attachment_response(row) -> FileResponse:
    return AttachmentService.open(row.id, None)
