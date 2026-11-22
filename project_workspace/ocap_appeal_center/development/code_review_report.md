<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-22T10:57:49+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>project_workspace/ocap_appeal_center/development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告 — 申诉与同住人申请记录中心

## 摘要

- 改动文件 29 个（后端 8、前端/小程序 21），`git diff --stat`：386 insertions(+), 135 deletions(-)；另有 4 个新文件（AppealCenter.vue、UnitsApplicationForm.vue、UnitsApplicationRecords.vue、0006_appeal_center.py）。
- 五维平均分：8.6 / 10。
- 问题统计：CRITICAL 0（已修复 0）/ MAJOR 0 / MINOR 7（已修复 4、OPEN 3）。

## 文件 → MOD/IFC 映射

| 文件 | MOD/IFC |
|---|---|
| `backend/apps/residency/models.py` | MOD-168/169、ADR-161/165 |
| `backend/apps/residency/migrations/0006_appeal_center.py` | MOD-168/169、数据迁移 |
| `backend/apps/residency/views.py`、`urls.py` | MOD-168/169、IFC-381~388 |
| `backend/apps/residency/housing.py` | MOD-169、IFC-389 |
| `frontend/src/shared/api.js` | MOD-173、IFC-391 |
| `frontend/src/shared/labels.js`、`miniprogram/utils/labels.js` | MOD-173、IFC-391e |
| `frontend/src/portal/units/AppealCenter.vue` | MOD-170、IFC-392a |
| `frontend/src/portal/units/UnitsAppeal.vue` | MOD-170、IFC-392a/b |
| `frontend/src/portal/units/UnitsMyAppeals.vue` | MOD-170、IFC-392b |
| `frontend/src/portal/units/UnitsApplications.vue` | MOD-171、IFC-392c |
| `frontend/src/portal/units/UnitsApplicationForm.vue` | MOD-171、IFC-392d |
| `frontend/src/portal/units/UnitsApplicationRecords.vue` | MOD-171、IFC-392c |
| `frontend/src/portal/units/UnitsIdentity.vue` | MOD-172、IFC-392e |
| `frontend/src/portal/Units.vue`、`layout/menus.js` | MOD-170、ADR-160 |
| `frontend/src/admin/AdminAppeals.vue` | MOD-168、IFC-384 |

## 自验证结果

以下为 1.1.0 缺陷修复后的复跑结果（DEF-AC-01 修复完成后执行）：

1. 后端全量测试：

```
Ran 1167 tests in 45.831s

OK (skipped=2)
```

（基线 1159 通过 / 2 skipped + GROUP_D 新增 8 条集成/E2E；本次 1167 全部通过，零失败。）

2. 前端全量测试：

```
Test Files  50 passed (50)
     Tests  568 passed (568)
```

（基线 562 通过 + GROUP_D 新增 6 条；本次 568 全部通过，零失败。）

3. 前端构建：

```
✓ built in 8.43s
```

（仅有既有 chunk >500kB 警告，无错误。）

4. 迁移一致性：

```
$ DJANGO_SECRET_KEY=<dummy> python manage.py makemigrations --check --dry-run residency
No changes detected in app 'residency'
```

（使用 test_settings 时 MIGRATION_MODULES 禁用迁移，故以默认配置执行只读检查，未生成文件。）

未验证项：无。

## 按模块评审

### MOD-168（申诉后端）

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 8/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-306 | MINOR | `views.py:AppealWithdrawView` | 撤回使用条件 update 防并发，但审计在事务内读取对象；高并发下审计对象快照一致，已确认无副作用 | FIXED |
| CR-307 | MINOR | `AdminAppeals.vue:57-68` | 备注输入放在操作列内，宽度收窄到 130px 以保持 ADR-121 表格总宽 | FIXED |

### MOD-169（同住申请后端与聚合）

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 8/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-308 | MINOR | `views.py:ResidentApplicationCreateView` | `applicant_name` 后端按“提供时校验、缺省允许”实现（IFC-385 偏差，兼容旧小程序） | OPEN |
| CR-309 | MINOR | `housing.py:_latest_resident_names` | 同住人实名与本人实名分两次查询；均为批量 IN 查询、不随行数增长，暂不合并 | OPEN |

### MOD-170（Web 申诉中心）

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 8/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-310 | MINOR | `Units.vue:initialTab`、`menus.js` | 旧地址 /units/appeals 仍可路由并默认“我的申诉”Tab，但菜单不再有独立项，侧栏无二级高亮（leaf=null） | OPEN |

### MOD-171（Web 同住申请中心）

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 8/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-311 | MINOR | `UnitsApplicationForm.vue:applyResident` | 实名 trim 后校验非空与 ≤64，与后端一致 | FIXED |
| CR-312 | MINOR | 前端测试 12 个文件 | 菜单项 5→4、提交体新增 applicant_name、API 导出集合扩展，均属需求驱动的期望更新 | FIXED |

### MOD-172（身份页实名）

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

无新增问题；缺失实名统一“—”，不改变既有空态分支。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无。

## 缺陷修复

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-AC-01 | `backend/apps/core/audit.py:10-15` | 撤回视图（`views.py:306`、`:490`）写入 `APPEAL_WITHDRAWN` / `RESIDENT_APPLICATION_WITHDRAWN`，但 `AUDIT_ACTIONS` 白名单未登记这两个动作；`AuditService.record` 在 `audit.py:66-67` 抛 `ValueError`，导致撤回接口 500 | 仅在 `AUDIT_ACTIONS` 增加两个动作名；未改动 `views.py`、前端、测试或接口契约 |

修复后关键回归：`python manage.py test --settings=config.test_settings` → Ran 1167 tests / OK (skipped=2)，GROUP_D 的 TC-INT-1502/1503/1505 与 TC-E2E-1615/1616 恢复通过。

## 现有测试调整

见 `implementation_plan.md` 的“测试影响”表，共 16 个测试文件；调整均为契约/需求有意变更所致，未放宽断言标准。
