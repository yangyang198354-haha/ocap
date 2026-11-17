<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-17T08:53:00+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0 APPROVED）</file>
    <file>requirements/user_stories.md（1.0.0 APPROVED）</file>
    <file>architecture/architecture_design.md（1.0.0 APPROVED）</file>
    <file>architecture/module_design.md（1.0.0 APPROVED）</file>
    <file>architecture/tech_stack.md（1.0.0 APPROVED）</file>
    <file>testing/integration_test_report.md（0.1.0，DEF-001/002）</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：品牌更名 Cyber@红枫岭 + Web 左侧导航布局 + 多分辨率自适应（INCREMENTAL，GROUP_C）

> 路径均相对仓库根；后端、`frontend/src/shared/api.js`、`miniprogram/utils/api.js` 零改动（ADR-117）。
> GR-B-001 条件 C1 生效：本组只改产品代码，**未新建、未修改** `frontend/tests/**`、`miniprogram/tests/**` 任何文件；MOD-131 全部归 GROUP_D。

## 1.1.0 修订（GROUP_C-003，缺陷回流 1/2，GR-D-001 FAIL）

只改产品代码 2 个文件，`frontend/tests/**`、`miniprogram/tests/**` 零改动，未执行任何 git 操作。

| DEF | 级别 | 位置 | 修改 |
|---|---|---|---|
| DEF-001 | MINOR | `frontend/src/brand/art/index.js:10`（`artFor`） | 查表前加 `Object.hasOwn(ARTS, themeKey)`，原型链键名（`__proto__`/`constructor`/`toString`/`hasOwnProperty`）回退 BentoArt（IFC-327） |
| DEF-002 | MAJOR | `frontend/src/portal/PortalLayout.vue:48-50`（`onMounted`） | 条件由 `!auth.me` 改为 `!auth.me \|\| !auth.me.identities`：登录后 `auth.me` 只是登录响应简要对象（无 identities）时也先 `fetchMe()`，再 `refreshPendingBadge()`，角标按真实身份刷新 |

- DEF-002 取"refresh 前先补全身份"方案：没有新增 watcher、没有轮询；`/me/housing` 仍是挂载时 1 次 + 进入 `/units*` 各 1 次，GR-C-001 记录的额外请求未加重。代价：刚登录进入首页时多一次 `GET /me`（与 Home.vue 自己的 `fetchMe` 并发，仅登录后首次挂载发生），`[ASSUMPTION]` 可接受。
- 追溯表 AC-209-02、AC-214-03 两行已更新；改动清单表本身不变（文件集合未变）。
- 实跑：前端 vitest 37 文件 / **438/438** 通过（含 TC-INT-874、TC-INT-914）；小程序 16 文件 / **119/119**；`npm run build -- --base=/ocap/` 通过。

## 0.2.0 修订（GROUP_C-002，GR-C-001-F01：品牌字体接入，CR-002 关闭）

- 用户选 A 得意黑 Smiley Sans；素材由 PM 准备（子集 woff2，字体内部名已改 OcapBrand，OFL 保留字体名条款）。本次新增 `frontend/src/brand/fonts/{OcapBrand-subset.woff2,OFL.txt,README.md}`（woff2/OFL sha256 与 PM 素材一致），修改 `frontend/src/brand/brand.css`（`@font-face` + `--brand-font: "OcapBrand", var(--font)`）。其余产品代码、测试文件零改动。
- 新增文件合计 3 个（新建总数 31 → 34）；修改文件数不变（brand.css 在 0.1.0 中已是新建文件）。
- 实跑：前端构建通过且 `dist/assets/OcapBrand-subset-c41YCxaj.woff2` 带哈希（12044 B，CSS 内 `url(/ocap/assets/...)`）；前端 vitest 仍为 39 失败 / 242 通过 / 281，失败文件与每文件条数与 0.1.0 完全一致（下表）；小程序 104/104。

## 实现概览

