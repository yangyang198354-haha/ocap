"""PHASE_08 集成测试：GR-D-006-F01 补齐的 11 个 Must Have 故事（US-006/010/013/025/028/035/042/068/071/073、US-070 后端部分）。

全部走真实 HTTP + ORM + 路由 + 权限；短信/微信仅用 apps/integrations/fakes.py 的替身。
分层标记：本文件位于 tests/integration/，由 `manage.py test tests.integration` 运行。
"""
from datetime import date, timedelta
from uuid import uuid4

from django.utils import timezone

from apps.accounts.models import User, VerificationCode
from apps.approval.models import ApprovalInstance
from apps.claims.models import Claim
from apps.committee.models import Seat
from apps.core.models import Attachment, AuditLog, RateLimit
from apps.income.models import IncomeSheet
from apps.integrations.fakes import FakeWeChatClient
from apps.integrations.wechat import set_wechat_client
from apps.polls.models import Poll
from apps.resolutions.models import Resolution
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_phone

LOGIN_FAILED_MESSAGE = "账号或密码错误；若从未设置过密码，请使用验证码登录"


def _invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE", original_name="inv.pdf",
        content_type="application/pdf", size=1024, sha256="x" * 64,
        storage_path=f"tmp/{uuid4().hex}", status="TEMP")


def _clear_limits():
    RateLimit.objects.all().delete()


# --------------------------------------------------------------------------- US-006
class WebPhoneLoginTests(ApiTestBase):
    """US-006 Web 手机号登录（验证码或密码）。"""

    def _set_password(self, token, password="Ocap2026pass"):
        resp = self.api("put", "/me/password", {"password": password, "password_confirm": password},
                        token=token)
        self.assert_ok(resp, 204)

    def test_code_login_returns_token_for_registered_phone(self):
        """AC-006-01：已注册手机号 + 有效验证码 → 200，令牌可访问 /me 且为同一用户。"""
        user, _ = self.make_user()
        resp = self.login_code(user.phone)
        self.assert_ok(resp)
        self.assertEqual(resp.data["user"]["id"], user.id)
        me = self.api("get", "/me", token=resp.data["token"])
        self.assert_ok(me)
        self.assertEqual(me.data["profile"]["id"], user.id)

    def test_password_login_by_phone_identifier(self):
        """AC-006-02：设置密码后，用手机号 + 正确密码登录成功。"""
        user, token = self.make_user()
        self._set_password(token)
        resp = self.api("post", "/auth/login/password",
                        {"identifier": user.phone, "password": "Ocap2026pass"})
        self.assert_ok(resp)
        self.assertEqual(resp.data["user"]["id"], user.id)

    def test_password_login_failure_message_is_uniform(self):
        """AC-006-03：未设密码 / 手机号未注册 / 密码错误三种情形，返回相同的 code 与 message（不泄露账号是否存在）。"""
        no_pwd, _ = self.make_user()
        with_pwd, token = self.make_user()
        self._set_password(token)
        bodies = []
        for identifier, password in ((no_pwd.phone, "Whatever2026a"),
                                     (next_phone(), "Whatever2026a"),
                                     (with_pwd.phone, "Wrong2026pass")):
            resp = self.api("post", "/auth/login/password",
                            {"identifier": identifier, "password": password})
            body = self.assert_error(resp, 400, "LOGIN_FAILED")
            bodies.append((body["code"], body["message"]))
        self.assertEqual(len(set(bodies)), 1, bodies)
        self.assertEqual(bodies[0][1], LOGIN_FAILED_MESSAGE)

    def test_wrong_login_code_rejected(self):
        """AC-006-04：错误验证码 → 400 CODE_INVALID，且未签发令牌。"""
        user, _ = self.make_user()
        self.request_code(user.phone, "LOGIN")
        resp = self.api("post", "/auth/login/code", {"phone": user.phone, "code": "000000"})
        body = self.assert_error(resp, 400, "CODE_INVALID")
        self.assertNotIn("token", body)

    def test_expired_login_code_rejected(self):
        """AC-006-04：验证码超过有效期 → 400 CODE_EXPIRED。"""
        user, _ = self.make_user()
        code = self.request_code(user.phone, "LOGIN")
        VerificationCode.objects.filter(target=user.phone, purpose="LOGIN").update(
            expires_at=timezone.now() - timedelta(seconds=1))
        resp = self.api("post", "/auth/login/code", {"phone": user.phone, "code": code})
        self.assert_error(resp, 400, "CODE_EXPIRED")

    def test_login_code_invalidated_after_five_wrong_attempts(self):
        """AC-006-04：同一验证码输错 5 次作废；之后即使输入正确验证码也不能登录。"""
        user, _ = self.make_user()
        code = self.request_code(user.phone, "LOGIN")
        statuses = []
        for _ in range(5):
            statuses.append(self.api("post", "/auth/login/code",
                                     {"phone": user.phone, "code": "000000"}).status_code)
        self.assertEqual(statuses[:4], [400, 400, 400, 400])
        self.assertEqual(statuses[4], 429)
        resp = self.api("post", "/auth/login/code", {"phone": user.phone, "code": code})
        self.assertIn(resp.status_code, (400, 429), resp.content)  # 已作废的验证码不得再换取令牌
        self.assertNotIn("token", resp.json())

    def test_password_wrong_five_times_locks_account(self):
        """AC-006-04：密码连续输错 5 次锁定（429 LOGIN_LOCKED，含 retry_after；锁定时长 15 分钟）。"""
        user, token = self.make_user()
        self._set_password(token)
        for _ in range(4):
            self.assertEqual(self.api("post", "/auth/login/password",
                                      {"identifier": user.phone, "password": "Wrong2026pass"}).status_code, 400)
        resp = self.api("post", "/auth/login/password",
                        {"identifier": user.phone, "password": "Wrong2026pass"})
        body = self.assert_error(resp, 429, "LOGIN_LOCKED")
        self.assertEqual(body["details"]["retry_after"], 900)
        resp = self.api("post", "/auth/login/password",
                        {"identifier": user.phone, "password": "Ocap2026pass"})
        self.assert_error(resp, 429, "LOGIN_LOCKED")


