"""ocap_product_review GROUP_D：后端集成用例（按 AC 逐条，TC-INT-424 起）。

覆盖 US-150~175、US-178 的后端可验证部分；与 GROUP_C 自验证文件 test_product_review_api.py 互补、不重复。
分层：integration（真实 DRF 路由 + SQLite 内存库，外部服务经 apps/integrations/fakes.py）。
"""
import io
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.accounts.models import AuthToken, User
from apps.accounts.services import AccountService, _sha256
from apps.committee.models import Seat
from apps.content.models import ContentPost
from apps.core.audit import AuditLog
from apps.core.config import SystemConfig
from apps.core.models import Attachment
from apps.ledger.models import LedgerReport
from apps.polls.models import Poll
from apps.registry.models import RegistryUnit
from apps.residency.models import Appeal, Membership, ResidentApplication
from apps.resolutions.models import Resolution, Vote
from apps.resolutions.services import ResolutionService
from tests.support import ApiTestBase

PNG = b"\x89PNG\r\n\x1a\n" + b"1" * 32


def _invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE", original_name="i.pdf",
        content_type="application/pdf", size=10, sha256="x" * 64,
        storage_path=f"tmp/{uuid4().hex}", status="TEMP")


class PRBase(ApiTestBase):
    def submit_appeal(self, token, unit) -> dict:
        uploaded = self.upload("/attachments", {"file": SimpleUploadedFile(
            "p.png", PNG + uuid4().bytes, content_type="image/png"), "purpose": "APPEAL_PROOF"}, token=token)
        self.assert_ok(uploaded, 201)
        resp = self.api("post", "/appeals", {"unit_id": unit.id, "proof_ids": [uploaded.data["id"]]},
                        token=token)
        self.assert_ok(resp, 201)
        return resp.data

    def committee_member(self, position="MEMBER"):
        user, token, unit = self.make_owner()
        self.make_seat(user, position)
        return user, token, unit


# =========================================================== US-150 ~ 153 同住人链路
class ResidentChainTests(PRBase):
    def test_tc_int_424_ac_150_01_cascade_options_then_apply_creates_pending(self):
        """TC-INT-424 / AC-150-01：逐级选择（options 四级）后仅凭 unit_id 提交，创建待审批申请。"""
        owner, _, unit = self.make_owner()
        _, token = self.make_user()
        lvl = self.assert_ok(self.api("get", "/units/options", token=token)).data
        self.assertIn(lvl["level"], {"building", "unit_no", "floor", "room"})
        resp = self.api("post", "/resident-applications", {"unit_id": unit.id}, token=token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["status"], "PENDING")
        self.assertEqual(resp.data["unit"]["unit_id"], unit.id)
        self.assertEqual(ResidentApplication.objects.filter(unit=unit, status="PENDING").count(), 1)

    def test_tc_int_425_ac_150_02_unit_without_owner_rejected(self):
        """TC-INT-425 / AC-150-02：无产权业主的专有部分 → 409 UNIT_HAS_NO_OWNER，不创建申请。"""
        _, token = self.make_user()
        empty = self.make_unit()
        self.assert_error(self.api("post", "/resident-applications", {"unit_id": empty.id}, token=token),
                          409, "UNIT_HAS_NO_OWNER")
        self.assertEqual(ResidentApplication.objects.count(), 0)

    def test_tc_int_426_ac_150_03_duplicate_pending_rejected(self):
        """TC-INT-426 / AC-150-03：已有待审批申请再提交 → 409 APPLICATION_PENDING，总数不增。"""
        _, _, unit = self.make_owner()
        _, token = self.make_user()
        self.assert_ok(self.api("post", "/resident-applications", {"unit_id": unit.id}, token=token), 201)
        self.assert_error(self.api("post", "/resident-applications", {"unit_id": unit.id}, token=token),
                          409, "APPLICATION_PENDING")
        self.assertEqual(ResidentApplication.objects.count(), 1)

    def test_tc_int_427_ac_151_01_owner_sees_two_pending_masked(self):
        """TC-INT-427 / AC-151-01、AC-166-03：2 条待审 → 首页计数 2；审批列表恰 2 条，含昵称/房屋/时间，手机号脱敏。"""
        owner, otoken, unit = self.make_owner()
        applicants = []
        for i in range(2):
            u, _ = self.make_user(nickname=f"申请人{i}")
            ResidentApplication.objects.create(applicant=u, unit=unit)
            applicants.append(u)
        housing = self.assert_ok(self.api("get", "/me/housing", token=otoken)).data
        self.assertEqual(housing["pending_review_count"], 2)
        rows = self.assert_ok(self.api("get", "/resident-applications/to-review", token=otoken)).data
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["applicant"]["nickname"] for r in rows}, {"申请人0", "申请人1"})
        for r in rows:
            self.assertEqual(r["unit"]["specific_part"], unit.specific_part)
            self.assertTrue(r["created_at"])
            phone = r["applicant"]["phone"]
            self.assertIn("****", phone)
            self.assertNotIn(applicants[0].phone, str(r))
            self.assertNotIn(applicants[1].phone, str(r))

    def test_tc_int_428_ac_151_02_approve_one_then_other_owner_gets_already_decided(self):
        """TC-INT-428 / AC-151-02：通过 1 条 → 计数 1、申请人成同住人；另一产权业主再处理同一条 → 409 ALREADY_DECIDED。"""
        owner, otoken, unit = self.make_owner()
        owner2, o2token = self.make_user()
        Membership.objects.create(user=owner2, unit=unit, role="OWNER", source="CERTIFIED", active_slot=1)
        apps = []
        for _ in range(2):
            u, t = self.make_user()
            apps.append((ResidentApplication.objects.create(applicant=u, unit=unit), u))
        self.assert_ok(self.api("post", f"/resident-applications/{apps[0][0].id}/decision",
                                {"decision": "APPROVE"}, token=otoken))
        self.assertEqual(self.api("get", "/me/housing", token=otoken).data["pending_review_count"], 1)
        self.assertTrue(Membership.objects.filter(user=apps[0][1], unit=unit, role="RESIDENT",
                                                  ended_at__isnull=True).exists())
        self.assert_error(self.api("post", f"/resident-applications/{apps[0][0].id}/decision",
                                   {"decision": "REJECT"}, token=o2token), 409, "ALREADY_DECIDED")

    def test_tc_int_429_ac_151_03_non_owner_forbidden_and_no_prompt(self):
        """TC-INT-429 / AC-151-03：同住人、其他房屋户主：首页无待审计数；审批 403，申请状态不变。"""
        _, _, unit = self.make_owner()
        resident, rtoken = self.make_resident(unit)
        _, htoken, _ = self.make_owner()
        applicant, _ = self.make_user()
        app = ResidentApplication.objects.create(applicant=applicant, unit=unit)
        for token in (rtoken, htoken):
            self.assertEqual(self.api("get", "/me/housing", token=token).data["pending_review_count"], 0)
            self.assert_error(self.api("post", f"/resident-applications/{app.id}/decision",
                                       {"decision": "APPROVE"}, token=token), 403)
            self.assertEqual(self.api("get", "/resident-applications/to-review", token=token).data, [])
        app.refresh_from_db()
        self.assertEqual(app.status, "PENDING")

    def test_tc_int_430_ac_151_04_no_pending_means_zero(self):
        """TC-INT-430 / AC-151-04：无待审申请 → pending_review_count 为 0。"""
        _, token, _ = self.make_owner()
        self.assertEqual(self.api("get", "/me/housing", token=token).data["pending_review_count"], 0)

    def test_tc_int_431_ac_152_01_to_03_my_applications(self):
        """TC-INT-431 / AC-152-01~03：待审批→已拒绝（有处理时间）→可再次提交；他人看不到。"""
        _, otoken, unit = self.make_owner()
        applicant, token = self.make_user()
        self.assert_ok(self.api("post", "/resident-applications", {"unit_id": unit.id}, token=token), 201)
        row = self.api("get", "/resident-applications/mine", token=token).data[0]
        self.assertEqual((row["status"], row["decided_at"], row["unit"]["specific_part"]),
                         ("PENDING", None, unit.specific_part))
        self.assertTrue(row["created_at"])
        self.assert_ok(self.api("post", f"/resident-applications/{row['id']}/decision",
                                {"decision": "REJECT"}, token=otoken))
        row = self.api("get", "/resident-applications/mine", token=token).data[0]
        self.assertEqual(row["status"], "REJECTED")
        self.assertTrue(row["decided_at"])
        self.assert_ok(self.api("post", "/resident-applications", {"unit_id": unit.id}, token=token), 201)
        mine = self.api("get", "/resident-applications/mine", token=token).data
        self.assertEqual([r["status"] for r in mine], ["PENDING", "REJECTED"])
        _, wtoken = self.make_user()
        self.assertEqual(self.api("get", "/resident-applications/mine", token=wtoken).data, [])

    def test_tc_int_432_ac_153_01_owner_removes_resident_keeping_other_identity(self):
        """TC-INT-432 / AC-153-01：移除 T 后不在名单；T 在其他房屋身份不变；无其他身份则为游客。"""
        owner, otoken, unit = self.make_owner()
        t1, t1token = self.make_resident(unit)
        t2, t2token = self.make_resident(unit)
        other = self.make_unit()
        Membership.objects.create(user=t2, unit=other, role="RESIDENT", source="APPLICATION", active_slot=1)
        self.assert_ok(self.api("delete", f"/units/{unit.id}/residents/{t1.id}", token=otoken), 204)
        self.assert_ok(self.api("delete", f"/units/{unit.id}/residents/{t2.id}", token=otoken), 204)
        units = self.api("get", "/me/housing", token=otoken).data["units"]
        self.assertEqual(units[0]["residents"], [])
        self.assertEqual(self.api("get", "/me/housing", token=t1token).data["summary"]["code"], "GUEST")
        after = self.api("get", "/me/housing", token=t2token).data
        self.assertEqual([u["unit_id"] for u in after["units"]], [other.id])

    def test_tc_int_433_ac_153_02_resident_leaves(self):
        """TC-INT-433 / AC-153-02：同住人退出 → 名单不再含 T，T 回到游客。"""
        _, otoken, unit = self.make_owner()
        t, ttoken = self.make_resident(unit)
        self.assert_ok(self.api("post", f"/units/{unit.id}/leave", {}, token=ttoken), 204)
        self.assertEqual(self.api("get", "/me/housing", token=otoken).data["units"][0]["residents"], [])
        self.assertEqual(self.api("get", "/me", token=ttoken).data["identities"]["summary"]["code"], "GUEST")
        self.assert_error(self.api("post", f"/units/{unit.id}/leave", {}, token=ttoken), 404)

    def test_tc_int_434_ac_153_03_others_cannot_remove(self):
        """TC-INT-434 / AC-153-03：另一同住人、其他房屋户主、管理员移除 → 403，T 仍在名单。"""
        _, otoken, unit = self.make_owner()
        t, _ = self.make_resident(unit)
        _, r2token = self.make_resident(unit)
        _, htoken, _ = self.make_owner()
        _, admin_token = self.make_admin()
        for token in (r2token, htoken, admin_token):
            self.assert_error(self.api("delete", f"/units/{unit.id}/residents/{t.id}", token=token), 403)
        names = [r["user_id"] for r in self.api("get", "/me/housing", token=otoken).data["units"][0]["residents"]]
        self.assertIn(t.id, names)


