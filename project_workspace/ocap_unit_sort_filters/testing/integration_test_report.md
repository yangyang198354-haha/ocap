<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T12:36:40+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>testing/unit_test_report.md</file>
    <file>architecture/module_design.md (1.0.0)</file>
    <file>development/code_review_report.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告

## 摘要

- 执行时间：2026-11-16T12:26:22+08:00（上一层门控 PASSED 后）；环境：venv Python 3.12 + Django 5.2.19，SQLite 内存库（`config.test_settings`）；真实 HTTP 客户端 + 真实认证头；管理命令用 `call_command`，文件写临时目录；不连接测试机，不跑 `backend/tests/remote`。
- 命令（仓库根，`PY=/tmp/claude-0/-root-myproject-ocap/c20123b9-4e57-4ebf-b3eb-04a35210d0d9/scratchpad/venv/bin/python`）：
  - `(cd backend && $PY manage.py test tests.integration --settings=config.test_settings)`
  - 仅新写：`(cd backend && $PY manage.py test tests.integration.test_registry_sort_options tests.integration.test_unit_sort_filters_me tests.integration.test_admin_registry_filters tests.integration.test_registry_filters_contract tests.integration.test_underground_relocation_cmd tests.integration.test_registry_export_cmd --settings=config.test_settings)`
- **total = pass + fail + skip + blocked + not_testable = 576 = 576 + 0 + 0 + 0 + 0**（既有 505 + 新写 71）
- 通过率 = pass / (pass + fail + blocked) = 576 / (576 + 0 + 0) = 1.00
- 判定模式：INCREMENTAL baseline：既有 505 条零新增失败；新写 71 条全部通过。
- 上一层（单元）门控：PASSED（195/195）。
- **本层门控：PASSED**

## 执行输出

```
$ (cd backend && $PY manage.py test tests.integration --settings=config.test_settings)
Ran 576 tests in 46.545s
OK

$ (cd backend && $PY manage.py test tests.integration.test_registry_sort_options tests.integration.test_unit_sort_filters_me tests.integration.test_admin_registry_filters tests.integration.test_registry_filters_contract tests.integration.test_underground_relocation_cmd tests.integration.test_registry_export_cmd --settings=config.test_settings)
Ran 71 tests in 1.914s
OK
```

变异验证（M-TE-012）：scratchpad 副本中把 `registry/services.py`、`identity/services.py`、`residency/housing.py` 回退到 HEAD，运行 `tests.integration.test_registry_sort_options tests.integration.test_unit_sort_filters_me tests.e2e.test_unit_sort_filters_journeys`：`Ran 24 tests … FAILED (failures=12)`（TC-INT-550、551、552、554、556、559、563、564、565、566、567、TC-E2E-510），证明新用例能抓住旧排序缺陷。仓库内产品代码未改。

## 分项结果（按集成边界）

### 边界 1：逐级选项 API ↔ 排序规则 ↔ 清册（MOD-105 ↔ MOD-104，`test_registry_sort_options.py`，14 条）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-550 | AC-183-01 | 楼栋 [1,2,10,11] | PASS | — | — |
| TC-INT-551 | AC-183-01 | “1栋/2栋/10栋”后缀写法 | PASS | — | — |
| TC-INT-552 | AC-183-02 | 单元 [1,2,10]，户号 [101,902,1001] | PASS | — | — |
| TC-INT-553 | AC-183-03 | 楼层 [-1,1,2,10] | PASS | — | — |
| TC-INT-554 | AC-183-04 | 户号 [5,A2,A10]，无丢失无重复 | PASS | — | — |
| TC-INT-555 | AC-183-05 | 车位无单元：skipped=[unit_no]，无空选项 | PASS | — | — |
| TC-INT-556 | AC-183-06 | 负二、{负一,-1}、1、2 | PASS | — | — |
| TC-INT-557 | AC-184-03、AC-185-01 | [1,10,地下车位] | PASS | — | — |
| TC-INT-558 | AC-185-03 | 无地下车位记录时不出现该项 | PASS | — | — |
| TC-INT-559 | AC-185-02、AC-186-01 | 选地下车位→跳单元→[负二,负一]→车位号，类型“车位”；1 栋下不再有负层 | PASS | — | — |
| TC-INT-560 | AC-186-02 | 手机号在清册车位名下认证 201 并出现在 /me/housing；不在清册 422 PHONE_NOT_IN_REGISTRY | PASS | — | — |
| TC-INT-561 | AC-186-03 | 改选 2 栋后下一级按 2 栋重新加载 | PASS | — | — |
| TC-INT-562 | IFC-288 | 缺上级参数/过长仍 400 INVALID_QUERY | PASS | — | — |
| TC-INT-563 | AC-184-01/02 | Web 与小程序 api.js 同路径 `/units/options`；两端级联组件源码无任何排序；新增楼栋 3 后 [2,3,10] | PASS | — | — |

