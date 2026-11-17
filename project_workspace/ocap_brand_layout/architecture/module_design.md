<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-17T00:02:47+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0 APPROVED）</file>
    <file>requirements/user_stories.md（1.0.0 APPROVED）</file>
    <file>architecture/architecture_design.md（0.1.0）</file>
    <file>../ocap_ui_theme/architecture/module_design.md（基线，MOD-023~029 / IFC-142~151）</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：品牌更名 Cyber@红枫岭 + Web 左侧导航布局 + 多分辨率自适应（INCREMENTAL）

> 编号接续全仓最大值：MOD-119 起、IFC-316 起（ADR 见 architecture_design.md，ADR-117 起）。
> 接口只写签名与契约，不含函数体。"新建/修改"均相对当前仓库。前端为 JavaScript（Vue 3 `<script setup>`），签名用 TypeScript 形式描述。
> **本批没有新增或修改任何后端 HTTP 接口、消息、CLI**（C-64）。所有 IFC 均为前端内部契约；它们调用的 HTTP 接口全部为既有接口，鉴权与校验沿用既有实现（见"对外接口与鉴权"小节）。
> 通用词：宽屏 = 视口 ≥768px，窄屏 = <768px（C-70，`frontend/src/shared/style.css:67,86`）。

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-119 | Web 品牌常量与网页标题 | 修改 `frontend/index.html`、`frontend/src/main.js`；新建 `frontend/src/brand/brand.js`、`frontend/src/brand/BrandMark.vue`、`frontend/src/brand/brand.css` | 产品名单一来源、品牌标识、品牌字体变量（占位）、网页标题 | REQ-FUNC-202、217（产品名）；REQ-NFUNC-041；US-207、223 | 无 |
| MOD-120 | 导航配置与共用布局件 | 新建 `frontend/src/layout/menus.js`、`labels.js`、`useBreakpoint.js`、`SideNav.vue`、`SubNavBar.vue`；修改 `frontend/src/shared/style.css` | 菜单配置、可见性/当前项/展开项解析、侧栏与二级切换条组件、布局骨架与自适应样式 | REQ-FUNC-205、208（配置）、209、210、211；REQ-NFUNC-038/039；US-210、211、216、217、225、229 | 无 |
| MOD-121 | 用户端布局与用户菜单 | 修改 `frontend/src/portal/PortalLayout.vue`；新建 `frontend/src/portal/PortalUserMenu.vue`；`BottomTabBar.vue` **不改** | 用户端左侧导航+右上角昵称菜单+窄屏切换条+底栏组合；侧栏角标 | REQ-FUNC-205、206、211、212、213、214(b)(c)、216；US-210、211、212、218、219、220、229、230 | MOD-119、MOD-120、MOD-123（`useHousingStore`，IFC-323） |
| MOD-122 | 个人中心拆分 | 修改 `frontend/src/portal/Me.vue`（改造为"我的"总览页）；新建 `frontend/src/portal/me/{MeStyle,MeIdentity,MeProfile,MePhone,MePassword,MeEmail,MeCancel}.vue`、`frontend/src/portal/me/useProfile.js` | 个人中心 7 个区块各成独立页；窄屏总览页 | REQ-FUNC-207、214(a)、215；US-213、220、221 | MOD-120（`PORTAL_USER_MENU`、`useIsWide`） |
| MOD-123 | 我的房屋拆分与状态仓库 | 修改 `frontend/src/portal/Units.vue`（改为分区宿主）、`frontend/src/portal/Home.vue`（快捷链接）；新建 `frontend/src/portal/units/{UnitsIdentity,UnitsReview,UnitsPick,UnitsAppeal,UnitsApplications,UnitsMyAppeals}.vue`、`frontend/src/stores/housing.js` | 6 个二级分区；申诉页自带房屋选择；侧栏角标数据源 | REQ-FUNC-208、215；US-214、221、230 | 无 |
| MOD-124 | 决议与报销二级分区 | 修改 `frontend/src/portal/Resolutions.vue`、`frontend/src/portal/Claims.vue` | 以 `section` 取代页内 `el-radio-group` | REQ-FUNC-208；US-215、230 | 无 |
| MOD-125 | 管理端布局与管理员菜单 | 修改 `frontend/src/admin/AdminLayout.vue`；新建 `frontend/src/admin/AdminUserMenu.vue`、`frontend/src/admin/adminSession.js`；修改 `frontend/src/admin/AdminLogin.vue`（仅保存账号名；品牌见 MOD-128）；删除 `frontend/src/theme/AdminThemeSwitcher.vue` | 左侧导航、窄屏抽屉、右上角管理员菜单（风格切换并入、退出） | REQ-FUNC-216、217、218、220、223；REQ-NFUNC-038；US-222、223、224、226、231 | MOD-119、MOD-120 |
| MOD-126 | 管理端页内分区二级 | 修改 `frontend/src/admin/{AdminFinance,AdminUsers,AdminAudit,AdminAiServices}.vue` | 4 页按 `section` 显示一个分区；去掉 `el-tabs` | REQ-FUNC-219、223；US-225、231 | 无 |
| MOD-127 | 路由 | 修改 `frontend/src/router/index.js` | 新增子路径、旧地址兼容、`/me` 宽窄分流 | REQ-FUNC-207、208、215、219；REQ-NFUNC-040；US-213、214、221、224 | MOD-120（`useBreakpoint`、`LEGACY_UNITS_HASH`）；组件由 MOD-122~126 提供 |
| MOD-128 | Web 登录/注册/管理端登录品牌设计 | 新建 `frontend/src/brand/AuthShell.vue`、`frontend/src/brand/art/{NeonArt,BentoArt,TerminalArt}.vue`、`frontend/src/brand/art/index.js`；修改 `frontend/src/portal/Login.vue`、`frontend/src/portal/Register.vue`、`frontend/src/admin/AdminLogin.vue`、`frontend/src/brand/brand.css` | 三套风格各一版配图 + 品牌头；表单字段与流程不变 | REQ-FUNC-201、204、221；REQ-NFUNC-041；US-207、209、227 | MOD-119 |
| MOD-129 | 小程序品牌与登录页 | 修改 `miniprogram/pages.json`、`miniprogram/pages/login/index.vue`、`themes/{neon,bento,terminal}.mp.css`；重新生成 `miniprogram/theme/generated/themes.scss` | 标题更名、登录页品牌头与三版纯 CSS 配图 | REQ-FUNC-203、222；REQ-NFUNC-041；US-208、228 | 无（沿用 `ThemeRoot`、`store/theme.js`） |
| MOD-130 | 风格体系适配 | 修改 `themes/{neon,bento,terminal}.theme.json`（`contrast`）、`themes/{neon,bento,terminal}.web.css`；重新生成 `frontend/src/theme/generated/{themes.css,registry.js}`、`miniprogram/theme/generated/{registry.js,themes.scss}` | 侧栏/切换条/用户菜单/登录页在三套风格下的结构性样式与对比度条目 | REQ-FUNC-216、204；REQ-NFUNC-039；US-222 | 无（`scripts/themes/*` 不改） |
| MOD-131 | 测试守护与既有用例同步 | 新建 `frontend/tests/{layout_menus,layout_nav,layout_router,user_menu,admin_session,brand,auth_shell,layout_css}.spec.js`、`miniprogram/tests/brand_login.spec.js`；修改既有用例（见"测试影响清单"） | 守护新规则；同步既有用例 | REQ-NFUNC-038/040/041；全部 US | MOD-119~130 |

## 模块详情

### MOD-119 Web 品牌常量与网页标题
- 职责：产品名只写一处；网页标题固定；品牌字体变量先占位。
- **IFC-328 品牌常量与品牌标识**（`frontend/src/brand/brand.js`、`BrandMark.vue`）
  ```ts
  export const BRAND_NAME: 'Cyber@红枫岭'                 // C-67：@ 半角、无空格
  export const ADMIN_BRAND_TITLE: 'Cyber@红枫岭 · 管理后台' // REQ-FUNC-217
  // BrandMark.vue：defineProps<{ size?: number }>()，默认 32；纯 SVG（圆角方块 + 枫叶折线 + @ 形电路环），
  // 颜色只用 currentColor 与 var(--accent)/var(--accent-2)，.vue 内不得出现颜色字面量；aria-hidden="true"
  ```
