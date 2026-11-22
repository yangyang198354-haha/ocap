<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-22T18:50:10+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_approval_flow/requirements/user_stories.md</file>
    <file>backend/apps/approval/models.py</file>
    <file>backend/apps/approval/services.py</file>
    <file>backend/apps/approval/views.py</file>
    <file>backend/apps/approval/urls.py</file>
  </input_files>
  <phase>PHASE_03,PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计 — 审批流程多步化与或/与签（ocap_approval_flow）

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-183 | 审批步骤数据模型与迁移 | `backend/apps/approval/models.py`（修改）；`backend/apps/approval/migrations/0003_approval_steps.py`（新建） | 步骤、步骤审批人、实例步骤状态、动作步骤归属、实例当前步骤 | REQ-FUNC-316~319、326~328；US-311、US-312、US-317 | — |
| MOD-184 | 步骤判定引擎 | `backend/apps/approval/services.py`（修改） | 提交时冻结步骤快照、按 ANY/ALL 判定、串行推进、并发一致性 | REQ-FUNC-320~324、REQ-NFUNC-064、REQ-NFUNC-065；US-313~316 | MOD-183 |
| MOD-185 | 管理后台流程配置 API | `backend/apps/approval/views.py`、`backend/apps/approval/urls.py`（修改） | 流程列表/详情/创建/更新/停用，嵌套 steps 校验 | REQ-FUNC-316~319、325~327、C-369；US-311、US-312 | MOD-183、MOD-184 |
| MOD-186 | 审批时间线 API | `backend/apps/approval/views.py`、`backend/apps/approval/urls.py`（修改） | 新增只读实例时间线，按权限返回步骤与动作 | REQ-FUNC-328~329、332；US-317、US-318 | MOD-183、MOD-184 |
| MOD-187 | 待办与决策 API 步骤化 | `backend/apps/approval/views.py`（修改） | 待办只返回当前步骤；决策按步骤校验 | REQ-FUNC-322、329、332、C-366；US-313~316、US-321 | MOD-184 |
| MOD-188 | Web 管理后台流程配置页 | `frontend/src/admin/AdminFlows.vue`（修改）；`frontend/src/shared/api.js`、`frontend/src/shared/labels.js`（修改） | 步骤编辑 UI：增删、排序、命名、选人、ANY/ALL | REQ-FUNC-316~319、325；US-311 | MOD-185 |
| MOD-189 | Web 用户端待办与审批时间线 | `frontend/src/portal/Tasks.vue`（修改）；`frontend/src/portal/ApprovalTimeline.vue`（新建）；`frontend/src/shared/api.js`（修改） | 待办展示当前步骤、提交备注、查看时间线与权限提示 | REQ-FUNC-322、328~330、332；US-313~321 | MOD-186、MOD-187 |
| MOD-190 | 小程序审批与进度 | `miniprogram/pages/approvals/index.vue`、`miniprogram/pages/approvals/detail.vue`（新建）；`miniprogram/pages.json`、`miniprogram/utils/api.js`、`miniprogram/utils/labels.js`（修改）；`miniprogram/pages/me/index.vue`（修改，加入口） | 小程序待办、审批、时间线 | REQ-FUNC-331、328~329、332；US-320 | MOD-186、MOD-187 |
| MOD-191 | 三端文案与状态标签 | `frontend/src/shared/labels.js`、`miniprogram/utils/labels.js`（修改） | 步骤策略、步骤状态、动作类型的中文文案统一 | C-368、REQ-FUNC-328；US-317 | — |

## 模块详情

### MOD-183 审批步骤数据模型与迁移

新增模型（字段清单，非代码）：

**`ApprovalStep`（新表）**
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | BigAutoField | PK | |
| `flow` | FK(`ApprovalFlow`) | `on_delete=CASCADE`, `related_name="steps"` | |
| `order` | PositiveSmallIntegerField | 1..50 | 步骤顺序，从 1 开始 |
| `name` | CharField(60) | 非空 | 步骤名称（REQ-FUNC-317） |
| `strategy` | CharField(4) | `ANY` / `ALL`，默认 `ANY` | 或签/会签（REQ-FUNC-319） |
| `created_at` | DateTimeField | `auto_now_add` | |

约束：`UniqueConstraint(fields=["flow","order"], name="uniq_flow_step_order")`。

**`StepApprover`（新表）**
| 字段 | 类型 | 约束 |
|---|---|---|
| `id` | BigAutoField | PK |
| `step` | FK(`ApprovalStep`) | `on_delete=CASCADE`, `related_name="approvers"` |
| `user` | FK(`accounts.User`) | `on_delete=CASCADE` |

