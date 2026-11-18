"""PHASE_08 集成测试：半数同意决议不得设置审批人（修复问题二）。

背景：历史上管理端允许 HALF_MAJORITY 流程同时配置审批人，审批人会随快照进入
ApprovalInstance.flow_snapshot.approver_ids，使半数同意决议错误地出现在
/approval/tasks 审批待办，审批人点"同意"时被 ApprovalEngine.decide() 以
USE_VOTE_ENDPOINT 拒绝。本组用例覆盖：创建/更新校验、提交后不落待办、
以及数据迁移对历史脏数据的清理。
"""
import importlib
from datetime import timedelta

from django.apps import apps as global_apps
from django.utils import timezone

from apps.approval.models import ApprovalFlow, ApprovalInstance, FlowApprover
from apps.approval.services import ApprovalEngine
from apps.core.errors import ApiError
from tests.support import ApiTestBase

# 迁移模块名以数字开头，无法用普通 import，改用 importlib 取出清理函数。
_migration = importlib.import_module("apps.approval.migrations.0002_clean_half_majority_approvers")
clean_half_majority_approvers = _migration.clean_half_majority_approvers


class HalfMajorityFlowApproverTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()
        self.chair, self.chair_token = self.make_user(nickname="主任")
        self.member, self.member_token = self.make_user(nickname="委员")
        self.make_seat(self.chair, position="CHAIR")
        self.make_seat(self.member, position="MEMBER")

    # ---------- 创建/更新校验 ----------
    def test_tc_int_create_half_majority_with_approvers_rejected(self):
        resp = self.api("post", "/admin/approval/flows", {
            "scope": "RESOLUTION", "name": "业委会决议", "mode": "HALF_MAJORITY",
            "approver_ids": [self.member.id],
        }, token=self.admin_token)
        self.assertEqual(resp.status_code, 400, resp.content)
        self.assertEqual(resp.json()["code"], "INVALID_VALUE")
        self.assertEqual(ApprovalFlow.objects.count(), 0)

    def test_tc_int_create_half_majority_without_approvers_ok(self):
        resp = self.api("post", "/admin/approval/flows", {
            "scope": "RESOLUTION", "name": "业委会决议", "mode": "HALF_MAJORITY",
        }, token=self.admin_token)
        self.assertEqual(resp.status_code, 201, resp.content)
        body = resp.json()
        self.assertEqual(body["mode"], "HALF_MAJORITY")
        self.assertEqual(body["approvers"], [])

    def test_tc_int_update_flow_to_half_majority_with_approvers_rejected(self):
        flow = self.make_flow(scope="RESOLUTION", mode="DESIGNATED", approvers=[self.member])
        resp = self.api("put", f"/admin/approval/flows/{flow.id}", {
            "mode": "HALF_MAJORITY", "approver_ids": [self.member.id],
        }, token=self.admin_token)
        self.assertEqual(resp.status_code, 400, resp.content)
        flow.refresh_from_db()
        self.assertEqual(flow.mode, "DESIGNATED")

    def test_tc_int_update_flow_to_half_majority_clearing_approvers_ok(self):
        flow = self.make_flow(scope="RESOLUTION", mode="DESIGNATED", approvers=[self.member])
        resp = self.api("put", f"/admin/approval/flows/{flow.id}", {
            "mode": "HALF_MAJORITY", "approver_ids": [],
        }, token=self.admin_token)
        self.assertEqual(resp.status_code, 200, resp.content)
        flow.refresh_from_db()
        self.assertEqual(flow.mode, "HALF_MAJORITY")
        self.assertEqual(FlowApprover.objects.filter(flow=flow).count(), 0)

    # ---------- 提交后不落审批待办 ----------
    def test_tc_int_half_majority_resolution_absent_from_approval_tasks(self):
        flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY")
        deadline = (timezone.now() + timedelta(days=1)).isoformat()
        created = self.api("post", "/resolutions", {
            "title": "今天晚上吃什么", "content": "投票决定", "approval_flow_id": flow.id,
            "vote_deadline": deadline,
        }, token=self.chair_token)
        self.assertEqual(created.status_code, 201, created.content)
        # 实例快照不含审批人
        instance = ApprovalInstance.objects.get(subject_type="resolution",
                                                subject_id=created.json()["id"])
        self.assertEqual(instance.flow_snapshot.get("approver_ids"), [])
        # 委员的审批待办里不出现该半数同意决议
        tasks = self.api("get", "/approval/tasks", token=self.member_token)
        self.assertEqual(tasks.status_code, 200, tasks.content)
        self.assertEqual(tasks.json()["count"], 0)
        # 半数同意决议仍应出现在决议"待办"（投票口径）里
        todo = self.api("get", "/resolutions?scope=todo", token=self.member_token)
        self.assertEqual(todo.status_code, 200, todo.content)
        self.assertEqual(len(todo.json()), 1)

    # ---------- decide 保险仍然有效 ----------
    def test_tc_int_decide_half_majority_snapshot_rejected(self):
        """历史脏数据（快照含审批人）即便漏进 decide，也必须被 USE_VOTE_ENDPOINT 拒绝。"""
        flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY")
        instance = ApprovalInstance.objects.create(
            scope="RESOLUTION", subject_type="resolution", subject_id=999, flow=flow,
            flow_snapshot={"name": flow.name, "mode": "HALF_MAJORITY",
                           "approver_ids": [self.member.id]},
            submitter=self.chair, revision=1, pending_slot=1,
        )
        with self.assertRaises(ApiError) as ctx:
            ApprovalEngine.decide(instance.id, self.member, "APPROVE")
        self.assertEqual(ctx.exception.code, "USE_VOTE_ENDPOINT")

    # ---------- 数据迁移清理历史脏数据 ----------
    def test_tc_int_migration_cleans_dirty_half_majority_data(self):
        flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY", approvers=[self.member])
        instance = ApprovalInstance.objects.create(
            scope="RESOLUTION", subject_type="resolution", subject_id=76, flow=flow,
            flow_snapshot={"name": flow.name, "mode": "HALF_MAJORITY",
                           "approver_ids": [self.member.id]},
            submitter=self.chair, revision=1, pending_slot=1,
        )
        clean_half_majority_approvers(global_apps, None)
        self.assertEqual(FlowApprover.objects.filter(flow=flow).count(), 0)
        instance.refresh_from_db()
        self.assertEqual(instance.flow_snapshot.get("approver_ids"), [])
