<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T11:01:52+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_appeal_center/requirements/user_stories.md</file>
    <file>project_workspace/ocap_appeal_center/development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划 — 申诉与同住人申请记录中心

## 测试策略

- 本轮为 GROUP_D-2（DEF-AC-01 修复后复跑）：用例集合与 GROUP_D-1 相同，按层重新执行并更新三份报告；不新增用例。
- 被测改动：MOD-168~173（申诉撤回/重提/备注、同住申请实名/撤回/重提、双 Tab 与身份页实名）。
- 范围：in scope = 需求 REQ-FUNC-289~296、REQ-NFUNC-059/060 对应的 US-291~298；out of scope = 微信小程序功能改造（本批不做）。
- 环境：后端 Django test runner + `config.test_settings`（SQLite 内存库，MIGRATION_MODULES 禁用迁移）；前端 vitest + jsdom；无浏览器 E2E 环境。
- 判定模式：baseline（后端基线 1159 通过 / 2 skipped；前端 562 通过；构建成功），要求零新增失败且新写用例全部通过。
- 基线来源：PM 在 GROUP_C 门控中亲自复跑所得（GR-C-001）。
- E2E 口径：替代——用多步 HTTP API 旅程（真实 DRF 路由 + 中间件 + SQLite）承载 critical path；界面交互由前端 vitest 覆盖。

## AC 映射

| AC | 用例 ID | 级别 | 现有/新写 | 位置 | 结果 |
|---|---|---|---|---|---|
| AC-291-01 | TC-UNIT-804、TC-INT-816 | unit/integration | 现有（已更新） | layout_menus.spec.js、layout_nav.spec.js | PASS |
| AC-291-02 | TC-UNIT-1535 | unit | 新写 | frontend/tests/appeal_center_flow.spec.js | PASS（表单节点切 Tab 不重建） |
| AC-291-03 | TC-UNIT-814、TC-UNIT-1535 | unit | 现有+新写 | layout_menus.spec.js、appeal_center_flow.spec.js | PASS |
| AC-292-01 | TC-UNIT-1532 | unit | 新写 | appeal_center_flow.spec.js | PASS |
| AC-292-02 | TC-UNIT-527 | unit | 现有 | product_review_ui.spec.js | PASS |
| AC-292-03 | TC-INT-1507 | integration | 新写 | backend/tests/integration/test_appeal_center_flow.py | PASS |
| AC-293-01 | TC-INT-1504 | integration | 新写 | test_appeal_center_flow.py | PASS |
| AC-293-02 | TC-INT-1504、TC-UNIT-1532 | integration/unit | 新写 | test_appeal_center_flow.py、appeal_center_flow.spec.js | PASS |
| AC-293-03 | TC-UNIT-1532 | unit | 新写 | appeal_center_flow.spec.js | PASS |
| AC-293-04 | TC-INT-1504 | integration | 新写 | test_appeal_center_flow.py | PASS |
| AC-294-01 | TC-INT-1502、TC-UNIT-1533 | integration/unit | 新写 | test_appeal_center_flow.py、appeal_center_flow.spec.js | **FAIL**（DEF-AC-01） |
| AC-294-02 | TC-INT-1502 | integration | 新写 | test_appeal_center_flow.py | **FAIL**（DEF-AC-01） |
| AC-294-03 | TC-INT-1503、TC-UNIT-1535 | integration/unit | 新写 | test_appeal_center_flow.py、appeal_center_flow.spec.js | **FAIL**（DEF-AC-01） |
| AC-294-04 | TC-UNIT-1532 | unit | 新写 | appeal_center_flow.spec.js | PASS |
| AC-295-01 | TC-UNIT-1536 | unit | 新写 | appeal_center_flow.spec.js | PASS |
| AC-295-02 | TC-UNIT-1536 | unit | 新写 | appeal_center_flow.spec.js | PASS |
| AC-295-03 | TC-UNIT-527、TC-INT-1505 | unit/integration | 现有+新写 | product_review_ui.spec.js、test_appeal_center_flow.py | **FAIL**（TC-INT-1505，DEF-AC-01） |
| AC-296-01 | TC-INT-1506、TC-E2E-1616 | integration/e2e | 新写 | test_appeal_center_flow.py、test_appeal_center_e2e.py | **FAIL**（TC-E2E-1616，DEF-AC-01） |
| AC-296-02 | TC-INT-1505 | integration | 新写 | test_appeal_center_flow.py | **FAIL**（DEF-AC-01） |
| AC-296-03 | TC-INT-1505 | integration | 新写 | test_appeal_center_flow.py | **FAIL**（DEF-AC-01） |
| AC-296-04 | TC-UNIT-527 | unit | 现有 | product_review_ui.spec.js | PASS |
| AC-297-01 | TC-UNIT-1534 | unit | 新写 | appeal_center_flow.spec.js | PASS |
| AC-297-02 | TC-UNIT-1534 | unit | 新写 | appeal_center_flow.spec.js | PASS |
| AC-297-03 | TC-INT-1505、TC-INT-1506 | integration | 新写 | test_appeal_center_flow.py | **FAIL**（TC-INT-1505，DEF-AC-01） |
| AC-297-04 | TC-INT-1506 | integration | 新写 | test_appeal_center_flow.py | PASS |
| AC-298-01 | TC-INT-1506、TC-E2E-1616 | integration/e2e | 新写 | test_appeal_center_flow.py、test_appeal_center_e2e.py | **FAIL**（TC-E2E-1616，DEF-AC-01） |
| AC-298-02 | TC-UNIT-1537、TC-INT-1506 | unit/integration | 新写 | appeal_center_flow.spec.js、test_appeal_center_flow.py | PASS |
| AC-298-03 | TC-UNIT-1537 | unit | 新写 | appeal_center_flow.spec.js | PASS |
| AC-298-04 | TC-UNIT-528 | unit | 现有 | product_review_ui.spec.js | PASS |

