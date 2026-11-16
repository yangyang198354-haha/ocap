<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-16T17:55:28+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：房屋选择结构整理、申诉审核增强、认证姓名核对与席位授予放宽（INCREMENTAL）

> 编号：已 grep 全部 `project_workspace/*/architecture/`，当前最大 ADR-105、MOD-110、IFC-298；本批 **ADR-106~116、MOD-111~118、IFC-299~315**。
> 路径相对仓库根；后端前缀 `backend/apps/`；HTTP 路径省略前缀 `/api/v1`。引用的现有代码均已 `git grep -n` / `sed -n` 核实。

## 架构概览

本批不新增服务、不新增第三方依赖，只有**一处迁移**（`residency.Appeal` 加一列，ADR-111）。改动落在六条线上，彼此耦合很弱：

1. **商铺归类（US-193/194/195）**：数据层把类型为商铺的 107 条记录改成楼栋 `商铺`，原楼栋/门牌写入"单元"列（ADR-106，Q-OA-27=A）；排序层把 `商铺` 作为保留楼栋名排在 `地下车位` 之后（ADR-108）；选项接口为商铺第二级附加显示名（ADR-109）。改库由独立命令 `relocate_shops` 完成（ADR-107），沿用上批 `relocate_underground_parking` 的全部安全机制，**不是迁移、不进部署流程**。
2. **导出（US-196）**：复用上批 `export_registry_import_file`，补"输出位置守卫"与"商铺未归类守卫"（ADR-110）。
3. **申诉增强（US-197/198/199）**：`Appeal.owner_name` 新列（ADR-111）；后台列表加字段与缩略图/大图（ADR-112，客户端经现有鉴权下载接口取 Blob，不新增服务端图片处理依赖）。
4. **认证姓名核对（US-200/201/202/204）**：`POST /certifications` 要求姓名并按"同一业主的姓名 + 手机号"比对，所有失败同一响应（ADR-113）；手机号注册/绑定时的自动绑定保持不变（C-61）。
5. **申诉通过追加清册（US-203）**：同事务内追加产权人与号码，失败整体回滚（ADR-114）。
6. **席位（US-205/206）**：授予校验改为"结束日 > 今天"；"在任"判定统一加"开始日 ≤ 今天"，所有调用点共用一个谓词（ADR-115）。

两端客户端（Web、小程序）同批同步契约（ADR-116，画像 P6）。

关键质量属性：

| 质量属性 | 来源 | 落点 |
|---|---|---|
| 数据修正可核对、可还原、幂等、原信息不丢 | REQ-FUNC-188、REQ-NFUNC-036 | ADR-106、ADR-107 |
| 个人信息不外泄（导出文件、核对失败响应、申诉资料） | C-59、REQ-NFUNC-034、REQ-NFUNC-037、C-63 | ADR-110、ADR-112、ADR-113 |
| 不能借认证/申诉改写他人清册或使他人自动获得身份 | C-58、C-61、REQ-FUNC-197 | ADR-113、ADR-114 |
| 两端一致、不破坏既有契约 | 画像 P5/P6、REQ-FUNC-185/187 | ADR-108、ADR-109、ADR-116 |
| 权限一致（"在任"所有判断点同口径） | REQ-FUNC-200 | ADR-115 |

沿用的既有决策（Status: Accepted，本批不改动，仅依赖）：

| 既有决策 | 本批如何依赖 | 出处 |
|---|---|---|
| ADR-064 专有部分标识由 `build_specific_part` 单点生成 | 商铺改库后标识由同一函数预演/写入 | `registry/models.py:47-56` |
| ADR-097/098 自然顺序规则单点（`registry/ordering.py`） | 在其上增加保留楼栋名层级 | `registry/ordering.py:6,68-80` |
| ADR-101/102 独立命令、默认 dry-run、`--backup`、`--expect-changes`、`--restore` | `relocate_shops` 复用其低层函数与流程 | `registry/underground.py`、`registry/management/commands/relocate_underground_parking.py` |
| ADR-103 导出命令（只读、自检、原子落盘） | 在其上加守卫 | `registry/exporting.py`、`registry/management/commands/export_registry_import_file.py` |
| ADR-082 权限与展示用同一"在任"口径 | 席位有效谓词覆盖同一批调用点 | `identity/services.py:62`（注释 ADR-082） |

## 部署视图

仅使用画像 P7 中存在的环境：**测试**（树莓派；gunicorn `ocap-backend` + nginx 站点 `ocap`，MySQL 库 `ocap`）。无生产环境。

| 组件 | 运行单元（P7） | 环境 | 说明 |
|---|---|---|---|
| 后端代码（MOD-111~116） | `ocap-backend`（gunicorn 127.0.0.1:9000） | 测试 | 整包 tar→scp→解包→`migrate --noinput`（执行 residency 0003）→重启（`.claude/skills/ocap-deploy/SKILL.md:140-149`） |
| Web 前端（MOD-117） | 静态产物 `/home/yangyang/ocap/web/ocap` | 测试 | `npm run build -- --base=/ocap/` 重新构建替换 |
| 小程序（MOD-118） | 无服务端运行单元 | — | **须重新构建并发布**（认证接口强制要求姓名，旧版本认证会得到 400，Q-OA-11=A 已接受） |
| `relocate_shops`（MOD-111） | 目标机 `backend/` 下 venv 执行 `manage.py`（一次性进程） | 测试 | 须用户当轮单独授权（C-57）；备份写 `/home/yangyang/ocap/snapshots/`（P7 已有目录，不含个人信息） |
| 导出命令（MOD-113） | 同上 | 测试 | 须用户当轮单独授权；输出到 `/home/yangyang/ocap_exports/`（见 ADR-110），**不在 `/home/yangyang/ocap/` 之内** |
| 部署脚本 / systemd / nginx | 不改 | — | 两条命令不得加入 `ocap-deploy` 的自动步骤（每次部署都会 `migrate --noinput`） |

