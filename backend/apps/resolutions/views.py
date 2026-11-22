"""决议视图（IFC-090/091/093）。"""
from datetime import timedelta
import uuid

from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
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

from django.db.models import Q

from .models import Resolution, Vote
from .services import ResolutionService, VoteStats, is_publicly_visible


class _Expected:
    """应参与人数口径缓存：与 judge_if_due 同函数同口径（IFC-358），整页最多算一次。"""

    def __init__(self) -> None:
        self._value: int | None = None

    def current(self) -> int:
        if self._value is None:
            self._value = CommitteeQuery.denominator_for_half_majority(SystemConfig.get("vote.denominator_mode"))
        return self._value


def resolution_view(row: Resolution, *, with_content: bool = True, stats: VoteStats | None = None,
                    expected: _Expected | None = None) -> dict:
    initiator = row.initiator
    data = {
        "id": row.id, "title": row.title, "status": row.status, "approval_mode": row.approval_mode,
        "vote_deadline": row.vote_deadline,
        "initiator": {"id": row.initiator_id, "labels": row.initiator_labels,
                      "display_name": initiator.nickname or initiator.account_no},
        "revision": row.revision, "decided_at": row.decided_at, "result": row.result,
        "created_at": row.created_at, "attachments": linked_attachment_list("resolution", row.id),
        "participation": None,
        "origin_id": row.origin_id,
        "reopened_by_id": row.reissued.order_by("id").values_list("id", flat=True).first(),
    }
    if with_content:
        data["content"] = row.content
        # 列表不逐行查审批实例，避免查询数随行数增长
        data["approval_instance_id"] = ApprovalEngine.instance_id_of("resolution", row.id)
    if row.approval_mode == "HALF_MAJORITY":
        # ADR-141：不再输出 votes（谁投了什么）；只输出聚合票数与参与进度
        stats = stats or ResolutionService.vote_stats([row])[row.id]
        expected = expected or _Expected()
        data["vote_counts"] = {"agree": stats["agree"], "disagree": stats["disagree"],
                               "abstain": stats["abstain"]}
        if row.status == "PENDING":
            total = expected.current()
        else:
            total = (row.result or {}).get("denominator")
            if not isinstance(total, int):
                total = expected.current()
        data["participation"] = {"voted": stats["voted"], "expected": total}
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
            # IFC-358：已结束，或表决进行中的半数同意决议（Q-B18-08=A）
            # REQ-FUNC-279：进行中优先，其余仍按发起时间倒序，避免进行中决议被分页挤到后面
            qs = (qs.filter(Q(status__in=["APPROVED", "REJECTED"])
                            | Q(status="PENDING", approval_mode="HALF_MAJORITY"))
                  .annotate(_ended_order=Case(When(status="PENDING", then=Value(0)),
                                              default=Value(1), output_field=IntegerField()))
                  .order_by("_ended_order", "-created_at"))
        return page_response(qs, request, ResolutionListSerializer)

    def post(self, request):
        data = request.data or {}
        flow, deadline = _validate_submission(data)
        origin = _origin_of(data, request.user)
        attachment_ids = _parse_attachment_ids(data.get("attachment_ids") or [])
        labels = CommitteeQuery.identity_labels(request.user.id)
        with transaction.atomic():
            row = Resolution.objects.create(
                title=str(data["title"]).strip(), content=str(data["content"]).strip(),
                initiator=request.user, initiator_labels=labels,
                approval_mode=flow.mode, vote_deadline=deadline, origin=origin,
            )
            AttachmentService.link(attachment_ids, linked_type="resolution", linked_id=str(row.id),
                                   purpose="RESOLUTION", owner=request.user)
            instance = ApprovalEngine.submit(scope="RESOLUTION", subject_type="resolution",
                                             subject_id=row.id, flow_id=flow.id, submitter=request.user)
            AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                                action="RESOLUTION_SUBMITTED", object_type="resolution",
                                object_id=str(row.id), result="SUCCESS",
                                detail={"mode": flow.mode, "instance": instance.id,
                                        "origin_id": origin.id if origin else None})
        return Response(resolution_view(row), status=status.HTTP_201_CREATED)


class ResolutionListSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = list(rows) if many else [rows]
        stats = ResolutionService.vote_stats(rows)  # 整页一次查询，分母整页最多算一次
        expected = _Expected()
        self.data = [resolution_view(r, with_content=False, stats=stats[r.id], expected=expected)
                     for r in rows]


def _todo_list(qs, user) -> list[dict]:
    rows = []
    for row in qs:
        instance = ApprovalEngine.pending_instance("resolution", row.id)
        if instance is None:
            continue
        if row.approval_mode == "HALF_MAJORITY":
            if CommitteeQuery.is_member(user.id) and not row.votes.filter(
                revision=row.revision, voter=user
            ).exists():
                rows.append(row)
        elif user.id in (instance.flow_snapshot.get("approver_ids") or []):
            rows.append(row)
    return ResolutionListSerializer(rows, many=True).data


class ResolutionDetailView(APIView):
    permission_classes = [IsMember]

    def get(self, request, resolution_id: int):
        row = Resolution.objects.select_related("initiator").filter(id=resolution_id).first()
        if row is None:
            raise ApiError("NOT_FOUND", "决议不存在", 404)
        _ensure_can_view(row, request.user)
        return Response(resolution_view(row))


def _ensure_can_view(row: Resolution, user) -> None:
    """详情与参与人共用的可见性：公开范围内，或发起人，或在任委员（IFC-358/359）。"""
    if is_publicly_visible(row):
        return
    if row.initiator_id != user.id and not CommitteeQuery.is_member(user.id):
        raise ApiError("FORBIDDEN", "无权查看", 403)


class ResolutionParticipantsView(APIView):
    """GET /resolutions/{id}/participants（IFC-359）：返回昵称、头像、参与时间与 user_id（用于跳转 profile）；
    无选项、手机号、真实姓名。"""
    permission_classes = [IsMember]

    def get(self, request, resolution_id: int):
        row = Resolution.objects.filter(id=resolution_id).first()
        if row is None:
            raise ApiError("NOT_FOUND", "决议不存在", 404)
        _ensure_can_view(row, request.user)
        if row.approval_mode != "HALF_MAJORITY":
            return Response({"mode": row.approval_mode, "count": 0, "results": []})
        votes = (row.votes.filter(revision=row.revision).select_related("voter").order_by("voted_at", "id"))
        results = [{"user_id": v.voter_id,
                    "display_name": v.voter.nickname or v.voter.account_no,
                    "avatar_url": v.voter.avatar_url, "voted_at": v.voted_at} for v in votes]
        return Response({"mode": row.approval_mode, "count": len(results), "results": results})


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
        if row.status != "WITHDRAWN":
            raise ApiError("NOT_RESUBMITTABLE", "该决议已结束，如需再次表决请新建决议", 409)
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


def _origin_of(data: dict, user) -> Resolution | None:
    """新建决议时的原单关联：只能是本人发起且已失败的决议（REQ-FUNC-271/273）。"""
    raw = data.get("origin_id")
    if raw in (None, ""):
        return None
    try:
        origin_id = int(raw)
    except (TypeError, ValueError) as exc:
        raise ApiError("INVALID_VALUE", "origin_id 不合法") from exc
    origin = Resolution.objects.filter(id=origin_id, initiator=user, status="REJECTED").first()
    if origin is None:
        raise ApiError("INVALID_VALUE", "原决议不存在或不可关联")
    return origin


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
        try:
            deadline = parse_datetime(str(raw)) if raw else None
        except ValueError:  # DEF-025：日期不存在（如 2026-02-30T10:00）
            deadline = None
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
