"""PHASE_09 E2E：多步用户旅程（真实 HTTP API 串联）。"""
from datetime import date, timedelta
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone

from apps.approval.models import ApprovalInstance
from apps.core.models import Attachment, RateLimit
from apps.income.models import IncomeSheet
from apps.polls.models import Poll
from apps.resolutions.models import Resolution
from tests.support import ApiTestBase, next_phone


def _make_invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE",
        original_name="inv.pdf", content_type="application/pdf", size=1024,
        sha256="x" * 64, storage_path=f"tmp/{uuid4().hex}", status="TEMP",
    )


class OwnerOnboardingJourneyTests(ApiTestBase):
    def test_register_certify_and_profile(self):
        """US-001/003/021/023：注册 → 认证户主 → 完善资料。"""
        phone = next_phone()
        code = self.request_code(phone, "REGISTER")
        reg = self.api("post", "/auth/register", {"phone": phone, "code": code})
        self.assert_ok(reg, 201)
        token = reg.data["token"]
        me = self.api("get", "/me", token=token)
        self.assert_ok(me)
        self.assertEqual(me.data["identities"]["labels"], ["游客"])
        unit = self.make_unit(phones=[phone])
        cert = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_ok(cert, 201)
        self.assertEqual(cert.data["role"], "HEAD")
        me = self.api("get", "/me", token=token)
        self.assert_ok(me)
        self.assertIn("产权业主", me.data["identities"]["labels"])
        profile = self.api("patch", "/me/profile", {"nickname": "业主小李"}, token=token)
        self.assert_ok(profile)
        self.assertEqual(profile.data["nickname"], "业主小李")


class ResidentJourneyTests(ApiTestBase):
    def test_owner_approves_then_removes_resident(self):
        """US-025/026：同住人申请 → 产权业主审批 → 移除。"""
        unit = self.make_unit(phones=[next_phone()])
        owner, owner_token = self.make_user(phone=unit.phones.all()[0].phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=owner_token), 201)
        resident, resident_token = self.make_user()
        app = self.api("post", "/resident-applications", {"unit_id": unit.id}, token=resident_token)
        self.assert_ok(app, 201)
        todo = self.api("get", "/resident-applications/to-review", token=owner_token)
        self.assert_ok(todo)
        self.assertEqual(todo.data[0]["id"], app.data["id"])
        decision = self.api("post", f"/resident-applications/{app.data['id']}/decision",
                            {"decision": "APPROVE"}, token=owner_token)
        self.assert_ok(decision)
        me = self.api("get", "/me", token=resident_token)
        self.assert_ok(me)
        self.assertIn("同住人", me.data["identities"]["labels"])
        removed = self.api("delete", f"/units/{unit.id}/residents/{resident.id}", token=owner_token)
        self.assert_ok(removed, 204)
        me = self.api("get", "/me", token=resident_token)
        self.assertNotIn("同住人", me.data["identities"]["labels"])


class AppealJourneyTests(ApiTestBase):
    def test_appeal_restores_owner_identity(self):
        """US-028/029：认证失败 → 申诉 → 管理员核准成为业主。"""
        user, token = self.make_user()
        unit = self.make_unit(phones=[next_phone()])
        rejected = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_error(rejected, 422, "PHONE_NOT_IN_REGISTRY")
        proof = SimpleUploadedFile("proof.png", b"\x89PNG\r\n\x1a\n" + b"3" * 32,
                                   content_type="image/png")
        uploaded = self.upload("/attachments", {"file": proof, "purpose": "APPEAL_PROOF"}, token=token)
        self.assert_ok(uploaded, 201)
        appeal = self.api("post", "/appeals", {"unit_id": unit.id,
                                               "proof_ids": [uploaded.data["id"]]}, token=token)
        self.assert_ok(appeal, 201)
        _, admin_token = self.make_admin()
        decision = self.api("post", f"/admin/appeals/{appeal.data['id']}/decision",
                            {"decision": "APPROVE"}, token=admin_token)
        self.assert_ok(decision)
        me = self.api("get", "/me", token=token)
        self.assert_ok(me)
        self.assertIn("产权业主", me.data["identities"]["labels"])


