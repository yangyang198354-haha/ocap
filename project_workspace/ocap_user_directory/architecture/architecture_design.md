<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-11T22:34:05.7369915+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>../ocap/architecture/module_design.md</file></input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 架构设计（增量）

## 架构概览

本次改动在现有系统内的位置：Django + DRF 后端的账号管理只读接口，与 Vue 3 + Element Plus 管理后台的“账号”页。数据来自既有账号（User）、房屋关系（Membership）、业委会席位（Seat）与业主清册（RegistryUnit / RegistryOwner / RegistryPhone），**不新增表、不新增外部依赖、不改动现有写入流程**。

关键质量属性：
- REQ-NFUNC-019：仅管理员可访问；手机号保持脱敏；实名只出现在管理后台。
- REQ-NFUNC-020：默认分页（20 条/页）下列表响应不超过 2 秒（开发机基线）。

## 部署视图

| 组件 | 运行单元 | 环境 |
|---|---|---|
| Web 后端 | gunicorn `ocap-backend`（127.0.0.1:9000） | 测试环境（内网/外网入口，画像 P7） |
| 数据库 | MySQL `ocap`（192.168.31.98:3306） | 测试环境（画像 P7） |
| Web 前端 | 静态构建产物，由 nginx `/ocap/` 提供 | 测试环境（画像 P7） |

不涉及内容 worker、定时任务、小程序与任何新服务。

## ADR

### ADR-064: 目录信息在后端单次聚合返回

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-123 ~ 128 需要在一页 20 个用户上同时展示身份、认证数量、实名与上次登录；现有列表接口只返回账号基础信息（`backend/apps/accounts/views.py:385-400`、`backend/apps/accounts/serializers.py:14-19`）。
- Options:
  - A 后端在现有列表接口内聚合，一次响应返回全部展示信息。优点：一次请求、口径统一、前端简单；缺点：后端需预取关联数据。
  - B 前端逐行调用现有“用户房屋关系”与清册接口。优点：后端不改；缺点：20 行最多 40+ 次请求，无法满足 REQ-NFUNC-020，且口径分散。
  - C 新增独立“用户目录”接口，前端与基础列表合并。优点：职责分离；缺点：两次请求、分页对齐复杂，无增量收益。
- Decision: 选择 A。沿用现有分页与权限，只在同一响应中增加计算字段。
- Consequences: 正向：单请求、无 N+1、权限与分页逻辑复用；负向：`AdminUserListView` 的查询复杂度上升，需要固定预取策略与查询数测试。

### ADR-065: 身份与认证数量在应用层基于预取记录计算

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-123 要求只显示最高身份，优先级为业委会职务（主任 > 副主任 > 委员 > 业主代表）> 户主 > 产权业主 > 同住人 > 游客；REQ-FUNC-124 要求统计有效认证的专有部分数量（`user_stories.md` AC-132-01 ~ 05）。
- Options:
  - A 预取当前有效 Membership 与 Seat，在 Python 中按固定优先级取最高身份，并对 Membership 的 unit_id 去重计数。优点：规则集中、易测试、SQL 简单；缺点：每页需固定数量关联查询。
  - B 用数据库子查询/注解（Subquery + Case/When）计算。优点：单条 SQL；缺点：优先级与多值去重表达复杂，跨 MySQL/SQLite 行为差异大，维护成本高。
- Decision: 选择 A，每页固定预取（users、memberships+unit、unit owners、phones、seats），在服务层计算。
- Consequences: 正向：与现有 `CommitteeQuery`/`MembershipService` 语义一致，可用纯单元测试覆盖优先级；负向：必须固定预取并加查询数回归测试，防止后续退化为 N+1。

### ADR-066: 实名搜索使用跨清册的数据库子查询并集

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-127 要求在保留账号/昵称/手机号搜索的同时支持按实名搜索；实名只存在于业主清册（`backend/apps/registry/models.py:43-65`），与用户通过手机号和有效产权关系关联。
- Options:
  - A 用子查询把“姓名匹配的清册业主 → 其手机号 / 其专有部分”与用户的有效产权关系求交集，与现有条件做 OR 并集，查询集去重后分页。优点：数据库内完成、可扩展、count 正确；缺点：SQL 较复杂，需 `distinct()`。
  - B 先查姓名得到手机号列表，再在 Python 中过滤全量用户。优点：实现简单；缺点：用户量大时全表载入，违背 REQ-NFUNC-020。
  - C 在用户表新增冗余实名字段并建索引。优点：查询最快；缺点：需要迁移与多来源同步，超出“无表结构变更”的增量约束。
- Decision: 选择 A。姓名匹配使用 `name__icontains`，并与 `ended_at IS NULL` 的有效 Membership、`HEAD/OWNER` 角色约束组合；最终查询集 `distinct()`。
- Consequences: 正向：无迁移、count 与分页沿用现有实现；负向：`icontains` 在 MySQL 上无法使用普通索引，用户量极大时可能变慢，列入技术风险并以分页上限缓解。

### ADR-067: 时间以机器可读格式返回，展示格式在前端统一

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-126 要求“YYYY-MM-DD HH:mm”与“从未登录”；现有接口时间字段均返回 ISO8601 或原值（`backend/apps/accounts/serializers.py`）。
- Options:
  - A 后端返回 ISO8601（可空），前端统一格式化为 `YYYY-MM-DD HH:mm`，空值显示“从未登录”。优点：接口可被其他客户端复用、时区处理集中；缺点：前端需一个格式化函数。
  - B 后端直接返回已格式化的中文字符串。优点：前端零处理；缺点：接口不可复用、测试需固定时区字符串，其他客户端无法本地化。
- Decision: 选择 A。后端保留 ISO8601；前端用共享格式化函数输出展示文本。
- Consequences: 正向：契约稳定、可测试；负向：前端多一处格式化逻辑，需覆盖空值与时区。

## 开放问题 / ASSUMPTION

- [ASSUMPTION] REQ-NFUNC-020 的“2 秒”按开发机 SQLite 内存库与 20 条/页衡量；生产 MySQL 上以同一分页上限验证，不额外引入缓存。
- [ASSUMPTION] “已认证（N 套）”的 N 统计所有有效 Membership（户主/产权业主/同住人），按专有部分去重；同住人计入“已认证专有部分”。
- 无需求冲突。
