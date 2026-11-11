<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-11T22:45:48+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>phase_status.md</file>
    <file>../ocap_registry_import/architecture/architecture_design.md (基线，ADR-034~044)</file>
    <file>../ocap_registry_import/architecture/module_design.md (基线，MOD-030~038)</file>
    <file>../ocap_ui_theme/architecture/architecture_design.md (基线，ADR-023~033)</file>
    <file>../ocap_ui_theme/architecture/module_design.md (基线，MOD-023~029)</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：管理端打磨（专有部分显示格式 + 管理端多风格）（INCREMENTAL）

> **1.1.0 定向修订（用户 Q-B1=B，2026-11-11T22:43:12，phase_status.md）**：管理端 B 风格在"主按钮用强调色"之外，顶栏改为 `--hero` 渐变、顶栏文字改用 `--on-hero`、导航当前页高亮改为强调色系。只改 ADR-075（Decision、完成口径、Consequences）、OQ-07（改写关闭）并新增 OQ-11/OQ-12，以及架构概览/关键事实中的对应描述；其余 ADR、编号、数量（ADR-064~077）不变。1.0.0 的 GR-B-001-F02（白底顶栏 + 黑色胶囊）由本次修订消除。
> 编号接续全项目：本次从 **ADR-064 / MOD-064 / IFC-243** 起（ADR-064~077、MOD-064~073、IFC-243~260）。
> 只设计到接口签名，不含实现代码。仓库事实以 `文件:行` 引用，均已用 `git grep` / 读取核实；没有新增第三方依赖，未联网（无新依赖，见 tech_stack）。
> 本次未执行 makemigrations、ssh、commit，未访问测试机；测试环境数据（5742 条、冲突 0、省略楼层段 24 条、非纯数字户号 27 条）全部取自 phase_status.md 中 PM 的只读核验记录。

## 架构概览

### 本次改动在现有系统中的位置

两项互相独立的变更在同一批交付：

| 变更 | 现状（已核实） | 本次改动 |
|---|---|---|
| A. 专有部分显示格式（REQ-FUNC-123~129） | 标识只在一处生成：`build_specific_part`（`backend/apps/registry/models.py:16-18`，以"-"连接非空段）。四个写入点都经它：模型 `save()`（`models.py:38-40`）、导入解析（`importing.py:389`，随后按 `casefold` 分组匹配 `:406-410`、批量建行 `:456`）、单条编辑判重（`views.py:157-159`）；唯一例外是单条新增的预检查用四字段元组而非标识（`views.py:115`）。读取、搜索、输出全部读存储列 `specific_part`：清册搜索 `views.py:83`、房屋关系搜索 `identity/views.py:103`、身份/房屋关系输出 `identity/services.py:22`、`identity/views.py:81`、自动绑定 `residency/auto_bind.py:22,51`、`residency/views.py:26` | 在原位替换规则（同名同签名，所有调用点自动生效）；单条新增预检查改经同一函数；手写数据迁移 `registry/0005` 把存量标识按新规则重新生成；导入说明/模板/示例与规则同源；新增只读核对命令 |
| B. 管理端多风格（REQ-FUNC-130~135） | 管理端强制风格 B：`frontend/src/theme/store.js:58-61`、`frontend/src/router/index.js:65-73`、`frontend/index.html:8-14`；偏好字段只在普通用户 `User.theme_key`（`backend/apps/accounts/models.py:27`），接口 `/me/theme` 为 `IsMember`（`accounts/views.py:255-265`，`core/permissions.py:28-32`）。管理员 `AdminAccount`（`models.py:45`）无偏好字段 | `AdminAccount` 增偏好字段 + `GET/PUT /admin/me/theme`（`IsAdmin`）；前端新增管理端风格 store、顶栏切换入口、设备记忆分键；管理端路由不再强制 B；管理端主题化按"变量化 + 作用域覆盖 + 守护测试"收口；管理端 B 风格另有"渐变顶栏 + 强调色高亮 + 强调色主按钮"三项仅限 `data-surface="admin"` 的覆盖（ADR-075，Q-B1=B） |

### 两条关键事实（影响设计量级，均已实测）

1. **专有部分显示层无需逐处改**：除 `build_specific_part` 外，仓库中没有第二处派生标识的代码（`git grep -n "specific_part" -- backend ':!backend/tests' ':!backend/apps/registry/migrations'` 全部为读取/输出，见上表）。因此"只实现一处、全后端共用"的落点就是 `models.py` 里这一个函数加一个数据迁移；搜索与各接口输出随存储值自动变为新格式。
2. **管理端 15 个页面已无写死颜色**：`git grep -nE "#[0-9a-fA-F]{3,8}\b|rgba?\(|hsl" -- frontend/src/admin` 仅命中 `admin/editor/colors.js`（富文本调色板数据，`.js` 文件，不属于页面）；`<style>` 块只有 4 处且无颜色（`AdminContentEditor.vue:420`、`AdminMedia.vue:79`、`editor/MediaPicker.vue:55`、`editor/Toolbar.vue:133`）；页面使用 `.page/.card/.title/.row` 等语义类，Element Plus 经 `--el-*` 映射换肤。用户看到"黑白"的原因是：路由强制 B（浅色）、顶栏 `.admin-bar` 无高亮与品牌样式（`style.css:56`，`AdminLayout.vue:3-22`）、B 风格主按钮写死 `#11121A`（`themes.css:383-392`，来自 `themes/bento.theme.json` 的 `accentBg`）。所以"主题化"的工作量集中在布局与作用域覆盖，页面本体以"守护测试证明已无固定色"为口径（ADR-075），而不是逐页大改。1.1.0 补充：用户 Q-B1=B 要求 B 风格的管理端顶栏也有颜色，因此顶栏背景改用已有变量 `--hero`（`themes/bento.theme.json:26` 的渐变）、文字改用 `--on-hero`（`:27`），不新增 token（`scripts/themes/schema.mjs` 的 `TOKEN_SPEC` 有固定清单，新增 token 须改构建脚本，超出本次范围）。

### 关键质量属性

| 属性 | 需求 | 落点 |
|---|---|---|
| 规则单点、各端一致 | REQ-FUNC-123/124/126/127/128 | ADR-064、ADR-069 |
| 存量重新生成：无损、幂等、冲突整批不生效、≤60 秒 | REQ-FUNC-125、REQ-NFUNC-19/23、C-31 | ADR-065/066/067 |
| 历史文本不改写 | Q-AP-08=A | ADR-068 |
| 管理员/用户偏好隔离 | C-33、REQ-FUNC-134 | ADR-071/072/073 |
| 首屏无闪烁、切换 ≤1 秒 | REQ-NFUNC-22 | ADR-073 |
| 零回归、前后端契约 | REQ-NFUNC-20、画像 P5/P6 | ADR-070/075/077；module_design MOD-073 |
| 可访问性（对比度/44px/减少动态） | REQ-NFUNC-21 | ADR-075 |

