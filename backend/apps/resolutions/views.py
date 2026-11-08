"""决议视图（IFC-090/091/093）。"""
from datetime import timedelta
import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.approval.models import ApprovalFlow
from apps.approval.services import ApprovalEngine, subject_title
from apps.core.attachments import AttachmentService, count_limit, linked_attachment_list
from apps.committee.services import CommitteeQuery
from apps.core.audit import AuditActor, AuditService
from apps.core.config import SystemConfig
from apps.core.errors import ApiError
from apps.core.permissions import IsChairOrVice, IsMember
from apps.core.serializers import page_response

from .models import Resolution, Vote
from .services import ResolutionService


def resolution_view(row: Resolution, *, with_content: bool = True) -> dict:
    data = {
        "id": row.id, "title": row.title, "status": row.status, "approval_mode": row.approval_mode,
        "vote_deadline": row.vote_deadline, "initiator": {"id": row.initiator_id,
                                                          "labels": row.initiator_labels},
        "revision": row.revision, "decided_at": row.decided_at, "result": row.result,
        "created_at": row.created_at, "attachments": linked_attachment_list("resolution", row.id),
    }
    if with_content:
        data["content"] = row.content
    if row.approval_mode == "HALF_MAJORITY":
        votes = list(row.votes.filter(revision=row.revision))
        data["votes"] = [{"voter_id": v.voter_id, "choice": v.choice, "voted_at": v.voted_at} for v in votes]
        data["vote_counts"] = {
            "agree": sum(1 for v in votes if v.choice == "AGREE"),
            "disagree": sum(1 for v in votes if v.choice == "DISAGREE"),
            "abstain": sum(1 for v in votes if v.choice == "ABSTAIN"),
        }
    return data


class ResolutionListCreateView(APIView):
    permission_classes = [IsChairOrVice]

    def get_permissions(self):
        # DEF-001：列表查询对所有登录用户开放，发起仍限主任/副主任。
        if self.request.method == "GET":
            return [IsMember()]
        return [IsChairOrVice()]

    def get(self, request):
        scope = request.query_params.get("scope", "public")
        qs = Resolution.objects.select_related("initiator").order_by("-created_at")
        if scope == "mine":
            qs = qs.filter(initiator=request.user)
        elif scope == "todo":
            qs = qs.filter(status="PENDING")
            return Response(_todo_list(qs, request.user))
        elif scope == "public":
            qs = qs.filter(status__in=["APPROVED", "REJECTED"])
        return page_response(qs, request, ResolutionListSerializer)

    def post(self, request):
        data = request.data or {}
        flow, deadline = _validate_submission(data)
        attachment_ids = _parse_attachment_ids(data.get("attachment_ids") or [])
        labels = CommitteeQuery.identity_labels(request.user.id)
        with transaction.atomic():
            row = Resolution.objects.create(
                title=str(data["title"]).strip(), content=str(data["content"]).strip(),
                initiator=request.user, initiator_labels=labels,
                approval_mode=flow.mode, vote_deadline=deadline,
            )
            AttachmentService.link(attachment_ids, linked_type="resolution", linked_id=str(row.id),
                                   purpose="RESOLUTION", owner=request.user)
            instance = ApprovalEngine.submit(scope="RESOLUTION", subject_type="resolution",
                                             subject_id=row.id, flow_id=flow.id, submitter=request.user)
            AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                                action="RESOLUTION_SUBMITTED", object_type="resolution",
                                object_id=str(row.id), result="SUCCESS",
                                detail={"mode": flow.mode, "instance": instance.id})
        return Response(resolution_view(row), status=status.HTTP_201_CREATED)


class ResolutionListSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [resolution_view(r, with_content=False) for r in rows]


def _todo_list(qs, user) -> list[dict]:
    result = []
    for row in qs:
        instance = ApprovalEngine.pending_instance("resolution", row.id)
        if instance is None:
            continue
        if row.approval_mode == "HALF_MAJORITY":
            if CommitteeQuery.is_member(user.id) and not row.votes.filter(
                revision=row.revision, voter=user
            ).exists():
                result.append(resolution_view(row, with_content=False))
        elif user.id in (instance.flow_snapshot.get("approver_ids") or []):
            result.append(resolution_view(row, with_content=False))
    return result


class ResolutionDetailView(APIView):
    permission_classes = [IsMember]

    def get(self, request, resolution_id: int):
        row = Resolution.objects.filter(id=resolution_id).first()
        if row is None:
            raise ApiError("NOT_FOUND", "决议不存在", 404)
        if row.status not in {"APPROVED", "REJECTED"}:
            if row.initiator_id != request.user.id and not CommitteeQuery.is_member(request.user.id):
                raise ApiError("FORBIDDEN", "无权查看", 403)
        return Response(resolution_view(row))


