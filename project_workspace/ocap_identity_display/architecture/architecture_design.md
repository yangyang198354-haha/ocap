<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-14T17:34:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_identity_display/requirements/user_stories.md</file>
    <file>backend/apps/identity/services.py</file>
    <file>backend/apps/committee/services.py</file>
    <file>frontend/src/portal/Home.vue</file>
    <file>frontend/src/stores/auth.js</file>
    <file>miniprogram/pages/index/index.vue</file>
    <file>miniprogram/pages/me/index.vue</file>
    <file>backend/apps/registry/models.py</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：用户端身份显示与认证房屋信息（INCREMENTAL）

## 架构概览

本次改动位于现有 Django + DRF 后端、Vue 3 Web 用户端与 uni-app 小程序的展示层，不新增服务、运行单元或第三方依赖。

关键质量属性：
- 口径一致（REQ-FUNC-136 ~ 141）：身份与房屋信息由后端 `/me` 统一计算，Web 与小程序只做展示，避免两端各自推导。
- 一次呈现（REQ-NFUNC-024）：主页在 `/me` 返回前显示加载占位，不先显示“游客 / 0 套”。
- 只展示当前有效关系（REQ-NFUNC-026）：沿用 `Membership.ended_at IS NULL` 与有效 `Seat` 过滤。

现有相关链路：
- `/me` 聚合：`backend/apps/identity/services.py:17-45`（`IdentityService.me`）。
- 身份文案：`backend/apps/committee/services.py:65-77`（`CommitteeQuery.identity_labels`）。
- 角色与有效期：`backend/apps/residency/models.py:8`（HEAD/OWNER/RESIDENT）、`ended_at`（`models.py:18-19`）。
- 清册类型与面积：`backend/apps/registry/models.py:10、66-67`。
- Web 主页：`frontend/src/portal/Home.vue:9、107-108`；身份读取 `frontend/src/stores/auth.js:10`。
- 小程序主页：`miniprogram/pages/index/index.vue:8、80-85`；“我的”页 `miniprogram/pages/me/index.vue:23`。

## 部署视图

| 组件 | 运行单元 | 环境 |
|---|---|---|
| Django 后端 | systemd `ocap-backend`（gunicorn `127.0.0.1:9000`） | 测试（内网树莓派 / 外网 frp），画像 P7 |
| Web 前端静态产物 | nginx `8090` 下 `/ocap/` | 同上 |
| 微信小程序 | 微信开发者工具 / 真机包 | 同上，构建产物由用户侧发布 |

本次不新增部署单元；无数据库结构变更，无需迁移。

## ADR

### ADR-001: 用户可见身份改为单一最高身份

- Status: Proposed
- Type: decision
- Context: 现有 `identity_labels` 先并列业委会职务，再并列第一条房屋关系的角色名（`committee/services.py:65-77`），首位认证者显示“户主”（`residency/models.py:8`、`residency/services.py:30`）。REQ-FUNC-136 / C-34 要求只显示一个身份，且有效职务直接显示职务（Q-ID-01）。
- Options:
  - A. 在 `CommitteeQuery.identity_labels` 内统一计算单一最高身份：有效职务（主任/副主任/委员/业主代表）> 产权业主（HEAD/OWNER）> 同住人（RESIDENT）> 游客。优点：所有消费方一致；缺点：影响 `initiator_labels` 等审计字段的文案长度（由多值变单值）。
  - B. 保留 `identity_labels` 供内部审计，新增 `identity_label` 仅供 `/me`。优点：审计文案不变；缺点：两套口径并存，后续仍可能泄漏“户主”。
- Decision: 选择 A。REQ-FUNC-136 要求用户端只有单一身份，且 `initiator_labels` 会随决议详情返回用户（`resolutions/views.py:29`），保留旧口径会继续出现“户主”（Q-ID-06）。
- Consequences: 正向：`/me`、决议发起人标签、报销/收入审计字段统一为单一身份；负向：既有测试中断言“户主/多标签”的用例需按新口径更新，历史 `initiator_labels` 数据不回填（超出本期范围）。

### ADR-002: 在 `/me` 的 `identities.units` 中扩展房屋展示字段

- Status: Proposed
- Type: decision
- Context: `identities.units` 目前只有 `unit_id`、`specific_part`、`role`（`identity/services.py:20-23`），缺少 REQ-FUNC-139/140 所需的类型与面积；Web 与小程序都需要同一份数据（REQ-FUNC-141）。
- Options:
  - A. 扩展 `GET /me` 的 `units`，一次返回名称、类型、面积与关系标签。优点：一次请求、两端同源、无额外鉴权面；缺点：`/me` 响应略增大（每用户通常 ≤ 数套）。
  - B. 新增 `GET /me/units` 独立接口。优点：职责单一；缺点：主页需两次请求，加载态更复杂，且要新增鉴权与测试面。
  - C. 前端按 `unit_id` 调清册接口补齐。优点：后端零改动；缺点：清册接口权限/字段面向管理端，暴露风险与跨端重复实现，违反 REQ-NFUNC-024。
- Decision: 选择 A。改动最小，且与 REQ-NFUNC-024“一次呈现”一致。
- Consequences: 正向：Web 与小程序共用同一契约；负向：`/me` 契约测试需更新，前端需容忍未知新增字段。

### ADR-003: 展示格式化由后端给出 `*_label` / `area_display`

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-140 要求面积两位小数 + “㎡”、类型中文、缺失“未登记”；REQ-FUNC-141 要求 Web 与小程序一致。
- Options:
  - A. 后端返回 `unit_type_label`、`area_display`、`role_label`，前端直接展示。优点：两端零重复格式化逻辑，空值文案一致；缺点：展示文案耦合在 API。
  - B. 后端只返回原始 `unit_type`、`area`，两端各自格式化。优点：API 更“纯”；缺点：两端需各写一套空值与精度规则，容易不一致。
- Decision: 选择 A。REQ-FUNC-141 的一致性优先，且 Type 中文枚举已在 `registry/models.py:10` 的 choices 中。
- Consequences: 正向：AC-146-01~05、AC-148-02 可直接断言字符串；负向：后续调整文案需改后端并回归两端。

### ADR-004: 主页加载态与失败态

- Status: Proposed
- Type: constraint-driven
- Context: REQ-NFUNC-024 要求不出现“先游客后真实身份”的跳变；现有 `Home.vue:9` 在 `auth.me` 为空时直接显示“游客”。
- Options（被排除）:
  - 仅在前端延迟渲染身份文案：仍无法区分“加载中”和“加载失败”，失败时会被误判为游客。
  - 后端增加同步阻塞：无必要，`/me` 已是单次请求。
- 约束来源: REQ-NFUNC-024 + 现有 `auth.fetchMe()`（`frontend/src/stores/auth.js:22-31`）已有 `loading` 状态。
- Decision: 使用 `auth.loading` / `auth.me` / 请求异常三态：加载中显示“加载中…”，失败显示“加载失败，请重试”并提供重试，成功后才显示身份。
- Consequences: 正向：不会把未加载或失败误显示为游客；负向：主页模板与测试需增加三态分支。

## 开放问题 / ASSUMPTION

- [ASSUMPTION] 同住人房屋在“认证房屋”中标注“同住人”，产权业主房屋标注“产权业主”（Q-ID-03 的用户答复未指定标签文案，采用与身份一致的词）。
- 历史 `Resolution.initiator_labels` / `IncomeSheet.creator_labels` 等已落库的多标签文案不回填；如需清理，另立数据修复需求。
