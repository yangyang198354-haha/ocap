<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-09T17:20:00+08:00</timestamp>
  <project_name>ocap_ui_theme</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0)</file>
    <file>requirements/user_stories.md (1.0.0)</file>
    <file>architecture/architecture_design.md (0.1.0)</file>
    <file>../ocap/architecture/module_design.md (基线，至 MOD-022 / IFC-141)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：ocap 多风格界面（INCREMENTAL）

> 编号接续基线：MOD-023 起、IFC-142 起。接口只写签名与契约，不含函数体。`新建`/`修改` 均相对当前仓库。
> 通用词：风格 key = 字符串，格式 `^[a-z][a-z0-9_-]{1,31}$`；本期三套 key 暂定 `neon`（A 霓虹玻璃）、`bento`（B 极光 Bento，默认）、`terminal`（C 赛博终端）`[ASSUMPTION]`，用户可改名，不影响设计。

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-023 | 账号风格偏好（后端） | 修改 `backend/apps/accounts/models.py`、`services.py`、`views.py`、`urls.py`；新建 `backend/apps/accounts/migrations/0002_user_theme_key.py`；新建测试 `backend/tests/integration/test_theme_preference_api.py` | 存取账号级风格偏好，仅本人可读写 | REQ-FUNC-070/072/073；US-075/078/091 | 无（复用 `core.permissions.IsMember`、`core.errors.ApiError`） |
| MOD-024 | 风格定义与构建 | 新建 `themes/*.theme.json`（3 份）、可选 `themes/*.web.css` / `*.mp.css`、`themes/schema.mjs`、`scripts/themes/build.mjs`；生成物 `frontend/src/theme/generated/{themes.css,registry.js}`、`miniprogram/theme/generated/{registry.js,themes.scss}` | 风格定义单一来源；校验并生成两端产物；对比度校验 | REQ-FUNC-069/074；REQ-NFUNC-005/008；US-074/080/088 | 无 |
| MOD-025 | Web 风格运行时 | 新建 `frontend/src/theme/{store.js,apply.js,ThemePicker.vue}`；修改 `frontend/index.html`、`frontend/src/main.js`、`frontend/src/router/index.js`、`frontend/src/shared/api.js`、`frontend/src/shared/style.css`、`frontend/src/portal/Me.vue`、`frontend/src/portal/Login.vue`（登录后对账）、`frontend/src/stores/auth.js` | 应用风格、对账优先级、点选保存、管理端固定 B、减少动态/低端降级、Element Plus 映射启用 | REQ-FUNC-069～073/076/078/081；REQ-NFUNC-007/008/010；US-074～076/078/079/082/086/089/090 | MOD-023（IFC-142/143）、MOD-024（生成物） |
| MOD-026 | Web 布局与响应式 | 修改 `frontend/src/portal/PortalLayout.vue`、`frontend/src/admin/AdminLayout.vue`；新建 `frontend/src/portal/BottomTabBar.vue` | 顶部导航高亮、窄屏底部 5 标签、吸底操作栏容器 | REQ-FUNC-079/080/076；REQ-NFUNC-006；US-084/085/082 | MOD-025（变量与类名） |
| MOD-027 | Web 页面换肤改造 | 修改 `frontend/src/portal/*.vue`（Claims、Income、Login、Me、PollDetail、Polls、Reports、ResolutionDetail、Resolutions、Register、Tasks、Units、Home、WechatCallback）与 `frontend/src/admin/*.vue`（AdminAppeals、AdminAudit、AdminFinance、AdminFlows、AdminLogin、AdminMemberships、AdminRegistry、AdminSeats、AdminUsers）；新建 `frontend/tests/theme.spec.js`、`frontend/tests/theme_build.spec.js` | 内联样式改为语义类；状态标签"圆点+文字+底色/描边"；关键组件按 design_spec §4 | REQ-FUNC-075/076/082；REQ-NFUNC-005/006；US-081/082/087/088 | MOD-025、MOD-026 |
| MOD-028 | 小程序风格运行时 | 新建 `miniprogram/theme/{apply.js,ThemeRoot.vue}`（路径：`miniprogram/components/ThemeRoot.vue`）、`miniprogram/store/theme.js`；修改 `miniprogram/utils/api.js`、`miniprogram/App.vue`、`miniprogram/pages.json`（tabBar 初值为风格 B 色值，列表仍 4 项）、`miniprogram/pages/login/index.vue`（登录后对账）、`miniprogram/store/auth.js` | 注入风格变量、同步原生 tabBar/导航栏、与账号偏好同步 | REQ-FUNC-069～073/077/078/081；REQ-NFUNC-007/008/010；US-077/083/086/090 | MOD-023（IFC-142/143）、MOD-024（生成物） |
| MOD-029 | 小程序页面换肤改造 | 修改 `miniprogram/pages/*/index.vue` 与 `pages/*/detail.vue`（共 11 页）；`pages/me/index.vue` 增加风格选择区块；新建 `miniprogram/tests/theme.spec.js` | 页面根套 `ThemeRoot`；内联样式改语义类；状态标签 | REQ-FUNC-071/077/082；US-077/083/087 | MOD-028 |

