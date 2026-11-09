<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-09T22:27:42+08:00</timestamp>
  <project_name>ocap_ui_theme</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/architecture_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>development/code_review_report.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：ocap 多风格界面（INCREMENTAL）

> 1.1.0 变更（缺陷回流 1/2）：DEF-001 已由开发修复（backend/apps/residency/views.py:116 `AppealAdminSerializer.__init__` 增加 `context=None`，GR-C-003 PASS）。本版只追加 DEF-001 回归用例 TC-INT-010…015（`backend/tests/integration/test_admin_appeals_regression.py`，6 个）并更新计数：后端 238 → 244，integration 165 → 171；frontend 122、miniprogram 69 不变。其余内容同 1.0.0。

## 测试策略

- **被测改动**：MOD-023（后端 `GET/PUT /api/v1/me/theme`、`User.theme_key`、迁移 0002）、MOD-024（`themes/` 风格定义 + `scripts/themes/build.mjs` 生成器）、MOD-025/026/027（Web 风格运行时、布局、14+9 页换肤）、MOD-028/029（小程序风格运行时与 11 页换肤）。
- **范围（in）**：后端 API 的鉴权/隔离/校验/迁移文件；风格 store 的六条优先级规则；首屏内联脚本；构建器的校验与对比度；样式规则存在性；Web/小程序页面在 jsdom 中的挂载、路由、登录对账、个人中心选择；前后端契约；权限零回归；三层 + 全量回归。
- **范围（out）**：真实浏览器/真机的视觉走查、动效与计时、低端设备实机降级、微信开发者工具中的 WXSS 与原生 tabBar 行为、`build:mp-weixin` 构建（均为人工清单，见 e2e_test_report）。
- **环境**：Python 3.12 + PM 临时 venv（Django 5.2.19），`backend/` 下 `manage.py test ... --settings=config.test_settings`（SQLite 内存库、`SMS_GATEWAY_BACKEND=memory`、locmem 邮件，不调用真实微信/短信/邮件）；Node 22 + vitest 2.1.9（frontend、miniprogram，jsdom，`uni` 为桩）。未连接测试机/生产库，未安装依赖。
- **判定模式**：INCREMENTAL / baseline —— 每层相对基线零新增失败且新写用例全部通过才进入下一层；E2E critical path 通过率 1.00，并覆盖前后端契约（画像 P5）。
- **基线来源**：PM 在 HEAD 8597cef 改动前实跑：后端 Ran 212 OK、frontend vitest 36 passed、miniprogram vitest 30 passed。本人另用 `git archive HEAD` 导出到 scratchpad 复核分层基线：unit 42 / integration 148 / e2e 16 / smoke 6（合计 212，全部 OK）。基线无既有失败。
- **分层机制**：后端按目录（`tests/unit|integration|e2e|smoke`）；前端与小程序无 tag 机制，按文件名固定归层（见下表），分层运行命令显式列出文件，新测试均已归入某层。

| 层 | 后端 | frontend 文件 | miniprogram 文件 |
|---|---|---|---|
| UNIT | `tests.unit` | api、auth.store、theme、theme_build、ui_blocks、**qa_unit_theme** | api、store、theme、ui_blocks、**qa_unit_theme** |
| INTEGRATION | `tests.integration` | login、pages、**qa_int_theme** | pages、**qa_int_theme** |
| E2E（替代口径） | `tests.e2e` | **qa_e2e_theme、qa_e2e_extend、qa_e2e_pages** | **qa_e2e_theme、qa_e2e_extend、qa_e2e_pages** |

（加粗为本次新写；其余为基线既有或 GROUP_C 随开发新增的用例，视为"现有"。）

- **critical path 口径：替代**。本机无浏览器、无 Playwright。E2E 层用"jsdom 中挂载真实 App + 真实路由 + 真实页面 + 真实 api.js，HTTP 层用带状态的假服务端"以及"后端真实 HTTP 多步 API 旅程"替代；视觉、动效、计时由人工清单覆盖。

### GR-C-002 conditions 处理

