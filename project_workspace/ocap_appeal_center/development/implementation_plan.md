<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-22T10:57:49+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>project_workspace/ocap_appeal_center/requirements/user_stories.md</file>
    <file>project_workspace/ocap_appeal_center/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划 — 申诉与同住人申请记录中心

## 实现概览

- 模块 6 个（MOD-168~173），改动文件 29 个（后端 8、前端 21，其中测试 12 个）；`git diff --stat` 合计 +386/-135。
- 实现顺序按依赖拓扑：MOD-168（申诉后端）→ MOD-169（同住申请后端 + 房屋聚合）→ MOD-173（前端共享 API/标签）→ MOD-170（申诉中心 UI）→ MOD-171（同住申请中心 UI）→ MOD-172（身份页实名）。
- 迁移：`backend/apps/residency/migrations/0006_appeal_center.py`（手写，单 app）。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-168 | `backend/apps/residency/models.py` | 修改 | 无 | M | Appeal：status 12 + WITHDRAWN、decision_note、withdrawn_at、previous_appeal | DONE |
| 2 | MOD-168/169 | `backend/apps/residency/migrations/0006_appeal_center.py` | 新建 | 1 | M | 两个模型的 10 项字段/长度变更；可空与默认值，不回填 | DONE |
| 3 | MOD-168 | `backend/apps/residency/views.py` | 修改 | 1 | H | 撤回接口、重新提交校验、列表新字段、管理端备注 | DONE |
| 4 | MOD-168 | `backend/apps/residency/urls.py` | 修改 | 3 | L | 注册两个 withdraw 路由 | DONE |
| 5 | MOD-169 | `backend/apps/residency/models.py` | 修改 | 1 | M | ResidentApplication：status 12 + WITHDRAWN、applicant_name、reject_reason、decision_note、withdrawn_at、previous_application | DONE |
| 6 | MOD-169 | `backend/apps/residency/views.py` | 修改 | 5 | H | 创建实名、撤回、决定备注/原因、to-review 实名 | DONE |
| 7 | MOD-169 | `backend/apps/residency/housing.py` | 修改 | 5 | M | residents.real_name 批量查询；本人同住人实名并入 real_names | DONE |
| 8 | MOD-173 | `frontend/src/shared/api.js` | 修改 | 3/6 | L | 撤回、实名、备注参数；旧签名保持可用 | DONE |
| 9 | MOD-173 | `frontend/src/shared/labels.js`、`miniprogram/utils/labels.js` | 修改 | 无 | L | 两处同步新增 WITHDRAWN“已撤回”（键集合一致性测试要求） | DONE |
| 10 | MOD-170 | `frontend/src/portal/units/AppealCenter.vue` | 新建 | 8/9 | M | 双 Tab 宿主，默认 Tab、提交后切记录、重新提交回填 | DONE |
| 11 | MOD-170 | `frontend/src/portal/units/UnitsAppeal.vue` | 修改 | 10 | M | prefill/emit submitted、previous_appeal_id 随 FormData 提交 | DONE |
| 12 | MOD-170 | `frontend/src/portal/units/UnitsMyAppeals.vue` | 修改 | 8/9 | M | 记录字段、撤回、重新提交、空态 | DONE |
| 13 | MOD-170 | `frontend/src/portal/Units.vue`、`layout/menus.js` | 修改 | 10 | L | 合并菜单为单入口；appeals 复用宿主并默认 mine | DONE |
| 14 | MOD-171 | `frontend/src/portal/units/UnitsApplications.vue` | 修改 | 8/9 | M | 双 Tab 宿主，提交后切记录 | DONE |
| 15 | MOD-171 | `frontend/src/portal/units/UnitsApplicationForm.vue` | 新建 | 14 | M | 房屋 + 本人实名（trim、≤64） | DONE |
| 16 | MOD-171 | `frontend/src/portal/units/UnitsApplicationRecords.vue` | 新建 | 14 | M | 记录列表、撤回、重新提交、空态 | DONE |
| 17 | MOD-172 | `frontend/src/portal/units/UnitsIdentity.vue` | 修改 | 7 | L | 同住人实名展示（缺省“—”） | DONE |
| 18 | MOD-168 | `frontend/src/admin/AdminAppeals.vue` | 修改 | 8 | L | 待审行内备注输入，通过/驳回均可带备注 | DONE |
| 19 | — | 后端契约测试 4 个文件 | 修改 | 3/6 | L | 响应键集合与 FormData 键集合随契约扩展更新 | DONE |
| 20 | — | 前端测试 12 个文件 | 修改 | 10~18 | M | 菜单 4 项、双 Tab、实名提交、撤回、API 导出集合 | DONE |