目录核实：部署手册预检要求 `/home/yangyang/ocap` 下"仅 `backend/`、`web/`、`snapshots/`"（`SKILL.md:93`），后端解包是叠加式 `tar xzf -C backend`，回滚会 `rm -rf backend`（`SKILL.md:132,280`）。因此导出目录选部署根的**同级**目录 `/home/yangyang/ocap_exports/`：部署解包、前端 `rm -rf web/ocap/*`、回滚均不会触及它，且预检的"无未纳入快照的东西"不被破坏。目录由主会话在导出授权时用 `install -d -m 700` 创建（不属于代码）。

建议的人工顺序（供 PM/E 阶段参考）：部署新代码（含迁移）→ `relocate_shops` dry-run → 用户确认数量/冲突 → apply → 核对第一级选项 → 导出（授权）。

## ADR

### ADR-106: 商铺归类的库内承载方式与原楼栋/门牌的保存位置
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-186/187/188、REQ-NFUNC-036、Q-OA-01=A（第二级为原楼栋/门牌）、Q-OA-02=B（原地改库）、Q-OA-27=A（原楼栋/门牌写入"单元"列）。清册四级结构 `building/unit_no/floor/room` 各 `max_length=32`，`unit_no` 可空（`registry/models.py:59-63`）；标识由 `build_specific_part` 生成，纯数字段会补后缀（`models.py:23-31`），故纯数字 `unit_no` 会生成"1单元"。PM 核查：107 条商铺单元列全空（requirements_spec.md 基线表末行）。
- Options:
  - A 原地改库：`building := "商铺"`，`unit_no :=` 原楼栋/门牌；其中**纯数字楼栋补"栋"**（`"1"→"1栋"`，其余原样，如 `建设南路142号`），要求原 `unit_no` 为空。优：不改模型、不加列、无迁移；第二级由既有"逐级选项"机制天然提供（`options()` 无特例）；导出/导入文件的"单元"列自然承载（Q-OA-27=A）；补"栋"后标识为 `商铺1栋负1层1139号` 而不是 `商铺1单元负1层1139号`。缺：`unit_no` 语义变成"原楼栋/门牌"（仅对商铺）；补"栋"使 `"1"` 与 `"1栋"` 两种原写法映射到同一值（二者在同层同户号下本就会生成同一标识而无法共存，`models.py:23-31`，所以不会造成合并冲突；备份保留逐记录原值，可精确还原）。
  - B 新增列 `RegistryUnit.origin_building`（迁移回填），`unit_no` 保持空。优：语义干净。缺：需要模型与迁移（单次需授权的数据修正之外又多一项迁移回填）、`options()` 要为商铺写特例、导入模板需新增列才能无损往返（违背 Q-OA-27=A，也违背"导出文件须通过现有预检"）、`build_specific_part` 要读新列。
  - C 虚拟入口（不改库，只在选项层聚合）。被 Q-OA-02=B 排除；且与 REQ-FUNC-188 的"库内楼栋改商铺"冲突。
- Decision: 选 A（REQ-FUNC-186/187/188，Q-OA-27=A）。纯函数 `shop_unit_no(old_building) -> str`（MOD-111）：去首尾空白；纯数字（`^[0-9]+$`，与 `_PURE_NUMBER` 同口径含"负"前缀不适用于楼栋）→ 追加"栋"；已以"栋"结尾或含其他文字 → 原样；结果长度须 ≤32，否则该记录计入冲突（`too_long`）而整批不执行；原 `unit_no` 非空计入冲突（`unit_no_occupied`），整批不执行。`商铺` 字面量唯一定义在 `registry/ordering.py:SHOP_BUILDING`。id=4347（1栋负1层1139号，商铺）按同一规则处理，改后标识 `商铺1栋负1层1139号`，其认证绑定（`Membership.unit_id`）不变（REQ-FUNC-186、AC-195-06）。
- Consequences: 正向：零模型改动、零迁移；两端客户端与导入导出无需新字段；原楼栋/门牌在库内可得（`unit_no`）且备份保留逐记录原值，丢失数可核对为 0（REQ-NFUNC-036）。负向：`unit_no` 对商铺含义特殊——后台清册页单元下拉会出现约 33 个原楼栋/门牌值（ADR-100 取值来自全清册去重，已接受）；将来经批量导入新增的商铺若仍写在 1~10 栋下，会重新出现在第一级编号楼栋中，需再次运行 `relocate_shops`（幂等）或另提需求让导入自动归类（见开放问题 OQ-02）；标识显示中"1栋"出现在"商铺"之后，是预期呈现。