- **网页标题**：`frontend/index.html:6` 的 `<title>` 改为 `Cyber@红枫岭`（静态，用户端与管理端共用，路由切换不改 `document.title`，AC-207-03/04）。首屏风格脚本 `index.html:8-17` 不改。
- **品牌字体变量**（`frontend/src/brand/brand.css`，由 `main.js` 在 `./theme/generated/themes.css` 之后引入）：`:root { --brand-font: var(--font); }` 与 `.brand-font { font-family: var(--brand-font); }`。**用户确认字体前不写 `@font-face`、不写 `url()`**（ADR-123）；确认后加入 `@font-face { font-family: "OcapBrand"; src: url("./fonts/<file>.woff2") format("woff2"); font-display: swap; }` 并把变量改为 `"OcapBrand", var(--font)`。字体文件存放 `frontend/src/brand/fonts/`，随 OFL 许可证文本一并入库。
- **字体子集步骤（开发说明）**：输入 = 字符集 `Cyber@红枫岭管理后台登录注册手机号·` 与 ASCII 可见字符；输出 = 单个 `.woff2`；字体源文件不入库；子集工具为本机一次性使用的通用开源工具，不写入 `requirements.txt`/`package.json`；用户未确认字体前不执行本步骤。
- 依赖：无。外部依赖：无新增 npm 依赖。

### MOD-120 导航配置与共用布局件
- 职责：见 ADR-118、ADR-121。

**IFC-316 菜单配置类型与常量**（`frontend/src/layout/menus.js`）
```ts
type Audience = 'all' | 'committee'            // 'committee' = 业委会成员（auth.isCommittee，stores/auth.js:13）
type BadgeKey = 'pendingReview'                // 目前仅"待我审批的同住人申请"
interface NavLeaf {                            // 二级项
  key: string                                  // 全菜单内唯一，如 'units.review'
  label: string
  to: string                                   // 绝对路径；默认分区沿用旧路径
  badge?: BadgeKey
  activeOn?: readonly string[]                 // 额外高亮前缀（如编辑页 '/admin/content/posts'）
}
interface NavNode {                            // 一级项
  key: string                                  // 如 'units'
  label: string
  audience: Audience
  match: readonly string[]                     // 路径前缀；'/' 仅精确匹配（沿用 BottomTabBar.vue:31）
  to?: string                                  // 无二级项时必填；有 children 时必须缺省
  children?: readonly NavLeaf[]                // 与 to 二选一
}
interface UserMenuItem { key: string; label: string; to: string }

export const PORTAL_MENU: readonly NavNode[]        // 9 项，顺序见下表
export const PORTAL_USER_MENU: readonly UserMenuItem[]  // 7 项（"退出登录"为动作，不在配置内，由菜单组件固定追加为最后一项）
export const ADMIN_MENU: readonly NavNode[]         // 9 项
export const LEGACY_UNITS_HASH: Readonly<Record<string, string>>  // { '#review': '/units/review', '#appeal': '/units/appeal' }
```
用户端 `PORTAL_MENU`（Q-BL-22=B：信息公开末位）：

| 序 | key | 一级 label | audience | match | to / children（二级 label → to） |
|---|---|---|---|---|---|
| 1 | home | 主页 | all | `['/']` | `/` |
| 2 | units | 我的房屋 | all | `['/units']` | 我的身份与房屋 → `/units`；待我审批的同住人申请 → `/units/review`（badge `pendingReview`）；选择房屋 → `/units/pick`；认证申诉 → `/units/appeal`；我的同住人申请 → `/units/applications`；我的申诉 → `/units/appeals` |
| 3 | resolutions | 决议 | all | `['/resolutions']` | 公开决议 → `/resolutions`；我发起的 → `/resolutions/mine`；待我表决 → `/resolutions/todo` |
| 4 | polls | 投票/调查 | all | `['/polls']` | `/polls` |
| 5 | claims | 报销/备用金 | committee | `['/claims']` | 我提交的 → `/claims`；待我审批 → `/claims/todo` |
| 6 | income | 收入表 | committee | `['/income']` | `/income` |
| 7 | reports | 财务报表 | all | `['/reports']` | `/reports` |
| 8 | tasks | 待办 | committee | `['/tasks']` | `/tasks` |
| 9 | info | 信息公开 | all | `['/info']` | `/info` |

`PORTAL_USER_MENU`（Q-BL-11/12=A）：界面风格 `/me/style`、我的身份 `/me/identity`、个人资料 `/me/profile`、手机号 `/me/phone`、设置密码 `/me/password`、邮箱验证 `/me/email`、账号注销 `/me/cancel`。
管理端 `ADMIN_MENU`（Q-BL-26=B、27=A；audience 全为 `all`）：

| 序 | key | 一级 label | match | to / children |
|---|---|---|---|---|
| 1 | registry | 业主清册 | `['/admin/registry']` | `/admin/registry` |
| 2 | appeals | 申诉 | `['/admin/appeals']` | `/admin/appeals` |
| 3 | memberships | 房屋关系 | `['/admin/memberships']` | `/admin/memberships` |
| 4 | seats | 业委会席位 | `['/admin/seats']` | `/admin/seats` |
| 5 | flows | 审批流程 | `['/admin/flows']` | `/admin/flows` |
| 6 | finance | 财务 | `['/admin/finance']` | 报销/备用金记录 → `/admin/finance`；金额上限 → `/admin/finance/limit` |
| 7 | users | 账号 | `['/admin/users']` | 管理员账号 → `/admin/users`；注册用户 → `/admin/users/registered` |
| 8 | content | 内容管理 | `['/admin/content']` | 信息公开 → `/admin/content/posts`（`activeOn: ['/admin/content/posts']`，使编辑页高亮）；版式模板 → `/admin/content/styles`；素材库 → `/admin/content/media`；AI 服务·模型与生成服务 → `/admin/content/services`；AI 服务·提示词模板 → `/admin/content/services/prompts`；平台账户 → `/admin/content/platforms`；内容参数 → `/admin/content/settings` |
| 9 | audit | 审计/配置 | `['/admin/audit']` | 系统配置 → `/admin/audit`；审计日志 → `/admin/audit/logs` |

**IFC-317 纯函数**（同文件）
```ts
interface MenuContext { isCommittee: boolean }           // auth.me 未加载时为 false（AC-211-04，沿用 PortalLayout.vue:30-32 的先显示全员项）
interface ActiveResult { node: NavNode | null; leaf: NavLeaf | null }

export function isPathMatch(path: string, pattern: string): boolean
  // pattern === '/' → 仅 path === '/'；否则 path === pattern || path.startsWith(pattern + '/')
export function visibleMenu(menu: readonly NavNode[], ctx: MenuContext): NavNode[]
  // 过滤 audience==='committee' 且 !ctx.isCommittee 的一级项；不置灰（REQ-FUNC-211）
export function resolveActive(menu: readonly NavNode[], path: string): ActiveResult
  // node：按配置顺序第一个任一 match 命中的一级项；leaf：该 node.children 中 to === path，其次 activeOn 命中；详情页（如 /resolutions/12）leaf 为 null（AC-215-04）
export function nextOpenKey(menu: readonly NavNode[], path: string): string | null
  // node 存在且有 children → node.key，否则 null（ADR-118 展开规则②）
```
输入校验：`path` 为 `route.path` 字符串（不含 query/hash）；空串/非字符串返回 `{node:null, leaf:null}` / `null`，不抛错。

**IFC-330 显示名截断**（`frontend/src/layout/labels.js`）：`export function truncateLabel(text: unknown, max?: number): string`；`max` 缺省 12；非字符串/空 → `''`；按 Unicode 码点（`[...text]`）计数，超出则截取前 `max` 个并追加 `…`。

**IFC-320 断点工具**（`frontend/src/layout/useBreakpoint.js`）
```ts
export const WIDE_QUERY = '(min-width: 768px)'
export function isWideNow(): boolean            // typeof window.matchMedia !== 'function' → false（jsdom 缺省按窄屏，ADR-120）
export function useIsWide(): Readonly<Ref<boolean>>  // 监听 matchMedia change，卸载时移除监听
```

**IFC-318 `SideNav.vue`**
```ts
defineProps<{
  menu: readonly NavNode[]                      // 调用方已按 visibleMenu 过滤
  badges?: Readonly<Partial<Record<BadgeKey, number>>>   // >0 才显示角标
  ariaLabel?: string                            // 缺省 '主导航'
}>()
// 无 emits。当前路径取自 useRoute().path；内部状态 openKey: Ref<string | null>
```
行为契约（ADR-118）：初始 `openKey = nextOpenKey(menu, route.path)`；`watch(route.path)` 重新赋值同一规则；点击有 children 的一级项（`<button>`）只切换 `openKey`（已展开则置 null），不导航；点击无 children 的一级项直接导航；同时至多一个展开。
DOM 契约（供样式与测试）：根 `nav.side-nav[aria-label]`；一级无二级项 `a.side-item`；一级有二级项 `button.side-item.side-group-toggle[aria-expanded][aria-controls]`（含箭头 `span.side-caret`，无二级项不渲染箭头）；二级列表 `ul.side-sub#side-sub-<key>`（**收起时不渲染**，用 `v-if`）；二级项 `a.side-sub-item`；当前项加 `is-active` 并设 `aria-current="page"`；角标 `span.side-badge`。当前项除颜色外有 3px 左侧指示条与加粗（REQ-NFUNC-039），每个可点击项 `min-height: var(--hit-min)`。
键盘：一级按钮与链接均为原生可聚焦元素（Tab/Enter/Space）；焦点在二级项内按 Esc 收起所属一级并把焦点还给其按钮。
外部依赖：vue-router（沿用）。

