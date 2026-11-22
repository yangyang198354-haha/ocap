<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-22T19:33:01+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.1.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告 — 审批流程多步化与或/与签（ocap_approval_flow）

## 摘要

- 改动：25 个已跟踪文件修改（+685 / -196），另新增 1 个迁移、2 个 Web 组件/页面组件、1 个小程序页面目录、2 个文档目录。
- 五维平均分：8.2 / 10。
- 问题统计：CRITICAL 0（已修复 0）/ MAJOR 0 / MINOR 6。
- 未 commit / push（画像 P9）。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC |
|---|---|
| `backend/apps/approval/models.py` | MOD-183 |
| `backend/apps/approval/migrations/0003_approval_steps.py` | MOD-183 |
| `backend/apps/approval/apps.py` | MOD-183（用户引用合并） |
| `backend/apps/approval/services.py` | MOD-184 / IFC-408 |
| `backend/apps/approval/views.py` | MOD-185~187 / IFC-402~407 |
| `backend/apps/approval/urls.py` | IFC-407 |
| `backend/apps/claims/views.py`、`income/views.py`、`resolutions/views.py` | MOD-186（详情暴露实例 ID） |
| `frontend/src/admin/AdminFlows.vue`、`admin/parts/StepsEditor.vue` | MOD-188 |
| `frontend/src/portal/Tasks.vue`、`portal/ApprovalTimeline.vue`、`portal/ResolutionDetail.vue` | MOD-189 |
| `frontend/src/shared/api.js`、`shared/labels.js` | MOD-189/191 |
| `miniprogram/pages/approvals/*`、`pages.json`、`pages/me/index.vue`、`utils/api.js`、`utils/labels.js` | MOD-190/191 |

## 自验证结果

| 命令 | 工作目录 | 输出尾部 | 结论 |
|---|---|---|---|
| `python -m compileall -q backend` | 仓库根 | 退出码 0 | 通过 |
| `python manage.py test --settings=config.test_settings` | `backend/` | `Ran 1167 tests in 34.195s`；`FAIL: test_tc_int_964_register_and_bind_response_field_registry_match` | 1 个失败为**预存在**：该测试读取 `miniprogram/pages/phone/index.vue` 期望旧的 registry_match 标记，而该文件在上一批次已改为 PhonePane 包装（`git log -1 -- miniprogram/pages/phone/index.vue` = f7316cb，本批次未修改）。除此外全部通过，无新增失败 |
| `python manage.py test tests.integration.test_approval_resolution_api tests.integration.test_approval_finality tests.integration.test_half_majority_flow_approvers` | `backend/` | `Ran 31 tests ... OK` | 通过 |
| `npm test` | `frontend/` | `Test Files 51 passed (51)` | 通过 |
| `npm run build` | `frontend/` | `✓ built in 8.28s` | 通过（仅有既有大 chunk 警告） |
| `npm test` | `miniprogram/` | `Test Files 20 passed (20)` | 通过 |
| `npm run build:mp-weixin` | `miniprogram/` | `ENOENT ... miniprogram/src/manifest.json` | 未验证：仓库缺少 `src/manifest.json`，构建脚本与项目根级目录结构不匹配（预存在，与本批次改动无关）；已删除失败构建产生的 `dist` 残留 |

## 按模块评审

### MOD-183 数据模型与迁移

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MINOR | `migrations/0003_approval_steps.py:forwards` | 历史动作统一归入第 1 步，多步回滚不可完全逆 | OPEN（已按设计记录） |

### MOD-184 判定引擎

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 7/10 | 7/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-002 | MINOR | `services.py:decide` | 单实例用行锁串行化，极端并发下同实例请求排队 | OPEN（可接受，审批低频） |
| CR-003 | MINOR | `services.py:timeline` | 逐实例构建时间线，未做批量接口 | OPEN（详情单条使用） |

### MOD-185 管理后台流程配置 API

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 7/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-004 | MINOR | `views.py:flow_view` | 每个审批人触发 1 次用户查询，后台小数据量下可接受 | OPEN |

### MOD-186 时间线 API

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 8/10 |

无新增问题；权限在 `can_view` 集中判定，越权返回 403。

### MOD-187 待办与决策 API

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 7/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-005 | MINOR | `views.py:TaskListView` | 待办遍历在办实例（Python 层过滤），规模增大时需改 SQL 过滤 | OPEN |

### MOD-188 Web 管理后台流程配置页

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 8/10 | 8/10 | 7/10 | 7/10 |

无新增问题；步骤控件抽为 `StepsEditor.vue`，避免内联模板导致运行时不编译。

### MOD-189 Web 用户端待办与时间线

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 7/10 |

无新增问题；无权限时后端 403，页面只显示错误文案，不渲染备注。

### MOD-190 小程序审批与进度

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 8/10 | 8/10 | 8/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-006 | MINOR | `miniprogram/pages/approvals/detail.vue` | 页面统一显示审批按钮，非当前步骤点击由后端 403 拒绝 | OPEN（后端兜底，避免前端推断身份） |

### MOD-191 三端文案与状态标签

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 10/10 | 9/10 | 8/10 |

无新增问题；四个新映射使用 `*_LABELS` 命名并置于文件末尾，满足既有 labels 键集合测试。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无。

## 缺陷修复

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-001 | `frontend/src/portal/ApprovalTimeline.vue` 模板 | 常量从 `*_TEXT` 重命名为 `*_LABELS` 时只改了 import，模板仍引用旧标识符，渲染时 `textOf(undefined, code)` 抛错 | 模板 4 处引用改为 `STEP_STRATEGY_LABELS / STEP_STATUS_LABELS / APPROVAL_ACTION_LABELS / APPROVAL_STATUS_LABELS`；复跑 `tests/approval_steps_ui.spec.js` 通过 |

缺陷来源：GROUP_D 的 TC-INT-1304 首跑失败（`Cannot read properties of undefined (reading 'ANY')`）。修复后前端全量 581 tests 全绿。

## 现有测试调整

| 文件 | 原断言 | 新断言 | 原因 |
|---|---|---|---|
| `miniprogram/tests/brand_login.spec.js` | 页面数 18 | 20 | 新增 `pages/approvals/index`、`detail` |
| `miniprogram/tests/qa_unit_theme.spec.js` | 页面数 18 | 20 | 同上 |
| `miniprogram/tests/qa_e2e_pages.spec.js` | 页面数 18 | 20 | 同上 |
| `miniprogram/tests/theme.spec.js` | 页面数 18 | 20 | 同上 |
| `miniprogram/tests/qa_e2e_extend.spec.js` | 页面/组件文件数 25 | 27 | 同上 |

仅调整与本次新增页面直接相关的计数断言，未改动任何测试逻辑或阈值。
