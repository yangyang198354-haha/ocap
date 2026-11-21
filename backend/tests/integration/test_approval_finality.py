"""PHASE_08 集成测试：审批失败终局与重新发起留痕（REQ-FUNC-269~275）。"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.management import call_command
from django.utils import timezone

from apps.approval.models import ApprovalInstance
from apps.claims.models import Claim
from apps.core.models import Attachment
from apps.income.models import IncomeSheet
from apps.resolutions.models import Resolution
from tests.support import ApiTestBase


def _invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE",
        original_name="inv.pdf", content_type="application/pdf", size=1024,
        sha256="x" * 64, storage_path=f"tmp/{uuid4().hex}", status="TEMP",
    )


class _TokenMixin:
    def token_of(self, user):
        from apps.accounts.services import AccountService

        return AccountService.issue_token(user)


class ResolutionFinalityTests(_TokenMixin, ApiTestBase):
    """REQ-FUNC-269/270/271/273/275：决议失败后原单终局，只能新建并留痕。"""

    def setUp(self):
        super().setUp()
        self.chair, _, _ = self.make_owner()
        self.make_seat(self.chair, "CHAIR")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.chair_token = self.token_of(self.chair)
        self.approver_token = self.token_of(self.approver)
        self.flow = self.make_flow(scope="RESOLUTION", mode="DESIGNATED",
                                   approvers=[self.approver])

    def _create(self, **overrides):
        return self.api("post", "/resolutions",
                        {"title": "加装电梯", "content": "拟加装电梯一部",
                         "approval_flow_id": self.flow.id, **overrides}, token=self.chair_token)

    def _decide(self, resolution_id, action):
        instance = ApprovalInstance.objects.get(subject_type="resolution",
                                                subject_id=resolution_id, status="PENDING")
        return self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": action, "comment": "预算不足" if action == "REJECT" else ""},
                        token=self.approver_token)

    def test_rejected_resolution_is_final_and_new_one_links_origin(self):
        old_id = self._create().data["id"]
        self.assert_ok(self._decide(old_id, "REJECT"))
        old = Resolution.objects.get(id=old_id)
        self.assertEqual(old.status, "REJECTED")

        resp = self.api("post", f"/resolutions/{old_id}/resubmit",
                        {"title": "加装电梯", "content": "改", "approval_flow_id": self.flow.id},
                        token=self.chair_token)
        self.assert_error(resp, 409, "NOT_RESUBMITTABLE")
        old.refresh_from_db()
        self.assertEqual((old.status, old.title), ("REJECTED", "加装电梯"))

        resp = self.api("post", "/resolutions",
                        {"title": "加装电梯（重新发起）", "content": "调整预算后重新表决",
                         "approval_flow_id": self.flow.id, "origin_id": old_id},
                        token=self.chair_token)
        self.assert_ok(resp, 201)
        new_id = resp.data["id"]
        self.assertEqual(resp.data["origin_id"], old_id)

        old_detail = self.api("get", f"/resolutions/{old_id}", token=self.chair_token)
        self.assert_ok(old_detail)
        self.assertEqual(old_detail.data["status"], "REJECTED")
        self.assertEqual(old_detail.data["reopened_by_id"], new_id)
        new_detail = self.api("get", f"/resolutions/{new_id}", token=self.chair_token)
        self.assertEqual(new_detail.data["origin_id"], old_id)

    def test_origin_must_be_own_rejected_resolution(self):
        other, _, _ = self.make_owner()
        self.make_seat(other, "CHAIR")
        other_token = self.token_of(other)
        other_id = self.api("post", "/resolutions",
                            {"title": "别人的决议", "content": "内容",
                             "approval_flow_id": self.flow.id}, token=other_token).data["id"]
        self.assert_ok(self._decide(other_id, "REJECT"))
        resp = self.api("post", "/resolutions",
                        {"title": "冒用", "content": "内容", "approval_flow_id": self.flow.id,
                         "origin_id": other_id}, token=self.chair_token)
        self.assert_error(resp, 400, "INVALID_VALUE")
        self.assertFalse(Resolution.objects.filter(title="冒用").exists())

    def test_withdrawn_resolution_can_still_resubmit(self):
        resolution_id = self._create().data["id"]
        self.assert_ok(self.api("post", f"/resolutions/{resolution_id}/withdraw",
                                token=self.chair_token))
        resp = self.api("post", f"/resolutions/{resolution_id}/resubmit",
                        {"title": "加装电梯（修订）", "content": "调整预算",
                         "approval_flow_id": self.flow.id}, token=self.chair_token)
        self.assert_ok(resp)
        self.assertEqual((resp.data["status"], resp.data["revision"]), ("PENDING", 2))


class HalfMajorityFinalityTests(_TokenMixin, ApiTestBase):
    """REQ-FUNC-274：到点自动判失败时同步关闭审批实例。"""

    def setUp(self):
        super().setUp()
        self.chair, _, _ = self.make_owner()
        self.make_seat(self.chair, "CHAIR")
        self.chair_token = self.token_of(self.chair)
        self.members, self.member_tokens = [], []
        for _ in range(3):
            user, _, _ = self.make_owner()
            self.make_seat(user, "MEMBER")
            self.members.append(user)
            self.member_tokens.append(self.token_of(user))
        self.flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY")

    def _create(self):
        return self.api("post", "/resolutions",
                        {"title": "公共收益使用", "content": "用于绿化改造",
                         "approval_flow_id": self.flow.id,
                         "vote_deadline": (timezone.now() + timedelta(days=2)).isoformat()},
                        token=self.chair_token)

    def test_auto_failure_closes_instance_and_blocks_resubmit(self):
        resolution_id = self._create().data["id"]
        for token, choice in zip(self.member_tokens, ["AGREE", "DISAGREE", "DISAGREE"]):
            self.assert_ok(self.api("post", f"/resolutions/{resolution_id}/votes",
                                    {"choice": choice}, token=token))
        Resolution.objects.filter(id=resolution_id).update(
            vote_deadline=timezone.now() - timedelta(minutes=1))
        call_command("run_due_jobs")

        row = Resolution.objects.get(id=resolution_id)
        self.assertEqual(row.status, "REJECTED")
        self.assertFalse(row.result["passed"])
        instance = ApprovalInstance.objects.get(subject_type="resolution",
                                                subject_id=resolution_id)
        self.assertEqual(instance.status, "REJECTED")
        self.assertIsNone(instance.pending_slot)
        self.assertIsNotNone(instance.decided_at)

        resp = self.api("get", "/resolutions?scope=todo", token=self.member_tokens[0])
        self.assert_ok(resp)
        self.assertEqual(len(resp.data), 0)

        resp = self.api("post", f"/resolutions/{resolution_id}/resubmit", {},
                        token=self.chair_token)
        self.assert_error(resp, 409, "NOT_RESUBMITTABLE")

        resp = self.api("post", "/resolutions",
                        {"title": "公共收益使用（重新发起）", "content": "调整方案",
                         "approval_flow_id": self.flow.id,
                         "vote_deadline": (timezone.now() + timedelta(days=2)).isoformat(),
                         "origin_id": resolution_id}, token=self.chair_token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["origin_id"], resolution_id)


class ClaimFinalityTests(_TokenMixin, ApiTestBase):
    """REQ-FUNC-269/271/273：报销与备用金失败后只能新建。"""

    def setUp(self):
        super().setUp()
        self.submitter, _, _ = self.make_owner()
        self.make_seat(self.submitter, "MEMBER")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.submitter_token = self.token_of(self.submitter)
        self.approver_token = self.token_of(self.approver)
        self.flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.approver])

    def _reimbursement(self, **overrides):
        payload = {"amount": "300.50", "reason": "打印费",
                   "occurred_on": str(date.today() - timedelta(days=1)),
                   "invoice_ids": [str(_invoice(self.submitter).id)],
                   "approval_flow_id": self.flow.id, **overrides}
        return self.api("post", "/claims/reimbursements", payload, token=self.submitter_token)

    def _advance(self, **overrides):
        payload = {"amount": "500.00", "reason": "出差预借", "expected_usage": "差旅",
                   "expected_settle_on": str(date.today() + timedelta(days=10)),
                   "approval_flow_id": self.flow.id, **overrides}
        return self.api("post", "/claims/advances", payload, token=self.submitter_token)

    def _reject(self, claim_id):
        instance = ApprovalInstance.objects.get(subject_type="claim", subject_id=claim_id,
                                                status="PENDING")
        self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                {"action": "REJECT", "comment": "票据不合规"},
                                token=self.approver_token))

    def test_rejected_reimbursement_is_final_and_new_one_links_origin(self):
        old_id = self._reimbursement().data["id"]
        self._reject(old_id)
        resp = self.api("post", f"/claims/{old_id}/resubmit",
                        {"amount": "300.50", "reason": "打印费",
                         "invoice_ids": [str(_invoice(self.submitter).id)],
                         "approval_flow_id": self.flow.id}, token=self.submitter_token)
        self.assert_error(resp, 409, "NOT_RESUBMITTABLE")

        resp = self._reimbursement(origin_id=old_id, reason="打印费（重新发起）")
        self.assert_ok(resp, 201)
        new_id = resp.data["id"]
        self.assertEqual(resp.data["origin_id"], old_id)
        old_detail = self.api("get", f"/claims/{old_id}", token=self.submitter_token)
        self.assert_ok(old_detail)
        self.assertEqual(old_detail.data["status"], "REJECTED")
        self.assertEqual(old_detail.data["reopened_by_id"], new_id)

    def test_rejected_advance_is_final_and_new_one_links_origin(self):
        old_id = self._advance().data["id"]
        self._reject(old_id)
        resp = self.api("post", f"/claims/{old_id}/resubmit",
                        {"amount": "500.00", "reason": "出差预借",
                         "approval_flow_id": self.flow.id}, token=self.submitter_token)
        self.assert_error(resp, 409, "NOT_RESUBMITTABLE")

        resp = self._advance(origin_id=old_id, reason="出差预借（重新发起）")
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["origin_id"], old_id)
        self.assertEqual(Claim.objects.get(id=old_id).status, "REJECTED")

    def test_withdrawn_claim_can_still_resubmit(self):
        claim_id = self._reimbursement().data["id"]
        self.assert_ok(self.api("post", f"/claims/{claim_id}/withdraw",
                                token=self.submitter_token))
        resp = self.api("post", f"/claims/{claim_id}/resubmit",
                        {"amount": "280.00", "reason": "打印费（修订）",
                         "invoice_ids": [str(_invoice(self.submitter).id)],
                         "approval_flow_id": self.flow.id}, token=self.submitter_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["revision"], 2)


class IncomeFinalityTests(_TokenMixin, ApiTestBase):
    """REQ-FUNC-269/270/273：收入表失败后只读留痕，只能新建。"""

    def setUp(self):
        super().setUp()
        self.clerk, _, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.approver, _, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.clerk_token = self.token_of(self.clerk)
        self.approver_token = self.token_of(self.approver)
        self.flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[self.approver])

    def _csv(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        rows = ["日期,金额,收入类别,来源说明,备注", "2026-06-01,300.50,物业费,6月物业费,"]
        return SimpleUploadedFile("income.csv", "\n".join(rows).encode("utf-8-sig"),
                                  content_type="text/csv")

    def _import(self, **data):
        return self.upload("/admin/income/sheets/import", {"file": self._csv()},
                           data=data, token=self.clerk_token)

    def _submit(self, sheet_id):
        return self.api("post", f"/admin/income/sheets/{sheet_id}/submit",
                        {"approval_flow_id": self.flow.id}, token=self.clerk_token)

    def _reject(self, sheet_id):
        instance = ApprovalInstance.objects.get(subject_type="income_sheet",
                                                subject_id=sheet_id, status="PENDING")
        self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                {"action": "REJECT", "comment": "金额有误"},
                                token=self.approver_token))

    def test_rejected_income_is_read_only_and_new_one_links_origin(self):
        old_id = self._import().data["id"]
        self.assert_ok(self._submit(old_id))
        self._reject(old_id)

        resp = self.api("post", f"/admin/income/sheets/{old_id}/resubmit",
                        {"approval_flow_id": self.flow.id}, token=self.clerk_token)
        self.assert_error(resp, 409, "NOT_RESUBMITTABLE")
        resp = self.api("patch", f"/admin/income/sheets/{old_id}",
                        {"records": [{"occurred_on": "2026-06-01", "amount": "999.00"}]},
                        token=self.clerk_token)
        self.assert_error(resp, 409, "IMMUTABLE")
        self.assertEqual(IncomeSheet.objects.get(id=old_id).total_amount, Decimal("300.50"))

        resp = self._import(origin_id=str(old_id))
        self.assert_ok(resp, 201)
        new_id = resp.data["id"]
        self.assertEqual(resp.data["origin_id"], old_id)
        old_detail = self.api("get", f"/admin/income/sheets/{old_id}", token=self.clerk_token)
        self.assert_ok(old_detail)
        self.assertEqual(old_detail.data["status"], "REJECTED")
        self.assertEqual(old_detail.data["reopened_by_id"], new_id)

    def test_withdrawn_income_can_still_resubmit(self):
        sheet_id = self._import().data["id"]
        self.assert_ok(self._submit(sheet_id))
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sheet_id}/withdraw",
                                token=self.clerk_token))
        resp = self.api("post", f"/admin/income/sheets/{sheet_id}/resubmit",
                        {"approval_flow_id": self.flow.id}, token=self.clerk_token)
        self.assert_ok(resp)
        self.assertEqual((resp.data["status"], IncomeSheet.objects.get(id=sheet_id).revision),
                         ("PENDING", 2))
