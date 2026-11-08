"""PHASE_08 集成测试：GROUP_C 返工（CR-011~024）后的新增覆盖。

覆盖 code_review_report §9.3 建议：账号合并（绑定/换绑，答卷冲突保留主账号）、备用金核销三种差额、
run_due_jobs 触发报表生成、收入逐条录入与重复行导入、管理员下载附件。
"""
import shutil
import tempfile
from datetime import date, timedelta
from io import StringIO
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from apps.accounts.models import User
from apps.approval.models import ApprovalInstance
from apps.core.models import Attachment, AuditLog
from apps.income.models import IncomeSheet
from apps.ledger.models import LedgerEntry, LedgerReport
from apps.polls.models import Poll, PollResponse
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_account_no, next_phone


def _invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE", original_name="inv.pdf",
        content_type="application/pdf", size=1024, sha256="x" * 64,
        storage_path=f"tmp/{uuid4().hex}", status="TEMP")


class AccountMergeTests(ApiTestBase):
    """US-012 / US-014 / US-016 / US-072：绑定、换绑手机号触发合并。"""

    def setUp(self):
        super().setUp()
        self.chair, _, _ = self.make_owner()
        self.make_seat(self.chair, "CHAIR")
        self.chair_token = self.token_of(self.chair)

    def _poll(self):
        payload = {"title": "合并测试调查", "deadline": (timezone.now() + timedelta(days=2)).isoformat(),
                   "kind": "SURVEY", "survey_scope": "OWNERS_AND_RESIDENTS",
                   "questions": [{"title": "是否同意", "qtype": "SINGLE", "options": ["同意", "反对"]}]}
        resp = self.api("post", "/polls", payload, token=self.chair_token)
        self.assert_ok(resp, 201)
        poll = Poll.objects.get(id=resp.data["id"])
        return poll, poll.questions.get()

    def _answer(self, poll, question, token, value):
        resp = self.api("post", f"/polls/{poll.id}/responses",
                        {"answers": [{"question_id": question.id, "value": value}]}, token=token)
        self.assert_ok(resp, 201)

    def _wechat_user(self):
        """仅微信登录、尚无手机号的账号 W（在另一专有部分为同住人）。"""
        user = User.objects.create(account_no=next_account_no(), phone=None, nickname="微信W")
        Membership.objects.create(user=user, unit=self.make_unit(), role="RESIDENT",
                                  source="APPLICATION", active_slot=1)
        return user, self.token_of(user)

    def test_bind_phone_merges_and_keeps_primary_answer(self):
        """AC-012-01 / AC-072-01：W 绑定属于 A 的手机号 → 合并，双方答卷冲突保留 A 的，W 的被丢弃并审计。"""
        a, a_token, a_unit = self.make_owner()
        w, w_token = self._wechat_user()
        poll, question = self._poll()
        self._answer(poll, question, a_token, "同意")
        self._answer(poll, question, w_token, "反对")

        code = self.request_me_code(w_token, "BIND_PHONE", target=a.phone)
        resp = self.api("post", "/me/phone/bind", {"phone": a.phone, "code": code}, token=w_token)
        self.assert_ok(resp, 200)
        self.assertTrue(resp.data["merged"])
        self.assertEqual(resp.data["user"]["id"], a.id)
        self.assertTrue(resp.data["token"])

        # 答卷：仅保留 A 的“同意”
        responses = PollResponse.objects.filter(poll=poll)
        self.assertEqual(responses.count(), 1)
        self.assertEqual(responses.get().user_id, a.id)
        self.assertEqual(responses.get().answers.get().value, "同意")
        self.assertTrue(AuditLog.objects.filter(action="MERGE_ANSWER_DISCARDED",
                                                object_id=str(poll.id)).exists())
        self.assertTrue(AuditLog.objects.filter(action="ACCOUNTS_MERGED",
                                                object_id=str(a.id)).exists())
        # 汇总：同意 1、反对 0（一人一票）
        Poll.objects.filter(id=poll.id).update(deadline=timezone.now() - timedelta(minutes=1))
        result = self.api("get", f"/polls/{poll.id}/result", token=self.chair_token)
        self.assert_ok(result)
        counts = {o["value"]: o["count"] for o in result.data["results"]["questions"][0]["options"]}
        self.assertEqual(counts, {"同意": 1, "反对": 0})

        # W 的专有部分身份并入 A；旧令牌失效；新令牌进入 A 的账号
        self.assertEqual(Membership.objects.filter(user=a, ended_at__isnull=True).count(), 2)
        self.assert_error(self.api("get", "/me", token=w_token), 401)
        me = self.api("get", "/me", token=resp.data["token"])
        self.assert_ok(me)
        self.assertEqual(me.data["profile"]["id"], a.id)
        self.assertFalse(me.data["identities"]["is_guest"])

    def test_bind_phone_merge_moves_secondary_only_answer(self):
        """AC-072-02：仅 W 作答 → 答卷并入合并后账号，票数不变。"""
        a, _, _ = self.make_owner()
        w, w_token = self._wechat_user()
        poll, question = self._poll()
        self._answer(poll, question, w_token, "反对")
        code = self.request_me_code(w_token, "BIND_PHONE", target=a.phone)
        self.assert_ok(self.api("post", "/me/phone/bind", {"phone": a.phone, "code": code},
                                token=w_token))
        response = PollResponse.objects.get(poll=poll)
        self.assertEqual(response.user_id, a.id)
        self.assertEqual(response.answers.get().value, "反对")

    def test_bind_free_phone_does_not_merge(self):
        """AC-012-03：手机号未属于他人 → 仅绑定，不合并。"""
        w, w_token = self._wechat_user()
        phone = next_phone()
        code = self.request_me_code(w_token, "BIND_PHONE", target=phone)
        resp = self.api("post", "/me/phone/bind", {"phone": phone, "code": code}, token=w_token)
        self.assert_ok(resp)
        self.assertFalse(resp.data["merged"])
        self.assertNotIn("token", resp.data)
        w.refresh_from_db()
        self.assertEqual(w.phone, phone)

    def test_bind_wrong_code_does_not_merge(self):
        """AC-012-02：验证码错误 → 不合并、双方不变。"""
        a, _, _ = self.make_owner()
        w, w_token = self._wechat_user()
        self.request_me_code(w_token, "BIND_PHONE", target=a.phone)
        resp = self.api("post", "/me/phone/bind", {"phone": a.phone, "code": "000000"}, token=w_token)
        self.assertIn(resp.status_code, (400, 429), resp.content)
        w.refresh_from_db()
        self.assertIsNone(w.phone)
        self.assertEqual(User.objects.get(id=a.id).status, "ACTIVE")
        self.assertEqual(w.status, "ACTIVE")

    def test_change_phone_merges_into_new_phone_account(self):
        """AC-014-01 / AC-072-01：换绑到属于 B 的新号 → 以 B 为主账号合并，答卷冲突保留 B 的。"""
        a, a_token, _ = self.make_owner()
        b, b_token, _ = self.make_owner()
        poll, question = self._poll()
        self._answer(poll, question, a_token, "反对")
        self._answer(poll, question, b_token, "同意")
        old_code = self.request_me_code(a_token, "CHANGE_PHONE", target=a.phone)
        new_code = self.request_me_code(a_token, "CHANGE_PHONE", target=b.phone)
        resp = self.api("post", "/me/phone/change",
                        {"old_phone": a.phone, "new_phone": b.phone,
                         "old_code": old_code, "new_code": new_code}, token=a_token)
        self.assert_ok(resp)
        self.assertTrue(resp.data["merged"])
        self.assertEqual(resp.data["user"]["id"], b.id)
        response = PollResponse.objects.get(poll=poll)
        self.assertEqual((response.user_id, response.answers.get().value), (b.id, "同意"))
        self.assertEqual(Membership.objects.filter(user=b, ended_at__isnull=True).count(), 2)


