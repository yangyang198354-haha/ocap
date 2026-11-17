"""PHASE_08 集成测试（ocap_identity_property）：清册匹配引导的 HTTP 接口、触发点、隐私与安全。

关联 US-232、US-239、US-240、US-241、US-242（后端部分）；MOD-132/133/134；IFC-332~337。
真实路由器 + ORM + FakeSms/FakeWeChat；合成手机号与姓名（C-73）；不连接任何真实外部服务。
TC-INT-930 起。
"""
import json

from apps.accounts.models import User
from apps.core.models import AuditLog, RateLimit
from apps.integrations.fakes import FakeWeChatClient
from apps.integrations.wechat import set_wechat_client
from apps.residency.models import Membership, PhoneMatchPrompt
from tests.phone_match_support import OWNER_NAME, PhoneMatchBase
from tests.support import next_account_no, next_phone


class RegisterTriggerTests(PhoneMatchBase):
    def test_tc_int_930_register_with_match_opens_prompt_without_binding(self):
        """TC-INT-930 / AC-239-01、AC-241-01：清册手机号注册 → auto_bound==[]、registry_match=={pending,count}、无 Membership、行 PENDING。"""
        phone = next_phone()
        self.reg_unit([phone])
        resp = self.assert_ok(self.register_raw(phone), 201)
        self.assertEqual(resp.data["auto_bound"], [])
        self.assertEqual(resp.data["registry_match"], {"pending": True, "count": 1})
        uid = resp.data["user"]["id"]
        self.assertFalse(Membership.objects.filter(user_id=uid).exists())
        self.assertEqual(self.prompt_status(uid), "PENDING")
        self.assertEqual(self.api("get", "/me", token=resp.data["token"]).data["identities"]["labels"], ["游客"])

    def test_tc_int_931_register_without_match_no_row(self):
        """TC-INT-931 / AC-239-03：手机号不在清册 → registry_match 为 {False,0}，不建行，注册 201。"""
        resp = self.assert_ok(self.register_raw(next_phone()), 201)
        self.assertEqual(resp.data["registry_match"], {"pending": False, "count": 0})
        self.assertEqual(resp.data["auto_bound"], [])
        self.assertFalse(PhoneMatchPrompt.objects.exists())

    def test_tc_int_932_registry_added_after_register_does_not_trigger(self):
        """TC-INT-932 / AC-239-09：注册后管理员才在清册补该手机号 → 不建行，GET 匹配为空，再登录也不触发。"""
        phone = next_phone()
        resp = self.assert_ok(self.register_raw(phone), 201)
        self.reg_unit([phone])
        self.assertEqual(self.matches(resp.data["token"]).data, {"pending": False, "total": 0, "units": []})
        RateLimit.objects.all().delete()  # 验证码发送限流：同一目标注册后立即登录需先清
        login = self.assert_ok(self.login_code(phone))
        self.assertEqual(self.matches(login.data["token"]).data["pending"], False)
        self.assertFalse(PhoneMatchPrompt.objects.exists())

    def test_tc_int_933_register_all_already_owned_no_prompt(self):
        """TC-INT-933 / AC-239-04：手机号匹配的专有部分用户均已是产权业主 → count=0 不引导（经绑定手机号触发）。"""
        phone = next_phone()
        unit = self.reg_unit([phone])
        user = User.objects.create(account_no=next_account_no(), phone=None)
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="CERTIFIED", active_slot=1,
                                  head_slot=1)
        token = self.token_of(user)
        code = self.request_me_code(token, "BIND_PHONE", target=phone)
        bound = self.assert_ok(self.api("post", "/me/phone/bind", {"phone": phone, "code": code}, token=token))
        self.assertEqual(bound.data["registry_match"], {"pending": False, "count": 0})
        self.assertFalse(PhoneMatchPrompt.objects.filter(user=user).exists())

    def test_tc_int_934_partial_owned_counts_only_unowned(self):
        """TC-INT-934 / AC-239-04：2 套匹配中已拥有 1 套 → count=1，仅列出未拥有的那套。"""
        phone = next_phone()
        owned = self.reg_unit([phone], room="301")
        free = self.reg_unit([phone], room="302")
        user = User.objects.create(account_no=next_account_no(), phone=None)
        Membership.objects.create(user=user, unit=owned, role="HEAD", source="CERTIFIED", active_slot=1,
                                  head_slot=1)
        token = self.token_of(user)
        code = self.request_me_code(token, "BIND_PHONE", target=phone)
        bound = self.assert_ok(self.api("post", "/me/phone/bind", {"phone": phone, "code": code}, token=token))
        self.assertEqual(bound.data["registry_match"], {"pending": True, "count": 1})
        self.assertEqual([u["unit_id"] for u in self.matches(token).data["units"]], [free.id])


