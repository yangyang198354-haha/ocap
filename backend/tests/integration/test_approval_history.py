"""ocap_approval_history GROUP_D：通用审批与同住人历史的 ORM/HTTP 集成测试。"""
from datetime import timedelta

from django.utils import timezone

from apps.approval.models import (ApprovalAction, ApprovalFlow, ApprovalInstance, ApprovalStep,
                                  StepApprover)
from apps.approval.services import ApprovalEngine
from apps.residency.models import Membership, ResidentApplication
from apps.resolutions.models import Resolution
from tests.support import ApiTestBase


class ApprovalHistoryBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.submitter, _ = self.make_user(nickname="提交人")
        self.a1, _ = self.make_user(nickname="审批一")
        self.a2, _ = self.make_user(nickname="审批二")
        self.a3, _ = self.make_user(nickname="审批三")
        for user in (self.a1, self.a2, self.a3):
            self.make_seat(user, "MEMBER")
        self.t1 = self.token_of(self.a1)
        self.t2 = self.token_of(self.a2)
        self.t3 = self.token_of(self.a3)
        self.subject_seq = 10000

    def make_instance(self, scope="RESOLUTION", steps=None):
        self.subject_seq += 1
        steps = steps or [("初审", "ANY", [self.a1])]
        flow = ApprovalFlow.objects.create(scope=scope, mode="DESIGNATED",
                                           name=f"历史流程{self.subject_seq}")
        for order, (name, strategy, approvers) in enumerate(steps, 1):
            step = ApprovalStep.objects.create(flow=flow, order=order, name=name, strategy=strategy)
            StepApprover.objects.bulk_create([StepApprover(step=step, user=user) for user in approvers])
        if scope == "RESOLUTION":
            resolution = Resolution.objects.create(title=f"历史决议{self.subject_seq}", content="历史测试",
                                                   initiator=self.submitter)
            subject_type, subject_id = "resolution", resolution.id
        else:
            subject_type, subject_id = "income_sheet", self.subject_seq
        return ApprovalEngine.submit(scope=scope, subject_type=subject_type, subject_id=subject_id,
                                     flow_id=flow.id, submitter=self.submitter)

    def add_action(self, instance, actor, action="APPROVE", comment="", step_order=1, when=None):
        state = instance.step_states.get(step_order=step_order)
        row = ApprovalAction.objects.create(instance=instance, actor=actor, action=action,
                                            comment=comment, step_state=state, step_order=step_order)
        if when is not None:
            ApprovalAction.objects.filter(id=row.id).update(acted_at=when)
            row.refresh_from_db()
        return row

    def handled(self, token, query=""):
        suffix = f"&{query}" if query else ""
        return self.assert_ok(self.api("get", f"/approval/tasks?view=handled{suffix}", token=token)).data


