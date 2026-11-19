<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-19T00:34:00+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/testing/test_plan.md</file>
    <file>backend/tests/integration/test_profile_ux_api.py</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告 — ocap_profile_ux

## 摘要

- 执行时间：2026-11-19 00:22（本地）
- 环境：backend/，`python manage.py test --settings=config.test_settings`（SQLite 内存库，外部依赖 fakes）
- 新写集成用例：7 条，全部 PASS。
- 全量：`total = pass + fail + skip + blocked + not_testable = 1132 + 6 + 1 + 0 + 0 = 1139`
- 通过率 = 1132 / (1132 + 6 + 0) = 99.47%
- 判定模式：baseline（零新增失败）→ **本层门控：PASSED**

## 执行输出

```
python manage.py test tests.integration.test_profile_ux_api --settings=config.test_settings
Ran 7 tests in 0.135s
OK
```

```
python manage.py test --settings=config.test_settings
Ran 1139 tests in 51.097s
FAILED (failures=6, skipped=1)
```

## 分项结果（按集成边界）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-1501（ProfileFieldsTests） | AC-271-01/02/03/04、AC-272-01/03、AC-270-02/03/04 | 签名/开关默认值、100 字边界、非业主 403、业主实名在公开 profile 可见/关闭即隐藏、白名单 8 键且无 phone/email/birthday/account_no、404/401 | PASS |
| TC-INT-1502（AvatarLimitTests） | AC-263-01/02/03、REQ-NFUNC-051 | 4.9MB 201、5.1MB 413 FILE_TOO_LARGE、gif 400 | PASS |
| TC-INT-1503（SeatListProfileUxTests） | AC-264-01/02/03、AC-265-01/02/03/04 | bucket=active 仅 ACTIVE、ended 含 REVOKED 且有 end_reason、holder_detail 8 键与脱敏电话、building/unit_no 过滤、非法 bucket 400、普通用户 403 | PASS |
| TC-INT-1504（FlowDetailTests） | AC-266-01、AC-267-01/02 | approvers 含 identity_label；PUT 改名与换审批人成功 | PASS |
| TC-INT-1505（MembershipFilterTests） | AC-268-01/02/03、AC-269-01/02/03 | building/unit_no/floor 过滤；name/手机后 4 位/q 搜索；非法 phone 400 | PASS |

## 与基线对比（baseline 模式）

6 条失败均为 GROUP_C 已记录的 Windows 环境预存失败，文件本次未改动：

| 失败 | 判定 | 依据 |
|---|---|---|
| `test_tc_e2e_519_relocate_shops_then_export_then_precheck_through_import_api` | 既有 | Windows 文件权限/路径语义；owner_auth 相关文件未改 |
| `test_tc_int_645_after_relocation_export_structure_counts_precheck_and_shop_column` | 既有 | 同上 |
| `test_tc_int_647_location_guard_rejects_open_dir_and_deploy_root_without_db_access` | 既有 | 同上 |
| `test_tc_int_627_backup_file_secure_and_without_personal_data` | 既有 | 0o600 断言在 Windows 不成立 |
| `test_tc_int_611_no_file_written_into_repo_root_and_no_part_left` | 既有 | 同上 |
| `test_tc_int_593_backup_file_secure_and_without_personal_data` | 既有 | 同上 |

新增失败：0。

## 失败汇总（需路由给开发）

无产品缺陷。
