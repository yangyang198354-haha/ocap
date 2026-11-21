"""PHASE_08 集成测试（ocap_owner_auth_v2）：商铺归类（命令 relocate_shops）、选项接口第一/二级、导出命令守卫。

关联 US-193、US-194、US-195（AC-195-01~07）、US-196（AC-196-01~07）。MOD-111/112/113，IFC-299~303。
SQLite 测试库 + call_command；备份与导出文件只写临时目录；全部合成数据，不连接测试机（画像 P8）。
退出码经 CommandError.returncode 断言：1 参数错误、2 冲突/数量不符/核对失败、3 备份或位置问题。
"""
import json
import os
import stat
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.registry.ordering import SHOP_BUILDING
from apps.residency.models import Appeal, Membership
from tests.support import ApiTestBase, next_phone

OWNER = "商铺测试业主"


def snapshot():
    return list(RegistryUnit.objects.order_by("id").values_list(
        "id", "building", "unit_no", "floor", "room", "specific_part", "unit_type", "area",
        "created_at", "updated_at"))


class ShopFixtureMixin:
    """合成清册：1/2/10 栋内的商铺（含 4347 类负层商铺）、门牌型商铺、非商铺各类记录。"""

    def build_registry(self):
        mk = RegistryUnit.objects.create
        self.shop_neg = mk(building="1", unit_no="", floor="负1", room="1139", unit_type="SHOP", area="30.00")
        self.shop_1 = mk(building="1", unit_no="", floor="1", room="105", unit_type="SHOP", area="40.00")
        self.shop_2 = mk(building="2", unit_no="", floor="1", room="5", unit_type="SHOP")
        self.shop_10 = mk(building="10", unit_no="", floor="1", room="8", unit_type="SHOP")
        self.shop_door = mk(building="建设南路142号", unit_no="", floor="", room="1", unit_type="SHOP")
        self.res = mk(building="1", unit_no="1", floor="3", room="301", unit_type="RESIDENCE", area="80.00")
        self.apt = mk(building="10", unit_no="", floor="5", room="502", unit_type="APARTMENT")
        self.no_type = mk(building="1", unit_no="", floor="1", room="109", unit_type=None)
        self.other = mk(building="2", unit_no="", floor="1", room="110", unit_type="OTHER")
        self.park = mk(building="地下车位", unit_no="", floor="负一", room="1", unit_type="PARKING", area="12.00")
        self.shop_ids = {self.shop_neg.id, self.shop_1.id, self.shop_2.id, self.shop_10.id, self.shop_door.id}
        owner = RegistryOwner.objects.create(unit=self.shop_neg, name=OWNER)
        self.phone = next_phone()
        RegistryPhone.objects.create(unit=self.shop_neg, owner=owner, phone=self.phone)
        self.user = User.objects.create(account_no="7100000001", phone=self.phone)
        self.membership = Membership.objects.create(user=self.user, unit=self.shop_neg, role="OWNER",
                                                    source="REGISTRY", active_slot=1)
        self.applicant = User.objects.create(account_no="7100000002", phone=next_phone())
        self.appeal = Appeal.objects.create(user=self.applicant, unit=self.shop_door, owner_name="申诉产权人")


