"""ocap_product_review GROUP_D 缺陷回流 2 后重测（TC-INT-544 起，新增；不改动已冻结用例）。

字段级前后端契约（PM 指令 1、GR-C-003 condition）：
  * TC-INT-544：Web 收入表页读取的 `can_void` 字段与后端 /admin/income/sheets 列表项一致（回流 1 新增字段）；
  * TC-INT-545：管理端财务页（type / status）、审计页（occurred_at / actor_type / result）读取的字段与后端响应一致，
    且后端真实响应里出现的枚举值全部落在 shared/adminText.js 的映射表键内（否则页面会回退显示英文原值）。
前端一侧只读源码文本，后端一侧用真实 HTTP 请求验证（与 test_frontend_contract.py 同口径）。
"""
import re
from datetime import date
from uuid import uuid4

from django.urls import resolve

from apps.approval.models import ApprovalInstance
from apps.core.audit import AuditActor, AuditService, system_actor
from apps.core.models import Attachment
from tests.integration.test_frontend_contract import REPO, extract_calls, reads, src
from tests.support import ApiTestBase


def _invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE", original_name="i.pdf",
        content_type="application/pdf", size=10, sha256="x" * 64,
        storage_path=f"tmp/{uuid4().hex}", status="TEMP")


def _table_keys(text: str, name: str) -> set[str]:
    """从 adminText.js 的 `export const NAME = { KEY: '…', … }` 取键。"""
    m = re.search(rf"export const {name}\s*=\s*\{{([^}}]*)\}}", text)
    assert m, f"adminText.js 中找不到 {name}"
    return set(re.findall(r"\b([A-Z][A-Z_]+)\s*:", m.group(1)))


class IncomeCanVoidContractTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.clerk, self.ctoken, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.approver, self.atoken, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.flow = self.make_flow(scope="INCOME", approvers=[self.approver])

    def _sheet(self, approve: bool):
        resp = self.api("post", "/admin/income/sheets", {"records": [
            {"occurred_on": str(date.today()), "amount": "10.00", "category": "物业费"}]}, token=self.ctoken)
        self.assert_ok(resp, 201)
        sid = resp.data["id"]
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sid}/submit",
                                {"approval_flow_id": self.flow.id}, token=self.ctoken))
        if approve:
            inst = ApprovalInstance.objects.get(subject_type="income_sheet", subject_id=sid)
            self.assert_ok(self.api("post", f"/approval/instances/{inst.id}/decision",
                                    {"action": "APPROVE"}, token=self.atoken))
        return sid

    def test_tc_int_544_us_178_can_void_field_contract_income_list_vs_income_page(self):
        """TC-INT-544 / US-178（AC-178-02）、US-060（AC-060-10）：前端 Income.vue 读取的 item.can_void 与后端
        GET /admin/income/sheets 列表项一致——列表项每一行都有布尔 can_void（已生效 + 原审批人 true，其余 false）；
        页面读取的全部 item.* 字段都在后端列表项中；作废调用 POST /admin/income/sheets/{id}/void 可解析到支持 POST 的路由；
        小程序不使用 can_void（C-44：小程序不补收入表）。"""
        page = src("frontend/src/portal/Income.vue")
        # 前端一侧：作废按钮同时依赖 status 与 can_void
        self.assertRegex(page, r"v-if=\"item\.status === 'EFFECTIVE' && item\.can_void\"")
        used = reads(page, ["item"])
        self.assertIn("can_void", used)
        # 前端调用：列表与作废两个调用都能解析到后端路由并支持对应方法
        calls = {(m, p): w for _, m, p, w in extract_calls(REPO / "frontend/src/shared/api.js")}
        self.assertIn(("GET", "/admin/income/sheets"), calls)
        void_paths = [p for (m, p) in calls if m == "POST" and p.startswith("/admin/income/sheets/${") and p.endswith("/void")]
        self.assertEqual(len(void_paths), 1, void_paths)
        view = resolve("/api/v1/admin/income/sheets/1/void").func.cls
        self.assertTrue(hasattr(view, "post"))
        # 后端一侧：真实响应
        eff = self._sheet(approve=True)
        pending = self._sheet(approve=False)
        for token, expected in ((self.atoken, True), (self.ctoken, False)):
            data = self.assert_ok(self.api("get", "/admin/income/sheets?page_size=50", token=token)).data
            rows = {r["id"]: r for r in data["results"]}
            self.assertEqual(set(rows), {eff, pending})
            for r in rows.values():
                self.assertIn("can_void", r)
                self.assertIsInstance(r["can_void"], bool)
                self.assertGreaterEqual(set(r), used - {"can_void"} | {"can_void"}, "页面读取了后端列表项没有的字段")
            self.assertIs(rows[eff]["can_void"], expected)
            self.assertIs(rows[pending]["can_void"], False)
        # 小程序没有收入表页，也不读取 can_void
        for path in (REPO / "miniprogram").rglob("*.vue"):
            self.assertNotIn("can_void", path.read_text(encoding="utf-8"), str(path))
        self.assertNotIn("can_void", src("miniprogram/utils/api.js"))


class AdminTextContractTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()
        self.member, self.mtoken, _ = self.make_owner()
        self.make_seat(self.member, "MEMBER")
        approver, _, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        self.flow = self.make_flow(scope="EXPENSE", approvers=[approver])

    def test_tc_int_545_us_167_admin_finance_and_audit_fields_and_enum_values_vs_admin_text(self):
        """TC-INT-545 / US-167（AC-167-03）、US-178（AC-178-02）、REQ-FUNC-158：AdminFinance 读取的 row.type / row.status、
        AdminAudit 读取的 row.occurred_at / actor_type / result 都存在于后端真实响应；响应里出现的枚举值全部落在
        shared/adminText.js 映射表的键内（否则页面回退显示英文原值）。"""
        text = src("frontend/src/shared/adminText.js")
        type_keys = _table_keys(text, "CLAIM_TYPE_TEXT")
        status_keys = _table_keys(text, "CLAIM_STATUS_TEXT")
        actor_keys = _table_keys(text, "AUDIT_ACTOR_TEXT")
        result_keys = _table_keys(text, "AUDIT_RESULT_TEXT")
        self.assertEqual((len(type_keys), len(status_keys), len(actor_keys), len(result_keys)), (3, 4, 3, 3))

        # 造数据：一张报销（PENDING）、一张被拒绝的发起（DENIED 审计）与管理员登录等产生的审计行
        resp = self.api("post", "/claims/reimbursements", {
            "amount": "10.00", "reason": "打印", "occurred_on": str(date.today()),
            "invoice_ids": [str(_invoice(self.member).id)], "approval_flow_id": self.flow.id}, token=self.mtoken)
        self.assert_ok(resp, 201)
        guest, gtoken = self.make_user()
        self.assert_error(self.api("post", "/claims/reimbursements", {
            "amount": "10.00", "reason": "x", "occurred_on": str(date.today()),
            "invoice_ids": [str(_invoice(guest).id)], "approval_flow_id": self.flow.id}, token=gtoken), 403)

        claims = self.assert_ok(self.api("get", "/admin/claims", token=self.admin_token)).data
        self.assertGreaterEqual(claims["count"], 1)
        fin_page = src("frontend/src/admin/AdminFinance.vue")
        self.assertEqual(reads(fin_page, ["row"]) & {"type", "status"}, {"type", "status"})
        for row in claims["results"]:
            self.assertIn(row["type"], type_keys)
            self.assertIn(row["status"], status_keys)

        # 审计行：管理员真实操作各写一条 SUCCESS / FAILURE；另用审计服务补 MEMBER / SYSTEM 主体与 DENIED 结果，
        # 使三种主体、三种结果都出现在真实的 /admin/audit-logs 响应里
        self.assert_ok(self.api("put", "/admin/committee/config", {"cap_member": 9}, token=self.admin_token))
        self.assert_error(self.api("put", "/admin/committee/config", {"cap_member": -3}, token=self.admin_token),
                          400, "INVALID_VALUE")
        AuditService.record(actor=AuditActor(type="MEMBER", id=self.member.id, label="委员"), action="INCOME_VOIDED",
                            object_type="income_sheet", object_id="1", result="DENIED")
        AuditService.record(actor=system_actor(), action="INCOME_VOIDED", object_type="income_sheet",
                            object_id="2", result="SUCCESS")
        logs = self.assert_ok(self.api("get", "/admin/audit-logs", {"page_size": 100}, token=self.admin_token)).data
        self.assertGreaterEqual(len(logs["results"]), 1)
        audit_page = src("frontend/src/admin/AdminAudit.vue")
        read_fields = reads(audit_page, ["row"])
        self.assertGreaterEqual(read_fields, {"occurred_at", "actor_type", "result"})
        self.assertEqual({r["actor_type"] for r in logs["results"]}, actor_keys)
        self.assertEqual({r["result"] for r in logs["results"]}, result_keys)
        for row in logs["results"]:
            self.assertGreaterEqual(set(row), {"occurred_at", "actor_type", "result"})
            self.assertIn(row["actor_type"], actor_keys)
            self.assertIn(row["result"], result_keys)
        # 前端调用路径可解析（列表筛选接口）
        calls = {(m, p) for _, m, p, _ in extract_calls(REPO / "frontend/src/shared/api.js")}
        for pair in (("GET", "/admin/claims"), ("GET", "/admin/audit-logs")):
            self.assertIn(pair, calls)
            self.assertTrue(hasattr(resolve("/api/v1" + pair[1]).func.cls, "get"))
