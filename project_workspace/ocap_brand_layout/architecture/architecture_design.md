<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-16T23:59:56+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0 APPROVED）</file>
    <file>requirements/user_stories.md（1.0.0 APPROVED）</file>
    <file>../ocap_ui_theme/architecture/architecture_design.md（基线，ADR-023~033）</file>
    <file>../ocap_ui_theme/architecture/module_design.md（基线，MOD-023~029 / IFC-142~151）</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：品牌更名 Cyber@红枫岭 + Web 左侧导航布局 + 多分辨率自适应（INCREMENTAL）

> 编号接续全仓最大值（2026-11-16 对 `project_workspace` 全部 .md 做 `grep` 核实）：ADR-117 起、MOD-119 起、IFC-316 起。
> 本文只做设计，不含实现代码。引用格式 `文件:行`；网页事实标 `[WEB: URL，访问日期]`。
> 用户已答复全部 Q-BL-01~32（phase_status.md clarifications，2026-11-16），本文按答复执行，不再列为开放问题。

## 架构概览

**本次改动在现有系统中的位置**：纯前端/展示层增量（C-64）。后端、数据库、`frontend/src/shared/api.js`、`miniprogram/utils/api.js` 均不改；改动落在 Web 前端布局/路由/页面拆分、风格体系的样式补充、小程序登录页与标题。

| 层 | 现状（基线） | 本次改动 |
|---|---|---|
| Web 用户端布局 | 顶部横排导航 + 底部 5 标签栏（窄屏）`frontend/src/portal/PortalLayout.vue:3-16`、`BottomTabBar.vue:21-28`；内容区 `.page` 最大 1180px `frontend/src/shared/style.css:7` | 宽屏（≥768px）改为左侧一级/二级导航 + 右上角昵称下拉；窄屏维持底栏，新增"我的"总览页与页顶二级切换条；内容区随视口铺满 |
| Web 管理端布局 | 顶栏 14 个横排链接 + 风格切换下拉 `frontend/src/admin/AdminLayout.vue:3-16,27-42`；无窄屏适配 | 左侧导航 9 个一级 + "内容管理"7 个二级；右上角管理员菜单（风格切换并入、退出）；窄屏抽屉 |
| 路由 | 用户端 13 条子路由、管理端 15 条 `frontend/src/router/index.js:10-28,34-50` | 为二级菜单新增子路径；旧地址保留为默认段；`/me`、`/units#review` 兼容 |
| 页面 | `Me.vue` 8 个区块一页、`Units.vue` 6 张卡片一页、决议/报销 `el-radio-group`、管理端 4 页内分区 | 个人中心拆 7 页 + 总览页；Units 拆 6 个分区组件；决议/报销/管理端 4 页按 `section` 显示一个分区 |
| 品牌 | 标题"业主委员会" `frontend/index.html:6`；登录页无配图 `Login.vue:2-4` | 产品名常量、品牌标识、3 套风格各一版登录配图（Web 3 个 SVG 组件，小程序纯 CSS）、品牌字体（待用户确认） |
| 小程序 | 登录页标题"业主委员会 · 登录" `miniprogram/pages/login/index.vue:4`；首页/全局导航栏标题 `miniprogram/pages.json:3,20` | 改名；登录页加品牌头与配图；其余页面布局不动 |

**核心设计思想（一句话）**：导航、二级菜单、右上角菜单全部由**一份类型化菜单配置**驱动（`frontend/src/layout/menus.js`），宽屏左侧栏、窄屏切换条、管理端抽屉、"我的"总览页共用同一配置与同一"当前项解析函数"；页面内分区统一用路由 `section` 参数表达，使"二级菜单项 = 可直达、可刷新的地址"；宽窄切换只用现有 768px 媒体查询（C-70），不引入新断点。

**关键质量属性**：
- 多分辨率（REQ-NFUNC-038、REQ-FUNC-212/213/223）→ ADR-121（弹性容器 + 自适应网格，不新增断点）。
- 可操作性（REQ-NFUNC-039：触控 ≥44px、键盘可达、非颜色高亮）→ ADR-118、ADR-122。
- 零回归（REQ-NFUNC-040）→ ADR-117（契约不变）、ADR-119（旧路径保持为默认段）、测试影响清单见 module_design。
- 品牌一致性（REQ-NFUNC-041）→ ADR-123、ADR-124，并由新增守护测试逐处核对。
- 风格体系兼容（REQ-FUNC-216、C-65）→ ADR-126。