### 边界 2：`/me`、`/me/housing` ↔ 排序规则 ↔ Membership（MOD-106 ↔ MOD-104，`test_unit_sort_filters_me.py`，5 条）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-564 | AC-192-01 | 认证时间与自然顺序相反，两处均 [2栋,10栋,地下车位车位] | PASS | — | — |
| TC-INT-565 | AC-192-02 | 刷新 5 次顺序与汇总身份不变 | PASS | — | — |
| TC-INT-566 | AC-192-03 | 户主 A、同住人 B：两行 [(A,HEAD),(B,RESIDENT)]，汇总“产权业主”（C-34） | PASS | — | 首轮：断言写成 HEAD，实际为 OWNER（C-34 户主不作身份文案），已修测试 |
| TC-INT-567 | AC-192-03 | 同一专有部分两条有效记录 /me/housing 两行相邻，/me 一行 | PASS | — | — |
| TC-INT-568 | AC-192-04 | 游客两处均空 | PASS | — | — |

### 边界 3：后台过滤 API ↔ 权限 ↔ 清册业主/手机号（MOD-107，`test_admin_registry_filters.py`，15 条）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-569 | AC-189-01 | building=1 精确，不含 10，count=2 | PASS | — | — |
| TC-INT-570 | AC-189-02 | 单元+户号交集；再叠加楼栋 | PASS | — | — |
| TC-INT-571 | AC-189-03 | 类型 PARKING / UNSET | PASS | — | — |
| TC-INT-572 | AC-189-04 | 姓名包含匹配 | PASS | — | — |
| TC-INT-573 | AC-189-05 | 电话“1234”命中且返回完整手机号；“9999”不命中 | PASS | — | — |
| TC-INT-574 | AC-189-06 | 无结果 200，count=0 | PASS | — | — |
| TC-INT-575 | AC-189-07 | 普通用户 403 / 匿名 401（列表与 filter-options），响应无清册数据 | PASS | — | — |
| TC-INT-576 | AC-189-08 | 空串参数等同无过滤，总数 6 | PASS | — | 首轮：测试曾传 `unit_type=""`（既有行为 400，见 test_plan O-02），已改为不传 |
| TC-INT-577 | IFC-291 | 多业主/多手机号命中，Exists 无重复行 | PASS | — | — |
| TC-INT-578 | AC-190-01/02 | q 保留并可与类型、楼栋组合 | PASS | — | — |
| TC-INT-579 | AC-190-03 | q 超 64 字符 400，文案不变 | PASS | — | — |
| TC-INT-580 | IFC-291 | building/unit_no/room >32、owner_name >64、owner_phone 非数字或 >11 位 → 400 INVALID_QUERY | PASS | — | — |
| TC-INT-581 | CR-001 | 首尾空白 strip；纯空白视为未设置；strip 后恰 32 字符不报错 | PASS | — | — |
| TC-INT-582 | AC-189-01 | 分页下 count 为过滤后总数（25，第 3 页 5 条） | PASS | — | — |
| TC-INT-583 | IFC-292 | filter-options：楼栋 [1,2,3,10,地下车位]、单元 [1,2]，无空值，无姓名/手机号 | PASS | — | — |

