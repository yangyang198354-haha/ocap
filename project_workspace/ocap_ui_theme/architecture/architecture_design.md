<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-09T17:05:00+08:00</timestamp>
  <project_name>ocap_ui_theme</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>../ocap/design/design_spec.md</file>
    <file>../ocap/design/prototype.html</file>
    <file>../ocap/architecture/architecture_design.md (基线，ADR-001~022)</file>
    <file>../ocap/architecture/module_design.md (基线，至 MOD-022 / IFC-141)</file>
    <file>../ocap/architecture/tech_stack.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：ocap 多风格界面（INCREMENTAL）

> 编号接续基线：ADR-023 起、MOD-023 起、IFC-142 起。本文只做设计，不含实现代码。
> 基线事实均已用 `git grep` / 读取核实，引用格式 `文件:行`。网页事实标 `[WEB: URL，2026-11-09]`。

## 架构概览

**本次改动在现有系统中的位置**：这是一次横切前端的"换肤"增量，后端只增一个轻量偏好字段与两个接口。

| 层 | 现状（基线） | 本次改动 |
|---|---|---|
| 后端 `accounts` | `User` 模型 `backend/apps/accounts/models.py:7`；个人资料接口 `me/profile` `backend/apps/accounts/urls.py:23`；权限 `IsMember` `backend/apps/core/permissions.py:28`；错误 `ApiError(code, message, http_status=400)` `backend/apps/core/errors.py:6-12` | `User` 增加可空列 `theme_key`；新增 `GET/PUT /api/v1/me/theme`；新增手写迁移 `accounts/0002` |
| Web 前端 | 单 SPA 含 portal 与 admin 两棵路由树 `frontend/src/router/index.js:5-39`；全局样式 7 行 `frontend/src/shared/style.css:1-7`；`main.js` 全量引入 Element Plus `frontend/src/main.js:3-4,13` | 新增风格运行时、基础样式（CSS 变量）、底部标签栏；两个布局与全部页面的内联样式改为类名 |
| 小程序 | uni-app，11 页，tabBar 4 项 `miniprogram/pages.json:21-28`；全局样式在 `App.vue` `<style>` | 新增 `ThemeRoot` 根容器、风格 store；11 页套根容器、内联样式改类名 |
| 新增 | — | 仓库根 `themes/`：风格定义的**单一来源**；`scripts/themes/build.mjs`：校验并生成两端产物 |

**核心设计思想（一句话）**：风格 = 一份数据文件（`themes/<key>.theme.json`），两端不含任何按风格分支的业务代码；业务页面只使用语义化 CSS 变量与类名。新增风格 = 新增数据文件 + 运行构建脚本，业务页面改动数为 0（REQ-FUNC-074，AC-080-01/02）。

**关键质量属性**（引用需求）：
- 可扩展性：REQ-FUNC-074 → ADR-024、ADR-025。
- 首屏无错误风格闪烁、切换 ≤ 1 s：REQ-NFUNC-010 → ADR-027。
- 零回归与契约一致：REQ-NFUNC-009 → ADR-023、ADR-029（既有 120 个后端用例全部通过 + 新增用例全过；前端/小程序现有用例零新增失败，GR-A-002-F01）。
- 无障碍与降级：REQ-NFUNC-005/006/007/008 → ADR-032、ADR-033。
- 安全：偏好仅本人可读写（AC-091-04）→ ADR-023。

## 部署视图

仅使用画像 P7 中存在的环境（"测试"；"生产"无）。不用 Docker。

| 组件 | 运行单元 | 环境 | 变更 |
|---|---|---|---|
| Django 后端 | systemd `ocap-backend`（gunicorn 127.0.0.1:9000） | 测试 | 代码 + 迁移 `accounts/0002`；**须执行迁移并重启 `ocap-backend`** |
| Web 前端静态文件 | `npm run build -- --base=/ocap/` 产物 → 目标机 `/home/yangyang/ocap/web`，由 nginx(8090) 提供（画像 P7、P4） | 测试 | 重新构建并替换静态文件；nginx 无需改动、无需重启 |
| 小程序 | `npm run build:mp-weixin` 产物，经微信开发者工具上传 | 无 P7 环境 | 重新构建；发布流程不在画像 P7 内，见开放问题 OQ-T08 |
| 风格构建脚本 | 开发机/CI 上的 Node 脚本 `scripts/themes/build.mjs` | 开发机、CI | 新增；不在目标机运行 |
| Freeark 服务/端口/目录/库 | — | — | 不触碰（画像 P7、P8） |