**IFC-319 `SubNavBar.vue`**
```ts
defineProps<{ items: readonly NavLeaf[]; badges?: Readonly<Partial<Record<BadgeKey, number>>> }>()
```
DOM：`nav.sub-nav-bar[aria-label="分区切换"]`，子项 `a.sub-nav-item`（当前项 `is-active` + `aria-current="page"`），容器 `overflow-x: auto`、不换行；宽屏由 CSS 隐藏（`display:none`，不使用 JS）。

**IFC-331 布局样式契约**（`frontend/src/shared/style.css` 修改；只允许使用既有断点对 `@media (min-width: 768px)` / `(max-width: 767.98px)`，不新增其他媒体查询，C-70）
- 变量：`--side-w: clamp(192px, 14vw, 248px)`、`--content-pad: clamp(12px, 1.2vw, 32px)`、`--topbar-h: 56px`。
- 类：`.shell`（宽屏 `grid-template-columns: var(--side-w) minmax(0, 1fr)`，窄屏单列）、`.side`（`position: sticky; top: 0; height: 100vh; overflow-y: auto`，窄屏 `display:none`）、`.side-brand`、`.side-nav` 及 `.side-item/.side-sub/.side-sub-item/.side-badge/.side-caret`、`.shell-main`（`min-width: 0`）、`.layout-main`、`.sub-nav-bar`（窄屏 `display:flex`，宽屏 `display:none`）、`.user-menu-trigger`。
- 内容宽度：`.layout-main .page { max-width: none; width: 100%; margin: 0; padding: var(--content-pad); }`；**布局外的 `.page`（登录/注册）保持原 `max-width: 1180px`**（`style.css:7` 保留）。
- 自适应网格（宽屏块内修改，不新增断点）：`.res-grid` → `repeat(auto-fill, minmax(380px, 1fr))`；`.home-quick-grid` → `repeat(auto-fit, minmax(150px, 1fr))`；`.claim-form-wrap` 与 `.home-grid` 沿用现有列数规则（`home-grid` 的 Bento 4 列在 `themes/bento.web.css` 中，随容器变宽，不变形）。
- 必须保持不变的既有规则（既有用例依赖，`frontend/tests/qa_unit_theme.spec.js:208-215`）：`--hit-min: 44px`；`.el-button, .el-input__wrapper…{min-height: var(--hit-min)}`；`.tabbar{display:none;}`；`.tabbar a{…min-height: var(--hit-min)}`；`.form-actions-sticky` 在桌面无 `position`、仅在 `@media (max-width: 767.98px)` 内 sticky；`:focus-visible` 描边。
- 删除不再使用的 `.topnav`/`.topbar .topnav` 规则时，须同步 `frontend/tests/admin_theme.spec.js`（见测试影响清单）。

### MOD-121 用户端布局与用户菜单
- 职责：宽屏组合侧栏、顶栏右上角用户菜单、内容区；窄屏维持原形态（Q-BL-03=C）。
- **布局 DOM 契约**（`PortalLayout.vue`）：
  ```
  div.shell
    aside.side                       (窄屏 CSS 隐藏)
      router-link.side-brand to="/"  BrandMark + BRAND_NAME
      SideNav :menu="visibleMenu(PORTAL_MENU, {isCommittee: auth.isCommittee})" :badges="{ pendingReview: housing.pendingReviewCount }"
    div.shell-main
      header.topbar                  (沿用既有类；sticky)
        router-link.brand to="/"     (仅窄屏显示，CSS 控制；文案 BRAND_NAME)
        PortalUserMenu               (仅宽屏显示，CSS 控制)
      main.portal-main.layout-main
        SubNavBar v-if="active.node?.children" :items="active.node.children"   (仅窄屏显示，CSS 控制)
        router-view
    BottomTabBar                     (不改)
  ```
  `active = computed(() => resolveActive(PORTAL_MENU, route.path))`。`onMounted` 保持 `auth.fetchMe()`（沿用 `PortalLayout.vue:30-32`）并调用 `useHousingStore().refreshPendingBadge()`；进入 `/units*` 路由时再刷新一次。`logout` 逻辑迁入 `PortalUserMenu`。
- **IFC-321 `PortalUserMenu.vue`**
  ```ts
  // 无 props / emits。读取 useAuthStore().me?.profile?.nickname；useRouter()
  // 显示名 = truncateLabel(nickname || '业主', 12)；完整名放 title 与菜单头部（AC-212-04，Q-BL-18=A）
  // el-dropdown :trigger="['hover','click']"，菜单项 = PORTAL_USER_MENU 的 7 项 + 分隔线 + "退出登录"（共 8 项，退出登录最后，AC-212-02）
  // 选择菜单项 → router.push(item.to)；"退出登录" → await auth.logout(); router.replace('/login')（行为同 PortalLayout.vue:47-50）
  ```
  DOM：触发器 `button.user-menu-trigger`（≥44px 高）；菜单项为 `el-dropdown-item`（Esc 关闭由组件提供，ADR-122）。
- 样式（BottomTabBar 与 `.tabbar` 相关规则不变）：宽屏顶栏只放用户菜单（右对齐），窄屏顶栏只放品牌文字（与现状一致）。
- 内容区网格（决议卡片、首页入口等）按 IFC-331 自适应。
- 依赖：MOD-119（品牌）、MOD-120（配置/组件/样式）、MOD-123（`useHousingStore`）。外部依赖：Element Plus 2.14.8（沿用，不新增）。

### MOD-122 个人中心拆分
- 职责：`Me.vue` 的 8 个区块各成页；原功能与校验逐字保留（REQ-FUNC-207）。
- **页面清单**（每页只含对应区块，逻辑从 `Me.vue` 对应行段原样迁移）：

| 组件 | 路由 | 源区块（`Me.vue` 现行位置） |
|---|---|---|
| `me/MeStyle.vue` | `/me/style` | 界面风格 `:3-6`（继续使用 `@/theme/ThemePicker.vue`，保持"立即生效、记住选择"，AC-213-06） |
| `me/MeIdentity.vue` | `/me/identity` | 身份 `:8-16`（`auth.identitySummary`、`meApi.housing()`） |
| `me/MeProfile.vue` | `/me/profile` | 个人资料 `:29-47`（昵称/性别/生日、头像 jpg/png ≤2MB 校验 `:171-183`）；保存成功后调用 `auth.fetchMe()` 使右上角昵称即时更新（AC-212-05） |
| `me/MePhone.vue` | `/me/phone` | 绑定手机号 `:49-58` 与更换手机号 `:60-74` 合一（按 `profile.phone` 空/非空互斥，Q-BL-12=A；合并换令牌逻辑 `:209-225` 原样） |
| `me/MePassword.vue` | `/me/password` | 设置密码 `:76-82` |
| `me/MeEmail.vue` | `/me/email` | 邮箱验证 `:84-95` |
| `me/MeCancel.vue` | `/me/cancel` | 账号注销 `:97-106`（`confirmDanger('cancelAccount')` 二次确认不变，AC-213-05） |

- **IFC-325 共用资料加载**（`frontend/src/portal/me/useProfile.js`）
  ```ts
  interface Profile { nickname: string; gender: number; birthday: string | null; phone: string; email: string; avatar_url: string }
  export function useProfile(): { profile: Reactive<Profile>; loadProfile(): Promise<void> }
  // loadProfile 调用 meApi.profile()（既有，api.js），失败 ElMessage.error(errorText(e))（行为同 Me.vue:138-145）
  ```
- **`Me.vue` 总览页**（窄屏，Q-BL-23=A）：`defineProps` 无；渲染 `PORTAL_USER_MENU` 的 7 项为大按钮列表（每项 `min-height: var(--hit-min)`）+ 末尾"退出登录"；`watch(useIsWide(), (wide) => wide && router.replace('/me/profile'))`；退出逻辑同 IFC-321。
- 鉴权：全部在用户端布局路由下，沿用 `router.beforeEach`（未登录跳 `/login?redirect=…`，`router/index.js:58-64`）；输入校验：各页沿用原有前端预校验与服务端最终校验（头像类型/大小、验证码长度、密码规则），不新增校验。
- 依赖：MOD-120。