## 模块详情

### MOD-023 账号风格偏好（后端）
- 职责：为普通用户保存/读取一个风格 key；未设置为 `NULL`（语义 = 默认 B，由客户端解释）。
- 数据：`User.theme_key = models.CharField(max_length=32, null=True, blank=True)`（位置：`backend/apps/accounts/models.py` 的 `User`，紧随 `cancelled_at`）。
- 服务签名（`AccountService`，`backend/apps/accounts/services.py`）：
  - `set_theme(user: User, theme: str) -> User`：格式校验后 `save(update_fields=["theme_key"])`。
  - 读取直接取 `user.theme_key`。
- 接口：

**IFC-142 `GET /api/v1/me/theme`**
- 鉴权：`permission_classes = [IsMember]`（`backend/apps/core/permissions.py:28`）；未登录 401 `UNAUTHORIZED`，管理员令牌 403 `FORBIDDEN`（同文件 :31-32）。仅返回 `request.user` 自己的值，无用户 id 参数 → 他人偏好不可达（AC-091-04）。
- 输入：无。
- 响应 200：`{"theme": string | null}`（单对象，非列表；`null` 表示从未选择）。

**IFC-143 `PUT /api/v1/me/theme`**
- 鉴权：同上 `IsMember`。
- 请求体：`{"theme": string}`，必填。
- 输入校验：`theme` 必须是字符串，匹配 `^[a-z][a-z0-9_-]{1,31}$`（长度 2~32）；缺失、非字符串、不匹配 → 400 `ApiError("INVALID_VALUE", "风格标识不合法")`；不校验是否属于启用集合（ADR-025）。不允许传 `null`（本期无"恢复默认"操作）。
- 响应 200：`{"theme": string}`（保存后的值）。
- 副作用：仅更新 `theme_key`，不写审计、不影响令牌与资料。
- URL 注册：`backend/apps/accounts/urls.py` 追加 `path("me/theme", ThemePreferenceView.as_view())`（`ThemePreferenceView` 新建于 `views.py`，含 `get` / `put`）。
- 迁移：见"数据迁移"。
- 依赖模块：无。外部依赖：无。

### MOD-024 风格定义与构建
- 职责：`themes/` 是风格的唯一来源；脚本校验并生成两端消费的产物。
- **IFC-144 风格定义文件 `themes/<key>.theme.json`**（TypeScript 形式描述契约）：

