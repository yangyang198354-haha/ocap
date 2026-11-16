<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-16T11:47:39+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：逐级选房排序统一、地下车位归属修正与后台清册过滤器（INCREMENTAL）

> 编号：已 grep 全部 `project_workspace/*/architecture/`，当前最大 ADR-096、MOD-103、IFC-284；本批 **ADR-097~105、MOD-104~110、IFC-285~298**。
> 路径相对仓库根；后端前缀 `backend/apps/`；HTTP 路径省略前缀 `/api/v1`。

## 架构概览

本批不引入新服务、新依赖、新表，也不产生迁移。改动落在三条线上：

1. **排序口径**：新增一个纯函数模块 `registry/ordering.py`（MOD-104）作为"数字自然顺序"的唯一定义，被四个出口复用：逐级选项四级（`registry/services.py:38-83`）、`/me` 已认证房屋（`identity/services.py:48`）、`/me/housing` 列表（`residency/housing.py:41`）、后台楼栋/单元下拉（新接口）。两个客户端（Web `UnitCascader.vue`、小程序 `UnitPicker.vue`）只渲染服务端返回的顺序，无任何客户端排序（已 `grep "\.sort(\|sorted(" frontend/src/portal miniprogram/pages miniprogram/components miniprogram/utils` 核实无结果），因此"两端一致"由服务端单点保证（REQ-FUNC-175）。
2. **后台清册过滤**：在 `AdminUnitListView.get`（`registry/views.py:74`）上扩展查询参数，新增一个只读下拉取值接口；前端 `AdminRegistry.vue` 加控件并同步 `frontend/src/shared/api.js`（画像 P6）。
3. **两项测试环境数据操作**（AUTH-01 只读导出、AUTH-02 原地更新）：各做成一个 Django management command（沿用 `registry_specific_part_preview` 的先例，`registry/management/commands/registry_specific_part_preview.py`），**不是迁移、不是 HTTP 接口、不在任何部署脚本里**，两者互不调用、可单独授权；共享的只有纯规则模块 `registry/underground.py`。

关键质量属性：

| 质量属性 | 来源 | 落点 |
|---|---|---|
| 顺序一致、可预测 | REQ-FUNC-173/174/175/184 | ADR-097、ADR-098、ADR-104 |
| 数据修正可核对、可还原、幂等 | REQ-NFUNC-032、AC-188-01~06 | ADR-101、ADR-102 |
| 个人信息不外泄 | C-55、REQ-NFUNC-012/033 | ADR-103（导出只在测试机内生成、0600、日志只写计数）、ADR-100（鉴权沿用 `IsAdmin`） |
| 不破坏既有契约 | 画像 P5/P6（前后端契约） | ADR-100、`test_frontend_contract.py:30-97` |

沿用的既有决策（Status: Accepted，本批不改动）：

| 既有决策 | 本批如何依赖 | 出处 |
|---|---|---|
| ADR-064 专有部分标识由 `build_specific_part` 单点生成 | 楼栋改为"地下车位"后标识自动重算；纯函数用于预演冲突 | `registry/models.py:47-56,77-79` |
| ADR-066 标识重算迁移冻结规则、冲突整批停止 | AUTH-02 的"冲突整批停止"沿用同一思路，但**不**用迁移承载（见 ADR-101） | `registry/migrations/0005_regenerate_specific_part.py:104-122` |
| 导入引擎 `read_rows` / `plan_import`（只读计划、预检不改清册） | AUTH-01 导出后用它自检（AC-187-03） | `registry/importing.py:236,395` |

## 部署视图

仅使用画像 P7 中存在的环境：**测试**（树莓派；gunicorn `ocap-backend` + nginx 站点 `ocap`，MySQL 库 `ocap`）。无生产环境。