| # | 条件 | 处理 |
|---|---|---|
| ① | 无 headless 浏览器 | 三套风格 × Web 14 页 / 管理端 9 页 / 小程序 11 页的视觉走查、首屏无闪烁、≤1 s 切换、低端设备降级、prefers-reduced-motion 实际效果标 `[NOT_TESTABLE: 无浏览器]`（manual），写入 e2e_test_report 人工验证清单 MV-01…MV-12，并单独统计 critical path 待人工验证条数（7 条）。可自动化部分（DOM 结构、data-theme 切换、类名、生成 CSS 规则存在、对比度独立复算、内联脚本行为、低端判定函数、逐页挂载与文本一致性）已自动化并执行。 |
| ② | build:mp-weixin 基线即失败 | 未排查构建环境；真机/开发者工具验证列入 MV-04。 |
| ③ | AC-084-02、AC-087-02、AC-074-02 | 按 PARTIAL 如实记录：AC-084-02 提交按钮在对话框内吸底而非标签栏上方（静态规则存在性已测，布局效果 MV-05）；AC-087-02 小程序报销页无拖拽区/文件列表/竖向步骤条（Should Have）；AC-074-02 中收入/支出/结余/参与率金额卡、投票参与进度条、搜索与通知角标、"未表决"票数、真实决议编号、审批人步骤因接口无数据按 implementation_plan 未编造（不测、不算缺陷）。 |
| ④ | 契约 | `/me/theme` GET/PUT（字段 `theme`）与 Home.vue 新增 `approvalApi.tasks`、`pollApi.list`、小程序首页 `api.polls`/`tasks` 的契约用例：TC-INT-001/002/003/004 + 现有 TC-INT-302，复跑通过。 |
| ⑤ | CR-011 | 记入遗留：构建器不校验新增风格的 `data-perf=low` 规则，不阻断；现有三套风格的降级规则存在性已由 TC-UNIT-105 断言。 |

## AC 映射

说明：为控制宽度，"前置/动作/预期"合并为"G/W/T 摘要"，"测试数据"见下节。运行方式均为 `sim`（本项目无硬件，P11 为"无"，列省略）。ID 规则：TC-xxx-0nn 后端新写；1nn 前端新写；2nn 小程序新写；3nn 现有（基线或 GROUP_C 随开发新增）。

现有用例 ID 登记：

| ID | 级别 | 位置 | 内容 |
|---|---|---|---|
| TC-UNIT-301 | UNIT | frontend/tests/theme.spec.js（13） | 颜色字面量守护、注册表、store 六条优先级、ThemePicker、测试风格 D 构建、底部标签栏/高亮 |
| TC-UNIT-302 | UNIT | frontend/tests/theme_build.spec.js（7） | 生成物与源一致、对比度 ≥ 声明阈值与 design_spec §5 表内值 |
| TC-UNIT-303 | UNIT | frontend/tests/ui_blocks.spec.js（12） | 首页语义区块、决议卡片三段比例、报销表单控件、页面无风格专属判断 |
| TC-UNIT-304 | UNIT | miniprogram/tests/theme.spec.js（8） | 小程序 store、ThemeRoot、我的页风格选择 |
| TC-UNIT-305 | UNIT | miniprogram/tests/ui_blocks.spec.js（5） | 小程序首页/决议卡片/报销类型卡片 |
| TC-UNIT-306 | UNIT | frontend/tests/{api,auth.store}.spec.js；miniprogram/tests/{api,store}.spec.js（共 41） | 基线既有，回归 |
| TC-INT-301 | INT | backend/tests/integration/test_theme_preference_api.py::ThemePreferenceApiTests（7） | requires_login、admin_token_forbidden、initial_value_is_null、put_then_get_roundtrip、invalid_values_rejected、users_are_isolated、put_does_not_touch_profile |
| TC-INT-302 | INT | backend/tests/integration/test_frontend_contract.py（RouteContractTests 3 + FieldContractTests::test_theme_preference_contract） | 路由/方法/字段契约 |
| TC-INT-303 | INT | frontend/tests/{login,pages}.spec.js；miniprogram/tests/pages.spec.js（共 34） | 基线既有页面/登录用例，回归 |
| TC-E2E-301 | E2E | backend/tests/e2e/（16） | 基线既有多步 API 旅程，回归 |