### 边界 4：前端 `api.js` / `AdminRegistry.vue` ↔ 后端路由与序列化（契约，`test_registry_filters_contract.py`，4 条；另现有 `test_frontend_contract.py` 路由解析 2 条自动覆盖新增路径）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-584 | AC-189 契约 | `registryUnits`、`registryFilterOptions` 为 adminHttp GET，resolve 到 `AdminUnitListView`、`AdminUnitFilterOptionsView`（未被 `<int:unit_id>` 吞掉），权限仅 `IsAdmin` | PASS | — | — |
| TC-INT-585 | AC-189-01~05 契约 | 页面传的 9 个参数名（page、page_size、q、unit_type、building、unit_no、room、owner_name、owner_phone）逐个：命中值 count=1，不匹配值 count=0（证明后端真正当作过滤条件） | PASS | — | — |
| TC-INT-586 | AC-189 契约 | 页面读取的 `data.buildings/unit_nos/results/count` 与表格列、`row.*` 均为后端真实响应键 | PASS | — | — |
| TC-INT-587 | AC-189-09 契约 | 页面不传 floor 参数；过滤区无“楼层”占位、无英文 select | PASS | — | — |
| （现有）`test_frontend_contract.py::test_web_api_routes_exist_and_support_method`、`::test_miniprogram_api_routes_exist_and_support_method` | 契约 | Web 全部调用（含新 `registryFilterOptions`）可解析且视图支持方法；小程序无变化 | PASS | — | — |

### 边界 5：管理命令 relocate_underground_parking ↔ 清册 ↔ 认证绑定 ↔ 审计（MOD-109，`test_underground_relocation_cmd.py`，17 条）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-588 | AC-188-05 | dry-run 无 INSERT/UPDATE/DELETE，库快照不变；输出计数与 old_building/floor/move 明细 | PASS | — | 首轮：move 标识写成“1负一1号”，实为“1栋负一1号”，已修测试 |
| TC-INT-589 | AC-187-06 | 输出无姓名/手机号 | PASS | — | — |
| TC-INT-590 | IFC-295 | --list-limit 越界报错；=1 只输出 1 行 move | PASS | — | — |
| TC-INT-591 | IFC-295 | 参数组合错误 → 退出码 1，库不变，无备份文件 | PASS | — | — |
| TC-INT-592 | AC-188-01/02 | apply：总数不变，被识别 3 条楼栋=地下车位，其余 0 改动；业主/手机号/有效绑定数不变；绑定仍指向同一记录，名称为新名称；输出 before/after 计数 | PASS | — | — |
| TC-INT-593 | AC-188-06 | 备份 0600、JSONL、records=3、末行 sha256；不含姓名/手机号 | PASS | — | — |
| TC-INT-594 | IFC-294 | 同事务 1 条 SYSTEM 审计 REGISTRY_UNIT_CHANGED，detail 仅 change/moved | PASS | — | — |
| TC-INT-595 | IFC-295 | --expect-changes 不符 → 退出码 2，库不变，无备份 | PASS | — | — |
| TC-INT-596 | IFC-295 | 备份已存在 / 父目录不存在 → 退出码 3，原文件不变 | PASS | — | — |
| TC-INT-597 | AC-188-04 | 再次 apply（expect 0）→ moved=0，快照不变，不生成备份；dry-run 显示 already_target=3 | PASS | — | — |
| TC-INT-598 | AC-188-03 | 冲突：退出码 2，整批停止，库逐记录不变，输出冲突清单；dry-run 有冲突同样先报告再 2 | PASS | — | — |
| TC-INT-599 | CR-003 | 已在目标楼栋的无关负层车位不阻断 apply | PASS | — | — |
| TC-INT-600 | OQ-02 | 非 1/1栋 楼栋被改记录计数；B1 列为 unrecognized 且不被改 | PASS | — | — |
| TC-INT-601 | AC-188-06 | --restore 只读：differences=3，库不变 | PASS | — | — |
| TC-INT-602 | AC-188-06 | --restore --apply：与修正前逐记录一致（含 updated_at），differences=0，计数不变 | PASS | — | — |
| TC-INT-603 | IFC-294 | 已还原后再还原 → 退出码 2，库不变 | PASS | — | — |
| TC-INT-604 | IFC-295 | 备份缺失/篡改/非备份格式 → 退出码 3，库不变 | PASS | — | — |

