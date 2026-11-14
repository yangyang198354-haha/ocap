"""PHASE_08 集成测试：业主清册导入增强（MOD-030~035 / IFC-152~164）。

覆盖 US-092~104 的管理端接口、导入引擎、逐级选项与自动绑定；HTTP 全链路走真实路由器与 ORM。
"""
import csv
import io
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.integrations.fakes import FakeWeChatClient
from apps.integrations.wechat import set_wechat_client
from apps.registry.import_spec import IMPORT_COLUMNS
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_account_no

IMPORT_URL = "/admin/registry/import"


def csv_bytes(rows, header=None) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header or IMPORT_COLUMNS)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def row(building="1", unit="1", floor="1", room="101", type_="住宅", area="89.50",
        name="张三", phone="") -> list:
    return [building, unit, floor, room, type_, area, name, phone]


class RegistryImportTestBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()

    def import_rows(self, rows, dry_run=False, header=None, name="registry.csv", token=None):
        upload = SimpleUploadedFile(name, csv_bytes(rows, header), content_type="text/csv")
        data = {"dry_run": "1"} if dry_run else None
        return self.upload(IMPORT_URL, {"file": upload}, data=data, token=token or self.admin_token)

    def make_registry_unit(self, *, building="1", unit_no="1", floor="1", room="101",
                           unit_type=None, area=None):
        return RegistryUnit.objects.create(building=building, unit_no=unit_no, floor=floor,
                                           room=room, unit_type=unit_type, area=area)

    def add_owner(self, unit, name, phones=()):
        owner = RegistryOwner.objects.create(unit=unit, name=name)
        for phone in phones:
            RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        return owner

    def get_admin_unit(self, unit_id):
        resp = self.api("get", f"/admin/registry/units?page_size=100", token=self.admin_token)
        self.assert_ok(resp)
        return next(item for item in resp.data["results"] if item["id"] == unit_id)

    def owners_of(self, unit):
        return list(RegistryOwner.objects.filter(unit=unit).order_by("id"))


class SpecAndTemplateTests(RegistryImportTestBase):
    def test_tc_int_101_spec_payload(self):
        """TC-INT-101 / AC-092-01：管理员可读取格式说明，字段与页面文案一致。"""
        resp = self.api("get", "/admin/registry/import/spec", token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["max_rows"], 20000)
        self.assertEqual(resp.data["max_file_mb"], 5)
        self.assertEqual([c["name"] for c in resp.data["columns"]], IMPORT_COLUMNS)
        self.assertIn("仅读取第一个工作表", resp.data["excel_sheet_note"])

    def test_tc_int_102_non_admin_denied(self):
        """TC-INT-102 / AC-092-02、AC-093-05、AC-094-04、AC-095-04、AC-097-05、AC-100-06：非管理员一律拒绝。"""
        _, token, unit = self.make_owner()
        calls = [
            ("get", "/admin/registry/import/spec", None),
            ("get", "/admin/registry/import/template?file_type=csv", None),
            ("get", "/admin/registry/units", None),
            ("post", "/admin/registry/units", {"building": "1", "room": "999", "unit_type": "SHOP"}),
            ("patch", f"/admin/registry/units/{unit.id}", {"area": "12.5"}),
            ("put", f"/admin/registry/units/{unit.id}/owners", {"owners": []}),
        ]
        for method, path, data in calls:
            resp = self.api(method, path, data, token=token)
            self.assertIn(resp.status_code, (401, 403), f"{method} {path} -> {resp.status_code}")
        upload = SimpleUploadedFile("r.csv", csv_bytes([row()]), content_type="text/csv")
        resp = self.upload(IMPORT_URL, {"file": upload}, token=token)
        self.assertIn(resp.status_code, (401, 403), resp.content)

    def test_tc_int_103_too_many_rows_rejected(self):
        """TC-INT-103 / AC-092-03：20001 数据行被拒绝，清册不改变。"""
        rows = [row(room=str(10000 + index), name=f"业主{index}") for index in range(20001)]
        resp = self.import_rows(rows)
        self.assert_error(resp, 400, "IMPORT_FILE_INVALID")
        self.assertEqual(resp.data["message"], "文件行数超过 20000")
        self.assertEqual(RegistryUnit.objects.count(), 0)

    def test_tc_int_104_bad_extension_and_oversize(self):
        """TC-INT-104 / AC-092-04、AC-092-05：.xls 与超过 5 MB 的文件被拒绝。"""
        bad = SimpleUploadedFile("r.xls", b"abc", content_type="application/vnd.ms-excel")
        resp = self.upload(IMPORT_URL, {"file": bad}, token=self.admin_token)
        self.assert_error(resp, 400, "IMPORT_FILE_INVALID")
        self.assertEqual(resp.data["message"], "仅支持 xlsx 或 csv")
        large = SimpleUploadedFile("big.csv", b"x" * (5 * 1024 * 1024 + 1), content_type="text/csv")
        resp = self.upload(IMPORT_URL, {"file": large}, token=self.admin_token)
        self.assert_error(resp, 413, "FILE_TOO_LARGE")
        self.assertEqual(resp.data["message"], "文件超过 5 MB")
        self.assertEqual(RegistryUnit.objects.count(), 0)

    def test_tc_int_105_csv_template(self):
        """TC-INT-105 / AC-138-02/03：BOM、表头与新规则示例（多业主/空手机号/车位/负楼层/商铺）齐全。"""
        resp = self.api("get", "/admin/registry/import/template?file_type=csv", token=self.admin_token)
        self.assert_ok(resp)
        self.assertIn("text/csv", resp["Content-Type"])
        self.assertIn("registry_import_template.csv", resp["Content-Disposition"])
        self.assertTrue(resp.content.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.reader(io.StringIO(resp.content.decode("utf-8-sig"))))
        self.assertEqual(rows[0], IMPORT_COLUMNS)
        examples = rows[1:]
        self.assertEqual(len(examples), 6)
        self.assertEqual(sum(1 for item in examples if item[3] == "301"), 3)
        self.assertEqual(sum(1 for item in examples if not item[7]), 4)
        self.assertTrue(any(item[4] == "车位" and not item[1] and not item[2] for item in examples))

    def test_tc_int_106_old_template_rejected(self):
        """TC-INT-106 / AC-093-06：旧 5 列模板整文件拒绝并列出缺少的列。"""
        old_header = ["楼栋", "单元", "楼层", "户号", "手机号"]
        resp = self.import_rows([["1", "1", "1", "101", "13800000001"]], header=old_header)
        self.assert_error(resp, 400, "IMPORT_COLUMNS_MISSING")
        self.assertEqual(resp.data["details"]["columns"], ["专有部分类型", "专有部分面积（平方米）", "业主姓名"])
        self.assertIn("请使用新模板", resp.data["message"])
        self.assertEqual(RegistryUnit.objects.count(), 0)


