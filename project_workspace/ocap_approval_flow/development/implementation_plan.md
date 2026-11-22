<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-22T19:33:01+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/architecture/module_design.md</file>
    <file>project_workspace/ocap_approval_flow/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划 — 审批流程多步化与或/与签（ocap_approval_flow）

## 实现概览

按依赖拓扑排序实现 9 个模块：数据模型与迁移（MOD-183）→ 判定引擎（MOD-184）→ API（MOD-185~187）→ 客户端（MOD-188~191）。后端 8 个文件修改 + 1 个迁移新建；Web 5 个文件修改 + 2 个组件新建；小程序 4 个文件修改 + 2 个页面新建。未引入任何新依赖，未 commit/push。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 |
|---|---|---|---|---|---|---|
| 1 | MOD-183 | `backend/apps/approval/models.py` | 修改 | — | M | 新增 ApprovalStep / StepApprover / ApprovalStepState；实例加 current_step_order；动作加 step_state / step_order |
| 2 | MOD-183 | `backend/apps/approval/migrations/0003_approval_steps.py` | 新建 | 1 | M | 建表、加字段、回填老流程与在办实例 |
| 3 | MOD-183 | `backend/apps/approval/apps.py` | 修改 | 1 | L | 注册 StepApprover 的用户引用合并处理器 |
| 4 | MOD-184 | `backend/apps/approval/services.py` | 修改 | 1 | H | 步骤快照、ANY/ALL 判定、串行推进、行锁并发、时间线与可见性 |
| 5 | MOD-185/186/187 | `backend/apps/approval/views.py` | 修改 | 4 | H | 流程步骤 CRUD、待办按当前步骤、决策校验、时间线接口 |
| 6 | MOD-186/187 | `backend/apps/approval/urls.py` | 修改 | 5 | L | 新增实例时间线路由 |
| 7 | MOD-185 | `backend/apps/claims/views.py`、`backend/apps/income/views.py`、`backend/apps/resolutions/views.py` | 修改 | 4 | L | 详情响应增加 approval_instance_id（列表不查，避免 N+1） |
| 8 | MOD-188/191 | `frontend/src/admin/AdminFlows.vue`、`frontend/src/admin/parts/StepsEditor.vue`、`frontend/src/shared/labels.js` | 修改/新建 | 5 | M | 步骤编辑器：增删、排序、命名、选人、或/与 |
| 9 | MOD-189/191 | `frontend/src/portal/Tasks.vue`、`frontend/src/portal/ApprovalTimeline.vue`、`frontend/src/portal/ResolutionDetail.vue`、`frontend/src/shared/api.js` | 修改/新建 | 5 | M | 待办显示当前步骤、备注弹窗、时间线组件与入口 |
| 10 | MOD-190/191 | `miniprogram/pages/approvals/index.vue`、`detail.vue`、`pages.json`、`pages/me/index.vue`、`utils/api.js`、`utils/labels.js` | 新建/修改 | 5 | M | 小程序待办、审批、时间线、入口与路由 |

## 需求追溯

