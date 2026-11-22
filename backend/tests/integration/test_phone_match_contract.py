"""PHASE_08 集成测试（ocap_identity_property）：新增三个 registry-matches 接口的前后端契约（画像 P5、P6；M-PM-002）。

解析 frontend/src/shared/api.js 与 miniprogram/utils/api.js 的调用（复用 test_frontend_contract 的解析器），
逐个 resolve 到后端路由并核对方法/权限；再对引导面板读取的字段与真实响应做集合包含核对。
只读前端源码，不改前端。TC-INT-960 起。
"""
import re

from apps.core.permissions import IsMember
from tests.integration.test_frontend_contract import (  # 仅导入函数与常量，避免重复收集其中的 TestCase
    MINI_API, REPO, WEB_API, extract_calls, resolve_path,
)
from tests.phone_match_support import PhoneMatchBase
from tests.support import next_phone

NEW_CALLS = {("member", "GET", "/me/registry-matches"),
             ("member", "POST", "/me/registry-matches/confirm"),
             ("member", "POST", "/me/registry-matches/dismiss")}


def src(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


class RegistryMatchRouteContractTests(PhoneMatchBase):
    def _assert_new_calls(self, source, label):
        calls = extract_calls(source)
        found = {c[:3] for c in calls} & NEW_CALLS
        self.assertEqual(found, NEW_CALLS, f"{label}：新增三个 registry-matches 调用未被契约解析器覆盖")
        for client, method, template, where in calls:
            if (client, method, template) not in NEW_CALLS:
                continue
            match = resolve_path(template)  # 无法解析则抛 Resolver404 → 测试失败
            view_cls = match.func.cls
            self.assertTrue(hasattr(view_cls, method.lower()), f"{where} 视图不支持 {method}")
            self.assertEqual(list(view_cls.permission_classes), [IsMember], where)
            self.assertNotIn("?", template, "契约正则要求字面量路径且不带 ?")

    def test_tc_int_960_web_api_new_calls_resolve(self):
        """TC-INT-960 / REQ-NFUNC-044、AC-239-01：Web api.js 三个新增调用被解析且各自 resolve 到 IsMember 视图并支持对应方法。"""
        self._assert_new_calls(WEB_API, "Web api.js")

    def test_tc_int_961_miniprogram_api_new_calls_resolve(self):
        """TC-INT-961 / REQ-NFUNC-044、AC-242-04：小程序 api.js 同三个调用同样被解析并 resolve。"""
        self._assert_new_calls(MINI_API, "miniprogram api.js")

    def test_tc_int_962_confirm_payload_key_matches_backend(self):
        """TC-INT-962 / AC-240-01：两端 confirm 调用提交的字段名为 unit_ids（后端读取同名键），不提交姓名/手机号。"""
        for rel in ("frontend/src/shared/api.js", "miniprogram/utils/api.js"):
            text = src(rel)
            line = next(l for l in text.splitlines() if "registry-matches/confirm" in l)
            self.assertIn("unit_ids", line, rel)
            self.assertNotRegex(line, r"\b(name|phone)\b", rel)
        phone = next_phone()
        unit = self.reg_unit([phone])
        token = self.register_raw(phone).data["token"]
        self.assert_ok(self.api("post", "/me/registry-matches/confirm", {"unit_ids": [unit.id]}, token=token))

    def test_tc_int_963_panel_reads_subset_of_response_fields(self):
        """TC-INT-963 / AC-239-01、AC-240-04：Web 面板与小程序卡片读取 pending/units/unit_id/specific_part/unit_type_label、succeeded/failed，
        均是真实响应键的子集；循环变量 match 只读这三个字段；不读取清册姓名/手机号类字段。"""
        phone = next_phone()
        unit = self.reg_unit([phone])
        token = self.register_raw(phone).data["token"]
        listing = self.assert_ok(self.matches(token)).data
        item_keys = set(listing["units"][0])
        top_keys = set(listing)
        confirmed = self.assert_ok(self.confirm(token, [unit.id])).data
        for rel in ("frontend/src/portal/parts/RegistryMatchPanel.vue", "miniprogram/components/RegistryMatchCard.vue"):
            text = src(rel)
            reads_match = set(re.findall(r"\bmatch\.(\w+)", text))
            self.assertTrue(reads_match, rel)
            self.assertLessEqual(reads_match, item_keys, rel)
            reads_data = set(re.findall(r"\bdata\??\.(\w+)", text))
            self.assertLessEqual(reads_data, top_keys | set(confirmed), rel)
            self.assertTrue({"pending", "units"} <= reads_data and {"succeeded", "failed"} <= reads_data, rel)
            self.assertNotRegex(text, r"\.(owner_name|name|phone|owners)\b", rel)

    def test_tc_int_964_register_and_bind_response_field_registry_match(self):
        """TC-INT-964 / AC-239-01、AC-241-01：Register.vue / MePhone.vue / 小程序 phone 页读取 registry_match.pending，真实注册响应含该字段；
        前端不再读取 auto_bound（不再展示"自动认证"提示）。"""
        phone = next_phone()
        self.reg_unit([phone])
        reg = self.assert_ok(self.register_raw(phone), 201)
        self.assertIn("registry_match", reg.data)
        self.assertLessEqual({"pending", "count"}, set(reg.data["registry_match"]))
        for rel in ("frontend/src/portal/Register.vue", "frontend/src/portal/me/MePhone.vue",
                    "miniprogram/pages/phone/index.vue"):
            text = src(rel)
            self.assertRegex(text, r"registry_match\??\.pending", rel)
            self.assertNotIn("auto_bound", text, rel)
            self.assertNotIn("自动认证", text, rel)

    def test_tc_int_965_housing_page_reads_type_and_area_fields(self):
        """TC-INT-965 / AC-232-01：Web 身份页与小程序"我的房屋"页读取的 unit_type_label/area_display 是 /me/housing 真实键。"""
        from decimal import Decimal
        from apps.residency.models import Membership
        user, token = self.make_user(phone=next_phone())
        unit = self.reg_unit(unit_type="RESIDENCE", area=Decimal("89.5"))
        Membership.objects.create(user=user, unit=unit, role="OWNER", source="CERTIFIED", active_slot=1)
        keys = set(self.assert_ok(self.api("get", "/me/housing", token=token)).data["units"][0])
        # MOD-179（ocap_navigation_ia）：小程序“我的房屋”页拆为宿主 + 三个面板，字段读取在 IdentityPane 中
        mini_paths = [
            "miniprogram/pages/units/index.vue",
            "miniprogram/pages/units/components/IdentityPane.vue",
            "miniprogram/pages/units/components/AppealPane.vue",
            "miniprogram/pages/units/components/ResidentPane.vue",
        ]
        sources = [("frontend/src/portal/units/UnitsIdentity.vue", src("frontend/src/portal/units/UnitsIdentity.vue"))]
        sources.append(("miniprogram/pages/units/**", "\n".join(src(rel) for rel in mini_paths)))
        for rel, text in sources:
            self.assertRegex(text, r"unit\.unit_type_label", rel)
            self.assertRegex(text, r"unit\.area_display", rel)
            self.assertLessEqual({"unit_type_label", "area_display"}, keys, rel)
