<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-21T12:11:30+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>frontend/tests/profile_hierarchy_e2e.spec.js</file>
    <file>miniprogram/tests/profile_hierarchy_e2e.spec.js</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告

## 摘要

critical path 口径：替代（多步组件旅程，项目无浏览器 E2E 框架）
total = pass + fail + skip + blocked + not_testable = 2 = 2 + 0 + 0 + 0 + 0；critical path 覆盖率 = 4/4 Must Have 故事 = 100%；critical path 通过率 = 2/2 = 100%；本层门控：PASSED。

## 全量回归

| 命令 | 计数 | 相对基线新增失败 |
|---|---|---|
| `frontend: npx vitest run --reporter=verbose` | 546 = 541 passed + 5 failed | 0 |
| `miniprogram: npm test` | 138 = 138 passed + 0 failed | 0 |

前端 5 条基线失败（本批改动前已存在，均不涉及 UserProfile / “我的”页）：
1. `identity_property_menu_router.spec.js` 路由解析（既有）
2. `layout_router.spec.js` 旧路径可解析（既有超时/路由）
3. `layout_css.spec.js` 登录页自适应（Login.vue AuthShell，既有）
4. `qa_unit_theme.spec.js` TC-UNIT-103 构建器拒绝不合规风格（既有）
5. `theme_build.spec.js` 生成物与源一致（既有行尾差异）

## 用户旅程

### TC-E2E-1502: 他人主页 → 本人主页
- 关联：US-273/274/275；环境：Windows / vitest / jsdom（替代）。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 以他人身份打开 `/users/9/profile`（real_name=杨扬） | 昵称 → 实名+徽章 → 身份 | 顺序与徽章均符合 | PASS |
| 2 | 打开本人 `/users/2/profile`（is_self=true） | 同样顺序与徽章，且显示编辑资料 | 符合 | PASS |

### TC-E2E-1503: 小程序“我的”页降级与恢复
- 关联：US-276；环境：Windows / vitest（替代）。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | `/me/profile` 返回 500，打开“我的” | 无实名与徽章，仍有昵称与身份 | 符合，无弹窗 | PASS |
| 2 | `/me/profile` 恢复返回杨扬，重新进入 | 昵称 → 实名+徽章 → 身份 | 符合 | PASS |

## 缺陷

无。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | AC-275-01/275-02、TC-UNIT-1512 | 在真实浏览器打开他人个人主页，切换霓虹玻璃/赛博终端主题 | 实名与身份在颜色、字重上肉眼可区分；徽章与实名相邻 | 浏览器 + 测试环境 | 否 |
| MV-02 | AC-276-01 | 微信开发者工具打开“我的”页（已开启实名账号） | 昵称 → 实名+徽章 → 身份，换行不重叠；主题色正常 | 微信开发者工具 | 否 |