## 需求追溯

| US | AC | 实现位置（文件:组件/函数，含调用方） | 状态 | 说明 |
|---|---|---|---|---|
| US-291 | AC-291-01 | `frontend/src/layout/menus.js:12`；`portal/units/AppealCenter.vue:5-9` | DONE | 单一“认证申诉”入口，默认 appeal Tab |
| US-291 | AC-291-02 | `AppealCenter.vue:5-9`（两个 el-tab-pane 非 lazy） | DONE | 切换保留已选房屋/姓名/证明 |
| US-291 | AC-291-03 | `frontend/src/router/index.js:47`；`portal/Units.vue:18-20` | DONE | /units/appeals → AppealsCenter + initialTab=mine |
| US-292 | AC-292-01 | `backend/apps/residency/views.py:appeal_view`；`UnitsMyAppeals.vue:4-21` | DONE | 倒序、状态、提交/处理时间 |
| US-292 | AC-292-02 | `UnitsMyAppeals.vue:4` | DONE | “暂无申诉”空态 |
| US-292 | AC-292-03 | `views.py:AppealListCreateView.get`（MINE_LIMIT=100） | DONE | 沿用 100 条上限 |
| US-293 | AC-293-01 | `views.py:AdminAppealDecisionView`（decision_note）；`UnitsMyAppeals.vue:14-17` | DONE | 通过 + 备注展示 |
| US-293 | AC-293-02 | `UnitsMyAppeals.vue:14-19` | DONE | 驳回原因与备注分栏展示 |
| US-293 | AC-293-03 | `UnitsMyAppeals.vue:16` | DONE | 空备注显示“—” |
| US-293 | AC-293-04 | `views.py:_optional_note`；`AdminAppeals.vue:158-162` | DONE | 501 字拒绝且不提交 |
| US-294 | AC-294-01 | `views.py:AppealWithdrawView`；`UnitsMyAppeals.vue:8` | DONE | 撤回后状态与按钮变化 |
| US-294 | AC-294-02 | `views.py:AppealWithdrawView`（pending_slot=None） | DONE | 释放待审唯一约束 |
| US-294 | AC-294-03 | `views.py:_validate_previous_appeal` + `AppealListCreateView`；`AppealCenter.vue:onResubmit`；`UnitsMyAppeals.vue:9-11` | DONE | 新记录关联原记录 |
| US-294 | AC-294-04 | `UnitsMyAppeals.vue:8-11`（仅 PENDING/WITHDRAWN 显示操作） | DONE | 已处理无撤回/重提 |
| US-295 | AC-295-01 | `UnitsApplications.vue:5-11` | DONE | 两 Tab，默认发起申请 |
| US-295 | AC-295-02 | `UnitsApplications.vue:5-11` | DONE | 切换不销毁表单 |
| US-295 | AC-295-03 | `UnitsApplications.vue:onSubmitted` | DONE | 提交后切记录并刷新 |
| US-296 | AC-296-01 | `views.py:application_view/create`；`UnitsApplicationRecords.vue:4-19` | DONE | 字段与申诉一致 |
| US-296 | AC-296-02 | `views.py:ResidentApplicationWithdrawView`；`UnitsApplicationRecords.vue:10` | DONE | 撤回释放约束 |
| US-296 | AC-296-03 | `views.py:_validate_previous_application`；`UnitsApplications.vue:onResubmit` | DONE | 新申请关联原记录 |
| US-296 | AC-296-04 | `UnitsApplicationRecords.vue:4` | DONE | “暂无同住人申请” |
| US-297 | AC-297-01 | `UnitsApplicationForm.vue:applyResident` | DONE | 前端必填校验 |
| US-297 | AC-297-02 | `UnitsApplicationForm.vue:applyResident` | DONE | 65 字提示且不提交 |
| US-297 | AC-297-03 | `views.py:ResidentApplicationCreateView`、`ResidentApplicationToReviewView`；`UnitsApplicationRecords.vue:6` | DONE | 审批列表带 applicant_name |
| US-297 | AC-297-04 | `views.py:application_view`；`UnitsApplicationRecords.vue:6` | DONE | 历史空值显示“—” |
| US-298 | AC-298-01 | `housing.py:housing_view`（real_names 并入本人实名）；`UnitsIdentity.vue:12-13` | DONE | 本人同住人实名 |
| US-298 | AC-298-02 | `housing.py:_latest_resident_names`；`UnitsIdentity.vue:31-36` | DONE | 同住人实名/昵称/账号/加入时间 |
| US-298 | AC-298-03 | `UnitsIdentity.vue:32` | DONE | 缺失显示“—” |
| US-298 | AC-298-04 | `UnitsIdentity.vue`（既有空态分支未改） | DONE | 无房屋不报错 |