### ADR-107: 商铺改库命令的实现与对上批代码的复用方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-188、REQ-NFUNC-036、C-57；特别指令"复用上批 relocate 命令模式（默认 dry-run、--backup、--expect-changes、幂等、--restore），独立命令、不进部署迁移"。上批已交付 `registry/underground.py`（`UnitRow/Counts/BackupInfo/ApplyResult/RestoreResult`、`load_rows`、`read_counts`、`unaffected_fingerprint`、`write_backup`、`_read_backup`）。部署每次执行 `manage.py migrate --noinput`（`SKILL.md:149`），迁移会自动执行；测试环境 `MIGRATION_MODULES` 置空，迁移测不到（画像 P4）。
- Options:
  - A 新建 `registry/shops.py` + 命令 `relocate_shops`，复用 `underground.py` 的低层函数；对 `underground.write_backup/_read_backup/verify_backup` 只**增加带缺省值的关键字参数 `format_name`**（旧调用不变，M-SA-015）。优：上批代码行为零变化，既有测试不受影响；商铺的规则（改 `unit_no`、`unit_no_occupied` 冲突）独立；备份格式用不同 `format_name`，不会把商铺备份误还原到地下车位命令。缺：`apply`/`restore` 流程在 `shops.py` 里再写一遍（约一屏），与 `underground.py` 结构相似。
  - B 抽取通用"relocation 引擎"，`underground` 与 `shops` 都作为规则插件。优：无重复。缺：重构已交付并通过门控的代码（其 TC-INT/单元用例都针对现有函数签名），回归面大；本批没有第三种规则，抽象无复用对象。
  - C Django 数据迁移（`RunPython`）。缺：`migrate` 一跑就改数据，违反"另行授权、不得自动执行"（C-57）；不能带 dry-run/备份参数；测试环境不跑迁移。参照 ADR-101 选项 B 的同一理由，M-SA-012。
  - D 管理端 HTTP 接口。缺：把一次性破坏性操作做成常驻入口，超出需求（同 ADR-101 选项 D）。
- Decision: 选 A。细则：(1) 识别条件仅 `unit_type == "SHOP"` 且 `building != SHOP_BUILDING`（C-60：类型空/其他不动）；已在 `商铺` 下的 SHOP 记录计入 `already_target`（幂等，AC-195-04）。(2) 冲突预演按"最终状态"检查三类：标识 `casefold()` 重复、四元组重复、`unit_no_occupied`/`too_long`；任一冲突整批停止并列出（AC-195-03）。因冲突检查基于最终状态且冲突即停止，更新不需要占位值两步法（M-SA-013：被改记录的新标识都以"商铺"开头，不可能等于另一待改记录的旧标识；若等于，说明该记录已在商铺楼栋下，会被识别为冲突而不是静默覆盖）。(3) 写入用 `QuerySet.update`，条件带旧 `building` 与旧 `unit_no`，必须恰好影响 1 行；`updated_at` 显式写入；同事务写一条既有审计动作 `REGISTRY_UNIT_CHANGED`（`detail={"change":"shop_relocation","moved":N}`）。(4) 事务内核对：专有部分/业主/手机号/有效认证绑定计数前后相等，被改记录 `building == 商铺` 且 `unit_no == shop_unit_no(备份中的旧楼栋)`（原信息丢失数 = 0），未受影响记录指纹相等；任一不符回滚。(5) `--restore PATH` 校验备份摘要与 `format_name`，原值写回全部列（含 `unit_no`、`updated_at`），要求这些记录当前仍是改后状态，否则中止。(6) 备份不含姓名与手机号。
- Consequences: 正向：授权边界与上批一致；`call_command` 可在 SQLite 测试库下用合成数据覆盖全部分支；上批命令与测试零改动。负向：`shops.py` 与 `underground.py` 有结构重复（接受，见 OQ-05 的后续合并建议）；备份只含被改记录，不能还原"改后又被别人手工修改的记录"（还原前校验，不符则中止并列出）；`underground.py` 三个函数新增了可选参数，需保证默认值路径行为不变（既有 `tests/unit/test_underground_rules.py`、`tests/integration/test_underground_relocation_cmd.py` 必须仍通过）。

### ADR-108: 第一级楼栋排序：编号楼栋 → 地下车位 → 商铺 → 其他文字楼栋
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-185（第一级只出现三大类并按此顺序，三类之外的楼栋列在其后）、REQ-FUNC-187（第二级各级按数字自然顺序）、AC-193-01/04。现状 `natural_key` 对楼栋的层级是：-1 空、0 整数、1 其他文字、2 保留名"地下车位"（`registry/ordering.py:68-80`），即"其他文字楼栋"排在"地下车位"之前；与 REQ-FUNC-185 要求的"三类之后"冲突。`/me`、`/me/housing`、后台下拉、选项服务共用 `natural_key`（上批 ADR-097）。
- Options:
  - A 扩展 `natural_key` 的楼栋层级为 `0 整数 → 1 地下车位 → 2 商铺 → 3 其他文字`（仅 `level == "building"`；其他三个层级仍是 `0 整数 → 1 文字`）。保留名用有序表 `RESERVED_BUILDINGS`（名称 → 层级）。优：所有出口（选项、`/me`、`/me/housing`、后台下拉）一次到位、仍是单点；商铺第二级自动用 `unit_no` 层级的现有规则（整数 → 文字，文字内数字段按数值，`1栋`<`2栋`<`10栋`<`建设南路…`）。缺：文字楼栋与保留名的相对次序改变，上批单元测试对 `natural_key("地下车位","building")[0] == 2` 的断言需更新。
  - B 保持 `natural_key` 不变，仅在 `RegistryService.options` 第一级后处理重排。缺：`/me` 与 `/me/housing` 的房屋行顺序仍按旧规则，同一批商铺在"我的房屋"里会排在"地下车位"之前，破坏上批 ADR-104 的"两处一致、与选项一致"。
  - C 客户端重排。缺：违背上批 ADR-097 选项 C 的排除理由（两端各写一份）。
