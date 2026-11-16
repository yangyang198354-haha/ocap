"""PHASE_09 E2E：逐级选房排序、地下车位归属修正、后台清册过滤与导出的用户旅程（多步 HTTP + 命令 + ORM + 路由 + 权限）。

critical path 口径：替代——无浏览器 E2E 框架，后端用多步 HTTP 旅程（含管理命令、真实导入接口），
前端用 jsdom 挂载真实页面 + 带状态假服务端（frontend/tests/registry_filters.spec.js 的 TC-E2E-515）。
关联 US-183~192。全部合成数据；导出文件与备份只写临时目录。
"""
import csv
import io
import re
import tempfile
from io import StringIO
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from apps.registry.import_spec import IMPORT_COLUMNS
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from tests.integration.test_registry_filters_contract import vue_load_params
from tests.support import ApiTestBase, next_phone

IMPORT_URL = "/admin/registry/import"


def csv_bytes(rows) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(IMPORT_COLUMNS)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def row(building, unit, floor, room, type_, area, name, phone):
    return [building, unit, floor, room, type_, area, name, phone]


class UnitSortFilterJourneyBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.phone = next_phone()

    def import_rows(self, rows=None, content=None, name="registry.csv", dry_run=False):
        upload = SimpleUploadedFile(name, content if content is not None else csv_bytes(rows),
                                    content_type="text/csv")
        return self.upload(IMPORT_URL, {"file": upload}, data={"dry_run": "1"} if dry_run else None,
                           token=self.admin_token)

    def cmd(self, name, *args):
        out = StringIO()
        call_command(name, *args, stdout=out)
        return dict(line.split("=", 1) for line in out.getvalue().splitlines() if "=" in line and "|" not in line)

    def legacy_rows(self):
        """用户现状：负一/负二层车位挂在 1 栋下。"""
        return [
            row("11", "1", "1", "101", "住宅", "80.00", "甲测试", self.phone),
            row("10", "1", "1", "101", "住宅", "80.00", "乙测试", self.phone),
            row("2", "1", "1", "101", "住宅", "80.00", "丙测试", self.phone),
            row("1", "1", "1", "101", "住宅", "80.00", "丁测试", ""),
            row("1", "", "负一", "1", "车位", "12.00", "戊测试", self.phone),
            row("1", "", "负二", "2", "车位", "12.00", "己测试", ""),
            row("1", "1", "08", "0801", "住宅", "80.00", "庚测试", ""),
        ]


class OptionsAndHousingJourney(UnitSortFilterJourneyBase):
    def values(self, token, **params):
        resp = self.api("get", "/units/options", params, token=token)
        self.assert_ok(resp)
        return resp.data

    def test_tc_e2e_510_import_relocate_select_underground_and_ordered_housing(self):
        """TC-E2E-510：US-183/184/185/186/192。管理员导入旧清册（车位在 1 栋）→ 修正命令（dry-run→apply）→
        用户逐级选择 → 选"地下车位"→负二/负一→车位号 → 认证 → /me 与 /me/housing 顺序一致（认证时间相反）。"""
        self.assert_ok(self.import_rows(self.legacy_rows()))
        user, token = self.make_user(phone=self.phone)

        # 修正前：1 栋下可见负层车位，第一级没有地下车位
        self.assertEqual([o["value"] for o in self.values(token)["options"]], ["1", "2", "10", "11"])
        self.assertEqual([o["value"] for o in self.values(token, building="1", unit_no="")["options"]], ["负二", "负一"])

        dry = self.cmd("relocate_underground_parking")
        self.assertEqual((dry["candidates"], dry["would_change"], dry["conflicts"]), ("2", "2", "0"))
        self.cmd("relocate_underground_parking", "--apply", "--backup", str(self.dir / "backup.jsonl"),
                 "--expect-changes", "2")

        # US-183/184/185：第一级自然顺序且地下车位最后
        first = self.values(token)
        self.assertEqual((first["level"], [o["value"] for o in first["options"]]),
                         ("building", ["1", "2", "10", "11", "地下车位"]))
        # US-185 AC-185-02：1 栋下不再出现负层
        level1 = self.values(token, building="1")
        self.assertEqual((level1["level"], [o["value"] for o in level1["options"]]), ("unit_no", ["1"]))
        floors1 = self.values(token, building="1", unit_no="1")
        self.assertEqual([o["value"] for o in floors1["options"]], ["1", "08"])
        # US-186：地下车位 → 单元级被跳过 → 负二、负一 → 车位号（类型为车位）
        step = self.values(token, building="地下车位")
        self.assertEqual((step["level"], step["skipped"], [o["value"] for o in step["options"]]),
                         ("floor", ["unit_no"], ["负二", "负一"]))
        rooms = self.values(token, building="地下车位", unit_no="", floor="负一")
        self.assertEqual([(o["value"], o["unit_type_label"]) for o in rooms["options"]], [("1", "车位")])
        parking_id = rooms["options"][0]["unit_id"]
        # 户号数值序（0801 与 101 在不同楼层，同楼层内数值序见集成用例）
        # 认证：先车位、再 10 栋、最后 2 栋（认证时间与自然顺序相反）
        ten = RegistryUnit.objects.get(building="10")
        two = RegistryUnit.objects.get(building="2")
        for unit_id, owner_name in ((parking_id, "戊测试"), (ten.id, "乙测试"), (two.id, "丙测试")):
            self.assert_ok(self.api("post", "/certifications", {"unit_id": unit_id, "name": owner_name},
                                    token=token), 201)
        me = [u["unit_id"] for u in self.api("get", "/me", token=token).data["identities"]["units"]]
        housing = self.api("get", "/me/housing", token=token).data["units"]
        self.assertEqual(me, [two.id, ten.id, parking_id])
        self.assertEqual([u["unit_id"] for u in housing], me)
        self.assertEqual(housing[-1]["specific_part"], "地下车位负一1号")
        # 刷新 5 次不变
        for _ in range(5):
            again = self.api("get", "/me/housing", token=token).data["units"]
            self.assertEqual([u["unit_id"] for u in again], me)

    def test_tc_e2e_511_unregistered_phone_gets_standard_prompt_for_underground_parking(self):
        """TC-E2E-511：US-186 AC-186-02：手机号不在清册该车位名下 → 422 PHONE_NOT_IN_REGISTRY，与普通房屋一致。"""
        self.assert_ok(self.import_rows(self.legacy_rows()))
        self.cmd("relocate_underground_parking", "--apply", "--backup", str(self.dir / "b.jsonl"), "--expect-changes", "2")
        _, stranger = self.make_user()
        parking = RegistryUnit.objects.get(building="地下车位", floor="负一")
        self.assert_error(self.api("post", "/certifications", {"unit_id": parking.id, "name": "戊测试"},
                                   token=stranger), 422, "OWNER_NOT_MATCHED")
        normal = RegistryUnit.objects.get(building="2")
        self.assert_error(self.api("post", "/certifications", {"unit_id": normal.id, "name": "丙测试"},
                                   token=stranger), 422, "OWNER_NOT_MATCHED")