class BindChangeMergeTests(PhoneMatchBase):
    def setUp(self):
        super().setUp()
        set_wechat_client(FakeWeChatClient())
        self.addCleanup(set_wechat_client, None)

    def _wechat_user(self, code="wx-identity-property"):
        wx = self.assert_ok(self.api("post", "/auth/wechat/miniapp", {"code": code}))
        return wx.data["user"]["id"], wx.data["token"]

    def test_tc_int_935_wechat_first_bind_triggers_and_no_phone_no_match(self):
        """TC-INT-935 / AC-239-05、AC-239-08、AC-242-04：微信用户无手机号时无匹配；首次绑定匹配手机号后出现 pending；响应 auto_bound==[]。"""
        phone = next_phone()
        unit = self.reg_unit([phone])
        uid, token = self._wechat_user()
        self.assertEqual(self.matches(token).data, {"pending": False, "total": 0, "units": []})
        code = self.request_me_code(token, "BIND_PHONE", target=phone)
        bound = self.assert_ok(self.api("post", "/me/phone/bind", {"phone": phone, "code": code}, token=token))
        self.assertFalse(bound.data["merged"])
        self.assertEqual(bound.data["auto_bound"], [])
        self.assertEqual(bound.data["registry_match"], {"pending": True, "count": 1})
        self.assertEqual([u["unit_id"] for u in self.matches(token).data["units"]], [unit.id])
        self.assertFalse(Membership.objects.filter(user_id=uid).exists())

    def test_tc_int_936_bind_unmatched_phone_no_prompt(self):
        """TC-INT-936 / AC-242-04：绑定不在清册的手机号 → registry_match 为 {False,0}，不建行。"""
        _, token = self._wechat_user("wx-identity-property-2")
        phone = next_phone()
        code = self.request_me_code(token, "BIND_PHONE", target=phone)
        bound = self.assert_ok(self.api("post", "/me/phone/bind", {"phone": phone, "code": code}, token=token))
        self.assertEqual(bound.data["registry_match"], {"pending": False, "count": 0})
        self.assertFalse(PhoneMatchPrompt.objects.exists())

    def test_tc_int_937_bind_with_account_merge_does_not_trigger(self):
        """TC-INT-937 / AC-239-12：绑定的手机号已属另一账号 → 合并；registry_match=={False,0}，主账号也无新引导。"""
        phone = next_phone()
        self.reg_unit([phone])
        primary, _ = self.make_user(phone=phone)
        _, token = self._wechat_user("wx-identity-property-3")
        code = self.request_me_code(token, "BIND_PHONE", target=phone)
        bound = self.assert_ok(self.api("post", "/me/phone/bind", {"phone": phone, "code": code}, token=token))
        self.assertTrue(bound.data["merged"])
        self.assertEqual(bound.data["registry_match"], {"pending": False, "count": 0})
        self.assertEqual(bound.data["auto_bound"], [])
        self.assertFalse(PhoneMatchPrompt.objects.filter(status="PENDING").exists())
        self.assertFalse(Membership.objects.filter(user=primary).exists())
        self.assertEqual(self.matches(bound.data["token"]).data["pending"], False)

    def test_tc_int_938_change_phone_expires_pending(self):
        """TC-INT-938 / AC-239-05：注册后（PENDING）更换为另一匹配清册的号码 → 行变 EXPIRED，不再引导，也不出现新引导。"""
        old_phone, new_phone = next_phone(), next_phone()
        self.reg_unit([old_phone], room="301")
        self.reg_unit([new_phone], room="302")
        resp = self.assert_ok(self.register_raw(old_phone), 201)
        token, uid = resp.data["token"], resp.data["user"]["id"]
        self.assertEqual(self.prompt_status(uid), "PENDING")
        RateLimit.objects.all().delete()
        old_code = self.request_me_code(token, "CHANGE_PHONE", target=old_phone)
        new_code = self.request_me_code(token, "CHANGE_PHONE", target=new_phone)
        changed = self.assert_ok(self.api("post", "/me/phone/change", {
            "old_phone": old_phone, "new_phone": new_phone, "old_code": old_code, "new_code": new_code},
            token=token))
        self.assertFalse(changed.data["merged"])
        self.assertEqual(self.prompt_status(uid), "EXPIRED")
        self.assertNotIn("registry_match", changed.data)
        self.assertEqual(self.matches(token).data, {"pending": False, "total": 0, "units": []})
        self.assertEqual(self.confirm(token, [1]).status_code, 409)

    def test_tc_int_939_change_phone_merge_drops_secondary_prompt(self):
        """TC-INT-939 / AC-239-05、AC-239-12：换号并入另一账号 → 被并入账号的待确认行不再为 PENDING，主账号无新引导。"""
        old_phone, new_phone = next_phone(), next_phone()
        self.reg_unit([old_phone])
        primary, primary_token = self.make_user(phone=new_phone)
        resp = self.assert_ok(self.register_raw(old_phone), 201)
        token, uid = resp.data["token"], resp.data["user"]["id"]
        RateLimit.objects.all().delete()
        old_code = self.request_me_code(token, "CHANGE_PHONE", target=old_phone)
        new_code = self.request_me_code(token, "CHANGE_PHONE", target=new_phone)
        changed = self.assert_ok(self.api("post", "/me/phone/change", {
            "old_phone": old_phone, "new_phone": new_phone, "old_code": old_code, "new_code": new_code},
            token=token))
        self.assertTrue(changed.data["merged"])
        self.assertFalse(PhoneMatchPrompt.objects.filter(user_id=uid, status="PENDING").exists())
        self.assertFalse(PhoneMatchPrompt.objects.filter(user=primary).exists())
        self.assertEqual(self.matches(primary_token).data["pending"], False)