- Decision: 选 A（REQ-FUNC-185/187）。"编号楼栋"= 去后缀后可解析为整数的楼栋（不写死 1~10，将来有 11 栋仍排在 1~10 之间的数字序中）；保留名之外的文字楼栋统一排在 `商铺` 之后。`UNDERGROUND_BUILDING` 保持原常量，新增 `SHOP_BUILDING: str = "商铺"` 与 `RESERVED_BUILDINGS: dict[str, int] = {"地下车位": 1, "商铺": 2}`；`NaturalKey` 的形状不变。
- Consequences: 正向：满足 AC-193-01/04/05；`/me/housing` 中商铺房屋排在地下车位之后，与第一级顺序一致。负向：上批 `backend/tests/unit/test_registry_ordering.py:68-73,83-91`、`backend/tests/integration/test_registry_sort_options.py` 中"A区在地下车位之前"的断言须同步更新（module_design "既有测试影响"）；任何把 `natural_key(...)[0]` 当作固定层级号使用的代码（`git grep "natural_key(" -- backend/apps` 仅 `services.py`、`ordering.py` 内部使用，已核实）不受影响。

### ADR-109: 商铺第二级的显示名（"楼栋/门牌"而不是"单元"）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-187（第二级为"原楼栋/门牌"）。两端选房控件对 `unit_no` 层固定写"单元"（`frontend/src/portal/parts/UnitCascader.vue:9`、`miniprogram/components/UnitPicker.vue:7`）。数据按 ADR-106 把原楼栋放进 `unit_no`，若不改文案，用户会在"单元"下拉里看到"建设南路142号"，令人困惑。
- Options:
  - A 选项接口在 `level == "unit_no"` 且已选楼栋为 `商铺` 时返回可选字段 `level_label: "楼栋/门牌"`；两端用它覆盖该级的占位/标签（缺省仍为"单元"）。优：服务端单点决定，两端各改 2 行，向后兼容（其他楼栋响应不含该键，既有响应结构测试不受影响）。缺：响应契约增加一个可选键。
  - B 客户端写死 `picked.building === '商铺'` 时改标签。缺：保留名字面量复制到两个客户端，违背 ADR-099"字面量集中定义"。
  - C 不改文案。缺：违反 REQ-FUNC-187 的"原楼栋/门牌"表述，易误选。
- Decision: 选 A。`GET /units/options` 仅当 `level=="unit_no"` 且 `building == SHOP_BUILDING` 时增加 `level_label = "楼栋/门牌"`，其他情形**不返回该键**（保持既有响应字典不变）。
- Consequences: 正向：两端一致、字面量不外泄。负向：契约多一个可选键，客户端须容忍缺省（`data.level_label || '单元'`）；跨 `has_empty` 的"未划分单元"文案对商铺不会出现（商铺 `unit_no` 全非空）。

### ADR-110: 导出文件的位置与守卫
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-189、C-59、Q-OA-05=A（部署目录外专用目录，700/600，不入库）、Q-OA-06=A（一次性带日期快照，不自动覆盖）、特别指令"确认部署解包不会覆盖"。上批命令已满足：只读、自检、`.part`→`os.replace`、0600（`registry/exporting.py:write_export_file`）；但 `--output` 可指向任意路径，且导出可在改库前运行得到"旧结构"文件。
- Options:
  - A 扩展现有命令：新增 `--output-dir DIR`（自动命名 `registry_import_YYYYMMDD-HHMMSS.xlsx`，不覆盖），并对**所有**输出路径加位置守卫（不得位于 `settings.BASE_DIR.parent`〔部署根〕、`MEDIA_ROOT`、`STATIC_ROOT` 之内；父目录属当前用户且权限不含组/其他位 `mode & 0o077 == 0`）；新增"商铺未归类守卫"：存在类型为商铺且楼栋不是 `商铺` 的记录时退出码 2 不生成（`--allow-unrelocated` 才继续并在输出写明"旧结构"）。优：沿用已验证代码；守卫可在 SQLite 测试中用 `tempfile.mkdtemp`（天然 0700）验证；目录与权限的约束落在代码里而不是靠人记。缺：命令参数变多；位置守卫依赖 `settings.BASE_DIR`。
  - B 新建独立导出命令。缺：重复上批已通过门控的自检/落盘逻辑。
  - C 新增管理端下载接口。缺：把含姓名手机号的整份清册做成常驻可下载入口，违反 C-59 与上批 ADR-103 选项 B 的排除理由。
- Decision: 选 A。输出目录约定为 `/home/yangyang/ocap_exports/`（见部署视图的目录核实）。`--output` 与 `--output-dir` 二选一（都缺或都给 → `CommandError`，退出码 1）；守卫失败退出码 3，不触库。文件权限 0600 沿用 `write_export_file`。命令输出与日志只含计数（C-59）。
- Consequences: 正向：满足 AC-196-01~07；部署解包/回滚不会触及导出目录；误把文件写进仓库或部署目录会被命令拒绝。负向：位置守卫只能防"误写"，不能阻止有 shell 权限的人手工复制；若改库尚未授权执行，导出被守卫拦下，须用户明确放行 `--allow-unrelocated`（此时文件为旧结构，交付说明须写明）。

