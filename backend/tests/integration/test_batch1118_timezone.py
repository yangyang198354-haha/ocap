"""PHASE_08 集成测试（ocap_batch_1118）：北京时间 00:00–08:00 席位到期的时区缺陷回归（GR-C-001 condition、用户答复 Q5=A）。

关联 AC-039-05/06（既有）、AC-258-03 周边的 expire_due；REQ-NFUNC-050。分层：integration。TC-INT-1140 起。
做法：patch django.utils.timezone.now 为 UTC 2026-11-17 16:30（= 北京时间 2026-11-18 00:30），此刻 UTC 日期=11-17、本地日期=11-18。
期望：term_end = 本地昨天（2026-11-17）的席位应被置 EXPIRED；term_end = 本地今天（2026-11-18）的席位仍 ACTIVE。
"""
from datetime import date, datetime, timezone as dt_timezone
from unittest import mock

from django.core.management import call_command
from django.utils import timezone

from apps.committee.models import Seat
from apps.core.models import AuditLog
from tests.support import ApiTestBase

FROZEN = datetime(2026, 11, 17, 16, 30, tzinfo=dt_timezone.utc)  # 北京时间 2026-11-18 00:30


class MidnightSeatExpiryTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch("django.utils.timezone.now", return_value=FROZEN)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.assertEqual(timezone.localdate(), date(2026, 11, 18))
        self.assertEqual(FROZEN.date(), date(2026, 11, 17))  # UTC 日期与本地日期相差一天，缺陷正是取了后者
        self.yesterday_seat = self._seat(date(2026, 11, 17))
        self.today_seat = self._seat(date(2026, 11, 18))

    def _seat(self, term_end):
        user, _, _ = self.make_owner()
        return Seat.objects.create(user=user, position="MEMBER", term_start=date(2026, 1, 1), term_end=term_end,
                                   status="ACTIVE", active_slot=1)

    def test_tc_int_1140_run_due_jobs_expires_local_yesterday_at_beijing_0030(self):
        """TC-INT-1140 / GR-C-001：北京时间 00:30 运行 run_due_jobs → term_end=本地昨天(2026-11-17) 的席位 EXPIRED 并写 SEAT_EXPIRED 审计；term_end=本地今天 仍 ACTIVE（到期当日仍有效）。"""
        call_command("run_due_jobs")
        self.yesterday_seat.refresh_from_db()
        self.today_seat.refresh_from_db()
        self.assertEqual(self.yesterday_seat.status, "EXPIRED")
        self.assertEqual(self.today_seat.status, "ACTIVE")
        self.assertTrue(AuditLog.objects.filter(action="SEAT_EXPIRED", object_id=str(self.yesterday_seat.id)).exists())
        self.assertFalse(AuditLog.objects.filter(action="SEAT_EXPIRED", object_id=str(self.today_seat.id)).exists())

    def test_tc_int_1141_jobs_endpoint_expires_local_yesterday_at_beijing_0030(self):
        """TC-INT-1141 / GR-C-001：同一时刻 POST /jobs/expire-committee-seats（管理员）→ expired=1，本地昨天的席位 EXPIRED，今天的 ACTIVE；非管理员 403。"""
        _, admin_token = self.make_admin()
        _, utoken = self.make_user()
        self.assertEqual(self.api("post", "/jobs/expire-committee-seats", token=utoken).status_code, 403)
        resp = self.api("post", "/jobs/expire-committee-seats", token=admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.json()["expired"], 1)
        self.assertEqual(Seat.objects.get(id=self.yesterday_seat.id).status, "EXPIRED")
        self.assertEqual(Seat.objects.get(id=self.today_seat.id).status, "ACTIVE")

    def test_tc_int_1142_pending_seat_also_expires_at_local_midnight(self):
        """TC-INT-1142 / AC-257-09：待绑定席位（user 为空）到期同样按本地日期失效，之后认证不再绑定。"""
        from apps.registry.models import RegistryOwner, RegistryUnit

        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room="999")
        owner = RegistryOwner.objects.create(unit=unit, name="业主甲")
        seat = Seat.objects.create(user=None, position="MEMBER", term_start=date(2026, 1, 1), term_end=date(2026, 11, 17),
                                   status="ACTIVE", active_slot=1, holder_owner=owner, holder_unit_text=unit.specific_part,
                                   holder_name="业主甲")
        call_command("run_due_jobs")
        seat.refresh_from_db()
        self.assertEqual(seat.status, "EXPIRED")
