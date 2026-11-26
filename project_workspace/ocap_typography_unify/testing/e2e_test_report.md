<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-27T01:05:00+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告 — Web 端字体与标题统一

## 摘要

critical path 口径：**替代（jsdom 路由多步页面旅程，即 E2E 层文件）** —— 项目无真实浏览器 E2E 框架。

- 执行时间：2026-11-27 00:59 ~ 01:04；环境：Windows PowerShell 5 / Node 22.12 / vitest run（jsdom）。
- 命令：`$env:VITE_API_BASE='/ocap/api/v1'; npm --prefix frontend run test`。
- 本层范围（受影响 E2E 文件）：`layout_e2e`（3）、`identity_property_e2e`（4）、`qa_e2e_theme`（4）。
- 度量：**total = 11 = pass 11 + fail 0 + skip 0 + blocked 0 + not_testable 0**。
- **critical path 覆盖率 = 8/8 = 100%**（US-361~368 共 8 个 Must Have，全部有 E2E/INT 真实执行用例）。
- **critical path 通过率 = 100%**（执行的 critical path 用例全部通过）。
- 判定模式：baseline 零新增失败；**本层门控：PASSED**。集成层门控已 PASSED，故执行本层。

## 全量回归

命令：`$env:VITE_API_BASE='/ocap/api/v1'; npm --prefix frontend run test`

```
Test Files  1 failed | 60 passed (61)
     Tests  1 failed | 630 passed (631)
  Duration  291.17s
```

- 相对基线（干净 HEAD：621 pass / 1 fail）：**新增失败数 = 0**。总数 622 → 631 的 +9 全部为新增通过用例（typography_tokens.spec.js）。
- 唯一失败：`product_review_ui.spec.js` TC-UNIT-577（预存基线失败，干净基线逐字复现，非本次引入；记录为 CR-404，留待后续单独修复）。

## 用户旅程

### TC-E2E-2101：管理端与用户端页面标题统一（对应 layout_e2e）

- 关联：US-361 / AC-361-01、AC-363-01、AC-364-03；US-368 / AC-368-02。环境：jsdom + mock /me。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 路由到个人资料页 | main 内 h1 = ['个人资料']，唯一 | 一致 | PASS |
| 2 | 路由到系统设置页 | main 内 h1 = ['系统设置']，唯一 | 一致 | PASS |
| 3 | 路由到我的认证与申诉 | h1 = ['我的认证与申诉'] | 一致 | PASS |

- 结论：PASS（layout_e2e.spec.js 3 项全过）。

### TC-E2E-2102：详情页实体标题提升为 h1（对应 identity_property_e2e）

- 关联：US-369 / AC-369-01；US-361 / AC-361-01。环境：jsdom + mock。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 路由到身份/房屋详情 | 实体名「我的身份与房屋」为唯一 h1 | mainTitles=['我的身份与房屋'] | PASS |
| 2 | 侧栏当前项 | 仅 1 个 .side-sub-item.is-active | 1 | PASS |

- 结论：PASS（identity_property_e2e.spec.js 4 项全过）。

### TC-E2E-2103：三主题切换下版式一致（对应 qa_e2e_theme）

- 关联：US-366 / AC-366-01、US-367 / AC-367-01。环境：jsdom。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 切换 bento/neon/terminal | 导航/卡片结构一致，无横向异常 | 一致 | PASS |

- 结论：PASS（qa_e2e_theme.spec.js 4 项全过）。

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| 无（本层无新增缺陷） | — | — | — | — |

> 预存失败 TC-UNIT-577（委员导航过滤）不属于本层 E2E 用例，且已确认为基线既有问题，见 integration_test_report 与 code_review_report，记录为 CR-404，不在本次范围。

## 人工验证清单

以下 AC 的真实视觉效果 jsdom 无法断言（不计算布局/字形宽度/对比度），已用源码断言做静态守护，需人工在真实浏览器复核：

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-01 | AC-366-03 / TC-UNIT-2106 | 部署到树莓派测试环境后，分别切到 bento/neon/terminal，打开同一页面（如 /resolutions）侧栏与标题，用浏览器 DevTools 量同一中文标题宽度 | terminal 标题不被强制大写、无 .06em 字距；三套主题同一中文标题宽度误差 ≤ 2px | 树莓派测试环境 + 桌面浏览器 | 是（US-366） |
| M-02 | AC-369-02 / TC-UNIT-2108 | 375px 视口（DevTools 移动模拟）打开含长标题页面（如 AdminFinance「财务报表与账户管理」、各详情页） | 长标题正常换行，不被截断（无 ellipsis/nowrap），无横向滚动条 | 树莓派测试环境 + 移动模拟 375px | 否（US-369 为 Should Have） |

> 说明：M-01/M-02 需先部署到测试环境方可执行；本次未授权部署，故列为待人工执行项，不计入自动化通过率分母（NOT_TESTABLE）。