| 组件 | 运行单元（P7） | 环境 | 说明 |
|---|---|---|---|
| 排序、过滤的后端代码（MOD-104~107） | `ocap-backend`（gunicorn 127.0.0.1:9000） | 测试 | 随常规部署整包 tar→scp→解包→重启；**无迁移** |
| 后台清册页过滤器（MOD-108） | Web 静态产物 `/home/yangyang/ocap/web` | 测试 | `npm run build -- --base=/ocap/` 重新构建替换 |
| 小程序 | 无代码改动 | — | 只消费服务端新顺序；不需重新构建（见 module_design MOD 总览备注） |
| AUTH-02 命令（MOD-109） | 目标机 `backend/` 目录下用 venv 执行 `manage.py`（一次性进程，不是常驻单元） | 测试 | 须用户当轮单独授权；备份文件写目标机 `/home/yangyang/ocap/snapshots/`（P7 已有该目录）一类的目标机本地路径 |
| AUTH-01 命令（MOD-110） | 同上 | 测试 | 须用户当轮单独授权；文件在目标机生成，由主会话取回到仓库根（Q-SF-13=B），取回与是否提交不属于本设计 |
| 部署脚本 / systemd / nginx | 不改 | — | 两条命令**不得**加入 `ocap-deploy` skill 的任何自动步骤（该 skill 每次部署都会执行 `manage.py migrate --noinput`，`.claude/skills/ocap-deploy/SKILL.md:149`） |

建议的人工顺序（供 PM/E 阶段参考，非强制）：部署新代码 → AUTH-02 dry-run → 用户确认冲突/数量 → AUTH-02 apply → AUTH-01 导出。两条命令对任一先后顺序都成立（导出对"已改/未改"两种库状态都能生成同一份文件，见 ADR-103）。

## ADR

### ADR-097: "数字自然顺序"的实现位置与方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-173/175/184 要求楼栋、单元、楼层、户号四级与两处"已认证房屋"列表使用同一排序口径；现状是楼栋 `sorted(set(...))` 文本序（`registry/services.py:51-52`）、单元文本序（:57-59）、户号 `order_by("room")` 文本序（:68）、楼层有独立的 `_floor_sort_key`（:9-19，只认"负/-"加阿拉伯数字），`/me` 按 `specific_part` 文本序（`identity/services.py:48`），`/me/housing` 按认证时间（`residency/housing.py:41`）。生产为 MySQL、测试为 SQLite（画像 P1），两者对 `CAST`/`REGEXP`/排序规则的行为不同。
- Options:
  - A 新增纯 Python 模块 `registry/ordering.py`，提供 `natural_key()`；各出口取出行后在内存中用同一个 key 排序。优：一处定义；MySQL/SQLite 行为一致，单元测试不依赖数据库；可支持"负一"中文数字与"地下车位"分层。缺：选项取值集合需整体读入内存（清册量级为千行级、上限 `MAX_DATA_ROWS=20000`，`import_spec.py:14`，可接受）；不能用 SQL 分页（这几处本就不分页）。
  - B 数据库侧排序：加排序辅助列（如存数值化的 `building_sort`）或用 `CAST`/`REGEXP`。优：可 SQL 分页。缺：需要迁移与回填（本批要求无迁移）；MySQL/SQLite 函数差异导致测试与生产行为可能分叉；中文数字无法在 SQL 里便宜地解析。
  - C 客户端排序（Web 与小程序各自实现）。优：服务端不动。缺：两端各写一份，"两端一致"（REQ-FUNC-175）只能靠测试守护；`/me` 与 `/me/housing` 之外的消费者（后续新页面）每次都要重做。
- Decision: 选 A。所有排序出口只依赖 `registry/ordering.py` 的 `natural_key` / `unit_sort_key`（REQ-FUNC-173/175/184）。`_floor_sort_key` 删除（`git grep` 确认仅 `registry/services.py` 引用，测试不直接导入）。
- Consequences: 正向：口径单点、可被纯单元测试穷举；客户端零改动。负向：选项取值要整体读入内存再排序（`options()` 现状已是 `set(values_list(...))`，不新增查询）；排序规则以后要改只能改这一个文件，需要用测试守住"四个出口同序"（见 module_design 测试规划）。

### ADR-098: 自然顺序的比较规则
- Status: Proposed
- Type: constraint-driven
- Context: 规则由用户答复固定：Q-SF-03=A（纯数字按数值在前、含文字的在后、文字内数字段按数值）、Q-SF-04=A（"负一/负二"等中文数字与"-1/负1"等价）、Q-SF-11=A（"地下车位"排在所有编号楼栋之后）；楼层现行"非数字排在数字之后"（`services.py:9-19`）需保持不退化（AC-183-03）。导入后楼栋/单元/楼层/户号可能带后缀（`build_specific_part` 对已带"栋/单元/层/号"的值原样保留，`registry/models.py:23-31`），所以库里可能出现 "1栋" 与 "1" 并存的写法（Q-SF-02b 待数据核对）。
- Options（被排除的替代方案与约束来源）:
  - 纯字符串自然排序（只把数字段当数值）：不满足 Q-SF-04（"负一"无法与 -1 等价、负层不排在正层前）。
  - 把"负一"在入库时规范化为 "-1"：需要改数据与导入规则，超出本批范围（REQ-FUNC-178/179 只改楼栋），且 Q-SF-02b 尚未核对实际写法。
  - 只对"地下车位"硬编码到列表末尾而不做分层：对 `/me` 的多级排序无法复用。
