"""PHASE_09 E2E：业主清册导入增强的用户旅程（多步 HTTP + ORM + 路由 + 权限）。

无浏览器 E2E 框架，采用最高可执行的端到端级用例（完整 API 旅程）替代。
"""
import csv
import io
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.models import AuditLog
from apps.registry.import_spec import IMPORT_COLUMNS
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from tests.support import ApiTestBase

IMPORT_URL = "/admin/registry/import"


def csv_bytes(rows) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(IMPORT_COLUMNS)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def row(building="1", unit="1", floor="1", room="101", type_="住宅", area="89.50",
        name="张三", phone="") -> list:
    return [building, unit, floor, room, type_, area, name, phone]


class RegistryImportJourneyTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()

    def import_rows(self, rows, dry_run=False, token=None):
        upload = SimpleUploadedFile("registry.csv", csv_bytes(rows), content_type="text/csv")
        data = {"dry_run": "1"} if dry_run else None
        return self.upload(IMPORT_URL, {"file": upload}, data=data, token=token or self.admin_token)

    def test_tc_e2e_101_import_multi_owner_then_register_and_select_parking(self):
        """TC-E2E-101：管理员查看说明→下载模板→导入多业主与车位→业主注册自动绑定→用户端逐级选择车位。"""
        spec = self.api("get", "/admin/registry/import/spec", token=self.admin_token)
        self.assert_ok(spec)
        self.assertEqual(spec.data["max_rows"], 20000)

        template = self.api("get", "/admin/registry/import/template?file_type=csv", token=self.admin_token)
        self.assert_ok(template)
        self.assertIn("楼栋", template.content.decode("utf-8-sig"))

        rows = [row(name="张一", phone="13700000101"),
                row(name="张二", phone="13700000102"),
                row(name="张三", phone=""),
                row(building="车库", unit="", floor="", room="A-101", type_="车位",
                    area="12.50", name="赵云", phone="13700000103")]
        preview = self.import_rows(rows, dry_run=True)
        self.assert_ok(preview)
        self.assertEqual(RegistryUnit.objects.count(), 0)
        commit = self.import_rows(rows)
        self.assert_ok(commit)
        self.assertEqual((commit.data["imported"], commit.data["owners_created"],
                          commit.data["failed"]), (2, 4, 0))

        residential = RegistryUnit.objects.get(room="101")
        _, first_token, _ = self.register("13700000101")
        self.assertEqual(Membership.objects.get(user=self.user_of(first_token), unit=residential).role,
                         "HEAD")
        _, token, _ = self.register("13700000102")
        user = self.user_of(token)
        self.assertEqual(Membership.objects.get(user=user, unit=residential).role, "OWNER")
        me = self.api("get", "/me", token=token)
        self.assertIn("产权业主", me.data["identities"]["labels"])

        units = self.api("get", "/units/options?building=1", token=token)
        self.assert_ok(units)
        floors = self.api("get", "/units/options?building=1&unit_no=1&floor=1", token=token)
        self.assert_ok(floors)
        self.assertEqual(floors.data["level"], "room")
        parking_levels = self.api("get", "/units/options?building=车库", token=token)
        self.assert_ok(parking_levels)
        self.assertEqual(parking_levels.data["skipped"], ["unit_no", "floor"])
        self.assertEqual(parking_levels.data["options"][0]["value"], "A-101")
        self.assertIn("车位", parking_levels.data["options"][0]["label"])

        _, parking_token, _ = self.register("13700000103")
        parking = RegistryUnit.objects.get(room="A-101")
        parking_user = self.user_of(parking_token)
        self.assertEqual(Membership.objects.get(user=parking_user, unit=parking).role, "HEAD")
        me_parking = self.api("get", "/me", token=parking_token)
        self.assertIn("车库-A-101", [item["specific_part"] for item in me_parking.data["identities"]["units"]])

    def test_tc_e2e_102_reimport_edit_and_certification_survives(self):
        """TC-E2E-102：首次导入→业主认证→重复导入补录并改类型→管理端编辑业主→既有认证保留。"""
        self.assert_ok(self.import_rows([row(name="张伟", phone="13700000201"),
                                        row(name="李娜")]))
        unit = RegistryUnit.objects.get(room="101")

        _, token, _ = self.register("13700000201")
        user = self.user_of(token)
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, role="HEAD",
                                                  ended_at__isnull=True).exists())

        again = self.import_rows([row(name="张伟", phone="13700000202", type_="公寓", area="90.00"),
                                  row(name="王强", type_="公寓", area="90.00")])
        self.assert_ok(again)
        self.assertEqual(again.data["updated"], 1)
        self.assertEqual(again.data["errors"], [])
        self.assertEqual(again.data["changes"],
                         [{"specific_part": unit.specific_part, "fields": ["unit_type", "area"]}])
        unit.refresh_from_db()
        self.assertEqual((unit.unit_type, unit.area), ("APARTMENT", Decimal("90.00")))
        self.assertEqual(sorted(o.name for o in RegistryOwner.objects.filter(unit=unit)),
                         ["张伟", "李娜", "王强"])

        detail = self.api("get", "/admin/registry/units?page_size=100", token=self.admin_token)
        self.assert_ok(detail)
        item = next(entry for entry in detail.data["results"] if entry["id"] == unit.id)
        self.assertEqual(item["unit_type_label"], "公寓")
        zhang = next(o for o in item["owners"] if o["name"] == "张伟")
        self.assertEqual(sorted(zhang["phones"]), ["13700000201", "13700000202"])

        kept = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                        {"owners": [{"id": zhang["id"], "name": "张伟",
                                     "phones": sorted(zhang["phones"])}]}, token=self.admin_token)
        self.assert_ok(kept)
        self.assertEqual([o["name"] for o in kept.data["owners"]], ["张伟"])
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, ended_at__isnull=True).exists())
        self.assertTrue(AuditLog.objects.filter(action="REGISTRY_UNIT_CHANGED",
                                                object_id=str(unit.id)).exists())

        _, legacy_token, _ = self.register("13700000203")
        legacy = RegistryUnit.objects.create(building="1", unit_no="9", floor="9", room="901")
        legacy_owner = RegistryOwner.objects.create(unit=legacy, name="老业主")
        RegistryPhone.objects.create(unit=legacy, owner=legacy_owner, phone="13700000203")
        listing = self.api("get", "/admin/registry/units?unit_type=UNSET", token=self.admin_token)
        self.assertIn(legacy.id, [entry["id"] for entry in listing.data["results"]])
        legacy_cert = self.api("post", "/certifications", {"unit_id": legacy.id}, token=legacy_token)
        self.assert_ok(legacy_cert, 201)

    def test_tc_e2e_103_owner_without_phone_appeal_then_admin_adds_phone(self):
        """TC-E2E-103：无手机号业主→用户认证被提示申诉→管理员补录手机号→同一用户认证成功。"""
        self.assert_ok(self.import_rows([row(name="王芳", phone="")]))
        unit = RegistryUnit.objects.get(room="101")
        _, token = self.make_user(phone="13900000301")

        denied = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_error(denied, 422, "PHONE_NOT_IN_REGISTRY")
        self.assertTrue(denied.data["details"]["appeal_available"])

        admin_view = self.api("get", "/admin/registry/units?page_size=100", token=self.admin_token)
        owner = next(entry for entry in admin_view.data["results"] if entry["id"] == unit.id)["owners"][0]
        self.assertEqual(owner["phones"], [])
        fixed = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                         {"owners": [{"id": owner["id"], "name": "王芳",
                                      "phones": ["13900000301"]}]}, token=self.admin_token)
        self.assert_ok(fixed)
        user = self.user_of(token)
        self.assertEqual(Membership.objects.filter(user=user).count(), 0)
        certified = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_ok(certified, 201)
        self.assertEqual(certified.data["role"], "HEAD")

    def test_tc_e2e_104_single_unit_lifecycle(self):
        """TC-E2E-104：新增车位缺面积被拒→新增商铺→改面积→按类型筛选→审计留痕。"""
        rejected = self.api("post", "/admin/registry/units",
                            {"building": "车库", "room": "B-201", "unit_type": "PARKING"},
                            token=self.admin_token)
        self.assert_error(rejected, 400, "INVALID_VALUE")
        self.assertEqual(rejected.data["message"], "车位须填写专有部分面积")
        self.assertEqual(RegistryUnit.objects.count(), 0)

        created = self.api("post", "/admin/registry/units",
                           {"building": "1", "unit_no": "1", "floor": "1", "room": "105",
                            "unit_type": "SHOP", "area": "120.25"}, token=self.admin_token)
        self.assert_ok(created, 201)
        self.assertEqual((created.data["unit_type_label"], created.data["area"]), ("商铺", "120.25"))
        unit_id = created.data["id"]

        updated = self.api("patch", f"/admin/registry/units/{unit_id}", {"area": "130.5"},
                           token=self.admin_token)
        self.assert_ok(updated)
        self.assertEqual(updated.data["area"], "130.50")

        listing = self.api("get", "/admin/registry/units?unit_type=SHOP", token=self.admin_token)
        self.assert_ok(listing)
        self.assertEqual([entry["id"] for entry in listing.data["results"]], [unit_id])
        self.assertTrue(AuditLog.objects.filter(action="REGISTRY_UNIT_CHANGED",
                                                object_id=str(unit_id)).exists())
