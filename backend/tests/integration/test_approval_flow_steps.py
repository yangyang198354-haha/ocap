"""GROUP_D 集成测试：多步审批、或签/会签、时间线（ocap_approval_flow）。"""
import pathlib

from django.urls import resolve

from apps.approval.models import ApprovalFlow, ApprovalInstance
from apps.resolutions.models import Resolution
from tests.support import ApiTestBase


class ApprovalStepsBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.chair, _, _ = self.make_owner()
        self.make_seat(self.chair, "CHAIR")
        self.chair_token = self.token_of(self.chair)
        self.a1, _, _ = self.make_owner()
        self.make_seat(self.a1, "MEMBER")
        self.a2, _, _ = self.make_owner()
        self.make_seat(self.a2, "MEMBER")
        self.a3, _, _ = self.make_owner()
        self.make_seat(self.a3, "MEMBER")
        self.t1 = self.token_of(self.a1)
        self.t2 = self.token_of(self.a2)
        self.t3 = self.token_of(self.a3)
        _, self.admin_token = self.make_admin()

    def make_steps_flow(self, steps, scope="RESOLUTION"):
        resp = self.api("post", "/admin/approval/flows",
                        {"scope": scope, "mode": "DESIGNATED", "name": "多步流程", "steps": steps},
                        token=self.admin_token)
        self.assert_ok(resp, 201)
        return ApprovalFlow.objects.get(id=resp.data["id"])

    def submit(self, flow):
        resp = self.api("post", "/resolutions",
                        {"title": "加装电梯", "content": "拟加装电梯一部", "approval_flow_id": flow.id},
                        token=self.chair_token)
        self.assert_ok(resp, 201)
        return resp.data["id"]

    def instance_of(self, resolution_id):
        return ApprovalInstance.objects.get(subject_type="resolution", subject_id=resolution_id)

    def decide(self, instance, action, token, comment=""):
        return self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": action, "comment": comment}, token=token)


class AdminFlowStepsTests(ApprovalStepsBase):
    def test_create_flow_with_steps(self):
        flow = self.make_steps_flow([
            {"name": "财务初审", "strategy": "ANY", "approver_ids": [self.a1.id]},
            {"name": "主任终审", "strategy": "ALL", "approver_ids": [self.a2.id, self.a3.id]},
        ])
        resp = self.api("get", f"/admin/approval/flows/{flow.id}", token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["step_count"], 2)
        self.assertEqual([s["name"] for s in resp.data["steps"]], ["财务初审", "主任终审"])
        self.assertEqual(resp.data["steps"][1]["strategy"], "ALL")

    def test_reject_empty_step_name(self):
        resp = self.api("post", "/admin/approval/flows",
                        {"scope": "RESOLUTION", "mode": "DESIGNATED", "name": "多步",
                         "steps": [{"name": "", "strategy": "ANY", "approver_ids": [self.a1.id]}]},
                        token=self.admin_token)
        self.assert_error(resp, 422, "INVALID_STEPS")

    def test_reject_step_without_approver(self):
        resp = self.api("post", "/admin/approval/flows",
                        {"scope": "RESOLUTION", "mode": "DESIGNATED", "name": "多步",
                         "steps": [{"name": "初审", "strategy": "ANY", "approver_ids": []}]},
                        token=self.admin_token)
        self.assert_error(resp, 422, "INVALID_STEPS")

    def test_reject_non_member_step_approver(self):
        outsider, _ = self.make_user()
        resp = self.api("post", "/admin/approval/flows",
                        {"scope": "RESOLUTION", "mode": "DESIGNATED", "name": "多步",
                         "steps": [{"name": "初审", "strategy": "ANY", "approver_ids": [outsider.id]}]},
                        token=self.admin_token)
        self.assert_error(resp, 422, "APPROVER_NOT_COMMITTEE_MEMBER")

    def test_delete_unreferenced_flow_physically(self):
        flow = self.make_steps_flow([
            {"name": "初审", "strategy": "ANY", "approver_ids": [self.a1.id]},
        ])
        self.assert_ok(self.api("delete", f"/admin/approval/flows/{flow.id}", token=self.admin_token), 204)
        self.assertFalse(ApprovalFlow.objects.filter(id=flow.id).exists())
        self.assertEqual(flow.steps.count(), 0)

    def test_delete_flow_in_use_rejected_with_reason(self):
        flow = self.make_steps_flow([
            {"name": "初审", "strategy": "ANY", "approver_ids": [self.a1.id]},
        ])
        self.submit(flow)
        resp = self.api("delete", f"/admin/approval/flows/{flow.id}", token=self.admin_token)
        self.assert_error(resp, 409, "FLOW_IN_USE")
        self.assertEqual(resp.data["details"]["count"], 1)
        self.assertIn("停用", resp.data["message"])
        self.assertTrue(ApprovalFlow.objects.filter(id=flow.id).exists())