class SettlementLedgerTests(ApiTestBase):
    """US-051 / US-050：备用金核销只按差额调整支出（CR-017）。"""

    def setUp(self):
        super().setUp()
        self.member, _, _ = self.make_owner()
        self.make_seat(self.member, "MEMBER")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.member_token = self.token_of(self.member)
        self.approver_token = self.token_of(self.approver)
        self.flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.approver])

    def _approve(self, claim_id, action="APPROVE"):
        instance = ApprovalInstance.objects.get(subject_type="claim", subject_id=claim_id)
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": action}, token=self.approver_token)
        self.assert_ok(resp)

    def _advance(self, amount="1000.00"):
        resp = self.api("post", "/claims/advances", {
            "amount": amount, "reason": "活动备用金", "expected_usage": "小区活动",
            "expected_settle_on": str(date.today() + timedelta(days=10)),
            "approval_flow_id": self.flow.id}, token=self.member_token)
        self.assert_ok(resp, 201)
        self._approve(resp.data["id"])
        return resp.data["id"]

    def _reimbursement(self, amount):
        invoice = _invoice(self.member)
        resp = self.api("post", "/claims/reimbursements", {
            "amount": amount, "reason": "活动开销", "occurred_on": str(date.today()),
            "invoice_ids": [str(invoice.id)], "approval_flow_id": self.flow.id},
            token=self.member_token)
        self.assert_ok(resp, 201)
        self._approve(resp.data["id"])
        return resp.data["id"]

    def _settle(self, advance_id, reimbursement_ids):
        resp = self.api("post", "/claims/settlements", {
            "advance_id": advance_id, "reimbursement_ids": reimbursement_ids, "reason": "活动核销",
            "approval_flow_id": self.flow.id}, token=self.member_token)
        self.assert_ok(resp, 201)
        self._approve(resp.data["id"])
        return resp.data

    def _expense_total(self):
        resp = self.api("post", "/ledger/reports/generate",
                        {"period_type": "YEAR", "year": date.today().year}, token=self.member_token)
        self.assert_ok(resp, 201)
        return resp.data["total_expense"]

    def test_advance_approved_counts_before_settlement(self):
        """AC-050-*：备用金预借审批通过即计入支出 1000.00。"""
        self._advance("1000.00")
        self.assertEqual(self._expense_total(), "1000.00")

    def test_settle_owe_more_pays_difference(self):
        """AC-051-03：预借 1000 / 报销 1200 → 差额 +200，该笔支出合计 1200（不得为 2200/2400）。"""
        advance_id = self._advance("1000.00")
        reimb_id = self._reimbursement("1200.00")
        settlement = self._settle(advance_id, [reimb_id])
        self.assertEqual(settlement["amount"], "200.00")
        self.assertEqual(self._expense_total(), "1200.00")

    def test_settle_refund_returns_cash(self):
        """AC-051-02：预借 1000 / 报销 800 → 差额 -200（多退），支出合计 800。"""
        advance_id = self._advance("1000.00")
        reimb_id = self._reimbursement("800.00")
        settlement = self._settle(advance_id, [reimb_id])
        self.assertEqual(settlement["amount"], "-200.00")
        self.assertEqual(self._expense_total(), "800.00")

    def test_settle_exact_equal_keeps_expense(self):
        """AC-051-01：预借 1000 / 报销 1000 → 差额 0，支出合计仍 1000，报销单不再重复计入。"""
        advance_id = self._advance("1000.00")
        reimb_id = self._reimbursement("1000.00")
        settlement = self._settle(advance_id, [reimb_id])
        self.assertEqual(settlement["amount"], "0.00")
        self.assertEqual(self._expense_total(), "1000.00")
        active = LedgerEntry.objects.filter(status="ACTIVE", direction="EXPENSE")
        self.assertEqual(sum(e.amount for e in active), 1000)
        self.assertFalse(LedgerEntry.objects.filter(source_type="claim", source_id=reimb_id,
                                                    status="ACTIVE").exists())

    def test_settle_requires_reimbursement_and_rejects_resettle(self):
        """AC-051-04 / AC-051-06：未关联报销单被拒；已核销的备用金不可再核销。"""
        advance_id = self._advance("1000.00")
        resp = self.api("post", "/claims/settlements", {
            "advance_id": advance_id, "reimbursement_ids": [], "reason": "x",
            "approval_flow_id": self.flow.id}, token=self.member_token)
        self.assert_error(resp, 400, "INVALID_VALUE")
        reimb_id = self._reimbursement("800.00")
        self._settle(advance_id, [reimb_id])
        reimb2 = self._reimbursement("100.00")
        resp = self.api("post", "/claims/settlements", {
            "advance_id": advance_id, "reimbursement_ids": [reimb2], "reason": "again",
            "approval_flow_id": self.flow.id}, token=self.member_token)
        self.assert_error(resp, 409, "SETTLED")


