<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-27T10:08:03.0867713+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>testing/unit_test_report.md</file>
    <file>requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告

## 摘要

- 执行时间：2026-11-27 09:56:25～09:57:51（Asia/Shanghai）。
- 环境：Django/DRF 真实 ORM 与认证头、SQLite 隔离测试库；Vitest/jsdom 挂载真实 Vue 页面、Pinia、内存路由与 `api.js`，仅 HTTP 为替身。
- 命令：
  - `backend/`：`$env:DJANGO_SECRET_KEY='test-only'; python manage.py test tests.integration --settings=config.test_settings`
  - `frontend/`：`npx vitest run tests/approval_history_ui.spec.js tests/approval_steps_ui.spec.js tests/approval_finality.spec.js tests/layout_contract.spec.js --passWithNoTests`
- `total = pass + fail + skip + blocked + not_testable = 944 + 0 + 1 + 0 + 0 = 945`。
- 通过率 = `pass/(pass+fail+blocked) = 944/944 = 100%`；INCREMENTAL baseline 模式，零新增失败且 11 条新写集成用例全部通过。
- **本层门控：PASSED**。

## 执行输出

后端完整集成层：

```text
Ran 922 tests in 66.260s
OK (skipped=1)
```

前端相关集成与契约：

```text
Test Files 4 passed (4)
Tests 23 passed (23)
```

既有 Element Plus `label act as value` 弃用警告仍出现，不影响退出码或测试结果。

## 分项结果

| TC | AC | 集成边界/描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-2301 | AC-370-01 | ApprovalAction ↔ 已处理 API：通过/拒绝后出现且每实例一次 | PASS | — | — |
| TC-INT-2302 | AC-370-02 | 两步实例：本人完成第 1 步后仍可见，整单 PENDING、当前第 2 步 | PASS | — | — |
| TC-INT-2303 | AC-370-03、04 | 仅被指派或仅他人操作不进入本人历史；待办不受历史查询影响 | PASS | — | — |
| TC-INT-2304 | AC-371-01、04 | 25 条历史含本人双动作：scope 过滤、去重、20+5 分页 | PASS | — | — |
| TC-INT-2305 | AC-371-02、03 | 既有实例时间线复用；无关委员直接访问仍 403 | PASS | — | — |
| TC-INT-2306 | AC-372-01、AC-373-01、02 | 通过记录字段完整；申请人 mine 保持本人可见、他人隔离 | PASS | — | — |
| TC-INT-2307 | AC-372-02、03 | 五种状态仅 APPROVED；他房与失效产权均排除 | PASS | — | — |
| TC-INT-2308 | AC-370-02、AC-371-02 | `Tasks.vue` ↔ API：在途摘要、当前步骤、完整时间线、只读 | PASS | — | — |
| TC-INT-2309 | AC-370-04、AC-371-01、04 | 空态/待办稳定、scope 重置、第二页 5 条 | PASS | — | — |
| TC-INT-2310 | AC-372-01、02 | `UnitsReview.vue` ↔ Store/API：通过后双列表刷新、历史只读与空态 | PASS | — | — |
| TC-INT-2311 | AC-373-01 | `UnitsApplicationRecords.vue`：本人通过状态、处理时间和备注不回归 | PASS | — | — |
| TC-INT-921～925 等既有契约 | AC-371-01、AC-372-01 | 页面引用、导出白名单、方法+路径 ↔ Django 路由 | PASS | — | — |
| 既有后端集成套件 | 回归 | 共 922 条，921 通过、1 条既有跳过 | PASS/SKIP | — | — |

## 与基线对比

失败 0；新增失败 0。开发门控的后端相关 101 条与前端契约 6 条均包含或对应于本轮更大范围执行；新增的后端历史 API、前端页面和路由契约均已实际执行。

## 失败汇总（需路由给开发）

无。