### US-074 三套风格
| AC | 用例 ID | 级别 | 现有/新写 | 位置 | G/W/T 摘要与预期 |
|---|---|---|---|---|---|
| AC-074-01 | TC-UNIT-101、TC-UNIT-301、TC-UNIT-201 | UNIT | 新写+现有 | frontend/tests/qa_unit_theme.spec.js；miniprogram/tests/qa_unit_theme.spec.js | 注册表恰 3 项，名称依次 霓虹玻璃/极光 Bento/赛博终端，各带 3 色块，Web 与小程序一致 |
| AC-074-01 | TC-INT-103、TC-INT-203 | INT | 新写 | qa_int_theme.spec.js（两端） | 个人中心/我的页渲染 3 个 radio，名称顺序正确，默认 bento 选中 |
| AC-074-01 | TC-E2E-102、TC-E2E-203 | E2E | 新写 | qa_e2e_theme/extend | 旅程中列表 keys = neon,bento,terminal（D 加入后 4 项） |
| AC-074-02 | TC-UNIT-101、TC-UNIT-301 | UNIT | 新写+现有 | 同上 | scheme：neon=dark、bento=light、terminal=dark；`dark` 类随风格切换 |
| AC-074-02 | MV-01 | manual | — | e2e 人工清单 | `[NOT_TESTABLE: 无浏览器]` 主色/圆角/字体/首页布局视觉一致性；PARTIAL（见条件③） |
| AC-074-03 | TC-UNIT-101 | UNIT | 新写 | qa_unit_theme.spec.js | 无 system/auto 选项；全部样式源与 apply.js/index.html 不含 prefers-color-scheme |
| AC-074-03 | MV-11 | manual | — | 人工清单 | `[NOT_TESTABLE]` 切换系统深浅色，实际页面不变 |

### US-075 默认 B
| AC | 用例 ID | 级别 | 现有/新写 | 位置 | 摘要 |
|---|---|---|---|---|---|
| AC-075-01 | TC-UNIT-003、TC-INT-301、TC-INT-102、TC-INT-201、TC-E2E-001、TC-E2E-101、TC-E2E-201 | UNIT/INT/E2E | 新写+现有 | backend unit/integration/e2e；两端 qa_*.spec.js | 新账号 theme_key=NULL；GET 返回 `{theme:null}`；登录后账号 null → bento，picker 中极光 Bento 选中 |
| AC-075-02 | TC-UNIT-108 | UNIT | 新写 | frontend qa_unit_theme.spec.js | 管理端 .vue 无"默认风格/新增风格/风格设置"文案，api.js 无管理端风格接口；后端无全站默认接口（无路由） |

### US-076 Web 个人中心选择
| AC | 用例 ID | 级别 | 位置 | 摘要 |
|---|---|---|---|---|
| AC-076-01 | TC-INT-103、TC-E2E-101、TC-UNIT-109；MV-06 | INT/E2E/UNIT/manual | frontend qa_* | 独立"界面风格"区块（标题为首个 h3，其后仍有资料等区块）；点击即 `data-theme` 切换，无确认步骤，PUT `{theme}`；同步逻辑耗时 < 1000 ms（jsdom）；真实渲染 ≤1 s 为 MV-06 |
| AC-076-02 | TC-INT-103 | INT | qa_int_theme.spec.js | terminal→neon→terminal→bento 来回 4 次均生效，4 次 PUT，任一时刻选中项 = 1 |
| AC-076-03 | TC-INT-103、TC-UNIT-301 | INT/UNIT | 同上 | PUT 失败：ElMessage 含"保存失败"，选中与 data-theme 回到保存前，资料区块仍在 |
| AC-076-04 | TC-INT-101 | INT | 同上 | 未登录访问 /me → 跳 /login?redirect=/me，DOM 无"界面风格" |

### US-077 小程序"我的"页
| AC | 用例 ID | 级别 | 位置 | 摘要 |
|---|---|---|---|---|
| AC-077-01 | TC-INT-203、TC-UNIT-304；MV-04、MV-06 | INT/UNIT/manual | miniprogram qa_int_theme.spec.js | 点选后 `.theme-root` 切换、PUT `/me/theme {theme}` 带 Bearer、`uni.setTabBarStyle` 被调用（桩）；真机 tabBar 与 ≤1 s 为人工 |
| AC-077-02 | TC-INT-201、TC-E2E-201、TC-E2E-001 | INT/E2E | 同上；backend e2e | 账号 neon、设备 terminal → 登录后 neon；换设备读到 Web 端保存的值 |
| AC-077-03 | TC-INT-101、TC-E2E-001 | INT/E2E | frontend；backend | 小程序保存后 Web 路由进入触发对账 → 账号值覆盖；后端 PUT/GET 跨 token 一致 |
| AC-077-04 | TC-INT-203、TC-UNIT-304 | INT/UNIT | miniprogram | PUT 失败 → toast"保存失败"，回滚选中与设备记忆 |

