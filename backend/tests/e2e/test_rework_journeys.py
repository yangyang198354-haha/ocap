"""PHASE_09 E2E：GROUP_C 返工（CR-011~024）后的多步用户旅程（真实 HTTP API 串联）。"""
from datetime import date, timedelta
from uuid import uuid4

from django.utils import timezone

from apps.accounts.models import User
from apps.approval.models import ApprovalInstance
from apps.core.models import Attachment, RateLimit
from apps.polls.models import Poll
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_account_no, next_phone


def _invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE", original_name="inv.pdf",
        content_type="application/pdf", size=1024, sha256="x" * 64,
        storage_path=f"tmp/{uuid4().hex}", status="TEMP")


class AccountMergeJourneyTests(ApiTestBase):
    def test_wechat_user_binds_registered_phone_and_merges(self):
        """US-012/015/016/066/072：手机号注册户主 A；仅微信登录的 W 绑定 A 的手机号 → 合并，
        A 的答卷保留，身份合并后以新令牌登录，旧令牌失效，管理员审计日志可查。"""
        # A：手机号注册 + 清册认证为户主
        phone = next_phone()
        reg = self.api("post", "/auth/register", {"phone": phone, "code": self.request_code(phone, "REGISTER")})
        self.assert_ok(reg, 201)
        a_token = reg.data["token"]
        unit_a = self.make_unit(phones=[phone])
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit_a.id}, token=a_token), 201)
        # W：仅微信登录（无手机号），在另一专有部分为同住人
        w = User.objects.create(account_no=next_account_no(), phone=None, nickname="微信W")
        unit_w = self.make_unit()
        Membership.objects.create(user=w, unit=unit_w, role="RESIDENT", source="APPLICATION", active_slot=1)
        w_token = self.token_of(w)
        # 主任发起调查，A 与 W 都作答（冲突）
        chair, chair_token, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        poll = self.api("post", "/polls", {
            "title": "合并旅程调查", "deadline": (timezone.now() + timedelta(days=2)).isoformat(),
            "kind": "SURVEY", "survey_scope": "OWNERS_AND_RESIDENTS",
            "questions": [{"title": "是否同意", "qtype": "SINGLE", "options": ["同意", "反对"]}]},
            token=chair_token)
        self.assert_ok(poll, 201)
        question = Poll.objects.get(id=poll.data["id"]).questions.get()
        for token, value in ((a_token, "同意"), (w_token, "反对")):
            self.assert_ok(self.api("post", f"/polls/{poll.data['id']}/responses",
                                    {"answers": [{"question_id": question.id, "value": value}]},
                                    token=token), 201)
        # W 绑定 A 的手机号
        RateLimit.objects.all().delete()  # 仅清理 60 秒重发限流的测试数据（同 test_journeys）
        code = self.request_me_code(w_token, "BIND_PHONE", target=phone)
        bind = self.api("post", "/me/phone/bind", {"phone": phone, "code": code}, token=w_token)
        self.assert_ok(bind)
        self.assertTrue(bind.data["merged"])
        new_token = bind.data["token"]
        # 合并后身份：户主 + 另一专有部分的同住人；一人一票；旧令牌失效
        me = self.api("get", "/me", token=new_token)
        self.assert_ok(me)
        units = {u["unit_id"]: u["role"] for u in me.data["identities"]["units"]}
        self.assertEqual(units, {unit_a.id: "HEAD", unit_w.id: "RESIDENT"})
        self.assertIn("产权业主", me.data["identities"]["labels"])
        self.assert_error(self.api("get", "/me", token=w_token), 401)
        detail = self.api("get", f"/polls/{poll.data['id']}", token=new_token)
        self.assertEqual([x["value"] for x in detail.data["my_response"]], ["同意"])
        # 手机号 / 微信两种入口进入同一账号
        RateLimit.objects.all().delete()
        again = self.login_code(phone)
        self.assert_ok(again)
        self.assertEqual(again.data["user"]["id"], reg.data["user"]["id"])
        # 管理员审计可查合并与答卷丢弃
        _, admin_token = self.make_admin()
        for action in ("ACCOUNTS_MERGED", "MERGE_ANSWER_DISCARDED"):
            logs = self.api("get", f"/admin/audit-logs?action={action}", token=admin_token)
            self.assert_ok(logs)
            self.assertGreaterEqual(logs.data["count"], 1, action)


