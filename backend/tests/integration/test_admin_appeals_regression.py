"""PHASE_08 回归（ocap_ui_theme，缺陷回流 1/2）：DEF-001 管理员申诉列表 GET /api/v1/admin/appeals 不得 500。

溯源：DEF-001（基线即存在的既有缺陷）；契约口径 AC-091-02（前端 adminHttp.get('/admin/appeals') 必须可用）；
权限口径 AC-091-03/04。分层：integration（真实 DRF 视图 + ORM + 全局鉴权，tests/integration 目录）。
"""
from apps.core.models import Attachment
from apps.residency.models import Appeal
from tests.support import ApiTestBase

LIST_KEYS = {"count", "page", "page_size", "results"}
ITEM_KEYS = {"id", "unit", "status", "submitted_at", "decided_at", "reject_reason", "applicant", "proof"}


class AdminAppealListRegressionTests(ApiTestBase):
    def _make_appeal(self, status="PENDING"):
        user, _ = self.make_user()
        unit = self.make_unit()
        appeal = Appeal.objects.create(user=user, unit=unit, status=status,
                                       pending_slot=1 if status == "PENDING" else None)
        return user, unit, appeal

    def test_tc_int_010_admin_list_returns_200_with_designed_shape(self):
        """TC-INT-010 DEF-001：管理员 GET 返回 200，分页包装与 results 字段同修复前设计一致。"""
        _, token = self.make_admin()
        user, unit, appeal = self._make_appeal()
        body = self.assert_ok(self.api("get", "/admin/appeals", token=token)).json()
        self.assertEqual(set(body), LIST_KEYS)
        self.assertEqual((body["count"], body["page"], body["page_size"]), (1, 1, 20))
        self.assertEqual(len(body["results"]), 1)
        item = body["results"][0]
        self.assertEqual(set(item), ITEM_KEYS)
        self.assertEqual(item["id"], appeal.id)
        self.assertEqual(item["status"], "PENDING")
        self.assertEqual(item["applicant"]["id"], user.id)
        self.assertEqual(item["applicant"]["account_no"], user.account_no)
        self.assertEqual(set(item["applicant"]), {"id", "account_no", "phone"})
        self.assertNotEqual(item["applicant"]["phone"], user.phone, "手机号必须脱敏")
        self.assertEqual(item["proof"], [])
        self.assertIsNone(item["decided_at"])

    def test_tc_int_011_proof_list_includes_linked_attachment(self):
        """TC-INT-011 DEF-001：申诉关联附件时 proof 含 id/name/size/content_type。"""
        _, token = self.make_admin()
        user, _, appeal = self._make_appeal()
        att = Attachment.objects.create(
            owner_type="MEMBER", owner_id=user.id, purpose="APPEAL_PROOF", original_name="proof.pdf",
            content_type="application/pdf", size=12, sha256="0" * 64, storage_path="x/proof.pdf",
            status="LINKED", linked_type="appeal", linked_id=str(appeal.id))
        body = self.assert_ok(self.api("get", "/admin/appeals", token=token)).json()
        proof = body["results"][0]["proof"]
        self.assertEqual(len(proof), 1)
        self.assertEqual(proof[0], {"id": str(att.id), "name": "proof.pdf", "size": 12,
                                    "content_type": "application/pdf"})

    def test_tc_int_012_status_filter_works(self):
        """TC-INT-012 DEF-001：?status= 过滤只返回对应状态；无匹配返回空 results；分页参数生效。"""
        _, token = self.make_admin()
        _, _, pending = self._make_appeal("PENDING")
        _, _, approved = self._make_appeal("APPROVED")
        _, _, rejected = self._make_appeal("REJECTED")
        everything = self.assert_ok(self.api("get", "/admin/appeals", token=token)).json()
        self.assertEqual(everything["count"], 3)
        for status, expected in (("PENDING", pending), ("APPROVED", approved), ("REJECTED", rejected)):
            body = self.assert_ok(self.api("get", f"/admin/appeals?status={status}", token=token)).json()
            self.assertEqual(body["count"], 1, status)
            self.assertEqual([r["id"] for r in body["results"]], [expected.id], status)
            self.assertEqual(body["results"][0]["status"], status)
        none = self.assert_ok(self.api("get", "/admin/appeals?status=NO_SUCH", token=token)).json()
        self.assertEqual((none["count"], none["results"]), (0, []))
        paged = self.assert_ok(self.api("get", "/admin/appeals?page=2&page_size=2", token=token)).json()
        self.assertEqual((paged["count"], paged["page"], paged["page_size"], len(paged["results"])), (3, 2, 2, 1))

    def test_tc_int_013_non_admin_rejected(self):
        """TC-INT-013 AC-091-03：匿名 401；坏令牌 401；游客/户主/委员(用户令牌)403，均不返回数据。"""
        self._make_appeal()
        owner, owner_token, _ = self.make_owner()
        guest, guest_token = self.make_user()
        member, member_token, _ = self.make_owner()
        self.make_seat(member)
        self.assertEqual(self.api("get", "/admin/appeals").status_code, 401)
        self.assertEqual(self.api("get", "/admin/appeals", token="bad-token").status_code, 401)
        for token in (guest_token, owner_token, member_token):
            resp = self.api("get", "/admin/appeals", token=token)
            self.assertEqual(resp.status_code, 403, resp.content)
            self.assertNotIn("results", resp.json())

    def test_tc_int_014_decision_flow_still_visible_in_list(self):
        """TC-INT-014 DEF-001：经真实决议接口通过申诉后，列表按 status 过滤可见（修复未破坏相邻接口）。"""
        _, token = self.make_admin()
        _, _, appeal = self._make_appeal()
        resp = self.api("post", f"/admin/appeals/{appeal.id}/decision", {"decision": "REJECT",
                                                                         "reject_reason": "材料不全"}, token=token)
        self.assertIn(resp.status_code, (200, 201), resp.content)
        body = self.assert_ok(self.api("get", "/admin/appeals?status=REJECTED", token=token)).json()
        self.assertEqual([r["id"] for r in body["results"]], [appeal.id])
        self.assertEqual(body["results"][0]["reject_reason"], "材料不全")