class HandledApprovalApiTests(ApprovalHistoryBase):
    def test_tc_int_2301_single_step_approved_record_is_read_only(self):
        """TC-INT-2301 / AC-370-01：单步通过后待办移除，已处理摘要完整且 GET 无写副作用。"""
        instance = self.make_instance()
        for path in ("/approval/tasks", "/approval/tasks?view=todo"):
            todo = self.assert_ok(self.api("get", path, token=self.t1)).data
            self.assertEqual(todo["count"], 1)
            self.assertNotIn("my_action", todo["results"][0])

        self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                {"action": "APPROVE", "comment": "同意"}, token=self.t1))
        self.assertEqual(self.api("get", "/approval/tasks", token=self.t1).data["count"], 0)
        self.assertEqual(self.api("get", "/approval/tasks?view=todo", token=self.t1).data["count"], 0)

        body = self.handled(self.t1)
        self.assertEqual(body["count"], 1)
        row = body["results"][0]
        self.assertEqual(row["instance_id"], instance.id)
        self.assertEqual(row["scope"], "RESOLUTION")
        self.assertEqual(row["subject_title"], Resolution.objects.get(id=instance.subject_id).title)
        self.assertTrue(row["submitter_label"])
        self.assertIsNotNone(row["submitted_at"])
        self.assertEqual(row["my_action"], "APPROVE")
        self.assertIsNotNone(row["my_acted_at"])
        self.assertEqual(row["my_comment"], "同意")
        self.assertEqual(row["my_step_order"], 1)
        self.assertEqual(row["my_step_name"], "初审")
        self.assertEqual(row["status"], "APPROVED")
        self.assertIsNone(row["step_order"])

        instance.refresh_from_db()
        before = (instance.status, instance.current_step_order,
                  ApprovalAction.objects.filter(instance=instance).count())
        self.assertEqual(self.handled(self.t1)["count"], 1)
        instance.refresh_from_db()
        after = (instance.status, instance.current_step_order,
                 ApprovalAction.objects.filter(instance=instance).count())
        self.assertEqual(after, before)

    def test_tc_int_2302_multistep_pending_keeps_current_step(self):
        """TC-INT-2302 / AC-370-02：完成前序步骤后仍可见，step_* 指向当前第 2 步。"""
        instance = self.make_instance(steps=[("财务初审", "ANY", [self.a1]),
                                              ("主任终审", "ANY", [self.a2])])
        self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                {"action": "APPROVE", "comment": "初审同意"}, token=self.t1))
        row = self.handled(self.t1)["results"][0]
        self.assertEqual(row["status"], "PENDING")
        self.assertEqual((row["step_order"], row["step_name"], row["step_strategy"]),
                         (2, "主任终审", "ANY"))
        self.assertEqual((row["my_step_order"], row["my_step_name"], row["my_comment"]),
                         (1, "财务初审", "初审同意"))
        self.assertEqual(self.handled(self.t2)["count"], 0)
        self.assertEqual(self.api("get", "/approval/tasks", token=self.t2).data["count"], 1)

    def test_tc_int_2303_assignment_or_other_action_does_not_count(self):
        """TC-INT-2303 / AC-370-03、04：仅被指定或只有他人动作均不进入本人历史，待办不受影响。"""
        assigned = self.make_instance(steps=[("待处理", "ANY", [self.a3])])
        other = self.make_instance(steps=[("他人处理", "ANY", [self.a1])])
        self.add_action(other, self.a1, comment="他人意见")

        self.assertEqual(self.handled(self.t3)["results"], [])
        todo = self.assert_ok(self.api("get", "/approval/tasks", token=self.t3)).data
        self.assertEqual(todo["count"], 1)
        self.assertEqual(todo["results"][0]["instance_id"], assigned.id)
        other_history = self.handled(self.t1)
        self.assertEqual(other_history["count"], 1)
        self.assertEqual(other_history["results"][0]["instance_id"], other.id)
        self.assertNotIn(assigned.id, [r["instance_id"] for r in other_history["results"]])

    def test_tc_int_2304_scope_latest_action_and_deduplicated_pagination(self):
        """TC-INT-2304 / AC-371-01、04：25 条去重分页，决议过滤为 2，摘要取本人最近动作。"""
        instances = []
        for index in range(25):
            scope = "RESOLUTION" if index < 2 else "INCOME"
            instance = self.make_instance(scope=scope)
            self.add_action(instance, self.a1, comment="首次")
            instances.append(instance)
        later = timezone.now() + timedelta(seconds=1)
        self.add_action(instances[0], self.a1, action="REJECT", comment="最近意见", when=later)

        page1 = self.handled(self.t1, "page=1&page_size=20")
        page2 = self.handled(self.t1, "page=2&page_size=20")
        self.assertEqual((page1["count"], len(page1["results"])), (25, 20))
        self.assertEqual((page2["count"], len(page2["results"])), (25, 5))
        ids = [r["instance_id"] for r in page1["results"] + page2["results"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {i.id for i in instances})

        filtered = self.handled(self.t1, "scope=RESOLUTION&page=1&page_size=20")
        self.assertEqual(filtered["count"], 2)
        self.assertEqual({r["scope"] for r in filtered["results"]}, {"RESOLUTION"})
        all_rows = self.handled(self.t1, "page_size=100")["results"]
        latest = next(r for r in all_rows if r["instance_id"] == instances[0].id)
        self.assertEqual((latest["my_action"], latest["my_comment"]), ("REJECT", "最近意见"))
        self.assertEqual(all_rows[0]["instance_id"], instances[0].id)

        self.assert_error(self.api("get", "/approval/tasks?view=unknown", token=self.t1), 400,
                          "INVALID_QUERY")
        self.assert_error(self.api("get", "/approval/tasks?view=handled&page=x", token=self.t1), 400,
                          "INVALID_QUERY")

    def test_tc_int_2305_timeline_reused_and_unrelated_user_forbidden(self):
        """TC-INT-2305 / AC-371-02、03：时间线含步骤动作意见；无关用户 403 且无详情。"""
        instance = self.make_instance(steps=[("财务初审", "ANY", [self.a1]),
                                              ("主任终审", "ANY", [self.a2])])
        self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                {"action": "APPROVE", "comment": "票据齐全"}, token=self.t1))
        timeline = self.assert_ok(self.api("get", f"/approval/instances/{instance.id}", token=self.t1)).data
        self.assertEqual(timeline["status"], "PENDING")
        self.assertEqual([s["name"] for s in timeline["steps"]], ["财务初审", "主任终审"])
        action = timeline["steps"][0]["actions"][-1]
        self.assertEqual(action["action"], "APPROVE")
        self.assertEqual(action["comment"], "票据齐全")
        self.assertTrue(action["actor_label"])
        self.assertIsNotNone(action["acted_at"])

        denied = self.assert_error(self.api("get", f"/approval/instances/{instance.id}", token=self.t3),
                                   403, "FORBIDDEN")
        self.assertNotIn("steps", denied)
        self.assertNotIn("actions", denied)


