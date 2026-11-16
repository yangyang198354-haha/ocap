<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T12:30:04+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0)</file>
    <file>requirements/user_stories.md (1.0.0)</file>
    <file>architecture/module_design.md (1.0.0)</file>
    <file>architecture/architecture_design.md (1.0.0)</file>
    <file>development/implementation_plan.md (1.0.0)</file>
    <file>development/code_review_report.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：逐级选房排序统一、地下车位归属修正与后台清册过滤器（INCREMENTAL）

## 测试策略

- **被改动**：MOD-104 自然顺序规则（`registry/ordering.py`）、MOD-105 选项排序、MOD-106 `/me` 与 `/me/housing` 排序、MOD-107 后台过滤 API 与 filter-options、MOD-108 `AdminRegistry.vue` + `api.js`、MOD-109 `relocate_underground_parking`、MOD-110 `export_registry_import_file`。
- **范围（in）**：US-183 ~ US-192 全部 AC；GR-C-001 条件（CR-001~004、契约、两条命令全路径、前端组件测试）。
- **范围（out）**：真实测试环境数据（AC-187-07、AC-188-05：未授权不连接测试机，不跑 `backend/tests/remote`，P4-1 仅部署后）；小程序无源码改动，仅跑既有 97 条回归；MySQL 下 `select_for_update` 并发保护（SQLite 忽略，列入 `[NOT_TESTABLE]`）。
- **环境**：venv Python 3.12 + Django 5.2.19（`/tmp/claude-0/-root-myproject-ocap/c20123b9-4e57-4ebf-b3eb-04a35210d0d9/scratchpad/venv/bin/python`），工作目录仓库根，子目录用 `(cd backend && …)`；后端 SQLite 内存库（`config.test_settings`，P4）；前端 vitest + jsdom，HTTP 层 mock（`tests/http.mock.js`）；备份、导出文件只写 `tempfile.TemporaryDirectory()`，不写仓库根；全部合成数据（C-55），不含真实姓名与手机号。
- **分层标记**：后端按目录（`backend/tests/{unit,integration,e2e}/`，P3）；前端按用例名前缀 TC-UNIT / TC-E2E（同一文件 `registry_filters.spec.js`，单元类 10 条、E2E 替代口径 1 条）。
- **判定模式**：INCREMENTAL baseline（P5）：每层相对基线零新增失败且新写用例全部通过才进入下一层；critical path 通过率须为 1.00，且覆盖前后端契约。基线（PM 实跑）：后端 Ran 723 OK；前端 vitest 248/248；小程序 97/97。层间门控公式见各报告。
- **critical path 口径：替代**——项目没有浏览器 E2E 框架（无 Playwright/Cypress）：后端用多步 HTTP 旅程（真实导入接口 + 管理命令 + 认证接口，TC-E2E-510~514），前端用 jsdom 挂载真实页面 + 带状态假服务端（TC-E2E-515）。
- **变异验证（M-TE-012）**：把 `services.py`、`identity/services.py`、`housing.py` 回退到 HEAD（旧排序）放进 scratchpad 副本运行新用例，12 条失败（TC-INT-550/551/552/554/556/559/563/564~567、TC-E2E-510），证明新用例能抓住排序缺陷；仓库内产品代码未被改动。

## AC 映射

级别栏：UNIT / INT / E2E；运行方式：本项目无硬件（P11-1 无），全部为 sim（真实执行，非硬件仿真），表中省略该列。“新写”= 本批新增；“现有”= 回归用的既有用例。