## 部署视图

仅使用画像 P7 中存在的环境（"测试"；"生产"无）。不用 Docker。

| 组件 | 运行单元 | 环境 | 变更 |
|---|---|---|---|
| Django 后端 | systemd `ocap-backend`（gunicorn 127.0.0.1:9000） | 测试 | **无变更**，不需迁移、不需重启 |
| Web 前端静态文件 | `npm run build -- --base=/ocap/`（画像 P4）产物 → `/home/yangyang/ocap/web`，由 nginx(8090) 提供（画像 P7） | 测试 | **重新构建并替换静态文件**；nginx 无需改动；若采用随包字体，产物多出 `.woff2` 静态文件，nginx 对 `woff2` 的 MIME 需在部署后核对（见开放问题 OQ-B05） |
| 小程序 | `npm run build:mp-weixin`（`miniprogram/package.json`）产物，经微信开发者工具上传 | 无 P7 环境（沿用 ocap_ui_theme OQ-T08） | **重新构建**；发布流程不在画像 P7 内；小程序名称在微信后台的登记由账号主体配置，不在代码范围 |
| 风格构建脚本 | 开发机/CI 上 `node scripts/themes/build.mjs --strict`（`scripts/themes/build.mjs` 已存在） | 开发机、CI | 修改 `themes/*.theme.json`（对比度条目）与 `themes/*.web.css`/`*.mp.css` 后重新生成两端产物；不在目标机运行 |
| Freeark 服务/端口/目录/库 | — | — | 不触碰（画像 P7、P8） |

## ADR

### ADR-117: 纯前端变更，API 契约不变，管理员账号名由前端本地保存
- Status: Proposed
- Type: constraint-driven
- Context: C-64（不新增、不修改后端接口与字段）、REQ-FUNC-220（右上角显示管理员身份）、Q-BL-28=A、REQ-NFUNC-040（前后端契约不变）、画像 P6（API 路径集中在 `frontend/src/shared/api.js` 与 `miniprogram/utils/api.js`）。现状：管理端登录响应含 `admin.username`（`backend/apps/accounts/views.py:364`），前端只保存令牌（`frontend/src/admin/AdminLogin.vue:30-31`）；管理端没有"读取当前管理员"接口。
- 被排除方案：(1) 新增 `GET /admin/me`（违反 C-64）；(2) 解析令牌取用户名（令牌为不透明串，且解析属于猜测，不可靠）；(3) 固定显示"管理员"（Q-BL-28 已选 A，且体验差）。
- Decision: 登录成功后把 `admin.username` 存入本设备 `localStorage` 键 `ocap_admin_name`（新建 `frontend/src/admin/adminSession.js`，IFC-326），退出登录时清除；读取时若管理端令牌不存在则返回空串（令牌因 401 被清除后不显示陈旧账号名）；取不到显示"管理员"。`api.js` 两处契约文件**不改**，`admin.login` 已原样返回响应（`frontend/src/shared/api.js:133`）。
- Consequences: 正向：零后端改动、零契约漂移；契约测试 `backend/tests/integration/test_frontend_contract.py` 无需增补。负向：账号名是前端本地缓存，若管理员改名需重新登录才更新（系统当前无改名功能，`AdminAccountListCreateView` 仅创建与重置密码，可接受）。

### ADR-118: 导航由类型化菜单配置驱动，侧栏组件自研而非采用 `el-menu`
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-205/209/210/211/218/219、REQ-NFUNC-038(c)（1366×768 下 9 个一级项无需滚动）、REQ-NFUNC-039（触控 ≥44px、键盘可达、高亮不只靠颜色）、C-65（三套风格不改业务页面）。同一份导航数据要被宽屏侧栏、窄屏二级切换条、管理端抽屉、"我的"总览页复用。基线导航是手写 `router-link` 列表 `PortalLayout.vue:34-42`、`AdminLayout.vue:27-42`，高亮用路径前缀 `PortalLayout.vue:45`。
- Options:
  - A. 声明式菜单配置（`menus.js`）+ 自研 `SideNav.vue`/`SubNavBar.vue`：优：一份数据多处复用；"当前项/展开项"解析是纯函数，可单测；样式只用既有语义变量，三套风格零额外映射；DOM 结构（`button[aria-expanded]` + `a[aria-current]`）与测试选择器稳定。缺：需自行实现展开状态与键盘细节（Tab/Enter 原生即可，成本小）。
  - B. 采用 Element Plus `el-menu`（`unique-opened` 可直接实现"只展开一个"，`frontend/node_modules/element-plus/es/components/menu/src/menu.d.ts:14` 有该属性）：优：现成。缺：`themes.css` 里没有任何 `--el-menu-*` 映射（`git grep -c "el-menu" frontend/src/theme/generated/themes.css` = 0），三套风格需新增整组变量映射并逐风格走查（ADR-026 的 OQ-T03 风险再现）；"点击一级只展开不跳转""直达自动展开"仍要自写 `open()` 调用；默认条目高 56px、窄屏抽屉复用困难。
  - C. 各布局手写模板（现状延伸）：优：改动直观。缺：用户端/管理端/窄屏条/总览页四处重复，"只展开一个""直达自动展开"规则会分叉。
