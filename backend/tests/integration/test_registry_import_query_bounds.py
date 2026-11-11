"""DEF-013 回归（TC-INT-312 / TC-INT-313）：清册导入回查查询的参数个数与查询数有界。

背景：提交 6fbd24d 把 `_create_owners` 的 __in 回查按 unit_id 分批，但每批仍带全部业主姓名，
20000 行时每条查询约 20000 个参数 × 40 批，正式导入超过 60 s（TC-E2E-302/303 504 IMPORT_TIMEOUT）。

本组用例不依赖机器速度：用 `connection.execute_wrapper` 记录每条 SQL 的实际绑定参数个数，
断言 (a) 回查类 SELECT 单条参数数 <= 批大小 500（远低于 SQLite 旧上限 999）；
(b) 回查 SELECT 条数随批数线性有界（不随姓名数放大）。每批带全集的实现会同时违反 (a)。
"""
import math
from decimal import Decimal

from django.db import connection

from apps.registry.importing import ImportPlan, PlannedOwner, _create_owners, Deadline
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit, build_specific_part
from django.core.files.uploadedfile import SimpleUploadedFile
from tests.integration.test_registry_import_enhancement import csv_bytes, row
from tests.support import ApiTestBase

BATCH = 500
SQLITE_LEGACY_LIMIT = 999


def unit_key(index: int) -> str:
    return build_specific_part("B", "1", "1", str(index)).casefold()


class QueryRecorder:
    """记录 (sql, 参数个数)；many=True 的批量执行按单次参数个数计。"""

    def __init__(self):
        self.entries: list[tuple[str, int]] = []

    def __call__(self, execute, sql, params, many, context):
        if params is not None and not many:
            self.entries.append((sql, len(params)))
        return execute(sql, params, many, context)

    def owner_selects(self):
        return [(s, n) for s, n in self.entries
                if s.lstrip().upper().startswith("SELECT") and f'"{RegistryOwner._meta.db_table}"' in s]


class CreateOwnersBoundTests(ApiTestBase):
    UNITS = 1200  # 3 个批次（500/500/200），全集参数数 1200 + 批大小 > 999

    def _make_units(self, count):
        units = RegistryUnit.objects.bulk_create([
            RegistryUnit(building="B", unit_no="1", floor="1", room=str(i),
                         specific_part=build_specific_part("B", "1", "1", str(i)),
                         unit_type="RESIDENCE", area=Decimal("89.50"))
            for i in range(count)
        ], batch_size=BATCH)
        return {u.specific_part.casefold(): u.id for u in RegistryUnit.objects.all()}, units

    def test_tc_int_312_create_owners_lookup_params_bounded_and_correct(self):
        """TC-INT-312 / AC-094-07、AC-100-07、AC-100-08：_create_owners 回查单条参数数 <= 500，结果映射正确。"""
        unit_ids, _ = self._make_units(self.UNITS)
        # 预置一位同单元的既有业主，姓名不在计划内，不得被映射进结果
        pre_unit = unit_ids[unit_key(0)]
        RegistryOwner.objects.create(unit_id=pre_unit, name="既有业主")

        plan = ImportPlan(rows_total=self.UNITS)
        for i in range(self.UNITS):
            plan.owners_to_create.append(PlannedOwner(unit_key=unit_key(i), name=f"业主{i}", unit_id=unit_ids[unit_key(i)]))

        recorder = QueryRecorder()
        with connection.execute_wrapper(recorder):
            result = _create_owners(plan, {}, Deadline(60))

        selects = recorder.owner_selects()
        self.assertTrue(selects, "应至少有一条 registry_owner 回查 SELECT")
        worst = max(n for _, n in selects)
        self.assertLessEqual(worst, BATCH, f"回查单条参数数 {worst} 超过批大小 {BATCH}（DEF-013：每批带全集）")
        self.assertLess(worst, SQLITE_LEGACY_LIMIT)
        self.assertLessEqual(len(selects), math.ceil(self.UNITS / BATCH), "回查条数应等于批数，不随姓名数放大")

        # 映射正确：每个计划业主都有 id，且 id 对应库中该单元该姓名的行；既有业主不入结果
        self.assertEqual(len(result), self.UNITS)
        self.assertNotIn((unit_key(0), "既有业主"), result)
        for i in (0, 499, 500, 1199):
            owner = RegistryOwner.objects.get(id=result[(unit_key(i), f"业主{i}")])
            self.assertEqual((owner.unit_id, owner.name), (unit_ids[unit_key(i)], f"业主{i}"))

    def test_tc_int_312b_same_unit_multiple_owners_mapped(self):
        """TC-INT-312 / AC-094-01：同一单元多位业主（含跨批单元），(unit,name) 精确映射。"""
        unit_ids, _ = self._make_units(600)
        plan = ImportPlan(rows_total=1200)
        for i in range(600):
            for name in ("甲", "乙"):
                plan.owners_to_create.append(
                    PlannedOwner(unit_key=unit_key(i), name=f"{name}{i}", unit_id=unit_ids[unit_key(i)]))
        result = _create_owners(plan, {}, Deadline(60))
        self.assertEqual(len(result), 1200)
        self.assertEqual(RegistryOwner.objects.get(id=result[(unit_key(599), "乙599")]).unit_id, unit_ids[unit_key(599)])
        self.assertEqual(RegistryOwner.objects.get(id=result[(unit_key(0), "甲0")]).name, "甲0")


class ImportQueryBoundsApiTests(ApiTestBase):
    N = 1500  # 经 API 的完整导入链路：3 个批次

    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()

    def test_tc_int_313_full_import_query_params_bounded(self):
        """TC-INT-313 / AC-094-07、AC-100-08：整条正式导入链路中，所有 registry 表查询的单条参数数 <= 999，
        且回查 SELECT 条数有界；导入结果计数正确。"""
        rows = [row(building=f"B{i // 100}", unit="1", floor=str(i % 30 + 1), room=str(i),
                    name=f"业主{i}", phone=f"137{i:08d}") for i in range(self.N)]
        upload = SimpleUploadedFile("registry.csv", csv_bytes(rows), content_type="text/csv")
        recorder = QueryRecorder()
        with connection.execute_wrapper(recorder):
            resp = self.upload("/admin/registry/import", {"file": upload}, token=self.admin_token)
        self.assertEqual(resp.status_code, 200, resp.content[:300])
        self.assertEqual((resp.data["rows_total"], resp.data["rows_ok"], resp.data["failed"]), (self.N, self.N, 0))
        self.assertEqual((resp.data["imported"], resp.data["owners_created"], resp.data["phones_created"]),
                         (self.N, self.N, self.N))
        self.assertEqual(RegistryOwner.objects.count(), self.N)
        self.assertEqual(RegistryPhone.objects.count(), self.N)

        registry_queries = [(s, n) for s, n in recorder.entries if '"registry_' in s]
        self.assertTrue(registry_queries)
        worst_sql, worst = max(registry_queries, key=lambda e: e[1])
        self.assertLessEqual(worst, SQLITE_LEGACY_LIMIT, f"存在参数数 {worst} 的查询：{worst_sql[:120]}")
        # 回查类 SELECT（不含 prefetch 的 owner_id IN）条数：三处回查各约 ceil(N/500) 条，整体有界
        selects = recorder.owner_selects()
        self.assertLessEqual(len(selects), 6 * math.ceil(self.N / BATCH))
        self.assertLessEqual(max(n for _, n in selects), BATCH)
