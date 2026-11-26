<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-27T01:05:00+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告 — Web 端字体与标题统一

## 摘要

- 执行时间：2026-11-27 00:59 ~ 01:04；环境：Windows PowerShell 5 / Node 22.12 / vitest run（jsdom）。
- 命令：`$env:VITE_API_BASE='/ocap/api/v1'; npm --prefix frontend run test`（全量；本层计数取自该次全量运行的按文件分解）。
- 本层范围：跨组件/路由挂载页面（真实 Vue 路由、mock HTTP）：`layout_pages`、`layout_nav`、`pages`、`qa_int_theme`、`identity_property_match_panel`。
- 度量：**total = 99 = pass 99 + fail 0 + skip 0 + blocked 0 + not_testable 0**。
- 通过率 = 99 / (99 + 0 + 0) = **100%**；判定模式：baseline 零新增失败；**本层门控：PASSED**。
- 单元层门控已 PASSED，故执行本层。

## 执行输出

最后一次执行（全量回归）输出尾部：

```
Test Files  1 failed | 60 passed (61)
     Tests  1 failed | 630 passed (631)
```

按文件（本层）：

```
✓ tests/layout_pages.spec.js (34 tests)
✓ tests/layout_nav.spec.js (19 tests)
✓ tests/pages.spec.js (14 tests)
✓ tests/qa_int_theme.spec.js (15 tests)
✓ tests/identity_property_match_panel.spec.js (17 tests)
```

## 分项结果（按集成边界）

| TC / 用例 | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| layout_pages 页面标题断言 | 361-01、361-02、362-03、363-01、363-03、367-02、368-02 | 管理端 16 页 + 用户端接入 PageHead，h1 唯一/文本正确 | PASS | — | — |
| layout_nav TC-INT-801~812 | 364-01 | 一二级导航渲染、术语「我的认证与申诉」 | PASS | — | — |
| layout_pages TC-INT-889 | 363-03、364-03 | 两端「信息公开」h1 一致 | PASS | — | — |
| pages.spec TC-WEB-017~028 | 364-01、368-02 | 角色页面渲染、动态标题 | PASS | — | — |
| identity_property_match_panel | 367-02 | 匹配面板 h2.title（区块标题，不再冒充 h1） | PASS | — | — |
| qa_int_theme | 366-01、367-01 | 主题切换下布局/卡片一致性 | PASS | — | — |

## 与基线对比（baseline 模式）

- 本层 99 项 **零失败**；相对基线**零新增失败**。
- 唯一失败 `product_review_ui.spec.js` TC-UNIT-577（AC-154-04/AC-166-01 委员导航应含「报销/备用金」）**不在本层受影响文件内**，且经干净基线复跑逐字复现，属**预存基线失败**，非本次改动引入：
  - 该测试文件不在本次 diff 内；
  - 失败机制为 `auth.isCommittee` 过滤（`menus.js` `audience:'committee'` 项被过滤），本次未改 `auth.js`/`PortalLayout.vue`/菜单过滤逻辑；
  - 干净基线（`git stash -u`）全量同样 621 pass / 1 fail，失败用例与断言逐字一致。

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| TC-UNIT-577（预存，非本次引入） | 委员侧栏缺「报销/备用金/收入表/待办」，与非委员一致 | `auth.isCommittee` 计算或测试 mock 时序（`product_review_ui.spec.js` 的 `ME('MEMBER')` 未使 committee 生效） | 记录为 CR-404，预存缺陷，不在本批次范围；建议后续单独修复，不阻塞本次交付 |