### US-078 记住风格
| AC | 用例 ID | 级别 | 位置 | 摘要 |
|---|---|---|---|---|
| AC-078-01 | TC-E2E-101、TC-E2E-201 | E2E | 两端 qa_e2e_theme | 选 neon → 退出 → 重新登录仍 neon |
| AC-078-02 | TC-E2E-102、TC-E2E-001、TC-E2E-201 | E2E | 同上；backend e2e | 空设备记忆登录 carol(terminal) → terminal；设备 2 token 读到设备 1 保存的值 |
| AC-078-03 | TC-UNIT-004、TC-INT-102、TC-INT-006、TC-E2E-101、TC-E2E-001 | UNIT/INT/E2E | 多处 | 同浏览器 bob(null) 登录 → bento，alice 账号值不变；PUT 带他人 id 无效 |
| AC-078-04 | TC-INT-001、TC-INT-002、TC-INT-301、TC-INT-302 | INT | backend test_ui_theme_qa.py / 现有 | 两端 api.js 均含 GET+PUT /me/theme 且 resolve 到支持该方法的视图；未解析调用数 = 0 |

### US-079 未登录页
| AC | 用例 ID | 级别 | 位置 | 摘要 |
|---|---|---|---|---|
| AC-079-01 | TC-UNIT-104、TC-INT-202、TC-E2E-101 | UNIT/INT/E2E | 两端 | 无记忆 → bento；Web 内联脚本在样式解析前同步设置；小程序登录页 theme-bento |
| AC-079-02 | TC-INT-104、TC-INT-203、TC-E2E-101、TC-E2E-201 | INT/E2E | 两端 | 退出登录保留 `ocap_theme`，登录页应用 terminal/neon |
| AC-079-03 | TC-UNIT-108、TC-INT-104、TC-INT-202 | UNIT/INT | 两端 | 登录/注册/回调页无 ThemePicker，登录页无 radio/theme-option |
| AC-079-04 | TC-UNIT-104、TC-UNIT-203、TC-E2E-102 | UNIT/E2E | 两端 | 设备记忆为已下线 key → store 回退 bento；渲染兜底 `:root` 默认变量即 B |

### US-080 新增风格不改业务页
| AC | 用例 ID | 级别 | 位置 | 摘要 |
|---|---|---|---|---|
| AC-080-01 | TC-UNIT-301、TC-E2E-103、TC-E2E-203 | UNIT/E2E | 两端 qa_e2e_extend | 对"三套 + 测试风格 D"临时目录实际运行 build.mjs，注入注册表后个人中心/我的页由 3 项变 4 项，含"测试风格 D" |
| AC-080-02 | TC-E2E-103、TC-E2E-203、TC-UNIT-301、TC-UNIT-303 | E2E/UNIT | 同上 | 选 D → PUT `{theme:'testd'}`，6 个用户端页 data-theme=testd；业务页面源码（Web 24 个 .vue、小程序 11 页）无 testd/测试风格字样；颜色字面量守护通过（页面零改动即可换肤）；视觉应用 MV-02 |
| AC-080-03 | TC-UNIT-103、TC-UNIT-301 | UNIT | frontend qa_unit_theme.spec.js | 缺字段/低对比度/min<4.5/key 与文件名不一致/坏 JSON/大写 key/缺 bento → 不进注册表并给出 `themes/<file>:<路径>` 错误，其余三套不受影响 |
| AC-080-04 | TC-UNIT-108 | UNIT | 同上 | 管理端无运行期新增风格入口 |

