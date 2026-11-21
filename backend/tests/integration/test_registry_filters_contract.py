"""PHASE_08 集成测试：后台清册过滤的前后端契约（GR-C-001 条件；画像 P5；M-PM-002）。

解析 frontend/src/shared/api.js 的 registryFilterOptions / registryUnits 与 AdminRegistry.vue 实际传的查询参数、
读取的响应键，逐个对应到后端路由、HTTP 方法、权限与真实过滤行为。
关联 US-189（AC-189-01~05、09）、US-191。
"""
import re
from pathlib import Path

from django.urls import resolve

from apps.core.permissions import IsAdmin
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.registry.views import AdminUnitFilterOptionsView, AdminUnitListView
from tests.integration.test_frontend_contract import WEB_API, extract_calls, resolve_path
from tests.support import ApiTestBase

REPO = Path(__file__).resolve().parents[3]
VUE = REPO / "frontend/src/admin/AdminRegistry.vue"


def vue_load_params() -> set[str]:
    """AdminRegistry.vue 中 admin.registryUnits({...}) 对象字面量的键。"""
    text = VUE.read_text(encoding="utf-8")
    block = re.search(r"admin\.registryUnits\(\{(.*?)\}\)", text, re.S)
    assert block, "未找到 admin.registryUnits({...}) 调用"
    return set(re.findall(r"^\s*(\w+)\s*[:,]", block.group(1), re.M))


class RegistryFilterContractTests(ApiTestBase):
    def test_tc_int_584_api_js_declares_filter_calls_resolving_to_admin_views(self):
        """AC-189 契约：api.js 的 registryUnits、registryFilterOptions 都以 adminHttp GET 调用，并解析到 IsAdmin 视图。"""
        calls = {(c[0], c[1], c[2]) for c in extract_calls(WEB_API)}
        self.assertIn(("admin", "GET", "/admin/registry/units"), calls)
        self.assertIn(("admin", "GET", "/admin/registry/units/filter-options"), calls)
        text = WEB_API.read_text(encoding="utf-8")
        self.assertRegex(text, r"registryFilterOptions:\s*\(\)\s*=>\s*adminHttp\.get\('/admin/registry/units/filter-options'\)")
        listing = resolve_path("/admin/registry/units")
        options = resolve_path("/admin/registry/units/filter-options")
        self.assertIs(listing.func.cls, AdminUnitListView)
        self.assertIs(options.func.cls, AdminUnitFilterOptionsView)  # 未被 <int:unit_id> 路由吞掉
        for match in (listing, options):
            self.assertTrue(hasattr(match.func.cls, "get"))
            self.assertEqual(set(match.func.cls.permission_classes), {IsAdmin})

    def test_tc_int_585_page_query_params_all_accepted_and_effective(self):
        """AC-189-01~05 契约：AdminRegistry.vue 传的每个查询参数名后端都识别并真正过滤（不匹配值 → 0 条）。"""
        params = vue_load_params()
        # B7（ocap_batch_1118，AC-255-01）：新增 sort、order 两个排序参数（非过滤条件，另断言被后端识别）
        self.assertEqual(params, {"page", "page_size", "q", "unit_type", "building", "unit_no", "floor", "room",
                                  "owner_name", "owner_phone", "sort", "order"})
        _, admin_token = self.make_admin()
        unit = RegistryUnit.objects.create(building="1", unit_no="2", floor="9", room="902",
                                           unit_type="RESIDENCE", area="50.00")
        owner = RegistryOwner.objects.create(unit=unit, name="张三丰")
        RegistryPhone.objects.create(unit=unit, owner=owner, phone="13800001234")
        hits = {"q": "902", "unit_type": "RESIDENCE", "building": "1", "unit_no": "2", "floor": "9", "room": "902",
                "owner_name": "张三", "owner_phone": "1234"}
        misses = {"q": "zzz", "unit_type": "SHOP", "building": "9", "unit_no": "9", "floor": "99", "room": "9",
                  "owner_name": "王五", "owner_phone": "9999"}
        for key in hits:
            ok = self.api("get", "/admin/registry/units", {key: hits[key], "page": 1, "page_size": 20}, token=admin_token)
            self.assert_ok(ok)
            self.assertEqual(ok.data["count"], 1, key)
            miss = self.api("get", "/admin/registry/units", {key: misses[key]}, token=admin_token)
            self.assert_ok(miss)
            self.assertEqual(miss.data["count"], 0, f"{key} 参数未被后端当作过滤条件")
        self.assertEqual(set(hits), params - {"page", "page_size", "sort", "order"})
        # sort/order 被后端识别：非法值 400 INVALID_QUERY，合法值 200 且不改变 count
        self.assert_error(self.api("get", "/admin/registry/units", {"sort": "zzz"}, token=admin_token), 400, "INVALID_QUERY")
        self.assert_error(self.api("get", "/admin/registry/units", {"sort": "floor", "order": "up"}, token=admin_token), 400, "INVALID_QUERY")
        for sort in ("building", "unit_no", "floor", "room"):
            ok = self.api("get", "/admin/registry/units", {"sort": sort, "order": "desc"}, token=admin_token)
            self.assert_ok(ok)
            self.assertEqual(ok.data["count"], 1)

    def test_tc_int_586_page_reads_only_existing_response_keys(self):
        """AC-189 契约：页面读取的 data.options / data.results / data.count 均为后端真实响应键。"""
        text = VUE.read_text(encoding="utf-8")
        self.assertIn("data.options", text)
        self.assertIn("admin.unitOptions(", text)
        self.assertNotIn("data.buildings", text)
        self.assertNotIn("data.unit_nos", text)
        _, admin_token = self.make_admin()
        RegistryUnit.objects.create(building="1", unit_no="1", floor="1", room="1")
        options = self.api("get", "/admin/registry/unit-options", token=admin_token)
        self.assertTrue({"level", "skipped", "has_empty", "options"} <= set(options.data))
        listing = self.api("get", "/admin/registry/units", token=admin_token)
        self.assertTrue({"results", "count"} <= set(listing.data))
        self.assertRegex(text, r"data\.results")
        self.assertRegex(text, r"data\.count")
        row_keys = set(listing.data["results"][0])
        used = set(re.findall(r'prop="(\w+)"', text)) | set(re.findall(r"row\.(\w+)", text))
        self.assertEqual(sorted(k for k in used if k not in row_keys and k not in {"owners", "unit_type_label"}), [])

    def test_tc_int_587_floor_filter_cascades_from_building_and_unit(self):
        """REQ-FUNC-281 契约：页面传 floor 过滤参数，楼层下拉随楼栋/单元级联；占位文字不含 select。"""
        text = VUE.read_text(encoding="utf-8")
        self.assertIn("floor", vue_load_params())
        header = text.split("<el-table", 1)[0]
        self.assertRegex(header, r'placeholder="楼层')
        self.assertRegex(text, r"disabled=\"!filters\.building\"")
        self.assertRegex(text, r"disabled=\"!filters\.unit_no\"")
        self.assertIsNone(re.search(r"select", re.sub(r"el-select|v-model|@change|filterable", "", header),
                                    re.I), "过滤区可见属性文字含英文 select")
