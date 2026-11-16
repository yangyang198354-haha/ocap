"""PHASE_08 集成测试：后台业主清册过滤 API（MOD-107，IFC-291/292）。

关联 US-189（AC-189-01~09）、US-190（AC-190-01~03）；CR-001（过滤参数 strip）。
真实管理员令牌与普通用户令牌，合成数据（C-55）。
"""
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from tests.support import ApiTestBase

URL = "/admin/registry/units"


def unit(building, unit_no, floor, room, unit_type="RESIDENCE"):
    return RegistryUnit.objects.create(building=building, unit_no=unit_no, floor=floor, room=room,
                                       unit_type=unit_type, area="50.00" if unit_type else None)


def owner(u, name, phones=()):
    o = RegistryOwner.objects.create(unit=u, name=name)
    for phone in phones:
        RegistryPhone.objects.create(unit=u, owner=o, phone=phone)
    return o


class AdminRegistryFilterTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        _, self.admin_token = self.make_admin()
        self.b1 = unit("1", "2", "9", "902")
        self.b10 = unit("10", "2", "9", "902")
        self.b1_other = unit("1", "1", "1", "101")
        self.shop = unit("2", "1", "1", "1", unit_type="SHOP")
        self.park = unit("地下车位", "", "负一", "7", unit_type="PARKING")
        self.unset = unit("3", "1", "1", "1", unit_type=None)
        owner(self.b1, "张三丰", ["13800001234"])
        owner(self.b10, "李四光", ["13900005678"])

    def get(self, **params):
        resp = self.api("get", URL, params, token=self.admin_token)
        self.assert_ok(resp)
        return resp.data

    def ids(self, **params):
        return {r["id"] for r in self.get(**params)["results"]}

    def test_tc_int_569_building_exact_match(self):
        """AC-189-01：楼栋='1' 精确匹配，不含 '10'，count 等于符合条数。"""
        data = self.get(building="1")
        self.assertEqual({r["id"] for r in data["results"]}, {self.b1.id, self.b1_other.id})
        self.assertEqual(data["count"], 2)
        self.assertNotIn(self.b10.id, {r["id"] for r in data["results"]})

    def test_tc_int_570_unit_and_room_combined(self):
        """AC-189-02：单元=2 且 户号=902 → 仅同时满足者（楼栋 1 与 10 两条）；再叠加楼栋 → 1 条。"""
        self.assertEqual(self.ids(unit_no="2", room="902"), {self.b1.id, self.b10.id})
        self.assertEqual(self.ids(unit_no="2", room="902", building="10"), {self.b10.id})

    def test_tc_int_571_type_filter_and_unset(self):
        """AC-189-03：类型=PARKING 只含车位；UNSET 只含未登记类型。"""
        self.assertEqual(self.ids(unit_type="PARKING"), {self.park.id})
        self.assertEqual(self.ids(unit_type="UNSET"), {self.unset.id})

    def test_tc_int_572_owner_name_contains(self):
        """AC-189-04：姓名过滤'张三'命中'张三丰'；'李四'不命中张三丰。"""
        self.assertEqual(self.ids(owner_name="张三"), {self.b1.id})
        self.assertNotIn(self.b1.id, self.ids(owner_name="李四"))

    def test_tc_int_573_owner_phone_contains_full_phone_shown(self):
        """AC-189-05：电话过滤'1234'命中；响应显示完整手机号；'9999'不命中。"""
        data = self.get(owner_phone="1234")
        self.assertEqual([r["id"] for r in data["results"]], [self.b1.id])
        self.assertEqual(data["results"][0]["owners"][0]["phones"], ["13800001234"])
        self.assertEqual(self.ids(owner_phone="9999"), set())

    def test_tc_int_574_no_match_empty_result(self):
        """AC-189-06：楼栋=1 且 类型=PARKING 无同时满足 → 200，count=0，results=[]。"""
        data = self.get(building="1", unit_type="PARKING")
        self.assertEqual((data["count"], data["results"]), (0, []))

    def test_tc_int_575_non_admin_forbidden_anonymous_unauthorized(self):
        """AC-189-07：普通登录用户 403、匿名 401，均不返回清册数据；filter-options 同样。"""
        _, user_token = self.make_user()
        for path in (URL, URL + "/filter-options"):
            body = self.assert_error(self.api("get", path, {"building": "1"}, token=user_token), 403)
            self.assertNotIn("results", body)
            body = self.assert_error(self.api("get", path, {"owner_name": "张"}), 401)
            self.assertNotIn("results", body)

    def test_tc_int_576_clearing_filters_restores_all(self):
        """AC-189-08：空串参数（unit_type 不传，前端对空值本就不传）等同无过滤，总数与不带参数时相同（6）。"""
        total = self.get()["count"]
        self.assertEqual(total, 6)
        cleared = self.get(building="", unit_no="", room="", owner_name="", owner_phone="", q="")
        self.assertEqual(cleared["count"], total)

    def test_tc_int_577_no_duplicate_rows_with_multiple_matching_owners(self):
        """IFC-291：多个业主/手机号同时命中，Exists 子查询不产生重复行，count 不虚高。"""
        owner(self.b1, "张三二", ["13800001235", "13800001236"])
        data = self.get(owner_name="张三", owner_phone="1234")
        self.assertEqual([r["id"] for r in data["results"]], [self.b1.id])
        data = self.get(owner_phone="138000012")
        self.assertEqual((data["count"], len(data["results"])), (1, 1))

    def test_tc_int_578_identifier_search_kept_and_combined(self):
        """AC-190-01/02：q='902' 命中两条；叠加类型住宅仍两条；叠加 SHOP → 空（类型不符不出现）。"""
        self.assertEqual(self.ids(q="902"), {self.b1.id, self.b10.id})
        self.assertEqual(self.ids(q="902", unit_type="RESIDENCE"), {self.b1.id, self.b10.id})
        self.assertEqual(self.ids(q="902", unit_type="SHOP"), set())
        self.assertEqual(self.ids(q="902", building="10"), {self.b10.id})

    def test_tc_int_579_q_too_long_message_unchanged(self):
        """AC-190-03：q 超 64 字符仍 400 INVALID_QUERY，文案不变，不返回数据。"""
        body = self.assert_error(self.api("get", URL, {"q": "9" * 65}, token=self.admin_token), 400, "INVALID_QUERY")
        self.assertIn("q 过长（最多 64 字符）", body["message"])
        self.assertEqual(self.ids(q="9" * 64), set())

    def test_tc_int_580_invalid_parameters_400(self):
        """IFC-291：building/unit_no/room >32、owner_name >64、owner_phone 非数字或 >11 位 → 400 INVALID_QUERY。"""
        for params in ({"building": "x" * 33}, {"unit_no": "x" * 33}, {"room": "x" * 33},
                       {"owner_name": "x" * 65}, {"owner_phone": "12ab"}, {"owner_phone": "1" * 12}):
            self.assert_error(self.api("get", URL, params, token=self.admin_token), 400, "INVALID_QUERY")

    def test_tc_int_581_cr001_params_stripped_before_matching(self):
        """CR-001：首尾空白被 strip（' 1 ' 等同 '1'）；纯空白视为未设置而非 400；strip 后才校验长度。"""
        self.assertEqual(self.ids(building=" 1 "), {self.b1.id, self.b1_other.id})
        self.assertEqual(self.get(building="   ")["count"], 6)
        self.assertEqual(self.get(owner_name="  ")["count"], 6)
        self.assertEqual(self.get(owner_phone="  ")["count"], 6)
        self.assertEqual(self.ids(owner_name=" 张三 "), {self.b1.id})
        self.assertEqual(self.ids(owner_phone=" 1234 "), {self.b1.id})
        self.assertEqual(self.get(room=" " + "9" * 32 + " ")["count"], 0)  # strip 后恰 32 字符，不报错

    def test_tc_int_582_pagination_count_is_filtered_total(self):
        """AC-189-01：分页下 count 为过滤后总数，而非本页条数。"""
        for i in range(25):
            unit("8", "1", "1", str(100 + i))
        data = self.get(building="8", page_size=10, page=3)
        self.assertEqual((data["count"], len(data["results"])), (25, 5))

    def test_tc_int_583_filter_options_sorted_no_personal_data(self):
        """IFC-292：楼栋按自然顺序且地下车位最后、单元数值序、无空值；不含姓名手机号。"""
        resp = self.api("get", URL + "/filter-options", token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(set(resp.data), {"buildings", "unit_nos"})
        self.assertEqual(resp.data["buildings"], ["1", "2", "3", "10", "地下车位"])
        self.assertEqual(resp.data["unit_nos"], ["1", "2"])
        text = resp.content.decode()
        for secret in ("张三丰", "13800001234", "李四光"):
            self.assertNotIn(secret, text)