### US-081 / US-082 / US-083 页面覆盖
| AC | 用例 ID | 级别 | 位置 | 摘要 |
|---|---|---|---|---|
| AC-081-01/02 | TC-E2E-104；MV-02 | E2E/manual | frontend/tests/qa_e2e_pages.spec.js | 用户端 14 路由 × 3 风格逐页挂载：data-theme 正确、渲染非空、无内联颜色字面量；视觉 14/14×3 为 MV-02 `[NOT_TESTABLE]` |
| AC-081-03 | TC-E2E-104、TC-UNIT-303 | E2E/UNIT | 同上 | 同一页面三种风格下文本内容完全一致（剔除选择器"已选"标记） |
| AC-082-01 | TC-E2E-105、TC-E2E-101；MV-03 | E2E/manual | 同上 | 管理端 9 路由（登录 + 8 页）data-theme 恒为 bento，即使设备记忆 terminal；视觉 9/9 为 MV-03 |
| AC-082-02 | TC-INT-101、TC-UNIT-301、TC-E2E-101 | INT/UNIT/E2E | frontend | 管理端不读写 ocap_theme、不请求 /me/theme；离开管理端回到用户端风格 |
| AC-082-03 | TC-E2E-105、TC-UNIT-108 | E2E/UNIT | frontend | 管理端页面无 radio/theme-picker/theme-option |
| AC-082-04 | TC-INT-101 | INT | frontend | 管理端令牌缺失仍跳 /admin/login；管理员令牌访问 /me/theme 为 403（TC-INT-005） |
| AC-083-01 | TC-E2E-202、TC-UNIT-304；MV-04 | E2E/UNIT/manual | miniprogram qa_e2e_pages | pages.json 11 页 × 3 风格：ThemeRoot 类 theme-<key>、注入 CSS 变量、无内联颜色；真机/tabBar/构建为 MV-04 |
| AC-083-02 | TC-UNIT-202 | UNIT | miniprogram qa_unit_theme | tabBar 保持 4 项（首页/决议/投票/我的）；初值 = bento 的 native 色值 |
| AC-083-03 | TC-INT-202 | INT | 同上 | 无记忆 theme-bento；有记忆 theme-terminal |
| AC-083-04 | TC-E2E-202 | E2E | 同上 | 三风格文本一致 |

### US-084 / US-085 导航与适配
| AC | 用例 ID | 级别 | 位置 | 摘要 |
|---|---|---|---|---|
| AC-084-01 | TC-INT-105、TC-E2E-106、TC-UNIT-301 | INT/E2E | frontend | 底部标签栏恰 5 项 首页/决议/投票/报销/我的，各带图标；逐项点击进入 /、/resolutions、/polls、/claims、/me，高亮项唯一；窄屏下顶部导航隐藏的实际效果 MV-05 |
| AC-084-02 | TC-UNIT-105；MV-05 | UNIT/manual | frontend | `[PARTIAL]` 仅断言 ≤767.98px 媒体查询内 `.form-actions-sticky{position:sticky}` 存在；对话框内吸底的实际布局为 MV-05 |
| AC-084-03 | TC-UNIT-105 | UNIT | frontend | 宽屏 `.tabbar{display:none}`；桌面规则体内无 position |
| AC-084-04 | MV-05 | manual | — | `[NOT_TESTABLE]` 窄屏单列、8 项不挤行 |
| AC-085-01/02 | TC-INT-105、TC-UNIT-301、TC-E2E-106 | INT/UNIT/E2E | frontend | /resolutions、/resolutions/7 顶部仅"决议"高亮；切 /polls 变"投票/调查"；高亮数 = 1 |

### US-086 下线回退
| AC | 用例 ID | 级别 | 位置 | 摘要 |
|---|---|---|---|---|
| AC-086-01 | TC-INT-102、TC-E2E-102、TC-UNIT-203、TC-INT-201、TC-E2E-002 | INT/E2E/UNIT | 多处 | 账号值/设备记忆为未注册 key → bento，登录后正常跳转；后端对格式合法的 key 原样保存与返回 |
| AC-086-02 | TC-E2E-102、TC-INT-203 | E2E/INT | 两端 | 个人中心 keys 恒为启用集合；可重选并立即生效、账号值更新 |
| AC-086-03 | TC-UNIT-104、TC-E2E-102 | UNIT/E2E | frontend | 设备记忆下线 → 登录页 bento |

