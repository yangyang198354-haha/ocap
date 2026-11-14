"""ocap_product_review GROUP_D：本地端到端旅程（TC-E2E-309 ~ 317、342、343）。

每个用例是多步、跨角色的完整旅程（真实 DRF 路由 + 中间件 + SQLite 内存库，外部服务经替身）。
critical path = Must Have 故事（US-150~162、US-176、US-178）的旅程；此处无浏览器，
旅程在 HTTP API 层完成，界面步骤由 frontend/miniprogram 的 vitest 用例覆盖（见 test_plan）。
"""
from datetime import date, timedelta
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import AuthToken
from apps.accounts.services import _sha256
from apps.core.audit import AuditLog
from apps.core.models import Attachment
from apps.resolutions.models import Resolution
from tests.support import ApiTestBase

PNG = b"\x89PNG\r\n\x1a\n" + b"7" * 32


def _invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE", original_name="i.pdf",
        content_type="application/pdf", size=10, sha256="x" * 64,
        storage_path=f"tmp/{uuid4().hex}", status="TEMP")


class ResidentJourneyTests(ApiTestBase):
    def test_tc_e2e_309_us_150_153_apply_review_remove_leave_full_journey(self):
        """TC-E2E-309 / US-150、151、152、153（AC-150-01、151-01/02、152-01/02、153-01/02）：
        逐级选房申请 → 业主首页提示 → 拒绝 → 再申请 → 通过 → 业主移除 → 再申请通过 → 同住人退出。"""
        owner, otoken, unit = self.make_owner()
        applicant, atoken = self.make_user(nickname="e2e_申请人")
        levels = self.assert_ok(self.api("get", "/units/options", token=atoken)).data
        self.assertTrue(levels["options"])
        apply = lambda: self.api("post", "/resident-applications", {"unit_id": unit.id}, token=atoken)
        first = self.assert_ok(apply(), 201).data
        self.assertEqual(self.api("get", "/me/housing", token=otoken).data["pending_review_count"], 1)
        queue = self.api("get", "/resident-applications/to-review", token=otoken).data
        self.assertEqual([q["id"] for q in queue], [first["id"]])
        self.assertEqual(queue[0]["applicant"]["nickname"], "e2e_申请人")
        self.assert_ok(self.api("post", f"/resident-applications/{first['id']}/decision",
                                {"decision": "REJECT"}, token=otoken))
        self.assertEqual(self.api("get", "/me/housing", token=otoken).data["pending_review_count"], 0)
        mine = self.api("get", "/resident-applications/mine", token=atoken).data
        self.assertEqual((mine[0]["status"], bool(mine[0]["decided_at"])), ("REJECTED", True))
        second = self.assert_ok(apply(), 201).data
        self.assert_ok(self.api("post", f"/resident-applications/{second['id']}/decision",
                                {"decision": "APPROVE"}, token=otoken))
        housing = self.api("get", "/me/housing", token=atoken).data
        self.assertEqual((housing["summary"]["label"], housing["units"][0]["role_label"]), ("同住人", "同住人"))
        self.assertEqual(housing["units"][0]["residents"], [])
        names = [r["user_id"] for r in self.api("get", "/me/housing", token=otoken).data["units"][0]["residents"]]
        self.assertEqual(names, [applicant.id])
        self.assert_ok(self.api("delete", f"/units/{unit.id}/residents/{applicant.id}", token=otoken), 204)
        self.assertEqual(self.api("get", "/me/housing", token=atoken).data["summary"]["label"], "游客")
        third = self.assert_ok(apply(), 201).data
        self.assert_ok(self.api("post", f"/resident-applications/{third['id']}/decision",
                                {"decision": "APPROVE"}, token=otoken))
        self.assert_ok(self.api("post", f"/units/{unit.id}/leave", {}, token=atoken), 204)
        self.assertEqual(self.api("get", "/me/housing", token=otoken).data["units"][0]["residents"], [])
        statuses = [r["status"] for r in self.api("get", "/resident-applications/mine", token=atoken).data]
        self.assertEqual(statuses, ["APPROVED", "APPROVED", "REJECTED"])
        actions = set(AuditLog.objects.values_list("action", flat=True))
        self.assertTrue({"RESIDENT_REMOVED", "RESIDENT_LEFT", "RESIDENT_APPLICATION_DECIDED"} <= actions)