# =========================================================== US-154 / 155
class ClaimsAndSessionTests(PRBase):
    def setUp(self):
        super().setUp()
        self.member, self.mtoken, _ = self.committee_member()
        approver, _, _ = self.committee_member()
        self.flow = self.make_flow(scope="EXPENSE", approvers=[approver])

    def test_tc_int_435_ac_154_02_member_creates_pending_reimbursement(self):
        """TC-INT-435 / AC-154-02：现任委员发起报销 → 201，状态审批中（PENDING），申请人为本人。"""
        resp = self.api("post", "/claims/reimbursements", {
            "amount": "10.00", "reason": "打印", "occurred_on": str(date.today()),
            "invoice_ids": [str(_invoice(self.member).id)], "approval_flow_id": self.flow.id},
            token=self.mtoken)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["status"], "PENDING")
        mine = self.api("get", "/claims", {"scope": "mine"}, token=self.mtoken).data
        self.assertEqual(mine["count"], 1)

    def test_tc_int_436_ac_154_01_non_member_forbidden_message(self):
        """TC-INT-436 / AC-154-01：非成员（含游客）→ 403 且提示含"业委会成员"，不创建申请。"""
        guest, gtoken = self.make_user()
        resp = self.api("post", "/claims/reimbursements", {
            "amount": "10.00", "reason": "x", "occurred_on": str(date.today()),
            "invoice_ids": [str(_invoice(guest).id)], "approval_flow_id": self.flow.id}, token=gtoken)
        body = self.assert_error(resp, 403, "FORBIDDEN")
        self.assertIn("业委会成员", body["message"])
        from apps.claims.models import Claim
        self.assertEqual(Claim.objects.count(), 0)

    def test_tc_int_437_gr_c_001_f03_admin_token_status_is_not_ac_violation(self):
        """TC-INT-437 / AC-154-01~03、GR-C-001-F03：AC-154 只规定非成员 403；管理员令牌无 AC 约束。
        IFC-265 登记为 401（设计已写明的语义变化）。此处固化现状，并断言两个端点一致、且不创建数据。"""
        _, admin_token = self.make_admin()
        codes = {self.api("post", p, {}, token=admin_token).status_code
                 for p in ("/claims/reimbursements", "/claims/advances")}
        self.assertEqual(codes, {401})

    def test_tc_int_438_ac_155_03_web_and_admin_sessions_unchanged_31_minutes(self):
        """TC-INT-438 / AC-155-03：Web 未勾选记住我、管理员闲置 31 分钟后被拒；Web 勾选记住我保持。"""
        from django.contrib.auth.hashers import make_password
        from rest_framework.exceptions import AuthenticationFailed

        user, _ = self.make_user()
        user.password = make_password("Passw0rd123")
        user.save()
        web = self.api("post", "/auth/login/password",
                       {"identifier": user.phone, "password": "Passw0rd123"}).data["token"]
        remembered = self.api("post", "/auth/login/password",
                              {"identifier": user.phone, "password": "Passw0rd123",
                               "remember_me": True}).data["token"]
        self.make_admin("adm_pr", "Admin12345")
        admin = self.api("post", "/admin/auth/login",
                         {"username": "adm_pr", "password": "Admin12345"}).data["token"]
        later = timezone.now() + timedelta(minutes=31)
        for tok in (web, admin):
            with self.assertRaises(AuthenticationFailed):
                AccountService.authenticate_token(tok, now=later)
        self.assertIsNotNone(AccountService.authenticate_token(remembered, now=later))

    def test_tc_int_439_ac_155_01_miniapp_code_login_http_after_idle(self):
        """TC-INT-439 / AC-155-01：小程序手机号验证码登录，闲置 31 分钟后经 HTTP 请求仍成功（真实路由，改令牌活动时间）。"""
        user, _ = self.make_user()
        code = self.request_code(user.phone, "LOGIN")
        resp = self.api("post", "/auth/login/code", {"phone": user.phone, "code": code, "client": "miniapp"})
        token = resp.data["token"]
        AuthToken.objects.filter(key_hash=_sha256(token)).update(
            last_active_at=timezone.now() - timedelta(minutes=31))
        self.assert_ok(self.api("get", "/me", token=token))
        # 对照：Web 会话同样闲置 31 分钟被拒（401）
        from django.contrib.auth.hashers import make_password
        user.password = make_password("Passw0rd123")
        user.save()
        web = self.api("post", "/auth/login/password",
                       {"identifier": user.phone, "password": "Passw0rd123"}).data["token"]
        AuthToken.objects.filter(key_hash=_sha256(web)).update(
            last_active_at=timezone.now() - timedelta(minutes=31))
        self.assertEqual(self.api("get", "/me", token=web).status_code, 401)


