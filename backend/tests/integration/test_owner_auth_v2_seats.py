"""PHASE_08 集成测试（ocap_owner_auth_v2）：席位授予放宽（US-205）与未来起始日席位生效判定（US-206）。

关联 AC-205-01~07、AC-206-01~05。MOD-116，IFC-311/312。
"在任"调用点（IFC-311 表）逐点验证：active_seat（权限）、active_member_ids、active_representative_ids、
denominator_for_half_majority、identity_view（/me 与用户目录）、后台用户列表席位预取。
"""
from datetime import timedelta
from unittest import mock

from django.utils import timezone

from apps.committee.models import CommitteeConfig, Seat
from apps.committee.services import CommitteeCommands, CommitteeQuery, add_months
from apps.core.models import AuditLog
from apps.approval.models import ApprovalInstance
from tests.support import ApiTestBase


def today():
    return timezone.localdate()


class SeatBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()
        cfg = CommitteeConfig.load()
        cfg.cap_member, cfg.cap_chair, cfg.cap_vice, cfg.cap_rep = 5, 2, 2, 5
        cfg.term_months_member = cfg.term_months_chair = cfg.term_months_vice = cfg.term_months_rep = 36
        cfg.save()

    def set_months(self, months):
        cfg = CommitteeConfig.load()
        cfg.term_months_member = cfg.term_months_chair = cfg.term_months_vice = cfg.term_months_rep = months
        cfg.save()

    def grant(self, user, position="MEMBER", start=None, token=None):
        body = {"user_id": user.id, "position": position}
        if start is not None:
            body["term_start"] = str(start)
        return self.api("post", "/admin/committee/seats", body, token=token or self.admin_token)

    def future_member(self, position="MEMBER", days=30):
        user, token, unit = self.make_owner()
        resp = self.grant(user, position, today() + timedelta(days=days))
        self.assert_ok(resp, 201)
        return user, token, resp.data