class MultiOwnerImportTests(RegistryImportTestBase):
    def test_tc_int_107_six_owners_with_four_phones(self):
        """TC-INT-107 / AC-094-01：同单元 6 位业主、4 个手机号，各自可认证。"""
        rows = [row(name=name, phone=phone) for name, phone in [
            ("张一", "13700000001"), ("张二", "13700000002"), ("张三", "13700000003"),
            ("张四", "13700000004"), ("张五", ""), ("张六", "")]]
        resp = self.import_rows(rows)
        self.assert_ok(resp)
        self.assertEqual(resp.data["imported"], 1)
        self.assertEqual(resp.data["owners_created"], 6)
        self.assertEqual(resp.data["phones_created"], 4)
        self.assertEqual(resp.data["failed"], 0)
        unit = RegistryUnit.objects.get()
        self.assertEqual(len(self.owners_of(unit)), 6)
        roles = []
        for phone in ("13700000001", "13700000002", "13700000003", "13700000004"):
            user, token = self.make_user(phone=phone)
            certified = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
            self.assert_ok(certified, 201)
            roles.append(certified.data["role"])
        self.assertEqual(roles[0], "HEAD")
        self.assertEqual(roles[1:], ["OWNER", "OWNER", "OWNER"])

    def test_tc_int_108_two_hundred_owners(self):
        """TC-INT-108 / AC-094-02：200 位业主全部登记，无“超过 10 个”限制。"""
        rows = [row(name=f"业主{index:03d}") for index in range(200)]
        resp = self.import_rows(rows)
        self.assert_ok(resp)
        self.assertEqual(resp.data["owners_created"], 200)
        unit = RegistryUnit.objects.get()
        self.assertEqual(len(self.owners_of(unit)), 200)
        detail = self.get_admin_unit(unit.id)
        self.assertEqual(len(detail["owners"]), 200)

    def test_tc_int_109_semicolon_phones(self):
        """TC-INT-109 / AC-094-03：分号分隔的两个手机号登记到同一位业主。"""
        resp = self.import_rows([row(name="张伟", phone="13800000000;13900000000")])
        self.assert_ok(resp)
        owner = self.owners_of(RegistryUnit.objects.get())[0]
        self.assertEqual(sorted(p.phone for p in owner.phones.all()), ["13800000000", "13900000000"])

    def test_tc_int_110_duplicate_rows_merge(self):
        """TC-INT-110 / AC-094-05：同单元同姓名同手机号两行登记为一位业主一个手机号。"""
        resp = self.import_rows([row(name="张伟", phone="13800000000")] * 2)
        self.assert_ok(resp)
        self.assertEqual(resp.data["owners_created"], 1)
        self.assertEqual(resp.data["phones_created"], 1)
        self.assertEqual(resp.data["failed"], 0)
        unit = RegistryUnit.objects.get()
        self.assertEqual(len(self.owners_of(unit)), 1)
        self.assertEqual(RegistryPhone.objects.filter(unit=unit).count(), 1)

    def test_tc_int_111_empty_phone_ok_and_empty_name_failed(self):
        """TC-INT-111 / AC-094-08、AC-094-09：手机号可空；姓名为空该行失败且不影响其他行。"""
        rows = [row(name="王芳", phone=""), row(room="102", name="", phone="13800000009"),
                row(room="103", name="李四", phone="13800000010")]
        resp = self.import_rows(rows)
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 1)
        self.assertEqual(resp.data["errors"][0]["reason"], "业主姓名不能为空")
        self.assertEqual(resp.data["errors"][0]["row"], 3)
        self.assertEqual(RegistryOwner.objects.filter(name="王芳").count(), 1)
        self.assertEqual(RegistryUnit.objects.count(), 2)

    def test_tc_int_112_import_audit_has_no_pii(self):
        """TC-INT-112 / AC-094-06：导入审计只含计数，不含姓名与手机号明文。"""
        self.assert_ok(self.import_rows([row(name="张伟", phone="13800000011")]))
        log = AuditLog.objects.filter(action="REGISTRY_IMPORTED").order_by("id").last()
        self.assertIsNotNone(log)
        text = str(log.detail)
        self.assertIn("imported", text)
        self.assertNotIn("张伟", text)
        self.assertNotIn("13800000011", text)