# --------------------------------------------------------------------------- US-010 / US-070(后端) / US-013
class SingleAccountAcrossEntriesTests(ApiTestBase):
    """US-010 手机号为账号唯一标识（Web 手机号 / 小程序手机号 / 微信三入口同一账号）。"""

    def setUp(self):
        super().setUp()
        self.wechat = FakeWeChatClient()
        set_wechat_client(self.wechat)
        self.addCleanup(set_wechat_client, None)

    def test_web_and_miniprogram_phone_logins_reach_same_account_and_identity(self):
        """AC-010-01：产权业主分别以 Web 验证码登录、小程序（EXTENDED 会话）验证码登录、密码登录 → 同一 user id，身份均含“户主”。"""
        owner, owner_token, _ = self.make_owner()
        self._pwd(owner_token)
        web = self.login_code(owner.phone)
        _clear_limits()
        code = self.request_code(owner.phone, "LOGIN")
        mini = self.api("post", "/auth/login/code",
                        {"phone": owner.phone, "code": code, "remember_me": True})
        pwd = self.api("post", "/auth/login/password",
                       {"identifier": owner.phone, "password": "Ocap2026pass"})
        for resp in (web, mini, pwd):
            self.assert_ok(resp)
            self.assertEqual(resp.data["user"]["id"], owner.id)
            me = self.api("get", "/me", token=resp.data["token"])
            self.assertEqual(me.data["profile"]["id"], owner.id)
            self.assertIn("产权业主", me.data["identities"]["labels"])

    def _pwd(self, token):
        resp = self.api("put", "/me/password",
                        {"password": "Ocap2026pass", "password_confirm": "Ocap2026pass"}, token=token)
        self.assert_ok(resp, 204)

    def test_wechat_bind_phone_then_wechat_and_phone_logins_same_account(self):
        """AC-010-02：微信登录（新建账号）→ 绑定未被占用手机号 → 再微信登录 / 手机号登录 → 同一账号。"""
        first = self.api("post", "/auth/wechat/miniapp", {"code": "wx-code-a"})
        self.assert_ok(first)
        self.assertTrue(first.data["is_new"])
        user_id = first.data["user"]["id"]
        phone = next_phone()
        code = self.request_me_code(first.data["token"], "BIND_PHONE", target=phone)
        bound = self.api("post", "/me/phone/bind", {"phone": phone, "code": code},
                         token=first.data["token"])
        self.assert_ok(bound)
        self.assertFalse(bound.data["merged"])
        again = self.api("post", "/auth/wechat/miniapp", {"code": "wx-code-a"})
        self.assert_ok(again)
        self.assertFalse(again.data["is_new"])
        self.assertEqual(again.data["user"]["id"], user_id)
        _clear_limits()
        by_phone = self.login_code(phone)
        self.assert_ok(by_phone)
        self.assertEqual(by_phone.data["user"]["id"], user_id)

    def test_second_account_for_same_phone_rejected(self):
        """AC-010-03：同一手机号不能再创建第二个账号：取注册码 409；微信账号绑定该号 → 合并为一个账号（总数不增加）。"""
        user, _ = self.make_user()
        resp = self.api("post", "/auth/codes", {"target": user.phone, "target_type": "PHONE",
                                                "purpose": "REGISTER"})
        self.assert_error(resp, 409, "PHONE_ALREADY_REGISTERED")
        wx = self.api("post", "/auth/wechat/miniapp", {"code": "wx-code-b"})
        self.assert_ok(wx)
        before = User.objects.filter(phone=user.phone, status="ACTIVE").count()
        code = self.request_me_code(wx.data["token"], "BIND_PHONE", target=user.phone)
        bound = self.api("post", "/me/phone/bind", {"phone": user.phone, "code": code},
                         token=wx.data["token"])
        self.assert_ok(bound)
        self.assertTrue(bound.data["merged"])
        self.assertEqual(User.objects.filter(phone=user.phone, status="ACTIVE").count(), before)
        self.assertEqual(bound.data["user"]["id"], user.id)

    # ---- US-070 后端部分 ----
    def test_first_wechat_login_is_new_then_not_new_and_profile_kept(self):
        """AC-070-01/02：首次小程序微信登录 is_new=true；保存昵称后再次微信登录 is_new=false，昵称保持用户最后设置的值。"""
        first = self.api("post", "/auth/wechat/miniapp", {"code": "wx-code-c"})
        self.assert_ok(first)
        self.assertTrue(first.data["is_new"])
        saved = self.api("patch", "/me/profile", {"nickname": "我的昵称"}, token=first.data["token"])
        self.assert_ok(saved)
        second = self.api("post", "/auth/wechat/miniapp", {"code": "wx-code-c"})
        self.assert_ok(second)
        self.assertFalse(second.data["is_new"])
        me = self.api("get", "/me", token=second.data["token"])
        self.assertEqual(me.data["profile"]["nickname"], "我的昵称")

    def test_phone_login_is_never_new(self):
        """AC-070-03：已有账号手机号登录响应 is_new=false（不触发头像昵称设置页）。"""
        user, _ = self.make_user()
        resp = self.login_code(user.phone)
        self.assert_ok(resp)
        self.assertFalse(resp.data["is_new"])

    def test_web_scan_first_login_takes_wechat_nickname_without_setup(self):
        """AC-070-04：Web 扫码首次微信登录 → 昵称取微信昵称（FakeWeChatClient 返回“微信用户”），不经头像昵称设置页。"""
        from apps.accounts.services import create_wechat_state

        state = create_wechat_state()
        resp = self.client_for().get("/api/v1/auth/wechat/web/callback",
                                     {"state": state, "code": "web-code-1"})
        self.assertEqual(resp.status_code, 302)
        ticket = resp["Location"].split("ticket=")[1]
        exchanged = self.api("post", "/auth/wechat/web/exchange", {"ticket": ticket})
        self.assert_ok(exchanged)
        me = self.api("get", "/me", token=exchanged.data["token"])
        self.assertEqual(me.data["profile"]["nickname"], "微信用户")


