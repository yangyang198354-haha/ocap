<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-08T22:58:45+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>0.4.0</version>
  <input_files><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>testing/test_plan.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>DRAFT</status>
</file_header>

> 复跑说明（ocap-GROUP_D-7）：GROUP_C-5 返工后重跑。REWORK_AUTHORIZED: project_workspace/ocap/testing/。

## 摘要

- 执行时间：2026-11-08 22:55 ~ 22:56（Asia/Shanghai）。
- 环境：Linux，Python 3.12.3，Django 5.2.19，DRF 3.18.3，`config.test_settings`，SQLite `:memory:`；Node v22.23.3，vitest 2.1.9。
- 命令：
  - `(cd backend && python manage.py test tests.unit --settings=config.test_settings)`
  - `(cd frontend && npx vitest run)`（api.spec.js + auth.store.spec.js 归入本层）
  - `(cd miniprogram && npx vitest run)`（api.spec.js + store.spec.js 归入本层）
- 本层用例：后端 42（33 既有 + 9 新写）+ Web vitest 19 + 小程序 vitest 13 = 74。
- total = pass + fail + skip + blocked + not_testable = 74 = 74 + 0 + 0 + 0 + 0。
- 通过率 = pass/(pass+fail+blocked) = 74/(74+0+0) = 100.00%。
- 判定模式与阈值：FULL_FLOW threshold，unit_pass = 0.80。
- **本层门控：PASSED**（100.00% ≥ 80%）。

## 执行输出

```
$ (cd backend && python manage.py test tests.unit --settings=config.test_settings)
..........................................
Ran 42 tests in 0.368s
OK
```

vitest 的单元层文件按文件名拆分，全量 `npx vitest run` 的计数在集成报告中给出（Web：3 个文件 33 passed；小程序：3 个文件 27 passed）。本层引用的文件：Web `api.spec.js`（11）、`auth.store.spec.js`（8）；小程序 `api.spec.js`（11）、`store.spec.js`（2）。

## 分项结果

| 模块 | TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|---|
| core 规则（test_core_rules.py） | TC-UNIT-001~014 | AC-049/061/033/009/032/040 | 金额、脱敏、密码规则、月份计算、限流（14） | PASS（14） | — | — |
| 领域规则（test_domain_rules.py） | TC-UNIT-015~033 | AC-049/059/055/057/046/065/039/027 | 报销金额、收入解析、投票题目/结果、决议判定、席位、户主晋升（19，含已更新的 TC-UNIT-021） | PASS（19） | — | — |
| 领域规则（新写） | TC-UNIT-034、035 | AC-059-02、AC-059-05 | 文件内重复行跳过并带行号；全部行错误不抛错、有效记录为 0 | PASS（2） | — | — |
| 报表生成（test_rework_rules.py） | TC-UNIT-037~039 | AC-061-01/02 | generate_due 上季/上年生成且幂等；一季度取上年 Q4；账目变化只重算过期周期 | PASS（3） | — | — |
| 配置（test_rework_rules.py） | TC-UNIT-040~043 | CR-024 | 缺失/空 DJANGO_SECRET_KEY 拒绝启动；提供密钥可启动且默认 hosts 安全；DEBUG 允许临时密钥 | PASS（4） | — | — |
| Web store（auth.store.spec.js） | TC-WEB-001~005 | US-036/041 | fetchMe、identities.labels、职位枚举（it.each）、游客、旧结构兼容、setAuth/logout | PASS（8） | — | — |
| Web api（api.spec.js） | TC-WEB-006~016 | US-012/014/049~059 | claims/polls/手机号/改密/收入表/撤销认证/附件/申诉/登录路径与字段；全量函数健全性 | PASS（11） | — | — |
| 小程序 api（api.spec.js） | TC-MP-001~011 | US-003/012/014/049~057 | 前缀与令牌、claims、polls、手机号、登录、申诉、上传、401 | PASS（11） | — | — |
| 小程序 store（store.spec.js） | TC-MP-012~013 | US-041 | fetchMe 存 identities 对象；setAuth/clear | PASS（2） | — | — |

说明：TC-UNIT-036 为 TC-UNIT-021 同一方法内的附属断言，不单独计数；表中后端 14+19+2+3+4 = 42，Web 8+11 = 19，小程序 11+2 = 13，合计 74。mock 仅打在 http 层（Web `vi.mock('@/shared/http')`，小程序 `uni.request/uploadFile` 桩），被测的 api.js 与 store 为真实代码。

## 与基线对比

基线（画像 P4）：后端单元 33/33 通过。本层既有用例 33 个：32 个未改仍通过；TC-UNIT-021（`test_row_error_ratio_over_2_percent`）按 AC-059-03 更新断言后通过（原断言与 Q93 取代的旧阈值冲突，非回归）。新增失败：0。前端与小程序无基线（此前无用例）。

## 失败汇总（需路由给开发）

无。