## 部署视图

仅使用画像 P7 中存在的环境（"测试"；"生产"无）。不用 Docker（P8）。

| 组件 | 运行单元 | 环境 | 变更 |
|---|---|---|---|
| Django 后端 | systemd `ocap-backend`（gunicorn 127.0.0.1:9000） | 测试 | 代码 + 迁移 `registry/0005`（数据）、`accounts/0003`（加列），均手写；须在目标机 `migrate` 后重启。建议"停服务 → migrate → 启动"以避免新旧规则混写（见开放问题 OQ-04） |
| Web 前端静态文件 | `npm run build -- --base=/ocap/` 产物 → `/home/yangyang/ocap/web`，nginx 8090 提供 | 测试 | 重新构建并替换；nginx 无需改动 |
| 风格构建脚本 | 开发机/CI 上 `node scripts/themes/build.mjs` | 开发机、CI | 修改 `themes/bento.web.css`、`themes/bento.theme.json` 后重新生成 `frontend/src/theme/generated/themes.css` 并提交；不在目标机运行 |
| 小程序 | 无 | — | **不改动**（ADR-077） |
| Freeark 服务/端口/目录/库 | — | — | 不触碰（P7、P8、C-34） |

## ADR

### ADR-064: 专有部分新拼接规则的唯一实现位置与语义
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-123/124（规则）、REQ-FUNC-126/127/128（各处一致、判重、导入分组匹配）、REQ-NFUNC-23（导入 20000 行 ≤60 秒）。现状 `build_specific_part` 已是全后端唯一的派生点（上表），调用者：`models.py:39`、`importing.py:389`、`views.py:157`。
- Options:
  - A. 在 `registry/models.py` **原位替换** `build_specific_part`（同名、同签名 `(building, unit_no, floor, room) -> str`），所有既有调用点零改动；单条新增预检查（`views.py:115`）改为经同一函数。优：只有一处实现；既有 import 路径（`importing.py:33`、`views.py:27`、测试 `test_registry_import_rules.py:27`）不变；性能为纯字符串运算。缺：规则含 5 条分支，函数比旧版复杂，需单元测试覆盖全部 AC。
  - B. 数据库生成列/触发器计算标识。缺：MySQL（生产）与 SQLite（测试，画像 P4）行为不同；迁移与运行期规则分叉；违背"手写迁移、单 app"的低风险路径。
  - C. 只改展示层（前端/序列化器格式化），库里仍存旧标识。缺：违背用户 Q1=A（改"专有部分本身"，搜索也按新格式）；搜索与判重仍是旧值；多端各写一份。
- Decision: 选 A。语义固定如下（每条对应 AC，函数只读不写库）：
  1. 每段先 `strip()`；空串整段跳过（REQ-FUNC-124 规则 1）。
  2. 取值已以该段后缀（楼栋"栋"、单元"单元"、楼层"层"、户号"号"）结尾 → 原样（规则 2）。
  3. 取值匹配 `[0-9]+` 或 `负[0-9]+`（仅 ASCII 数字）→ 补后缀（规则 3）；其余（含"3.0""-1""B1""1F""整栋""A-088"）→ 原样（规则 4）。
  4. 楼层省略（规则 5）：楼层非空，令 `stem = 楼层去掉末尾"层"`，`stem` 非空且户号以 `stem + "层"` 开头 → 不输出楼层段，户号按规则 2~4 处理。
  5. 四段结果直接连接，不加分隔符。
  6. 最大长度：每段 ≤32（`validate_unit_fields` 既有上限）+ 后缀共 5 字符 = 133 ≤ 列宽 140（`models.py:26`），无需改列。
  ASCII 数字限定是本设计的选择（全角数字按"含非数字内容"原样保留），见开放问题 OQ-02。
- Consequences: 正向：一处实现、所有写入点自动一致；规则演进只改一处（迁移不受影响，见 ADR-066）。负向：旧测试中约 10 个文件的旧格式断言必须同步更新（module_design MOD-073 清单）；`uniq_registry_unit`（四字段元组唯一，`models.py:33-35`）与 `specific_part` 唯一并存，"1"与"1层"这类写法在元组上不同但标识相同，靠标识唯一约束与预检查拦截（REQ-FUNC-127）。

### ADR-065: 存量标识重新生成的执行方式
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-125（上线时全部现有标识按新规则重生成，原值不变，可重复，冲突整批不生效）、REQ-NFUNC-19/23、画像 P6/P7/P8（手写迁移；部署流程含"迁移"一步；禁止 makemigrations 产物与在目标机生成迁移）。PM 实测 5742 条。
- Options:
  - A. 手写数据迁移 `registry/0005_regenerate_specific_part.py`（`RunPython`，带反向函数），随部署的 `migrate` 一次完成。优：与代码发布同一动作、测试库不跑迁移但函数可被测试直接调用（沿用 `0003_backfill_legacy_owners.py` 的写法）；有 Django 迁移状态记录，天然"只执行一次"，且函数本身幂等；可逆。缺：MySQL 无 DDL 事务，须在函数内显式 `transaction.atomic`（ADR-067）。
  - B. 单独的管理命令，部署后手动执行。缺：代码已上线而数据仍是旧格式的窗口内，搜索与判重表现不一致；依赖人工记得执行；无迁移状态记录。
  - C. 惰性重算（保存时才换成新格式）。缺：新旧格式长期混杂，搜索 `1栋1单元` 命中不全；违背"上线后全部是新格式"（AC-134-01）。
- Decision: 选 A。迁移只依赖 `apps.get_model` 取得的历史模型，不依赖应用代码（ADR-066）。核对用途的只读管理命令另设（MOD-066），不承担写入。
- Consequences: 正向：一次性、可逆、可测。负向：迁移失败（冲突）时 `migrate` 报错中止，部署需先用核对命令预检（E1 要求）。

