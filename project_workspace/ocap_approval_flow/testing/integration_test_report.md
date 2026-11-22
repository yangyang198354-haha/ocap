<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T19:52:51+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告 — ocap_approval_flow

## 摘要

- 执行时间：2026-11-22 19:46–19:52
- 环境：Django test runner + `config.test_settings`（SQLite 内存库）；vitest
- 命令：`backend/python manage.py test tests.integration.test_approval_flow_steps --settings=config.test_settings`；`frontend/npm test`；`miniprogram/npm test`
- 新写集成用例：total = pass + fail + skip + blocked + not_testable = 23 = 23 + 0 + 0 + 0 + 0
- 通过率 = 23 / (23 + 0 + 0) = 100%
- 判定模式：INCREMENTAL baseline；**本层门控：PASSED**

## 执行输出

```
backend: Ran 19 tests in 0.628s / OK
frontend: Test Files 52 passed (52) / Tests 581 passed (581)
miniprogram: Test Files 21 passed (21) / Tests 151 passed (151)
```

## 分项结果（按集成边界）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-INT-1310 | AC-316-01~318-02 | MOD-185 ↔ 模型：流程 steps 创建与三类校验（4 条） | PASS | — |
| TC-INT-1311 | AC-322-01、AC-326-01 | MOD-184 ↔ MOD-187：串行推进、待办归属、配置快照（3 条） | PASS | — |
| TC-INT-1312 | AC-320-01~320-03 | MOD-184：或签部分拒绝/全部拒绝/通过（3 条） | PASS | — |
| TC-INT-1313 | AC-321-01~321-03 | MOD-184：会签部分通过/全员通过/任一拒绝（3 条） | PASS | — |
| TC-INT-1314 | AC-328-01、AC-329-01/02、AC-332-01 | MOD-186：时间线内容、可见性、备注长度（3 条） | PASS | — |
| TC-INT-1315 | AC-327-01/02 | MOD-184 ↔ 迁移：旧流程单步兼容（1 条） | PASS | — |
| TC-INT-1316 | 契约 | MOD-189/190 ↔ MOD-186/187：客户端路径解析到后端路由（1 条） | PASS | — |
| TC-INT-1304 | AC-328-01/02/03 | Web ApprovalTimeline 渲染 | PASS（发现 DEF-001，已修复） | 产品缺陷（已修复） |
| TC-INT-1305 | AC-322-01、AC-332-02 | Web Tasks 步骤展示与带备注提交 | PASS | — |
| TC-INT-1310（小程序） | AC-331-01 | 小程序 api.js 契约 | PASS | — |
| TC-INT-1311（小程序） | AC-331-02 | 小程序页面注册与文案引用 | PASS | — |

DEF-001：`ApprovalTimeline.vue` 模板仍引用已重命名的 `*_TEXT` 常量，导致渲染期 `textOf(undefined)`。TC-INT-1304 首跑失败，修复为 `*_LABELS` 后通过；该修复已记入 code_review_report“缺陷修复”。

## 与基线对比（baseline 模式）

- 后端 baseline 1167 tests / 1 预存在失败（`test_tc_int_964_register_and_bind_response_field_registry_match`）。
- 本次全量 1186 tests（+19 新写），预存在失败仍为同 1 条，**新增失败 0**。
- 前端、小程序新增失败 0。

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| TC-INT-1304（首跑） | `Cannot read properties of undefined (reading 'ANY')` | `ApprovalTimeline.vue` 模板常量 | DEF-001（FIXED） |