class AppealIdentityJourneyTests(ApiTestBase):
    def test_tc_e2e_310_us_156_157_158_appeal_reject_resubmit_approve_then_revoke(self):
        """TC-E2E-310 / US-156、157、158（AC-156-01~04、157-01、157-04、158-02）：
        申诉 → 驳回（原因可见）→ 再申诉 → 通过 → 三处身份一致（本人/汇总/管理端）→ 管理员撤销认证 → 审计。"""
        unit = self.make_unit(phones=["13900009999"], name="张三")
        user, token = self.make_user(nickname="e2e_申诉人")
        _, admin_token = self.make_admin()

        def submit():
            up = self.upload("/attachments", {"file": SimpleUploadedFile(
                "p.png", PNG + uuid4().bytes, content_type="image/png"), "purpose": "APPEAL_PROOF"}, token=token)
            return self.assert_ok(self.api("post", "/appeals", {
                "unit_id": unit.id, "proof_ids": [up.data["id"]]}, token=token), 201).data

        first = submit()
        pending = self.api("get", "/admin/appeals", {"status": "PENDING"}, token=admin_token).data
        self.assertEqual([a["id"] for a in pending["results"]], [first["id"]])
        self.assert_ok(self.api("post", f"/admin/appeals/{first['id']}/decision",
                                {"decision": "REJECT", "reject_reason": "产权证明模糊"}, token=admin_token))
        row = self.api("get", "/appeals/mine", token=token).data[0]
        self.assertEqual((row["status"], row["reject_reason"]), ("REJECTED", "产权证明模糊"))
        second = submit()
        self.assert_ok(self.api("post", f"/admin/appeals/{second['id']}/decision",
                                {"decision": "APPROVE"}, token=admin_token))
        me = self.api("get", "/me", token=token).data["identities"]
        housing = self.api("get", "/me/housing", token=token).data
        users = self.api("get", "/admin/users", {"q": user.account_no}, token=admin_token).data["results"]
        self.assertEqual({me["summary"]["label"], housing["summary"]["label"], users[0]["identity_label"]}, {"户主"})
        self.assert_ok(self.api("post", "/admin/memberships/revoke", {"user_id": user.id, "unit_id": unit.id},
                                token=admin_token))
        self.assertEqual(self.api("get", "/me/housing", token=token).data["units"], [])
        self.assertEqual(self.api("get", "/me/housing", token=token).data["summary"]["label"], "游客")
        self.assertTrue(AuditLog.objects.filter(action="CERTIFICATION_REVOKED").exists())


class CancelJourneyTests(ApiTestBase):
    def test_tc_e2e_311_us_164_cancel_closes_pending_everywhere(self):
        """TC-E2E-311 / US-164、158（AC-164-01~03）：用户有待审申请与申诉 → 验证码注销 → 业主待审与首页计数清空、
        管理员待审申诉清空、已关闭记录不能再通过、已处理历史不变、审计各 1 条。"""
        owner, otoken, unit = self.make_owner()
        _, admin_token = self.make_admin()
        user, token = self.make_user()
        other_unit = self.make_unit(phones=["13900008888"])
        self.assert_ok(self.api("post", "/resident-applications", {"unit_id": unit.id}, token=token), 201)
        up = self.upload("/attachments", {"file": SimpleUploadedFile("p.png", PNG, content_type="image/png"),
                                          "purpose": "APPEAL_PROOF"}, token=token)
        appeal = self.assert_ok(self.api("post", "/appeals", {"unit_id": other_unit.id,
                                                              "proof_ids": [up.data["id"]]}, token=token), 201).data
        self.assertEqual(self.api("get", "/me/housing", token=otoken).data["pending_review_count"], 1)
        code = self.request_me_code(token, "CANCEL")
        self.assertEqual(self.api("post", "/me/cancel", {"phone": user.phone, "code": code},
                                  token=token).status_code, 204)
        self.assertEqual(self.api("get", "/me/housing", token=otoken).data["pending_review_count"], 0)
        self.assertEqual(self.api("get", "/resident-applications/to-review", token=otoken).data, [])
        pend = self.api("get", "/admin/appeals", {"status": "PENDING"}, token=admin_token).data
        self.assertEqual(pend["results"], [])
        self.assert_error(self.api("post", f"/admin/appeals/{appeal['id']}/decision", {"decision": "APPROVE"},
                                   token=admin_token), 409, "ALREADY_CLOSED")
        self.assertEqual(AuditLog.objects.filter(action="APPEAL_CLOSED").count(), 1)
        self.assertEqual(AuditLog.objects.filter(action="RESIDENT_APPLICATION_CLOSED").count(), 1)
        self.assertEqual(self.api("get", "/me", token=token).status_code, 401)


