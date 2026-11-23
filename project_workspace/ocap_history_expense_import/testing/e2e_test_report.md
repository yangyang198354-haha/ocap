<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-23T18:04:30+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/testing/test_plan.md</file><file>project_workspace/ocap_history_expense_import/testing/integration_test_report.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（历史支出导入）

## 摘要

critical path 口径：替代（后端 API 多步旅程 + Web 页面组件用例；项目无浏览器 E2E 框架）。

- total = pass + fail + skip + blocked + not_testable = 1 = 1 + 0 + 0 + 0 + 0（新增 E2E 旅程 1 条；Web 页面用例见单元报告）。
- critical path 覆盖率 = 4/4 Must Have 故事 = 100%（US-333、US-334、US-337、US-338 均在最高可执行层有用例）。
- critical path 通过率 = 100%。
- 全量回归：后端 1218 通过、前端 55 文件/590 通过；相对基线（1191 / 54 文件 / 585）新增失败 0。
- **本层门控：PASSED**。

## 全量回归

```
$ cd /workspace/backend && /tmp/ocap-venv/bin/python manage.py test --settings=config.test_settings
Ran 1218 tests in 91.393s
OK
Found 1218 test(s).

$ cd /workspace/frontend && npx vitest run
 Test Files  55 passed (55)
      Tests  590 passed (590)

$ cd /workspace/frontend && VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/
✓ built in 18.36s
```

相对基线新增失败：0（基线 1191 / 585，画像 P4；前端文件数 54→55 为新增 spec）。

## 用户旅程

### TC-E2E-2101: 主任补录 2022Q3 历史支出 → 生成往年报表 → 整批作废 → 重导

- 关联：US-334 / AC-334-01，US-335 / AC-335-01，US-336 / AC-336-01、02，US-337 / AC-337-01、03，US-338 / AC-338-01。
- 环境：Django test client + SQLite 内存库；xlsx 由 openpyxl 内存生成。
- 位置：`backend/tests/e2e/test_history_expense_journey.py::HistoryExpenseJourneyTests::test_tc_e2e_history_expense_full_journey`。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 主任上传含 3 行的 xlsx | 201；imported_rows=3；台账 3 条 | 一致 | PASS |
| 2 | GET 批次列表 | total_amount=350.50 | 一致 | PASS |
| 3 | 生成 2022Q3 报表 | total_expense=350.50，明细含 3 条历史来源 | 一致 | PASS |
| 4 | 业主查看该报表 | 200 | 一致 | PASS |
| 5 | 整批作废 | 报表 stale=True | 一致 | PASS |
| 6 | 重新生成 2022Q3 | total_expense=0.00 | 一致 | PASS |
| 7 | 再次导入同一文件 | 201；imported_rows=3；1 条 VOIDED + 1 条 IMPORTED | 一致 | PASS |
| 8 | 业主尝试导入 | 403 | 一致 | PASS |

- 结论：PASS。

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| DEF-001 | MAJOR（已修复） | 管理员令牌访问历史支出/收入接口返回 401，AC-338-01 要求 403 | TC-INT-2114 | `backend/apps/core/permissions.py:96-101`；已与 `IsMember` 对齐返回 403 |

无未修复缺陷。

## 人工验证清单

无（本期无 manual/hil 用例，测试替身为内存实现）。

## 冻结核对

四个测试文件最后修改时间：17:55:27 / 17:55:39 / 17:56:05 / 17:56:23；本报告与 unit/integration 报告均在 18:01 之后写入，之后未再修改测试文件；报告计数取自 18:00 前最后一次全量执行。
