<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-09T22:27:42+08:00</timestamp>
  <project_name>ocap_ui_theme</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>testing/unit_test_report.md</file>
    <file>testing/integration_test_report.md</file>
    <file>development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告：ocap 多风格界面

> 1.1.0（缺陷回流 1/2）：DEF-001 已修复并有回归用例（TC-INT-010…015，见集成报告边界 6）；E2E 层无新增/改动用例，已重跑，结果同 1.0.0（pass 30 / not_testable 12）。全量回归后端 238 → 244。

## 摘要

critical path 口径：替代（后端真实 HTTP 多步 API 旅程；jsdom 中挂载真实 App + 真实路由 + 全部页面 + 真实 api.js，HTTP 层/`uni.request` 用带状态的假服务端。本机无浏览器与微信开发者工具，视觉/动效/计时/真机项进入人工验证清单）

- 执行时间：2026-11-09T22:23:56+08:00 起（最后一次执行）；环境同前两层。
- 命令：
  - `cd backend && python manage.py test tests.e2e --settings=config.test_settings`
  - `cd frontend && npx vitest run tests/qa_e2e_theme.spec.js tests/qa_e2e_extend.spec.js tests/qa_e2e_pages.spec.js`
  - `cd miniprogram && npx vitest run tests/qa_e2e_theme.spec.js tests/qa_e2e_extend.spec.js tests/qa_e2e_pages.spec.js`
- total = pass + fail + skip + blocked + not_testable = 30 + 0 + 0 + 0 + 12 = 42
  - pass 30 = 后端 18（基线既有旅程 16 + 本次新写 2）+ frontend 8（新写）+ miniprogram 4（新写）；
  - not_testable 12 = 人工验证清单 MV-01…MV-12（原因：无浏览器 / 无微信开发者工具；这些 AC 的可自动化部分已在 pass 中执行）。
- 通过率 = pass / (pass + fail + blocked) = 30 / (30 + 0 + 0) = 1.00（NOT_TESTABLE 不计入分母）
- critical path 覆盖率 = 有 E2E 级已执行用例的 Must Have 故事 / Must Have 故事总数 = 12 / 12 = 1.00
- critical path 通过率 = 本次新写 critical path E2E 用例 14 / 14 = 1.00（后端 2 + frontend 8 + miniprogram 4）
- **critical path 待人工验证：7 条**（MV-01、MV-02、MV-03、MV-04、MV-05、MV-06、MV-11；涉及 Must Have 故事 US-074、076、077、080、081、082、083、084）。另有非 critical path 的人工项 5 条（MV-07、MV-08、MV-09、MV-10、MV-12，均为 Should Have 故事）。只要还有人工验证未完成，最终状态至多 DELIVERED_WITH_ISSUES。
- 前后端契约（画像 P5）：已在集成层 TC-INT-001/002/003/004/302 执行并通过（未解析调用数 = 0；`/me/theme` GET/PUT 字段 `theme`；Home.vue 新增 `approvalApi.tasks`、`pollApi.list`），并在本层 TC-E2E-101/102/201 中通过真实 api.js 走通 GET/PUT `/me/theme` 的前端调用链。
- 上一层（集成）门控 PASSED，本层得以执行。**本层门控：PASSED**（新增失败 0；新写 14 / 14 通过）。

## 全量回归

时间：2026-11-09T22:23:56+08:00 – 22:27:32+08:00（最后一次）。

```
$ cd backend && python manage.py test --settings=config.test_settings
Ran 244 tests in 8.713s
OK

$ cd backend && python manage.py check --settings=config.test_settings
System check identified no issues (0 silenced).

$ cd backend && python manage.py makemigrations --check --dry-run --settings=config.test_settings
No changes detected

$ cd backend && python manage.py test tests.smoke --settings=config.test_settings
Ran 6 tests
OK

$ python -m compileall -q backend
compile-ok

$ cd frontend && npx vitest run --passWithNoTests
 Test Files  12 passed (12)
      Tests  122 passed (122)

$ cd miniprogram && npx vitest run --passWithNoTests
 Test Files  10 passed (10)
      Tests  69 passed (69)

$ node scripts/themes/build.mjs --strict --check
themes-check exit=0
```

