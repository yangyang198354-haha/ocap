<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T12:52:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告

## 摘要

- 执行时间：2026-11-22T12:51+08:00；环境：Vitest + Django `config.test_settings`（测试库），HTTP/uni.request 全 mock。
- 命令：
  - frontend：`npx vitest run tests/user_menu.spec.js tests/layout_router.spec.js tests/layout_nav.spec.js tests/layout_pages.spec.js tests/identity_property_menu_router.spec.js tests/identity_property_identity_page.spec.js`
  - miniprogram：`npx vitest run tests/navigation_ia.spec.js tests/identity_property_pages.spec.js tests/product_review_ui.spec.js tests/pages.spec.js`
  - backend：`python manage.py test tests.integration.test_frontend_contract tests.integration.test_owner_auth_v2_contract tests.integration.test_phone_match_contract --settings=config.test_settings`
- `total = pass + fail + skip + blocked + not_testable = 197 + 0 + 0 + 0 + 0 = 197`
- 通过率 = `197 / 197 = 100%`；判定模式：baseline 零新增失败。
- **本层门控：PASSED**

## 执行输出

```
frontend:     Test Files 6 passed (6) | Tests 104 passed (104)
miniprogram:  Test Files 4 passed (4) | Tests  50 passed (50)
backend:      Ran 43 tests ... OK
```

## 分项结果

| 集成边界 | TC | AC | 结果 |
|---|---|---|---|
| MOD-174 ↔ SideNav/SubNavBar | TC-INT-803/804/816、TC-INT-824 | AC-299-01/02/04、AC-301-02 | PASS |
| MOD-175 ↔ auth/housing store | TC-INT-841/843 | AC-302-01/02、AC-303-01 | PASS |
| MOD-176 ↔ housing store/UnitsReview | TC-WEB-910/911/912、TC-INT-1103/1104/1105 | AC-300-01~03、AC-306-02、AC-307-01 | PASS |
| MOD-177 ↔ vue-router | TC-INT-830、TC-INT-972/973 | AC-306-01~03 | PASS |
| MOD-178 ↔ menus | TC-INT-898/899/904 | AC-302-01/02/04 | PASS |
| MOD-179 ↔ api/http（小程序） | TC-E2E-1101~1104、TC-MP-903/905 | AC-304-01~04、AC-301-01 | PASS |
| MOD-180 ↔ theme/api | TC-E2E-1105/1106、TC-MP-904 | AC-305-01~04 | PASS |
| MOD-181 ↔ 两端常量 | TC-UNIT-1101、TC-MP-903 | AC-309-01/02 | PASS |
| MOD-182 ↔ 后端 /me/email/verify、/me/cancel | TC-E2E-1107/1108 | AC-305-01、AC-310-01 | PASS |
| 后端契约（字段/端点/客户端解析） | TC-INT-488/490/713/719/965 | AC-299~310 的接口部分 | PASS |

## 与基线对比（baseline 模式）

相对基线零新增失败。首次执行时 `TC-E2E-1108` 失败（见下方 DEF-001），修复后本层重跑全绿；最终计数来自最后一次执行。

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| TC-E2E-1108 | 点击“确认注销”后未发起 `/me/cancel`，控制台出现未处理 Promise 拒绝 | `miniprogram/pages/cancel/index.vue` 调用 `confirmDanger('cancelAccount')`，但 `utils/confirm.js` 的 `CONFIRM_TEXTS` 无该键 | DEF-001（已修复并复测） |
