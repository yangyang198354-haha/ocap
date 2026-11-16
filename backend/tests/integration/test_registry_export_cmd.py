"""PHASE_08 集成测试：命令 export_registry_import_file（MOD-110，IFC-296/297，AUTH-01）。

SQLite 测试库 + call_command；输出文件写到临时目录（不写仓库根）；全部合成数据，不连接测试机。
关联 US-187（AC-187-01~08）、US-188（与 AC-187-05 联动）；CR-004（--allow-gaps 计数差只报告）。
退出码经 CommandError.returncode 断言：1 参数错误、2 冲突/无法表达/自检不通过、3 目标文件问题。
"""
import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.core.models import AuditLog
from apps.registry import exporting
from apps.registry.import_spec import IMPORT_COLUMNS
from apps.registry.importing import Deadline, read_rows
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit

REPO = Path(__file__).resolve().parents[3]
NAMES = ["甲测试", "乙测试", "丙测试", "丁测试", "戊测试", "己测试"]
PHONES = ["13800000000", "13800000001", "13900000002", "13900000003", "13700000004"]


def owner(unit, name, phones=()):
    o = RegistryOwner.objects.create(unit=unit, name=name)
    for phone in phones:
        RegistryPhone.objects.create(unit=unit, owner=o, phone=phone)
    return o


def db_state():
    return (RegistryUnit.objects.count(), RegistryOwner.objects.count(), RegistryPhone.objects.count(),
            AuditLog.objects.count(),
            list(RegistryUnit.objects.order_by("id").values_list("id", "building", "specific_part", "updated_at")))


class ExportBase(TestCase):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        mk = RegistryUnit.objects.create
        self.p1 = mk(building="1", unit_no="", floor="负一", room="1", unit_type="PARKING", area="12.00")
        self.p2 = mk(building="1栋", unit_no="", floor="负二", room="2", unit_type="PARKING", area="12.50")
        self.p3 = mk(building="1", unit_no="", floor="负1", room="3", unit_type="PARKING", area="12.00")
        self.res = mk(building="1", unit_no="01", floor="08", room="0801", unit_type="RESIDENCE", area="80.00")
        self.shop = mk(building="2", unit_no="1", floor="1", room="1", unit_type=None, area=None)
        owner(self.p1, NAMES[0], [PHONES[0], PHONES[1]])
        owner(self.p2, NAMES[1], [PHONES[0]])
        owner(self.p3, NAMES[2])
        owner(self.res, NAMES[3], [PHONES[2]])
        owner(self.res, NAMES[4], [PHONES[3]])
        owner(self.shop, NAMES[5], [PHONES[4]])

    def run_cmd(self, *args):
        out = StringIO()
        try:
            call_command("export_registry_import_file", *args, stdout=out)
        except CommandError as exc:
            return exc.returncode, out.getvalue()
        return 0, out.getvalue()

    def kv(self, text):
        return dict(line.split("=", 1) for line in text.splitlines() if "=" in line and "|" not in line)

    def path(self, name="registry_import_underground_parking.csv"):
        return str(self.dir / name)

    def file_rows(self, path):
        raw = Path(path).read_bytes()
        return [[r.cells[c] for c in IMPORT_COLUMNS] for r in read_rows(Path(path).name, raw, Deadline(60))]


