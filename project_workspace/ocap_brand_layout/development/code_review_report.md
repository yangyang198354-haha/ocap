<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-17T08:53:00+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>development/implementation_plan.md</file>
    <file>architecture/module_design.md（1.0.0 APPROVED）</file>
    <file>requirements/user_stories.md（1.0.0 APPROVED）</file>
    <file>testing/integration_test_report.md（0.1.0，DEF-001/002）</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：品牌更名 + Web 左侧导航布局 + 多分辨率自适应（GROUP_C）

## 摘要

- 改动范围（`git diff --shortstat HEAD`，不含 `.claude/`、`project_workspace/`）：34 个已跟踪文件，+523/−794 行（含已暂存的 `AdminThemeSwitcher.vue` 删除）；另有 31 个新建文件（未跟踪）。无无关文件：`git status` 中其余改动（`.claude/agent-memory/*`、`project_workspace/_kb_inbox.jsonl`）为本任务开始前已存在的未提交改动。
- `git diff --stat`（已跟踪，不含新建）：36 files changed, 537 insertions(+), 753 deletions(-)（含上述 `.claude`、`_kb_inbox` 的既有改动）。
- 五维平均分（12 个模块各 5 维，共 60 个评分）：Correctness 8.25、Security 9.00、Performance 8.67、Maintainability 8.33、Testability 7.42；总平均 8.33（500/60）。
- 问题统计（0.2.0 重算）：CRITICAL 0（已修复 0）/ MAJOR 2（1 条 FIXED：CR-002；1 条 OPEN：CR-001）/ MINOR 10（1 条 FIXED：CR-004；9 条 OPEN，含 0.2.0 新增 CR-012）。共 12 条（CR-001 ~ CR-012），OPEN 共 10 条（0.1.0 为 10 条：CR-002 关闭、CR-012 新增）。
- 0.2.0 修订：GR-C-001-F01，品牌字体接入，CR-002 关闭。新增 3 个文件（`frontend/src/brand/fonts/{OcapBrand-subset.woff2,OFL.txt,README.md}`），修改 `frontend/src/brand/brand.css`（未跟踪新建文件，不进 `git diff --stat`）；其余文件零改动，无无关文件。上面的 `git diff` 行数口径（已跟踪文件）不受影响，新建文件合计 34 个。
- 1.1.0 修订（缺陷回流 1/2，GR-D-001）：修复 DEF-001（`frontend/src/brand/art/index.js:10`）、DEF-002（`frontend/src/portal/PortalLayout.vue:48-50`），新增 CR-013（MINOR，FIXED）、CR-014（MAJOR，FIXED）；本次只改这 2 个产品文件，无无关文件。CR-001 的 39 条用例已由 GROUP_D 同步，前端现为 438/438，标 FIXED。
- 问题统计（1.1.0 重算）：CRITICAL 0（已修复 0）/ MAJOR 3（CR-001、CR-002、CR-014 均 FIXED，OPEN 0）/ MINOR 11（CR-004、CR-013 FIXED；9 条 OPEN：CR-003、CR-005 ~ CR-012）。共 14 条（CR-001 ~ CR-014），OPEN 共 9 条。
- 结论：产品代码、构建、风格生成物就绪；既有测试 39 条失败全部落在 module_design 测试影响清单内（见 implementation_plan"现有测试同步清单"），待 GROUP_D 同步。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC |
|---|---|
| `frontend/src/brand/{brand.js,BrandMark.vue,brand.css}`、`frontend/index.html`、`frontend/src/main.js` | MOD-119 / IFC-328 |
| `frontend/src/brand/fonts/{OcapBrand-subset.woff2,OFL.txt,README.md}`（0.2.0） | MOD-119 / ADR-123（AC-209-03、REQ-FUNC-204） |
| `frontend/src/layout/{menus.js,labels.js,useBreakpoint.js,SideNav.vue,SubNavBar.vue}`、`frontend/src/shared/style.css` | MOD-120 / IFC-316/317/318/319/320/330/331 |
| `frontend/src/portal/{PortalLayout.vue,PortalUserMenu.vue}` | MOD-121 / IFC-321 |
| `frontend/src/portal/{Me.vue,me/*}` | MOD-122 / IFC-325 |
| `frontend/src/stores/housing.js`、`portal/{Units.vue,units/*,Home.vue}` | MOD-123 / IFC-323/324 |
| `frontend/src/portal/{Resolutions.vue,Claims.vue}` | MOD-124 / IFC-324 |
| `frontend/src/admin/{AdminLayout.vue,AdminUserMenu.vue,adminSession.js,AdminLogin.vue}`；删除 `theme/AdminThemeSwitcher.vue` | MOD-125 / IFC-326 |
| `frontend/src/admin/{AdminFinance,AdminUsers,AdminAudit,AdminAiServices,AdminSeats,AdminMemberships}.vue` | MOD-126 / IFC-324 |
| `frontend/src/router/index.js` | MOD-127 / IFC-322 |
| `frontend/src/brand/{AuthShell.vue,art/*}`、`portal/{Login,Register}.vue`、`admin/AdminLogin.vue` | MOD-128 / IFC-327 |
| `miniprogram/{pages.json,pages/login/index.vue}` | MOD-129 / IFC-329 |
| `themes/*.{web.css,mp.css,theme.json}`、`frontend/src/theme/generated/themes.css`、`miniprogram/theme/generated/themes.scss` | MOD-129（mp.css）、MOD-130 |
| `frontend/tests/**`、`miniprogram/tests/**` | MOD-131（本组不做，C1） |