class ShopCommandBase(ShopFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.build_registry()

    def code_of(self, *args):
        out = StringIO()
        try:
            call_command("relocate_shops", *args, stdout=out)
        except CommandError as exc:
            return exc.returncode, out.getvalue()
        return 0, out.getvalue()

    def kv(self, text):
        return dict(line.split("=", 1) for line in text.splitlines() if "=" in line and "|" not in line)

    def backup_path(self, name="b.jsonl"):
        return str(self.dir / name)

    def apply(self, n=5, name="b.jsonl"):
        return self.code_of("--apply", "--backup", self.backup_path(name), "--expect-changes", str(n))


class ShopDryRunTests(ShopCommandBase):
    def test_tc_int_621_dry_run_reports_and_writes_nothing(self):
        """AC-195-01/07：默认 dry-run 无 INSERT/UPDATE/DELETE，库快照不变；would_change=5（仅商铺类型），其余记录不计入。"""
        before = snapshot()
        with CaptureQueriesContext(connection) as ctx:
            code, out = self.code_of()
        self.assertEqual(code, 0, out)
        writes = [q["sql"] for q in ctx.captured_queries
                  if q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))]
        self.assertEqual(writes, [])
        self.assertEqual(snapshot(), before)
        v = self.kv(out)
        self.assertEqual((v["total_units"], v["shop_units"], v["already_target"], v["would_change"], v["conflicts"]),
                         ("10", "5", "0", "5", "0"))
        self.assertEqual(v["second_level_values"], "4")  # 1栋、2栋、10栋、建设南路142号
        self.assertIn("old_building|1|2", out)
        self.assertIn("floor|负1|1", out)

    def test_tc_int_622_dry_run_output_has_no_personal_data(self):
        """C-59 / AC-195-07：命令输出不含姓名与手机号。"""
        _, out = self.code_of()
        for secret in (OWNER, self.phone, "申诉产权人"):
            self.assertNotIn(secret, out)


class ShopArgumentTests(ShopCommandBase):
    def test_tc_int_623_argument_errors_exit_1_without_touching_db(self):
        """IFC-302：--apply 缺 --backup 或 --expect-changes、--backup 无 --apply、--restore 与 --backup 同用、负数、--list-limit 越界 → 退出码 1，库不变。"""
        before = snapshot()
        cases = [("--apply",), ("--apply", "--backup", self.backup_path()),
                 ("--apply", "--expect-changes", "5"), ("--backup", self.backup_path()),
                 ("--expect-changes", "5"),
                 ("--apply", "--backup", self.backup_path(), "--expect-changes", "-1"),
                 ("--restore", self.backup_path("r.jsonl"), "--backup", self.backup_path("x.jsonl")),
                 ("--list-limit", "0"), ("--list-limit", "100001")]
        for args in cases:
            code, _ = self.code_of(*args)
            self.assertEqual(code, 1, args)
        self.assertEqual(snapshot(), before)
        self.assertEqual(os.listdir(self.dir), [])

    def test_tc_int_624_apply_expect_mismatch_exit_2_and_no_backup(self):
        """AC-195-01：--expect-changes 与计划条数不符 → 退出码 2，库未改动，不生成备份。"""
        before = snapshot()
        code, out = self.apply(n=4)
        self.assertEqual(code, 2, out)
        self.assertEqual(snapshot(), before)
        self.assertEqual(os.listdir(self.dir), [])

    def test_tc_int_625_backup_exists_or_parent_missing_exit_3(self):
        """IFC-302：备份路径已存在或父目录不存在 → 退出码 3，不触库，已存在文件内容不变。"""
        existing = self.dir / "exists.jsonl"
        existing.write_text("old", encoding="utf-8")
        before = snapshot()
        self.assertEqual(self.code_of("--apply", "--backup", str(existing), "--expect-changes", "5")[0], 3)
        self.assertEqual(existing.read_text(encoding="utf-8"), "old")
        missing = str(self.dir / "nope" / "b.jsonl")
        self.assertEqual(self.code_of("--apply", "--backup", missing, "--expect-changes", "5")[0], 3)
        self.assertEqual(snapshot(), before)