class ExportSuccessTests(ExportBase):
    def test_tc_int_605_export_rows_relocated_and_other_cells_equal_db(self):
        """AC-187-01：表头=模板 8 列；负层车位楼栋均为地下车位；其余行逐单元格等于库内值；被改行数=3。"""
        path = self.path()
        code, out = self.run_cmd("--output", path)
        self.assertEqual(code, 0, out)
        header = Path(path).read_bytes().decode("utf-8-sig").splitlines()[0]
        self.assertEqual(header, ",".join(IMPORT_COLUMNS))
        rows = self.file_rows(path)
        self.assertEqual(len(rows), 6)
        by_name = {r[6]: r for r in rows}
        for name in NAMES[:3]:
            self.assertEqual(by_name[name][0], "地下车位", name)
            self.assertEqual(by_name[name][4], "车位")
        self.assertEqual(by_name[NAMES[0]], ["地下车位", "", "负一", "1", "车位", "12.00", NAMES[0], "13800000000;13800000001"])
        self.assertEqual(by_name[NAMES[1]][1:4], ["", "负二", "2"])
        self.assertEqual(by_name[NAMES[3]], ["1", "01", "08", "0801", "住宅", "80.00", NAMES[3], "13900000002"])
        self.assertEqual(by_name[NAMES[5]], ["2", "1", "1", "1", "", "", NAMES[5], "13700000004"])
        self.assertEqual(self.kv(out)["relocated_units"], "3")

    def test_tc_int_606_counts_equal_and_precheck_passes_before_relocation(self):
        """AC-187-02/03/05：文件与库的 专有部分/业主/手机号 计数差为 0；预检失败 0；库未执行修正时新增专有部分=3、业主=3、手机号=3。"""
        code, out = self.run_cmd("--output", self.path())
        self.assertEqual(code, 0, out)
        v = self.kv(out)
        self.assertEqual((v["db_units"], v["db_owners_named"], v["db_phones_distinct"]), ("5", "6", "5"))
        self.assertEqual((v["file_units"], v["file_owners_named"], v["file_phones_distinct"]), ("5", "6", "5"))
        self.assertEqual((v["diff_units"], v["diff_owners_named"], v["diff_phones_distinct"]), ("0", "0", "0"))
        self.assertEqual(v["precheck_rows_failed"], "0")
        self.assertEqual((v["precheck_would_create_units"], v["precheck_would_create_owners"],
                          v["precheck_would_create_phones"], v["precheck_would_update_units"]), ("3", "3", "3", "0"))
        self.assertEqual(v["roundtrip_mismatches"], "0")
        # 独立核对：库内计数
        self.assertEqual(RegistryOwner.objects.exclude(name__isnull=True).count(), 6)
        self.assertEqual(RegistryPhone.objects.values("phone").distinct().count(), 5)

    def test_tc_int_607_after_relocation_precheck_creates_nothing_and_file_identical(self):
        """AC-187-05：数据库修正后导出，预检新增专有部分/业主/手机号 = 0，更新 0；文件内容与修正前导出相同。"""
        before_path, after_path = self.path("before.csv"), self.path("after.csv")
        self.run_cmd("--output", before_path)
        call_command("relocate_underground_parking", "--apply", "--backup", str(self.dir / "bk.jsonl"),
                     "--expect-changes", "3", stdout=StringIO())
        code, out = self.run_cmd("--output", after_path)
        self.assertEqual(code, 0, out)
        v = self.kv(out)
        self.assertEqual((v["precheck_would_create_units"], v["precheck_would_create_owners"],
                          v["precheck_would_create_phones"], v["precheck_would_update_units"], v["relocated_units"]),
                         ("0", "0", "0", "0", "0"))
        self.assertEqual(self.file_rows(before_path), self.file_rows(after_path))
        self.assertEqual(Path(before_path).read_bytes(), Path(after_path).read_bytes())

    def test_tc_int_608_export_is_read_only(self):
        """AC-187-02 / C-56：导出期间无 INSERT/UPDATE/DELETE；导出前后记录数、业主数、手机号数、审计数与记录内容不变。"""
        before = db_state()
        with CaptureQueriesContext(connection) as ctx:
            code, _ = self.run_cmd("--output", self.path())
        self.assertEqual(code, 0)
        writes = [q["sql"] for q in ctx.captured_queries
                  if q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))]
        self.assertEqual(writes, [])
        self.assertEqual(db_state(), before)

    def test_tc_int_609_leading_zeros_and_long_numbers_preserved_xlsx_and_csv(self):
        """AC-187-04：'0801'、'01'、'08'、'13800000000' 在 xlsx 与 csv 导出文件中均原样（无前导零丢失、无科学计数、无 .0）。"""
        for name in ("a.xlsx", "a.csv"):
            path = self.path(name)
            code, out = self.run_cmd("--output", path)
            self.assertEqual(code, 0, out)
            rows = {r[6]: r for r in self.file_rows(path)}
            self.assertEqual(rows[NAMES[3]][1:4], ["01", "08", "0801"], name)
            self.assertEqual(rows[NAMES[0]][7], "13800000000;13800000001", name)
            self.assertEqual(self.kv(out)["roundtrip_mismatches"], "0")

    def test_tc_int_620_floor_with_hyphen_fails_precheck_and_writes_nothing(self):
        """AC-187-03 / AC-187-08：库内楼层写成 '-1'（导入校验不接受含“-”的楼层）→ 自检 rows_failed=1，退出码 2，不落盘（宁可不生成也不产出会被拒绝的文件）。"""
        RegistryUnit.objects.create(building="1", unit_no="", floor="-1", room="9", unit_type="PARKING",
                                    area="12.00").owners.create(name="连字符测试")
        code, out = self.run_cmd("--output", self.path())
        self.assertEqual(code, 2)
        self.assertEqual(self.kv(out)["precheck_rows_failed"], "1")
        self.assertEqual(os.listdir(self.dir), [])

    def test_tc_int_610_stdout_has_no_personal_data(self):
        """AC-187-06 / C-55：命令输出只含计数与 id，不含姓名与手机号。"""
        _, out = self.run_cmd("--output", self.path())
        for secret in NAMES + PHONES:
            self.assertNotIn(secret, out)

    def test_tc_int_611_no_file_written_into_repo_root_and_no_part_left(self):
        """AC-187-06：测试输出只落在临时目录；成功后无 .part 残留；本次运行没有在仓库根新增任何文件（比对运行前后文件集合，
        不依赖仓库根既有状态：用户保留在仓库根的导出文件不会影响本用例，GR-C-001-F01）。"""
        before = {p.name for p in REPO.iterdir()}
        self.run_cmd("--output", self.path())
        after = {p.name for p in REPO.iterdir()}
        self.assertEqual(sorted(os.listdir(self.dir)), ["registry_import_underground_parking.csv"])
        self.assertEqual(sorted(after - before), [], "本次导出在仓库根新增了文件")
        self.assertEqual(sorted(before - after), [], "本次导出在仓库根移除了文件")
        self.assertEqual(os.stat(self.path()).st_mode & 0o777, 0o600)


