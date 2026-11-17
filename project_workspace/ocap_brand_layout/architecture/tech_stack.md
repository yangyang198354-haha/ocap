<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-17T00:06:01+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0 APPROVED）</file>
    <file>architecture/architecture_design.md（0.1.0）</file>
    <file>architecture/module_design.md（0.1.0）</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型：品牌更名 + Web 左侧导航布局 + 多分辨率自适应（INCREMENTAL）

> 本批**不新增任何第三方依赖**（npm / pip 均无新增），全部沿用画像 P1 技术栈。版本取自本机 `frontend/node_modules`、`miniprogram/node_modules` 的实测（2026-11-17，`node -p "require('./node_modules/<pkg>/package.json').version"`），依赖声明见 `frontend/package.json`、`miniprogram/package.json`。
> 品牌字体为**待用户确认项**（OQ-B01）：下文给出 2 个候选，确认前开发用回退字体栈占位。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言（Web 前端） | JavaScript（ES modules），Vue SFC `<script setup>` | Node 22.23.3（本机 `node -v`）；Vue 3.5.45（实测，声明 `^3.5.13`，`frontend/package.json`） | 沿用 | 画像 P1；既有页面全部为该写法 | REQ-NFUNC-040 | 低 |
| Web 框架与构建 | Vue 3 + Vite | Vite 6.4.5（实测，声明 `^6.0.1`） | 沿用 | 画像 P1；`npm run build -- --base=/ocap/`（画像 P4）不变 | REQ-NFUNC-040 | 低 |
| 路由 | vue-router | 4.6.4（实测，声明 `^4.4.5`） | 沿用 | 子路径 + `props` + `beforeEnter` 即可实现 ADR-119；路径参数正则 `:id(\\d+)` 为该库既有语法（本仓库此前未使用，须开发以用例验证） | REQ-FUNC-207/208/215/219 | 低 |
| 状态管理 | Pinia | 2.3.1（实测，声明 `^2.1.7`） | 沿用 | 新增 `stores/housing.js`，与 `stores/auth.js` 同风格 | REQ-FUNC-208 | 低 |
| UI 组件库 | Element Plus | 2.14.8（实测，声明 `^2.8.7`）；MIT | 沿用 | 用 `el-dropdown`（`trigger` 数组，`dropdown.d.ts:24-26`）、`el-drawer`；**不采用 `el-menu`**（ADR-118：无风格映射、规则需自写） | REQ-FUNC-206/218/220、REQ-NFUNC-039 | 低（`el-drawer` 在窄屏的焦点/滚动锁定行为需用例核对） |
| 样式 | 原生 CSS 自定义属性 + `clamp()` / `auto-fill` / `auto-fit` + 现有 768px 媒体查询对 | 浏览器能力；无编译依赖 | 沿用 | ADR-121：不新增断点（C-70）；风格差异在 `themes/<key>.web.css`（ocap_ui_theme ADR-024/026） | REQ-FUNC-212/213、REQ-NFUNC-038 | 中（见风险 R-02、R-03） |
| 风格体系 | `themes/*.theme.json` + `scripts/themes/build.mjs`（仅 Node 内置模块） | 脚本已存在，本批不改脚本 | 沿用 | ADR-126：只增 `contrast` 条目与结构性 CSS | REQ-FUNC-216、REQ-NFUNC-005 | 低 |
| 品牌配图（Web） | 内联 SVG Vue 组件（3 个） | — | 新增代码，无新依赖 | ADR-124：矢量、不依赖外部素材、颜色取语义变量 | REQ-FUNC-204/221 | 中（视觉需用户目视确认，可能一轮返工） |
| 品牌配图（小程序） | WXSS 纯 CSS（渐变/边框/阴影） | uni-app 工程既有能力 | 新增代码，无新依赖 | ADR-124；包体积受限、SVG 在 WXSS 的支持未核实（OQ-B04） | REQ-FUNC-222 | 中 |
| 品牌字体（Web） | **待用户确认**（候选 A/B，见下节）；以子集化 `.woff2` 随包分发 | 未选定 | 新增静态资源，无 npm 依赖 | ADR-123：不用 CDN；无新依赖；失败回退系统字体 | REQ-FUNC-204 | 中（许可证文本须随包；子集生成工具不在仓库依赖中） |
| 品牌字体（小程序） | 系统字体（沿用 `--font`） | `miniprogram/theme/generated` 的 `--font` | 沿用 | Q-BL-05：小程序无法加载远程字体且包体积受限 | REQ-FUNC-204 | 低 |
| 小程序框架 | uni-app（Vue 3）+ Pinia | `@dcloudio/uni-app` 3.0.0-alpha-5030620261106001、Vite 5.4.21（实测）；声明 `^3.0.0-4060620250520001` | 沿用 | 画像 P1；`ThemeRoot`、`store/theme.js` 复用 | REQ-FUNC-203/222 | 低（工程依赖的预发布版本为既有状态） |
| 测试 | vitest 2.1.9 + @vue/test-utils + jsdom 25 | vitest 2.1.9（实测）；`@vue/test-utils ^2.4.6`、`jsdom ^25.0.1`（声明） | 沿用 | 画像 P3/P4；新用例位置 `frontend/tests/*.spec.js`、`miniprogram/tests/*.spec.js`；jsdom 无 `matchMedia`，用例按需桩 | REQ-NFUNC-040 | 低（jsdom 不计算布局，真实视口度量走人工清单） |
| 进程管理/部署 | 物理机 tar → scp → systemd；nginx 8090 静态文件 | 画像 P7 | 沿用 | 无后端变更；仅替换 `web` 静态目录 | — | 低 |
| CI/CD | GitHub Actions（`.github/workflows/ci.yml`，只测试与构建） | 画像 P7 | 沿用 | 无变更 | — | 低 |
| 新增依赖 | **无** | — | — | 满足"INCREMENTAL 尽量不新增" | — | — |