### MOD-123 我的房屋拆分与状态仓库
- 职责：见 ADR-127。
- **IFC-323 `useHousingStore`**（Pinia，`frontend/src/stores/housing.js`）
  ```ts
  interface HousingUnit { unit_id: number; specific_part: string; role: string; role_label: string; residents: Resident[]; /* 其余字段沿用 /me/housing 响应 */ }
  interface HousingState {
    housing: { summary: { code: string; label: string }; units: HousingUnit[]; pending_review_count: number }
    toReview: ResidentApplication[]
    myApplications: ResidentApplication[]
    myAppeals: Appeal[]
    prefillOwnerName: string                       // OWNER_NOT_MATCHED 时由认证页写入，申诉页读取并清空
  }
  // getters
  pendingReviewCount: number                        // toReview 已加载 → toReview.length；否则 housing.pending_review_count
  // actions（失败抛出，由调用组件 ElMessage.error(errorText(e))，与 Units.vue:121-127 行为一致）
  loadHousing(): Promise<void>                      // meApi.housing()
  loadLists(): Promise<void>                        // unitApi.residentApplicationsToReview / myResidentApplications / myAppeals，并行
  refresh(): Promise<void>                          // loadHousing + loadLists
  refreshPendingBadge(): Promise<void>              // 静默：仅当 useAuthStore().me 含 role 为 HEAD/OWNER 的房屋时调用 meApi.housing()；任何失败置 0，不提示（沿用 Home.vue:183-190）
  setPrefillOwnerName(name: string): void
  consumePrefillOwnerName(): string
  ```
- **宿主 `Units.vue`（IFC-324）**：`defineProps<{ section?: UnitsSection }>()`，`UnitsSection = 'identity'|'review'|'pick'|'appeal'|'applications'|'appeals'`，缺省 `identity`；按 `section` 渲染对应分区组件（`<component :is>` 映射表），自身不再含业务逻辑；`watch(() => props.section)` 无需重载（分区组件自行 `onMounted` 加载）。**同一组件实例在兄弟路由间复用**，分区组件用 `v-if`/`<component :key="section">` 保证切换时重新挂载。
- **分区组件**（逻辑从 `Units.vue` 原样迁移，行号为现行位置）：
  - `UnitsIdentity.vue`：我的身份与房屋 `:3-24`；`leave`/`removeResident` `:217-238`；确认框 `confirmDanger('leaveUnit'|'removeResident')` 不变。
  - `UnitsReview.vue`：待我审批 `:26-35`；`decideResident` `:207-215`，成功后 `store.refresh()` 使角标即时更新（AC-214-03）。
  - `UnitsPick.vue`：选择房屋 `:37-49`；`UnitCascader` 绑定本页 `pickedUnitId`；`certify` `:148-166`——`OWNER_NOT_MATCHED` 时 `store.setPrefillOwnerName(name)`、`ElMessage.warning('姓名与手机号未能通过核对，请上传产权证明提交申诉')`、`router.push('/units/appeal')`，不再 `scrollIntoView`；`applyResident` `:197-205`。
  - `UnitsAppeal.vue`：认证申诉 `:51-71`，**自带 `UnitCascader` 与 `appealUnitId`**（Q-BL-21=A）；"提交申诉"在未选房屋时 `disabled`（AC-214-04）；挂载时 `consumePrefillOwnerName()` 填入姓名；`uploadProof`/`submitAppeal` 逻辑与请求体（`unit_id`、`owner_name`、`proof_ids`）`:168-195` 不变。
  - `UnitsApplications.vue`：我的同住人申请 `:73-82`。
  - `UnitsMyAppeals.vue`：我的申诉 `:84-96`。
- **`Home.vue`**：`Home.vue:12` 的 `/units#review` 改为 `/units/review`（旧地址仍由路由重定向兜底，REQ-FUNC-215）；其余不变；`Home.vue:145-155` 快捷入口路径不变。
- 鉴权：沿用用户端路由守卫；输入校验：姓名 ≤64（`maxlength`）、产权证明 1~5 份（`:limit`、上传前判断）等沿用原页面，不改。
- 依赖：无。

### MOD-124 决议与报销二级分区
- **IFC-324（同一约定）**：`Resolutions.vue`：`defineProps<{ section?: 'public'|'mine'|'todo' }>()`（缺省 `public`）；原 `scope` ref（`:93`）改为 `computed(() => props.section)`；删除 `el-radio-group` 与 `@change="resetAndLoad"`（`:8-12`）；`watch(() => props.section, resetAndLoad)`，因为兄弟路由复用同一实例。卡片区标题按分区显示（公开决议/我发起的/待我表决）。"发起决议"按钮仍仅主任/副主任（`auth.isChairOrVice`，`:6`，AC-215-03）。
- `Claims.vue`：`defineProps<{ section?: 'mine'|'todo' }>()`（缺省 `mine`）；`scope`（`:178`）同上；删除 `el-radio-group`（`:12-15`）；"新建申请""备用金核销"按钮与 `v-if="auth.isCommittee"` 不变；`scope === 'mine'` 撤回按钮判断（`:33`）改读同一计算值。非业委会成员直接访问 `/claims` 的行为与改动前一致（AC-211-03，不新增路由权限）。
- 请求参数与路径不变：`resolutionApi.list(scope, params)`、`claimApi.list({scope,…})`（`frontend/src/shared/api.js` 不改）。

### MOD-125 管理端布局与管理员菜单
- **布局 DOM 契约**（`AdminLayout.vue`）：
  ```
  div.admin-shell.shell
    aside.side.admin-side
      router-link.side-brand to="/admin"  BrandMark + ADMIN_BRAND_TITLE
      SideNav :menu="ADMIN_MENU" aria-label="管理端导航"
    div.shell-main
      header.admin-bar
        button.admin-menu-btn (aria-label="打开导航"，仅窄屏显示，CSS 控制) → drawerOpen = true
        AdminUserMenu
      main.layout-main
        router-view
    el-drawer v-model="drawerOpen" direction="ltr" :with-header="false" size="min(280px, 85vw)"
      .side-brand + SideNav :menu="ADMIN_MENU"
  ```
  `watch(() => route.fullPath, () => (drawerOpen.value = false))`（点击二级项后自动关闭，AC-231-03）；`watch(useIsWide(), (w) => w && (drawerOpen.value = false))`（AC-231-04）。顶部不再有横排导航与"退出"按钮（AC-224-01）。
- **IFC-326 管理端会话与菜单**
  ```ts
  // frontend/src/admin/adminSession.js
  export const ADMIN_NAME_KEY: 'ocap_admin_name'
  export function saveAdminName(name: unknown): void   // 仅接受 trim 后 1~64 字符的字符串，否则忽略；localStorage 失败静默
  export function readAdminName(): string              // 管理端令牌（getToken(true)）为空时返回 ''；否则返回已存名或 ''
  export function clearAdminName(): void
  ```
  ```ts
  // frontend/src/admin/AdminUserMenu.vue —— 无 props / emits
  // 触发器显示 truncateLabel(readAdminName() || '管理员', 12)，title 为完整名（AC-226-05）
  // el-dropdown :trigger="['hover','click']"；菜单项依次：THEMES 的 3 项（来自 useAdminThemeStore().list，当前项显示"已选"）、分隔线、"退出登录"（共 4 项，AC-226-02；不含个人资料类项，C-69）
  // 选风格：await useAdminThemeStore().select(key)；失败 ElMessage.error('保存失败，已恢复原风格，请稍后重试')（文案与原 AdminThemeSwitcher.vue:38 一致，AC-226-03）
  // 退出：setToken('', true); clearAdminName(); useAdminThemeStore().resetSession(); router.replace('/admin/login')（沿用 AdminLayout.vue:44-48，并增加 clearAdminName）
  ```
  `AdminLogin.vue` 登录成功后在 `setToken` 之后调用 `saveAdminName(result.admin?.username)`（`admin.login` 已原样返回响应，`api.js:133` 不改，ADR-117）。
- 鉴权：管理端路由沿用 `meta.admin` 守卫，未持令牌跳 `/admin/login`（`router/index.js:60-62`，AC-224-04、AC-223-03）；风格偏好仍走 `/admin/me/theme`（既有，`adminStore.js`），设备键 `ocap_admin_theme` 不变（C-65/C-69）。输入校验：账号名仅作展示，经 Vue 文本插值转义，无富文本。
- 依赖：MOD-119、MOD-120。

### MOD-126 管理端页内分区二级
- **IFC-324（同一约定）**：