- Decision: 分层比较键，层级由小到大：`-1` 空值（排最前，对应 `has_empty` 的"未划分"项位置）；`0` 整数（可带 `负` 或 `-` 符号；数字为阿拉伯数字或中文数字零〇一二两三…九十九；先去掉该层级的可选后缀：楼栋"栋"、单元"单元"、楼层"层"、户号"号"）按数值升序；`1` 其他文字——拆成"连续数字段 / 非数字段"，数字段按数值比较、非数字段按 Unicode 码位比较；`2` 保留名——仅楼栋层级的字符串 "地下车位"，恒排在其余楼栋之后。相同层级相同数值时用原字符串码位序作确定性并列规则（因此 "-1" 与 "负一" 数值相等、相邻出现，二者都保留，不合并、不丢失，AC-183-06）。
- Consequences: 正向：满足 AC-183-01~06、AC-184-03、AC-192-01；"1栋"与"1"同为数值 1，不会因后缀写法不一致被拆到两处。负向：不识别 `B1`、`地下1层` 这类写法（会落入"其他文字"层，排在数字之后）；"-1"与"负一"若在库中并存，用户在下拉里会看到两个相邻项（不做合并，属数据问题，见开放问题 OQ-02）；超过 99 的中文数字不解析、按文字处理。

### ADR-099: 地下车位在逐级选项中的呈现方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-176/177 要求第一级出现"地下车位"、选后下一级为负层、再选车位号；Q-SF-02=A 楼栋取值"地下车位"；REQ-FUNC-178/179 要求导入文件与数据库同步把数据改归属。现有机制已支持空单元自动跳过（`options()` 的 `skipped`，`registry/services.py:56-66`），客户端按 `skipped`/`has_empty` 驱动（`UnitCascader.vue:applyLevel`）。
- Options:
  - A 数据层归属：把类型为车位且楼层为负层的记录的 `building` 改为 "地下车位"（单元本就为空），逐级选项服务**不写任何特例**——"地下车位"就是一个普通楼栋值，仅在排序层给保留名分层（ADR-098）。优：数据、导入文件、标识三者同源；选项与认证流程零特例；清册无此类记录时选项自然不出现（AC-185-03）；两个客户端零改动。缺：必须改数据（本来就是需求）；标识 `specific_part` 随之重算（`build_specific_part("地下车位", "", "负一", "001")` 得 "地下车位负一层001号"，"地下车位"非纯数字不补"栋"，`models.py:23-31`），与既有记录可能冲突，需预演（ADR-102）。
  - B 虚拟入口：数据不动，`options()` 在第一级额外拼出一个"地下车位"项，选中后把"任意楼栋下的负层车位"聚合为楼层与车位号两级。优：不改数据。缺：违背 Q-SF-02=A 与 REQ-FUNC-178/179（要求改数据与导入文件）；聚合后"选哪一栋下的车位"信息丢失，认证后 `/me` 显示的标识仍是"1栋…"，与选择入口不一致；`options()` 需新增参数与特例，Web 与小程序都要处理新响应形态（`level` 之外的新模式）。
- Decision: 选 A（REQ-FUNC-176/177/178/179）。`options()` 保持现有响应结构 `{level, skipped, has_empty, options}` 与 `IFC-152` 契约不变，只改排序（IFC-288）。用户选 "地下车位" 后：单元级候选全空 → `skipped=["unit_no"]`，第二级返回负层（负二在前、负一其后，ADR-098），第三级为 `level="room"`。
- Consequences: 正向：客户端与接口契约零变化，AC-185/186 由既有机制加新数据直接满足；"地下车位"之外的任何楼栋行为不变。负向：功能是否生效取决于数据是否已修正——AUTH-02 未执行前，用户端看不到"地下车位"入口（AC-185-03 的合理表现，需在交付说明里写明上线顺序）；`building == "地下车位"` 这一字面值成为跨模块契约，集中定义在 `registry/ordering.py:UNDERGROUND_BUILDING`，不得在别处写字面量。

