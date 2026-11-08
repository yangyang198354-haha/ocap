<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-08T22:59:40+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>0.4.0</version>
  <input_files><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>testing/test_plan.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>DRAFT</status>
</file_header>

> 复跑说明（ocap-GROUP_D-7）：GROUP_C-5 返工后重跑。REWORK_AUTHORIZED: project_workspace/ocap/testing/。

## 摘要

critical path 口径：替代（`backend/tests/e2e/` 的多步 API 旅程用例；项目无浏览器/小程序 E2E 框架。前后端契约由集成层 `test_frontend_contract.py` 与 vitest 路径断言补充，见集成报告）

- 执行时间：2026-11-08 22:55 ~ 22:57（Asia/Shanghai）。
- 环境：Linux，Python 3.12.3，Django 5.2.19，DRF 3.18.3，`config.test_settings`，SQLite `:memory:`，fake 短信/邮件。
- 命令：
  - `(cd backend && python manage.py test tests.e2e --settings=config.test_settings)`
  - `(cd backend && python manage.py test tests.smoke --settings=config.test_settings)`
- 本层用例：E2E 旅程 13（10 既有 + 3 新写）+ 冒烟 6（既有，回归用）+ 不可测 4 = 23。
- total = pass + fail + skip + blocked + not_testable = 23 = 19 + 0 + 0 + 0 + 4。
- 通过率 = pass/(pass+fail+blocked) = 19/(19+0+0) = 100.00%。
- critical path 覆盖率 = 34 / 69 = 49.28%（有 E2E 旅程用例的 Must Have 故事 / Must Have 故事总数；0.3.0 为 27/69，新增 US-012、015、016、051、062、066、072）。
- critical path 通过率 = 13 / 13 = 100.00%（threshold critical_path = 1.00）。
- 判定模式与阈值：FULL_FLOW threshold。
- **本层门控：PASSED**（critical path 通过率 100% ≥ 100%；覆盖率 49.28%，未覆盖的 35 个 Must Have 故事由集成层契约/API 用例覆盖，没有 E2E 旅程，已知缺口）。
- 待人工验证：4 条（MV-004 ~ MV-006 为小程序/微信真机相关，MV-001 为微信真实链路），critical path 中含 manual 项，最终状态至多 DELIVERED_WITH_ISSUES（协议 §K）。

## 全量回归

```
$ (cd backend && python manage.py test --settings=config.test_settings)
Ran 160 tests in 6.391s
FAILED (failures=1)
FAIL: test_web_api_routes_exist_and_support_method (tests.integration.test_frontend_contract.RouteContractTests...)

$ (cd frontend && npx vitest run)      → Test Files 3 passed (3)   Tests 33 passed (33)
$ (cd miniprogram && npx vitest run)   → Test Files 3 passed (3)   Tests 27 passed (27)
```

- 全量计数：total = 220 = 219 pass + 1 fail + 0 skip + 0 blocked + 0 not_testable（后端 160 = 159 + 1；Web 33；小程序 27）。通过率 219/220 = 99.55%。
- 与分层一致：单元 74 + 集成 127 + 本层可执行 19 = 220。
- 基线对比：后端基线 120/120（画像 P4）。既有 120 个用例全部通过（含按 AC-059 更新断言的 2 条）；新写后端 40 个用例中 39 通过、1 失败。**相对基线新增失败 1 条**：`RouteContractTests.test_web_api_routes_exist_and_support_method`（DEF-005，产品缺陷；该用例为新写，基线中不存在）。前端、小程序无基线。

## 用户旅程

### TC-E2E-001: 注册 → 认证户主 → 完善资料
- 关联：US-001 / US-021 / US-023 / US-030；环境：test_settings + fake SMS。
- 步骤：请求 REGISTER 码（202）→ 注册（201）→ `GET /me`（游客）→ 清册认证（201，HEAD）→ `GET /me`（户主）→ PATCH 资料（200）。
- 结果：PASS。

