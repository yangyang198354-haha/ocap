<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-19T00:33:00+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/testing/test_plan.md</file>
    <file>frontend/tests/profile_ux.spec.js</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告 — ocap_profile_ux

## 摘要

- 执行时间：2026-11-19 00:25（本地）
- 环境：frontend/，vitest 2.1.9 + jsdom，Element Plus
- 命令：`cd frontend && npx vitest run tests/profile_ux.spec.js`；全量 `npm test`
- 本层新写用例：7 条，全部 PASS。
- 全量：`total = pass + fail + skip + blocked + not_testable = 534 + 5 + 0 + 0 + 0 = 539`
- 通过率 = 534 / (534 + 5 + 0) = 99.07%
- 判定模式：baseline（零新增失败）→ **本层门控：PASSED**

## 执行输出

```
npx vitest run tests/profile_ux.spec.js
 ✓ tests/profile_ux.spec.js (7 tests) 1001ms
 Test Files  1 passed (1)
```

```
cd frontend && npm test
 Test Files  5 failed | 41 passed (46)
      Tests  5 failed | 534 passed (539)
   Duration  161.92s
```

## 分项结果

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-UNIT-1501 | AC-270-01/02、AC-272-01/03 | 他人 profile 展示昵称/身份/签名，is_self 显示编辑入口，无敏感字段 | PASS |
| TC-UNIT-1502 | AC-270-01、AC-272-02 | 空签名显示"这个人很懒，什么都没写"；他人页无编辑入口 | PASS |
| TC-UNIT-1503 | AC-271-03、AC-272-01 | 保存签名档提交 `{signature}`；非产权业主实名开关禁用 | PASS |
| TC-UNIT-1504 | AC-264-01、AC-265-01 | 席位主表 10 列、默认 bucket=active、展开请求 bucket=ended、脱敏电话与类型可见 | PASS |
| TC-UNIT-1505 | AC-269-02/01、AC-270-01 | 电话号码走 phone 参数、姓名走 q 参数；用户列链接到 profile | PASS |
| TC-UNIT-1506 | AC-261-01、AC-262-01/02 | 右上角头像与昵称同触发器，无头像回退默认头像图片 | PASS |
| TC-INT-1501 | 契约 | `meApi.userProfile` → GET /users/{id}/profile | PASS |

## 与基线对比（baseline 模式）

全量失败 5 条，逐条比对：

| 失败 | 判定 | 依据 |
|---|---|---|
| TC-UNIT-873（Login.vue AuthShell） | 既有 | 产品文件与本次 diff 无关；GROUP_C 阶段已复现同样失败 |
| qa_unit_theme TC-UNIT-103（风格构建器 fatal） | 既有 | 主题脚本本次未改动；GROUP_C 阶段已复现 |
| theme_build（生成物换行差异） | 既有 | Windows 换行差异；生成物与脚本本次未改动 |
| identity_property_e2e / identity_property_menu_router（随机出现） | 环境（满载超时） | 单独运行 `Test Files 1 passed`；本次改动不涉身份路由逻辑 |
| layout_router / layout_e2e（随机出现） | 环境（满载超时） | 单独运行通过（本次已复跑并记录） |

新增失败：0。

## 失败汇总（需路由给开发）

无产品缺陷。