## ADR

### ADR-023: 账号级风格偏好的存储与接口
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-072（账号级跨设备同步）、REQ-FUNC-070（未选过默认 B，含上线前已有账号）、REQ-NFUNC-009（零回归）、AC-091-04（仅本人可读写）、画像 P6（手写单 app 迁移、前后端契约文件同步）。现有 `PATCH /me/profile` 用白名单 `editable = {"nickname","gender","birthday","email","avatar_attachment_id"}` `backend/apps/accounts/services.py:331`，`profile_view` 返回固定字段 `views.py:243-252`。
- Options:
  - A. 在 `User` 加可空列 `theme_key`，新增专用端点 `GET/PUT /me/theme`。优：不改动既有响应形状，既有契约/测试不受影响；权限与校验集中；改动单 app。缺：多一个端点与一次请求。
  - B. 把 `theme_key` 并入 `/me/profile`（扩白名单 + `profile_view` 加字段）。优：少一个端点。缺：改变既有响应字段（基线测试若逐字段比对可能受影响）；偏好更新与资料编辑耦合；资料编辑页含头像昵称等校验分支，风险面更大。
  - C. 新建 `UserPreference` 键值表。优：以后可放更多偏好。缺：当前只有一个偏好，属于过度设计；多一张表与一个 app 级迁移。
- Decision: 选 A。理由：零回归最重要（REQ-NFUNC-009），A 对既有接口零改动；单列可空天然表达"未选择 = NULL = 默认 B"，上线前已有账号无需数据回填（REQ-FUNC-070）。接口只作用于 `request.user`，不接受用户 id 参数，故他人偏好不可达（AC-091-04）。
- Consequences: 正向：迁移极小（可空列，MySQL 与 SQLite 均无需回填）、可逆（RemoveField）；契约测试自动覆盖新路径。负向：以后若出现第二个偏好需再评估是否升级为偏好表（届时迁移列数据）；登录响应不含主题，客户端登录后须多一次 `GET /me/theme`（ADR-027 说明该请求不影响首屏）。

### ADR-024: 风格定义的单一来源与注册机制
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-074（新增风格只加一份定义、不改业务页面、列表自动出现）、AC-080-01/02/03（不合规定义不出现在列表且有可定位错误）、REQ-FUNC-069。Web（Vite 6.4.5）与小程序（Vite 5.4.21，uni-app 3.0.0-alpha-5030620261106001）是两个独立工程 `frontend/package.json`、`miniprogram/package.json`，实测版本取自各自 `node_modules`。
- Options:
  - A. 仓库根 `themes/<key>.theme.json`（数据）+ Node 构建脚本校验并**生成**两端产物（Web：CSS + 注册表模块；小程序：注册表模块含 token）；生成物入库，测试核对"生成物与源文件一致"。优：两端完全同源；校验逻辑只写一份；无运行期依赖；不合规定义在构建期被拒绝并给出文件/字段定位。缺：新增风格要多执行一步构建命令；需维护生成物与源的一致性测试。
  - B. 各端用 Vite `import.meta.glob` 直接读取 `themes/*.json`，运行期注入变量。优：无生成物。缺：Web 的 CSS 要等 JS 执行后才注入，难以做到首屏无闪烁（ADR-027）；小程序工程根目录外的文件能否被 `uni` 构建正确处理，我不能确认（OQ-T02）。
  - C. 两端各自维护一份风格定义。优：最简单。缺：违反"同步"要求，必然漂移；新增风格要改两处。