## 品牌字体候选（待用户确认，OQ-B01）

使用范围（决定子集字符集）：`Cyber@红枫岭`、`管理后台`、`登录`、`注册`、`手机号注册`、分隔符`·`；字母与数字取 ASCII 可见字符集即可。Web 端三套风格、登录页/注册页/管理端登录页统一使用同一品牌字体；其他正文仍为系统字体栈。

| 项 | 候选 A：得意黑 Smiley Sans | 候选 B：Orbitron（拉丁）+ 系统中文 |
|---|---|---|
| 风格 | 倾斜紧凑的无衬线，覆盖拉丁与汉字，科技感偏人文；"红枫岭"三个汉字与"Cyber@"同一字体，品牌名视觉统一 | 几何方正的科幻风拉丁字体，"Cyber@"科技感最强；汉字"红枫岭"回退到系统字体，品牌名为两种字体混排 |
| 许可证 | SIL Open Font License 1.1 `[WEB: https://github.com/atelier-anchor/smiley-sans，2026-11-16]`（仓库 README 写明；发布包含 `.woff2`） | 位于 Google Fonts 仓库 `ofl/` 目录，目录内含 `OFL.txt`，故为 OFL 系列 `[WEB: https://github.com/google/fonts/tree/main/ofl/orbitron，2026-11-16]`（页面未直接写出许可证名与版权人，**采用前须打开 `OFL.txt` 核对版本与版权声明**） |
| 字符集与子集化 | 含拉丁与 CJK；按上述字符集子集化为单个 `.woff2`（约 30 个字形） | 含拉丁（可变字重 `Orbitron[wght].ttf`，目录内文件名）；仅需 ASCII 子集；汉字不含 |
| 预估体积 | 约 8~20 KB `[ESTIMATE]`（官方页面未给出体积；子集后依字形数估计） | 约 6~15 KB `[ESTIMATE]`（取静态单字重子集；若保留可变字重轴会更大） |
| 随包分发 | 子集 `.woff2` + `OFL.txt` 放 `frontend/src/brand/fonts/`，`brand.css` 的 `@font-face` 以 `url()` 引用，`font-display: swap`，Vite 构建时带哈希输出到 `dist/assets`（体积 >4KB 不内联）；无 CDN | 同左 |
| 回退 | 失败/不支持时落到 `var(--font)`（系统字体栈，`themes.css:29`），登录表单与文案完整可读（AC-209-03） | 同左；汉字本就走系统字体 |
| 优缺点 | 优：品牌名统一、一个文件、许可证明确。缺：倾斜风格的"科技感"弱于 B，用户需目视确认 | 优：赛博/科幻感强。缺：品牌名混排字体；许可证需开发时核对 `OFL.txt` |
| 建议 | **推荐 A**（许可证已在作者仓库页面核对、覆盖汉字、单文件）；若用户希望更强的科幻感，可选 B 并接受混排 | — |

