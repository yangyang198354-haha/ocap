<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-22T12:01:25+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_navigation_ia/requirements/user_stories.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/architecture_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计 — 导航信息架构整合（Web + 微信小程序）

## 模块总览

| MOD | 名称 | 文件（新建/修改，路径相对仓库根） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-174 | Web 菜单与文案配置 | 修改 `frontend/src/layout/menus.js` | “我的房屋”二级项收敛为 3 项；用户菜单分组常量与文案；旧地址映射 | REQ-FUNC-297/298/299/300/303/304/310/315、REQ-NFUNC-062；US-299/302/307/309 | 无 |
| MOD-175 | Web 用户下拉菜单 | 修改 `frontend/src/portal/PortalUserMenu.vue`；新增/修改全局样式 `frontend/src/shared/style.css` | 两组菜单渲染、400ms 过渡、180ms 悬停意图、减少动效降级 | REQ-FUNC-305/306/307/308/309/310/311、REQ-NFUNC-061；US-302/303/308 | MOD-174（IFC-393、IFC-396） |
| MOD-176 | Web 身份与房屋页 Tab 化 | 修改 `frontend/src/portal/units/UnitsIdentity.vue`、`frontend/src/portal/Units.vue` | 双 Tab 宿主；复用 `UnitsReview`；Tab 数量与侧栏角标一致 | REQ-FUNC-301/302/315；US-300/307 | MOD-174、MOD-177 |
| MOD-177 | Web 路由兼容与初始 Tab | 修改 `frontend/src/router/index.js` | 旧地址重定向、Tab 白名单、`initialTab` props 契约 | REQ-FUNC-314、REQ-NFUNC-063；US-306/310 | MOD-174（IFC-393） |
| MOD-178 | Web 窄屏“我的”页分组 | 修改 `frontend/src/portal/Me.vue` | 按 `USER_MENU_GROUPS` 渲染两组入口 | REQ-FUNC-304、REQ-NFUNC-062；US-302/309 | MOD-174 |
| MOD-179 | 小程序“我的房屋”三 Tab | 修改 `miniprogram/pages/units/index.vue`；新建 `miniprogram/pages/units/components/IdentityPane.vue`、`AppealPane.vue`、`ResidentPane.vue` | 顶部三 Tab 宿主；身份面板内含“待我审批”子 Tab；内容从原单文件迁出 | REQ-FUNC-312；US-304 | MOD-181 |
| MOD-180 | 小程序“我的”页分组 | 修改 `miniprogram/pages/me/index.vue`；修改 `miniprogram/pages.json` | 个人设置/系统设置分组；保留财务报表、业务入口与退出登录 | REQ-FUNC-313；US-305 | MOD-181 |
| MOD-181 | 小程序菜单常量 | 新建 `miniprogram/utils/menu.js` | 维护三 Tab、用户菜单分组、资料页映射与统一文案 | REQ-FUNC-304/312/313、REQ-NFUNC-062；US-304/305/309 | 无 |
| MOD-182 | 小程序邮箱验证与账号注销页 | 新建 `miniprogram/pages/email/index.vue`、`miniprogram/pages/cancel/index.vue`；修改 `miniprogram/utils/api.js`、`miniprogram/pages.json` | 复用后端 `/me/email/verify`、`/me/cancel` 的最小页面，补齐 C-363 菜单项 | REQ-FUNC-313；US-305 | MOD-181、既有 `utils/http.js` |

## 模块详情

### MOD-174 Web 菜单与文案配置

**职责**：菜单结构、文案与旧地址映射的唯一配置点。

**接口 IFC-393**（`frontend/src/layout/menus.js`，TypeScript 形状描述）：

```ts
type NavLeaf = {
  key: string
  label: string
  to: string
  activeOn?: string[]
  badge?: 'pendingReview'
}

type NavGroup = {
  key: 'personal' | 'system'
  label: '个人设置' | '系统设置'
  items: NavLeaf[]
}

export const PORTAL_MENU: Array<NavLeaf & { match: string[]; audience: 'all' | 'committee'; children?: NavLeaf[] }>
export const USER_MENU_GROUPS: NavGroup[]
export const PORTAL_USER_MENU: NavLeaf[]   // 由 USER_MENU_GROUPS 展平，供既有测试/窄屏兼容
export const USER_MENU_TIMING: { transitionMs: 400; hoverIntentMs: 180 }
export const LEGACY_UNITS_HASH: Record<string, string>
```