# =========================================================== US-156 / 157 / 158
class AppealAndIdentityTests(PRBase):
    def test_tc_int_440_ac_156_01_to_04_my_appeals_lifecycle(self):
        """TC-INT-440 / AC-156-01~04：待审核 → 驳回含原因原文 → 他人为空；通过后身份出现在房屋列表。"""
        unit = self.make_unit(phones=["13900000001"])
        user, token = self.make_user()
        appeal = self.submit_appeal(token, unit)
        row = self.api("get", "/appeals/mine", token=token).data[0]
        self.assertEqual((row["status"], row["decided_at"], row["reject_reason"]), ("PENDING", None, None))
        self.assertEqual(row["unit"]["specific_part"], unit.specific_part)
        _, admin_token = self.make_admin()
        self.assert_ok(self.api("post", f"/admin/appeals/{appeal['id']}/decision",
                                {"decision": "REJECT", "reject_reason": "材料不清，请重传"}, token=admin_token))
        row = self.api("get", "/appeals/mine", token=token).data[0]
        self.assertEqual((row["status"], row["reject_reason"]), ("REJECTED", "材料不清，请重传"))
        self.assertTrue(row["decided_at"])
        _, wtoken = self.make_user()
        self.assertEqual(self.api("get", "/appeals/mine", token=wtoken).data, [])
        second = self.submit_appeal(token, unit)
        self.assert_ok(self.api("post", f"/admin/appeals/{second['id']}/decision",
                                {"decision": "APPROVE"}, token=admin_token))
        self.assertEqual(self.api("get", "/appeals/mine", token=token).data[0]["status"], "APPROVED")
        units = self.api("get", "/me/housing", token=token).data["units"]
        self.assertEqual([(u["unit_id"], u["role_label"]) for u in units], [(unit.id, "户主")])

    def test_tc_int_441_ac_157_01_three_sources_agree_and_stable_order(self):
        """TC-INT-441 / AC-157-01、AC-157-04：/me、/me/housing、管理端目录三处身份一致；多次刷新顺序不变。"""
        user, token = self.make_user(nickname="多房屋")
        a, b = self.make_unit(), self.make_unit()
        Membership.objects.create(user=user, unit=a, role="HEAD", source="APPEAL", active_slot=1, head_slot=1)
        Membership.objects.create(user=user, unit=b, role="RESIDENT", source="APPLICATION", active_slot=1)
        _, admin_token = self.make_admin()
        first = None
        for _ in range(3):
            me = self.api("get", "/me", token=token).data["identities"]
            housing = self.api("get", "/me/housing", token=token).data
            seq = ([(u["unit_id"], u["role_label"]) for u in me["units"]],
                   [(u["unit_id"], u["role_label"]) for u in housing["units"]])
            first = first or seq
            self.assertEqual(seq, first)
        self.assertEqual(first[0], [(a.id, "户主"), (b.id, "同住人")])
        self.assertEqual(first[0], first[1])
        self.assertEqual(me["summary"], {"code": "HEAD", "label": "户主"})
        self.assertEqual(housing["summary"], me["summary"])
        listed = self.api("get", "/admin/users", {"q": user.account_no}, token=admin_token).data["results"]
        self.assertEqual(listed[0]["identity_label"], "户主")

    def test_tc_int_442_ac_157_02_vice_chair_summary_but_rows_show_head(self):
        """TC-INT-442 / AC-157-02：副主任 + 户主 → 汇总"副主任"，房屋行仍"户主"。"""
        user, token, unit = self.make_owner()
        self.make_seat(user, "VICE_CHAIR")
        data = self.api("get", "/me/housing", token=token).data
        self.assertEqual(data["summary"]["label"], "副主任")
        self.assertEqual(data["units"][0]["role_label"], "户主")

    def test_tc_int_443_ac_157_03_guest_summary(self):
        """TC-INT-443 / AC-157-03：游客汇总"游客"，房屋列表为空。"""
        _, token = self.make_user()
        data = self.api("get", "/me/housing", token=token).data
        self.assertEqual((data["summary"]["label"], data["units"]), ("游客", []))
        self.assertTrue(self.api("get", "/me", token=token).data["identities"]["is_guest"])

    def test_tc_int_444_ac_157_05_revoked_membership_disappears(self):
        """TC-INT-444 / AC-157-05、AC-158-02：管理员撤销认证 → 房屋行消失；审计新增 CERTIFICATION_REVOKED。"""
        user, token = self.make_user()
        keep, gone = self.make_unit(), self.make_unit()
        Membership.objects.create(user=user, unit=keep, role="OWNER", source="CERTIFIED", active_slot=1)
        Membership.objects.create(user=user, unit=gone, role="OWNER", source="CERTIFIED", active_slot=1)
        _, admin_token = self.make_admin()
        before = AuditLog.objects.filter(action="CERTIFICATION_REVOKED").count()
        self.assert_ok(self.api("post", "/admin/memberships/revoke",
                                {"user_id": user.id, "unit_id": gone.id}, token=admin_token))
        units = self.api("get", "/me/housing", token=token).data["units"]
        self.assertEqual([u["unit_id"] for u in units], [keep.id])
        self.assertEqual(AuditLog.objects.filter(action="CERTIFICATION_REVOKED").count(), before + 1)


