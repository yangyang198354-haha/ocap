<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-22T12:01:25+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_navigation_ia/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_03,PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计 — 导航信息架构整合（Web + 微信小程序）

## 架构概览

本次为 INCREMENTAL 增量，范围仅 Web 前端（Vue 3 + Vite + Element Plus + Pinia）与微信小程序（uni-app Vue 3），**后端不改**。改动集中在三处：`frontend/src/layout/menus.js` 的菜单与文案配置、`frontend/src/portal/` 的身份页与用户菜单呈现、`miniprogram/pages/` 的页面拆分与分组。后端接口、数据模型与权限全部复用现有实现。

现有系统位置与本次增量：

| 层 | 现有位置 | 本次增量 |
|---|---|---|
| Web 菜单配置 | `frontend/src/layout/menus.js:4-46`（`PORTAL_MENU`、`PORTAL_USER_MENU`） | “我的房屋”二级项收敛为 3 项；新增用户菜单分组常量与文案表；保留旧地址映射 |
| Web 侧栏/切换条 | `frontend/src/layout/SideNav.vue:1-108`、`SubNavBar.vue:1-34`、`PortalLayout.vue:8,18` | 无结构性改动，自动消费新菜单配置与 3 项二级菜单 |
| Web 身份页 | `frontend/src/portal/units/UnitsIdentity.vue:45-47`（底部 `UnitsReview` 卡片） | 改为页内双 Tab（身份与房屋 / 待我审批），`UnitsReview.vue` 内容复用 |
| Web 用户菜单 | `frontend/src/portal/PortalUserMenu.vue:3-18` | 分“个人设置/系统设置”两组；动效 400ms、悬停意图 180ms |
| Web 窄屏“我的”页 | `frontend/src/portal/Me.vue:6-13` | 按同一分组常量渲染 |
| Web 路由 | `frontend/src/router/index.js:37-48` | `/units/review` 落到“待我审批”Tab；其余旧地址保持 |
| 小程序房屋页 | `miniprogram/pages/units/index.vue:1-75` | 拆为页内三 Tab 宿主 + 3 个子面板组件；待审批为身份面板子 Tab |
| 小程序“我的”页 | `miniprogram/pages/me/index.vue:4-48` | 个人设置/系统设置分组；新增邮箱验证、账号注销两个最小页面 |
| 小程序共享常量 | 无 | 新建 `miniprogram/utils/menu.js`，与 Web 文案表逐项一致 |

关键质量属性：

- REQ-NFUNC-061：下拉菜单过渡 400ms、悬停意图延迟 180ms，尊重 `prefers-reduced-motion`。
- REQ-NFUNC-062：Web 侧栏、窄屏切换条、小程序三处菜单层级、名称、顺序一致（约束 C-363）。
- REQ-NFUNC-063：旧地址不 404，宽窄屏切换与刷新后高亮正确。

## 部署视图

只使用画像 P7 中存在的环境与方式，不新增运行单元：

| 组件 | 运行单元 | 环境 |
|---|---|---|
| Web 前端（本次唯一 Web 变更） | Vite 构建产物，nginx `8090` 下 `/ocap/` 静态目录 | 测试（内网）树莓派 192.168.31.51；外网经 frp 反代 |
| Web 后端 | 不构建、不重启（无代码变更） | 同上 |
| 数据库 | 无迁移 | 同上 |
| 微信小程序 | 重新构建 mp-weixin 产物并在开发者工具/体验版验证 | 微信开发者工具（不涉及服务端发布） |

生产环境在画像 P7 中不存在，本设计不假设生产部署。

## ADR

### ADR-166: 菜单与文案采用“单端单一来源 + 双端一致性测试”

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-297~310、REQ-FUNC-304、REQ-NFUNC-062、C-363；现有 Web 菜单集中在 `menus.js:4-46`，小程序文案分散在 `pages/units/index.vue` 与 `pages/me/index.vue`，存在改名漂移风险。
- Options:
  - A. Web 在 `menus.js` 内维护 `HOUSING_MENU` 与 `USER_MENU_GROUPS` 文案表；小程序新建 `utils/menu.js` 维护同一份文案表；两端各一处定义，测试逐字比对关键文案。
    - 优：不新增构建依赖；与现有结构一致；测试可捕获文案漂移。
    - 缺：两套代码各存一份常量，需靠测试保证一致。
  - B. 抽取共享 JSON 包供 Web 与小程序同时 import。
    - 优：物理上只有一份文案。
    - 缺：需要新增 workspace/构建配置，超出本次“不引入新依赖与构建改造”的约束。
  - C. 保持分散硬编码，仅在页面内改名。
    - 优：改动最小。
    - 缺：无法满足 REQ-NFUNC-062，后续改名仍会漂移。
