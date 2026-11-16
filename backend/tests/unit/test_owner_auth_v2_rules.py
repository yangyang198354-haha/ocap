"""PHASE_07 单元测试（ocap_owner_auth_v2）：纯规则——商铺归类规则、楼栋排序、姓名归一、席位生效谓词、导出位置守卫。

关联 US-193（AC-193-01/03/04）、US-194（AC-194-01）、US-195（AC-195-03/04）、US-196（AC-196-03）、
US-200（AC-200-05）、US-205（AC-205-03）、US-206（AC-206-01/03/05）。
全部合成数据，不连接任何环境，不读取仓库根文件内容（GR-C-001-F01）。
"""
import os
import stat
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.test import SimpleTestCase

from apps.committee.effective import effective_q, is_effective
from apps.registry import exporting
from apps.registry.models import build_specific_part
from apps.registry.ordering import RESERVED_BUILDINGS, SHOP_BUILDING, UNDERGROUND_BUILDING, natural_key, sorted_values
from apps.registry.ownership import OWNER_NAME_MAX, normalize_owner_name
from apps.registry.shops import SHOP_BACKUP_FORMAT, plan_shop_relocation, shop_unit_no
from apps.registry.underground import UnitRow

TS = "2026-01-01T00:00:00+00:00"


def row(uid, building="1", unit_no="", floor="1", room="101", unit_type="SHOP", sp=None):
    return UnitRow(id=uid, building=building, unit_no=unit_no, floor=floor, room=room,
                   specific_part=sp or build_specific_part(building, unit_no, floor, room),
                   unit_type=unit_type, area=None, created_at=TS, updated_at=TS)


class ShopUnitNoTests(SimpleTestCase):
    def test_tc_unit_650_shop_unit_no_rules(self):
        """AC-194-01 / OQ-01：纯数字补"栋"；已含"栋"或文字原样；全角数字也补；首尾空白去除；空串返回空串。"""
        cases = {"1": "1栋", "10": "10栋", "１０": "１０栋", "1栋": "1栋", "建设南路142号": "建设南路142号",
                 "枫林路124号附1号": "枫林路124号附1号", "未标注A": "未标注A", " 2 ": "2栋", "": "", "   ": ""}
        for old, expected in cases.items():
            self.assertEqual(shop_unit_no(old), expected, repr(old))
        self.assertEqual(shop_unit_no(None), "")


class PlanShopRelocationTests(SimpleTestCase):
    def test_tc_unit_651_only_shop_type_is_moved_and_4347_like_negative_floor(self):
        """AC-193-02/03、AC-195-02：只识别类型为商铺；住宅/车位/类型空/其他不动；负层商铺（4347 类，楼层"负1"）进 moves，
        新标识 商铺1栋负1层1139号，原楼栋在 new_unit_no 中不丢失。"""
        plan = plan_shop_relocation([
            row(4347, "1", "", "负1", "1139"),
            row(2, "1", "1", "3", "301", unit_type="RESIDENCE"),
            row(3, "1", "", "负一", "7", unit_type="PARKING"),
            row(4, "1", "", "2", "9", unit_type=None),
            row(5, "1", "", "2", "10", unit_type="OTHER"),
            row(6, "建设南路142号", "", "", "1", unit_type="SHOP"),
        ])
        moves = {m.unit_id: m for m in plan.moves}
        self.assertEqual(set(moves), {4347, 6})
        self.assertEqual(moves[4347].new_unit_no, "1栋")
        self.assertEqual(moves[4347].new_specific_part, "商铺1栋负1层1139号")
        self.assertEqual(moves[6].new_unit_no, "建设南路142号")
        self.assertEqual((plan.total_units, plan.shop_units, plan.already_target, plan.conflicts), (6, 2, 0, ()))
        self.assertEqual(plan.second_level_values, 2)
        self.assertEqual(plan.old_building_counts, {"1": 1, "建设南路142号": 1})

    def test_tc_unit_652_idempotent_already_target_not_moved(self):
        """AC-195-04：已在楼栋"商铺"下的商铺不进 moves，计入 already_target；二次计划 would_change=0。"""
        done = row(1, SHOP_BUILDING, "1栋", "负1", "1139", sp="商铺1栋负1层1139号")
        plan = plan_shop_relocation([done, row(2, "2", "", "1", "5")])
        self.assertEqual((plan.already_target, len(plan.moves)), (1, 1))
        plan2 = plan_shop_relocation([done, row(2, SHOP_BUILDING, "2栋", "1", "5", sp="商铺2栋1层5号")])
        self.assertEqual((plan2.already_target, len(plan2.moves), plan2.conflicts), (2, 0, ()))

    def test_tc_unit_653_four_conflict_kinds_stop_whole_batch(self):
        """AC-195-03：标识重复(specific_part/tuple)、原 unit_no 非空、新值超 32 字、旧楼栋为空 → 均进 conflicts。"""
        existing = row(10, SHOP_BUILDING, "1栋", "1", "5", unit_type="OTHER", sp="商铺1栋1层5号")
        dup = plan_shop_relocation([existing, row(11, "1", "", "1", "5")])
        self.assertIn("specific_part", {c.kind for c in dup.conflicts})
        self.assertIn("tuple", {c.kind for c in dup.conflicts})
        occupied = plan_shop_relocation([row(12, "1", "A", "1", "5")])
        self.assertEqual([c.kind for c in occupied.conflicts], ["unit_no_occupied"])
        too_long = plan_shop_relocation([row(13, "建" * 33, "", "1", "5")])
        self.assertEqual([c.kind for c in too_long.conflicts], ["too_long"])
        empty = plan_shop_relocation([row(14, "", "", "1", "5")])
        self.assertEqual([c.kind for c in empty.conflicts], ["empty_building"])
        for plan in (dup, occupied, too_long, empty):
            self.assertTrue(plan.conflicts)

    def test_tc_unit_654_one_vs_one_dong_same_slot_conflict(self):
        """OQ-01 / ADR-106：原楼栋写法 "1" 与 "1栋" 的商铺同层同户号，补"栋"后标识相同 → 冲突（而不是静默合并）。"""
        plan = plan_shop_relocation([row(1, "1", "", "1", "5"), row(2, "1栋", "", "1", "5")])
        self.assertTrue(any(c.kind == "specific_part" and set(c.unit_ids) == {1, 2} for c in plan.conflicts))

    def test_tc_unit_655_backup_format_is_distinct_from_underground(self):
        """ADR-107：商铺备份 format_name 与地下车位备份不同，防止误还原。"""
        from apps.registry.underground import BACKUP_FORMAT
        self.assertNotEqual(SHOP_BACKUP_FORMAT, BACKUP_FORMAT)