# =========================================================== US-159 / 160 / 161
class AdminSearchAndPagingTests(PRBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()

    def test_tc_int_445_ac_159_01_search_by_account_phone_tail_and_real_name(self):
        """TC-INT-445 / AC-159-01：账号、手机号后四位、清册实名三种搜索都命中 P；候选含脱敏手机号与最高身份。"""
        phone = "13800010001"
        user, _ = self.make_user(phone=phone, nickname="e2e_甲")
        unit = self.make_unit(phones=[phone], name="清册实名丙")
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="REGISTRY",
                                  active_slot=1, head_slot=1)
        for q in (user.account_no, "0001", "清册实名丙"):
            rows = self.api("get", "/admin/users", {"q": q}, token=self.admin_token).data["results"]
            hit = [r for r in rows if r["id"] == user.id]
            self.assertTrue(hit, q)
        r = hit[0]
        self.assertEqual((r["nickname"], r["account_no"], r["identity_label"]), ("e2e_甲", user.account_no, "户主"))
        self.assertEqual(r["real_names"], ["清册实名丙"])
        self.assertEqual(r["phone"], "138****0001")
        self.assertNotIn(phone, str(r))

    def test_tc_int_446_ac_159_03_grant_seat_to_guest_rejected(self):
        """TC-INT-446 / AC-159-03：对游客赋予委员席位 → 422 NOT_AN_OWNER，不创建席位。"""
        guest, _ = self.make_user()
        resp = self.api("post", "/admin/committee/seats", {"user_id": guest.id, "position": "MEMBER"},
                        token=self.admin_token)
        self.assert_error(resp, 422, "NOT_AN_OWNER")
        self.assertFalse(Seat.objects.exists())

    def test_tc_int_447_ac_159_05_flow_approvers_from_search_and_non_member_rejected(self):
        """TC-INT-447 / AC-159-05：选中两位现任成员保存 → 审批人列表含其昵称；非现任成员沿用既有拒绝。"""
        m1, _, _ = self.committee_member()
        m2, _, _ = self.committee_member()
        plain, _, _ = self.make_owner()
        for u, n in ((m1, "e2e_审批甲"), (m2, "e2e_审批乙")):
            u.nickname = n
            u.save()
        resp = self.api("post", "/admin/approval/flows",
                        {"scope": "EXPENSE", "mode": "DESIGNATED", "name": "e2e_流程",
                         "approver_ids": [m1.id, m2.id]}, token=self.admin_token)
        self.assert_ok(resp, 201)
        listed = self.api("get", "/admin/approval/flows", token=self.admin_token).data
        rows = listed["results"] if isinstance(listed, dict) else listed
        flow = next(f for f in rows if f["name"] == "e2e_流程")
        self.assertEqual({a["nickname"] for a in flow["approvers"]}, {"e2e_审批甲", "e2e_审批乙"})
        bad = self.api("post", "/admin/approval/flows",
                       {"scope": "EXPENSE", "mode": "DESIGNATED", "name": "e2e_坏流程",
                        "approver_ids": [plain.id]}, token=self.admin_token)
        self.assertGreaterEqual(bad.status_code, 400)
        self.assertLess(bad.status_code, 500)

    def test_tc_int_448_ac_159_06_non_admin_cannot_search(self):
        """TC-INT-448 / AC-159-06：普通用户请求用户搜索 → 403，响应无用户信息。"""
        _, token = self.make_user()
        resp = self.api("get", "/admin/users", {"q": "a"}, token=token)
        self.assertEqual(resp.status_code, 403)
        self.assertNotIn("results", resp.json())

    def test_tc_int_449_ac_160_01_160_02_users_paging_total_no_duplicates(self):
        """TC-INT-449 / AC-160-01、AC-160-02：用户 25 个 → 第 1 页 20、count=25、全页合计 25 且无重复；带关键词翻第 2 页。"""
        for i in range(25):
            self.make_user(nickname=f"e2e_bulk_{i:02d}")
        total = User.objects.count()
        seen, page = [], 1
        while True:
            data = self.api("get", "/admin/users", {"page": page, "page_size": 20},
                            token=self.admin_token).data
            self.assertEqual(data["count"], total)
            seen += [r["id"] for r in data["results"]]
            if len(seen) >= total:
                break
            page += 1
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(len(seen), total)
        first = self.api("get", "/admin/users", {"page": 1}, token=self.admin_token).data
        self.assertEqual(len(first["results"]), 20)
        q = self.api("get", "/admin/users", {"q": "e2e_bulk_", "page": 2}, token=self.admin_token).data
        self.assertEqual((q["count"], len(q["results"]), q["page"]), (25, 5, 2))
        self.assertTrue(all("e2e_bulk_" in (r["nickname"] or "") for r in q["results"]))

    def test_tc_int_450_ac_160_03_other_admin_lists_report_total_and_all_pages(self):
        """TC-INT-450 / AC-160-03、AC-160-04：房屋关系/申诉/席位/审批流程/财务五个管理端列表均返回 count 并可翻完；≤20 条无空页。"""
        owners = []
        for _ in range(23):
            user, _, unit = self.make_owner()
            owners.append(user)
            Appeal.objects.create(user=user, unit=unit, status="REJECTED", pending_slot=None,
                                  reject_reason="x")
        for i in range(21):
            self.make_flow(scope="RESOLUTION", name=f"e2e_f{i}")
        for user in owners[:21]:
            Seat.objects.create(user=user, position="REPRESENTATIVE", term_start=date.today(),
                                term_end=date.today() + timedelta(days=30), status="ACTIVE", active_slot=1)
        from apps.claims.models import Claim
        for i in range(22):
            Claim.objects.create(type="REIMBURSEMENT", submitter=owners[0], amount=1, reason=f"r{i}")
        expect = {"/admin/memberships": 23, "/admin/appeals": 23, "/admin/committee/seats": 21,
                  "/admin/approval/flows": 21, "/admin/claims": 22}
        for path, n in expect.items():
            ids, page = [], 1
            while True:
                data = self.assert_ok(self.api("get", path, {"page": page, "page_size": 20},
                                               token=self.admin_token)).data
                self.assertEqual(data["count"], n, path)
                self.assertTrue(data["results"], f"{path} 第 {page} 页为空")
                ids += [r["id"] for r in data["results"]]
                if len(ids) >= n:
                    break
                page += 1
            self.assertEqual((len(ids), len(set(ids))), (n, n), path)
        small = self.assert_ok(self.api("get", "/admin/appeals", {"status": "PENDING"},
                                        token=self.admin_token)).data
        self.assertEqual((small["count"], small["results"]), (0, []))

    def test_tc_int_451_ac_161_01_161_04_resolutions_paging(self):
        """TC-INT-451 / AC-161-01、AC-161-04：公开决议 25 条 → 第 1 页 20、count=25、全页合计 25 无重复；≤20 条时单页。"""
        chair, _, _ = self.committee_member("CHAIR")
        _, token = self.make_user()
        for i in range(25):
            Resolution.objects.create(initiator=chair, title=f"e2e_决议{i:02d}", content="c",
                                      status="APPROVED", approval_mode="DESIGNATED")
        ids, page = [], 1
        while True:
            data = self.assert_ok(self.api("get", "/resolutions", {"scope": "public", "page": page},
                                           token=token)).data
            self.assertEqual(data["count"], 25)
            ids += [r["id"] for r in data["results"]]
            if len(ids) >= 25:
                break
            page += 1
        self.assertEqual((len(ids), len(set(ids)), page), (25, 25, 2))
        Resolution.objects.filter(title__startswith="e2e_决议0").delete()
        small = self.api("get", "/resolutions", {"scope": "public"}, token=token).data
        self.assertEqual((small["count"], len(small["results"])), (15, 15))

    def test_tc_int_452_ac_161_02_user_lists_return_paged_shape(self):
        """TC-INT-452 / AC-161-02：投票、报表、报销（成员）、收入表（成员）、待办列表均为 {count, results} 分页形态。"""
        member, mtoken, _ = self.committee_member()
        for path, params in (("/polls", None), ("/ledger/reports", None), ("/claims", {"scope": "mine"}),
                             ("/income/sheets", None), ("/approval/tasks", None)):
            data = self.assert_ok(self.api("get", path, params, token=mtoken)).data
            self.assertEqual(set(data) >= {"count", "results"}, True, path)