| 组件 | `section` 类型（缺省取首项） | 分区 → 内容（现行位置） |
|---|---|---|
| `AdminFinance.vue` | `'claims' \| 'limit'` | claims：筛选卡 + 记录表 `:3-18,27-40`；limit：金额上限卡 `:19-26`；`loadConfig`/`saveAmountMax` 仅在 limit 分区加载 |
| `AdminUsers.vue` | `'admins' \| 'registered'` | admins：管理员账号卡与"新建管理员"对话框 `:3-20,51-58`；registered：注册用户卡 `:22-49` |
| `AdminAudit.vue` | `'config' \| 'logs'` | config：系统配置 `:3-10`；logs：审计日志 `:11-36` |
| `AdminAiServices.vue` | `'models' \| 'prompts'` | models：`el-tab-pane "模型与生成服务"` 内容 `:5-28`；prompts：`"提示词模板"` `:29-45`；删除 `el-tabs`（`:4`、`:46`），页面标题随分区显示 |

  每页 `watch(() => props.section)`：分区变化时只触发该分区所需请求（兄弟路由复用同一实例）。请求路径、请求体、错误提示均不变（AC-225-05）。
- **表格宽度任务（ADR-121，R-02）**：在 1366×768 下核对 `AdminUsers.vue` 注册用户表（固定宽合计 1010 + `min-width` 120）、`AdminSeats.vue`（1040）、`AdminMemberships.vue`/`AdminAudit.vue`（760）。要求固定宽合计 ≤ 内容区宽 − 24px（含滚动条）；超出者把次要列改为 `min-width` 弹性列或压缩列宽，不改变列的含义与顺序。此项为开发任务，验收见 `layout_css.spec.js` 的静态宽度检查与 E2E 人工清单。
- 依赖：无。

### MOD-127 路由
- **IFC-322 路由表**（`frontend/src/router/index.js`；`beforeEach`/`afterEach` 守卫逻辑不变，`:58-77`）

用户端（布局路由 `/` 的子路由，需登录）：

| path | 组件 | `props` | 说明 |
|---|---|---|---|
| `''` | `Home.vue` | — | 不变 |
| `me` | `Me.vue`（总览） | — | `beforeEnter: () => isWideNow() ? { path: '/me/profile', replace: true } : true`（Q-BL-13/23） |
| `me/style`、`me/identity`、`me/profile`、`me/phone`、`me/password`、`me/email`、`me/cancel` | `portal/me/MeStyle` … `MeCancel` | — | 新增 7 条 |
| `units` | `Units.vue` | `{ section: 'identity' }` | `beforeEnter: (to) => LEGACY_UNITS_HASH[to.hash] ? { path: LEGACY_UNITS_HASH[to.hash], replace: true } : true`（REQ-FUNC-215，`/units#review`→`/units/review`） |
| `units/review`、`units/pick`、`units/appeal`、`units/applications`、`units/appeals` | `Units.vue` | `{ section: '<同名>' }` | 新增 5 条 |
| `resolutions` / `resolutions/mine` / `resolutions/todo` | `Resolutions.vue` | `{ section: 'public' / 'mine' / 'todo' }` | 后两条新增 |
| `resolutions/:id(\\d+)` | `ResolutionDetail.vue` | — | 原 `resolutions/:id` 加数字约束；静态路径先于参数路径声明 |
| `claims` / `claims/todo` | `Claims.vue` | `{ section: 'mine' / 'todo' }` | 后者新增 |
| `tasks`、`income`、`polls`、`polls/:id`、`reports`、`info`、`info/:id` | 原组件 | — | 不变 |

管理端（`/admin` 子路由，`meta.admin`）：原 15 条路径与组件**一字不变**；仅为 4 页补 `props` 并新增 4 条：`finance`→`{section:'claims'}`、`finance/limit`→`{section:'limit'}`；`users`→`{section:'admins'}`、`users/registered`→`{section:'registered'}`；`audit`→`{section:'config'}`、`audit/logs`→`{section:'logs'}`；`content/services`→`{section:'models'}`、`content/services/prompts`→`{section:'prompts'}`。`/admin` → `/admin/registry` 重定向与 `/:pathMatch(.*)*` → `/` 不变。

- 鉴权：沿用 `to.meta.public`/`to.meta.admin` 守卫（`router/index.js:58-64`）；新增路由均在原布局路由之下，继承其鉴权，无需新增 `meta`。
- 输入校验（路由参数）：`resolutions/:id(\\d+)` 限定数字；其余新增路径为静态字面量；不匹配者落入 `/:pathMatch(.*)*` → `/`（AC-210-04）。
- 依赖：MOD-120（`isWideNow`、`LEGACY_UNITS_HASH`）。

### MOD-128 Web 登录/注册/管理端登录品牌设计
- **IFC-327 `AuthShell.vue` 与配图注册表**
  ```ts
  // frontend/src/brand/AuthShell.vue
  defineProps<{ surface: 'portal' | 'admin'; subtitle: string }>()   // 默认插槽 = 现有表单卡片
  // 风格 key：surface==='portal' → useThemeStore().current；'admin' → useAdminThemeStore().current
  // frontend/src/brand/art/index.js
  export function artFor(themeKey: string): Component   // 'neon'|'bento'|'terminal'；其他/缺失 → BentoArt（与 DEFAULT_THEME 一致）
  ```
  DOM 契约：`div.auth-shell` → `div.auth-art`（`aria-hidden="true"`，内含当前风格的 SVG 组件）+ `div.auth-panel`（`BrandMark` + `h1.auth-brand.brand-font`（文案 `BRAND_NAME`）+ `p.auth-sub`（`subtitle`）+ 插槽）。宽屏左右分栏（配图栏占剩余宽度，表单栏 `minmax(360px, 480px)`），窄屏上下排列（配图条高 `clamp(120px, 28vw, 180px)`），配图永不覆盖表单（AC-209-04）；`.auth-shell` 不使用 `.page`，保证整页铺满且无横向滚动。**页面不渲染任何风格切换入口**（REQ-FUNC-078）。
- **各页改造**：`Login.vue` 外层改 `AuthShell surface="portal" subtitle="登录"`（`el-tabs` 三个登录方式、"手机号注册""微信扫码登录"、`done()` 里先 `reconcileAfterLogin` 再跳转的流程全部不变，`Login.vue:39-123`）；`Register.vue` → `subtitle="手机号注册"`；`AdminLogin.vue` → `surface="admin" subtitle="管理后台登录"`，保留"管理后台登录不支持'记住我'。"提示与 `admin.login` 调用。请求路径、字段、错误文案均不变（AC-209-06、AC-227-03）。
- **字体回退**：品牌文字使用 `.brand-font`（`font-family: var(--brand-font)`，MOD-119）；字体缺失或加载失败时回退 `var(--font)` 系统字体，不弹任何提示（AC-209-03）。
- **三版视觉元素清单与 AC-209-05 观察清单**（Web 登录页、注册页、管理端登录页共用同一组三个配图组件；管理端登录页的配图随 `ocap_admin_theme`，不读 `ocap_theme`，AC-227-02）。观察项编号：(1) 科技视觉元素（电路/网格线条｜数据流/粒子｜发光描边或光晕｜等宽/像素字形装饰，至少一类）；(2) 品牌名同屏；(3) 三套可识别为同一品牌；(4) 用户目视确认。

| 风格 | 背景（与色板一致，AC-209-01） | 构图与视觉元素（SVG，颜色全部取语义变量） | 满足的 (1) 类别 | (2)(3) 的做法 |
|---|---|---|---|---|
| neon 霓虹玻璃 | `--bg`（`#07080F`） | ① 底部透视网格地平线（线条收束到灭点）；② 三个半透明"玻璃"六边形/圆环叠放，描边发光（`filter: drop-shadow` 取 `--accent`/`--accent-2`）；③ 6~8 个粒子点沿两条弧线缓慢漂移（CSS 动画，`prefers-reduced-motion` 与 `data-perf=low` 下关闭，沿用 `themes.css` 既有规则）；④ 品牌名下方霓虹下划线 | 电路/网格线条、数据流/粒子、发光描边 | 品牌名 `h1.auth-brand` 置于配图栏左上，与 `BrandMark` 同屏 |
| bento 极光 Bento | `--bg`（`#F3F4FA`），配图栏底为 `--hero`（靛→紫→粉） | ① 5 块圆角"Bento"方块拼贴，其中 2 块内含芯片电路线条图标；② 极光渐变光斑（径向渐变，不叠半透明白层压在文字下）；③ 点阵（dot grid）；④ 一块"数据条"，内含等宽数字 `01 / 10` | 电路线条、发光/光晕、等宽字形装饰 | 品牌名用 `--on-hero` 置于 `--hero` 实底之上（对比度沿用 `bento.theme.json` 已有 Hero 条目），不与光斑重叠 |
| terminal 赛博终端 | `--bg`（`#0A0A0B`） | ① 终端窗口框（标题栏三点 + 边框发光，`--accent` 荧光绿描边）；② 窗内等宽命令行 `> boot cyber@hongfengling`、`> auth --mode secure`（装饰文本，`aria-hidden`）；③ 扫描线（重复线性渐变）与 CRT 网格；④ 方块光标闪烁（动画，`prefers-reduced-motion` 关闭）；⑤ 两列二进制"数据雨"式字符流（静态，减少性能压力） | 电路/网格线条、数据流/粒子、发光描边、等宽/像素字形装饰 | 品牌名以等宽粗体置于终端窗口标题位，与配图同屏 |

  三版共同点（观察项 (3)）：同一 `BrandMark`、同一品牌字体、品牌名位置一致（左上）、同一表单栏版式。