- Decision: 选择 A。符合画像既有结构，且用测试满足 REQ-NFUNC-062 的可验证性；不引入新依赖。
- Consequences:
  - 正向：Web 三个消费点（SideNav、SubNavBar、Me）共用同一配置；小程序分组集中。
  - 负向：文案在两处维护，必须配套一致性测试（GROUP_D 覆盖）；新增菜单需要同步改两处。

### ADR-167: “待我审批”改为身份页页内 Tab，并保留 `/units/review` 深链

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-301、REQ-FUNC-302、REQ-FUNC-315、US-300、AC-300-01~04、AC-306-02；现状为 `UnitsIdentity.vue:45-47` 底部渲染 `UnitsReview.vue`，侧栏角标挂在 `units.identity`。
- Options:
  - A. 在 `UnitsIdentity.vue` 内使用 `el-tabs` 双面板：面板一为现有身份与房屋内容，面板二渲染 `UnitsReview`；新增 `initialTab` prop，`/units/review` 重定向到 `/units?tab=review`。
    - 优：复用现有 `UnitsReview` 与 housing store；Tab 切换不销毁已渲染面板（Element Plus 默认保留），审批后角标刷新逻辑不变。
    - 缺：`UnitsIdentity` 增加一层宿主职责；需要处理旧 hash 与 query 两种落点。
  - B. 为“待我审批”新增独立路由页面。
    - 优：页面职责单一。
    - 缺：用户要求“作为另外一个 tab 放到这个页面”，独立路由违背需求；侧栏高亮与角标需额外维护。
  - C. 保留底部卡片，顶部再加一个锚点 Tab。
    - 优：改动最小。
    - 缺：违反 AC-300-01“页面正文不再出现独立卡片”。
- Decision: 选择 A。满足“页内 Tab”语义，复用现有列表与操作，深链通过 query 白名单落点。
- Consequences:
  - 正向：审批入口与房屋信息同屏；角标与 Tab 数量共用 `housing.pendingReviewCount`。
  - 负向：非产权业主访问 `/units?tab=review` 时要安全回落到默认 Tab（AC-306-02）；需前端测试覆盖。

### ADR-168: 保留 `el-dropdown`，用超时参数与 popper 样式实现分组与慢动效

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-305~311、REQ-NFUNC-061、US-302/303/308；现状 `PortalUserMenu.vue:4` 为 `el-dropdown`，`trigger=['hover','click']`，无分组、无自定义时长。
- Options:
  - A. 继续使用 `el-dropdown`：`show-timeout=180`、`hide-timeout=180` 控制悬停意图；`popper-class="user-menu-popper"` 配合全局 CSS 把展开/收起过渡设为 400ms，并在 `prefers-reduced-motion` 下置 0；分组用不可点击的组标题 + `el-dropdown-item`。
    - 优：不新增组件与依赖；键盘与点击行为沿用 Element Plus；分组结构简单。
    - 缺：依赖 `el-dropdown` 的超时属性与 popper 过渡类名；需在实现时以实际渲染验证（见开放问题 A-01）。
  - B. 自研下拉组件（手动 `mouseenter` 计时 + `Transition`）。
    - 优：动效与分组完全可控。
    - 缺：需自行实现键盘导航、焦点管理与点击外部关闭，回归风险高。
  - C. 改用 `el-popover` 承载菜单。
    - 优：动效可控。
    - 缺：需重做菜单项交互与可访问性，收益不足。
- Decision: 选择 A；若实现时发现 `show-timeout`/`hide-timeout` 在当前 Element Plus 版本不生效，则在同一个组件内加 180ms 的 `mouseenter` 计时包装，不更换组件库。
- Consequences:
  - 正向：改动集中在 `PortalUserMenu.vue` 与一段全局样式；点击展开不受 180ms 延迟影响。
  - 负向：popper 被 teleport 到 body，过渡样式必须用全局选择器而不能用 scoped；需在实现计划中注明样式落点。

