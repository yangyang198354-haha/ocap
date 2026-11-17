"""PHASE_09 E2E（后端多步旅程，替代口径之一；ocap_identity_property）：注册/绑定手机号 → 引导 → 确认/不是 → 身份与房屋 → 同住人申请与审批。

关联 US-232~243；全部走真实 HTTP 路由 + ORM；合成手机号与姓名（C-73）。TC-E2E-900 起。
"""
from decimal import Decimal

from apps.core.models import RateLimit
from apps.integrations.fakes import FakeWeChatClient
from apps.integrations.wechat import set_wechat_client
from apps.residency.models import Membership
from tests.phone_match_support import OWNER_NAME, PhoneMatchBase
from tests.support import next_phone


class RegisterConfirmOwnerJourneyTests(PhoneMatchBase):
    def test_tc_e2e_900_register_confirm_housing_and_review_cards(self):
        """TC-E2E-900 / US-239、US-240、US-241、US-232、US-234、US-235：注册 → 引导列出 2 套 → 只确认 1 套 → 房屋明细含类型与面积 →
        同住人申请 → 产权业主看到待审批并通过 → 同住人出现在房屋名下；未勾选的那套无关系；注册后到确认前身份仍为游客。"""
        phone = next_phone()
        a = self.reg_unit([phone], room="901", unit_type="RESIDENCE", area=Decimal("89.50"))
        b = self.reg_unit([phone], room="902", unit_type="APARTMENT", area=None)
        reg = self.assert_ok(self.register_raw(phone), 201)
        token, uid = reg.data["token"], reg.data["user"]["id"]
        self.assertEqual(reg.data["registry_match"], {"pending": True, "count": 2})
        self.assertEqual(self.api("get", "/me", token=token).data["identities"]["labels"], ["游客"])
        listing = self.assert_ok(self.matches(token)).data
        self.assertEqual([u["unit_type_label"] for u in listing["units"]], ["住宅", "公寓"])

        done = self.assert_ok(self.confirm(token, [a.id]))
        self.assertEqual((done.data["succeeded"], done.data["failed"]), (1, 0))
        self.assertEqual(self.active_units(uid), {a.id})
        self.assertEqual(self.matches(token).data["pending"], False)
        housing = self.assert_ok(self.api("get", "/me/housing", token=token)).data
        self.assertEqual(housing["summary"]["label"], "产权业主")
        self.assertEqual([(u["specific_part"], u["unit_type_label"], u["area_display"], u["role_label"])
                          for u in housing["units"]], [(a.specific_part, "住宅", "89.50 ㎡", "产权业主")])

        applicant, applicant_token = self.make_user()
        created = self.assert_ok(self.api("post", "/resident-applications", {"unit_id": a.id},
                                          token=applicant_token), 201)
        self.assertEqual(self.api("get", "/me/housing", token=token).data["pending_review_count"], 1)
        review = self.assert_ok(self.api("get", "/resident-applications/to-review", token=token)).data
        self.assertEqual([r["id"] for r in review], [created.data["id"]])
        self.assert_ok(self.api("post", f"/resident-applications/{created.data['id']}/decision",
                                {"decision": "APPROVE"}, token=token))
        housing = self.api("get", "/me/housing", token=token).data
        self.assertEqual([r["user_id"] for r in housing["units"][0]["residents"]], [applicant.id])
        self.assertEqual(housing["pending_review_count"], 0)
        self.assertEqual(self.api("get", "/resident-applications/to-review", token=token).data, [])
        self.assertFalse(Membership.objects.filter(user_id=uid, unit=b).exists())

    def test_tc_e2e_901_non_owner_sees_no_review_and_cannot_decide(self):
        """TC-E2E-901 / US-234（AC-234-04、AC-234-05）、REQ-NFUNC-042：游客与同住人看不到待审批（空列表、角标 0）；对他人专有部分的申请审批 403
        且状态保持 PENDING；两位产权业主都能看到并审批同一申请。"""
        owner1, owner1_token, unit1 = self.make_owner()
        owner2, owner2_token, unit2 = self.make_owner()
        applicant, applicant_token = self.make_user()
        app1 = self.assert_ok(self.api("post", "/resident-applications", {"unit_id": unit1.id},
                                       token=applicant_token), 201).data["id"]
        app2 = self.assert_ok(self.api("post", "/resident-applications", {"unit_id": unit2.id},
                                       token=applicant_token), 201).data["id"]
        guest, guest_token = self.make_user()
        resident, resident_token = self.make_resident(unit1)
        for token in (guest_token, resident_token):
            self.assertEqual(self.api("get", "/resident-applications/to-review", token=token).data, [])
            self.assertEqual(self.api("get", "/me/housing", token=token).data["pending_review_count"], 0)
            self.assert_error(self.api("post", f"/resident-applications/{app1}/decision",
                                       {"decision": "APPROVE"}, token=token), 403, "FORBIDDEN")
        # owner1 不是 unit2 的产权业主：列表不含 app2，直接审批 403，状态不变
        self.assertEqual([r["id"] for r in self.api("get", "/resident-applications/to-review",
                                                    token=owner1_token).data], [app1])
        self.assert_error(self.api("post", f"/resident-applications/{app2}/decision",
                                   {"decision": "APPROVE"}, token=owner1_token), 403, "FORBIDDEN")
        from apps.residency.models import ResidentApplication
        self.assertEqual(ResidentApplication.objects.get(id=app2).status, "PENDING")
        self.assertFalse(Membership.objects.filter(user=applicant, unit=unit2).exists())
        # 同一专有部分的第二位产权业主同样可见可审批
        second = self.make_owner(unit=unit1, role="OWNER")
        self.assertEqual([r["id"] for r in self.api("get", "/resident-applications/to-review",
                                                    token=second[1]).data], [app1])

    def test_tc_e2e_902_owner_with_two_units_sees_both_applications(self):
        """TC-E2E-902 / US-234（AC-234-06）、US-235（AC-235-01）：产权业主两套房各有 1 条待审批 → 列表恰 2 条，角标数 2。"""
        owner, token, unit1 = self.make_owner()
        unit2 = self.reg_unit(room="777")
        Membership.objects.create(user=owner, unit=unit2, role="HEAD", source="CERTIFIED", active_slot=1,
                                  head_slot=1)
        for unit in (unit1, unit2):
            _, applicant_token = self.make_user()
            self.assert_ok(self.api("post", "/resident-applications", {"unit_id": unit.id},
                                    token=applicant_token), 201)
        review = self.api("get", "/resident-applications/to-review", token=token).data
        self.assertEqual({r["unit"]["unit_id"] for r in review}, {unit1.id, unit2.id})
        self.assertEqual(len(review), 2)
        self.assertEqual(self.api("get", "/me/housing", token=token).data["pending_review_count"], 2)