| 范围 | 基线（PM，HEAD 8597cef） | 本次 | 差值构成 | 新增失败 |
|---|---|---|---|---|
| 后端 | Ran 212 OK | Ran 244 OK | +8 GROUP_C 随开发新增，+24 本次新写（含回流 DEF-001 回归 6） | 0 |
| frontend | 36 passed | 122 passed | +32 GROUP_C，+54 本次新写 | 0 |
| miniprogram | 30 passed | 69 passed | +13 GROUP_C，+26 本次新写 | 0 |

相对基线新增失败数：**0**（无逐条清单）。既有失败：无。`npm run build` 与小程序构建不在本次范围（Web 构建由开发自验证；小程序构建基线即失败，见 MV-04）。

另外按 AC-091-03 取得**改动前后对照**：权限矩阵（TC-INT-009，66 个断言）原样在 `git archive HEAD` 导出的基线代码树与当前代码树各跑一次，均通过。

## 用户旅程

以下"实际响应"均为本次执行中断言通过的实际观测值（jsdom / Django 测试客户端）。

### TC-E2E-101: Web 完整旅程（默认 B → 选 A → 全站沿用 → 退出沿用 → 重登 → 他人不串号 → 管理端固定 B）
- 关联：US-075/076/078/079/082；AC-075-01、AC-076-01、AC-078-01/03、AC-079-01/02/03、AC-082-02；环境：真实 App + router + 全部页面，假服务端账号 alice/bob；位置 frontend/tests/qa_e2e_theme.spec.js

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 首次整页加载（执行 index.html 内联脚本）访问 /login | data-theme=bento，无风格入口 | bento，无 radio | PASS |
| 2 | alice（账号 null）密码登录 | 对账后 bento，跳转 / | bento，路径 / | PASS |
| 3 | /me 点击 neon | 即时 data-theme=neon、dark 类，PUT `neon` 一次，bento 先为选中 | 同 | PASS |
| 4 | 依次访问 /resolutions /polls /claims /units /tasks /reports | 均保持 neon | 6 页均 neon | PASS |
| 5 | 退出登录 → /login | 路径 /login，仍为 neon | 同 | PASS |
| 6 | alice 重新登录 | neon（账号值） | neon | PASS |
| 7 | bob（null）同浏览器登录 | bento，alice 账号值仍 neon | bento；alice.theme=neon | PASS |
| 8 | bob 选 terminal；进入 /admin/registry；再回 /me | 管理端 bento，设备记忆仍 terminal；回用户端 terminal | 同 | PASS |
- 结论：PASS

### TC-E2E-102: 换设备 / 下线回退（3 个用例）
- 关联：US-078/079/086；AC-078-02、AC-079-04、AC-086-01/02/03；位置 frontend/tests/qa_e2e_theme.spec.js
- 空设备记忆登录 carol（账号 terminal）→ 登录前 bento，登录后 terminal 且设备记忆写回 terminal：PASS
- 账号值 `retired-d`（已下线）→ 登录后 bento 并进入 /；个人中心 keys = neon,bento,terminal 且 bento 选中；点 terminal 即时生效，账号值更新为 terminal：PASS
- 设备记忆 `retired-d`（未登录）→ /register、/login 均 bento：PASS
- 结论：PASS

