<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-19T00:35:00+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/testing/test_plan.md</file>
    <file>backend/tests/e2e/test_profile_ux_journeys.py</file>
    <file>frontend/tests/profile_ux.spec.js</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告 — ocap_profile_ux

## 摘要

critical path 口径：替代（多步 API 旅程；项目无浏览器 E2E 框架，取最高层的跨模块 API 旅程）

- 执行时间：2026-11-19 00:22（本地）
- 新写旅程：1 条（TC-E2E-1501），PASS
- `total = pass + fail + skip + blocked + not_testable = 1 + 0 + 0 + 0 + 0 = 1`
- critical path 覆盖率（替代口径）= 5 / 13 Must Have 故事（US-263/264/270/271/272）
- critical path 通过率 = 5 / 5 = 1.00
- 本层门控：**PASSED**
- 全量回归（前端）：`Test Files 5 failed | 41 passed (46)`，`Tests 5 failed | 534 passed (539)`，相对基线新增失败 0（5 条均为既有或满载超时，逐条见单元报告）
- 全量回归（后端）：`Ran 1139 tests`，`failures=6`，相对基线新增失败 0（6 条均为既有 Windows 权限类）

## 用户旅程

### TC-E2E-1501: 清册业主资料 → 实名开关 → 他人查看 → 头像上传 → 管理员席位列表

- 关联：US-263、US-264、US-270、US-271、US-272 / AC-263-01、AC-264-01/02、AC-270-01/02/03/04、AC-271-01/02/04、AC-272-01
- 环境：Django 测试配置 + fakes 短信；命令 `python manage.py test tests.e2e.test_profile_ux_journeys --settings=config.test_settings`

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 清册业主注册并建立 HEAD 认证（含 registry_owner） | 注册 201，认证建立 | 成功 | PASS |
| 2 | PATCH 签名（real_name_visible=false） | 200；他人 profile real_name=null | 符合 | PASS |
| 3 | PATCH real_name_visible=true，访客 GET 其 profile | 200；real_name=张三、signature 可见、无 phone | 符合 | PASS |
| 4 | 上传 4.9MB PNG 并设置头像 | 201；他人 profile avatar_url 非空 | 符合 | PASS |
| 5 | 管理员赋予席位并 GET bucket=active&building=1栋 | 201；holder_detail.name=张三、unit_text 非空；默认 active | 符合 | PASS |

- 结论：PASS

## 缺陷

无。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | AC-260-01 / AC-260-02 | 登录后打开 /me/profile，分别在 ≥768px 与 <768px 视口观察昵称/性别/生日/保存按钮 | 宽屏四项垂直中心偏差 ≤2px 且等高；窄屏整行换行、底边对齐、无重叠 | Chrome（桌面 1366 与 375 宽度） | 是 |
| MV-02 | AC-262-01 | 观察顶部右上角头像/昵称/箭头 | 头像 24–32px 圆形，三者中心线偏差 ≤2px | Chrome | 否 |
| MV-03 | AC-265-02 | 管理端席位页展开"资格失效/已结束" | 显示状态文案与结束原因（有数据时） | 测试环境含历史席位数据 | 否 |
| MV-04 | AC-270-01 | 从房屋关系/席位昵称点击进入 profile | 跳转到 `/users/{id}/profile`，内容与权限符合 | Chrome | 是 |
