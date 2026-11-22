"""ocap_appeal_center GROUP_D 集成测试（TC-INT-1502 ~ 1507）。

覆盖 US-291~298 的后端契约：撤回、重新提交关联、处理备注、同住申请实名、身份页同住人实名、100 条截断。
分层标记：integration（真实 DRF 路由 + 中间件 + SQLite 内存库）。
"""
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.core.models import AuditLog
from apps.residency.models import Appeal, Membership, ResidentApplication
from tests.support import ApiTestBase

PNG = b"\x89PNG\r\n\x1a\n" + b"5" * 32


def _proof(test, token):
    uploaded = test.upload("/attachments", {
        "file": SimpleUploadedFile("proof.png", PNG, content_type="image/png"),
        "purpose": "APPEAL_PROOF"}, token=token)
    test.assert_ok(uploaded, 201)
    return uploaded.data["id"]


class AppealLifecycleTests(ApiTestBase):
    def _appeal(self, user_token, unit):
        return self.assert_ok(self.api("post", "/appeals", {
            "unit_id": unit.id, "owner_name": "新产权人",
            "proof_ids": [_proof(self, user_token)]}, token=user_token), 201).data

    def test_tc_int_1502_withdraw_own_pending_only_and_release_slot(self):
        """TC-INT-1502 / AC-294-01、AC-294-02、C-359、C-360：本人待审可撤回；非本人 403；非待审 409；撤回释放待审约束。"""
        user, token = self.make_user()
        other, other_token = self.make_user()
        unit = self.make_unit()
        appeal = self._appeal(token, unit)
        resp = self.api("post", f"/appeals/{appeal['id']}/withdraw", {}, token=other_token)
        self.assert_error(resp, 403, "FORBIDDEN")
        resp = self.api("post", f"/appeals/{appeal['id']}/withdraw", {}, token=token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "WITHDRAWN")
        self.assertTrue(resp.data["withdrawn_at"])
        mine = self.api("get", "/appeals/mine", token=token).data
        self.assertEqual(mine[0]["status"], "WITHDRAWN")
        self.assert_error(self.api("post", f"/appeals/{appeal['id']}/withdraw", {}, token=token),
                          409, "NOT_PENDING")
        # 撤回后同一专有部分可再次提交（C-360）
        again = self._appeal(token, unit)
        self.assertEqual(again["status"], "PENDING")
        # 已处理的记录不可撤回
        _, admin_token = self.make_admin()
        self.assert_ok(self.api("post", f"/admin/appeals/{again['id']}/decision",
                                {"decision": "APPROVE"}, token=admin_token))
        self.assert_error(self.api("post", f"/appeals/{again['id']}/withdraw", {}, token=token),
                          409, "NOT_PENDING")
        self.assertIn("APPEAL_WITHDRAWN", set(AuditLog.objects.values_list("action", flat=True)))

    def test_tc_int_1503_resubmit_links_previous_and_rejects_invalid_source(self):
        """TC-INT-1503 / AC-294-03、D-02、IFC-382：重新提交生成新记录并关联；来源必须为本人已撤回。"""
        user, token = self.make_user()
        unit = self.make_unit()
        first = self._appeal(token, unit)
        self.assert_error(self.api("post", "/appeals", {
            "unit_id": unit.id, "owner_name": "改名", "proof_ids": [_proof(self, token)],
            "previous_appeal_id": first["id"]}, token=token), 400, "INVALID_PREVIOUS_RECORD")
        self.assert_ok(self.api("post", f"/appeals/{first['id']}/withdraw", {}, token=token))
        second = self.assert_ok(self.api("post", "/appeals", {
            "unit_id": unit.id, "owner_name": "改名", "proof_ids": [_proof(self, token)],
            "previous_appeal_id": first["id"]}, token=token), 201).data
        self.assertEqual(second["previous_appeal_id"], first["id"])
        self.assertEqual(second["status"], "PENDING")
        mine = self.api("get", "/appeals/mine", token=token).data
        self.assertEqual([(r["id"], r["status"], r["previous_appeal_id"]) for r in mine],
                         [(second["id"], "PENDING", first["id"]), (first["id"], "WITHDRAWN", None)])
        _, other_token = self.make_user()
        self.assert_error(self.api("post", "/appeals", {
            "unit_id": unit.id, "owner_name": "x", "proof_ids": [_proof(self, other_token)],
            "previous_appeal_id": first["id"]}, token=other_token), 400, "INVALID_PREVIOUS_RECORD")

    def test_tc_int_1504_decision_note_and_length_guard(self):
        """TC-INT-1504 / AC-293-01、AC-293-02、AC-293-04、IFC-384：通过与驳回均可备注；501 字拒绝且不落库。"""
        user, token = self.make_user()
        unit = self.make_unit()
        appeal = self._appeal(token, unit)
        _, admin_token = self.make_admin()
        too_long = "备" * 501
        resp = self.api("post", f"/admin/appeals/{appeal['id']}/decision",
                        {"decision": "APPROVE", "note": too_long}, token=admin_token)
        self.assert_error(resp, 400, "INVALID_VALUE")
        self.assertEqual(Appeal.objects.get(id=appeal["id"]).status, "PENDING")
        self.assert_ok(self.api("post", f"/admin/appeals/{appeal['id']}/decision",
                                {"decision": "APPROVE", "note": "资料齐全"}, token=admin_token))
        mine = self.api("get", "/appeals/mine", token=token).data
        self.assertEqual((mine[0]["status"], mine[0]["decision_note"]), ("APPROVED", "资料齐全"))
        second = self._appeal(token, self.make_unit())
        resp = self.api("post", f"/admin/appeals/{second['id']}/decision",
                        {"decision": "REJECT"}, token=admin_token)
        self.assert_error(resp, 400, "INVALID_VALUE")
        self.assert_ok(self.api("post", f"/admin/appeals/{second['id']}/decision",
                                {"decision": "REJECT", "reject_reason": "证明不清晰",
                                 "note": "请补整页照片"}, token=admin_token))
        rejected = self.api("get", "/appeals/mine", token=token).data[0]
        self.assertEqual((rejected["reject_reason"], rejected["decision_note"]),
                         ("证明不清晰", "请补整页照片"))