| US | AC | 实现位置（文件:函数/组件，含调用方客户端） | 状态 | 说明 |
|---|---|---|---|---|
| US-311 | AC-316-01 | `backend/apps/approval/views.py:_validate_flow_payload/_save_steps`；`frontend/src/admin/AdminFlows.vue`；`frontend/src/admin/parts/StepsEditor.vue` | DONE | 创建 2 步、名称/策略/审批人落库并在详情展示 |
| US-311 | AC-317-01 | `views.py:_validate_flow_payload`（name 1~60）；`StepsEditor.vue`（maxlength） | DONE | 空名称返回 INVALID_STEPS 422 |
| US-311 | AC-318-01 | `views.py:_validate_flow_payload`（approver_ids 非空） | DONE | 返回“每个步骤至少选择一名审批人” |
| US-311 | AC-318-02 | `views.py:_validate_flow_payload`（CommitteeQuery.is_member） | DONE | 返回 APPROVER_NOT_COMMITTEE_MEMBER 422 |
| US-311 | AC-325-01 | `AdminFlows.vue:moveStep/saveEdit`；`views.py:_save_steps` | DONE | 上移后按新顺序重建步骤 |
| US-312 | AC-326-01 | `services.py:submit`（冻结 flow_snapshot + ApprovalStepState） | DONE | 在办实例不受配置变更影响 |
| US-312 | AC-327-01 | `migrations/0003_approval_steps.py:forwards`；`services.py:_flow_steps` | DONE | 老流程折算 1 步 ANY |
| US-312 | AC-327-02 | `migrations/0003_approval_steps.py:forwards`；`services.py:_ensure_states` | DONE | 在办实例回填步骤状态，缺状态时惰性补建 |
| US-313 | AC-320-01 | `services.py:decide`（ANY 且 approvals 非空 → 通过并推进） | DONE | 后端；`Tasks.vue`/小程序 detail 提交 |
| US-313 | AC-320-02 | `services.py:decide`（ANY 部分拒绝不终局） | DONE | 动作记录但不改状态 |
| US-313 | AC-320-03 | `services.py:decide`（rejects >= approver_ids → 拒绝） | DONE | 整单 REJECTED |
| US-314 | AC-321-01 | `services.py:decide`（ALL 且未全员通过 → 保持 ACTIVE） | DONE | |
| US-314 | AC-321-02 | `services.py:decide`（ALL 全员通过 → 推进） | DONE | |
| US-314 | AC-321-03 | `services.py:decide`（ALL 任一拒绝 → 拒绝） | DONE | |
| US-315 | AC-322-01 | `views.py:TaskListView`；`services.py:pending_subject_ids` | DONE | 待办只含当前步骤 |
| US-315 | AC-323-01 | `services.py:decide`（无下一步 → APPROVED + 回调） | DONE | 复用既有 approved 回调 |
| US-316 | AC-324-01 | `services.py:decide`（step REJECTED → instance REJECTED，后续不激活） | DONE | |
| US-316 | AC-324-02 | `services.py:resubmit`（仅 WITHDRAWN 可重提） | DONE | 既有终局规则保持 |
| US-317 | AC-328-01 | `services.py:timeline`；`frontend/src/portal/ApprovalTimeline.vue`；`miniprogram/pages/approvals/detail.vue` | DONE | 步骤名、到达时间、动作、备注 |
| US-317 | AC-328-02 | `services.py:timeline`（未到达步骤 reached_at=null、actions=[]） | DONE | 前端显示“未开始” |
| US-317 | AC-328-03 | `ApprovalTimeline.vue`（action.comment 展示）；`detail.vue` | DONE | 空备注不显示 |
| US-318 | AC-329-01 | `services.py:can_view`（历史审批人） | DONE | 历史步骤 approver_ids 命中即可见 |
| US-318 | AC-329-02 | `services.py:can_view` + `views.py:InstanceDetailView` | DONE | 返回 FORBIDDEN 403 |
| US-319 | AC-330-01 | `views.py:TaskListView`；`frontend/src/portal/Tasks.vue` | DONE | 非当前步骤审批人列表不可见 |
| US-319 | AC-330-02 | `views.py:InstanceDetailView`；管理后台可复用同一接口 | DONE | 时间线内容一致 |
| US-320 | AC-331-01 | `miniprogram/pages/approvals/detail.vue:decide`；`miniprogram/utils/api.js` | DONE | 提交后刷新时间线 |
| US-320 | AC-331-02 | `miniprogram/pages/approvals/detail.vue`；`index.vue` | DONE | 与 Web 同字段、同权限 |
| US-321 | AC-332-01 | `services.py:decide`（len(comment) > 500 → INVALID_VALUE） | DONE | 拒绝提交并保留输入 |
| US-321 | AC-332-02 | `services.py:decide`（comment 默认空串） | DONE | 空备注可提交 |

## 迁移

- 文件：`backend/apps/approval/migrations/0003_approval_steps.py`
- 内容：新建 3 张表及唯一约束；`approvalinstance.current_step_order`；`approvalaction.step_state/step_order`；回填老流程为 1 步、在办实例步骤状态与历史动作归属。
- 可逆性：schema 可逆；数据回填仅单步 ANY 流程可逆，多步回滚会丢步骤数据，标 `[MANUAL_ROLLBACK_REQUIRED]`（E1 需在部署计划写明备份）。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| 流程详情/列表响应保留扁平 `approvers` 字段 | IFC-402/403 | 兼容既有前端调用与既有测试 | 无；新字段 `steps` 为准 |
| 步骤策略控件使用 `el-radio-group` 而非下拉 | MOD-188（未指定控件） | 避免与既有多选下拉测试冲突、减少误操作 | 无 |
| 步骤数防御上限 50 | AS-01 | 防止无界数组 | 业务语义不变 |
| 列表接口不返回 `approval_instance_id` | IFC-407（详情接口） | 避免列表查询数随行数增长（既有 N+1 测试） | 详情页可用 |

## 开放问题

- `[ASSUMPTION]` 历史动作无 step_state 时统一归属第 1 步，并返回 `legacy=true`。
- `[ASSUMPTION]` 半数同意实例的时间线返回 `steps=[]`，由决议详情展示投票结果。
- 小程序 `npm run build:mp-weixin` 因仓库缺少 `src/manifest.json` 失败（预存在，与本批次无关）；`npm test` 通过。
