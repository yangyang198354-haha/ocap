<file_header>
  <author_agent>sdlc-test-engineer</author_agent>
  <timestamp>2026-11-07T23:57:31+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>0.3.0</version>
  <input_files><file>testing/test_plan.md</file><file>requirements/user_stories.md</file><file>testing/unit_test_report.md</file><file>testing/integration_test_report.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

> 复跑说明（ocap-GROUP_D-2）：DEF-001~004 修复后复跑，原 3 条失败全部转绿。

## 摘要

critical path 口径：替代（`backend/tests/e2e/` 的多步 API 旅程用例，项目无浏览器 / 小程序 E2E 框架）

- 执行时间：2026-11-07 23:56 ~ 23:57（Asia/Shanghai，复跑）。
- 环境：Windows，Python 3.14.6，Django 6.0.6，DRF 3.17.1，`config.test_settings`，SQLite `:memory:`。
- 命令：`python manage.py test tests.e2e --settings=config.test_settings -v 1`。
- total = pass + fail + skip + blocked + not_testable = 10 = 10 + 0 + 0 + 0 + 0。
- 通过率 = 10/(10+0+0) = 100.00%。
- critical path 覆盖率 = 27 / 69 = 39.13%（有 E2E 用例的 Must Have 故事 / Must Have 故事总数）。
- critical path 通过率 = 10 / 10 = 100.00%。
- 判定模式与阈值：FULL_FLOW threshold，critical_path = 1.00。
- **本层门控：PASSED**（100.00% = 100%，原缺陷失败已全部转绿）。

## 全量回归

```
python manage.py test tests.unit tests.integration tests.e2e --settings=config.test_settings -v 1
Ran 115 tests in 0.980s

OK
```

- 全量计数：total = 115 = 115 pass + 0 fail + 0 skip + 0 blocked + 0 not_testable；通过率 115/115 = 100.00%。
- 相对修复前（106 通过 + 9 失败）：9 条失败全部转绿，无回退、无新增失败。

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

## 缺陷复核

| DEF | 级别 | 原现象 | 复现用例 | 修复结果 |
|---|---|---|---|---|
| DEF-001 | MAJOR | 审批通过的决议公开列表对普通登录用户返回 403 | TC-INT-038、TC-E2E-004 | FIXED（列表 GET 改 `IsMember`） |
| DEF-002 | MAJOR | 已生效收入表与台账报表对普通登录用户返回 403 | TC-INT-061、TC-INT-063、TC-E2E-007 | FIXED（财务读接口改 `IsMember`） |
| DEF-003 | MAJOR | 同一周期二次手动生成台账返回 409 `LEDGER_LOCKED` | TC-INT-064 | FIXED（覆盖原行、版本 +1） |
| DEF-004 | MAJOR | 调查 / 业主代表投票应答仅业委会成员可调用，且 Poll 模型缺字段 | TC-INT-070、TC-INT-071、TC-E2E-009 | FIXED（参与资格校验 + 模型/migration 补齐） |

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-001 | AC-002-*、AC-004-*、AC-008-*（TC-INT-009 仅验证降级） | 在配置真实微信 AppID/Secret 的环境，用微信扫码 / 小程序一键登录 | 首次创建游客账号；已绑定进入既有账号；拒绝授权不建号 | 微信开放平台 / 小程序真机与凭据 | 是 |
| MV-002 | AC-019-*、AC-059-*（xlsx 路径） | 安装 openpyxl 后，用 xlsx 清册与收入表各导入一次 | 与 CSV 一致：行数、金额合计、错误行提示 | 具备 openpyxl 的后端环境 | 否 |
| MV-003 | 前端 / 小程序全部 AC | 在依赖安装完成后执行 `npm test` 并按用户故事走查关键页面 | 页面流程与 API 行为一致 | Node + 已安装依赖的 frontend / miniprogram | 是 |