class ExportRefusalTests(ExportBase):
    def test_tc_int_612_gaps_refused_without_allow_gaps(self):
        """AC-187-01/02：存在无具名业主的专有部分 → 退出码 2，不生成文件，输出 gaps 计数与 gap_unit id。"""
        gap = RegistryUnit.objects.create(building="3", unit_no="1", floor="1", room="1")
        code, out = self.run_cmd("--output", self.path())
        self.assertEqual(code, 2)
        self.assertEqual(os.listdir(self.dir), [])
        self.assertEqual(self.kv(out)["gaps_units"], "1")
        self.assertIn(f"gap_unit|{gap.id}", out)

    def test_tc_int_613_unnamed_owner_counts_as_gap(self):
        """IFC-296：业主 name 为空 → gaps_unnamed_owners=1，退出码 2。"""
        RegistryOwner.objects.create(unit=self.p3, name=None)
        code, out = self.run_cmd("--output", self.path())
        self.assertEqual(code, 2)
        self.assertEqual(self.kv(out)["gaps_unnamed_owners"], "1")
        self.assertEqual(os.listdir(self.dir), [])

    def test_tc_int_614_cr004_allow_gaps_reports_difference_without_failing(self):
        """CR-004：--allow-gaps 时文件不含缺口记录，计数差只报告不判失败（diff_units=-1），文件仍生成且预检失败 0。"""
        RegistryUnit.objects.create(building="3", unit_no="1", floor="1", room="1")
        path = self.path()
        code, out = self.run_cmd("--output", path, "--allow-gaps")
        self.assertEqual(code, 0, out)
        v = self.kv(out)
        self.assertEqual((v["gaps_units"], v["db_units"], v["file_units"], v["diff_units"]), ("1", "6", "5", "-1"))
        self.assertEqual(v["precheck_rows_failed"], "0")
        self.assertTrue(Path(path).exists())
        self.assertEqual(len(self.file_rows(path)), 6)

    def test_tc_int_615_conflict_refuses_and_lists(self):
        """AC-187-01 / IFC-296：改后标识与既有记录冲突 → 退出码 2，不生成文件，输出冲突清单。"""
        existing = RegistryUnit.objects.create(building="地下车位", unit_no="", floor="负一", room="1",
                                               unit_type="OTHER")
        owner(existing, "冲突测试")
        code, out = self.run_cmd("--output", self.path())
        self.assertEqual(code, 2)
        self.assertEqual(os.listdir(self.dir), [])
        self.assertIn(f"conflict|specific_part|地下车位负一1号|{self.p1.id},{existing.id}", out)

    def test_tc_int_616_argument_and_target_validation(self):
        """IFC-297：缺 --output / 扩展名非法 / 父目录不存在 → 参数错误（1）；目标已存在无 --overwrite → 3 且原文件不变，加 --overwrite 才覆盖。"""
        with self.assertRaises(CommandError):
            call_command("export_registry_import_file", stdout=StringIO())
        for bad in (self.path("x.txt"), str(self.dir / "nope" / "x.csv")):
            code, _ = self.run_cmd("--output", bad)
            self.assertEqual(code, 1, bad)
        target = self.path("t.csv")
        Path(target).write_text("old", encoding="utf-8")
        code, _ = self.run_cmd("--output", target)
        self.assertEqual(code, 3)
        self.assertEqual(Path(target).read_text(encoding="utf-8"), "old")
        code, out = self.run_cmd("--output", target, "--overwrite")
        self.assertEqual(code, 0, out)
        self.assertNotEqual(Path(target).read_bytes(), b"old")

    def test_tc_int_617_precheck_failure_writes_nothing(self):
        """AC-187-08：自检不通过 → 退出码 2，不落盘（无文件、无 .part）。"""
        bad = mock.Mock(ok=False, file_counts=exporting.ExportCounts(0, 0, 0),
                        diff={"units": 0, "owners_named": 0, "phones_distinct": 0}, rows_failed=1, imported=0,
                        updated=0, owners_created=0, phones_created=0, roundtrip_mismatches=0)
        with mock.patch.object(exporting, "verify_export", return_value=bad):
            code, _ = self.run_cmd("--output", self.path())
        self.assertEqual(code, 2)
        self.assertEqual(os.listdir(self.dir), [])

    def test_tc_int_618_write_failure_cleans_part_and_keeps_existing_file(self):
        """AC-187-08：落盘失败（os.replace 抛 OSError）→ 退出码 3，.part 被清除，已有同名文件保持原样，库无写入。"""
        target = self.path("keep.csv")
        Path(target).write_text("old", encoding="utf-8")
        before = db_state()
        with mock.patch.object(exporting.os, "replace", side_effect=OSError(28, "No space")):
            code, _ = self.run_cmd("--output", target, "--overwrite")
        self.assertEqual(code, 3)
        self.assertEqual(sorted(os.listdir(self.dir)), ["keep.csv"])
        self.assertEqual(Path(target).read_text(encoding="utf-8"), "old")
        self.assertEqual(db_state(), before)

    def test_tc_int_619_read_failure_leaves_no_file_and_no_db_write(self):
        """AC-187-08：读取清册中途失败（异常）→ 命令异常退出，无文件、无 .part、库无写入。"""
        before = db_state()
        with mock.patch.object(exporting, "load_rows", side_effect=RuntimeError("读取中断")):
            with self.assertRaises(RuntimeError):
                self.run_cmd("--output", self.path())
        self.assertEqual(os.listdir(self.dir), [])
        self.assertEqual(db_state(), before)