class ResolutionWithdrawView(APIView):
    permission_classes = [IsMember]

    def post(self, request, resolution_id: int):
        row = Resolution.objects.filter(id=resolution_id, initiator=request.user).first()
        if row is None:
            raise ApiError("NOT_FOUND", "决议不存在或非本人发起", 404)
        if row.status != "PENDING":
            raise ApiError("ALREADY_DECIDED", "该决议已处理", 409)
        instance = ApprovalEngine.pending_instance("resolution", row.id)
        if instance is None:
            raise ApiError("NOT_FOUND", "审批实例不存在", 404)
        ApprovalEngine.withdraw(instance.id, request.user)
        row.refresh_from_db()
        return Response(resolution_view(row))


class ResolutionResubmitView(APIView):
    permission_classes = [IsMember]

    def post(self, request, resolution_id: int):
        row = Resolution.objects.filter(id=resolution_id, initiator=request.user).first()
        if row is None:
            raise ApiError("NOT_FOUND", "决议不存在或非本人发起", 404)
        if row.status not in {"REJECTED", "WITHDRAWN"}:
            raise ApiError("NOT_RESUBMITTABLE", "当前状态不可重新提交", 409)
        data = request.data or {}
        flow, deadline = _validate_submission(data)
        attachment_ids = _parse_attachment_ids(data.get("attachment_ids") or [])
        with transaction.atomic():
            row.title = str(data["title"]).strip()
            row.content = str(data["content"]).strip()
            row.status = "PENDING"
            row.approval_mode = flow.mode
            row.vote_deadline = deadline
            row.decided_at = None
            row.result = None
            row.revision += 1
            row.save()
            row.votes.filter(revision=row.revision).delete()
            if attachment_ids:
                AttachmentService.link(attachment_ids, linked_type="resolution",
                                       linked_id=str(row.id), purpose="RESOLUTION", owner=request.user)
            ApprovalEngine.resubmit(scope="RESOLUTION", subject_type="resolution", subject_id=row.id,
                                    flow_id=flow.id, submitter=request.user, revision=row.revision)
        return Response(resolution_view(row))


class VoteView(APIView):
    permission_classes = [IsMember]

    def post(self, request, resolution_id: int):
        row = (Resolution.objects.select_related("initiator")
               .filter(id=resolution_id).first())
        if row is None:
            raise ApiError("NOT_FOUND", "决议不存在", 404)
        if not CommitteeQuery.is_member(request.user.id):
            raise ApiError("FORBIDDEN", "需要业委会成员身份", 403)
        if row.approval_mode != "HALF_MAJORITY":
            raise ApiError("NOT_VOTING", "该决议不采用投票方式", 409)
        if row.status != "PENDING":
            raise ApiError("ALREADY_DECIDED", "该决议已处理", 409)
        if row.vote_deadline is None or timezone.now() > row.vote_deadline:
            raise ApiError("VOTE_CLOSED", "投票已截止", 409)
        choice = (request.data or {}).get("choice")
        if choice not in {"AGREE", "DISAGREE", "ABSTAIN"}:
            raise ApiError("INVALID_VALUE", "choice 不合法")
        _, created = Vote.objects.get_or_create(
            resolution=row, revision=row.revision, voter=request.user, defaults={"choice": choice},
        )
        if not created:
            raise ApiError("ALREADY_VOTED", "本轮已投票", 409)
        return Response(resolution_view(row))


def _validate_submission(data: dict):
    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()
    if not (1 <= len(title) <= 200) or not (1 <= len(content) <= 20000):
        raise ApiError("INVALID_VALUE", "标题或正文长度不合法")
    try:
        flow = ApprovalFlow.objects.get(id=int(data.get("approval_flow_id")), scope="RESOLUTION",
                                        is_active=True)
    except (TypeError, ValueError, ApprovalFlow.DoesNotExist) as exc:
        raise ApiError("INVALID_VALUE", "审批流程不可用") from exc
    deadline = None
    if flow.mode == "HALF_MAJORITY":
        from django.utils.dateparse import parse_datetime

        raw = data.get("vote_deadline")
        deadline = parse_datetime(str(raw)) if raw else None
        if deadline is None:
            raise ApiError("INVALID_VALUE", "半数同意决议须填写投票截止时间")
        if deadline.tzinfo is None:
            deadline = timezone.make_aware(deadline)
        min_minutes = int(SystemConfig.get("vote.min_window_minutes"))
        if deadline < timezone.now() + timedelta(minutes=min_minutes):
            raise ApiError("VOTE_WINDOW_TOO_SHORT", f"投票窗口不得少于 {min_minutes} 分钟")
    return flow, deadline


def _parse_attachment_ids(values) -> list:
    if len(values) > int(count_limit("RESOLUTION")):
        raise ApiError("ATTACHMENT_LIMIT", "附件数量超过上限")
    parsed = []
    for raw in values:
        try:
            parsed.append(uuid.UUID(str(raw)))
        except ValueError as exc:
            raise ApiError("ATTACHMENT_LIMIT", "附件 id 不合法") from exc
    return parsed


_ = (ResolutionService, subject_title)
