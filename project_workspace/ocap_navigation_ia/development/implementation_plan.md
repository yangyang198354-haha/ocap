<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-22T12:06:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.1.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_navigation_ia/requirements/user_stories.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/module_design.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/tech_stack.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划 — 导航信息架构整合（Web + 微信小程序）

## 实现概览

- 模块 9 个（MOD-174 ~ MOD-182），文件 16 个（修改 8、新建 8），无后端改动、无迁移、无新增依赖。
- 实现顺序按依赖拓扑：MOD-174（Web 配置叶子）→ MOD-175/177/178 → MOD-176；MOD-181（小程序配置叶子）→ MOD-179/180 → MOD-182。
- 采用架构 ADR-166（单端单一来源 + 双端一致性测试）、ADR-167（身份页页内 Tab）、ADR-168（保留 el-dropdown + 超时/popper 样式）、ADR-169（小程序宿主 + 三面板）、ADR-170（重定向表 + Tab 白名单）。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-174 | `frontend/src/layout/menus.js` | 修改 | — | M | 二级项收敛为 3 项并改名；新增 `USER_MENU_GROUPS`、`USER_MENU_TIMING`；`PORTAL_USER_MENU` 由分组展平；保留 `LEGACY_UNITS_HASH` | DONE |
| 2 | MOD-175 | `frontend/src/portal/PortalUserMenu.vue` | 修改 | MOD-174 | M | 两组渲染、组标题与分隔、`show/hide-timeout=180`、`popper-class` | DONE |
| 3 | MOD-175 | `frontend/src/shared/style.css` | 修改 | — | L | 全局 `.user-menu-popper` 过渡 400ms、组标题样式、减少动效降级 | DONE |
| 4 | MOD-177 | `frontend/src/router/index.js` | 修改 | MOD-174 | L | `/units/review` → `/units?tab=review`；`/units/appeals` → `/units/appeal?tab=mine` | DONE |
| 5 | MOD-178 | `frontend/src/portal/Me.vue` | 修改 | MOD-174 | L | 按 `USER_MENU_GROUPS` 渲染两组，退出登录置底 | DONE |
| 6 | MOD-176 | `frontend/src/portal/Units.vue` | 修改 | MOD-177 | M | 读取 `route.query.tab` 白名单并传 `initialTab` | DONE |
| 7 | MOD-176 | `frontend/src/portal/units/UnitsIdentity.vue` | 修改 | MOD-174/177 | M | 双 Tab 宿主，复用 `UnitsReview`，角标与数量同源 | DONE |
| 8 | MOD-181 | `miniprogram/utils/menu.js` | 新建 | — | L | 三 Tab、用户菜单分组、资料页映射 | DONE |
| 9 | MOD-179 | `miniprogram/pages/units/components/IdentityPane.vue` | 新建 | MOD-181 | H | 身份与房屋 + 认证产权 + 待审批子 Tab | DONE |
| 10 | MOD-179 | `miniprogram/pages/units/components/AppealPane.vue` | 新建 | MOD-181 | H | 认证申诉 / 我的申诉子 Tab | DONE |
| 11 | MOD-179 | `miniprogram/pages/units/components/ResidentPane.vue` | 新建 | MOD-181 | M | 发起申请 + 申请记录 | DONE |
| 12 | MOD-179 | `miniprogram/pages/units/index.vue` | 修改 | MOD-181、9-11 | M | 三 Tab 宿主，加载 housing，处理 `review=1` | DONE |
| 13 | MOD-180 | `miniprogram/pages/me/index.vue` | 修改 | MOD-181/182 | M | 个人设置/系统设置分组，保留报表与业务入口 | DONE |
| 14 | MOD-182 | `miniprogram/utils/api.js` | 修改 | — | L | 新增 `verifyEmail`、`cancelAccount` | DONE |
| 15 | MOD-182 | `miniprogram/pages/email/index.vue` | 新建 | MOD-181 | M | 邮箱验证最小页面 | DONE |
| 16 | MOD-182 | `miniprogram/pages/cancel/index.vue` | 新建 | MOD-181 | M | 账号注销最小页面 | DONE |
| 17 | MOD-180/182 | `miniprogram/pages.json` | 修改 | 15/16 | L | 注册两个新页面 | DONE |