class DismissAndWechatJourneyTests(PhoneMatchBase):
    def setUp(self):
        super().setUp()
        set_wechat_client(FakeWeChatClient())
        self.addCleanup(set_wechat_client, None)

    def test_tc_e2e_903_wechat_bind_dismiss_then_manual_certify(self):
        """TC-E2E-903 / US-239（AC-239-05、AC-239-06）、US-241（AC-241-03）、US-238：微信用户绑定清册手机号 → 引导 → 选"不是" → 无关系、
        再登录不再引导 → 仍可用姓名手动认证成功（认证规则不变，C-71）。"""
        phone = next_phone()
        unit = self.reg_unit([phone], name=OWNER_NAME)
        wx = self.assert_ok(self.api("post", "/auth/wechat/miniapp", {"code": "wx-ip-e2e-903"}))
        token, uid = wx.data["token"], wx.data["user"]["id"]
        code = self.request_me_code(token, "BIND_PHONE", target=phone)
        bound = self.assert_ok(self.api("post", "/me/phone/bind", {"phone": phone, "code": code}, token=token))
        self.assertEqual(bound.data["registry_match"], {"pending": True, "count": 1})
        self.assertEqual(self.dismiss(token).status_code, 204)
        self.assertFalse(Membership.objects.filter(user_id=uid).exists())
        self.assertEqual(self.api("get", "/me/housing", token=token).data["units"], [])
        RateLimit.objects.all().delete()
        relogin = self.assert_ok(self.login_code(phone))
        self.assertEqual(self.matches(relogin.data["token"]).data["pending"], False)
        manual = self.api("post", "/certifications", {"unit_id": unit.id, "name": OWNER_NAME}, token=token)
        self.assert_ok(manual, 201)
        self.assertEqual(self.api("get", "/me/housing", token=token).data["summary"]["label"], "产权业主")

    def test_tc_e2e_904_resident_application_rules_without_name(self):
        """TC-E2E-904 / US-243（AC-243-01、AC-243-04、AC-243-05、AC-243-06）：申请不含姓名；无产权业主 409 UNIT_HAS_NO_OWNER；
        已是产权业主 409 ALREADY_CERTIFIED；重复提交 409 APPLICATION_PENDING 且只有 1 条待审；申请出现在"我的申请"并进入产权业主待审批。"""
        _, owner_token, unit = self.make_owner()
        empty_unit = self.reg_unit(room="404")
        user, token = self.make_user()
        self.assert_error(self.api("post", "/resident-applications", {"unit_id": empty_unit.id}, token=token),
                          409, "UNIT_HAS_NO_OWNER")
        self.assert_error(self.api("post", "/resident-applications", {"unit_id": unit.id}, token=owner_token),
                          409, "ALREADY_CERTIFIED")
        created = self.assert_ok(self.api("post", "/resident-applications", {"unit_id": unit.id}, token=token),
                                 201)
        self.assertEqual(created.data["status"], "PENDING")
        self.assert_error(self.api("post", "/resident-applications", {"unit_id": unit.id}, token=token),
                          409, "APPLICATION_PENDING")
        mine = self.api("get", "/resident-applications/mine", token=token).data
        self.assertEqual([(m["unit"]["unit_id"], m["status"]) for m in mine], [(unit.id, "PENDING")])
        review = self.api("get", "/resident-applications/to-review", token=owner_token).data
        self.assertEqual([r["id"] for r in review], [created.data["id"]])