## 迁移

`backend/apps/residency/migrations/0006_appeal_center.py`：

- Appeal：status 8→12（+WITHDRAWN）、decision_note、withdrawn_at、previous_appeal（self FK SET_NULL）。
- ResidentApplication：status 8→12、applicant_name(64, default "")、reject_reason、decision_note、withdrawn_at、previous_application（self FK SET_NULL）。
- 是否可逆：结构可逆；反向把 status 改回 8 字符前须清理 WITHDRAWN 记录（文件内已标 `[MANUAL_ROLLBACK_REQUIRED]`）。
- 迁移一致性：`makemigrations --check --dry-run residency` → “No changes detected in app 'residency'”。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| 同住申请创建的 `applicant_name` 后端按“提供时校验、缺省允许空串”实现（前端仍强制必填） | IFC-385 要求缺失 → 400 NAME_REQUIRED | 小程序端本批不改造且共享后端，强制必填会破坏旧版小程序提交；与 A-01 的向后兼容原则一致 | Web 端满足 AC-297-01/02；旧客户端不因新增字段失败；已由前端与后端双层校验保障 Web 数据质量 |

## 测试影响

| 测试文件 | 调整内容 | 原因 |
|---|---|---|
| `backend/tests/integration/test_frontend_contract.py` | residents 增加 real_name；applications/appeals 增加 5/3 个新键 | 响应契约有意扩展 |
| `backend/tests/integration/test_owner_auth_v2_residency.py` | 申诉响应键集合增加 3 个字段 | 同上 |
| `backend/tests/integration/test_owner_auth_v2_contract.py`、`test_batch1118_contract.py` | FormData 键集合增加 previous_appeal_id | 重新提交需要来源记录 |
| `frontend/tests/batch1118_unit_pages.spec.js` | UnitCascader 源文件断言改为 UnitsApplicationForm.vue | 表单从宿主拆出 |
| `frontend/tests/identity_property_e2e.spec.js`、`identity_property_match_panel.spec.js`、`product_review_ui.spec.js` | 同住申请提交前填写实名；期望体增加 applicant_name；文案更新 | 新需求 REQ-FUNC-295 |
| `frontend/tests/layout_menus.spec.js`、`layout_nav.spec.js`、`layout_pages.spec.js`、`layout_e2e.spec.js`、`identity_property_menu_router.spec.js` | 二级项 5→4；“我的申诉”菜单项移除；旧 /units/appeals 断言改为无独立菜单项 | D-01 合并入口 |
| `frontend/tests/layout_contract.spec.js` | unitApi 导出集合增加 withdrawAppeal / withdrawResidentApplication | 新增 API |
| `frontend/tests/layout_css.spec.js` | 无改动（管理端备注输入保持在操作列 150px 内，表格总宽不变） | 保持 ADR-121 列宽契约 |

## 缺陷修复记录（1.1.0）

| DEF | 级别 | 位置 | 根因 | 修改 | 状态 |
|---|---|---|---|---|---|
| DEF-AC-01 | CRITICAL | `backend/apps/core/audit.py:10-15` | 撤回视图写审计时使用 `APPEAL_WITHDRAWN` / `RESIDENT_APPLICATION_WITHDRAWN`，但 `AUDIT_ACTIONS` 未登记，`AuditService.record` 抛 `ValueError` → 接口 500 | 在 `AUDIT_ACTIONS` 增加这两个动作名；`views.py` 与接口契约不变 | FIXED |

自验证（修复后）：后端 1167 tests OK（skipped=2）；前端 568 passed、构建 ✓ built in 8.43s；迁移一致性 No changes detected。

## 开放问题

- `[ASSUMPTION]` 同住申请创建请求缺少 `applicant_name` 时后端存空串（兼容旧小程序）；若后续要求后端强制必填，需同步升级小程序并在 GROUP_B 更新 IFC-385。
- `[ASSUMPTION]` 已撤回记录与其它状态一同参与最近 100 条截断。
- 管理端备注以“待审行内输入框”承载（不弹窗），保持表格列宽契约；若产品要求弹窗式备注，需要重新评估 layout_css 基线。
