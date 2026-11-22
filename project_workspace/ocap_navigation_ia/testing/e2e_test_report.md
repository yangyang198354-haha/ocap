<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T12:52:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告

## 摘要

critical path 口径：替代（前端组件级多步用户旅程 + 小程序页面级多步旅程；项目无浏览器/真机 E2E 驱动框架）

- 执行时间：2026-11-22T12:51+08:00；环境：Vitest + jsdom，HTTP/uni mock。
- 命令：
  - frontend：`npx vitest run tests/layout_e2e.spec.js tests/identity_property_e2e.spec.js tests/batch1118_e2e.spec.js`
  - miniprogram：`npx vitest run tests/navigation_ia.spec.js -t "TC-E2E-11"`
- `total = pass + fail + skip + blocked + not_testable = 19 + 0 + 0 + 0 + 0 = 19`
- 通过率 = `19 / 19 = 100%`；**本层门控：PASSED**
- critical path 覆盖率 = `11 / 11 = 100%`（Must Have 故事 US-299~307、309、310 均有已执行 E2E 级用例）；critical path 通过率 = `19 / 19 = 100%`。

## 全量回归

| 套件 | 命令 | 计数 | 相对基线新增失败 |
|---|---|---|---|
| frontend | `npm test` | Test Files 51 passed；Tests 575 passed | 0（基线 568 + 新写 7） |
| miniprogram | `npm test` | Test Files 20 passed；Tests 147 passed | 0（基线 138 + 新写 9） |
| backend | `python manage.py test --settings=config.test_settings` | Ran 1167, OK (skipped=2) | 0 |

## 用户旅程

### TC-E2E-801：Web 宽屏导航全流程
- 关联：US-299/300/302/303/306/307；环境：jsdom + mock API。
- 登录 → 展开“我的房屋”3 项 → 进入身份页（双 Tab）→ 审批一条使角标 2→1 → 右上角菜单两组 → `/units/review`、`/me/identity` 兼容。
- 结论：PASS。

### TC-E2E-802：Web 窄屏导航全流程
- 关联：US-299/301/302/303；环境：jsdom + mock API。
- 底栏进入 → 二级切换条 3 项 → “我的认证与申述”仅显示申诉 → 底部“我的”分组 5+1 + 退出登录。
- 结论：PASS。

### TC-E2E-910/911：Web 身份页游客与业主旅程
- 关联：US-300/307；业主双 Tab 与审批；游客仅身份 Tab。
- 结论：PASS。

### TC-E2E-1613：侧栏二级菜单点击与键盘收起
- 关联：US-299；点击“我的认证与申述”导航并只高亮该项。
- 结论：PASS。

### TC-E2E-1101~1104：小程序“我的房屋”三 Tab 旅程
- 关联：US-304；三 Tab 切换、申诉子 Tab、业主审批子 Tab、同住人申请入口。
- 结论：PASS。

### TC-E2E-1105~1108：小程序设置与账号旅程
- 关联：US-305/310；四入口跳转、界面风格保存、邮箱验证三步、注销两步并清登录态。
- 结论：PASS。

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 | 状态 |
|---|---|---|---|---|---|
| DEF-001 | MAJOR | 注销页确认后不发起请求（未知确认类型导致 Promise 拒绝） | TC-E2E-1108 | `miniprogram/pages/cancel/index.vue` → `utils/confirm.js` 缺 `cancelAccount` 文案 | FIXED（补充确认文案后复测通过） |

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | AC-308-02 / TC-INT-1101 | 在桌面浏览器悬停右上角头像 180ms 再移开、点击展开 | 展开/收起可感知但不拖沓；点击立即展开 | Chrome/Edge 桌面 | 否 |
| MV-02 | AC-308-03 | 系统开启“减少动态效果”后重复 MV-01 | 无 400ms 过渡（0s） | 桌面浏览器 + OS 设置 | 否 |
| MV-03 | AC-304-01~04 | 微信开发者工具导入 `miniprogram` 构建产物，走三个 Tab 与子 Tab | 与组件测试一致；无布局错位 | 微信开发者工具 | 是 |
| MV-04 | AC-305-04 | 真机切换界面风格 | 立即生效并持久化 | 微信真机 | 否 |