```ts
type HexColor = string            // '#RRGGBB'
interface ThemeDefinition {
  schemaVersion: 1
  key: string                     // 与文件名 <key> 一致；格式同 ADR-025
  name: string                    // 显示名，1~12 字符
  order: number                   // 列表排序，整数
  scheme: 'dark' | 'light'        // 固定明暗；不提供跟随系统
  swatch: [HexColor, HexColor, HexColor]   // 选择器缩略色块
  tokens: {                       // 全部必填
    bg: HexColor; surface: string; text: HexColor; muted: HexColor; line: string
    accent: HexColor; accent2: HexColor; accentText: HexColor; onAccent: HexColor
    accentBg: string              // 主按钮背景（可为渐变）
    success: HexColor; warning: HexColor; danger: HexColor
    radiusSm: string; radiusMd: string; radiusLg: string   // 如 '12px'
    shadow: string; font: string; mono: string
    glass: string; glassLowEnd: string; blur: string       // glassLowEnd = 低端设备降级时的不透明纯色
    decor: '0' | '1'              // 装饰层（光斑/扫描线等）是否存在
  }
  native: {                       // 小程序原生部分
    tabBar: { color: HexColor; selectedColor: HexColor; backgroundColor: HexColor; borderStyle: 'black' | 'white' }
    navBar: { frontColor: '#ffffff' | '#000000'; backgroundColor: HexColor }
    windowBackground: HexColor
  }
  contrast: Array<{ fg: keyof tokens | HexColor; bg: HexColor; min: number; label: string }>
        // bg 为"等效不透明背景色"，渐变取最不利端点；min 不得低于 4.5（普通文字）
}
```

  可选同名 `themes/<key>.web.css`、`themes/<key>.mp.css`：仅用于结构性差异（如 C 的终端式列表、A 的光斑层），选择器必须以 `[data-theme="<key>"]`（Web）/ `.theme-<key>`（小程序）开头，由脚本拼入生成物；业务页面无需感知。
- **IFC-145 构建命令** `node scripts/themes/build.mjs [--strict] [--check]`
  - 行为：读取 `themes/*.theme.json` → 校验（字段完整、颜色格式、`key` 与文件名一致、key 唯一、`contrast` 全部达标）→ 通过的写入生成物；**不合规者不写入注册表**，向 stderr 输出 `themes/<file>:<字段路径>: <原因>`（AC-080-03 的"可定位错误"）。
  - `--strict`：存在任何不合规定义时退出码 1（CI 使用）；缺省退出码 0（便于本地逐个调试）。
  - `--check`：不写文件，仅比较"重新生成的内容"与已提交生成物，不一致退出码 1（供测试与 CI 使用）。
  - 默认风格：脚本要求 `bento` 必须存在且合规，否则任何模式均退出码 1（`:root` 默认值取自它）。
- 生成物契约：
  - `frontend/src/theme/generated/themes.css`：`:root{…B 的变量…}`、各 `html[data-theme="<key>"]{…业务变量 + --el-* 映射…}`、`html[data-perf="low"]` 降级规则、`@media (prefers-reduced-motion: reduce)` 规则、拼入的 `.web.css`。
  - `frontend/src/theme/generated/registry.js`：`export const THEMES: ReadonlyArray<{key:string; name:string; order:number; scheme:'dark'|'light'; swatch:string[]}>`、`export const DEFAULT_THEME = 'bento'`。
  - `miniprogram/theme/generated/registry.js`：同上并附 `tokens: Record<string,string>` 与 `native`；`miniprogram/theme/generated/themes.scss`：拼入的 `.mp.css` 规则。
- 依赖：仅 Node 内置模块（`node:fs`、`node:path`），无第三方包。

### MOD-025 Web 风格运行时
- 职责：见 ADR-026/027/030/032。
- **IFC-146 Web 风格 store**（`frontend/src/theme/store.js`，Pinia）：