### TC-E2E-002: 同住人申请 → 户主审批 → 移除
- 关联：US-024 / US-029。
- 步骤：申请（201）→ 户主待审列表（1 条）→ 同意（200）→ 同住人 `/me`（含"同住人"）→ 户主移除（204）→ `/me` 不再含"同住人"。
- 结果：PASS。

### TC-E2E-003: 认证失败 → 申诉 → 管理员核准
- 关联：US-026。
- 步骤：认证（422 `PHONE_NOT_IN_REGISTRY`）→ 上传凭证（201）→ 申诉（201）→ 管理员核准（200）→ `/me` 含"户主"。
- 结果：PASS。

### TC-E2E-004: 指定审批决议 → 公开可查
- 关联：US-044 / US-045 / US-047。
- 步骤：主任发起（201）→ 审批人待办 1 条 → 同意（APPROVED）→ 其他业主读详情（200）→ 公开列表（200）。
- 结果：PASS（DEF-001 已修复）。

### TC-E2E-005: 半数表决决议 → 到期判定 → 结果公开
- 关联：US-046 / US-047 / US-065。
- 步骤：主任发起（201）→ 3 委员同意（200）→ 截止时间改过期 → `run_due_jobs` → 状态 APPROVED、`result.agree=3` → 其他业主持有可读详情。
- 结果：PASS。

### TC-E2E-006: 收入导入审批 → 报销审批 → 台账生成
- 关联：US-049 / US-050 / US-058 / US-059 / US-060 / US-061。
- 步骤：CSV 导入（201，300.50）→ 提交审批 → 同意（APPROVED）→ 报销 100.00 创建（201）→ 同意 → 生成台账（201，收入 300.50 / 支出 100.00 / 结余 200.50）。
- 结果：PASS。

### TC-E2E-007: 财务报表对任意登录用户可见
- 关联：US-063。
- 步骤：预置已生效收入表 → 生成台账（201）→ 普通业主读收入表列表与台账报表（200）。
- 结果：PASS（DEF-002 已修复）。

### TC-E2E-008: 业委会投票闭环
- 关联：US-052 / US-053 / US-057。
- 步骤：主任创建投票（201）→ 委员应答（201）→ 截止改过期 → 结果（200，首选项 count=1）。
- 结果：PASS。

### TC-E2E-009: 业主代表 / 产权业主参与投票调查
- 关联：US-054 / US-055 / US-056。
- 步骤：主任创建调查（201）→ 业主代表应答（201）→ 产权业主应答（201）。
- 结果：PASS（DEF-004 已修复）。

### TC-E2E-010: 注册 → 设置密码 → 密码登录 → 注销
- 关联：US-001 / US-009 / US-031。
- 步骤：注册（201）→ 设置密码（204）→ 密码登录（200）→ CANCEL 码（202）→ 注销（204）→ 旧 token `/me`（401）。
- 结果：PASS。

### TC-E2E-011: 微信账号绑定已注册手机号 → 合并
- 关联：US-012 / US-015 / US-016 / US-066 / US-072（AC-012-01、AC-072-01）；环境：test_settings + fake SMS。
- 步骤：A 手机号注册并认证户主（201）→ W 仅微信、同住人 → 主任创建调查 → A、W 都作答（201）→ W 取 BIND_PHONE 码并绑定 A 的手机号 → `merged=true` 并返回新令牌 → `/me` 身份为 {A 户主, W 同住人}、标签含"户主" → 旧令牌 `/me` 401 → 详情 `my_response`=["同意"]（保留 A 的）→ 手机号验证码登录得同一 user id → 管理员审计含 ACCOUNTS_MERGED、MERGE_ANSWER_DISCARDED。
- 结果：PASS。

### TC-E2E-012: 备用金预借 → 报销 → 核销 → 公开报表
- 关联：US-049 / US-050 / US-051 / US-061 / US-063（AC-051-03）。
- 步骤：预借 1000 并审批通过 → 报销 1200 并审批通过 → 核销（差额 +200）→ 生成报表 → 普通业主读报表，支出合计 1200（非 2200/2400）。
- 结果：PASS。

