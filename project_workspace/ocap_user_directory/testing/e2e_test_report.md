<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T22:46:57.2524963+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>development/code_review_report.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 E2E 测试报告

critical path 口径：替代（后端 API 多步旅程 TC-E2E-305 + 前端组件用例）

## 摘要

- 执行时间：2026-11-11 22:45 ~ 22:46（Asia/Shanghai）。
- 命令：`python manage.py test tests.e2e --settings=config.test_settings`
- 计数：total 34 = pass 33 + fail 0 + skip 1 + blocked 0 + not_testable 0；通过率 = 33 / (33 + 0 + 0) = 100%。
- 新增：TC-E2E-305（管理员登录 → 按实名搜索 → 查看四类目录信息）1 个，PASS。
- critical path 覆盖率 = 5 / 5 Must Have 故事 = 100%；critical path 通过率 = 1 / 1 = 100%。
- 判定模式：baseline；**本层门控：PASSED**。

## 执行输出

```
> python manage.py test tests.e2e --settings=config.test_settings
Ran 34 tests in 4.966s
OK (skipped=1)

> python manage.py test tests.e2e.test_admin_user_directory_journey --settings=config.test_settings -v 2
TC-E2E-305 / US-132 ~ 136：管理员登录后按实名搜索并看到身份/认证/实名/上次登录。 ... ok
Ran 1 test in 0.015s
OK
```

## 全量回归

| 范围 | 命令 | 结果 | 相对基线新增失败 |
|---|---|---|---|
| 后端全量 | `python manage.py test --settings=config.test_settings` | Ran 530 tests, OK (skipped=9) | 0（基线 520 OK，新增 10 个用例） |
| 前端全量 | `npm run test -- --run` | Tests 2 failed \| 154 passed (156) | 0（2 个失败为基线既有 Windows 主题环境问题） |
| 小程序 | `npm run test -- --run` | Test Files 11 passed；Tests 75 passed (75) | 0 |

## 用户旅程

### TC-E2E-305: 管理员登录后台并查看注册用户目录

- 关联：US-132 ~ US-136 / AC-132-01 ~ 05、AC-133-01、AC-134-01/03、AC-135-01/02、AC-136-02；环境：Django test runner + SQLite 内存库，真实路由与权限。
- 步骤与结果：

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 创建管理员、业主用户、专有部分、清册业主/手机号、户主关系、业委会委员席位 | 数据创建成功 | 创建成功 | PASS |
| 2 | POST `/api/v1/admin/auth/login` 管理员账号密码 | 200，返回 token | 200，返回 token | PASS |
| 3 | GET `/api/v1/admin/users?q=张三` | 200，结果含该用户 | 200，命中该用户 | PASS |
| 4 | 校验用户行 | identity_label=委员、certified_units=1、real_names=["张三"]、last_login_at 非空、手机号脱敏 | 与期望一致 | PASS |

- 结论：PASS。

## 缺陷

无。

## 人工验证清单

无（全部 AC 均有自动化用例覆盖）。