class BuildingOrderTests(SimpleTestCase):
    def test_tc_unit_656_first_level_three_classes_then_other_text(self):
        """AC-193-01/04：楼栋序 1..10 → 地下车位 → 商铺 → 其他文字楼栋（配套用房）；两端数字自然序（2 在 10 之前）。"""
        values = ["商铺", "配套用房", "10", "地下车位", "2", "1", "9", "3", "4", "5", "6", "7", "8"]
        self.assertEqual(sorted_values(values, "building"),
                         ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "地下车位", "商铺", "配套用房"])
        self.assertEqual(RESERVED_BUILDINGS, {UNDERGROUND_BUILDING: 1, SHOP_BUILDING: 2})
        self.assertEqual(natural_key("配套用房", "building")[0], 3)
        self.assertLess(natural_key("商铺", "building"), natural_key("配套用房", "building"))

    def test_tc_unit_657_shop_second_level_natural_order(self):
        """AC-194-01：商铺第二级值 1栋<2栋<10栋<建设南路142号（数字段按数值，文字段在后）。"""
        values = ["建设南路142号", "10栋", "2栋", "1栋", "枫林路124号附1号"]
        ordered = sorted_values(values, "unit_no")
        self.assertEqual(ordered[:3], ["1栋", "2栋", "10栋"])
        self.assertEqual(set(ordered[3:]), {"建设南路142号", "枫林路124号附1号"})

    def test_tc_unit_658_reserved_name_only_at_building_level(self):
        """C-60：保留名只在楼栋层级有特殊层级；"商铺"出现在 unit_no 层级只是普通文字（层级 1）。"""
        self.assertEqual(natural_key("商铺", "unit_no")[0], 1)
        self.assertEqual(natural_key("商铺", "building")[0], 2)
        self.assertEqual(natural_key(" 商铺 ", "building")[0], 2)
        self.assertEqual(natural_key("商铺A", "building")[0], 3)


class OwnerNameTests(SimpleTestCase):
    def test_tc_unit_659_normalize_owner_name(self):
        """AC-200-05：全角空格与首尾空白去除；中间空格保留；非字符串按空串；不做模糊。"""
        self.assertEqual(normalize_owner_name("　张三 "), "张三")
        self.assertEqual(normalize_owner_name("张 三"), "张 三")
        self.assertNotEqual(normalize_owner_name("张三丰"), normalize_owner_name("张三"))
        for bad in (None, 123, [], {}):
            self.assertEqual(normalize_owner_name(bad), "")
        self.assertEqual(normalize_owner_name("   "), "")
        self.assertEqual(OWNER_NAME_MAX, 64)