### US-087 ~ US-090 质量项
| AC | 用例 ID | 级别 | 摘要 |
|---|---|---|---|
| AC-087-01 | TC-UNIT-107、TC-UNIT-303；MV-10 | UNIT/manual | 表决中=is-warning、已通过=is-success、未通过=is-danger，均含圆点与互异文字；灰度可辨为 MV-10 |
| AC-087-02 | TC-UNIT-303；MV-10 | UNIT/manual | `[PARTIAL]` Web 报销表单/决议卡片控件逻辑；小程序报销页部分完成（Should Have）；三风格视觉为 MV-10 |
| AC-087-03 | TC-UNIT-204、TC-UNIT-305 | UNIT | 小程序状态标签同 Web |
| AC-088-01 | TC-UNIT-102、TC-UNIT-302 | UNIT | 独立 WCAG 实现（黑白=21 自检）复算：每风格正文/次要/强调相对页面底色 ≥4.5；声明的每个组合独立复算 ≥ 其 min 且 min ≥4.5；design_spec §5 表内值由 TC-UNIT-302 断言 |
| AC-088-02 | TC-UNIT-105；MV-09 | UNIT/manual | `--hit-min:44px` 并作用于 el-button/input/select 与 .tabbar a；实测点击区域 MV-09 |
| AC-088-03 | TC-UNIT-105；MV-09 | UNIT/manual | `:focus-visible` 有描边/光环规则；键盘遍历实测 MV-09 |
| AC-088-04 | TC-UNIT-103 | UNIT | 低于阈值的风格被构建器拒绝（等价于不得发布） |
| AC-089-01 | TC-UNIT-105、TC-UNIT-205；MV-08 | UNIT/manual | `prefers-reduced-motion` 块含 animation:none!important、transition:none!important、隐藏 .theme-decor；小程序样式无 infinite；实机效果 MV-08 |
| AC-089-02 | TC-UNIT-105、TC-UNIT-106、TC-UNIT-102；MV-08 | UNIT/manual | `detectLowEnd`（内存≤4GB 或 ≤4 核）→ data-perf=low；`html[data-perf=low]` 令 --blur:none、--glass=不透明；降级纯色上正文 ≥4.5 |
| AC-089-03 | MV-08 | manual | `[NOT_TESTABLE]` 流畅度结论只能人工；降级逻辑生效已由上行证明 |
| AC-090-01 | TC-UNIT-109；MV-06 | UNIT/manual | 乐观应用同步完成且 < 1000 ms（jsdom 逻辑耗时，不等于真实渲染） |
| AC-090-02 | TC-UNIT-104；MV-07 | UNIT/manual | 内联脚本同步设置 data-theme（无 B→C 跳变的逻辑前提）；录屏逐帧 MV-07 |
| AC-090-03 | TC-INT-102、TC-UNIT-301 | INT/UNIT | 偏好读取失败 → 保持设备记忆风格并继续跳转，设备记忆不被清空 |

### US-091 零回归与契约
| AC | 用例 ID | 级别 | 位置 | 摘要 |
|---|---|---|---|---|
| AC-091-01 | 全量回归 | 全部 | — | 后端 244 OK（基线 212）；frontend 122（基线 36）；miniprogram 69（基线 30）；新增失败 0 |
| AC-091-02 | TC-INT-001/002/003/004、TC-INT-302 | INT | backend/tests/integration/test_ui_theme_qa.py 等 | 未解析调用数 = 0（Web+小程序共 >110 个调用逐个 resolve 且方法受视图支持）；`/me/theme` 与 Home 新增 3 个调用路径+方法+权限（户主 /approval/tasks=403、委员=200 实测） |
| AC-091-03 | TC-INT-009 | INT | 同上 | 6 角色（匿名/游客/户主/委员/主任/管理员）× 11 个受保护操作共 66 个断言；期望值取自 HEAD 导出基线实测，并在基线导出与当前代码上各跑一次，结果一致 |
| AC-091-04 | TC-INT-005/006/007、TC-INT-301、TC-E2E-001 | INT/E2E | 同上 | 未登录/坏令牌 401、管理员 403；无 user id 参数，带他人 id 无效；A/B 隔离；POST/DELETE/PATCH 405 |
| AC-091-05 | 全层 | — | config/test_settings.py | `SMS_GATEWAY_BACKEND=memory`、locmem 邮件；微信经 FakeWeChatClient；前端 HTTP 层与 `uni.request` 全为替身，无网络调用 |

### DEF-001 回归用例（1.1.0 新增，缺陷回流 1/2）

