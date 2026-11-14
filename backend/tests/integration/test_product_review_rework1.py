"""ocap_product_review GROUP_D 缺陷回流 1 后重测（TC-INT-539 起，新增；不改动已冻结用例）。
覆盖 DEF-019（作废只属于原审批人；每个非授权角色各用独立数据）、DEF-017（失败保存审计字段）、DEF-018（合并失效审计字段）。
"""
from datetime import date

from apps.approval.models import ApprovalInstance
from apps.committee.models import Seat
from apps.committee.models import CommitteeConfig
from apps.core.audit import AuditLog
from apps.identity.services import IdentityService
from apps.income.models import IncomeSheet
from tests.support import ApiTestBase


class IncomeVoidRework1Tests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.clerk, self.clerk_token, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.approver, self.atoken, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.approver2, self.a2token, _ = self.make_owner()
        self.make_seat(self.approver2, "MEMBER")
        self.other, self.otoken, _ = self.make_owner()
        self.make_seat(self.other, "MEMBER")
        self.flow = self.make_flow(scope="INCOME", approvers=[self.approver, self.approver2])
        self.admin, self.admin_token = self.make_admin()

    def _sheet(self, amount="100.00"):
        resp = self.api("post", "/admin/income/sheets", {"records": [
            {"occurred_on": str(date.today()), "amount": amount, "category": "物业费"}]}, token=self.clerk_token)
        self.assert_ok(resp, 201)
        sid = resp.data["id"]
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sid}/submit", {"approval_flow_id": self.flow.id},
                                token=self.clerk_token))
        return sid

    def _approve(self, sid, token):
        inst = ApprovalInstance.objects.get(subject_type="income_sheet", subject_id=sid)
        self.assert_ok(self.api("post", f"/approval/instances/{inst.id}/decision", {"action": "APPROVE"}, token=token))

    def _effective_sheet(self, amount="100.00", approve_by=None):
        sid = self._sheet(amount)
        self._approve(sid, approve_by or self.atoken)
        self.assertEqual(IncomeSheet.objects.get(id=sid).status, "EFFECTIVE")
        return sid

    def _void(self, sid, token):
        return self.api("post", f"/admin/income/sheets/{sid}/void", {}, token=token)

    def _total(self):
        resp = self.api("post", "/ledger/reports/generate", {"period_type": "YEAR", "year": date.today().year},
                        token=self.clerk_token)
        self.assert_ok(resp, 201)
        return resp.data["total_income"]

    def test_tc_int_539_us_060_each_non_approver_denied_on_own_data_and_stays_effective(self):
        """TC-INT-539 / US-060（AC-060-10）：非原审批人（其他委员、录入人、管理员）各用独立已生效收入表尝试作废，
        每个都被拒绝（委员 403 / 管理员 401 或 403），收入表保持已生效且仍计入报表；原审批人对独立数据作废成功。"""
        results = {}
        for who, token in (("其他委员", self.otoken), ("录入人", self.clerk_token), ("管理员", self.admin_token)):
            sid = self._effective_sheet()
            resp = self._void(sid, token)
            results[who] = (resp.status_code, IncomeSheet.objects.get(id=sid).status)
        self.assertEqual(results["其他委员"], (403, "EFFECTIVE"))
        self.assertEqual(results["录入人"], (403, "EFFECTIVE"))
        self.assertIn(results["管理员"][0], (401, 403))
        self.assertEqual(results["管理员"][1], "EFFECTIVE")
        # 三份被拒绝作废的表仍计入报表：3 * (100.00)
        self.assertEqual(self._total(), "300.00")
        # 原审批人对独立数据成功
        sid = self._effective_sheet()
        resp = self._void(sid, self.atoken)
        self.assert_ok(resp)
        self.assertEqual(IncomeSheet.objects.get(id=sid).status, "VOID")

    def test_tc_int_540_us_060_original_approver_void_audit_and_report(self):
        """TC-INT-540 / US-060（AC-060-04）、US-064（AC-064-09）：原审批人作废 → VOID，审计含操作人、对象、结果 SUCCESS；
        重新生成报表不再计入；重复作废 409；流程指定的另一位审批人（未实际审批）同样可作废。"""
        sid = self._effective_sheet("250.00")
        self.assertEqual(self._total(), "250.00")
        self.assert_ok(self._void(sid, self.atoken))
        row = AuditLog.objects.filter(action="INCOME_VOIDED", object_id=str(sid), result="SUCCESS").get()
        self.assertEqual((row.actor_id, row.object_type), (self.approver.id, "income_sheet"))
        self.assertEqual(self._total(), "0.00")
        self.assertEqual(self._void(sid, self.atoken).status_code, 409)
        # 指定审批人之二（流程快照中的审批人，未参与决定）
        sid2 = self._effective_sheet("70.00", approve_by=self.atoken)
        self.assert_ok(self._void(sid2, self.a2token))
        self.assertEqual(IncomeSheet.objects.get(id=sid2).status, "VOID")

    def test_tc_int_541_us_060_can_void_flag_in_admin_list_and_denied_audit(self):
        """TC-INT-541 / US-060（AC-060-10；Web 作废按钮 can_void 条件的后端侧）：管理端列表项 can_void——
        已生效且当前用户是原审批人为 true；其他委员/录入人为 false；待审批、已作废为 false；被拒绝的作废尝试写 DENIED 审计，表保持生效。"""
        eff = self._effective_sheet()
        pending = self._sheet()
        voided = self._effective_sheet()
        self.assert_ok(self._void(voided, self.atoken))

        def flags(token):
            resp = self.assert_ok(self.api("get", "/admin/income/sheets?page_size=50", token=token))
            return {row["id"]: row.get("can_void") for row in resp.data["results"]}

        for token, expect_eff in ((self.atoken, True), (self.a2token, True), (self.otoken, False), (self.clerk_token, False)):
            got = flags(token)
            self.assertIs(got[eff], expect_eff)
            self.assertIs(got[pending], False)
            self.assertIs(got[voided], False)
        self.assertEqual(self._void(eff, self.otoken).status_code, 403)
        denied = AuditLog.objects.filter(action="INCOME_VOIDED", object_id=str(eff), result="DENIED")
        self.assertEqual([r.actor_id for r in denied], [self.other.id])
        self.assertEqual(IncomeSheet.objects.get(id=eff).status, "EFFECTIVE")