### ADR-100: 后台清册过滤的接口扩展方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-180/181/182/183、REQ-NFUNC-033、Q-SF-14=A。现状：`AdminUnitListView.get` 只支持 `q`（`specific_part` 包含）与 `unit_type`（`registry/views.py:74-90`），`IsAdmin` 鉴权；`page_response` 按 `page`/`page_size`（上限 100）分页（`core/serializers.py:4-13`）。前后端契约守护测试只认 `http.`/`adminHttp.` + 字面量路径、不带 `?`（`backend/tests/integration/test_frontend_contract.py:30-97`）。
- Options:
  - A 在现有 `GET /admin/registry/units` 上新增查询参数 `building`、`unit_no`、`room`、`owner_name`、`owner_phone`（与 `q`、`unit_type` 同时生效，AND），另加只读接口 `GET /admin/registry/units/filter-options` 返回楼栋、单元的现有取值（自然顺序）。业主条件用 `Exists` 子查询，不 JOIN，因此不需要 `distinct()`，分页计数准确。优：沿用同一鉴权、分页、序列化器；契约增量最小；前端只改一处调用。缺：多一个接口；`icontains` 在姓名/手机号列上不走索引（清册千行级可接受，REQ-NFUNC 未设性能指标，Q-SF-12=A）。
  - B 前端拉全量后本地过滤。优：后端不动。缺：分页与总数不再由服务端给出（违反 AC-189-01 "分页总数等于符合条数"）；一次拉取全部姓名手机号扩大暴露面（REQ-NFUNC-012/033）。
  - C 引入 django-filter。优：声明式。缺：新增第三方依赖（本批要求尽量不新增），为 5 个参数不值得。
- Decision: 选 A。语义（REQ-FUNC-182，Q-SF-09=A）：楼栋、单元、户号、类型精确匹配；姓名按 `icontains`，手机号按 `contains`（仅数字、1~11 位）；各参数缺省或空串表示不限制；姓名条件与手机号条件各自独立成立（取单位交集，不要求同一位业主同时满足）；`q` 行为不变（AC-190-01~03）。校验：`building`/`unit_no`/`room` ≤32 字符，`owner_name` ≤64，`owner_phone` 须匹配 `^\d{1,11}$`，违者 `400 INVALID_QUERY`；鉴权 `IsAdmin`（非管理员 403、未登录 401，REQ-NFUNC-033）。`filter-options` 同样 `IsAdmin`，不接受任何参数。
- Consequences: 正向：兼容既有调用（旧参数集合行为不变）；契约测试可自动覆盖新路径（字面量、`IsAdmin`）。负向：精确匹配走 MySQL 默认不区分大小写/尾空格的排序规则，"A"与"a"会被视为相同（楼栋多为数字，影响可忽略）；单元下拉取全清册去重值而非随所选楼栋级联收窄（Q-SF-14=A 只要求"取现有值"），未选楼栋时单元里可能出现该楼栋不存在的值，选出空结果属正常（AC-189-06 的空状态覆盖）。

### ADR-101: 两项测试环境数据操作的承载方式与独立授权
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-178/179、REQ-NFUNC-032、C-51/C-55/C-56、GR-A-002 条件：AUTH-01（只读导出）与 AUTH-02（原地更新）必须是两个独立、可单独授权的操作，且都不得在常规部署中自动执行；AUTH-02 要有 dry-run、修正前备份、冲突整批停止、幂等、前后计数核对。部署流程每次都执行 `manage.py migrate --noinput`（`.claude/skills/ocap-deploy/SKILL.md:149`），迁移因此会在每个环境自动执行。画像 P8：测试不得连接测试机数据库，故实现必须能在 SQLite 测试库下用合成数据验证。
- Options:
  - A 两个独立的 management command：`export_registry_import_file`（AUTH-01）、`relocate_underground_parking`（AUTH-02），位于 `registry/management/commands/`；彼此不互相调用；规则代码放在纯模块 `registry/underground.py` 供两者读取。优：不被部署流程自动触发；可用 `call_command` 在 SQLite 测试库里测；参数可强制 dry-run 默认与备份/数量确认；有先例（`registry_specific_part_preview`，`registry/management/commands/registry_specific_part_preview.py`）。缺：需要人在目标机手动执行（这正是"另行授权"所要求的）。
  - B Django 数据迁移（类似 0005 的 `RunPython`，`registry/migrations/0005_regenerate_specific_part.py`）。优：随部署自动一致。缺：违反"不得自动执行"——`migrate` 一跑就会改数据；不能携带 dry-run/备份参数；测试环境 `MIGRATION_MODULES` 置空，迁移不被测试跑到（画像 P4），行为只能靠直接调函数验证；只读导出更不可能是迁移。
  - C 手写 SQL / 目标机临时脚本。优：简单。缺：不在仓库、不可测、无 dry-run 与计数核对的统一实现，容易漏掉标识冲突。
  - D 管理端 HTTP 接口。优：有 UI。缺：把一次性的破坏性操作和个人信息导出做成常驻、可被误点的网络入口，扩大攻击面与误操作面；超出需求。