class SingleEntryTests(RegistryImportTestBase):
    def test_tc_int_113_put_twelve_owners(self):
        """TC-INT-113 / AC-095-01、AC-095-02：一次保存 12 位业主，姓名与完整手机号回显。"""
        unit = self.make_registry_unit()
        owners = [{"name": f"业主{index}", "phones": [f"136000000{index:02d}"]} for index in range(12)]
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners", {"owners": owners},
                        token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(len(resp.data["owners"]), 12)
        self.assertEqual(resp.data["owners"][0]["name"], "业主0")
        self.assertEqual(resp.data["owners"][0]["phones"], ["13600000000"])

    def test_tc_int_114_invalid_phone_rejected(self):
        """TC-INT-114 / AC-095-03：手机号格式错误被拒绝，原业主不变。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000012"])
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                        {"owners": [{"name": "张伟", "phones": ["123"]}]}, token=self.admin_token)
        self.assert_error(resp, 400, "INVALID_VALUE")
        self.assertEqual(resp.data["message"], "手机号格式不正确")
        self.assertEqual([o.name for o in self.owners_of(unit)], ["张伟"])
        self.assertEqual(RegistryPhone.objects.filter(unit=unit).count(), 1)

    def test_tc_int_115_empty_name_rejected(self):
        """TC-INT-115 / AC-095-07：业主姓名留空被拒绝，原业主不变。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟")
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                        {"owners": [{"name": "  "}]}, token=self.admin_token)
        self.assert_error(resp, 400, "INVALID_VALUE")
        self.assertEqual(resp.data["message"], "业主姓名不能为空")
        self.assertEqual([o.name for o in self.owners_of(unit)], ["张伟"])

    def test_tc_int_116_owner_without_phone(self):
        """TC-INT-116 / AC-095-08：姓名为王芳、手机号为空可保存并回显。"""
        unit = self.make_registry_unit()
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                        {"owners": [{"name": "王芳"}]}, token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["owners"][0], {"id": resp.data["owners"][0]["id"], "name": "王芳",
                                                 "phones": []})

    def test_tc_int_117_delete_owner_keeps_certification(self):
        """TC-INT-117 / AC-095-05：删除业主后既有认证保留，清册中该手机号不再参与比对。"""
        unit = self.make_registry_unit()
        owner = self.add_owner(unit, "张伟", ["13800000013"])
        user, token = self.make_user(phone="13800000013")
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=token), 201)
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners", {"owners": []},
                        token=self.admin_token)
        self.assert_ok(resp)
        self.assertFalse(RegistryOwner.objects.filter(id=owner.id).exists())
        self.assertFalse(RegistryPhone.objects.filter(unit=unit, phone="13800000013").exists())
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, ended_at__isnull=True,
                                                  role="HEAD").exists())

    def test_tc_int_118_me_masks_phone_and_hides_name(self):
        """TC-INT-118 / AC-095-06：用户端 /me 不含完整手机号与业主姓名。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000014"])
        user, token = self.make_user(phone="13800000014")
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=token), 201)
        resp = self.api("get", "/me", token=token)
        self.assert_ok(resp)
        text = resp.content.decode("utf-8")
        self.assertNotIn("13800000014", text)
        self.assertNotIn("张伟", text)
        self.assertIn("138****0014", text)


class TypeAndAreaImportTests(RegistryImportTestBase):
    def test_tc_int_119_import_four_types(self):
        """TC-INT-119 / AC-096-01：四种类型与面积按文件登记，商铺面积为空。"""
        rows = [row(room="301", type_="住宅", area="89.50", name="甲"),
                row(room="302", type_="公寓", area="60", name="乙"),
                row(room="303", type_="商铺", area="", name="丙"),
                row(building="车库", unit="", floor="", room="A-088", type_="车位", area="12.50", name="丁")]
        resp = self.import_rows(rows)
        self.assert_ok(resp)
        self.assertEqual(resp.data["imported"], 4)
        by_room = {u.room: u for u in RegistryUnit.objects.all()}
        self.assertEqual(by_room["301"].unit_type, "RESIDENCE")
        self.assertEqual(by_room["301"].area, Decimal("89.50"))
        self.assertEqual(by_room["302"].area, Decimal("60.00"))
        self.assertIsNone(by_room["303"].area)
        self.assertEqual(by_room["A-088"].unit_type, "PARKING")
        self.assertEqual(by_room["A-088"].specific_part, "车库A-088")

    def test_tc_int_120_type_validation(self):
        """TC-INT-120 / AC-096-02、AC-096-03：新单元类型为空或越界均失败。"""
        resp = self.import_rows([row(room="301", type_="", name="甲"),
                                 row(room="302", type_="别墅", name="乙")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 2)
        reasons = {e["row"]: e["reason"] for e in resp.data["errors"]}
        self.assertEqual(reasons[2], "专有部分类型为空")
        self.assertIn("专有部分类型不在允许范围内", reasons[3])
        self.assertEqual(RegistryUnit.objects.count(), 0)

    def test_tc_int_121_area_validation(self):
        """TC-INT-121 / AC-096-04：abc/-5/0/12.345 分别失败并给出原因。"""
        resp = self.import_rows([row(room="301", area="abc"), row(room="302", area="-5"),
                                 row(room="303", area="0"), row(room="304", area="12.345")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 4)
        reasons = {e["row"]: e["reason"] for e in resp.data["errors"]}
        for line in (2, 3, 4):
            self.assertEqual(reasons[line], "专有部分面积须为大于 0 的数值")
        self.assertEqual(reasons[5], "专有部分面积最多 2 位小数")

    def test_tc_int_122_type_conflict_in_group(self):
        """TC-INT-122 / AC-096-05：同单元两行类型不同，全部行失败且不写入。"""
        resp = self.import_rows([row(type_="住宅", name="甲"), row(type_="商铺", name="乙")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 2)
        self.assertEqual({e["reason"] for e in resp.data["errors"]}, {"同一专有部分的类型不一致"})
        self.assertEqual(RegistryUnit.objects.count(), 0)

    def test_tc_int_123_missing_type_column(self):
        """TC-INT-123 / AC-096-06：缺“专有部分类型”列整文件拒绝。"""
        header = [c for c in IMPORT_COLUMNS if c != "专有部分类型"]
        resp = self.import_rows([["1", "1", "1", "101", "89.50", "张三", ""]], header=header)
        self.assert_error(resp, 400, "IMPORT_COLUMNS_MISSING")
        self.assertEqual(resp.data["details"]["columns"], ["专有部分类型"])
        self.assertEqual(RegistryUnit.objects.count(), 0)

    def test_tc_int_124_parking_requires_area(self):
        """TC-INT-124 / AC-096-07：车位面积为空失败；住宅为空成功。"""
        resp = self.import_rows([row(room="A-088", type_="车位", area=""),
                                 row(room="301", type_="住宅", area="")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 1)
        self.assertEqual(resp.data["errors"][0]["reason"], "车位的专有部分面积不能为空")
        self.assertTrue(RegistryUnit.objects.filter(room="301", area__isnull=True).exists())


class SingleUnitAdminTests(RegistryImportTestBase):
    def test_tc_int_125_create_and_update_unit(self):
        """TC-INT-125 / AC-097-01：新增商铺 120.25，修改面积为 130.5。"""
        resp = self.api("post", "/admin/registry/units", {"building": "1", "unit_no": "1",
                                                          "floor": "1", "room": "105",
                                                          "unit_type": "SHOP", "area": "120.25"},
                        token=self.admin_token)
        self.assert_ok(resp, 201)
        unit_id = resp.data["id"]
        self.assertEqual(resp.data["unit_type_label"], "商铺")
        self.assertEqual(resp.data["area"], "120.25")
        updated = self.api("patch", f"/admin/registry/units/{unit_id}", {"area": "130.5"},
                           token=self.admin_token)
        self.assert_ok(updated)
        self.assertEqual(updated.data["area"], "130.50")

    def test_tc_int_126_create_requires_type(self):
        """TC-INT-126 / AC-097-02：新增不选类型被拒绝。"""
        resp = self.api("post", "/admin/registry/units",
                        {"building": "1", "room": "106", "area": "10"}, token=self.admin_token)
        self.assert_error(resp, 400, "INVALID_VALUE")
        self.assertEqual(resp.data["message"], "请选择专有部分类型")

    def test_tc_int_127_invalid_area_rejected(self):
        """TC-INT-127 / AC-097-03：面积非数值或超过 2 位小数被拒绝，原记录不变。"""
        unit = self.make_registry_unit(unit_type="RESIDENCE", area=Decimal("88.00"))
        for value in ("abc", "1.234"):
            resp = self.api("patch", f"/admin/registry/units/{unit.id}", {"area": value},
                            token=self.admin_token)
            self.assert_error(resp, 400, "INVALID_VALUE")
            self.assertEqual(resp.data["message"], "专有部分面积格式不正确")
        unit.refresh_from_db()
        self.assertEqual(unit.area, Decimal("88.00"))

    def test_tc_int_128_filter_by_type(self):
        """TC-INT-128 / AC-097-04：按车位与未登记筛选。"""
        self.make_registry_unit(room="301", unit_type="PARKING", area=Decimal("12.50"))
        self.make_registry_unit(room="302", unit_type="RESIDENCE", area=Decimal("89.50"))
        self.make_registry_unit(room="303")
        parking = self.api("get", "/admin/registry/units?unit_type=PARKING", token=self.admin_token)
        self.assert_ok(parking)
        self.assertEqual([row["room"] for row in parking.data["results"]], ["301"])
        unset = self.api("get", "/admin/registry/units?unit_type=UNSET", token=self.admin_token)
        self.assert_ok(unset)
        self.assertEqual([row["room"] for row in unset.data["results"]], ["303"])

    def test_tc_int_129_change_is_audited(self):
        """TC-INT-129 / AC-097-06：修改类型/面积写清册变更审计，不影响既有认证。"""
        unit = self.make_registry_unit()
        owner = self.add_owner(unit, "张伟", ["13800000015"])
        user, token = self.make_user(phone="13800000015")
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=token), 201)
        resp = self.api("patch", f"/admin/registry/units/{unit.id}",
                        {"unit_type": "APARTMENT", "area": "90.00"}, token=self.admin_token)
        self.assert_ok(resp)
        self.assertTrue(AuditLog.objects.filter(action="REGISTRY_UNIT_CHANGED",
                                                object_id=str(unit.id)).exists())
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, ended_at__isnull=True).exists())

    def test_tc_int_130_parking_area_required_and_residence_optional(self):
        """TC-INT-130 / AC-097-07、AC-097-08：车位必填面积；住宅可为空且显示未登记。"""
        denied = self.api("post", "/admin/registry/units",
                          {"building": "车库", "room": "A-089", "unit_type": "PARKING"},
                          token=self.admin_token)
        self.assert_error(denied, 400, "INVALID_VALUE")
        self.assertEqual(denied.data["message"], "车位须填写专有部分面积")
        self.assertEqual(RegistryUnit.objects.count(), 0)
        created = self.api("post", "/admin/registry/units",
                           {"building": "1", "room": "307", "unit_type": "RESIDENCE"},
                           token=self.admin_token)
        self.assert_ok(created, 201)
        self.assertIsNone(created.data["area"])
        self.assertEqual(created.data["unit_type_label"], "住宅")


class OptionTests(RegistryImportTestBase):
    def test_tc_int_131_parking_specific_part(self):
        """TC-INT-131 / AC-098-01：无单元/楼层的车位标识为“车库A-088”。"""
        resp = self.api("post", "/admin/registry/units",
                        {"building": "车库", "unit_no": "", "floor": "", "room": "A-088",
                         "unit_type": "PARKING", "area": "12.50"}, token=self.admin_token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["specific_part"], "车库A-088")

    def test_tc_int_132_options_skip_empty_levels(self):
        """TC-INT-132 / AC-098-02：车库下单元与楼层为空，直接返回户号。"""
        self.make_registry_unit(building="车库", unit_no="", floor="", room="A-088",
                                unit_type="PARKING", area=Decimal("12.50"))
        _, token, _ = self.make_owner()
        resp = self.api("get", "/units/options?building=车库", token=token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["level"], "room")
        self.assertEqual(resp.data["skipped"], ["unit_no", "floor"])
        self.assertEqual(resp.data["options"][0]["value"], "A-088")
        self.assertIn("车位", resp.data["options"][0]["label"])

    def test_tc_int_133_options_has_empty_and_reachable_shop(self):
        """TC-INT-133 / AC-098-03：混合楼栋不出现空选项，空单元商铺仍可到达。"""
        self.make_registry_unit(room="301", unit_type="RESIDENCE", area=Decimal("89.50"))
        self.make_registry_unit(unit_no="", floor="", room="B-001", unit_type="SHOP")
        _, token, _ = self.make_owner()
        units = self.api("get", "/units/options?building=1", token=token)
        self.assert_ok(units)
        self.assertEqual(units.data["level"], "unit_no")
        self.assertTrue(units.data["has_empty"])
        self.assertNotIn("", [item["value"] for item in units.data["options"]])
        shops = self.api("get", "/units/options?building=1&unit_no=", token=token)
        self.assert_ok(shops)
        self.assertEqual(shops.data["level"], "room")
        self.assertIn("B-001", [item["value"] for item in shops.data["options"]])

    def test_tc_int_134_import_missing_levels(self):
        """TC-INT-134 / AC-098-04：缺楼栋/户号失败；单元楼层为空不报错。"""
        resp = self.import_rows([row(building="", name="甲"),
                                 row(room="", name="乙"),
                                 row(unit="", floor="", name="丙", building="车库", room="A-090",
                                     type_="车位", area="12.00")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 2)
        reasons = {e["row"]: e["reason"] for e in resp.data["errors"]}
        self.assertEqual(reasons[2], "缺少楼栋")
        self.assertEqual(reasons[3], "缺少户号")
        self.assertEqual(resp.data["imported"], 1)
        self.assertTrue(RegistryUnit.objects.filter(specific_part="车库A-090").exists())

    def test_tc_int_135_legacy_four_levels(self):
        """TC-INT-135 / AC-132-04：四级齐全时按新规则生成标识，逐级选择不变。"""
        unit = self.make_registry_unit(building="1", unit_no="2", floor="3", room="301",
                                       unit_type="RESIDENCE", area=Decimal("89.50"))
        self.assertEqual(unit.specific_part, "1栋2单元3层301号")
        _, token, _ = self.make_owner()
        resp = self.api("get", "/units/options?building=1&unit_no=2&floor=3", token=token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["level"], "room")
        self.assertEqual(resp.data["options"][0]["value"], "301")

    def test_tc_int_136_import_parking_row(self):
        """TC-INT-136 / AC-098-06：车位一行导入成功且业主登记。"""
        resp = self.import_rows([row(building="车库", unit="", floor="", room="A-088",
                                     type_="车位", area="12.50", name="赵云", phone="")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 0)
        unit = RegistryUnit.objects.get()
        self.assertEqual(unit.specific_part, "车库A-088")
        self.assertEqual([o.name for o in self.owners_of(unit)], ["赵云"])

    def test_tc_int_314_floor_options_numeric_order(self):
        """TC-INT-314 / AC-098-02：楼层选项按数值升序（负层在前），不按字符串排序。"""
        for floor in ("33", "4", "10", "2", "负1", "负2"):
            self.make_registry_unit(building="1", unit_no="1", floor=floor, room=f"{floor}-01",
                                    unit_type="RESIDENCE", area=Decimal("89.50"))
        _, token, _ = self.make_owner()
        resp = self.api("get", "/units/options?building=1&unit_no=1", token=token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["level"], "floor")
        self.assertEqual([item["value"] for item in resp.data["options"]],
                         ["负2", "负1", "2", "4", "10", "33"])


class ReimportTests(RegistryImportTestBase):
    def test_tc_int_137_reimport_adds_owner(self):
        """TC-INT-137 / AC-099-01：既有业主保留，新姓名追加，单元计入更新。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟")
        self.add_owner(unit, "李娜")
        resp = self.import_rows([row(name="王强")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["updated"], 1)
        self.assertEqual([o.name for o in self.owners_of(unit)], ["张伟", "李娜", "王强"])

    def test_tc_int_138_same_name_appends_phone(self):
        """TC-INT-138 / AC-099-02：同名追加手机号，业主数不变。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000016"])
        resp = self.import_rows([row(name="张伟", phone="13800000017")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["owners_created"], 0)
        self.assertEqual(resp.data["phones_created"], 1)
        owners = self.owners_of(unit)
        self.assertEqual(len(owners), 1)
        self.assertEqual(sorted(p.phone for p in owners[0].phones.all()),
                         ["13800000016", "13800000017"])

    def test_tc_int_139_type_area_update_listed(self):
        """TC-INT-139 / AC-099-03：类型与面积改为文件值，并列出修改字段。"""
        unit = self.make_registry_unit(unit_type="RESIDENCE", area=Decimal("89.50"))
        resp = self.import_rows([row(type_="公寓", area="90.00")])
        self.assert_ok(resp)
        unit.refresh_from_db()
        self.assertEqual(unit.unit_type, "APARTMENT")
        self.assertEqual(unit.area, Decimal("90.00"))
        self.assertEqual(resp.data["changes"],
                         [{"specific_part": unit.specific_part, "fields": ["unit_type", "area"]}])

    def test_tc_int_140_empty_type_area_keeps_existing(self):
        """TC-INT-140 / AC-099-04：文件类型/面积为空时既有值不变。"""
        unit = self.make_registry_unit(unit_type="RESIDENCE", area=Decimal("89.50"))
        resp = self.import_rows([row(type_="", area="", name="新业主")])
        self.assert_ok(resp)
        unit.refresh_from_db()
        self.assertEqual((unit.unit_type, unit.area), ("RESIDENCE", Decimal("89.50")))
        self.assertEqual(resp.data["changes"], [])

    def test_tc_int_141_import_never_deletes_owners(self):
        """TC-INT-141 / AC-099-05：文件未包含的既有业主与其认证保留。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "李娜", ["13800000018"])
        user, token = self.make_user(phone="13800000018")
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=token), 201)
        self.assert_ok(self.import_rows([row(name="王强")]))
        self.assertIn("李娜", [o.name for o in self.owners_of(unit)])
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, ended_at__isnull=True).exists())

    def test_tc_int_142_phone_conflict_other_owner(self):
        """TC-INT-142 / AC-099-07：手机号属于同单元另一位业主时该行失败。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000019"])
        resp = self.import_rows([row(name="李娜", phone="13800000019")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 1)
        self.assertEqual(resp.data["errors"][0]["reason"], "手机号已登记给同一专有部分的另一位业主")
        self.assertEqual([o.name for o in self.owners_of(unit)], ["张伟"])

    def test_tc_int_143_trailing_space_same_name(self):
        """TC-INT-143 / AC-099-08：“张伟 ”与既有“张伟”同一人；“张伟（二）”为新增。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟")
        resp = self.import_rows([row(name="张伟 "), row(name="张伟（二）")])
        self.assert_ok(resp)
        self.assertEqual(sorted(o.name for o in self.owners_of(unit)), sorted(["张伟", "张伟（二）"]))
        self.assertEqual(len(self.owners_of(unit)), 2)


