"""MOD-046：数据库任务队列（IFC-176）。"""
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Protocol

from django.db import transaction
from django.utils import timezone

from .conf import ContentSettings
from .models import ContentJob


@dataclass(frozen=True)
class Done:
    result: dict


@dataclass(frozen=True)
class Wait:
    next_run_at: datetime
    progress: dict | None = None


@dataclass(frozen=True)
class Fail:
    code: str
    message: str = ""


class JobContext:
    def __init__(self, job: ContentJob, now: datetime):
        self.job = job
        self.now = now

    def save_state(self, state: Mapping) -> None:
        ContentJob.objects.filter(id=self.job.id).update(state=dict(state))
        self.job.state = dict(state)

    def heartbeat(self) -> None:
        seconds = int(ContentSettings.get("content.job.lease_seconds"))
        # 1.1.0（ADR-063 第 6 条）：以当前时间续租，不再用任务开始时间 self.now
        ContentJob.objects.filter(id=self.job.id).update(
            lease_until=timezone.now() + timezone.timedelta(seconds=seconds))


class JobHandler(Protocol):
    kind: str
    idempotent: bool

    def run(self, ctx: JobContext): ...

    def on_interrupted(self, job: ContentJob) -> None: ...


_HANDLERS: dict[str, JobHandler] = {}


class JobService:
    @staticmethod
    def register_handler(handler: JobHandler) -> None:
        _HANDLERS[handler.kind] = handler

    @staticmethod
    def handlers() -> dict[str, JobHandler]:
        return dict(_HANDLERS)

    @staticmethod
    def enqueue(*, kind: str, payload: Mapping, admin_id: int, admin_label: str,
                subject_type: str = "", subject_id: str = "", max_attempts: int = 2) -> ContentJob:
        return ContentJob.objects.create(
            kind=kind, payload=dict(payload), status="QUEUED",
            next_run_at=timezone.now(), max_attempts=max_attempts,
            subject_type=subject_type, subject_id=str(subject_id)[:64],
            created_by_admin_id=admin_id, created_by_label=admin_label[:64],
        )

    @staticmethod
    def claim_next(*, now: datetime, lease_seconds: int) -> ContentJob | None:
        candidates = ContentJob.objects.filter(
            status__in=["QUEUED", "WAITING_REMOTE"], next_run_at__lte=now
        ).order_by("next_run_at", "id")[:5]
        for job in candidates:
            token = secrets.token_hex(16)
            updated = ContentJob.objects.filter(
                id=job.id, status__in=["QUEUED", "WAITING_REMOTE"], next_run_at__lte=now
            ).update(status="RUNNING", lease_token=token,
                     lease_until=now + timezone.timedelta(seconds=lease_seconds),
                     started_at=job.started_at or now, attempts=job.attempts + 1)
            if updated:
                return ContentJob.objects.get(id=job.id)
        return None

    @staticmethod
    def run_one(job_id: int, *, now: datetime | None = None) -> ContentJob:
        now = now or timezone.now()
        job = ContentJob.objects.filter(id=job_id).first()
        if job is None:
            return None
        handler = _HANDLERS.get(job.kind)
        if handler is None:
            ContentJob.objects.filter(id=job.id).update(
                status="FAILED", error_code="NO_HANDLER", error_message="没有可用的任务处理器",
                finished_at=now, lease_token="", lease_until=None)
            return ContentJob.objects.get(id=job.id)
        ctx = JobContext(job, now)
        try:
            outcome = handler.run(ctx)
        except Exception as exc:  # noqa: BLE001 - 处理器异常统一失败
            outcome = Fail("INTERNAL", str(exc))
        if isinstance(outcome, Done):
            ContentJob.objects.filter(id=job.id).update(
                status="SUCCEEDED", result=outcome.result, error_code="", error_message="",
                finished_at=now, lease_token="", lease_until=None)
        elif isinstance(outcome, Wait):
            ContentJob.objects.filter(id=job.id).update(
                status="WAITING_REMOTE", next_run_at=outcome.next_run_at,
                lease_token="", lease_until=None,
                state={**job.state, **(outcome.progress or {})})
        else:
            ContentJob.objects.filter(id=job.id).update(
                status="FAILED", error_code=outcome.code, error_message=outcome.message[:500],
                finished_at=now, lease_token="", lease_until=None)
        return ContentJob.objects.get(id=job.id)

    @staticmethod
    def requeue_expired(now: datetime) -> dict[str, int]:
        result = {"requeued": 0, "failed": 0}
        expired = ContentJob.objects.filter(status="RUNNING", lease_until__lt=now)
        for job in expired:
            handler = _HANDLERS.get(job.kind)
            if handler is not None and handler.idempotent and job.attempts < job.max_attempts:
                ContentJob.objects.filter(id=job.id).update(
                    status="QUEUED", next_run_at=now, lease_token="", lease_until=None)
                result["requeued"] += 1
            else:
                if handler is not None:
                    handler.on_interrupted(job)
                ContentJob.objects.filter(id=job.id).update(
                    status="FAILED", error_code="INTERRUPTED",
                    error_message="任务中断且不自动重试", finished_at=now,
                    lease_token="", lease_until=None)
                result["failed"] += 1
        return result

    @staticmethod
    def view(job: ContentJob) -> dict:
        progress = None
        if job.status in {"RUNNING", "WAITING_REMOTE"} and job.state:
            percent = job.state.get("percent")
            step = job.state.get("phase") or job.state.get("step") or ""
            progress = {"step": str(step), "percent": percent}
        return {
            "id": job.id, "kind": job.kind, "status": job.status,
            "progress": progress, "result": job.result,
            "error_code": job.error_code, "error_message": job.error_message,
            "created_by_label": job.created_by_label, "created_at": job.created_at,
            "started_at": job.started_at, "finished_at": job.finished_at,
        }

    @staticmethod
    def get(job_id: int) -> ContentJob:
        from apps.core.errors import NotFound
        job = ContentJob.objects.filter(id=job_id).first()
        if job is None:
            raise NotFound("任务不存在")
        return job

    @staticmethod
    def purge(now: datetime) -> int:
        days = int(ContentSettings.get("content.job.retention_days"))
        cutoff = now - timezone.timedelta(days=days)
        deleted, _ = ContentJob.objects.filter(
            status__in=["SUCCEEDED", "FAILED"], finished_at__lt=cutoff).delete()
        return deleted