- Decision: 选 A。约束落实：(1) 两个命令分别是独立文件、独立参数、独立授权，**不共享运行状态**，也不互相调用；(2) 任何 `ocap-deploy` 步骤、CI、迁移、测试默认命令都不调用它们；(3) 两个命令的写入保护各自独立（AUTH-01 全程零写；AUTH-02 默认 dry-run，写入须 `--apply` 且带 `--backup` 与 `--expect-changes`，见 ADR-102）。
- Consequences: 正向：授权边界清晰，误执行需要主动输入多个参数；单元/集成测试可覆盖全部分支。负向：需要把代码先随常规部署发到目标机才能执行（代码本身无副作用）；两条命令的执行记录只在运维日志里，不在代码仓库中（AUTH-02 在库内写一条既有动作 `REGISTRY_UNIT_CHANGED` 审计，见 ADR-102）。

### ADR-102: AUTH-02（原地更新）的安全机制
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-179、REQ-NFUNC-032、AC-188-01~06、C-52：识别规则"类型为车位且楼层为负层"（Q-SF-07=A）；只改这些记录的楼栋；记录总数、已认证绑定数不变，其余记录改动数为 0；标识冲突整批停止并上报（Q-SF-08=A）；修正前有可还原备份，还原后差异 0；重复执行无新增。`RegistryUnit.specific_part` 唯一且四元组 `(building, unit_no, floor, room)` 唯一（`registry/models.py:65,71-74`）。清册无处保存 `specific_part` 的冗余副本（已 `git grep specific_part -- apps` 核实，其余 app 都实时读取 `unit.specific_part`），故只改 `building` 与 `specific_part` 两列即可，已认证绑定（`Membership.unit_id`）不受影响（C-52）。
- Options:
  - A 命令内置：`plan_relocation`（纯函数，预演最终状态下的两类唯一冲突）→ 默认 dry-run → `--apply` 时先把受影响记录写成**无个人信息**的 JSONL 备份文件并回读校验 → 单个 `transaction.atomic()` 内用 `QuerySet.update` 逐行带旧值条件更新 → 事务内核对前后计数与"未受影响记录指纹" → 任何不符回滚；另提供 `--restore` 按备份还原。优：备份与还原由同一份代码实现、可在 SQLite 下证明"还原后差异 0"；备份不含姓名手机号，可留在目标机；冲突在写入前就停。缺：备份格式要自己维护。
  - B 只依赖 mysqldump 备份。优：整库级。缺：不可在测试中验证"还原差异 0"；要求执行者另有数据库客户端权限与口令操作；dump 含全部姓名手机号，管理更重。
  - C 影子表（新增备份表）。优：库内可查。缺：需要新迁移与新表，违背"本批无迁移"；备份表同样要处理个人信息。