class DryRunTests(RegistryImportTestBase):
    def _hundred_rows(self):
        rows = []
        for index in range(100):
            rows.append(row(room=str(1000 + index), name=f"业主{index}",
                            phone=f"135{index:08d}"))
        return rows

    def test_tc_int_144_dry_run_no_write_and_same_numbers(self):
        """TC-INT-144 / AC-100-01、AC-100-03：预检不写库，数字与正式导入一致。"""
        rows = self._hundred_rows()
        preview = self.import_rows(rows, dry_run=True)
        self.assert_ok(preview)
        self.assertTrue(preview.data["dry_run"])
        self.assertEqual((preview.data["imported"], preview.data["updated"],
                          preview.data["failed"]), (100, 0, 0))
        self.assertEqual(RegistryUnit.objects.count(), 0)
        commit = self.import_rows(rows)
        self.assert_ok(commit)
        self.assertFalse(commit.data["dry_run"])
        for key in ("imported", "updated", "failed", "rows_total", "owners_created", "phones_created"):
            self.assertEqual(preview.data[key], commit.data[key], key)
        self.assertEqual(RegistryUnit.objects.count(), 100)

    def test_tc_int_145_error_rows_reported(self):
        """TC-INT-145 / AC-100-02：第 7/12/15 行错误原因正确，失败计数 3。"""
        rows = [row(room=str(2000 + index), name=f"业主{index}") for index in range(15)]
        rows[5][7] = "123"                       # 第 7 行：手机号格式
        rows[10][4] = "别墅"                      # 第 12 行：类型越界
        rows[13][4] = "车位"                      # 第 15 行：车位无面积
        rows[13][5] = ""
        resp = self.import_rows(rows, dry_run=True)
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 3)
        errors = {e["row"]: e["reason"] for e in resp.data["errors"]}
        self.assertEqual(errors[7], "手机号格式不正确")
        self.assertIn("专有部分类型不在允许范围内", errors[12])
        self.assertEqual(errors[15], "车位的专有部分面积不能为空")

    def test_tc_int_146_bad_phone_row_counted_once(self):
        """TC-INT-146 / AC-100-04：一行三个手机号其中一个非法，只计一次失败且不计新增。"""
        resp = self.import_rows([row(name="张伟", phone="13800000020;bad;13900000021")])
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 1)
        self.assertEqual(resp.data["imported"], 0)
        self.assertEqual(resp.data["updated"], 0)
        self.assertEqual(RegistryUnit.objects.count(), 0)