- Decision: 选 A。菜单配置类型见 IFC-316，解析函数见 IFC-317。展开规则（Q-BL-15=A，固定）：① 初始（进入 `/` 或任何无二级项的一级页）全部收起；② 路由变化时，若当前页属于某个有二级项的一级菜单则该一级展开（含详情页 `/resolutions/:id`、`/admin/content/posts/:id`），否则全部收起；③ 点击有二级项的一级菜单只切换展开/收起，不导航；④ 同时至多展开一个；⑤ 点击无二级项的一级菜单直接导航，不显示展开箭头。
- Consequences: 正向：REQ-FUNC-209/210 的规则集中在一处可测；风格新增不影响导航。负向：自研组件要自行保证无障碍（`aria-expanded`、`aria-current`、焦点环沿用 `style.css:5`），由 module_design 的守护测试覆盖。

### ADR-119: 二级菜单项 = 路由子路径；默认分区沿用旧路径；页内分区用 `section` 参数
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-208/219（点击二级项内容区只显示该项、刷新后停留）、REQ-FUNC-215（旧地址 `/me`、`/units#review` 不得 404/空白）、REQ-NFUNC-040、US-224 AC-224-04（管理端既有 15 个子路由路径不变）、Q-BL-20/21（我的房屋 6 项、申诉页自带房屋选择）。基线：`Units.vue` 单页 6 张卡片（`Units.vue:3-97`），`Resolutions.vue:93`/`Claims.vue:178` 用 `scope` 状态、`el-radio-group` 切换，管理端 4 页卡片平铺。
- Options:
  - A. 路由子路径 + 路由 `props: { section }`：每个二级项一个地址；默认（第一个）分区沿用旧路径（如 `/units`、`/resolutions`、`/claims`、`/admin/finance`），新增路径只多出非默认分区。优：旧地址原样可用，旧书签/测试路径不变；"刷新停留"天然成立；当前项解析按路径精确匹配；页面组件可保持一个文件，用 `section` 决定渲染哪个分区（Resolutions/Claims/管理端 4 页）；Units 因 6 个分区状态互不相同，拆为 6 个分区组件由宿主 `Units.vue` 按 `section` 渲染。缺：路由表增加条目；详情路由 `resolutions/:id` 须加数字约束避免与分区路径冲突。
  - B. 查询参数 `?tab=`：优：路由表不变。缺：高亮需同时比对路径与查询；`/units#review` 之类哈希兼容仍需特例；与"地址即二级项"的直觉不一致，浏览器前进后退行为较差。
  - C. 各分区全部拆成独立页面组件（无 `section` 宿主）：优：最彻底。缺：Resolutions/Claims/管理端页内容共享列表分页与对话框状态，强拆需重复大量代码并改动更多既有用例。
- Decision: 选 A。路由表见 IFC-322；分区约定见 IFC-324：宿主组件声明 `section` prop（字符串联合类型），路由用 `props: { section: 'x' }`，缺省取第一个分区；非法 `section` 不会出现（路径由静态路由或带正则的参数限定，未知地址仍落到 `/:pathMatch(.*)*` → `/`，沿用 `router/index.js:53`）。`resolutions/:id` 改为 `resolutions/:id(\\d+)`；旧地址 `/units#review`、`/units#appeal` 由 `/units` 路由的 `beforeEnter` 按 `to.hash` 重定向到 `/units/review`、`/units/appeal`，首页链接同步改为新地址。
- Consequences: 正向：旧路径全部保留（用户端 `/me` 除外，见 ADR-125），管理端 15 个既有路径一字不变，新增 4 个；二级项高亮与展开用同一函数。负向：Units 拆分改动面最大（6 个分区组件 + 状态仓库，ADR-127），现有 Units 相关用例需随之重指向（module_design 测试影响清单）；`resolutions/:id(\\d+)` 约束假定决议 id 为整数（`Resolutions.vue:106` 的编号由数值 id 派生，成立）。

