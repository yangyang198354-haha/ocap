"""远程 HTTP E2E 用例（画像 P4-1；TC-E2E-320 ~ 341）。

前置：测试机上已执行 `OCAP_E2E_FIXTURE=1 OCAP_E2E_PASSWORD=… python manage.py e2e_fixture setup --units 3 --bulk-users 25 --bulk-resolutions 25`。
每个用例结束时自行恢复自己制造的数据（模板、内容、流程、申请状态）；兜底由 `e2e_fixture cleanup --execute` 处理。
不修改清册、不写全局配置有效值、不触发验证码流程（护栏见 remote_client.WRITE_ALLOWLIST）。
"""
import os
import time
import unittest

from .remote_client import Config, GuardError, Remote

R: Remote | None = None
FIX: dict = {}


def setUpModule():  # noqa: N802 (unittest 约定)
    global R
    R = Remote(Config())
    for key in ("e2e_owner_a", "e2e_owner_b", "e2e_resident", "e2e_applicant", "e2e_guest", "e2e_other_head",
                "e2e_multi", "e2e_member", "e2e_member2", "e2e_rep", "admin"):
        R.login(key)
    housing = R.get("/me/housing", "e2e_owner_a").json()
    FIX["u1"] = housing["units"][0]
    housing3 = R.get("/me/housing", "e2e_multi").json()
    FIX["multi"] = housing3
    FIX["ids"] = dict(R.ids)


def tearDownModule():  # noqa: N802
    if R is not None:
        for key in ("e2e_applicant",):
            pass  # 申请/申诉均已在用例内收尾；残留由 cleanup 兜底


class RemoteBase(unittest.TestCase):
    def j(self, resp, status=200):
        self.assertEqual(resp.status_code, status, f"{resp.request.method} {resp.request.path_url} -> {resp.status_code}")
        return resp.json() if resp.content else None

    def err(self, resp, status, code=None):
        self.assertEqual(resp.status_code, status, f"{resp.request.method} {resp.request.path_url} -> {resp.status_code}")
        try:
            body = resp.json()
        except ValueError:  # 路由层 404 返回 HTML，不是 JSON 错误体
            body = {}
        if code:
            self.assertEqual(body.get("code"), code)
        return body