### ADR-111: 申诉"产权人名字"的存储
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-192、REQ-FUNC-197、Q-OA-07=A（不给用户账号加实名字段，已排除 C）、Q-OA-10=A（1~64 字，既有申诉显示"未提供"）。`Appeal` 现无此字段（`residency/models.py:31-41`）。画像 P6：迁移手写、单 app。
- Options:
  - A `Appeal.owner_name = CharField(max_length=64, blank=True, default="")`，新增手写迁移 `residency/migrations/0003_appeal_owner_name.py`（单 app，仅 `AddField`，可逆）。优：与申诉同生命周期；查询/展示/审核直接读；空串表达"未提供"，不需要为历史行回填。缺：需要一次迁移（随部署 `migrate` 自动执行，加列带缺省值，MySQL 上对千行级表代价可忽略 `[ESTIMATE]`）。
  - B 存入附件元数据或审计 `detail`。缺：列表要多表查询、不可校验长度、审核无法稳定取值。
  - C 在用户账号上加"实名"字段。需求已明确不采纳（超出范围）。
- Decision: 选 A。`null=False, blank=True, default=""`（避免 MySQL 可空列与 `pending_slot` 唯一约束的交互，且不改既有约束）；存储值为 `normalize_owner_name()` 的结果（去首尾空白、全角空格归一）。对外语义："空串 → `None`（显示"未提供"）"。
- Consequences: 正向：历史申诉无需回填；审核页与通过后追加清册读同一来源。负向：这是本批唯一迁移，须在 `data_migration` 小节列出并让 `makemigrations --check --dry-run`（画像 P4）无漂移；成员侧 `GET /appeals/mine` 的字段集合被契约测试锁定（`backend/tests/integration/test_frontend_contract.py:619`），故本批**不**向成员侧响应加 `owner_name`，只加在管理端列表。

### ADR-112: 申诉资料缩略图与大图的获取方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-190/191、REQ-NFUNC-034（仅管理员与申请人可见；缩略图、大图不得出现在公开位置；无权访问返回 401/403 且无图片字节）、C-62。现有下载接口 `GET /attachments/<uuid>/download` 要求登录（`IsMemberOrAdmin`），按 `linked_type` 策略放行（`core/attachments.py:112-132`、`residency/apps.py:23-33`），无权时 `AttachmentService.open` 抛 404（`core/attachments.py:119`）；Web 管理端已用 axios 取 Blob 再打开（`frontend/src/admin/AdminAppeals.vue:openProof`、`frontend/src/shared/api.js:179`）。`backend/requirements.txt` 无 Pillow（`git grep -n "PIL\|Pillow"` 无结果）。
- Options:
  - A 沿用现有下载接口；管理端组件按需（可视区内才请求、并发≤3）取 Blob，用 `createImageBitmap(blob, {resizeWidth})` 降采样生成缩略图后立即丢弃原 Blob，大图弹出层再取原图 Blob；pdf 显示图标，弹出层用 `<iframe>` 预览 Blob，失败则给下载入口。无权访问的响应由策略决定（见下）。优：零新依赖、零新服务端接口、鉴权单点；与现有 AdminAppeals 用法一致。缺：缩略图仍要把原图传到浏览器（单文件 ≤10MB，每条 ≤5 个），列表一页多条时带宽/内存压力大。
  - B 服务端缩略图接口（新增 Pillow 依赖 + `/attachments/<id>/thumbnail`）。优：传输小。缺：新增第三方依赖与目标机 aarch64 安装/内存风险（4GB Pi，画像 P7/Freeark 同机共存），且 pdf 仍无法出缩略图。
  - C 公开静态地址/带签名的 URL 放进 `<img src>`。违反 REQ-NFUNC-034（"不得出现在任何公开可访问的位置"）；`?token=` 类做法还会把凭据写进访问日志（通用经验）。
- Decision: 选 A。同时把无权访问的响应对齐 AC-198-04：`AppealAttachmentPolicy.can_open` 在"已登录、非管理员、非申请人本人"时抛 `ApiError("FORBIDDEN", "无权查看该资料", 403)`（响应体仅含错误 JSON）；申诉不存在仍返回 False（→404）；未登录由 `IsMemberOrAdmin` 返回 401（`core/permissions.py:36` 起，既有）。管理端列表单页最多 20 条（`usePaging` 默认，`frontend/src/shared/usePaging.js:5`），列表序列化器对附件改为按页一次批量查询（避免逐行查询）。
- Consequences: 正向：满足 REQ-NFUNC-034 与 AC-198-01~05；无新依赖。负向：缩略图带宽成本未消除（`[ESTIMATE]`：手机拍照约 1~5MB，一页最坏 20×5 个文件；已用可视区懒加载+并发上限缓解），若测试环境实测卡顿，再提 B（需要用户同意新增依赖，见 OQ-03）；`test_rework_cr011_024.py:376` 现断言"无关普通用户 404"，改为 403 须同步该用例。