class FinanceJourneyTests(ApiTestBase):
    def test_tc_e2e_312_us_154_168_170_member_claim_approved_report_masked_limit_changed(self):
        """TC-E2E-312 / US-154、168、170（AC-154-01/02、168-01、170-01/03）：非成员被拒 → 委员发起报销 → 审批通过 →
        生成季度报表 → 普通用户看到明细合计、支出事由为空；管理员把上限改为 500000 后新提交按新上限，旧记录不变。"""
        member, mtoken, _ = self.make_owner()
        self.make_seat(member, "MEMBER")
        approver, atoken, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        plain, ptoken, _ = self.make_owner()
        _, admin_token = self.make_admin()
        flow = self.make_flow(scope="EXPENSE", approvers=[approver])
        body = lambda who, amount: {"amount": amount, "reason": "e2e_私人事由XYZ", "occurred_on": str(date.today()),
                                    "invoice_ids": [str(_invoice(who).id)], "approval_flow_id": flow.id}
        self.assert_error(self.api("post", "/claims/reimbursements", body(plain, "10.00"), token=ptoken), 403)
        claim = self.assert_ok(self.api("post", "/claims/reimbursements", body(member, "800000.00"),
                                        token=mtoken), 201).data
        self.assertEqual(claim["status"], "PENDING")
        tasks = self.assert_ok(self.api("get", "/approval/tasks", {"scope": "EXPENSE"}, token=atoken)).data
        self.assertEqual(tasks["count"], 1)
        task = tasks["results"][0]
        self.assertEqual((task["subject_type"], task["subject_id"]), ("claim", claim["id"]))
        self.assert_ok(self.api("post", f"/approval/instances/{task['instance_id']}/decision",
                                {"action": "APPROVE"}, token=atoken))
        self.assertEqual(self.api("get", f"/claims/{claim['id']}", token=mtoken).data["status"], "APPROVED")
        report = self.assert_ok(self.api("post", "/ledger/reports/generate",
                                         {"period_type": "YEAR", "year": date.today().year}, token=mtoken), 201).data
        detail = self.assert_ok(self.api("get", f"/ledger/reports/{report['id']}", token=ptoken)).data
        expense = [r for r in detail["detail"] if r["direction"] == "EXPENSE"]
        self.assertEqual((detail["total_expense"], len(expense)), ("800000.00", 1))
        self.assertIsNone(expense[0]["summary"])
        self.assertNotIn("XYZ", str(detail))
        self.assert_ok(self.api("put", "/admin/system-config/claim.amount_max", {"value": "500000"},
                                token=admin_token))
        self.assert_error(self.api("post", "/claims/reimbursements", body(member, "500000.01"), token=mtoken),
                          400, "INVALID_VALUE")
        self.assert_ok(self.api("post", "/claims/reimbursements", body(member, "500000.00"), token=mtoken), 201)
        self.assertEqual(self.api("get", f"/claims/{claim['id']}", token=mtoken).data["amount"], "800000.00")