### ADR-120: 宽窄屏形态切换以 CSS 媒体查询为主，JS 只用于 `/me` 重定向
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-214（窄屏维持现状）、C-70（断点沿用 768px，不新增）、AC-220-04（767/768 之间不同时出现底栏与固定侧栏）、ocap_ui_theme ADR-031（用 CSS 媒体查询，首帧不跳变）。`style.css:67,86` 已用 `max-width: 767.98px` / `min-width: 768px`。
- Options:
  - A. CSS 媒体查询决定显示哪套导航（侧栏、右上角菜单、切换条、底栏同时在 DOM，按断点显隐）；仅在两处需要"按宽度做行为"时用 `window.matchMedia('(min-width: 768px)')`：`/me` 路由进入时宽屏重定向到个人资料页（Q-BL-13=A + Q-BL-23=A）、管理端抽屉打开状态在转宽屏时自动关闭。优：首帧无跳变、与既有 ADR-031 一致；jsdom 无 `matchMedia`，约定缺失时按窄屏处理，使既有用例中"点击底部'我的'进入 `/me`"（`frontend/tests/qa_e2e_pages.spec.js:132`）继续成立。缺：DOM 中有被隐藏的导航。
  - B. 全部用 JS 读取宽度决定渲染：缺：首帧可能跳变；与 ADR-031 相悖。
  - C. 单一响应式布局（侧栏在窄屏变抽屉）：与 Q-BL-03=C（窄屏维持现状）冲突。
- Decision: 选 A。`useBreakpoint`（IFC-320）导出 `isWideNow()` 与 `useIsWide()`；`matchMedia` 不可用时 `isWideNow()` 返回 `false`。
- Consequences: 正向：形态切换无 JS 依赖，符合 AC-220-04。负向：窄屏下 DOM 里仍有（隐藏的）侧栏，`display:none` 使其不可聚焦、不被读屏读到；测试需注意选择器会同时匹配隐藏元素（jsdom 不解析媒体查询）。

### ADR-121: 多分辨率内容宽度策略——弹性容器与自适应网格，不新增断点
- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-038（1366×768 / 1920×1080 / 2560×1440 / 3840×2160：(a) 无横向滚动，(b) 侧栏右侧内容区主要内容占用 ≥90%，(c) 1366×768 下全部一级菜单无需滚动）、REQ-FUNC-212/213/223、C-70（不新增断点）、AC-218-02（4K 并排列数不少于 1920）。基线 `.page { max-width: 1180px }`（`style.css:7`）；决议卡片 2 列固定（`style.css:158`）；首页入口 6 列固定（`style.css:137`）；`el-table` 列宽多为固定值，实测固定宽度合计：`AdminUsers.vue` 两表合计 1490（注册用户表 1010 + 弹性 120）、`AdminSeats.vue` 1040、`AdminMemberships.vue`/`AdminAudit.vue` 760（`awk` 统计各 `el-table-column` 的 `width`）。
- Options:
  - A. 流式容器：布局内的 `.page` 取消最大宽度（`.layout-main .page { max-width: none }`，登录页等布局外的 `.page` 不变）；侧栏宽 `clamp(192px, 14vw, 248px)`、内容内边距 `clamp(12px, 1.2vw, 32px)`；卡片网格改 `repeat(auto-fill, minmax(Npx, 1fr))`，列数随宽度自增；`min-width: 0` 防止网格子项撑破。优：不新增断点，只用 `clamp()`/`auto-fill`；容器占用率 = (内容区 − 两侧内边距)/内容区，1366 时约 97%、4K 时约 99%，满足 ≥90%。缺：超宽屏下单张卡片内表单控件仍保持自身宽度（"主要内容占用宽度"以内容容器计，在度量定义中写明）。
  - B. 分档断点（如 1440/1920/2560）分别设 `max-width`：缺：违反 C-70；档间过渡处出现留白。
  - C. 仅把 `max-width` 提到 2200px：缺：4K 两侧仍留约 40% 空白，不满足 (b)。
