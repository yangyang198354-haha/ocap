<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-14T17:50:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告

## 摘要

critical path 口径：替代（后端多步 API 旅程 + Web/小程序页面挂载）
- 执行时间：2026-11-14 17:46（Asia/Shanghai）
- 命令：`python manage.py test tests.e2e --settings=config.test_settings`
- total = pass + fail + skip + blocked + not_testable = 36 + 0 + 1 + 0 + 0 = 37
- 通过率 = 36 / (36 + 0 + 0) = 100%
- critical path 覆盖率 = 3 / 3 Must Have 故事（US-145、US-146、US-148）= 100%
- critical path 通过率 = 100%
- 本层门控：PASSED

## 全量回归

| 套件 | 命令 | 计数 | 相对基线新增失败 |
|---|---|---|---|
| 后端 | `python manage.py test --settings=config.test_settings` | Ran 572 tests，OK（skipped=9） | 0 |
| 前端 | `npm test` | 20 files / 185 tests passed | 0 |
| 小程序 | `npm test` | 12 files / 78 tests passed | 0 |

说明：改动前基线为后端 561 项通过、前端 181 项通过、小程序 75 项通过。本次新增 14 项后端测试与 7 项客户端测试；11 项旧口径断言按需求更新（见 code_review_report），无其他失败。

## 用户旅程

### TC-E2E-501: 清册手机号注册 → 自动认证 → 主页身份与房屋

- 关联：US-145 / AC-145-02；US-146 / AC-146-01；US-148 / AC-148-01
- 环境：Django test runner + SQLite
- 步骤：注册（201）→ GET /me
- 结果：labels=["产权业主"]；units 含 `1栋1单元9层902号`、住宅、`89.50 ㎡`、产权业主。PASS

### TC-E2E-502: 产权业主认证 → 同住人申请 → 审批通过 → 同住人主页

- 关联：US-145 / AC-145-04；US-146 / AC-146-08
- 步骤：产权业主认证（201）→ 同住人申请（201）→ 审批通过（200）→ GET /me
- 结果：labels=["同住人"]；房屋类型“公寓”、面积“未登记”、关系“同住人”。PASS

### TC-E2E-503: 产权业主 + 业委会职务 → 职务优先

- 关联：US-145 / AC-145-07
- 步骤：认证（201）→ 任命副主任 → GET /me
- 结果：labels=["副主任"]；房屋关系仍为产权业主。PASS

## 缺陷

无。

## 人工验证清单

| 编号 | 对应 AC/TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | AC-148-04 | Web 完成清册认证 → 立即打开小程序主页 | 小程序显示“产权业主”，不显示过期“游客” | 微信开发者工具或真机 + 测试后端 | 否（Must Have 故事已由 TC-E2E-501 覆盖） |
| MV-02 | US-146 视觉 | 在 Web 三套主题与小程序分别查看“认证房屋”卡片 | 明细不溢出、空态正常、面积与类型可读 | 浏览器 / 微信开发者工具 | 否 |
