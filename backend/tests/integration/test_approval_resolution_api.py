"""PHASE_08 集成测试：审批流程与决议。"""
from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone

from apps.approval.models import ApprovalInstance
from apps.resolutions.models import Resolution
from tests.support import ApiTestBase


class ApprovalFlowTests(ApiTestBase):
    def test_designated_flow_requires_committee_approver(self):
        _, admin_token = self.make_admin()
        outsider, _ = self.make_user()
        resp = self.api("post", "/admin/approval/flows",
                        {"scope": "RESOLUTION", "mode": "DESIGNATED", "name": "指定审批",
                         "approver_ids": [outsider.id]}, token=admin_token)
        self.assert_error(resp, 422, "APPROVER_NOT_COMMITTEE_MEMBER")

    def test_half_majority_only_for_resolution(self):
        _, admin_token = self.make_admin()
        resp = self.api("post", "/admin/approval/flows",
                        {"scope": "EXPENSE", "mode": "HALF_MAJORITY", "name": "错误流程"},
                        token=admin_token)
        self.assert_error(resp, 400, "INVALID_VALUE")

    def test_flow_options_visible_to_committee(self):
        owner, _, _ = self.make_owner()
        self.make_seat(owner, "MEMBER")
        _, token = self.make_user()
        _, admin_token = self.make_admin()
        self.assert_ok(self.api("post", "/admin/approval/flows",
                                {"scope": "EXPENSE", "mode": "DESIGNATED", "name": "报销审批",
                                 "approver_ids": [owner.id]}, token=admin_token), 201)
        resp = self.api("get", "/approval/flows?scope=EXPENSE", token=token)
        self.assert_error(resp, 403)
        member_token = self.token_of(owner)
        resp = self.api("get", "/approval/flows?scope=EXPENSE", token=member_token)
        self.assert_ok(resp)
        self.assertEqual(len(resp.data), 1)

    def token_of(self, user):
        from apps.accounts.services import AccountService

        return AccountService.issue_token(user)


class DesignatedResolutionTests(ApiTestBase):
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

    def _create(self):
        return self.api("post", "/resolutions",
                        {"title": "加装电梯", "content": "拟加装电梯一部",
                         "approval_flow_id": self.flow.id}, token=self.chair_token)

    def test_designated_approve_then_public(self):
        resp = self._create()
        self.assert_ok(resp, 201)
        resolution_id = resp.data["id"]
        resp = self.api("get", f"/resolutions/{resolution_id}", token=self.approver_token)
        self.assert_ok(resp)
        instance = ApprovalInstance.objects.get(subject_type="resolution", subject_id=resolution_id)
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=self.approver_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "APPROVED")
        row = Resolution.objects.get(id=resolution_id)
        self.assertEqual(row.status, "APPROVED")
        _, owner_token, _ = self.make_owner()
        self.assert_ok(self.api("get", f"/resolutions/{resolution_id}", token=owner_token))

    def test_public_list_visible_to_any_member(self):
        resp = self._create()
        resolution_id = resp.data["id"]
        instance = ApprovalInstance.objects.get(subject_type="resolution", subject_id=resolution_id)
        self.api("post", f"/approval/instances/{instance.id}/decision",
                 {"action": "REJECT", "comment": "预算不足"}, token=self.approver_token)
        _, owner_token, _ = self.make_owner()
        resp = self.api("get", "/resolutions?scope=public", token=owner_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["count"], 1)

    def test_pending_detail_forbidden_to_stranger(self):
        resp = self._create()
        _, stranger_token = self.make_user()
        resp = self.api("get", f"/resolutions/{resp.data['id']}", token=stranger_token)
        self.assert_error(resp, 403, "FORBIDDEN")

    def test_non_approver_cannot_decide(self):
        resp = self._create()
        instance = ApprovalInstance.objects.get(subject_type="resolution",
                                                subject_id=resp.data["id"])
        _, stranger_token = self.make_user()
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=stranger_token)
        self.assert_error(resp, 403)

    def test_todo_list_for_approver(self):
        self._create()
        resp = self.api("get", "/approval/tasks?scope=RESOLUTION", token=self.approver_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["count"], 1)
        resp = self.api("get", "/approval/tasks?scope=RESOLUTION", token=self.chair_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["count"], 0)

    def test_withdraw_and_resubmit(self):
        resp = self._create()
        resolution_id = resp.data["id"]
        resp = self.api("post", f"/resolutions/{resolution_id}/withdraw", token=self.chair_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "WITHDRAWN")
        resp = self.api("post", f"/resolutions/{resolution_id}/resubmit",
                        {"title": "加装电梯（修订）", "content": "调整预算",
                         "approval_flow_id": self.flow.id}, token=self.chair_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "PENDING")
        self.assertEqual(resp.data["revision"], 2)


class HalfMajorityResolutionTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.chair, _, _ = self.make_owner()
        self.make_seat(self.chair, "CHAIR")
        self.members = []
        for _ in range(3):
            user, _, _ = self.make_owner()
            self.make_seat(user, "MEMBER")
            self.members.append(user)
        self.chair_token = self.token_of(self.chair)
        self.member_tokens = [self.token_of(u) for u in self.members]
        self.flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY")

    def token_of(self, user):
        from apps.accounts.services import AccountService

        return AccountService.issue_token(user)

    def _create(self, deadline=None):
        deadline = deadline or (timezone.now() + timedelta(days=2))
        return self.api("post", "/resolutions",
                        {"title": "公共收益使用", "content": "用于绿化改造",
                         "approval_flow_id": self.flow.id,
                         "vote_deadline": deadline.isoformat()}, token=self.chair_token)

    def test_deadline_window_validated(self):
        resp = self._create(deadline=timezone.now() + timedelta(minutes=5))
        self.assert_error(resp, 400, "VOTE_WINDOW_TOO_SHORT")

    def test_vote_requires_committee_and_once(self):
        row = self._create()
        self.assert_ok(row, 201)
        _, outsider_token = self.make_user()
        resp = self.api("post", f"/resolutions/{row.data['id']}/votes",
                        {"choice": "AGREE"}, token=outsider_token)
        self.assert_error(resp, 403, "FORBIDDEN")
        resp = self.api("post", f"/resolutions/{row.data['id']}/votes",
                        {"choice": "AGREE"}, token=self.member_tokens[0])
        self.assert_ok(resp)
        resp = self.api("post", f"/resolutions/{row.data['id']}/votes",
                        {"choice": "DISAGREE"}, token=self.member_tokens[0])
        self.assert_error(resp, 409, "ALREADY_VOTED")

    def test_judge_after_deadline_passes(self):
        row = self._create()
        resolution_id = row.data["id"]
        for token, choice in zip(self.member_tokens, ["AGREE", "AGREE", "AGREE"]):
            self.assert_ok(self.api("post", f"/resolutions/{resolution_id}/votes",
                                    {"choice": choice}, token=token))
        call_command("run_due_jobs")
        self.assertEqual(Resolution.objects.get(id=resolution_id).status, "PENDING")
        Resolution.objects.filter(id=resolution_id).update(
            vote_deadline=timezone.now() - timedelta(minutes=1))
        call_command("run_due_jobs")
        row = Resolution.objects.get(id=resolution_id)
        self.assertEqual(row.status, "APPROVED")
        self.assertEqual(row.result["agree"], 3)
        self.assertEqual(row.result["denominator"], 4)

    def test_vote_after_deadline_blocked(self):
        row = self._create()
        Resolution.objects.filter(id=row.data["id"]).update(
            vote_deadline=timezone.now() - timedelta(minutes=1))
        resp = self.api("post", f"/resolutions/{row.data['id']}/votes",
                        {"choice": "AGREE"}, token=self.member_tokens[0])
        self.assert_error(resp, 409, "VOTE_CLOSED")