class ReRegisterAfterCancelTests(ApiTestBase):
    """US-013 账号注销后同一手机号可作为全新账号再注册。"""

    def _cancel(self, user, token):
        _clear_limits()
        code = self.request_me_code(token, "CANCEL")
        self.assert_ok(self.api("post", "/me/cancel", {"phone": user.phone, "code": code}, token=token), 204)

    def test_reregister_creates_fresh_guest_account(self):
        """AC-013-01：注销后同号注册 → 新 user id，身份“游客”，原户主身份/昵称不恢复，新旧账号无关联。

        该号码不登记在清册中，因此不触发 US-102 的清册自动绑定。
        """
        unit = self.make_unit()
        user, token, _ = self.make_owner(unit=unit)
        phone = user.phone
        self.api("patch", "/me/profile", {"nickname": "旧昵称"}, token=token)
        self._cancel(user, token)
        _clear_limits()
        code = self.request_code(phone, "REGISTER")
        resp = self.api("post", "/auth/register", {"phone": phone, "code": code})
        self.assert_ok(resp, 201)
        new_id = resp.data["user"]["id"]
        self.assertNotEqual(new_id, user.id)
        me = self.api("get", "/me", token=resp.data["token"])
        self.assertEqual(me.data["identities"]["labels"], ["游客"])
        self.assertTrue(me.data["identities"]["is_guest"])
        self.assertIsNone(me.data["profile"]["nickname"])
        self.assertFalse(Membership.objects.filter(user_id=new_id).exists())
        old = User.objects.get(id=user.id)
        self.assertEqual(old.status, "CANCELLED")
        self.assertNotEqual(old.phone, phone)
        self.assert_error(self.api("get", "/me", token=token), 401)

    def test_reregister_owner_auto_bound_by_registry(self):
        """US-102：清册中登记的手机号再注册时由清册自动绑定（取代 AC-013-02 的"需重新认证"）。

        自动绑定来源为清册；再次手动认证返回 409 ALREADY_CERTIFIED。
        """
        phone = next_phone()
        unit = self.make_unit(phones=[phone])
        user, token = self.make_user(phone=phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=token), 201)
        self._cancel(user, token)
        _clear_limits()
        code = self.request_code(phone, "REGISTER")
        reg = self.api("post", "/auth/register", {"phone": phone, "code": code})
        self.assert_ok(reg, 201)
        self.assertEqual([row["specific_part"] for row in reg.data["auto_bound"]],
                         [unit.specific_part])
        membership = Membership.objects.get(user_id=reg.data["user"]["id"], unit=unit,
                                            ended_at__isnull=True)
        self.assertEqual(membership.source, "REGISTRY")
        again = self.api("post", "/certifications", {"unit_id": unit.id}, token=reg.data["token"])
        self.assert_error(again, 409, "ALREADY_CERTIFIED")

    def test_register_with_active_phone_rejected(self):
        """AC-013-03：手机号账号未注销 → 注册被拒（409 PHONE_ALREADY_REGISTERED）。"""
        user, _ = self.make_user()
        resp = self.api("post", "/auth/codes", {"target": user.phone, "target_type": "PHONE",
                                                "purpose": "REGISTER"})
        self.assert_error(resp, 409, "PHONE_ALREADY_REGISTERED")


# --------------------------------------------------------------------------- US-025
class GuestTests(ApiTestBase):
    """US-025 游客身份与可执行操作。"""

    def test_guest_can_apply_for_certification_and_resident_binding(self):
        """AC-025-02：游客可提交清册认证（201）与同住人申请（201）。"""
        owner, _, unit = self.make_owner()
        guest, guest_token = self.make_user()
        me = self.api("get", "/me", token=guest_token)
        self.assertTrue(me.data["identities"]["is_guest"])
        self.assertEqual(me.data["identities"]["labels"], ["游客"])
        resp = self.api("post", "/resident-applications", {"unit_id": unit.id}, token=guest_token)
        self.assert_ok(resp, 201)
        cert_unit = self.make_unit(phones=[guest.phone])
        self.assert_ok(self.api("post", "/certifications", {"unit_id": cert_unit.id}, token=guest_token), 201)

    def test_guest_cannot_do_owner_only_actions(self):
        """AC-025-03：游客审批同住人申请 / 移除同住人 / 读取待审列表 → 403。"""
        owner, owner_token, unit = self.make_owner()
        applicant, applicant_token = self.make_user()
        created = self.api("post", "/resident-applications", {"unit_id": unit.id}, token=applicant_token)
        self.assert_ok(created, 201)
        _, guest_token = self.make_user()
        resp = self.api("post", f"/resident-applications/{created.data['id']}/decision",
                        {"decision": "APPROVE"}, token=guest_token)
        self.assert_error(resp, 403)
        resp = self.api("delete", f"/units/{unit.id}/residents/{applicant.id}", token=guest_token)
        self.assert_error(resp, 403)
        # 对照：产权业主可以
        resp = self.api("get", "/resident-applications/to-review", token=owner_token)
        self.assert_ok(resp)