class TwoStepSequentialTests(ApprovalStepsBase):
    def setUp(self):
        super().setUp()
        self.flow = self.make_steps_flow([
            {"name": "财务初审", "strategy": "ANY", "approver_ids": [self.a1.id]},
            {"name": "主任终审", "strategy": "ANY", "approver_ids": [self.a2.id]},
        ])

    def test_tasks_only_for_current_step(self):
        rid = self.submit(self.flow)
        tasks1 = self.api("get", "/approval/tasks?scope=RESOLUTION", token=self.t1)
        self.assertEqual(tasks1.data["count"], 1)
        tasks2 = self.api("get", "/approval/tasks?scope=RESOLUTION", token=self.t2)
        self.assertEqual(tasks2.data["count"], 0)
        self.decide(self.instance_of(rid), "APPROVE", self.t1)
        tasks1 = self.api("get", "/approval/tasks?scope=RESOLUTION", token=self.t1)
        tasks2 = self.api("get", "/approval/tasks?scope=RESOLUTION", token=self.t2)
        self.assertEqual(tasks1.data["count"], 0)
        self.assertEqual(tasks2.data["count"], 1)

    def test_second_step_approver_cannot_decide_early(self):
        rid = self.submit(self.flow)
        resp = self.decide(self.instance_of(rid), "APPROVE", self.t2)
        self.assert_error(resp, 403, "FORBIDDEN")

    def test_two_steps_approved_end_to_end(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.assert_ok(self.decide(instance, "APPROVE", self.t1))
        instance.refresh_from_db()
        self.assertEqual(instance.status, "PENDING")
        self.assertEqual(instance.current_step_order, 2)
        resp = self.assert_ok(self.decide(instance, "APPROVE", self.t2))
        self.assertEqual(resp.data["status"], "APPROVED")
        self.assertEqual(Resolution.objects.get(id=rid).status, "APPROVED")
        timeline = self.assert_ok(self.api("get", f"/approval/instances/{instance.id}", token=self.chair_token))
        self.assertEqual([s["status"] for s in timeline.data["steps"]], ["APPROVED", "APPROVED"])
        # 时间线需回传审批人昵称（前端按 step.approvers 渲染），不能只回 approver_ids
        self.assertEqual([a["id"] for a in timeline.data["steps"][0]["approvers"]], [self.a1.id])
        self.assertEqual([a["id"] for a in timeline.data["steps"][1]["approvers"]], [self.a2.id])
        self.assertTrue(all("nickname" in a for a in timeline.data["steps"][0]["approvers"]))

    def test_config_change_does_not_affect_inflight(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.api("put", f"/admin/approval/flows/{self.flow.id}",
                 {"steps": [{"name": "临时新增", "strategy": "ANY", "approver_ids": [self.a3.id]}]},
                 token=self.admin_token)
        instance.refresh_from_db()
        self.assertEqual(instance.step_states.count(), 2)
        self.assertEqual(instance.current_step_order, 1)


class AnyStrategyTests(ApprovalStepsBase):
    def setUp(self):
        super().setUp()
        self.flow = self.make_steps_flow([
            {"name": "或签初审", "strategy": "ANY", "approver_ids": [self.a1.id, self.a2.id]},
            {"name": "终审", "strategy": "ANY", "approver_ids": [self.a3.id]},
        ])

    def test_any_one_passes_step(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.decide(instance, "APPROVE", self.t1)
        instance.refresh_from_db()
        self.assertEqual(instance.current_step_order, 2)
        self.assertEqual(instance.step_states.get(step_order=1).status, "APPROVED")

    def test_partial_reject_does_not_end(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.assert_ok(self.decide(instance, "REJECT", self.t1, "金额需核实"))
        instance.refresh_from_db()
        self.assertEqual(instance.status, "PENDING")
        self.assertEqual(instance.current_step_order, 1)
        timeline = self.assert_ok(self.api("get", f"/approval/instances/{instance.id}", token=self.chair_token))
        self.assertEqual(timeline.data["steps"][0]["actions"][-1]["comment"], "金额需核实")
        self.decide(instance, "APPROVE", self.t2)
        instance.refresh_from_db()
        self.assertEqual(instance.current_step_order, 2)

    def test_all_reject_fails_instance(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.decide(instance, "REJECT", self.t1)
        instance.refresh_from_db()
        self.assertEqual(instance.status, "PENDING")
        self.decide(instance, "REJECT", self.t2)
        instance.refresh_from_db()
        self.assertEqual(instance.status, "REJECTED")
        self.assertEqual(Resolution.objects.get(id=rid).status, "REJECTED")


class AllStrategyTests(ApprovalStepsBase):
    def setUp(self):
        super().setUp()
        self.flow = self.make_steps_flow([
            {"name": "会签初审", "strategy": "ALL", "approver_ids": [self.a1.id, self.a2.id]},
            {"name": "终审", "strategy": "ANY", "approver_ids": [self.a3.id]},
        ])

    def test_partial_approve_still_pending(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.decide(instance, "APPROVE", self.t1)
        instance.refresh_from_db()
        self.assertEqual(instance.status, "PENDING")
        self.assertEqual(instance.current_step_order, 1)
        self.assertEqual(instance.step_states.get(step_order=1).status, "ACTIVE")

    def test_all_approve_advances(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.decide(instance, "APPROVE", self.t1)
        self.decide(instance, "APPROVE", self.t2)
        instance.refresh_from_db()
        self.assertEqual(instance.current_step_order, 2)

    def test_any_reject_fails_step(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.decide(instance, "APPROVE", self.t1)
        resp = self.decide(instance, "REJECT", self.t2, "不同意")
        self.assertEqual(resp.data["status"], "REJECTED")
        instance.refresh_from_db()
        self.assertEqual(instance.step_states.get(step_order=1).status, "REJECTED")


class TimelineAndValidationTests(ApprovalStepsBase):
    def setUp(self):
        super().setUp()
        self.flow = self.make_steps_flow([
            {"name": "初审", "strategy": "ANY", "approver_ids": [self.a1.id]},
            {"name": "终审", "strategy": "ANY", "approver_ids": [self.a2.id]},
        ])

    def test_timeline_permissions(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.decide(instance, "APPROVE", self.t1)
        # 历史审批人
        self.assert_ok(self.api("get", f"/approval/instances/{instance.id}", token=self.t1))
        # 发起人
        self.assert_ok(self.api("get", f"/approval/instances/{instance.id}", token=self.chair_token))
        # 无关成员
        stranger, _, _ = self.make_owner()
        self.make_seat(stranger, "MEMBER")
        resp = self.api("get", f"/approval/instances/{instance.id}", token=self.token_of(stranger))
        self.assert_error(resp, 403, "FORBIDDEN")

    def test_comment_length_limit(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        resp = self.decide(instance, "APPROVE", self.t1, "x" * 501)
        self.assert_error(resp, 400, "INVALID_VALUE")
        self.assert_ok(self.decide(instance, "APPROVE", self.t1, "x" * 500))

    def test_duplicate_decision_rejected(self):
        rid = self.submit(self.flow)
        instance = self.instance_of(rid)
        self.decide(instance, "APPROVE", self.t1)
        resp = self.decide(instance, "APPROVE", self.t1)
        self.assert_error(resp, 403, "FORBIDDEN")


class ClientContractTests(ApprovalStepsBase):
    def test_client_paths_resolve_to_backend_routes(self):
        root = pathlib.Path(__file__).resolve().parents[3]
        frontend = (root / "frontend/src/shared/api.js").read_text(encoding="utf-8")
        mini = (root / "miniprogram/utils/api.js").read_text(encoding="utf-8")
        for source in (frontend, mini):
            self.assertIn("/approval/tasks", source)
            self.assertIn("/approval/instances/", source)
        self.assertIn("/admin/approval/flows", frontend)
        self.assertIsNotNone(resolve("/api/v1/approval/tasks").func)
        self.assertIsNotNone(resolve("/api/v1/approval/instances/1").func)
        self.assertIsNotNone(resolve("/api/v1/approval/instances/1/decision").func)


class LegacyFlowCompatTests(ApprovalStepsBase):
    def test_legacy_flow_becomes_single_step(self):
        flow = self.make_flow(scope="RESOLUTION", mode="DESIGNATED", approvers=[self.a1])
        rid = self.submit(flow)
        instance = self.instance_of(rid)
        self.assertEqual(instance.step_states.count(), 1)
        self.assertEqual(instance.step_states.first().strategy, "ANY")
        resp = self.decide(instance, "APPROVE", self.t1)
        self.assertEqual(resp.data["status"], "APPROVED")
