<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T12:52:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告

## 摘要

- 执行时间：2026-11-22T12:50+08:00；环境：Vitest（Node），mock HTTP，无网络。
- 命令：
  - `npx vitest run tests/navigation_ia.spec.js tests/layout_menus.spec.js tests/layout_css.spec.js`（frontend）
  - `npx vitest run tests/navigation_ia.spec.js -t "TC-UNIT-1101"`（miniprogram；其余 8 条不属于本层）
- `total = pass + fail + skip + blocked + not_testable = 44 + 0 + 0 + 0 + 0 = 44`
- 通过率 = `pass / (pass + fail + blocked) = 44 / 44 = 100%`；判定模式：baseline 零新增失败。
- **本层门控：PASSED**

## 执行输出

```
> Test Files  3 passed (3)
>      Tests  43 passed (43)

> Test Files  1 passed (1)
>      Tests  1 passed | 8 skipped (9)
```

## 分项结果

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-UNIT-804/805/814 | AC-299-01/02、AC-302-01/02 | Web 菜单二级项 3 项、用户菜单两组展平 6 项、`/units/appeal` 文案 | PASS |
| TC-UNIT-1101 | AC-309-01、AC-302-01/02、AC-303-01 | 两组菜单 key/label/顺序与展平结果；无“手机号/认证申诉” | PASS |
| TC-UNIT-1102 | AC-308-01/02 | `USER_MENU_TIMING = {400, 180}` | PASS |
| TC-INT-1101 | AC-308-02 | el-dropdown `show/hide-timeout=180`、trigger 含 hover/click、popper-class | PASS |
| TC-INT-1102 | AC-308-01/03 | 全局 CSS 400ms 过渡 + `prefers-reduced-motion: reduce` → 0s | PASS |
| TC-UNIT-1101（mini） | AC-305-01/02、AC-309-01 | `MP_USER_GROUPS` 4+1 项、无“设置密码”、三 Tab 文案 | PASS |
| layout_menus / layout_css 既有用例 | AC-291/AC-252 等回归 | 菜单与断点约束未回退 | PASS |

## 与基线对比（baseline 模式）

相对基线（frontend 568 / mini 138 全绿）：本层新增 15 条用例全部通过；既有用例零新增失败。

## 失败汇总（需路由给开发）

无。