# --------------------------------------------------------------------------- US-028
class ChangePhoneTests(ApiTestBase):
    """US-028 已认证用户更换手机号。"""

    def _change(self, token, old_phone, new_phone, new_code=None, old_code=None):
        old_code = old_code or self.request_me_code(token, "CHANGE_PHONE", target=old_phone)
        if new_code is None:
            new_code = self.request_me_code(token, "CHANGE_PHONE", target=new_phone)
        return self.api("post", "/me/phone/change",
                        {"old_phone": old_phone, "new_phone": new_phone,
                         "old_code": old_code, "new_code": new_code}, token=token)

    def test_change_to_free_phone_keeps_all_identities(self):
        """AC-028-01：新号未属任何账号 → 更换成功，不合并，户主身份保留。"""
        owner, token, unit = self.make_owner()
        new_phone = next_phone()
        resp = self._change(token, owner.phone, new_phone)
        self.assert_ok(resp)
        self.assertFalse(resp.data["merged"])
        self.assertEqual(User.objects.get(id=owner.id).phone, new_phone)
        me = self.api("get", "/me", token=token)
        self.assertIn("产权业主", me.data["identities"]["labels"])
        self.assertTrue(Membership.objects.filter(user=owner, unit=unit, role="HEAD",
                                                  ended_at__isnull=True).exists())

    def test_change_with_wrong_new_code_changes_nothing(self):
        """AC-028-02：新号验证码错误 → 400/429，原手机号与身份不变。"""
        owner, token, _ = self.make_owner()
        old_phone = owner.phone
        new_phone = next_phone()
        old_code = self.request_me_code(token, "CHANGE_PHONE", target=old_phone)
        self.request_me_code(token, "CHANGE_PHONE", target=new_phone)
        resp = self._change(token, old_phone, new_phone, new_code="000000", old_code=old_code)
        self.assertIn(resp.status_code, (400, 429), resp.content)
        self.assertEqual(User.objects.get(id=owner.id).phone, old_phone)
        me = self.api("get", "/me", token=token)
        self.assertIn("产权业主", me.data["identities"]["labels"])

    def test_old_phone_cannot_login_after_change(self):
        """AC-028-04：更换成功后旧号登录失败（404 PHONE_NOT_REGISTERED），新号登录进入同一账号。"""
        owner, token, _ = self.make_owner()
        old_phone, new_phone = owner.phone, next_phone()
        self.assert_ok(self._change(token, old_phone, new_phone))
        _clear_limits()
        req = self.api("post", "/auth/codes", {"target": old_phone, "target_type": "PHONE",
                                               "purpose": "LOGIN"})
        if req.status_code == 202:  # 即使能取到码，也不得登录进任何账号
            from apps.integrations.fakes import FakeSmsGateway

            code = [r for r in FakeSmsGateway.shared().sent if r[0] == old_phone][-1][1]
            resp = self.api("post", "/auth/login/code", {"phone": old_phone, "code": code})
            self.assert_error(resp, 404, "PHONE_NOT_REGISTERED")
        else:
            self.assertIn(req.status_code, (400, 404), req.content)
        self.assertFalse(User.objects.filter(phone=old_phone).exists())
        new_login = self.login_code(new_phone)
        self.assert_ok(new_login)
        self.assertEqual(new_login.data["user"]["id"], owner.id)


# --------------------------------------------------------------------------- US-035
class RegistryPhoneChangeAfterCertificationTests(ApiTestBase):
    """US-035 清册手机号被修改或删除后已认证身份保留。"""

    def _certified(self):
        phone = next_phone()
        unit = self.make_unit(phones=[phone])
        user, token = self.make_user(phone=phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=token), 201)
        _, admin_token = self.make_admin()
        return user, token, unit, admin_token

    def test_modify_registry_phone_keeps_owner(self):
        """AC-035-01：管理员把清册手机号改成其他号码 → 用户仍是该专有部分的有效产权业主。"""
        user, token, unit, admin_token = self._certified()
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                        {"owners": [{"name": "新业主", "phones": [next_phone()]}]}, token=admin_token)
        self.assert_ok(resp)
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, ended_at__isnull=True).exists())
        me = self.api("get", "/me", token=token)
        self.assertIn("产权业主", me.data["identities"]["labels"])

    def test_delete_registry_phone_keeps_head(self):
        """AC-035-02：管理员把清册手机号全部删除 → 户主身份仍在。"""
        user, token, unit, admin_token = self._certified()
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners", {"owners": []}, token=admin_token)
        self.assert_ok(resp)
        self.assertEqual(unit.phones.count(), 0)
        membership = Membership.objects.get(user=user, unit=unit, ended_at__isnull=True)
        self.assertEqual(membership.role, "HEAD")

    def test_certification_after_change_compares_new_registry(self):
        """AC-035-03：清册手机号改动后，他人用原号码认证 → 422 PHONE_NOT_IN_REGISTRY 且可申诉；新号码持有者认证成功。"""
        user, token, unit, admin_token = self._certified()
        old_phone = user.phone
        new_phone = next_phone()
        self.assert_ok(self.api("put", f"/admin/registry/units/{unit.id}/owners",
                                {"owners": [{"name": "新业主", "phones": [new_phone]}]}, token=admin_token))
        # 让原用户换成别的号码，由另一个账号持有原清册号码 P
        User.objects.filter(id=user.id).update(phone=next_phone())
        other, other_token = self.make_user(phone=old_phone)
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=other_token)
        body = self.assert_error(resp, 422, "PHONE_NOT_IN_REGISTRY")
        self.assertTrue(body["details"]["appeal_available"])
        holder, holder_token = self.make_user(phone=new_phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=holder_token), 201)

    def test_non_admin_cannot_modify_registry_phones(self):
        """AC-035-04：普通用户 / 业委会成员修改清册手机号 → 403；未登录 → 401，清册不变。"""
        user, token, unit, _ = self._certified()
        member, member_token, _ = self.make_owner()
        self.make_seat(member, "CHAIR")
        for tok, expected in ((token, (403,)), (member_token, (403,)), (None, (401,))):
            resp = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                            {"owners": [{"name": "新业主", "phones": [next_phone()]}]}, token=tok)
            self.assertIn(resp.status_code, expected, resp.content)
        self.assertEqual(unit.phones.count(), 1)