class CommitteeAuditRework1Tests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()

    def test_tc_int_542_us_040_failed_config_save_audit_fields_and_config_unchanged(self):
        """TC-INT-542 / US-040（AC-040-08）、US-064（AC-064-06）：非法值保存 → 400，新增 1 条 FAILURE 审计，
        操作人为该管理员、detail.field 为出错字段，配置值不变；随后合法保存仍写 SUCCESS（正例，避免只测失败分支）。"""
        self.assert_ok(self.api("put", "/admin/committee/config", {"cap_member": 4}, token=self.admin_token))
        config = CommitteeConfig.objects.first()
        before_cap = config.cap_member
        self.assertEqual(before_cap, 4)
        base = AuditLog.objects.filter(action="COMMITTEE_CONFIG_CHANGED").count()
        self.assert_error(self.api("put", "/admin/committee/config", {"cap_member": -3}, token=self.admin_token),
                          400, "INVALID_VALUE")
        rows = AuditLog.objects.filter(action="COMMITTEE_CONFIG_CHANGED").order_by("-id")
        self.assertEqual(rows.count(), base + 1)
        last = rows.first()
        self.assertEqual((last.result, last.actor_id, last.detail.get("field")), ("FAILURE", self.admin.id, "cap_member"))
        config.refresh_from_db()
        self.assertEqual(config.cap_member, before_cap)
        self.assert_ok(self.api("put", "/admin/committee/config", {"cap_member": before_cap + 1}, token=self.admin_token))
        rows = AuditLog.objects.filter(action="COMMITTEE_CONFIG_CHANGED").order_by("-id")
        self.assertEqual((rows.count(), rows.first().result), (base + 2, "SUCCESS"))

    def test_tc_int_543_us_066_merge_invalidation_audit_fields_for_each_seat_kind(self):
        """TC-INT-543 / US-066（AC-066-05）、US-064（AC-064-08）：合并使被取代席位失效（委员、业主代表各一例）时，
        各有 1 条 SEAT_INVALIDATED 审计，object_id 为被取代席位 id，detail.reason=ACCOUNT_MERGED，席位状态 MERGED；
        保留席位不产生失效审计。"""
        for lower in ("MEMBER", "REPRESENTATIVE"):
            a, _, _ = self.make_owner()
            b, _, _ = self.make_owner()
            keep = self.make_seat(a, "CHAIR")
            gone = self.make_seat(b, lower)
            IdentityService.merge_accounts(a, b, admin_id=None)
            self.assertEqual(Seat.objects.get(id=gone.id).status, "MERGED")
            rows = AuditLog.objects.filter(action="SEAT_INVALIDATED", object_id=str(gone.id))
            self.assertEqual(rows.count(), 1, lower)
            self.assertEqual(rows.get().detail.get("reason"), "ACCOUNT_MERGED")
            self.assertEqual(AuditLog.objects.filter(action="SEAT_INVALIDATED", object_id=str(keep.id)).count(), 0)
