<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-14T17:49:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/testing/test_plan.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告

## 摘要

- 执行时间：2026-11-14 17:46（Asia/Shanghai）
- 环境：Python 3.14.6 / Django 6.0.6 / DRF 3.17.1，SQLite 内存库
- 命令：`python manage.py test tests.integration --settings=config.test_settings`
- total = pass + fail + skip + blocked + not_testable = 379 + 0 + 5 + 0 + 0 = 384
- 通过率 = 379 / (379 + 0 + 0) = 100%；判定模式 baseline；**本层门控：PASSED**

## 执行输出

```
Ran 384 tests in 6.6s
OK (skipped=5)
Found 384 test(s).
System check identified no issues (0 silenced).
```

## 分项结果

集成边界：`/me` 视图 ↔ identity/committee/residency/registry；前端源码 ↔ 后端路由与字段契约。

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-501 | AC-145-01、AC-146-06 | 游客 labels/units/is_guest | PASS |
| TC-INT-502 | AC-145-02/10、AC-146-01/04/05 | 清册产权业主与完整房屋字段 | PASS |
| TC-INT-503 | AC-145-03 | 申诉通过显示产权业主 | PASS |
| TC-INT-504 | AC-145-04/05、AC-146-08 | 同住人、产权业主优先、关系标注 | PASS |
| TC-INT-505 | AC-145-07/08/09、AC-146-03 | 职务优先与失效回落、车位展示 | PASS |
| TC-INT-506 | AC-146-02/04/05/09 | 排序、缺失值、同 unit 去重 | PASS |
| TC-INT-507 | AC-145-06、AC-146-07、AC-147-03 | 已结束关系排除 | PASS |
| TC-INT-508 | REQ-FUNC-141 | Web 与小程序源码均读取 4 个展示字段 | PASS |
| 其余既有集成用例 | — | 回归 | PASS |

## 与基线对比（baseline 模式）

- 基线：改动前 `tests.integration` 376 项通过（全量 561 中同层）。
- 本次新增 8 项，全部通过；既有失败 0；新增失败 0。

## 失败汇总（需路由给开发）

无。