- 依赖：MOD-119。外部依赖：无新增（SVG 内联）。

### MOD-129 小程序品牌与登录页
- **IFC-329 小程序页面契约**
  - `miniprogram/pages.json`：`pages[0]`（`pages/index/index`）`navigationBarTitleText` 与 `globalStyle.navigationBarTitleText` 改为 `Cyber@红枫岭`（`pages.json:3,20`）；登录页自身 `navigationBarTitleText` 仍为"登录"；tabBar 4 项文案、`manifest.json:5` description、其余页面标题均不改（Q-BL-02=A）。
  - `miniprogram/pages/login/index.vue`：保持 `ThemeRoot` 根容器与全部登录逻辑（验证码/密码/微信一键登录、`afterLogin` 先对账再跳转，`:62-68`）不变；把标题 `业主委员会 · 登录`（`:4`）改为品牌头：
    ```
    ThemeRoot
      view.auth-page
        view.auth-art(aria-hidden)  ← 4 个空 view：.art-a .art-b .art-c .art-d（纯 CSS 绘制，无文本、无内联颜色）
        view.auth-brand
          view.brand-mark
          text.auth-brand-name   Cyber@红枫岭
          text.auth-brand-sub    登录
        view.card ...（既有表单卡片，原样）
    ```
    不渲染风格入口（REQ-FUNC-078 / AC-228-02）；字体使用 `--font` 系统字体，不加载远程字体（AC-228-01）；全部颜色取 CSS 变量。
- **三版 CSS 配图**（写入 `themes/<key>.mp.css`，选择器均以 `.theme-<key>` 开头；运行 `node scripts/themes/build.mjs` 重新生成 `miniprogram/theme/generated/themes.scss`；不设循环动画，沿用 ocap_ui_theme ADR-032）：

| 风格 | 元素（CSS：渐变/边框/阴影/定位，无 SVG） | (1) 类别 |
|---|---|---|
| neon | `.art-a` 网格（两层 `linear-gradient` 线条）、`.art-b` 圆环发光（`border` + `box-shadow`，`--accent`）、`.art-c` 玻璃方块（半透明纯色，**不使用 `backdrop-filter`**，ocap_ui_theme ADR-032）、`.art-d` 光点 | 网格线条、发光描边 |
| bento | `.art-a/.art-b/.art-c` 三块圆角方块（`--hero`/`--surface` 渐变）、`.art-d` 点阵（径向渐变重复） | 光晕、点阵网格 |
| terminal | `.art-a` 扫描线（`repeating-linear-gradient`）、`.art-b` 终端边框发光、`.art-c` 方块光标（静态）、`.art-d` 等宽字符块（用 `--mono` 字体的 `::before` 伪元素内容，仅装饰符号） | 网格线条、发光描边、等宽字形装饰 |

  WXSS 对 `repeating-linear-gradient`/多重 `box-shadow` 的真机支持属 OQ-B04（`[UNSOURCED]`）；降级规则：不支持的效果回退为 `--accent` 纯色块，保证观察项 (1) 至少保留一类。
- 依赖：无。外部依赖：uni-app（沿用现有版本，不新增）。

### MOD-130 风格体系适配
- 职责：只补结构性样式与对比度条目，不改风格 token 集合、不改 `schema.mjs`/`build.mjs`（ADR-126）。
- `themes/<key>.web.css`：补充 `.side`/`.side-nav`/`.side-item.is-active`/`.sub-nav-bar`/`.user-menu-trigger`/`.auth-shell` 的风格化规则。Bento：侧栏白底、当前项沿用黑色高亮胶囊（与 `themes/bento.web.css:12` 的 `.topnav a.is-active` 同款，改选择器为 `.side-item.is-active, .side-sub-item.is-active`）；管理端继续只在 `html[data-theme="bento"][data-surface="admin"]` 前缀内定义（`bento.web.css:52-`，管理端顶栏渐变 `.admin-bar` 保留）；neon：玻璃侧栏（半透明纯色，`data-perf=low` 已有降级）；terminal：等宽侧栏、当前项荧光描边。neon/terminal 的 web.css 不得出现 `.admin-bar`（`admin_theme.spec.js:47-50` 现行断言）。
- `themes/<key>.theme.json` 的 `contrast` 新增条目（`min` 由构建脚本实测、≥4.5，渐变逐停点建项）：① 侧栏次要文字（`muted`）/ 侧栏底；② 侧栏当前项文字（`accentText`）/ 当前项底的等效不透明色；③ 登录页品牌标题（`onHero`）/ `--hero` 各停点（bento 已有 `#4F46E5`、`#DB2777`、`#7C3AED` 三个停点条目可复用，neon/terminal 补各自停点）；④ 管理端顶栏用户菜单触发文字 / 顶栏底。
- 运行 `node scripts/themes/build.mjs --strict`，把生成物（`frontend/src/theme/generated/*`、`miniprogram/theme/generated/*`）一并提交。
- 依赖：无。

### MOD-131 测试守护与既有用例同步
- 新建用例位置遵守画像 P3：`frontend/tests/*.spec.js`、`miniprogram/tests/*.spec.js`。

| 文件 | 守护内容（对应 AC） |
|---|---|
| `frontend/tests/layout_menus.spec.js` | 配置条数与顺序：用户端业委会 9 项/非成员 6 项、管理端 9 项、内容管理 7 项、`PORTAL_USER_MENU` 7 项；`resolveActive` 对 `/resolutions/12`、`/info/5`、`/polls/3`、`/admin/content/posts/12`、`/admin/content/services/prompts`、`/me/profile`（无高亮）；`nextOpenKey`；`truncateLabel`（AC-210-02、211-01/02、212-04、215-04、224-02、225-02） |
| `frontend/tests/layout_nav.spec.js` | `SideNav`：默认全收起、点击展开/再点收起且不导航、同时只展开一个、直达自动展开并高亮二级项、无二级项无箭头、角标显示/隐藏、`aria-expanded`/`aria-current`；`SubNavBar` 项与高亮（AC-216-01~04、217-01/02、214-03、230-01/02/04） |
| `frontend/tests/layout_router.spec.js` | 路由表：旧路径全部可解析（用户端、管理端 15 条）；`/units#review`→`/units/review`；`/me` 在 `matchMedia` 桩为宽屏时→`/me/profile`、窄屏停在总览；`resolutions/mine` 不被 `:id(\\d+)` 吞掉；未知地址→`/`；管理端无令牌→`/admin/login`；`props.section` 正确（AC-215、220-05、221-01~03、224-03/04） |
| `frontend/tests/user_menu.spec.js` | `PortalUserMenu`：8 项顺序、退出登录最后、昵称为空显示"业主"、超长截断+title、退出清登录态跳 `/login`；`AdminUserMenu`：4 项、"已选"标记、账号名缺省"管理员"、选择失败回滚并提示、退出清令牌与账号名（AC-212、226） |
| `frontend/tests/admin_session.spec.js` | `adminSession`：保存/读取/清除；无令牌时 `readAdminName()` 为空；非法值被忽略（AC-226-01/05） |
| `frontend/tests/brand.spec.js` | `index.html` 标题；`BRAND_NAME` 字面；REQ-NFUNC-041 的 9 处残留旧名为 0（含小程序文件，经读文件而非渲染）；`.vue`/`.css`/`index.html` 中无 CDN 域名（`fonts.googleapis`、`fonts.gstatic`、`cdn.`）与 `http(s)://` 字体 `url()`；`brand.css` 含 `font-display: swap` 与回退变量（AC-207-03/04、209-03、223-02） |
| `frontend/tests/auth_shell.spec.js` | `artFor` 三 key 返回三个不同组件、未知 key 回退 bento；Login/Register/AdminLogin 渲染品牌名与配图；登录页无 `[role=radio]`、无风格入口；三套组件文件无颜色字面量（AC-209-01/02、227-01/02） |
| `frontend/tests/layout_css.spec.js` | 静态样式断言（jsdom 不计算布局）：`.layout-main .page` 取消最大宽度；`--side-w`/`--content-pad` 使用 `clamp(`；`style.css` 与各 `web.css` 的 `@media` 条件只含 `767.98px`/`768px`/`prefers-reduced-motion`（无新断点，C-70）；`res-grid`/`home-quick-grid` 使用 `auto-fill/auto-fit`；各管理端表格固定列宽合计 ≤ 1110（R-02）（REQ-NFUNC-038 的静态部分） |
| `miniprogram/tests/brand_login.spec.js` | `pages.json` 两处标题；登录页含"Cyber@红枫岭"、无旧名、3 种风格各 `theme-<key>` 类下渲染且无风格入口、无内联颜色、三个登录入口仍在（AC-208-01~03、228-01~03） |