### ADR-066: 迁移内规则采用"冻结副本"，不引用应用代码
- Status: Proposed
- Type: decision
- Context: 画像 P6/特别说明：数据迁移不应 import 会随代码演进的拼接函数；`models.build_specific_part` 今后可能再改，若迁移引用它，则在新环境（空库逐个迁移）或回滚重放时产生与本次变更不同的结果。
- Options:
  - A. 迁移文件内**复制一份冻结的规则实现**（新规则 `_frozen_rule_v1` 与旧规则 `_frozen_legacy_rule` 各一份），并配"冻结金标"测试：用迁移文件自带的字面量金标表（不引用应用函数）断言冻结副本输出；另用应用函数金标测试守护当前规则。优：迁移结果永远等于"本次变更时刻的规则"；反向迁移可精确还原旧格式；测试可发现任何一方被误改。缺：规则在迁移与 `models.py` 各有一份——这是有意的两份（一份运行时，一份历史快照），须在迁移文件头注明"禁止随运行时规则修改"。
  - B. 迁移 import `apps.registry.models.build_specific_part`。缺：规则演进后迁移语义漂移；历史模型与运行时函数混用。
  - C. 把规则抽到新模块 `registry/legacy_rules.py` 供迁移引用。缺：仍是应用代码，仍可能被后人"顺手改"；多一个模块却没有解决漂移，只是换了位置。
- Decision: 选 A。"只实现一处"（ADR-064）约束的是**运行时**路径；迁移副本是历史快照，不参与任何运行时写入。
- Consequences: 正向：迁移可永久重放。负向：当前规则变更时，需有意识地**不**改迁移；用金标测试的两份期望表（迁移表、运行时表）在今天相同、日后可分叉，分叉即表示规则演进。

### ADR-067: 唯一约束下的更新顺序、冲突处理与原子性
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-125（冲突整批不生效并列出冲突，Q-AP-03=A）、REQ-NFUNC-19、C-31。`specific_part` 有唯一约束（`models.py:26`）；MySQL 默认排序规则大小写不敏感（沿用 ADR-035 第 4 点）。**存在中途违反的真实可能**：记录 P=(车库,"","","A-088") 新值 `车库A-088`，记录 Q=(车库A,"","","088") 旧值恰为 `车库A-088`；单遍逐行更新时 P 先于 Q 会撞唯一约束，而 Q 随后会变成 `车库A088号`，最终并无冲突。
- Options:
  - A. **先检测、再两阶段更新、整体一个事务**：读出全部行，按冻结规则算出新值；以"最终值"（改动行取新值、未改动行取原值）按 `casefold` 分组，组内 >1 即冲突 → 先打印全部冲突记录再抛错，**未写任何数据**；无冲突时，只对"值会变化"的行做两阶段更新：阶段 1 把这些行统一置为占位值 `~regen~<id>`，阶段 2 写入新值；两阶段在同一个 `transaction.atomic()` 内，任何异常（含库层 `IntegrityError`）整体回滚。优：不因更新顺序违反唯一约束；整批生效或整批不生效（Q-AP-03=A）；第二次执行时无变化行，不产生写入（幂等）。缺：变化行写两次；占位前缀需断言库中无同前缀值。
  - B. 单遍逐行更新，遇冲突再回滚。缺：上述交叉情形会把无冲突的数据误判为失败。
  - C. 临时删除唯一约束再恢复。缺：DDL 在 MySQL 不可回滚，失败时留下无约束的表；违反"整批不生效"。
- Decision: 选 A，细则：
  1. 事务：MySQL 不支持事务性 DDL，Django 对其不会包裹迁移，因此 `transaction.atomic(using=schema_editor.connection.alias)` 在函数内显式使用。
  2. 批量写：`bulk_update(["specific_part"], batch_size=200)`（SQLite 变量上限，参见既有提交"导入批量查询分批适配 SQLite 变量上限"，每行约 3 个变量，200×3<999）；`bulk_update` 不刷新 `updated_at`（`auto_now` 不触发，M-SA-005），本迁移不改 `updated_at`（OQ-05）。
  3. 检测使用 `casefold`，库层唯一约束作为最后防线：若检测漏掉（如 MySQL 的重音不敏感），`IntegrityError` 触发整体回滚。
  4. 冲突输出：全部冲突记录逐行写 stderr（`id|旧标识|新标识|楼栋|单元|楼层|户号`），异常消息含冲突记录数（AC-134-04）。
  5. 非纯数字户号核对清单（AC-134-05，保留口径）：成功后按相同字段格式写 stdout，只读、不改数据；户号全为纯数字的记录不进入清单。
  6. 反向（回滚）：对称——用冻结旧规则重算，做同样的检测与两阶段更新；若迁移后新建的记录在旧规则下互相冲突则反向也整批中止并列出，须人工处理。
  7. 预估：5742 条中变化行 ≈ 全部（旧格式含"-"，几乎都变）→ 约 2×⌈5742/200⌉ ≈ 58 条更新语句 + 1 次全表读，远小于 60 秒 `[ESTIMATE]`（REQ-NFUNC-23 前半，仍须在测试环境实测）。
- Consequences: 正向：交叉情形安全；冲突不丢数据。负向：占位值短暂存在于事务内（对外不可见，回滚即消失）；变化行写两次。

### ADR-068: 历史文本不改写（Q-AP-08=A）——持久化副本核实结果
- Status: Proposed
- Type: constraint-driven
- Context: Q-AP-08=A（用户 2026-11-11 放行：历史文本保持原文不改写）、C-31。
- 约束来源：用户 Q-AP-08=A；审计记录的不可篡改性。
- 被排除方案：迁移内扫描并改写审计详情或自由文本（用户已选 A；且无结构化副本可安全改写）。
- 核实结果（`git grep` / 读取模型）：
  | 位置 | 是否保存 `specific_part` 字符串副本 | 依据 |
  |---|---|---|
  | `AuditLog.detail`（`core/models.py:18`） | 否。各写入点的 detail 键：清册变更 `change/owner_count`（`registry/views.py:350-356`）、导入统计（`views.py:311-318`）、认证 `role/source/origin`（`residency/services.py:33-35`）、`user_id/unit_id`（`identity/services.py:142`，`residency/views.py:265`） | 全部为 id/计数/枚举 |
  | `Membership / Appeal / ResidentApplication` | 否，外键 `unit`（`residency/models.py:14,35,52`），读取时取 `unit.specific_part` | 随迁移自动呈现新格式 |
  | `ledger`、`polls`、`approval`、`claims`、`income`、`committee`、`content` 的 JSON/文本字段 | 否（`git grep -n unit` 在这些 app 的 models 与服务中无命中） | — |
  | 通知表 | 不存在（`git grep -in notification -- backend/apps` 仅命中内容样式名） | — |
  | 前端/小程序本地存储 | 否，仅令牌、风格键、倒计时（`frontend/src/shared/http.js:15-21`、`theme/store.js:14-17`、`miniprogram/store/theme.js:16`） | — |
  | 自由文本：申诉驳回理由 `Appeal.reject_reason`（`residency/models.py:40`）、决议正文 `resolutions/models.py:10`、信息公开文档 `content/models.py:11`、报销摘要 `ledger/models.py:13` | 非结构化手写文本，可能含旧格式字样 | 保持原文，不改写 |