### TC-E2E-103: 新增"测试风格 D"（Web）
- 关联：US-080；AC-080-01/02/03；位置 frontend/tests/qa_e2e_extend.spec.js；对"三套 + testd"临时目录**真实运行 build.mjs** 后注入注册表
- 个人中心列表 = 霓虹玻璃 / 极光 Bento / 赛博终端 / 测试风格 D（3→4）；生成 CSS 含 `html[data-theme="testd"]`；构建无错误；选 D 后 PUT `{theme:'testd'}`，6 个用户端页 data-theme=testd；Web 24 个业务页面源码无 `testd`/`测试风格` 字样（业务页面改动数 = 0）
- 结论：PASS

### TC-E2E-104: 用户端 14 页 × 三套风格逐页走查（自动化部分）
- 关联：US-081；AC-081-01/02/03；位置 frontend/tests/qa_e2e_pages.spec.js
- 14 个路由（login、register、login/wechat、首页、me、units、resolutions、resolutions/1、tasks、claims、income、polls、polls/1、reports）在 neon/bento/terminal 下各访问一次：路径到达、data-theme 正确、渲染非空、无内联颜色字面量、同一页面三风格文本完全一致（只变外观不变内容）。42 次页面访问全部满足。
- 结论：PASS（视觉 14/14×3 为 MV-02）

### TC-E2E-105: 管理端 9 页固定 B
- 关联：US-082；AC-082-01/03；设备记忆 terminal、管理端令牌已设；/admin/login 与 8 个后台页共 9 个路由：data-theme 均为 bento，无 radio / theme-picker / theme-option，无内联颜色，ocap_theme 仍为 terminal。
- 结论：PASS（视觉 9/9 为 MV-03）

### TC-E2E-106: 底部标签栏逐项点击
- 关联：US-084/085；AC-084-01、AC-085-01/02；点击 首页/决议/投票/报销/我的，路径依次为 /、/resolutions、/polls、/claims、/me，每次高亮项唯一且为被点击项。
- 结论：PASS（窄屏下顶部导航隐藏的实际效果为 MV-05）

### TC-E2E-201: 小程序旅程
- 关联：US-075/077/078/079/086；位置 miniprogram/tests/qa_e2e_theme.spec.js
- 首次打开登录页 theme-bento；alice 登录（null）→ bento 并 reLaunch 首页；我的页选 neon → 账号值 neon、`theme-neon`；退出后（重建 store）登录页 theme-neon；bob 登录 → bento 且 alice 账号值仍 neon：PASS
- 换设备：carol 登录 → terminal；账号值 `retired-d` 的 alice 登录 → bento，我的页 3 项，重选 terminal 后账号值与 `theme-terminal` 更新：PASS
- 结论：PASS

### TC-E2E-202: 小程序 11 页 × 三套风格逐页走查（自动化部分）
- 关联：US-083；AC-083-01/04；pages.json 的 11 页逐个挂载：存在 `.theme-root.theme-<key>`、注入 `--bg` 等 CSS 变量、无内联颜色字面量（我的页风格色块豁免）、三风格文本一致、渲染非空。
- 结论：PASS（真机/开发者工具为 MV-04）

### TC-E2E-203: 小程序新增"测试风格 D"
- 关联：US-080；AC-080-01/02；我的页 3→4 项，含"测试风格 D"；选 D → PUT `{theme:'testd'}`，`theme-testd`；11 个页面源码无该风格痕迹。
- 结论：PASS

### TC-E2E-001 / TC-E2E-002: 后端多步 API 旅程
- 关联：US-075/077/078/086/091；AC-075-01、AC-077-02/03、AC-078-02/03、AC-086-01、AC-091-04；位置 backend/tests/e2e/test_ui_theme_journeys.py
- 001：注册 → GET `{theme:null}` → PUT neon → 另一设备（新令牌）登录读到 neon → 设备 2 改 terminal → 设备 1 重新登录读到 terminal；第二个用户全程 null；管理员令牌 403：PASS
- 002：存入格式合法的下线 key 原样返回 → 重新保存 bento → 非法值 400 且偏好不变：PASS
- 结论：PASS