- **REQ-NFUNC-038 的真实视口度量**（1366×768、1920×1080、2560×1440、3840×2160 下的横向滚动、占用率、侧栏可见性）jsdom 无法度量，列入 E2E/人工清单；GROUP_D 在测试环境 `https://ai-freeark.xin/ocap/` 经浏览器完成（画像 P4-1 范围内，只读浏览，无写入）。

#### 测试影响清单（既有用例，`git grep` 定位；基线：前端 vitest 181/181、小程序 75/75 以实跑为准，基线零新增失败）

| 既有用例文件:位置 | 受影响原因 | 需同步的范围 |
|---|---|---|
| `frontend/tests/admin_theme.spec.js:11,58-67,151-166` | `AdminLayout` 不再有 `.admin-bar .topnav a`（14 项）与 `.admin-bar .brand`、风格切换入口 `.admin-theme-trigger` | 重写为：`.side-nav` 内 9 个一级、`.side-brand` 文案、`.admin-bar .user-menu-trigger` 存在、当前项高亮；CSS 断言（`.admin-bar .topnav a.is-active/:hover` 次序）改为侧栏对应规则 |
| `frontend/tests/admin_theme.spec.js:72-74` | `bento.web.css` 中 `.topnav`/`.tabbar a.is-active` 原样断言；`.topnav` 规则随用户端导航迁移被替换 | `.tabbar a.is-active` 部分保留；`.topnav` 断言改为 `.side-item.is-active` |
| `frontend/tests/qa_int_theme.spec.js:236-262` | `PortalLayout` 顶部 `.topnav a.is-active` / `.topnav` 存在 | 改为 `.side-nav .is-active`；"底部标签栏 5 项"断言（`.tabbar a`）保持 |
| `frontend/tests/qa_int_theme.spec.js:171-205` | `Me` 页含风格区块 | 改为挂载 `portal/me/MeStyle.vue` |
| `frontend/tests/qa_unit_theme.spec.js:259-266` | "只有 `Me.vue` 引用 ThemePicker"、`AdminLayout` 含 `AdminThemeSwitcher`、`AdminThemeSwitcher.vue` 含 `admin-theme-trigger` | 改为"只有 `portal/me/MeStyle.vue` 引用 ThemePicker"；管理端断言改为 `AdminLayout` 含 `AdminUserMenu`、`AdminUserMenu.vue` 含风格项 |
| `frontend/tests/qa_unit_theme.spec.js:268-275` | 统计 `import('@/(portal\|admin)/(\w+).vue')` 个数 17/17 | 新增组件放在 `portal/me/`、`portal/units/` 子目录，正则 `\w+` 不匹配含 `/` 的路径，计数预期不变；仍须实跑确认 |
| `frontend/tests/qa_e2e_pages.spec.js:24,132-139` | 底栏"我的"点击后 `currentRoute.path` 期望 `/me` | jsdom 无 `matchMedia` 时 `isWideNow()` 为 false，路径仍为 `/me`，**预期无需改**；需实跑确认；`PORTAL` 路径清单可补新增路径 |
| `frontend/tests/qa_e2e_extend.spec.js:53-70`、`qa_e2e_theme.spec.js:123,148,157,179` | 在 `/me` 上找 `[role=radio]` 风格选择器并点击 | 改为 `/me/style` |
| `frontend/tests/product_review_ui.spec.js:277-292` | 顶部导航 `nav.topnav` 文本含/不含"报销/备用金""收入表""待办""个人中心" | 改为 `nav.side-nav` 文本；"个人中心"不再在导航中 |
| `frontend/tests/product_review_ui.spec.js:65-188,576` | `Units.vue` 单页全部行为；`:576` 读取 `portal/Units.vue` 文件内容 | 按分区重指向 `portal/units/*.vue`（或给 `Units` 传 `section`）；认证失败转申诉的断言改为"写入仓库预填姓名并跳 `/units/appeal`"；`:576` 的文件扫描范围加入新文件 |
| `frontend/tests/product_review_ui.spec.js:190-266`、`pages.spec.js:231-258`（TC-WEB-028/029）、`qa_int_theme.spec.js:84-87` | `Me.vue` 的资料/头像/手机号绑定更换 | 重指向 `me/MeProfile.vue`、`me/MePhone.vue`；`qa_int_theme:84-87`（未登录访问 `/me` 的重定向）不变 |
| `frontend/tests/owner_auth_v2.spec.js:15,52-` | `Units.vue` 姓名核对与申诉 | 重指向 `UnitsPick.vue`、`UnitsAppeal.vue`；`OWNER_NOT_MATCHED` 后不再保留已选房屋（OQ-B03） |
| `frontend/tests/product_review_ui.spec.js:300-345`、`ui_blocks.spec.js:77-157`、`pages.spec.js`（Resolutions/Claims） | `Resolutions`/`Claims` 页内 `scope` 状态 | 默认分区（`public`/`mine`）与旧行为一致；需要其他分区的用例传 `section`；若有点击 radio 的断言则改写 |
| `frontend/tests/admin_users.spec.js:12,59`、`product_review_ui.spec.js:435-455`（AdminUsers）、`:507`（AdminFinance）、`product_review_rework2.spec.js:25-26,83,106,224-226`（AdminAudit/AdminFinance） | 管理端 4 页分区后默认只显示首个分区 | 注册用户表用例传 `section: 'registered'`；审计日志表用例传 `section: 'logs'`；金额上限用例传 `section: 'limit'`；`rework2:224-226` 的"映射被页面使用"文件内容断言不变，须实跑确认 |
| `frontend/tests/theme.spec.js:141,181-197` | `ThemePicker` 3 项、`BottomTabBar` 5 项与 `href` | `BottomTabBar` 不改，预期无需改 |
| `frontend/tests/qa_unit_theme.spec.js:185-215` | `style.css` 结构（`.tabbar`、`.form-actions-sticky`、`:focus-visible`、`--hit-min`） | 新增 CSS 须保持这些规则（见 IFC-331），预期无需改 |
| `frontend/tests/theme.spec.js`（`.vue` 颜色字面量扫描，ocap_ui_theme ADR-029） | 新增 `.vue` 文件 | 新增组件（含三个 SVG 配图）不得含十六进制/`rgb()`/`hsl()` 字面量 |
| `miniprogram/tests/qa_int_theme.spec.js:65-80`、`qa_e2e_theme.spec.js:7,51-70`、`pages.spec.js:10,250-280`（登录） | 登录页改版 | 断言多为 `ThemeRoot` 类与按钮文本，预期无需改；新增的 `.auth-art` 不得含文本或内联颜色（`qa_e2e_pages.spec.js:26`） |

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-201 | US-207 | MOD-128、MOD-119 |
| REQ-FUNC-202 | US-207 | MOD-119 |
| REQ-FUNC-203 | US-208 | MOD-129 |
| REQ-FUNC-204 | US-209 | MOD-128、MOD-119、MOD-130 |
| REQ-FUNC-205 | US-210、229 | MOD-120、MOD-121、MOD-127 |
| REQ-FUNC-206 | US-212 | MOD-121、MOD-122 |
| REQ-FUNC-207 | US-213 | MOD-122、MOD-127 |
| REQ-FUNC-208 | US-214、215、230 | MOD-123、MOD-124、MOD-120、MOD-121、MOD-127 |
| REQ-FUNC-209 | US-216 | MOD-120 |
| REQ-FUNC-210 | US-217 | MOD-120 |
| REQ-FUNC-211 | US-211 | MOD-120、MOD-121 |
| REQ-FUNC-212 | US-218 | MOD-120（样式）、MOD-121、MOD-125、MOD-130 |
| REQ-FUNC-213 | US-219 | MOD-120（样式）、MOD-121、MOD-125、MOD-126 |
| REQ-FUNC-214 | US-220、230 | MOD-121、MOD-122、MOD-127、MOD-120 |
| REQ-FUNC-215 | US-221、220 | MOD-127、MOD-122、MOD-123 |
| REQ-FUNC-216 | US-222 | MOD-130、MOD-121、MOD-125 |
| REQ-FUNC-217 | US-223 | MOD-125、MOD-119 |
| REQ-FUNC-218 | US-224 | MOD-125、MOD-120、MOD-127 |
| REQ-FUNC-219 | US-225 | MOD-126、MOD-120、MOD-127 |
| REQ-FUNC-220 | US-226 | MOD-125 |
| REQ-FUNC-221 | US-227 | MOD-128 |
| REQ-FUNC-222 | US-228 | MOD-129 |
| REQ-FUNC-223 | US-231 | MOD-125、MOD-126、MOD-120 |
| REQ-NFUNC-038 | US-218、219、231 | MOD-120、MOD-121、MOD-125、MOD-126、MOD-131 |
| REQ-NFUNC-039 | — | MOD-120、MOD-121、MOD-125 |
| REQ-NFUNC-040 | 全部 | MOD-127（旧路径）、MOD-131（回归） |
| REQ-NFUNC-041 | US-207、208、223 | MOD-119、MOD-121、MOD-125、MOD-128、MOD-129、MOD-131 |