- Decision: 选 A。度量口径（写入守护测试的断言依据）：内容容器 = `.layout-main .page`；占用率 = 该元素 `clientWidth` ÷（视口宽 − 侧栏宽），1366/1920/2560/3840 四档均须 ≥ 0.90。1366×768 下侧栏总高度 = 品牌位 + 9×44px，约 460px，小于 768px，无需滚动；展开一个二级组时侧栏区域自身滚动（`overflow-y: auto`），不影响页面主体。具体网格与表格宽度处理见 module_design MOD-121、MOD-126 与风险 R-02。
- Consequences: 正向：同一套规则覆盖四档分辨率与缩放等效视口。负向：1366 下内容区比原 1180px 窄约 50px，`AdminUsers.vue` 注册用户表（固定 1010 + 弹性 120）在含浏览器滚动条时可能出现表内横向滚动，须调整列宽（module_design MOD-126 列为开发任务并在 1366 下实测）；这是已识别风险而非未知项。

### ADR-122: 右上角用户菜单采用 `el-dropdown`（悬停 + 点击双触发）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-206/220（悬停或点击均可展开，触屏点击必须可用）、REQ-NFUNC-039（键盘 Tab/Enter/Esc）、Q-BL-18=A（昵称过长截断）。
- Options:
  - A. `el-dropdown` 设置 `trigger` 为数组 `['hover','click']`：Element Plus 2.14.8 的 `trigger` 类型为 `Arrayable<"click"|"contextmenu"|"hover">`（`frontend/node_modules/element-plus/es/components/dropdown/src/dropdown.d.ts:24-26`）；键盘与 Esc 关闭由组件提供；弹层挂到 body，沿用 `html` 上的风格变量（ocap_ui_theme ADR-026）。优：现成、无新依赖、三套风格已有映射（管理端已用同一组件 `AdminThemeSwitcher.vue:2`）。缺：Esc/焦点行为依赖组件实现，需用例覆盖。
  - B. 自制弹层：优：完全可控。缺：焦点陷阱、点击外部关闭、键盘处理全部要自写。
- Decision: 选 A。用户端 `PortalUserMenu.vue`（IFC-321）与管理端 `AdminUserMenu.vue`（IFC-326）各一个；两者菜单项都有 `command`；昵称/账号名用 `truncateLabel(name, 12)`（IFC-330，按码点计数）截断，完整名放 `title` 与菜单头部。管理端菜单把原顶栏风格切换并入（Q-BL-29=A），逻辑沿用 `adminStore.select`（`frontend/src/theme/adminStore.js:40-52`）与失败回滚文案（`AdminThemeSwitcher.vue:38`）；`AdminThemeSwitcher.vue` 删除。
- Consequences: 正向：REQ-NFUNC-039 的键盘要求由成熟组件承担。负向：`AdminThemeSwitcher.vue` 删除后，`frontend/tests/qa_unit_theme.spec.js:263-264` 对其存在性的断言须改写（module_design 测试影响清单）。

### ADR-123: 品牌字体随包分发（子集化 woff2），不用 CDN，最终选型待用户确认
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-204（统一品牌字体，加载失败回退系统字体）、Q-BL-05=B（Web 随包分发开源字体）、Q-BL-31=A（设计阶段给 1~2 个候选，用户确认后采用）、AC-209-03、特殊指示（不得用 CDN；引入新 npm 依赖须在 ADR 列方案并标明需用户批准；不联网下载/安装）。基线：仓库内无任何字体文件，`frontend/public`、`frontend/src/assets` 均不存在；字体栈为系统回退链（`themes.css:29`）。品牌字体只用于有限字符：`Cyber@红枫岭`、`管理后台`、`登录`、`注册`、分隔符"·"，故可子集化。
- Options:
  - A. 把开源字体按上述字符子集化后以 `.woff2` 放入 `frontend/src/brand/fonts/`，在 `brand.css` 用 `@font-face`（`font-display: swap`）引用，Vite 构建时哈希并随 `dist` 发布：优：无新依赖、无外网请求、子集后体积小、失败回退到 `var(--font)`；缺：子集文件需开发在本地用字体工具一次性生成并提交（工具不在仓库依赖中，生成步骤写入 module_design 的开发说明）。
  - B. 通过 npm 包 `@fontsource/*` 引入：优：版本化。缺：**新增第三方依赖，须用户批准**；其 CJK 子集不覆盖"枫岭"等字时仍需自备文件；包体较大。本批不选。
  - C. CDN（如 Google Fonts）：缺：明令禁止；国内网络与可用性风险。