class MatchesEndpointTests(PhoneMatchBase):
    def setUp(self):
        super().setUp()
        self.phone = next_phone()
        self.unit = self.reg_unit([self.phone], unit_type="RESIDENCE")
        self.resp = self.register_raw(self.phone)
        self.token = self.resp.data["token"]

    def test_tc_int_940_matches_response_shape_and_privacy(self):
        """TC-INT-940 / AC-239-01、AC-239-07、REQ-NFUNC-043：200 只含 pending/total/units；单项只含 unit_id/坐落/类型；不含姓名与手机号。"""
        resp = self.assert_ok(self.matches(self.token))
        self.assertEqual(set(resp.data), {"pending", "total", "units"})
        self.assertEqual(resp.data["pending"], True)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["units"], [{"unit_id": self.unit.id, "specific_part": self.unit.specific_part,
                                               "unit_type_label": "住宅"}])
        text = resp.content.decode("utf-8")
        self.assertNotIn(OWNER_NAME, text)
        self.assertNotIn(self.phone, text)

    def test_tc_int_941_matches_requires_login_and_member(self):
        """TC-INT-941 / AC-239-08：未登录 401；管理员令牌不得读取成员引导接口（401/403）。"""
        self.assert_error(self.api("get", "/me/registry-matches"), 401)
        _, admin_token = self.make_admin()
        self.assertIn(self.api("get", "/me/registry-matches", token=admin_token).status_code, (401, 403))

    def test_tc_int_942_matches_cannot_probe_other_phone(self):
        """TC-INT-942 / AC-239-08、REQ-NFUNC-043：查询参数（phone/user_id）被忽略；用户 B 只能看到自己手机号的匹配。"""
        _, other_token = self.make_user(phone=next_phone())
        resp = self.api("get", f"/me/registry-matches?phone={self.phone}&user_id=1", token=other_token)
        self.assertEqual(self.assert_ok(resp).data, {"pending": False, "total": 0, "units": []})
        self.assertNotIn(self.phone, resp.content.decode("utf-8"))

    def test_tc_int_943_matches_ten_twelve_units_total(self):
        """TC-INT-943 / AC-239-10、AC-239-11：同号 12 套全部返回（后端不设上限、不折叠）；total==12，按数字自然顺序。"""
        phone = next_phone()
        ids = [self.reg_unit([phone], building="车库", unit_no="", floor="", room=f"B-{n}",
                             unit_type="PARKING").id for n in (10, 2, 1, 3, 4, 5, 6, 7, 8, 9, 11, 12)]
        resp = self.assert_ok(self.register_raw(phone), 201)
        self.assertEqual(resp.data["registry_match"], {"pending": True, "count": 12})
        data = self.matches(resp.data["token"]).data
        self.assertEqual(data["total"], 12)
        self.assertEqual(len(data["units"]), 12)
        self.assertEqual([u["specific_part"] for u in data["units"]], [f"车库B-{n}" for n in range(1, 13)])
        self.assertEqual({u["unit_id"] for u in data["units"]}, set(ids))
        # 恰 10 套边界同样全部返回
        phone10 = next_phone()
        for n in range(1, 11):
            self.reg_unit([phone10], building="车库", unit_no="", floor="", room=f"C-{n}", unit_type="PARKING")
        resp10 = self.assert_ok(self.register_raw(phone10), 201)
        self.assertEqual(self.matches(resp10.data["token"]).data["total"], 10)