- Decision: 选 A，细则：
  1. **默认只读**：无 `--apply` 时只打印计划（计数、冲突清单、旧楼栋/楼层写法分布、前后标识示例），退出码反映是否有冲突，不创建任何文件。
  2. **识别**：`类型 == PARKING` 且 `楼层` 经 `parse_integer_text(floor, "层") < 0`（支持 "-1"、"负1"、"负一"、"负一层"，ADR-098）。已在 "地下车位" 下的记录计入 `already_target`，不重复修改（幂等）。
  3. **冲突预演**：按"最终状态"（被改记录用新值、其余用旧值）检查两类唯一性——`specific_part` 的 `casefold()` 重复、四元组重复；任一冲突 → 整批不改、列出冲突涉及的记录 id 与新标识（AC-188-03）。因为冲突检查基于最终状态且冲突即整批停止，更新不需要占位值两步法（不会出现"新值等于另一待改记录的旧值"，这种情形只可能是该记录自己已在 "地下车位" 下，会被计入冲突）。
  4. **备份**：`--backup PATH`（必填于 apply，路径必须不存在，`O_EXCL`、权限 0600）写 JSONL：头部含时间、各计数（专有部分、业主、手机号、有效认证绑定数）与记录数；每条记录含受影响记录的完整列（id、四级取值、标识、类型、面积、创建/更新时间）；末行为内容 SHA-256。写完后回读校验行数与摘要，失败则停止、不触库。备份**不含**业主姓名与手机号。
  5. **写入**：`--expect-changes N` 必填，须等于 dry-run 给出的待改数量（防止对着过期计划执行）；事务内先 `select_for_update` 锁住候选行并重算计划，数量或 id 集合与备份不一致即中止；更新用 `QuerySet.update`（带旧 `building` 条件，必须恰好影响 1 行），`updated_at` 显式写当前时间；同事务内写一条既有动作 `REGISTRY_UNIT_CHANGED` 的审计（`detail={"change":"underground_relocation","moved":N}`，不含个人信息，`core/audit.py:11-15` 已含该动作，无需改白名单）。
  6. **核对**：事务提交前重新统计并要求——专有部分总数、业主数、手机号数、有效认证绑定数与修正前相等；被改记录的 `building` 均为 "地下车位"；除被改记录外所有记录的内容指纹（id、四级取值、标识、类型、面积）与修正前相等（AC-188-01）；任一不符抛错使整个事务回滚。
  7. **还原**：`--restore PATH` 同样默认 dry-run，`--apply` 才写；先校验备份摘要，再把备份中每条记录的全部列（含 `updated_at`）原值写回，事务内核对计数与"逐记录与备份一致，差异 0"（AC-188-06）。
- Consequences: 正向：满足 AC-188-01~06 与 REQ-NFUNC-032；dry-run 同时承担 Q-SF-02b 的数据核对（旧楼栋写法、负层写法分布、负层但非车位的记录数）。负向：备份只保存被改记录，不能还原"事后又被别人改过的记录"（还原前校验这些记录当前状态仍是修正后的值，否则列出并中止）；执行与回滚期间若有并发导入，写入时唯一约束报错会使整个事务回滚（视为整批停止，需重新 dry-run）；`QuerySet.update` 绕过 `save()`，故标识由 `build_specific_part` 在内存中预先计算并显式写入——同一函数负责 dry-run 与写入，避免两处口径分叉。

### ADR-103: AUTH-01（只读导出）的生成方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-178、REQ-NFUNC-032（导出计数与库逐项相等）、AC-187-01~08、C-51/C-55/C-56、Q-SF-01=B（原文件在服务器上不存在；导入接口只在内存读取，不落盘，`registry/views.py:284-306`）、Q-SF-13=B（文件放仓库根；是否提交由用户另定，设计不含 git 操作）。导入模板列固定 8 列（`registry/import_spec.py:27-36`），多位业主分多行，同一业主多个手机号用英文分号（`importing.py:_parse_row` 对 `;`、`，`、换行拆分），xlsx 的编号类列需文本格式（`import_template.py:_TEXT_COLUMNS`）。
- Options:
  - A management command `export_registry_import_file`：服务端用 ORM 在一个事务快照内只读取清册，按模板列生成行，对"类型为车位且楼层为负层"的行把楼栋写为 "地下车位"，生成 xlsx/csv 字节后**用现有 `read_rows` + `plan_import`（只读）自检**，再原子写文件。优：不新增常驻接口；复用 `IMPORT_COLUMNS`/文本列格式；自检即 AC-187-03 的预检；零写库可由测试断言。缺：命令要在目标机执行（需要授权）。
  - B 新增管理端 HTTP 下载接口（导出全部清册含姓名手机号）。优：管理员可随时下载。缺：把"一次性导出个人信息"做成常驻接口，扩大暴露面，且需求不要求；与 REQ-NFUNC-012 精神相悖。
  - C 用 mysql 客户端 / 手工脚本导出 CSV 后人工改。优：无需开发。缺：不可测；csv 前导零（"0801"）与手机号易被改写（AC-187-04）；无计数核对。
