<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-09T22:21:05+08:00</timestamp>
  <project_name>ocap_ui_theme</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>testing/integration_test_report.md</file>
    <file>development/implementation_plan.md</file>
    <file>architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：ocap 多风格界面

## 摘要

- `git diff --stat`（已跟踪文件）：43 files changed, 395 insertions(+), 94 deletions(-)；其中 `.claude/agent-memory/pm-orchestrator/MEMORY.md`、`project_workspace/_kb_inbox.jsonl` 为开发前已存在的 PM 改动，不属本次产出。新建文件另见 implementation_plan 清单（后端迁移与测试、`themes/`、`scripts/themes/`、`frontend/src/theme/`、`frontend/tests/theme*.spec.js`、`miniprogram/{components,theme,store/theme.js,tests/theme.spec.js}` 等）。
- 0.2.0 返工（GR-C-001 FAIL）：`git diff --stat`（已跟踪）44 files changed, 926 insertions(+), 167 deletions(-)，其中 `.claude/agent-memory/**`、`project_workspace/_kb_inbox.jsonl` 为开发前已有的 PM 改动。0.2.0 新增未跟踪文件：`frontend/src/portal/UiIcon.vue`、`frontend/src/shared/voteShare.js`、`frontend/tests/ui_blocks.spec.js`、`miniprogram/utils/voteShare.js`、`miniprogram/tests/ui_blocks.spec.js`、`themes/{neon,bento,terminal}.mp.css`；修改 `themes/*.web.css`、Home/Resolutions/Claims（Web）、小程序 index/resolutions/claims 页、两端基础样式与重新生成的 themes.css / themes.scss。
- 五维平均分：Correctness 8.0 / Security 9.0 / Performance 8.0 / Maintainability 8.0 / Testability 8.5。
- 问题统计：CRITICAL 0（已修复 0；GR-C-001-F01 对应的 AC-074-02 由“简化版标 DONE”改为实现 + 如实标 PARTIAL）/ MAJOR 4（CR-004 部分关闭仍 OPEN、CR-005、CR-007、CR-011）/ MINOR 7（CR-001 已 FIXED，其余 OPEN）。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC |
|---|---|
| backend/apps/accounts/{models,services,views,urls}.py、migrations/0002_user_theme_key.py | MOD-023 / IFC-142、143 |
| backend/tests/integration/{test_theme_preference_api,test_frontend_contract}.py | MOD-023（测试） |
| themes/*、scripts/themes/*、{frontend,miniprogram}/…/generated/* | MOD-024 / IFC-144、145 |
| frontend/src/theme/*、shared/api.js、index.html、main.js、router/index.js、Login/Register/WechatCallback/Me.vue | MOD-025 / IFC-146、147、150 |
| frontend/src/portal/{PortalLayout,BottomTabBar}.vue、admin/AdminLayout.vue、shared/style.css | MOD-026 / IFC-148 |
| frontend/src/portal/*.vue、admin/AdminAppeals.vue、StatusTag.vue、frontend/tests/theme*.spec.js | MOD-027 |
| miniprogram/{store/theme.js,components/ThemeRoot.vue,utils/api.js,App.vue,pages.json,pages/login} | MOD-028 / IFC-149、151 |
| miniprogram/pages/*（11 页）、components/StatusTag.vue、tests/{theme.spec,setup}.js | MOD-029 |

## 自验证结果

| 项 | 命令（工作目录） | 结果 |
|---|---|---|
| 静态检查 | `python3 -m compileall -q backend`（仓库根） | 无输出，通过 |
| 系统检查 | `manage.py check --settings=config.test_settings`（backend/，PM venv Django 5.2.19） | `System check identified no issues (0 silenced).` |
| 后端全量 | `manage.py test --settings=config.test_settings` | `Ran 220 tests in 7.9s` / `OK`（基线 212 + 新增 8） |
| 迁移漂移 | `manage.py makemigrations --check --dry-run --settings=config.test_settings` | `No changes detected` |
| 迁移往返 | 临时 SQLite 文件库 migrate → migrate accounts 0001 → migrate | 均 OK，`theme_key` 列 1→0→1（详见 implementation_plan） |
| 风格构建 | `node scripts/themes/build.mjs --strict --check`（仓库根，Node v22） | 退出码 0，生成物一致 |
| Web 测试 | `npx vitest run --passWithNoTests`（frontend/） | `Test Files 6 passed (6)` / `Tests 56 passed (56)`（基线 36 + 新 20） |
| Web 构建 | `npm run build -- --base=/ocap/`（frontend/） | `✓ built in 26.07s`（仅 chunk > 500 kB 的既有告警） |
| 小程序测试 | `npx vitest run --passWithNoTests`（miniprogram/） | `Test Files 4 passed (4)` / `Tests 38 passed (38)`（基线 30 + 新 8） |
| 小程序构建 | `npm run build:mp-weixin`（miniprogram/） | **失败**：先 `ENOENT src/manifest.json`；加 `UNI_INPUT_DIR=.` 后 `TypeError: Cannot read properties of undefined (reading 'vueOptions')`。`git archive HEAD` 导出的基线同命令同样失败 → 环境（uni alpha 工具链）问题，**未验证**；H5 构建 `uni build` 亦失败（缺 `ssr/entry-server.js`） |
| 小程序模板编译 | `@vue/compiler-sfc`（frontend/node_modules）解析并编译 14 个 SFC | `checked 14 bad 0`（0.1.0；0.2.0 未单独重跑，改由 vitest 挂载 index / resolutions / claims 页覆盖模板编译） |

**0.2.0 返工自验证（本次实跑）**

| 项 | 命令（工作目录） | 结果 |
|---|---|---|
| 后端全量 | `manage.py test --settings=config.test_settings`（backend/，Django 5.2.19） | `Ran 220 tests in 7.9s` / `OK` |
| 静态检查 | `python -m compileall -q backend` | 通过 |
| 风格构建 | `node scripts/themes/build.mjs --strict` 后 `--strict --check` | 重新生成 themes.css / themes.scss；check 退出码 0 |
| Web 测试 | `npx vitest run`（frontend/） | `Test Files 7 passed (7)` / `Tests 68 passed (68)`（基线 36；含新增 `ui_blocks.spec.js` 12 个） |
| Web 构建 | `npm run build -- --base=/ocap/`（frontend/） | `✓ built in 25.03s` |
| 小程序测试 | `npx vitest run`（miniprogram/） | `Test Files 5 passed (5)` / `Tests 43 passed (43)`（基线 30；含新增 5 个） |
| 小程序构建 | `build:mp-weixin` | 未验证（CR-007，基线同样失败，按 PM 指示不再排查） |
| 浏览器 / 微信开发者工具视觉 | — | 未验证：三套风格的首页 12 栏 / Bento / 动效 / 倒计时的实际观感未人工走查 |

未验证项：小程序构建产物、WXSS 对自定义属性/`@import` scss 的处理、`uni.setTabBarStyle/setNavigationBarColor/setBackgroundColor` 真机行为、浏览器中的视觉与动效（均需微信开发者工具/浏览器）。

## 按模块评审

### MOD-023 账号风格偏好（后端）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 10/10 | 9/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MINOR | backend/apps/accounts/views.py `ThemePreferenceView.put` | `request.data` 为 JSON 数组时按空对象处理（返回 400 而非 500），已加防护；记录以便评审知悉 | FIXED |

### MOD-024 风格定义与构建

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-002 | MINOR | themes/bento.theme.json contrast | Hero 对比度实测 4.5996，原表 4.60 为四舍五入；阈值取 4.59，需 PM/设计确认 | OPEN |
| CR-003 | MINOR | scripts/themes/build.mjs | 重复 key 检查实际不可达（key 必须等于文件名），仅作防御代码 | OPEN |

### MOD-025/026/027 Web

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-004 | MAJOR | frontend/src/portal/{Resolutions,Claims}.vue | 0.2.0：决议卡片（三段比例条）与报销表单（类型卡片、¥ 金额、字数计数、拖拽区 + 列表、步骤条、汇总）已实现，见 `ui_blocks.spec.js`。残留：无“未表决”票数 / 真实编号 / 审批人步骤（接口无字段，未编造）；小程序报销页无拖拽区与步骤条；视觉未走查 | OPEN（部分关闭） |
| CR-005 | MAJOR | Claims.vue / Resolutions.vue 页脚 | AC-084-02：报销表单仍是对话框（0.2.0 决定保持以免改动业务逻辑），`.form-actions-sticky` 在对话框内吸底，不是"标签栏上方"；需浏览器验证 | OPEN |
| CR-006 | MINOR | frontend/src/shared/style.css | 全局 `.el-button{min-height:44px}` 会放大管理端 `size=small` 按钮，属为满足 AC-088-02 的有意取舍 | OPEN |
| CR-008 | MINOR | frontend/src/portal/Home.vue | 首页新增 `approvalApi.tasks`、`pollApi.list` 两个只读调用（现有接口，失败按空态）；与“API 调用集合不变”存在张力，需 PM 确认（OQ-D07）。非委员用户每次打开首页会多一次 403 的 `/approval/tasks` 请求 | OPEN |
| CR-009 | MINOR | themes/bento.web.css `.home-stat.is-odd` | 深色数据块次要文字色 `#B7BBCB` 未纳入 `contrast` 声明与构建期校验（OQ-D09）；目测对比度充足但未计算 | OPEN |
| CR-010 | MINOR | 过程 | 违反规则 3：`style.css` 追加用 Bash heredoc，小程序 index 页与本报告文件头改版本用 Python 脚本；内容已核对 diff，无其他影响 | OPEN（记录） |
| CR-011 | MAJOR | themes/*.web.css | 装饰动效降级机制：`prefers-reduced-motion` 全局规则关闭所有 animation / transition（生成器已有）；`data-perf=low` 只在 A、C 的文件里逐条写了 `animation:none`。B 无循环动画。新增风格需自行遵守该约定，构建器未校验；另外 `.home-q` 的 hover `transition` 在低端设备未关闭（仅 transform，影响小） | OPEN |

### MOD-028/029 小程序

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 7/10 | 9/10 | 8/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-007 | MAJOR | miniprogram 构建 | 构建不可运行（环境），WXSS 变量/`@import` scss（无 sass）/原生 API 未验证；阻止声称"构建通过" | OPEN |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

共 4 条（CR-004、CR-005、CR-007、CR-011；>3，逐条写明）：
- CR-004：Web 已改造，残留项均因现有接口无数据而不编造（未表决数、真实编号、审批人姓名）；小程序无拖拽能力。建议 PM 评估是否由后端补字段后在下一迭代完成。
- CR-005：保持对话框是为不改变业务逻辑（`showCreate/openCreate`）；建议 E2E/人工在窄屏验证，必要时下个迭代改为页内表单。
- CR-007：环境（uni alpha 工具链）问题，基线同样失败；需有完整工具链的机器 / 微信开发者工具验证，PM 安排。
- CR-011：降级约定靠各风格文件自觉；建议下个迭代由 `build.mjs` 校验“含 `animation` 的规则必须有对应 `data-perf=low` 关闭规则”。
另：三套风格首页的实际观感（0.2.0 重点）未在浏览器 / 微信开发者工具走查，是 AC-074-02 仍标 PARTIAL 的主要原因，建议 E2E 阶段或用户目视确认。

## 缺陷修复

1.1.0（缺陷回流 1/2，REWORK_AUTHORIZED）：

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-001 | backend/apps/residency/views.py:116 `AppealAdminSerializer.__init__` | `page_response` 以 `serializer_cls(rows, many=True, context=context)` 调用；`AppealAdminSerializer` 的自定义 `__init__` 不接受 `context`，GET /api/v1/admin/appeals 抛 `TypeError`（500）。其他自定义序列化类都已带 `context=None`，此类遗漏 | 签名改为 `(self, rows, many=False, context=None)`，接受并忽略 `context`；不改 `page_response`、不改响应字段。改动 1 行 |

CR-012（MINOR，FIXED）：residency/views.py:116，同上修复，既有缺陷，非本次风格改造引入。

其余 `page_response` 调用方已检查（`git grep -n page_response -- backend`）：9 个自定义类均已带 `context=None`，4 个为 DRF `ModelSerializer`，无同类问题。

自验证（1.1.0，backend/，PM venv Django 5.2.19）：
- 修复前（`git stash` 暂存该文件）手动请求：`TypeError: AppealAdminSerializer.__init__() got an unexpected keyword argument 'context'`。
- 修复后，测试库内用 DRF test client 以管理员令牌请求：`GET /admin/appeals -> 200 {'count': 1, 'page': 1, 'page_size': 20} keys: ['applicant','decided_at','id','proof','reject_reason','status','submitted_at','unit']`；`?status=PENDING -> 200 1`。脚本在 scratchpad（`verify_def001.py`），不在仓库内。
- `manage.py test --settings=config.test_settings`：`Ran 238 tests in 8.865s` / `OK`（零新增失败）。
- `python -m compileall -q backend`：通过。
- 回归测试由 test-engineer 编写，本次未新增测试文件。`git diff -- backend/apps/residency/views.py`：1 行修改。

问题统计更新：MINOR +1（CR-012，FIXED）；CRITICAL/MAJOR 不变。

## 现有测试调整

0.2.0：无。既有用例（含 `frontend/tests/pages.spec.js` 的 Home / Claims 用例、`miniprogram/tests/pages.spec.js` 的首页用例）断言一字未改，全部通过；新增用例在 `ui_blocks.spec.js`（Web、小程序各一份）。

0.1.0 记录：无。既有用例未做任何修改；仅 `miniprogram/tests/setup.js` 的 `uni` 桩追加 3 个 API（`setTabBarStyle`、`setNavigationBarColor`、`setBackgroundColor`），使 `ThemeRoot` 在 jsdom 中可挂载，不改变原有桩。