class ConfirmEndpointTests(PhoneMatchBase):
    def setUp(self):
        super().setUp()
        self.phone = next_phone()
        self.units = [self.reg_unit([self.phone], room=str(301 + i)) for i in range(3)]
        resp = self.register_raw(self.phone)
        self.token, self.uid = resp.data["token"], resp.data["user"]["id"]

    def test_tc_int_944_confirm_success_shape_and_no_name_needed(self):
        """TC-INT-944 / AC-240-01、AC-240-02、AC-241-02：请求只含 unit_ids；200 {succeeded,failed,results}；仅勾选的 2 套生成 Membership。"""
        resp = self.assert_ok(self.confirm(self.token, [self.units[0].id, self.units[1].id]))
        self.assertEqual((resp.data["succeeded"], resp.data["failed"]), (2, 0))
        self.assertEqual(resp.data["results"][0], {"unit_id": self.units[0].id,
                                                   "specific_part": self.units[0].specific_part,
                                                   "ok": True, "role": "HEAD", "code": None})
        self.assertEqual(self.active_units(self.uid), {self.units[0].id, self.units[1].id})
        me = self.api("get", "/me", token=self.token).data["identities"]
        self.assertEqual(me["labels"], ["产权业主"])
        self.assertNotIn("户主", resp.content.decode("utf-8") + json.dumps(me, ensure_ascii=False))

    def test_tc_int_945_confirm_foreign_unit_rejected_whole_batch(self):
        """TC-INT-945 / AC-240-06、REQ-NFUNC-043：含他人手机号的专有部分 → 422 OWNER_NOT_MATCHED，整批无 Membership，响应不含清册信息，仍 PENDING 可再确认。"""
        victim = self.reg_unit([next_phone()], room="888", name="测试清册业主丙")
        resp = self.confirm(self.token, [self.units[0].id, victim.id])
        body = self.assert_error(resp, 422, "OWNER_NOT_MATCHED")
        text = resp.content.decode("utf-8")
        self.assertNotIn(victim.specific_part, text)
        self.assertNotIn("测试清册业主丙", text)
        self.assertEqual(body.get("details", {}), {})
        self.assertEqual(self.active_units(self.uid), set())
        self.assertEqual(self.prompt_status(self.uid), "PENDING")
        self.assert_ok(self.confirm(self.token, [self.units[0].id]))

    def test_tc_int_946_confirm_unknown_unit_same_exit(self):
        """TC-INT-946 / AC-240-06：不存在的 unit_id 与越权同为 422 OWNER_NOT_MATCHED（不可据状态码区分存在性）。"""
        self.assert_error(self.confirm(self.token, [987654321]), 422, "OWNER_NOT_MATCHED")

    def test_tc_int_947_confirm_not_pending_409(self):
        """TC-INT-947 / AC-239-06、AC-241-03：无引导 / 已确认 / 已选"不是" → 409 MATCH_NOT_PENDING，且不产生关系。"""
        _, other_token = self.make_user(phone=next_phone())
        self.assert_error(self.confirm(other_token, [self.units[0].id]), 409, "MATCH_NOT_PENDING")
        self.assert_ok(self.confirm(self.token, [self.units[0].id]))
        self.assert_error(self.confirm(self.token, [self.units[1].id]), 409, "MATCH_NOT_PENDING")
        self.assertEqual(self.active_units(self.uid), {self.units[0].id})
        phone2 = next_phone()
        u2 = self.reg_unit([phone2], room="777")
        token2 = self.register_raw(phone2).data["token"]
        self.assertEqual(self.dismiss(token2).status_code, 204)
        self.assert_error(self.confirm(token2, [u2.id]), 409, "MATCH_NOT_PENDING")

    def test_tc_int_948_confirm_body_validation_400(self):
        """TC-INT-948 / AC-240-03：空列表、非列表、缺字段、字符串/布尔/浮点元素、超 500 个 → 400 INVALID_VALUE，不产生关系。"""
        uid = self.units[0].id
        bad = [{"unit_ids": []}, {"unit_ids": "1"}, {}, {"unit_ids": [str(uid)]}, {"unit_ids": [True]},
               {"unit_ids": [1.5]}, {"unit_ids": list(range(1, 502))}, {"unit_ids": None}]
        for body in bad:
            resp = self.api("post", "/me/registry-matches/confirm", body, token=self.token)
            self.assert_error(resp, 400, "INVALID_VALUE")
        self.assertEqual(self.active_units(self.uid), set())
        self.assertEqual(self.prompt_status(self.uid), "PENDING")

    def test_tc_int_949_confirm_dedups_unit_ids(self):
        """TC-INT-949 / AC-240-02：重复的 unit_id 去重，只处理一次，succeeded==1。"""
        resp = self.assert_ok(self.confirm(self.token, [self.units[0].id, self.units[0].id]))
        self.assertEqual((resp.data["succeeded"], resp.data["failed"], len(resp.data["results"])), (1, 0, 1))

    def test_tc_int_950_confirm_requires_login(self):
        """TC-INT-950 / AC-240-06：未登录 401；dismiss 未登录同样 401。"""
        self.assert_error(self.api("post", "/me/registry-matches/confirm", {"unit_ids": [1]}), 401)
        self.assert_error(self.api("post", "/me/registry-matches/dismiss", {}), 401)

    def test_tc_int_951_confirm_rate_limit_shared_with_certify(self):
        """TC-INT-951 / AC-240-06：确认与手动认证共用 certify:{user.id} 每小时 30 次：先用 29 次手动认证（400/404 均计数），第 30 次确认仍可用，第 31 次 429。"""
        for _ in range(29):
            self.api("post", "/certifications", {"unit_id": 987654321, "name": "测试"}, token=self.token)
        self.assert_ok(self.confirm(self.token, [self.units[0].id]))
        self.assert_error(self.confirm(self.token, [self.units[1].id]), 429, "CODE_RATE_LIMITED")
        self.assert_error(self.api("post", "/certifications", {"unit_id": self.units[1].id, "name": "测试"},
                                   token=self.token), 429, "CODE_RATE_LIMITED")
        self.assertEqual(self.active_units(self.uid), {self.units[0].id})

    def test_tc_int_952_confirm_audit_masked_phone_no_pii(self):
        """TC-INT-952 / AC-240-05：审计 origin_label=清册自动绑定，phone_masked=138-style 脱敏，不含明文手机号与清册姓名；用户端响应也不含。"""
        resp = self.assert_ok(self.confirm(self.token, [self.units[0].id]))
        log = AuditLog.objects.filter(action="CERTIFY_BY_REGISTRY").order_by("id").last()
        self.assertEqual(log.detail["origin_label"], "清册自动绑定")
        self.assertEqual(log.detail["phone_masked"], f"{self.phone[:3]}****{self.phone[-4:]}")
        self.assertNotIn(self.phone, str(log.detail))
        self.assertNotIn(OWNER_NAME, str(log.detail))
        self.assertNotIn(self.phone, resp.content.decode("utf-8"))
        self.assertNotIn(OWNER_NAME, resp.content.decode("utf-8"))

    def test_tc_int_953_confirm_partial_failure_reports_counts(self):
        """TC-INT-953 / AC-240-04：所选 B 已被本人手动认证 → A 成功，B 为 ALREADY_CERTIFIED，响应 succeeded==1/failed==1，无 5xx。"""
        a, b = self.units[0], self.units[1]
        Membership.objects.create(user_id=self.uid, unit=b, role="HEAD", source="CERTIFIED", active_slot=1,
                                  head_slot=1)
        resp = self.assert_ok(self.confirm(self.token, [a.id, b.id]))
        self.assertEqual((resp.data["succeeded"], resp.data["failed"]), (1, 1))
        codes = {r["unit_id"]: r["code"] for r in resp.data["results"]}
        self.assertEqual(codes, {a.id: None, b.id: "ALREADY_CERTIFIED"})
        self.assertEqual(Membership.objects.filter(user_id=self.uid, unit=b, ended_at__isnull=True).count(), 1)

    def test_tc_int_954_other_users_prompt_does_not_authorize(self):
        """TC-INT-954 / AC-240-06：用户 B 即使被拿到 A 的 unit_id 也无法确认（B 无 PENDING → 409；B 有 PENDING 但手机号不同 → 422）。"""
        phone_b = next_phone()
        self.reg_unit([phone_b], room="555")
        token_b = self.register_raw(phone_b).data["token"]
        self.assert_error(self.confirm(token_b, [self.units[0].id]), 422, "OWNER_NOT_MATCHED")
        self.assertFalse(Membership.objects.filter(unit=self.units[0]).exists())


