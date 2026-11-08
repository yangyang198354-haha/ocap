"""投票视图（IFC-120/121/122）。"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.committee.services import CommitteeQuery
from apps.core.audit import AuditActor, AuditService
from apps.core.config import SystemConfig
from apps.core.errors import ApiError
from apps.core.permissions import IsChairOrVice, IsMember
from apps.core.serializers import page_response
from apps.residency.services import MembershipService

from .models import Participant, Poll, PollAnswer, PollResponse, Question
from .services import PollService


def poll_view(poll: Poll) -> dict:
    return {"id": poll.id, "kind": poll.kind, "title": poll.title, "description": poll.description,
            "survey_scope": poll.survey_scope, "participant_count": poll.participant_count,
            "deadline": poll.deadline, "status": poll.status, "created_at": poll.created_at,
            "creator_id": poll.creator_id, "question_count": poll.questions.count()}


class PollListCreateView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        PollService.close_due()
        qs = Poll.objects.order_by("-created_at")
        return page_response(qs, request, PollSerializer)

    def post(self, request):
        if not CommitteeQuery.is_chair_or_vice(request.user.id):
            raise ApiError("FORBIDDEN", "需要主任或副主任身份", 403)
        data = request.data or {}
        title = str(data.get("title", "")).strip()
        if not (1 <= len(title) <= 200):
            raise ApiError("INVALID_VALUE", "标题须为 1~200 字符")
        description = str(data.get("description", ""))[:5000]
        deadline = parse_datetime(str(data.get("deadline", "")))
        if deadline is None:
            raise ApiError("INVALID_VALUE", "截止时间格式不正确")
        if deadline.tzinfo is None:
            deadline = timezone.make_aware(deadline)
        min_minutes = int(SystemConfig.get("vote.min_window_minutes"))
        if deadline < timezone.now() + timedelta(minutes=min_minutes):
            raise ApiError("VOTE_WINDOW_TOO_SHORT", f"投票窗口不得少于 {min_minutes} 分钟")
        questions = data.get("questions")
        normalized = _validate_questions(questions)
        kind = str(data.get("kind") or "").upper()
        if kind not in {"REP_VOTE", "SURVEY"}:
            raise ApiError("INVALID_VALUE", "kind 必填且须为 REP_VOTE 或 SURVEY")
        scope = data.get("survey_scope")
        if kind == "SURVEY":
            if scope not in {"OWNERS_ONLY", "OWNERS_AND_RESIDENTS"}:
                raise ApiError("INVALID_VALUE", "survey_scope 必填")
        else:
            scope = None
        representative_ids: list[int] = []
        if kind == "REP_VOTE":
            representative_ids = sorted(set(CommitteeQuery.active_representative_ids()))
            if not representative_ids:
                raise ApiError("NO_REPRESENTATIVES", "尚无业主代表", 409)
        with transaction.atomic():
            poll = Poll.objects.create(creator=request.user, kind=kind, title=title,
                                       description=description, survey_scope=scope,
                                       deadline=deadline,
                                       participant_count=len(representative_ids) or None)
            for order, raw in enumerate(normalized):
                Question.objects.create(poll=poll, title=raw["title"], qtype=raw["qtype"],
                                        required=raw["required"], options=raw["options"], order=order)
            if representative_ids:
                Participant.objects.bulk_create([
                    Participant(poll=poll, user_id=user_id) for user_id in representative_ids
                ])
        AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                            action="POLL_CREATED", object_type="poll", object_id=str(poll.id),
                            result="SUCCESS")
        return Response(poll_detail_view(poll), status=status.HTTP_201_CREATED)


class PollSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [poll_view(r) for r in rows]


def _validate_questions(questions) -> list[dict]:
    if not isinstance(questions, list) or not questions:
        raise ApiError("INVALID_VALUE", "至少需要一个题目")
    if len(questions) > int(SystemConfig.get("poll.max_questions")):
        raise ApiError("INVALID_VALUE", "题目数量超过上限")
    normalized = []
    for raw in questions:
        if not isinstance(raw, dict) or not str(raw.get("title", "")).strip():
            raise ApiError("INVALID_VALUE", "题目文本不能为空")
        qtype = str(raw.get("qtype") or "SINGLE").upper()
        if qtype not in {"AGREE_OPPOSE_ABSTAIN", "SCORE", "SINGLE", "MULTI", "TEXT"}:
            raise ApiError("INVALID_VALUE", "题型不合法")
        if qtype in {"SINGLE", "MULTI"}:
            options = raw.get("options")
            if not isinstance(options, list) or not (2 <= len(options) <= 10):
                raise ApiError("INVALID_VALUE", "每个题目需要 2~10 个选项")
            for opt in options:
                if not isinstance(opt, str) or not opt.strip():
                    raise ApiError("INVALID_VALUE", "选项须为非空字符串")
            options = [str(o).strip() for o in options]
        else:
            options = []
        normalized.append({"title": str(raw["title"]).strip(), "qtype": qtype,
                           "required": bool(raw.get("required", True)), "options": options})
    return normalized


class PollDetailView(APIView):
    permission_classes = [IsMember]

    def get(self, request, poll_id: int):
        PollService.close_due()
        poll = Poll.objects.filter(id=poll_id).first()
        if poll is None:
            raise ApiError("NOT_FOUND", "投票不存在", 404)
        return Response(poll_detail_view(poll, viewer=request.user))


def poll_detail_view(poll: Poll, viewer=None) -> dict:
    data = {**poll_view(poll), "questions": [{
        "id": q.id, "title": q.title, "qtype": q.qtype, "required": q.required, "options": q.options,
    } for q in poll.questions.all()]}
    if viewer is not None:
        data["can_respond"] = _can_respond(poll, viewer)
        response = poll.responses.filter(user=viewer).first()
        if response is not None:
            data["my_response"] = [{"question_id": a.question_id, "value": a.value}
                                   for a in response.answers.all()]
        if poll.status == "CLOSED":
            data["results"] = PollService.results(poll)
    return data


def _can_respond(poll: Poll, user) -> bool:
    if poll.kind == "REP_VOTE":
        return poll.participants.filter(user=user).exists()
    return MembershipService.is_owner_or_resident_of_any(
        user.id, include_residents=poll.survey_scope == "OWNERS_AND_RESIDENTS")


class PollResponseView(APIView):
    # DEF-004：调查面向产权业主/同住人，代表投票面向发起时快照的业主代表。
    permission_classes = [IsMember]

    def post(self, request, poll_id: int):
        poll = Poll.objects.filter(id=poll_id).first()
        if poll is None:
            raise ApiError("NOT_FOUND", "投票不存在", 404)
        if poll.status != "OPEN" or poll.deadline <= timezone.now():
            raise ApiError("POLL_CLOSED", "投票已截止", 409)
        if poll.kind == "REP_VOTE":
            if not CommitteeQuery.is_representative(request.user.id):
                raise ApiError("FORBIDDEN", "需要业主代表身份", 403)
            if not poll.participants.filter(user=request.user).exists():
                raise ApiError("FORBIDDEN", "不在本次投票参与人名单内", 403)
        elif not MembershipService.is_owner_or_resident_of_any(
                request.user.id,
                include_residents=poll.survey_scope == "OWNERS_AND_RESIDENTS"):
            raise ApiError("FORBIDDEN", "无权参与本次调查", 403)
        if poll.responses.filter(user=request.user).exists():
            raise ApiError("ALREADY_VOTED", "已提交过投票", 409)
        answers = (request.data or {}).get("answers")
        if not isinstance(answers, list):
            raise ApiError("INVALID_VALUE", "answers 不合法")
        questions = {q.id: q for q in poll.questions.all()}
        chosen: dict[int, str] = {}
        for raw in answers:
            try:
                question_id = int(raw.get("question_id"))
            except (TypeError, ValueError) as exc:
                raise ApiError("INVALID_VALUE", "question_id 不合法") from exc
            question = questions.get(question_id)
            if question is None:
                raise ApiError("INVALID_VALUE", "题目不属于该投票")
            if question_id in chosen:
                raise ApiError("INVALID_VALUE", "同一题目重复作答")
            value = str(raw.get("value", "")).strip()
            if not value:
                raise ApiError("INVALID_VALUE", "答案不能为空")
            if question.qtype == "AGREE_OPPOSE_ABSTAIN":
                if value not in {"AGREE", "DISAGREE", "ABSTAIN"}:
                    raise ApiError("INVALID_VALUE", "答案须为 AGREE/DISAGREE/ABSTAIN")
            elif question.qtype == "SINGLE":
                if value not in question.options:
                    raise ApiError("INVALID_VALUE", "选项不合法")
            elif question.qtype == "MULTI":
                selected = [str(v).strip() for v in (raw.get("value") or [])]
                if not selected or any(v not in question.options for v in selected):
                    raise ApiError("INVALID_VALUE", "选项不合法")
                value = ",".join(selected)
            elif question.qtype == "SCORE":
                try:
                    score = int(value)
                except ValueError:
                    raise ApiError("INVALID_VALUE", "打分须为整数") from None
                if score < 1 or score > 5:  # AC-055-02
                    raise ApiError("INVALID_VALUE", "打分须在 1~5 之间")
            chosen[question_id] = value
        required_ids = {q.id for q in questions.values() if q.required}
        if not required_ids.issubset(chosen.keys()):
            raise ApiError("INVALID_VALUE", "须回答所有必答题")
        with transaction.atomic():
            response = PollResponse.objects.create(poll=poll, user=request.user)
            PollAnswer.objects.bulk_create([
                PollAnswer(response=response, question=questions[qid], value=val)
                for qid, val in chosen.items()
            ])
            Participant.objects.get_or_create(poll=poll, user=request.user)
        AuditService.record(actor=AuditActor("MEMBER", request.user.id, request.user.identity_label),
                            action="POLL_VOTED", object_type="poll", object_id=str(poll.id),
                            result="SUCCESS")
        return Response({"submitted_at": response.submitted_at}, status=status.HTTP_201_CREATED)


class PollResultView(APIView):
    permission_classes = [IsMember]

    def get(self, request, poll_id: int):
        PollService.close_due()
        poll = Poll.objects.filter(id=poll_id).first()
        if poll is None:
            raise ApiError("NOT_FOUND", "投票不存在", 404)
        if poll.status != "CLOSED":  # REQ-FUNC-047：截止前任何人（含发起人）不可见结果
            raise ApiError("NOT_CLOSED", "投票尚未截止", 409)
        return Response({"id": poll.id, "status": poll.status,
                         "results": PollService.results(poll)})


_ = IsChairOrVice