- 模块：MOD-119 ~ MOD-130 共 12 个全部实现；MOD-131（测试守护与既有用例同步）按 C1 不在本组范围，状态 SKIPPED-BY-CONDITION，交 GROUP_D。
- 文件（`git status` 实数）：新建 31 个（含 `frontend/src/brand/*`、`layout/*`、`portal/me/*`、`portal/units/*`、`stores/housing.js`、`admin/AdminUserMenu.vue`、`admin/adminSession.js`、`portal/PortalUserMenu.vue`）；修改 32 个（含风格定义 `themes/*` 8 个，及重新生成的 `themes.css`、`themes.scss` 2 个生成物）；删除 1 个（`frontend/src/theme/AdminThemeSwitcher.vue`，经 `git rm` 已暂存删除，未提交）。文件清单与行数统计见 code_review_report 摘要。
- 顺序（module_design 依赖拓扑）：先无依赖的 119/120/123/124/126/129/130，再 121/122/125/128，最后 127；末尾重新运行 `scripts/themes/build.mjs --strict` 并构建/测试。
- 基线（实跑，2026-11-17，改动前）：前端 vitest **281/281**（26 个文件）、小程序 **104/104**（15 个文件）。**与调用指令和画像 P4 写的 181/181、75/75 不一致**（画像数字已过期，建议 PM 修订画像 P4），后端本批零改动、未运行（本机无 Django）。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-119 | `frontend/src/brand/brand.js`、`BrandMark.vue`、`brand.css` | 新建 | — | L | `BRAND_NAME`/`ADMIN_BRAND_TITLE` 单一来源；SVG 品牌标识（无颜色字面量）；0.1.0 为 `--brand-font: var(--font)` 占位；**0.2.0 接入字体**：`@font-face "OcapBrand"`（`url('./fonts/OcapBrand-subset.woff2')`、`font-display: swap`），`--brand-font: "OcapBrand", var(--font)` | DONE |
| 1a | MOD-119 | `frontend/src/brand/fonts/{OcapBrand-subset.woff2,OFL.txt,README.md}` | 新建（0.2.0） | 1 | L | 子集字体、许可证全文、来源/子集字符/改名原因/重新生成步骤说明 | DONE |
| 2 | MOD-119 | `frontend/index.html`、`frontend/src/main.js` | 修改 | 1 | L | `<title>` 改为 Cyber@红枫岭；`main.js` 在 themes.css 之后引入 brand.css | DONE |
| 3 | MOD-120 | `frontend/src/layout/menus.js`、`labels.js`、`useBreakpoint.js` | 新建 | — | M | 类型化菜单配置（用户端 9、用户菜单 7、管理端 9/内容管理 7）、`isPathMatch/visibleMenu/resolveActive/nextOpenKey`、`truncateLabel`、`isWideNow/useIsWide` | DONE |
| 4 | MOD-120 | `frontend/src/layout/SideNav.vue`、`SubNavBar.vue` | 新建 | 3 | M | 侧栏（点击一级只展开不导航、同时一个、直达自动展开、Esc 收起并还焦点）、窄屏切换条 | DONE |
| 5 | MOD-120 | `frontend/src/shared/style.css` | 修改 | 3,4 | M | `--side-w/--content-pad/--topbar-h`（clamp）、`.shell/.side/.side-*`、`.layout-main .page` 取消最大宽、`.res-grid`/`.home-quick-grid` 自适应、`.sub-nav-bar`、`.user-menu-trigger`、`.auth-*`；仅用既有 767.98px/768px 媒体查询；保留 `--hit-min`、`.tabbar`、`.form-actions-sticky`、`:focus-visible` | DONE |
| 6 | MOD-123 | `frontend/src/stores/housing.js` | 新建 | — | M | Pinia 仓库：四份数据 + `pendingReviewCount` + `refreshPendingBadge`（静默，失败置 0）+ 预填姓名 | DONE |
| 7 | MOD-123 | `frontend/src/portal/Units.vue`（宿主）、`portal/units/{UnitsIdentity,UnitsReview,UnitsPick,UnitsAppeal,UnitsApplications,UnitsMyAppeals}.vue` | 修改+新建 | 6 | H | 6 个分区组件，逻辑自原 Units.vue 迁移；申诉页自带 UnitCascader；认证失败只带姓名转 `/units/appeal` | DONE |
| 8 | MOD-123 | `frontend/src/portal/Home.vue` | 修改 | 7 | L | `/units#review` 改 `/units/review`（一处） | DONE |
| 9 | MOD-124 | `frontend/src/portal/Resolutions.vue`、`Claims.vue` | 修改 | — | M | `section` prop 取代 `el-radio-group`；`watch(scope, resetAndLoad)` | DONE |
| 10 | MOD-126 | `frontend/src/admin/AdminFinance.vue`、`AdminUsers.vue`、`AdminAudit.vue`、`AdminAiServices.vue` | 修改 | — | M | `section` prop；每分区只请求自己的数据；去掉 `el-tabs` | DONE |
| 11 | MOD-126 | `frontend/src/admin/AdminSeats.vue`、`AdminMemberships.vue` | 修改 | — | L | 次要列由 `width` 改 `min-width`（OQ-B07，见下） | DONE |
| 12 | MOD-122 | `frontend/src/portal/me/{MeStyle,MeIdentity,MeProfile,MePhone,MePassword,MeEmail,MeCancel}.vue`、`useProfile.js`；`portal/Me.vue` | 新建+修改 | 3 | M | 个人中心 7 页；`Me.vue` 改为窄屏"我的"总览页（宽屏监听后 `replace('/me/profile')`） | DONE |
| 13 | MOD-121 | `frontend/src/portal/PortalUserMenu.vue`、`PortalLayout.vue` | 新建+修改 | 1,3,4,6 | M | 左侧导航 + 右上角昵称下拉（`el-dropdown` trigger `['hover','click']`）+ 窄屏切换条 + 底栏（`BottomTabBar.vue` 未改） | DONE |
| 14 | MOD-125 | `frontend/src/admin/adminSession.js`、`AdminUserMenu.vue`、`AdminLayout.vue`、`AdminLogin.vue`；删除 `theme/AdminThemeSwitcher.vue` | 新建+修改+删除 | 1,3,4 | M | 左侧导航、窄屏 `el-drawer`、右上角管理员菜单（3 风格项+退出）、账号名本机缓存 | DONE |
| 15 | MOD-127 | `frontend/src/router/index.js` | 修改 | 3,7,9,10,12 | M | 新增子路径、`units` hash 兼容、`/me` 宽窄分流、`resolutions/:id(\d+)`；同一组件的多路由只 import 一次（保持 `qa_unit_theme` 的 17/17 计数口径） | DONE |
| 16 | MOD-128 | `frontend/src/brand/AuthShell.vue`、`brand/art/{index.js,NeonArt,BentoArt,TerminalArt}.vue`；`portal/Login.vue`、`Register.vue`、`admin/AdminLogin.vue` | 新建+修改 | 1 | H | 三套风格各一版 SVG 配图；配图不含文本节点（装饰字符经 CSS 伪元素输出），保证三风格页面文本一致 | DONE |
| 17 | MOD-129 | `miniprogram/pages.json`、`pages/login/index.vue` | 修改 | — | M | 首页与全局标题改名；登录页品牌头 + `.auth-art`（4 个空 view） | DONE |
| 18 | MOD-129/130 | `themes/{neon,bento,terminal}.mp.css` | 修改 | 17 | M | 三版纯 CSS 配图（不含 backdrop-filter、不设循环动画） | DONE |
| 19 | MOD-130 | `themes/{neon,bento,terminal}.web.css`、`*.theme.json` | 修改 | 5 | M | 侧栏/切换条/用户菜单/登录页结构样式；`contrast` 新增条目 | DONE |
| 20 | MOD-130 | `frontend/src/theme/generated/themes.css`、`miniprogram/theme/generated/themes.scss` | 重新生成 | 18,19 | L | `node scripts/themes/build.mjs --strict`（退出码 0）；`--check --strict` 退出码 0；`registry.js` 无变化 | DONE |
| 21 | MOD-131 | `frontend/tests/*`、`miniprogram/tests/*` | — | — | — | **本组不做**（C1）；GROUP_D 负责新建 9 个 spec 与既有 spec 同步 | SKIPPED-BY-CONDITION |

