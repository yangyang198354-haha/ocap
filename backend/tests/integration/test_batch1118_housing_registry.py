"""PHASE_08 集成测试（ocap_batch_1118）：身份页真实姓名与共有产权人（US-247/248）、清册默认与表头排序、管理端选项接口（US-254/255）。

关联 AC-247-01~04、AC-248-01~05、AC-254-01~04、AC-255-01~05、REQ-NFUNC-046/048。分层：integration。TC-INT-1100 起。
姓名/手机号均为合成值（C-79）。
"""
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.registry.ordering import unit_sort_key
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_phone


class HousingNamesBase(ApiTestBase):
    def unit_with(self, owners, room="902"):
        """owners: [(姓名, [手机号...])]"""
        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room=room)
        for name, phones in owners:
            owner = RegistryOwner.objects.create(unit=unit, name=name)
            for phone in phones:
                RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        return unit

    def certify(self, user, unit, role="OWNER"):
        return Membership.objects.create(user=user, unit=unit, role=role, source="CERTIFIED", active_slot=1,
                                         head_slot=1 if role == "HEAD" else None)

    def housing(self, token):
        return self.assert_ok(self.api("get", "/me/housing", token=token))


class RealNameTests(HousingNamesBase):
    def test_tc_int_1100_owner_sees_own_real_name(self):
        """TC-INT-1100 / AC-247-01：产权业主（已验证手机号与清册业主"业主甲"登记号码一致）→ real_names=["业主甲"]。"""
        user, token = self.make_user()
        self.certify(user, self.unit_with([("业主甲", [user.phone])]), "HEAD")
        self.assertEqual(self.housing(token).data["real_names"], ["业主甲"])

    def test_tc_int_1101_same_name_in_two_units_deduplicated(self):
        """TC-INT-1101 / AC-247-02：2 套房登记同一姓名 → real_names 只出现 1 次（去重保序）；两个不同姓名按房屋序各 1 次。"""
        user, token = self.make_user()
        self.certify(user, self.unit_with([("业主甲", [user.phone])], room="901"), "HEAD")
        self.certify(user, self.unit_with([("业主甲", [user.phone])], room="902"))
        self.assertEqual(self.housing(token).data["real_names"], ["业主甲"])
        self.certify(user, self.unit_with([("业主丙", [user.phone])], room="903"))
        self.assertEqual(self.housing(token).data["real_names"], ["业主甲", "业主丙"])

    def test_tc_int_1102_guest_resident_and_blank_registry_name_show_nothing(self):
        """TC-INT-1102 / AC-247-03、NFUNC-046(1)：游客、仅同住人、清册姓名为空的产权业主 → real_names=[]；响应中不含昵称代替，也不含清册里其他业主姓名。"""
        guest, gtoken = self.make_user(nickname="游客昵称")
        resp = self.housing(gtoken)
        self.assertEqual(resp.data["real_names"], [])
        resident, rtoken = self.make_user(nickname="同住昵称")
        unit = self.unit_with([("业主甲", [next_phone()])], room="911")
        self.certify(resident, unit, "RESIDENT")
        data = self.housing(rtoken).data
        self.assertEqual(data["real_names"], [])
        blank, btoken = self.make_user()
        bunit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room="912")
        o = RegistryOwner.objects.create(unit=bunit, name=None)
        RegistryPhone.objects.create(unit=bunit, owner=o, phone=blank.phone)
        self.certify(blank, bunit, "HEAD")
        bdata = self.housing(btoken).data
        self.assertEqual(bdata["real_names"], [])
        self.assertNotIn("游客昵称", str(resp.data["real_names"]))

    def test_tc_int_1103_other_user_never_sees_my_real_name(self):
        """TC-INT-1103 / AC-247-04、AC-248-03：用户 B 的 /me/housing、/me、公开决议响应中出现用户 A 真实姓名（合成唯一串）次数 = 0。"""
        a, atoken = self.make_user()
        self.certify(a, self.unit_with([("唯一合成姓名甲乙", [a.phone])], room="921"), "HEAD")
        b, btoken = self.make_user()
        self.certify(b, self.unit_with([("业主乙", [b.phone])], room="922"), "HEAD")
        for path in ("/me/housing", "/me", "/me/profile", "/resolutions?scope=public", "/units/options"):
            self.assertNotIn("唯一合成姓名甲乙", self.api("get", path, token=btoken).content.decode(), path)
        self.assertIn("唯一合成姓名甲乙", self.housing(atoken).content.decode())


