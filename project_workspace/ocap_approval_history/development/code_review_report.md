<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-27T09:28:09.0530216+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/tech_stack.md</file>
    <file>development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 审批与同住人申请历史记录代码评审报告

## 摘要

本批实现 4 个 MOD、核验 1 个继承 MOD；修改 6 个产品文件，并最小调整 1 个既有前端契约测试。 scoped `git diff --stat`：

```text
 backend/apps/approval/views.py            | 68 ++++++++++++++++++++++++++++---
 backend/apps/residency/urls.py            |  6 ++-
 backend/apps/residency/views.py           | 27 +++++++++---
 frontend/src/portal/Tasks.vue             | 28 +++++++++----
 frontend/src/portal/units/UnitsReview.vue | 57 ++++++++++++++++++--------
 frontend/src/shared/api.js                |  4 ++
 frontend/tests/layout_contract.spec.js    |  2 +-
 7 files changed, 154 insertions(+), 38 deletions(-)
```

其中 `frontend/src/shared/api.js` 的收入表 `deleteSheet` 2 行是任务开始前已有未提交改动，不属于本批且未修改；其余收入表软删除、审计、记忆及其他项目文件也均保留。五维平均分 9.16/10；问题统计 CRITICAL 0（已修复 0）/ MAJOR 1（已修复 1）/ MINOR 1（已修复 1），无未解决问题。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC | 说明 |
|---|---|---|
| `backend/apps/approval/views.py` | MOD-228 / IFC-454 | `view=todo|handled`、本人实际动作去重查询、最近动作摘要、scope 与分页 |
| `backend/apps/residency/views.py` | MOD-230 / IFC-455；MOD-232 | 新增固定 APPROVED 查询；共享审批人序列化；本人申请查询保持不变 |
| `backend/apps/residency/urls.py` | MOD-230 / IFC-455 | 注册 `resident-applications/approved` |
| `frontend/src/portal/Tasks.vue` | MOD-229 / IFC-454、IFC-456 | 待办/已处理切换、历史摘要、空态、筛选分页和只读时间线 |
| `frontend/src/portal/units/UnitsReview.vue` | MOD-231 / IFC-457 | 已通过记录、空态和处理后同步刷新 |
| `frontend/src/shared/api.js` | MOD-231 / IFC-457 | 新增 `approvedResidentApplications()`；既有 `approvalApi.tasks` 直接复用 |
| `frontend/tests/layout_contract.spec.js` | IFC-457 契约基线 | 仅在既有白名单加入新增函数，不断言放宽 |

## 自验证结果

| 检查 | 实际命令 | 输出尾部 / 结论 |
|---|---|---|
| 后端编译 | 仓库根：`python -m compileall -q backend` | `COMPILE_OK` |
| 后端相关测试 | `backend/`：`$env:DJANGO_SECRET_KEY='test-only'; python manage.py test tests.integration.test_approval_flow_steps tests.integration.test_approval_finality tests.integration.test_approval_resolution_api tests.integration.test_residency_api tests.integration.test_owner_auth_v2_residency --settings=config.test_settings` | `Ran 101 tests in 2.309s`；`OK` |
| 前端契约复测 | `frontend/`：`npx vitest run tests/layout_contract.spec.js --passWithNoTests` | `Test Files 1 passed (1)`；`Tests 6 passed (6)` |
| 前端全量测试 | `frontend/`：`npx vitest run --passWithNoTests` | `Test Files 61 passed (61)`；`Tests 631 passed (631)`；`Duration 292.21s` |
| Web 生产构建 | `frontend/`：`$env:VITE_API_BASE='/ocap/api/v1'; npm run build -- --base=/ocap/` | `1887 modules transformed`；`✓ built in 9.22s`；仅有既有大 chunk 警告 |
| 改动格式 | 仓库根：对以上 7 个文件执行 `git diff --check -- ...` | 退出码 0，无空白错误 |

未执行迁移检查：本批无模型或迁移变更。未运行小程序测试或构建：本批经用户确认仅覆盖 Web。

## 按模块评审

### MOD-228

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

- 以 `ApprovalAction.actor` 与 `APPROVE`/`REJECT` 为收录依据，实例 `distinct()` 去重；`my_*` 取本人最近动作，终单由既有状态机清空当前步骤。
- 沿用 `IsCommitteeMember`，未扩大离任后的可见性；非法视图、scope 和非整数分页均由 `ApiError` 拦截。
- 预取本人动作与步骤状态；沿用既有内存分页方式，避免为历史视图另建查询体系。

### MOD-229

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

- 复用 `usePaging`，切换视图或 scope 均重置分页；已处理行显示约定字段，待办默认行为保持。
- 只有待办视图渲染“同意”“拒绝”；历史仅通过既有 `ApprovalTimeline` 读取详情。

### MOD-230

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

- 每次请求按有效 `HEAD`/`OWNER` 关系计算专有部分，固定 `status="APPROVED"`；其他状态和失去产权后的记录均不返回。
- 复用申请人摘要及手机号脱敏；`select_related` 避免逐行读取房屋和申请人。

### MOD-231

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

- 展示专有部分、申请人、实名快照、提交/处理时间、通过状态和备注；空态及只读操作符合 IFC。
- 处理后并行刷新既有待办/角标和已通过记录；不引入新状态仓库。

### MOD-232

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |

- `ResidentApplicationMineView` 仍为 `applicant=request.user`；`UnitsApplicationRecords.vue` 仍显示通过状态、处理时间与处理备注。
- 未修改申请人查询或页面，既有 residency 测试通过。

## CR 问题表

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MAJOR | `frontend/tests/layout_contract.spec.js:103` | 新增 IFC-457 导出后，TC-INT-923 固定白名单缺少 `approvedResidentApplications`，全量前端测试出现 1 个失败 | FIXED |
| CR-002 | MINOR | `frontend/src/portal/Tasks.vue:30` | 多步在途的已处理记录最初复用 PENDING 的“待审批”文案，与 AC-370-02 的“审批中”不一致 | FIXED |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无。

## 缺陷修复

非缺陷修复模式，无 DEF 回流。

## 现有测试调整

1. `frontend/tests/layout_contract.spec.js` 的 TC-INT-923：按排序在 `unitApi` 期望数组开头加入 `approvedResidentApplications`。原因是 IFC-455/457 有意新增该只读 API；未删除既有期望、未放宽相等断言，也未新增测试文件。调整后该文件 6/6 通过。