### TC-E2E-013: 逐条录入收入 → 审批生效 → 报表 → 作废重算
- 关联：US-058 / US-060 / US-061 / US-062。
- 步骤：逐条录入（201，DRAFT）→ 提交审批 → 同意生效 → 报表含该收入 → 作废 → 手动重新生成，收入归零。
- 结果：PASS。

### 冒烟 tests.smoke（既有 6 个）
- 命令输出：`Ran 6 tests in 0.241s  OK`。结果：PASS（6）。

### TC-E2E-NT-001 ~ 004: 不可测项
- TC-E2E-NT-001：微信扫码 / 小程序一键登录真实链路（AC-002/004/008）→ NOT_TESTABLE，MV-001。
- TC-E2E-NT-002：uni-app 运行时页面渲染与 `uni.chooseImage/uploadFile` 真机行为 → NOT_TESTABLE，MV-004。
- TC-E2E-NT-003：微信开发者工具/真机登录与手机号授权 → NOT_TESTABLE，MV-005。
- TC-E2E-NT-004：小程序业务流程真机走查（登录 → 报销 / 投票 → 绑定手机号）→ NOT_TESTABLE，MV-006。

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| DEF-005 | MINOR | Web `api.js` 的 `admin.registryUnit(id)` 发 `GET /admin/registry/units/${id}`，后端 `AdminUnitDetailView` 无 `get`，返回 405。`git grep` 显示 `registryUnit(` 在 `frontend/src` 内无页面调用（`AdminRegistry.vue` 未使用），属死代码/契约不一致，尚未造成运行时故障。影响 US-018（保存业主清册，管理端）；不在 critical path 的 E2E 旅程中。修复二选一：删除该前端函数，或后端补 GET 详情（需与 module_design 对齐）。 | TC-INT-082 | `frontend/src/shared/api.js:132`；`backend/apps/registry/views.py:62` |

## 缺陷复核（历史）

DEF-001 ~ 004（0.3.0 已 FIXED）本次回归未复现：对应 TC-INT-038、061、063、064、070 与 TC-E2E-004、007、009 均通过。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-001 | AC-002/004/008（TC-E2E-NT-001；TC-INT-009 仅验证降级） | 在配置真实微信 AppID/Secret 的环境，用微信扫码 / 小程序一键登录 | 首次创建游客账号；已绑定手机号的微信登录进入原账号；昵称取自微信 | 真实微信开放平台与小程序账号 | 是 |
| MV-002 | AC-019、AC-059（xlsx 路径） | 安装 openpyxl 后，用 xlsx 清册与收入表各导入一次 | 与 CSV 一致：行数、金额合计、错误/重复行提示 | 具备 openpyxl 的后端环境 | 否 |
| MV-003 | Web 全部 AC（视觉与浏览器行为） | 浏览器打开 Web 端，按 US 走查登录、报销/核销、投票、手机号绑定/换绑、管理端撤销认证 | 页面与 API 行为一致，无控制台报错 | Chrome + 测试环境后端 | 是 |
| MV-004 | TC-E2E-NT-002 | 微信开发者工具/HBuilderX 构建小程序，进入"报销/备用金"，选发票上传并提交 | `uni.chooseImage`+`uploadFile` 成功，POST /claims/reimbursements 带 invoice_ids，列表出现新单 | HBuilderX + 微信开发者工具 + 测试环境后端 | 是 |
| MV-005 | TC-E2E-NT-003 | 真机登录，验证码登录新账号（is_new）→ 进入头像昵称页；已有账号密码登录 | 新账号进资料页；老账号进首页；手机号授权/绑定可合并 | 真机微信 | 是 |
| MV-006 | TC-E2E-NT-004 | 真机走查：登录 → 投票作答与查看结果 → 绑定手机号（合并）→ 申诉带证明 | 各页面跳转（含 tabBar switchTab）正确；合并后换用新令牌 | 真机微信 + 测试环境后端 | 是 |
