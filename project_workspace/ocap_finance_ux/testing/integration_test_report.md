<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-23T23:30:00.0000000+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/testing/test_plan.md</file>
    <file>backend/tests/integration/test_finance_accounts_api.py</file>
    <file>frontend/tests/finance_accounts_ui.spec.js</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告 — ocap_finance_ux

## 摘要

- 执行时间：2026-11-23 23:28；环境：同上，真实 DRF 认证 + ORM + 路由，无外部服务。
- 后端命令：`python manage.py test tests.integration.test_finance_accounts_api tests.integration.test_frontend_contract --settings=config.test_settings`
- 前端命令：`npx vitest run tests/finance_accounts_ui.spec.js`
- 计数（后端）：total = pass + fail + skip + blocked + not_testable = 36 = 36 + 0 + 0 + 0 + 0；通过率 100.0%。
- 计数（前端）：total = 5 = 5 + 0 + 0 + 0 + 0；通过率 100.0%。
- 判定模式：baseline（零新增失败）；**本层门控：PASSED**。

## 执行输出

```
$ python manage.py test tests.integration.test_finance_accounts_api tests.integration.test_frontend_contract --settings=config.test_settings
Ran 36 tests in 1.597s
OK

$ npx vitest run tests/finance_accounts_ui.spec.js
Test Files  1 passed (1)
     Tests  5 passed (5)
```

## 分项结果（后端新增 10 例）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-1407 | AC-405-04、AC-409-01/02 | 账户汇总权限与结构 | PASS |
| TC-INT-1408 | AC-405-04、AC-409-04 | ENABLED 过滤 + recent=0 | PASS |
| TC-INT-1409 | AC-404-01/02/04/05 | 管理端创建/唯一/校验/权限 + 审计 | PASS |
| TC-INT-1410 | AC-404-02/03、AC-405-01 | 改名/默认转移/停用不改流水 | PASS |
| TC-INT-1411 | AC-401-01/02、AC-403-01/06 | 报表列表过滤与期初期末字段 | PASS |
| TC-INT-1412 | AC-402-05、AC-403-03 | 详情账户视角 + 404 | PASS |
| TC-INT-1413 | AC-403-06 | legacy 详情 null | PASS |
| TC-INT-1414 | AC-407-01/02 | 收入表指定账户生效 | PASS |
| TC-INT-1415 | AC-407-04 | 停用账户被拒 | PASS |
| TC-INT-1416 | AC-407-03 | 备用金指定账户生效 | PASS |

前端新增 5 例（TC-WEB-1401~1405）全部 PASS；现有前后端契约测试（`test_frontend_contract`，26 例）全部 PASS，确认 `accountApi` 四个调用均可解析到后端路由且方法/权限匹配。

## 集成边界覆盖

- MOD-195 ↔ 前端 MOD-201/198/199/200：契约测试解析 api.js 全部调用。
- MOD-192/194 ↔ MOD-195：服务聚合/链式结果经 API 断言。
- MOD-192 ↔ MOD-193：收入/备用金服务入账账户归属经审批链验证。

## 与基线对比

基线 0 失败；本层 0 新增失败。

## 失败汇总

无。注：测试设置不执行迁移（`Apply all migrations: (none)`），迁移回填类 AC 见 e2e 报告人工清单 M-01。