约束：`UniqueConstraint(fields=["step","user"], name="uniq_step_approver")`。

**`ApprovalStepState`（新表，实例侧）**
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | BigAutoField | PK | |
| `instance` | FK(`ApprovalInstance`) | `on_delete=CASCADE`, `related_name="step_states"` | |
| `step_order` | PositiveSmallIntegerField | | 快照顺序 |
| `name` | CharField(60) | | 快照步骤名 |
| `strategy` | CharField(4) | `ANY` / `ALL` | 快照策略 |
| `approver_ids` | JSONField | default `list` | 快照审批人 ID 列表（历史人物变更不影响在办） |
| `status` | CharField(10) | `PENDING` / `ACTIVE` / `APPROVED` / `REJECTED`，默认 `PENDING` | |
| `reached_at` | DateTimeField | null | 该步到达时间（REQ-FUNC-328） |
| `decided_at` | DateTimeField | null | 该步判定时间 |

约束：`UniqueConstraint(fields=["instance","step_order"], name="uniq_instance_step")`。

**`ApprovalInstance`（新增字段）**
| 字段 | 类型 | 说明 |
|---|---|---|
| `current_step_order` | PositiveSmallIntegerField，null | 当前步骤顺序；null 表示已结束 |

**`ApprovalAction`（新增字段）**
| 字段 | 类型 | 说明 |
|---|---|---|
| `step_state` | FK(`ApprovalStepState`)，null，`on_delete=SET_NULL` | 动作归属步骤 |
| `step_order` | PositiveSmallIntegerField，null | 冗余快照，便于历史动作兜底展示 |

`FlowApprover` 保留不删（回滚兜底），新代码不再写入；在模型 docstring 标注“deprecated，由 StepApprover 取代”。

### MOD-184 步骤判定引擎

接口签名（`backend/apps/approval/services.py`）：

```python
class ApprovalEngine:
    @staticmethod
    def submit(*, scope: str, subject_type: str, subject_id: int, flow_id: int,
               submitter, revision: int = 1) -> ApprovalInstance: ...

    @staticmethod
    def decide(instance_id: int, actor, action: str, comment: str = "") -> ApprovalInstance: ...

    @staticmethod
    def timeline(instance_id: int, viewer) -> dict: ...  # 供 MOD-186 调用

    @staticmethod
    def current_step(instance: ApprovalInstance) -> ApprovalStepState | None: ...
```

提交（`submit`）：
1. 读取 `ApprovalStep` 与 `StepApprover`，按 `order` 升序冻结为 `flow_snapshot = {"schema_version": 2, "name": ..., "mode": ..., "steps": [...]}`。
2. 为每一步创建 `ApprovalStepState(status="PENDING")`；第 1 步置 `ACTIVE` 且 `reached_at=now`；实例 `current_step_order=1`。
3. 无步骤的旧 `DESIGNATED` 流程：合成 1 步（`name=flow.name`、`strategy=ANY`、审批人取 `FlowApprover`），保证 REQ-FUNC-327。
4. `HALF_MAJORITY` 流程不建步骤状态，保持现有投票链路。

决策（`decide`），在 `transaction.atomic()` 内：

1. `select_for_update()` 锁实例与当前 `ApprovalStepState`。
2. 校验：实例 `PENDING`；actor 属于当前步骤 `approver_ids`；actor 仍是现任业委会成员（C-366）；`EXPENSE`/`INCOME` 禁止自审（C-366）。
3. 追加 `ApprovalAction(step_state=当前步, step_order=当前步.order, ...)`。
4. 判定当前步：
   - `strategy=ANY`：任一 `APPROVE` → 该步 `APPROVED`；`REJECT` 仅记录，直到该步所有审批人都已拒绝 → 该步 `REJECTED`（REQ-FUNC-320）。
   - `strategy=ALL`：全部审批人 `APPROVE` → 该步 `APPROVED`；任一 `REJECT` → 该步 `REJECTED`（REQ-FUNC-321）。
5. 该步通过 → 下一步 `ACTIVE` + `reached_at=now` + 实例 `current_step_order` 前移；无下一步 → 实例 `APPROVED`、`decided_at/decided_by`、触发 `approved` 回调（REQ-FUNC-323）。
6. 该步未通过 → 实例 `REJECTED`、触发 `rejected` 回调（REQ-FUNC-324）；后续步骤保持 `PENDING` 不得激活。
7. 重复提交同一决策：若 actor 已在当前步有 `APPROVE` 动作，返回 `ALREADY_DECIDED`（409），保证幂等。