### ADR-113: 认证姓名核对的服务端口径与统一失败响应
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-193/194/195/196/198、REQ-NFUNC-037、Q-OA-11=A（缺姓名一律 400，不兼容旧客户端）、Q-OA-13=A（去首尾空格、全半角空格归一后逐字相同）、Q-OA-14=A（清册姓名为空视为不一致）、Q-OA-23=A（自动绑定通路不变）、C-61。现状 `CertificationView.post`：无手机号 → 409 `PHONE_REQUIRED`，手机号不在该专有部分登记 → 422 `PHONE_NOT_IN_REGISTRY`（`residency/views.py:61-67`）；`phone_registered` 只比手机号（`registry/services.py:8-9`）。同一专有部分内手机号唯一、姓名唯一（`registry/models.py:91,103`），因此"姓名 + 手机号同一业主"在所选专有部分内最多命中 1 位业主。
- Options:
  - A 新增纯模块 `registry/ownership.py`：`normalize_owner_name()` + `owner_matches(unit_id, name, phone)`，在 **Python 内**取该专有部分下该手机号对应的业主（≤1 行）后比较归一化姓名；`CertificationView` 把所有失败（姓名不一致、手机号不一致、该专有部分无此业主、清册姓名为空、账号无手机号）合并为**同一**响应 `422 OWNER_NOT_MATCHED`，文案固定、`details={"appeal_available": true}`。优：不依赖 MySQL 排序规则（`utf8mb4` 默认大小写/尾空格不敏感的比较会让"张三 "与"张三"在 SQL 里相等，与"逐字相同"口径不一致）；统一响应天然满足 REQ-NFUNC-037；不泄露业主姓名/手机号。缺：多一次小查询。
  - B 复用旧码 `PHONE_NOT_IN_REGISTRY` 并扩展含义。缺：名字与语义不符（姓名错也叫"手机号不在清册"）；既有两端客户端按该码触发提示，旧客户端无姓名输入也会走通该提示，掩盖契约变更；新码使旧客户端明确失败（Q-OA-11=A 要求不兼容）。
  - C 在 SQL 里 `filter(owner__name=name)`。缺：同 A 的排序规则问题；全角/半角空格归一在 SQL 中难以表达。
- Decision: 选 A。流程：限频（沿用 30 次/小时，REQ-NFUNC-037）→ 校验 `unit_id`、`name`（缺失/非字符串/空白 → 400 `NAME_REQUIRED` "请输入姓名"；归一后 >64 字 → 400 `INVALID_VALUE`）→ 专有部分不存在 404 → 已是产权业主 409 `ALREADY_CERTIFIED` → `owner_matches` 为假（含账号无手机号）→ 422 `OWNER_NOT_MATCHED` → 否则 `MembershipService.certify_owner(..., "REGISTRY")`（首位认证者成为户主，沿用）。**第二套房与首次认证走同一代码路径**（REQ-FUNC-198）：现有代码从未实现"用新号码自动更新清册"，因此本批无需删除任何代码，只需测试证明"认证不写清册"。`AutoBindService.bind_by_phone`（手机号注册/绑定触发，`residency/auto_bind.py:26`；调用方 `accounts/views.py:116`、`identity/views.py:47`）**不修改**（Q-OA-23=A、C-61）。
- Consequences: 正向：REQ-NFUNC-037 由"单一错误出口"保证，而非靠多处文案一致；比较口径不受数据库排序规则影响。负向：错误码变更使以下现有测试须同步（module_design "既有测试影响"）：断言 `PHONE_NOT_IN_REGISTRY` / `PHONE_REQUIRED`（认证路径）的约 15 处与所有不带 `name` 的 `/certifications` 调用；账号无手机号的用户不再得到 409，而是 422 并走申诉；错误信息不区分原因，客户服务排查"为什么没通过"只能看审计/清册（无审计新增，REQ 未要求）。

### ADR-114: 申诉通过后追加清册的事务与冲突规则
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-197（追加不替换；同名追加号码、同号拒绝；整体回滚；无手机号只写姓名并提示）、REQ-NFUNC-035 `[INFERRED]`（审计，用户已随故事确认）、C-58、C-61、Q-OA-15/16/17/18=A。现状：`AdminAppealDecisionView.post` 在 `transaction.atomic()` 内调用 `certify_owner(..., "APPEAL")`，不触清册（`residency/views.py:152-186`）；`certify_owner` 内已对专有部分行 `select_for_update`（`residency/services.py:49`）；清册约束：`(unit, name)` 唯一、`(unit, phone)` 唯一（`registry/models.py:73,91,103`）。
- Options:
  - A 在 `registry/ownership.py` 提供 `append_owner_from_appeal(unit_id, name, phone) -> AppendResult`，由决定视图在**同一 `transaction.atomic()`** 内于 `certify_owner` 之后调用；任何 `ApiError` 使事务回滚（认证关系、清册、申诉状态均不落库）。优：REQ-FUNC-197 的"整笔回滚"由数据库事务保证；规则集中且纯 DB 层可测；审计与更新同事务。缺：`residency` 视图依赖 `registry.ownership`（方向 residency → registry，已存在先例 `residency/views.py:19-20`，无循环）。
  - B 通过后用信号/异步任务补写清册。缺：失败时认证已生效，违反"整体回滚、申诉保持待审"。
  - C 复用 `AdminUnitOwnersView.put` 的整体替换逻辑（`registry/views.py:228-272`）。缺：该接口是"替换整个业主列表"，语义与"追加"相反，直接复用会覆盖原产权人。
