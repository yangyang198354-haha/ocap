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
  </input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 审批与同住人申请历史记录实现计划

## 实现概览

实现 4 个新增/修改 MOD，核验 1 个继承 MOD；预计局部修改 6 个既有产品文件。顺序为 MOD-228、MOD-230（后端被依赖方）→ MOD-229、MOD-231（Web 调用方）→ MOD-232（既有行为核验），与 module_design 的无环依赖一致。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 L/M/H | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-228 | `backend/apps/approval/views.py` | 修改 | 无 | M | 增加 view/分页校验、本人动作去重查询、最近动作摘要和 handled 分页响应 | DONE |
| 2 | MOD-230 | `backend/apps/residency/views.py`、`backend/apps/residency/urls.py` | 修改 | 无 | L | 共享审批人序列化摘要；新增固定 APPROVED + 当前产权过滤的只读端点 | DONE |
| 3 | MOD-229 | `frontend/src/portal/Tasks.vue` | 修改 | MOD-228 | M | 待办/已处理切换、历史字段与空态、条件化操作按钮、复用时间线 | DONE |
| 4 | MOD-231 | `frontend/src/shared/api.js`、`frontend/src/portal/units/UnitsReview.vue` | 修改 | MOD-230 | L | 局部新增 approved API 方法和已通过记录分区，处理后同步刷新 | DONE |
| 5 | MOD-232 | `backend/apps/residency/views.py` 的 MineView、`frontend/src/portal/units/UnitsApplicationRecords.vue` | 不修改 | 无 | L | 运行既有相关测试并静态核对申请人范围和通过结果展示 | DONE |

## 需求追溯

| US | AC | 实现位置（文件:函数/组件，含调用方客户端） | 状态 | 说明 |
|---|---|---|---|---|
| US-370 | AC-370-01 | `approval/views.py:TaskListView`；`Tasks.vue:submitDecision/历史列表` | DONE | 待办移除、已处理收录与摘要字段 |
| US-370 | AC-370-02 | `approval/views.py:TaskListView._handled`；`Tasks.vue:历史列表` | DONE | 多步在途状态、当前步骤与只读按钮 |
| US-370 | AC-370-03 | `approval/views.py:TaskListView._handled` | DONE | actor/action 过滤排除未操作及他人动作 |
| US-370 | AC-370-04 | `Tasks.vue:el-empty`；`approval/views.py:TaskListView` | DONE | 已处理空态且待办查询独立 |
| US-371 | AC-371-01 | `approval/views.py:TaskListView`；`Tasks.vue:scope/filters` | DONE | scope 过滤与去重 count |
| US-371 | AC-371-02 | `Tasks.vue:openTimeline`；既有 `ApprovalTimeline.vue`；`approval/services.py:timeline` | DONE | 复用完整步骤、动作和意见详情，无再次审批 |
| US-371 | AC-371-03 | 既有 `approval/views.py:InstanceDetailView`；`approval/services.py:can_view/timeline` | DONE | 不改既有 403 权限 |
| US-371 | AC-371-04 | `approval/views.py:TaskListView`；`Tasks.vue:PagerBar/gotoPage` | DONE | 去重后分页与总数 |
| US-372 | AC-372-01 | `residency/views.py:ResidentApplicationApprovedView`；`UnitsReview.vue:decideResident/已通过记录` | DONE | 处理后待办移除并显示通过记录字段 |
| US-372 | AC-372-02 | `residency/views.py:ResidentApplicationApprovedView`；`UnitsReview.vue:已通过空态` | DONE | 固定 APPROVED，排除其他状态 |
| US-372 | AC-372-03 | `residency/views.py:ResidentApplicationApprovedView` | DONE | 每次按有效 HEAD/OWNER 过滤 |
| US-373 | AC-373-01 | 既有 `residency/views.py:ResidentApplicationMineView`；`UnitsApplicationRecords.vue` | DONE | 保持本人通过结果、时间和备注 |
| US-373 | AC-373-02 | 既有 `residency/views.py:ResidentApplicationMineView` | DONE | 保持 applicant=request.user |

## 迁移

无。不新增或修改迁移文件。

## 架构偏差

无。

## 开放问题

无。