- Decision: 选 A。细则：
  1. **只读**：全部读取在 `transaction.atomic()` 内完成（MySQL 默认可重复读，得到同一时点快照）；命令不调用任何写 API。测试用 `CaptureQueriesContext` 断言没有 INSERT/UPDATE/DELETE（AC-187-02、C-56）。
  2. **行生成**：每位有名业主一行；业主有多个手机号时合并为一个单元格（`;` 分隔）；楼栋/单元/楼层/户号/类型标签/面积按库内原值输出；面积为 NULL 输出空。被识别记录的楼栋输出 "地下车位"，其余行逐单元格等于库内值（AC-187-01）；对已处于 "地下车位" 的记录原样输出，因此无论 AUTH-02 是否已执行都得到同一份文件。
  3. **无法表达的记录**：导入模板要求每行都有业主姓名（`importing.py:_parse_row`）。库内"没有任何有名业主的专有部分""姓名为 NULL 的遗留业主"无法放进模板行。默认遇到则**不写文件**，退出码非 0，输出各类计数与专有部分 id（不含姓名手机号）；显式 `--allow-gaps` 才继续写出文件，并在报告里列出"文件与库的计数差"（此时 AC-187-02 的"差 0"不成立，由用户决定，见 OQ-01）。
  4. **自检**：写文件前对生成的字节执行 `read_rows` → `plan_import`，要求 `errors == []`（AC-187-03）、`imported == 被改行涉及的专有部分数`、`owners_created`/`phones_created` 与之对应（AUTH-02 之后则三者皆为 0，AC-187-05）；同时用文件内容重算专有部分数、业主数、去重手机号数并与库内计数逐项比较（REQ-NFUNC-032）；文件须 ≤5 MB、≤20000 行（`import_spec.py:13-14`）。任一不符 → 不落盘并退出非 0（AC-187-08）。
  5. **落盘**：`--output PATH` 必填；路径已存在则拒绝（除非 `--overwrite`）；先写同目录 `.part` 临时文件（`O_EXCL`、权限 0600）→ `fsync` → `os.replace`；任何失败清除临时文件。建议文件名 `registry_import_underground_parking.xlsx`（仓库根，Q-SF-13=B）；xlsx 为默认格式（文本列），`.csv` 扩展名则生成带 BOM 的 csv。
  6. **输出**：标准输出与日志只含计数与专有部分 id、标识（地址类字符串），不含姓名与手机号（C-55）。
- Consequences: 正向：满足 AC-187-01~08；文件可被现有预检直接通过；与 AUTH-02 无运行时耦合。负向：导出文件本身含个人信息，只在目标机生成与（经授权）取回，文件落到仓库根后是否入库由用户另定（见 OQ-03，这与已批准需求 C-55/AC-187-06 "不得入库"字面冲突，需 PM 处理）；对"无法表达的记录"的处置依赖用户判断。

### ADR-104: 已认证房屋列表（/me 与 /me/housing）的排序统一
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-184、AC-192-01~04、基线 AC-157-01/02、ocap_product_review DEF-A（`/me` 按 `specific_part` 文本序，`identity/services.py:48`；`/me/housing` 按 `certified_at, id`，`residency/housing.py:41`）。约束来源：用户答复 Q-SF-06=A（同一口径、两处一致）；基线要求汇总身份与房屋行身份相互独立、刷新顺序不变。
- Options（被排除的替代方案）:
  - 只改 `/me`、保持 `/me/housing` 按认证时间：违背 Q-SF-06=A "两处一致"与 AC-192-01。
  - 在数据库层 `order_by`：受 ADR-097 排除（MySQL/SQLite 行为不一致、无排序列）。
  - 改 `identity_view` 的入参顺序以统一：`identity_view` 取最高身份靠 `max(...)`（`accounts/directory.py:20-33`），与入参顺序无关，但改它的入参会让汇总逻辑与排序耦合，且 `/me` 与 `/me/housing` 之外的调用方也会受影响。
- Decision: 两处在组装"房屋行"时使用同一个 `unit_sort_key(building, unit_no, floor, room, unit_id)`（IFC-286）对房屋行排序；`identity_view` 的入参保持原顺序不动；同一专有部分既是产权业主又是同住人的两条有效记录在 `/me/housing` 中仍分别列出（既有行为，`tests/integration/test_identity_display.py:118-123` 构造了此场景），排序时以 `(unit key, membership.id)` 并列处理；`/me` 仍按专有部分去重取最高角色（`identity/services.py:42-47`）。不改 `housing_view` 的 `residents` 排序（`certified_at, id`，不属于本需求）。
- Consequences: 正向：关闭 DEF-A 的排序部分；游客与无房屋时仍返回空列表（AC-192-04）；刷新顺序仅取决于清册数据，稳定。负向：`/me/housing` 的顺序不再反映认证先后，若产品后续需要"最近认证优先"需另行提出；现有测试 `test_identity_display.py:124`（期望按 `specific_part` 序）与远程用例 `backend/tests/remote/remote_cases.py:77-83` 的期望需同步复核（module_design "既有测试影响"）。