### ADR-169: 小程序“我的房屋”拆为宿主 + 三个面板，并新增邮箱/注销最小页面

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-312、REQ-FUNC-313、US-304、US-305、AC-304-01~04、AC-305-01~04；现状 `pages/units/index.vue:1-75` 单文件堆叠 6 张卡片，`pages/me/index.vue:4-48` 混排；小程序缺少邮箱验证与账号注销页面，但后端已有 `/me/email/verify` 与 `/me/cancel`（`frontend/src/shared/api.js:40,45`）。
- Options:
  - A. `pages/units/index.vue` 保留为 Tab 宿主，新建 `pages/units/components/{IdentityPane,AppealPane,ResidentPane}.vue` 承载三块内容；待审批作为 `IdentityPane` 内的子 Tab。`pages/me/index.vue` 按分组渲染，新增 `pages/email/index.vue`、`pages/cancel/index.vue` 复用现有后端接口。
    - 优：单文件复杂度可控；菜单项全部可达，满足 C-363 与 REQ-FUNC-313；后端零改动。
    - 缺：新增 5 个文件与 2 条路由；小程序构建产物需重新验证。
  - B. 保持单文件，用 `v-if` 切换三块内容。
    - 优：文件数少。
    - 缺：单文件继续膨胀，测试与维护困难；“我的”页仍缺邮箱/注销入口，无法满足需求。
  - C. 小程序不提供邮箱/注销，菜单标注“请在 Web 端操作”。
    - 优：不新增页面。
    - 缺：违反 REQ-FUNC-313 的条目清单与 C-363 双端一致。
- Decision: 选择 A。面板拆分控制复杂度；邮箱验证与账号注销用最小页面复用既有后端接口，不新增后端能力。
- Consequences:
  - 正向：三端入口齐全，页面职责清晰。
  - 负向：小程序新增 2 个页面需加入 `pages.json` 并在构建后验证；邮箱/注销页面需遵循既有表单与错误处理模式。

### ADR-170: 旧地址兼容采用“重定向表 + Tab 白名单”

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-314、REQ-NFUNC-063、C-362；现有 `menus.js:89-90` 的 `LEGACY_UNITS_HASH` 与 `router/index.js:37-48` 的重定向。
- 被排除方案与约束来源:
  - 移除 `/units/appeal`、`/units/appeals`、`/units/review` 等旧路由：违反 C-362 与 AC-306-01/02。
  - 仅改菜单文案、不处理深链 Tab：违反 AC-306-02 与 REQ-FUNC-314。
- Decision: 保留并扩展现有重定向：`/units/appeal` → `/units/appeal`（新名称页面，默认“认证申诉”Tab）、`/units/appeals` → `/units/appeal?tab=mine`、`/units/review` → `/units?tab=review`；`initialTab` 只接受 `identity|review|appeal|mine|form|records` 白名单，非法值回落默认。
- Consequences:
  - 正向：书签、历史链接、外部入口不失效。
  - 负向：路由与页面 props 的 Tab 契约需要在前端测试中固定，避免后续改名再次破坏。

## 开放问题 / ASSUMPTION

| ID | 内容 | 处理 |
|---|---|---|
| A-01 | `[ASSUMPTION]` Element Plus `el-dropdown` 的 `show-timeout`/`hide-timeout` 在 2.8.7 可用 | 实现时以实际渲染验证；不生效则按 ADR-168 的兜底方案加 180ms 计时包装 |
| A-02 | 小程序“个人资料”复用现有 `pages/profile-setup/index.vue`（完善资料） | 沿用现有页面，不改其内容；如需独立资料页另立需求 |
| A-03 | 小程序“我的”页保留“财务报表”“报销/备用金”（委员会成员可见）“退出登录” | 按需求 Q5 推荐默认执行；财务报表作为独立卡片放在设置分组之后 |
| A-04 | 动效取值 400ms / 180ms 为需求 Q7 推荐默认 | 若用户后续要求更慢，只改常量，不改组件结构 |
