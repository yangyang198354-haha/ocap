"""PHASE_07 单元测试：地下车位归属规则（MOD-109，IFC-294 纯函数）与导出行生成的纯规则。

关联 US-187（AC-187-01）、US-188（AC-188-01/03/04）；CR-003。
"""
from django.test import SimpleTestCase

from apps.registry.ordering import UNDERGROUND_BUILDING
from apps.registry.underground import UnitRow, is_negative_floor, plan_relocation


def row(uid, building="1", unit_no="", floor="负一", room="1", unit_type="PARKING", sp=None):
    from apps.registry.models import build_specific_part
    return UnitRow(id=uid, building=building, unit_no=unit_no, floor=floor, room=room,
                   specific_part=sp or build_specific_part(building, unit_no, floor, room),
                   unit_type=unit_type, area="12.00", created_at="2026-01-01T00:00:00+00:00",
                   updated_at="2026-01-01T00:00:00+00:00")


class NegativeFloorTests(SimpleTestCase):
    def test_tc_unit_623_negative_floor_spellings(self):
        """AC-187-01：负一/负二/-1/负1/负一层 均为负层；1、B1、空 不是。"""
        for text in ("负一", "负二", "-1", "负1", "负一层", "-2"):
            self.assertTrue(is_negative_floor(text), text)
        for text in ("1", "B1", "", None, "0", "10"):
            self.assertFalse(is_negative_floor(text), repr(text))


class PlanRelocationTests(SimpleTestCase):
    def test_tc_unit_624_identifies_only_parking_with_negative_floor(self):
        """AC-188-01：只识别类型为车位且楼层为负层；负层住宅、正层车位不改。"""
        plan = plan_relocation([
            row(1, floor="负一", room="1"),
            row(2, floor="-2", room="2"),
            row(3, floor="负一", room="3", unit_type="RESIDENCE"),
            row(4, floor="1", room="4"),
            row(5, floor="B1", room="5"),
        ])
        self.assertEqual({m.unit_id for m in plan.moves}, {1, 2})
        self.assertEqual(plan.candidates, 2)
        self.assertEqual(plan.negative_floor_non_parking, 1)
        self.assertEqual(plan.total_units, 5)
        self.assertEqual(plan.conflicts, ())
        # OQ-02：车位楼层写法清单，B1 未识别
        self.assertEqual(plan.parking_floor_spellings["B1"], (1, False))
        self.assertEqual(plan.parking_floor_spellings["负一"], (1, True))

    def test_tc_unit_625_new_specific_part_uses_underground_building(self):
        """AC-188-01：新标识由 build_specific_part 生成，旧楼栋分布被统计。"""
        plan = plan_relocation([row(1, building="1栋", floor="负一", room="7", unit_no="")])
        move = plan.moves[0]
        self.assertEqual(move.old_building, "1栋")
        self.assertEqual(move.new_specific_part, "地下车位负一7号")  # 中文层数不补"层"（ADR-064 既有规则）
        self.assertEqual(plan.old_building_counts, {"1栋": 1})
        self.assertEqual(plan.other_building_negative_parking, 0)

    def test_tc_unit_626_other_building_negative_parking_counted(self):
        """OQ-02 / Q-SF-02b-3：非 1/1栋 楼栋下的被改记录单独计数。"""
        plan = plan_relocation([row(1, building="2", room="1"), row(2, building="1", room="2")])
        self.assertEqual(plan.other_building_negative_parking, 1)

    def test_tc_unit_627_already_target_is_idempotent(self):
        """AC-188-04：已在地下车位的负层车位不进 moves，计入 already_target。"""
        plan = plan_relocation([row(1, building=UNDERGROUND_BUILDING, floor="负一", room="1")])
        self.assertEqual(plan.moves, ())
        self.assertEqual(plan.already_target, 1)
        self.assertEqual(plan.candidates, 1)

    def test_tc_unit_628_conflict_specific_part_reported(self):
        """AC-188-03：改后标识与既有记录相同 → conflict(specific_part)，含两条记录 id。"""
        existing = row(2, building=UNDERGROUND_BUILDING, floor="负一", room="1", unit_type="OTHER")
        plan = plan_relocation([row(1, building="1", floor="负一", room="1"), existing])
        by_kind = {c.kind: c for c in plan.conflicts}
        self.assertEqual(set(by_kind), {"specific_part", "tuple"})
        self.assertEqual(set(by_kind["specific_part"].unit_ids), {1, 2})
        self.assertEqual(by_kind["specific_part"].key, "地下车位负一1号")

    def test_tc_unit_629_cr003_unrelated_duplicates_not_reported(self):
        """CR-003：冲突只报告含被改记录的重复组；与被改记录无关的既有重复（大小写）不报。"""
        unrelated_a = row(10, building="X", floor="1", room="a", unit_type="RESIDENCE", sp="X1层a号")
        unrelated_b = row(11, building="Y", floor="1", room="b", unit_type="RESIDENCE", sp="x1层A号")
        plan = plan_relocation([row(1, floor="负一", room="1"), unrelated_a, unrelated_b])
        self.assertEqual(plan.conflicts, ())
        self.assertEqual(len(plan.moves), 1)

    def test_tc_unit_630_casefold_conflict_when_moved_record_involved(self):
        """CR-003 对照：重复组含被改记录（标识仅大小写不同）→ 仍报冲突。"""
        other = row(2, building=UNDERGROUND_BUILDING, floor="负一", room="a", unit_type="OTHER",
                    sp="地下车位负一a")
        plan = plan_relocation([row(1, floor="负一", room="A"), other])
        self.assertEqual([c.kind for c in plan.conflicts if c.kind == "specific_part"], ["specific_part"])
