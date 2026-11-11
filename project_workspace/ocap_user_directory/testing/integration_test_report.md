<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T22:46:57.2524963+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>development/implementation_plan.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 集成测试报告

## 摘要

- 执行时间：2026-11-11 22:45（Asia/Shanghai）；环境：Django test runner + SQLite 内存库。
- 命令：`python manage.py test tests.integration --settings=config.test_settings`
- 计数：total 352 = pass 347 + fail 0 + skip 5 + blocked 0 + not_testable 0；通过率 = 347 / (347 + 0 + 0) = 100%。
- 新增用例：TC-INT-389 ~ 397 共 9 个，全部通过。
- 基线：本次改动前该层 343 个用例 OK（5 skipped）；新增失败 0。
- 判定模式：baseline；**本层门控：PASSED**。

## 执行输出

```
> python manage.py test tests.integration --settings=config.test_settings
Ran 352 tests in 4.864s
OK (skipped=5)

> python manage.py test tests.integration.test_admin_user_directory --settings=config.test_settings -v 2
TC-INT-389 ... ok
TC-INT-390 ... ok
TC-INT-391 ... ok
TC-INT-392 ... ok
TC-INT-393 ... ok
TC-INT-394 ... ok
TC-INT-395 ... ok
TC-INT-396 ... ok
TC-INT-397 ... ok
Ran 9 tests in 0.120s
OK
```

## 分项结果

集成边界：MOD-062（目录聚合）↔ 既有 `residency.Membership` / `committee.Seat` / `registry.RegistryOwner/Phone/Unit` / `accounts.User`；MOD-063 通过契约由前端单元用例覆盖。

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-389 | AC-132-01 ~ 04、AC-136-04 | 最高身份优先级与过期席位回退 | PASS | — | — |
| TC-INT-390 | AC-132-05、AC-136-02 | 认证套数去重与撤销后减少 | PASS | — | — |
| TC-INT-391 | AC-133-01 ~ 03 | 多套实名去重保序 | PASS | — | — |
| TC-INT-392 | AC-133-04 ~ 05、AC-136-01 | 无手机号/未匹配/非产权/撤销后实名空 | PASS | — | — |
| TC-INT-393 | AC-134-01、AC-134-03 | 登录时间 ISO8601 与从未登录 null | PASS | — | — |
| TC-INT-394 | AC-135-01 ~ 04 | 实名搜索与原有搜索并存 | PASS | — | — |
| TC-INT-395 | AC-135-02、GR-B-001-F01 | 实名搜索同记录匹配负向用例 | PASS | — | — |
| TC-INT-396 | AC-132-06 | 未登录 401、普通用户 403 | PASS | — | — |
| TC-INT-397 | AC-135-05、GR-B-001-F02 | 每页查询数不随行数增长 | PASS | — | — |

## 与基线对比（baseline 模式）

- 失败清单：无。
- 既有 343 个集成用例：0 失败，与基线一致。
- 新增 9 个用例：全部通过。
- 新增失败：0。

## 失败汇总（需路由给开发）

无。
