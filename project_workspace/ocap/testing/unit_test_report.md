<file_header>
  <author_agent>sdlc-test-engineer</author_agent>
  <timestamp>2026-11-07T23:57:31+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>0.3.0</version>
  <input_files><file>testing/test_plan.md</file><file>requirements/user_stories.md</file><file>development/implementation_plan.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

> 复跑说明（ocap-GROUP_D-2）：DEF-001~004 修复后复跑，本层结果不变。

## 摘要

- 执行时间：2026-11-07 23:56 ~ 23:57（Asia/Shanghai，复跑）。
- 环境：Windows，Python 3.14.6，Django 6.0.6，DRF 3.17.1，`config.test_settings`，SQLite `:memory:`。
- 命令：`python manage.py test tests.unit --settings=config.test_settings -v 1`（工作目录 `backend/`）。
- total = pass + fail + skip + blocked + not_testable = 33 = 33 + 0 + 0 + 0 + 0。
- 通过率 = pass/(pass+fail+blocked) = 33/(33+0+0) = 100.00%。
- 判定模式与阈值：FULL_FLOW threshold，unit_pass ≥ 0.80。
- **本层门控：PASSED**。

## 执行输出

```
python manage.py test tests.unit --settings=config.test_settings -v 1
Ran 33 tests in 0.046s
OK
```

## 分项结果

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-001~003 | AC-049-*、AC-061-* | 金额格式化：空值、两位小数四舍五入、负数符号 | PASS | — | — |
| TC-UNIT-004~005 | AC-033-* | 手机号 / 邮箱脱敏 | PASS | — | — |
| TC-UNIT-006~009 | AC-009-*、AC-032-* | 密码强度规则（长度、纯数字、弱口令、合规） | PASS | — | — |
| TC-UNIT-010~011 | AC-040-* | 任期加月：月末裁剪与跨年 | PASS | — | — |
| TC-UNIT-012~014 | AC-032-* | 限流命中、锁定与错误体形状 | PASS | — | — |
| TC-UNIT-015~018 | AC-049-* | 报销金额解析（精度、零值、上限、非数字） | PASS | — | — |
| TC-UNIT-019~022 | AC-059-* | 收入表解析（千分位、缺列、2% 错误率边界） | PASS | — | — |
| TC-UNIT-023~025 | AC-055-* | 题目与选项校验（单选项、重复 key） | PASS | — | — |
| TC-UNIT-026 | AC-057-* | 投票结果计数与百分比 | PASS | — | — |
| TC-UNIT-027~030 | AC-046-*、AC-065-* | 半数同意判定（通过 / 未通过 / 未到期 / 幂等） | PASS | — | — |
| TC-UNIT-031 | AC-039-* | 委员 / 业主代表身份判定与分母 | PASS | — | — |
| TC-UNIT-032~033 | AC-027-* | 户主空缺晋升（有 OWNER / 无 OWNER） | PASS | — | — |

## 与基线对比

FULL_FLOW / greenfield，无既有基线；本层 0 新增失败。

## 失败汇总（需路由给开发）

无。