class SeatEffectiveTests(SimpleTestCase):
    def seat(self, start, end, status="ACTIVE"):
        return SimpleNamespace(status=status, term_start=start, term_end=end)

    def test_tc_unit_660_is_effective_boundaries(self):
        """AC-206-01/03/05、AC-205-03：开始日=今天生效、开始日明天不生效；结束日=今天仍生效、结束日昨天失效；非 ACTIVE 不生效。"""
        today = date(2026, 11, 16)
        one = timedelta(days=1)
        self.assertTrue(is_effective(self.seat(today, today + 30 * one), today))
        self.assertTrue(is_effective(self.seat(today - 30 * one, today), today))
        self.assertFalse(is_effective(self.seat(today + one, today + 400 * one), today))
        self.assertFalse(is_effective(self.seat(today - 30 * one, today - one), today))
        self.assertFalse(is_effective(self.seat(today - one, today + one, status="REPLACED"), today))

    def test_tc_unit_661_effective_q_shape(self):
        """IFC-311：effective_q 由 status=ACTIVE、term_start<=今天、term_end>=今天三个条件组成。"""
        today = date(2026, 11, 16)
        text = str(effective_q(today))
        for part in ("status", "term_start__lte", "term_end__gte"):
            self.assertIn(part, text)


class ExportLocationGuardTests(SimpleTestCase):
    def make_dir(self, mode):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        os.chmod(tmp.name, mode)
        return Path(tmp.name)

    def test_tc_unit_662_default_output_name_is_dated_xlsx(self):
        """AC-196-03/04：默认文件名含日期时间，.xlsx；不同秒不同名。"""
        a = exporting.default_output_name(datetime(2026, 11, 16, 9, 8, 7))
        b = exporting.default_output_name(datetime(2026, 11, 16, 9, 8, 8))
        self.assertEqual(a, "registry_import_20261116-090807.xlsx")
        self.assertNotEqual(a, b)
        self.assertEqual(exporting.default_output_name(datetime(2026, 1, 2, 3, 4, 5), ".csv"),
                         "registry_import_20260102-030405.csv")

    @staticmethod
    def _posix():
        return hasattr(os, "getuid")

    def test_tc_unit_663_dir_700_outside_deploy_root_passes(self):
        """AC-196-03：部署根之外、属当前用户、权限 700 的目录通过守卫。"""
        directory = self.make_dir(0o700)
        exporting.check_output_location(directory / "x.xlsx")

    def test_tc_unit_664_dir_too_open_rejected(self):
        """AC-196-03：父目录 755 / 770 被拒（含组或其他位）。"""
        if not self._posix():
            self.skipTest("非 POSIX 开发机不检查权限位")
        for mode in (0o755, 0o770, 0o707):
            directory = self.make_dir(mode)
            with self.assertRaises(exporting.OutputLocationError, msg=oct(mode)):
                exporting.check_output_location(directory / "x.xlsx")
        self.assertEqual(stat.S_IMODE(os.stat(self.make_dir(0o700)).st_mode), 0o700)

    def test_tc_unit_665_inside_deploy_root_media_or_static_rejected(self):
        """AC-196-03 / C-59：部署根（BASE_DIR 的上级）、MEDIA_ROOT、STATIC_ROOT 内的路径被拒绝——目录权限与属主均合规（700、当前用户），
        因此只可能因"位置"被拒（不与权限检查混淆）；部署根之外的同样合规目录通过（对照）。"""
        from django.test import override_settings

        root = self.make_dir(0o700)
        backend = root / "backend"
        media = backend / "var" / "attachments"
        static = root / "static_out"
        for directory in (backend, backend / "var", media, static):
            directory.mkdir(parents=True, exist_ok=True)
            os.chmod(directory, 0o700)
        outside = self.make_dir(0o700)
        with override_settings(BASE_DIR=backend, MEDIA_ROOT=str(media), STATIC_ROOT=str(static)):
            for target in (root / "x.xlsx", backend / "x.xlsx", media / "x.xlsx", static / "x.xlsx"):
                with self.assertRaises(exporting.OutputLocationError, msg=str(target)) as ctx:
                    exporting.check_output_location(target)
                self.assertIn("部署目录或站点目录", str(ctx.exception))
            exporting.check_output_location(outside / "x.xlsx")

    def test_tc_unit_689_real_settings_deploy_root_and_media_rejected(self):
        """AC-196-03：真实 settings 下，部署根与 MEDIA_ROOT 内的路径同样被拒（不依赖目录权限）。"""
        for target in (Path(settings.BASE_DIR).parent / "x.xlsx", Path(settings.MEDIA_ROOT) / "sub" / "x.xlsx",
                       Path(settings.BASE_DIR) / "apps" / "x.xlsx"):
            with self.assertRaises(exporting.OutputLocationError):
                exporting.check_output_location(target)

    def test_tc_unit_666_missing_parent_rejected(self):
        """AC-196-07：父目录不存在时抛 OutputLocationError（不触库）。"""
        directory = self.make_dir(0o700)
        with self.assertRaises(exporting.OutputLocationError):
            exporting.check_output_location(directory / "nope" / "x.xlsx")