class LegacyCompatibilityTests(RegistryImportTestBase):
    def test_tc_int_147_legacy_unit_listed_unset(self):
        """TC-INT-147 / AC-101-01：既有专有部分类型与面积为空时返回 null（前端显示未登记）。"""
        unit = self.make_registry_unit()
        detail = self.get_admin_unit(unit.id)
        self.assertIsNone(detail["unit_type"])
        self.assertIsNone(detail["unit_type_label"])
        self.assertIsNone(detail["area"])

    def test_tc_int_148_legacy_certification_unchanged(self):
        """TC-INT-148 / AC-101-02：既有专有部分的手机号认证行为不变。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000022"])
        user, token = self.make_user(phone="13800000022")
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["specific_part"], unit.specific_part)

    def test_tc_int_149_backfill_keeps_membership(self):
        """TC-INT-149 / AC-101-03：补录类型与面积不影响既有业主与认证。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000023"])
        user, token = self.make_user(phone="13800000023")
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=token), 201)
        membership = Membership.objects.get(user=user, unit=unit)
        self.assert_ok(self.api("patch", f"/admin/registry/units/{unit.id}",
                                {"unit_type": "RESIDENCE", "area": "88.00"}, token=self.admin_token))
        membership.refresh_from_db()
        self.assertIsNone(membership.ended_at)
        self.assertEqual(len(self.owners_of(unit)), 1)

    def test_tc_int_150_edit_owners_without_type(self):
        """TC-INT-150 / AC-101-04：未登记类型的既有专有部分可只改业主。"""
        unit = self.make_registry_unit()
        owner = self.add_owner(unit, "张伟")
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                        {"owners": [{"id": owner.id, "name": "张伟", "phones": ["13800000024"]},
                                    {"name": "李娜"}]}, token=self.admin_token)
        self.assert_ok(resp)
        unit.refresh_from_db()
        self.assertIsNone(unit.unit_type)
        self.assertIsNone(unit.area)
        self.assertEqual(len(self.owners_of(unit)), 2)