class DesignatedResolutionJourneyTests(ApiTestBase):
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

    def test_resolution_approve_and_public_read(self):
        """US-044/045/048：发起 → 指定人审批 → 全体可查。"""
        created = self.api("post", "/resolutions",
                           {"title": "外墙维修", "content": "维修北侧外墙",
                            "approval_flow_id": self.flow.id}, token=self.chair_token)
        self.assert_ok(created, 201)
        resolution_id = created.data["id"]
        instance = ApprovalInstance.objects.get(subject_type="resolution", subject_id=resolution_id)
        todo = self.api("get", "/approval/tasks?scope=RESOLUTION", token=self.approver_token)
        self.assert_ok(todo)
        self.assertEqual(todo.data["count"], 1)
        decided = self.api("post", f"/approval/instances/{instance.id}/decision",
                           {"action": "APPROVE"}, token=self.approver_token)
        self.assert_ok(decided)
        self.assertEqual(decided.data["status"], "APPROVED")
        _, owner_token, _ = self.make_owner()
        detail = self.api("get", f"/resolutions/{resolution_id}", token=owner_token)
        self.assert_ok(detail)
        listing = self.api("get", "/resolutions?scope=public", token=owner_token)
        self.assert_ok(listing)


class HalfMajorityResolutionJourneyTests(ApiTestBase):
    def test_vote_then_expire_and_publish(self):
        """US-046/047：半数表决 → 到期判定 → 结果公开。"""
        chair, _, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        members = []
        for _ in range(3):
            user, _, _ = self.make_owner()
            self.make_seat(user, "MEMBER")
            members.append(user)
        flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY")
        created = self.api("post", "/resolutions",
                           {"title": "公共收益使用", "content": "绿化改造",
                            "approval_flow_id": flow.id,
                            "vote_deadline": (timezone.now() + timedelta(days=1)).isoformat()},
                           token=self.token_of(chair))
        self.assert_ok(created, 201)
        for user in members:
            resp = self.api("post", f"/resolutions/{created.data['id']}/votes",
                            {"choice": "AGREE"}, token=self.token_of(user))
            self.assert_ok(resp)
        Resolution.objects.filter(id=created.data["id"]).update(
            vote_deadline=timezone.now() - timedelta(minutes=1))
        call_command("run_due_jobs")
        row = Resolution.objects.get(id=created.data["id"])
        self.assertEqual(row.status, "APPROVED")
        _, owner_token, _ = self.make_owner()
        detail = self.api("get", f"/resolutions/{created.data['id']}", token=owner_token)
        self.assert_ok(detail)
        self.assertEqual(detail.data["result"]["agree"], 3)


class FinanceCommitteeJourneyTests(ApiTestBase):
    def test_income_expense_and_ledger(self):
        """US-058/059/061/062：收入导入审批 → 报销审批 → 台账生成。"""
        clerk, _, _ = self.make_owner()
        self.make_seat(clerk, "MEMBER")
        approver, _, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        clerk_token, approver_token = self.token_of(clerk), self.token_of(approver)
        income_flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[approver])
        expense_flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[approver])
        file = SimpleUploadedFile("income.csv",
                                  "日期,金额,收入类别,来源说明,备注\n"
                                  "2026-06-01,300.50,物业费,6月物业费,\n"
                                  .encode("utf-8-sig"), content_type="text/csv")
        sheet = self.upload("/admin/income/sheets/import", {"file": file}, token=clerk_token)
        self.assert_ok(sheet, 201)
        self.assertEqual(sheet.data["total_amount"], "300.50")
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sheet.data['id']}/submit",
                                {"approval_flow_id": income_flow.id}, token=clerk_token))
        instance = ApprovalInstance.objects.get(subject_type="income_sheet",
                                                subject_id=sheet.data["id"])
        self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                {"action": "APPROVE"}, token=approver_token))
        self.assertEqual(IncomeSheet.objects.get(id=sheet.data["id"]).status, "EFFECTIVE")
        invoice = _make_invoice(clerk)
        claim = self.api("post", "/claims/reimbursements",
                         {"amount": "100.00", "reason": "绿化养护",
                          "occurred_on": str(date.today() - timedelta(days=1)),
                          "invoice_ids": [str(invoice.id)],
                          "approval_flow_id": expense_flow.id}, token=clerk_token)
        self.assert_ok(claim, 201)
        claim_instance = ApprovalInstance.objects.get(subject_type="claim",
                                                      subject_id=claim.data["id"])
        self.assert_ok(self.api("post", f"/approval/instances/{claim_instance.id}/decision",
                                {"action": "APPROVE"}, token=approver_token))
        report = self.api("post", "/ledger/reports/generate",
                          {"period_type": "YEAR", "year": 2026},
                          token=clerk_token)
        self.assert_ok(report, 201)
        self.assertEqual(report.data["total_income"], "300.50")
        self.assertEqual(report.data["total_expense"], "100.00")
        self.assertEqual(report.data["balance"], "200.50")