### ADR-105: 后台过滤器中文化的实现方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-183、AC-191-01~03、Q-SF-14=A。现状 `AdminRegistry.vue:9-13` 的类型 `el-select` 没有 `placeholder`，Element Plus 在控件为空值时回落到内置英文 "Select"；`frontend/src/main.js:9` 使用 `app.use(ElementPlus)`，未设置中文 locale，所以表格空状态也会出现英文 "No Data"。
- Options:
  - A 在清册页这几个控件上逐个显式设置中文 `placeholder` / `no-data-text` / `empty-text`。优：改动只在本页，不影响其他页面既有断言；满足"新增、调整的过滤器用中文"（REQ-FUNC-183）。缺：其他页面的 Element Plus 内置英文文案仍在。
  - B 全局 `app.use(ElementPlus, { locale: zhCn })`。优：一劳永逸。缺：影响全站所有页面的内置文案（日期选择、分页、空状态…），超出本批范围，可能触动其他页面已有的前端测试断言；需要新增 locale 语言包的引用与构建体积评估。
- Decision: 选 A（REQ-FUNC-183 范围限定为"本批新增与调整的过滤器"）。全局 locale 作为独立改进记入开放问题 OQ-04。
- Consequences: 正向：改动面小、可由组件级测试断言可见文字不含 "select"（大小写不敏感）。负向：站内其他页面的英文内置文案不变（本批不处理）。

## 开放问题 / ASSUMPTION

| 编号 | 问题 / 假设 | 影响与处理 |
|---|---|---|
| OQ-01 | `[ASSUMPTION]` 库内可能存在导入模板无法表达的记录：没有任何有名业主的专有部分、姓名为 NULL 的遗留业主（迁移 0003 回填产物，见 ocap_registry_import ADR-037）。设计默认遇到即停止导出（`--allow-gaps` 才继续）。真实库中是否存在，授权后由 dry-run/导出报告的计数确认 | 影响 REQ-NFUNC-032 "导出与库逐项相等（差 0）"能否达成；若存在，需用户决定是接受差异还是先补登业主姓名 |
| OQ-02 | `[ASSUMPTION]` 负层楼层写法可被 `parse_integer_text` 识别（"-1"、"负1"、"负一"、"负一层"）。`B1`、`地下1层` 等写法不识别，会被 AUTH-02 漏改。dry-run 会列出车位类记录的全部楼层写法及是否被识别（即 Q-SF-02b 的数据核对） | 授权后由 dry-run 输出确认；若出现未识别写法，回 GROUP_B 补规则再执行 apply |
| OQ-03 | **需求冲突提示**：已批准 REQ-FUNC-178、C-55、AC-187-06 要求导出文件"不得进入代码仓库"，而用户答复 Q-SF-13=B 为"放到工作区根目录，提交进 repo 跟踪"（`phase_status.md` clarifications，PM 已提示仓库为公开仓库、提交需用户当轮再确认）。本设计不含任何 git 操作，也不替用户判断；命令只把文件写到 `--output` 指定的路径，并给出建议文件名 `registry_import_underground_parking.xlsx` | 请 PM 在需求侧确认 C-55/AC-187-06 的最终口径（修订需求或由用户明确放弃该约束）后再进入 GROUP_C；GROUP_D 的 AC-187-06 用例据此调整 |
| OQ-04 | 全局 Element Plus 中文 locale 是否另立需求 | 本批不做（ADR-105） |
| OQ-05 | 是否把 dry-run（只读）与 apply 分开授权：命令层面 dry-run 与 apply 是同一命令的不同参数；建议用户授权 AUTH-02 时同时明确"允许先 dry-run" | 由 PM 在授权话术里写明；命令层有 `--apply`+`--backup`+`--expect-changes` 三重确认，不会因授权了 dry-run 就写库 |
| OQ-06 | `[ASSUMPTION]` 清册规模为千行级（`import_spec.MAX_DATA_ROWS=20000` 为上限）；排序与过滤的内存/`icontains` 开销在此量级可接受（Q-SF-12=A 不设性能指标）`[ESTIMATE]` | 无需处理；若后续规模增长，改为 SQL 侧过滤的收益有限，排序仍在内存 |