- Decision: 选 A。规则：先 `select_for_update` 锁该专有部分行；用归一化姓名在该专有部分的业主中找同名者（`RegistryOwner.name` 在 Python 内归一比较）；找到 → 复用该业主，找不到 → 新建业主（存归一化后的姓名）；手机号取 `appeal.user.phone`，为空则不写电话；若该号码已属于**另一位**业主 → 抛 `ApiError("PHONE_OWNED_BY_OTHER", "该手机号已登记在本专有部分的另一位业主名下，无法更新清册", 409)`；号码已属同一业主 → 不变；否则为该业主追加 `RegistryPhone`。申诉无产权人名字（历史申诉）→ 不调用追加，结果 `SKIPPED_NO_OWNER_NAME`。同事务写审计 `REGISTRY_UNIT_CHANGED`（`detail={"change":"appeal_append_owner","appeal_id","unit_id","result","owner_before":[姓名…],"owner_after":[姓名…],"phone_after":"138****0009"|None}`；手机号一律脱敏，姓名按 REQ-NFUNC-035 要求记录，仅管理员可见的审计页；`core/audit.py:11-15` 已含该动作，无需改白名单）。追加不调用 `AutoBindService`（C-61）。响应增加 `registry_update`：`{result, owner_phone_written, notice}`，`notice` 在无手机号时为"该产权人无联系电话"。后台列表给出 `applicant.has_phone`，使管理员**通过前**就能看到提示（AC-203-02）。
- Consequences: 正向：满足 AC-203-01~09；失败路径唯一（抛错回滚）。负向：通过申诉的响应新增 409 `PHONE_OWNED_BY_OTHER` 错误出口，前端须展示；审计 detail 含姓名（不含完整手机号），其可见范围继承现有审计页权限；"同名视为同一业主"在极端情况下（真正的重名不同人）会把新号码追加给旧业主——需求已接受（Q-OA-17=A）。

### ADR-115: 席位"在任"判定统一与授予校验放宽
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-199/200、Q-OA-19=A（结束日严格晚于今天）、Q-OA-20=A（开始日前不生效）、Q-OA-21=A（不绕过已有席位与人数上限）、Q-OA-28=A（未来起始日席位授予即占名额、阻止重复授予）。现状"有效"判断散在多处且只看 `term_end`：`CommitteeQuery.active_seat/active_member_ids/active_representative_ids/denominator_for_half_majority`（`committee/services.py:31-62,80-90`）、`identity_view`（`accounts/directory.py:23`）、后台用户列表预取（`accounts/views.py:430-433`）；`ALREADY_SEATED` 与 `CAP_REACHED` 按 `status == "ACTIVE"` 计数、不看日期（`committee/services.py:107,111`），与 Q-OA-28=A 一致；`expire_due` 只处理 `term_end < today`（`committee/services.py:215-217`）。授予视图当前以"开始日 < 今天"拒绝（`committee/views.py:66-67`），`term_end = add_months(开始日, 月数)`（`services.py:116`；`add_months` 对 year 超出 9999 会抛 `ValueError`）。
- Options:
  - A 新增无依赖小模块 `committee/effective.py`：`effective_q(today) -> Q`（`status="ACTIVE", term_start ≤ today ≤ term_end`）与 `is_effective(seat, today) -> bool`；上述所有调用点改用它；授予校验搬进 `CommitteeCommands.grant`（`term_end <= today` → 400）。优：一个定义，调用点逐个替换，`git grep term_end__gte` 可穷举；不改模型、无迁移；`ALREADY_SEATED`/`CAP_REACHED` 保持原计数口径。缺：须逐个调用点核对并补测试。
  - B 新增 Seat 状态 `PENDING`（开始日前），由到期任务在开始日激活。优：现有 `status="ACTIVE"` 过滤自然排除未来席位。缺：需要迁移（`status` choices，虽为元数据）、到期任务多一类转换、任务未跑时席位错过生效日，且占名额/重复授予的计数要改成含 `PENDING`（与现有 `ALREADY_SEATED` 查询耦合）；`MERGED/REPLACED` 等流转要对新状态逐一核对。
  - C 只放宽授予校验，不改"有效"判定。违反 REQ-FUNC-200，且会让开始日在将来的席位立刻拥有权限。
- Decision: 选 A。细则：(1) `grant` 在配置校验之后算出 `term_end`，`term_end <= today` → `ApiError("INVALID_VALUE", "按配置任期，该席位已于 {term_end} 结束，不能授予", 400)`；然后才是 `ALREADY_SEATED`（409）与 `CAP_REACHED`（409），次序保证补录不绕过这两项（AC-205-04/05）。(2) 视图删除"开始日 < 今天"分支；`term_start` 增加上界（今天起 5 年内，超出 400 `INVALID_VALUE` "任期开始日过远"），防止 `add_months` 对极大日期抛 `ValueError` 变成 500 `[ASSUMPTION]`（见 OQ-04）。(3) `CommitteeCommands.change` 对**未生效**席位变更职位时，新席位沿用原 `term_start`（`max(原 term_start, 今天)`），不让变更悄悄提前生效；对已生效席位行为不变（开始日取今天）。(4) 响应与列表增加 `effective: bool`；后台席位页对"在任但未生效"显示"待生效"。(5) `expire_due` 不改（只处理 `term_end < today`，未来起始日席位不会被误处理，AC-206-02 由测试证明）。
- Consequences: 正向：权限判断（`IsCommitteeMember`、审批、报销、收入、身份显示、业主个人信息）一次对齐，AC-206-01/03/05 可由同一谓词验证；无迁移。负向：调用点较多（见 module_design MOD-116 清单），遗漏任一处会出现"显示在任但无权限"或相反的不一致，须有"全部调用点"清单化测试；`ALREADY_SEATED`/`CAP_REACHED` 计入未生效席位，意味着未来席位占名额（Q-OA-28=A 的既定取舍）；上批 `test_product_review_ac.py:830-836`（TC-INT-472，断言"任期开始日不得早于今天"）须改写。