方法/函数集合对比（`git diff` 前后 `function|const|class` 名集合）：只有 `AdminLayout.vue`、`Me.vue`、`PortalLayout.vue`、`Units.vue` 有名称消失，均为 module_design 规定的迁移——`navItems/isActive/logout` → `layout/menus.js` + `PortalUserMenu.vue`/`AdminUserMenu.vue`；`Me.vue` 的资料/手机号/密码/邮箱/注销函数 → `portal/me/*`；`Units.vue` 的 `loadHousing/loadLists/refresh` → `stores/housing.js`，其余 → `portal/units/*`；无丢失逻辑。

## 自验证结果

| 项 | 命令（工作目录） | 结果 |
|---|---|---|
| 风格生成 | `node scripts/themes/build.mjs --strict`（仓库根） | 退出码 0，写入 `themes.css`、`themes.scss`；随后 `--check --strict` 退出码 0（生成物与定义一致） |
| 前端构建 | `npm run build -- --base=/ocap/`（`frontend/`） | `✓ built in 42.29s`，仅有既有的 >500kB chunk 提示 |
| 字体接入后构建（0.2.0） | 同上 | `✓ built in 39.13s`；`dist/assets/OcapBrand-subset-c41YCxaj.woff2` 12044 B；`index-*.css` 含 `@font-face{font-family:OcapBrand;src:url(/ocap/assets/OcapBrand-subset-c41YCxaj.woff2) format("woff2");font-display:swap}` 与 `"OcapBrand", var(--font)`；`frontend/dist` 为 git 忽略目录 |
| 字体文件完整性（0.2.0） | `sha256sum`（仓库根） | `fonts/OcapBrand-subset.woff2` = `c02ca28c…2109`、`OFL.txt` = `9401f405…bec72`，均与 PM 素材一致 |
| 前端测试（0.2.0，字体接入后） | `npx vitest run --passWithNoTests`（`frontend/`） | `Test Files 10 failed \| 16 passed (26)`；`Tests 39 failed \| 242 passed (281)`；失败按文件：admin_theme 3、admin_users 1、owner_auth_v2 7、pages 3、product_review_rework2 1、product_review_ui 15、qa_e2e_extend 1、qa_e2e_theme 3、qa_int_theme 4、qa_unit_theme 1，合计 39，与 0.1.0 记录（implementation_plan"现有测试同步清单"）逐文件逐条数一致，无新增失败 |
| 小程序测试（0.2.0） | 同上（`miniprogram/`） | `Test Files 15 passed (15)`；`Tests 104 passed (104)` |
| 前端测试（基线，改动前） | `npx vitest run --passWithNoTests`（`frontend/`） | `Test Files 26 passed (26)`；`Tests 281 passed (281)` |
| 前端测试（改动后） | 同上 | `Test Files 10 failed \| 16 passed (26)`；`Tests 39 failed \| 242 passed (281)`；39 条失败逐条归类见 implementation_plan（38 条清单内、1 条清单边缘，无清单外） |
| 小程序测试（基线） | `npx vitest run --passWithNoTests`（`miniprogram/`） | `Test Files 15 passed (15)`；`Tests 104 passed (104)` |
| 小程序测试（改动后） | 同上 | `Test Files 15 passed (15)`；`Tests 104 passed (104)` |
| 小程序构建 | `npm run build:mp-weixin`（`miniprogram/`） | **失败**：`@dcloudio/uni-mp-weixin/dist/uni.compiler.js not found`、`ENOENT .../miniprogram/src/manifest.json`；对改动前基线（`git archive HEAD` 副本 + 链接同一 node_modules）重跑得到同样错误 → 非本批引入（M-SD-006），未验证 |
| 小程序登录页编译检查 | `@vue/compiler-sfc`（解析/`compileTemplate`/`compileScript`，`frontend/node_modules`） | `parse errors 0`、`template errors 0`、`script ok true`、颜色字面量 `[]` |
| 临时功能自检 | 临时 vitest spec（`frontend/.selfcheck/`，已删除，不属仓库测试） | 路由与导航行为 16 项中，用户端 6 项（侧栏 9/6 项、展开收起/单开/角标、详情页高亮、旧地址与 `/me` 宽窄分流、窄屏切换条、认证失败转申诉预填）+ 管理端 3 项（侧栏/内容管理 7 项/账号名/退出、缺省名、分区页）+ 登录页 3 套配图与管理端登录账号名保存、menus 纯函数 3 项均断言通过；最后一次运行仅 1 项因测试自身的 mock 触发 Element Plus 表格 `rows is not iterable` 在 `w.unmount()` 处报错（断言本身已全部通过），不是产品缺陷 |
| 前端测试（1.1.0，缺陷修复后） | `npx vitest run --passWithNoTests`（`frontend/`） | `Test Files 37 passed (37)`；`Tests 438 passed (438)`（含 TC-INT-874、TC-INT-914） |
| 小程序测试（1.1.0） | 同上（`miniprogram/`） | `Test Files 16 passed (16)`；`Tests 119 passed (119)` |
| 前端构建（1.1.0） | `npm run build -- --base=/ocap/`（`frontend/`） | `✓ built in 37.49s`，仅既有 >500kB chunk 提示 |
| 静态检查/后端 | `python -m compileall`、`manage.py check/test` | **未验证**：本批后端零改动；本机无 Django（画像 P4）。`test_frontend_contract.py` 只读 `api.js` 两份契约文件，本批未改动 |
| 迁移 | — | 无迁移（纯前端） |