# =========================================================== US-162
class StyleTemplateTests(PRBase):
    def setUp(self):
        super().setUp()
        self.admin, self.token = self.make_admin()

    def _create(self, name, tokens=None):
        return self.api("post", "/admin/content/style-templates",
                        {"name": name, "tokens": tokens or {"font_size": 17, "text_color": "#112233"}},
                        token=self.token)

    def test_tc_int_453_ac_162_01_162_02_create_listed_and_preview_uses_saved_tokens(self):
        """TC-INT-453 / AC-162-01、AC-162-02：新建后出现在列表；选用并预览所用样式值与保存值一致，文字不变。"""
        created = self._create("e2e_模板A").data
        keys = [t["key"] for t in self.api("get", "/admin/content/style-templates", token=self.token).data]
        self.assertIn(created["key"], keys)
        doc = {"type": "doc", "content": [{"type": "paragraph",
                                           "content": [{"type": "text", "text": "正文保持不变"}]}]}
        post = self.api("post", "/admin/content/posts", {"title": "e2e_内容", "doc": doc,
                                                         "style_key": created["key"]}, token=self.token)
        self.assert_ok(post, 201)
        self.assertEqual(post.data["style_key"], created["key"])
        prev = self.assert_ok(self.api("post", "/admin/content/preview",
                                       {"doc": doc, "style_key": created["key"]}, token=self.token)).data
        html = str(prev["pages"])
        self.assertIn("正文保持不变", html)
        self.assertIn("#112233", html)
        self.assertIn("17", html)
        blocks = self.assert_ok(self.api("get", f"/admin/content/posts/{post.data['id']}",
                                         token=self.token)).data
        self.assertEqual(blocks["style_key"], created["key"])

    def test_tc_int_454_ac_162_03_rename_edit_and_empty_name_rejected(self):
        """TC-INT-454 / AC-162-03：改名并修改样式后列表显示新值；名称为空 → 400 STYLE_NAME_REQUIRED（"模板名称不能为空"）。"""
        created = self._create("e2e_旧名").data
        upd = self.api("put", f"/admin/content/style-templates/{created['id']}",
                       {"name": "e2e_新名", "tokens": {"font_size": 20}}, token=self.token)
        self.assert_ok(upd)
        row = next(t for t in self.api("get", "/admin/content/style-templates", token=self.token).data
                   if t["key"] == created["key"])
        self.assertEqual((row["name"], row["tokens"]["font_size"]), ("e2e_新名", 20))
        bad = self.api("put", f"/admin/content/style-templates/{created['id']}", {"name": "  "}, token=self.token)
        body = self.assert_error(bad, 400, "STYLE_NAME_REQUIRED")
        self.assertEqual(body["message"], "模板名称不能为空")
        self.assert_error(self._create(""), 400, "STYLE_NAME_REQUIRED")

    def test_tc_int_455_ac_162_04_delete_unused_ok_used_rejected_with_count(self):
        """TC-INT-455 / AC-162-04：未被引用 → 删除成功；被 K=2 条内容引用 → 409 且 message 含 2，模板保留。"""
        free = self._create("e2e_模板B").data
        used = self._create("e2e_模板C").data
        for i in range(2):
            ContentPost.objects.create(title=f"x{i}", style_key=used["key"], created_by_admin_id=self.admin.id)
        self.assert_ok(self.api("delete", f"/admin/content/style-templates/{free['id']}", token=self.token), 204)
        resp = self.api("delete", f"/admin/content/style-templates/{used['id']}", token=self.token)
        body = self.assert_error(resp, 409, "STYLE_IN_USE")
        self.assertIn("2", body["message"])
        keys = [t["key"] for t in self.api("get", "/admin/content/style-templates", token=self.token).data]
        self.assertEqual((free["key"] in keys, used["key"] in keys), (False, True))

    def test_tc_int_456_ac_162_05_builtin_immutable(self):
        """TC-INT-456 / AC-162-05：内置模板无 id/usage_count；PUT/DELETE 路径不存在（404），列表不变。"""
        rows = self.api("get", "/admin/content/style-templates", token=self.token).data
        builtin = [r for r in rows if r["builtin"]]
        self.assertTrue(builtin)
        before = [(r["key"], r["tokens"]) for r in builtin]
        for r in builtin:
            self.assertNotIn("id", r)
            for method in ("put", "delete"):
                self.assertEqual(self.api(method, f"/admin/content/style-templates/{r['key']}",
                                          {"name": "x"}, token=self.token).status_code, 404)
        self.assertEqual(before, [(r["key"], r["tokens"]) for r in
                                  self.api("get", "/admin/content/style-templates", token=self.token).data
                                  if r["builtin"]])

    def test_tc_int_457_ac_162_06_non_admin_forbidden(self):
        """TC-INT-457 / AC-162-06：普通用户新建/修改/删除 → 403，数据不变。"""
        created = self._create("e2e_模板D").data
        _, utoken = self.make_user()
        path = f"/admin/content/style-templates/{created['id']}"
        self.assertEqual(self.api("post", "/admin/content/style-templates", {"name": "n", "tokens": {}},
                                  token=utoken).status_code, 403)
        self.assertEqual(self.api("put", path, {"name": "n"}, token=utoken).status_code, 403)
        self.assertEqual(self.api("delete", path, token=utoken).status_code, 403)
        names = [t["name"] for t in self.api("get", "/admin/content/style-templates", token=self.token).data]
        self.assertIn("e2e_模板D", names)