## 需求追溯

状态口径：DONE = 产品代码已实现；"视口度量待 D" = CSS 已按口径实现，jsdom 不能度量，真实视口验收归 GROUP_D 人工清单（module_design MOD-131 末段）。PARTIAL 均写明原因。自验证引用：自检 = 本组临时自检 spec（已删除，见 code_review_report"自验证结果"）。

| US | AC | 实现位置（文件:函数/组件，含调用方客户端） | 状态 | 说明 |
|---|---|---|---|---|
| US-207 | AC-207-01 | `frontend/src/brand/AuthShell.vue:7`（h1 取 `BRAND_NAME`）；`portal/Login.vue:2`；`brand/brand.js:2` | DONE | 自检：/login 标题=Cyber@红枫岭，无"业主委员会 · 登录"；三种登录方式与流程代码未改 |
| US-207 | AC-207-02 | `portal/Register.vue:2`（`AuthShell subtitle="手机号注册"`） | DONE | "注册并登录""返回登录"保留 |
| US-207 | AC-207-03 | `frontend/index.html:6`；`router/index.js` 未设置 `document.title` | DONE | 静态标题 |
| US-207 | AC-207-04 | 同上（用户端与管理端共用 index.html）；`admin/AdminLogin.vue:2` | DONE | 令牌行为不变 |
| US-208 | AC-208-01 | `miniprogram/pages/login/index.vue:11-13`（`auth-brand-name`=Cyber@红枫岭） | DONE | 三个登录入口代码未改；小程序 vitest 104/104 |
| US-208 | AC-208-02 | `miniprogram/pages.json:3`、`:20` | DONE | tabBar 与其余标题未改 |
| US-208 | AC-208-03 | `miniprogram/pages/login/index.vue`（提示语原样保留） | DONE | |
| US-209 | AC-209-01 | `brand/art/NeonArt.vue`、`BentoArt.vue`、`TerminalArt.vue`；`brand/art/index.js:artFor`；`brand/AuthShell.vue:themeKey/art` | DONE | 背景取 `--bg`；三版构图不同；字体见 AC-209-03 说明 |
| US-209 | AC-209-02 | `brand/art/index.js:artFor`（`Object.hasOwn` 白名单，未知/缺失/原型链键名回退 bento，DEF-001 1.1.0 修复）；`AuthShell.vue` 无风格入口 | DONE | 自检：无 `[role=radio]`；TC-INT-862/874 通过 |
| US-209 | AC-209-03 | `brand/brand.css`（`@font-face OcapBrand` + `--brand-font: "OcapBrand", var(--font)`）；`brand/fonts/OcapBrand-subset.woff2` | DONE | 0.2.0：品牌字体随包分发、无 CDN/外网地址；`font-display: swap`，文件加载失败或子集外字符回退 `var(--font)` 系统栈；构建产物 `dist/assets/OcapBrand-subset-c41YCxaj.woff2`。回退行为的浏览器实测（断网/删文件）jsdom 不能度量，归 GROUP_D 人工清单 |
| US-209 | AC-209-04 | `shared/style.css:.auth-shell/.auth-art/.auth-panel` 及窄屏块 | DONE | 视口度量待 D；窄屏配图条高 `clamp(120px,28vw,180px)`，配图与表单不重叠 |
| US-209 | AC-209-05 | 三个 art 组件（清单 (1)(2)(3) 的实现），`themes/*.web.css` `.auth-brand` | PARTIAL | (1)(2)(3) 已按设计实现；品牌字体已接入（0.2.0，得意黑子集 OcapBrand）；(4) 须用户目视确认（验收人为用户，代码无法替代），故仍标 PARTIAL |
| US-209 | AC-209-06 | `Login.vue`/`Register.vue` 脚本部分未改 | DONE | 请求路径与字段不变 |
| US-210 | AC-210-01 | `portal/PortalLayout.vue:2-9`（`SideNav`+品牌位）；`layout/menus.js:4-37` | DONE | 自检：业委会成员 9 项；顶栏无横排链接与退出 |
| US-210 | AC-210-02 | `layout/menus.js:resolveActive`；`SideNav.vue:active` | DONE | 自检：`/resolutions/12` 仅"决议"高亮；`/info/5` 仅"信息公开" |
| US-210 | AC-210-03 | `SideNav.vue`（`router-link`）；`router/index.js` 旧路径不变 | DONE | |
| US-210 | AC-210-04 | `router/index.js` 末条 `/:pathMatch(.*)*`→`/`；`resolutions/:id(\d+)` | DONE | 自检：`/nope`、`/resolutions/abc`→`/` |
| US-211 | AC-211-01 | `layout/menus.js:visibleMenu`；`PortalLayout.vue:menu` | DONE | 自检：非成员 6 项，无置灰 |
| US-211 | AC-211-02 | 同上 | DONE | |
| US-211 | AC-211-03 | `router/index.js:claims`（未新增权限）；`Claims.vue` 行为未改 | DONE | |
| US-211 | AC-211-04 | `PortalLayout.vue:onMounted` 先 `visibleMenu`（`isCommittee` 为 false） | DONE | 自检：/me 未返回前 6 项 |
| US-212 | AC-212-01 | `portal/PortalUserMenu.vue:3`（`trigger=['hover','click']`） | DONE | |
| US-212 | AC-212-02 | `PortalUserMenu.vue:12-13`；`layout/menus.js:39-47` | DONE | 8 项，退出登录最后 |
| US-212 | AC-212-03 | `PortalUserMenu.vue:onCommand`（`auth.logout`→`/login`，并 `$reset` 房屋仓库） | DONE | |
| US-212 | AC-212-04 | `PortalUserMenu.vue:fullName/displayName`；`layout/labels.js:truncateLabel` | DONE | 空→"业主"，>12 码点截断+title |
| US-212 | AC-212-05 | `portal/me/MeProfile.vue:47`（保存成功后 `auth.fetchMe()`） | DONE | |
| US-213 | AC-213-01 | `router/index.js:28-34`（7 条 `me/*`）；`portal/me/*.vue` | DONE | |
| US-213 | AC-213-02 | `me/MeProfile.vue:checkAvatar`（逻辑自 Me.vue 原样迁移） | DONE | 文案不变 |
| US-213 | AC-213-03 | `me/MePhone.vue`（`profile.phone` 空/非空互斥） | DONE | |
| US-213 | AC-213-04 | `me/MePassword.vue:savePassword` | DONE | 服务端文案原样展示 |
| US-213 | AC-213-05 | `me/MeCancel.vue:cancelAccount`（`confirmDanger('cancelAccount')`） | DONE | |
| US-213 | AC-213-06 | `me/MeStyle.vue`（`ThemePicker` 原样） | DONE | |
| US-214 | AC-214-01 | `layout/menus.js:6-16`；`portal/units/*` | DONE | 自检：展开 6 项 |
| US-214 | AC-214-02 | `portal/Units.vue`（`section`→分区组件，`:key`）；`router/index.js:36-44` | DONE | |
| US-214 | AC-214-03 | `stores/housing.js:pendingReviewCount`；`PortalLayout.vue:SideNav :badges`、`onMounted`（me 缺 identities 先 `fetchMe`，DEF-002 1.1.0 修复）；`units/UnitsReview.vue:decideResident`（`store.refresh`） | DONE | 自检：角标 2；>0 才显示；刚登录场景 TC-INT-914 通过 |
| US-214 | AC-214-04 | `units/UnitsAppeal.vue:22`（`:disabled="!appealUnitId"`，自带 `UnitCascader`） | DONE | 自检：未选房屋时禁用；请求体字段不变 |
| US-214 | AC-214-05 | `units/UnitsPick.vue:certify` | DONE | 请求体 `{unit_id,name}` 不变 |
| US-215 | AC-215-01 | `portal/Resolutions.vue:89-93`；`layout/menus.js:resolutions` | DONE | 自检：无 `el-radio-group`，3 个二级项 |
| US-215 | AC-215-02 | `portal/Claims.vue:175-177`；`layout/menus.js:claims` | DONE | 新建申请/备用金核销按钮保持 |
| US-215 | AC-215-03 | `Resolutions.vue:6`（`auth.isChairOrVice` 未改） | DONE | |
| US-215 | AC-215-04 | `menus.js:resolveActive`（leaf=null）；`SideNav.vue:openKey` | DONE | 自检：详情页决议展开、二级无高亮 |
| US-216 | AC-216-01 | `SideNav.vue:openKey=nextOpenKey`（主页为 null） | DONE | |
| US-216 | AC-216-02 | `SideNav.vue:toggle` | DONE | 点击不导航 |
| US-216 | AC-216-03 | 同上（单个 `openKey`） | DONE | 自检 |
| US-216 | AC-216-04 | `SideNav.vue:openKey` 初值与 `watch(route.path)` | DONE | |
| US-217 | AC-217-01 | `SideNav.vue:15-22`（无 children 渲染 `a.side-item`，无 `side-caret`） | DONE | |
| US-217 | AC-217-02 | `menus.js:resolveActive`（`/polls/:id` 命中 `/polls`） | DONE | |
| US-218 | AC-218-01 | `style.css:94 .layout-main .page{max-width:none}`、`--content-pad`、`--side-w` | DONE | 视口度量待 D |
| US-218 | AC-218-02 | `style.css:237 .res-grid auto-fill minmax(380px,1fr)` | DONE | 视口度量待 D |
| US-218 | AC-218-03 | `style.css:94` | DONE | |
| US-218 | AC-218-04 | 同 AC-218-01（相对单位） | DONE | 视口度量待 D |
| US-219 | AC-219-01 | `style.css:.side-item min-height var(--hit-min)`、`.side{overflow-y:auto}` | DONE | 静态估算：9 项 ≈ 56+9×46=470px<768；视口度量待 D |
| US-219 | AC-219-02 | `style.css:.layout-main .page`、`.res-grid`；管理端表格宽度见 OQ-B07 | DONE | 视口度量待 D |
| US-219 | AC-219-03 | `style.css:.user-menu-trigger`、`.topbar-user` | DONE | 视口度量待 D |
| US-220 | AC-220-01 | `style.css:137-146`（窄屏隐藏 `.side`/`.topbar-user`）；`BottomTabBar.vue` 未改 | DONE | 自检：窄屏底栏 5 项 |
| US-220 | AC-220-02 | `portal/Me.vue`（7 项 + 退出登录，`.me-overview-item min-height var(--hit-min)`） | DONE | 自检：8 个条目 |
| US-220 | AC-220-03 | `Me.vue:logoutNow`；`router-link` 到各页 | DONE | |
| US-220 | AC-220-04 | `style.css` 仅 767.98px/768px 对；`.tabbar{display:none!important}`（≥768） | DONE | 视口度量待 D |
| US-220 | AC-220-05 | `router/index.js:27`（`beforeEnter` 宽屏→`/me/profile`）；`Me.vue:30` | DONE | 自检：窄屏停在总览，桩宽屏→个人资料 |
| US-221 | AC-221-01 | `router/index.js:27` | DONE | |
| US-221 | AC-221-02 | `portal/Home.vue:12`（`/units/review`）；`router/index.js:37-40` | DONE | 自检：`/units#review`→`/units/review` |
| US-221 | AC-221-03 | `router.beforeEach` 未改（未登录→`/login?redirect=/me`） | DONE | |
| US-222 | AC-222-01 | `themes/*.theme.json` `contrast` 新增条目；`themes/*.web.css` | DONE | `build.mjs --strict` 通过（对比度由脚本校验，≥4.5） |
| US-222 | AC-222-02 | `me/MeStyle.vue`（`ThemePicker`/`theme/store.js` 未改） | DONE | |
| US-222 | AC-222-03 | `theme/adminStore.js` 未改；`AdminUserMenu.vue:pickTheme` | DONE | |
| US-222 | AC-222-04 | `themes/bento.web.css` 管理端段；`contrast` | DONE | |
| US-223 | AC-223-01 | `admin/AdminLayout.vue:5-8`（`ADMIN_BRAND_TITLE`，链 `/admin`） | DONE | 自检：品牌位文本一致 |
| US-223 | AC-223-02 | 9 处：`index.html:6`、`AuthShell.vue:7`（登录/注册/管理端登录）、`PortalLayout.vue:6,13`、`AdminLayout.vue:6`、`pages.json:3,20`、`login/index.vue:12` | DONE | `git grep "业主委员会 · 登录\|业主委员会 · 管理后台"` 于产品代码为 0（测试文件中的旧断言由 D 同步） |
| US-223 | AC-223-03 | `router.beforeEach` 未改 | DONE | |
| US-224 | AC-224-01 | `layout/menus.js:ADMIN_MENU`；`AdminLayout.vue:8` | DONE | 自检：9 项；无 `.topnav` |
| US-224 | AC-224-02 | `menus.js` `content.posts.activeOn` | DONE | 单元自检 |
| US-224 | AC-224-03 | `menus.js:ADMIN_MENU` 无 children 项 | DONE | |
| US-224 | AC-224-04 | `router/index.js:62-84`（原 15 条路径不变，新增 4 条） | DONE | |
| US-225 | AC-225-01 | `AdminLayout.vue`+`SideNav.vue` | DONE | |
| US-225 | AC-225-02 | `menus.js:ADMIN_MENU.content`（7 项）；`AdminAiServices.vue`（无 `el-tabs`） | DONE | 自检 |
| US-225 | AC-225-03 | `AdminFinance.vue:isLimit`、`AdminAudit.vue:isLogs` | DONE | 自检：limit 页无记录表 |
| US-225 | AC-225-04 | `SideNav.vue:openKey`（`/admin/users/registered`→账号展开+注册用户高亮） | DONE | 自检 |
| US-225 | AC-225-05 | `AdminFinance.vue:saveAmountMax` 未改 | DONE | |
| US-226 | AC-226-01 | `admin/AdminUserMenu.vue:fullName`；`adminSession.js`；`AdminLogin.vue:33` | DONE | 自检：刷新后读 localStorage 仍显示 |
| US-226 | AC-226-02 | `AdminUserMenu.vue:13-22` | DONE | 自检：4 项，当前项"已选" |
| US-226 | AC-226-03 | `AdminUserMenu.vue:pickTheme`（失败文案原样） | DONE | |
| US-226 | AC-226-04 | `AdminUserMenu.vue:logout` | DONE | 自检：清令牌与账号名并跳 `/admin/login` |
| US-226 | AC-226-05 | `AdminUserMenu.vue:fullName`（缺省"管理员"）；`truncateLabel` | DONE | 自检 |
| US-227 | AC-227-01 | `admin/AdminLogin.vue:2`（`AuthShell surface="admin"`） | DONE | 观察清单同 AC-209-05（(4) 待用户） |
| US-227 | AC-227-02 | `AuthShell.vue:themeKey`（admin 读 `useAdminThemeStore`） | DONE | 自检：读 `ocap_admin_theme` 不读 `ocap_theme` |
| US-227 | AC-227-03 | `AdminLogin.vue` 脚本与提示语未改 | DONE | |
| US-227 | AC-227-04 | `style.css:.auth-*` | DONE | 视口度量待 D |
| US-228 | AC-228-01 | `miniprogram/pages/login/index.vue:3-8,114-120`；`themes/*.mp.css` | PARTIAL | 三版 CSS 配图已实现并重新生成 `themes.scss`；WXSS 对渐变/阴影的真机表现未核实（OQ-B04，无微信开发者工具，`build:mp-weixin` 基线亦失败） |
| US-228 | AC-228-02 | `miniprogram/store/theme.js`（未改，缺省 bento）；登录页无风格入口 | DONE | |
| US-228 | AC-228-03 | 登录逻辑代码未改 | DONE | 小程序 vitest 104/104 |
| US-229 | AC-229-01 | `menus.js:PORTAL_MENU[8]`（info，末位） | DONE | |
| US-229 | AC-229-02 | `menus.js:resolveActive` | DONE | 自检 |
| US-229 | AC-229-03 | `Home.vue` 快捷入口未改 | DONE | |
| US-230 | AC-230-01 | `layout/SubNavBar.vue`；`PortalLayout.vue:15`；`style.css:.sub-nav-bar` | DONE | 自检：/units/appeals 窄屏 6 项，当前项高亮 |
| US-230 | AC-230-02 | 同上（决议 3、报销 2） | DONE | |
| US-230 | AC-230-03 | `style.css`（768 断点 CSS 显隐） | DONE | 视口度量待 D |
| US-230 | AC-230-04 | `Home.vue:12` → `/units/review`；`SubNavBar` 角标 | DONE | |
| US-231 | AC-231-01 | `style.css:.layout-main .page`；`AdminLayout.vue` | DONE | 视口度量待 D |
| US-231 | AC-231-02 | `AdminLayout.vue`；OQ-B07 表格宽度 | DONE | 视口度量待 D |
| US-231 | AC-231-03 | `AdminLayout.vue:13-16,25-31`（`.admin-menu-btn`+`el-drawer`，`watch(route.fullPath)` 关闭） | DONE | 抽屉在 jsdom 的焦点/滚动锁定由 D 覆盖 |
| US-231 | AC-231-04 | `AdminLayout.vue:watch(isWide)` | DONE | |