## 按模块评审

### MOD-119 Web 品牌常量与网页标题
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-002 | MAJOR | `frontend/src/brand/brand.css`、`frontend/src/brand/fonts/` | 品牌字体仅占位（C2/OQ-B01）。0.2.0 已接入用户选定的得意黑子集（OcapBrand）：`@font-face` + `--brand-font: "OcapBrand", var(--font)`，随包 woff2 与 OFL.txt，无 CDN；5 处 `.brand-font` 文字均在子集内，构建产物含带哈希 woff2，测试无新增失败。遗留（不属本条缺陷）：`.woff2` MIME 待部署核对（OQ-B05）、真实浏览器目视待用户（AC-209-05(4)） | FIXED |
| CR-012 | MINOR | `frontend/src/brand/fonts/OcapBrand-subset.woff2` | 二进制字体入库，只能用 sha256 与 PM 素材核对，无法在代码评审中审阅内容；改名正确性（name 表无 Smiley/得意黑）由 PM 在制作时核对，开发侧未再用字体工具复验（不得安装工具） | OPEN |

### MOD-120 导航配置与共用布局件
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-006 | MINOR | `layout/SideNav.vue:27`、`admin/AdminLayout.vue:5,25` | 管理端抽屉打开时页面里有两份 `SideNav`，`id="side-sub-<key>"`/`aria-controls` 重复；仅影响读屏的 id 引用，功能无碍 | OPEN |
| CR-007 | MINOR | `layout/SideNav.vue:36` | 待审批角标只显示在二级项（按 IFC-318），"我的房屋"折叠时看不到数字；首页仍有数字链接 | OPEN |
| CR-011 | MINOR | `frontend/src/shared/style.css:133` | `.admin-login` 规则在管理端登录页改用 `AuthShell` 后不再被引用（死规则，按最小改动未删） | OPEN |

### MOD-121 用户端布局与用户菜单
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-008 | MINOR | `portal/PortalLayout.vue:watch`、`stores/housing.js:41` | 每次进入 `/units*` 路由静默 `GET /me/housing` 一次，与分区自身加载并发，多一次请求（1.1.0 未加重） | OPEN |
| CR-014 | MAJOR | `portal/PortalLayout.vue:48-50` | DEF-002：刚登录时 `auth.me` 为登录响应简要对象（无 identities），`onMounted` 因其非空跳过 `fetchMe`，角标按"无房屋"置 0，之后无刷新，违反 AC-214-03。修复：`!auth.me \|\| !auth.me.identities` 时先 `fetchMe`。副作用：登录后首次挂载多一次 `GET /me`，无新增轮询 | FIXED |

### MOD-122 个人中心拆分
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-010 | MINOR | `portal/me/MeEmail.vue:6,31` | 比"原样迁移"多一行"当前邮箱"与一次 `GET /me/profile`（`[ASSUMPTION]`，原因见 implementation_plan"架构偏差"） | OPEN |

