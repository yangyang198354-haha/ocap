<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-14T09:45:35+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>phase_status.md</file><file>testing/test_plan.md</file><file>testing/unit_test_report.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告：产品评审修正（0.3.0）

## 摘要

> 0.3.0（缺陷回流 2/2 后的最终重测）。上一层（单元）门控 PASSED，本层按 baseline 模式执行。0.2.0 因单元层 FAILED 未执行本层；0.1.0 的 3 条失败（TC-INT-512/513/514，DEF-017/018/019）已修复并全部转绿。

- 执行时间：2026-11-14T09:40:41 ~ 09:41（+08:00，最后一次执行）；环境：`PY=/tmp/claude-0/-root-myproject-ocap/0130fd24-0fdc-48ac-9199-c3a574e51a0e/scratchpad/venv/bin/python`（Python 3.12.3、Django 5.2.19），SQLite 内存库（`config.test_settings`）；迁移用例（TC-INT-497）另用系统临时目录的 SQLite 文件库。
- 命令：`(cd backend && $PY manage.py test tests.integration --settings=config.test_settings)`
- total = pass + fail + skip + blocked + not_testable = 497 = 497 + 0 + 0 + 0 + 0（495 既有/0.2.0 + 2 新写 TC-INT-544、545）
- 通过率 = pass / (pass + fail + blocked) = 497 / 497 = 1.0000
- 判定模式：baseline（零新增失败，新写用例全部通过）。基线：PM GROUP_C-005 后复跑后端全量 710 OK（integration 495）；本次 497，既有用例新增失败 0，新写 2 条全部通过。基线中的既有失败 TC-INT-311（画像 P4，期望 4 行实际 6 行）已按 REQ-FUNC-166 更新断言并通过，不再失败。
- **本层门控：PASSED**。
- 字段级契约（PM 指令 1）：既有契约用例（TC-INT-486 ~ 496、契约-1/2/3/4、test_frontend_contract.py）全部通过；新增 TC-INT-544（can_void）、TC-INT-545（adminText 枚举与管理端财务/审计页读取字段）。前端 Web/小程序 api.js 全部调用均能 resolve 到后端路由且视图支持该 HTTP 方法（无法对应数 = 0）。

## 执行输出

```
$ (cd backend && $PY manage.py test tests.integration --settings=config.test_settings)
Ran 497 tests in 37.005s
OK

$ (cd backend && $PY manage.py test tests.integration.test_product_review_rework2 --settings=config.test_settings)
Ran 2 tests in 0.325s
OK
```

## 分项结果

按集成边界；0.1.0/0.2.0 已有的 495 条（含 TC-INT-424 ~ 543 与既有集成用例）逐条复跑，全部 PASS，描述未改，明细见 test_plan"AC 映射"。本版新增：

### Web 前端页面 ↔ 后端接口（MOD-前端 Income ↔ MOD-income；AdminFinance/AdminAudit ↔ MOD-claims/core）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-544 | AC-178-02、AC-060-10（US-060、US-178） | 字段级契约（回流 1 新增 `can_void`）：Income.vue 的作废按钮依赖 `item.status === 'EFFECTIVE' && item.can_void`；api.js 中 GET `/admin/income/sheets` 与 POST `/admin/income/sheets/${id}/void` 均 resolve 到支持对应方法的后端视图；后端真实列表项每一行都含布尔 `can_void`（已生效且为原审批人=true，录入人/待审批=false），页面读取的全部 `item.*` 字段都在后端列表项中；小程序不使用 `can_void`（C-44） | PASS | — | — |
| TC-INT-545 | AC-167-03、AC-178-02（US-167、US-178，REQ-FUNC-158） | 字段级契约 + 枚举一致（GR-C-003）：AdminFinance 读取 `row.type/row.status`、AdminAudit 读取 `row.occurred_at/actor_type/result`，后端真实响应（`/admin/claims`、`/admin/audit-logs`）均含这些字段；响应里出现的 type（报销）、status、actor_type（成员/管理员/系统 三种）、result（成功/失败/拒绝 三种）全部落在 `shared/adminText.js` 映射表的键内，且审计响应的主体、结果取值集合恰等于映射表键集合；两个调用路径可解析 | PASS | — | — |

**用例有效性（变异检验，scratchpad 副本，非仓库）**：把 `apps/income/views.py` 列表项的 `can_void` 去掉后，TC-INT-544 失败（`'can_void' not found in {...}`），还原后通过。

## 与基线对比（baseline 模式）

| 项 | 基线（GROUP_C-005 后 PM 复跑） | 本次 | 差异 |
|---|---|---|---|
| `tests.integration` | 495（全通过） | 497（全通过） | +2 新写，全通过；既有新增失败 0 |
| 既有失败 TC-INT-311 | 画像 P4 登记的既有失败 | 通过 | 已修复（REQ-FUNC-166 口径，GROUP_D-001 更新断言） |

失败清单：无。

## 失败汇总（需路由给开发）

无。

## 说明与限制

- 契约用例只读前端源码文本，后端一侧用真实 HTTP（Django test client + 真实认证头）；前端页面渲染行为在单元层（TC-UNIT-5xx）验证，二者合起来覆盖"前端读取的字段 ↔ 后端实际返回"。
- 审计响应里的 MEMBER/SYSTEM 主体与 DENIED 结果，TC-INT-545 用审计服务直接补写（`AuditService.record`），管理员的 SUCCESS/FAILURE 行来自真实接口操作；映射的键域已与模型 choices 在 TC-UNIT-598 中比对。
- 迁移启用时 content 应用漂移（OBS-3）仍同 0.1.0，未变化。
