<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T22:41:08+08:00</timestamp>
  <project_name>ocap_fix_defb_def024</project_name>
  <version>1.0.0</version>
  <input_files><file>development/implementation_plan.md</file><file>phase_status.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

## 摘要
- 执行时间：2026-11-16；命令：`(cd backend && manage.py test tests.integration --settings=config.test_settings)`
- total = pass + fail + skip + blocked + not_testable = 687 + 0 + 0 + 0 + 0 = 687（含新写 12：DEF-024 的 2 + DEF-025 的 10）；通过率 = 687/687 = 100%
- 判定模式 baseline：零新增失败，新写用例全部通过。本层门控：PASSED

## 执行输出
```
Ran 687 tests in 46.877s
OK
```
新写文件单独：`tests.integration.test_def024_seat_term_start` -> Ran 2 / OK；`tests.integration.test_def025_nonexistent_dates` -> Ran 10 / OK。

## 分项结果（HTTP/DRF 视图 ↔ 日期解析）
| TC | AC | 描述 | 结果 | 实际输出 | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-720 | AC-205-01 / DEF-024 | committee term_start=2026-02-30、2026-13-01、abc → 400 INVALID_VALUE，无席位 | PASS | — | — |
| TC-INT-721 | AC-205-01 | 合法 term_start 仍 201 | PASS | — | — |
| TC-INT-730 | 个人资料 PATCH /me/profile / DEF-025 | birthday=2026-02-30、2026-13-01、123（非字符串）→ 400 INVALID_VALUE「生日格式不正确」 | PASS | — | — |
| TC-INT-731 | 同上（正例） | birthday=1990-05-06 → 200 且读回一致 | PASS | — | — |
| TC-INT-732 | 报销发起 / DEF-025 | occurred_on=2026-02-30 → 400「请填写费用发生日期」 | PASS | — | — |
| TC-INT-733 | 同上（正例） | occurred_on=今天 → 201 | PASS | — | — |
| TC-INT-734 | 备用金发起 / DEF-025 | expected_settle_on=2026-02-30 → 400「预计核销日期须晚于今日」 | PASS | — | — |
| TC-INT-735 | 同上（正例） | 10 天后 → 201 | PASS | — | — |
| TC-INT-736 | 投票创建 / DEF-025 | deadline=2026-02-30T10:00 → 400「截止时间格式不正确」 | PASS | — | — |
| TC-INT-737 | 同上（正例） | 2 天后 → 201 | PASS | — | — |
| TC-INT-738 | 决议创建 HALF_MAJORITY / DEF-025 | vote_deadline=2026-02-30T10:00 → 400「半数同意决议须填写投票截止时间」 | PASS | — | — |
| TC-INT-739 | 同上（正例） | 2 天后 → 201 | PASS | — | — |
说明：DEF-025 属缺陷修复，无独立 US/AC 编号；TC-INT-730~739 溯源到 DEF-025（implementation_plan 2.0.0 需求追溯表）。

测试写错记录：TC-INT-721（上一轮）因夹具缺名额配置修 1 轮；本轮夹具按 test_finance_polls_api / test_product_review_ac 既有 setUp（CHAIR 席位 + EXPENSE 审批流）准备，一次通过，无修改轮次。

## 变异验证
(1) DEF-024：见 0.1.0，TC-INT-720 在修复前树 errors=2。
(2) DEF-025：`git archive 5b5e72d backend` 导出修复前树（不含 DEF-024/025 修复），复制 test_def025_nonexistent_dates.py 运行：
```
Ran 10 tests in 0.203s
FAILED (errors=7)
```
7 个 ERROR = TC-INT-730 的 3 个子用例（2026-02-30、2026-13-01、123）+ TC-INT-732、734、736、738；正例 731、733、735、737、739 修复前即通过（符合预期）。修复后工作树 Ran 10 / OK。五处各至少一条负例在修复前失败，已确认。

## 与基线对比
零新增失败；既有失败：无。

## 失败汇总（需路由给开发）
无。
