<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-14T17:37:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_identity_display/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术栈：用户端身份显示与认证房屋信息

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言（后端） | Python | 本机 3.14.6；目标机 3.13（画像 P4/P7） | 沿用 | 现有后端运行时 | 全部 | 无新增 |
| Web 框架 | Django + DRF | 本机 Django 6.0.6、DRF 3.17.1（画像 P4 实测） | 沿用 | 现有 API 层 | REQ-FUNC-136~141 | 本机版本高于选型目标 5.2，沿用既有差异，不在本期处理 |
| 前端框架 | Vue 3 + Pinia + Element Plus | vue ^3.5.13、pinia ^2.1.7、element-plus ^2.8.7（`frontend/package.json:20-24`） | 沿用 | 现有 Web 用户端 | REQ-FUNC-136/139/140 | 无 |
| 小程序框架 | uni-app (Vue 3) + Pinia | `@dcloudio/uni-app ^3.0.0-4060620250520001`、pinia ^2.1.7（`miniprogram/package.json:13-17`） | 沿用 | 现有小程序 | REQ-FUNC-141 | 无 |
| 数据存储 | MySQL（测试环境）/ SQLite（测试运行） | 画像 P7 / `config.test_settings` | 沿用 | 本次无结构变更 | — | 无 |
| 测试（后端） | Django test runner | 画像 P4 | 沿用 | 现有测试体系 | AC 验证 | 无 |
| 测试（前端/小程序） | vitest | vitest ^2.1.9（两份 `package.json`） | 沿用 | 现有测试体系 | AC 验证 | 无 |
| 新增第三方依赖 | 无 | — | — | 本次只改现有代码与模板 | — | 无许可证/维护风险 |

## 技术风险

| 级别 | 风险 | 缓解措施 |
|---|---|---|
| Medium | 现有后端测试与前端/小程序测试大量断言 `/me` 返回“户主”或多标签，行为变更会导致既有用例失败 | 在 GROUP_D 按新口径更新受影响用例（只改断言与夹具，不改业务）；以改动前实跑结果为基线，确认失败均属预期口径变更，无其他新增失败 |
| Low | `/me` 响应字段增加导致前端契约测试集合断言失败 | 同步更新 `backend/tests/integration/test_frontend_contract.py` 的字段集合断言，并新增 `units[]` 字段断言 |
| Low | 历史决议/收入/报销记录中已保存的多标签文案不回填，仍可能出现“户主” | 本次范围仅当前身份与认证房屋；历史数据修复另立需求（见 architecture_design 开放问题） |
| Low | 小程序与 Web 对缺失字段的兜底文案不一致 | 后端统一提供 `unit_type_label` / `area_display` / `role_label`；两端只做透传 |
