<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T22:41:08+08:00</timestamp>
  <project_name>ocap_fix_defb_def024</project_name>
  <version>1.0.0</version>
  <input_files><file>development/implementation_plan.md</file><file>phase_status.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

## 摘要
critical path 口径：替代（本批无新增 Must Have 故事；以本地 e2e 层现有用例 + TC-INT-720/721、TC-INT-730~739 的 HTTP 级用例代替）
- 本地 e2e 层：`manage.py test tests.e2e` -> Ran 61 / OK；total = pass + fail + skip + blocked + not_testable = 61 + 0 + 0 + 0 + 0 = 61；通过率 100%
- critical path 覆盖率 = 1/1（US-205 有已执行用例 TC-INT-720/721；DEF-025 涉及的五处接口各有已执行用例）；通过率 = 100%
- 本层门控：PASSED（远程 TC-E2E-321/324 待部署后验证，见人工验证清单）

## 全量回归
命令：`(cd backend && manage.py test --settings=config.test_settings)`
```
Ran 957 tests in 76.010s
OK
```
957 = 基线 947 + 新写 10（TC-INT-730~739）；分层：unit 203 + integration 687 + e2e 61 + smoke 6 = 957；相对基线新增失败 0。前端、小程序本批未改动，未重跑，沿用基线。

## DEF-B 修改登记（backend/tests/remote/remote_cases.py，仅期望文案；同 0.1.0）
| 行 | 原 | 新 |
|---|---|---|
| 68 docstring | 两行（户主 + 同住人）、汇总"户主" | 两行（产权业主 + 同住人）、汇总"产权业主" |
| 77 | sorted labels == ["同住人", "户主"] | ["产权业主", "同住人"] |
| 78 | summary.label == "户主" | "产权业主" |
| 83 | identity_label == ["户主"] | ["产权业主"] |
| 114 | identity_label == "户主" | "产权业主" |
remote 套件不在本地运行（P4-1），仅 ast/py_compile；部署后经授权由 GROUP_E2 运行，期望 TC-E2E-321、324 转为通过。

## 用户旅程
本批无新增本地旅程；见全量回归。

## 缺陷
无新增产品缺陷。DEF-024、DEF-025 的修复已由回归用例验证（修复前失败、修复后通过）。

## 观察项
DEF-025 排查时开发另查得 income/views.py strptime、registry fromisoformat、content ai_jobs fromisoformat 均非外部输入或已自行处理，未测。

## 人工验证清单
| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-1 | TC-E2E-321、TC-E2E-324（DEF-B） | 部署后经用户授权，按 P4-1 在测试环境运行 backend/tests/remote 入口 | 两用例通过，标签均为"产权业主" | 测试环境 + e2e 夹具 | 否 |