class PageResponseListSmokeTests(ApiTestBase):
    """TC-INT-015：对所有使用 page_response 的列表接口，用对应角色请求不得 500（同类缺陷防线）。"""

    ADMIN_LISTS = ["/admin/appeals", "/admin/admins", "/admin/users", "/admin/approval/flows",
                   "/admin/committee/seats", "/admin/memberships", "/admin/claims",
                   "/admin/audit-logs", "/admin/registry/units"]
    MEMBER_LISTS = ["/polls", "/resolutions", "/claims", "/income/sheets", "/ledger/reports",
                    "/admin/income/sheets"]  # 该路径由委员令牌（IsIncomeMember）访问，非管理员令牌

    def test_tc_int_015_page_response_lists_do_not_500(self):
        """TC-INT-015 DEF-001：管理员 9 个 + 委员 6 个列表接口均 200 且为分页包装。"""
        _, admin_token = self.make_admin()
        member, member_token, _ = self.make_owner()
        self.make_seat(member)
        failures = []
        for path in self.ADMIN_LISTS:
            resp = self.api("get", path, token=admin_token)
            body = resp.json() if resp.status_code == 200 else None
            if resp.status_code != 200 or not LIST_KEYS <= set(body):
                failures.append((path, resp.status_code))
        for path in self.MEMBER_LISTS:
            resp = self.api("get", path, token=member_token)
            body = resp.json() if resp.status_code == 200 else None
            ok = resp.status_code == 200 and (isinstance(body, list) or LIST_KEYS <= set(body))
            if not ok:
                failures.append((path, resp.status_code))
        self.assertEqual(failures, [])
