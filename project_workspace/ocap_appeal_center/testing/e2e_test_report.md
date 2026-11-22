<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T11:01:52+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>1.0.0</version>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告 — 申诉与同住人申请记录中心

critical path 口径：替代（多步 HTTP API 旅程；当前环境无浏览器 E2E，界面交互由 frontend vitest 覆盖）

## 摘要

- total = pass + fail + skip + blocked + not_testable = 75 + 0 + 0 + 0 + 0 = 75
- critical path 覆盖率 = 有已执行用例的 Must Have 故事 / Must Have 故事总数 = 8 / 8 = 100%
- critical path 通过率 = 8 / 8 = 100%（DEF-AC-01 修复后两条旅程恢复通过）
- 本层门控：PASSED（本轮为 GROUP_D-2 复跑；E2E 层 Ran 75 tests / OK）
- 环境：Django test runner + `config.test_settings`，真实 DRF 路由、中间件、SQLite。

## 全量回归

命令：
- `cd backend && python manage.py test --settings=config.test_settings`
- `npm --prefix frontend test`
- `npm --prefix frontend run build`

计数：
- 后端：Ran 1167 tests / OK (skipped=2)；总通过 1165。
  基线 1159 通过 / 2 skipped；新增 8 条（6 集成 + 2 E2E）全部通过。
- 前端：Test Files 50 passed，Tests 568 passed（基线 562 + 新增 6）。
- 构建：✓ built in 8.43s。
- 相对基线新增失败：0。

| 新增失败 | 层 | 原因 |
|---|---|---|
| 无 | — | DEF-AC-01 修复后，TC-INT-1502/1503/1505 与 TC-E2E-1615/1616 全部恢复通过 |

## 用户旅程

### TC-E2E-1615: 申诉提交 → 撤回 → 重新提交 → 通过并备注
- 关联：US-291、292、293、294（AC-291-01、292-01、293-01、294-01/02/03）；环境：Django test client + SQLite
- 结果：**PASS**
- 实际：撤回 200 且状态为已撤回 → 重提 201 且 previous_appeal_id 指向原记录 → 管理员通过并备注 → 我的申诉返回 APPROVED + “资料齐全”。

### TC-E2E-1616: 同住申请 → 撤回 → 重提 → 驳回 → 再申请 → 通过 → 身份页实名
- 关联：US-295、296、297、298（AC-295-03、296-01/02/03、297-03、298-01/02）；环境：Django test client + SQLite
- 结果：**PASS**
- 实际：驳回原因/备注可查 → 通过后业主同住人列表显示实名 → 本人 real_names 含实名。

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 | 状态 |
|---|---|---|---|---|---|
| DEF-AC-01 | CRITICAL | 撤回申诉/同住申请时接口抛 500（`未登记的审计动作`） | TC-INT-1502、1503、1505；TC-E2E-1615、1616 | `backend/apps/core/audit.py` 的 `AUDIT_ACTIONS` | FIXED（GROUP_C-2，补齐两个审计动作；本轮复跑通过） |

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MAN-AC-01 | AC-291-02（真实浏览器文件选择状态） | 在“认证申诉”Tab 选择房屋、填姓名、选 2 份证明，切到“我的申诉”再切回 | 已选房屋、姓名、2 份文件仍在 | 浏览器 + 测试环境 | 否（组件测试已覆盖节点不重建） |