# --------------------------------------------------------------------------- US-042
class RepresentativeGrantTests(ApiTestBase):
    """US-042 管理员赋予业主代表身份。"""

    def setUp(self):
        super().setUp()
        _, self.admin_token = self.make_admin()
        self.assert_ok(self.api("put", "/admin/committee/config",
                                {"term_months_chair": 12, "term_months_vice": 12,
                                 "term_months_member": 12, "term_months_rep": 12,
                                 "cap_rep": 1, "cap_member": 5},
                                token=self.admin_token))

    def _grant(self, user, token=None):
        return self.api("post", "/admin/committee/seats",
                        {"user_id": user.id, "position": "REPRESENTATIVE",
                         "term_start": str(date.today())}, token=token or self.admin_token)

    def test_grant_to_owner_succeeds_and_user_becomes_participant(self):
        """AC-042-01：产权业主被赋予 → 201；/me 显示业主代表；之后发起的代表投票自动含其参与；审计新增 SEAT_GRANTED（AC-042-06）。"""
        owner, owner_token, _ = self.make_owner()
        before = AuditLog.objects.filter(action="SEAT_GRANTED").count()
        resp = self._grant(owner)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["position"], "REPRESENTATIVE")
        me = self.api("get", "/me", token=owner_token)
        self.assertIn("业主代表", me.data["identities"]["labels"])
        self.assertEqual(AuditLog.objects.filter(action="SEAT_GRANTED").count(), before + 1)
        chair, chair_token, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        poll = self.api("post", "/polls",
                        {"title": "代表投票", "kind": "REP_VOTE",
                         "deadline": (timezone.now() + timedelta(days=1)).isoformat(),
                         "questions": [{"title": "同意?", "qtype": "AGREE_OPPOSE_ABSTAIN"}]},
                        token=chair_token)
        self.assert_ok(poll, 201)
        self.assertTrue(Poll.objects.get(id=poll.data["id"]).participants.filter(user=owner).exists())

    def test_grant_to_resident_or_guest_rejected(self):
        """AC-042-02：同住人 / 游客被赋予 → 422 NOT_AN_OWNER。"""
        _, _, unit = self.make_owner()
        resident, _ = self.make_resident(unit)
        guest, _ = self.make_user()
        for target in (resident, guest):
            self.assert_error(self._grant(target), 422, "NOT_AN_OWNER")
        self.assertFalse(Seat.objects.filter(position="REPRESENTATIVE").exists())

    def test_grant_over_cap_rejected(self):
        """AC-042-03：业主代表人数已达上限（cap_rep=1） → 409 CAP_REACHED。"""
        first, _, _ = self.make_owner()
        second, _, _ = self.make_owner()
        self.assert_ok(self._grant(first), 201)
        self.assert_error(self._grant(second), 409, "CAP_REACHED")

    def test_grant_to_committee_member_rejected(self):
        """AC-042-04：已持有委员席位者不可再被赋予业主代表（不可兼任）→ 409 ALREADY_SEATED。"""
        member, _, _ = self.make_owner()
        self.make_seat(member, "MEMBER")
        self.assert_error(self._grant(member), 409, "ALREADY_SEATED")
        self.assertEqual(Seat.objects.filter(user=member, status="ACTIVE").count(), 1)

    def test_non_admin_cannot_grant(self):
        """AC-042-05：普通业主 / 主任赋予业主代表 → 403；未登录 → 401，无席位产生。"""
        target, _, _ = self.make_owner()
        chair, chair_token, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        _, owner_token, _ = self.make_owner()
        for tok, expected in ((owner_token, (403,)), (chair_token, (403,)), (None, (401,))):
            resp = self.api("post", "/admin/committee/seats",
                            {"user_id": target.id, "position": "REPRESENTATIVE"}, token=tok)
            self.assertIn(resp.status_code, expected, resp.content)
        self.assertFalse(Seat.objects.filter(user=target, status="ACTIVE").exists())