- Decision: 迁移只改 `registry_registryunit.specific_part`，不碰上表任何位置。**没有业务上需要同步的冗余结构化副本**，故无新增开放问题；自由文本中的旧格式字样作为已知现象记入开放问题 OQ-08，仅供知悉。
- Consequences: 正向：迁移面最小、历史可追溯。负向：旧审计详情/自由文本中若出现旧格式，与现标识不一致，属预期。

### ADR-069: 搜索、判重与输出：不派生第二套规则
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-126（搜索按新格式匹配、旧格式关键词不再命中，Q-AP-06=A）、REQ-FUNC-127（判重以新格式为准）、REQ-FUNC-128（导入分组/匹配）。
- Options:
  - A. 存储列即新格式；搜索继续对存储列做包含匹配（`views.py:83`、`identity/views.py:103` 不改）；判重、导入分组/匹配使用同一个 `build_specific_part` 的结果与存储列比较；各接口输出继续读存储列（`identity/services.py:22` 等不改）。优：零额外代码路径；Q-AP-06=A 自然成立。缺：依赖"存储列永远由该函数写入"这一不变量。
  - B. 搜索关键词先经规则"规范化"再匹配。缺：规则是对完整四段的函数，对 `1栋1单元` 这种片段无意义；还会让旧格式关键词被误改写命中，违背 Q-AP-06=A。
  - C. 另存"搜索用标识"列。缺：多一列与迁移，无需求依据。
- Decision: 选 A。不变量的守护：新增一致性测试（MOD-073）——对"模型保存、批量导入、单条新增、单条编辑"四条路径各建一条记录，断言 `specific_part == build_specific_part(四字段)`；并用 AST 扫描断言 `apps/` 下除 `registry/models.py` 外无第二个名为 `build_specific_part` 的定义、`apps/registry` 下无 `"-".join(` 形式的拼接。
- Consequences: 正向：搜索、判重、输出一致且无新代码。负向：不变量靠测试守护而非库约束（可接受：库层已有 `specific_part` 唯一约束兜底重复）。

### ADR-070: 导入说明、模板与示例以后端 `import_spec` 为单一来源
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-129（说明与示例体现新规则，模板示例行导入后生成的标识与说明展示一致）。现状：规则文案在 `import_spec.py:61-69,84-93`；模板示例在 `import_template.py:8-13`；前端对话框另有一行**硬编码**示例 `RegistryImportDialog.vue:33`（含旧写法"车库 / 空单元 / 空楼层 / A-088"）。
- Options:
  - A. 示例行（`EXAMPLE_ROWS`）移入 `import_spec.py`，由 `spec_payload()` 经 `build_specific_part` 实算每个示例的标识，随 `GET /admin/registry/import/spec` 下发 `examples` 与 `suffix_rules`；模板生成与前端对话框都读它，前端删除硬编码示例行。优：说明、模板、真实规则不可能漂移；可单测"模板示例行预检失败 0 且标识逐字一致"（AC-138-03）。缺：spec 响应增加字段（只增不改，向后兼容）。
  - B. 只改前端硬编码文案与后端文案。缺：三处各写一份，规则再改必漂移；与基线 ADR-041"后端单一来源"冲突。
- Decision: 选 A。示例行扩充为覆盖 `1栋1单元1层301号`（3 行多业主）、`车库A-088`、`1栋负1层924号`（车位，楼层"负1"）、`10栋1层1号`（商铺）；手机号用虚构号段（沿用基线 A-5）。
- Consequences: 正向：单一来源。负向：模板示例行增多（4 → 6 行），若管理员忘记删除就上传会被当真实数据（基线风险 R8，继续靠"填写说明"首行提示缓解）。

### ADR-071: 管理员风格偏好的存储与接口
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-130/131/132（顶栏切换、默认 B、记在管理员账号、跨设备）、C-33（普通用户令牌不得读写管理员偏好，反之亦然）、画像 P6（手写单 app 迁移、两处契约文件同步）。基线 ADR-023：用户偏好为 `User.theme_key` + `/me/theme`（`IsMember`）。
- Options:
  - A. `AdminAccount` 增可空列 `theme_key`；新端点 `GET/PUT /admin/me/theme`，`IsAdmin`；校验规则复用 `THEME_KEY_RE`（`accounts/services.py:24`）。优：与用户偏好物理隔离，C-33 由两个既有权限类天然保证（`IsAdmin` 对用户令牌 403、`IsMember` 对管理员令牌 403，`core/permissions.py:19-37`）；`/me/theme` 零改动；迁移极小可逆。缺：多一个端点与一份校验调用。
  - B. 让 `/me/theme` 同时接受两类令牌并按主体分流。缺：该视图是 `IsMember`（`accounts/views.py:255`），放宽后 C-33 要靠视图内分支保证，权限矩阵变复杂；既有测试 `test_theme_preference_api.py:12-15`（管理员令牌 403）会失效。
  - C. 新建 `Preference(principal, principal_id, theme)` 表。缺：当前只有一个偏好，过度设计，多一张表和 app 级迁移。
- Decision: 选 A（接口契约见 module_design IFC-248/249）。后端同样只校验格式、不维护启用集合（沿用 ADR-025）；已下线 key 由客户端回退 B（REQ-FUNC-131）。
- Consequences: 正向：C-33 由现有权限类保证，可被两条越权用例直接验证（AC-141-03）。负向：偏好逻辑在两个视图各有一份（只有 3 行差异）；管理员账号被禁用（`is_active=False`）后 `IsAdmin` 返回 401，偏好保留不丢。

### ADR-072: 前端风格状态——独立管理端 store，共享核心工具
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-130~132/134、REQ-NFUNC-22。现状用户端 store（`frontend/src/theme/store.js`）状态与方法绑死 `/me/theme` 与设备键 `ocap_theme`（`:14-17,33-53`），并含 `forAdminRoute()`（`:58-61`）。
- Options:
  - A. 新建 `useAdminThemeStore`，与 `useThemeStore` 并列；两者共享 `theme/core.js`（注册表查找、`resolveKey`、设备读写的带键版本）。优：两个 store 状态、键、接口完全分离，用户端 store 行为零回归；偏好隔离（REQ-FUNC-134）由构造保证。缺：两个 store 有相似的 `select/reconcile` 结构（各 ~20 行）。
  - B. 给现有 store 加 `scope` 参数/双份状态。缺：一个 store 里混两个主体的状态，容易把管理员值写进用户键；用户端既有 11 个相关测试都要动。
  - C. 工厂函数 `createThemeStore(scope, api, deviceKey)` 生成两个 store。优：无重复。缺：Pinia 以 id 区分 store，工厂+测试替换更难读；对现有 `useThemeStore` 调用方与测试的导入方式有侵入。