- `PORTAL_MENU` 中 `units.children` 固定为：`units.identity`（我的身份与房屋，`to: '/units'`，`activeOn: ['/me/identity']`，`badge: 'pendingReview'`）、`units.appeal`（我的认证与申述，`to: '/units/appeal'`）、`units.applications`（我的同住人申请，`to: '/units/applications'`）。
- `USER_MENU_GROUPS`：`personal` 组依次为个人资料(`/me/profile`)、绑定手机(`/me/phone`)、设置密码(`/me/password`)、邮箱验证(`/me/email`)、账号注销(`/me/cancel`)；`system` 组为界面风格(`/me/style`)。
- 输入校验：本模块为静态常量，无外部输入；消费方传入非法 Tab 时由 MOD-177 白名单拦截。
- 鉴权：不涉及；菜单可见性继续由 `visibleMenu()` 按 `isCommittee` 过滤。

**依赖**：无。**外部依赖**：无。

### MOD-175 Web 用户下拉菜单

**职责**：按两组渲染下拉菜单，实现可感知但不拖沓的动效。

**接口 IFC-396**（`frontend/src/portal/PortalUserMenu.vue`）：

- Props：无（读取 `auth.me`、`USER_MENU_GROUPS`、`USER_MENU_TIMING`）。
- 行为契约：
  - `trigger=['hover','click']`；悬停时 `show-timeout=180`、`hide-timeout=180`，点击立即展开。
  - `popper-class="user-menu-popper"`；全局样式 `.user-menu-popper.el-zoom-in-top-enter-active, .user-menu-popper.el-zoom-in-top-leave-active { transition-duration: 400ms; }`，`@media (prefers-reduced-motion: reduce)` 下 `transition-duration: 0s`。
  - 组标题渲染为不可点击的 `<li role="presentation" class="user-menu-group-title">`，组间以 `<li role="separator">` 分隔；菜单项沿用 `el-dropdown-item`。
  - “退出登录”渲染在两组之后，`divided` 样式保留。
- 输入校验：命令值只接受 `USER_MENU_GROUPS` 中的 `to` 或 `'logout'`；其他值忽略。
- 鉴权：沿用登录态；退出登录调用现有 `auth.logout()`。

**依赖**：MOD-174（IFC-393、IFC-396）。**外部依赖**：Element Plus `el-dropdown`（既有）。

### MOD-176 Web 身份与房屋页 Tab 化

**职责**：把“待我审批的同住人申请”从底部卡片改为页内第二个 Tab。

**接口 IFC-394**（`frontend/src/portal/units/UnitsIdentity.vue`）：

```ts
type IdentityTab = 'identity' | 'review'
props: { initialTab?: IdentityTab }   // 默认 'identity'
```

- 模板：`el-tabs v-model="tab"`；面板一 `name="identity"` 为现有汇总身份、真实姓名、房屋列表；面板二 `name="review"` 渲染 `<UnitsReview />`，仅当 `ownsAnyUnit` 为真时渲染该 Tab。
- Tab 标题：`待我审批的同住人申请`，有数量时追加 `el-badge :value="pendingReviewCount"`；数量来源 `housing.pendingReviewCount`，与侧栏角标同源。
- 输入校验：`initialTab` 非 `IdentityTab` 时回落 `'identity'`；非产权业主请求 `review` 时回落 `'identity'`。
- 鉴权：沿用 `ownsAnyUnit` 与后端 403；前端隐藏不作为权限边界。

**依赖**：MOD-174（角标 key）、MOD-177（初始 Tab）。**外部依赖**：`UnitsReview.vue`、`housing` store。

### MOD-177 Web 路由兼容与初始 Tab

**职责**：保证旧地址可用，并把深链落到正确 Tab。

**接口 IFC-395**（`frontend/src/router/index.js`）：

| 旧地址 | 新落点 | 初始 Tab |
|---|---|---|
| `/units/appeal` | `/units/appeal` | `appeal`（默认） |
| `/units/appeals` | `/units/appeal?tab=mine` | `mine` |
| `/units/review` | `/units?tab=review` | `review` |
| `/me/identity` | `/units` | `identity` |
| `/units#appeal` | `/units/appeal` | `appeal` |

- `Units.vue` 从 `route.query.tab` 读取值，经白名单 `['identity','review','appeal','mine','form','records']` 校验后作为 `initialTab` 传给子视图；非法值忽略。
- 输入校验：query 为字符串；白名单外一律回落默认值，不抛错。
- 鉴权：沿用现有路由守卫（登录态）。

**依赖**：MOD-174（`LEGACY_UNITS_HASH`）。**外部依赖**：vue-router（既有）。

### MOD-178 Web 窄屏“我的”页分组

**职责**：窄屏总览页与下拉菜单同构。

**接口 IFC-397**（`frontend/src/portal/Me.vue`）：

- 渲染 `USER_MENU_GROUPS`：每组一个 `<section>`，标题为组 `label`，条目为 `router-link`；末尾保留“退出登录”按钮。
- 输入校验：无外部输入。
- 鉴权：沿用登录态。

**依赖**：MOD-174。**外部依赖**：无。

