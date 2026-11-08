"""投票统计（IFC-122）。"""
from django.db.models import Count
from django.utils import timezone

from .models import Poll, PollAnswer


def merge_responses(primary_id: int, secondary_id: int) -> list[str]:
    """账号合并：两账号都已作答则保留 primary、丢弃 secondary 并审计；仅 secondary 作答则并入（REQ-FUNC-067）。"""
    from apps.core.audit import AuditActor, AuditService

    from .models import PollResponse

    moved: list[str] = []
    for response in list(PollResponse.objects.filter(user_id=secondary_id)):
        poll_id = response.poll_id
        if PollResponse.objects.filter(poll_id=poll_id, user_id=primary_id).exists():
            response.delete()
            AuditService.record(actor=AuditActor("SYSTEM", None, "系统"),
                                action="MERGE_ANSWER_DISCARDED", object_type="poll",
                                object_id=str(poll_id), result="SUCCESS",
                                detail={"primary": primary_id, "secondary": secondary_id})
            moved.append(f"discard_answer:{poll_id}")
        else:
            response.user_id = primary_id
            response.save(update_fields=["user"])
            moved.append(f"move_answer:{poll_id}")
    return moved


def merge_participants(primary_id: int, secondary_id: int) -> list[str]:
    """账号合并：参与人名单并入 primary，重复则丢弃 secondary 的一条。"""
    from .models import Participant

    moved: list[str] = []
    for row in list(Participant.objects.filter(user_id=secondary_id)):
        if Participant.objects.filter(poll_id=row.poll_id, user_id=primary_id).exists():
            row.delete()
        else:
            row.user_id = primary_id
            row.save(update_fields=["user"])
            moved.append(f"move_participant:{row.poll_id}")
    return moved


class PollService:
    @staticmethod
    def close_due(now=None) -> int:
        now = now or timezone.now()
        due = list(Poll.objects.filter(status="OPEN", deadline__lt=now))
        for poll in due:
            poll.status = "CLOSED"
            poll.closed_at = now
            poll.result_snapshot = PollService.results(poll)
            poll.save(update_fields=["status", "closed_at", "result_snapshot"])
        return len(due)

    @staticmethod
    def results(poll: Poll) -> dict:
        participants = poll.participants.count()
        responses = poll.responses.count()
        questions = []
        for question in poll.questions.all():
            qtype = question.qtype
            if qtype in {"SINGLE", "MULTI"}:
                counts = {opt: 0 for opt in question.options}
                for answer in question.answers.all():
                    value = answer.value or ""
                    if qtype == "MULTI":
                        for v in value.split(","):
                            v = v.strip()
                            if v in counts:
                                counts[v] += 1
                    elif value in counts:
                        counts[value] += 1
                options = []
                for opt in question.options:
                    votes = counts.get(opt, 0)
                    percentage = round(votes * 100.0 / responses, 1) if responses else 0.0
                    options.append({"value": opt, "count": votes, "percentage": percentage})
                questions.append({"id": question.id, "title": question.title, "qtype": qtype,
                                  "options": options})
            elif qtype == "AGREE_OPPOSE_ABSTAIN":
                counts = {"AGREE": 0, "DISAGREE": 0, "ABSTAIN": 0}
                for row in question.answers.values("value").annotate(total=Count("id")):
                    if row["value"] in counts:
                        counts[row["value"]] = row["total"]
                questions.append({"id": question.id, "title": question.title, "qtype": qtype,
                                  "counts": counts})
                if poll.kind == "REP_VOTE" and poll.participant_count:
                    questions[-1]["denominator"] = poll.participant_count
                    questions[-1]["passed"] = counts["AGREE"] * 2 > poll.participant_count
            elif qtype == "SCORE":
                scores = [int(a.value) for a in question.answers.all()
                          if (a.value or "").lstrip("-").isdigit()]
                avg = round(sum(scores) / len(scores), 1) if scores else 0.0
                questions.append({"id": question.id, "title": question.title, "qtype": qtype,
                                  "average": avg, "count": len(scores)})
            else:  # TEXT
                questions.append({"id": question.id, "title": question.title, "qtype": qtype,
                                  "count": question.answers.count()})
        return {"participants": participants, "responses": responses, "questions": questions}
