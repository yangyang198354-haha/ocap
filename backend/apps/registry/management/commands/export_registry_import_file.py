# MOD-110 / implements IFC-297 / depends registry.exporting
"""AUTH-01：从清册只读导出并按导入模板生成文件（全程只读，不写库、不写审计）。

退出码：0 成功；1 参数错误；2 冲突/无法表达的记录未 --allow-gaps/自检不通过（不落盘）；3 目标文件问题。
输出只含计数与专有部分 id，不含姓名与手机号。
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.registry import exporting


def _fail(message: str, code: int) -> CommandError:
    return CommandError(message, returncode=code)


class Command(BaseCommand):
    help = "只读导出清册为导入文件（xlsx/csv），地下车位已归属“地下车位”；须用户另行授权后在目标机执行"

    def add_arguments(self, parser):
        parser.add_argument("--output", help="输出文件路径（.xlsx 或 .csv）")
        parser.add_argument("--output-dir", dest="output_dir",
                            help="输出目录（已存在）；文件名自动取 registry_import_日期-时间.xlsx，不覆盖已有文件")
        parser.add_argument("--overwrite", action="store_true", help="允许覆盖已存在的目标文件")
        parser.add_argument("--allow-gaps", action="store_true", dest="allow_gaps",
                            help="存在模板无法表达的记录时仍生成文件（报告写出差异）")
        parser.add_argument("--allow-unrelocated", action="store_true", dest="allow_unrelocated",
                            help="商铺尚未归类时仍生成文件（文件为旧结构，交付说明须写明）")

    def handle(self, *args, **options):
        if bool(options["output"]) == bool(options["output_dir"]):
            raise CommandError("--output 与 --output-dir 须且仅须给出一个")
        if options["output_dir"]:
            directory = Path(options["output_dir"])
            if not directory.is_dir():
                raise CommandError("--output-dir 须为已存在的目录")
            output = directory / exporting.default_output_name(timezone.localtime())
            if output.exists():
                raise _fail("目标文件已存在，拒绝覆盖", 3)
        else:
            output = Path(options["output"])
            if output.suffix.lower() not in (".xlsx", ".csv"):
                raise CommandError("--output 扩展名须为 .xlsx 或 .csv")
            if not output.parent.is_dir():
                raise CommandError("--output 的父目录不存在")
            if output.exists() and not options["overwrite"]:
                raise _fail("目标文件已存在，拒绝覆盖（可加 --overwrite）", 3)
        try:
            exporting.check_output_location(output)
        except exporting.OutputLocationError as exc:
            raise _fail(f"输出位置不符合要求：{exc}", 3) from exc

        write = self.stdout.write
        pending = exporting.pending_shop_units()
        if pending and not options["allow_unrelocated"]:
            write(f"pending_shop_units={pending}")
            raise _fail("商铺尚未归类（请先执行 relocate_shops），不生成文件；确认导出旧结构可加 --allow-unrelocated", 2)
        write("structure=legacy" if pending else "structure=shop_relocated")

        bundle = exporting.build_export_bundle()
        db = bundle.db_counts
        write(f"db_units={db.units}")
        write(f"db_owners_named={db.owners_named}")
        write(f"db_phones_distinct={db.phones_distinct}")
        write(f"relocated_units={bundle.relocated_units}")
        write(f"gaps_units={len(bundle.gaps.units_without_named_owner)}")
        write(f"gaps_unnamed_owners={bundle.gaps.unnamed_owners}")
        for unit_id in bundle.gaps.units_without_named_owner[:50]:
            write(f"gap_unit|{unit_id}")
        for conflict in bundle.conflicts:
            write(f"conflict|{conflict.kind}|{conflict.key}|{','.join(str(i) for i in conflict.unit_ids)}")
        if bundle.conflicts:
            raise _fail("存在标识冲突，不生成文件", 2)
        has_gaps = bool(bundle.gaps.units_without_named_owner or bundle.gaps.unnamed_owners)
        if has_gaps and not options["allow_gaps"]:
            raise _fail("存在导入模板无法表达的记录，不生成文件（确认后可加 --allow-gaps）", 2)

        content = exporting.render_file(bundle, output.name)
        report = exporting.verify_export(content, output.name, bundle)
        fc = report.file_counts
        write(f"file_units={fc.units}")
        write(f"file_owners_named={fc.owners_named}")
        write(f"file_phones_distinct={fc.phones_distinct}")
        for key, value in report.diff.items():
            write(f"diff_{key}={value}")
        write(f"precheck_rows_failed={report.rows_failed}")
        write(f"precheck_would_create_units={report.imported}")
        write(f"precheck_would_create_owners={report.owners_created}")
        write(f"precheck_would_create_phones={report.phones_created}")
        write(f"precheck_would_update_units={report.updated}")
        write(f"roundtrip_mismatches={report.roundtrip_mismatches}")
        write(f"output_bytes={len(content)}")
        if not report.ok:
            raise _fail("自检不通过，不生成文件", 2)
        try:
            exporting.write_export_file(output, content, overwrite=options["overwrite"])
        except OSError as exc:
            raise _fail(f"写入目标文件失败：{exc.strerror}", 3) from exc
        write(f"output={output}")
