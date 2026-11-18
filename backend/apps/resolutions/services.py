"""决议服务（IFC-092）。"""
from typing import TypedDict

from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.config import SystemConfig
from apps.committee.services import CommitteeQuery

from .models import Resolution


def on_approved(subject_id: int) -> None:
    _close(subject_id, "APPROVED", None)


def on_rejected(subject_id: int) -> None:
    _close(subject_id, "REJECTED", None)


def on_withdrawn(subject_id: int) -> None:
    Resolution.objects.filter(id=subject_id, status="PENDING").update(
        status="WITHDRAWN", decided_at=timezone.now(),
    )
    AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="RESOLUTION_WITHDRAWN",
                        object_type="resolution", object_id=str(subject_id), result="SUCCESS")


def _close(subject_id: int, status: str, result: dict | None) -> None:
    Resolution.objects.filter(id=subject_id, status="PENDING").update(
        status=status, decided_at=timezone.now(), result=result,
    )
    AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="RESOLUTION_DECIDED",
                        object_type="resolution", object_id=str(subject_id), result="SUCCESS",
                        detail={"status": status, "result": result})


def merge_votes(primary_id: int, secondary_id: int) -> list[str]:
    """账号合并：同一决议同一轮次两账号都已表决则保留 primary，丢弃 secondary 并审计；其余并入。"""
    from .models import Vote

    moved: list[str] = []
    for vote in list(Vote.objects.filter(voter_id=secondary_id)):
        if Vote.objects.filter(resolution_id=vote.resolution_id, revision=vote.revision,
                               voter_id=primary_id).exists():
            resolution_id = vote.resolution_id
            vote.delete()
            AuditService.record(actor=AuditActor("SYSTEM", None, "系统"),
                                action="MERGE_ANSWER_DISCARDED", object_type="resolution",
                                object_id=str(resolution_id), result="SUCCESS",
                                detail={"primary": primary_id, "secondary": secondary_id})
            moved.append(f"discard_vote:{resolution_id}")
        else:
            vote.voter_id = primary_id
            vote.save(update_fields=["voter"])
            moved.append(f"move_vote:{vote.resolution_id}")
    return moved


class ResolutionService:
    @staticmethod
    def vote_stats(rows) -> dict[int, "VoteStats"]:
        """IFC-358：本页决议当前轮次投票统计（一次查询）。"""
        return vote_stats(rows)

    @staticmethod
    def judge_if_due(resolution_id: int, now=None) -> str:
        now = now or timezone.now()
        resolution = Resolution.objects.filter(id=resolution_id).first()
        if resolution is None:
            return "ALREADY_DECIDED"
        if resolution.status != "PENDING" or resolution.approval_mode != "HALF_MAJORITY":
            return "ALREADY_DECIDED"
        if resolution.vote_deadline is None or now < resolution.vote_deadline:
            return "NOT_DUE"
        votes = list(resolution.votes.filter(revision=resolution.revision))
        agree = sum(1 for v in votes if v.choice == "AGREE")
        disagree = sum(1 for v in votes if v.choice == "DISAGREE")
        abstain = sum(1 for v in votes if v.choice == "ABSTAIN")
        denominator = CommitteeQuery.denominator_for_half_majority(
            SystemConfig.get("vote.denominator_mode")
        )
        passed = agree * 2 > denominator
        result = {"agree": agree, "disagree": disagree, "abstain": abstain,
                  "denominator": denominator,
                  "denominator_mode": SystemConfig.get("vote.denominator_mode"),
                  "passed": passed}
        updated = Resolution.objects.filter(id=resolution_id, status="PENDING").update(
            status="APPROVED" if passed else "REJECTED", decided_at=now, result=result,
        )
        if not updated:
            return "ALREADY_DECIDED"
        AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="RESOLUTION_DECIDED",
                            object_type="resolution", object_id=str(resolution_id), result="SUCCESS",
                            detail={"result": result})
        return "PASSED" if passed else "FAILED"

    @staticmethod
    def judge_all_due(now=None) -> int:
        now = now or timezone.now()
        ids = Resolution.objects.filter(status="PENDING", approval_mode="HALF_MAJORITY",
                                        vote_deadline__lte=now).values_list("id", flat=True)
        return sum(1 for rid in list(ids)
                   if ResolutionService.judge_if_due(rid, now) in {"PASSED", "FAILED"})


class VoteStats(TypedDict):
    agree: int
    disagree: int
    abstain: int
    voted: int


def is_publicly_visible(row: Resolution) -> bool:
    """IFC-358：已结束（通过/未通过），或表决进行中的半数同意决议，对所有已登录用户可见。"""
    if row.status in ("APPROVED", "REJECTED"):
        return True
    return row.status == "PENDING" and row.approval_mode == "HALF_MAJORITY"


def vote_stats(rows) -> dict[int, VoteStats]:
    """本页决议当前轮次的投票统计，一次查询（IFC-358，无 N+1）。"""
    revisions = {r.id: r.revision for r in rows}
    stats: dict[int, VoteStats] = {
        rid: {"agree": 0, "disagree": 0, "abstain": 0, "voted": 0} for rid in revisions}
    if not revisions:
        return stats
    from .models import Vote

    key = {"AGREE": "agree", "DISAGREE": "disagree", "ABSTAIN": "abstain"}
    for resolution_id, revision, choice in Vote.objects.filter(
            resolution_id__in=list(revisions)).values_list("resolution_id", "revision", "choice"):
        if revisions[resolution_id] != revision:
            continue
        entry = stats[resolution_id]
        entry[key[choice]] += 1
        entry["voted"] += 1
    return stats
