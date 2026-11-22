<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-22T18:50:10+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_approval_flow/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_03,PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计 — 审批流程多步化与或/与签（ocap_approval_flow）

## 架构概览

本次改动位于现有 Django/DRF 单体后端的 `apps/approval` 应用与三个客户端（Web 管理后台、Web 用户端、微信小程序）。不新增服务、不改变部署拓扑，继续沿用“后端单体 + 前端静态构建 + 小程序构建”的形态（画像 P1/P7）。

改动核心是把当前“流程 → 审批人平铺、首个决策即终局”的引擎，升级为“流程 → 有序步骤 → 步骤审批人 + 步骤策略”的两级结构，并在实例侧增加**步骤状态快照**，使：

- 步骤串行推进、每步按 ANY（或签）/ ALL（会签）独立判定（REQ-FUNC-316~322）；
- 任一步未通过即整单拒绝，最后一步通过即整单通过并触发现有业务回调（REQ-FUNC-323~324）；
- 审批动作可归属到步骤，形成可查询的审批时间线（REQ-FUNC-328~332）；
- 已存在的流程与在办实例不受升级影响（REQ-FUNC-326~327）。

关键质量属性：

| 质量属性 | 目标 | 来源 |
|---|---|---|
| 正确性 | 同一步骤并发审批最终只产生一个判定，不重复推进 | REQ-NFUNC-064 |
| 可追溯 | 动作只追加，保留操作者/动作/步骤/时间/备注 | REQ-NFUNC-065、REQ-FUNC-328 |
| 兼容性 | 既有流程折算 1 步；在办实例按快照执行 | REQ-FUNC-326~327、C-367 |
| 安全性 | 配置仅管理员；时间线仅授权人可见 | C-369、REQ-FUNC-329 |
| 一致性 | Web 与小程序展示同一状态 | C-368 |

## 部署视图

| 组件 | 运行单元 | 环境 | 本次变化 |
|---|---|---|---|
| Django 后端 | gunicorn `127.0.0.1:9000`，systemd `ocap-backend` | 测试（树莓派 192.168.31.51） | 新增迁移、引擎与接口改动；需重启 |
| Web 前端 | 静态产物，经 nginx `8090`/`/ocap/` 提供 | 同上 | `AdminFlows.vue`、`Tasks.vue` 等改动；需重新构建 |
| 微信小程序 | 小程序构建产物 | 微信开发者工具/体验版 | 待办、审批、进度页面改动；需重新构建发布 |
| MySQL | `192.168.31.98:3306` 库 `ocap` | 同上 | 新增表与字段（scoped 迁移） |

不引入容器、消息队列、缓存或新中间件（画像 P8）。

## ADR

### ADR-171: 步骤用独立实体建模，而不是塞进流程快照 JSON

- Status: Proposed
- Type: decision
- Context: 需要支持有序步骤、步骤名、每步审批人与每步 ANY/ALL 策略（REQ-FUNC-316~319），并能在配置页查询、校验、展示（REQ-FUNC-325）。
- Options:
  - A. 新增 `ApprovalStep` + `StepApprover` 两张表：结构化、可查询、可用唯一约束保证顺序，配置与校验直观；代价是新增表与迁移。
  - B. 只在 `ApprovalFlow` 上加一个 `steps` JSONField：改动最小；但无法用数据库约束保证“步骤顺序唯一/每步至少一人”，配置页与校验必须在应用层反复解析 JSON，时间线也难关联。
- Decision: 选择 A。步骤是需要被查询、校验与审计的一等实体；JSON 方案把完整性问题推给每个调用方，违背 REQ-NFUNC-065 的可追溯要求。
- Consequences: 正向——配置、待办、时间线都基于同一条结构化数据，校验集中；负向——需要新增表、兼容迁移，并保留旧 `FlowApprover` 表一个批次作为回滚兜底。

### ADR-172: 步骤判定集中在 ApprovalEngine，不散落到各业务应用

- Status: Proposed
- Type: decision
- Context: 决议、支出、收入三类单据共用审批引擎（`backend/apps/approval/services.py:25-135`），三类业务只注册回调（`backend/apps/resolutions/apps.py:16-17`、`backend/apps/income/apps.py:16-17`、`backend/apps/claims/apps.py`）。需要新增步骤判定与推进（REQ-FUNC-320~324）。
- Options:
  - A. 在 `ApprovalEngine` 内集中实现步骤状态机，业务应用只消费 approved/rejected 回调。
  - B. 各业务应用自行根据步骤与动作判定，引擎只存动作。
- Decision: 选择 A。三类单据的判定规则必须一致（C-368、REQ-NFUNC-064），集中实现可避免三份分叉逻辑；现有回调机制已足够表达业务生效。
- Consequences: 正向——单点保证或签/会签语义与并发正确性；负向——引擎复杂度上升，需要更完整的单元测试覆盖状态迁移。