class ResidentApplicationLifecycleTests(ApiTestBase):
    def _apply(self, token, unit, name="同住申请人", previous=None):
        body = {"unit_id": unit.id, "applicant_name": name}
        if previous:
            body["previous_application_id"] = previous
        return self.api("post", "/resident-applications", body, token=token)

    def test_tc_int_1505_applicant_name_withdraw_and_resubmit(self):
        """TC-INT-1505 / AC-295-03、AC-296-02/03、AC-297-01/03、IFC-385/386：实名保存、撤回、重新提交关联与校验。"""
        owner, otoken, unit = self.make_owner()
        applicant, atoken = self.make_user()
        resp = self._apply(atoken, unit, "")
        self.assert_error(resp, 400, "NAME_REQUIRED")
        resp = self._apply(atoken, unit, "名" * 65)
        self.assert_error(resp, 400, "INVALID_VALUE")
        first = self.assert_ok(self._apply(atoken, unit, "张三"), 201).data
        self.assertEqual(first["applicant_name"], "张三")
        # 待审记录不能作为重新提交来源
        self.assert_error(self._apply(atoken, unit, "张三", first["id"]), 400, "INVALID_PREVIOUS_RECORD")
        self.assert_error(self.api("post", f"/resident-applications/{first['id']}/withdraw", {},
                                   token=otoken), 403, "FORBIDDEN")
        self.assert_ok(self.api("post", f"/resident-applications/{first['id']}/withdraw", {}, token=atoken))
        second = self.assert_ok(self._apply(atoken, unit, "张三丰", first["id"]), 201).data
        self.assertEqual(second["previous_application_id"], first["id"])
        mine = self.api("get", "/resident-applications/mine", token=atoken).data
        self.assertEqual([(r["id"], r["status"], r["previous_application_id"]) for r in mine],
                         [(second["id"], "PENDING", first["id"]), (first["id"], "WITHDRAWN", None)])
        queue = self.api("get", "/resident-applications/to-review", token=otoken).data
        self.assertEqual(queue[0]["applicant_name"], "张三丰")

    def test_tc_int_1506_decision_note_reason_and_housing_real_name(self):
        """TC-INT-1506 / AC-296-01、AC-298-01/02/03、C-361、IFC-388/389：审批原因/备注、身份页实名与缺失占位。"""
        owner, otoken, unit = self.make_owner()
        applicant, atoken = self.make_user()
        legacy, _ = self.make_user()
        legacy_app = ResidentApplication.objects.create(
            applicant=legacy, unit=unit, status="APPROVED", decided_by=owner,
            decided_at=timezone.now(), pending_slot=None)
        Membership.objects.create(user=legacy, unit=unit, role="RESIDENT", source="APPLICATION",
                                  active_slot=1)
        first = self.assert_ok(self._apply(atoken, unit, "李四"), 201).data
        self.assert_ok(self.api("post", f"/resident-applications/{first['id']}/decision",
                                {"decision": "REJECT", "reject_reason": "信息不符",
                                 "note": "请核对门牌"}, token=otoken))
        rejected = self.api("get", "/resident-applications/mine", token=atoken).data[0]
        self.assertEqual((rejected["reject_reason"], rejected["decision_note"]),
                         ("信息不符", "请核对门牌"))
        second = self.assert_ok(self._apply(atoken, unit, "李四"), 201).data
        self.assert_ok(self.api("post", f"/resident-applications/{second['id']}/decision",
                                {"decision": "APPROVE", "note": "已核实"}, token=otoken))
        owner_housing = self.api("get", "/me/housing", token=otoken).data
        residents = owner_housing["units"][0]["residents"]
        self.assertEqual([(r["user_id"], r["real_name"]) for r in residents],
                         [(legacy.id, None), (applicant.id, "李四")])
        self_in_housing = self.api("get", "/me/housing", token=atoken).data
        self.assertIn("李四", self_in_housing["real_names"])

    def test_tc_int_1507_mine_lists_cap_at_100(self):
        """TC-INT-1507 / AC-292-03、REQ-NFUNC-060：两类记录列表只返回最近 100 条。"""
        user, token = self.make_user()
        unit = self.make_unit()
        now = timezone.now()
        Appeal.objects.bulk_create([
            Appeal(user=user, unit=unit, status="REJECTED", pending_slot=None,
                   submitted_at=now - timedelta(seconds=i)) for i in range(101)])
        ResidentApplication.objects.bulk_create([
            ResidentApplication(applicant=user, unit=unit, status="REJECTED", pending_slot=None,
                                created_at=now - timedelta(seconds=i)) for i in range(101)])
        self.assertEqual(len(self.api("get", "/appeals/mine", token=token).data), 100)
        self.assertEqual(len(self.api("get", "/resident-applications/mine", token=token).data), 100)