class AdminSeatAndFlowJourneyTests(ApiTestBase):
    def test_tc_e2e_313_us_159_160_search_grant_seat_configure_flow_and_page(self):
        """TC-E2E-313 / US-159、160（AC-159-01/03/05/06、160-01）：管理员按手机号后四位搜索 → 选中游客被拒 →
        选中产权业主赋予委员席位 → 流程添加审批人（席位持有者）→ 非管理员搜索被拒 → 席位与账号列表翻页总数一致。"""
        _, admin_token = self.make_admin()
        self.assert_ok(self.api("put", "/admin/committee/config",
                                {"term_months_chair": 12, "term_months_vice": 12, "term_months_member": 12,
                                 "term_months_rep": 12, "cap_member": 30}, token=admin_token))
        owner, otoken, _ = self.make_owner(phone="13800005678")
        owner.nickname = "e2e_业主甲"
        owner.save()
        guest, _ = self.make_user(phone="13800005679", nickname="e2e_游客乙")
        hits = self.api("get", "/admin/users", {"q": "5678"}, token=admin_token).data["results"]
        self.assertEqual([h["id"] for h in hits], [owner.id])
        self.assertEqual(hits[0]["phone"], "138****5678")
        self.assert_error(self.api("post", "/admin/committee/seats", {"user_id": guest.id, "position": "MEMBER"},
                                   token=admin_token), 422, "NOT_AN_OWNER")
        seat = self.assert_ok(self.api("post", "/admin/committee/seats", {"user_id": owner.id, "position": "MEMBER"},
                                       token=admin_token), 201).data
        self.assertEqual(seat["position"], "MEMBER")
        flow = self.assert_ok(self.api("post", "/admin/approval/flows", {
            "scope": "EXPENSE", "mode": "DESIGNATED", "name": "e2e_流程", "approver_ids": [owner.id]},
            token=admin_token), 201).data
        self.assertTrue(flow)
        self.assertEqual(self.api("get", "/admin/users", {"q": "5678"}, token=otoken).status_code, 403)
        for i in range(21):
            u, _, _ = self.make_owner()
            self.make_seat(u, "REPRESENTATIVE")
        seats = self.api("get", "/admin/committee/seats", {"page": 2, "page_size": 20}, token=admin_token).data
        self.assertEqual((seats["count"], len(seats["results"])), (22, 2))
        users = self.api("get", "/admin/users", {"page": 1, "page_size": 20}, token=admin_token).data
        self.assertEqual(len(users["results"]), 20)
        self.assertGreater(users["count"], 20)


class ContentStyleJourneyTests(ApiTestBase):
    def test_tc_e2e_314_us_162_169_template_crud_content_publish_offline_404(self):
        """TC-E2E-314 / US-162、169（AC-162-01~05、169-01）：新建模板 → 内容选用并发布 → 删除被拒（引用 1 条）→
        内容下线 → 用户端 404 → 删除内容 → 删除模板成功 → 内置模板不可改。"""
        _, admin_token = self.make_admin()
        _, utoken = self.make_user()
        tpl = self.assert_ok(self.api("post", "/admin/content/style-templates",
                                      {"name": "e2e_模板A", "tokens": {"font_size": 18, "text_color": "#223344"}},
                                      token=admin_token), 201).data
        doc = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "旅程正文"}]}]}
        post = self.assert_ok(self.api("post", "/admin/content/posts",
                                       {"title": "e2e_内容", "doc": doc, "style_key": tpl["key"]},
                                       token=admin_token), 201).data
        self.assert_ok(self.api("post", f"/admin/content/posts/{post['id']}/publish", {}, token=admin_token))
        detail = self.assert_ok(self.api("get", f"/info/posts/{post['id']}", token=utoken)).data
        self.assertIn("旅程正文", str(detail))
        listing = [t for t in self.api("get", "/admin/content/style-templates", token=admin_token).data
                   if t["key"] == tpl["key"]]
        self.assertEqual(listing[0]["usage_count"], 1)
        self.assert_error(self.api("delete", f"/admin/content/style-templates/{tpl['id']}", token=admin_token),
                          409, "STYLE_IN_USE")
        self.assert_ok(self.api("post", f"/admin/content/posts/{post['id']}/offline", {}, token=admin_token))
        self.assert_error(self.api("get", f"/info/posts/{post['id']}", token=utoken), 404)
        self.assert_ok(self.api("delete", f"/admin/content/posts/{post['id']}", token=admin_token), 204)
        self.assert_ok(self.api("delete", f"/admin/content/style-templates/{tpl['id']}", token=admin_token), 204)
        self.assertEqual(self.api("put", "/admin/content/style-templates/builtin:classic", {"name": "x"},
                                  token=admin_token).status_code, 404)