### ADR-173: 在办实例使用“步骤状态快照”，历史流程折算为 1 步

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-326 要求改配置不影响在办实例；REQ-FUNC-327 要求既有流程折算为 1 步；C-367 要求拒绝终局与留痕不变。
- 被排除方案与约束来源:
  - 运行时实时读取 `ApprovalStep` 判定：被排除，因为管理员改步骤会导致在办单据换人/跳步，违反 REQ-FUNC-326 与留痕要求。
  - 升级时重建所有在办实例：被排除，属于不可逆的数据改写，违反 REQ-NFUNC-065。
- Decision: 实例继续使用 `flow_snapshot`，升级为 `schema_version=2` 的步骤快照，并在实例侧持久化每步状态（到达时间、状态）。旧快照（v1：mode + approver_ids）读取时视为“1 步、ANY、步骤名=流程名”。
- Consequences: 正向——在办实例完全按发起时配置执行；负向——快照与步骤表存在冗余，需在提交时一次性写入并冻结。

### ADR-174: 审批动作显式归属步骤

- Status: Proposed
- Type: decision
- Context: 时间线需要展示“每一步谁批准、备注、时间”（REQ-FUNC-328），现有 `ApprovalAction` 只有 instance 维度（`backend/apps/approval/models.py:49-55`）。
- Options:
  - A. 给 `ApprovalAction` 增加 `step_state` 外键与 `step_order` 快照字段。
  - B. 不改进作表，时间线按动作时间与步骤到达时间区间推算归属。
- Decision: 选择 A。时间区间推算在并发、补录、时区边界下不可靠，且无法在数据库层保证归属唯一；显式外键可直接支撑按步骤聚合。
- Consequences: 正向——时间线查询简单、可索引；负向——历史动作的 `step_state` 为空，需要读取端按 `step_order` 或“第 1 步”兜底。

### ADR-175: 并发推进用数据库事务 + 行锁，而不是乐观版本重试

- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-064 要求同一步骤多人并发审批结果唯一。现有 `decide()` 用 `filter(status="PENDING").update(...)` 做原子抢占（`backend/apps/approval/services.py:104-110`），但多步推进需要同时更新实例与步骤状态。
- Options:
  - A. `transaction.atomic()` + `select_for_update()` 锁住实例与当前步骤状态，串行化判定。
  - B. 乐观锁：读取版本号，写入时 `filter(version=...)` 比较并重试。
- Decision: 选择 A。审批是低频写操作，行锁成本可接受，且能一次保证“步骤推进 + 实例终态 + 动作落库”三者原子；乐观锁在会签计数场景需要复杂的重试与幂等处理。
- Consequences: 正向——判定逻辑简单、结果确定；负向——同一实例的并发请求会短暂排队，需在测试中覆盖并发用例。

### ADR-176: 时间线使用独立只读接口，三端共用

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-328~331 要求 Web 管理后台、Web 用户端、小程序展示同一时间线；现有审批接口只有待办与决策（`backend/apps/approval/urls.py:7-12`），没有实例详情。
- Options:
  - A. 新增 `GET /approval/instances/{id}` 只读时间线接口，权限在服务层统一判定。
  - B. 把时间线嵌进决议/报销/收入各自的详情接口。
- Decision: 选择 A。三类业务详情结构不同，内嵌会导致三份重复实现与三套权限判断；独立接口让三端共用一份契约。
- Consequences: 正向——三端一致、权限集中；负向——详情页需要多一次请求，需前端并行加载。

### ADR-177: 客户端只做展示与提交，不做判定

- Status: Proposed
- Type: constraint-driven
- Context: C-368 要求 Web 与小程序状态一致；REQ-FUNC-329 要求越权不可见。
- 被排除方案与约束来源:
  - 客户端本地判定或签/会签结果：被排除，因为三端会产生分叉，且客户端可信度低（协议 §L）。
  - 小程序单独一套后端接口：被排除，违反画像 P1 的单后端事实与 C-368。
- Decision: 三端调用同一组 `/approval/*` 接口；客户端只渲染后端返回的步骤状态、时间线与可操作性。
- Consequences: 正向——口径唯一、测试可用契约覆盖；负向——客户端必须处理“接口返回不可操作”的展示态。

## 开放问题 / ASSUMPTION

| 编号 | 内容 | 处理 |
|---|---|---|
| AS-01 | 步骤数量防御性上限设为 50 | [ASSUMPTION] 用户确认“不设业务上限”；为避免无界数组，接口校验设 50 步防御上限，不改变业务语义 |
| OQ-B-01 | 同一人跨步骤重复时，配置页是否仅提示不阻断 | 按需求开放问题 1 的结论：允许，保存时提示；本设计不阻断 |
| OQ-B-02 | 历史动作（无 step_state）在时间线中的展示归属 | 归入第 1 步并在响应中保留 `legacy=true` 标记 |
| OQ-B-03 | 半数同意（HALF_MAJORITY）是否也需要时间线 | 本次不改造其投票链路；时间线接口对其返回投票摘要或空步骤列表，交由 GROUP_C 按最小改动实现 |
