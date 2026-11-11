"""MOD-064 / IFC-243：专有部分拼接规则金标（US-132、US-133）。"""
import ast
from pathlib import Path

from django.test import SimpleTestCase

from apps.registry.models import build_specific_part


class SpecificPartRuleTests(SimpleTestCase):
    def test_tc_unit_201_full_fields(self):
        """AC-132-01/04：四级齐全时直接连接并补后缀。"""
        self.assertEqual(build_specific_part("1栋", "1单元", "1", "101"), "1栋1单元1层101号")
        self.assertEqual(build_specific_part("10栋", "3单元", "10", "1001"), "10栋3单元10层1001号")

    def test_tc_unit_202_empty_levels(self):
        """AC-132-02/03：空段跳过，车位与商铺。"""
        self.assertEqual(build_specific_part("1栋", "", "负1", "924"), "1栋负1层924号")
        self.assertEqual(build_specific_part("10栋", "", "1", "1"), "10栋1层1号")

    def test_tc_unit_203_suffix_not_duplicated(self):
        """AC-133-01/02：已带后缀与纯数字生成同一结果。"""
        self.assertEqual(build_specific_part("1栋", "1单元", "1层", "101号"), "1栋1单元1层101号")
        self.assertEqual(build_specific_part("1", "1", "1", "101"), "1栋1单元1层101号")

    def test_tc_unit_204_non_numeric_values(self):
        """AC-133-03/05/06：非数字保持原样。"""
        self.assertEqual(build_specific_part("建设南路146号", "", "", "整栋"), "建设南路146号整栋")
        self.assertEqual(build_specific_part("1栋", "", "", "924"), "1栋924号")
        self.assertEqual(build_specific_part("1栋", "", "-1", "924"), "1栋-1924号")
        self.assertEqual(build_specific_part("1栋", "", "B1", "924"), "1栋B1924号")
        self.assertEqual(build_specific_part("车库", "", "", "A-088"), "车库A-088")

    def test_tc_unit_205_floor_implied_by_room(self):
        """AC-133-04/08/09：户号以“楼层值+层”开头时省略楼层段。"""
        self.assertEqual(build_specific_part("圣灯路155号", "", "1", "1层"), "圣灯路155号1层")
        self.assertEqual(build_specific_part("建设南路160号", "", "1", "1层A"), "建设南路160号1层A")
        self.assertEqual(build_specific_part("建设南路160号", "", "1", "1层B"), "建设南路160号1层B")
        self.assertEqual(build_specific_part("建设南路160号", "", "2", "1层"), "建设南路160号2层1层")

    def test_tc_unit_206_strip_and_decimal(self):
        """AC-133-07：首尾空格去除；“3.0”不视为纯数字。"""
        self.assertEqual(build_specific_part(" 1栋 ", "", "", "101"), "1栋101号")
        self.assertEqual(build_specific_part("1栋", "", "3.0", "101"), "1栋3.0101号")

    def test_tc_unit_207_single_definition(self):
        """ADR-069：apps/ 下只有一个 build_specific_part 定义，registry 内无旧式 "-".join。"""
        backend = Path(__file__).resolve().parents[2]
        definitions = []
        legacy_join = []
        for path in (backend / "apps").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "build_specific_part":
                    definitions.append(path.relative_to(backend).as_posix())
            if path.parts[-2] == "registry" and '"-".join(' in text:
                legacy_join.append(path.relative_to(backend).as_posix())
        self.assertEqual(definitions, ["apps/registry/models.py"])
        self.assertEqual(legacy_join, [])
