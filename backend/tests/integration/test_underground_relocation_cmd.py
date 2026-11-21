"""PHASE_08 集成测试：命令 relocate_underground_parking（MOD-109，IFC-294/295，AUTH-02）。

SQLite 测试库 + call_command；备份文件写到临时目录（不写仓库根）；全部合成数据，不连接测试机。
关联 US-188（AC-188-01~06）、US-187（AC-187-06 日志只含计数）；CR-003。
退出码经 CommandError.returncode 断言：1 参数错误、2 冲突/数量不符/核对失败、3 备份文件问题。
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

from apps.core.models import AuditLog
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from tests.support import next_phone
from apps.accounts.models import User

OWNER_NAME = "夜间测试业主"


def snapshot():
    return list(RegistryUnit.objects.order_by("id").values_list(
        "id", "building", "unit_no", "floor", "room", "specific_part", "unit_type", "area",
        "created_at", "updated_at"))


class RelocationCommandBase(TestCase):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        mk = RegistryUnit.objects.create
        self.p1 = mk(building="1", unit_no="", floor="负一", room="1", unit_type="PARKING", area="12.00")
        self.p2 = mk(building="1栋", unit_no="", floor="-2", room="2", unit_type="PARKING", area="12.00")
        self.p3 = mk(building="1", unit_no="", floor="负1", room="3", unit_type="PARKING", area="12.00")
        self.res = mk(building="1", unit_no="1", floor="9", room="902", unit_type="RESIDENCE", area="80.00")
        self.pos = mk(building="1", unit_no="", floor="2", room="9", unit_type="PARKING", area="12.00")
        self.neg_res = mk(building="1", unit_no="1", floor="负一", room="5", unit_type="RESIDENCE", area="30.00")
        self.moved_ids = {self.p1.id, self.p2.id, self.p3.id}
        # 业主、手机号与认证绑定（被改记录上的绑定必须保持）
        owner = RegistryOwner.objects.create(unit=self.p1, name=OWNER_NAME)
        self.phone = next_phone()
        RegistryPhone.objects.create(unit=self.p1, owner=owner, phone=self.phone)
        self.user = User.objects.create(account_no="7000000001", phone=self.phone)
        self.membership = Membership.objects.create(user=self.user, unit=self.p1, role="OWNER",
                                                    source="REGISTRY", active_slot=1)

    def run_cmd(self, *args, **kwargs):
        out = StringIO()
        call_command("relocate_underground_parking", *args, stdout=out, **kwargs)
        return out.getvalue()

    def code_of(self, *args):
        """返回 (退出码, stdout)；命令抛 CommandError 时取其 returncode。"""
        out = StringIO()
        try:
            call_command("relocate_underground_parking", *args, stdout=out)
        except CommandError as exc:
            return exc.returncode, out.getvalue()
        return 0, out.getvalue()

    def kv(self, text):
        return dict(line.split("=", 1) for line in text.splitlines() if "=" in line and "|" not in line)

    def backup_path(self, name="b.jsonl"):
        return str(self.dir / name)


class DryRunTests(RelocationCommandBase):
    def test_tc_int_588_dry_run_reports_and_writes_nothing(self):
        """AC-188-05：默认 dry-run 只读（无 INSERT/UPDATE/DELETE，库快照不变），输出计数与明细。"""
        before = snapshot()
        with CaptureQueriesContext(connection) as ctx:
            out = self.run_cmd()
        writes = [q["sql"] for q in ctx.captured_queries
                  if q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))]
        self.assertEqual(writes, [])
        self.assertEqual(snapshot(), before)
        values = self.kv(out)
        self.assertEqual((values["total_units"], values["candidates"], values["already_target"],
                          values["would_change"], values["conflicts"]), ("6", "3", "0", "3", "0"))
        self.assertEqual(values["negative_floor_non_parking"], "1")
        self.assertIn("old_building|1|2", out)
        self.assertIn("old_building|1栋|1", out)
        self.assertIn("floor|负一|1|recognized", out)
        self.assertIn(f"move|{self.p1.id}|1栋负一1号|地下车位负一1号", out)

    def test_tc_int_589_output_has_no_personal_data(self):
        """AC-187-06 / C-55：输出只含计数与标识，不含业主姓名、手机号。"""
        out = self.run_cmd()
        self.assertNotIn(OWNER_NAME, out)
        self.assertNotIn(self.phone, out)

    def test_tc_int_590_list_limit_bounds_and_truncates(self):
        """IFC-295：--list-limit 越界 → 参数错误；=1 时 move 明细只输出 1 行。"""
        for bad in (0, 100001):
            with self.assertRaises(CommandError):
                self.run_cmd(list_limit=bad)
        out = self.run_cmd("--list-limit", "1")
        self.assertEqual(sum(1 for line in out.splitlines() if line.startswith("move|")), 1)

    def test_tc_int_591_argument_validation_exit_code_1(self):
        """IFC-295：--apply 缺 --backup/--expect-changes；--backup 无 --apply；--restore 与 --backup 混用 → 退出码 1，库不变。"""
        before = snapshot()
        for args in (("--apply",), ("--apply", "--backup", self.backup_path()),
                     ("--apply", "--expect-changes", "3"), ("--backup", self.backup_path()),
                     ("--expect-changes", "3"), ("--restore", self.backup_path(), "--backup", "x"),
                     ("--apply", "--backup", self.backup_path(), "--expect-changes", "-1")):
            code, _ = self.code_of(*args)
            self.assertEqual(code, 1, args)
        self.assertEqual(snapshot(), before)
        self.assertEqual(os.listdir(self.dir), [])


class ApplyTests(RelocationCommandBase):
    def apply(self, expect=3, name="b.jsonl"):
        path = self.backup_path(name)
        out = self.run_cmd("--apply", "--backup", path, "--expect-changes", str(expect))
        return path, out

    def test_tc_int_592_apply_moves_only_identified_and_keeps_bindings(self):
        """AC-188-01/02：apply 后总数不变；被识别记录楼栋=地下车位、标识更新；其余 0 改动；业主/手机号/绑定数不变且绑定仍指向同一记录。"""
        before = {row[0]: row for row in snapshot()}
        counts_before = (RegistryUnit.objects.count(), RegistryOwner.objects.count(),
                         RegistryPhone.objects.count(), Membership.objects.filter(ended_at__isnull=True).count())
        _, out = self.apply()
        self.assertEqual(self.kv(out)["moved"], "3")
        after = {row[0]: row for row in snapshot()}
        self.assertEqual(set(after), set(before))
        for uid in self.moved_ids:
            self.assertEqual(after[uid][1], "地下车位")
            self.assertNotEqual(after[uid][5], before[uid][5])
            self.assertEqual(after[uid][2:5], before[uid][2:5])  # 单元/楼层/户号原值不变
        self.assertEqual(after[self.p1.id][5], "地下车位负一1号")
        for uid in set(before) - self.moved_ids:
            self.assertEqual(after[uid], before[uid], f"未识别记录 {uid} 被改动")
        counts_after = (RegistryUnit.objects.count(), RegistryOwner.objects.count(),
                        RegistryPhone.objects.count(), Membership.objects.filter(ended_at__isnull=True).count())
        self.assertEqual(counts_after, counts_before)
        membership = Membership.objects.get(pk=self.membership.pk)
        self.assertEqual(membership.unit_id, self.p1.id)
        self.assertEqual((membership.role, membership.ended_at), ("OWNER", None))
        self.assertEqual(membership.unit.specific_part, "地下车位负一1号")
        for key in ("before_units", "after_units", "before_active_memberships", "after_active_memberships"):
            self.assertIn(key, self.kv(out))
        self.assertEqual(self.kv(out)["before_units"], self.kv(out)["after_units"])

    def test_tc_int_593_backup_file_secure_and_without_personal_data(self):
        """AC-188-06 / NFUNC-032：备份 0600、JSONL、头部 records=3、末行 sha256；不含姓名与手机号。"""
        path, out = self.apply()
        mode = stat.S_IMODE(os.stat(path).st_mode)
        # POSIX 专属断言：Windows 的 chmod 不生效，由 Linux CI 做真实校验
        if os.name != "nt":
            self.assertEqual(mode, 0o600)
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        header = json.loads(lines[0])
        self.assertEqual((header["format"], header["records"]), ("ocap-underground-backup/1", 3))
        self.assertEqual(len(lines), 5)
        self.assertEqual(set(json.loads(lines[-1])), {"sha256"})
        content = Path(path).read_text(encoding="utf-8")
        self.assertNotIn(OWNER_NAME, content)
        self.assertNotIn(self.phone, content)
        self.assertNotIn(OWNER_NAME, out)
        self.assertNotIn(self.phone, out)
        self.assertIn(f"backup_records=3", out)

    def test_tc_int_594_apply_writes_system_audit_entry(self):
        """IFC-294：同事务写 1 条 REGISTRY_UNIT_CHANGED 审计，detail 仅含 change 与 moved 计数。"""
        before = AuditLog.objects.filter(action="REGISTRY_UNIT_CHANGED").count()
        self.apply()
        rows = AuditLog.objects.filter(action="REGISTRY_UNIT_CHANGED", object_id="underground_relocation")
        self.assertEqual(AuditLog.objects.filter(action="REGISTRY_UNIT_CHANGED").count(), before + 1)
        row = rows.get()
        self.assertEqual((row.actor_type, row.result), ("SYSTEM", "SUCCESS"))
        self.assertEqual(row.detail, {"change": "underground_relocation", "moved": 3})

    def test_tc_int_595_expect_changes_mismatch_exit_2_and_db_unchanged(self):
        """IFC-295：--expect-changes 与计划不符 → 退出码 2，库不变，备份文件未产生。"""
        before = snapshot()
        code, _ = self.code_of("--apply", "--backup", self.backup_path(), "--expect-changes", "2")
        self.assertEqual(code, 2)
        self.assertEqual(snapshot(), before)
        self.assertEqual(os.listdir(self.dir), [])

    def test_tc_int_596_backup_exists_exit_3_without_touching_db(self):
        """IFC-295：备份路径已存在 → 退出码 3，库不变，原文件内容不被覆盖；父目录不存在同样 3。"""
        path = self.backup_path()
        Path(path).write_text("keep", encoding="utf-8")
        before = snapshot()
        code, _ = self.code_of("--apply", "--backup", path, "--expect-changes", "3")
        self.assertEqual(code, 3)
        self.assertEqual(Path(path).read_text(encoding="utf-8"), "keep")
        self.assertEqual(snapshot(), before)
        code, _ = self.code_of("--apply", "--backup", str(self.dir / "nope" / "b.jsonl"), "--expect-changes", "3")
        self.assertEqual(code, 3)

    def test_tc_int_597_idempotent_second_apply_changes_nothing(self):
        """AC-188-04：已执行一次后再执行（expect 0）→ moved=0，新增 0、改动 0，记录快照与第一次后相同，不再生成备份。"""
        self.apply()
        once = snapshot()
        out = self.run_cmd("--apply", "--backup", self.backup_path("b2.jsonl"), "--expect-changes", "0")
        self.assertEqual(self.kv(out)["moved"], "0")
        self.assertEqual(snapshot(), once)
        self.assertFalse((self.dir / "b2.jsonl").exists())
        dry = self.kv(self.run_cmd())
        self.assertEqual((dry["would_change"], dry["already_target"]), ("0", "3"))

    def test_tc_int_598_conflict_stops_whole_batch_and_lists_conflicts(self):
        """AC-188-03：改后标识与既有记录冲突 → 退出码 2，整批停止，库逐记录不变，输出冲突清单且不含个人信息。"""
        existing = RegistryUnit.objects.create(building="地下车位", unit_no="", floor="负一", room="1",
                                               unit_type="OTHER")
        before = snapshot()
        code, out = self.code_of("--apply", "--backup", self.backup_path(), "--expect-changes", "3")
        self.assertEqual(code, 2)
        self.assertEqual(snapshot(), before)
        self.assertEqual(os.listdir(self.dir), [])
        self.assertIn("conflicts=2", out)  # specific_part 与 tuple 两类
        self.assertIn(f"conflict|specific_part|地下车位负一1号|{self.p1.id},{existing.id}", out)
        self.assertNotIn(OWNER_NAME, out)
        # dry-run 也先输出报告再以 2 退出（ASSUMPTION：dry-run 有冲突退出码 2）
        code, out = self.code_of()
        self.assertEqual(code, 2)
        self.assertIn("conflict|", out)

    def test_tc_int_599_cr003_unrelated_duplicates_do_not_block(self):
        """CR-003（命令级）：已在目标楼栋、与被改记录无关的负层车位不构成冲突，apply 仍成功并计入 already_target。
        （无关重复组不阻断的纯规则用例见 TC-UNIT-629。）"""
        RegistryUnit.objects.create(building="地下车位", unit_no="", floor="负二", room="99", unit_type="PARKING",
                                    area="12.00")
        _, out = self.apply()
        self.assertEqual(self.kv(out)["moved"], "3")
        self.assertEqual(self.kv(self.run_cmd())["already_target"], "4")

    def test_tc_int_600_other_building_and_unrecognized_floor_reported(self):
        """OQ-02：非 1/1栋 楼栋下的被改记录单独计数；未识别写法（B1）列出为 unrecognized 且不被改。"""
        RegistryUnit.objects.create(building="2", unit_no="", floor="负二", room="8", unit_type="PARKING",
                                    area="12.00")
        b1 = RegistryUnit.objects.create(building="1", unit_no="", floor="B1", room="8", unit_type="PARKING",
                                         area="12.00")
        out = self.run_cmd()
        values = self.kv(out)
        self.assertEqual((values["would_change"], values["other_building_negative_parking"]), ("4", "1"))
        self.assertIn("floor|B1|1|unrecognized", out)
        self.apply(expect=4)
        self.assertEqual(RegistryUnit.objects.get(pk=b1.pk).building, "1")


class RestoreTests(RelocationCommandBase):
    def setUp(self):
        super().setUp()
        self.original = snapshot()
        self.path = self.backup_path()
        self.run_cmd("--apply", "--backup", self.path, "--expect-changes", "3")

    def test_tc_int_601_restore_dry_run_reports_differences_only(self):
        """AC-188-06：--restore（无 --apply）只读，differences=3，库不变。"""
        changed = snapshot()
        out = self.run_cmd("--restore", self.path)
        self.assertEqual(self.kv(out)["differences"], "3")
        self.assertEqual(self.kv(out)["restored"], "0")
        self.assertEqual(snapshot(), changed)

    def test_tc_int_602_restore_apply_returns_to_pre_state_exactly(self):
        """AC-188-06：--restore --apply 后与修正前逐记录一致（含标识、updated_at），differences=0，计数不变。"""
        out = self.run_cmd("--restore", self.path, "--apply")
        self.assertEqual((self.kv(out)["restored"], self.kv(out)["differences"]), ("3", "0"))
        self.assertEqual(snapshot(), self.original)
        self.assertEqual(Membership.objects.get(pk=self.membership.pk).unit_id, self.p1.id)
        self.assertEqual(self.kv(out)["before_units"], self.kv(out)["after_units"])
        # 还原后可再次 dry-run 识别到同样 3 条
        self.assertEqual(self.kv(self.run_cmd())["would_change"], "3")

    def test_tc_int_603_restore_when_not_in_modified_state_aborts(self):
        """IFC-294：备份记录当前不是修正后状态（已还原过）→ 退出码 2，库不变。"""
        self.run_cmd("--restore", self.path, "--apply")
        code, _ = self.code_of("--restore", self.path, "--apply")
        self.assertEqual(code, 2)
        self.assertEqual(snapshot(), self.original)

    def test_tc_int_604_restore_rejects_missing_or_tampered_backup(self):
        """IFC-295：备份缺失 / 篡改（摘要不符）/ 非备份格式 → 退出码 3，库不变。"""
        changed = snapshot()
        code, _ = self.code_of("--restore", str(self.dir / "missing.jsonl"), "--apply")
        self.assertEqual(code, 3)
        tampered = self.dir / "tampered.jsonl"
        tampered.write_text(Path(self.path).read_text(encoding="utf-8").replace("负一", "负三", 1), encoding="utf-8")
        code, _ = self.code_of("--restore", str(tampered), "--apply")
        self.assertEqual(code, 3)
        junk = self.dir / "junk.jsonl"
        junk.write_text("not a backup\n", encoding="utf-8")
        code, _ = self.code_of("--restore", str(junk))
        self.assertEqual(code, 3)
        self.assertEqual(snapshot(), changed)
