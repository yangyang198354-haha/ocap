"""MOD-066 / IFC-245：只读预览专有部分标识重新生成结果。"""
import re

from django.core.management.base import BaseCommand, CommandError

from apps.registry.models import RegistryUnit, build_specific_part

_PURE_NUMBER = re.compile(r"(?:负)?[0-9]+")


class Command(BaseCommand):
    help = "只读预览：按当前规则计算专有部分标识的变化、冲突、省略楼层段与非纯数字户号"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50, help="明细最多输出条数（1~100000）")

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit < 1 or limit > 100000:
            raise CommandError("--limit 须在 1~100000 之间")

        rows = list(RegistryUnit.objects.values("id", "building", "unit_no", "floor", "room", "specific_part"))
        finals: dict[int, str] = {}
        changes: list[tuple[int, str, str]] = []
        floor_omitted = 0
        review: list[tuple[int, str, str, str, str, str, str]] = []

        for row in rows:
            new_value = build_specific_part(row["building"], row["unit_no"], row["floor"], row["room"])
            finals[row["id"]] = new_value
            if new_value != row["specific_part"]:
                changes.append((row["id"], row["specific_part"], new_value))
            no_floor = build_specific_part(row["building"], row["unit_no"], "", row["room"])
            if (row["floor"] or "").strip() and new_value == no_floor:
                floor_omitted += 1
            room = (row["room"] or "").strip()
            if room and not _PURE_NUMBER.fullmatch(room):
                review.append((row["id"], row["specific_part"], new_value, row["building"],
                               row["unit_no"], row["floor"], row["room"]))

        groups: dict[str, list[int]] = {}
        for row_id, value in finals.items():
            groups.setdefault(value.casefold(), []).append(row_id)
        conflicts = [(key, ids) for key, ids in groups.items() if len(ids) > 1]

        self.stdout.write(f"total={len(rows)}")
        self.stdout.write(f"would_change={len(changes)}")
        self.stdout.write(f"conflicts={len(conflicts)}")
        self.stdout.write(f"floor_omitted={floor_omitted}")
        self.stdout.write(f"review={len(review)}")
        for key, ids in conflicts:
            self.stdout.write(f"conflict|{key}|{','.join(str(row_id) for row_id in ids)}")
        for item in review[:limit]:
            self.stdout.write("|".join(str(part) for part in item))