class ResidentApprovedHistoryApiTests(ApiTestBase):
    def test_tc_int_2306_approved_history_and_applicant_records(self):
        """TC-INT-2306 / AC-372-01、AC-373-01、02：审批人与申请人分别看到有权记录。"""
        owner, owner_token, unit = self.make_owner()
        applicant, applicant_token = self.make_user(nickname="小王")
        other, other_token = self.make_user(nickname="其他申请人")
        created = self.assert_ok(self.api("post", "/resident-applications",
                                          {"unit_id": unit.id, "applicant_name": "张同住"},
                                          token=applicant_token), 201).data
        self.assert_ok(self.api("post", f"/resident-applications/{created['id']}/decision",
                                {"decision": "APPROVE", "note": "已核实"}, token=owner_token))
        ResidentApplication.objects.create(applicant=other, unit=unit, status="APPROVED",
                                           applicant_name="他人", decided_by=owner,
                                           decided_at=timezone.now(), decision_note="他人备注", pending_slot=None)

        self.assertEqual(self.api("get", "/resident-applications/to-review", token=owner_token).data, [])
        approved = self.assert_ok(self.api("get", "/resident-applications/approved", token=owner_token)).data
        row = next(r for r in approved if r["id"] == created["id"])
        self.assertEqual(row["unit"]["specific_part"], unit.specific_part)
        self.assertEqual(row["applicant"]["nickname"], "小王")
        self.assertEqual(row["applicant_name"], "张同住")
        self.assertEqual(row["status"], "APPROVED")
        self.assertIsNotNone(row["created_at"])
        self.assertIsNotNone(row["decided_at"])
        self.assertEqual(row["decision_note"], "已核实")

        mine = self.assert_ok(self.api("get", "/resident-applications/mine", token=applicant_token)).data
        self.assertEqual([r["id"] for r in mine], [created["id"]])
        self.assertEqual((mine[0]["status"], mine[0]["decision_note"]), ("APPROVED", "已核实"))
        self.assertIsNotNone(mine[0]["decided_at"])
        self.assertFalse(Membership.objects.filter(user=applicant, unit=unit,
                                                   role__in=["HEAD", "OWNER"]).exists())
        self.assertEqual(self.api("get", "/resident-applications/mine", token=other_token).data[0]["applicant_name"],
                         "他人")

    def test_tc_int_2307_only_approved_and_current_ownership(self):
        """TC-INT-2307 / AC-372-02、03：固定通过状态、空结果与当前产权隔离。"""
        owner, owner_token, unit = self.make_owner()
        applicant, _ = self.make_user()
        applications = {}
        for status in ("PENDING", "APPROVED", "REJECTED", "WITHDRAWN", "CLOSED"):
            applications[status] = ResidentApplication.objects.create(
                applicant=applicant, unit=unit, status=status, applicant_name=status,
                decided_by=owner if status == "APPROVED" else None,
                decided_at=timezone.now() if status == "APPROVED" else None,
                decision_note="通过备注" if status == "APPROVED" else status,
                pending_slot=1 if status == "PENDING" else None)
        other_unit = self.make_unit()
        outsider = ResidentApplication.objects.create(applicant=applicant, unit=other_unit, status="APPROVED",
                                                      decided_at=timezone.now(), pending_slot=None)

        for path in ("/resident-applications/approved", "/resident-applications/approved?status=REJECTED"):
            rows = self.assert_ok(self.api("get", path, token=owner_token)).data
            self.assertEqual([r["id"] for r in rows], [applications["APPROVED"].id])
            self.assertNotIn(outsider.id, [r["id"] for r in rows])
        _, empty_token, _ = self.make_owner()
        self.assertEqual(self.api("get", "/resident-applications/approved", token=empty_token).data, [])

        Membership.objects.filter(user=owner, unit=unit, ended_at__isnull=True).update(
            ended_at=timezone.now(), active_slot=None, head_slot=None, end_reason="REVOKED")
        self.assertEqual(self.api("get", "/resident-applications/approved", token=owner_token).data, [])