# --------------------------------------------------------------------------- US-068
class InFlightIdentityInvalidationTests(ApiTestBase):
    """US-068 身份失效时在途事项保持不变。"""

    def setUp(self):
        super().setUp()
        self.chair, _, _ = self.make_owner()
        self.chair_seat = self.make_seat(self.chair, "CHAIR")
        self.approver, _, _ = self.make_owner()
        self.approver_seat = self.make_seat(self.approver, "MEMBER")
        self.chair_token = self.token_of(self.chair)
        self.approver_token = self.token_of(self.approver)
        self.res_flow = self.make_flow(scope="RESOLUTION", mode="DESIGNATED", approvers=[self.approver])
        _, self.admin_token = self.make_admin()

    def _revoke(self, seat):
        resp = self.api("delete", f"/admin/committee/seats/{seat.id}", token=self.admin_token)
        self.assert_ok(resp, 204)

    def _create_resolution(self):
        resp = self.api("post", "/resolutions",
                        {"title": "加装电梯", "content": "拟加装电梯一部",
                         "approval_flow_id": self.res_flow.id}, token=self.chair_token)
        self.assert_ok(resp, 201)
        return resp.data["id"]

    def _claim(self, flow, submitter, token):
        resp = self.api("post", "/claims/reimbursements",
                        {"amount": "100.00", "reason": "打印费",
                         "occurred_on": str(date.today() - timedelta(days=1)),
                         "invoice_ids": [str(_invoice(submitter).id)],
                         "approval_flow_id": flow.id}, token=token)
        self.assert_ok(resp, 201)
        return resp.data["id"]

    def test_initiator_seat_revoked_resolution_stays_pending_and_flow_continues(self):
        """AC-068-01：发起人业委会身份被撤销 → 决议仍为审批中；原指定审批人仍可审批通过。"""
        resolution_id = self._create_resolution()
        self._revoke(self.chair_seat)
        self.assertEqual(Resolution.objects.get(id=resolution_id).status, "PENDING")
        instance = ApprovalInstance.objects.get(subject_type="resolution", subject_id=resolution_id)
        self.assertEqual(instance.status, "PENDING")
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=self.approver_token)
        self.assert_ok(resp)
        self.assertEqual(Resolution.objects.get(id=resolution_id).status, "APPROVED")

    def test_approver_seat_revoked_cannot_approve_and_claim_stays_pending(self):
        """AC-068-02：指定审批人身份被撤销 → 审批 403；报销单保持审批中，不自动转交。"""
        member, _, _ = self.make_owner()
        self.make_seat(member, "MEMBER")
        member_token = self.token_of(member)
        flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.approver])
        claim_id = self._claim(flow, member, member_token)
        self._revoke(self.approver_seat)
        instance = ApprovalInstance.objects.get(subject_type="claim", subject_id=claim_id)
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=self.approver_token)
        self.assert_error(resp, 403)
        instance.refresh_from_db()
        self.assertEqual(instance.status, "PENDING")
        self.assertEqual(Claim.objects.get(id=claim_id).status, "PENDING")
        self.assertEqual(instance.flow_snapshot["approver_ids"], [self.approver.id])

    def test_withdraw_and_resubmit_with_valid_flow_after_approvers_invalid(self):
        """AC-068-03：审批人全部失效后，发起人撤回并选新的有效流程重新提交 → 重新进入审批中。"""
        member, _, _ = self.make_owner()
        self.make_seat(member, "MEMBER")
        member_token = self.token_of(member)
        old_flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.approver])
        claim_id = self._claim(old_flow, member, member_token)
        self._revoke(self.approver_seat)
        self.assert_ok(self.api("post", f"/claims/{claim_id}/withdraw", token=member_token))
        new_approver, _, _ = self.make_owner()
        self.make_seat(new_approver, "MEMBER")
        new_flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[new_approver])
        resp = self.api("post", f"/claims/{claim_id}/resubmit",
                        {"amount": "100.00", "reason": "打印费",
                         "invoice_ids": [str(_invoice(member).id)],
                         "approval_flow_id": new_flow.id}, token=member_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "PENDING")
        self.assertEqual(resp.data["revision"], 2)

    def test_expired_representative_cannot_respond_but_earlier_answer_and_denominator_kept(self):
        """AC-068-04：业主代表 R1 已提交、R2 任期到期后提交被拒 403；R1 的答卷保持，分母（participant_count）仍为发起时的 2。"""
        rep1, _, _ = self.make_owner()
        rep2, _, _ = self.make_owner()
        self.make_seat(rep1, "REPRESENTATIVE")
        seat2 = self.make_seat(rep2, "REPRESENTATIVE")
        created = self.api("post", "/polls",
                           {"title": "代表投票", "kind": "REP_VOTE",
                            "deadline": (timezone.now() + timedelta(days=1)).isoformat(),
                            "questions": [{"title": "同意?", "qtype": "AGREE_OPPOSE_ABSTAIN"}]},
                           token=self.chair_token)
        self.assert_ok(created, 201)
        poll = Poll.objects.get(id=created.data["id"])
        question = poll.questions.get()
        answers = {"answers": [{"question_id": question.id, "value": "AGREE"}]}
        self.assert_ok(self.api("post", f"/polls/{poll.id}/responses", answers,
                                token=self.token_of(rep1)), 201)
        Seat.objects.filter(id=seat2.id).update(term_end=timezone.localdate() - timedelta(days=1))
        resp = self.api("post", f"/polls/{poll.id}/responses", answers, token=self.token_of(rep2))
        self.assert_error(resp, 403, "FORBIDDEN")
        poll.refresh_from_db()
        self.assertEqual(poll.participant_count, 2)
        self.assertEqual(poll.responses.count(), 1)
        self.assertEqual(poll.responses.get().answers.get().value, "AGREE")
        self.assertTrue(poll.participants.filter(user=rep2).exists())

    def test_public_resolution_still_shows_initiator_label_after_seat_revoked(self):
        """AC-068-05：已公开决议在发起人身份失效后仍可读，且仍存在发起人信息（不被抹除）。"""
        resolution_id = self._create_resolution()
        instance = ApprovalInstance.objects.get(subject_type="resolution", subject_id=resolution_id)
        self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                {"action": "APPROVE"}, token=self.approver_token))
        self._revoke(self.chair_seat)
        _, viewer_token, _ = self.make_owner()
        resp = self.api("get", f"/resolutions/{resolution_id}", token=viewer_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "APPROVED")
        self.assertEqual(resp.data["initiator"]["id"], self.chair.id)
        self.assertIn("主任", resp.data["initiator"]["labels"])

    def test_invalidated_user_cannot_use_privileged_actions(self):
        """AC-068-06：身份失效者发起决议 / 发起投票 / 审批 → 403。"""
        resolution_id = self._create_resolution()
        self._revoke(self.chair_seat)
        self._revoke(self.approver_seat)
        resp = self.api("post", "/resolutions",
                        {"title": "再发起", "content": "x", "approval_flow_id": self.res_flow.id},
                        token=self.chair_token)
        self.assert_error(resp, 403)
        resp = self.api("post", "/polls",
                        {"title": "再投票", "kind": "SURVEY", "survey_scope": "OWNERS_ONLY",
                         "deadline": (timezone.now() + timedelta(days=1)).isoformat(),
                         "questions": [{"title": "q", "qtype": "SINGLE", "options": ["a", "b"]}]},
                        token=self.chair_token)
        self.assert_error(resp, 403, "FORBIDDEN")
        instance = ApprovalInstance.objects.get(subject_type="resolution", subject_id=resolution_id)
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=self.approver_token)
        self.assert_error(resp, 403)

    def test_invalidated_initiator_can_withdraw_own_but_others_cannot(self):
        """AC-068-07：发起人身份已失效仍可撤回自己的在途决议（WITHDRAWN）；其他委员 / 管理员撤回他人事项被拒。"""
        resolution_id = self._create_resolution()
        self._revoke(self.chair_seat)
        # 其他业委会成员（指定审批人）不能撤回
        resp = self.api("post", f"/resolutions/{resolution_id}/withdraw", token=self.approver_token)
        self.assertIn(resp.status_code, (403, 404), resp.content)
        # 管理员令牌不能撤回
        resp = self.api("post", f"/resolutions/{resolution_id}/withdraw", token=self.admin_token)
        self.assertEqual(resp.status_code, 403, resp.content)
        self.assertEqual(Resolution.objects.get(id=resolution_id).status, "PENDING")
        resp = self.api("post", f"/resolutions/{resolution_id}/withdraw", token=self.chair_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "WITHDRAWN")


