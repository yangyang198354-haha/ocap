<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-27T09:01:31.6049532+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 审批与同住人申请历史记录架构设计

## 架构概览

本批为现有 Django/DRF 后端与 Vue 3 Web 用户端的只读增量，不改变审批状态机、同住人处理逻辑或数据模型：

- 通用审批已处理记录以 `ApprovalAction` 中当前用户实际提交的 `APPROVE`/`REJECT` 为收录依据；实例、步骤和动作已持久化，见 `backend/apps/approval/models.py:49-64,67-102` 与 `backend/apps/approval/services.py:183-188`。
- 通用审批继续复用 `GET /approval/tasks` 的业务类型筛选、分页结构和 `ApprovalTimeline` 详情入口，见 `backend/apps/approval/views.py:220-253`、`frontend/src/portal/Tasks.vue:44-46`。
- 同住人已通过记录按请求时的有效 `HEAD`/`OWNER` 关系过滤，复用 `application_view` 与申请人摘要结构，见 `backend/apps/residency/views.py:462-469,505-518`。
- 申请人现有“我的申请”保持 `applicant=request.user` 的查询范围，见 `backend/apps/residency/views.py:496-502`。
- 本批无新增 REQ-NFUNC；权限隔离、只读性和既有规则不变对应 C-402～C-405。

## 部署视图

| 组件 | 运行单元 | 画像 P7 环境 | 本批影响 |
|---|---|---|---|
| Django/DRF 后端 | gunicorn `127.0.0.1:9000`，systemd `ocap-backend` | 测试（内网）及共用该服务的测试（外网） | 发布时需重启后端；不执行数据库迁移 |
| Vue 3 Web 静态产物 | 现有 Vite 构建，经 nginx `/ocap/` 提供 | 测试（内网）nginx `8090`；测试（外网）复用现有 frp/nginx 通道 | 需重新构建并发布静态产物 |
| MySQL / 测试 SQLite | 沿用现有数据库 | 测试环境独立 MySQL；本地/CI 使用 SQLite 内存库 | 无表、字段或索引变化 |
| 微信小程序 | 不在本批范围 | — | 不构建、不发布 |

仅形成部署设计；是否部署仍需用户另行授权。

## ADR

### ADR-206：以本人实际审批动作界定通用审批已处理记录

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-385、REQ-FUNC-386 与 C-402 要求“处理过”可追溯，且不能仅凭被指定为审批人或整单终局就收录。
- Options: 被排除方案 A：按步骤审批人名单查询，会把尚未操作的人纳入，违反 C-402；被排除方案 B：按整单处理人或终局状态查询，会漏掉多步审批中已完成前序步骤的记录，也会误收他人处理的记录。约束来源为用户原文、C-402 及 `ApprovalAction` 留痕 `backend/apps/approval/services.py:183-188`。
- Decision: 以 `ApprovalAction.actor_id=当前用户` 且 `action ∈ {APPROVE, REJECT}` 查询关联实例；同一实例去重，展示本人最近一次通过/拒绝动作及其时间、意见和步骤。
- Consequences: 正向：单步、多步、或签、会签及撤回前已处理实例使用同一口径；负向：同一实例存在多次本人动作时只把最近一次作为列表摘要，完整动作仍须从既有时间线查看。

### ADR-207：通用审批历史复用待办列表接口并增加视图参数

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-385、REQ-FUNC-386 要求已处理视图沿用业务类型筛选与分页；现有 `GET /approval/tasks` 已有相同的外层结构和 Web 分页状态。
- Options:
  - A：扩展 `GET /approval/tasks?view=todo|handled`。优点：复用现有路由、筛选、分页与 `approvalApi.tasks`；`view` 缺省为 `todo`，既有客户端响应不变。缺点：一个视图函数包含两种查询分支，需要清晰隔离序列化字段。
  - B：新增 `GET /approval/handled`。优点：路由语义独立。缺点：重复 scope、分页和人员摘要装配，前后端需维护第二套列表入口。
- Decision: 选择 A；仅新增可选 `view` 参数与 handled 分支，待办默认分支及审批动作接口保持不变。
- Consequences: 正向：改动面和契约测试范围较小；负向：必须验证缺省参数与 `view=todo` 完全保持原待办行为，避免历史功能回归待办。

### ADR-208：同住人已通过记录使用独立只读列表端点

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-388 与 C-405 要求产权业主仅查看当前拥有专有部分的通过记录，且不把待审、拒绝、撤回、关闭混入。
- Options:
  - A：扩展 `/resident-applications/to-review` 的状态参数。优点：可复用现有视图。缺点：`to-review` 的待审语义与已通过历史冲突，状态参数还可能被误用为查询其他审批人历史。
  - B：新增固定语义的 `GET /resident-applications/approved`，服务端固定 `status=APPROVED`。优点：路由和权限意图明确，不暴露任意状态筛选。缺点：增加一条路由和一个轻量视图类。
- Decision: 选择 B；两个视图共享现有序列化辅助逻辑和相同的实时产权过滤，不新增任意 `status` 查询参数。
- Consequences: 正向：从契约上保证只返回通过记录；负向：需新增前后端路由契约测试，并避免复制导致申请人摘要字段漂移。

### ADR-209：历史记录只读并复用现有审批过程详情

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-387、REQ-FUNC-389、C-403、C-404 要求复查过程但不改变审批规则，也不能收窄既有时间线可见范围。
- Options: 被排除方案 A：为历史列表新增另一套详情接口，会形成第二份权限规则；被排除方案 B：在历史记录中复用待办操作按钮，会提供无效的再次审批入口。约束来源为 C-403/C-404、现有 `ApprovalEngine.can_view` 与 `timeline`（`backend/apps/approval/services.py:279-305,297-352`）。
- Decision: 已处理列表只新增 `ApprovalTimeline` 打开入口，继续调用既有 `GET /approval/instances/{id}`；不修改 `can_view`、decision 接口或同住人 decision 逻辑。历史视图不渲染通过/拒绝按钮。
- Consequences: 正向：权限与详情字段只有一份权威实现；负向：列表权限与详情权限仍需分别测试，不能把“出现在列表”当作唯一的详情授权依据。

## 开放问题 / ASSUMPTION

无。Q-AH-01～03 已由用户按当前范围确认；本批无 `[ASSUMPTION]`。
