<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-21T12:11:30+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_hierarchy/requirements/user_stories.md</file>
    <file>project_workspace/ocap_profile_hierarchy/development/implementation_plan.md</file>
    <file>frontend/tests/profile_ux.spec.js</file>
    <file>miniprogram/tests/identity_display.spec.js</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：个人主页信息层级与实名认证徽章

## 测试策略

- 被测改动：`frontend/src/portal/UserProfile.vue`、`miniprogram/pages/me/index.vue` 及其测试。
- 范围：9 条 Must Have AC；不含后端（无改动）、不含管理端。
- 环境：Windows 开发机；frontend/小程序 vitest + jsdom；无真实网络。
- 判定模式：INCREMENTAL baseline（零新增失败）；critical path 100%。
- 基线来源：本批改动前已存在的 5 条前端失败（路由、登录页样式、主题构建器、生成物行尾），见集成报告“与基线对比”。
- 分层：unit = 单页面组件 + mock HTTP；integration = 客户端调用路径与后端路由契约（`frontend/tests/layout_contract.spec.js`）；E2E = 本项目无浏览器 E2E 框架，用多步组件旅程替代（首行声明）。

## AC 映射

| AC | 用例 ID | 级别 | 现有/新写 | 位置 | 前置 | 动作 | 预期 |
|---|---|---|---|---|---|---|---|
| AC-273-01 | TC-UNIT-1509、TC-E2E-1502 | unit / e2e-替代 | 新写 | `frontend/tests/profile_ux.spec.js`、`profile_hierarchy_e2e.spec.js` | real_name=杨扬、identity=产权业主 | 渲染他人主页 | 昵称索引 < 实名索引 < 身份索引 |
| AC-273-02 | TC-UNIT-1510 | unit | 新写 | `profile_ux.spec.js` | real_name=null | 渲染主页 | 无 `.real-name`、无徽章 |
| AC-273-03 | TC-UNIT-1511 | unit | 新写 | `profile_ux.spec.js` | nickname='' | 渲染主页 | 显示“未设置昵称”且在身份之前 |
| AC-274-01 | TC-UNIT-1509、TC-MP-504、TC-E2E-1502 | unit / e2e-替代 | 新写 | 上述两文件 + `miniprogram/tests/identity_display.spec.js` | 实名可见 | 渲染 | `.real-name` 内存在“已实名认证”徽章 |
| AC-274-02 | TC-UNIT-1510、TC-MP-505 | unit | 新写 | 同上 | 无实名/请求失败 | 渲染 | 无徽章、无“实名：”文本 |
| AC-275-01 | TC-UNIT-1512 | unit | 新写 | `profile_ux.spec.js` | — | 读取组件样式规则 | `.real-name` 用 `var(--text)`/650；`.identity-tag` 不含同样规则 |
| AC-275-02 | TC-UNIT-1512、TC-UNIT-1509 | unit | 新写 | `profile_ux.spec.js` | 无实名 | 渲染 | 身份保留 `.identity-tag` 独立样式 |
| AC-276-01 | TC-MP-504、TC-E2E-1503 | unit / e2e-替代 | 新写 | `miniprogram/tests/identity_display.spec.js`、`profile_hierarchy_e2e.spec.js` | `GET /me/profile` 返回杨扬 | 打开“我的”页 | 昵称 < 实名 < 身份，且存在徽章 |
| AC-276-02 | TC-MP-505 | unit | 新写 | `identity_display.spec.js` | 游客/未开启实名 | 打开“我的”页 | 无实名与徽章，仍有昵称与身份 |
| AC-276-03 | TC-MP-505、TC-E2E-1503 | unit / e2e-替代 | 新写 | 同上 | `/me/profile` 500 | 打开“我的”页 | 静默降级；恢复后重新显示 |

## 测试数据需求

前端 mock 返回公开 profile；小程序 mock `/me`、`/me/housing`、`/me/profile`、`/ledger/reports`。无持久化写入，无 `[DATA_REQUIRED]`。

## 不可测项

无。

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-273 | TC-UNIT-1509、1510、1511、TC-E2E-1502 | unit / e2e-替代 |
| US-274 | TC-UNIT-1509、1510、TC-MP-504、505 | unit |
| US-275 | TC-UNIT-1509、1512 | unit |
| US-276 | TC-MP-504、505、TC-E2E-1503 | unit / e2e-替代 |