### MOD-123 我的房屋拆分与状态仓库
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 8/10 |

无新增问题（行为变化 OQ-B03 已在 implementation_plan 记录并经自检验证）。

### MOD-124 决议与报销二级分区
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 7/10 |

无问题。

### MOD-125 管理端布局与管理员菜单
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-005 | MINOR | `admin/AdminUserMenu.vue:4` | 触发器额外带 `admin-theme-trigger` 类名以保持既有 TC-E2E-105 选择器；属 [DEVIATION]，D 若改选择器可去掉 | OPEN |

### MOD-126 管理端页内分区二级
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 7/10 |

无新增问题（OQ-B07 表格宽度已处理：AdminUsers 注册用户表 1130→990；AdminRegistry 1070 余量仅约 20px，建议 D 真实 1366 视口目视核对）。

### MOD-127 路由
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 8/10 |

无问题。

### MOD-128 Web 登录/注册/管理端登录品牌设计
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-004 | MINOR | `brand/art/BentoArt.vue`、`TerminalArt.vue` | 首版配图用 SVG `<text>`，使 `/login`、`/register` 三风格 `textContent` 不一致，令既有 TC-E2E-104 失败；已改为 `foreignObject` + CSS `content: attr()` | FIXED |
| CR-013 | MINOR | `brand/art/index.js:10` | DEF-001：`ARTS[themeKey]` 对 `__proto__`/`constructor`/`toString`/`hasOwnProperty` 取到 Object.prototype 成员，违反 IFC-327"未知键回退 BentoArt"；改用 `Object.hasOwn(ARTS, themeKey)` 守卫 | FIXED |

### MOD-129 小程序品牌与登录页
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 7/10 | 9/10 | 9/10 | 8/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-003 | MINOR | `miniprogram/pages/login/index.vue`、`themes/*.mp.css` | WXSS 对渐变/多重阴影的真机表现未核实（OQ-B04）；`build:mp-weixin` 基线即失败，无法产出构建；降级规则（纯色块）尚未实现 | OPEN |

### MOD-130 风格体系适配
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 8/10 |

无新增问题（对比度条目 17 条，`--strict` 通过；`scripts/themes/*` 未改）。

### 跨模块
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MAJOR | `frontend/tests/**`（10 个文件 39 条） | 既有用例在新结构下失败，由 GROUP_D 同步（GR-B-001-F01/C1）；38 条在测试影响清单内，1 条（`pages.spec.js` TC-WEB-030）行号在清单范围外但根因同清单 Me.vue 拆分项。1.1.0：GROUP_D 已同步，前端 438/438 | FIXED |
| CR-009 | MINOR | `frontend/src/admin/AdminUsers.vue`；`frontend/.selfcheck/`（已删） | 流程偏差：AdminUsers.vue 的一组等价替换用 Python 脚本完成（规则 3 要求只用 Edit/Write），已用 `git diff` 逐段复核，内容无影响；另在 `frontend/.selfcheck/` 建过临时自检 spec（不在 `tests/` 下，已删除，交付时不存在） | OPEN |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

1.1.0：无 OPEN 的 MAJOR（CR-001 已由 GROUP_D 同步，CR-002 于 0.2.0 FIXED，CR-014 本次 FIXED）。

## 缺陷修复

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-001（MINOR） | `frontend/src/brand/art/index.js:10` | `ARTS` 是普通对象字面量，`ARTS['__proto__']` 等原型链键名取到 Object.prototype 成员（真值），绕过回退 | `typeof` 判断后加 `Object.hasOwn(ARTS, themeKey)`；TC-INT-862/874 通过 |
| DEF-002（MAJOR） | `frontend/src/portal/PortalLayout.vue:48-50` | `onMounted` 只判断 `!auth.me`；登录后 `auth.me` 为简要对象（无 identities）而被视为已加载，`refreshPendingBadge` 读到空房屋列表置 0，Home 稍后补全身份时无人再刷新角标 | 条件改为 `!auth.me \|\| !auth.me.identities`，先 `fetchMe` 再刷新；不加 watcher、不加轮询，进入 `/units*` 的额外 `GET /me/housing` 次数不变；TC-INT-914、TC-INT-885/886/887 通过 |

## 现有测试调整

1.1.0 同样未修改任何测试文件（TC-INT-874/914 判定正确，不改）。0.2.0 及之前：本组**未修改**任何测试文件（C1）。39 条失败用例的逐条归类见 `implementation_plan.md`"现有测试同步清单"。其余既有用例（前端 242、小程序 104）原样通过。