```ts
function useThemeStore(): {
  current: string                         // 当前生效 key（已回退过的）
  list: ReadonlyArray<ThemeMeta>          // 来自 generated/registry.js，按 order 排序
  initFromDevice(): void                  // 读 localStorage['ocap_theme']，不合法则 DEFAULT_THEME
  reconcileAfterLogin(): Promise<void>    // GET /me/theme；账号值权威（ADR-027 第 3 条）；失败静默保持当前
  select(key: string): Promise<void>      // 乐观应用 + 写设备记忆 + PUT；失败回滚并抛出，调用方提示"保存失败"
  forAdminRoute(): void                   // 固定 bento，不读写设备记忆
}
```

- **IFC-147 DOM 应用函数**（`frontend/src/theme/apply.js`）：`applyTheme(key: string, scheme: 'dark'|'light'): void`（设置 `html[data-theme]`；scheme 为 dark 时给 `html` 加 `dark` 类，用于 Element Plus 官方 `dark/css-vars.css`）；`detectLowEnd(): boolean`（启发式，设置 `html[data-perf]`）。
- **IFC-150 `frontend/src/shared/api.js` 追加**（画像 P6：两处契约同步）：
  - `meApi.theme: () => get('/me/theme')` → `{ theme: string | null }`
  - `meApi.setTheme: (theme: string) => http.put('/me/theme', { theme })` → `{ theme: string }`
- 其他修改点：
  - `frontend/index.html`：`<head>` 内同步内联脚本（读 `ocap_theme`，路径含 `/admin` 时用 `bento`，格式不符则不设置）；加 `<meta name="viewport">` 已存在，不改。
  - `main.js`：在 `./shared/style.css` 之后引入 `./theme/generated/themes.css`，并在 `element-plus/dist/index.css` 之后引入 `element-plus/theme-chalk/dark/css-vars.css`（顺序保证我们的覆盖最后生效）。
  - `router/index.js`：`router.afterEach`：`to.meta.admin` → `forAdminRoute()`；否则 `initFromDevice()`（已登录则触发 `reconcileAfterLogin()`）。现有 `beforeEach` 不改（`router/index.js:46-54`）。
  - `Me.vue`：新增"界面风格"区块，渲染 `ThemePicker`（`frontend/src/theme/ThemePicker.vue`，列表来自 `store.list`，每项带色块 `swatch` + 名称，选中态可见；保存失败 `ElMessage.error('保存失败…')`）。
  - 登录页（`Login.vue`）登录成功后：`await store.reconcileAfterLogin()` 再跳转；不提供任何风格入口（AC-079-03）。`WechatCallback.vue`、`Register.vue` 登录成功路径同样先对账再跳转。
- 依赖：MOD-023（IFC-142/143，经 IFC-150）；MOD-024 生成物。外部依赖：Element Plus（沿用 2.14.8，不新增）。

### MOD-026 Web 布局与响应式
- 职责：见 ADR-031。
- **IFC-148 底部标签栏组件** `frontend/src/portal/BottomTabBar.vue`：无 props；固定 5 项 `[{label:'首页',to:'/'},{label:'决议',to:'/resolutions'},{label:'投票',to:'/polls'},{label:'报销',to:'/claims'},{label:'我的',to:'/me'}]`，每项图标 + 文字标签；当前项依据 `route.path` 前缀匹配（`/` 仅精确）高亮；每项点击区域高 ≥ 44px；断点以上 `display:none`。
- 修改：`PortalLayout.vue` 顶部导航增加同样的当前项高亮；窄屏隐藏顶部导航并渲染 `BottomTabBar`；内容区底部留出标签栏高度。基础样式表提供 `.form-actions-sticky`（窄屏 sticky 于标签栏上方，宽屏恢复静态），用于 `Claims.vue` 等表单的提交按钮容器。`AdminLayout.vue` 只做去内联样式，不加风格入口。
- 依赖：MOD-025。外部依赖：vue-router（沿用）。