子集生成（开发一次性步骤，**不安装进仓库依赖**，由开发在本地用字体子集化工具（如 fontTools 的 `pyftsubset`，通用开源工具，须经用户同意后才在本机使用）完成，不在目标机运行；步骤说明见 module_design MOD-119）：以上述字符集为输入，输出 `woff2`；保留字体许可证文本；字体源文件不入库，仅提交子集产物与 `OFL.txt`。若采用 npm 包 `@fontsource/*` 属新增依赖，须用户批准（ADR-123 方案 B，本批不选）。

## 技术风险

### High

（无。本批为纯前端展示层变更，无数据、无接口、无迁移。）

### Medium

| ID | 风险 | 缓解措施 |
|---|---|---|
| R-01 | **既有用例改动面大**：`Units.vue`、`Me.vue`、`PortalLayout`、`AdminLayout` 及 4 个管理端页的结构变化使约 15 个既有 spec 文件需要同步（见 module_design 测试影响清单），可能被门控当作"新增失败" | 测试影响清单逐文件列出同步范围；GROUP_C 先改代码、同步既有用例、再跑全量；基线以实跑为准（画像 P4：前端 181/181、小程序 75/75），同步后须全部通过，不得删除断言来"变绿" |
| R-02 | **1366 宽度下表格溢出**：内容区比原 1180px 容器窄约 50px；`AdminUsers` 注册用户表固定 1010 + 弹性 120、`AdminSeats` 固定 1040 在含滚动条时可能出现表内横向滚动，违反 REQ-FUNC-213/223 | ADR-121、MOD-126 的表格宽度任务：开发在 1366 下核对并把次要列改弹性/压缩；`layout_css.spec.js` 对各表格固定列宽合计设 ≤1110 的静态上限；GROUP_D 用真实浏览器在 1366×768 目视复核 |
| R-03 | **窄屏边缘宽度**：宽屏起点 768px 时侧栏 192px，内容区仅约 576px，卡片、表格较挤 | 768px 起内容区使用 `auto-fill` 网格与弹性列；GROUP_D 在 768~1024 之间抽样走查；如不可接受，调整 `--side-w` 下限（只改变量，不新增断点） |
| R-04 | **登录页视觉未被用户认可**：科技感由用户目视确认（AC-209-05(4)），首版可能返工；小程序 WXSS 对渐变/阴影的真机表现未核实（OQ-B04） | 设计已给出每版元素清单与观察清单；开发先交付三版预览截图（桌面 + 375px），用户确认后再收尾；小程序在微信开发者工具核对并按降级规则处理 |
| R-05 | **字体选型与许可证**：最终字体待用户确认；候选 B 的许可证须开发核对 `OFL.txt`；二进制字体文件入库 | 用户确认前不写 `@font-face`（构建不依赖字体文件）；入库时附 `OFL.txt`；`brand.spec.js` 扫描字体 `url()` 不得为外网地址 |

### Low

| ID | 风险 | 缓解措施 |
|---|---|---|
| R-06 | `/me` 在宽/窄屏落点不同；jsdom 无 `matchMedia`，窄屏默认可能与真实浏览器不一致 | `isWideNow()` 缺 `matchMedia` 时返回 false 并写入用例；`layout_router.spec.js` 显式桩宽屏/窄屏两种情形 |
| R-07 | 同一组件实例在兄弟路由间复用，分区切换若未监听 `section` 会显示陈旧数据 | IFC-324 要求各宿主 `watch(() => props.section)`；`layout_router.spec.js`/页面用例覆盖"切换分区后内容变化" |
| R-08 | 目标机 nginx 对 `.woff2` 的 MIME 未核实（OQ-B05） | 部署后核对响应头；不识别时浏览器回退系统字体，页面仍可用 |
| R-09 | `el-drawer`（管理端窄屏）与 `el-dropdown`（Esc/焦点）行为依赖 Element Plus 版本 | 沿用已安装的 2.14.8，不升级；`user_menu.spec.js`、`layout_nav.spec.js` 覆盖 Esc 与关闭行为 |
| R-10 | 删除 `AdminThemeSwitcher.vue` 后遗留引用 | `git grep -n AdminThemeSwitcher -- frontend` 须为 0（已核实现有引用仅 `AdminLayout.vue:10,22` 与 `qa_unit_theme.spec.js:263-264`） |