class AutoBindTests(RegistryImportTestBase):
    def setUp(self):
        super().setUp()
        set_wechat_client(FakeWeChatClient())
        self.addCleanup(set_wechat_client, None)

    def test_tc_int_151_register_auto_binds_head(self):
        """TC-INT-151 / AC-102-01：清册手机号注册即认证为户主，来源清册。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000031"])
        _, token, _ = self.register("13800000031")
        user = self.user_of(token)
        membership = Membership.objects.get(user=user, unit=unit)
        self.assertEqual((membership.role, membership.source), ("HEAD", "REGISTRY"))
        me = self.api("get", "/me", token=token)
        self.assert_ok(me)
        self.assertIn("产权业主", me.data["identities"]["labels"])

    def test_tc_int_152_register_binds_all_units(self):
        """TC-INT-152 / AC-102-02：同一手机号登记 3 个专有部分，全部绑定且相互独立。"""
        phone = "13800000032"
        units = []
        for index in range(3):
            unit = self.make_registry_unit(room=str(201 + index))
            self.add_owner(unit, f"业主张{index}", [phone])
            units.append(unit)
        user, token, _ = self.register(phone)
        user = self.user_of(token)
        self.assertEqual(Membership.objects.filter(user=user, ended_at__isnull=True).count(), 3)
        self.assertEqual(set(Membership.objects.filter(user=user).values_list("unit_id", flat=True)),
                         {unit.id for unit in units})
        self.assertEqual(Membership.objects.filter(user=user, role="HEAD").count(), 3)

    def test_tc_int_153_second_owner_keeps_single_head(self):
        """TC-INT-153 / AC-102-03：已有户主时第二位业主为普通产权业主。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000033"])
        self.add_owner(unit, "李娜", ["13800000034"])
        _, token_first, _ = self.register("13800000033")
        first = self.user_of(token_first)
        _, token_second, _ = self.register("13800000034")
        second = self.user_of(token_second)
        self.assertEqual(Membership.objects.get(user=first, unit=unit).role, "HEAD")
        self.assertEqual(Membership.objects.get(user=second, unit=unit).role, "OWNER")
        self.assertEqual(Membership.objects.filter(unit=unit, head_slot=1, ended_at__isnull=True).count(), 1)

    def test_tc_int_154_register_without_registry_phone(self):
        """TC-INT-154 / AC-102-04：不在清册的手机号注册不产生身份也不报错。"""
        _, token, phone = self.register("13800000035")
        self.assertEqual(Membership.objects.filter(user=self.user_of(token)).count(), 0)

    def test_tc_int_155_wechat_bind_phone_auto_binds(self):
        """TC-INT-155 / AC-102-06：微信用户首次绑定清册手机号后自动认证。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000036"])
        wx = self.api("post", "/auth/wechat/miniapp", {"code": "wx-registry-bind"})
        self.assert_ok(wx)
        code = self.request_me_code(wx.data["token"], "BIND_PHONE", target="13800000036")
        bound = self.api("post", "/me/phone/bind", {"phone": "13800000036", "code": code},
                         token=wx.data["token"])
        self.assert_ok(bound)
        self.assertFalse(bound.data["merged"])
        self.assertEqual([item["unit_id"] for item in bound.data["auto_bound"]], [unit.id])
        self.assertEqual(Membership.objects.filter(user_id=wx.data["user"]["id"], unit=unit,
                                                   role="HEAD").count(), 1)

    def test_tc_int_156_resident_upgraded(self):
        """TC-INT-156 / AC-102-07：同住人在自动绑定后升级为产权业主。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000037"])
        wx = self.api("post", "/auth/wechat/miniapp", {"code": "wx-registry-resident"})
        self.assert_ok(wx)
        user_id = wx.data["user"]["id"]
        Membership.objects.create(user_id=user_id, unit=unit, role="RESIDENT",
                                  source="APPLICATION", active_slot=1)
        code = self.request_me_code(wx.data["token"], "BIND_PHONE", target="13800000037")
        bound = self.api("post", "/me/phone/bind", {"phone": "13800000037", "code": code},
                         token=wx.data["token"])
        self.assert_ok(bound)
        self.assertEqual(Membership.objects.get(user_id=user_id, unit=unit, ended_at__isnull=True).role,
                         "HEAD")
        self.assertEqual(Membership.objects.get(user_id=user_id, unit=unit, ended_at__isnull=False)
                         .end_reason, "UPGRADED")

    def test_tc_int_157_auto_bind_audit_and_no_pii(self):
        """TC-INT-157 / AC-102-08：审计记录来源为清册自动绑定，提示与日志不含姓名与手机号明文。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "张伟", ["13800000038"])
        user, token, _ = self.register("13800000038")
        log = AuditLog.objects.filter(action="CERTIFY_BY_REGISTRY").order_by("id").last()
        self.assertIsNotNone(log)
        self.assertEqual(log.detail["origin_label"], "清册自动绑定")
        detail = str(log.detail)
        self.assertNotIn("张伟", detail)
        self.assertNotIn("13800000038", detail)
        me = self.api("get", "/me", token=token)
        self.assertNotIn("张伟", me.content.decode("utf-8"))
        self.assertNotIn("13800000038", me.content.decode("utf-8"))

    def test_tc_int_158_later_registry_add_does_not_bind(self):
        """TC-INT-158 / AC-102-09、AC-104-04：清册后补手机号不自动绑定，仍可手动认证。"""
        user, token = self.make_user(phone="13800000039")
        unit = self.make_registry_unit()
        owner = self.add_owner(unit, "王芳")
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                        {"owners": [{"id": owner.id, "name": "王芳", "phones": ["13800000039"]}]},
                        token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(Membership.objects.filter(user=user).count(), 0)
        certified = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_ok(certified, 201)
        self.assertEqual(certified.data["role"], "HEAD")

    def test_tc_int_166_phone_bind_without_wechat_auto_binds(self):
        """TC-INT-166 / AC-102-10：已注册未绑定手机号的用户首次绑定清册手机号后自动认证。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "钱七", ["13800000040"])
        user = User.objects.create(account_no=next_account_no(), phone=None, nickname="待绑定用户")
        token = self.token_of(user)
        code = self.request_me_code(token, "BIND_PHONE", target="13800000040")
        bound = self.api("post", "/me/phone/bind", {"phone": "13800000040", "code": code}, token=token)
        self.assert_ok(bound)
        self.assertEqual([item["unit_id"] for item in bound.data["auto_bound"]], [unit.id])
        self.assertEqual(Membership.objects.filter(user=user, unit=unit, role="HEAD").count(), 1)
        self.assertTrue(AuditLog.objects.filter(action="CERTIFY_BY_REGISTRY").exists())


