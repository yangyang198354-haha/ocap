<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T22:41:08+08:00</timestamp>
  <project_name>ocap_fix_defb_def024</project_name>
  <version>1.0.0</version>
  <input_files><file>development/implementation_plan.md</file><file>phase_status.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

## 测试策略
- 被测改动：DEF-024（committee/views.py term_start）；DEF-025（accounts birthday、claims occurred_on / expected_settle_on、polls deadline、resolutions vote_deadline：不存在日期 → 原 400 INVALID_VALUE）；DEF-B（remote_cases.py 期望文案，不本地运行）。
- 环境：venv Python（Django 5.2），config.test_settings，SQLite 内存库。判定：baseline，零新增失败且新写用例全部通过。基线（GR-C-002 后）：后端 947 OK。
- 范围外：income/registry/content 的 strptime/fromisoformat（非外部输入）。

## AC 映射
| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置 | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-205-01（DEF-024） | TC-INT-720 / 721 | integration | sim | 新写（0.1.0） | tests/integration/test_def024_seat_term_start.py | 管理员、产权业主、名额任期已配置 | POST /admin/committee/seats | 坏日期 400 INVALID_VALUE；合法 201 | 内存库 |
| DEF-025 accounts | TC-INT-730 / 731 | integration | sim | 新写 | tests/integration/test_def025_nonexistent_dates.py::Def025NonexistentDateTests | 已登录产权业主（CHAIR 席位） | PATCH /me/profile | 2026-02-30、2026-13-01、123 → 400「生日格式不正确」；1990-05-06 → 200 | 内存库 |
| DEF-025 claims 报销 | TC-INT-732 / 733 | integration | sim | 新写 | 同上 | EXPENSE 审批流 + 发票附件 | POST /claims/reimbursements | 2026-02-30 → 400「请填写费用发生日期」；今天 → 201 | 同上 |
| DEF-025 claims 备用金 | TC-INT-734 / 735 | integration | sim | 新写 | 同上 | 同上 | POST /claims/advances | 2026-02-30 → 400「预计核销日期须晚于今日」；10 天后 → 201 | 同上 |
| DEF-025 polls | TC-INT-736 / 737 | integration | sim | 新写 | 同上 | CHAIR 席位 | POST /polls | 2026-02-30T10:00 → 400「截止时间格式不正确」；2 天后 → 201 | 同上 |
| DEF-025 resolutions | TC-INT-738 / 739 | integration | sim | 新写 | 同上 | RESOLUTION/HALF_MAJORITY 审批流 | POST /resolutions | 2026-02-30T10:00 → 400「半数同意决议须填写投票截止时间」；2 天后 → 201 | 同上 |
| DEF-B（AC-157-01/03/04、AC-159-01/06 的远程期望） | TC-E2E-321、324 | e2e（远程） | 仅部署后经授权远程执行 | 现有修改 | backend/tests/remote/remote_cases.py :68、:77、:78、:83、:114 | — | — | "产权业主" | 远程夹具 |
DEF-025 无独立 US/AC 编号，用例溯源到 DEF-025 与 implementation_plan 2.0.0 追溯表。

## 测试数据需求
无 [DATA_REQUIRED]。

## 不可测项
| AC | 原因 |
|---|---|
| TC-E2E-321/324 本地执行 | 远程用例按 P4-1 不在本地运行；已列入人工验证清单 |

## 故事覆盖核对
本批为缺陷修复，无 Must Have 故事新增；受影响故事 US-205。
| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-205 | TC-INT-720、TC-INT-721 | integration |