class AdvanceSettlementJourneyTests(ApiTestBase):
    def test_advance_reimbursement_settlement_and_public_report(self):
        """US-049/050/051/061/063：备用金预借 1000 → 报销 1200 → 核销 → 报表支出合计 1200，普通业主可见。"""
        member, _, _ = self.make_owner()
        self.make_seat(member, "MEMBER")
        approver, _, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        member_token, approver_token = self.token_of(member), self.token_of(approver)
        flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[approver])

        def approve(claim_id):
            instance = ApprovalInstance.objects.get(subject_type="claim", subject_id=claim_id)
            self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                    {"action": "APPROVE"}, token=approver_token))

        adv = self.api("post", "/claims/advances", {
            "amount": "1000.00", "reason": "活动备用金", "expected_usage": "小区活动",
            "expected_settle_on": str(date.today() + timedelta(days=7)), "approval_flow_id": flow.id},
            token=member_token)
        self.assert_ok(adv, 201)
        approve(adv.data["id"])
        reimb = self.api("post", "/claims/reimbursements", {
            "amount": "1200.00", "reason": "活动开销", "occurred_on": str(date.today()),
            "invoice_ids": [str(_invoice(member).id)], "approval_flow_id": flow.id}, token=member_token)
        self.assert_ok(reimb, 201)
        approve(reimb.data["id"])
        # 核销前（预借 + 报销各自入账）支出为 2200，核销后只按差额调整
        before = self.api("post", "/ledger/reports/generate", {"period_type": "YEAR", "year": date.today().year},
                          token=member_token)
        self.assertEqual(before.data["total_expense"], "2200.00")
        settle = self.api("post", "/claims/settlements", {
            "advance_id": adv.data["id"], "reimbursement_ids": [reimb.data["id"]], "reason": "核销",
            "approval_flow_id": flow.id}, token=member_token)
        self.assert_ok(settle, 201)
        self.assertEqual(settle.data["amount"], "200.00")
        approve(settle.data["id"])
        after = self.api("post", "/ledger/reports/generate", {"period_type": "YEAR", "year": date.today().year},
                         token=member_token)
        self.assertEqual(after.data["total_expense"], "1200.00")
        self.assertEqual(after.data["balance"], "-1200.00")
        # 普通业主可读报表，且明细中不出现个人手机号
        _, owner_token, _ = self.make_owner()
        listing = self.api("get", "/ledger/reports", token=owner_token)
        self.assert_ok(listing)
        report = self.api("get", f"/ledger/reports/{after.data['id']}", token=owner_token)
        self.assert_ok(report)
        self.assertEqual(report.data["total_expense"], "1200.00")
        self.assertNotIn(member.phone, str(report.data))
        # 前端列表：备用金已显示 settlement_id（已核销）
        mine = self.api("get", "/claims?scope=mine&type=ADVANCE&status=APPROVED&page_size=100", token=member_token)
        self.assertEqual(mine.data["results"][0]["settlement_id"], settle.data["id"])


class IncomeManualEntryJourneyTests(ApiTestBase):
    def test_manual_entry_submit_approve_report_then_void(self):
        """US-058/060/061/062：逐条录入 → 提交审批 → 生效计入报表 → 作废后手动重新生成，收入归零。"""
        clerk, _, _ = self.make_owner()
        self.make_seat(clerk, "MEMBER")
        approver, _, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        clerk_token, approver_token = self.token_of(clerk), self.token_of(approver)
        flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[approver])
        today = date.today()
        sheet = self.api("post", "/admin/income/sheets", {"records": [
            {"occurred_on": str(today), "amount": "120.50", "category": "停车费", "source_note": "11月", "remark": ""},
            {"occurred_on": str(today), "amount": "79.50", "category": "广告费", "source_note": "电梯广告", "remark": ""}]},
            token=clerk_token)
        self.assert_ok(sheet, 201)
        self.assertEqual(sheet.data["total_amount"], "200.00")
        # 待审批前不计入报表
        report = self.api("post", "/ledger/reports/generate", {"period_type": "YEAR", "year": today.year}, token=clerk_token)
        self.assertEqual(report.data["total_income"], "0.00")
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sheet.data['id']}/submit",
                                {"approval_flow_id": flow.id}, token=clerk_token))
        instance = ApprovalInstance.objects.get(subject_type="income_sheet", subject_id=sheet.data["id"])
        self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                {"action": "APPROVE"}, token=approver_token))
        report = self.api("post", "/ledger/reports/generate", {"period_type": "YEAR", "year": today.year}, token=clerk_token)
        self.assertEqual((report.data["total_income"], report.data["balance"]), ("200.00", "200.00"))
        # 普通业主经 /income/sheets 读取已生效收入表
        _, owner_token, _ = self.make_owner()
        sheets = self.api("get", "/income/sheets", token=owner_token)
        self.assert_ok(sheets)
        self.assertEqual(sheets.data["results"][0]["total_amount"], "200.00")
        # 作废后重新生成，收入不再计入
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sheet.data['id']}/void", token=clerk_token))
        report = self.api("post", "/ledger/reports/generate", {"period_type": "YEAR", "year": today.year}, token=clerk_token)
        self.assertEqual(report.data["total_income"], "0.00")