- Decision: 选 A。理由：同时满足 REQ-FUNC-074 的"一份定义"、REQ-NFUNC-010 的"静态 CSS 先于脚本"（B 做不到）、AC-080-03 的"构建期校验"。脚本只用 Node 内置模块，无新依赖。
- Consequences: 正向：新增风格的步骤固定为 1) 新建 `themes/<key>.theme.json`（可选同名 `.web.css` / `.mp.css` 放结构性差异样式），2) 运行 `node scripts/themes/build.mjs`，3) 提交；业务页面文件改动 = 0。负向：生成物进入 diff（可读性略降，由 CI 一致性测试兜底）；Node 版本要求见 tech_stack。

### ADR-025: 后端只校验偏好格式，不维护"启用风格集合"
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-081（已保存风格不在启用集合则回退 B）、REQ-FUNC-074（新增风格不应牵动后端）、AC-086-01、AC-080-01。
- Options:
  - A. 后端只校验 key 的格式（小写字母开头，仅字母/数字/下划线/连字符，长度 2~32），启用集合由客户端注册表决定；未知 key 由客户端回退 B。优：新增/下线风格后端零改动、无需重启；"下线"自然回退。缺：后端可存入"格式合法但不存在"的 key（无安全影响，仅影响本人显示）。
  - B. 后端读取一份启用集合（配置或生成的 JSON）并拒绝未知 key。优：数据更干净。缺：后端要随每次新增风格发布（目标机仅部署 backend 目录，仓库根 `themes/` 不在其中）；Web/小程序/后端三处同步，扩展成本上升，违背 REQ-FUNC-074 精神。
- Decision: 选 A。理由：REQ-FUNC-074/081 要求"只新增一份定义"，且客户端本就必须有回退逻辑（AC-086-01/03）。
- Consequences: 正向：后端稳定、不随风格变化发版。负向：数据库中可能存在已下线 key（可接受，读时回退）；"非法值"的定义弱于枚举（用格式与长度上限防滥用，见 IFC-143）。

### ADR-026: Web 换肤机制与 Element Plus 组件换肤
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-069/075/076、REQ-NFUNC-010。基线：`main.js` 全量引入 Element Plus 与 `element-plus/dist/index.css`；已装 Element Plus 2.14.8，MIT，且 `node_modules/element-plus/theme-chalk/dark/css-vars.css` 存在（已核实）；`dist/index.css` 中无 `color-mix`（grep 计数 0），故主色的 `light-3…9`、`dark-2` 梯度**不会**自动随 `--el-color-primary` 变化，须显式输出。24 个文件使用 `<el-*>`/`ElMessage`（`git grep` 实测）。
- Options:
  - A. CSS 自定义属性：在 `<html data-theme="key">` 上以属性选择器输出每个风格的变量块；业务类名读取语义变量；Element Plus 通过覆盖 `--el-*` 变量换肤；深色风格（A、C）额外给 `<html>` 加 `dark` 类并引入官方 `dark/css-vars.css`。优：运行期切换 = 改一个属性，瞬时；弹层（Teleport 到 body）也继承 `html` 上的变量；无需重新编译。缺：需为 Element Plus 输出一整组 `--el-*` 映射（含梯度），视觉要逐组件走查。
  - B. 为每个风格编译一份独立 CSS，切换时替换 `<link>`。优：隔离。缺：切换有网络/解析延迟，易闪烁；体积翻倍；难满足 ≤ 1 s 与无闪烁。
  - C. Element Plus SCSS 编译期变量覆盖。缺：编译期只能产出一套，运行期无法切换。不可行。