### MOD-027 Web 页面换肤改造
- 职责：每个页面的内联颜色/圆角/阴影改为 `style.css` 提供的语义类（`.page .card .row .muted .title .btn …`）或 `var(--…)`；状态标签组件化为 `.tag` + `.tag-dot` + 语义色类 `.is-success/.is-warning/.is-danger`（"圆点 + 文字 + 底色/描边"，REQ-FUNC-082）；决议卡片、金额输入、申请类型选择、附件区、审批流程预览按 design_spec §4。
- 守护测试（新建）：
  - `frontend/tests/theme.spec.js`：扫描 `frontend/src/**/*.vue`，除生成物与 `style.css` 外不得含十六进制/`rgb()`/`hsl()` 颜色字面量；`ThemeStore` 优先级规则（ADR-027 六条）；未知 key 回退；管理端固定 B；构造"测试风格 D"定义并经构建函数校验后出现在 `THEMES`（AC-080-01），缺字段的不出现（AC-080-03）。
  - `frontend/tests/theme_build.spec.js`：`build.mjs --check` 通过；对每个风格逐项计算 `contrast` 并断言 ≥ 阈值，12 个组合不低于 design_spec §5 表内值（AC-088-01）。
- 依赖：MOD-025、MOD-026。

### MOD-028 小程序风格运行时
- 职责：见 ADR-028。
- **IFC-149 `ThemeRoot` 组件**（`miniprogram/components/ThemeRoot.vue`）：无 props、默认插槽；根节点 `<view class="theme-root theme-{{key}}" :style="cssVars">`，`min-height:100vh` 并以 `--bg` 为背景；`setup` 同步读取 `uni.getStorageSync('ocap_theme')` 得初值（首帧即正确）；挂载与风格变化时调用 `applyNative(key)`。
- **IFC-151 小程序 store**（`miniprogram/store/theme.js`，Pinia，与 IFC-146 同形）：`current`、`list`、`initFromDevice()`、`reconcileAfterLogin()`、`select(key)`、`applyNative(key)`（调用 `uni.setTabBarStyle`、`uni.setNavigationBarColor`，`uni.setBackgroundColor` 视 OQ-T04 而定；非 tabBar 页调用 `setTabBarStyle` 失败时吞掉错误）。
- **`miniprogram/utils/api.js` 追加**（IFC-151 的 API 部分，与 IFC-150 同步）：`theme: () => http.get('/me/theme')`，`setTheme: (theme) => http.put('/me/theme', { theme })`（`http.put` 已存在 `miniprogram/utils/http.js:80`，无需补齐）。
- `App.vue` 全局样式改为引用变量类；`pages.json` 的 tabBar `color / selectedColor` 初值写风格 B 色值，列表仍为 4 项（OQ-T09）。
- 登录页登录成功后先 `await reconcileAfterLogin()` 再 `reLaunch`/`switchTab`；无风格入口。
- 依赖：MOD-023；MOD-024 生成物。外部依赖：uni-app API（沿用现有版本）。