class CoOwnerTests(HousingNamesBase):
    def test_tc_int_1104_co_owners_exclude_self_and_hide_phone(self):
        """TC-INT-1104 / AC-248-01、AC-248-04：清册登记业主甲、乙，用户是业主甲 → co_owners=["业主乙"]（不含本人）；乙尚未注册仍显示姓名，无手机号、无注册状态字段。"""
        user, token = self.make_user()
        other_phone = next_phone()
        unit = self.unit_with([("业主甲", [user.phone]), ("业主乙", [other_phone])])
        self.certify(user, unit, "HEAD")
        resp = self.housing(token)
        row = resp.data["units"][0]
        self.assertEqual(row["co_owners"], ["业主乙"])
        text = resp.content.decode()
        self.assertNotIn(other_phone, text)
        self.assertNotIn("未注册", text)
        self.assertTrue(all(isinstance(n, str) for n in row["co_owners"]))

    def test_tc_int_1105_single_owner_has_empty_co_owners(self):
        """TC-INT-1105 / AC-248-02：清册只登记 1 位业主（本人）→ co_owners=[]（页面显示"无"）。"""
        user, token = self.make_user()
        self.certify(user, self.unit_with([("业主甲", [user.phone])], room="301"), "HEAD")
        self.assertEqual(self.housing(token).data["units"][0]["co_owners"], [])

    def test_tc_int_1106_resident_sees_full_names_guest_and_uncertified_see_none(self):
        """TC-INT-1106 / AC-248-03、NFUNC-046(2)：本专有部分的同住人看到共有产权人全名（含业主甲、乙）；游客、未认证该专有部分的用户读取 /me/housing 无该专有部分任何业主姓名；
        普通用户访问管理端业主候选接口 403、清册管理列表 403（成功数 0）。"""
        unit = self.unit_with([("业主甲", [next_phone()]), ("业主乙", [next_phone()])], room="331")
        resident, rtoken = self.make_user()
        self.certify(resident, unit, "RESIDENT")
        rdata = self.housing(rtoken).data
        self.assertEqual(set(rdata["units"][0]["co_owners"]), {"业主甲", "业主乙"})
        self.assertEqual(rdata["real_names"], [])
        guest, gtoken = self.make_user()
        other, otoken = self.make_user()
        self.certify(other, self.unit_with([("业主丙", [other.phone])], room="332"), "HEAD")
        for token in (gtoken, otoken):
            text = self.housing(token).content.decode()
            self.assertNotIn("业主甲", text)
            self.assertNotIn("业主乙", text)
            self.assertEqual(self.api("get", "/admin/committee/owner-candidates", {"unit_id": unit.id}, token=token).status_code, 403)
            self.assertEqual(self.api("get", "/admin/registry/units", token=token).status_code, 403)

    def test_tc_int_1107_each_unit_row_has_its_own_co_owners_and_queries_bounded(self):
        """TC-INT-1107 / AC-248-05、M-SA-010：2 套房各 1 位共有产权人，每行只显示各自的；/me/housing 查询数不随房屋数增长（2 套 vs 6 套）。"""
        user, token = self.make_user()
        u1 = self.unit_with([("业主甲", [user.phone]), ("共有人一", [next_phone()])], room="401")
        u2 = self.unit_with([("业主甲", [user.phone]), ("共有人二", [next_phone()])], room="402")
        self.certify(user, u1, "HEAD")
        self.certify(user, u2)
        rows = {r["unit_id"]: r["co_owners"] for r in self.housing(token).data["units"]}
        self.assertEqual(rows, {u1.id: ["共有人一"], u2.id: ["共有人二"]})

        def count():
            with CaptureQueriesContext(connection) as ctx:
                self.housing(token)
            return len(ctx)
        base = count()
        for i in range(4):
            self.certify(user, self.unit_with([("业主甲", [user.phone]), (f"共有人{i}", [next_phone()])], room=f"41{i}"))
        self.assertLessEqual(count(), base + 1)


class RegistrySortBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        _, self.token = self.make_admin()

    def mk(self, building, unit_no, floor, room):
        return RegistryUnit.objects.create(building=building, unit_no=unit_no, floor=floor, room=room)

    def listing(self, **params):
        return self.assert_ok(self.api("get", "/admin/registry/units", params, token=self.token))

    def parts(self, resp):
        return [r["specific_part"] for r in resp.json()["results"]]

    def all_parts(self, page_size=2, **params):
        collected, page = [], 1
        while True:
            resp = self.listing(page=page, page_size=page_size, **params)
            collected += self.parts(resp)
            if len(collected) >= resp.json()["count"] or not resp.json()["results"]:
                return collected, resp.json()["count"]
            page += 1


class RegistryDefaultOrderTests(RegistrySortBase):
    def test_tc_int_1110_default_order_building_unit_floor_room_natural(self):
        """TC-INT-1110 / AC-254-01：录入顺序打乱的 4 条（1栋2单元10层1001、1栋1单元2层201、1栋1单元10层1001、2栋1单元1层101）→ 未带排序参数时顺序为
        1栋1单元2层201、1栋1单元10层1001、1栋2单元10层1001、2栋1单元1层101（数字自然顺序，2 在 10 之前）。"""
        a = self.mk("1栋", "2单元", "10", "1001")
        b = self.mk("1栋", "1单元", "2", "201")
        c = self.mk("1栋", "1单元", "10", "1001")
        d = self.mk("2栋", "1单元", "1", "101")
        resp = self.listing()
        self.assertEqual([r["id"] for r in resp.json()["results"]], [b.id, c.id, a.id, d.id])

    def test_tc_int_1111_pagination_consistent_no_gap_no_duplicate(self):
        """TC-INT-1111 / AC-254-02、NFUNC-048：共 3 页（5 条每页 2）依次翻页汇总 → 行数=总数、无重复、整体顺序等于一次取全量的顺序；楼层 2 在 10 之前。"""
        for f, r in (("10", "1001"), ("2", "201"), ("1", "101"), ("3", "301"), ("20", "2001")):
            self.mk("1栋", "1单元", f, r)
        full = self.parts(self.listing(page_size=50))
        pages, count = self.all_parts(page_size=2)
        self.assertEqual((count, len(pages), len(set(pages))), (5, 5, 5))
        self.assertEqual(pages, full)
        floors = [int(p.split("单元")[1].split("层")[0]) if "层" in p else 0 for p in pages]
        self.assertEqual(floors, sorted(floors))

    def test_tc_int_1112_filter_then_same_order(self):
        """TC-INT-1112 / AC-254-03：楼栋=1栋 过滤时只含 1栋记录并仍按同一顺序；楼栋过滤+降序排序同样限定在过滤结果内。"""
        self.mk("2栋", "1单元", "1", "101")
        x = self.mk("1栋", "1单元", "10", "1001")
        y = self.mk("1栋", "1单元", "2", "201")
        resp = self.listing(building="1栋")
        self.assertEqual([r["id"] for r in resp.json()["results"]], [y.id, x.id])
        resp = self.listing(building="1栋", sort="floor", order="desc")
        self.assertEqual([r["id"] for r in resp.json()["results"]], [x.id, y.id])
        self.assertEqual(resp.json()["count"], 2)

    def test_tc_int_1113_underground_and_shop_levels_follow_existing_rule(self):
        """TC-INT-1113 / AC-254-04：含"地下车位""商铺"楼栋与负层时，默认顺序与既有 unit_sort_key 规则完全一致（不新增写法），地下车位在数字楼栋之后、商铺最后，负层在 1 层之前。"""
        rows = [("商铺", "建设南路142号", "", "1"), ("地下车位", "1", "负一", "5"), ("10栋", "1单元", "1", "101"),
                ("2栋", "1单元", "-1", "101"), ("2栋", "1单元", "1", "101"), ("1栋", "1单元", "1", "101")]
        for r in rows:
            self.mk(*r)
        got = [(r["building"], r["floor"]) for r in self.listing(page_size=50).json()["results"]]
        expected = [(b, f) for _, b, f in sorted(((unit_sort_key(*r, 0), r[0], r[2]) for r in rows), key=lambda t: t[0])]
        self.assertEqual(got, expected)
        buildings = [b for b, _ in got]
        self.assertEqual(buildings[:3], ["1栋", "2栋", "2栋"])
        self.assertLess(buildings.index("地下车位"), buildings.index("商铺"))
        self.assertLess(buildings.index("10栋"), buildings.index("地下车位"))
        self.assertEqual([f for b, f in got if b == "2栋"], ["-1", "1"])