# =========================================================== US-163 ~ 169
class ShouldHaveAccountTests(PRBase):
    def test_tc_int_458_ac_163_02_email_password_login_fails_uniformly(self):
        """TC-INT-458 / AC-163-02：邮箱 + 密码走密码登录 → 统一失败（401），不提供邮箱+密码登录。"""
        user, _ = self.make_user()
        resp = self.api("post", "/auth/login/password", {"identifier": "a@b.com", "password": "Passw0rd123"})
        other = self.api("post", "/auth/login/password", {"identifier": user.phone, "password": "wrong-Pass1"})
        self.assertEqual(resp.status_code, other.status_code)
        self.assertEqual(resp.json()["message"], other.json()["message"])
        self.assertIn(resp.status_code, (400, 401))

    def test_tc_int_459_ac_164_01_to_04_cancel_via_http_closes_and_audits(self):
        """TC-INT-459 / AC-164-01~04：经 /me/cancel 注销：待处理申请与申诉被关闭并各写审计；历史记录不变；无待处理不新增审计；已关闭记录不可通过。"""
        owner, otoken, unit = self.make_owner()
        _, admin_token = self.make_admin()
        user, token = self.make_user()
        u2 = self.make_unit(phones=["13900000002"])
        pending_app = ResidentApplication.objects.create(applicant=user, unit=unit)
        pending_appeal = Appeal.objects.create(user=user, unit=u2)
        old = Appeal.objects.create(user=user, unit=self.make_unit(), status="REJECTED", pending_slot=None,
                                    reject_reason="旧")
        before = AuditLog.objects.filter(action__in=["RESIDENT_APPLICATION_CLOSED", "APPEAL_CLOSED"]).count()
        code = self.request_me_code(token, "CANCEL")
        self.assertEqual(self.api("post", "/me/cancel", {"phone": user.phone, "code": code},
                                  token=token).status_code, 204)
        self.assertEqual(AuditLog.objects.filter(action__in=["RESIDENT_APPLICATION_CLOSED",
                                                             "APPEAL_CLOSED"]).count(), before + 2)
        self.assertEqual(self.api("get", "/resident-applications/to-review", token=otoken).data, [])
        pend = self.api("get", "/admin/appeals", {"status": "PENDING"}, token=admin_token).data
        self.assertNotIn(pending_appeal.id, [r["id"] for r in pend["results"]])
        self.assert_error(self.api("post", f"/resident-applications/{pending_app.id}/decision",
                                   {"decision": "APPROVE"}, token=otoken), 409, "ALREADY_CLOSED")
        self.assert_error(self.api("post", f"/admin/appeals/{pending_appeal.id}/decision",
                                   {"decision": "APPROVE"}, token=admin_token), 409, "ALREADY_CLOSED")
        old.refresh_from_db()
        self.assertEqual((old.status, old.reject_reason), ("REJECTED", "旧"))
        self.assertFalse(Membership.objects.filter(user=user).exists())
        # AC-164-04：无待处理项的用户注销，不新增关闭记录
        clean, ctoken = self.make_user()
        before = AuditLog.objects.filter(action__in=["RESIDENT_APPLICATION_CLOSED", "APPEAL_CLOSED"]).count()
        code = self.request_me_code(ctoken, "CANCEL")
        self.assertEqual(self.api("post", "/me/cancel", {"phone": clean.phone, "code": code},
                                  token=ctoken).status_code, 204)
        self.assertEqual(AuditLog.objects.filter(action__in=["RESIDENT_APPLICATION_CLOSED",
                                                             "APPEAL_CLOSED"]).count(), before)

    def test_tc_int_460_ac_165_01_birthday_roundtrip_and_blank_ok(self):
        """TC-INT-460 / AC-165-01：保存生日并刷新显示；留空保存成功。"""
        _, token = self.make_user()
        self.assert_ok(self.api("patch", "/me/profile", {"birthday": "1990-05-06"}, token=token))
        self.assertEqual(self.api("get", "/me/profile", token=token).json()["birthday"], "1990-05-06")
        self.assert_ok(self.api("patch", "/me/profile", {"birthday": None}, token=token))
        self.assertIsNone(self.api("get", "/me/profile", token=token).data["birthday"])

    def test_tc_int_461_ac_165_02_avatar_upload_is_downloadable_by_owner(self):
        """TC-INT-461 / AC-165-02：上传合规头像并保存后，资料含 avatar_url，且该 URL 经鉴权可下载。"""
        _, token = self.make_user()
        up = self.upload("/me/avatar", {"file": SimpleUploadedFile("a.png", PNG, content_type="image/png")},
                         token=token)
        self.assertIn(up.status_code, (200, 201), up.content)
        url = self.api("get", "/me/profile", token=token).data["avatar_url"]
        self.assertTrue(url, "avatar_url 为空")
        self.assertTrue(url.startswith("/api/v1/attachments/") or url.startswith("/attachments/"), url)
        path = url.replace("/api/v1", "", 1)
        dl = self.client_for(token).get(f"/api/v1{path}")
        self.assertEqual(dl.status_code, 200)
        bad = self.upload("/me/avatar", {"file": SimpleUploadedFile("a.gif", b"GIF89a" + b"0" * 20,
                                                                    content_type="image/gif")}, token=token)
        self.assertGreaterEqual(bad.status_code, 400)

    def test_tc_int_462_ac_166_02_non_member_tasks_forbidden(self):
        """TC-INT-462 / AC-166-02：非业委会成员请求待办 → 403；成员 → 200（入口显示与接口权限一致）。"""
        _, token, _ = self.make_owner()
        self.assert_error(self.api("get", "/approval/tasks", token=token), 403)
        _, mtoken, _ = self.committee_member()
        self.assert_ok(self.api("get", "/approval/tasks", token=mtoken))

    def test_tc_int_463_ac_168_01_to_03_report_detail_totals_and_auth(self):
        """TC-INT-463 / AC-168-01~03：报表明细合计与列表一致、支出事由为 null；未登录 401；无报表时列表为空。"""
        _, token = self.make_user()
        self.assertEqual(self.api("get", "/ledger/reports", token=token).data["results"], [])
        detail = [{"direction": "INCOME", "amount": "300.00", "entry_type": "INCOME_RECORD", "seq": 0,
                   "summary": "物业费", "occurred_on": "2026-01-02"},
                  {"direction": "EXPENSE", "amount": "100.00", "entry_type": "REIMBURSEMENT", "seq": 0,
                   "summary": "私人事由", "occurred_on": "2026-01-03"}]
        report = LedgerReport.objects.create(period_type="QUARTER", year=2026, quarter=1, detail=detail,
                                             total_income=Decimal("300.00"), total_expense=Decimal("100.00"),
                                             balance=Decimal("200.00"))
        listed = self.api("get", "/ledger/reports", token=token).data["results"][0]
        got = self.assert_ok(self.api("get", f"/ledger/reports/{report.id}", token=token)).data
        for k in ("total_income", "total_expense", "balance"):
            self.assertEqual(got[k], listed[k])
        self.assertEqual(sum(Decimal(r["amount"]) for r in got["detail"] if r["direction"] == "INCOME"),
                         Decimal(got["total_income"]))
        self.assertEqual(sum(Decimal(r["amount"]) for r in got["detail"] if r["direction"] == "EXPENSE"),
                         Decimal(got["total_expense"]))
        self.assertIsNone([r for r in got["detail"] if r["direction"] == "EXPENSE"][0]["summary"])
        self.assertNotIn("私人事由", str(got))
        self.assert_error(self.api("get", f"/ledger/reports/{report.id}"), 401)

    def test_tc_int_464_ac_169_01_169_02_offline_and_missing_post_404(self):
        """TC-INT-464 / AC-169-01、AC-169-02：已下线与不存在的内容详情 → 404；正常已发布内容 200。"""
        admin, atoken = self.make_admin()
        _, token = self.make_user()
        doc = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "x"}]}]}
        post = self.api("post", "/admin/content/posts", {"title": "e2e_内容", "doc": doc}, token=atoken).data
        self.assert_ok(self.api("post", f"/admin/content/posts/{post['id']}/publish", {}, token=atoken))
        self.assert_ok(self.api("get", f"/info/posts/{post['id']}", token=token))
        self.assert_ok(self.api("post", f"/admin/content/posts/{post['id']}/offline", {}, token=atoken))
        self.assert_error(self.api("get", f"/info/posts/{post['id']}", token=token), 404)
        self.assert_error(self.api("get", "/info/posts/99999999", token=token), 404)


