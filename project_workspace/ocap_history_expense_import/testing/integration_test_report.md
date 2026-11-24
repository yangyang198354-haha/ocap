<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-23T18:03:30+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/testing/test_plan.md</file><file>project_workspace/ocap_history_expense_import/development/implementation_plan.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（历史支出导入）

## 摘要

- 执行时间：2026-11-23 17:56~18:00；环境：`/tmp/ocap-venv`（Django 5.2，SQLite 内存库，外部服务替身）。
- 命令：
  - `manage.py test tests.integration.test_history_expense_api --settings=config.test_settings`
  - `manage.py test tests.integration.test_frontend_contract --settings=config.test_settings`（前后端契约，现有用例）
- total = pass + fail + skip + blocked + not_testable = 40 = 40 + 0 + 0 + 0 + 0（新写 14 + 契约 26）。
- 通过率 = 40/(40+0+0) = 100%；判定模式：baseline（零新增失败）；**本层门控：PASSED**。

## 执行输出

```
$ cd /workspace/backend && /tmp/ocap-venv/bin/python manage.py test tests.integration.test_history_expense_api --settings=config.test_settings
Ran 14 tests in 0.625s
OK
Found 14 test(s).

$ /tmp/ocap-venv/bin/python manage.py test tests.integration.test_frontend_contract --settings=config.test_settings
Ran 26 tests in 1.105s
OK
Found 26 test(s).
```

## 分项结果（按集成边界）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-INT-2101 | AC-333-01 | 导入服务 ↔ 模板接口：xlsx/csv 内容 | PASS | — |
| TC-INT-2102 | AC-333-02 | 权限类 ↔ 模板接口：401/403 矩阵 | PASS | — |
| TC-INT-2103 | AC-334-01 | 导入服务 ↔ LedgerService ↔ Audit：只写 EXPENSE 台账，不建 Claim/审批实例 | PASS | — |
| TC-INT-2104 | AC-334-02 | 导入服务 ↔ 行明细：混合行错误行号与计数 | PASS | — |
| TC-INT-2105 | AC-334-02 | 导入服务 ↔ 批次：全错不建批次、不写台账 | PASS | — |
| TC-INT-2106 | AC-334-03 | 导入服务 ↔ 历史批次：文件内/历史重复、备注不参与 | PASS | — |
| TC-INT-2107 | AC-334-04 | 上传边界 ↔ 解析：413、5001 行 400、仅首表 | PASS | — |
| TC-INT-2108 | AC-334-05 | 解析 ↔ 接口错误：缺列明细、未来日期行 | PASS | — |
| TC-INT-2109 | AC-335-01/02 | 批次列表/详情序列化 ↔ ORM | PASS | — |
| TC-INT-2110 | AC-336-01 | 作废服务 ↔ 台账/报表/审计 | PASS | — |
| TC-INT-2111 | AC-336-02 | 作废幂等 ↔ 重导与权限 | PASS | — |
| TC-INT-2112 | AC-337-01/03 | 台账 ↔ 报表生成/重算：含历史来源，作废后归零 | PASS | — |
| TC-INT-2113 | AC-337-02 | 报表查询 ↔ 业主/匿名 | PASS | — |
| TC-INT-2114 | AC-338-01 | 权限类 ↔ 5 个端点 × 5 类主体 | PASS | — |
| TC-INT-2115 | IFC-408~412 | 前端 api.js 调用扫描 ↔ 后端路由/方法/权限 | PASS | — |

## 与基线对比（baseline 模式）

- 新增 14 条集成用例全部通过；契约测试 26 条（现有）通过，新增的 5 条 `historicalExpenseApi` 调用被静态扫描并成功 resolve。
- 无既有失败、无新增失败。

## 失败汇总（需路由给开发）

无。执行期间发现并已由开发修复的缺陷：管理员令牌访问 `IsIncomeMember` 端点原返回 401（AC-338-01 要求 403），见 e2e 报告 DEF-001（已修复）。