- Decision: 选 A。候选字体与许可证、体积估计见 tech_stack.md；最终选型**待用户确认**（标为待用户确认项，OQ-B01）。开发在用户确认前用回退字体栈占位：`brand.css` 中 `--brand-font` 先等于 `var(--font)`，**不写 `@font-face` 与 `url()`**（否则文件不存在会令 Vite 构建失败）；用户确认并交付子集文件后再加入 `@font-face` 与变量覆盖，其余代码不变。小程序不加载远程字体，沿用系统字体（Q-BL-05、AC-228-01）。
- Consequences: 正向：不改依赖清单、不增加网络依赖。负向：字体文件作为二进制入库，许可证文本须随包留存（`OFL.txt`）；若用户选 B 方案类字体包需另行批准。

### ADR-124: 登录页配图——Web 三个 SVG 组件，小程序纯 CSS 绘制
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-204/221/222、Q-BL-04=A（由开发绘制矢量图形）、Q-BL-06=C、Q-BL-30=A、Q-BL-32=A（三套均须体现科技感，用户目视对照清单确认）、AC-209-01~05、AC-227-01、AC-228-01、ocap_ui_theme "新增风格不改业务页面"（REQ-FUNC-074）、`frontend/tests/theme.spec.js` 对 `.vue` 内颜色字面量的禁令（ocap_ui_theme ADR-029）。三版的"构图不相同"（AC-209-01）。
- Options:
  - A. Web：三个 SVG 组件（`art/NeonArt.vue`、`art/BentoArt.vue`、`art/TerminalArt.vue`）+ 共用 `AuthShell.vue` 按当前风格 key 选择组件，未知 key 回退 bento；颜色一律用 `var(--accent)` 等语义变量（SVG 通过 `<style scoped>` 的 `fill`/`stroke` 取变量，避免 `.vue` 内出现颜色字面量）。小程序：`<view>` + `themes/<key>.mp.css` 中按 `.theme-<key>` 作用域的 CSS 绘制，不使用 SVG（WXSS 对 SVG 背景的支持未核实，见 OQ-B04），不设循环动画（沿用 ocap_ui_theme ADR-032）。优：构图可各异；深浅色自动跟随变量；无外部素材；`prefers-reduced-motion` 沿用既有全局规则（`themes.css` 内 `@media (prefers-reduced-motion: reduce)`）。缺：三个组件各有维护成本；新增第四套风格时需补一个组件（缺省回退 bento，不改业务页）。
  - B. 单个 SVG + 按 `[data-theme]` 用 CSS 显隐不同图层：优：只有一个组件。缺：三套版本共享同一骨架，难以做到"构图不相同"；大量隐藏节点。
  - C. 位图/外部插画：缺：违背 Q-BL-04=A（矢量、不依赖外部素材）；小程序包体积受限。
- Decision: 选 A。每版的视觉元素清单与 AC-209-05 观察清单见 module_design MOD-128/MOD-129；三版共用同一品牌标识 `BrandMark`（IFC-328）与品牌字体，保证"能被识别为同一品牌"。品牌标题文字取 `--on-hero`，置于 `--hero` 底上，复用已校验的对比度组合（`themes/bento.theme.json` 的 `contrast` 已含 Hero 白字 / 渐变两端），不叠加半透明白色层（避免拉低对比度，P-SA-014）；表单区与配图分栏，配图不覆盖输入区（AC-209-04）。
- Consequences: 正向：科技感元素可逐项对照观察清单；风格新增有明确回退。负向：视觉最终由用户目视确认（AC-209-05(4)），首版可能需一轮返工；小程序 WXSS 对渐变/阴影等的真机表现需在微信开发者工具核对。

