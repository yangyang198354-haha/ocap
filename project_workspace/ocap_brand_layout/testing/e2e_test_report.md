<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-17T09:10:00+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>testing/integration_test_report.md</file><file>development/implementation_plan.md（2.0.0）</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告：品牌更名 + 左侧导航布局（INCREMENTAL，GROUP_D-003，缺陷回流 1/2 后重跑）

## 摘要

critical path 口径：替代（jsdom 整 App 旅程：真实 App + 真实路由 + 假服务端，`frontend/tests/layout_e2e.spec.js`；项目无浏览器 E2E 框架；US-208 以小程序最高层可执行用例 TC-UNIT-881~895 替代）

- 执行时间：2026-11-17T09:02:50+08:00 起（E2E 层）；09:03:22 起全量回归。环境：Node + vitest（jsdom），无外网，HTTP 全部 mock。
- 命令：`(cd frontend && npx vitest run --passWithNoTests tests/layout_e2e.spec.js tests/qa_e2e_extend.spec.js tests/qa_e2e_theme.spec.js tests/qa_e2e_pages.spec.js)`
- **本层门控：PASSED**（INT 层门控 PASSED 后执行；相对基线零新增失败，新写 E2E 用例 3/3 通过）。
- 本层 metrics：total = pass + fail + skip + blocked + not_testable = 11 + 0 + 0 + 0 + 5 = 16（执行 11 条：新写 TC-E2E-801~803 共 3 条 + 既有已同步 qa_e2e_* 8 条；5 条为人工验证项 MV-01~05，NOT_TESTABLE，不计入通过率分母）。通过率 = pass/(pass+fail+blocked) = 11/11 = 100%。
- critical path 通过率 = 3/3 = 100%（TC-E2E-801~803）；加替代用例 US-208 的 TC-UNIT-881~895（小程序 brand_login 15/15）共 18/18 = 100%。
- critical path 覆盖率 = 有 E2E 级用例的 Must Have 故事 / Must Have 故事总数：可自动化范围 20/20 = 100%（19 个有 jsdom 旅程用例：US-207、209~216、220、222~227、229、230、231；US-208 以小程序最高层用例替代）；含待人工的口径 20/22 = 90.9%，缺口 US-218、US-219 只能真实视口度量，NOT_TESTABLE，已列人工清单 MV-01/02，计"待人工验证"，不计入通过率分母。
- critical path 中待人工验证条数 = 4（MV-01、MV-02、MV-04、MV-05，均对应 Must Have 故事）；非 critical path 待人工 1 条（MV-03，US-228 Should Have）。只要这些未完成，最终状态至多 DELIVERED_WITH_ISSUES。
- 已知局限：TC-E2E-801 步骤 4 仍按"进入 /units* 后"断言角标（`layout_e2e.spec.js:185` 的注释写于 DEF-002 修复前，测试冻结未改）；该旅程本身不再证明/反证 DEF-002，修复由 TC-INT-914（真实登录链路）守护并已 PASS。
- 缺陷：DEF-001、DEF-002 均已修复并回归通过，当前无未解决缺陷。

## 全量回归

命令与计数（修复后实跑，最后一次执行，冻结后无测试文件改动）：

```
(cd frontend && npx vitest run --passWithNoTests)      [09:03:22]
 Test Files  37 passed (37)
      Tests  438 passed (438)
(cd miniprogram && npx vitest run --passWithNoTests)   [09:06:46]
 Test Files  16 passed (16)
      Tests  119 passed (119)
```

- 前端 438 = 基线 281 + 新写 157，全部通过；小程序 119 = 基线 104 + 新写 15，全部通过。
- 总计 557：total = pass + fail + skip + blocked + not_testable = 557 + 0 + 0 + 0 + 0 = 557（不含人工验证项 MV-01~05）。
- **相对基线新增失败 = 0 条**（与 PM 在 GR-C-003 的实跑一致：前端 37 文件 438/438，小程序 16 文件 119/119）。0.1.0 的 2 条失败（TC-INT-874、TC-INT-914）已转绿。
- 后端：**未运行**，不标 PASS，不计入计数。证据：`git diff --stat HEAD -- backend frontend/src/shared/api.js miniprogram/utils/api.js` 输出 0 行（零改动）；本机无 Django（画像 P4）。

## 用户旅程

### TC-E2E-801：用户端宽屏旅程（业委会成员）
- 关联：US-207/209/210/211/212/213/214/215/216/221/222/229；AC-207-01/03、209-01/02、210-01/04、212-01~05、213-01/06、214-02/03、215-01/04、216-01~03、221-01/02、222-02、229-01、217-01
- 环境：jsdom 整 App，假服务端，设备风格记忆 neon（用例 3985ms）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 打开 /login | 品牌名+neon 配图、无风格入口、静态标题 | 与期望一致 | PASS |
| 2 | 登录 → 主页 | 9 个一级、二级全部收起、右上角昵称 | 一致 | PASS |
| 3 | 决议展开/我发起的 | 同时只展开一个；二级项高亮 | 一致 | PASS |
| 4 | 我的房屋展开 → 待我审批 → 审批后 | 二级 6 项；进入 /units* 后角标 2→1 | 一致（断言点为进入后，见"已知局限"） | PASS |
| 5~9 | 信息公开直达；右上角菜单 8 项、改昵称；风格 C；旧地址兼容；退出 | 与 AC 一致 | 一致 | PASS |
- 结论：PASS