### ADR-116: 两端客户端契约同步与转申诉流程
- Status: Proposed
- Type: constraint-driven
- Context: 画像 P6："API 路径集中在 `frontend/src/shared/api.js`、`miniprogram/utils/api.js`，修改后端路由或序列化字段时必须同步修改这两处"；画像 P5：E2E critical path 须覆盖前后端契约；REQ-FUNC-192/193/195 要求 Web 与小程序同批改动；契约守护测试 `backend/tests/integration/test_frontend_contract.py:30-97` 只认 `http.`/`adminHttp.` + 字面量路径、路径不带 `?`。
- Options（被排除的替代方案与约束来源）:
  - 只改 Web、小程序后续补：违反 REQ-FUNC-193（"两端同批"）与 Q-OA-11=A（后端一律要求姓名，旧小程序认证会 400）。
  - 在小程序增加 pdf 选择（`wx.chooseMessageFile`）：uni-app 文档把 `wx.chooseMessageFile` 列为仅 mp-weixin 的微信原生接口，参数细节在微信文档中，而 `uni.chooseFile` 在小程序不受支持 `[WEB: https://uniapp.dcloud.net.cn/api/media/file.html，2026-11-16]`；微信官方文档不在仓库（画像 P11-3 同类条目），本批小程序申诉资料保持**图片**（`uni.chooseImage`，现状，`miniprogram/pages/units/index.vue:chooseProof`），pdf 仅 Web 支持（`accept` 增加 `.pdf`）。后端已允许 pdf（`core/attachments.py:19-20`）。
- Decision: 契约变更集中在三处：`unitApi.certify(unitId, name)` → `post('/certifications', { unit_id, name })`；`createAppeal` 的 `data` 增加 `owner_name`、`proof_ids` 支持 1~5 个；`/units/options` 响应的可选 `level_label`。认证失败（`code === 'OWNER_NOT_MATCHED'`）时客户端保留已选专有部分与已输入姓名，把姓名默认带入申诉表单的"产权人名字"并引导到申诉区；提示文案不含任何清册信息（AC-201-02）。管理端新增调用无（缩略图/大图沿用 `admin.downloadAttachment`，`frontend/src/shared/api.js:179`），`api.js` 无新增路径。
- Consequences: 正向：契约测试自动覆盖；小程序与 Web 行为一致。负向：小程序须重新构建发布才能继续使用认证；小程序申诉暂无法上传 pdf（需求"jpg/png/pdf"在小程序端未全覆盖，见 OQ-06）。

## 开放问题 / ASSUMPTION

| 编号 | 问题 / 假设 | 影响与处理 |
|---|---|---|
| OQ-01 | `[ASSUMPTION]` 纯数字原楼栋写入 `unit_no` 时补"栋"（`1→1栋`），其余原样（ADR-106）。Q-OA-27=A 只说"写入单元列"，未说是否补后缀。 | 若用户要求原样写入（`1`），标识会显示"商铺1单元…"；命令内 `shop_unit_no` 是单一函数，改它即可（备份仍保留逐记录原值）。请用户确认或默认采用补"栋"。 |
| OQ-02 | 商铺归类后，**今后经批量导入新增**的商铺若楼栋写 1~10 栋，会再次出现在第一级编号楼栋下（ADR-106 负向）。 | 本批不改导入引擎（需求未要求）。可选后续：导入时自动归类，或每次导入后手工再跑 `relocate_shops`（幂等）。 |
| OQ-03 | `[ESTIMATE]` 缩略图靠客户端降采样，带宽成本未消除（ADR-112）。 | 若测试环境体验不可接受，再提服务端缩略图方案（新增 Pillow 依赖，需用户同意）。 |
| OQ-04 | `[ASSUMPTION]` 席位 `term_start` 上界定为"今天起 5 年内"（ADR-115）。需求只要求"未来还有任期就可以授予"，未给上界；无上界会因 `add_months` 对极大日期抛 `ValueError` 变成 500。 | 5 年为设计取值，请用户确认；也可改为"不得晚于 2099-12-31"。 |
| OQ-05 | `shops.py` 与 `underground.py` 的 apply/restore 流程结构相似（ADR-107 负向）。 | 后续若再出现第三种归属修正，再抽取通用引擎；本批不动已验收代码。 |
| OQ-06 | 小程序申诉资料本批只支持图片（ADR-116），而需求 AC-201-01 写"jpg/png/pdf"。 | 若需要小程序支持 pdf，须核对微信官方 `wx.chooseMessageFile` 文档（不在仓库，`[UNSOURCED]`）后另批实现；本批 Web 满足 pdf。请用户确认可接受。 |
| OQ-07 | `[ASSUMPTION]` 附件下载对"已登录的无关普通用户"由 404 改为 403（ADR-112），以满足 AC-198-04"401 或 403"。 | 须改写现有用例 `test_rework_cr011_024.py:376`；若用户更看重"不暴露资料存在性"，可回退为 404 并把 AC-198-04 解释为"被拒绝"。 |
| OQ-08 | `/units/options` 的 `level_label` 为新增的可选响应键（ADR-109）。 | 契约变更，两端须容忍缺省；`backend/tests/integration/test_frontend_contract.py` 无字段级断言（只校验路径/方法/权限），不受影响。 |
| OQ-09 | 清册 Q-OA-29 的数据核对项（姓名为空的业主数、商铺楼层写法、改库后冲突）依赖授权后的只读 dry-run。 | 由 `relocate_shops` dry-run 输出提供计数；不在设计阶段连接测试机（画像 P9）。 |
