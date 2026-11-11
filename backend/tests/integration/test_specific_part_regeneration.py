"""MOD-065 / IFC-244：存量标识重新生成迁移（US-134、REQ-NFUNC-19/23）。"""
import contextlib
import importlib
import io
import time

from django.db import connection
from django.test import TestCase

from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit

migration = importlib.import_module("apps.registry.migrations.0005_regenerate_specific_part")


class FakeSchemaEditor:
    def __init__(self):
        self.connection = connection


class RegenerationTests(TestCase):
    def _rows(self, rows):
        RegistryUnit.objects.bulk_create([
            RegistryUnit(building=building, unit_no=unit_no, floor=floor, room=room,
                         specific_part=specific_part)
            for building, unit_no, floor, room, specific_part in rows
        ], batch_size=200)

    def _run(self, func):
        apps = __import__("django.apps", fromlist=["apps"]).apps
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            func(apps, FakeSchemaEditor())
        return out.getvalue(), err.getvalue()

    def test_tc_int_401_regenerate_and_reverse(self):
        """AC-134-01/02/03：按新规则重生成、字段不变、可逆。"""
        self._rows([
            ("10栋", "3单元", "10", "1001", "10栋-3单元-10-1001"),
            ("1栋", "", "负1", "924", "1栋-负1-924"),
            ("10栋", "", "1", "1", "10栋-1-1"),
        ])
        unit = RegistryUnit.objects.get(room="1001")
        owner = RegistryOwner.objects.create(unit=unit, name="张三")
        RegistryPhone.objects.create(unit=unit, owner=owner, phone="13800000001")

        out, _ = self._run(migration.regenerate_specific_parts)
        self.assertIn("total=3", out)
        self.assertEqual(RegistryUnit.objects.get(room="1001").specific_part, "10栋3单元10层1001号")
        self.assertEqual(RegistryUnit.objects.get(room="924").specific_part, "1栋负1层924号")
        self.assertEqual(RegistryUnit.objects.get(room="1").specific_part, "10栋1层1号")
        self.assertEqual(RegistryUnit.objects.get(room="1001").building, "10栋")
        self.assertEqual(RegistryUnit.objects.get(room="1001").floor, "10")
        self.assertEqual(RegistryOwner.objects.filter(unit__room="1001").count(), 1)
        self.assertEqual(RegistryPhone.objects.count(), 1)

        # 幂等：第二次无变化
        out2, _ = self._run(migration.regenerate_specific_parts)
        self.assertIn("would_change=0", out2)

        # 反向：恢复旧格式
        self._run(migration.restore_legacy_specific_parts)
        self.assertEqual(RegistryUnit.objects.get(room="1001").specific_part, "10栋-3单元-10-1001")

    def test_tc_int_402_conflict_aborts_whole_batch(self):
        """AC-134-04：重新生成后标识相同 → 整批不生效并输出冲突。"""
        self._rows([
            ("1", "1", "1", "101", "1-1-1-101"),
            ("1", "1", "1层", "101号", "1-1-1层-101号"),
        ])
        with self.assertRaises(RuntimeError):
            self._run(migration.regenerate_specific_parts)
        self.assertEqual(
            sorted(RegistryUnit.objects.values_list("specific_part", flat=True)),
            ["1-1-1-101", "1-1-1层-101号"],
        )

    def test_tc_int_403_cross_update_has_no_conflict(self):
        """ADR-067：新值等于另一行旧值时，两阶段更新成功。"""
        self._rows([
            ("车库", "", "", "A-088", "车库-A-088"),
            ("车库A", "", "", "088", "车库A-088"),
        ])
        self._run(migration.regenerate_specific_parts)
        values = set(RegistryUnit.objects.values_list("specific_part", flat=True))
        self.assertEqual(values, {"车库A-088", "车库A088号"})

    def test_tc_int_404_review_lists_non_numeric_rooms(self):
        """AC-134-05：户号非纯数字进入核对清单。"""
        self._rows([
            ("建设南路146号", "", "", "整栋", "建设南路146号-整栋"),
            ("1栋", "1单元", "1", "101", "1栋-1单元-1-101"),
        ])
        out, _ = self._run(migration.regenerate_specific_parts)
        self.assertIn("review=1", out)
        self.assertIn("建设南路146号-整栋|建设南路146号整栋", out)

    def test_tc_int_405_large_batch_under_time_budget(self):
        """AC-134-06 / REQ-NFUNC-23：5742 条在 60 秒内完成。"""
        rows = [("B", "1", "1", str(i), f"B-1-1-{i}") for i in range(5742)]
        self._rows(rows)
        started = time.monotonic()
        out, _ = self._run(migration.regenerate_specific_parts)
        elapsed = time.monotonic() - started
        self.assertIn("total=5742", out)
        self.assertLess(elapsed, 60)
