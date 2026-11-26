<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-27T01:05:00+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/testing/test_plan.md</file>
    <file>frontend/tests/typography_tokens.spec.js</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告 — Web 端字体与标题统一

## 摘要

- 执行时间：2026-11-27 00:59 ~ 01:04；环境：Windows PowerShell 5 / Node 22.12 / vitest run（jsdom）。
- 命令：`$env:VITE_API_BASE='/ocap/api/v1'; npm --prefix frontend run test`（全量；本层计数取自该次全量运行的按文件分解）。
- 本层范围：与本次改动相关的单元层文件（读 CSS 源 / 单组件、外部依赖 mock）：`typography_tokens`（新）、`layout_css`、`layout_menus`、`theme_build`、`theme`、`brand`、`admin_theme`、`ui_blocks`。
- 度量：**total = 99 = pass 99 + fail 0 + skip 0 + blocked 0 + not_testable 0**。
- 通过率 = 99 / (99 + 0 + 0) = **100%**；判定模式：baseline 零新增失败；**本层门控：PASSED**。
- 新增用例：`typography_tokens.spec.js` 9 项全部通过。

## 执行输出

最后一次执行（全量回归）输出尾部：

```
Test Files  1 failed | 60 passed (61)
     Tests  1 failed | 630 passed (631)
```

按文件（本层）：

```
✓ tests/typography_tokens.spec.js (9 tests) 20ms
✓ tests/layout_css.spec.js (15 tests)
✓ tests/layout_menus.spec.js (21 tests)
✓ tests/theme_build.spec.js (7 tests)
✓ tests/theme.spec.js (14 tests)
✓ tests/brand.spec.js (10 tests)
✓ tests/admin_theme.spec.js (11 tests)
✓ tests/ui_blocks.spec.js (12 tests)
```

## 分项结果（新增用例）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-2101 | 365-01、368-01 | 页面标题令牌 24/32/700、窄屏 22/30；.page-head h1/.page-title 只引用令牌 | PASS | — | — |
| TC-UNIT-2102 | 365-02、367-01 | 卡片标题令牌 18/26/650；bento/generated 无 20px 覆盖 | PASS | — | — |
| TC-UNIT-2103 | 365-03 | 分区标题 14/20；三层级字号均 var(--text-*) | PASS | — | — |
| TC-UNIT-2104 | 366-01 | 一级导航 15/600；三主题+generated .side-item 无 font-size 覆盖 | PASS | — | — |
| TC-UNIT-2105 | 366-02 | 二级导航 13/500；13<15；三主题不覆盖 | PASS | — | — |
| TC-UNIT-2106 | 366-03、367-03 | terminal 标题/导航不 uppercase、无 .06em；保留 --mono | PASS | — | — |
| TC-UNIT-2107 | 362-01 | style.css + 三主题 + generated 无 .page-eyebrow | PASS | — | — |
| TC-UNIT-2108 | 362-01、369-02 | terminal 无 h1::before "> " 前缀；标题无 ellipsis/nowrap | PASS | — | — |
| TC-UNIT-2109 | REQ-NFUNC-080 | generated 已同步清理（无 side-item 字号覆盖/20px 放大/标题 uppercase） | PASS | — | — |

新增用例初期 2 处断言假设错误（合并选择器匹配、生成态是否重声明基础令牌）已按源码修正为与实现对齐，属**测试问题**（非产品缺陷），修正后 9/9 通过。

## 与基线对比（baseline 模式）

- 基线（干净 HEAD，本次改动 stash 后）：前端 621 pass / 1 fail。
- 本次（含新增用例）：630 pass / 1 fail。差的 +9 全部为新增通过用例。
- 本层 99 项 **零失败**；相对基线**零新增失败**。

## 失败汇总（需路由给开发）

无（本层无失败）。唯一失败 `product_review_ui.spec.js` TC-UNIT-577 属集成/导航域，为预存基线失败，详见 integration_test_report「与基线对比」与 code_review_report「基线对比」。