class FinanceTransparencyJourneyTests(ApiTestBase):
    def test_any_member_reads_reports(self):
        """US-063：财务报表所有登录用户可见（含收入表与台账）。"""
        clerk, _, _ = self.make_owner()
        self.make_seat(clerk, "MEMBER")
        _, admin_token = self.make_admin()
        sheet = IncomeSheet.objects.create(submitted_by=clerk, status="EFFECTIVE",
                                           period_start=timezone.localdate(),
                                           period_end=timezone.localdate())
        self.assert_ok(self.api("post", "/ledger/reports/generate",
                                {"period_type": "YEAR", "year": 2026},
                                token=self.token_of(clerk)), 201)
        _, owner_token, _ = self.make_owner()
        sheets = self.api("get", "/income/sheets", token=owner_token)
        self.assert_ok(sheets)
        reports = self.api("get", "/ledger/reports", token=owner_token)
        self.assert_ok(reports)


class PollJourneyTests(ApiTestBase):
    def test_committee_poll_lifecycle(self):
        """US-052/053：业委会发起 → 成员投票 → 到期出结果。"""
        chair, _, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        member, _, _ = self.make_owner()
        self.make_seat(member, "MEMBER")
        created = self.api("post", "/polls",
                           {"title": "电梯维保方案",
                            "deadline": (timezone.now() + timedelta(days=1)).isoformat(),
                            "kind": "SURVEY", "survey_scope": "OWNERS_ONLY",
                            "questions": [{"title": "是否同意方案A", "qtype": "SINGLE",
                                           "options": ["同意", "反对"]}]},
                           token=self.token_of(chair))
        self.assert_ok(created, 201)
        question = Poll.objects.get(id=created.data["id"]).questions.get()
        voted = self.api("post", f"/polls/{created.data['id']}/responses",
                         {"answers": [{"question_id": question.id, "value": "同意"}]},
                         token=self.token_of(member))
        self.assert_ok(voted, 201)
        Poll.objects.filter(id=created.data["id"]).update(
            deadline=timezone.now() - timedelta(minutes=1))
        result = self.api("get", f"/polls/{created.data['id']}/result", token=self.token_of(member))
        self.assert_ok(result)
        options = result.data["results"]["questions"][0]["options"]
        agree = next(o for o in options if o["value"] == "同意")
        self.assertEqual(agree["count"], 1)


class PollRepresentationJourneyTests(ApiTestBase):
    def test_owner_and_representative_can_respond(self):
        """US-054/055：调查对象为产权业主/同住人，业主代表可参与代表投票。"""
        chair, _, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        rep, _, _ = self.make_owner()
        self.make_seat(rep, "REPRESENTATIVE")
        owner, owner_token, _ = self.make_owner()
        created = self.api("post", "/polls",
                           {"title": "满意度调查",
                            "deadline": (timezone.now() + timedelta(days=1)).isoformat(),
                            "kind": "SURVEY", "survey_scope": "OWNERS_ONLY",
                            "questions": [{"title": "总体满意度", "qtype": "SINGLE",
                                           "options": ["满意", "不满意"]}]},
                           token=self.token_of(chair))
        self.assert_ok(created, 201)
        question = Poll.objects.get(id=created.data["id"]).questions.get()
        answers = [{"question_id": question.id, "value": "满意"}]
        rep_resp = self.api("post", f"/polls/{created.data['id']}/responses",
                            {"answers": answers}, token=self.token_of(rep))
        self.assert_ok(rep_resp, 201)
        owner_resp = self.api("post", f"/polls/{created.data['id']}/responses",
                              {"answers": answers}, token=owner_token)
        self.assert_ok(owner_resp, 201)


class AccountLifecycleJourneyTests(ApiTestBase):
    def test_register_password_login_and_cancel(self):
        """US-001/011/016：注册 → 设置密码 → 密码登录 → 注销。"""
        phone = next_phone()
        code = self.request_code(phone, "REGISTER")
        reg = self.api("post", "/auth/register", {"phone": phone, "code": code})
        self.assert_ok(reg, 201)
        token = reg.data["token"]
        password = "Ocap2026pass"
        self.assert_ok(self.api("put", "/me/password",
                                {"password": password, "password_confirm": password},
                                token=token), 204)
        login = self.api("post", "/auth/login/password",
                         {"identifier": reg.data["user"]["account_no"], "password": password})
        self.assert_ok(login)
        RateLimit.objects.filter(key__contains=phone).delete()
        cancel_code = self.request_me_code(token, "CANCEL")
        cancelled = self.api("post", "/me/cancel", {"phone": phone, "code": cancel_code}, token=token)
        self.assert_ok(cancelled, 204)
        self.assert_error(self.api("get", "/me", token=token), 401)