class GrantBackfillTests(SeatBase):
    def test_tc_int_690_start_before_today_allowed_when_term_still_ahead(self):
        """AC-205-01：配置任期 36 个月，开始日 = 今天 − 300 天（结束日仍晚于今天）→ 201，不再提示「任期开始日不得早于今天」；
        席位记录开始日 = 所给日期，结束日 = 开始日 + 36 个月；已立即生效（effective=true）。"""
        user, _, _ = self.make_owner()
        start = today() - timedelta(days=300)
        resp = self.grant(user, "MEMBER", start)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["term_start"], start)
        self.assertEqual(resp.data["term_end"], add_months(start, 36))
        self.assertTrue(resp.data["effective"])
        seat = Seat.objects.get(user=user)
        self.assertEqual((seat.term_start, seat.term_end, seat.status), (start, add_months(start, 36), "ACTIVE"))
        self.assertNotIn("不得早于今天", resp.content.decode())

    def test_tc_int_691_term_already_ended_rejected_with_end_date_message(self):
        """AC-205-02：开始日 2020-01-01（36 个月，结束日 2023-01-01）→ 400，提示「按配置任期，该席位已于 2023-01-01 结束，不能授予」，不产生席位。"""
        from datetime import date

        user, _, _ = self.make_owner()
        resp = self.grant(user, "MEMBER", date(2020, 1, 1))
        body = self.assert_error(resp, 400, "INVALID_VALUE")
        self.assertEqual(body["message"], "按配置任期，该席位已于 2023-01-01 结束，不能授予")
        self.assertFalse(Seat.objects.filter(user=user).exists())

    def test_tc_int_692_end_date_equal_today_rejected_tomorrow_accepted(self):
        """AC-205-03：推算结束日恰为今天 → 被拒并给出同样提示；推算结束日为明天 → 授予成功。"""
        self.set_months(12)
        eq = next(today() - timedelta(days=d) for d in range(300, 400)
                  if add_months(today() - timedelta(days=d), 12) == today())
        gt = next(today() - timedelta(days=d) for d in range(300, 400)
                  if add_months(today() - timedelta(days=d), 12) == today() + timedelta(days=1))
        user, _, _ = self.make_owner()
        body = self.assert_error(self.grant(user, "MEMBER", eq), 400, "INVALID_VALUE")
        self.assertIn(f"已于 {today():%Y-%m-%d} 结束，不能授予", body["message"])
        self.assertFalse(Seat.objects.filter(user=user).exists())
        self.assert_ok(self.grant(user, "MEMBER", gt), 201)
        self.assertEqual(Seat.objects.get(user=user).term_end, today() + timedelta(days=1))

    def test_tc_int_693_backfill_does_not_bypass_already_seated(self):
        """AC-205-04：用户已有有效席位时补录 → 409 ALREADY_SEATED，不产生新席位（与结束日校验先后无关，结束日合法的补录）。"""
        user, _, _ = self.make_owner()
        self.assert_ok(self.grant(user, "MEMBER"), 201)
        resp = self.grant(user, "REPRESENTATIVE", today() - timedelta(days=100))
        self.assert_error(resp, 409, "ALREADY_SEATED")
        self.assertEqual(Seat.objects.filter(user=user).count(), 1)

    def test_tc_int_694_backfill_does_not_bypass_cap(self):
        """AC-205-05：该身份在任人数已达上限 → 补录 409 CAP_REACHED。"""
        cfg = CommitteeConfig.load()
        cfg.cap_rep = 1
        cfg.save()
        first, _, _ = self.make_owner()
        second, _, _ = self.make_owner()
        self.assert_ok(self.grant(first, "REPRESENTATIVE"), 201)
        self.assert_error(self.grant(second, "REPRESENTATIVE", today() - timedelta(days=100)), 409, "CAP_REACHED")
        self.assertFalse(Seat.objects.filter(user=second).exists())

    def test_tc_int_695_only_admin_can_grant(self):
        """AC-205-06：非管理员（普通用户令牌）403、未登录 401，不产生席位。"""
        user, token, _ = self.make_owner()
        self.assert_error(self.api("post", "/admin/committee/seats", {"user_id": user.id, "position": "MEMBER"},
                                   token=token), 403)
        self.assert_error(self.api("post", "/admin/committee/seats", {"user_id": user.id, "position": "MEMBER"}), 401)
        self.assertFalse(Seat.objects.exists())

    def test_tc_int_696_backfill_does_not_change_existing_approvals(self):
        """AC-205-07：补录开始日早于授予时间的席位后，期间已发起的审批实例状态与记录逐项不变，无新增审批记录。"""
        member, mtoken, _ = self.make_owner()
        self.make_seat(member, "MEMBER")
        approver, _, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[approver])
        from apps.core.models import Attachment
        from uuid import uuid4
        inv = Attachment.objects.create(owner_type="MEMBER", owner_id=member.id, purpose="INVOICE",
                                        original_name="i.pdf", content_type="application/pdf", size=10,
                                        sha256="x" * 64, storage_path=f"tmp/{uuid4().hex}", status="TEMP")
        resp = self.api("post", "/claims/reimbursements", {
            "amount": "10.00", "reason": "r", "occurred_on": str(today()), "invoice_ids": [str(inv.id)],
            "approval_flow_id": flow.id}, token=mtoken)
        self.assert_ok(resp, 201)

        def state():
            return list(ApprovalInstance.objects.order_by("id").values_list("id", "status", "subject_id"))

        before = state()
        self.assertTrue(before)
        other, _, _ = self.make_owner()
        self.assert_ok(self.grant(other, "MEMBER", today() - timedelta(days=200)), 201)
        self.assertEqual(state(), before)