class OptionLabelAndAppealTests(RegistryImportTestBase):
    def test_tc_int_159_room_labels(self):
        """TC-INT-159 / AC-103-01、AC-103-02、AC-103-03：末级选项含类型与面积；未登记只显示户号。"""
        self.make_registry_unit(room="301", unit_type="RESIDENCE", area=Decimal("89.50"))
        self.make_registry_unit(room="302", unit_type=None, area=None)
        self.make_registry_unit(building="车库", unit_no="", floor="", room="A-088",
                                unit_type="PARKING", area=Decimal("12.50"))
        self.add_owner(RegistryUnit.objects.get(room="A-088"), "赵云", ["13800000040"])
        _, token, _ = self.make_owner()
        rooms = self.api("get", "/units/options?building=1&unit_no=1&floor=1", token=token)
        self.assert_ok(rooms)
        labels = {item["value"]: item["label"] for item in rooms.data["options"]}
        self.assertEqual(labels["301"], "301（住宅 89.50 ㎡）")
        self.assertEqual(labels["302"], "302")
        parking = self.api("get", "/units/options?building=车库", token=token)
        self.assert_ok(parking)
        self.assertEqual(parking.data["options"][0]["label"], "A-088（车位 12.50 ㎡）")
        text = parking.content.decode("utf-8")
        self.assertNotIn("赵云", text)
        self.assertNotIn("13800000040", text)

    def test_tc_int_160_options_require_login(self):
        """TC-INT-160 / AC-103-04：未登录请求选项被拒绝。"""
        self.make_registry_unit()
        resp = self.api("get", "/units/options?building=1")
        self.assertIn(resp.status_code, (401, 403))

    def test_tc_int_161_phone_mismatch_points_to_appeal(self):
        """TC-INT-161 / AC-104-01：清册无此手机号时提示申诉入口。"""
        unit = self.make_registry_unit()
        self.add_owner(unit, "王芳")
        user, token = self.make_user(phone="13900000009")
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_error(resp, 422, "PHONE_NOT_IN_REGISTRY")
        self.assertEqual(resp.data["message"], "手机号与清册不一致，可提交产权申诉")
        self.assertTrue(resp.data["details"]["appeal_available"])

    def test_tc_int_162_certify_requires_phone(self):
        """TC-INT-162 / AC-104-03：账号未绑定手机号时提示先绑定。"""
        unit = self.make_registry_unit()
        user = User.objects.create(account_no=next_account_no(), phone=None)
        token = self.token_of(user)
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_error(resp, 409, "PHONE_REQUIRED")
        self.assertEqual(resp.data["message"], "请先绑定手机号")

    def test_tc_int_163_admin_adds_phone_then_certify(self):
        """TC-INT-163 / AC-104-04：管理员补录手机号后同一用户认证通过，无需申诉。"""
        unit = self.make_registry_unit()
        owner = self.add_owner(unit, "王芳")
        user, token = self.make_user(phone="13900000010")
        self.assert_error(self.api("post", "/certifications", {"unit_id": unit.id}, token=token),
                          422, "PHONE_NOT_IN_REGISTRY")
        self.assert_ok(self.api("put", f"/admin/registry/units/{unit.id}/owners",
                                {"owners": [{"id": owner.id, "name": "王芳",
                                             "phones": ["13900000010"]}]},
                                token=self.admin_token))
        self.assertEqual(Membership.objects.filter(user=user).count(), 0)
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["role"], "HEAD")