### MOD-179 小程序“我的房屋”三 Tab

**职责**：页面宿主 + 三个面板，替代原单页堆叠。

**接口 IFC-398**（`miniprogram/pages/units/index.vue`）：

```js
// 页面状态
const tab = ref('identity') // 'identity' | 'appeal' | 'applications'
const housing = reactive({ summary, units, pending_review_count })
// 子面板契约（props / emits）
IdentityPane:  props { housing: Object, ownsAnyUnit: Boolean }
               emits ['refresh', 'open-applications']
AppealPane:    props { }
               emits ['submitted']
ResidentPane:  props { housing: Object }
               emits ['refresh']
```

- 顶部 Tab 条使用普通 `<view>` + `@click`，文案来自 `MP_HOUSING_TABS`（MOD-181）；默认 `identity`。
- `IdentityPane` 内含子 Tab：`身份与房屋` / `待我审批`；后者仅 `ownsAnyUnit` 时渲染，数据调用沿用 `api.residentApplicationsToReview()`。
- `AppealPane` 内含 `认证申诉` / `我的申诉` 子 Tab，提交成功后自动切到“我的申诉”。
- `ResidentPane` 包含发起申请与申请记录。
- 输入校验：Tab 值只接受三个常量；提交表单沿用既有校验（姓名 ≤64、证明 1~5 张等）。
- 鉴权：沿用 `http` 注入的 token 与后端权限。

**依赖**：MOD-181。**外部依赖**：`@dcloudio/uni-app`、既有 `utils/api.js`。

### MOD-180 小程序“我的”页分组

**职责**：把设置项按两组呈现，保留既有业务入口。

**接口 IFC-399**（`miniprogram/pages/me/index.vue`）：

- 渲染顺序：个人摘要卡片 → “个人设置”分组（个人资料、绑定手机、邮箱验证、账号注销）→ “系统设置”分组（界面风格）→ 财务报表卡片 → 业务入口（委员会成员可见“报销/备用金”）→ 退出登录。
- 入口映射：个人资料 → `/pages/profile-setup/index`；绑定手机 → `/pages/phone/index`；邮箱验证 → `/pages/email/index`；账号注销 → `/pages/cancel/index`；界面风格 → 页内主题选择。
- 输入校验：无新增输入；页面跳转目标为静态常量。
- 鉴权：沿用 `auth.isCommittee` 与登录态。
- 口径说明：小程序“个人设置”按 REQ-FUNC-313 为四项（个人资料、绑定手机、邮箱验证、账号注销），不含“设置密码”；C-363 与 REQ-NFUNC-062 约束的是同一功能在三端的名称一致，不要求三端功能集合完全相同（Web 保留设置密码，小程序不新增改密页）。

**依赖**：MOD-181、MOD-182（邮箱/注销页）。**外部依赖**：`store/theme.js`、`utils/api.js`。

### MOD-181 小程序菜单常量

**职责**：小程序侧唯一的菜单文案与分组来源。

**接口 IFC-400**（`miniprogram/utils/menu.js`）：

```js
export const MP_HOUSING_TABS = [
  { key: 'identity', label: '我的身份与房屋' },
  { key: 'appeal', label: '我的认证与申述' },
  { key: 'applications', label: '我的同住人申请' }
]
export const MP_USER_GROUPS = [
  { key: 'personal', label: '个人设置', items: [
    { key: 'profile', label: '个人资料', url: '/pages/profile-setup/index' },
    { key: 'phone', label: '绑定手机', url: '/pages/phone/index' },
    { key: 'email', label: '邮箱验证', url: '/pages/email/index' },
    { key: 'cancel', label: '账号注销', url: '/pages/cancel/index' }
  ] },
  { key: 'system', label: '系统设置', items: [
    { key: 'style', label: '界面风格', action: 'theme' }
  ] }
]
```

- 文案必须与 C-363 逐字一致；`REQ-NFUNC-062` 由前端与小程序测试逐项比对。
- 输入校验：静态常量；无外部输入。

**依赖**：无。**外部依赖**：无。

### MOD-182 小程序邮箱验证与账号注销页

**职责**：让“个人设置”中的邮箱验证、账号注销在小程序可达，复用现有后端接口。

**接口 IFC-401**（`miniprogram/utils/api.js` 新增）：

```js
sendMeCode: (purpose, target) => http.post('/me/codes', target ? { purpose, target } : { purpose }) // 已存在
verifyEmail: (email, code) => http.post('/me/email/verify', { email, code })
cancelAccount: (phone, code) => http.post('/me/cancel', { phone, code })
```