汇总：101 条 AC；DONE 99；PARTIAL 2（AC-209-05(4) 待用户目视确认，字体已接入；AC-228-01 WXSS 真机未核实）；MISSING 0。Must Have 范围内 PARTIAL 仅 AC-209-05（需用户目视），已按 US-209 AC 文本"验收人为用户"处理。

## 迁移

无（纯前端；后端零改动，无 Django 迁移，满足画像 P6/P8）。新增浏览器本地存储键 `ocap_admin_name`（缺失时显示"管理员"，不影响既有会话）。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| `AdminUserMenu.vue` 触发器同时带 `admin-theme-trigger` 类名 | IFC-326（只写 `.user-menu-trigger`） | 既有用例 `qa_e2e_pages.spec.js` TC-E2E-105（不在测试影响清单的行范围内）按 `.admin-theme-trigger` 判断"管理端有风格入口"；保留该类名让它无需改动即可通过 | 无样式影响（`.admin-theme-trigger` 的样式规则已删除）；GROUP_D 若改选择器可去掉 [DEVIATION，已在 AdminUserMenu.vue 文件头注释说明] |
| 配图中的装饰字符不用 SVG `<text>`，改为 `foreignObject` + CSS `content: attr()` | module_design MOD-128 视觉元素清单（装饰命令行文本） | 既有 TC-E2E-104 要求同一页面在三套风格下 `textContent` 一致；SVG `<text>` 会进入文本 | 视觉元素不变；装饰字符不进入可访问性树（配图本就 `aria-hidden`） |
| `MeEmail.vue` 增加只读行"当前邮箱：…"并在挂载时调用 `meApi.profile()` | MOD-122（原样迁移） | 原 Me.vue 邮箱区块与资料区块同页，可见当前邮箱；拆页后"发送验证码到当前邮箱"缺少上下文 | 多 1 次 `GET /me/profile`；无新接口 [ASSUMPTION] |
| `UnitsPick.vue` 说明文字"请改用下方产权申诉"改为"请改用「认证申诉」" | MOD-123（原样迁移） | 申诉已是独立二级页，"下方"不再成立 | 既有 `owner_auth_v2.spec.js:152` 对旧文案有断言，该文件在测试影响清单内，由 D 同步 |