### 边界 6：管理命令 export_registry_import_file ↔ 清册 ↔ 导入引擎预检（MOD-110，`test_registry_export_cmd.py`，16 条）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-605 | AC-187-01 | 表头=模板 8 列；负层车位楼栋=地下车位；其余行逐格等于库内值；relocated_units=3 | PASS | — | 首轮：测试数据楼层写 “-2”，被导入校验拒绝（见 test_plan O-01），改为“负二”并另设 TC-INT-620 |
| TC-INT-606 | AC-187-02/03/05 | 文件与库计数差 0；预检失败 0；修正前新增专有部分 3、业主 3、手机号 3、更新 0；回读不一致 0 | PASS | — | — |
| TC-INT-607 | AC-187-05 | 修正后导出：新增专有部分/业主/手机号=0、更新=0；与修正前文件字节相同 | PASS | — | — |
| TC-INT-608 | AC-187-02 | 导出期间无写 SQL；库计数、审计数、记录内容不变 | PASS | — | — |
| TC-INT-609 | AC-187-04 | xlsx 与 csv：“01”“08”“0801”“13800000000;13800000001” 原样，回读不一致 0 | PASS | — | — |
| TC-INT-610 | AC-187-06 | stdout 无姓名与手机号 | PASS | — | — |
| TC-INT-611 | AC-187-06 | 输出只在临时目录，无 .part 残留，仓库根无导出文件，权限 0600 | PASS | — | — |
| TC-INT-612 | AC-187-01/02 | 无具名业主的专有部分 → 退出码 2，不落盘，输出 gap_unit id | PASS | — | — |
| TC-INT-613 | IFC-296 | 业主 name 为空计入 gaps_unnamed_owners，退出码 2 | PASS | — | — |
| TC-INT-614 | CR-004 | --allow-gaps：文件仍生成，diff_units=-1 只报告，预检失败 0 | PASS | — | — |
| TC-INT-615 | AC-187-01 | 冲突：退出码 2，不落盘，输出冲突清单 | PASS | — | — |
| TC-INT-616 | IFC-297 | 缺 --output / 扩展名非法 / 父目录不存在 → 1；目标已存在无 --overwrite → 3 且原文件不变；加 --overwrite 才覆盖 | PASS | — | — |
| TC-INT-617 | AC-187-08 | 自检不通过 → 退出码 2，不落盘 | PASS | — | — |
| TC-INT-618 | AC-187-08 | os.replace 失败 → 退出码 3，.part 清除，已有文件保持原样，库无写入 | PASS | — | — |
| TC-INT-619 | AC-187-08 | 读取清册中途失败 → 异常，无文件无 .part，库无写入 | PASS | — | — |
| TC-INT-620 | AC-187-03/08 | 库内楼层含“-”被导入校验拒绝 → 自检 rows_failed=1，退出码 2，不落盘 | PASS | — | — |

## 与基线对比（baseline 模式）

| 项 | 基线（PM 实跑，开发后） | 本次 | 差异 |
|---|---|---|---|
| `tests.integration` 既有用例 | 505 通过（723 − 162 − 50 − 6） | 505 通过（576 − 新写 71） | 新增失败 0 |
| 失败清单 | 无 | 无 | 既有 0 / 新增 0 |

## 失败汇总（需路由给开发）

无。产品缺陷 0 条（观察项 O-01、O-02 见 test_plan，非缺陷）。