- Decision: 选 A。`useThemeStore.forAdminRoute()` 随 ADR-076 删除。
- Consequences: 正向：用户端路径零回归。负向：两份相似逻辑；以相同的测试矩阵覆盖（MOD-073）。

### ADR-073: 设备记忆分键与首屏无闪烁
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-134、REQ-NFUNC-22、基线 ADR-027（首屏同步内联脚本）。
- 约束来源：用户 Q-AP-07=A（管理端与用户端偏好互相独立，同一设备也不共用记忆）；REQ-NFUNC-22（刷新/直接打开后台地址时风格与已保存风格一致）。
- 被排除方案：管理端与用户端共用 `ocap_theme`（Q-AP-07=B，用户未选）；管理端首屏恒为 B 再由脚本跳变（违反 REQ-NFUNC-22）。
- Decision: 设备键分为 `ocap_theme`（用户端，沿用）与 `ocap_admin_theme`（新）。`index.html` 内联脚本按路径选键：路径含 `/admin` 读 `ocap_admin_theme`，否则读 `ocap_theme`；两者都用同一个格式正则（`^[a-z][a-z0-9_-]{1,31}$`）；缺失/非法 → bento；同时设置 `data-surface`（`admin` | `portal`，见 ADR-075）。账号偏好与设备记忆的对账规则沿用 ADR-027 的第 3~6 条，对管理端同样成立：账号值权威；账号值为 NULL → B 并写回设备记忆（管理员无论设备上有何记忆均如此，REQ-FUNC-131）；读取失败 → 保持当前、不清设备记忆（AC-140-03）；登录成功后先对账再跳转，使登录后首屏已是账号风格（AC-141-01/04）；登出保留设备记忆，登录页沿用（AC-141-05）。
- Consequences: 正向：两端记忆互不覆盖；首屏与保存值一致。负向：同设备上换管理员账号时，新账号登录对账前设备记忆属于上一位管理员，由"登录成功后先对账再跳转"覆盖。

### ADR-074: 顶栏风格入口的形态
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-130（顶栏入口、选项取自注册表、新增风格自动出现、点击立即生效）、AC-139-01~04、REQ-NFUNC-21（44px 点击区域）。管理端无个人中心页（C-33）。
- Options:
  - A. 新组件 `AdminThemeSwitcher.vue`：顶栏中的 `el-dropdown`，选项来自 `useAdminThemeStore().list`（即风格注册表）；每项 = 色块 `swatch` + 名称，当前项带"已选"。优：占位小，13 个导航项已很挤；列表由注册表驱动，新增风格自动出现（AC-139-03）。缺：多一次点击展开。
  - B. 复用 `ThemePicker.vue` 卡片单选。缺：该组件绑定用户端 store（`ThemePicker.vue:23-33`），要加 scope 参数；卡片式占位大，不适合顶栏。
  - C. 在管理端新增"设置"页。缺：超出范围（"不新增功能页面"），且路由数与基线测试 `qa_unit_theme.spec.js:262` 的页数断言冲突。
- Decision: 选 A。登录页不放入口（REQ-FUNC-132 备注）。保存失败 → `ElMessage.error('保存失败…')` 并回滚（与 `ThemePicker.vue:30-34` 同口径）。
- Consequences: 正向：入口轻量、自动同步注册表。负向：下拉在窄屏需验证触控区域（REQ-NFUNC-21，走查清单项）。

### ADR-075: 管理端主题化的范围、实现方式与完成口径（1.1.0 修订：渐变顶栏与强调色高亮）
- Status: Proposed（1.1.0 修订；取代 1.0.0 的 Decision，Options 沿用并扩充）
- Type: decision
- Context: REQ-FUNC-133（15 个页面 + 顶栏布局同等程度应用风格，不得再有固定白底顶栏或固定黑色主按钮，一次改完）、AC-142-01~06、REQ-NFUNC-21。事实见"两条关键事实"第 2 条。基线 ADR-029 已有守护：`frontend/tests/theme.spec.js:34-45` 扫描 `frontend/src` 全部 `.vue`，禁止颜色字面量。
  **1.1.0 新增输入**：用户 Q-B1=B（phase_status.md，2026-11-11T22:43:12）：管理端 B 风格顶栏用渐变（与用户端首页横幅 `--hero` 同色系）、导航当前页高亮用强调色、主按钮用强调色，用户端不受影响。已核实的事实：（1）`--hero` = `linear-gradient(135deg, #4F46E5 0%, #7C3AED 55%, #DB2777 100%)`，`--on-hero` = `#FFFFFF`（`themes/bento.theme.json:26-27`）；（2）构建脚本的对比度校验只接受"单个 `#RRGGBB` 等效不透明背景"（`scripts/themes/schema.mjs:68`），`hero` 在 `TOKEN_SPEC` 中只是非空字符串，不解析渐变；（3）构建脚本的作用域校验要求 `web.css` 每个逗号分隔的选择器以 `html[data-theme="bento"]` 开头（`scripts/themes/build.mjs:125-154,207`），`html[data-theme="bento"][data-surface="admin"] …` 满足；（4）用户端 B 的黑色高亮胶囊在 `themes/bento.web.css:12`，导航胶囊容器在 `:10`，均无 `data-surface` 限定；（5）全局焦点环为 `outline: 2px solid var(--accent)`（`frontend/src/shared/style.css:5`），而 `--accent` 恰为渐变起点色 `#4F46E5`，在渐变顶栏左段上不可见。以下数值均用仓库内 `scripts/themes/schema.mjs` 的 `contrastRatio`/`mix` 在本机实算（只读，未改任何文件）：`#FFFFFF` 对 `#4F46E5` = 6.29、对 `#7C3AED` = 5.70、对 `#DB2777` = 4.60；对整条渐变按 1000 个采样点插值取最小值 = 4.592（在 100% 端）；`#FFFFFF` 叠 16% 白后对 `#DB2777` = 3.77（不达标）；叠 22% `#11121A` 后 = 6.50；`#4F46E5` 对 `#FFFFFF` = 6.29；`#FF5C8A`（accent2）对 `#FFFFFF` = 2.94（不达标）。