### MOD-029 小程序页面换肤改造
- 职责：11 个页面根节点包 `ThemeRoot`；去内联样式；状态标签同 MOD-027；`pages/me/index.vue` 新增"界面风格"区块（列表来自 store，点选调用 `select`，失败 `uni.showToast({ title: '保存失败', icon: 'none' })` 并回滚）。
- 测试：`miniprogram/tests/theme.spec.js`（store 规则、`ThemeRoot` 变量注入、`me` 页点选与回滚）；`miniprogram/tests/setup.js` 的 `uni` 桩需补 `setTabBarStyle`、`setNavigationBarColor`、`put` 对应请求桩（该桩只模拟 API，不代表真机行为）。
- 依赖：MOD-028。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-069 | US-074 | MOD-024、MOD-025、MOD-028 |
| REQ-FUNC-070 | US-075 | MOD-023、MOD-025、MOD-028 |
| REQ-FUNC-071 | US-076、US-077 | MOD-025、MOD-029 |
| REQ-FUNC-072 | US-078 | MOD-023、MOD-025、MOD-028 |
| REQ-FUNC-073 | US-076 | MOD-023、MOD-025 |
| REQ-FUNC-074 | US-080 | MOD-024（+ MOD-027 守护测试） |
| REQ-FUNC-075 | US-081 | MOD-025、MOD-026、MOD-027 |
| REQ-FUNC-076 | US-082 | MOD-025、MOD-026、MOD-027 |
| REQ-FUNC-077 | US-077、US-083 | MOD-028、MOD-029 |
| REQ-FUNC-078 | US-079 | MOD-025、MOD-028 |
| REQ-FUNC-079 | US-084 | MOD-026、MOD-027 |
| REQ-FUNC-080 | US-085 | MOD-026 |
| REQ-FUNC-081 | US-086 | MOD-025、MOD-028 |
| REQ-FUNC-082 | US-087 | MOD-027、MOD-029 |
| REQ-NFUNC-005 | US-088 | MOD-024、MOD-027 |
| REQ-NFUNC-006 | US-088 | MOD-025（基础样式）、MOD-026、MOD-027、MOD-029 |
| REQ-NFUNC-007 | US-089 | MOD-024（生成的媒体查询）、MOD-025、MOD-028 |
| REQ-NFUNC-008 | US-089 | MOD-024、MOD-025、MOD-028 |
| REQ-NFUNC-009 | US-091 | MOD-023（偏好隔离、契约）、MOD-027（守护测试）、全部（测试策略） |
| REQ-NFUNC-010 | US-090 | MOD-025、MOD-028 |

## 依赖关系

- MOD-025 → MOD-023（经 IFC-142/143，由 IFC-150 调用）
- MOD-025 → MOD-024（消费生成物）
- MOD-026 → MOD-025
- MOD-027 → MOD-025、MOD-026
- MOD-028 → MOD-023（经 IFC-142/143，由 IFC-151 调用）
- MOD-028 → MOD-024（消费生成物）
- MOD-029 → MOD-028
- MOD-023、MOD-024 无上游依赖

已检查：无循环依赖（依赖方向为 024/023 ← 025/028 ← 026/029 ← 027）。

## 测试策略与契约

- 后端：原有 120 个用例全部通过 + 新增用例全过（GR-A-002-F01 的表述）。新增 `backend/tests/integration/test_theme_preference_api.py`：未登录 401；管理员令牌 403；用户 GET 初始为 `null`；PUT 合法 key 后 GET 一致；非法值（空、`null`、数字、大写、含空格、33 字符、1 字符）→ 400 `INVALID_VALUE`；用户 A/B 互不影响（AC-078-03、AC-091-04）；老用户（迁移前创建，无需回填）GET 为 `null`（AC-075-01）。
- 契约：现有 `backend/tests/integration/test_frontend_contract.py` 用正则解析 `frontend/src/shared/api.js` 与 `miniprogram/utils/api.js` 中的 `get/post/put/patch/delete('/…')` 调用并 `resolve("/api/v1"+path)`；IFC-150/151 的写法（`get('/me/theme')`、`http.put('/me/theme', …)`）符合该正则，自动覆盖新路径（AC-078-04、AC-091-02）。须在该文件为 `/me/theme` 增加字段级用例（响应键 `theme`、请求键 `theme`）。
- 前端/小程序：见 MOD-027、MOD-029 的测试；现有用例零新增失败；`frontend/tests/pages.spec.js`、`miniprogram/tests/pages.spec.js` 若按文本或结构断言，需随改造同步更新并说明。
- 视觉走查（逐页 14/14、9/9、11/11）、低端设备降级与帧流畅度结论、首屏无闪烁录屏：属 E2E/人工清单（AC-081、AC-082、AC-083、AC-089-03、AC-090-02），不是自动化可替代的项。

## 数据迁移