| 用例 | 级别 | 现有/新写 | 位置 | G/W/T 摘要与预期 |
|---|---|---|---|---|
| TC-INT-010 | INT | 新写 | test_admin_appeals_regression.py::AdminAppealListRegressionTests | Given 一条 PENDING 申诉；When 管理员令牌 GET /api/v1/admin/appeals；Then 200，键集合 {count,page,page_size,results}，count=1/page=1/page_size=20，result 键集合 {id,unit,status,submitted_at,decided_at,reject_reason,applicant,proof}，applicant 键 {id,account_no,phone} 且手机号脱敏 |
| TC-INT-011 | INT | 新写 | 同上 | 申诉关联 LINKED 附件 → proof = [{id,name,size,content_type}] 精确相等 |
| TC-INT-012 | INT | 新写 | 同上 | 三条申诉(PENDING/APPROVED/REJECTED)：无过滤 count=3；?status= 各取 1 条且 id 精确；未知状态 count=0；page=2&page_size=2 → 第 2 页 1 条 |
| TC-INT-013 | INT | 新写 | 同上 | 匿名 401、坏令牌 401；游客/户主/委员的用户令牌 403 且不含 results |
| TC-INT-014 | INT | 新写 | 同上 | 经真实 POST decision(REJECT, reject_reason) 后，?status=REJECTED 列表含该申诉且 reject_reason 一致 |
| TC-INT-015 | INT | 新写 | 同上::PageResponseListSmokeTests | 对全部使用 page_response 的列表接口冒烟：管理员令牌 9 个（/admin/appeals、admins、users、approval/flows、committee/seats、memberships、claims、audit-logs、registry/units）+ 委员令牌 6 个（/polls、/resolutions、/claims、/income/sheets、/ledger/reports、/admin/income/sheets）均 200 且为分页包装（或列表） |

### 本次新写用例清单（后端）
| ID | 位置 | AC |
|---|---|---|
| TC-UNIT-001…007 | backend/tests/unit/test_ui_theme_rules.py（`ThemeKeyRuleTests` 2、`SetThemeServiceTests` 4、`ThemeMigrationFileTests` 1） | AC-078-01、AC-080-03、AC-075-01、AC-078-03、AC-086-01、画像 P6 |
| TC-INT-001…004 | backend/tests/integration/test_ui_theme_qa.py::ThemeContractTests | AC-078-04、AC-091-02 |
| TC-INT-005…008 | 同文件::ThemePreferenceSecurityTests | AC-091-04、AC-091-02 |
| TC-INT-009 | 同文件::PermissionRegressionTests | AC-091-03 |
| TC-INT-010…014 | backend/tests/integration/test_admin_appeals_regression.py::AdminAppealListRegressionTests（5，**1.1.0 新增**） | DEF-001；AC-091-02（前端 `adminHttp.get('/admin/appeals')` 调用可用）、AC-091-03/04 |
| TC-INT-015 | 同文件::PageResponseListSmokeTests（1，**1.1.0 新增**） | DEF-001 同类防线；AC-091-03 |
| TC-E2E-001、002 | backend/tests/e2e/test_ui_theme_journeys.py | AC-075/077/078/086/091 |

前端/小程序新写用例以文件内 `describe` 标题的 TC-ID 为准（TC-UNIT-101…109、TC-INT-101…105、TC-E2E-101…106；TC-UNIT-201…205、TC-INT-201…203、TC-E2E-201…203）；报告中计数按 vitest `it` 个数。

## 测试数据需求

- 全部数据在测试内构造：后端用 `tests/support.py` 工厂（用户、户主、委员/主任席位、管理员）；前端/小程序用内联假服务端账号表 alice/bob/carol（`theme` 分别为 null/null/'terminal'）与假页面数据。
- 持久化数据：仅 SQLite 内存库与 jsdom localStorage / uni 存储桩，每个用例前清空，无唯一化问题。
- 测试风格 D：测试内用临时目录（os.tmpdir）复制三份定义并追加 `testd.theme.json`，用毕删除，不写入 `themes/`。
- 无 `[DATA_REQUIRED]`。

## 不可测项

| AC | 原因 |
|---|---|
| AC-074-02（视觉部分）、AC-074-03（真实系统深浅色） | 无浏览器；MV-01、MV-11 |
| AC-081-01/02、AC-082-01（视觉部分）、AC-083-01（视觉/真机） | 无浏览器与微信开发者工具；MV-02/03/04 |
| AC-084-02、AC-084-04 | 窄屏布局需浏览器；MV-05（AC-084-02 另为 PARTIAL） |
| AC-076-01、AC-077-01、AC-090-01 的"≤1 s 真实渲染" | 需浏览器计时；MV-06 |
| AC-090-02 | 需录屏逐帧；MV-07 |
| AC-089-01/02/03 的实机效果与流畅度结论 | MV-08 |
| AC-088-02/03 的实测 | MV-09 |
| AC-087-01 灰度、AC-087-02 视觉 | MV-10 |
| AC-085 视觉高亮 | MV-12（逻辑部分已自动化） |
| 小程序 `build:mp-weixin`、WXSS 变量/`@import` scss、原生 tabBar/导航栏/`setBackgroundColor` 真机行为 | CR-007 基线即失败，按 GR-C-002 条件②不排查；MV-04 |