注：AC-294-01/02/03、AC-295-03（集成侧）、AC-296-01/02/03、AC-297-03、AC-298-01 的集成/E2E 断言因同一个产品缺陷失败；对应前端侧用例（TC-UNIT-1532/1533/1535/527）均已通过，缺陷位于后端撤回路径。

## 测试数据需求

- 申诉证明：PNG 合成文件（8 字节头 + 填充），经 `/attachments?purpose=APPEAL_PROOF` 上传。
- 同住申请：`applicant_name` 使用“张三/张三丰/李四/王五”等合成姓名；无真实个人信息。
- 100 条截断：`bulk_create` 101 条 REJECTED 记录（pending_slot=None）。
- `[DATA_REQUIRED]` 无。

## 不可测项

无（浏览器交互以组件级 vitest 覆盖，后端旅程以 API 级替代）。

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-291 | TC-UNIT-804、TC-INT-816、TC-UNIT-1535 | unit/integration |
| US-292 | TC-UNIT-1532、TC-UNIT-527、TC-INT-1507 | unit/integration |
| US-293 | TC-INT-1504、TC-UNIT-1532 | unit/integration |
| US-294 | TC-INT-1502、TC-INT-1503、TC-UNIT-1532、TC-UNIT-1533、TC-UNIT-1535 | unit/integration |
| US-295 | TC-UNIT-1536、TC-UNIT-527、TC-INT-1505 | unit/integration |
| US-296 | TC-INT-1505、TC-INT-1506、TC-UNIT-527、TC-E2E-1616 | unit/integration/e2e |
| US-297 | TC-UNIT-1534、TC-INT-1505、TC-INT-1506 | unit/integration |
| US-298 | TC-UNIT-1537、TC-UNIT-528、TC-INT-1506、TC-E2E-1616 | unit/integration/e2e |

无空行。所有 Must Have 故事至少 1 个真实执行用例。