### 基线既有后端旅程（TC-E2E-301）
- backend/tests/e2e 既有 16 个旅程（注册认证、决议、报销、收入表、投票等）在改动后全部通过，作为权限与业务零回归的补充证据。
- 结论：PASS

## 缺陷

| DEF | 级别 | 状态 | 现象 | 复现/回归用例 | 位置 |
|---|---|---|---|---|---|
| DEF-001 | MAJOR（既有缺陷，非本次改动引入） | **已修复（1.1.0 验证）** | 管理员 `GET /api/v1/admin/appeals` 抛 `TypeError: AppealAdminSerializer.__init__() got an unexpected keyword argument 'context'`（线上 HTTP 500），管理端"申诉"页无法加载 | 回归：TC-INT-010、011、012、013、014、015（backend/tests/integration/test_admin_appeals_regression.py）。在 `git archive HEAD` 的未修复树上 6 个中 5 个出错（TypeError），在修复后的当前代码上 6/6 通过 | 修复点 backend/apps/residency/views.py:116 `AppealAdminSerializer.__init__(self, rows, many=False, context=None)`；原因调用方 backend/apps/core/serializers.py:12 以 `context=` 构造 |

DEF-001 验证结论：修复后管理员列表 200、分页与 results 字段同设计一致、?status= 过滤可用、非管理员被拒绝（匿名/坏令牌 401，游客/户主/委员 403）；全部 `page_response` 列表接口冒烟（15 个）无 500。当前无未关闭缺陷。

**如实记录的部分完成项（非缺陷，GR-C-002 条件③）**：AC-084-02 PARTIAL（提交按钮在对话框内吸底，不在标签栏上方）；AC-087-02 小程序报销页部分完成（无拖拽区/文件列表/竖向步骤条，Should Have）；AC-074-02 中收入/支出/结余/参与率金额卡、投票参与进度条、搜索与通知角标、"未表决"票数、真实决议编号、审批人步骤按 implementation_plan 因接口无数据未编造。遗留：CR-011（构建器不校验新增风格的 `data-perf=low` 规则）、CR-008（非委员首页多一次 403 请求，TC-INT-004 实测）。

## 人工验证清单

