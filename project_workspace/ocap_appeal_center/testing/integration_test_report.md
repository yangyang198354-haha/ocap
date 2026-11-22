<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T11:01:52+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>1.0.0</version>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告 — 申诉与同住人申请记录中心

## 摘要

- 执行时间：2026-11-22 10:59–11:00（Asia/Shanghai；本轮为 DEF-AC-01 修复后的 GROUP_D-2 复跑）
- 环境：Django test runner + `config.test_settings`（SQLite 内存库；真实 DRF 路由、中间件、模型与审计）。
- 命令：`cd backend && python manage.py test tests.integration --settings=config.test_settings`
- total = pass + fail + skip + blocked + not_testable = 849 + 0 + 1 + 0 + 0 = 850
- 通过率 = 849 / (849 + 0 + 0) = 100%
- 判定模式：baseline（基线集成层零失败）→ 新增 6 条全部通过，既有 844 条零新增失败。**本层门控：PASSED**

## 执行输出

```
Ran 850 tests in 37.412s
OK (skipped=1)
```

DEF-AC-01 修复后，TC-INT-1502/1503/1505 由 ERROR 恢复为 PASS；审计动作 `APPEAL_WITHDRAWN`、`RESIDENT_APPLICATION_WITHDRAWN` 已登记。

## 分项结果

| TC | AC | 描述 | 结果 | 实际输出 | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-1502 | AC-294-01/02、C-359/C-360 | 本人撤回、非本人 403、非待审 409、释放待审约束 | PASS | — | — |
| TC-INT-1503 | AC-294-03、D-02 | 重新提交关联原记录、非法来源 400 | PASS | — | — |
| TC-INT-1504 | AC-293-01/02/04 | 通过/驳回备注与 501 字拒绝 | PASS | — | — |
| TC-INT-1505 | AC-295-03、AC-296-02/03、AC-297-01/03 | 实名保存、撤回、重提关联 | PASS | — | — |
| TC-INT-1506 | AC-296-01、AC-298-01/02/03、C-361 | 审批原因/备注、身份页实名与缺失占位 | PASS | — | — |
| TC-INT-1507 | AC-292-03、REQ-NFUNC-060 | 两类列表最近 100 条截断 | PASS | — | — |
| 既有 844 条 | — | 全量回归 | PASS（1 skipped） | — | — |

## 与基线对比（baseline 模式）

| 失败 | 归属 | 依据 |
|---|---|---|
| 无 | — | 新增 6 条全部通过；既有 844 条无新增失败 |

## 失败汇总（需路由给开发）

无。