## 需求追溯（Must Have + Should Have）

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-299 | AC-299-01 | `menus.js:PORTAL_MENU.units.children` | DONE | 3 项、顺序固定 |
| US-299 | AC-299-02 | `menus.js` 文案 + `SubNavBar/SideNav` 自动消费 | DONE | `/units/appeal` 保持原路由，仅改文案 |
| US-299 | AC-299-03 | `UnitsIdentity.vue` 申诉按钮 → `/units/appeal`（默认 appeal Tab） | DONE | 由 `UnitsAppeal.vue` 现有按钮承载 |
| US-299 | AC-299-04 | 同一 `PORTAL_MENU.children` 供 `SubNavBar` | DONE | 窄屏与宽屏同源 |
| US-300 | AC-300-01 | `UnitsIdentity.vue:el-tabs` | DONE | 默认 identity，无独立卡片 |
| US-300 | AC-300-02 | `UnitsIdentity.vue` Tab 标题 `el-badge` + `UnitsReview` | DONE | 数量取 `housing.pendingReviewCount` |
| US-300 | AC-300-03 | `UnitsIdentity.vue` `v-if="ownsAnyUnit"` 的 el-tab-pane | DONE | 非业主不渲染 Tab |
| US-300 | AC-300-04 | `UnitsReview.vue:6` 空态文案 | DONE | 复用现有空态 |
| US-301 | AC-301-01 | `menus.js` units.applications + `UnitsApplications.vue` | DONE | 双 Tab 不变 |
| US-301 | AC-301-02 | `resolveActive` 按 `to` 精确匹配 | DONE | 现有逻辑 |
| US-302 | AC-302-01 | `PortalUserMenu.vue` 两组渲染 + `USER_MENU_GROUPS` | DONE | 组标题 visible |
| US-302 | AC-302-02 | `USER_MENU_GROUPS` 移除“手机号/我的身份与房屋”；`MePhone.vue` 标题 | DONE | 页面标题改为“绑定手机” |
| US-302 | AC-302-03 | system 组 style 项 → `/me/style` | DONE | — |
| US-302 | AC-302-04 | personal 组 profile/email/cancel 地址不变 | DONE | — |
| US-303 | AC-303-01 | `PortalUserMenu.vue` 两组之后 `divided` 退出登录 | DONE | — |
| US-303 | AC-303-02 | `onCommand('logout')` 清会话并跳登录 | DONE | 现有逻辑 |
| US-304 | AC-304-01 | `miniprogram/pages/units/index.vue` 三 Tab + `MP_HOUSING_TABS` | DONE | 默认 identity |
| US-304 | AC-304-02 | `AppealPane.vue` 子 Tab + 提交后切 mine | DONE | — |
| US-304 | AC-304-03 | `IdentityPane.vue` 待审批子 Tab（仅业主） | DONE | 数据沿用 `/resident-applications/to-review` |
| US-304 | AC-304-04 | `ResidentPane.vue` 发起 + 记录 | DONE | — |
| US-305 | AC-305-01 | `pages/me/index.vue` 两组分组 | DONE | 组标题可见 |
| US-305 | AC-305-02 | `MP_USER_GROUPS` 绑定手机 + `pages/phone/index.vue` 标题 | DONE | 标题改为“绑定手机” |
| US-305 | AC-305-03 | 入口文案固定“绑定手机” | DONE | 不随是否有手机号变化 |
| US-305 | AC-305-04 | 系统设置下主题选择即时生效 | DONE | 复用 `store/theme.js` |
| US-306 | AC-306-01 | `router/index.js` `/units/appeals` 重定向；`AppealCenter` initialTab | DONE | — |
| US-306 | AC-306-02 | `/units/review` → `/units?tab=review`；`Units.vue` 白名单 | DONE | 非业主回落 identity |
| US-306 | AC-306-03 | `/me/identity` 路由保持 | DONE | — |
| US-306 | AC-306-04 | 路由驱动高亮，刷新无状态依赖 | DONE | — |
| US-307 | AC-307-01 | `housing.pendingReviewCount` 同时供侧栏与 Tab | DONE | 单一数据源 |
| US-307 | AC-307-02 | `UnitsReview` 处理成功后 `store.refresh()` | DONE | 现有逻辑 |
| US-308 | AC-308-01 | `style.css` `.user-menu-popper` 400ms | DONE | — |
| US-308 | AC-308-02 | `PortalUserMenu.vue` `show/hide-timeout=180` | DONE | 点击不延迟（Element Plus 行为） |
| US-308 | AC-308-03 | `prefers-reduced-motion: reduce` → 0s | DONE | — |
| US-309 | AC-309-01 | 两端常量逐字一致（C-363） | DONE | — |
| US-309 | AC-309-02 | 菜单无“认证申诉”，仅页内 Tab | DONE | — |
| US-310 | AC-310-01 | 全部入口保留（Web 5+1 项、小程序 4+1 项） | DONE | — |
| US-310 | AC-310-02 | 现有宽窄屏断点逻辑不变 | DONE | — |
| US-310 | AC-310-03 | 菜单无权限过滤；待审批 Tab 仅业主 | DONE | — |

## 迁移

无。后端零改动，不涉及数据库。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| `[DEVIATION]` 小程序邮箱验证使用 `purpose='EMAIL_VERIFY'`，`verifyEmail(code)` 仅传 code | IFC-401 写作 `purpose='EMAIL'`、`verifyEmail(email, code)` | 后端与 Web 现有实现（`frontend/src/shared/api.js:40`、`MeEmail.vue:44,53`）以 `EMAIL_VERIFY` + 当前资料邮箱为准；按真实契约实现 | 无；仅小程序调用参数与真实接口一致 |
| `[DEVIATION]` 保留 `/units/pick` 路由与 `UnitsPick` 组件 | module_design 只要求菜单移除“认证产权” | AC-236-03 与 C-362 的兼容要求，且“我的身份与房屋”页仍需按钮跳转 | 无；菜单不再暴露该入口 |

## 开放问题

- `[ASSUMPTION]` Element Plus 2.8.7 的 `show-timeout`/`hide-timeout` 生效（ADR-168 A-01）；若不生效，过渡仍由 400ms CSS 保证“可感知”，悬停延迟退化为默认行为，登记为测试阶段观察项。
- `[ASSUMPTION]` 小程序 `pages/me` 的“界面风格”采用同页主题区块（不新增独立页），点击入口滚动定位；与 AC-305-04“进入主题选择区域”一致。

## 缺陷修复记录（1.1.0）

| DEF | 位置 | 根因 | 修改 |
|---|---|---|---|
| DEF-001（GROUP_D 回流） | `miniprogram/utils/confirm.js` | 注销页调用 `confirmDanger('cancelAccount')`，但 `CONFIRM_TEXTS` 未定义该键，Promise 被拒绝导致确认后不发起请求 | 补充 `cancelAccount` 确认文案（标题 + 两条后果）；复测 TC-E2E-1108 通过 |