## 依赖关系

- MOD-121 → MOD-119（IFC-328）、MOD-120（IFC-316/317/318/319/330/331）、MOD-123（IFC-323）
- MOD-122 → MOD-120（IFC-316、IFC-320）
- MOD-125 → MOD-119（IFC-328）、MOD-120（IFC-316/317/318/330）
- MOD-127 → MOD-120（IFC-316 的 `LEGACY_UNITS_HASH`、IFC-320）；路由引用 MOD-122~126 的组件（构建期引用，非运行期调用环）
- MOD-128 → MOD-119（IFC-328）
- MOD-123、MOD-124、MOD-126、MOD-129、MOD-130 无上游依赖
- MOD-131 → 以上全部（仅测试）

已检查：无循环依赖（依赖方向为 119/120/123/124/126/129/130 ← 121/122/125/128 ← 127）。`MOD-123` 的 `useHousingStore` 被 `MOD-121` 读取，反向无调用。

## 对外接口与鉴权

本批没有新增或修改 HTTP 接口、消息或 CLI。前端运行时用到的既有 HTTP 接口（路径、方法、字段、权限均不变，`frontend/src/shared/api.js` 与 `miniprogram/utils/api.js` **不改**）：

| 用途 | 既有接口 | 鉴权 | 出处 |
|---|---|---|---|
| 用户昵称/身份/房屋 | `GET /me`、`GET /me/profile`、`GET /me/housing` | `IsMember`（沿用） | `frontend/src/stores/auth.js:29`、`Me.vue:140,149` |
| 个人中心各页的写操作 | `PATCH /me/profile`、`/me/codes`、`/me/phone/bind`、`/me/phone/change`、`/me/password`、`/me/email*`、`/me/cancel` | `IsMember`（沿用） | `Me.vue:162,198,229,238,249,259,270,281` 调用的 `meApi.*` |
| 我的房屋各分区 | `unitApi.certify/createAppeal/residentApplications*/myAppeals/…` | `IsMember`（沿用） | `Units.vue:131-134,152,184,199,209,220,231` |
| 决议、报销列表 | `resolutionApi.list(scope,…)`、`claimApi.list({scope,…})` | 沿用（决议公开/成员权限，报销为业委会成员） | `Resolutions.vue:95-97`、`Claims.vue:180-182` |
| 管理端登录与偏好 | `POST /admin/auth/login`（响应含 `admin.username`）、`GET/PUT /admin/me/theme` | 登录无需令牌（沿用）；偏好 `IsAdmin`（沿用） | `api.js:133`、`backend/apps/accounts/views.py:364`、`frontend/src/theme/adminStore.js` |
| 风格偏好（用户端/小程序） | `GET/PUT /me/theme` | `IsMember`（沿用 ocap_ui_theme IFC-142/143） | `frontend/src/theme/store.js` |

输入校验：新增前端状态均来自路由（静态路径或 `(\\d+)` 限定）或本地存储（`ocap_admin_name` 只接受 1~64 字符字符串，展示时由 Vue 文本插值转义）；不新增表单字段与服务端输入。

## 数据迁移

无。

- 无数据库字段、表、索引变化，无 Django 迁移；后端代码零改动，因此不涉及画像 P6/P8 对迁移的约束。
- 新增的浏览器本地存储键 `ocap_admin_name`（管理员账号名，ADR-117）不是迁移：缺失时前端显示"管理员"，不影响既有会话；既有键（`ocap_theme`、`ocap_admin_theme`、`ocap_token`、`ocap_admin_token`）不变，旧版本用户升级后无需任何数据处理。
- 可逆性：回滚前端构建产物即可恢复旧界面，无数据残留风险。

## 受影响的运行单元 / 构建

| 单元 | 动作 | 依据 |
|---|---|---|
| systemd `ocap-backend`（gunicorn）、MySQL 库 `ocap` | **无变化**：不迁移、不重启 | 纯前端（C-64） |
| nginx（站点 `ocap`，8090） | 无需改动、无需重启；部署后核对 `.woff2` 响应 MIME（OQ-B05，仅当采用随包字体） | 仅替换静态文件 |
| Web 前端静态文件 | **重新构建** `npm run build -- --base=/ocap/`（`frontend/`，画像 P4）并替换 `/home/yangyang/ocap/web` | 布局、路由、页面、品牌、样式全部变更 |
| 小程序 | **重新构建** `npm run build:mp-weixin`（`miniprogram/`）；发布流程不在画像 P7 | `pages.json`、登录页、生成样式变更 |
| 风格构建脚本 `scripts/themes/build.mjs` | 开发机/CI 运行 `--strict` 并提交生成物；不在目标机运行 | `themes/*` 与生成物变更 |
| 前端/小程序测试 | `frontend/`：`npx vitest run --passWithNoTests`；`miniprogram/`：同（画像 P4） | 零新增失败 |
| 定时任务、Freeark 服务/端口/目录/库 | 无影响 | — |
| 固件/比特流 | 不适用 | — |

## 领域与外部依赖出处

画像 P11-1/P11-2 为"无"；P11-3 的外部 API（微信/阿里云/邮件/内容发布与 AI 服务）与本次改动无关，不调用、不修改。下表登记本设计引用的**既有代码事实与平台能力**：

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| IFC-322 / ADR-117 | 管理端登录响应含 `admin.username` | [CODE: backend/apps/accounts/views.py:364] |
| ADR-117 | 前端 `admin.login` 原样返回响应 | [CODE: frontend/src/shared/api.js:133] |
| IFC-321/326 / ADR-122 | `el-dropdown` 的 `trigger` 类型为 `Arrayable<"click"\|"contextmenu"\|"hover">`（Element Plus 2.14.8） | [CODE: frontend/node_modules/element-plus/es/components/dropdown/src/dropdown.d.ts:24-26；版本见 frontend/node_modules/element-plus/package.json] |
| ADR-118 | `el-menu` 具备 `uniqueOpened`；`themes.css` 中无 `--el-menu-*` 映射 | [CODE: frontend/node_modules/element-plus/es/components/menu/src/menu.d.ts:14]；`git grep -c "el-menu" frontend/src/theme/generated/themes.css` = 0 |
| IFC-317 | 用户端当前项解析沿用前缀规则 | [CODE: frontend/src/portal/PortalLayout.vue:45]、[CODE: frontend/src/portal/BottomTabBar.vue:31] |
| IFC-323 | `/me/housing` 返回 `pending_review_count` | [CODE: frontend/src/portal/Home.vue:186] |
| ADR-127 | `UnitCascader` 初值不回显所选楼栋/单元 | [CODE: frontend/src/portal/parts/UnitCascader.vue:29,39-40] |
| IFC-329 | 小程序首页/全局导航栏标题位置 | [CODE: miniprogram/pages.json:3,20] |
| MOD-129 | WXSS 对 `repeating-linear-gradient`、多重 `box-shadow`、SVG 背景的支持 | [UNSOURCED]，OQ-B04，设计不依赖 SVG，开发验证 |
| MOD-128/ADR-123 | 候选字体许可证 | [WEB: https://github.com/atelier-anchor/smiley-sans，2026-11-16]（OFL-1.1）；[WEB: https://github.com/google/fonts/tree/main/ofl/orbitron，2026-11-16]（目录含 OFL.txt）；详见 tech_stack.md |
| ADR-121 | 各管理端表格固定列宽合计 | 本地统计（`awk` 汇总各 `.vue` 中 `el-table-column` 的 `width`，2026-11-16）：AdminUsers 1490（两表）、AdminSeats 1040、AdminMemberships/AdminAudit 760 |