## 开放问题

- OQ-B01（品牌字体）：**已处理（0.2.0）**。用户选 A 得意黑；`brand.css` 已写 `@font-face { font-family: "OcapBrand"; src: url('./fonts/OcapBrand-subset.woff2') format('woff2'); font-display: swap; }` 与 `--brand-font: "OcapBrand", var(--font)`；CSS 中无 "Smiley"/"得意黑" 作为 font-family 名（OFL 保留字体名）。`.brand-font` 的使用位置共 5 处：`AuthShell.vue:7`（h1，`BRAND_NAME`）、`PortalLayout.vue:6,13`（`BRAND_NAME`）、`AdminLayout.vue:6,28`（`ADMIN_BRAND_TITLE` = "Cyber@红枫岭 · 管理后台"）。子集覆盖核对：渲染文字为 ASCII（含空格）+ 红枫岭管理后台 + "·"（U+00B7），**全部在子集内，无子集外字符**；`AuthShell` 的副标题（"手机号注册"等）不带 `.brand-font`，走系统字体，同样无需子集。字体 12044 B，sha256 与 PM 素材一致。若日后品牌文案新增字符，需按 `fonts/README.md` 重新子集化。
  - 局限（如实记录）：未在真实浏览器中目视渲染字体效果；`@font-face` 能否被浏览器加载只验证到"构建产物含带哈希 woff2 且 CSS 引用正确"；视觉验收见 AC-209-05(4)。
