# MOD-109 / implements IFC-295 / depends registry.underground
"""AUTH-02：把"类型为车位且楼层为负层"的专有部分改归属楼栋"地下车位"（默认 dry-run，只读）。

退出码：0 正常；1 参数错误；2 冲突/数量不符/核对失败（已回滚）；3 备份或还原文件问题。
输出只含计数与记录 id、标识，不含姓名与手机号。
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.registry import underground as ug


def _fail(message: str, code: int) -> CommandError:
    return CommandError(message, returncode=code)


class Command(BaseCommand):
    help = "地下车位归属修正：dry-run（默认）、--apply（须 --backup 与 --expect-changes）、--restore"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="实际写入（apply）或实际还原（与 --restore 合用）")
        parser.add_argument("--backup", help="备份文件路径（apply 必填，须不存在）")
        parser.add_argument("--expect-changes", type=int, dest="expect_changes",
                            help="期望修改条数（apply 必填，须等于 dry-run 的 would_change）")
        parser.add_argument("--restore", help="按备份文件还原（默认只读，加 --apply 才写）")
        parser.add_argument("--list-limit", type=int, default=50, dest="list_limit",
                            help="明细最多输出条数（1~100000）")

    def handle(self, *args, **options):
        limit = options["list_limit"]
        if limit < 1 or limit > 100000:
            raise CommandError("--list-limit 须在 1~100000 之间")
        apply = options["apply"]
        backup = options["backup"]
        expect = options["expect_changes"]
        restore = options["restore"]

        if restore:
            if backup or expect is not None:
                raise CommandError("--restore 不能与 --backup、--expect-changes 同时使用")
            return self._restore(Path(restore), apply)
        if apply:
            if not backup or expect is None:
                raise CommandError("--apply 必须同时给出 --backup 与 --expect-changes")
            if expect < 0:
                raise CommandError("--expect-changes 须为非负整数")
        elif backup or expect is not None:
            raise CommandError("--backup、--expect-changes 仅与 --apply 一起使用")

        backup_path = Path(backup) if backup else None
        if backup_path is not None:
            if backup_path.exists():
                raise _fail("备份文件已存在，拒绝覆盖", 3)
            if not backup_path.parent.is_dir():
                raise _fail("备份文件的父目录不存在", 3)

        rows = ug.load_rows()
        plan = ug.plan_relocation(rows)
        self._report(plan, limit)
        if plan.conflicts:
            raise _fail("存在标识冲突，整批停止，库未改动", 2)
        if not apply:
            return None
        if expect != len(plan.moves):
            raise _fail(f"--expect-changes={expect} 与计划 would_change={len(plan.moves)} 不符，库未改动", 2)
        if not plan.moves:
            self.stdout.write("moved=0")
            return None

        try:
            info = ug.write_backup(backup_path, plan, rows, ug.read_counts())
        except ug.BackupError as exc:
            raise _fail(f"备份失败：{exc}", 3) from exc
        self.stdout.write(f"backup={info.path}")
        self.stdout.write(f"backup_records={info.records}")
        self.stdout.write(f"backup_sha256={info.sha256}")
        try:
            result = ug.apply_relocation(plan, info, expect)
        except (ug.RelocationConflict, ug.RelocationAborted, ug.RelocationVerifyError) as exc:
            raise _fail(f"修正失败，事务已回滚：{exc}", 2) from exc
        self.stdout.write(f"moved={result.moved}")
        self._counts("before", result.before)
        self._counts("after", result.after)
        return None

    def _restore(self, path: Path, apply: bool):
        try:
            result = ug.restore_from_backup(path, apply)
        except ug.BackupError as exc:
            raise _fail(f"备份文件问题：{exc}", 3) from exc
        except (ug.RelocationAborted, ug.RelocationVerifyError) as exc:
            raise _fail(f"还原失败：{exc}", 2) from exc
        self.stdout.write(f"restored={result.restored}")
        self.stdout.write(f"differences={result.differences}")
        self._counts("before", result.before)
        self._counts("after", result.after)

    def _counts(self, prefix: str, counts: ug.Counts) -> None:
        self.stdout.write(f"{prefix}_units={counts.units}")
        self.stdout.write(f"{prefix}_owners={counts.owners}")
        self.stdout.write(f"{prefix}_phones={counts.phones}")
        self.stdout.write(f"{prefix}_active_memberships={counts.active_memberships}")

    def _report(self, plan: ug.RelocationPlan, limit: int) -> None:
        write = self.stdout.write
        write(f"total_units={plan.total_units}")
        write(f"candidates={plan.candidates}")
        write(f"already_target={plan.already_target}")
        write(f"would_change={len(plan.moves)}")
        write(f"conflicts={len(plan.conflicts)}")
        write(f"negative_floor_non_parking={plan.negative_floor_non_parking}")
        write(f"other_building_negative_parking={plan.other_building_negative_parking}")
        for building, count in sorted(plan.old_building_counts.items()):
            write(f"old_building|{building}|{count}")
        for floor, (count, recognized) in sorted(plan.parking_floor_spellings.items()):
            write(f"floor|{floor}|{count}|{'recognized' if recognized else 'unrecognized'}")
        for conflict in plan.conflicts[:limit]:
            write(f"conflict|{conflict.kind}|{conflict.key}|{','.join(str(i) for i in conflict.unit_ids)}")
        for move in plan.moves[:limit]:
            write(f"move|{move.unit_id}|{move.old_specific_part}|{move.new_specific_part}")