class SessionJourneyTests(ApiTestBase):
    def test_tc_e2e_315_us_155_miniapp_password_login_survives_idle_but_not_seven_days(self):
        """TC-E2E-315 / US-155（AC-155-01/02）：小程序账号密码登录 → 闲置 31 分钟仍可访问 → 6 天 23 小时仍可 → 满 7 天 401。"""
        from django.contrib.auth.hashers import make_password

        user, _ = self.make_user()
        user.password = make_password("Passw0rd123")
        user.save()
        token = self.api("post", "/auth/login/password", {"identifier": user.account_no,
                                                          "password": "Passw0rd123",
                                                          "client": "miniapp"}).data["token"]
        row = AuthToken.objects.get(key_hash=_sha256(token))
        AuthToken.objects.filter(pk=row.pk).update(last_active_at=timezone.now() - timedelta(minutes=31))
        self.assert_ok(self.api("get", "/me", token=token))
        AuthToken.objects.filter(pk=row.pk).update(created_at=timezone.now() - timedelta(days=6, hours=23))
        self.assert_ok(self.api("get", "/me", token=token))
        AuthToken.objects.filter(pk=row.pk).update(created_at=timezone.now() - timedelta(days=7, minutes=1))
        self.assertEqual(self.api("get", "/me", token=token).status_code, 401)
        self.assertFalse(AuthToken.objects.filter(pk=row.pk).exists())


class ResolutionRuleJourneyTests(ApiTestBase):
    def test_tc_e2e_316_us_171_172_half_majority_resolution_denominator_and_window(self):
        """TC-E2E-316 / US-171、172（AC-171-01、172-04）：主任发起半数同意决议（窗口 59 分钟被拒、2 小时成功）→ 4 名委员投票 →
        截止后判定：同意 3 票 × 2 > 在任 5 人 → 通过，分母 5；列表可见结果。"""
        chair, ctoken, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        members = []
        for _ in range(4):
            u, t, _ = self.make_owner()
            self.make_seat(u, "MEMBER")
            members.append((u, t))
        flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY")
        payload = lambda minutes: {"title": "e2e_半数决议", "content": "正文", "approval_flow_id": flow.id,
                                   "vote_deadline": (timezone.now() + timedelta(minutes=minutes)).isoformat()}
        self.assertGreaterEqual(self.api("post", "/resolutions", payload(59), token=ctoken).status_code, 400)
        created = self.assert_ok(self.api("post", "/resolutions", payload(120), token=ctoken), 201).data
        for (u, t), choice in zip(members, ["AGREE", "AGREE", "DISAGREE", "ABSTAIN"]):
            self.assert_ok(self.api("post", f"/resolutions/{created['id']}/votes", {"choice": choice}, token=t))
        self.assert_ok(self.api("post", f"/resolutions/{created['id']}/votes", {"choice": "AGREE"}, token=ctoken))
        row = Resolution.objects.get(id=created["id"])
        self.assertEqual(row.status, "PENDING")  # 截止前不判定（AC-171-04）
        call_command("run_due_jobs")
        self.assertEqual(Resolution.objects.get(id=created["id"]).status, "PENDING")
        Resolution.objects.filter(id=created["id"]).update(vote_deadline=timezone.now() - timedelta(minutes=1))
        call_command("run_due_jobs")
        done = self.api("get", f"/resolutions/{created['id']}", token=members[0][1]).data
        self.assertEqual(done["status"], "APPROVED")
        self.assertEqual((done["result"]["agree"], done["result"]["denominator"]), (3, 5))
        public = self.api("get", "/resolutions", {"scope": "public"}, token=members[0][1]).data
        self.assertIn(created["id"], [r["id"] for r in public["results"]])