class RegistrySortParamTests(RegistrySortBase):
    def setUp(self):
        super().setUp()
        self.u = {}
        for key, args in {"A": ("1栋", "1单元", "2", "201"), "B": ("1栋", "1单元", "10", "1001"), "C": ("1栋", "2单元", "10", "1001"),
                          "D": ("2栋", "1单元", "1", "101"), "E": ("10栋", "1单元", "3", "301")}.items():
            self.u[key] = self.mk(*args)

    def ids(self, **params):
        return [r["id"] for r in self.listing(page_size=50, **params).json()["results"]]

    def test_tc_int_1114_floor_desc_primary_key_others_default_order(self):
        """TC-INT-1114 / AC-255-01：sort=floor&order=desc → 楼层 10（B、C 同层，按默认楼栋/单元序 B,C）在前，再 3、2、1；order=asc 切回升序；两态切换。"""
        u = self.u
        self.assertEqual(self.ids(sort="floor", order="desc"), [u["B"].id, u["C"].id, u["E"].id, u["A"].id, u["D"].id])
        self.assertEqual(self.ids(sort="floor", order="asc"), [u["D"].id, u["A"].id, u["E"].id, u["B"].id, u["C"].id])
        self.assertEqual(self.ids(sort="floor"), self.ids(sort="floor", order="asc"))

    def test_tc_int_1115_each_sortable_column_desc_and_asc(self):
        """TC-INT-1115 / AC-255-01：楼栋/单元/楼层/房号四列各自升降序结果为主键自然顺序（楼栋 10 在 2 之后）。"""
        u = self.u
        bld = [r["building"] for r in self.listing(page_size=50, sort="building", order="asc").json()["results"]]
        self.assertEqual(bld, ["1栋", "1栋", "1栋", "2栋", "10栋"])
        bld = [r["building"] for r in self.listing(page_size=50, sort="building", order="desc").json()["results"]]
        self.assertEqual(bld, ["10栋", "2栋", "1栋", "1栋", "1栋"])
        room = [r["room"] for r in self.listing(page_size=50, sort="room", order="desc").json()["results"]]
        self.assertEqual(room, ["1001", "1001", "301", "201", "101"])
        unit_no = [r["unit_no"] for r in self.listing(page_size=50, sort="unit_no", order="desc").json()["results"]]
        self.assertEqual(unit_no[0], "2单元")
        self.assertEqual(set(self.ids(sort="room", order="desc")), {x.id for x in u.values()})

    def test_tc_int_1116_sort_is_global_not_page_local_and_stable_across_pages(self):
        """TC-INT-1116 / AC-255-02、NFUNC-048：房号降序，第 1 页（每页 2）为全部数据中房号最大的两条（不是仅当前页排序）；逐页汇总 = 全量排序，无重复遗漏。"""
        first = self.listing(page=1, page_size=2, sort="room", order="desc").json()["results"]
        self.assertEqual([r["room"] for r in first], ["1001", "1001"])
        for sort in ("building", "unit_no", "floor", "room"):
            for order in ("asc", "desc"):
                pages, count = self.all_parts(page_size=2, sort=sort, order=order)
                full = self.parts(self.listing(page_size=50, sort=sort, order=order))
                self.assertEqual((count, len(set(pages))), (5, 5), (sort, order))
                self.assertEqual(pages, full, (sort, order))

    def test_tc_int_1117_invalid_sort_params_return_400_invalid_query(self):
        """TC-INT-1117 / AC-255-04、IFC-361：sort 非白名单（type/area/owner/注入串）→ 400 INVALID_QUERY；order 非 asc/desc → 400；仅给 order 不给 sort → 400；响应无记录。"""
        for params in ({"sort": "unit_type"}, {"sort": "area"}, {"sort": "owner"}, {"sort": "id; drop"}, {"sort": "floor", "order": "up"},
                       {"sort": "floor", "order": ""}, {"order": "desc"}):
            resp = self.api("get", "/admin/registry/units", params, token=self.token)
            body = self.assert_error(resp, 400, "INVALID_QUERY")
            self.assertNotIn("results", body)

    def test_tc_int_1118_sort_with_filter_and_non_admin_rejected(self):
        """TC-INT-1118 / AC-255-03、AC-255-05：排序与过滤叠加（楼栋=1栋 + 房号降序）保持过滤范围；用户端令牌与未登录带 sort 请求 → 403/401，记录暴露 0。"""
        u = self.u
        self.assertEqual(self.ids(building="1栋", sort="room", order="desc"), [u["B"].id, u["C"].id, u["A"].id])
        _, utoken = self.make_user()
        resp = self.api("get", "/admin/registry/units", {"sort": "floor", "order": "desc"}, token=utoken)
        self.assertEqual(resp.status_code, 403)
        self.assertNotIn("results", resp.json())
        self.assertEqual(self.api("get", "/admin/registry/units", {"sort": "floor"}).status_code, 401)