class FutureSeatTests(SeatBase):
    def test_tc_int_697_future_start_granted_but_not_effective_in_response_and_list(self):
        """AC-206-01、IFC-312：开始日在将来 → 授予成功（201），status 仍为 ACTIVE 但 effective=false；列表同样；开始日=今天 → effective=true（AC-206-03/05）。"""
        user, _, data = self.future_member(days=15)
        self.assertEqual((data["status"], data["effective"]), ("ACTIVE", False))
        now_user, _, _ = self.make_owner()
        resp = self.grant(now_user, "MEMBER", today())
        self.assertEqual((resp.data["effective"], resp.data["term_start"]), (True, today()))
        listing = self.api("get", "/admin/committee/seats", token=self.admin_token).json()["results"]
        flags = {r["user"]["id"]: r["effective"] for r in listing}
        self.assertEqual((flags[user.id], flags[now_user.id]), (False, True))

    def test_tc_int_698_callsite_me_identity_and_labels(self):
        """IFC-311 调用点 identity_view / identity_labels：未来席位在开始日前 /me 不显示业委会身份（summary 为产权业主），committee 为空；开始日=今天的席位立即显示委员。"""
        user, token, _ = self.future_member(days=10)
        me = self.api("get", "/me", token=token).json()["identities"]
        self.assertIsNone(me["committee"])
        self.assertEqual(me["summary"]["label"], "产权业主")
        self.assertNotIn("委员", me["labels"])
        eff, etoken, _ = self.make_owner()
        self.assert_ok(self.grant(eff, "MEMBER", today()), 201)
        me2 = self.api("get", "/me", token=etoken).json()["identities"]
        self.assertEqual((me2["committee"]["position"], me2["summary"]["label"]), ("MEMBER", "委员"))
        self.assertIn("委员", me2["labels"])

    def test_tc_int_699_callsite_permissions_committee_member_endpoints(self):
        """IFC-311 调用点 active_seat → IsCommitteeMember：未来席位用户调用委员专属接口（发起报销）403 FORBIDDEN 且提示无权限；
        开始日=今天的委员通过权限层（得到参数校验 400 而非 403）。"""
        _, ftoken, _ = self.future_member(days=10)
        denied = self.api("post", "/claims/reimbursements", {}, token=ftoken)
        self.assert_error(denied, 403, "FORBIDDEN")
        eff, etoken, _ = self.make_owner()
        self.assert_ok(self.grant(eff, "MEMBER", today()), 201)
        passed = self.api("post", "/claims/reimbursements", {}, token=etoken)
        self.assertEqual(passed.status_code, 400)

    def test_tc_int_700_callsite_chair_vice_and_flow_approver_checks(self):
        """IFC-311 调用点 is_chair_or_vice / is_member：未来起始日的主任不能发起决议（403）；未来起始日的委员不能被选为审批流程审批人（422 APPROVER_NOT_COMMITTEE_MEMBER）；
        生效后（开始日=今天）均可。"""
        chair, ctoken, _ = self.future_member("CHAIR", days=10)
        self.assert_error(self.api("post", "/resolutions", {}, token=ctoken), 403, "FORBIDDEN")
        self.assertFalse(CommitteeQuery.is_chair_or_vice(chair.id))
        member, _, _ = self.future_member("MEMBER", days=10)
        resp = self.api("post", "/admin/approval/flows", {"scope": "EXPENSE", "mode": "DESIGNATED",
                                                          "name": "未来席位审批人", "approver_ids": [member.id]},
                        token=self.admin_token)
        self.assert_error(resp, 422, "APPROVER_NOT_COMMITTEE_MEMBER")
        eff, _, _ = self.make_owner()
        self.assert_ok(self.grant(eff, "MEMBER", today()), 201)
        ok = self.api("post", "/admin/approval/flows", {"scope": "EXPENSE", "mode": "DESIGNATED",
                                                        "name": "已生效审批人", "approver_ids": [eff.id]},
                      token=self.admin_token)
        self.assert_ok(ok, 201)

    def test_tc_int_701_callsite_member_and_representative_id_lists_and_denominator(self):
        """IFC-311 调用点 active_member_ids / active_representative_ids / denominator_for_half_majority：
        未来席位不计入在任委员/代表名单，也不计入半数分母（在任人数口径）；已生效的计入。"""
        fmember, _, _ = self.future_member("MEMBER", days=10)
        frep, _, _ = self.future_member("REPRESENTATIVE", days=10)
        emember, _, _ = self.make_owner()
        erep, _, _ = self.make_owner()
        self.assert_ok(self.grant(emember, "MEMBER", today()), 201)
        self.assert_ok(self.grant(erep, "REPRESENTATIVE", today() - timedelta(days=5)), 201)
        self.assertEqual(CommitteeQuery.active_member_ids(), [emember.id])
        self.assertEqual(CommitteeQuery.active_representative_ids(), [erep.id])
        self.assertEqual(CommitteeQuery.denominator_for_half_majority("ACTIVE_COUNT"), 1)
        self.assertNotIn(fmember.id, CommitteeQuery.active_member_ids())
        self.assertNotIn(frep.id, CommitteeQuery.active_representative_ids())

    def test_tc_int_702_callsite_admin_user_list_identity(self):
        """IFC-311 调用点 后台用户列表席位预取：未来席位用户在后台用户目录的身份为「产权业主」；生效席位显示「委员」。"""
        fut, _, _ = self.future_member(days=10)
        eff, _, _ = self.make_owner()
        self.assert_ok(self.grant(eff, "MEMBER", today()), 201)
        rows = {r["id"]: r for r in self.api("get", "/admin/users?page_size=100", token=self.admin_token).json()["results"]}
        self.assertEqual(rows[fut.id]["identity_label"], "产权业主")
        self.assertEqual(rows[eff.id]["identity_label"], "委员")

    def test_tc_int_703_expire_due_ignores_future_seat_but_expires_past_one(self):
        """AC-206-02：到期任务不把开始日在将来的席位置为已到期；结束日已过的席位仍被置为已到期。"""
        fut, _, data = self.future_member(days=10)
        old_user, _, _ = self.make_owner()
        old = Seat.objects.create(user=old_user, position="MEMBER", term_start=today() - timedelta(days=400),
                                  term_end=today() - timedelta(days=1), status="ACTIVE", active_slot=1)
        self.assertEqual(CommitteeCommands.expire_due(today()), 1)
        self.assertEqual(Seat.objects.get(id=data["id"]).status, "ACTIVE")
        old.refresh_from_db()
        self.assertEqual(old.status, "EXPIRED")

    def test_tc_int_704_future_seat_occupies_slot_blocks_duplicate_and_counts_toward_cap(self):
        """AC-206-04（Q-OA-28=A）：已被授予未来席位的用户再授予另一席位 → 409 ALREADY_SEATED；未来席位计入该身份人数上限（上限 1 时他人 409 CAP_REACHED）。"""
        cfg = CommitteeConfig.load()
        cfg.cap_member = 1
        cfg.save()
        user, _, _ = self.future_member("MEMBER", days=20)
        self.assert_error(self.grant(user, "REPRESENTATIVE"), 409, "ALREADY_SEATED")
        other, _, _ = self.make_owner()
        self.assert_error(self.grant(other, "MEMBER", today()), 409, "CAP_REACHED")
        self.assertEqual(Seat.objects.filter(status="ACTIVE").count(), 1)

    def test_tc_int_705_seat_effective_the_day_it_starts(self):
        """AC-206-01/05：开始日前一天不生效、开始日当天起生效——用同一席位在「昨天/今天」两个时点判定（CommitteeQuery 以本地日期为准）。"""
        user, token, data = self.future_member(days=1)
        self.assertFalse(CommitteeQuery.is_member(user.id))
        tomorrow = today() + timedelta(days=1)
        with mock.patch("apps.committee.services.timezone.localdate", return_value=tomorrow):
            self.assertTrue(CommitteeQuery.is_member(user.id))
            self.assertEqual(CommitteeQuery.active_seat(user.id).id, data["id"])

    def test_tc_int_706_change_keeps_future_start_for_unstarted_seat(self):
        """IFC-312：对未生效席位变更职位（PATCH）→ 新席位沿用旧开始日、仍未生效；对已生效席位变更 → 新席位开始日=今天、已生效。"""
        user, _, data = self.future_member("MEMBER", days=20)
        resp = self.api("patch", f"/admin/committee/seats/{data['id']}", {"position": "REPRESENTATIVE"},
                        token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual((resp.data["position"], resp.data["term_start"], resp.data["effective"]),
                         ("REPRESENTATIVE", today() + timedelta(days=20), False))
        old = Seat.objects.get(id=data["id"])
        self.assertEqual((old.status, old.end_reason), ("REPLACED", "CHANGED"))
        eff, _, _ = self.make_owner()
        created = self.grant(eff, "MEMBER", today() - timedelta(days=100))
        changed = self.api("patch", f"/admin/committee/seats/{created.data['id']}", {"position": "VICE_CHAIR"},
                           token=self.admin_token)
        self.assert_ok(changed)
        self.assertEqual((changed.data["term_start"], changed.data["effective"]), (today(), True))

    def test_tc_int_707_term_start_upper_bound_and_bad_date(self):
        """OQ-04（设计假设）：开始日超过今天起约 5 年（5×366 天）→ 400「任期开始日过远」，不产生席位；恰在上界通过；非法格式 → 400 INVALID_VALUE。"""
        user, _, _ = self.make_owner()
        far = self.grant(user, "MEMBER", today() + timedelta(days=5 * 366 + 1))
        self.assertEqual(self.assert_error(far, 400, "INVALID_VALUE")["message"], "任期开始日过远")
        self.assertFalse(Seat.objects.filter(user=user).exists())
        self.assert_ok(self.grant(user, "MEMBER", today() + timedelta(days=5 * 366)), 201)
        other, _, _ = self.make_owner()
        bad = self.api("post", "/admin/committee/seats", {"user_id": other.id, "position": "MEMBER",
                                                          "term_start": "不是日期"}, token=self.admin_token)
        self.assert_error(bad, 400, "INVALID_VALUE")

    def test_tc_int_708_grant_audit_recorded_for_backfill(self):
        """AC-205-01：补录授予写 SEAT_GRANTED 审计（含 user_id 与职位），审计记录数 +1。"""
        user, _, _ = self.make_owner()
        before = AuditLog.objects.filter(action="SEAT_GRANTED").count()
        self.assert_ok(self.grant(user, "MEMBER", today() - timedelta(days=50)), 201)
        rows = AuditLog.objects.filter(action="SEAT_GRANTED")
        self.assertEqual(rows.count(), before + 1)
        self.assertEqual(rows.latest("id").detail, {"user_id": user.id, "position": "MEMBER"})