class ShopApplyTests(ShopCommandBase):
    def test_tc_int_626_apply_moves_only_shops_and_keeps_origin_and_bindings(self):
        """AC-195-01/02/06、AC-193-02：apply 后专有部分总数、业主数、手机号数、有效认证绑定数不变；楼栋为"商铺"的记录数=5=修正前商铺数；
        其余 5 条记录逐字段不变；原楼栋/门牌在 unit_no（纯数字补"栋"，门牌原样），丢失数=0；4347 类负层商铺标识为 商铺1栋负1层1139号。"""
        total = RegistryUnit.objects.count()
        owners, phones = RegistryOwner.objects.count(), RegistryPhone.objects.count()
        active = Membership.objects.filter(ended_at__isnull=True).count()
        others_before = [r for r in snapshot() if r[0] not in self.shop_ids]
        code, out = self.apply()
        self.assertEqual(code, 0, out)
        v = self.kv(out)
        self.assertEqual((v["moved"], v["lost_origin"]), ("5", "0"))
        self.assertEqual((v["before_units"], v["after_units"]), (str(total), str(total)))
        self.assertEqual(RegistryUnit.objects.count(), total)
        self.assertEqual((RegistryOwner.objects.count(), RegistryPhone.objects.count()), (owners, phones))
        self.assertEqual(Membership.objects.filter(ended_at__isnull=True).count(), active)
        self.assertEqual(RegistryUnit.objects.filter(building=SHOP_BUILDING).count(), 5)
        self.assertEqual([r for r in snapshot() if r[0] not in self.shop_ids], others_before)
        moved = {u.id: u for u in RegistryUnit.objects.filter(id__in=self.shop_ids)}
        self.assertEqual(moved[self.shop_neg.id].specific_part, "商铺1栋负1层1139号")
        self.assertEqual((moved[self.shop_neg.id].building, moved[self.shop_neg.id].unit_no), (SHOP_BUILDING, "1栋"))
        self.assertEqual(moved[self.shop_1.id].unit_no, "1栋")
        self.assertEqual(moved[self.shop_2.id].unit_no, "2栋")
        self.assertEqual(moved[self.shop_10.id].unit_no, "10栋")
        self.assertEqual(moved[self.shop_door.id].unit_no, "建设南路142号")
        self.assertEqual(moved[self.shop_door.id].specific_part, "商铺建设南路142号1号")
        # 楼层、户号、类型、面积不变
        self.assertEqual((moved[self.shop_neg.id].floor, moved[self.shop_neg.id].room,
                          moved[self.shop_neg.id].unit_type, str(moved[self.shop_neg.id].area)),
                         ("负1", "1139", "SHOP", "30.00"))
        # 已认证绑定、待审申诉不受影响
        self.membership.refresh_from_db()
        self.assertEqual((self.membership.unit_id, self.membership.role, self.membership.ended_at),
                         (self.shop_neg.id, "OWNER", None))
        self.appeal.refresh_from_db()
        self.assertEqual((self.appeal.status, self.appeal.unit_id), ("PENDING", self.shop_door.id))
        # 单一审计记录，不含个人信息
        rows = AuditLog.objects.filter(action="REGISTRY_UNIT_CHANGED", object_id="shop_relocation")
        self.assertEqual(rows.count(), 1)
        self.assertEqual(rows[0].detail, {"change": "shop_relocation", "moved": 5})

    def test_tc_int_627_backup_file_secure_and_without_personal_data(self):
        """AC-195-05 / C-59：备份 0600、头部格式为商铺格式、仅含被改的 5 条、不含姓名与手机号；stdout 同样不含。"""
        code, out = self.apply()
        self.assertEqual(code, 0, out)
        path = Path(self.backup_path())
        # POSIX 专属断言：Windows 的 chmod 不生效，由 Linux CI 做真实校验
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        text = path.read_text(encoding="utf-8")
        header = json.loads(text.splitlines()[0])
        self.assertEqual((header["format"], header["records"]), ("ocap-shop-backup/1", 5))
        for secret in (OWNER, self.phone, "申诉产权人"):
            self.assertNotIn(secret, text)
            self.assertNotIn(secret, out)
        ids = {json.loads(line)["id"] for line in text.splitlines()[1:-1]}
        self.assertEqual(ids, self.shop_ids)

    def test_tc_int_628_second_apply_is_idempotent(self):
        """AC-195-04：已执行后再 dry-run would_change=0、already_target=5；再 apply（--expect-changes 0）新增 0、改动 0、库快照不变。"""
        self.assertEqual(self.apply()[0], 0)
        after_first = snapshot()
        code, out = self.code_of()
        v = self.kv(out)
        self.assertEqual((code, v["would_change"], v["already_target"], v["shop_units"]), (0, "0", "5", "5"))
        code, out = self.code_of("--apply", "--backup", self.backup_path("b2.jsonl"), "--expect-changes", "0")
        self.assertEqual(code, 0, out)
        self.assertIn("moved=0", out)
        self.assertEqual(snapshot(), after_first)
        self.assertFalse((self.dir / "b2.jsonl").exists())

    def test_tc_int_629_apply_audit_and_no_other_writes(self):
        """AC-195-01：除 RegistryUnit 更新与 1 条审计外无其他表写入（业主、手机号、绑定、申诉行不变）。"""
        before = (list(RegistryOwner.objects.values_list("id", "name")),
                  list(RegistryPhone.objects.values_list("id", "phone")),
                  list(Membership.objects.values_list("id", "unit_id", "role")),
                  list(Appeal.objects.values_list("id", "unit_id", "status")))
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(self.apply()[0], 0)
        tables = {q["sql"].split()[1 if q["sql"].upper().startswith("UPDATE") else 2].strip('"')
                  for q in ctx.captured_queries
                  if q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))}
        self.assertTrue(tables <= {"registry_registryunit", "core_auditlog"}, tables)
        after = (list(RegistryOwner.objects.values_list("id", "name")),
                 list(RegistryPhone.objects.values_list("id", "phone")),
                 list(Membership.objects.values_list("id", "unit_id", "role")),
                 list(Appeal.objects.values_list("id", "unit_id", "status")))
        self.assertEqual(after, before)