以上 AC 均仍有可自动化部分且已执行；仅"视觉/计时/实机"部分计为 NOT_TESTABLE，不计入通过率分母。

## 故事覆盖核对

Must Have 故事共 12 个（US-074、075、076、077、078、079、080、081、082、083、084、091）。每个故事至少 1 个真实执行的用例（纯人工项不单独充当覆盖）。

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-074 | TC-UNIT-101、TC-UNIT-201、TC-INT-103、TC-INT-203、TC-E2E-102 | UNIT / INT / E2E |
| US-075 | TC-UNIT-003、TC-INT-301、TC-INT-102、TC-INT-201、TC-E2E-001、TC-E2E-101、TC-E2E-201 | UNIT / INT / E2E |
| US-076 | TC-UNIT-109、TC-INT-103、TC-INT-101、TC-E2E-101 | UNIT / INT / E2E |
| US-077 | TC-INT-203、TC-INT-201、TC-UNIT-304、TC-E2E-201、TC-E2E-001 | UNIT / INT / E2E |
| US-078 | TC-UNIT-004、TC-INT-001、TC-INT-006、TC-INT-102、TC-E2E-101、TC-E2E-102、TC-E2E-201、TC-E2E-001 | UNIT / INT / E2E |
| US-079 | TC-UNIT-104、TC-INT-104、TC-INT-202、TC-E2E-101、TC-E2E-102、TC-E2E-201 | UNIT / INT / E2E |
| US-080 | TC-UNIT-103、TC-UNIT-301、TC-E2E-103、TC-E2E-203 | UNIT / E2E |
| US-081 | TC-UNIT-303、TC-E2E-104 | UNIT / E2E |
| US-082 | TC-UNIT-108、TC-INT-101、TC-E2E-101、TC-E2E-105 | UNIT / INT / E2E |
| US-083 | TC-UNIT-202、TC-UNIT-304、TC-INT-202、TC-E2E-202 | UNIT / INT / E2E |
| US-084 | TC-UNIT-105、TC-INT-105、TC-E2E-106 | UNIT / INT / E2E |
| US-091 | TC-INT-001、TC-INT-002、TC-INT-005、TC-INT-006、TC-INT-009、TC-INT-010…015（DEF-001 回归）、TC-E2E-001 + 全量回归 | INT / E2E |

critical path 覆盖率（有 E2E 级用例的 Must Have 故事 / Must Have 故事总数）= 12 / 12 = 1.00。

## 基线对比

| 范围 | 基线（HEAD 8597cef，改动前） | 改动后（最后一次执行） | 新增失败 |
|---|---|---|---|
| 后端全量 | Ran 212 OK（unit 42 / integration 148 / e2e 16 / smoke 6） | Ran 244 OK（unit 49 / integration 171 / e2e 18 / smoke 6）= 212 + GROUP_C 新增 8 + 本次新写 24（含回流新增 DEF-001 回归 6） | 0 |
| frontend vitest | 36 passed | 122 passed（36 + GROUP_C 32 + 本次 54） | 0 |
| miniprogram vitest | 30 passed | 69 passed（30 + GROUP_C 13 + 本次 26） | 0 |
| 既有失败 | 无 | 无 | — |

发现并记录一项**既有（基线即存在）缺陷**，与本次改动无关：`GET /api/v1/admin/appeals` 返回 500（DEF-001，详见 e2e_test_report"缺陷"），在 `git archive HEAD` 导出的基线上同样复现；该接口无基线测试覆盖，所以基线 212 OK 未暴露。**状态（1.1.0）：已修复，回归用例 TC-INT-010…015 全部通过；同批用例在未修复的 HEAD 导出树上 6 个中 5 个失败（TC-INT-013 非管理员拒绝在修复前后都通过），证明回归用例能捕获该缺陷。**

## 遗留与说明

- CR-011（新增风格的 `data-perf=low` 规则构建器不校验）：记入遗留，不阻断。
- CR-008（非委员打开首页会多一次 403 的 `/approval/tasks`）：TC-INT-004 实测确认为 403 且前端吞错按空态（Home 取不到数据不编造，由 TC-UNIT-303 覆盖）。