class AdminFilterJourney(UnitSortFilterJourneyBase):
    def test_tc_e2e_512_admin_filters_flow_as_the_page_drives_it(self):
        """TC-E2E-512：US-189/190/191（接口侧）：管理员取下拉取值 → 用页面真实传的参数名逐项过滤 → 组合 → 清空；
        非管理员被拒。参数名取自 AdminRegistry.vue 的 admin.registryUnits({...})（前后端契约）。"""
        rows = self.legacy_rows()
        rows[1][7] = "13800001234"  # 10 栋乙测试
        self.assert_ok(self.import_rows(rows))
        self.cmd("relocate_underground_parking", "--apply", "--backup", str(self.dir / "b.jsonl"), "--expect-changes", "2")

        page_keys = vue_load_params()
        self.assertTrue({"building", "unit_no", "room", "owner_name", "owner_phone", "unit_type", "q"} <= page_keys)

        opts = self.api("get", "/admin/registry/units/filter-options", token=self.admin_token)
        self.assert_ok(opts)
        self.assertEqual(opts.data["buildings"], ["1", "2", "10", "11", "地下车位"])
        self.assertEqual(opts.data["unit_nos"], ["1"])

        def listing(**params):
            resp = self.api("get", "/admin/registry/units", {"page": 1, "page_size": 20, **params},
                            token=self.admin_token)
            self.assert_ok(resp)
            return resp.data

        total = listing()["count"]
        self.assertEqual(total, 7)
        self.assertEqual(listing(building="1")["count"], 2)   # 1 栋两条住宅（丁、庚），不含 10/11 栋与地下车位
        self.assertEqual(listing(building="地下车位", unit_type="PARKING")["count"], 2)
        self.assertEqual(listing(building="1", unit_type="PARKING")["count"], 0)
        by_phone = listing(owner_phone="1234")
        self.assertEqual([r["building"] for r in by_phone["results"]], ["10"])
        self.assertEqual(by_phone["results"][0]["owners"][0]["phones"], ["13800001234"])
        self.assertEqual(listing(owner_name="乙测")["count"], 1)
        self.assertEqual(listing(q="0801")["count"], 1)
        self.assertEqual(listing(q="0801", unit_type="APARTMENT")["count"], 0)
        self.assertEqual(listing(room="0801", unit_no="1")["count"], 1)
        # 重置（页面对空值不传参数）
        self.assertEqual(listing()["count"], total)
        # 非管理员
        _, user_token = self.make_user()
        self.assert_error(self.api("get", "/admin/registry/units", {"building": "1"}, token=user_token), 403)
        self.assert_error(self.api("get", "/admin/registry/units/filter-options", token=user_token), 403)