### MOD-185 管理后台流程配置 API

**IFC-402 `GET /admin/approval/flows`**

- 权限：`IsAdmin`（沿用 `backend/apps/core/permissions.py:19-25`）。
- 查询：`scope?`（`RESOLUTION|EXPENSE|INCOME`）、`page?`、`page_size?`。
- 响应：分页 `{count:int, page:int, page_size:int, results: FlowSummary[]}`。
- `FlowSummary`：`{id:int, scope:str, name:str, mode:"DESIGNATED"|"HALF_MAJORITY", is_active:bool, step_count:int, steps: StepSummary[]}`。
- `StepSummary`：`{order:int, name:str, strategy:"ANY"|"ALL", approver_count:int}`。

**IFC-402 `POST /admin/approval/flows`**

- 请求体：

```ts
type CreateFlowPayload = {
  scope: "RESOLUTION" | "EXPENSE" | "INCOME";
  name: string;                 // 1~60
  mode?: "DESIGNATED" | "HALF_MAJORITY"; // 默认 DESIGNATED
  steps?: Array<{
    name: string;               // 1~60，必填
    strategy: "ANY" | "ALL";    // 默认 ANY
    approver_ids: number[];     // 至少 1 个，去重
  }>;                           // DESIGNATED 时 1~50 步
};
```

- 校验与错误：`INVALID_VALUE`（400）scope/mode/名称非法；`INVALID_STEPS`（422）步骤为空、步骤名空、审批人为空、重复步骤名不阻断但返回 `warnings: string[]`；`APPROVER_NOT_COMMITTEE_MEMBER`（422）审批人非现任业委会成员；`HALF_MAJORITY` 仅允许 `RESOLUTION` 且不得传 steps。
- 响应：`201` + `FlowDetail`。

**IFC-403 `GET/PUT/DELETE /admin/approval/flows/{flow_id}`**

- `GET`：`FlowDetail`：`FlowSummary` + `steps[].approvers: Array<{id:int, nickname:string, identity_label:string}>`。
- `PUT`：请求体同创建，字段均可选（部分更新）；`is_active:boolean` 可单独更新（沿用前端 `toggle` 调用）。
- `DELETE`：`204`，行为保持现有“停用”语义（`backend/apps/approval/views.py:112-125`）。
- 所有写入记 `AuditService` `APPROVAL_FLOW_CHANGED`，`detail` 增加 `steps_count:int`。

### MOD-186 审批时间线 API

**IFC-407 `GET /approval/instances/{instance_id}`**

- 权限：成员身份 + 下列任一（REQ-FUNC-329）：实例发起人、当前步骤审批人、任一历史步骤审批人、管理员。越权返回 `FORBIDDEN`（403）。
- 响应：

```ts
type ApprovalTimeline = {
  id: number;
  scope: "RESOLUTION" | "EXPENSE" | "INCOME";
  subject_type: string;
  subject_id: number;
  subject_title: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "WITHDRAWN";
  current_step_order: number | null;
  submitted_at: string;   // ISO8601
  decided_at: string | null;
  steps: Array<{
    order: number;
    name: string;
    strategy: "ANY" | "ALL";
    status: "PENDING" | "ACTIVE" | "APPROVED" | "REJECTED";
    reached_at: string | null;
    decided_at: string | null;
    approvers: Array<{id: number; nickname: string; identity_label: string}>;
    actions: Array<{
      actor_id: number;
      actor_label: string;
      action: "SUBMIT" | "APPROVE" | "REJECT" | "WITHDRAW";
      comment: string;
      acted_at: string;
      legacy?: boolean;      // 历史动作无 step_state 时为 true
    }>;
  }>;
};
```

- 未到达步骤：`status="PENDING"`、`reached_at=null`、`actions=[]`（REQ-FUNC-328）。
- `HALF_MAJORITY` 实例：返回 `steps: []` 并在 `status` 上沿用现有投票状态；不改造投票链路（OQ-B-03）。

### MOD-187 待办与决策 API 步骤化

**IFC-405 `GET /approval/tasks`**

- 权限：`IsCommitteeMember`（沿用 `backend/apps/core/permissions.py:46-54`）。
- 过滤：实例 `PENDING` 且 actor 属于**当前步骤** `approver_ids`（REQ-FUNC-322）。
- 响应分页 `results[]` 每项新增：`step_order:int`、`step_name:string`、`step_strategy:"ANY"|"ALL"`、`step_reached_at:string|null`；保留 `instance_id/scope/subject_type/subject_id/subject_title/submitter_label/submitted_at`。