- Decision: 选 A。生成脚本为每个风格同时输出：业务语义变量（`--bg --surface --text --muted --line --accent --accent-2 --accent-text --on-accent --success --warning --danger --radius-* --shadow-* --font --mono --blur --glass`）与 Element Plus 映射变量（`--el-color-primary` 及 `light-3/5/7/8/9`、`dark-2`、`--el-color-success/warning/danger/error/info`、`--el-bg-color`、`--el-bg-color-page`、`--el-bg-color-overlay`、`--el-text-color-primary/regular/secondary/placeholder`、`--el-border-color(-light/-lighter)`、`--el-fill-color-blank`、`--el-border-radius-base/small`）。梯度由脚本内的混色函数从主色与背景色计算（不引入依赖）。`:root` 默认值 = 风格 B，保证未知/缺失 `data-theme` 时回退 B。
- Consequences: 正向：切换成本低；A/B/C 与未来风格同一路径。负向：Element Plus 内部若使用了未列入映射的变量，某些组件在个别风格下可能残留默认色，需在测试阶段逐组件走查（见 OQ-T03）；`dark/css-vars.css` 与我们的覆盖块依赖加载顺序（我们的样式放最后，同特异性后者生效）。

### ADR-027: 首屏无错误风格闪烁，本地记忆与账号偏好的优先级
- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-010（首屏即正确风格、切换 ≤ 1 s）、REQ-FUNC-072/078、REQ-FUNC-076（管理端固定 B）、AC-078-03（共用浏览器不串号）、AC-079-02/04、AC-090-02/03。
- Options:
  - A. 双层来源 + 同步内联脚本：`index.html` `<head>` 里一段同步内联脚本，在样式解析前读取设备记忆键 `ocap_theme` 并设置 `html[data-theme]`；变量 CSS 为静态样式表（ADR-024-A）；应用启动后再与账号偏好对账。优：首帧即正确；脚本极短。缺：内联脚本不能校验注册表（只做格式校验），未知 key 靠 CSS 的 `:root` 默认值回退 B。
  - B. 等 `GET /me/theme` 返回后再渲染。优：最准。缺：首屏被网络阻塞或白屏，违背 REQ-NFUNC-010 与 AC-090-03。
  - C. 只用账号偏好、不留本地记忆。缺：未登录页无法"沿用本设备记忆"（REQ-FUNC-078）。
- Decision: 选 A。优先级规则（固定）：
  1. 管理端路由（路径含 `/admin`）恒为 B，**不读取**设备记忆（REQ-FUNC-076）；
  2. 页面加载：用设备记忆 `ocap_theme`（有且合法）否则 B 立即渲染；
  3. 已登录：随后 `GET /me/theme`，**账号值权威**：账号值有效 → 应用并写回设备记忆；账号值为 NULL → 应用 B 并写回设备记忆（不沿用设备上其他账号的记忆，AC-078-03）；账号值不在注册表 → 回退 B（不改写数据库，REQ-FUNC-081）；请求失败 → 保持当前，不清空记忆（AC-090-03）；
  4. 登录流程：登录成功后先 `await GET /me/theme` 再跳转，故登录页保持原风格直到新账号风格就绪，无中间态；
  5. 点选：先本地应用并写设备记忆，再 `PUT /me/theme`；失败则回滚到之前的风格并提示"保存失败"（AC-076-03、AC-077-04）；
  6. 退出登录：保留设备记忆，登录页沿用（AC-079-02）。
- Consequences: 正向：首帧正确、无空白；规则可单元测试。负向：同一设备上换账号时，新账号登录的那一刻之前设备记忆属于上一个账号，由第 3、4 条覆盖；另一设备改了风格后，本设备刷新会先显示旧风格再切换（US-090-03 允许）。

### ADR-028: 小程序换肤方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-077、REQ-NFUNC-008/010。`uni.scss` 变量是**编译期**替换，无法运行期切换（用户在任务说明中指出，且 uni-app 官方文档定位其为编译期 SCSS 变量机制；我未做实机验证）。基线：全局样式写在 `App.vue` `<style>`，页面内联 `style` 共 71 处（`git grep -c 'style="' -- miniprogram/pages` 逐文件求和），tabBar 在 `pages.json` 为原生 tabBar `miniprogram/pages.json:21-28`。
- Options:
  - A. 每页根节点包一层 `ThemeRoot` 组件：以 `:style` 注入当前风格的 CSS 自定义属性（来自生成的注册表 token），子孙样式一律 `var(--…)`；原生 tabBar 用 `uni.setTabBarStyle`、导航栏用 `uni.setNavigationBarColor`、窗口背景用 `uni.setBackgroundColor` 同步。优：运行期切换瞬时；新增风格只需注册表新增条目；与 Web 的变量名完全一致，两端业务样式可复用同一套语义。缺：每页需套一层根容器（本期一次性改造）；原生部分只能改有限属性。
  - B. 为每个风格编写一份 SCSS，用 class（`.theme-neon` 等）全量编译多份规则。优：不依赖 CSS 变量。缺：规则数 × 风格数，包体增大（微信小程序有主包体积限制）；新增风格要改样式源码，违背 REQ-FUNC-074。
  - C. `uni.scss` 编译期变量。缺：运行期无法切换。不可行。