- Options:
  - A. **布局重做 + 作用域覆盖 + 守护测试**：（1）`AdminLayout.vue` 改为数据驱动导航，使用 `.brand`、`active-class="is-active"`、纳入切换入口；（2）`style.css` 的 `.admin-bar` 与 `.topbar` 合并样式规则、窄屏不隐藏管理导航；（3）给 `<html>` 增设 `data-surface="admin|portal"`，并在 `themes/bento.web.css` 增加仅作用于管理端的覆盖：主按钮 `var(--accent)`（AC-142-03，用户端 B 的黑色主按钮不变，NFUNC-20）；（3b，1.1.0）同一作用域内再覆盖顶栏渐变背景、顶栏文字色、导航胶囊容器、导航当前页高亮、顶栏内次级按钮与焦点环（具体规则见 module_design IFC-258）；（4）`themes/bento.theme.json` 的 `contrast` 增项，由构建脚本实算校验（1.1.0 增至三项，见 Decision 第 4 点）；（5）页面本体仅在守护测试发现违规时才改。优：改动集中；用户端零回归；完成口径可自动核对。缺：页面"同等程度"的视觉效果需走查补充。
    **1.1.0 对 A 内部的三个子选择（均在 A 之内，不改变 A/B/C 的取舍）**：
    - **顶栏渐变的取色**：A1 复用 `--hero`/`--on-hero`（选中）：与用户端首页横幅同源，Q-B1=B 要求"同色系"，不新增 token、不改构建脚本；缺：渐变端点 `#DB2777` 上白字只有 4.60:1，余量 0.1。A2 新增专用 token（如 `adminBar`）：须改 `schema.mjs` 的 `TOKEN_SPEC`、两份注册表与小程序生成物，波及面超出管理端。A3 把 hero 改暗以增加余量：会改变用户端首页横幅外观，违反 NFUNC-20。
    - **导航胶囊容器与悬停底色**：C1 半透明白（用户建议的方向）：白叠在渐变上变亮，`#DB2777` 端白字降到 3.77:1，不达标，排除。C2 半透明深色 `rgba(17,18,26,.22)`（选中，与既有 `bento.web.css:10` 同为 `#11121A` 色系）：叠加只会使背景变暗，白字对比度恒不低于渐变本身（`#DB2777` 端 6.50:1），因此无需对 rgba 单独设对比度项，只需守护"叠加色只能是深色"。C3 不设容器：13 个链接直接落在渐变上，当前页高亮与悬停没有承托，换行时观感松散。
    - **导航当前页高亮（管理端）**：H1 白色胶囊 + `--accent-text` 文字（选中）：`#4F46E5` 对 `#FFFFFF` = 6.29（已有 `contrast` 项"强调色 / 白卡"同一组合），胶囊对渐变顶栏的边界对比为 4.60~6.29；是"强调色系"的反白用法。H2 `--accent` 填充胶囊 + 白字：白字对 `#4F46E5` 达标，但 `#4F46E5` 正是渐变起点色，胶囊在顶栏左段与背景同色，须再加白色描边才能辨认，观感更杂；备选，见 OQ-11。H3 `--accent-2`（`#FF5C8A`）填充：白字 2.94:1，不达标，排除。
  - B. 全局把 B 风格的 `accentBg` 改为强调色。缺：改变用户端 B 的主按钮外观，违反 REQ-NFUNC-20（除两项变更外不变）。
  - C. 在管理端每个页面逐个加主题类/装饰。缺：改动面最大（15 页 + 布局），而页面已无固定色，收益低；回归风险集中在页面。