### ADR-125: 窄屏入口可达——"我的"总览页、页顶二级切换条与 `/me` 兼容
- Status: Proposed
- Type: constraint-driven
- Context: Q-BL-03=C（窄屏维持现状，仅宽屏启用左侧导航与右上角菜单）、Q-BL-11/12/13=A、Q-BL-23=A（总览页）、Q-BL-24=A（页顶切换条）、REQ-FUNC-214/215、US-220/221/230。约束来源即上述用户答复。
- 被排除方案：窄屏顶部也显示昵称下拉（与 Q-BL-03=C 冲突）；窄屏也提供左侧抽屉（用户端，同冲突；注意管理端窄屏抽屉是 Q-BL-25=A，另行成立）；窄屏仍用页内原形态平铺（Q-BL-24 选项 B，用户未选）。
- Decision: ① 窄屏底栏 5 项不变（`BottomTabBar.vue` 不改，其"我的"仍指向 `/me`）；② `/me` 路由由 `Me.vue`（改造为"我的"总览页）承载，页内列出个人中心 7 项入口与"退出登录"，每项触控 ≥44px；③ `/me` 的 `beforeEnter`：宽屏重定向到 `/me/profile`（Q-BL-13=A），窄屏进入总览页；总览页监听 `useIsWide()`，窗口由窄变宽时 `replace('/me/profile')`；④ 窄屏下有二级项的一级页（我的房屋 6、决议 3、报销 2），由 `PortalLayout` 在内容区顶部渲染 `SubNavBar`（IFC-319，横向滚动，仅窄屏显示，CSS 控制）；⑤ 个人中心 7 页窄屏下可直接访问，返回总览页靠底栏"我的"（AC-220-03）。
- Consequences: 正向：旧书签 `/me` 在两种屏宽下都有明确落点。负向：`/me` 在宽/窄屏落点不同，测试须显式设置 `matchMedia` 桩；个人中心"我的身份"页与总览页内容有少量重叠（身份摘要），可接受。

### ADR-126: 与既有风格体系兼容——不新增风格 token，对比度条目补充，管理端作用域规则沿用
- Status: Proposed
- Type: constraint-driven
- Context: C-65（不得破坏 ocap_ui_theme 的三套风格、账号级偏好、"新增风格不改业务页"，也不得破坏 ocap_admin_polish 对管理端的独立偏好与设备键）、REQ-FUNC-216、US-222（对比度 ≥4.5:1）、ocap_ui_theme ADR-024/033（`themes/<key>.theme.json` 为单一来源；`contrast` 声明待测组合，构建脚本按 WCAG 公式计算，`scripts/themes/build.mjs --strict`）。基线：`frontend/src/theme/adminStore.js`（设备键 `ocap_admin_theme`）、`frontend/src/theme/store.js`、`index.html:8-17` 的首屏脚本不变。
- 被排除方案：新增 `--side-*` 之类的风格 token（会改动 `schema.mjs` 并要求三份风格定义同步，且无必要——侧栏可用现有 `--overlay/--text/--muted/--glass/--accent-text/--line`）；把侧栏样式写进业务页面（违反守护测试）。
- Decision: ① 布局骨架类（`.shell`、`.side`、`.side-nav` 等）写入 `frontend/src/shared/style.css`，只引用既有语义变量；② 各风格的结构性差异（Bento 的胶囊高亮与黑色当前项、管理端渐变顶栏、Terminal 的等宽侧栏、Neon 的玻璃侧栏）写入 `themes/<key>.web.css`，管理端规则继续使用 `html[data-theme="…"][data-surface="admin"]` 前缀（`themes/bento.web.css:52-` 已有）；③ 在三份 `themes/*.theme.json` 的 `contrast` 数组为新增的前景/背景组合补条目（侧栏次要文字/侧栏底、侧栏当前项强调文字/当前项底、登录页品牌标题/配图底各停点，渐变逐停点建项，P-SA-014），阈值由构建脚本实测，≥4.5；④ 重新运行 `node scripts/themes/build.mjs` 更新 `frontend/src/theme/generated/*` 与 `miniprogram/theme/generated/*`，CI 的 `--check` 保持一致；⑤ 登录页按设备记忆显示对应版本，沿用 `index.html:8-17`、`adminStore.js:7`、`miniprogram/store/theme.js:8-20` 现有读取逻辑，不新增设备键，登录页不提供风格入口（REQ-FUNC-078）。
- Consequences: 正向：风格新增仍只需新增定义文件（缺省回退 bento 配图）；对比度回归可自动检查。负向：`.admin-bar .brand/.topnav` 相关的既有样式断言（`frontend/tests/admin_theme.spec.js:58-75`）会随管理端布局变化失效，须改写（测试影响清单）；`themes/*.web.css` 改动面大，需在三套风格下走查。

