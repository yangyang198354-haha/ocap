<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-24T23:21:23+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_multi_account_ux/testing/test_plan.md</file><file>project_workspace/ocap_multi_account_ux/development/implementation_plan.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

## 摘要

critical path 口径：替代（多步 API 旅程 + 页面组件挂载；本机无浏览器/真机 E2E 驱动）
total = pass + fail + skip + blocked + not_testable = 78 + 0 + 0 + 0 + 0 = 78
critical path 覆盖率（E2E 级）= 4/15 = 26.67%（US-341、US-342、US-344、US-348）；替代口径故事覆盖 = 15/15 = 100%（含集成/组件层，见 test_plan 故事覆盖核对）
critical path 通过率 = 1/1 = 100.00%；**本层门控：PASSED**
判定模式：INCREMENTAL / baseline（零新增失败）；新写 E2E 用例 1（TC-E2E-2001）。

## 全量回归

| 套件 | 命令 | 计数 | 相对基线新增失败 |
|---|---|---|---|
| 后端全量 | `python manage.py test --settings=config.test_settings` | `Ran 1256 tests in 125.532s` / `OK (skipped=2)`（pass 1254 / skip 2 / fail 0） | 0（基线 1238，本次 +18 均为新写用例） |
| Web 前端 | `npx vitest run --passWithNoTests` | 57 文件 / 607 用例通过 | 0（基线 595，本次 +12） |
| 小程序 | `npm test` | 22 文件 / 154 用例通过 | 0（基线 151，本次 +3） |

失败逐条比对：无既有失败，无新增失败。

## 用户旅程

### TC-E2E-2001：多账户收入→报销→历史支出全链路与报表口径

- 关联：US-341、US-342、US-344、US-348；AC-412-01、AC-413-02、AC-415-02、AC-416-02、AC-419-01、AC-420-02
- 环境：`config.test_settings`，真实 Django 路由 + 审批引擎 + 台账服务；账户 A=默认、B=公共收益账户
- 测试数据唯一化：本用例数据在测试库内构造，日期取运行日，无持久环境写入。
- 文件：`backend/tests/e2e/test_multi_account_ux_journey.py::MultiAccountFinanceJourneyTests::test_income_reimbursement_and_historical_expense_all_land_in_selected_account`

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 导入 500.00 收入到账户 B 并提交审批、审批通过 | 草稿 account_id=B；审批后台账记 B | 返回 account_id=2/B；审批通过 | PASS |
| 2 | 提交报销 300.50 到账户 B 并审批通过 | 报销 account_name=B；仅 B 记 -300.50 | account_name=公共收益账户；B 余额 199.50 | PASS |
| 3 | 导入 100.00 历史支出到 B（审批前） | 批次 PENDING、posted_rows=0、B 余额不变 | PENDING/0；B 余额 199.50 | PASS |
| 4 | 审批通过历史支出 | 批次 IMPORTED，B 余额 99.50 | IMPORTED；B=99.50 | PASS |
| 5 | 校验默认账户 A | A 全程 0.00 | A=0.00 | PASS |
| 6 | 生成当季报表并按账户 B 查列表与详情 | 列表 B 收入 500.00/支出 400.50/结余 99.50，与详情一致 | 完全一致 | PASS |
| 7 | 按账户 A 查详情 / 不带账户查详情 | A 全 0；组织口径与 B 相同（仅 B 有流水） | 一致 | PASS |

- 结论：PASS

## 缺陷

无。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-01 | AC-410-01/02 / TC-WEB-2001 | 管理后台财务-账户页查看“编辑”“设为默认”“停用/启用”按钮 | 按钮文字与背景对比清晰可辨（WCAG AA ≥ 4.5:1），默认账户“设为默认”置灰 | Chrome / Edge 桌面浏览器，测试环境 192.168.31.51:8090 | 否 |
| M-02 | AC-417-01/02 / TC-WEB-2009 | 报表页在 1440px、1024px、768px 宽度下查看 3/8 个账户卡片 | 卡片从左到右等分屏宽；账户多于可视宽度时出现横向滚动条，不换行挤压 | Chrome / Edge 桌面浏览器 | 否 |
| M-03 | AC-417-03 / TC-WEB-2009 | 8 个账户时横向滚动卡片区 | 合计余额标题与金额固定不随卡片滚动 | Chrome / Edge 桌面浏览器 | 否 |
| M-04 | AC-421-01/02/03 / TC-WEB-2010 | 打开任一账户报表详情，核对指标与明细 | 收入绿色系、支出红色系，与账户卡片流水颜色一致；仅支出/空明细显示正常 | Chrome / Edge 桌面浏览器 | 否 |
