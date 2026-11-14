<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-14T17:48:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告

## 摘要

- 执行时间：2026-11-14 17:45~17:46（Asia/Shanghai）
- 环境：Python 3.14.6 / Django 6.0.6（`config.test_settings`）；Node 20 / vitest 2.1.9（jsdom）
- 命令：`python manage.py test tests.unit tests.smoke --settings=config.test_settings`；`npm test`（frontend）；`npm test`（miniprogram）
- 后端单元/冒烟：total 151 = pass 148 + fail 0 + skip 3 + blocked 0 + not_testable 0
- 前端：total 185 = pass 185 + fail 0 + skip 0 + blocked 0 + not_testable 0
- 小程序：total 78 = pass 78 + fail 0 + skip 0 + blocked 0 + not_testable 0
- 合并：total 414 = pass 411 + fail 0 + skip 3 + blocked 0 + not_testable 0
- 通过率 = 411 / (411 + 0 + 0) = 100%；判定模式 baseline；**本层门控：PASSED**

## 执行输出

```
# backend
Ran 151 tests in 0.988s
OK (skipped=3)

# frontend
Test Files  20 passed (20)
     Tests  185 passed (185)

# miniprogram
Test Files  12 passed (12)
     Tests  78 passed (78)
```

## 分项结果

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-WEB-501 | AC-145-02、AC-146-01/02/04/05/08、AC-148-01/02 | 主页展示身份、数量、名称、类型、面积、关系标签 | PASS |
| TC-WEB-502 | AC-145-01、AC-146-06、AC-148-03 | 游客数量 0 与空状态 | PASS |
| TC-WEB-503 | AC-147-01 | `/me` 未返回时显示加载中，不显示游客/0 | PASS |
| TC-WEB-504 | AC-147-02 | `/me` 失败显示加载失败与重试 | PASS |
| TC-MP-501 | AC-145-02、AC-146-01/02/04/05/08、AC-148-01/02 | 小程序首页房屋明细 | PASS |
| TC-MP-502 | AC-145-01、AC-146-06、AC-148-03 | 小程序游客空状态 | PASS |
| TC-MP-503 | AC-145-02、AC-148-01 | “我的”页单一身份、不出现“户主” | PASS |
| 其余既有单元/组件用例 | — | 回归 | PASS |

## 与基线对比（baseline 模式）

- 基线：改动前后端 561 项通过、前端 181 项通过、小程序 75 项通过。
- 本次新增：前端 4 项、小程序 3 项、后端 14 项（计入集成/E2E 报告）。
- 新增失败：0。

## 失败汇总（需路由给开发）

无。
