<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-09T17:30:00+08:00</timestamp>
  <project_name>ocap_ui_theme</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md (0.1.0)</file>
    <file>architecture/module_design.md (0.1.0)</file>
    <file>../ocap/architecture/tech_stack.md (基线)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型：ocap 多风格界面（INCREMENTAL）

> 原则：沿用既有栈，**不新增任何第三方依赖**（用户约束 5；未经同意不安装依赖）。版本出处为仓库清单或本地实测。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 后端语言/框架 | Django + DRF | `Django>=5.2,<6.0`（画像 P1，`backend/requirements.txt`）；测试机 5.2.19（画像 P7）。**不得用 6.x 生成迁移**（画像 P4） | 沿用 | 偏好接口是 `APIView` + `IsMember`，与既有模式一致 | REQ-FUNC-072 | 低 |
| 数据存储 | MySQL（测试环境库 `ocap`）/ SQLite 内存库（测试） | 画像 P1 | 沿用 | 新增一个可空 `CharField`，两种库行为一致；无新数据库/消息队列 | REQ-FUNC-072 | 低：见迁移风险 |
| 迁移 | 手写单 app 迁移 | 画像 P6 | 沿用 | `accounts/0002_user_theme_key.py` | REQ-NFUNC-009 | 低：测试不跑迁移，需手动往返验证 |
| Web 前端框架 | Vue 3 + vue-router + Pinia + Vite | `vue ^3.5.13`、`vue-router ^4.4.5`、`pinia ^2.1.7`、`vite ^6.0.1`（`frontend/package.json`）；实装 vite 6.4.5（`frontend/node_modules`） | 沿用 | 风格 store 用 Pinia，路由守卫用 vue-router | REQ-FUNC-069～081 | 低 |
| Web UI 组件库 | Element Plus | `^2.8.7`（`frontend/package.json`）；实装 2.14.8，MIT（`frontend/node_modules/element-plus/package.json`） | 沿用，**不改造为按需引入** | 换肤只靠 CSS 变量覆盖 + 官方 `dark/css-vars.css`（已核实存在）。按需引入插件（`unplugin-vue-components` 等）与换肤无关，引入会新增依赖与构建变量，故本期不采用 | REQ-FUNC-075/076 | 中：主色梯度变量需自行输出；个别组件可能漏映射（OQ-T03） |
| 小程序框架 | uni-app (Vue 3) + Pinia | `@dcloudio/uni-app ^3.0.0-4060620250520001`（`miniprogram/package.json`）；实装 `3.0.0-alpha-5030620261106001`；vite 实装 5.4.21（`miniprogram/node_modules`） | 沿用 | 运行期换肤用 `ThemeRoot` + CSS 变量 + `uni.setTabBarStyle` / `uni.setNavigationBarColor`；`uni.scss` 编译期变量不可用于运行期切换 | REQ-FUNC-077 | 中：Vue3 线仍为 alpha 标签（基线已记录）；若干平台能力待真机验证（OQ-T04/T05） |
| 风格定义与构建 | JSON 数据文件 + Node 脚本（仅用 `node:fs`/`node:path`） | Node：开发机 v22.23.3（`node --version` 实测）；CI 为 20（`.github/workflows/ci.yml:64,92`）。脚本须同时兼容 20 与 22 | **新增（自写，非第三方依赖）** | 单一来源、构建期校验与对比度计算；与 ADR-024 对应；无需新包 | REQ-FUNC-074；REQ-NFUNC-005 | 中：生成物与源可能漂移 → `--check` 测试守护；ESM `.mjs` 在 vitest 中被导入需确认配置（开发阶段验证） |
| 样式技术 | CSS 自定义属性 + 媒体查询（`prefers-reduced-motion`、断点 768px `[ASSUMPTION]`）+ `html[data-theme]`/`html[data-perf]` | 浏览器标准特性，无版本依赖 | 新增（无依赖） | 运行期切换瞬时，弹层继承 `html` 变量 | REQ-FUNC-069/079；REQ-NFUNC-007/008/010 | 低 |
| 字体 | 系统字体栈，不引入网络字体 | — | 沿用约束 | C-24、design_spec §2.2；原型字体名仅作栈中的候选，缺失则回退系统字体 | REQ-FUNC-069 | 低：不同设备字体不一致 |
| 测试 | Django test runner；vitest 2.x + @vue/test-utils + jsdom | `vitest ^2.1.9`、`@vue/test-utils ^2.4.6`、`jsdom ^25.0.1`（两个 `package.json`） | 沿用 | 新增用例落在画像 P3 规定位置：`backend/tests/integration/`、`frontend/tests/`、`miniprogram/tests/` | REQ-NFUNC-009 | 低 |
| 对比度核对 | 构建脚本内置 WCAG 2.1 相对亮度公式 + vitest 断言 | 公式为公开标准 | 新增（自写） | 色值一改即自动复核；不引入外部库 | REQ-NFUNC-005 | 中：渐变/半透明背景需给等效色（OQ-T07） |
| 进程管理 | systemd `ocap-backend` + nginx | 画像 P7 | 沿用 | 后端需迁移+重启；前端静态替换 | — | 低 |
| CI/CD | GitHub Actions `ci.yml` | `.github/workflows/ci.yml` | 沿用，建议加一步 `node scripts/themes/build.mjs --strict --check` | 防止生成物漂移与不合规风格入库（由后续阶段落实） | REQ-FUNC-074 | 低 |
| 部署方式 | 物理机 tar → scp → 迁移 → systemd 重启，不用容器 | 画像 P7、P8 | 沿用 | 禁用 Docker | — | 低 |
| 新增第三方依赖 | **无** | — | — | 见开头原则；许可证/维护风险项不适用 | — | — |

## 技术风险

### High
- 无。

### Medium
1. **Element Plus 漏映射导致深色风格残留默认色**。缓解：映射表集中在构建脚本一处，补充不改页面；测试阶段对所用组件（`el-button/input/select/table/dialog/message/tag/form/pagination/date-picker` 等，以 `git grep` 为准）逐个在 A、C 下走查。
2. **小程序平台能力未核实（WXSS 变量与 `backdrop-filter`、`uni.setBackgroundColor`、`page-meta`、减少动态效果检测、原生页面切换动画）**。缓解：设计基线不依赖它们（ADR-028、ADR-032）；开发阶段在微信开发者工具验证；不满足 AC-089-01 的页面切换项时回报用户决策（OQ-T05）。
3. **一次性改造 25 个 Web 文件（181 处内联样式）与 11 个小程序页面（71 处）的样式回归**。缓解：颜色字面量守护测试、现有页面用例、契约测试、逐页人工清单（14/14、9/9、11/11）。
4. **对比度等效色与渐变端点**。缓解：风格定义中显式声明等效背景，构建期计算，设计复核（OQ-T07）。
5. **生成物与源漂移**。缓解：`--check` 纳入 vitest 与 CI。

### Low
1. **低端设备判定为启发式**（`navigator.deviceMemory` 并非所有浏览器提供）。缓解：仅影响风格 A 的模糊降级，测试报告如实给出结论（AC-089-03）。
2. **迁移未被测试覆盖（测试 `MIGRATION_MODULES` 置空）**。缓解：开发机对 SQLite 文件库手动 `migrate` 与回退一次；漂移检查只检查不提交。
3. **窄屏断点 768px 为假设**。缓解：断点为单一 CSS 变量/常量，OQ-T06 确认后可调。
4. **后端存储格式合法但未注册的 key**。缓解：客户端回退 B（REQ-FUNC-081），无安全影响。