class RegistryTemplateJourneyTests(ApiTestBase):
    def test_tc_e2e_317_us_175_template_download_preflight_then_import_matches(self):
        """TC-E2E-317 / US-175（AC-175-01/02）：管理员下载模板 → 预检（6 行/4 新增/不写入）→ 正式导入 → 结果与预检一致，清册恰多 4 个专有部分。"""
        from apps.registry.models import RegistryUnit

        _, admin_token = self.make_admin()
        resp = self.client_for(admin_token).get("/api/v1/admin/registry/import/template", {"file_type": "xlsx"})
        raw = b"".join(resp.streaming_content) if resp.streaming else resp.content
        mk = lambda: SimpleUploadedFile("t.xlsx", raw, content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
        pre = self.assert_ok(self.upload("/admin/registry/import?dry_run=1", {"file": mk()}, token=admin_token)).data
        self.assertEqual(RegistryUnit.objects.count(), 0)
        real = self.assert_ok(self.upload("/admin/registry/import", {"file": mk()}, token=admin_token)).data
        for key in ("rows_total", "failed", "imported"):
            self.assertEqual(pre[key], real[key], key)
        self.assertEqual((real["rows_total"], real["failed"], real["imported"]), (6, 0, 4))
        self.assertEqual(RegistryUnit.objects.count(), 4)
        self.assertEqual(set(RegistryUnit.objects.values_list("specific_part", flat=True)),
                         {"1栋1单元3层301号", "车库A-088", "1栋负1层924号", "10栋1层1号"})


class PagingAndRegressionJourneyTests(ApiTestBase):
    def test_tc_e2e_342_us_161_resolution_list_paging_journey(self):
        """TC-E2E-342 / US-161（AC-161-01、04）：公开决议 45 条 → 翻 3 页（20 / 20 / 5），合计 45 且无重复、每页都带总数；
        删到 15 条后只有 1 页；"加载更多"式连续翻页（小程序语义：page 递增直到 count）得到同一结果。"""
        chair, _, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        _, token = self.make_user()
        for i in range(45):
            Resolution.objects.create(initiator=chair, title=f"e2e_决议{i:02d}", content="c", status="APPROVED",
                                      approval_mode="DESIGNATED")
        seen, sizes = [], []
        for page in (1, 2, 3):
            data = self.assert_ok(self.api("get", "/resolutions", {"scope": "public", "page": page, "page_size": 20},
                                           token=token)).data
            self.assertEqual(data["count"], 45)
            sizes.append(len(data["results"]))
            seen += [r["id"] for r in data["results"]]
        self.assertEqual((sizes, len(set(seen))), ([20, 20, 5], 45))
        Resolution.objects.filter(title__gte="e2e_决议15").delete()
        data = self.assert_ok(self.api("get", "/resolutions", {"scope": "public"}, token=token)).data
        self.assertEqual((data["count"], len(data["results"])), (15, 15))

    def test_tc_e2e_343_us_178_existing_user_flows_unchanged_for_registered_user(self):
        """TC-E2E-343 / US-178（AC-178-03 的本地对应）：注册用户依次登录、查看决议列表、"我的房屋"、个人中心 → 全部 200，
        既有字段（token/user/is_new；count/results；is_guest/units/committee/labels；account_no/phone/nickname 等）齐全且含义未变。"""
        from django.contrib.auth.hashers import make_password

        user, _ = self.make_user(nickname="e2e_回归")
        user.password = make_password("Passw0rd123")
        user.save()
        login = self.assert_ok(self.api("post", "/auth/login/password", {"identifier": user.phone, "password": "Passw0rd123"}))
        self.assertTrue({"token", "user", "is_new"} <= set(login.data))
        self.assertEqual((login.data["user"]["account_no"], login.data["is_new"]), (user.account_no, False))
        token = login.data["token"]
        listing = self.assert_ok(self.api("get", "/resolutions", {"scope": "public"}, token=token)).data
        self.assertTrue({"count", "page", "page_size", "results"} <= set(listing))
        me = self.assert_ok(self.api("get", "/me", token=token)).data
        self.assertTrue({"is_guest", "units", "committee", "labels"} <= set(me["identities"]))
        self.assertEqual((me["identities"]["is_guest"], me["identities"]["labels"], me["profile"]["nickname"]),
                         (True, ["游客"], "e2e_回归"))
        self.assertEqual(self.assert_ok(self.api("get", "/me/housing", token=token)).data["units"], [])
        prof = self.assert_ok(self.api("get", "/me/profile", token=token)).data
        self.assertEqual((prof["account_no"], prof["nickname"], prof["phone"]), (user.account_no, "e2e_回归", "139****" + user.phone[-4:]))