# --------------------------------------------------------------------------- US-071
class MultiApproverTests(ApiTestBase):
    """US-071 多审批人规则与自批边界。"""

    def setUp(self):
        super().setUp()
        self.m, _, _ = self.make_owner()
        self.make_seat(self.m, "MEMBER")
        self.p1, _, _ = self.make_owner()
        self.make_seat(self.p1, "MEMBER")
        self.p2, _, _ = self.make_owner()
        self.make_seat(self.p2, "MEMBER")
        self.m_token, self.p1_token, self.p2_token = (self.token_of(u) for u in (self.m, self.p1, self.p2))

    def _claim(self, flow, **extra):
        return self.api("post", "/claims/reimbursements",
                        {"amount": "200.00", "reason": "耗材",
                         "occurred_on": str(date.today() - timedelta(days=1)),
                         "invoice_ids": [str(_invoice(self.m).id)],
                         "approval_flow_id": flow.id, **extra}, token=self.m_token)

    def _decide(self, claim_id, token, action="APPROVE"):
        instance = ApprovalInstance.objects.get(subject_type="claim", subject_id=claim_id)
        return self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": action}, token=token)

    def test_any_one_of_two_approvers_passes(self):
        """AC-071-01：流程指定 P1、P2，P1 同意 → 申请 APPROVED。"""
        flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.p1, self.p2])
        claim_id = self._claim(flow).data["id"]
        resp = self._decide(claim_id, self.p1_token)
        self.assert_ok(resp)
        self.assertEqual(Claim.objects.get(id=claim_id).status, "APPROVED")

    def test_second_approver_after_decision_rejected_state_unchanged(self):
        """AC-071-02：P1 已通过后 P2 再通过 / 拒绝 → 409 ALREADY_DECIDED，状态与金额不变。"""
        flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.p1, self.p2])
        claim_id = self._claim(flow).data["id"]
        self.assert_ok(self._decide(claim_id, self.p1_token))
        for action in ("APPROVE", "REJECT"):
            self.assert_error(self._decide(claim_id, self.p2_token, action), 409, "ALREADY_DECIDED")
        claim = Claim.objects.get(id=claim_id)
        self.assertEqual((claim.status, str(claim.amount)), ("APPROVED", "200.00"))

    def test_only_self_in_flow_rejects_claim_advance_and_income(self):
        """AC-071-03：流程审批人只有申请人本人 → 报销 / 预借 / 收入表提交均 422 NO_ELIGIBLE_APPROVER，且不创建申请。"""
        expense_flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.m])
        before = Claim.objects.count()
        resp = self._claim(expense_flow)
        self.assert_error(resp, 422, "NO_ELIGIBLE_APPROVER")
        resp = self.api("post", "/claims/advances",
                        {"amount": "500.00", "reason": "预借", "expected_usage": "差旅",
                         "expected_settle_on": str(date.today() + timedelta(days=10)),
                         "approval_flow_id": expense_flow.id}, token=self.m_token)
        self.assert_error(resp, 422, "NO_ELIGIBLE_APPROVER")
        self.assertEqual(Claim.objects.filter(status="PENDING").count(), 0)
        self.assertEqual(Claim.objects.count(), before)
        income_flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[self.m])
        sheet = IncomeSheet.objects.create(submitted_by=self.m)
        resp = self.api("post", f"/admin/income/sheets/{sheet.id}/submit",
                        {"approval_flow_id": income_flow.id}, token=self.m_token)
        self.assertIn(resp.status_code, (409, 422), resp.content)
        self.assertNotEqual(IncomeSheet.objects.get(id=sheet.id).status, "PENDING")

    def test_submitter_with_another_approver_cannot_self_approve(self):
        """AC-071-04：审批人为 M 与 P → 提交成功（PENDING）；M 自批 403 SELF_APPROVAL_FORBIDDEN；P 批准成功。"""
        flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[self.m, self.p1])
        resp = self._claim(flow)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["status"], "PENDING")
        claim_id = resp.data["id"]
        self.assert_error(self._decide(claim_id, self.m_token), 403, "SELF_APPROVAL_FORBIDDEN")
        self.assertEqual(Claim.objects.get(id=claim_id).status, "PENDING")
        self.assert_ok(self._decide(claim_id, self.p1_token))
        self.assertEqual(Claim.objects.get(id=claim_id).status, "APPROVED")

    def test_chair_designated_self_may_approve_resolution(self):
        """AC-071-05：主任发起指定负责人审批的决议，负责人就是本人 → 允许审批通过，状态 APPROVED。"""
        chair, _, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        chair_token = self.token_of(chair)
        flow = self.make_flow(scope="RESOLUTION", mode="DESIGNATED", approvers=[chair])
        created = self.api("post", "/resolutions",
                           {"title": "自批决议", "content": "内容", "approval_flow_id": flow.id},
                           token=chair_token)
        self.assert_ok(created, 201)
        instance = ApprovalInstance.objects.get(subject_type="resolution", subject_id=created.data["id"])
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=chair_token)
        self.assert_ok(resp)
        self.assertEqual(Resolution.objects.get(id=created.data["id"]).status, "APPROVED")

    def test_chair_not_designated_cannot_approve_resolution(self):
        """AC-071-06：指定负责人是另一人 Q，主任 D 审批 → 403 FORBIDDEN，决议保持 PENDING。"""
        chair, _, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        chair_token = self.token_of(chair)
        flow = self.make_flow(scope="RESOLUTION", mode="DESIGNATED", approvers=[self.p1])
        created = self.api("post", "/resolutions",
                           {"title": "他批决议", "content": "内容", "approval_flow_id": flow.id},
                           token=chair_token)
        self.assert_ok(created, 201)
        instance = ApprovalInstance.objects.get(subject_type="resolution", subject_id=created.data["id"])
        resp = self.api("post", f"/approval/instances/{instance.id}/decision",
                        {"action": "APPROVE"}, token=chair_token)
        self.assert_error(resp, 403, "FORBIDDEN")
        self.assertEqual(Resolution.objects.get(id=created.data["id"]).status, "PENDING")