本机无 headless 浏览器与微信开发者工具（GR-C-002 条件①②）。以下均为 NOT_TESTABLE（manual），建议在 Chrome（桌面 + 移动模拟）、真机/微信开发者工具中完成；每项的可自动化部分已在上文执行。

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | AC-074-02（PARTIAL）/ TC-UNIT-101、301 | 分别选择 A、B、C，打开首页与个人中心，对照 design_spec §1–§2 与 prototype.html 检查主色、圆角、字体、首页布局、深/浅色底 | A、C 深色底，B 浅色底；与设计一致（金额型数据卡/参与率进度条等因接口无数据而省略，属已知 PARTIAL） | Chrome 桌面 + 手机视口 | 是 |
| MV-02 | AC-081-01/02、AC-080-02 / TC-E2E-104、103 | 对 A/B/C（及构造的测试风格 D）各走一遍 14 个用户端页面（含布局/导航、各状态标签、表单、表格、Element Plus 弹窗/下拉/日期选择） | 14/14 页均呈现所选风格，无残留旧版样式、无深色下默认白底的 Element Plus 组件（OQ-T03） | Chrome | 是 |
| MV-03 | AC-082-01/02 / TC-E2E-105 | 同一浏览器先在用户端选风格 C，再登录管理端，逐个打开登录页与 8 个后台页 | 9/9 页均为风格 B；管理端无任何风格入口；管理员登录/令牌行为不变 | Chrome | 是 |
| MV-04 | AC-083-01/03、AC-077-01 / TC-E2E-202、TC-INT-203；GR-C-002 条件② | 在微信开发者工具与真机运行小程序（需先在有完整 uni 工具链的环境构建 `build:mp-weixin`，基线构建 ENOENT manifest.json，CR-007）；三风格逐页检查 11 个页面及底部标签栏，在"我的"点选风格观察 tabBar/导航栏/窗口背景变化 | 11/11 页与标签栏均呈现所选风格；WXSS 对 CSS 变量与 `@import` scss 生效；`setTabBarStyle/setNavigationBarColor/setBackgroundColor` 在真机生效，tabBar 仍为 4 项 | 微信开发者工具 + iOS/Android 真机 | 是 |
| MV-05 | AC-084-01/02/03/04（AC-084-02 PARTIAL）/ TC-E2E-106、TC-UNIT-105 | 在 ≤767px 视口打开用户端：确认顶部导航隐藏、底部 5 项标签栏；打开报销/决议发起对话框并滚动；在 ≥768px 打开同页；三风格各检查一次 | 窄屏底部恰 5 项带文字标签、页面单列、8 个导航项不挤行；对话框内提交按钮吸底（已知并非"标签栏上方"）；内容底部不被标签栏遮挡；桌面显示顶部导航、无标签栏、提交按钮不吸底 | Chrome 响应式模式 + 手机浏览器 | 是 |
| MV-06 | AC-076-01、AC-077-01、AC-090-01 / TC-UNIT-109 | 在个人中心/我的页点击风格，用 DevTools Performance 或录屏计时到新风格完整渲染 | ≤ 1 s；无需刷新/确认步骤 | Chrome / 微信开发者工具 | 是 |
| MV-07 | AC-090-02、AC-090-03 / TC-UNIT-104 | 保存风格 C 后刷新任一页面并录屏逐帧检查；用限速网络模拟偏好读取变慢 | 首屏即风格 C，无先 B/旧样式后跳变帧；读取慢时按设备记忆呈现，无空白页 | Chrome + 录屏 | 否 |
| MV-08 | AC-089-01/02/03 / TC-UNIT-105、106 | 开启系统"减少动态效果"后在 A/B/C 下浏览并跳转；用低内存/低核数设备或 DevTools 节流 + 修改 `navigator.deviceMemory` 检查风格 A；小程序检查页面切换动画 | 光斑/流光/扫描线/光标闪烁/脉冲等装饰动效 = 0、过渡 = 0；A 的玻璃模糊降级为不透明纯色且正文可读；记录降级是否生效与流畅度结论（无数值指标） | Chrome（可模拟 prefers-reduced-motion）+ 低端安卓机 | 否 |
| MV-09 | AC-088-02/03 / TC-UNIT-105 | DevTools 量取三风格下按钮、输入框、标签栏项高度；用 Tab 键遍历页面；检查所有图标是否带文字 | 点击区域 ≥44px（用户端、管理端、小程序）；任一聚焦元素有可见光环/描边；图标均有文字标签 | Chrome、真机 | 否 |
| MV-10 | AC-087-01/02/03（AC-087-02 PARTIAL） / TC-UNIT-107、204 | 在决议列表查看 表决中/已通过/未通过 标签并将页面转灰度；打开 Web 报销/备用金申请对话框与小程序报销页，检查 5 类组件与决议卡片 | 三种状态仅凭圆点与文字即可区分；Web 5 类组件三风格均按 design_spec §4 呈现；小程序报销页已知无拖拽区/文件列表/竖向步骤条 | Chrome（灰度滤镜）、微信开发者工具 | 否 |
| MV-11 | AC-074-03 / TC-UNIT-101 | 将操作系统/浏览器分别切到深色与浅色模式，依次打开三风格页面 | 页面明暗只取决于所选风格，不随系统变化 | Chrome、手机 | 是 |
| MV-12 | AC-085-01/02 / TC-INT-105、TC-E2E-106 | 在宽屏顶部导航与窄屏底部标签栏中观察当前页高亮的视觉可辨性（决议列表、决议详情、投票） | 仅当前项高亮且肉眼可辨；三风格均如此 | Chrome | 否 |