class ExportAndRelocationJourney(UnitSortFilterJourneyBase):
    def export(self, name):
        path = self.dir / name
        values = self.cmd("export_registry_import_file", "--output", str(path))
        return path, values

    def test_tc_e2e_513_export_then_real_import_precheck_before_and_after_relocation(self):
        """TC-E2E-513：US-187/188：导出文件经真实批量导入预检——修正前：失败 0、将在"地下车位"下新增 2 个；
        执行库内修正后：失败 0、新增 0、更新 0、业主新增 0；正式导入后库计数不变；前导零保持。"""
        self.assert_ok(self.import_rows(self.legacy_rows()))
        before_counts = (RegistryUnit.objects.count(), RegistryOwner.objects.count(), RegistryPhone.objects.count())
        path, v = self.export("before.csv")
        self.assertEqual((v["diff_units"], v["diff_owners_named"], v["diff_phones_distinct"]), ("0", "0", "0"))
        self.assertEqual((v["relocated_units"], v["precheck_rows_failed"]), ("2", "0"))
        self.assertEqual((RegistryUnit.objects.count(), RegistryOwner.objects.count(),
                          RegistryPhone.objects.count()), before_counts)  # 只读
        content = path.read_bytes()
        self.assertIn("0801", content.decode("utf-8-sig"))
        preview = self.import_rows(content=content, name="before.csv", dry_run=True)
        self.assert_ok(preview)
        self.assertEqual((preview.data["failed"], preview.data["imported"], preview.data["owners_created"]), (0, 2, 2))

        self.cmd("relocate_underground_parking", "--apply", "--backup", str(self.dir / "bk.jsonl"), "--expect-changes", "2")
        after_path, v2 = self.export("after.csv")
        self.assertEqual(after_path.read_bytes(), content)  # AUTH-02 前后文件相同
        again = self.import_rows(content=after_path.read_bytes(), name="after.csv", dry_run=True)
        self.assert_ok(again)
        self.assertEqual((again.data["failed"], again.data["imported"], again.data["updated"],
                          again.data["owners_created"]), (0, 0, 0, 0))
        commit = self.import_rows(content=after_path.read_bytes(), name="after.csv")
        self.assert_ok(commit)
        self.assertEqual((RegistryUnit.objects.count(), RegistryOwner.objects.count(),
                          RegistryPhone.objects.count()), before_counts)
        self.assertEqual(RegistryUnit.objects.get(room="0801").floor, "08")

    def test_tc_e2e_514_relocation_keeps_certified_binding_and_restore_returns_exactly(self):
        """TC-E2E-515：US-188 AC-188-01/02/04/06：已认证业主的车位被修正后，/me/housing 仍绑定同一记录、名称为新名称；
        重复执行 0 改动；按备份还原后名称恢复、记录逐项与修正前一致。"""
        self.assert_ok(self.import_rows(self.legacy_rows()))
        user, token = self.make_user(phone=self.phone)
        parking = RegistryUnit.objects.get(building="1", floor="负一")
        self.assert_ok(self.api("post", "/certifications", {"unit_id": parking.id, "name": "戊测试"},
                                token=token), 201)
        original = list(RegistryUnit.objects.order_by("id").values_list(
            "id", "building", "unit_no", "floor", "room", "specific_part", "unit_type", "area", "updated_at"))
        membership = Membership.objects.get(user=user, unit=parking)

        backup = str(self.dir / "bk.jsonl")
        moved = self.cmd("relocate_underground_parking", "--apply", "--backup", backup, "--expect-changes", "2")
        self.assertEqual(moved["moved"], "2")
        housing = self.api("get", "/me/housing", token=token).data["units"]
        self.assertEqual([(u["unit_id"], u["specific_part"], u["role"]) for u in housing],
                         [(parking.id, "地下车位负一1号", membership.role)])
        self.assertEqual(Membership.objects.get(pk=membership.pk).ended_at, None)
        noop = self.cmd("relocate_underground_parking", "--apply", "--backup", str(self.dir / "bk2.jsonl"),
                        "--expect-changes", "0")
        self.assertEqual(noop["moved"], "0")

        restored = self.cmd("relocate_underground_parking", "--restore", backup, "--apply")
        self.assertEqual((restored["restored"], restored["differences"]), ("2", "0"))
        now = list(RegistryUnit.objects.order_by("id").values_list(
            "id", "building", "unit_no", "floor", "room", "specific_part", "unit_type", "area", "updated_at"))
        self.assertEqual(now, original)
        housing = self.api("get", "/me/housing", token=token).data["units"]
        self.assertEqual(housing[0]["specific_part"], parking.specific_part)
        self.assertEqual(housing[0]["unit_id"], parking.id)
        self.assertTrue(re.search(r"1栋?负一", housing[0]["specific_part"]))