class ShopConflictTests(ShopCommandBase):
    def assert_blocked(self, expected_kind):
        before = snapshot()
        code, out = self.code_of()
        self.assertEqual(code, 2, out)
        self.assertIn(f"conflict|{expected_kind}|", out)
        code, out = self.apply(n=5)
        self.assertEqual(code, 2, out)
        self.assertEqual(snapshot(), before)
        self.assertEqual(os.listdir(self.dir), [])

    def test_tc_int_630_specific_part_conflict_stops_whole_batch(self):
        """AC-195-03：改后标识与既有记录重复 → 整批不执行、列出冲突、库与记录内容不变、无备份文件。"""
        RegistryUnit.objects.create(building=SHOP_BUILDING, unit_no="2栋", floor="1", room="5", unit_type="OTHER")
        self.assert_blocked("specific_part")

    def test_tc_int_631_unit_no_occupied_conflict(self):
        """AC-195-03：原 unit_no 非空的商铺 → unit_no_occupied，整批停止（其余合法记录也不改）。"""
        RegistryUnit.objects.create(building="3", unit_no="A", floor="1", room="1", unit_type="SHOP")
        self.assert_blocked("unit_no_occupied")

    def test_tc_int_632_too_long_conflict(self):
        """AC-195-03：新 unit_no 超过 32 字（32 位数字楼栋补"栋"后 33）→ too_long，整批停止。"""
        RegistryUnit.objects.create(building="1" * 32, unit_no="", floor="1", room="1", unit_type="SHOP")
        self.assert_blocked("too_long")

    def test_tc_int_633_empty_building_conflict(self):
        """AC-195-03：旧楼栋为空的商铺无法保留原信息 → empty_building，整批停止。"""
        RegistryUnit.objects.create(building="", unit_no="", floor="1", room="1", unit_type="SHOP")
        self.assert_blocked("empty_building")

    def test_tc_int_634_one_and_one_dong_spellings_both_map_to_same_second_level_value(self):
        """OQ-01 / AC-194-03：楼栋写法 "1" 与 "1栋" 的商铺（不同户号）补"栋"后同属第二级"1栋"，无冲突、不丢记录；
        同层同户号的两种写法本就因标识相同而无法共存（库唯一约束），故不会造成合并冲突。"""
        other = RegistryUnit.objects.create(building="1栋", unit_no="", floor="1", room="106", unit_type="SHOP")
        code, out = self.code_of()
        self.assertEqual((code, self.kv(out)["conflicts"], self.kv(out)["would_change"]), (0, "0", "6"))
        self.assertEqual(self.apply(n=6)[0], 0)
        self.assertEqual(RegistryUnit.objects.get(id=other.id).unit_no, "1栋")
        self.assertEqual(RegistryUnit.objects.filter(building=SHOP_BUILDING, unit_no="1栋").count(), 3)