- Decision: 选 A。**为什么用 `data-surface` 而不是布局根类**：`el-dialog`/`el-message` 等弹层 Teleport 到 `body`（基线 ADR-026），布局根类选择器够不着，挂在 `<html>` 上才能覆盖；`data-surface` 由 `index.html` 脚本与路由守卫设置（IFC-254/255）。
  **1.1.0 补充决定（Q-B1=B）**，全部规则只写在 `themes/bento.web.css`，选择器一律以 `html[data-theme="bento"][data-surface="admin"]` 开头，且再带 `.admin-bar` 或 `.el-button--primary` 限定（双重限定：即使 `data-surface` 因路由切换瞬时滞后，用户端页面也不含 `.admin-bar` 元素，不会被命中）：
  1. **顶栏背景**：`.admin-bar` 背景取 `var(--hero)`，文字 `var(--on-hero)`，去掉下边框；品牌文字、导航链接、风格切换触发器（`.admin-theme-trigger`，文字与 SVG 图标用 `currentColor`）、退出按钮的文字/边框/图标颜色统一为 `var(--on-hero)`。
  2. **导航胶囊容器**：背景 `rgba(17,18,26,.22)`（C2），圆角 `var(--radius-lg)`（避免 13 个链接换行时 999px 胶囊变形），去掉用户端 B 的白底与投影；链接悬停底色同为 `rgba(17,18,26,.22)`。
  3. **当前页高亮**：管理端 `a.is-active` 背景 `var(--surface)`、文字 `var(--accent-text)`、`font-weight: 650`（H1）；用户端 `bento.web.css:12` 的黑色胶囊规则**原样保留，不改一个字符**。
  4. **对比度口径（构建脚本只能校验单色，不能校验渐变）**：对 `--on-hero` 在渐变上的文字，取**渐变各色停点的最差值**作为构建期校验：保留 `bento.theme.json` 已有的 `#DB2777`（4.59）与 `#4F46E5`（4.5）两项，**新增** `onHero / #7C3AED`（min 5.6）一项，使三个停点（0%、55%、100%）均有 `contrast` 项，由 `build.mjs` 实算；渐变两个停点之间的插值色由前端守护测试补足（对 `tokens.hero` 解析停点、按 CSS 的 sRGB 线性插值取 ≥1000 个采样点，断言 `onHero` 对每个采样色 ≥4.5，当前实测最小 4.592）。半透明深色叠加层不单设项（恒更暗，见 C2），由守护测试断言"叠加色 RGB 仅为 `17,18,26`"。高亮胶囊文字沿用已有项"强调色 / 白卡"（`accentText / #FFFFFF`，6.29），主按钮沿用 1.0.0 新增项 `onAccent / #4F46E5`（min 6.2）。
  5. **焦点环**：`.admin-bar :focus-visible` 的 `outline-color` 改为 `var(--on-hero)`（原 `--accent` 在渐变左段不可见）。
  6. **退出按钮与风格触发器**：透明底 + `var(--on-hero)` 文字与描边（`--el-button-*` 变量覆盖），悬停底 `rgba(17,18,26,.22)`；不使用 `el-button--primary`，避免与"主按钮用强调色"规则混淆。
  7. **不回归 neon / terminal**：它们的管理端顶栏仍是 `var(--overlay)` 背景（`style.css` 通用规则），本次所有新规则不命中它们。唯一的跨风格影响来自 1.0.0 已有的结构改动（导航项新增 `is-active`、品牌 `<strong>`→`.brand`、新增切换入口）：neon 的高亮 = 通用规则 `var(--glass)` 底 + `--accent-text` 字（`style.css:51`），terminal 的高亮 = `themes/terminal.web.css:20-21` 既有下划线与 "> " 前缀，均是各自用户端导航的既有外观，且 `.brand` 在深色 `--overlay` 上取 `var(--text)`；两者均**预期且需要**出现（AC-142-04 要求任一风格有导航高亮），由 15 页 × 3 风格走查确认。不回归的自动化口径见完成口径第 5 项。
  **完成口径（可核对，GROUP_D 据此写用例）**：
  | # | 口径 | 核对方式 |
  |---|---|---|
  | 1 | 管理端全部 `.vue`（`frontend/src/admin/**`，共 15 页 + `AdminLayout.vue` + `RegistryImportDialog.vue` + `editor/*.vue`）无颜色字面量 | 既有 `theme.spec.js:34-45`（保持通过）+ 新增针对 `src/admin` 的单列断言 |
  | 2 | 管理端 `.vue` 的内联 `style` 属性不含 `color/background/border/box-shadow/font-family/opacity` | 新增 `frontend/tests/admin_theme.spec.js` 正则扫描 |
  | 3 | 管理端 `<style>` 块中颜色类属性的取值只能是 `var(--…)`、`transparent`、`inherit`、`currentColor` | 同上 |
  | 4 | `AdminLayout.vue` 不含 `<strong>` 品牌写法/固定色；导航项均带 `active-class="is-active"`；渲染 `AdminThemeSwitcher` | 同上 + 组件挂载断言 |
  | 5 | 生成物 `themes.css` 中存在 `html[data-theme="bento"][data-surface="admin"] .el-button--primary`，且其背景取 `var(--accent)`；`neon`/`terminal` 的主按钮不含 `#11121A`。**1.1.0 补充**：生成物中存在 `html[data-theme="bento"][data-surface="admin"] .admin-bar` 规则且 `background` 取 `var(--hero)`、`color` 取 `var(--on-hero)`；存在 `… .admin-bar .topnav a.is-active` 规则，`background` 取 `var(--surface)`、`color` 取 `var(--accent-text)`，且该规则块不含 `#11121A`；`.admin-bar` 的半透明叠加色只出现 `rgba(17,18,26,…)`；`bento.web.css` 中每个含 `.admin-bar` 的选择器都以 `html[data-theme="bento"][data-surface="admin"]` 开头；用户端规则 `html[data-theme="bento"] .topnav a.is-active, … .tabbar a.is-active { background: #11121A; color: #fff; }`（`bento.web.css:12`）与 `.topnav` 胶囊规则（`:10`）在生成物中保持原样；`neon`/`terminal` 的 web.css 与生成物段落中不含 `.admin-bar` | 读取生成物与源文件断言；`build.mjs --check` 通过 |
  | 6 | 三套风格 × 管理端主按钮文字对比度 ≥4.5:1。**1.1.0 补充**：B 风格管理端顶栏白字对渐变三个停点（`#4F46E5`/`#7C3AED`/`#DB2777`）与停点间插值色 ≥4.5:1；高亮胶囊文字 `accentText / #FFFFFF` ≥4.5:1 | 构建脚本 `contrast` 实算（含新增项 `onAccent / #4F46E5`、`onHero / #7C3AED`）+ 前端守护测试对渐变插值采样 |
  | 7 | 15 页 × 3 风格逐页走查：背景、顶栏、主按钮、导航高亮、表格/表单/弹窗/标签/卡片取色一致；44px；减少动态效果下装饰动画 0。**1.1.0 补充（B 风格管理端，每页一次）**：顶栏为渐变且渐变与用户端首页横幅同色系；品牌、13 个导航链接、风格切换触发器、退出按钮的文字/图标肉眼清晰；当前页高亮为白色胶囊 + 强调色文字、与其余链接区分明显；键盘 Tab 到顶栏各控件时焦点环可见；导航换行（窄屏、13 项）时胶囊容器不变形、各控件 ≥44px；同一浏览器切到用户端页面后，B 风格用户端顶栏仍是白底 + 黑色高亮胶囊（零回归目视确认）；neon/terminal 管理端顶栏仍为深色底，当前页高亮为各自既有样式 | 人工走查清单（视觉项，不能自动化，写入 test_plan 的人工验证清单） |
  14 页 + 登录页 + 布局的改动清单见 module_design MOD-071。
- Consequences: 正向：用户端零回归（所有新规则双重限定，用户端规则不改）；管理端 B 风格不再是"白底顶栏 + 黑色高亮"，Q-B1=B 的三项要求都落在同一个文件、同一作用域内；完成口径大部分可自动化，对渐变的对比度有"停点 + 插值采样"两级守护。负向：第 7 项依赖人工走查；顶栏白字在渐变右端（`#DB2777`）余量只有 0.1（4.60 对 4.5），若日后有人调整 `hero` 渐变，须同步更新 `contrast` 并通过守护测试；构建脚本不会自动解析渐变，该口径靠测试而非构建期保证；半透明深色叠加层的"恒更暗"论证依赖"叠加色只能是深色"这条守护断言；白色高亮胶囊与"强调色填充"相比更克制，若用户期望填充色，见 OQ-11 的备选（只改 `bento.web.css` 一条规则）。