### TC-E2E-802：非成员与窄屏旅程
- 关联：US-211、220、230；AC-211-01/03、220-01/02/03/05、230-01/02；环境：jsdom，窄屏用 matchMedia 桩（用例 1499ms）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 非成员登录 | 一级菜单 6 项，无报销/收入表/待办 | 一致 | PASS |
| 2 | 直达 /claims | 不白屏，行为同改动前 | 一致 | PASS |
| 3 | 窄屏进入 /me | "我的"总览页：7 项入口 + 退出登录 | 一致 | PASS |
| 4 | 点击"个人资料" | 一次点击进入个人资料页 | 一致 | PASS |
- 结论：PASS

### TC-E2E-803：管理端旅程
- 关联：US-207(AC-207-04)、223~227、231；AC-223-01、224-01~03、225-01/02/04、226-01~04、227-01/02、231-03/04；环境：jsdom，管理端独立风格记忆（用例 3951ms）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 打开 /admin/login | 读 ocap_admin_theme、品牌配图、无风格入口 | 一致 | PASS |
| 2 | 登录 → /admin/registry | 左侧导航 9 项，二级收起；账号/内容管理展开与高亮 | 一致 | PASS |
| 3 | 右上角菜单 | 3 风格项 + 退出，切换风格与账号名显示 | 一致 | PASS |
| 4 | 窄屏 | 抽屉可唤出，选二级项后关闭 | 一致 | PASS |
| 5 | 退出 | 清令牌与账号名，回 /admin/login | 一致 | PASS |
- 结论：PASS

### 既有 E2E 回归（已同步，8 条）
- qa_e2e_theme TC-E2E-101（1）、TC-E2E-102（3）、qa_e2e_pages TC-E2E-104/105/106（3）、qa_e2e_extend TC-E2E-103（1）：全部 PASS（单独跑 `Test Files 4 passed (4) / Tests 11 passed (11)`，含上述新写 3 条）。

## 缺陷

| DEF | 级别 | 状态 | 现象 | 回归用例（结果） | 位置 |
|---|---|---|---|---|---|
| DEF-001 | MINOR | **已修复**（GROUP_C-003，GR-C-003） | `artFor('__proto__'/'constructor'/'toString'/'hasOwnProperty')` 曾返回非组件对象，违反 IFC-327 | TC-INT-874：0.1.0 FAIL → 0.2.0 PASS | `frontend/src/brand/art/index.js:10` |
| DEF-002 | MAJOR | **已修复**（GROUP_C-003，GR-C-003） | 刚登录（`auth.me` 为简要对象）后展开"我的房屋"无角标 2，违反 AC-214-03 | TC-INT-914：0.1.0 FAIL → 0.2.0 PASS；TC-E2E-801 PASS | `frontend/src/portal/PortalLayout.vue:49` |

## 人工验证清单

全部 NOT_TESTABLE（jsdom 无布局引擎/真实字体/微信渲染引擎）；不计入通过率分母。建议在部署后的测试环境（画像 P4-1 只读浏览，无写入）或本地 `npm run dev` 由人工完成。

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | AC-218-01~04、219-01/03、220-04、230-03、231-01、227-04、209-04；静态口径 TC-UNIT-861~867、872、873 | 浏览器缩放 100%，视口依次 1366×768、1920×1080、2560×1440、3840×2160（另 1280×720、4K 缩放 150%）；用户端打开主页/决议/报销/收入表/财务报表/信息公开，管理端打开业主清册/申诉/房屋关系/审批流程/账号/审计配置，登录页同样；DevTools 在 767↔768 宽度间拖动 | (a) 无横向滚动条（scrollWidth ≤ 视口宽）；(b) 侧栏右侧内容区主要内容占用宽度 ≥ 90%；(c) 1366×768 下用户端业委会成员 9 项、管理端 9 项一级菜单无需滚动全部可见；767/768 切换时底栏与侧栏/抽屉不同时出现；登录页配图不覆盖表单 | 桌面浏览器 + DevTools 设备模拟（或相应分辨率显示器） | 是（US-218/219/231 Must） |
| MV-02 | AC-219-02、231-02；TC-UNIT-874、875 | 1366×768 打开 AdminRegistry、AdminSeats、AdminUsers（注册用户）表格与"新增专有部分"弹窗；用户端决议列表/收入表/我的房屋各二级页 | 无横向滚动条、控件不重叠、弹窗完整可见；AdminRegistry 静态余量仅约 20px（OQ-B07），重点目视 | 同上，1366 宽 | 是（US-219/231 Must） |
| MV-03 | AC-228-01；TC-UNIT-884~895 | 微信开发者工具（或真机）分别设置本地风格记忆 neon/bento/terminal，打开 `pages/login/index` | 三版均显示"Cyber@红枫岭"与 CSS 配图（渐变/边框/阴影无错位、无缺失），配色随风格；无远程字体请求 | 微信开发者工具 / 真机（本机无；`build:mp-weixin` 基线即失败） | 否（US-228 Should Have） |
| MV-04 | AC-209-05(4)、227-01 | 设备风格记忆分别为 neon/bento/terminal，依次打开 `/login`、`/register`、`/admin/login`（管理端用 `ocap_admin_theme`），按"科技感观察清单"逐项判断 | 清单 4 项全部为"是"；用户本人确认"有赛博科技感"（验收人为用户） | 桌面浏览器 | 是（US-209/227 Must） |
| MV-05 | AC-209-03、227-04；TC-UNIT-846~849 | 用 DevTools 阻断 `OcapBrand-subset-*.woff2` 请求（或离线）后刷新 `/login`、`/register`、`/admin/login`；正常加载时目视品牌名字体；部署后以只读 HTTP 请求核对 `.woff2` 的 `Content-Type`（应为 `font/woff2`，OQ-B05） | 阻断后文字回退系统字体，表单字段/按钮完整可见、无乱码、无字体相关弹窗；正常加载时品牌名为得意黑风格字形 | 桌面浏览器 + DevTools | 是（US-209 Must） |
