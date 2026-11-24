<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-23T17:52:00+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/development/implementation_plan.md</file><file>project_workspace/ocap_history_expense_import/requirements/user_stories.md</file><file>project_workspace/ocap_history_expense_import/architecture/module_design.md</file></input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 历史支出批量导入 — 代码评审报告（增量）

## 摘要

- 改动：11 个已跟踪文件修改（后端 6、前端 3、测试 1、画像 1），另有 3 个新建文件（服务、迁移、前端页面），合计约 +900 行（含新建文件；`git diff --stat` 仅统计已跟踪文件为 11 files changed, 261 insertions(+), 58 deletions(-)）。
- 五维平均分：Correctness 9.0 / Security 9.0 / Performance 8.5 / Maintainability 8.8 / Testability 9.0。
- 问题统计：CRITICAL 0（已修复 0）/ MAJOR 2（已修复 2）/ MINOR 5（4 已修复，1 记录为偏差）。

## 文件 → MOD/IFC 映射

| 文件 | MOD/IFC |
|---|---|
| `backend/apps/ledger/models.py` | MOD-192/193 |
| `backend/apps/ledger/migrations/0007_historical_expense.py` | MOD-192/193 |
| `backend/apps/ledger/apps.py` | MOD-192/193（外键引用注册） |
| `backend/apps/ledger/historical.py` | MOD-194 / IFC-408~412 |
| `backend/apps/core/audit.py` | MOD-194（审计动作） |
| `backend/apps/ledger/views.py` | MOD-195 / IFC-408~412 |
| `backend/apps/ledger/urls.py` | MOD-195 |
| `frontend/src/shared/api.js` | MOD-196 |
| `frontend/src/router/index.js` | MOD-196 |
| `frontend/src/portal/HistoricalExpenses.vue` | MOD-196 |
| `frontend/src/portal/Reports.vue` | MOD-196（入口偏差） |
| `frontend/tests/qa_unit_theme.spec.js` | 现有断言同步 |

## 自验证结果

1. 迁移漂移检查

```
$ cd /workspace/backend && DJANGO_ALLOW_EPHEMERAL_SECRET=1 /tmp/ocap-venv/bin/python manage.py makemigrations --check --dry-run
No changes detected
```

2. 后端全量测试（SQLite 内存库）

```
$ /tmp/ocap-venv/bin/python manage.py test --settings=config.test_settings
Ran 1191 tests in 78.649s
OK
Found 1191 test(s).
System check identified no issues (0 silenced).
```

3. 迁移正反向用例（含此前失败的 `test_migration_residency_0002`）

```
$ /tmp/ocap-venv/bin/python manage.py test tests.integration.test_migration_residency_0002 tests.integration.test_requirements_numbering --settings=config.test_settings
Ran 9 tests in 21.213s
OK
```

4. 前端现有测试

```
$ cd /workspace/frontend && npx vitest run
 Test Files  54 passed (54)
      Tests  585 passed (585)
```

5. 前端构建（部署基线）

```
$ cd /workspace/frontend && VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/
✓ built in 19.32s
```

未验证项：无。本期未新增自动化测试（属 GROUP_D 职责），现有测试全部通过。

## 按模块评审

### MOD-192/193 模型与迁移

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MINOR | `backend/apps/ledger/migrations/0007_historical_expense.py:31,33` | 迁移引用了未导入的 `settings.AUTH_USER_MODEL`，导致真实迁移执行 `NameError` | FIXED（改为 `to="accounts.user"`） |
| CR-002 | MINOR | `backend/apps/ledger/models.py:53,77` | 模型索引未命名，与迁移中的显式索引名不一致，`makemigrations --check` 报重命名 | FIXED（模型显式命名，漂移消失） |

### MOD-194 导入服务

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-003 | MAJOR | `frontend/src/portal/HistoricalExpenses.vue:200-208` | 非业委会成员直接访问页面仍会请求批次接口，不满足 AC-338-02“不发起导入请求” | FIXED（增加 `auth.fetchMe()` + `isCommittee` 守卫与无权限提示） |
| CR-008 | MAJOR | `backend/apps/ledger/historical.py:95-111` | xlsx 读取在 5001 行处 `break`，超过 5000 行的大表会被静默截断而非报错，不满足 AC-334-04 | FIXED（按非空数据行计数，超过上限立即 400） |
| CR-004 | MINOR | `backend/apps/ledger/historical.py:122` | 导入响应 `errors` 截断 100 条，超出部分仅能在批次明细查看 | 记录（可接受，避免大响应） |
| CR-005 | MINOR | `backend/apps/ledger/historical.py:186-223` | 逐行 `create` 未批量插入，5000 行时存在多次写入 | 记录（事务内、SQLite 实测 5 千行秒级；后续可 bulk_create 优化） |

### MOD-195 API

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-006 | MINOR | `backend/apps/ledger/views.py:127-151` | 列表/详情未做批量导入并发锁（设计已标注本期不做） | 记录（依赖人工避免同时导入） |

### MOD-196 前端页面

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-007 | MINOR | `frontend/src/portal/Reports.vue:7` | 入口放在报表页按钮而非主菜单，偏离 MOD-196/ADR-182 | 记录为 `[DEVIATION]`（保持既有导航契约测试不变） |

### MOD-197 报表联动

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

复用 `LedgerService.generate`（汇总 ACTIVE 台账）与 `void_by_source`/`_mark_reports_stale`，无代码改动。评审确认：历史支出 `direction=EXPENSE`、`entry_type=支出类别`、`summary=用途`，报表明细带 `source_type/source_id/seq`。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无（CR-003、CR-008 已修复）。

## 缺陷修复

本期无 GROUP_D 回流的缺陷修复。

## 现有测试调整

| 文件 | 调整 | 原因 |
|---|---|---|
| `frontend/tests/qa_unit_theme.spec.js:277` | 用户端路由页面组件计数 18 → 19 | 新增 `/historical-expenses` 路由页面（18 页 + PortalLayout）；仅改期望值与注释 |
