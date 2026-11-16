"""PHASE_07 单元测试：数字自然顺序规则（MOD-104，IFC-285~287）。

关联 US-183（AC-183-01~06）、US-184（AC-184-03）、US-185（AC-185-01）、US-186（AC-186-01）。
"""
from django.test import SimpleTestCase

from apps.registry.ordering import (
    UNDERGROUND_BUILDING, natural_key, parse_integer_text, sorted_values, unit_sort_key,
)


class ParseIntegerTextTests(SimpleTestCase):
    def test_tc_unit_610_arabic_chinese_and_signed_values(self):
        """AC-183-06：负一/-1/负1 同值 -1，负二 -2，十一 11。"""
        cases = {"-1": -1, "负1": -1, "负一": -1, "负二": -2, "-2": -2, "1": 1, "10": 10,
                 "十": 10, "十一": 11, "二十": 20, "０８": 8, "零": 0}
        for text, expected in cases.items():
            self.assertEqual(parse_integer_text(text), expected, text)

    def test_tc_unit_611_suffix_stripped_once(self):
        """AC-183-01：'10栋' 带后缀按数值 10；'负一层' 按 -1。"""
        self.assertEqual(parse_integer_text("10栋", "栋"), 10)
        self.assertEqual(parse_integer_text("负一层", "层"), -1)
        self.assertEqual(parse_integer_text("1单元", "单元"), 1)
        self.assertIsNone(parse_integer_text("栋", "栋"))

    def test_tc_unit_612_non_numeric_returns_none_without_raising(self):
        """AC-183-04：非数字文字返回 None，不抛异常（含 None、空串、超过 99 的中文数字）。"""
        for text in (None, "", "  ", "A2", "B1", "负", "-", "一百", "地下车位"):
            self.assertIsNone(parse_integer_text(text), repr(text))


class NaturalKeyOrderTests(SimpleTestCase):
    def test_tc_unit_613_buildings_1_2_10_11(self):
        """AC-183-01：楼栋 1、2、10、11 的顺序（不是 1、10、11、2）。"""
        self.assertEqual(sorted_values(["11", "2", "10", "1"], "building"), ["1", "2", "10", "11"])

    def test_tc_unit_614_building_with_suffix_mixed(self):
        """AC-183-01：'1栋/2栋/10栋' 带后缀写法同样按数值，并与不带后缀的 '1' 相邻且全部保留。"""
        result = sorted_values(["10栋", "2栋", "1栋", "1"], "building")
        self.assertEqual(sorted(result), sorted(["10栋", "2栋", "1栋", "1"]))
        self.assertEqual([parse_integer_text(v, "栋") for v in result], [1, 1, 2, 10])
        self.assertEqual(result[-1], "10栋")

    def test_tc_unit_615_unit_and_room_numbers(self):
        """AC-183-02：单元 1、2、10；户号 101、902、1001。"""
        self.assertEqual(sorted_values(["10", "2", "1"], "unit_no"), ["1", "2", "10"])
        self.assertEqual(sorted_values(["1001", "902", "101"], "room"), ["101", "902", "1001"])

    def test_tc_unit_616_floors_negative_first(self):
        """AC-183-03：-1、1、2、10 → -1 在最前。"""
        self.assertEqual(sorted_values(["10", "2", "1", "-1"], "floor"), ["-1", "1", "2", "10"])

    def test_tc_unit_617_text_rooms_after_numbers_digit_segments_numeric(self):
        """AC-183-04：5 在前，其后 A2、A10（数字段按数值），无丢失无重复。"""
        self.assertEqual(sorted_values(["A10", "A2", "5", "A2"], "room"), ["5", "A2", "A10"])

    def test_tc_unit_618_chinese_negative_floor_spellings(self):
        """AC-183-06 / AC-186-01：负二 < 负一 ≈ -1 < 1 < 2，所有写法都保留。"""
        values = ["2", "负一", "1", "-1", "负二", "负1"]
        result = sorted_values(values, "floor")
        self.assertEqual(result[0], "负二")
        self.assertEqual(set(result[1:4]), {"负一", "-1", "负1"})
        self.assertEqual(result[4:], ["1", "2"])
        self.assertEqual(sorted(result), sorted(set(values)))

    def test_tc_unit_619_underground_building_last_only_for_building(self):
        """AC-184-03 / AC-185-01：楼栋级"地下车位"排在所有编号楼栋之后（含非数字楼栋 'A区'）。"""
        self.assertEqual(sorted_values(["地下车位", "10", "1", "A区"], "building"),
                         ["1", "10", "A区", UNDERGROUND_BUILDING])
        # 仅 building 级保留：其他层级"地下车位"只是普通文字
        self.assertEqual(natural_key("地下车位", "floor")[0], 1)
        self.assertEqual(natural_key("地下车位", "building")[0], 2)

    def test_tc_unit_620_empty_values_first_and_not_dropped(self):
        """AC-183-05：空值键层级最低；sorted_values 不改写不丢弃。"""
        self.assertEqual(natural_key(None, "unit_no"), natural_key("", "unit_no"))
        self.assertLess(natural_key("", "floor"), natural_key("-5", "floor"))
        self.assertEqual(sorted_values(["2", "", "1"], "unit_no"), ["", "1", "2"])

    def test_tc_unit_621_keys_always_mutually_comparable(self):
        """IFC-285：任意混合输入的键可两两比较（不出现 int 与 str 混比 TypeError）。"""
        mixed = ["", "1", "-1", "负一", "A2", "A10", "B1", "1栋", "地下车位", "十二", "3a", "a3"]
        for level in ("building", "unit_no", "floor", "room"):
            ordered = sorted(mixed, key=lambda v: natural_key(v, level))
            self.assertEqual(len(ordered), len(mixed))

    def test_tc_unit_622_unit_sort_key_four_levels_and_id_tiebreak(self):
        """AC-192-01：四级键 + unit_id 并列；2栋 < 10栋 < 地下车位。"""
        keys = [unit_sort_key("地下车位", "", "负一", "5", 3),
                unit_sort_key("10栋", "1单元", "1", "101", 2),
                unit_sort_key("2栋", "1单元", "1", "101", 1)]
        self.assertEqual([k[-1] for k in sorted(keys)], [1, 2, 3])
        self.assertLess(unit_sort_key("1", "1", "1", "101", 1), unit_sort_key("1", "1", "1", "101", 2))
