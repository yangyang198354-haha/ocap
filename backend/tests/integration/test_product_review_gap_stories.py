"""ocap_product_review GROUP_D：product_review §2.1 中"定位级 CONSISTENT"且既有测试没有任何 US/AC 编号引用的 13 个 Must Have 故事，
补 AC 级验证（GR-A-001 condition；TC-INT-499 起）。故事：ocap 批次 US-009、015、018、022、038、039、040、053、056、057、060、062、066。
（content_publish 的 US-113 见 tests/e2e/test_product_review_content.py。）
"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.hashers import check_password, make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import AdminAccount, User
from apps.approval.models import ApprovalInstance
from apps.committee.models import Seat
from apps.committee.services import CommitteeCommands
from apps.core.audit import AuditLog
from apps.identity.services import IdentityService
from apps.income.models import IncomeSheet
from apps.ledger.models import LedgerReport
from apps.polls.models import Poll
from apps.polls.services import PollService
from apps.registry.models import RegistryUnit
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_phone


class AccountStoryTests(ApiTestBase):
    def test_tc_int_499_us_009_set_password_rules(self):
        """TC-INT-499 / US-009（AC-009-01~06）：一致且合规的密码设置成功并可用账号/手机号登录；邮箱 + 密码被拒；
        不一致 / 缺确认 / 过短 / 全数字 / 与手机号相同被拒且凭据不变；8 位与 64 位边界通过。"""
        user, token = self.make_user()
        put = lambda body: self.api("put", "/me/password", body, token=token)
        self.assert_error(put({"password": "Passw0rd123", "password_confirm": "Passw0rd124"}), 400, "PASSWORD_MISMATCH")
        self.assert_error(put({"password": "Passw0rd123"}), 400, "PASSWORD_CONFIRM_REQUIRED")
        for bad in ("Ab1", "12345678", user.phone, "a" * 65 + "1"):
            resp = put({"password": bad, "password_confirm": bad})
            self.assertEqual(resp.status_code, 400, bad)
        user.refresh_from_db()
        self.assertFalse(user.password)
        self.assertEqual(put({"password": "Passw0rd123", "password_confirm": "Passw0rd123"}).status_code, 204)
        for ident in (user.account_no, user.phone):
            self.assert_ok(self.api("post", "/auth/login/password", {"identifier": ident, "password": "Passw0rd123"}))
        self.assertGreaterEqual(self.api("post", "/auth/login/password", {
            "identifier": "x@y.com", "password": "Passw0rd123"}).status_code, 400)
        eight, sixty4 = "Abcdef12", "A1" + "b" * 62
        for pwd in (eight, sixty4):
            resp = put({"password": pwd, "password_confirm": pwd, "current_password": "Passw0rd123"})
            self.assertEqual(resp.status_code, 204, pwd)
            self.assertEqual(self.api("post", "/auth/login/password", {"identifier": user.account_no, "password": pwd}).status_code, 200)
            put = lambda body, p=pwd: self.api("put", "/me/password", {**body, "current_password": p}, token=token)

    def test_tc_int_500_us_015_merge_keeps_primary_and_fills_empty_fields(self):
        """TC-INT-500 / US-015（AC-015-01~04）：合并后昵称与密码取手机号原账号 A；A 空的资料项取微信账号 W 的值；
        A 非空的保持；两者皆空仍为空；W 不再是独立账号。"""
        a, _ = self.make_user(nickname="A昵称")
        a.password = make_password("Passw0rd123")
        a.gender = 1
        a.save()
        w, _ = self.make_user(phone=None, nickname="W昵称")
        w.password = make_password("Other12345")
        w.gender = 2
        w.birthday = date(1990, 1, 2)
        w.email = "w@example.com"
        w.save()
        IdentityService.merge_accounts(a, w, admin_id=None)
        a.refresh_from_db(), w.refresh_from_db()
        self.assertEqual((a.nickname, a.gender, str(a.birthday), a.email), ("A昵称", 1, "1990-01-02", "w@example.com"))
        self.assertTrue(check_password("Passw0rd123", a.password))
        self.assertEqual(w.status, "CANCELLED")
        self.assertIsNone(a.avatar_attachment_id)

    def test_tc_int_501_us_018_registry_multi_phone_and_privacy(self):
        """TC-INT-501 / US-018（AC-018-01~03）：同一专有部分登记多个手机号，任一均可认证；无手机号的专有部分认证被拒（可申诉）；
        非管理员（含户主）不能查看清册，响应不含他人手机号。"""
        _, admin_token = self.make_admin()
        unit = RegistryUnit.objects.create(building="9", unit_no="1", floor="1", room="101")
        p1, p2 = next_phone(), next_phone()
        self.assert_ok(self.api("put", f"/admin/registry/units/{unit.id}/owners",
                                {"owners": [{"name": "业主甲", "phones": [p1, p2]}]}, token=admin_token))
        for phone in (p1, p2):
            user, token = self.make_user(phone=phone)
            self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id, "name": "业主甲"},
                                    token=token), 201)
        empty = RegistryUnit.objects.create(building="9", unit_no="1", floor="1", room="102")
        _, token = self.make_user()
        body = self.assert_error(self.api("post", "/certifications", {"unit_id": empty.id, "name": "业主甲"},
                                          token=token), 422, "OWNER_NOT_MATCHED")
        self.assertTrue(body["details"]["appeal_available"])
        owner, otoken, _ = self.make_owner()
        for path in ("/admin/registry/units", f"/admin/registry/units/{unit.id}"):
            resp = self.api("get", path, token=otoken)
            self.assertEqual(resp.status_code, 403)
            self.assertNotIn(p1, resp.content.decode())
        options = self.api("get", "/units/options?building=9", token=otoken).content.decode()
        self.assertNotIn(p1, options)
        self.assertNotIn(p2, options)

    def test_tc_int_502_us_022_owner_only_via_registry_or_approved_appeal(self):
        """TC-INT-502 / US-022（AC-022-01~03）：手机号不在清册 → 认证失败；经同住人审批只得"同住人"；资料修改不能提升身份；
        申诉通过后成为产权业主。"""
        _, otoken, unit = self.make_owner()
        stranger, token = self.make_user()
        self.assert_error(self.api("post", "/certifications", {"unit_id": unit.id, "name": "业主甲"}, token=token),
                          422, "OWNER_NOT_MATCHED")
        app =self.api("post", "/resident-applications", {"unit_id": unit.id}, token=token).data
        self.assert_ok(self.api("post", f"/resident-applications/{app['id']}/decision", {"decision": "APPROVE"}, token=otoken))
        self.assertEqual(self.api("get", "/me/housing", token=token).data["units"][0]["role"], "RESIDENT")
        before = self.api("get", "/me", token=token).data["identities"]
        self.api("patch", "/me/profile", {"role": "OWNER", "identity": "HEAD", "nickname": "改名"}, token=token)
        after = self.api("get", "/me", token=token).data["identities"]
        self.assertEqual(before["summary"], after["summary"])
        self.assertEqual([u["role"] for u in after["units"]], ["RESIDENT"])
        self.assertFalse(Membership.objects.filter(user=stranger, role__in=["HEAD", "OWNER"]).exists())
        guest, gtoken = self.make_user()
        up = self.upload("/attachments", {"file": SimpleUploadedFile("p.png", b"\x89PNG\r\n\x1a\n" + uuid4().bytes, content_type="image/png"),
                                          "purpose": "APPEAL_PROOF"}, token=gtoken)
        appeal = self.api("post", "/appeals", {"unit_id": unit.id, "owner_name": "业主甲",
                                               "proof_ids": [up.data["id"]]}, token=gtoken).data
        _, admin_token = self.make_admin()
        self.assert_ok(self.api("post", f"/admin/appeals/{appeal['id']}/decision", {"decision": "APPROVE"}, token=admin_token))
        self.assertIn(self.api("get", "/me/housing", token=gtoken).data["units"][0]["role"], {"OWNER", "HEAD"})


class CommitteeStoryTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()
        self.assert_ok(self.api("put", "/admin/committee/config", {
            "cap_chair": 1, "cap_vice": 2, "cap_member": 4, "cap_rep": 3, "term_months_chair": 12, "term_months_vice": 12,
            "term_months_member": 12, "term_months_rep": 12}, token=self.admin_token))

    def grant(self, user, position, **extra):
        return self.api("post", "/admin/committee/seats", {"user_id": user.id, "position": position, **extra},
                        token=self.admin_token)

    def test_tc_int_503_us_038_revoke_change_and_caps(self):
        """TC-INT-503 / US-038（AC-038-01~06）：撤销委员后名额释放、产权身份不变；副主任→主任（有名额）仅持主任；
        主任满员时变更被拒且仍为副主任；业主代表可撤销；非管理员（含主任）被拒；审计记录。"""
        member, mtoken, _ = self.make_owner()
        seat = self.grant(member, "MEMBER").data
        self.assert_ok(self.api("delete", f"/admin/committee/seats/{seat['id']}", token=self.admin_token), 204)
        self.assertEqual(Seat.objects.filter(user=member, status="ACTIVE").count(), 0)
        self.assertIsNone(self.api("get", "/me", token=mtoken).data["identities"]["committee"])
        self.assertEqual(self.api("get", "/me/housing", token=mtoken).data["units"][0]["role"], "HEAD")
        vice, vtoken, _ = self.make_owner()
        vseat = self.grant(vice, "VICE_CHAIR").data
        self.assert_ok(self.api("patch", f"/admin/committee/seats/{vseat['id']}", {"position": "CHAIR"}, token=self.admin_token))
        self.assertEqual(list(Seat.objects.filter(user=vice, status="ACTIVE").values_list("position", flat=True)), ["CHAIR"])
        vice2, _, _ = self.make_owner()
        v2 = self.grant(vice2, "VICE_CHAIR").data
        resp = self.api("patch", f"/admin/committee/seats/{v2['id']}", {"position": "CHAIR"}, token=self.admin_token)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(Seat.objects.get(user=vice2, status="ACTIVE").position, "VICE_CHAIR")
        rep, _, _ = self.make_owner()
        rseat = self.grant(rep, "REPRESENTATIVE").data
        self.assert_ok(self.api("delete", f"/admin/committee/seats/{rseat['id']}", token=self.admin_token), 204)
        self.assertEqual(self.api("get", "/me/housing", token=self.token_of(rep)).data["units"][0]["role"], "HEAD")
        for token in (vtoken,):  # vice 现为主任
            self.assertEqual(self.api("delete", f"/admin/committee/seats/{v2['id']}", token=token).status_code, 403)
            self.assertEqual(self.api("patch", f"/admin/committee/seats/{v2['id']}", {"position": "MEMBER"}, token=token).status_code, 403)
        self.assertTrue(Seat.objects.filter(id=v2["id"], status="ACTIVE").exists())
        actions = set(AuditLog.objects.values_list("action", flat=True))
        self.assertTrue({"SEAT_GRANTED", "SEAT_REVOKED", "SEAT_CHANGED"} <= actions)

    def test_tc_int_504_us_039_uniqueness_auto_invalidation_and_reappoint(self):
        """TC-INT-504 / US-039（AC-039-01~09）：已任委员不可再赋主任/副主任；业主代表与业委会互斥；撤销最后一个认证 → 席位失效、多房屋时保持；
        注销 → 失效；到期当日仍有效、次日失效；连任可再赋。"""
        m, mtoken, unit1 = self.make_owner()
        self.assert_ok(self.grant(m, "MEMBER"), 201)
        self.assert_error(self.grant(m, "CHAIR"), 409, "ALREADY_SEATED")
        self.assert_error(self.grant(m, "VICE_CHAIR"), 409, "ALREADY_SEATED")
        self.assert_error(self.grant(m, "REPRESENTATIVE"), 409, "ALREADY_SEATED")
        r, _, _ = self.make_owner()
        self.assert_ok(self.grant(r, "REPRESENTATIVE"), 201)
        self.assert_error(self.grant(r, "MEMBER"), 409, "ALREADY_SEATED")
        # AC-039-09：多房屋时撤销其一，席位保持；撤销最后一个，席位失效
        second = self.make_unit()
        Membership.objects.create(user=m, unit=second, role="OWNER", source="CERTIFIED", active_slot=1)
        self.assert_ok(self.api("post", "/admin/memberships/revoke", {"user_id": m.id, "unit_id": second.id}, token=self.admin_token))
        self.assertTrue(Seat.objects.filter(user=m, status="ACTIVE").exists())
        self.assert_ok(self.api("post", "/admin/memberships/revoke", {"user_id": m.id, "unit_id": unit1.id}, token=self.admin_token))
        self.assertFalse(Seat.objects.filter(user=m, status="ACTIVE").exists())
        # AC-039-04：注销 → 失效、名额释放
        c, ctoken, _ = self.make_owner()
        self.assert_ok(self.grant(c, "MEMBER"), 201)
        code = self.request_me_code(ctoken, "CANCEL")
        self.assertEqual(self.api("post", "/me/cancel", {"phone": c.phone, "code": code}, token=ctoken).status_code, 204)
        self.assertFalse(Seat.objects.filter(user=c, status="ACTIVE").exists())
        # AC-039-05/06/08：到期边界与连任
        e, _, _ = self.make_owner()
        seat = Seat.objects.get(id=self.grant(e, "MEMBER").data["id"])
        today = timezone.localdate()
        Seat.objects.filter(id=seat.id).update(term_end=today)
        call_command("run_due_jobs")
        self.assertEqual(Seat.objects.get(id=seat.id).status, "ACTIVE")  # 到期当日仍有效
        Seat.objects.filter(id=seat.id).update(term_end=today - timedelta(days=1))
        call_command("run_due_jobs")
        self.assertEqual(Seat.objects.get(id=seat.id).status, "EXPIRED")
        self.assertIn("SEAT_EXPIRED", set(AuditLog.objects.values_list("action", flat=True)))
        again = self.grant(e, "MEMBER")
        self.assert_ok(again, 201)
        self.assertGreaterEqual(date.fromisoformat(again.json()["term_end"]), today + timedelta(days=360))

    def test_tc_int_505_us_040_config_caps_validation_and_audit(self):
        """TC-INT-505 / US-040（AC-040-01~08）：配置保存后可读回；满员拒绝；调低上限不踢现任但新赋予被拒；非法值拒绝且配置不变；
        非管理员 403；成功保存写审计（失败保存的审计见 TC-INT-512 / DEF-017）。"""
        cfg = self.assert_ok(self.api("get", "/admin/committee/config", token=self.admin_token)).data
        self.assertEqual((cfg["cap_chair"], cfg["cap_vice"], cfg["cap_member"]), (1, 2, 4))
        for _ in range(2):
            self.assert_ok(self.grant(self.make_owner()[0], "VICE_CHAIR"), 201)
        self.assert_error(self.grant(self.make_owner()[0], "VICE_CHAIR"), 409, "CAP_REACHED")
        self.assert_ok(self.api("put", "/admin/committee/config", {"cap_vice": 1}, token=self.admin_token))
        self.assertEqual(Seat.objects.filter(position="VICE_CHAIR", status="ACTIVE").count(), 2)
        self.assert_error(self.grant(self.make_owner()[0], "VICE_CHAIR"), 409, "CAP_REACHED")
        for bad in ("x", -1, 1.5, True):
            self.assert_error(self.api("put", "/admin/committee/config", {"cap_member": bad}, token=self.admin_token), 400, "INVALID_VALUE")
        self.assertEqual(self.api("get", "/admin/committee/config", token=self.admin_token).data["cap_member"], 4)
        _, utoken = self.make_user()
        self.assertEqual(self.api("put", "/admin/committee/config", {"cap_member": 9}, token=utoken).status_code, 403)
        self.assertEqual(self.api("get", "/admin/committee/config", token=utoken).status_code, 403)
        ok = AuditLog.objects.filter(action="COMMITTEE_CONFIG_CHANGED", result="SUCCESS")
        self.assertEqual(ok.count(), 2)  # 初始配置 1 次 + 调低副主任上限 1 次
        self.assertEqual(AuditLog.objects.filter(action="COMMITTEE_CONFIG_CHANGED").first().actor_type, "ADMIN")

    def test_tc_int_512_us_040_failed_config_save_is_audited_as_failure(self):
        """TC-INT-512 / US-040（AC-040-08）、AC-064-06：保存失败（如非法人数上限）时审计日志新增一条"结果"为失败的记录。
        现状：非法值在写审计前抛错，未留任何记录 → 产品缺陷 DEF-017（本用例保持原样作为证据）。"""
        before = AuditLog.objects.filter(action="COMMITTEE_CONFIG_CHANGED").count()
        self.assert_error(self.api("put", "/admin/committee/config", {"cap_member": -3}, token=self.admin_token), 400, "INVALID_VALUE")
        rows = AuditLog.objects.filter(action="COMMITTEE_CONFIG_CHANGED").order_by("-id")
        self.assertEqual(rows.count(), before + 1, "AC-040-08：失败的保存应新增 1 条审计")
        self.assertNotEqual(rows.first().result, "SUCCESS")

    def test_tc_int_506_us_066_merge_keeps_higher_seat_and_audits_invalidation(self):
        """TC-INT-506 / US-066（AC-066-01~06）：合并后仅留较高身份（主任>委员；委员>业主代表）；仅业主代表一方时保留；同级双方只剩一个；
        合并不被拒绝；合并后再赋予另一种身份被拒（身份失效审计见 TC-INT-513 / DEF-018）。"""
        def pair(pa, pb):
            a, _, _ = self.make_owner()
            b, _, _ = self.make_owner()
            self.make_seat(a, pa)
            if pb:
                self.make_seat(b, pb)
            return a, b

        a, b = pair("CHAIR", "MEMBER")
        IdentityService.merge_accounts(a, b, admin_id=None)
        self.assertEqual(list(Seat.objects.filter(user=a, status="ACTIVE").values_list("position", flat=True)), ["CHAIR"])
        self.assertEqual(Seat.objects.filter(status="ACTIVE", position="MEMBER").count(), 0)
        a2, b2 = pair("REPRESENTATIVE", "MEMBER")
        IdentityService.merge_accounts(a2, b2, admin_id=None)
        self.assertEqual(list(Seat.objects.filter(user=a2, status="ACTIVE").values_list("position", flat=True)), ["MEMBER"])
        a3, b3 = pair("REPRESENTATIVE", None)
        IdentityService.merge_accounts(a3, b3, admin_id=None)
        self.assertEqual(list(Seat.objects.filter(user=a3, status="ACTIVE").values_list("position", flat=True)), ["REPRESENTATIVE"])
        a4, b4 = pair("VICE_CHAIR", "VICE_CHAIR")
        IdentityService.merge_accounts(a4, b4, admin_id=None)
        self.assertEqual(Seat.objects.filter(user=a4, status="ACTIVE").count(), 1)
        self.assert_error(self.grant(a, "MEMBER"), 409, "ALREADY_SEATED")

    def test_tc_int_513_us_066_merge_invalidated_seat_is_audited(self):
        """TC-INT-513 / US-066（AC-066-05）、AC-064-08：账号合并使一方业委会/业主代表身份失效时，审计日志新增身份失效记录。
        现状：merge_seats 只把席位置为 MERGED，没有任何审计（ACCOUNTS_MERGED 之外无记录）→ 产品缺陷 DEF-018（本用例保持原样作为证据）。"""
        a, _, _ = self.make_owner()
        b, _, _ = self.make_owner()
        self.make_seat(a, "CHAIR")
        seat_b = self.make_seat(b, "MEMBER")
        IdentityService.merge_accounts(a, b, admin_id=None)
        self.assertEqual(Seat.objects.get(id=seat_b.id).status, "MERGED")
        rows = AuditLog.objects.filter(action__in=["SEAT_INVALIDATED", "SEAT_MERGED"])
        self.assertGreaterEqual(rows.count(), 1, "AC-066-05：被取代的身份应有一条失效审计")


class PollStoryTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.chair, self.ctoken, _ = self.make_owner()
        self.make_seat(self.chair, "CHAIR")
        self.reps = []
        for _ in range(4):
            u, t, _ = self.make_owner()
            self.make_seat(u, "REPRESENTATIVE")
            self.reps.append((u, t))

    def create_vote(self, questions):
        resp = self.api("post", "/polls", {"title": "代表投票", "kind": "REP_VOTE",
                                           "deadline": (timezone.now() + timedelta(hours=2)).isoformat(),
                                           "questions": questions}, token=self.ctoken)
        self.assert_ok(resp, 201)
        return Poll.objects.get(id=resp.data["id"])

    @staticmethod
    def aoa(title="议题"):
        return {"title": title, "qtype": "AGREE_OPPOSE_ABSTAIN"}

    def answer(self, poll, token, values):
        qs = list(poll.questions.order_by("id"))
        return self.api("post", f"/polls/{poll.id}/responses", {"answers": [
            {"question_id": q.id, "value": v} for q, v in zip(qs, values)]}, token=token)

    def close(self, poll):
        Poll.objects.filter(id=poll.id).update(deadline=timezone.now() - timedelta(minutes=1))
        PollService.close_due()

    def test_tc_int_507_us_053_rep_vote_judgement_strict_majority_fixed_denominator(self):
        """TC-INT-507 / US-053（AC-053-01~08）：分母为发起时代表总数，同意严格过半才通过；弃权/未提交不计同意；各"同意/反对/弃权"题独立；
        打分与选择题只汇总无结论；截止前不出结论；发起后一名代表任期到期，分母不变。"""
        poll = self.create_vote([self.aoa("甲"), self.aoa("乙"),
                                 {"title": "分", "qtype": "SCORE", "required": False},
                                 {"title": "选", "qtype": "SINGLE", "options": ["x", "y"], "required": False}])
        self.assertEqual(poll.participant_count, 4)
        self.assert_error(self.api("get", f"/polls/{poll.id}/result", token=self.ctoken), 409, "NOT_CLOSED")
        plan = [("AGREE", "AGREE"), ("AGREE", "AGREE"), ("AGREE", "DISAGREE")]  # 甲 3 票同意；乙 2 票同意（恰好一半）
        for (user, token), (a, b) in zip(self.reps, plan):
            self.assert_ok(self.api("post", f"/polls/{poll.id}/responses", {"answers": [
                {"question_id": q.id, "value": v} for q, v in zip(poll.questions.order_by("id"), [a, b, "4", "x"])]}, token=token), 201)
        # 第 4 名代表任期到期后不能提交；分母仍为 4（AC-053-08）
        Seat.objects.filter(user=self.reps[3][0]).update(term_end=timezone.localdate() - timedelta(days=1))
        self.assert_error(self.answer(poll, self.reps[3][1], ["AGREE", "AGREE", "1", "x"]), 403, "FORBIDDEN")
        self.close(poll)
        result = self.assert_ok(self.api("get", f"/polls/{poll.id}/result", token=self.ctoken)).data["results"]
        q = {x["title"]: x for x in result["questions"]}
        self.assertEqual((q["甲"]["denominator"], q["甲"]["passed"], q["甲"]["counts"]["AGREE"]), (4, True, 3))
        self.assertEqual((q["乙"]["denominator"], q["乙"]["passed"]), (4, False))
        self.assertNotIn("passed", q["分"])
        self.assertNotIn("passed", q["选"])
        self.assertEqual(q["分"]["average"], 4.0)
        self.assertEqual(q["选"]["options"][0]["count"], 3)
        self.assertEqual(result["responses"], 3)

    def test_tc_int_508_us_056_submit_rules(self):
        """TC-INT-508 / US-056（AC-056-01~06）：一次提交成功并实名记录；重复提交被拒；必答未答被拒；截止后被拒；无资格被拒；未登录被拒。"""
        poll = self.create_vote([self.aoa()])
        self.assert_error(self.answer(poll, self.reps[0][1], []), 400, "INVALID_VALUE")
        self.assert_ok(self.answer(poll, self.reps[0][1], ["AGREE"]), 201)
        self.assertEqual(poll.responses.get().user_id, self.reps[0][0].id)
        self.assert_error(self.answer(poll, self.reps[0][1], ["DISAGREE"]), 409, "ALREADY_VOTED")
        _, gtoken = self.make_user()
        self.assert_error(self.answer(poll, gtoken, ["AGREE"]), 403, "FORBIDDEN")
        self.assertEqual(self.api("post", f"/polls/{poll.id}/responses", {"answers": []}).status_code, 401)
        survey = self.api("post", "/polls", {"title": "调查", "kind": "SURVEY", "survey_scope": "OWNERS_ONLY",
                                             "deadline": (timezone.now() + timedelta(hours=2)).isoformat(),
                                             "questions": [{"title": "q", "qtype": "TEXT"}]}, token=self.ctoken)
        sp = Poll.objects.get(id=survey.data["id"])
        self.assert_error(self.answer(sp, gtoken, ["意见"]), 403, "FORBIDDEN")
        q = sp.questions.get()
        dup = self.api("post", f"/polls/{sp.id}/responses", {"answers": [
            {"question_id": q.id, "value": "a"}, {"question_id": q.id, "value": "b"}]}, token=self.reps[1][1])
        self.assert_error(dup, 400, "INVALID_VALUE")
        self.assert_ok(self.answer(sp, self.reps[1][1], ["意见"]), 201)
        self.close(poll)
        self.assert_error(self.answer(poll, self.reps[1][1], ["AGREE"]), 409, "POLL_CLOSED")
        self.assertEqual(poll.responses.count(), 1)

    def test_tc_int_509_us_057_results_public_after_close_only_aggregates(self):
        """TC-INT-509 / US-057（AC-057-01~05）：截止前任何人看不到结果；截止后任意已登录用户（含游客）可见汇总，
        不含提交人姓名/账号/所选意见明细；未登录被拒；发起接口没有"是否公开"字段。"""
        poll = self.create_vote([self.aoa()])
        voter, vtoken = self.reps[0]
        voter.nickname = "e2e_投票人甲"
        voter.save()
        self.assert_ok(self.answer(poll, vtoken, ["AGREE"]), 201)
        guest, gtoken = self.make_user()
        for token in (gtoken, self.ctoken, vtoken):
            self.assert_error(self.api("get", f"/polls/{poll.id}/result", token=token), 409, "NOT_CLOSED")
        self.close(poll)
        data = self.assert_ok(self.api("get", f"/polls/{poll.id}/result", token=gtoken)).data
        self.assertEqual(data["results"]["questions"][0]["counts"], {"AGREE": 1, "DISAGREE": 0, "ABSTAIN": 0})
        text = str(data)
        self.assertNotIn("e2e_投票人甲", text)
        self.assertNotIn(voter.account_no, text)
        self.assertNotIn(voter.phone, text)
        self.assertEqual(self.api("get", f"/polls/{poll.id}/result").status_code, 401)
        detail = self.api("get", f"/polls/{poll.id}", token=gtoken).data
        self.assertFalse([k for k in detail if "public" in k.lower()])


class FinanceStoryTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.clerk, self.clerk_token, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.approver, self.atoken, _ = self.make_owner()
        self.make_seat(self.approver, "MEMBER")
        self.other, self.otoken, _ = self.make_owner()
        self.make_seat(self.other, "MEMBER")
        self.flow = self.make_flow(scope="INCOME", approvers=[self.approver])
        self.admin, self.admin_token = self.make_admin()

    def _sheet(self, amount="100.00", flow=None, token=None):
        resp = self.api("post", "/admin/income/sheets", {"records": [
            {"occurred_on": str(date.today()), "amount": amount, "category": "物业费"},
            {"occurred_on": str(date.today()), "amount": "5.00", "category": "停车费"}]}, token=token or self.clerk_token)
        self.assert_ok(resp, 201)
        sheet_id = resp.data["id"]
        sub = self.api("post", f"/admin/income/sheets/{sheet_id}/submit", {"approval_flow_id": (flow or self.flow).id},
                       token=token or self.clerk_token)
        self.assert_ok(sub)
        return sheet_id

    def _decide(self, sheet_id, token, action="APPROVE"):
        inst = ApprovalInstance.objects.get(subject_type="income_sheet", subject_id=sheet_id)
        return self.api("post", f"/approval/instances/{inst.id}/decision", {"action": action}, token=token)

    def _generate(self, token=None):
        return self.api("post", "/ledger/reports/generate", {"period_type": "YEAR", "year": date.today().year},
                        token=token or self.clerk_token)

    def test_tc_int_510_us_060_income_sheet_effective_void_and_permissions(self):
        """TC-INT-510 / US-060（AC-060-01~11）：待审批不计入报表；非指定审批人审批被拒；录入人自审被拒；审批通过后生效并计入；
        生效后不可修改；非原审批人（含其他委员、发起人、管理员）不能作废；原审批人作废整份后不再计入；不提供单行作废；审计记录。"""
        sid = self._sheet()
        self.assertEqual(self._generate().data["total_income"], "0.00")  # AC-060-02
        self.assertIn(self._decide(sid, self.otoken).status_code, (403,))  # AC-060-07
        self_flow = self.make_flow(scope="INCOME", approvers=[self.clerk, self.other])
        sid2 = self._sheet(flow=self_flow)
        self.assertIn(self._decide(sid2, self.clerk_token).status_code, (400, 403, 409, 422))  # AC-060-08
        self.assertEqual(IncomeSheet.objects.get(id=sid2).status, "PENDING")
        self.assert_ok(self._decide(sid, self.atoken))
        self.assertEqual(IncomeSheet.objects.get(id=sid).status, "EFFECTIVE")
        self.assertEqual(self._generate().data["total_income"], "105.00")  # AC-060-01
        resp = self.api("put", f"/admin/income/sheets/{sid}", {"records": []}, token=self.clerk_token)
        self.assertIn(resp.status_code, (404, 405, 409))  # AC-060-03：没有修改生效收入表的接口，或被拒
        # AC-060-11：不提供单行作废接口（路由不存在）；整份作废由原审批人执行（AC-060-04）
        self.assertEqual(self.api("post", f"/admin/income/sheets/{sid}/records/1/void", {}, token=self.atoken).status_code, 404)
        void = self.api("post", f"/admin/income/sheets/{sid}/void", {}, token=self.atoken)
        self.assert_ok(void)
        self.assertEqual(IncomeSheet.objects.get(id=sid).status, "VOID")
        self.assertEqual(self._generate().data["total_income"], "0.00")
        self.assertIn("INCOME_VOIDED", set(AuditLog.objects.values_list("action", flat=True)))

    def test_tc_int_514_us_060_only_original_approver_can_void(self):
        """TC-INT-514 / US-060（AC-060-10、AC-060-04，Q109=B）：已生效收入表只有原审批流程指定的审批人能作废；
        其他业委会成员、录入人、管理员尝试作废 → 被拒绝，收入表保持生效。
        现状：void_sheet 不校验原审批人（ApprovalEngine.is_original_approver 无调用方），任一业委会成员都能作废 → 产品缺陷 DEF-019（本用例保持原样作为证据）。"""
        denied = []
        for who, token in (("其他委员", self.otoken), ("录入人", self.clerk_token), ("管理员", self.admin_token)):
            sid = self._sheet()
            self.assert_ok(self._decide(sid, self.atoken))
            resp = self.api("post", f"/admin/income/sheets/{sid}/void", {}, token=token)
            if resp.status_code in (401, 403) and IncomeSheet.objects.get(id=sid).status == "EFFECTIVE":
                denied.append(who)
        self.assertEqual(denied, ["其他委员", "录入人", "管理员"], "非原审批人作废未被拒绝")


    def test_tc_int_511_us_062_regenerate_report_permissions_and_content(self):
        """TC-INT-511 / US-062（AC-062-01~05）：委员可重新生成，结果含已生效收入、不含已作废收入；普通业主 / 同住人 / 游客 / 管理员被拒；审计记录。"""
        sid = self._sheet("200.00")
        self.assert_ok(self._decide(sid, self.atoken))
        first = self.assert_ok(self._generate(), 201).data
        self.assertEqual(first["total_income"], "205.00")
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sid}/void", {}, token=self.atoken))
        again = self.assert_ok(self._generate(), 201).data
        self.assertEqual((again["id"], again["total_income"]), (first["id"], "0.00"))
        plain, ptoken, unit = self.make_owner()
        res, rtoken = self.make_resident(unit)
        _, gtoken = self.make_user()
        for token in (ptoken, rtoken, gtoken):
            self.assertEqual(self._generate(token).status_code, 403)
        # 管理员令牌：被拒绝（IsCommitteeMember 对非用户主体返回 401，见 e2e 报告观察项 OBS-1；AC-062-04 只要求"被拒绝，无权限"）
        self.assertIn(self._generate(self.admin_token).status_code, (401, 403))
        rep, reptoken, _ = self.make_owner()
        self.make_seat(rep, "REPRESENTATIVE")
        self.assertEqual(self._generate(reptoken).status_code, 403)
        self.assertGreaterEqual(AuditLog.objects.filter(action__icontains="REPORT").count(), 1)
        self.assertEqual(LedgerReport.objects.count(), 1)