class LedgerJobTests(ApiTestBase):
    def test_run_due_jobs_generates_reports_idempotently(self):
        """AC-061-01/02 / REQ-FUNC-050：run_due_jobs 生成上一季度与上一年度报表，重复运行不重复生成。"""
        out = StringIO()
        call_command("run_due_jobs", stdout=out)
        self.assertIn("'reports_generated': 2", out.getvalue())
        self.assertEqual(LedgerReport.objects.count(), 2)
        self.assertEqual({r.period_type for r in LedgerReport.objects.all()}, {"QUARTER", "YEAR"})
        out = StringIO()
        call_command("run_due_jobs", stdout=out)
        self.assertIn("'reports_generated': 0", out.getvalue())
        self.assertEqual(LedgerReport.objects.count(), 2)


class IncomeEntryTests(ApiTestBase):
    """US-058 / US-059：逐条录入与重复行导入。"""

    def setUp(self):
        super().setUp()
        self.clerk, _, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.clerk_token = self.token_of(self.clerk)
        self.approver_token = self.token_of(self.approver)
        self.flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[self.approver])

    def _record(self, **overrides):
        return {"occurred_on": "2026-06-01", "amount": "120.50", "category": "物业费",
                "source_note": "6月", "remark": "", **overrides}

    def test_single_entry_creates_one_sheet(self):
        """AC-058-01/-08：逐条录入创建 DRAFT 收入表（来源 MANUAL），合计正确，可提交审批。"""
        resp = self.api("post", "/admin/income/sheets", {"records": [self._record()]},
                        token=self.clerk_token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["status"], "DRAFT")
        self.assertEqual(resp.data["source"], "MANUAL")
        self.assertEqual(resp.data["total_amount"], "120.50")
        sheet = IncomeSheet.objects.get(id=resp.data["id"])
        self.assertEqual(sheet.records.count(), 1)
        resp = self.api("post", f"/admin/income/sheets/{sheet.id}/submit",
                        {"approval_flow_id": self.flow.id}, token=self.clerk_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "PENDING")

    def test_single_entry_rejects_bad_amount_and_non_committee(self):
        """AC-058-02/-03：三位小数金额被拒（400 INCOME_RECORD_INVALID）；非业委会成员 403。"""
        resp = self.api("post", "/admin/income/sheets",
                        {"records": [self._record(amount="100.123")]}, token=self.clerk_token)
        body = self.assert_error(resp, 400, "INCOME_RECORD_INVALID")
        self.assertEqual(body["details"]["errors"][0]["row"], 1)
        ok = self.api("post", "/admin/income/sheets",
                      {"records": [self._record(amount="100.12")]}, token=self.clerk_token)
        self.assert_ok(ok, 201)
        _, owner_token, _ = self.make_owner()
        resp = self.api("post", "/admin/income/sheets", {"records": [self._record()]}, token=owner_token)
        self.assert_error(resp, 403, "FORBIDDEN")

    def _csv(self, rows):
        header = "日期,金额,收入类别,来源说明,备注"
        return SimpleUploadedFile("income.csv", "\n".join([header, *rows]).encode("utf-8-sig"),
                                  content_type="text/csv")

    def test_import_skips_duplicate_rows_in_file(self):
        """AC-059-02：文件内重复行被跳过并给出行号，其余行导入。"""
        rows = ["2026-06-01,10.00,物业费,A,", "2026-06-01,10.00,物业费,A,", "2026-06-01,10.00,物业费,B,"]
        resp = self.upload("/admin/income/sheets/import", {"file": self._csv(rows)}, token=self.clerk_token)
        self.assert_ok(resp, 201)
        summary = resp.data["import_summary"]
        self.assertEqual((summary["imported"], summary["failed"]), (2, 1))
        self.assertEqual(summary["errors"][0]["row"], 3)
        self.assertEqual(summary["errors"][0]["reason"], "DUPLICATE")

    def test_import_skips_rows_duplicating_pending_sheet(self):
        """AC-059-02 / 059-05：与已提交（PENDING）收入表四项全同的行跳过；全部重复则导入 0 条、不建表。"""
        rows = ["2026-06-01,10.00,物业费,A,"]
        first = self.upload("/admin/income/sheets/import", {"file": self._csv(rows)}, token=self.clerk_token)
        self.assert_ok(first, 201)
        self.assert_ok(self.api("post", f"/admin/income/sheets/{first.data['id']}/submit",
                                {"approval_flow_id": self.flow.id}, token=self.clerk_token))
        before = IncomeSheet.objects.count()
        again = self.upload("/admin/income/sheets/import", {"file": self._csv(rows)}, token=self.clerk_token)
        self.assert_ok(again, 200)
        self.assertIsNone(again.data["sheet"])
        self.assertEqual(again.data["import_summary"]["imported"], 0)
        self.assertEqual(again.data["import_summary"]["errors"][0]["reason"], "DUPLICATE")
        self.assertEqual(IncomeSheet.objects.count(), before)


