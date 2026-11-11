<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T23:32:38.0156563+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_admin_polish/testing/test_plan.md</file>
    <file>project_workspace/ocap_admin_polish/development/implementation_plan.md</file>
    <file>project_workspace/ocap_admin_polish/development/code_review_report.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告

## 摘要

- 执行时间：2026-11-11 23:31（Asia/Shanghai；前端最后一次执行 23:31:54）；环境：Windows / Python 3.14.6 / Django 6.0.6 / SQLite 内存库 + vitest/jsdom。
- 后端命令：`cd backend; python manage.py test tests.integration --settings=config.test_settings`
- 后端 `total = pass + fail + skip + blocked + not_testable = 371 + 0 + 5 + 0 + 0 = 376`
- 后端通过率 = 371 / (371 + 0 + 0) = 100%；判定模式 baseline；**本层门控：PASSED**。
- 前端命令：`cd frontend; npm run test -- --run` → `Test Files 19 passed / Tests 181 passed`（0 failed）。
- 新增后端集成用例 24 个（迁移 5、一致性 6、管理员偏好 6、预览命令 4、跨端显示 3）；新增前端用例 24 个（管理端主题守护 11、管理端 store 12、API 契约 1）。

## 执行输出

```
Creating test database for alias 'default'...
.................................................................................................................................................................................................................................................................................................................sssss..................................................................
----------------------------------------------------------------------
Ran 376 tests in 6.102s

OK (skipped=5)
Destroying test database for alias 'default'...
Found 376 test(s).
System check identified no issues (0 silenced).
```

前端：
```
Test Files  19 passed (19)
     Tests  181 passed (181)
```

契约测试：`backend/tests/integration/test_frontend_contract.py` 全部通过（含新增 `/admin/me/theme` 解析为 `IsAdmin` 视图）；`frontend/tests/api.spec.js` 覆盖 `admin.theme/setTheme` 路径与方法。

## 分项结果

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-401 | AC-134-01/02/03 | 迁移重生成 + 字段不变 + 幂等 + 可逆 | PASS | — | — |
| TC-INT-402 | AC-134-04 | 冲突整批不生效 | PASS | — | — |
| TC-INT-403 | ADR-067 | 交叉更新两阶段成功 | PASS | — | — |
| TC-INT-404 | AC-134-05 | 非纯数字户号核对清单 | PASS | — | — |
| TC-INT-405 | AC-134-06 / NFUNC-23 | 5742 条 <60 秒 | PASS | — | — |
| TC-INT-411 | — | 模型保存经规则 | PASS | — | — |
| TC-INT-412 | AC-137-02/03 | 导入等价字段合并 | PASS | — | — |
| TC-INT-413 | AC-136-01/02/04 | 新增/编辑/判重 | PASS | — | — |
| TC-INT-414 | AC-135-03/04 | 新旧关键词搜索 | PASS | — | — |
| TC-INT-415 | AC-138-02/03 | 模板示例单一来源 | PASS | — | — |
| TC-INT-416 | AC-136-03 | 非管理员拒绝 | PASS | — | — |
| TC-INT-421 | AC-135-01/02/06 | 管理端/房屋关系/me 一致 | PASS | — | — |
| TC-INT-422 | AC-135-03/04 | 旧关键词不命中（两接口） | PASS | — | — |
| TC-INT-423 | AC-135-06 | /me 不含业主姓名/手机号 | PASS | — | — |
| `test_admin_theme_preference_api.py` 六个用例 | AC-141-03、AC-143-01/03 | 管理员偏好接口与隔离 | PASS | — | — |
| `test_registry_specific_part_preview.py` 四个用例 | AC-134-03/04/05 | 预览命令只读、冲突、limit | PASS | — | — |
| admin_theme.spec.js 口径 1~9 | AC-142-01~06 | 作用域/渐变/对比度/结构 | PASS | — | — |
| TC-UNIT-501~504（前端） | AC-139/140/141/143 | 管理端 store | PASS | — | — |
| TC-WEB-013b | IFC-251 | 管理端偏好 API 路径 | PASS | — | — |
| 既有集成用例 | — | 清册导入、身份、权限、内容等 | PASS / SKIP 5 | — | 既有 skip |

## 与基线对比（baseline 模式）

- 后端集成基线：352 tests OK（5 skipped）；本次 376（+24），失败 0，无新增失败。
- 前端基线：154 passed / 2 failed（既有 Windows 主题环境问题）。本次 181 passed / 0 failed；2 个既有失败已修（`theme.spec.js` 临时目录改 `os.tmpdir()`，主题构建行尾问题随重新生成消除），不属新增失败。
- skip 5 个为既有条件跳过，非本次引入。

## 失败汇总（需路由给开发）

无。
