"""到期任务（IFC-130）：投票截止、决议判定、席位到期、过期数据清理、审计保留。"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import AuthToken, LoginTicket, VerificationCode, WeChatLoginState
from apps.committee.services import CommitteeCommands
from apps.core.audit import AuditActor, AuditService
from apps.core.config import SystemConfig
from apps.core.models import AuditLog, JobRun
from apps.polls.services import PollService
from apps.resolutions.services import ResolutionService


class Command(BaseCommand):
    help = "执行到期任务（幂等，可重复运行）"

    def handle(self, *args, **options):
        now = timezone.now()
        summary = {}
        try:
            summary["polls_closed"] = PollService.close_due(now)
            summary["resolutions_judged"] = ResolutionService.judge_all_due(now)
            summary["seats_expired"] = CommitteeCommands.expire_due(now.date())
            summary["tokens_purged"] = AuthToken.objects.filter(
                last_active_at__lt=now - timedelta(days=30)).delete()[0]
            summary["codes_purged"] = VerificationCode.objects.filter(
                created_at__lt=now - timedelta(days=1)).delete()[0]
            summary["states_purged"] = WeChatLoginState.objects.filter(
                expires_at__lt=now - timedelta(days=1)).delete()[0]
            summary["tickets_purged"] = LoginTicket.objects.filter(
                expires_at__lt=now - timedelta(days=1)).delete()[0]
            months = int(SystemConfig.get("audit.retention_months"))
            cutoff = now - timedelta(days=30 * months)
            deleted, _ = AuditLog.objects.filter(occurred_at__lt=cutoff).delete()
            summary["audit_purged"] = deleted
            if deleted:
                AuditService.record(actor=AuditActor("SYSTEM", None, "系统"), action="AUDIT_PURGED",
                                    object_type="audit_log", object_id="auto", result="SUCCESS",
                                    detail={"deleted": deleted, "cutoff_months": months})
            JobRun.objects.update_or_create(
                job_name="run_due_jobs",
                defaults={"last_run_at": now, "last_status": "SUCCESS", "last_error": ""},
            )
        except Exception as exc:  # 记录失败后重新抛出，便于 systemd 观察
            JobRun.objects.update_or_create(
                job_name="run_due_jobs",
                defaults={"last_run_at": now, "last_status": "FAILURE", "last_error": str(exc)[:2000]},
            )
            raise
        self.stdout.write(self.style.SUCCESS(f"run_due_jobs ok: {summary}"))