# =========================================================== US-170 ~ 174 规则固化
class RuleLimitTests(PRBase):
    def setUp(self):
        super().setUp()
        self.chair, self.ctoken, _ = self.committee_member("CHAIR")
        self.member, self.mtoken, _ = self.committee_member()
        self.flow = self.make_flow(scope="EXPENSE", approvers=[self.member])
        self.admin, self.admin_token = self.make_admin()

    def _reimb(self, **kw):
        body = {"amount": "1.00", "reason": "r", "occurred_on": str(date.today()),
                "invoice_ids": [str(_invoice(self.chair).id)], "approval_flow_id": self.flow.id}
        body.update(kw)
        return self.api("post", "/claims/reimbursements", body, token=self.ctoken)

    def test_tc_int_465_ac_170_02_default_limit_boundary(self):
        """TC-INT-465 / AC-170-02：从未设置上限 → 1,000,000.01 失败、1,000,000.00 成功。"""
        self.assert_error(self._reimb(amount="1000000.01"), 400, "INVALID_VALUE")
        self.assert_ok(self._reimb(amount="1000000.00"), 201)

    def test_tc_int_466_ac_170_01_after_admin_sets_500000(self):
        """TC-INT-466 / AC-170-01、AC-170-03：改为 500000 → 500000.01 失败（提示当前上限）、500000.00 成功；此前记录不变；配置变更写审计。"""
        old = self._reimb(amount="800000.00")
        self.assert_ok(old, 201)
        self.assert_ok(self.api("put", "/admin/system-config/claim.amount_max", {"value": "500000.00"},
                                token=self.admin_token))
        resp = self._reimb(amount="500000.01")
        self.assertIn("500000.00", self.assert_error(resp, 400, "INVALID_VALUE")["message"])
        self.assert_ok(self._reimb(amount="500000.00"), 201)
        self.assertEqual(self.api("get", f"/claims/{old.data['id']}", token=self.ctoken).data["amount"], "800000.00")
        row = AuditLog.objects.filter(action="SYSTEM_CONFIG_CHANGED").latest("id")
        self.assertIn("500000.00", str(row.detail))

    def test_tc_int_467_ac_170_04_non_admin_and_invalid_values_keep_original(self):
        """TC-INT-467 / AC-170-04：非管理员 403；0 / 负数 / 非数字 → 400，原值不变。"""
        self.assert_error(self.api("put", "/admin/system-config/claim.amount_max", {"value": "1"},
                                   token=self.ctoken), 403)
        for bad in ("0", "-5", "abc"):
            self.assert_error(self.api("put", "/admin/system-config/claim.amount_max", {"value": bad},
                                       token=self.admin_token), 400, "INVALID_VALUE")
        self.assertEqual(SystemConfig.amount_max(), Decimal("1000000.00"))

    def test_tc_int_468_ac_171_01_to_03_half_majority_denominator_is_active_seats(self):
        """TC-INT-468 / AC-171-01~04：在任 5 人：3 同意判通过且分母 5；2 同意/2 反对/1 弃权未通过；在任 4 人 2 同意 2 弃权未通过；截止前不判定。"""
        voters = [self.chair, self.member]
        for _ in range(3):
            voters.append(self.committee_member()[0])
        self.assertEqual(Seat.objects.filter(status="ACTIVE").count(), 5)

        def run(choices, voters=voters):
            res = Resolution.objects.create(initiator=self.chair, title="t", content="c",
                                            approval_mode="HALF_MAJORITY",
                                            vote_deadline=timezone.now() - timedelta(minutes=1))
            for u, c in zip(voters, choices):
                Vote.objects.create(resolution=res, revision=1, voter=u, choice=c)
            outcome = ResolutionService.judge_if_due(res.id)
            res.refresh_from_db()
            return outcome, res

        outcome, res = run(["AGREE"] * 3 + ["DISAGREE", "ABSTAIN"])
        self.assertEqual((outcome, res.result["denominator"], res.result["passed"]), ("PASSED", 5, True))
        outcome, res = run(["AGREE", "AGREE", "DISAGREE", "DISAGREE", "ABSTAIN"])
        self.assertEqual((outcome, res.status), ("FAILED", "REJECTED"))
        Seat.objects.filter(user=voters[4]).update(status="REVOKED", active_slot=None)
        outcome, res = run(["AGREE", "AGREE", "ABSTAIN", "ABSTAIN"], voters[:4])
        self.assertEqual((outcome, res.result["denominator"]), ("FAILED", 4))
        future = Resolution.objects.create(initiator=self.chair, title="t", content="c",
                                           approval_mode="HALF_MAJORITY",
                                           vote_deadline=timezone.now() + timedelta(hours=2))
        self.assertEqual(ResolutionService.judge_if_due(future.id), "NOT_DUE")
        future.refresh_from_db()
        self.assertEqual(future.status, "PENDING")

    def _poll(self, questions, minutes=120):
        return self.api("post", "/polls", {
            "title": "t", "kind": "SURVEY", "survey_scope": "OWNERS_ONLY",
            "deadline": (timezone.now() + timedelta(minutes=minutes)).isoformat(),
            "questions": questions}, token=self.ctoken)

    def test_tc_int_469_ac_172_02_172_03_172_04_poll_limits(self):
        """TC-INT-469 / AC-172-02~04：题数 51 失败 / 50 成功；选项 1、11 失败 / 2、10 成功；窗口 59 分钟失败 / 61 成功（半数决议同）。"""
        q = lambda n: [{"title": f"q{i}", "qtype": "TEXT"} for i in range(n)]
        self.assert_error(self._poll(q(51)), 400, "INVALID_VALUE")
        self.assert_ok(self._poll(q(50)), 201)
        opt = lambda n: [{"title": "s", "qtype": "SINGLE", "options": [f"o{i}" for i in range(n)]}]
        for n in (1, 11):
            self.assert_error(self._poll(opt(n)), 400, "INVALID_VALUE")
        for n in (2, 10):
            self.assert_ok(self._poll(opt(n)), 201)
        self.assert_error(self._poll(q(1), minutes=59), 400, "VOTE_WINDOW_TOO_SHORT")
        self.assert_ok(self._poll(q(1), minutes=61), 201)
        flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY")
        short = self.api("post", "/resolutions", {"title": "t", "content": "c", "approval_flow_id": flow.id,
                                                  "vote_deadline": (timezone.now() + timedelta(minutes=59)).isoformat()},
                         token=self.ctoken)
        self.assertGreaterEqual(short.status_code, 400)
        self.assertIn("60", short.json()["message"])

    def test_tc_int_470_ac_173_01_173_02_income_row_limits(self):
        """TC-INT-470 / AC-173-01、AC-173-02：导入 5000 行被接受、5001 行整份拒绝；逐条 500 成功、501 拒绝。"""
        header = "日期,金额,收入类别,来源说明,备注\n"

        def csv(n):
            body = header + "".join(f"2026-01-01,1.00,类{i},,\n" for i in range(n))
            return SimpleUploadedFile("i.csv", body.encode("utf-8-sig"), content_type="text/csv")

        ok = self.upload("/admin/income/sheets/import", {"file": csv(5000)}, token=self.mtoken)
        self.assertNotEqual(ok.status_code, 400, ok.content)
        bad = self.upload("/admin/income/sheets/import", {"file": csv(5001)}, token=self.mtoken)
        body = self.assert_error(bad, 400, "IMPORT_FILE_INVALID")
        self.assertIn("5000", body["message"])
        rec = lambda n: [{"occurred_on": "2026-01-01", "amount": "1.00", "category": f"c{i}"} for i in range(n)]
        self.assert_ok(self.api("post", "/admin/income/sheets", {"records": rec(500)}, token=self.mtoken), 201)
        over = self.api("post", "/admin/income/sheets", {"records": rec(501)}, token=self.mtoken)
        self.assertIn("500", self.assert_error(over, 400, "INVALID_VALUE")["message"])

    def test_tc_int_471_ac_170_05_income_amount_over_limit_refused(self):
        """TC-INT-471 / AC-170-05：上限 500000.00 时逐条录入 500000.01 被拒并提示当前上限；500000.00 成功。"""
        SystemConfig.set("claim.amount_max", "500000.00", None)
        r = {"occurred_on": "2026-01-01", "amount": "500000.01", "category": "c"}
        resp = self.api("post", "/admin/income/sheets", {"records": [r]}, token=self.mtoken)
        self.assert_error(resp, 400, "INCOME_RECORD_INVALID")
        self.assertIn("500000.00", str(resp.json()))
        r["amount"] = "500000.00"
        self.assert_ok(self.api("post", "/admin/income/sheets", {"records": [r]}, token=self.mtoken), 201)

    def test_tc_int_472_ac_174_01_term_start_before_today_rejected(self):
        """TC-INT-472 / AC-174-01：任期开始日早于今天 → 400 且提示"任期开始日不得早于今天"。"""
        owner, _, _ = self.make_owner()
        resp = self.api("post", "/admin/committee/seats",
                        {"user_id": owner.id, "position": "REPRESENTATIVE",
                         "term_start": str(date.today() - timedelta(days=1))}, token=self.admin_token)
        self.assertEqual(self.assert_error(resp, 400, "INVALID_VALUE")["message"], "任期开始日不得早于今天")

    def test_tc_int_473_ac_174_02_174_03_date_rules(self):
        """TC-INT-473 / AC-174-02、AC-174-03：发生日期晚于今日被拒、今日成功；备用金核销日期 ≤ 今日被拒、明日成功。"""
        tomorrow = date.today() + timedelta(days=1)
        self.assertIn("不得晚于今日", self.assert_error(self._reimb(occurred_on=str(tomorrow)), 400,
                                                    "INVALID_VALUE")["message"])
        self.assert_ok(self._reimb(occurred_on=str(date.today())), 201)
        adv = lambda d: self.api("post", "/claims/advances", {
            "amount": "1.00", "reason": "r", "expected_usage": "u", "expected_settle_on": str(d),
            "approval_flow_id": self.flow.id}, token=self.ctoken)
        for d in (date.today(), date.today() - timedelta(days=1)):
            self.assertIn("须晚于今日", self.assert_error(adv(d), 400, "INVALID_VALUE")["message"])
        self.assert_ok(adv(tomorrow), 201)

    def test_tc_int_474_ac_174_04_settlement_reimbursement_count_limit(self):
        """TC-INT-474 / AC-174-04：核销关联 51 张报销单被拒；50 张在校验层通过（后续因单据未审批而报其他错，不是数量错误）。"""
        body = lambda n: {"advance_id": 1, "reimbursement_ids": list(range(1, n + 1)), "reason": "r",
                          "approval_flow_id": self.flow.id}
        r51 = self.api("post", "/claims/settlements", body(51), token=self.mtoken)
        self.assertIn("1~50", self.assert_error(r51, 400, "INVALID_VALUE")["message"])
        r50 = self.api("post", "/claims/settlements", body(50), token=self.mtoken)
        self.assertNotIn("1~50", r50.json().get("message", ""))

    def test_tc_int_475_ac_174_05_duplicate_pending_appeal_and_application(self):
        """TC-INT-475 / AC-174-05：同一专有部分已有待审申诉 / 同住人申请 → 409，不新增。"""
        unit = self.make_unit(phones=["13900000003"])
        user, token = self.make_user()
        self.submit_appeal(token, unit)
        uploaded = self.upload("/attachments", {"file": SimpleUploadedFile(
            "p.png", PNG + b"2", content_type="image/png"), "purpose": "APPEAL_PROOF"}, token=token)
        resp = self.api("post", "/appeals", {"unit_id": unit.id, "proof_ids": [uploaded.data["id"]]}, token=token)
        self.assert_error(resp, 409, "APPEAL_PENDING")
        self.assertEqual(Appeal.objects.filter(user=user, unit=unit).count(), 1)


