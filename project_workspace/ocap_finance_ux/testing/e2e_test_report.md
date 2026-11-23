<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-23T23:33:00.0000000+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/testing/test_plan.md</file>
    <file>backend/tests/e2e/test_finance_accounts_journey.py</file>
    <file>frontend/tests/finance_accounts_ui.spec.js</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告 — ocap_finance_ux

## 摘要

critical path 口径：替代（多步 API 旅程 TC-E2E-1401 + 前端组件用例 TC-WEB-1401~1405；项目无浏览器 E2E 框架）

- 执行时间：2026-11-23 23:28–23:32；环境：Django 测试设置 + vitest。
- E2E 计数：total = pass + fail + skip + blocked + not_testable = 1 = 1 + 0 + 0 + 0 + 0。
- 前端组件计数：total = 5 = 5 + 0 + 0 + 0 + 0。
- critical path 覆盖率 = 8 / 9 = 88.9%（US-327 为 NOT_TESTABLE，原因见人工清单 M-01）。
- critical path 通过率 = 100.0%。
- 判定：baseline（零新增失败）；**本层门控：PASSED**。

## 全量回归

```
$ python manage.py test --settings=config.test_settings
Ran 1206 tests in 82.199s
OK (skipped=2)

$ npx vitest run
Test Files  53 passed (53)
```

基线（GROUP_C 门控）：后端 1188 / 前端 52 文件。相对基线新增失败数：0（新增 18 条后端用例 + 1 个前端测试文件 / 5 条用例）。

## 用户旅程

### TC-E2E-1401: 建账户 → 收入生效 → 余额/流水 → 链式报表 → 作废级联 → 停用

- 关联：US-322/323/324/325/326/328/329/330（AC-401/402/403/404/405/407/408/409）。
- 环境：`tests/e2e/test_finance_accounts_journey.py`，真实认证与审批链。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 管理员 POST `/admin/ledger/accounts` | 201，余额 0.00 | 201，`balance=0.00` | PASS |
| 2 | 业委会成员带 `account_id` 建收入表 → 提交 → 审批通过 | 流水归属所选账户 | `LedgerEntry.account_id` 命中 | PASS |
| 3 | GET `/ledger/accounts/summary` | 余额 100.00、最近 1 笔 | 与期望一致 | PASS |
| 4 | 生成 Q1、Q2、YEAR 2025 | Q1 期初 0/期末 100；Q2 期初=Q1 期末；年度期末=Q2 期末 | 全部相等 | PASS |
| 5 | GET 报表列表 `period_type=YEAR`；GET 详情 `account_id` | 仅 1 条年度；账户视角期末 100.00 | 与期望一致 | PASS |
| 6 | 审批人作废收入表 → 重生成 Q1 | 后续期间标记过期；Q1/Q2 期末归 0，Q2 stale=false | 与期望一致 | PASS |
| 7 | 管理员停用账户 → GET summary?status=ENABLED | 不含停用账户；历史余额仍为 0.00 | 与期望一致 | PASS |

- 结论：PASS

### 前端组件旅程（关键交互）

| TC | 场景 | 结果 |
|---|---|---|
| TC-WEB-1401 | 报表页展示账户合计/卡片/最近流水 | PASS |
| TC-WEB-1402 | 「仅年报」筛选按 period_type 重新请求 | PASS |
| TC-WEB-1403 | 点击报表打开浮层、显示期初/期末、关闭后列表保留 | PASS |
| TC-WEB-1404 | 主页账户卡片合计/账户名，点击进入 /reports | PASS |
| TC-WEB-1405 | 管理端新建账户空表单提示必填且不发请求 | PASS |

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 | 状态 |
|---|---|---|---|---|---|
| DEF-001 | MAJOR | 「仅年报/仅季报」筛选不生效（请求未带 `period_type`）；`el-option :value="null"` 触发 Element Plus 属性类型告警 | TC-WEB-1402、TC-WEB-1403 | `frontend/src/portal/Reports.vue`（`usePaging.filters` 需为 ref/computed）、`ReportDetailDialog.vue`（全部账户选项改空串） | FIXED（GROUP_C 缺陷修复，重跑通过） |

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需环境 | critical path |
|---|---|---|---|---|---|
| M-01 | US-327 / AC-406-03/04 | 在测试环境 MySQL 快照上依次执行 0004→0006，重复执行回填迁移 | 默认账户唯一；全部流水有账户；总额不变；重复执行无新增账户 | 树莓派测试环境 + MySQL 快照 | 是 |
| M-02 | AC-401-06 | 报表页选「仅年报」后刷新浏览器 | 回到「全部」、第 1 页 | 浏览器 | 否 |
| M-03 | AC-402-03 | 360px 视口打开报表浮层 | 浮层不横向滚动，明细内滚动 | 浏览器设备模拟 | 否 |
| M-04 | AC-402-04 | 系统开启“减少动态效果”后打开浮层 | 无位移/缩放动画 | 浏览器 | 否 |
| M-05 | AC-408-04 | 断开后端使汇总接口失败后打开主页 | 卡片显示“加载失败 + 重试”，其他区块正常 | 浏览器 + 测试环境 | 否 |