- OQ-B03（认证失败转申诉只预填姓名）：**已实测并按设计处理**。`UnitsPick.vue:44-48` 在 `OWNER_NOT_MATCHED` 时 `store.setPrefillOwnerName(name)` + `router.push('/units/appeal')`；`UnitsAppeal.vue:70` `consumePrefillOwnerName()` 填入姓名并清空仓库，房屋需重新选择，未选房屋时"提交申诉"为 disabled。自检 spec 覆盖：姓名预填=「张三」（trim 后）、仓库预填被清空、提交按钮 disabled。保留房屋需改造 `UnitCascader`（不在本批）。
- OQ-B04（WXSS 真机表现）：`[UNSOURCED]`。设计只用渐变/边框/阴影，不依赖 SVG；未在微信开发者工具核对（本机无）。降级规则未单独实现，需 D/E 在工具中核对后再决定是否加降级。
- OQ-B05（`.woff2` MIME）：**待部署核对**。现已有随包字体（`dist/assets/OcapBrand-subset-<hash>.woff2`），目标机 nginx 对 `.woff2` 的 `Content-Type`（应为 `font/woff2`）`[UNSOURCED]` 未核实；E1/部署后用只读 HTTP 请求核对响应头一次。不识别时回退系统字体，页面仍可用（AC-209-03）。
- OQ-B06（对比度条目）：**已完成**。`themes/*.theme.json` 新增 17 条（bento 4、neon 7、terminal 6），`min` 取 `scripts/themes/schema.mjs:contrastRatio` 实测值向下取两位小数，`build.mjs --strict` 退出码 0。实测值：bento 侧栏次要文字/白底 5.946、当前项白字/#11121A 18.662、登录标题/页面底 17.002、副标题/页面底 5.417；neon 侧栏次要文字/#14152A 7.699、当前项 accentText/玻璃叠加等效色 #2C2C3F 5.518、顶栏文字/#14152A 15.530、登录标题/页面底 17.300、副标题 8.577、Hero 文字/渐变起终点等效色 11.574 与 14.507；terminal 侧栏次要文字/#111113 6.668、当前项/#1C1C1F 14.388、顶栏文字 16.826、登录标题/页面底 17.655、副标题 6.996、Hero 文字/#111113 16.826。登录页品牌标题实际放在 `.auth-panel`（`--bg` 底，文字色 `--text`，DOM 契约优先），故按"标题/页面底"建项；bento 管理端顶栏用户菜单文字复用既有 `onHero` 渐变三停点条目（4.5/5.6/4.59）。
- OQ-B07（1366 宽表格）：**已核算（静态，本机无浏览器，非真实视口度量）**。1366 视口（扣约 17px 滚动条）：侧栏 `clamp(192px,14vw,248px)`=192px，内容内边距 `clamp(12px,1.2vw,32px)`=16.4px，卡片内边距+边框 34px，表格容器宽 ≈ 1366−17−192−32.8−34 ≈ **1090px**。各管理端表格"固定宽+min-width"合计（`awk`/脚本统计）：AdminUsers 注册用户表原 1130（1010+120）**超出**→ 改后 990（固定 650 + 弹性 `min-width` 340：账号 130、昵称 100、实名 110；ID 70→60、手机号 140→125、状态 110→90、身份 110→95、认证 130→125、上次登录 160→155）；AdminSeats 1040（<1090，余量约 50，用户列改 `min-width` 以便宽屏分摊）；AdminRegistry 1070（<1090，余量约 20，**请 D 在真实 1366 视口目视核对**）；AdminMemberships/AdminAudit 760、AdminContentPosts 940 等均 <1090。列含义与顺序未变。AdminUsers 管理员账号表（固定 480）账号列改 `min-width`。
- `[ASSUMPTION]` 侧栏角标只显示在二级项（`SideNav.vue:36`，按 IFC-318），折叠状态下看不到待审批数字；首页仍有"待审批同住人申请：N"链接。
- `[ASSUMPTION]` `refreshPendingBadge` 在进入每个 `/units*` 路由时静默调用一次 `GET /me/housing`（`PortalLayout.vue:watch`），会与分区自身加载并发多一次请求；换取角标实时性。
- 窄屏下 `SubNavBar` 角标沿用同一 `pendingReview` 数据源。
- 未验证项：`npm run build:mp-weixin` 失败（`@dcloudio/uni-mp-weixin/dist/uni.compiler.js not found` / 缺 `src/manifest.json`），**改动前基线（`git archive HEAD` 副本）同样失败**，非本批引入（M-SD-006）；改用 `@vue/compiler-sfc` 对 `pages/login/index.vue` 做解析/模板/脚本编译检查，0 错误，无颜色字面量。
- 后端：本批零改动，本机无 Django，未运行后端测试；`backend/tests/integration/test_frontend_contract.py` 只读 `api.js` 两份契约文件，本批未改动。

