"""PHASE_08 集成测试：逐级选房选项排序（MOD-105，IFC-288）+ Web/小程序一致（客户端无排序）。

关联 US-183（AC-183-01~06）、US-184（AC-184-01~03）、US-185（AC-185-01~03）、US-186（AC-186-01~03）。
真实 HTTP + 真实鉴权头 + SQLite 测试库；全部合成数据。
"""
import re
from pathlib import Path

from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from tests.support import ApiTestBase

REPO = Path(__file__).resolve().parents[3]


def mk(building, unit_no, floor, room, unit_type="RESIDENCE", area="50.00"):
    return RegistryUnit.objects.create(building=building, unit_no=unit_no, floor=floor, room=room,
                                       unit_type=unit_type, area=area)


class RegistrySortOptionsTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        _, self.token = self.make_user()

    def options(self, **params):
        resp = self.api("get", "/units/options", params, token=self.token)
        self.assert_ok(resp)
        return resp.data

    def values(self, **params):
        return [o["value"] for o in self.options(**params)["options"]]

    def test_tc_int_550_buildings_numeric_order(self):
        """AC-183-01：楼栋 1、2、10、11 → [1,2,10,11]。"""
        for b in ("11", "2", "10", "1"):
            mk(b, "1", "1", "101")
        data = self.options()
        self.assertEqual(data["level"], "building")
        self.assertEqual([o["value"] for o in data["options"]], ["1", "2", "10", "11"])

    def test_tc_int_551_building_suffix_forms(self):
        """AC-183-01：'1栋/2栋/10栋' 后缀写法按数值排序，且全部保留。"""
        for b in ("10栋", "2栋", "1栋"):
            mk(b, "1", "1", "101")
        self.assertEqual(self.values(), ["1栋", "2栋", "10栋"])

    def test_tc_int_552_units_and_rooms_numeric_order(self):
        """AC-183-02：单元 1、2、10；户号 101、902、1001。"""
        for unit_no in ("10", "2", "1"):
            mk("1", unit_no, "9", "902")
        self.assertEqual(self.values(building="1"), ["1", "2", "10"])
        for room in ("1001", "902", "101"):
            mk("5", "1", "9", room)
        data = self.options(building="5", unit_no="1", floor="9")
        self.assertEqual(data["level"], "room")
        self.assertEqual([o["value"] for o in data["options"]], ["101", "902", "1001"])

    def test_tc_int_553_floors_negative_first_not_regressed(self):
        """AC-183-03：楼层 -1、1、2、10 → [-1,1,2,10]。"""
        for f in ("10", "2", "1", "-1"):
            mk("1", "1", f, "1")
        self.assertEqual(self.values(building="1", unit_no="1"), ["-1", "1", "2", "10"])

    def test_tc_int_554_non_numeric_rooms_no_loss_no_duplicate(self):
        """AC-183-04：户号 A2、A10、5 → 5 在前，其后 A2、A10；无报错、无丢失、无重复。"""
        for room in ("A10", "A2", "5"):
            mk("3", "1", "1", room)
        data = self.options(building="3", unit_no="1", floor="1")
        self.assertEqual([o["value"] for o in data["options"]], ["5", "A2", "A10"])
        self.assertEqual(len({o["unit_id"] for o in data["options"]}), 3)

    def test_tc_int_555_empty_level_skipped(self):
        """AC-183-05：车位无单元 → 单元级被跳过（skipped=[unit_no]），下一级为楼层，顺序规则不变。"""
        for f in ("2", "1"):
            mk("6", "", f, "1", unit_type="PARKING")
        data = self.options(building="6")
        self.assertEqual(data["skipped"], ["unit_no"])
        self.assertEqual(data["level"], "floor")
        self.assertEqual([o["value"] for o in data["options"]], ["1", "2"])
        self.assertNotIn("", [o["value"] for o in data["options"]])

    def test_tc_int_556_chinese_negative_floors(self):
        """AC-183-06：负二、负一、-1、1、2 → 负二在最前，负一与-1相邻且都在 1、2 之前，全部出现。"""
        for f in ("2", "-1", "1", "负一", "负二"):
            mk("7", "1", f, "1")
        values = self.values(building="7", unit_no="1")
        self.assertEqual(values[0], "负二")
        self.assertEqual(set(values[1:3]), {"负一", "-1"})
        self.assertEqual(values[3:], ["1", "2"])
        self.assertEqual(len(values), 5)

    def test_tc_int_557_underground_building_listed_last(self):
        """AC-184-03 / AC-185-01：楼栋 1、10、地下车位 → 顺序 [1,10,地下车位]。"""
        for b in ("地下车位", "10", "1"):
            mk(b, "", "负一" if b == "地下车位" else "1", "1", unit_type="PARKING" if b == "地下车位" else "RESIDENCE")
        self.assertEqual(self.values(), ["1", "10", "地下车位"])

    def test_tc_int_558_no_underground_records_option_absent(self):
        """AC-185-03：无地下车位记录时不出现该选项，其余不受影响。"""
        for b in ("2", "1"):
            mk(b, "1", "1", "1")
        values = self.values()
        self.assertEqual(values, ["1", "2"])
        self.assertNotIn("地下车位", values)

    def test_tc_int_559_underground_flow_floors_then_rooms(self):
        """AC-185-02 / AC-186-01：选地下车位 → 单元级被跳过，楼层 [负二, 负一]，选定后车位号全部显示且类型为车位。"""
        mk("1", "1", "1", "101")
        for room, f in (("2", "负二"), ("1", "负一"), ("3", "负一")):
            mk("地下车位", "", f, room, unit_type="PARKING", area="12.00")
        data = self.options(building="地下车位")
        self.assertEqual(data["skipped"], ["unit_no"])
        self.assertEqual(data["level"], "floor")
        self.assertEqual([o["value"] for o in data["options"]], ["负二", "负一"])
        rooms = self.options(building="地下车位", unit_no="", floor="负一")
        self.assertEqual(rooms["level"], "room")
        self.assertEqual([o["value"] for o in rooms["options"]], ["1", "3"])
        self.assertTrue(all(o["unit_type"] == "PARKING" and o["unit_type_label"] == "车位"
                            for o in rooms["options"]))
        # AC-185-02：1 栋下不再出现负层
        self.assertEqual(self.values(building="1", unit_no="1"), ["1"])

    def test_tc_int_560_underground_certification_and_unregistered(self):
        """AC-186-02：手机号在清册该车位名下 → 认证成功并出现在 /me/housing；不在清册 → 422 PHONE_NOT_IN_REGISTRY。"""
        unit = mk("地下车位", "", "负一", "1", unit_type="PARKING", area="12.00")
        owner_user, owner_token = self.make_user()
        owner = RegistryOwner.objects.create(unit=unit, name="测试车主")
        RegistryPhone.objects.create(unit=unit, owner=owner, phone=owner_user.phone)
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=owner_token)
        self.assert_ok(resp, 201)
        housing = self.api("get", "/me/housing", token=owner_token).data["units"]
        self.assertEqual([u["unit_id"] for u in housing], [unit.id])
        self.assertEqual(housing[0]["specific_part"], unit.specific_part)
        _, stranger_token = self.make_user()
        self.assert_error(self.api("post", "/certifications", {"unit_id": unit.id}, token=stranger_token),
                          422, "PHONE_NOT_IN_REGISTRY")

    def test_tc_int_561_switch_building_reloads_levels(self):
        """AC-186-03：先选地下车位再改选 2 栋 → 下一级按 2 栋重新加载，不含负层车位。"""
        mk("地下车位", "", "负一", "1", unit_type="PARKING")
        mk("2", "1", "1", "101")
        mk("2", "2", "1", "101")
        self.assertEqual(self.options(building="地下车位")["level"], "floor")
        data = self.options(building="2")
        self.assertEqual(data["level"], "unit_no")
        self.assertEqual([o["value"] for o in data["options"]], ["1", "2"])
        self.assertEqual(data["skipped"], [])

    def test_tc_int_562_validation_unchanged(self):
        """IFC-288：缺上级参数 / 过长仍为 400 INVALID_QUERY（输入校验不变）。"""
        self.assert_error(self.api("get", "/units/options", {"unit_no": "1"}, token=self.token), 400, "INVALID_QUERY")
        self.assert_error(self.api("get", "/units/options", {"building": "x" * 33}, token=self.token),
                          400, "INVALID_QUERY")

    def test_tc_int_563_web_and_miniprogram_share_one_server_order(self):
        """AC-184-01/02：两端调用同一路径 /units/options，且客户端组件不做任何重排序（顺序只来自服务端）。"""
        web_api = (REPO / "frontend/src/shared/api.js").read_text(encoding="utf-8")
        mini_api = (REPO / "miniprogram/utils/api.js").read_text(encoding="utf-8")
        self.assertRegex(web_api, r"get\('/units/options'")
        self.assertRegex(mini_api, r"get\('/units/options'")
        sources = [REPO / "frontend/src/portal/parts/UnitCascader.vue",
                   REPO / "miniprogram/components/UnitPicker.vue"]
        for path in sources:
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"\.sort\(|\.toSorted\(|localeCompare|sorted\(", text),
                              f"{path.name} 出现客户端排序")
        # 服务端新增楼栋 3 后，两端使用的同一接口顺序为 2、3、10
        for b in ("10", "2", "3"):
            mk(b, "1", "1", "1")
        self.assertEqual(self.values(), ["2", "3", "10"])