**IFC-406 `POST /approval/instances/{instance_id}/decision`**

- 请求体：`{action:"APPROVE"|"REJECT", comment?:string}`；`comment` 最长 500，超出返回 `INVALID_VALUE`（400），不落库（REQ-FUNC-332）。
- 校验：非当前步骤审批人 → `NOT_CURRENT_STEP`（409）；重复决策 → `ALREADY_DECIDED`（409）；非委员会成员 → `APPROVER_NO_LONGER_ELIGIBLE`（403）；自审财务单 → `SELF_APPROVAL_FORBIDDEN`（403）。
- 响应：`ApprovalTimeline`（直接返回最新时间线，省一次请求）。

### MOD-188 Web 管理后台流程配置页

- `AdminFlows.vue` 创建/详情弹窗改为步骤编辑：步骤卡片列表，支持新增、删除、上移/下移；每步输入名称、选择策略（或签/会签）、用现有 `UserPicker` 选审批人。
- `mode=HALF_MAJORITY` 时隐藏步骤区并提示“由全体业委会成员投票”。
- 校验在提交前本地提示，最终以后端返回的 `INVALID_STEPS`/`APPROVER_NOT_COMMITTEE_MEMBER` 为准。
- `shared/api.js` 的 `admin.createFlow/updateFlow` 透传 `steps`；`shared/labels.js` 增加 `STEP_STRATEGY_TEXT`、`STEP_STATUS_TEXT`、`ACTION_TEXT`。

### MOD-189 Web 用户端待办与时间线

- `Tasks.vue`：每条待办显示当前步骤名与策略；点击“同意/拒绝”弹出备注输入（可选，≤500 字），调用 `approvalApi.decide(instanceId, action, comment)`。
- 新增 `ApprovalTimeline.vue`：按步骤渲染时间线（步骤名、状态、到达时间、审批人、动作与备注）；用于决议/报销/收入详情页的审批进度区，也用于独立审批详情。
- `shared/api.js` 增加 `approvalApi.instance(instanceId)`。
- 无权限时后端返回 403，页面显示“无权查看审批过程”，不渲染任何备注。

### MOD-190 小程序审批与进度

- 新增 `pages/approvals/index.vue`（待办列表）与 `pages/approvals/detail.vue`（时间线 + 审批操作），在 `pages.json` 注册。
- `utils/api.js` 增加 `instance(id)`，`tasks`/`decide` 透传 `comment`。
- `pages/me/index.vue` 增加“待我审批”入口，仅业委会成员可见（与 Web 菜单一致）。
- 展示字段与 Web 完全相同，文案来自 `utils/labels.js`（C-368）。

### MOD-191 三端文案与状态标签

- 统一枚举文案：策略 `ANY=或签（任一通过）`、`ALL=会签（全部同意）`；步骤状态 `PENDING=未开始`、`ACTIVE=进行中`、`APPROVED=已通过`、`REJECTED=已拒绝`；动作 `APPROVE=通过`、`REJECT=拒绝` 等。
- Web 与小程序各维护一份同值映射，测试用同一组断言值核对（C-368）。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-316 | US-311 | MOD-183、MOD-185、MOD-188 |
| REQ-FUNC-317 | US-311 | MOD-183、MOD-185、MOD-188 |
| REQ-FUNC-318 | US-311 | MOD-183、MOD-185、MOD-188 |
| REQ-FUNC-319 | US-311、US-313、US-314 | MOD-183、MOD-185、MOD-188 |
| REQ-FUNC-320 | US-313 | MOD-184、MOD-187 |
| REQ-FUNC-321 | US-314 | MOD-184、MOD-187 |
| REQ-FUNC-322 | US-313~315 | MOD-184、MOD-187、MOD-189、MOD-190 |
| REQ-FUNC-323 | US-315 | MOD-184 |
| REQ-FUNC-324 | US-316 | MOD-184 |
| REQ-FUNC-325 | US-311 | MOD-185、MOD-188 |
| REQ-FUNC-326 | US-312 | MOD-183、MOD-184 |
| REQ-FUNC-327 | US-312 | MOD-183、MOD-184 |
| REQ-FUNC-328 | US-317 | MOD-183、MOD-184、MOD-186、MOD-189、MOD-190、MOD-191 |
| REQ-FUNC-329 | US-318 | MOD-186、MOD-189、MOD-190 |
| REQ-FUNC-330 | US-319 | MOD-189 |
| REQ-FUNC-331 | US-320 | MOD-190 |
| REQ-FUNC-332 | US-317、US-321 | MOD-183、MOD-187、MOD-189、MOD-190 |
| REQ-NFUNC-064 | US-313~316 | MOD-184 |
| REQ-NFUNC-065 | US-317 | MOD-183、MOD-184、MOD-186 |