class DismissEndpointTests(PhoneMatchBase):
    def test_tc_int_955_dismiss_204_idempotent_and_never_reprompts(self):
        """TC-INT-955 / AC-239-06：dismiss → 204 无关系；GET pending=false；再次 dismiss 仍 204；再登录不再弹出；可手动认证。"""
        phone = next_phone()
        unit = self.reg_unit([phone], name="测试清册业主丁")
        resp = self.register_raw(phone)
        token, uid = resp.data["token"], resp.data["user"]["id"]
        self.assertEqual(self.dismiss(token).status_code, 204)
        self.assertEqual(self.dismiss(token).status_code, 204)
        self.assertEqual(self.prompt_status(uid), "DISMISSED")
        self.assertEqual(self.matches(token).data, {"pending": False, "total": 0, "units": []})
        self.assertFalse(Membership.objects.filter(user_id=uid).exists())
        RateLimit.objects.all().delete()  # 验证码发送限流：同一目标注册后立即登录需先清
        login = self.assert_ok(self.login_code(phone))
        self.assertEqual(self.matches(login.data["token"]).data["pending"], False)
        manual = self.api("post", "/certifications", {"unit_id": unit.id, "name": "测试清册业主丁"},
                          token=token)
        self.assert_ok(manual, 201)

    def test_tc_int_956_dismiss_without_row_is_noop(self):
        """TC-INT-956 / AC-239-06：无引导行时 dismiss 也返回 204，且不建行。"""
        _, token = self.make_user(phone=next_phone())
        self.assertEqual(self.dismiss(token).status_code, 204)
        self.assertFalse(PhoneMatchPrompt.objects.exists())


