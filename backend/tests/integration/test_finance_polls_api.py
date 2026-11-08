"""PHASE_08 集成测试：报销、收入、台账与投票。"""
from datetime import date, timedelta
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.approval.models import ApprovalInstance
from apps.claims.models import Claim
from apps.core.models import Attachment
from apps.income.models import IncomeSheet
from apps.polls.models import Poll
from tests.support import ApiTestBase


def _make_invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE",
        original_name="inv.pdf", content_type="application/pdf", size=1024,
        sha256="x" * 64, storage_path=f"tmp/{uuid4().hex}", status="TEMP",
    )


class ClaimTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.submitter, _, _ = self.make_owner()
        self.make_seat(self.submitter, "MEMBER")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.submitter_token = self.token_of(self.submitter)
        self.approver_token = self.token_of(self.approver)
        self.flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.approver])

    def token_of(self, user):
        from apps.accounts.services import AccountService

        return AccountService.issue_token(user)

    def _reimbursement(self, **overrides):
        invoice = _make_invoice(self.submitter)
        payload = {"amount": "300.50", "reason": "打印费",
                   "occurred_on": str(date.today() - timedelta(days=1)),
                   "invoice_ids": [str(invoice.id)],
                   "approval_flow_id": self.flow.id, **overrides}
        return self.api("post", "/claims/reimbursements", payload, token=self.submitter_token)

    def test_amount_precision_and_validation(self):
        resp = self._reimbursement()
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["amount"], "300.50")
        self.assertEqual(resp.data["status"], "PENDING")
        resp = self._reimbursement(amount="300.555")
        self.assert_error(resp, 400, "INVALID_VALUE")
        resp = self._reimbursement(amount="0")
        self.assert_error(resp, 400, "INVALID_VALUE")

    def test_approve_claim(self):
        claim_id = self._reimbursement().data["id"]
        instance = ApprovalInstance.objects.get(subject_type="claim", subject_id=claim_id)
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=self.approver_token)
        self.assert_ok(resp)
        claim = Claim.objects.get(id=claim_id)
        self.assertEqual(claim.status, "APPROVED")
        self.assertEqual(resp.data["status"], "APPROVED")

    def test_self_approval_forbidden(self):
        flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.submitter])
        resp = self._reimbursement(approval_flow_id=flow.id)
        if resp.status_code == 201:
            instance = ApprovalInstance.objects.get(subject_type="claim",
                                                    subject_id=resp.data["id"])
            resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                            {"action": "APPROVE"}, token=self.submitter_token)
        self.assertIn(resp.status_code, (400, 403, 422), resp.content)

    def test_withdraw_and_resubmit(self):
        claim_id = self._reimbursement().data["id"]
        resp = self.api("post", f"/claims/{claim_id}/withdraw", token=self.submitter_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "WITHDRAWN")
        invoice = _make_invoice(self.submitter)
        resp = self.api("post", f"/claims/{claim_id}/resubmit",
                        {"amount": "280.00", "reason": "打印费（修订）",
                         "invoice_ids": [str(invoice.id)],
                         "approval_flow_id": self.flow.id}, token=self.submitter_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["revision"], 2)
        self.assertEqual(resp.data["amount"], "280.00")

    def test_advance_and_settlement(self):
        # 预借
        advance = self.api("post", "/claims/advances",
                           {"amount": "500.00", "reason": "出差预借",
                            "expected_usage": "差旅",
                            "expected_settle_on": str(date.today() + timedelta(days=10)),
                            "approval_flow_id": self.flow.id}, token=self.submitter_token)
        self.assert_ok(advance, 201)
        advance_instance = ApprovalInstance.objects.get(subject_type="claim",
                                                        subject_id=advance.data["id"])
        self.api("post", f"/approval/instances/{advance_instance.id}/decision",
                 {"action": "APPROVE"}, token=self.approver_token)
        # 报销
        reimb = self._reimbursement(amount="700.00")
        self.assert_ok(reimb, 201)
        reimb_instance = ApprovalInstance.objects.get(subject_type="claim",
                                                      subject_id=reimb.data["id"])
        self.api("post", f"/approval/instances/{reimb_instance.id}/decision",
                 {"action": "APPROVE"}, token=self.approver_token)
        # 结算：金额 = 报销 − 预借 = 200
        settle = self.api("post", "/claims/settlements",
                          {"advance_id": advance.data["id"],
                           "reimbursement_ids": [reimb.data["id"]],
                           "reason": "核销",
                           "approval_flow_id": self.flow.id}, token=self.submitter_token)
        self.assert_ok(settle, 201)
        self.assertEqual(settle.data["type"], "SETTLEMENT")
        self.assertEqual(settle.data["amount"], "200.00")

    def test_settlement_requires_income_member(self):
        advance = self.api("post", "/claims/advances",
                           {"amount": "100.00", "reason": "备用金",
                            "expected_usage": "备用",
                            "expected_settle_on": str(date.today() + timedelta(days=5)),
                            "approval_flow_id": self.flow.id}, token=self.submitter_token)
        self.assert_ok(advance, 201)
        adv_inst = ApprovalInstance.objects.get(subject_type="claim", subject_id=advance.data["id"])
        self.api("post", f"/approval/instances/{adv_inst.id}/decision",
                 {"action": "APPROVE"}, token=self.approver_token)
        owner, owner_token, _ = self.make_owner()
        resp = self.api("post", "/claims/settlements",
                        {"advance_id": advance.data["id"], "reimbursement_ids": [],
                         "reason": "x", "approval_flow_id": self.flow.id}, token=owner_token)
        self.assert_error(resp, 403, "FORBIDDEN")

    def test_stranger_cannot_view_claim(self):
        claim_id = self._reimbursement().data["id"]
        _, stranger_token = self.make_user()
        resp = self.api("get", f"/claims/{claim_id}", token=stranger_token)
        self.assert_error(resp, 403, "FORBIDDEN")

    def test_admin_can_list_claims(self):
        self._reimbursement()
        _, admin_token = self.make_admin()
        resp = self.api("get", "/admin/claims", token=admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["count"], 1)


class IncomeTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.clerk, _, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.clerk_token = self.token_of(self.clerk)
        self.approver_token = self.token_of(self.approver)
        self.flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[self.approver])

    def token_of(self, user):
        from apps.accounts.services import AccountService

        return AccountService.issue_token(user)

    def _csv(self, rows=None):
        rows = rows or ["日期,金额,收入类别,来源说明,备注",
                        "2026-06-01,300.50,物业费,6月物业费,"]
        return SimpleUploadedFile("income.csv", "\n".join(rows).encode("utf-8-sig"),
                                  content_type="text/csv")

    def _import(self, token=None):
        return self.upload("/admin/income/sheets/import", {"file": self._csv()},
                           token=token or self.clerk_token)

    def test_import_totals_and_validation(self):
        resp = self._import()
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["total_amount"], "300.50")
        self.assertEqual(resp.data["import_summary"]["imported"], 1)

    def test_import_requires_committee(self):
        _, owner_token, _ = self.make_owner()
        resp = self._import(token=owner_token)
        self.assert_error(resp, 403, "FORBIDDEN")

    def test_import_row_error_ratio(self):
        rows = ["日期,金额,收入类别,来源说明,备注"]
        for i in range(40):
            rows.append(f"2026-06-01,10.00,物业费,项目{i},")
        rows += ["bad,10.00,物业费,,", "2026-06-01,-1,物业费,,",
                 "2026-06-01,1.001,物业费,,"]
        resp = self.upload("/admin/income/sheets/import", {"file": self._csv(rows)},
                           token=self.clerk_token)
        self.assert_error(resp, 400, "IMPORT_ROW_ERRORS")

    def test_import_missing_columns(self):
        resp = self.upload("/admin/income/sheets/import",
                           {"file": SimpleUploadedFile("bad.csv", b"\xef\xbb\xbf\xe6\x97\xa5\xe6\x9c\x9f\n2026-01-01\n")},
                           token=self.clerk_token)
        self.assert_error(resp, 400, "IMPORT_COLUMNS_MISSING")

    def test_submit_approve_and_void(self):
        sheet_id = self._import().data["id"]
        resp = self.api("post", f"/admin/income/sheets/{sheet_id}/submit",
                        {"approval_flow_id": self.flow.id}, token=self.clerk_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "PENDING")
        instance = ApprovalInstance.objects.get(subject_type="income_sheet", subject_id=sheet_id)
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=self.approver_token)
        self.assert_ok(resp)
        self.assertEqual(IncomeSheet.objects.get(id=sheet_id).status, "EFFECTIVE")
        resp = self.api("post", f"/admin/income/sheets/{sheet_id}/void", token=self.clerk_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "VOID")

    def test_submit_empty_sheet(self):
        sheet = IncomeSheet.objects.create(submitted_by=self.clerk)
        resp = self.api("post", f"/admin/income/sheets/{sheet.id}/submit",
                        {"approval_flow_id": self.flow.id}, token=self.clerk_token)
        self.assert_error(resp, 409, "INCOME_SHEET_EMPTY")

    def test_approved_sheets_visible_to_any_member(self):
        sheet_id = self._import().data["id"]
        self.api("post", f"/admin/income/sheets/{sheet_id}/submit",
                 {"approval_flow_id": self.flow.id}, token=self.clerk_token)
        instance = ApprovalInstance.objects.get(subject_type="income_sheet", subject_id=sheet_id)
        self.api("post", f"/approval/instances/{instance.id}/decision",
                 {"action": "APPROVE"}, token=self.approver_token)
        _, owner_token, _ = self.make_owner()
        resp = self.api("get", "/income/sheets", token=owner_token)
        self.assert_ok(resp)
        resp = self.api("get", f"/income/sheets/{sheet_id}", token=owner_token)
        self.assert_ok(resp)


class LedgerTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.clerk, _, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.clerk_token = self.token_of(self.clerk)
        self.approver_token = self.token_of(self.approver)
        self.income_flow = self.make_flow(scope="INCOME", mode="DESIGNATED",
                                          approvers=[self.approver])
        self.expense_flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED",
                                           approvers=[self.approver])
        self._seed()

    def token_of(self, user):
        from apps.accounts.services import AccountService

        return AccountService.issue_token(user)

    def _seed(self):
        csv = SimpleUploadedFile("income.csv",
                                 "日期,金额,收入类别,来源说明,备注\n"
                                 "2026-06-01,300.50,物业费,6月物业费,\n"
                                 .encode("utf-8-sig"), content_type="text/csv")
        sheet_id = self.upload("/admin/income/sheets/import", {"file": csv},
                               token=self.clerk_token).data["id"]
        self.api("post", f"/admin/income/sheets/{sheet_id}/submit",
                 {"approval_flow_id": self.income_flow.id}, token=self.clerk_token)
        instance = ApprovalInstance.objects.get(subject_type="income_sheet", subject_id=sheet_id)
        self.api("post", f"/approval/instances/{instance.id}/decision",
                 {"action": "APPROVE"}, token=self.approver_token)
        invoice = _make_invoice(self.clerk)
        claim = self.api("post", "/claims/reimbursements",
                         {"amount": "100.00", "reason": "绿化",
                          "occurred_on": str(date.today() - timedelta(days=1)),
                          "invoice_ids": [str(invoice.id)],
                          "approval_flow_id": self.expense_flow.id}, token=self.clerk_token)
        claim_instance = ApprovalInstance.objects.get(subject_type="claim",
                                                      subject_id=claim.data["id"])
        self.api("post", f"/approval/instances/{claim_instance.id}/decision",
                 {"action": "APPROVE"}, token=self.approver_token)

    def _generate(self, token=None):
        return self.api("post", "/ledger/reports/generate",
                        {"period_type": "YEAR", "year": 2026},
                        token=token or self.clerk_token)

    def test_generate_totals_and_precision(self):
        resp = self._generate()
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["total_income"], "300.50")
        self.assertEqual(resp.data["total_expense"], "100.00")
        self.assertEqual(resp.data["balance"], "200.50")

    def test_report_visible_to_any_member(self):
        self._generate()
        _, owner_token, _ = self.make_owner()
        resp = self.api("get", "/ledger/reports", token=owner_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["count"], 1)

    def test_regenerate_same_period(self):
        first = self._generate()
        self.assert_ok(first, 201)
        second = self._generate()
        self.assert_ok(second, 201)
        self.assertEqual(second.data["id"], first.data["id"])

    def test_non_committee_cannot_generate(self):
        _, owner_token, _ = self.make_owner()
        resp = self._generate(token=owner_token)
        self.assert_error(resp, 403, "FORBIDDEN")


class PollTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.chair, _, _ = self.make_owner()
        self.make_seat(self.chair, "CHAIR")
        self.member, _, _ = self.make_owner()
        self.make_seat(self.member, "MEMBER")
        self.chair_token = self.token_of(self.chair)
        self.member_token = self.token_of(self.member)
        self._question = [{"title": "是否同意加装电梯", "qtype": "SINGLE",
                           "options": ["同意", "反对"]}]

    def token_of(self, user):
        from apps.accounts.services import AccountService

        return AccountService.issue_token(user)

    def _create(self, token=None, deadline=None, **overrides):
        deadline = deadline or (timezone.now() + timedelta(days=2))
        payload = {"title": "加装电梯调查", "description": "请投票",
                   "deadline": deadline.isoformat(), "kind": "SURVEY",
                   "survey_scope": "OWNERS_ONLY", "questions": self._question, **overrides}
        return self.api("post", "/polls", payload, token=token or self.chair_token)

    def test_only_chair_or_vice_creates(self):
        self.assert_ok(self._create(), 201)
        resp = self._create(token=self.member_token)
        self.assert_error(resp, 403, "FORBIDDEN")

    def test_deadline_window(self):
        resp = self._create(deadline=timezone.now() + timedelta(minutes=5))
        self.assert_error(resp, 400, "VOTE_WINDOW_TOO_SHORT")

    def test_vote_and_duplicate(self):
        poll_id = self._create().data["id"]
        question = Poll.objects.get(id=poll_id).questions.get()
        answers = [{"question_id": question.id, "value": "同意"}]
        resp = self.api("post", f"/polls/{poll_id}/responses", {"answers": answers},
                        token=self.member_token)
        self.assert_ok(resp, 201)
        resp = self.api("post", f"/polls/{poll_id}/responses", {"answers": answers},
                        token=self.member_token)
        self.assert_error(resp, 409, "ALREADY_VOTED")

    def test_invalid_option_rejected(self):
        poll_id = self._create().data["id"]
        question = Poll.objects.get(id=poll_id).questions.get()
        resp = self.api("post", f"/polls/{poll_id}/responses",
                        {"answers": [{"question_id": question.id, "value": "NOPE"}]},
                        token=self.member_token)
        self.assert_error(resp, 400, "INVALID_VALUE")

    def test_owner_participates_in_survey(self):
        poll_id = self._create().data["id"]
        question = Poll.objects.get(id=poll_id).questions.get()
        _, owner_token, _ = self.make_owner()
        resp = self.api("post", f"/polls/{poll_id}/responses",
                        {"answers": [{"question_id": question.id, "value": "同意"}]},
                        token=owner_token)
        self.assert_ok(resp, 201)

    def test_results_after_close(self):
        poll_id = self._create().data["id"]
        question = Poll.objects.get(id=poll_id).questions.get()
        self.api("post", f"/polls/{poll_id}/responses",
                 {"answers": [{"question_id": question.id, "value": "同意"}]},
                 token=self.member_token)
        resp = self.api("get", f"/polls/{poll_id}/result", token=self.member_token)
        self.assert_error(resp, 409, "NOT_CLOSED")
        Poll.objects.filter(id=poll_id).update(deadline=timezone.now() - timedelta(minutes=1))
        resp = self.api("get", f"/polls/{poll_id}/result", token=self.member_token)
        self.assert_ok(resp)
        options = resp.data["results"]["questions"][0]["options"]
        agree = next(o for o in options if o["value"] == "同意")
        self.assertEqual(agree["count"], 1)