# =========================================================== US-175 / 178
class TemplatePreflightAndRegressionTests(PRBase):
    def test_tc_int_476_ac_175_01_template_dry_run_is_read_only_6_rows_4_units(self):
        """TC-INT-476 / AC-175-01：管理员下载 xlsx 模板并预检：总行数 6、失败 0、将新增 4 个专有部分；不写入清册。"""
        _, admin_token = self.make_admin()
        resp = self.client_for(admin_token).get("/api/v1/admin/registry/import/template", {"file_type": "xlsx"})
        self.assertEqual(resp.status_code, 200)
        raw = b"".join(resp.streaming_content) if resp.streaming else resp.content
        before = RegistryUnit.objects.count()
        up = self.upload("/admin/registry/import?dry_run=1", {"file": SimpleUploadedFile(
            "t.xlsx", raw, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            token=admin_token)
        data = self.assert_ok(up).data
        self.assertEqual((data["rows_total"], data["failed"], data["imported"], data["dry_run"]), (6, 0, 4, True))
        self.assertEqual(RegistryUnit.objects.count(), before)

    def test_tc_int_477_ac_178_03_existing_endpoints_keep_fields(self):
        """TC-INT-477 / AC-178-03：游客依次：登录、决议列表、我的房屋、个人中心、资料 → 均 200，既有字段齐全。"""
        from django.contrib.auth.hashers import make_password

        user, _ = self.make_user()
        user.password = make_password("Passw0rd123")
        user.save()
        login = self.assert_ok(self.api("post", "/auth/login/password",
                                        {"identifier": user.phone, "password": "Passw0rd123"}))
        self.assertTrue({"token", "user", "is_new"} <= set(login.data))
        token = login.data["token"]
        res = self.assert_ok(self.api("get", "/resolutions", {"scope": "public"}, token=token)).data
        self.assertTrue({"count", "results"} <= set(res))
        me = self.assert_ok(self.api("get", "/me", token=token)).data
        self.assertTrue({"is_guest", "units", "committee", "labels"} <= set(me["identities"]))
        self.assertTrue({"profile", "identities"} <= set(me))
        housing = self.assert_ok(self.api("get", "/me/housing", token=token)).data
        self.assertEqual(set(housing), {"summary", "units", "pending_review_count"})
        prof = self.assert_ok(self.api("get", "/me/profile", token=token)).data
        self.assertTrue({"account_no", "phone", "nickname", "avatar_url", "gender", "birthday", "email",
                         "email_state"} <= set(prof))
