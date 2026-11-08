"""定时任务 HTTP 触发接口（IFC-135~140）。

全部幂等，管理员可手动触发；与 `manage.py run_due_jobs` 共用底层服务。
"""
from datetime import timedelta

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import AuthToken, LoginTicket, VerificationCode, WeChatLoginState
from apps.committee.services import CommitteeCommands
from apps.core.audit import AuditActor, AuditService
from apps.core.config import SystemConfig
from apps.core.models import AuditLog
from apps.core.permissions import IsAdmin
from apps.ledger.services import LedgerService
from apps.polls.services import PollService
from apps.resolutions.services import ResolutionService


class _JobView(APIView):
    permission_classes = [IsAdmin]


class ApproveResolutionsView(_JobView):
    def post(self, request):
        now = timezone.now()
        judged = ResolutionService.judge_all_due(now)
        return Response({"judged": judged})


class ClosePollsView(_JobView):
    def post(self, request):
        now = timezone.now()
        closed = PollService.close_due(now)
        return Response({"closed": closed})


class ExpireMembershipsView(_JobView):
    """成员关系目前无到期字段，保留接口供后续扩展。"""

    def post(self, request):
        return Response({"expired": 0})


class ExpireCommitteeSeatsView(_JobView):
    def post(self, request):
        today = timezone.now().date()
        expired = CommitteeCommands.expire_due(today)
        return Response({"expired": expired})


class LedgerGenerateDueView(_JobView):
    def post(self, request):
        reports = LedgerService.generate_due()
        return Response({"generated": len(reports),
                         "report_ids": [r.id for r in reports]})


class AuthCleanupView(_JobView):
    def post(self, request):
        now = timezone.now()
        purged = {
            "tokens": AuthToken.objects.filter(
                last_active_at__lt=now - timedelta(days=30)).delete()[0],
            "codes": VerificationCode.objects.filter(
                created_at__lt=now - timedelta(days=1)).delete()[0],
            "states": WeChatLoginState.objects.filter(
                expires_at__lt=now - timedelta(days=1)).delete()[0],
            "tickets": LoginTicket.objects.filter(
                expires_at__lt=now - timedelta(days=1)).delete()[0],
        }
        return Response({"purged": purged})


class AuditCleanupView(_JobView):
    def post(self, request):
        now = timezone.now()
        months = int(SystemConfig.get("audit.retention_months"))
        cutoff = now - timedelta(days=30 * months)
        deleted, _ = AuditLog.objects.filter(occurred_at__lt=cutoff).delete()
        if deleted:
            AuditService.record(actor=AuditActor("SYSTEM", None, "系统"),
                                action="AUDIT_PURGED", object_type="audit_log",
                                object_id="auto", result="SUCCESS",
                                detail={"deleted": deleted, "cutoff_months": months})
        return Response({"purged": deleted})