| AC | 用例 ID | 级别 | 现有/新写 | 位置（文件::类::方法） | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|
| AC-183-01 | TC-UNIT-613、614、TC-INT-550、551 | UNIT、INT | 新写 | `tests/unit/test_registry_ordering.py::NaturalKeyOrderTests`；`tests/integration/test_registry_sort_options.py::RegistrySortOptionsTests` | 楼栋 1/2/10/11、“1栋/2栋/10栋” | `sorted_values`；GET `/units/options` | [1,2,10,11]；[1栋,2栋,10栋] | 合成清册 |
| AC-183-02 | TC-UNIT-615、TC-INT-552 | UNIT、INT | 新写 | 同上 | 单元 1/2/10，户号 101/902/1001 | 同上 | 单元 [1,2,10]；户号 [101,902,1001] | 合成 |
| AC-183-03 | TC-UNIT-616、TC-INT-553 | UNIT、INT | 新写 | 同上 | 楼层 -1/1/2/10 | 同上 | [-1,1,2,10] | 合成 |
| AC-183-04 | TC-UNIT-612、617、TC-INT-554 | UNIT、INT | 新写 | 同上 | 户号 A2/A10/5 | 同上 | [5,A2,A10]，无丢失无重复 | 合成 |
| AC-183-05 | TC-UNIT-620、TC-INT-555 | UNIT、INT | 新写 | 同上 | 车位无单元 | GET options(building) | skipped=[unit_no]，无空选项 | 合成 |
| AC-183-06 | TC-UNIT-610、618、TC-INT-556 | UNIT、INT | 新写 | 同上 | 楼层 负二/负一/-1/1/2 | 同上 | 负二在前，负一与-1相邻，均在 1、2 之前，全部保留 | 合成 |
| AC-184-01 | TC-INT-563、TC-E2E-510 | INT、E2E | 新写 | `test_registry_sort_options.py::…::test_tc_int_563…`；`tests/e2e/test_unit_sort_filters_journeys.py::OptionsAndHousingJourney` | Web `api.js` 与小程序 `utils/api.js`、两端级联组件 | 解析两端调用与组件源码 | 同一路径 `/units/options`，组件无任何排序，顺序只来自服务端 | 仓库源码 + 合成 |
| AC-184-02 | TC-INT-563 | INT | 新写 | 同上 | 清册含 2、3、10 | GET options | [2,3,10] | 合成 |
| AC-184-03 | TC-UNIT-619、TC-INT-557 | UNIT、INT | 新写 | 同上 | 楼栋 1、10、地下车位 | GET options | [1,10,地下车位] | 合成 |
| AC-185-01 | TC-UNIT-619、TC-INT-557、TC-E2E-510 | UNIT、INT、E2E | 新写 | 同上 | 存在楼栋为地下车位的车位 | 第一级 | “地下车位”在所有编号楼栋之后 | 合成 |
| AC-185-02 | TC-INT-559、TC-E2E-510 | INT、E2E | 新写 | 同上 | 车位已改归属 | 选 1 栋逐级 | 楼层/户号不再出现负层车位 | 合成 |
| AC-185-03 | TC-INT-558 | INT | 新写 | 同上 | 无地下车位记录 | 第一级 | 不出现“地下车位” | 合成 |
| AC-186-01 | TC-INT-559、TC-E2E-510 | INT、E2E | 新写 | 同上 | 地下车位有负一/负二层车位 | 逐级 | 单元级跳过；楼层 [负二,负一]；车位号显示全部，类型“车位” | 合成 |
| AC-186-02 | TC-INT-560、TC-E2E-510、511 | INT、E2E | 新写 | 同上 | 手机号在/不在清册该车位名下 | POST `/certifications` | 201 且出现在 `/me/housing`；不在 → 422 `PHONE_NOT_IN_REGISTRY`（与普通房屋一致） | 合成 |
| AC-186-03 | TC-INT-561 | INT | 新写 | 同上 | 先选地下车位再改选 2 栋 | GET options | 按 2 栋重新加载，无负层残留 | 合成 |
| AC-187-01 | TC-UNIT-623、631、632、TC-INT-605、615、TC-E2E-513 | UNIT、INT、E2E | 新写 | `tests/unit/test_underground_rules.py`、`test_registry_export_rows.py`；`tests/integration/test_registry_export_cmd.py` | 含负层车位、其他行的合成清册 | 导出命令 | 表头=模板 8 列；负层车位楼栋=地下车位；其余行逐格等于库内值；被改行数=2/3；冲突时拒绝 | 合成 |
| AC-187-02 | TC-INT-606、608、612、614、TC-E2E-513 | INT、E2E | 新写 | 同上 | 同一时点清册 | 导出 + 计数比对 | 专有部分/业主/手机号（去重）差 0；导出前后库计数与内容不变（无写 SQL） | 合成 |
| AC-187-03 | TC-INT-606、620、TC-E2E-513 | INT、E2E | 新写 | 同上 | 生成的文件 | 现有批量导入预检 | 失败行 0；预检期间库不变；含“-”楼层 → 自检失败不落盘 | 合成 |
| AC-187-04 | TC-UNIT-631、632、TC-INT-609、TC-E2E-513 | UNIT、INT、E2E | 新写 | 同上 | 楼层/户号/手机号 “08”“0801”“13800000000” | xlsx 与 csv 生成并回读 | 逐格原样 | 合成 |
| AC-187-05 | TC-INT-606、607、TC-E2E-513 | INT、E2E | 新写 | 同上 | 库内修正前/后 | 预检 | 修正前新增专有部分=2/3（并存提示的依据）；修正后新增专有部分/业主=0、更新=0；前后文件字节相同 | 合成 |
| AC-187-06 | TC-INT-610、611 | INT | 新写 | 同上 | 导出命令 | 查输出与落盘位置 | stdout 无姓名/手机号；文件只在临时目录，仓库根无 xlsx/csv；`.gitignore` 命中由 GROUP_C 的 `git check-ignore` 证明（PM 复核） | 合成 |
| AC-187-07 | [NOT_TESTABLE: 流程性验收——本批未授权导出，未连接测试机；证据为本测试全程只用 SQLite 与 `git status` 无真实文件] | — | — | — | — | — | — | — |
| AC-187-08 | TC-INT-617、618、619 | INT | 新写 | 同上 | 自检失败 / 落盘失败 / 读取中断 | 导出命令 | 退出码 2 / 3 / 异常；无残缺文件、无 `.part`；已有同名文件保持原样；库无写入 | 合成 |
| AC-188-01 | TC-UNIT-624、625、TC-INT-592、TC-E2E-514 | UNIT、INT、E2E | 新写 | `tests/integration/test_underground_relocation_cmd.py` | 含负层车位、负层住宅、正层车位、B1 | `--apply --backup --expect-changes` | 总数不变；被识别记录楼栋=地下车位；其余记录 0 改动；业主/手机号/绑定数不变 | 合成 |
| AC-188-02 | TC-INT-592、TC-E2E-514 | INT、E2E | 新写 | 同上 | 已认证业主的车位 | apply | 绑定仍指向同一记录，名称为新名称，角色与状态不变 | 合成 |
| AC-188-03 | TC-UNIT-628~630、TC-INT-598 | UNIT、INT | 新写 | 同上 | 改后标识与既有记录冲突 | apply / dry-run | 退出码 2，整批停止，库逐记录不变，列出冲突清单 | 合成 |
| AC-188-04 | TC-UNIT-627、TC-INT-597、TC-E2E-514 | UNIT、INT、E2E | 新写 | 同上 | 已执行一次 | 再执行 | 新增 0、改动 0，不再生成备份 | 合成 |
| AC-188-05 | TC-INT-588、591、595、596 | INT | 新写 | 同上 | 无 `--apply` / 参数不全 | dry-run | 零写（无 INSERT/UPDATE/DELETE）、库快照不变；参数错误退出码 1，数量不符 2，备份已存在 3 | 合成 |
| AC-188-06 | TC-INT-593、601、602、603、604、TC-E2E-514 | INT、E2E | 新写 | 同上 | apply 前强制备份 | restore | 备份 0600、含 sha256、不含个人信息；还原后与修正前逐记录一致（含 updated_at），差异 0；篡改/缺失备份退出码 3 | 合成 |
| AC-189-01 | TC-INT-569、582、TC-UNIT-645、TC-E2E-512、515 | INT、UNIT、E2E | 新写 | `tests/integration/test_admin_registry_filters.py`；`frontend/tests/registry_filters.spec.js` | 楼栋 1 与 10 | building=1 | 仅楼栋 1（精确），count=过滤后总数 | 合成 |
| AC-189-02 | TC-INT-570、TC-UNIT-645 | INT、UNIT | 新写 | 同上 | 单元 2、户号 902 | 组合过滤 | 交集 | 合成 |
| AC-189-03 | TC-INT-571、TC-UNIT-641 | INT、UNIT | 新写 | 同上 | 类型车位/未登记 | unit_type | 只含车位 / 只含未登记 | 合成 |
| AC-189-04 | TC-INT-572、TC-E2E-515 | INT、E2E | 新写 | 同上 | 业主“张三丰” | owner_name=张三/李四 | 命中 / 不命中 | 合成 |
| AC-189-05 | TC-INT-573、577、TC-UNIT-646、TC-E2E-515 | INT、UNIT、E2E | 新写 | 同上 | 手机号 13800001234 | owner_phone=1234/9999 | 命中且返回完整手机号 / 不命中；多业主命中无重复行 | 合成 |
| AC-189-06 | TC-INT-574、TC-UNIT-642、TC-E2E-515 | INT、UNIT、E2E | 新写 | 同上 | 无同时满足的组合 | 查询 | 200、count=0、空状态“暂无数据” | 合成 |
| AC-189-07 | TC-INT-575 | INT | 新写 | 同上 | 普通用户 / 匿名 | 访问列表与 filter-options（带过滤参数） | 403 / 401，响应无清册数据 | 合成 |
| AC-189-08 | TC-INT-576、TC-UNIT-644、647、TC-E2E-512、515 | INT、UNIT、E2E | 新写 | 同上 | 清空全部条件 | 重新查询 | 总数恢复；空条件不传参 | 合成 |
| AC-189-09 | TC-UNIT-640、TC-INT-587 | UNIT、INT | 新写 | 同上 | 打开页面 | 查过滤器区域 | 占位文字恰为 6 项 + 标识搜索，无“楼层” | — |
| AC-190-01 | TC-INT-578、TC-E2E-512 | INT、E2E | 新写 | 同上 | 标识含“902” | q=902 | 命中，行为与变更前一致 | 合成 |
| AC-190-02 | TC-INT-578、TC-UNIT-645 | INT、UNIT | 新写 | 同上 | q=902 + 类型 | 组合 | 同时满足；类型不符不出现 | 合成 |
| AC-190-03 | TC-INT-579 | INT | 新写 | 同上 | q 超 64 字符 | 查询 | 400 INVALID_QUERY，文案不变 | 合成 |
| AC-191-01 | TC-UNIT-640、643、TC-E2E-515 | UNIT、E2E | 新写 | `frontend/tests/registry_filters.spec.js` | 未选任何条件 | 查看控件文字 | 全部中文，不含 select（不区分大小写） | — |
| AC-191-02 | TC-UNIT-641 | UNIT | 新写 | 同上 | 展开类型下拉 | 查看选项 | 全部类型、未登记类型、住宅、公寓、商铺、车位、其他 | — |
| AC-191-03 | TC-UNIT-642、TC-E2E-515 | UNIT、E2E | 新写 | 同上 | 结果为空 | 看表格 | “暂无数据”，无 No Data | — |
| AC-192-01 | TC-INT-564、TC-E2E-510 | INT、E2E | 新写 | `tests/integration/test_unit_sort_filters_me.py` | 认证时间与自然顺序相反（地下车位最早、2栋最晚） | GET `/me`、`/me/housing` | 两处均为 2栋、10栋、地下车位车位 | 合成 |
| AC-192-02 | TC-INT-565、TC-E2E-510 | INT、E2E | 新写 | 同上 | 同上 | 重复刷新 5 次 | 顺序与汇总身份不变；小程序/Web 同一接口（TC-INT-563） | 合成 |
| AC-192-03 | TC-INT-566、567 | INT | 新写 | 同上 | A 户主、B 同住人；同一部分两条记录 | `/me/housing`、`/me` | 仍各出一行，汇总“产权业主”（C-34），仅顺序变化 | 合成 |
| AC-192-04 | TC-INT-568 | INT | 新写 | 同上 | 游客 | 两处查询 | 空列表无报错 | 合成 |
| CR-001 | TC-INT-581 | INT | 新写 | `test_admin_registry_filters.py` | 参数带空白 | 查询 | strip 后匹配；纯空白视为未设置；strip 后才校验长度 | 合成 |
| CR-002 | TC-UNIT-640~649、TC-E2E-515 | UNIT、E2E | 新写 | `frontend/tests/registry_filters.spec.js` | — | 组件测试 | 见上 | — |
| CR-003 | TC-UNIT-629、630、TC-INT-598、599 | UNIT、INT | 新写 | `test_underground_rules.py`、`test_underground_relocation_cmd.py` | 无关重复组 / 含被改记录的重复组 | plan_relocation / 命令 | 只报告含被改记录的重复组 | 合成 |
| CR-004 | TC-INT-614 | INT | 新写 | `test_registry_export_cmd.py` | `--allow-gaps` 且有缺口 | 导出 | 文件仍生成，diff_units=-1 只报告不判失败，预检失败 0 | 合成 |
| 契约（M-PM-002） | TC-INT-584~587；现有 `test_frontend_contract.py` 2 条路由解析 | INT | 新写 + 现有 | `tests/integration/test_registry_filters_contract.py` | 解析 `api.js` 与 `AdminRegistry.vue` | resolve 路由、方法、权限；页面传的 9 个参数名逐个验证真正过滤；页面读取的响应键 ⊆ 后端响应 | 全部可解析且生效 | 合成 |
| 退出码 | TC-INT-591、595、596、598、603、604、612、613、615、616、617、618 | INT | 新写 | 两条命令测试 | 各异常场景 | call_command | 1 参数错误、2 冲突/数量不符/核对失败/自检失败、3 备份或目标文件问题 | 合成 |
| 回归（现有） | `test_identity_display.py::test_tc_int_506`、`test_frontend_contract.py`、全量 723 后端 + 248 前端 + 97 小程序 | INT 等 | 现有 | — | — | 全量回归 | 零新增失败 | — |