## 现有测试同步清单（C1：失败用例逐条对照 module_design"测试影响清单"）

改动后 `npx vitest run`：前端 **39 失败 / 242 通过 / 共 281**（10 个文件失败）；小程序 **104/104 通过**。39 条失败**全部**对应测试影响清单（根因均为 Me/Units 拆分、顶部导航→侧栏、`AdminThemeSwitcher`→`AdminUserMenu`、管理端 4 页分区），无任何"清单外且应由产品代码修复"的失败；其中 1 条（TC-WEB-030）行号在清单所列范围之外但根因同清单 Me.vue 拆分项，标"清单边缘"。

| # | 失败用例（文件:用例） | 对应清单行 | 归类 |
|---|---|---|---|
| 1-3 | `admin_theme.spec.js` 管理端顶栏渐变/高亮悬停规则；用户端 B 黑色胶囊 `.topnav` 断言；`AdminLayout` 渲染 14 个导航链接 | `admin_theme.spec.js:11,58-67,151-166`、`:72-74` | 清单内 |
| 4 | `admin_users.spec.js` TC-UNIT-411 | `admin_users.spec.js:12,59`（需传 `section:'registered'`） | 清单内 |
| 5-11 | `owner_auth_v2.spec.js` TC-UNIT-667~673（7 条，均挂载 `Units.vue` 整页） | `owner_auth_v2.spec.js:15,52-`（重指向 `UnitsPick/UnitsAppeal`；669 另含 OQ-B03 行为变化；673 含旧文案"下方产权申诉"） | 清单内 |
| 12-13 | `pages.spec.js` TC-WEB-028、TC-WEB-029 | `pages.spec.js:231-258`（重指向 `MePhone`） | 清单内 |
| 14 | `pages.spec.js` TC-WEB-030（改密 + 注销，`:273`） | 根因同清单"Me.vue 拆分"（重指向 `MePassword`/`MeCancel`） | 清单边缘 |
| 15 | `product_review_rework2.spec.js` TC-UNIT-591 | `product_review_rework2.spec.js:25-26,83,106,224-226`（AdminAudit 传 `section:'logs'`） | 清单内 |
| 16-20 | `product_review_ui.spec.js` TC-UNIT-522、523、524、527、529（Units） | `product_review_ui.spec.js:65-188` | 清单内 |
| 21-25 | `product_review_ui.spec.js` TC-UNIT-530~534（Me） | `product_review_ui.spec.js:190-266` | 清单内 |
| 26 | `product_review_ui.spec.js` TC-UNIT-577（顶部导航） | `product_review_ui.spec.js:277-292` | 清单内 |
| 27-28 | `product_review_ui.spec.js` TC-UNIT-543、544（AdminUsers） | `product_review_ui.spec.js:435-455` | 清单内 |
| 29 | `product_review_ui.spec.js` TC-UNIT-547（金额上限，需 `section:'limit'`） | `product_review_ui.spec.js:507` | 清单内 |
| 30 | `product_review_ui.spec.js` TC-UNIT-548（11 个确认键静态扫描，`Units`/`Me` 文件已拆） | `product_review_ui.spec.js:576`（文件扫描范围加入新文件） | 清单内 |
| 31 | `qa_e2e_extend.spec.js` TC-E2E-103（`/me` 风格选择器） | `qa_e2e_extend.spec.js:53-70`（改 `/me/style`） | 清单内 |
| 32-34 | `qa_e2e_theme.spec.js` TC-E2E-101、102（2 条） | `qa_e2e_theme.spec.js:123,148,157,179` | 清单内 |
| 35-36 | `qa_int_theme.spec.js` TC-INT-103（2 条） | `qa_int_theme.spec.js:171-205`（挂载 `MeStyle.vue`） | 清单内 |
| 37-38 | `qa_int_theme.spec.js` TC-INT-105（2 条） | `qa_int_theme.spec.js:236-262` | 清单内 |
| 39 | `qa_unit_theme.spec.js` TC-UNIT-108 | `qa_unit_theme.spec.js:259-266` | 清单内 |

清单预测"预期无需改、需实跑确认"的条目实跑**全部通过**：`qa_e2e_pages.spec.js:24,132-139`（底栏"我的"→`/me`）、`qa_unit_theme.spec.js:268-275`（17/17 计数，靠路由里同一组件只 import 一次保持）、`:185-215`（style.css 结构）、`theme.spec.js`（含新 .vue 无颜色字面量扫描）、小程序登录页相关断言。实现过程中曾出现两条清单外失败并已用产品代码修复：TC-E2E-104（配图 `<text>` 使三风格文本不一致，改为 CSS 伪元素输出）、TC-E2E-105（`.admin-theme-trigger` 选择器，保留类名，见"架构偏差"）。