class ShopRestoreTests(ShopCommandBase):
    def test_tc_int_635_restore_returns_to_pre_state_exactly(self):
        """AC-195-05：apply 后按备份 --restore --apply，逐记录与修正前一致（差异 0），已认证绑定数不变；--restore 无 --apply 只读。"""
        before = snapshot()
        active = Membership.objects.filter(ended_at__isnull=True).count()
        self.assertEqual(self.apply()[0], 0)
        after_apply = snapshot()
        self.assertNotEqual(after_apply, before)
        code, out = self.code_of("--restore", self.backup_path())
        self.assertEqual((code, self.kv(out)["restored"]), (0, "0"))
        self.assertEqual(snapshot(), after_apply)
        code, out = self.code_of("--restore", self.backup_path(), "--apply")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.kv(out)["restored"], self.kv(out)["differences"]), ("5", "0"))
        self.assertEqual(snapshot(), before)
        self.assertEqual(Membership.objects.filter(ended_at__isnull=True).count(), active)

    def test_tc_int_636_restore_aborts_when_not_in_modified_state_or_bad_backup(self):
        """AC-195-05：记录当前不是修正后状态 → 退出码 2 且库不变；备份缺失 → 3；备份内容被改动（摘要不符）→ 3。"""
        self.assertEqual(self.apply()[0], 0)
        RegistryUnit.objects.filter(id=self.shop_1.id).update(building="3")
        mid = snapshot()
        code, out = self.code_of("--restore", self.backup_path(), "--apply")
        self.assertEqual(code, 2, out)
        self.assertEqual(snapshot(), mid)
        self.assertEqual(self.code_of("--restore", str(self.dir / "none.jsonl"))[0], 3)
        tampered = self.dir / "t.jsonl"
        tampered.write_text(Path(self.backup_path()).read_text(encoding="utf-8").replace("1139", "9999"),
                            encoding="utf-8")
        self.assertEqual(self.code_of("--restore", str(tampered), "--apply")[0], 3)
        self.assertEqual(snapshot(), mid)


