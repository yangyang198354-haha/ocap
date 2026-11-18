"""端到端旅程：半数同意决议不设审批人（修复问题二）。

真实 DRF 路由 + 中间件 + SQLite 内存库。覆盖一条完整旅程：
管理端误把半数同意流程配置审批人被拒 → 正确创建（不设审批人）→ 主任发起决议 →
审批人用户的"审批待办"里看不到该决议（不再误入 /approval/tasks）→ 委员投票 →
截止判定通过。即问题二"审批人点同意报 USE_VOTE_ENDPOINT"从源头不再发生。
"""
from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone

from apps.resolutions.models import Resolution
from tests.support import ApiTestBase


class HalfMajorityNoApproverJourneyTests(ApiTestBase):
    def test_tc_e2e_half_majority_flow_has_no_approver_and_no_task_leak(self):
        _, admin_token = self.make_admin()
        chair, ctoken, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        members = []
        for _ in range(4):
            u, t, _ = self.make_owner()
            self.make_seat(u, "MEMBER")
            members.append((u, t))

        # 1) 误配置：半数同意 + 指定审批人 → 被拒
        self.assert_error(self.api("post", "/admin/approval/flows", {
            "scope": "RESOLUTION", "mode": "HALF_MAJORITY", "name": "e2e_业委会决议",
            "approver_ids": [members[0][0].id],
        }, token=admin_token), 400, "INVALID_VALUE")

        # 2) 正确配置：半数同意、不设审批人 → 201，审批人为空
        flow = self.assert_ok(self.api("post", "/admin/approval/flows", {
            "scope": "RESOLUTION", "mode": "HALF_MAJORITY", "name": "e2e_业委会决议",
        }, token=admin_token), 201).data
        self.assertEqual(flow["approvers"], [])

        # 3) 主任发起半数同意决议
        created = self.assert_ok(self.api("post", "/resolutions", {
            "title": "今天晚上吃什么", "content": "投票决定", "approval_flow_id": flow["id"],
            "vote_deadline": (timezone.now() + timedelta(hours=2)).isoformat(),
        }, token=ctoken), 201).data

        # 4) 审批人用户的"审批待办"看不到该决议（问题二的错位已消除）
        for _, t in members:
            tasks = self.assert_ok(self.api("get", "/approval/tasks", token=t)).data
            self.assertEqual(tasks["count"], 0)
        # 决议"待办"（投票口径）则应可见
        todo = self.assert_ok(self.api("get", "/resolutions?scope=todo", token=members[0][1])).data
        self.assertEqual([r["id"] for r in todo], [created["id"]])

        # 5) 投票并在截止后判定通过（同意 3 票 ×2 > 在任 5 人）
        for (_, t), choice in zip(members, ["AGREE", "AGREE", "DISAGREE", "ABSTAIN"]):
            self.assert_ok(self.api("post", f"/resolutions/{created['id']}/votes",
                                    {"choice": choice}, token=t))
        self.assert_ok(self.api("post", f"/resolutions/{created['id']}/votes",
                                {"choice": "AGREE"}, token=ctoken))
        Resolution.objects.filter(id=created["id"]).update(
            vote_deadline=timezone.now() - timedelta(minutes=1))
        call_command("run_due_jobs")
        done = self.assert_ok(self.api("get", f"/resolutions/{created['id']}",
                                       token=members[0][1])).data
        self.assertEqual(done["status"], "APPROVED")