- `pages/email/index.vue`：输入邮箱 → 发送验证码（`purpose: 'EMAIL'`, `target: email`）→ 输入 6 位验证码 → 调用 `verifyEmail`；成功后返回“我的”。
- `pages/cancel/index.vue`：展示注销后果说明 → 发送验证码（`purpose: 'CANCEL'`）→ 输入验证码 → 调用 `cancelAccount`；成功后清空本地 token 并回到登录页。
- 输入校验：邮箱须匹配 `^[^@\s]+@[^@\s]+\.[^@\s]+$`；验证码 6 位数字；手机号取自 `auth.me.profile.phone`，缺失时提示先绑定手机。
- 鉴权：Bearer token 由既有 `utils/http.js` 注入；接口权限沿用后端 `IsMember`。
- 错误处理：沿用 `http` 的统一错误提示；409/400 显示后端文案，不新增错误码。

**依赖**：MOD-181、既有 `utils/http.js`。**外部依赖**：后端 `/me/codes`、`/me/email/verify`、`/me/cancel`（均已有，见 `frontend/src/shared/api.js:40,45` 与 `backend/tests/integration/test_auth_api.py:110-135`）。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-297 | US-299 | MOD-174 |
| REQ-FUNC-298 | US-299 | MOD-174 |
| REQ-FUNC-299 | US-299 | MOD-174、MOD-176 |
| REQ-FUNC-300 | US-299 | MOD-174 |
| REQ-FUNC-301 | US-300 | MOD-176 |
| REQ-FUNC-302 | US-300 | MOD-176 |
| REQ-FUNC-303 | US-301 | MOD-174、MOD-176 |
| REQ-FUNC-304 | US-299、US-309 | MOD-174、MOD-178、MOD-181 |
| REQ-FUNC-305 | US-302 | MOD-175 |
| REQ-FUNC-306 | US-302 | MOD-175 |
| REQ-FUNC-307 | US-302 | MOD-175 |
| REQ-FUNC-308 | US-302 | MOD-175 |
| REQ-FUNC-309 | US-302 | MOD-175 |
| REQ-FUNC-310 | US-302 | MOD-175 |
| REQ-FUNC-311 | US-303 | MOD-175 |
| REQ-FUNC-312 | US-304 | MOD-179、MOD-181 |
| REQ-FUNC-313 | US-305 | MOD-180、MOD-181、MOD-182 |
| REQ-FUNC-314 | US-306 | MOD-177 |
| REQ-FUNC-315 | US-307 | MOD-176、MOD-174 |
| REQ-NFUNC-061 | US-308 | MOD-175 |
| REQ-NFUNC-062 | US-309 | MOD-174、MOD-178、MOD-181 |
| REQ-NFUNC-063 | US-310 | MOD-176、MOD-177、MOD-179 |

## 依赖关系

- MOD-175 → MOD-174（读取 `USER_MENU_GROUPS`、`USER_MENU_TIMING`，IFC-393/IFC-396）
- MOD-176 → MOD-174（角标 key）、MOD-177（`initialTab`，IFC-395）
- MOD-177 → MOD-174（`LEGACY_UNITS_HASH`）
- MOD-178 → MOD-174（`USER_MENU_GROUPS`）
- MOD-179 → MOD-181（Tab 文案，IFC-400）
- MOD-180 → MOD-181（分组文案）、MOD-182（邮箱/注销页 URL）
- MOD-182 → MOD-181、既有 `utils/http.js`

已检查：无循环依赖；MOD-174 与 MOD-181 为无依赖的配置叶子。

## 数据迁移

无。本批次不涉及数据库字段、表、索引或数据回填；后端零改动。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 构建/验证 |
|---|---|---|
| Web 前端静态产物 | 菜单、身份页 Tab、下拉菜单、窄屏“我的”页变化 | `npm --prefix frontend run build`；测试 `npm --prefix frontend test` |
| Web 后端（gunicorn `ocap-backend`） | 无代码变更，不重启 | 无需构建；可复跑后端测试确认零回归 |
| 数据库（MySQL 192.168.31.98/ocap） | 无迁移 | 不执行 `migrate` |
| 微信小程序产物 | 页面拆分、分组、新增 2 页、`pages.json` 变化 | `npm --prefix miniprogram run build:mp-weixin`；测试 `npm --prefix miniprogram test` |
| nginx（8090） | 仅替换静态目录内容 | 由部署阶段处理，不在本次设计内 |

## 领域与外部依赖出处

本批次不新增或修改任何硬件、算法、闭源 API 调用；涉及的微信登录/手机号接口保持原样。因此本表不适用。

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| MOD-182 | 邮箱验证与账号注销复用后端既有接口 `/me/email/verify`、`/me/cancel` | `[CODE: frontend/src/shared/api.js:40,45]`、`[CODE: backend/tests/integration/test_auth_api.py:110-135]` |
| MOD-182 | 发送验证码接口 `/me/codes`（含 `purpose`/`target`） | `[CODE: miniprogram/utils/api.js:26]` |