class HousingFieldsTests(PhoneMatchBase):
    def test_tc_int_957_housing_units_have_type_and_area(self):
        """TC-INT-957 / AC-232-01、AC-232-02：/me/housing 的 units 含 unit_type_label、area_display；未登记为"未登记"。"""
        from decimal import Decimal
        user, token = self.make_user(phone=next_phone())
        full = self.reg_unit(room="301", unit_type="RESIDENCE", area=Decimal("89.50"))
        empty = self.reg_unit(room="302", unit_type=None, area=None)
        for unit in (full, empty):
            Membership.objects.create(user=user, unit=unit, role="OWNER", source="CERTIFIED", active_slot=1)
        units = {u["unit_id"]: u for u in self.assert_ok(self.api("get", "/me/housing", token=token)).data["units"]}
        self.assertEqual((units[full.id]["unit_type_label"], units[full.id]["area_display"]), ("住宅", "89.50 ㎡"))
        self.assertEqual((units[empty.id]["unit_type_label"], units[empty.id]["area_display"]),
                         ("未登记", "未登记"))
        self.assertEqual(set(units[full.id]), {"unit_id", "specific_part", "role", "role_label", "certified_at",
                                               "residents", "pending_application_count",
                                               "unit_type_label", "area_display"})

    def test_tc_int_958_housing_only_active_relations(self):
        """TC-INT-958 / AC-232-03：已结束的关系不出现在 /me/housing；无有效关系 units==[]、汇总为游客。"""
        user, token = self.make_user(phone=next_phone())
        unit = self.reg_unit(room="303")
        Membership.objects.create(user=user, unit=unit, role="OWNER", source="CERTIFIED", active_slot=None,
                                  ended_at="2026-01-01T00:00:00Z", end_reason="REVOKED")
        data = self.assert_ok(self.api("get", "/me/housing", token=token)).data
        self.assertEqual(data["units"], [])
        self.assertEqual(data["summary"]["label"], "游客")

    def test_tc_int_959_me_identities_units_unchanged(self):
        """TC-INT-959 / REQ-NFUNC-044：/me identities.units 每套含 unit_type/unit_type_label/area/area_display（输出逐字不变）。"""
        from decimal import Decimal
        user, token = self.make_user(phone=next_phone())
        unit = self.reg_unit(room="304", unit_type="APARTMENT", area=Decimal("60"))
        Membership.objects.create(user=user, unit=unit, role="RESIDENT", source="APPLICATION", active_slot=1)
        row = self.api("get", "/me", token=token).data["identities"]["units"][0]
        self.assertEqual((row["unit_type"], row["unit_type_label"], row["area"], row["area_display"]),
                         ("APARTMENT", "公寓", "60.00", "60.00 ㎡"))