- Decision: 选 A。平台能力依据：`uni.setTabBarStyle` 支持 `color / selectedColor / backgroundColor / borderStyle`（`borderStyle` 仅 `black|white`），H5 与微信小程序均支持 [WEB: https://uniapp.dcloud.net.cn/api/ui/tabbar.html，2026-11-09]；`uni.setNavigationBarColor` 支持 `frontColor`（仅 `#ffffff` / `#000000`）与 `backgroundColor`，微信小程序支持 [WEB: https://uniapp.dcloud.net.cn/api/ui/navigationbar.html，2026-11-09]。tabBar 初值在 `pages.json` 写为风格 B 的色值，使默认风格零闪烁。
- Consequences: 正向：不依赖 `uni.scss`；两端变量同名。负向：存在我无法确认的平台细节（`uni.setBackgroundColor` 的页面/平台支持、WXSS 对 CSS 自定义属性与 `backdrop-filter` 的真机表现、`page-meta` 的支持），已列入开放问题 OQ-T04/T05，设计上均有不依赖它们的基线（只用 `ThemeRoot` + `setTabBarStyle` + `setNavigationBarColor`，小程序风格 A 不使用 `backdrop-filter`）。

### ADR-029: 页面改造策略（约 181 处内联样式）
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-075（一次改完用户端全部页面）、REQ-FUNC-076、REQ-FUNC-077、REQ-NFUNC-009。约束来源：用户 Q124=A（一次性改完，不分期）；Q118=A（以后新增风格不改业务页面）。基线 `git grep -c 'style="'` 逐文件求和：Web portal 133 + admin 48 = 181（与 GR-A-001 一致），小程序另有 71。
- 被排除方案：分期只改 3 个示例页（违反 Q124）；保留内联样式并用 `!important` 覆盖（脆弱、不可维护）。
- Decision: 本期**一次性**把页面中的内联颜色/圆角/阴影/间距改为基础样式表中的语义类（`.card .row .muted .title .btn .tag .page …`）或引用语义变量；这是"本期改造"，与"以后新增风格时业务页面改动数 = 0"不矛盾——后者约束的是新增风格的增量，前提正是本期完成改造。守护措施：新增前端测试扫描 `frontend/src` 与 `miniprogram/pages` 中的 `.vue` 文件，**禁止出现十六进制颜色字面量与 `rgb(a)/hsl` 字面量**（风格定义文件、生成物、基础样式表豁免），使"新增风格不改页面"可被自动验证（AC-080-02）。
- Consequences: 正向：改造完成后新增风格无页面改动；测试可守住不回退。负向：本期改动文件多（Web 25 个含内联样式的文件、小程序 11 个页面文件），回归风险集中在样式；靠现有 vitest 页面用例 + 契约测试 + 人工逐页清单兜底。

### ADR-030: 管理端固定风格 B 的实现
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-076、C-23。约束来源：用户 Q114=A、Q119=A；管理端与用户端是两种主体、令牌分开 `frontend/src/shared/http.js:15`、`backend/apps/accounts/models.py:43`，管理端无个人中心页。
- 被排除方案：给 `AdminAccount` 加偏好（违反"管理员不可切换"）；管理端复制一份独立样式（两套维护）。
- Decision: 同一 SPA 内，路由守卫 `afterEach` 按 `to.meta.admin` 把 `html[data-theme]` 设为 `bento`（该分支不读取也不写入设备记忆与账号偏好）；`index.html` 内联脚本对路径含 `/admin` 的首屏同样直接设为 `bento`。管理端布局（`AdminLayout.vue`）不渲染任何风格选择入口；后端 `IsMember` 对管理员令牌访问 `/me/theme` 返回 403（`permissions.py:31-32`），保证管理员无法写偏好。
- Consequences: 正向：不新增管理端数据与接口。负向：用户端与管理端共享 SPA，须保证从 `/admin` 跳回用户端路由时按 ADR-027 重新应用用户风格（`afterEach` 两个分支都处理）。

### ADR-031: 响应式与 Web 窄屏底部标签栏
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-079（窄屏隐藏顶部导航、底部 5 标签：首页、决议、投票、报销、我的；表单提交吸底）、REQ-FUNC-080（导航高亮）、REQ-NFUNC-006（点击区域 ≥ 44px）。基线：`PortalLayout.vue:4-20` 顶部导航 8 项、无高亮、无响应式；`Claims.vue` 含表单（21 处内联样式）。
- Options:
  - A. 同一布局组件内用 CSS 媒体查询切换：顶部导航与底部标签栏同时存在于 DOM，按断点显示其一；吸底使用 `position: sticky` 的操作栏类，底部预留标签栏高度与 `env(safe-area-inset-bottom)`。优：无 JS 判断、无首帧跳变、窗口缩放即时响应。缺：DOM 里有一份被隐藏的导航。
  - B. JS 读取窗口宽度/UA 决定渲染哪套导航。缺：首帧可能跳变；SSR 无关但仍多一类状态；与 REQ-NFUNC-010 精神冲突。
- Decision: 选 A。断点取 768px（`max-width: 767.98px` 为窄屏）`[ASSUMPTION]`，需求只说"窄屏"，具体断点留给设计，用户未指定，见 OQ-T06。底部 5 标签对应路由 `/`、`/resolutions`、`/polls`、`/claims`、`/me`；高亮用"当前路径前缀匹配"（`/` 仅精确匹配），故 `/resolutions/:id` 高亮"决议"。顶部导航中的"待办/我的房屋/收入表/财务报表"在窄屏下不出现在底部栏，须在首页或个人中心提供入口（OQ-T06）。
- Consequences: 正向：布局与风格正交，三套风格共用。负向：窄屏下 4 个次要入口需要补入口位置，影响首页与个人中心的内容编排。

### ADR-032: 减少动态效果与低端设备降级
- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-007（`prefers-reduced-motion` 时装饰动效与页面切换过渡归零）、REQ-NFUNC-008（风格 A 玻璃模糊在低端设备降级为半透明纯色，无数值指标，降级后对比度 ≥ 4.5:1）。原型已有该媒体查询 `project_workspace/ocap/design/prototype.html:367`。
- Options:
  - A. 纯 CSS：`@media (prefers-reduced-motion: reduce)` 全局关闭 `animation/transition` 并令装饰层不可见；低端设备由一小段启动脚本按启发式（`navigator.deviceMemory` ≤ 4 或 `navigator.hardwareConcurrency` ≤ 4）设置 `html[data-perf="low"]`，CSS 在该属性下把 `--blur` 置 0 并把 `--glass` 换为不透明度更高的纯色（该纯色在风格定义里单独声明并参与对比度校验）。优：不引入依赖，降级有明确触发点。缺：启发式不完美（`deviceMemory` 只在部分浏览器存在）。
  - B. 运行期测帧率后自适应降级。缺：需求明确不设帧率指标；实现复杂、有抖动风险。
- Decision: 选 A。启发式只用于风格 A 的模糊（其他风格无模糊）。小程序侧：风格 A 在小程序**不使用** `backdrop-filter`，直接用半透明纯色（天然已是降级形态）；小程序没有已确认的"减少动态效果"检测接口（OQ-T05），故小程序**不设循环装饰动画**，使 AC-089-01 在小程序以"构造上为 0"满足；页面切换动画由原生导航决定，是否可关属平台能力，列入 OQ-T05。
- Consequences: 正向：满足需求且无新依赖。负向：低端设备判定为启发式，测试报告须如实给出"降级是否生效与流畅度结论"（AC-089-03）；小程序页面切换动画的关闭未必可做。

### ADR-033: 可访问性对比度在最终色值上的核对方式
- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-005（正文/次要/强调 ≥ 4.5:1；design_spec §5 的 12 个组合均不低于表内值）、AC-088-01/04、C-21（最终色值以用户确认为准，design_spec 值为 PM 计算）。
- Options:
  - A. 风格定义中声明 `contrast` 字段（待测组合：前景 token、背景 token、阈值），构建脚本按 WCAG 2.1 相对亮度公式计算，低于阈值即视为不合规（该风格不进入列表，构建 `--strict` 失败）；同时新增 vitest 用例读取最终色值输出每个组合的实测值。优：每次改色值自动复核，新增风格同样受保护（AC-080-03）；无依赖。缺：渐变背景（主按钮、Hero）需取"最不利端点色"逐点测算，由风格定义显式列出端点。
  - B. 人工用外部工具抽检。缺：不可重复，色值一改就失效。
- Decision: 选 A。点击区域 ≥ 44px 与焦点可见由基础样式表统一设定（`--hit-min: 44px`），测试以样式规则断言 + 人工走查（AC-088-02/03）。
- Consequences: 正向：对比度成为可回归的自动检查。负向：渐变与半透明叠加背景的"实际背景色"需要在风格定义里给出等效不透明背景，若不准确会导致误判或漏判，设计复核时需人工确认等效色（OQ-T07）。

## 开放问题 / ASSUMPTION

| ID | 内容 | 类型 / 影响 |
|---|---|---|
| OQ-T01 | 风格显示名文案（"霓虹玻璃""极光 Bento""赛博终端"）与最终色值需用户确认（C-21，AC-074-01） | 需用户确认；不阻断设计 |
| OQ-T02 | 小程序 `uni` 构建对工程根目录之外文件的处理未实测，所以设计采用"生成物复制进各工程"而非跨目录引用（ADR-024-A） | 已规避，开发阶段验证生成物可被两端构建 |
| OQ-T03 | Element Plus 内部是否还使用上文映射表之外的变量，导致个别组件在深色风格下残留默认色 | 测试阶段逐组件走查；映射表可在不改页面的前提下补充 |
| OQ-T04 | 微信小程序 WXSS 对 CSS 自定义属性的支持范围、`uni.setBackgroundColor` 在各页面的支持、`page-meta` 的可用性：未从官方文档核实 | 设计有不依赖它们的基线（ADR-028）；开发阶段需在微信开发者工具验证 |
| OQ-T05 | 小程序是否存在可用的"减少动态效果"与"设备性能等级"检测接口、原生页面切换动画能否关闭：未核实 | 基线策略见 ADR-032；若不能满足 AC-089-01 的页面切换项，需用户决定降低要求或用其他方案 |
| OQ-T06 | `[ASSUMPTION]` 窄屏断点 768px；窄屏下"待办/我的房屋/收入表/财务报表"的入口位置（建议放首页快捷入口与个人中心列表） | 用户或设计确认 |
| OQ-T07 | 对比度中渐变与半透明背景的等效色由风格定义给出，需设计/用户复核 | 开发前复核 |
| OQ-T08 | 小程序的构建产物如何发布（上传体验版/审核）不在画像 P7 中；本期只负责产出可构建的代码 | PM/用户 |
| OQ-T09 | Q125（小程序 tabBar 是否增加"报销"）：本设计按保持 4 项（`pages.json` tabBar 不变，仅运行期改色）；若改为 5 项，只影响 `pages.json` 与 AC-083-02 | 非阻断 |
| OQ-T10 | 偏好接口未设限流（只改本人一个字段，写入成本低）；如需防滥用，可复用现有 `RateLimiter.hit` `backend/apps/accounts/views.py` 中的用法 | `[ASSUMPTION]`，PM 门控确认 |
