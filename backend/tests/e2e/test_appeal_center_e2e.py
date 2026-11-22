"""ocap_appeal_center GROUP_D 端到端旅程（TC-E2E-1615 ~ 1616）。

critical path 口径：替代（多步 HTTP API 旅程；当前环境无浏览器 E2E，前端交互由 frontend vitest 覆盖）。
每条用例跨角色、跨模块完成完整用户旅程。
"""
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.models import AuditLog
from tests.support import ApiTestBase

PNG = b"\x89PNG\r\n\x1a\n" + b"6" * 32


class AppealCenterJourneyTests(ApiTestBase):
    def test_tc_e2e_1615_appeal_submit_withdraw_resubmit_approve_note(self):
        """TC-E2E-1615 / US-291、292、293、294（AC-291-01、292-01、293-01、294-01/02/03）：申诉提交→撤回→重提→通过并备注。"""
        user, token = self.make_user()
        unit = self.make_unit()
        _, admin_token = self.make_admin()

        def proof():
            uploaded = self.upload("/attachments", {
                "file": SimpleUploadedFile("p.png", PNG, content_type="image/png"),
                "purpose": "APPEAL_PROOF"}, token=token)
            return self.assert_ok(uploaded, 201).data["id"]

        first = self.assert_ok(self.api("post", "/appeals", {
            "unit_id": unit.id, "owner_name": "产权人甲", "proof_ids": [proof()]}, token=token), 201).data
        self.assert_ok(self.api("post", f"/appeals/{first['id']}/withdraw", {}, token=token))
        second = self.assert_ok(self.api("post", "/appeals", {
            "unit_id": unit.id, "owner_name": "产权人乙", "proof_ids": [proof()],
            "previous_appeal_id": first["id"]}, token=token), 201).data
        self.assert_ok(self.api("post", f"/admin/appeals/{second['id']}/decision",
                                {"decision": "APPROVE", "note": "资料齐全"}, token=admin_token))
        mine = self.api("get", "/appeals/mine", token=token).data
        self.assertEqual([(r["id"], r["status"], r["decision_note"], r["previous_appeal_id"]) for r in mine],
                         [(second["id"], "APPROVED", "资料齐全", first["id"]),
                          (first["id"], "WITHDRAWN", None, None)])
        actions = set(AuditLog.objects.values_list("action", flat=True))
        self.assertTrue({"APPEAL_SUBMITTED", "APPEAL_WITHDRAWN", "APPEAL_DECIDED"} <= actions)


class ResidentCenterJourneyTests(ApiTestBase):
    def test_tc_e2e_1616_resident_apply_withdraw_resubmit_reject_approve_real_name(self):
        """TC-E2E-1616 / US-295、296、297、298（AC-295-03、296-01/02/03、297-03、298-01/02）：同住申请→撤回→重提→驳回→再申请→通过→身份页实名。"""
        owner, otoken, unit = self.make_owner()
        applicant, atoken = self.make_user()
        first = self.assert_ok(self.api("post", "/resident-applications", {
            "unit_id": unit.id, "applicant_name": "王五"}, token=atoken), 201).data
        self.assert_ok(self.api("post", f"/resident-applications/{first['id']}/withdraw", {}, token=atoken))
        second = self.assert_ok(self.api("post", "/resident-applications", {
            "unit_id": unit.id, "applicant_name": "王五", "previous_application_id": first["id"]},
            token=atoken), 201).data
        queue = self.api("get", "/resident-applications/to-review", token=otoken).data
        self.assertEqual(queue[0]["applicant_name"], "王五")
        self.assert_ok(self.api("post", f"/resident-applications/{second['id']}/decision",
                                {"decision": "REJECT", "reject_reason": "信息不符",
                                 "note": "请补充门牌"}, token=otoken))
        mine = self.api("get", "/resident-applications/mine", token=atoken).data
        self.assertEqual((mine[0]["reject_reason"], mine[0]["decision_note"]), ("信息不符", "请补充门牌"))
        third = self.assert_ok(self.api("post", "/resident-applications", {
            "unit_id": unit.id, "applicant_name": "王五"}, token=atoken), 201).data
        self.assert_ok(self.api("post", f"/resident-applications/{third['id']}/decision",
                                {"decision": "APPROVE", "note": "已核实"}, token=otoken))
        owner_housing = self.api("get", "/me/housing", token=otoken).data
        self.assertEqual(owner_housing["units"][0]["residents"][0]["real_name"], "王五")
        applicant_housing = self.api("get", "/me/housing", token=atoken).data
        self.assertIn("王五", applicant_housing["real_names"])
        self.assertEqual(applicant_housing["units"][0]["role_label"], "同住人")