class AdminUnitOptionsTests(RegistrySortBase):
    def test_tc_int_1119_admin_unit_options_same_shape_no_owner_data_admin_only(self):
        """TC-INT-1119 / IFC-351、AC-256-01：管理端 /admin/registry/unit-options 响应形状同成员端 /units/options（level/skipped/has_empty/options），不含业主姓名与手机号；
        缺上级参数 400 INVALID_QUERY；普通用户 403、未登录 401。"""
        unit = self.mk("1栋", "1单元", "9", "902")
        o = RegistryOwner.objects.create(unit=unit, name="业主甲")
        RegistryPhone.objects.create(unit=unit, owner=o, phone="13900001234")
        resp = self.assert_ok(self.api("get", "/admin/registry/unit-options", token=self.token))
        member = self.assert_ok(self.api("get", "/units/options", token=self.make_user()[1]))
        self.assertEqual(set(resp.json()), set(member.json()))
        self.assertEqual(resp.json()["level"], "building")
        text = resp.content.decode()
        self.assertNotIn("业主甲", text)
        self.assertNotIn("13900001234", text)
        deeper = self.assert_ok(self.api("get", "/admin/registry/unit-options", {"building": "1栋", "unit_no": "1单元", "floor": "9"}, token=self.token))
        self.assertEqual(deeper.json()["level"], "room")
        self.assertEqual(self.api("get", "/admin/registry/unit-options", {"unit_no": "1单元"}, token=self.token).status_code, 400)
        self.assertEqual(self.api("get", "/admin/registry/unit-options", token=self.make_user()[1]).status_code, 403)
        self.assertEqual(self.api("get", "/admin/registry/unit-options").status_code, 401)