### ADR-127: 我的房屋拆分后的状态共享采用 Pinia 仓库 `housing`
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-208、Q-BL-21=A（申诉页自带房屋选择）、AC-214-03（"待我审批的同住人申请"二级项显示角标，该角标在侧栏出现，位于 Units 页面之外）、AC-221-02。基线 `Units.vue` 一个组件持有 `housing`、`toReview`、`myApplications`、`myAppeals`（`Units.vue:114-117`）及共享的 `pickedUnitId`（`:111`，认证与申诉共用）；认证失败 `OWNER_NOT_MATCHED` 时把姓名带入申诉并 `scrollIntoView('#appeal')`（`:157-163`）；`UnitCascader` 只在内部保存所选楼栋/单元，初值不回显（`frontend/src/portal/parts/UnitCascader.vue:29,39-40`）。
- Options:
  - A. Pinia 仓库 `frontend/src/stores/housing.js`：持有四份数据与"待审批计数"，分区组件各自读取并调用刷新；侧栏角标直接读仓库。优：侧栏与分区共享同一数据源；无需父子传参；与既有 `auth` 仓库风格一致（`stores/auth.js`）。缺：多一个模块。
  - B. 宿主 `Units.vue` 持有状态，用 `provide/inject` 传给分区：优：局部。缺：侧栏角标在宿主之外，拿不到。
  - C. 每个分区各自请求数据：优：最简单。缺：角标需第二套请求；"通过后刷新"要跨组件通知。
- Decision: 选 A（IFC-323）。两处行为变化须说明：① 认证与申诉各自独立选择房屋（Q-BL-21=A），不再共用 `pickedUnitId`；② `OWNER_NOT_MATCHED` 时只把姓名写入仓库 `prefill.ownerName` 并跳转 `/units/appeal`，**不带房屋**（`UnitCascader` 无法按 id 回显所选楼栋/单元，若只回填 id 会出现"按钮可点但界面看不出已选哪套"的误导），用户在申诉页重新选房。`/me/housing` 返回的 `pending_review_count`（`Home.vue:186`）用于布局层的角标静默刷新。
- Consequences: 正向：角标与分区数据一致。负向：认证失败后用户需在申诉页重选房屋，比旧版多一步（列为 `[ASSUMPTION]`，若要保留房屋须另行改造 `UnitCascader`，不在本批范围）。

## 开放问题 / ASSUMPTION

| ID | 内容 | 类型 / 影响 |
|---|---|---|
| OQ-B01 | **品牌字体最终选型待用户确认**（tech_stack.md 给出 2 个候选：得意黑 Smiley Sans、Orbitron）。开发先用回退字体栈占位，确认并交付子集文件后再接入（ADR-123） | 待用户确认；不阻断开发 |
| OQ-B02 | `[ASSUMPTION]` 管理端既有 15 个路径不变，4 个有分区的页面新增 4 个子路径（`/admin/finance/limit`、`/admin/users/registered`、`/admin/audit/logs`、`/admin/content/services/prompts`），默认分区沿用旧路径（ADR-119） | 与 AC-224-04 一致；若 PM 门控另有解读请指出 |
| OQ-B03 | `[ASSUMPTION]` 认证失败转申诉时只带姓名、不带房屋（ADR-127）。保留房屋需改造 `UnitCascader` 回显 | 行为小变化，影响 `owner_auth_v2.spec.js` 相关用例 |
| OQ-B04 | 小程序 WXSS 对 `repeating-linear-gradient`、多重 `box-shadow` 发光、`transform: rotate` 的真机表现、以及 SVG 作为背景/`image` 源的支持：`[UNSOURCED]`（未从微信官方文档核实）。设计只用 CSS 渐变/边框/阴影且不依赖 SVG，开发需在微信开发者工具核对；不支持的效果降级为纯色块（观察清单第 1 项至少保留"网格线条"或"光晕"之一） | 开发阶段验证 |
| OQ-B05 | `[UNSOURCED]` 目标机 nginx 对 `.woff2` 的 MIME 配置未核实（画像 P7 只记录了站点与端口）。若随包字体后浏览器拒绝解析，则回退到系统字体，页面可读性不受影响（AC-209-03）；E1 部署后核对一次响应头 | 部署后核对 |
| OQ-B06 | 对比度条目的 `min` 值由构建脚本实测填入，开发阶段完成；渐变底按停点逐一建项 | 开发阶段 |
| OQ-B07 | 1366×768 下 `AdminUsers.vue` 注册用户表（固定宽 1010 + 弹性 120）与 `AdminSeats.vue`（固定宽 1040）可能在含滚动条时超出内容区；列宽调整量以 1366 实测为准（ADR-121、R-02） | 开发阶段实测 |