class ShopOptionsTests(ShopFixtureMixin, ApiTestBase):
    """AC-193、AC-194：第一级三大类顺序、1~10 栋不含商铺、商铺第二级与逐级选到目标记录。"""

    def setUp(self):
        super().setUp()
        self.build_registry()
        _, self.token = self.make_user()
        for building in ("3", "4", "5", "6", "7", "8", "9"):
            RegistryUnit.objects.create(building=building, unit_no="1", floor="1", room="101", unit_type="RESIDENCE")
        RegistryUnit.objects.create(building="1", unit_no="2", floor="1", room="102", unit_type="RESIDENCE")
        call_command("relocate_shops", "--apply", "--backup", str(Path(tempfile.mkdtemp()) / "b.jsonl"),
                     "--expect-changes", "5", stdout=StringIO())

    def options(self, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return self.assert_ok(self.api("get", f"/units/options?{query}" if query else "/units/options",
                                       token=self.token)).json()

    def walk(self, building):
        """逐级选到户号，返回 (各级 level 序列, 叶子 options)。"""
        levels, params = [], {"building": building}
        body = self.options(**params)
        while body["level"] != "room":
            levels.append(body["level"])
            params[body["level"]] = body["options"][0]["value"]
            body = self.options(**params)
        return levels, body["options"]

    def test_tc_int_637_first_level_order_and_no_door_plate_entries(self):
        """AC-193-01：第一级依次 1..10、地下车位、商铺（共 12 项），门牌型楼栋不并列出现。"""
        values = [o["value"] for o in self.options()["options"]]
        self.assertEqual(values, [*map(str, range(1, 11)), "地下车位", "商铺"])
        self.assertNotIn("建设南路142号", values)

    def test_tc_int_638_shop_records_leave_numbered_buildings_but_other_types_stay(self):
        """AC-193-02/03：1 栋逐级选到的户号中没有任何商铺；类型为空/其他的记录仍在原栋内；选"商铺"能找到 4347 类商铺。"""
        listed = {}
        for building in ("1", "2", "10"):
            params = {"building": building}
            ids = set()

            def descend(extra):
                body = self.options(**{**params, **extra})
                if body["level"] == "room":
                    ids.update(o["unit_id"] for o in body["options"])
                    return
                values = [o["value"] for o in body["options"]] + ([""] if body["has_empty"] else [])
                skipped = {level: "" for level in body["skipped"]}  # 客户端对被跳过的空层级回传空串
                for value in values:
                    descend({**extra, **skipped, body["level"]: value})
            descend({})
            listed[building] = ids
        self.assertEqual(listed["1"] & self.shop_ids, set())
        self.assertIn(self.no_type.id, listed["1"])
        self.assertIn(self.other.id, listed["2"])
        self.assertIn(self.apt.id, listed["10"])
        self.assertIn(self.res.id, listed["1"])
        levels, leaves = self.walk("商铺")
        self.assertEqual(levels[0], "unit_no")
        found = set()

        def collect(extra):
            body = self.options(building="商铺", **extra)
            if body["level"] == "room":
                found.update(o["unit_id"] for o in body["options"])
                return
            values = [o["value"] for o in body["options"]] + ([""] if body["has_empty"] else [])
            skipped = {level: "" for level in body["skipped"]}
            for value in values:
                collect({**extra, **skipped, body["level"]: value})
        collect({})
        self.assertEqual(found, self.shop_ids)  # 无重复无遗漏（AC-194-03）
        self.assertIn(self.shop_neg.id, found)

    def test_tc_int_639_shop_second_level_label_order_and_other_levels_have_no_label(self):
        """AC-194-01、IFC-300：商铺第二级 1栋<2栋<10栋<建设南路142号，带 level_label="楼栋/门牌"；其他楼栋第二级响应不含该键；
        AC-194-04：改选 2 栋后不残留商铺原楼栋选项。"""
        body = self.options(building="商铺")
        self.assertEqual(body["level"], "unit_no")
        self.assertEqual(body["level_label"], "楼栋/门牌")
        self.assertEqual([o["value"] for o in body["options"]], ["1栋", "2栋", "10栋", "建设南路142号"])
        self.assertFalse(body["has_empty"])
        for building in ("1", "2"):
            other = self.options(building=building)
            self.assertNotIn("level_label", other)
        two = self.options(building="2")
        self.assertEqual(two["level"], "floor")
        self.assertNotIn("建设南路142号", [o["value"] for o in two["options"]])
        self.assertNotIn("level_label", self.options(building="商铺", unit_no="1栋"))

    def test_tc_int_640_door_plate_shop_skips_empty_levels(self):
        """AC-194-02：门牌型商铺（无楼层）自动跳过空层级，直接给出户号选项，选项即该商铺。"""
        body = self.options(building="商铺", unit_no="建设南路142号")
        self.assertEqual(body["level"], "room")
        self.assertEqual(body["skipped"], ["floor"])
        self.assertEqual([o["unit_id"] for o in body["options"]], [self.shop_door.id])
        self.assertEqual(body["options"][0]["unit_type"], "SHOP")

    def test_tc_int_641_no_shop_records_no_shop_option_and_other_text_building_after_shop(self):
        """AC-193-04/05：新增第四种楼栋"配套用房"排在商铺之后；清册无商铺时不出现"商铺"，其余顺序不变、接口无报错。"""
        RegistryUnit.objects.create(building="配套用房", unit_no="", floor="1", room="1", unit_type="OTHER")
        values = [o["value"] for o in self.options()["options"]]
        self.assertEqual(values[-3:], ["地下车位", "商铺", "配套用房"])
        RegistryUnit.objects.filter(building=SHOP_BUILDING).delete()
        values = [o["value"] for o in self.options()["options"]]
        self.assertNotIn("商铺", values)
        self.assertEqual(values[-2:], ["地下车位", "配套用房"])

    def test_tc_int_642_options_requires_login(self):
        """IFC-300：未登录访问选项接口 401（鉴权不变）。"""
        self.assert_error(self.api("get", "/units/options"), 401)


class ExportGuardTests(ShopFixtureMixin, TestCase):
    """AC-196-01~07：导出位置守卫、商铺未归类守卫、--output-dir 日期命名与不覆盖、归类后导出计数与预检。"""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        os.chmod(self.dir, 0o700)
        self.build_registry()
        # 导出要求每个专有部分都有具名业主
        for unit in RegistryUnit.objects.filter(owners__isnull=True):
            RegistryOwner.objects.create(unit=unit, name=f"合成{unit.id}")

    def run_cmd(self, *args):
        out = StringIO()
        try:
            call_command("export_registry_import_file", *args, stdout=out)
        except CommandError as exc:
            return exc.returncode, out.getvalue()
        return 0, out.getvalue()

    def kv(self, text):
        return dict(line.split("=", 1) for line in text.splitlines() if "=" in line and "|" not in line)

    def relocate(self):
        call_command("relocate_shops", "--apply", "--backup", str(self.dir / "bk.jsonl"),
                     "--expect-changes", "5", stdout=StringIO())

    def test_tc_int_643_unrelocated_shops_block_export_with_exit_2(self):
        """AC-196-01 / ADR-110：存在类型为商铺且楼栋非"商铺"的记录 → 退出码 2、不生成文件、输出 pending_shop_units=5。"""
        code, out = self.run_cmd("--output-dir", str(self.dir))
        self.assertEqual(code, 2, out)
        self.assertEqual(self.kv(out)["pending_shop_units"], "5")
        self.assertEqual([p.name for p in self.dir.iterdir()], [])

    def test_tc_int_644_allow_unrelocated_exports_legacy_structure(self):
        """ADR-110：--allow-unrelocated 放行并输出 structure=legacy；文件生成。"""
        code, out = self.run_cmd("--output-dir", str(self.dir), "--allow-unrelocated")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.kv(out)["structure"], "legacy")
        self.assertEqual(len(list(self.dir.glob("registry_import_*.xlsx"))), 1)

    def test_tc_int_645_after_relocation_export_structure_counts_precheck_and_shop_column(self):
        """AC-196-01/02/06：归类后导出 structure=shop_relocated；专有部分/业主/手机号计数差 0；预检失败 0、新增 0、更新 0；
        楼栋列为"商铺"的行数=5，原楼栋/门牌在"单元"列；导出前后清册不变（只读）；文件权限 0600，文件名含日期。"""
        from apps.registry.import_spec import IMPORT_COLUMNS
        from apps.registry.importing import Deadline, read_rows

        self.relocate()
        before = (snapshot(), RegistryOwner.objects.count(), RegistryPhone.objects.count())
        with CaptureQueriesContext(connection) as ctx:
            code, out = self.run_cmd("--output-dir", str(self.dir))
        self.assertEqual(code, 0, out)
        writes = [q["sql"] for q in ctx.captured_queries
                  if q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))]
        self.assertEqual(writes, [])
        self.assertEqual((snapshot(), RegistryOwner.objects.count(), RegistryPhone.objects.count()), before)
        v = self.kv(out)
        self.assertEqual(v["structure"], "shop_relocated")
        self.assertEqual((v["diff_units"], v["diff_owners_named"], v["diff_phones_distinct"]), ("0", "0", "0"))
        self.assertEqual((v["precheck_rows_failed"], v["precheck_would_create_units"], v["precheck_would_update_units"],
                          v["precheck_would_create_owners"], v["precheck_would_create_phones"], v["relocated_units"]),
                         ("0", "0", "0", "0", "0", "0"))
        files = list(self.dir.glob("registry_import_*.xlsx"))
        self.assertEqual(len(files), 1)
        self.assertRegex(files[0].name, r"^registry_import_\d{8}-\d{6}\.xlsx$")
        # POSIX 专属断言：Windows 的 chmod 不生效，由 Linux CI 做真实校验
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(files[0].stat().st_mode), 0o600)
        raw = files[0].read_bytes()
        rows = [[r.cells[c] for c in IMPORT_COLUMNS] for r in read_rows(files[0].name, raw, Deadline(60))]
        shop_rows = [r for r in rows if r[0] == SHOP_BUILDING]
        self.assertEqual(len(shop_rows), 5)
        self.assertEqual({r[1] for r in shop_rows}, {"1栋", "2栋", "10栋", "建设南路142号"})
        for secret in (OWNER, self.phone):
            self.assertNotIn(secret, out)

    def test_tc_int_646_output_dir_dated_names_never_overwrite(self):
        """AC-196-04：同一目录再次导出不覆盖旧文件——同秒重复退出码 3 且旧文件字节不变；清册变更后旧文件内容不被更新。"""
        self.relocate()
        self.assertEqual(self.run_cmd("--output-dir", str(self.dir))[0], 0)
        first = next(self.dir.glob("registry_import_*.xlsx"))
        original = first.read_bytes()
        RegistryOwner.objects.create(unit=self.res, name="清册后来新增")
        code, _ = self.run_cmd("--output-dir", str(self.dir))
        self.assertIn(code, (0, 3))  # 同一秒内为 3（不覆盖）；跨秒则生成新日期文件，二者都不得改动旧文件
        self.assertEqual(first.read_bytes(), original)
        self.assertGreaterEqual(len(list(self.dir.glob("registry_import_*.xlsx"))), 1)

    def test_tc_int_647_location_guard_rejects_open_dir_and_deploy_root_without_db_access(self):
        """AC-196-03 / AC-196-07：目录权限 755 → 退出码 3；输出路径位于部署根内（目录权限与属主合规，只可能因位置被拒）→ 退出码 3；
        两种情况都不生成文件；守卫先于库访问（零查询）；部署根之外的 700 目录通过（对照，见 TC-INT-645）。"""
        if os.name == "nt":
            self.skipTest("Windows 不支持 POSIX 目录权限语义；由 Linux CI 校验")
        from django.test import override_settings

        open_dir = Path(tempfile.mkdtemp())
        os.chmod(open_dir, 0o755)
        self.addCleanup(lambda: os.rmdir(open_dir) if not any(open_dir.iterdir()) else None)
        deploy_root = Path(tempfile.mkdtemp())
        os.chmod(deploy_root, 0o700)
        (deploy_root / "backend").mkdir(mode=0o700)
        self.addCleanup(lambda: [p.unlink() for p in deploy_root.glob("*") if p.is_file()] or
                        (os.rmdir(deploy_root / "backend"), os.rmdir(deploy_root)))
        with override_settings(BASE_DIR=deploy_root / "backend", MEDIA_ROOT=str(deploy_root / "backend" / "var")):
            with CaptureQueriesContext(connection) as ctx:
                code, _ = self.run_cmd("--output-dir", str(open_dir))
                code2, _ = self.run_cmd("--output-dir", str(deploy_root))
        self.assertEqual((code, code2), (3, 3))
        self.assertEqual(list(open_dir.iterdir()), [])
        self.assertEqual(list(deploy_root.glob("*.xlsx")), [])
        self.assertEqual(len(ctx.captured_queries), 0)

    def test_tc_int_648_output_args_exclusive(self):
        """IFC-303：--output 与 --output-dir 都不给或都给 → CommandError（参数错误）。"""
        with self.assertRaises(CommandError):
            call_command("export_registry_import_file", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("export_registry_import_file", "--output", str(self.dir / "a.csv"),
                         "--output-dir", str(self.dir), stdout=StringIO())

    def test_tc_int_649_leading_zero_cells_preserved_after_relocation(self):
        """AC-196-06：归类后导出文件中 "0801"、"13800000000" 仍为文本原值，往返差异 0。"""
        from apps.registry.import_spec import IMPORT_COLUMNS
        from apps.registry.importing import Deadline, read_rows

        unit = RegistryUnit.objects.create(building="3", unit_no="01", floor="08", room="0801", unit_type="RESIDENCE")
        owner = RegistryOwner.objects.create(unit=unit, name="前导零测试")
        RegistryPhone.objects.create(unit=unit, owner=owner, phone="13800000000")
        self.relocate()
        code, out = self.run_cmd("--output-dir", str(self.dir))
        self.assertEqual(code, 0, out)
        path = next(self.dir.glob("registry_import_*.xlsx"))
        rows = {r.cells["业主姓名"]: r for r in read_rows(path.name, path.read_bytes(), Deadline(60))}
        cells = rows["前导零测试"].cells
        self.assertEqual((cells["单元"], cells["楼层"], cells["户号"], cells["手机号"]),
                         ("01", "08", "0801", "13800000000"))
        self.assertEqual(self.kv(out)["roundtrip_mismatches"], "0")