### ADR-076: 替代"管理端固定风格 B"（Supersedes ADR-030，修订 ADR-027 第 1 条）
- Status: Proposed（基线 ADR-030 → Superseded by ADR-076）
- Type: constraint-driven
- Context: REQ-FUNC-135（替代 REQ-FUNC-076）、US-144、AC-144-01~04。
- 约束来源：用户 Q3=A（管理员可在顶栏切换三套风格，默认 B）；`requirements_spec.md` REQ-FUNC-135。
- 被排除方案：保留 `forAdminRoute()` 强制 B 并另加"管理端手动覆盖"（两套状态并存，易冲突）。
- Decision: 删除路由守卫中对管理端强制 B 的分支与 `useThemeStore.forAdminRoute()`；管理端路由进入时改调 `useAdminThemeStore.enter()`（应用设备记忆/当前值），随后在有管理员令牌且未对账时调用 `reconcile()`；用户端分支保持基线逻辑（`router/index.js:71-73`）。基线 ADR-030 中"后端 `IsMember` 对管理员令牌访问 `/me/theme` 返回 403"的部分继续有效，且是 C-33 的一半保证。ADR-027 第 1 条（"管理端恒为 B，不读取设备记忆"）改为"管理端读取 `ocap_admin_theme`"，其余五条不变。
- Consequences: 正向：规则单一、无强制分支。负向：基线中"管理端固定 B"的断言测试须同步更新（AC-144-04）：`frontend/tests/theme.spec.js:121-133`、`qa_unit_theme.spec.js:150-156,250-262`、`qa_int_theme.spec.js:48-63`、`qa_e2e_theme.spec.js:147-156`，以及后端 `backend/tests/` 中涉及管理端风格的用例（MOD-073 逐个核对）。

### ADR-077: 小程序不改动
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-126（小程序显示一致）、超出范围清单（小程序无管理端）、画像 P6（契约文件同步）。
- 约束来源：需求"超出范围"第 1 条；代码事实：`git grep -n "specific" -- miniprogram` **无任何命中**；`pages/phone/index.vue:68-69` 只用 `auto_bound` 的数量；`pages/units/index.vue` 的选项文案来自 `/units/options` 的字段原值与 `label`（Q-AP-05=A 不变）；`pages/index/index.vue:81` 只数身份列表长度；`miniprogram/utils/api.js` 无任何管理端调用。
- 被排除方案：为"显示一致"在小程序侧新增格式化代码（无展示点，无意义）。
- Decision: 小程序零代码改动、零契约改动；"一致"由后端输出保证（ADR-069）。若将来小程序新增展示 `specific_part` 的页面，自然读取到新格式。
- Consequences: 正向：无小程序构建/发布影响。负向：无（小程序侧没有可测试的新增行为；GROUP_D 以"小程序现有用例零新增失败 + 契约测试 `test_miniprogram_api_routes_exist_and_support_method` 通过"作为证据）。

## 开放问题 / ASSUMPTION

| ID | 内容 | 类型 / 影响 |
|---|---|---|
| OQ-01 | Q-AP-08（历史文本不改写）用户已答 A（phase_status.md 2026-11-11T22:18:16）；Q-AP-09 已由"全部按照推荐"覆盖。核实结果见 ADR-068：无结构化冗余副本需要同步 | 已关闭，仅登记 |
| OQ-02 | `[ASSUMPTION]` "纯数字"只认 ASCII `0-9`；全角数字（如"１"）、其他文种数字按"含非数字内容"原样保留。需求只写"纯数字"，未提全角 | 需用户/PM 确认；可让 PM 在测试环境只读统计"含非 ASCII 数字字符的楼栋/单元/楼层/户号"条数，若为 0 则无影响 |
| OQ-03 | `[ASSUMPTION]` 规则（5）仅在楼层非空且去"层"后的 `stem` 非空时判定；户号以 `stem+"层"` 开头才省略，不要求户号其余部分有特定形态（"1层楼"也算开头匹配） | 与 REQ-FUNC-124 字面一致；边界走查见 AC-133-04/08/09 |
| OQ-04 | 部署顺序建议"停 `ocap-backend` → `migrate` → 启动"，避免迁移与重启之间旧代码用旧规则写入单条编辑造成新旧混杂；若不停服务则窗口内的写入需事后用 MOD-066 核对命令复查。具体步骤由 GROUP_E1 在 deployment_plan 给出，并含迁移前 `dumpdata registry.registryunit`（不含个人信息）备份 | E1 要求；设计不自行 ssh |
| OQ-05 | `[ASSUMPTION]` 数据迁移不刷新 `updated_at`（只改派生标识，不视为业务修改） | 如需刷新，仅改 MOD-065 一行 |
| OQ-06 | `[ASSUMPTION]` 管理员偏好接口不设限流（同基线 OQ-T10，只改本人一个字段） | PM 门控确认 |
| OQ-07 | **已关闭（1.1.0）**。管理端 B 风格主按钮改用强调色 `--accent`（#4F46E5）、顶栏渐变、导航高亮改强调色系，均已由用户 Q-B1=B（2026-11-11T22:43:12）确认，仅作用于管理端；对比度（白字/#4F46E5 = 6.29）由构建脚本实算校验。具体取色与形态的细节见 OQ-11、OQ-12 | 已关闭 |
| OQ-08 | 审计详情与自由文本中既有的旧格式字样保持原样（Q-AP-08=A，ADR-068）；本次没有找到需要同步的结构化冗余副本 | 已知现象，非阻断 |
| OQ-09 | `[ASSUMPTION]` 管理端窄屏（<768px）不新增底部标签栏，顶栏导航允许换行（需求"不做布局重构"）。窄屏仅保证可用与 44px 点击区域 | 走查清单项 |
| OQ-10 | REQ-NFUNC-23 前半仍为 `[INFERRED]`（≤60 秒）；本设计估算迁移约 58 条批量更新语句，远小于上限 `[ESTIMATE]`，需测试环境实测 | 沿用需求中的待确认项 |
| OQ-11 | `[ASSUMPTION]`（1.1.0）Q-B1=B 只说"导航当前页高亮用强调色"，未给形态。本设计选"白色胶囊 + `--accent-text` 强调色文字"（H1），理由：`#4F46E5` 是渐变起点色，直接填充会在顶栏左段与背景同色；`--accent-2` 白字不达标。导航容器选半透明深色而非用户建议的半透明白（后者在渐变右端白字仅 3.77:1，不达标）。若用户走查后希望"强调色填充"，备选 H2：胶囊 `background: var(--accent)`、`color: var(--on-accent)`，加 `box-shadow: 0 0 0 2px var(--on-hero)` 描边，只改 `bento.web.css` 的一条规则，对比度已有 `onAccent / #4F46E5` 覆盖，其余设计不变 | 视觉走查（口径 7）请用户确认形态；改选 H2 不触发其他设计变更 |
| OQ-12 | `[ASSUMPTION]`（1.1.0）`--hero` 渐变与 `--on-hero` 不变（用户端首页横幅同源）；顶栏白字在渐变右端余量仅 0.1（4.60 对 4.5，插值最小 4.592）。渐变色停点之间的校验由前端守护测试补足，`build.mjs` 不解析渐变（`schema.mjs:68` 只接受单色），本次不改构建脚本 | 若日后调整 `hero`，须同时改 `contrast` 项并通过守护测试；是否把渐变校验并入构建脚本留作后续改进，不在本次范围 |