## 依赖关系

```
MOD-183（模型/迁移）
   ↑
MOD-184（判定引擎） → MOD-185（后台配置 API）
   ↑                    ↑
MOD-186（时间线 API）  MOD-188（后台页面）
MOD-187（待办/决策 API）→ MOD-189（Web 用户端）→ MOD-191（文案）
                        → MOD-190（小程序）→ MOD-191（文案）
```

检查结果：无循环依赖；客户端 MOD 只依赖 API MOD，API MOD 只依赖引擎与模型。

## 数据迁移

迁移文件：`backend/apps/approval/migrations/0003_approval_steps.py`（手写 scoped 迁移，遵循画像 P6，不提交 `makemigrations` 全量产物）。

1. **建表**：`ApprovalStep`、`StepApprover`、`ApprovalStepState`，含上述唯一约束与索引（`instance`、`flow`、`step`）。
2. **加字段**：`ApprovalInstance.current_step_order`（null）；`ApprovalAction.step_state`（null, SET_NULL）、`ApprovalAction.step_order`（null）。
3. **数据回填**：
   - 对每个 `mode=DESIGNATED` 的 `ApprovalFlow`：创建 1 条 `ApprovalStep(order=1, name=flow.name, strategy="ANY")`，并把 `FlowApprover` 复制为 `StepApprover`。
   - 对每个 `status=PENDING` 的 `ApprovalInstance`：按 `flow_snapshot` 生成 `ApprovalStepState`（第 1 步 `ACTIVE`，其余 `PENDING`），`current_step_order=1`；历史 `ApprovalAction` 的 `step_order=1`、`step_state` 指向第 1 步。
   - `HALF_MAJORITY` 实例不建步骤状态。
4. **可逆性**：schema 可逆；数据回填仅对“单步 ANY”流程可逆（反向把第 1 步审批人写回 `FlowApprover`）。多步流程回滚会丢失步骤数据，标记 `[MANUAL_ROLLBACK_REQUIRED]`，E1 部署计划须写明备份要求。
5. **风险**：回填在单事务内按 flow 分批（每批 200 个流程），避免长事务锁表；迁移前须备份 `approval_approvalflow`、`approval_flowapprover`、`approval_approvalinstance`、`approval_approvalaction` 四张表。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 操作 |
|---|---|---|
| `ocap-backend`（gunicorn，systemd） | 新迁移 + 引擎/接口代码 | 迁移后重启服务 |
| MySQL `ocap` 库 | 3 张新表、2 张表加字段、数据回填 | 执行 `python manage.py migrate approval`（部署时由 E2 执行） |
| Web 前端静态产物 | `AdminFlows.vue`、`Tasks.vue`、`ApprovalTimeline.vue`、`api.js`、`labels.js` | `npm run build`，产物替换到 `/home/yangyang/ocap/web/ocap` |
| 微信小程序 | 新增审批页面与 API 方法 | 重新构建，微信开发者工具上传体验版 |
| 定时任务 / 后台作业 | 无 | 无 |

## 领域与外部依赖出处

画像 P11 声明为“无专用硬件、无领域算法”，闭源 API（微信、短信、邮件）本次均不涉及。审批人资格与回调机制来自本仓库现有代码：

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| MOD-184 | 审批人须为现任业委会成员；财务类禁止自审 | `[CODE: backend/apps/approval/services.py:36-44,98-103]` |
| MOD-184 | approved/rejected/withdrawn 回调注册机制 | `[CODE: backend/apps/approval/services.py:13-22]`；`[CODE: backend/apps/resolutions/apps.py:16-17]`；`[CODE: backend/apps/income/apps.py:16-17]` |
| MOD-185 | 管理员权限类 `IsAdmin` | `[CODE: backend/apps/core/permissions.py:19-25]` |
| MOD-187 | 委员会成员权限类 `IsCommitteeMember` | `[CODE: backend/apps/core/permissions.py:46-54]` |
| MOD-183 | 现有实例快照字段 `flow_snapshot` | `[CODE: backend/apps/approval/models.py:32]` |