class NoRetroactiveAndAbandonedTests(PhoneMatchBase):
    def test_tc_int_966_abandoned_prompt_leaves_no_relation_after_relogin(self):
        """TC-INT-966 / AC-241-03：注册后未在引导页操作（等同关闭浏览器），重新登录——仍无房屋关系，/me/housing 为空（页面据此显示提醒），引导仍可再次确认。"""
        phone = next_phone()
        unit = self.reg_unit([phone])
        reg = self.assert_ok(self.register_raw(phone), 201)
        RateLimit.objects.all().delete()
        login = self.assert_ok(self.login_code(phone))
        housing = self.assert_ok(self.api("get", "/me/housing", token=login.data["token"])).data
        self.assertEqual(housing["units"], [])
        self.assertEqual(housing["summary"]["label"], "游客")
        self.assertFalse(Membership.objects.filter(user_id=reg.data["user"]["id"]).exists())
        self.assertEqual(self.matches(login.data["token"]).data["total"], 1)
        self.assert_ok(self.confirm(login.data["token"], [unit.id]))

    def test_tc_int_967_legacy_silent_bindings_untouched(self):
        """TC-INT-967 / AC-241-04：改动前已静默绑定（source=REGISTRY）的既有用户，登录后身份与房屋关系不变，且不产生引导行（不追溯）。"""
        phone = next_phone()
        unit = self.reg_unit([phone])
        user, _ = self.make_user(phone=phone)
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="REGISTRY", active_slot=1, head_slot=1)
        login = self.assert_ok(self.login_code(phone))
        identities = self.api("get", "/me", token=login.data["token"]).data["identities"]
        self.assertEqual(identities["labels"], ["产权业主"])
        self.assertEqual(self.active_units(user.id), {unit.id})
        self.assertFalse(PhoneMatchPrompt.objects.filter(user=user).exists())
        self.assertEqual(self.matches(login.data["token"]).data, {"pending": False, "total": 0, "units": []})