# --------------------------------------------------------------------------- US-073
class AdminPasswordResetTests(ApiTestBase):
    """US-073 管理员重置其他管理员的密码。"""

    def test_admin_resets_other_admin_password(self):
        """AC-073-01：A 重置 B → 204；B 旧密码登录 400，新密码登录 200；B 的旧令牌失效；审计 ADMIN_PASSWORD_RESET。"""
        a, a_token = self.make_admin(password="AdminA12345")
        b, b_token = self.make_admin(username="adminbee", password="AdminB12345")
        self.assert_ok(self.api("get", "/admin/audit-logs", token=b_token))
        resp = self.api("post", f"/admin/admins/{b.id}/reset-password",
                        {"password": "NewPass2026x"}, token=a_token)
        self.assert_ok(resp, 204)
        self.assert_error(self.api("post", "/admin/auth/login",
                                   {"username": "adminbee", "password": "AdminB12345"}), 400)
        new_login = self.api("post", "/admin/auth/login",
                             {"username": "adminbee", "password": "NewPass2026x"})
        self.assert_ok(new_login)
        self.assertTrue(new_login.data["token"])
        self.assert_error(self.api("get", "/admin/audit-logs", token=b_token), 401)
        self.assertTrue(AuditLog.objects.filter(action="ADMIN_PASSWORD_RESET",
                                                object_id=str(b.id)).exists())

    def test_member_cannot_reset_admin_password(self):
        """AC-073-02：普通用户 / 产权业主 / 业委会成员调用重置接口 → 403，被重置者密码不变。"""
        b, _ = self.make_admin(username="adminbee2", password="AdminB12345")
        user, user_token = self.make_user()
        owner, owner_token, _ = self.make_owner()
        chair, chair_token, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        for tok in (user_token, owner_token, chair_token):
            resp = self.api("post", f"/admin/admins/{b.id}/reset-password",
                            {"password": "NewPass2026x"}, token=tok)
            self.assert_error(resp, 403)
        self.assert_ok(self.api("post", "/admin/auth/login",
                                {"username": "adminbee2", "password": "AdminB12345"}))

    def test_anonymous_cannot_reset_and_no_self_service_entry(self):
        """AC-073-03：未登录访客重置 → 401（OBS-001 已修复）；系统没有管理员自助注册 / 找回入口（对应路径 404/405）。"""
        b, _ = self.make_admin(username="adminbee3", password="AdminB12345")
        resp = self.api("post", f"/admin/admins/{b.id}/reset-password", {"password": "NewPass2026x"})
        self.assertEqual(resp.status_code, 401, resp.content)
        for path in ("/admin/auth/register", "/admin/auth/forgot-password", "/admin/auth/reset-password"):
            self.assertIn(self.api("post", path, {"username": "x"}).status_code, (404, 405), path)
        self.assert_ok(self.api("post", "/admin/auth/login",
                                {"username": "adminbee3", "password": "AdminB12345"}))


# --------------------------------------------------------------------------- US-002（fake 微信，补齐可测部分）
class WebWechatScanTests(ApiTestBase):
    """US-002 Web 微信扫码登录（经 FakeWeChatClient；真实扫码/授权页面为 NOT_TESTABLE，见 MV-001）。"""

    def setUp(self):
        super().setUp()
        self.wechat = FakeWeChatClient()
        set_wechat_client(self.wechat)
        self.addCleanup(set_wechat_client, None)

    def _scan(self, code="scan-1", state=None):
        from apps.accounts.services import create_wechat_state

        return self.client_for().get("/api/v1/auth/wechat/web/callback",
                                     {"state": state or create_wechat_state(), "code": code})

    def _token_from(self, resp):
        ticket = resp["Location"].split("ticket=")[1]
        exchanged = self.api("post", "/auth/wechat/web/exchange", {"ticket": ticket})
        self.assert_ok(exchanged)
        return exchanged

    def test_second_scan_enters_existing_account(self):
        """AC-002-02：同一微信再次扫码 → 进入已有账号，不新建账号。"""
        first = self._token_from(self._scan("scan-same"))
        count = User.objects.count()
        second = self._token_from(self._scan("scan-same"))
        self.assertEqual(first.data["user"]["id"], second.data["user"]["id"])
        self.assertEqual(User.objects.count(), count)
        self.assertFalse(second.data["is_new"])

    def test_invalid_state_or_wechat_error_creates_no_account(self):
        """AC-002-03：二维码失效（state 无效/已用）或微信侧失败 → 重定向带 error，不创建账号、不发 ticket。"""
        before = User.objects.count()
        bad = self._scan(state="not-a-valid-state")
        self.assertEqual(bad.status_code, 302)
        self.assertIn("error=STATE_INVALID", bad["Location"])
        self.assertNotIn("ticket=", bad["Location"])
        self.wechat.fail_kind = "UPSTREAM"
        failed = self._scan("scan-fail")
        self.assertEqual(failed.status_code, 302)
        self.assertIn("error=", failed["Location"])
        self.assertNotIn("ticket=", failed["Location"])
        self.assertEqual(User.objects.count(), before)

    def test_wechat_user_without_phone_must_bind_phone_before_certification(self):
        """AC-002-04：未验证手机号的微信用户做清册认证 → 409 PHONE_REQUIRED；其他登录后功能（/me）不受限。"""
        token = self._token_from(self._scan("scan-nophone")).data["token"]
        self.assert_ok(self.api("get", "/me", token=token))
        unit = self.make_unit(phones=[next_phone()])
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_error(resp, 409, "PHONE_REQUIRED")