## 测试数据需求

- 全部为运行时合成：每个用例在 SQLite 内存库中创建专有部分/业主/手机号/认证绑定，手机号用 `tests.support.next_phone()` 或固定的 `138/139/137` 段合成号，姓名为“甲测试”等占位；不使用真实个人信息（C-55）。
- 备份/导出文件写 `tempfile.TemporaryDirectory()`，用例结束清理；不唯一化问题不适用（内存库每用例回滚）。
- `[DATA_REQUIRED]`：无。

## 不可测项

| AC | 原因 |
|---|---|
| AC-187-07 | 流程性验收（“未授权则不连接测试机、不生成真实文件”）：没有可执行的被测行为。证据：全部用例仅用 SQLite 与合成数据，`backend/tests/remote` 未运行，`git status` 无导出文件。不计入通过率分母 |
| （附带）MySQL 下 `select_for_update` 并发保护 | SQLite 忽略行锁，CR-003 已声明仅 MySQL 生效；无法在本环境测试。属开发评审中的已知限制，非 AC，不计入分母；列入人工验证清单（见 e2e_test_report） |

## 观察项（非缺陷，记录供 PM 与用户知悉）

- O-01：库内楼层若写成 `-1`/`-2`（含连字符），现有导入校验拒绝含“-”的楼层（“楼层不得含‘-’”），导出自检会 `rows_failed=1` 并以退出码 2 拒绝落盘（TC-INT-620，属保护性失败而非数据损坏）。真实清册若存在此类写法，授权导出时会被拦下，需先人工核对楼层写法（命令 dry-run 的 `floor|…|recognized/unrecognized` 清单即为此设计）。
- O-02：`unit_type=`（空串）调用后台列表仍返回 400（既有行为，前端对空值不传该参数），新增的 `building/unit_no/room/owner_*` 空串则视为未设置。未改动，不计缺陷。

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-183 | TC-UNIT-610~622、TC-INT-550~556 | UNIT、INT |
| US-184 | TC-UNIT-619、TC-INT-557、563、TC-E2E-510 | UNIT、INT、E2E |
| US-185 | TC-UNIT-619、TC-INT-557~559、TC-E2E-510 | UNIT、INT、E2E |
| US-186 | TC-INT-559~561、TC-E2E-510、511 | INT、E2E |
| US-187 | TC-UNIT-623、631、632、TC-INT-605~620、TC-E2E-513 | UNIT、INT、E2E |
| US-188 | TC-UNIT-624~630、TC-INT-588、591~604、TC-E2E-514 | UNIT、INT、E2E |
| US-189 | TC-INT-569~577、580~584、TC-UNIT-640、644~649、TC-E2E-512、515 | UNIT、INT、E2E |
| US-190 | TC-INT-578、579、TC-UNIT-645、TC-E2E-512 | UNIT、INT、E2E |
| US-191 | TC-UNIT-640~643、TC-E2E-515 | UNIT、E2E |
| US-192 | TC-INT-564~568、TC-E2E-510 | INT、E2E |