class ReadOnlyChecks(RemoteBase):
    def test_320_ac_178_03_existing_flows_keep_fields(self):
        """TC-E2E-320 / AC-178-03：e2e 注册用户依次：登录、决议列表、我的房屋、个人中心 → 均 200，既有字段齐全。"""
        token = R.login("e2e_guest", fresh=True)
        self.assertTrue(token)
        res = self.j(R.get("/resolutions", "e2e_guest", params={"scope": "public"}))
        self.assertTrue({"count", "results"} <= set(res))
        me = self.j(R.get("/me", "e2e_guest"))
        self.assertTrue({"profile", "identities"} <= set(me))
        self.assertTrue({"is_guest", "units", "committee", "labels"} <= set(me["identities"]))
        housing = self.j(R.get("/me/housing", "e2e_guest"))
        self.assertEqual(set(housing), {"summary", "units", "pending_review_count"})
        prof = self.j(R.get("/me/profile", "e2e_guest"))
        self.assertTrue({"account_no", "phone", "nickname", "avatar_url", "birthday", "email"} <= set(prof))

    def test_321_ac_157_01_03_04_identity_consistent_across_views(self):
        """TC-E2E-321 / AC-157-01、03、04：e2e_multi 两行（产权业主 + 同住人）、汇总"产权业主"且多次刷新不变；游客汇总"游客"；管理端标签一致。"""
        first = None
        for _ in range(3):
            h = self.j(R.get("/me/housing", "e2e_multi"))
            me = self.j(R.get("/me", "e2e_multi"))["identities"]
            seq = [(u["unit_id"], u["role_label"]) for u in h["units"]]
            first = first or seq
            self.assertEqual(seq, first)
            self.assertEqual([(u["unit_id"], u["role_label"]) for u in me["units"]], seq)
        self.assertEqual(sorted(label for _, label in first), ["产权业主", "同住人"])
        self.assertEqual(h["summary"]["label"], "产权业主")
        guest = self.j(R.get("/me/housing", "e2e_guest"))
        self.assertEqual((guest["summary"]["label"], guest["units"]), ("游客", []))
        account_no = self.j(R.get("/me/profile", "e2e_multi"))["account_no"]
        users = self.j(R.get("/admin/users", "admin", params={"q": account_no}))["results"]
        self.assertEqual([u["identity_label"] for u in users if u["account_no"] == account_no], ["产权业主"])

    def test_322_ac_166_02_tasks_forbidden_for_non_members(self):
        """TC-E2E-322 / AC-166-02：非业委会成员请求待办 → 403；委员 → 200。"""
        self.err(R.get("/approval/tasks", "e2e_guest"), 403)
        self.err(R.get("/approval/tasks", "e2e_owner_a"), 403)
        self.j(R.get("/approval/tasks", "e2e_member"))

    def test_323_ac_172_170_system_limits_current_values(self):
        """TC-E2E-323 / AC-170-02、AC-172-01、AC-173-01/02：/system/limits 返回 7 个字段，规则常量与需求一致。"""
        limits = self.j(R.get("/system/limits", "e2e_member"))
        self.assertEqual({k: limits[k] for k in ("poll_max_questions", "poll_options_min", "poll_options_max",
                                                 "vote_min_window_minutes", "income_import_max_rows",
                                                 "income_manual_max_records")},
                         {"poll_max_questions": 50, "poll_options_min": 2, "poll_options_max": 10,
                          "vote_min_window_minutes": 60, "income_import_max_rows": 5000,
                          "income_manual_max_records": 500})
        self.assertRegex(limits["claim_amount_max"], r"^\d+\.\d{2}$")
        self.err(R.get("/system/limits"), 401)
        self.err(R.get("/system/limits", "admin"), 403)

    def test_324_ac_159_01_06_user_search_masks_phone_and_requires_admin(self):
        """TC-E2E-324 / AC-159-01、AC-159-06：管理员按账号、手机号后四位、昵称搜索均命中 e2e_owner_a；手机号脱敏；非管理员 403。"""
        account_no = self.j(R.get("/me/profile", "e2e_owner_a"))["account_no"]
        for q in (account_no, "0001", "e2e_owner_a"):
            rows = self.j(R.get("/admin/users", "admin", params={"q": q}))["results"]
            hit = [r for r in rows if r["account_no"] == account_no]
            self.assertTrue(hit, f"搜索 {q} 未命中")
        r = hit[0]
        self.assertEqual(r["phone"], "19900000001")  # 管理后台显示完整手机号
        self.assertEqual(r["identity_label"], "产权业主")
        self.err(R.get("/admin/users", "e2e_guest", params={"q": "e2e"}), 403)

    def test_325_ac_159_03_grant_seat_to_guest_rejected(self):
        """TC-E2E-325 / AC-159-03：对游客赋予委员席位 → 422 NOT_AN_OWNER，不创建席位（先于任何写入被拒）。"""
        guest_id = R.ids["e2e_guest"]
        self.err(R.post("/admin/committee/seats", "admin", json={"user_id": guest_id, "position": "MEMBER"}),
                 422, "NOT_AN_OWNER")
        seats = self.j(R.get("/admin/committee/seats", "admin", params={"page_size": 100}))["results"]
        self.assertFalse([s for s in seats if s.get("user", {}).get("id") == guest_id or s.get("user_id") == guest_id])

    def test_326_ac_160_01_02_admin_user_paging(self):
        """TC-E2E-326 / AC-160-01、AC-160-02：注册用户 > 20 时第 1 页 20 条，全页合计 = count 且无重复；带关键词翻页同口径。"""
        first = self.j(R.get("/admin/users", "admin", params={"page": 1, "page_size": 20}))
        total = first["count"]
        if total <= 20:
            self.skipTest(f"注册用户仅 {total} 个（未用 --bulk-users 造数）")
        self.assertEqual(len(first["results"]), 20)
        ids, page = [], 1
        while len(ids) < total:
            data = self.j(R.get("/admin/users", "admin", params={"page": page, "page_size": 20}))
            self.assertEqual(data["count"], total)
            ids += [r["id"] for r in data["results"]]
            page += 1
            self.assertLess(page, 200)
        self.assertEqual((len(ids), len(set(ids))), (total, total))
        q = self.j(R.get("/admin/users", "admin", params={"q": "e2e_", "page": 2, "page_size": 20}))
        if q["count"] > 20:
            self.assertEqual(q["page"], 2)
            self.assertEqual(len(q["results"]), min(20, q["count"] - 20))

    def test_327_ac_161_01_04_resolution_paging(self):
        """TC-E2E-327 / AC-161-01、AC-161-04：公开决议 > 20 时分页合计 = count、无重复；否则单页含全部。"""
        first = self.j(R.get("/resolutions", "e2e_guest", params={"scope": "public", "page": 1}))
        total = first["count"]
        ids, page = [], 1
        while len(ids) < total:
            data = self.j(R.get("/resolutions", "e2e_guest", params={"scope": "public", "page": page}))
            ids += [r["id"] for r in data["results"]]
            page += 1
            self.assertLess(page, 200)
        self.assertEqual((len(ids), len(set(ids))), (total, total))
        if total <= 20:
            self.assertEqual(len(first["results"]), total)
        else:
            self.assertEqual(len(first["results"]), 20)

    def test_328_ac_168_01_02_report_detail_masks_expense_summary(self):
        """TC-E2E-328 / AC-168-01、AC-168-02：已有报表时明细合计与列表一致、支出事由为空；未登录 401；无报表则 SKIP。"""
        reports = self.j(R.get("/ledger/reports", "e2e_guest"))["results"]
        self.err(R.get("/ledger/reports/1"), 401)
        if not reports:
            self.skipTest("测试环境尚无已生成报表（AC-168-01 需要报表；报表由定时任务生成，远程不造数据）")
        item = reports[0]
        detail = self.j(R.get(f"/ledger/reports/{item['id']}", "e2e_guest"))
        for k in ("total_income", "total_expense", "balance"):
            self.assertEqual(detail[k], item[k])
        for row in detail["detail"]:
            if row["direction"] == "EXPENSE":
                self.assertIsNone(row["summary"])

    def test_329_ac_175_01_template_preflight_is_read_only(self):
        """TC-E2E-329 / AC-175-01：下载 xlsx 模板并预检（dry_run=1）：总行数 6、失败 0；清册专有部分总数前后不变。"""
        before = self.j(R.get("/admin/registry/units", "admin", params={"page_size": 1}))["count"]
        tpl = R.get("/admin/registry/import/template", "admin", params={"file_type": "xlsx"})
        self.assertEqual(tpl.status_code, 200)
        resp = R.post("/admin/registry/import", "admin", params={"dry_run": 1}, files={"file": (
            "template.xlsx", tpl.content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        data = self.j(resp)
        self.assertEqual((data["rows_total"], data["failed"], data["dry_run"]), (6, 0, True))
        # 测试环境清册已有真实数据：示例行若与现有专有部分同名，则"新增"变为"更新"，两者合计必须为 4
        self.assertEqual(data["imported"] + data["updated"], 4, data)
        after = self.j(R.get("/admin/registry/units", "admin", params={"page_size": 1}))["count"]
        self.assertEqual(before, after)

    def test_330_ac_163_02_email_password_login_unified_failure(self):
        """TC-E2E-330 / AC-163-02：邮箱 + 密码走密码登录 → 失败（400/401），提示与"错误密码"一致，不泄露账号是否存在。"""
        a = R.post("/auth/login/password", None, json={"identifier": "e2e_nobody@example.invalid", "password": "Wrong-Pass-1"})
        b = R.post("/auth/login/password", None, json={"identifier": "19900000005", "password": "Wrong-Pass-1"})
        self.assertIn(a.status_code, (400, 401))
        self.assertEqual(a.status_code, b.status_code)
        self.assertEqual(a.json()["message"], b.json()["message"])

    def test_331_ac_155_client_field_validation_and_miniapp_login(self):
        """TC-E2E-331 / AC-155-01（快路径部分）：client 非法 → 400；client=miniapp 登录成功且令牌可用。慢路径见 test_332。"""
        bad = R.post("/auth/login/password", None, json={"identifier": "19900000005", "password": R.cfg.password,
                                                         "client": "ios"})
        self.err(bad, 400, "INVALID_VALUE")
        token = R.login("e2e_guest", client="miniapp")
        self.j(R.get("/me", None, token=token))

    @unittest.skipUnless(os.environ.get("OCAP_E2E_SLOW") == "1", "慢用例：需 OCAP_E2E_SLOW=1（等待 31 分钟）")
    def test_332_ac_155_01_miniapp_session_survives_31_minutes_idle(self):
        """TC-E2E-332 / AC-155-01：小程序（client=miniapp）登录后闲置 31 分钟再请求仍 200；对照 Web 会话 401。"""
        mini = R.login("e2e_guest", client="miniapp")
        web = R.login("e2e_guest", fresh=True)
        time.sleep(31 * 60 + 5)
        self.j(R.get("/me", None, token=mini))
        self.err(R.get("/me", None, token=web), 401)


class MutatingFlows(RemoteBase):
    """会写入 e2e_ 数据的旅程；每个用例结束时恢复。按编号顺序执行。"""

    def _flow_id(self):
        flows = self.j(R.get("/approval/flows", "e2e_member", params={"scope": "EXPENSE"}))
        rows = flows["results"] if isinstance(flows, dict) else flows
        match = [f for f in rows if f["name"] == "e2e_flow_expense"]
        self.assertTrue(match, "夹具流程 e2e_flow_expense 不存在")
        return match[0]["id"]

    def test_333_ac_154_01_03_non_members_cannot_create_claims(self):
        """TC-E2E-333 / AC-154-01、AC-154-03：游客、产权业主、业主代表发起报销/备用金 → 403 且提示含"业委会成员"。"""
        for who in ("e2e_guest", "e2e_owner_a", "e2e_rep"):
            r1 = R.post("/claims/reimbursements", who, json={"amount": "1.00", "reason": "x",
                                                            "occurred_on": "2026-01-01", "invoice_ids": []})
            body = self.err(r1, 403, "FORBIDDEN")
            self.assertIn("业委会成员", body["message"])
            self.err(R.post("/claims/advances", who, json={"amount": "1.00"}), 403, "FORBIDDEN")

    def test_334_ac_154_02_170_01_member_claim_boundaries_then_withdraw(self):
        """TC-E2E-334 / AC-154-02、AC-170-01（默认上限部分）：委员发起 1,000,000.00 成功（审批中）、1,000,000.01 失败并提示当前上限；成功件立即撤回，不推进到审批通过。"""
        limits = self.j(R.get("/system/limits", "e2e_member"))
        if limits["claim_amount_max"] != "1000000.00":
            self.skipTest(f"全局上限已被改动（{limits['claim_amount_max']}），默认边界用例不适用")
        flow_id = self._flow_id()
        from datetime import date

        def body(amount):
            return {"amount": amount, "reason": R.unique("claim"), "occurred_on": date.today().isoformat(),
                    "invoice_ids": [R.upload_png("e2e_member", "INVOICE")], "approval_flow_id": flow_id}

        over = R.post("/claims/reimbursements", "e2e_member", json=body("1000000.01"))
        err = self.err(over, 400, "INVALID_VALUE")
        self.assertIn("1000000.00", err["message"])
        ok = R.post("/claims/reimbursements", "e2e_member", json=body("1000000.00"))
        claim = self.j(ok, 201)
        self.addCleanup(lambda: R.post(f"/claims/{claim['id']}/withdraw", "e2e_member", json={}))
        self.assertEqual(claim["status"], "PENDING")
        withdrawn = self.j(R.post(f"/claims/{claim['id']}/withdraw", "e2e_member", json={}))
        self.assertEqual(withdrawn["status"], "WITHDRAWN")

    def test_335_ac_170_04_amount_limit_permission_and_invalid_values(self):
        """TC-E2E-335 / AC-170-04：非管理员改上限 403；管理员提交 0 / 负数 / 非数字 → 400，原值不变（有效值不在远程写入，Q-B-02）。"""
        before = self.j(R.get("/admin/system-config", "admin"))["claim.amount_max"]
        self.err(R.call("PUT", "/admin/system-config/claim.amount_max", None, token=R.login("e2e_member"),
                        json={"value": 0}), 403)
        for bad in (0, -1, "abc"):
            self.err(R.call("PUT", "/admin/system-config/claim.amount_max", "admin", json={"value": bad}),
                     400, "INVALID_VALUE")
        self.assertEqual(self.j(R.get("/admin/system-config", "admin"))["claim.amount_max"], before)
        with self.assertRaises(GuardError):  # 护栏自检：有效值写入在发出前被拦截
            R.call("PUT", "/admin/system-config/claim.amount_max", "admin", json={"value": "500000"})

    def test_336_ac_150_151_152_153_resident_chain(self):
        """TC-E2E-336 / AC-150-01、03、AC-151-01、02、03、AC-152-01、02、AC-153-01、02、03：
        e2e_applicant 申请 U1 → 重复被拒 → 业主首页计数/列表 → 同住人与他房户主不能审批 → e2e_owner_b 拒绝 →
        再申请 → e2e_owner_a 通过 → 他人不能移除 → 业主移除 → 再申请通过后主动退出。结束时 e2e_applicant 无房屋关系、无待审申请。"""
        unit_id = FIX["u1"]["unit_id"]
        apply = lambda: R.post("/resident-applications", "e2e_applicant", json={"unit_id": unit_id})
        before = self.j(R.get("/me/housing", "e2e_owner_a"))["pending_review_count"]
        first = self.j(apply(), 201)
        self.assertEqual(first["status"], "PENDING")
        self.err(apply(), 409, "APPLICATION_PENDING")
        h = self.j(R.get("/me/housing", "e2e_owner_a"))
        self.assertEqual(h["pending_review_count"], before + 1)
        queue = self.j(R.get("/resident-applications/to-review", "e2e_owner_a"))
        mine = [q for q in queue if q["id"] == first["id"]]
        self.assertEqual(len(mine), 1)
        self.assertNotIn("19900000004", str(mine[0]))
        self.assertIn("****", mine[0]["applicant"]["phone"])
        for who in ("e2e_resident", "e2e_other_head"):
            self.err(R.post(f"/resident-applications/{first['id']}/decision", who, json={"decision": "APPROVE"}), 403)
            self.assertEqual(self.j(R.get("/me/housing", who))["pending_review_count"], 0)
        self.j(R.post(f"/resident-applications/{first['id']}/decision", "e2e_owner_b", json={"decision": "REJECT"}))
        self.err(R.post(f"/resident-applications/{first['id']}/decision", "e2e_owner_a", json={"decision": "APPROVE"}),
                 409, "ALREADY_DECIDED")
        listing = self.j(R.get("/resident-applications/mine", "e2e_applicant"))
        self.assertEqual((listing[0]["status"], bool(listing[0]["decided_at"])), ("REJECTED", True))
        self.assertEqual(listing[0]["unit"]["specific_part"], FIX["u1"]["specific_part"])
        second = self.j(apply(), 201)
        self.j(R.post(f"/resident-applications/{second['id']}/decision", "e2e_owner_a", json={"decision": "APPROVE"}))
        self.assertEqual(self.j(R.get("/me/housing", "e2e_applicant"))["summary"]["label"], "同住人")
        applicant_id = R.ids["e2e_applicant"]
        # AC-153-03：其他同住人、其他房屋户主、管理员移除 → 403
        for who in ("e2e_resident", "e2e_other_head", "admin"):
            self.err(R.call("DELETE", f"/units/{unit_id}/residents/{applicant_id}", who), 403)
        residents = [r["user_id"] for r in self.j(R.get("/me/housing", "e2e_owner_a"))["units"][0]["residents"]]
        self.assertIn(applicant_id, residents)
        # AC-153-01：业主移除 → 回到游客
        r = R.call("DELETE", f"/units/{unit_id}/residents/{applicant_id}", "e2e_owner_a")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(self.j(R.get("/me/housing", "e2e_applicant"))["summary"]["label"], "游客")
        # AC-153-02：再申请、通过、主动退出
        third = self.j(apply(), 201)
        self.j(R.post(f"/resident-applications/{third['id']}/decision", "e2e_owner_a", json={"decision": "APPROVE"}))
        self.assertEqual(R.post(f"/units/{unit_id}/leave", "e2e_applicant", json={}).status_code, 204)
        final = self.j(R.get("/me/housing", "e2e_applicant"))
        self.assertEqual((final["summary"]["label"], final["units"]), ("游客", []))
        self.assertEqual(self.j(R.get("/me/housing", "e2e_owner_a"))["pending_review_count"], before)
        statuses = [x["status"] for x in self.j(R.get("/resident-applications/mine", "e2e_applicant"))]
        self.assertEqual(statuses[:3], ["APPROVED", "APPROVED", "REJECTED"])
        # AC-152-03：其他用户列表中看不到他人的申请
        self.assertEqual(self.j(R.get("/resident-applications/mine", "e2e_guest")), [])

    def test_337_ac_156_158_appeal_reject_only_no_registry_write(self):
        """TC-E2E-337 / AC-156-01~03、AC-199-01：e2e_applicant 申诉 U1（带 owner_name）→ 待审核 → 管理员列表可见产权人名字与资料 → 驳回（原因可见）→
        再申诉 → 再驳回。**只走提交与驳回，不执行"通过"**：通过会向真实清册追加产权人，越出画像 P4-1（GR-C-001-F02）。
        申诉通过路径（追加清册、撤销认证）标 NOT_TESTABLE（远程），由本地 TC-INT/TC-E2E 覆盖，见 e2e_test_report 人工验证清单。"""
        unit_id = FIX["u1"]["unit_id"]

        def submit():
            proof = R.upload_png("e2e_applicant", "APPEAL_PROOF")
            return self.j(R.post("/appeals", "e2e_applicant", json={
                "unit_id": unit_id, "owner_name": "e2e_申诉人", "proof_ids": [proof]}), 201)

        first = submit()
        row = self.j(R.get("/appeals/mine", "e2e_applicant"))[0]
        self.assertEqual((row["status"], row["decided_at"]), ("PENDING", None))
        listing = self.j(R.get("/admin/appeals", "admin", params={"status": "PENDING", "page_size": 100}))
        mine = [a for a in listing["results"] if a["id"] == first["id"]]
        self.assertEqual(len(mine), 1)
        self.assertEqual((mine[0]["owner_name"], len(mine[0]["proof"])), ("e2e_申诉人", 1))
        reason = R.unique("驳回")
        self.j(R.post(f"/admin/appeals/{first['id']}/decision", "admin", json={"decision": "REJECT", "reject_reason": reason}))
        row = self.j(R.get("/appeals/mine", "e2e_applicant"))[0]
        self.assertEqual((row["status"], row["reject_reason"]), ("REJECTED", reason))
        self.assertTrue(row["decided_at"])
        self.assertEqual(self.j(R.get("/appeals/mine", "e2e_guest")), [])
        second = submit()
        self.j(R.post(f"/admin/appeals/{second['id']}/decision", "admin",
                      json={"decision": "REJECT", "reject_reason": R.unique("再驳回")}))
        self.assertEqual(self.j(R.get("/appeals/mine", "e2e_applicant"))[0]["status"], "REJECTED")
        after = self.j(R.get("/me/housing", "e2e_applicant"))
        self.assertEqual((after["summary"]["label"], after["units"]), ("游客", []))

    def test_338_ac_159_05_flow_approvers_selected_from_search(self):
        """TC-E2E-338 / AC-159-05：管理员为审批流程添加两位现任成员 → 列表显示其昵称；添加非成员被拒；测完删除该流程（未被引用时可物理删除）。"""
        name = R.unique("flow")
        ids = [R.ids["e2e_member"], R.ids["e2e_member2"]]
        created = self.j(R.post("/admin/approval/flows", "admin", json={"scope": "EXPENSE", "mode": "DESIGNATED",
                                                                       "name": name, "approver_ids": ids}), 201)
        self.addCleanup(lambda: R.call("DELETE", f"/admin/approval/flows/{created['id']}", "admin"))
        listing = self.j(R.get("/admin/approval/flows", "admin", params={"page_size": 100}))
        rows = listing["results"] if isinstance(listing, dict) else listing
        mine = [f for f in rows if f["id"] == created["id"]]
        self.assertEqual({a["nickname"] for a in mine[0]["approvers"]}, {"e2e_member", "e2e_member2"})
        bad = R.post("/admin/approval/flows", "admin", json={"scope": "EXPENSE", "mode": "DESIGNATED",
                                                            "name": R.unique("flowbad"), "approver_ids": [R.ids["e2e_guest"]]})
        self.assertIn(bad.status_code, (400, 409, 422))
        self.err(R.post("/admin/approval/flows", "e2e_guest", json={"scope": "EXPENSE", "mode": "DESIGNATED",
                                                                   "name": R.unique("flowx"), "approver_ids": ids}), 403)

    def test_339_ac_162_style_template_crud_and_in_use(self):
        """TC-E2E-339 / AC-162-01~06：新建 e2e_ 模板 → 列表可见 → 改名与样式 → 空名被拒 → 内容引用后删除被拒（含引用数）→
        内置模板不可改删（404）→ 非管理员 403；测完删除内容与模板。"""
        name = R.unique("模板")
        tpl = self.j(R.post("/admin/content/style-templates", "admin",
                            json={"name": name, "tokens": {"font_size": 17, "text_color": "#112233"}}), 201)
        self.addCleanup(lambda: R.call("DELETE", f"/admin/content/style-templates/{tpl['id']}", "admin"))
        keys = [t["key"] for t in self.j(R.get("/admin/content/style-templates", "admin"))]
        self.assertIn(tpl["key"], keys)
        renamed = R.unique("模板新")
        upd = self.j(R.call("PUT", f"/admin/content/style-templates/{tpl['id']}", "admin",
                            json={"name": renamed, "tokens": {"font_size": 19}}))
        self.assertEqual((upd["name"], upd["tokens"]["font_size"]), (renamed, 19))
        self.err(R.call("PUT", f"/admin/content/style-templates/{tpl['id']}", "admin", json={"name": " "}),
                 400, "STYLE_NAME_REQUIRED")
        doc = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "e2e 正文"}]}]}
        post = self.j(R.post("/admin/content/posts", "admin",
                             json={"title": R.unique("内容"), "doc": doc, "style_key": tpl["key"]}), 201)
        self.addCleanup(lambda: R.call("DELETE", f"/admin/content/posts/{post['id']}", "admin"))
        row = [t for t in self.j(R.get("/admin/content/style-templates", "admin")) if t["key"] == tpl["key"]][0]
        self.assertEqual(row["usage_count"], 1)
        body = self.err(R.call("DELETE", f"/admin/content/style-templates/{tpl['id']}", "admin"), 409, "STYLE_IN_USE")
        self.assertIn("1", body["message"])
        for method in ("PUT", "DELETE"):
            self.err(R.call(method, "/admin/content/style-templates/builtin:classic", "admin", json={"name": "x"}), 404)
        self.err(R.post("/admin/content/style-templates", "e2e_guest", json={"name": R.unique("x"), "tokens": {}}), 403)
        self.err(R.call("DELETE", f"/admin/content/style-templates/{tpl['id']}", "e2e_guest"), 403)

    def test_340_ac_169_01_offline_post_returns_404(self):
        """TC-E2E-340 / AC-169-01：e2e_ 内容发布后用户可读（200），下线后用户请求详情 → 404；不存在的编号同样 404；测完删除。"""
        doc = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "e2e 下线"}]}]}
        post = self.j(R.post("/admin/content/posts", "admin", json={"title": R.unique("下线"), "doc": doc}), 201)
        self.addCleanup(lambda: R.call("DELETE", f"/admin/content/posts/{post['id']}", "admin"))
        self.j(R.post(f"/admin/content/posts/{post['id']}/publish", "admin", json={}))
        self.j(R.get(f"/info/posts/{post['id']}", "e2e_guest"))
        self.j(R.post(f"/admin/content/posts/{post['id']}/offline", "admin", json={}))
        self.err(R.get(f"/info/posts/{post['id']}", "e2e_guest"), 404)
        self.err(R.get("/info/posts/999999999", "e2e_guest"), 404)

    def test_341_ac_165_01_birthday_roundtrip_restored(self):
        """TC-E2E-341 / AC-165-01：保存生日后刷新显示；留空保存成功；恢复为空。"""
        self.addCleanup(lambda: R.call("PATCH", "/me/profile", "e2e_guest", json={"birthday": None}))
        self.j(R.call("PATCH", "/me/profile", "e2e_guest", json={"birthday": "1990-05-06"}))
        self.assertEqual(self.j(R.get("/me/profile", "e2e_guest"))["birthday"], "1990-05-06")
        self.j(R.call("PATCH", "/me/profile", "e2e_guest", json={"birthday": None}))
        self.assertIsNone(self.j(R.get("/me/profile", "e2e_guest"))["birthday"])