class AdminAttachmentDownloadTests(ApiTestBase):
    """管理员可下载申诉证明附件（CR-015/US-026 管理端审核）；无关用户 404；未登录 401。"""

    def setUp(self):
        super().setUp()
        self._media = tempfile.mkdtemp(prefix="ocap-test-media-")
        self._override = override_settings(MEDIA_ROOT=self._media)
        self._override.enable()

    def tearDown(self):
        self._override.disable()
        shutil.rmtree(self._media, ignore_errors=True)
        super().tearDown()

    def test_admin_downloads_appeal_proof(self):
        user, token = self.make_user()
        unit = self.make_unit(phones=[next_phone()])
        content = b"\x89PNG\r\n\x1a\n" + b"proof-bytes"
        uploaded = self.upload("/attachments", {
            "file": SimpleUploadedFile("proof.png", content, content_type="image/png"),
            "purpose": "APPEAL_PROOF"}, token=token)
        self.assert_ok(uploaded, 201)
        appeal = self.api("post", "/appeals", {"unit_id": unit.id, "proof_ids": [uploaded.data["id"]]},
                          token=token)
        self.assert_ok(appeal, 201)
        _, admin_token = self.make_admin()
        path = f"/attachments/{uploaded.data['id']}/download"
        resp = self.client_for(admin_token).get(f"/api/v1{path}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(b"".join(resp.streaming_content), content)
        self.assertIn("proof.png", resp["Content-Disposition"])
        self.assertEqual(resp["X-Content-Type-Options"], "nosniff")
        # 无关普通用户不可见（404）
        _, stranger = self.make_user()
        self.assertEqual(self.client_for(stranger).get(f"/api/v1{path}").status_code, 404)
        # 未登录 401
        self.assertEqual(self.client_for().get(f"/api/v1{path}").status_code, 401)