- 新字段：`accounts_user.theme_key`（`CharField(max_length=32, null=True, blank=True)`，无默认值、无索引、无唯一约束；现有 MySQL 与 SQLite 均无需回填，NULL = 未选择）。
- 迁移文件：`backend/apps/accounts/migrations/0002_user_theme_key.py`，**手写**、单 app（仅 `accounts`）、`dependencies = [("accounts", "0001_initial")]`、单个 `migrations.AddField`；文件头不得出现 "Generated by Django"（画像 P6、P8）；不得用 Django 6.x 生成或校验（画像 P4）。
- 可逆：是（`AddField` 的反向为删除该列）。
- 数据风险：加可空列无默认值，MySQL 上为快速元数据变更或轻量表重建（用户表规模小）`[ESTIMATE]`；回滚会丢弃已保存的风格偏好（可接受）。
- 校验：迁移漂移检查 `python manage.py makemigrations --check --dry-run --settings=config.test_settings`（只检查，产物不提交）；测试用 `MIGRATION_MODULES` 置空，不跑迁移（画像 P4），故迁移文件的正确性另需在开发机对 SQLite 文件库手动 `migrate`/`migrate accounts 0001` 往返验证一次（不连测试机数据库）。

## 受影响的运行单元 / 构建

| 单元 | 动作 | 依据 |
|---|---|---|
| systemd `ocap-backend`（gunicorn） | 部署后需执行迁移并**重启** | 新增模型字段、视图、路由（画像 P7） |
| nginx（站点 `ocap`，8090） | 无需改动、无需重启 | 仅替换静态文件 |
| Web 前端静态文件 | **重新构建** `npm run build -- --base=/ocap/` 并替换 `/home/yangyang/ocap/web` | 前端全部页面与样式变更 |
| 小程序 | **重新构建** `build:mp-weixin`；发布方式不在画像 P7（OQ-T08） | 页面与 tabBar 初值变更 |
| 风格构建脚本 | 开发机/CI 在构建前运行 `node scripts/themes/build.mjs --strict`（建议纳入 `.github/workflows/ci.yml` 与前端/小程序 `prebuild`，由开发/DevOps 阶段落实） | ADR-024 |
| 定时任务（`run_due_jobs` timer）、Freeark 相关 | 无影响 | — |
| 固件/比特流 | 不适用 | — |

## 领域与外部依赖出处

画像 P11-3 的外部 API（微信/阿里云/邮件）与本次改动无关，不调用、不修改；下表登记本设计引用的**平台能力**与既有代码事实。

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| IFC-142/143 | `IsMember` 对管理员返回 403、未登录 401 | [CODE: backend/apps/core/permissions.py:28-34] |
| IFC-143 | `ApiError(code, message, http_status=400)` | [CODE: backend/apps/core/errors.py:6-12] |
| IFC-143 | 既有视图用 `ApiError("INVALID_VALUE", …)` 表达非法取值 | [CODE: backend/apps/accounts/services.py:338,342] |
| IFC-150/151 | 契约测试按 `get/post/put/patch/delete('/path')` 正则解析 api.js | [CODE: backend/tests/integration/test_frontend_contract.py:29-32] |
| MOD-028 | `uni.setTabBarStyle` 支持 color/selectedColor/backgroundColor/borderStyle（black\|white），H5 与微信小程序支持 | [WEB: https://uniapp.dcloud.net.cn/api/ui/tabbar.html，2026-11-09] |
| MOD-028 | `uni.setNavigationBarColor` 的 frontColor 仅 #ffffff/#000000，微信小程序支持 | [WEB: https://uniapp.dcloud.net.cn/api/ui/navigationbar.html，2026-11-09] |
| MOD-025 | Element Plus 2.14.8 带 `theme-chalk/dark/css-vars.css` | [LOCAL: frontend/node_modules/element-plus（ls 实测，2026-11-09）] |
| MOD-028 | WXSS 对 CSS 自定义属性/`backdrop-filter`、`uni.setBackgroundColor`、`page-meta`、减少动态效果检测 | [UNSOURCED]，已写入 OQ-T04/T05，设计不依赖 |
