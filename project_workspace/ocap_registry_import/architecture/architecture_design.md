<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-10T22:02:14+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>../ocap/architecture/architecture_design.md (基线)</file>
    <file>../ocap/architecture/module_design.md (基线)</file>
    <file>../ocap/architecture/tech_stack.md (基线)</file>
    <file>../ocap_ui_theme/architecture/architecture_design.md (编号参照，至 ADR-033)</file>
    <file>phase_status.md (clarifications：用户 2026-11-10 对 Q1~Q6 的答复)</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：业主清册导入增强（INCREMENTAL）

> 编号接续：全仓已用最大 ADR-033 / MOD-029 / IFC-151（`grep` project_workspace/ocap*/architecture/ 与 development/ 核实），本次从 **ADR-034 / MOD-030 / IFC-152** 起。
> 本文只做设计到接口签名，不含实现代码。仓库事实以 `文件:行` 引用，均已读取核实；网页事实标 `[WEB: URL，访问日期]`。
> **0.2.0（DRAFT）**：已写入用户 2026-11-10 对 GROUP_B-1 问题的答复（Q1 初次使用/统一上传、Q2=A、Q3=A、Q4=A、Q6=B，见文末"已答复问题"），0.1.0 中的待定标记已全部去除。Q1 的落地口径由 PM 给出、**待用户确认**（见 ADR-037），其余无阻断项。

## 架构概览

### 本次改动在现有系统中的位置

| 层 | 现状（基线，已核实） | 本次改动 |
|---|---|---|
| `registry` 模型 | `RegistryUnit` 四级必填、`specific_part` 由 `save()` 拼成"楼-单-层-户"（`backend/apps/registry/models.py:5-22`）；`RegistryPhone` 挂在专有部分下、无姓名（`models.py:25-32`） | 专有部分增类型、面积，单元/楼层可空；新增 `RegistryOwner`（一位业主一条）；`RegistryPhone` 增 `owner` 外键 |
| `registry` 视图 | 单条登记手机号整体覆盖且≤10个（`views.py:92-112`）；导入逐行 `get_or_create`、预检不校验手机号、坏手机号既计失败又计导入（`views.py:149-169`）；xlsx 在第 5001 行截断（`views.py:204-206`） | 导入重写为"计划 + 应用"两阶段（ADR-038）；新增 owners 接口、模板下载、格式说明接口；列表加类型/面积/业主/筛选 |
| `residency` | `certify_owner(user_id, unit_id, source)` 已含户主先到先得与同住人升级（`backend/apps/residency/services.py:14-42`）；手动认证只比对手机号（`residency/views.py:44-51`） | 加一个可选的审计来源参数；新增 `auto_bind.py` |
| `accounts` / `identity` | 注册：`RegisterView` → `AccountService.register_by_phone`（`accounts/views.py:85-96`、`accounts/services.py:168-185`）；绑定手机号：`PhoneBindView` → `IdentityService.bind_phone`（`identity/views.py:35-45`、`identity/services.py:47-63`） | 两个视图在成功后调用自动绑定，响应增加 `auto_bound` 字段 |
| Web 前端 | `AdminRegistry.vue`（无模板/说明/类型/面积，结果为 JSON 文本，`:100-108`）；`Units.vue` 固定四级下拉（`:6-20`）；axios 超时 15 秒（`frontend/src/shared/http.js:25`） | 管理页重做导入流程；用户端逐级选择动态跳级、显示类型面积；注册/绑定手机号后显示自动绑定提示 |
| 小程序 | **有同类页面** `miniprogram/pages/units/index.vue`（四级 picker）与 `miniprogram/pages/phone/index.vue`（绑定手机号，无注册页）；管理端功能不在小程序 | 纳入：units 页动态跳级并显示类型面积；phone 页显示自动绑定提示 |
| 契约文件 | `frontend/src/shared/api.js:131-140`（清册管理）、`:38`（options）；`miniprogram/utils/api.js:21`（options） | 同步修改（画像 P6）；`backend/tests/integration/test_frontend_contract.py` 会解析 api.js 并逐个 `resolve()` 路由 |

### 设计要点（一句话）

清册由"专有部分 → 手机号"改为"专有部分 → 产权业主（姓名）→ 手机号"，业主是 `RegistryOwner` 新表；认证比对仍只看 `RegistryPhone(unit, phone)`，因此认证链路（`RegistryService.phone_registered`、`certify_owner`）不改语义（C-21）。导入把校验与写入拆开：同一个纯函数"计划"产出结果，预检只返回计划，正式导入把计划批量写入，从构造上保证预检与正式一致（REQ-FUNC-093）。

### 关键质量属性

| 属性 | 需求 | 落点 |
|---|---|---|
| 性能：20000 行、5 MB，预检/正式各 ≤ 60 秒 | REQ-NFUNC-015 | ADR-038、ADR-040，及下一节"GR-A-001 condition 处理" |
| 业主数量无上限 | REQ-NFUNC-011、REQ-FUNC-087 | ADR-034（无 JSON/定长结构）；owners 接口不设业务上限 |
| 隐私：姓名/手机号仅管理员页面可见 | REQ-NFUNC-012 | 用户端 `options`、自动绑定提示不含姓名、手机号；审计 detail 不含姓名（ADR-043、IFC-152） |
| 兼容：既有数据与认证不变 | REQ-FUNC-094、C-21、C-22 | ADR-035、ADR-037 |
| Excel/WPS 可用、编号类列按文本 | REQ-NFUNC-013 | ADR-039、ADR-041 |
| 审计 | REQ-NFUNC-014 | 复用既有审计动作，不新增（`backend/apps/core/audit.py:11-15`）；见 ADR-043 |

## GR-A-001 condition 处理：20000 行 / 60 秒的性能、超时与前端提示方案

> 对应 GR-A-001 condition 与 Q-RI-23（用户可改口径，以用户为准）。结论先行：**同步处理可行，但必须同时改后端算法（逐行 ORM → 批量）和三处超时配置（axios、nginx、gunicorn）；后两者无法在仓库内核实，列为 High 风险并要求 E1 阶段核验。**

### 1. 为什么现有写法不行

现有导入对每个数据行至少执行 `get_or_create`（1~2 条查询）加每个手机号一次 `get_or_create`（`backend/apps/registry/views.py:158-167`），且在循环内逐条提交。20000 行约 6 万次以上往返，测试环境 MySQL 在局域网另一台主机（`.env` 的 `DB_HOST`，画像 P7），每次往返按 1~3 ms 估算就是 60~180 秒 `[ESTIMATE]`，不满足 60 秒。

### 2. 性能方案（ADR-038）

| 环节 | 方案 | 查询量级（20000 行、每行一个独立专有部分的最坏情形） |
|---|---|---|
| 读文件 | xlsx 用 `openpyxl.load_workbook(read_only=True)` 流式读，读满"表头 + 20001 行"即停并报"行数超限"；csv 用标准库 `csv`。全空行跳过且不计入行数 | 0 次 DB |
| 行级校验 | 纯 Python，一次遍历：规范化文本、类型/面积/姓名/手机号/长度校验 | 0 |
| 查重（专有部分） | 以规范化后的专有部分标识为键，按 500 个一批 `filter(specific_part__in=…)` 读出已有专有部分，再按 `unit_id__in` 批量读出其业主与手机号，全部放入内存字典 | 约 `⌈units/500⌉ × 3`，20000 个 → 约 120 次 |
| 查重（业主、手机号） | 全在内存字典中比较：同专有部分内"姓名 → 业主"、"手机号 → 业主姓名"，文件内先到先处理 | 0 |
| 写入 | 单个 `transaction.atomic()`：`bulk_create(units, batch_size=1000)` → 按标识回查 id → `bulk_update(units, ["unit_type","area","updated_at"], batch_size=500)` → `bulk_create(owners)` → 回查 id → `bulk_create(phones)` | 每类约 `⌈n/1000⌉ × 2` 次，合计 < 100 次 |
| 合计 | **约 200~300 次查询**（对比现状约 6 万次） | 估算 DB 耗时 < 15 秒，xlsx 解析 + 内存计划 < 10 秒（树莓派），总计约 25 秒 `[ESTIMATE]`；留出 2 倍余量 |

要点：
- MySQL 的 `bulk_create` 不回填主键（Django 仅在支持 `RETURNING` 的后端回填），所以"创建后按键回查 id"是必须步骤，不能假定 `obj.pk` 有值。
- `bulk_create` 不调用 `save()`，因此 `specific_part` 必须由计划阶段用同一个函数 `build_specific_part()` 计算后传入；模型 `save()` 也调用同一个函数，保证两条路径一致（ADR-035）。
- `bulk_update` 不会刷新 `auto_now` 字段，`updated_at` 须显式赋值。
- 批大小受 SQLite 变量上限（测试库）约束，`IN` 列表一批 500 个。
- **测试可验证的预算**：在 SQLite 测试库上用 20000 行合成文件断言"总查询数 ≤ 300"，这是对算法正确性的回归保护；真实耗时（60 秒）仍须在画像 P7 测试环境实测（AC-100-07/08 的口径）。

### 3. 超时处理（ADR-040）

分层时限，**内层先到、外层兜底**：

| 层 | 值 | 谁生效 | 出处 / 状态 |
|---|---|---|---|
| 服务端软期限 `REGISTRY_IMPORT_TIME_BUDGET_SECONDS` | 60 秒（与 REQ-NFUNC-015 同值，配置项，测试可调小） | 视图入口取 `time.monotonic()`，解析后、每 1000 行计划、每个写入批次后检查；超限抛 `ImportTimeout` | 新增 |
| gunicorn worker `--timeout` | 目标 **90 秒**（> 软期限 30 秒余量） | gunicorn 默认 **30 秒**，超过则杀 worker，客户端得到 502 `[WEB: https://gunicorn.org/reference/settings/，2026-11-10]`。目标机 `ocap-backend.service` 的 `ExecStart` 参数**不在仓库内**（画像 P3 注明 `deploy/systemd/` 无该单元；`.claude/skills/ocap-deploy/SKILL.md` 仅有 `ocap-run-due-jobs` 相关内容且 `grep -n "timeout\|--workers\|ExecStart"` 无 gunicorn 参数） | **未核实**，High 风险 R1 |
| nginx `proxy_read_timeout` / `proxy_send_timeout`（**仅 ocap 站点 8090** 的 `/ocap/api/`、`/api/`） | 目标 **90 秒** | nginx 默认均为 **60 秒** `[WEB: https://nginx.org/en/docs/http/ngx_http_proxy_module.html，2026-11-10]`。SKILL.md:179-186 描述的两处配置要点中没有任何超时指令，据此推断仍为默认 60 秒（推断，需到目标机核实） | **未核实**，High 风险 R1 |
| nginx `client_max_body_size` | 目标 **6m**（> 5 MB 上限） | 默认 **1m**，超出返回 413 `[WEB: https://nginx.org/en/docs/http/ngx_http_core_module.html，2026-11-10]`；SKILL.md:179-186 未出现该指令 | **未核实**，High 风险 R1 |
| 外网入口：阿里云 VPS nginx(443) + frp，及 Freeark nginx 的 `^~ /ocap/` 段 | 不处理 | **不在本次范围，列为已知限制**（Q6=B）：REQ-NFUNC-015 的 60 秒验收仅限内网入口 `http://192.168.31.51:8090/ocap/`；经外网入口时 5 MB 上传与 60 秒处理可能被这两层的默认值（1m / 60 s）拦截。本次不设计、不修改这两处（P7 同机共存约束；P8 禁止改动 Freeark） | 已知限制 |
| 浏览器 axios | 导入/预检请求单独设 **100 秒**（> 90 秒） | `frontend/src/shared/http.js:25` 全局 `timeout: 15000`，不改会在 15 秒误判超时；axios 支持按请求覆盖 `timeout`，无需改全局值 | 仓库已核实 |

**超时后的行为**：

| 场景 | 行为 | 数据状态 |
|---|---|---|
| 预检超时 | 返回 `504 IMPORT_TIMEOUT`，提示"处理超过 60 秒，请把文件拆成较小的几份后重试" | 预检不写库，无影响 |
| 正式导入在软期限内超时 | 正在进行的事务整体回滚，返回 `504 IMPORT_TIMEOUT`，提示同上并明确"清册未发生任何改变" | **全有或全无**（单事务），不会留下半个文件 |
| gunicorn / nginx 先于软期限断开（配置未改的情形） | 连接断开，事务随 DB 连接关闭回滚；客户端收到 502/504（HTML 或空体）或连接错误 | 回滚，但客户端无法得知；前端按下表处理 |
| 客户端等待超过 100 秒（网络问题） | axios 抛 `ECONNABORTED` | 服务端可能仍在处理并可能提交成功；结果**未知** |
| 并发导入（双击、两个管理员） | 后到者在写入时撞唯一约束，回滚并返回 `409 IMPORT_CONFLICT`，提示"有其他导入正在进行，请稍后重试"；前端在处理期间禁用按钮并只发一个请求 | 回滚，无脏数据 |

**重复导入是安全的**：合并规则只增不删、同名追加手机号、类型面积仅用非空值覆盖（REQ-FUNC-092），因此"结果未知"时重新预检/导入同一文件是幂等的，前端据此给出提示。

### 4. 前端"处理中"与超时提示方案

| 状态 | 展示 |
|---|---|
| 点击"预检"/"确认导入"后 | 立即打开不可关闭的进度对话框：旋转图标 + "处理中，最长约 60 秒，请勿关闭或刷新页面"，并启动秒表显示已等待秒数；"选择文件""预检""确认导入""下载模板"按钮全部禁用（防重复提交） |
| 返回结果 | 对话框切换为结果表（新增/更新专有部分、业主、手机号、失败行数、被修改项）；"处理中"状态消失（AC-100-08）；失败 > 0 时显示"下载错误清单"（ADR-042） |
| 收到 `IMPORT_TIMEOUT` | 对话框显示固定文案"处理超时（超过 60 秒）。清册未发生任何改变。请把文件拆成较小的几份后重试。"（预检与正式导入共用，预检本就不写库） |
| 收到 `IMPORT_CONFLICT` | "有其他导入正在进行，请稍后重试。" |
| 收到 502/504 或 `ECONNABORTED`/无响应 | "与服务器的连接中断，导入结果未知。请刷新清册列表核对；重复导入同一文件是安全的（只增不删）。" 并给"刷新列表"按钮 |
| 其他错误（如缺列、行数超限） | 沿用 `errorText(e)`（`frontend/src/shared/format.js`），缺列时把 `details.columns` 渲染为列名并显示"请使用新模板" |

小程序无管理端，不涉及。

### 5. 本方案仍无法保证的部分（风险，已入 tech_stack）

- 目标机 gunicorn 的 worker 数与类型未知：同步 worker 数为 1 时，一次 60 秒导入会让整个后端对其他用户不可用（R2）。
- 20000 行实际耗时依赖目标机 MySQL 延迟，`[ESTIMATE]` 未经实测，须在 PHASE_09 前用合成文件在测试环境实测（R3）。
- Q-RI-23 的计量口径（无并发、单管理员）保持默认；若用户改为有并发，需重估（R2）。
- 外网入口（VPS nginx + frp、Freeark nginx）不在本次范围：REQ-NFUNC-015 的 60 秒验收只在内网入口 `http://192.168.31.51:8090/ocap/` 进行（Q6=B）；外网上传大文件或长耗时导入可能先被默认值拦截（413/502/504），列为**已知限制**。

### E1 要求（R1/R2，对 GROUP_E1 的明确要求）

1. 在 deployment_plan 中列出**只读核实清单**：`ocap-backend.service` 的 `ExecStart`（gunicorn `--timeout`、`--workers`、worker 类型）、ocap 站点 8090 的 `client_max_body_size`、`proxy_read_timeout`、`proxy_send_timeout`，以及 `/ocap/` 与 `/api/` 的 location 是否继承同一设置。
2. 对核实结果给出**调整方案**（目标值 gunicorn `--timeout 90`、worker ≥ 2、nginx 三项如上），含改前备份、`nginx -t` 后 `reload`、`systemctl daemon-reload` + 重启、验证、回滚步骤。
3. 调整范围**仅限画像 P7 允许的对象**：`ocap-backend` 单元与 ocap 站点 8090 配置。**不得触碰** Freeark 的服务、端口、目录、库与 nginx 配置，也不涉及 VPS nginx/frp。
4. 执行方说明（与画像 P9 一致）：子代理不得 ssh（E2 除外），因此"只读核实"由 PM 经只读 ssh 执行（P9 允许）或写入 E2 预检步骤；"调整"只在 E2 经用户当轮授权后执行。若核实发现无法在上述范围内达到目标值，E1 须在 deployment_plan 中如实标注并升级给 PM，而不是扩大修改范围。

## 部署视图

仅使用画像 P7 中存在的环境（"测试"；"生产"无）。不用 Docker（P8）。

| 组件 | 运行单元 | 环境 | 变更 |
|---|---|---|---|
| Django 后端 | systemd `ocap-backend`（gunicorn 127.0.0.1:9000） | 测试 | 代码 + 迁移 `registry/0002~0004`（手写）；**须迁移并重启 `ocap-backend`**；gunicorn `--timeout` 与 worker 数须核实/调整（R1、R2） |
| ocap nginx 站点 | `/etc/nginx/sites-available/ocap`（监听 8090，内网入口） | 测试 | **仅核实并按需调整本站点**：`client_max_body_size 6m;`、`proxy_read_timeout 90s;`、`proxy_send_timeout 90s;`；`nginx -t` + `reload`（SKILL.md:80、:194），改前备份。核实与调整方案由 GROUP_E1 给出（见下"E1 要求"） |
| Freeark nginx（`^~ /ocap/` 段）、阿里云 VPS nginx + frp | 外网入口 | 测试 | **不触碰**（Q6=B 已知限制；P7、P8） |
| Web 前端静态文件 | `npm run build -- --base=/ocap/` 产物 → `/home/yangyang/ocap/web`（画像 P4、P7） | 测试 | 重新构建并替换 |
| 小程序 | `miniprogram` 构建产物，经微信开发者工具上传 | 无 P7 环境 | 重新构建；发布流程不在画像内 |
| `ocap-run-due-jobs` timer | `deploy/systemd/` | 测试 | **无变化** |
| Freeark 服务/端口/目录/库 | — | — | 不触碰（P7、P8） |

## ADR

### ADR-034: 产权业主与手机号的数据结构
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-090/098 要求"一位业主一条记录：姓名必填、手机号选填、同一专有部分内手机号唯一"；REQ-FUNC-086/092 要求同名业主可有多个手机号（AC-094-03、AC-099-02）；REQ-FUNC-087 / REQ-NFUNC-011 要求业主数量无上限；REQ-FUNC-011 / C-21 要求认证仍只比对手机号。现状 `RegistryPhone(unit, phone)` 带 `uniq_registry_phone` 与 `phone` 索引（`backend/apps/registry/models.py:25-32`），`RegistryService.phone_registered`（`registry/services.py:7-8`）和自动绑定都依赖"按手机号查"。
- Options:
  - A. 新增 `RegistryOwner(unit, name)`，`RegistryPhone` 增 `owner` 外键、保留 `unit` 与 `(unit, phone)` 唯一约束。优：认证与自动绑定查询零改动；数量无上限；同名多手机号自然表达；手机号唯一约束仍由数据库保证。缺：`unit` 在 `RegistryPhone` 上与 `owner.unit` 冗余，需服务层保证一致。
  - B. 用 `RegistryOwner(unit, name, phone)` 取代 `RegistryPhone`。优：少一张表。缺：同名多手机号需多行同名，与"同名视为一位业主"冲突；"同一专有部分内姓名唯一"约束无法成立。
  - C. 在 `RegistryUnit` 上存业主 JSON。优：改动小。缺：MySQL 上无法对手机号建索引，自动绑定和认证需全表扫描；约束全靠应用层；SQLite 测试库行为不同。
- Decision: 选 A。`RegistryOwner.name` 在 `(unit, name)` 上唯一；`RegistryPhone.owner` 为非空外键（经 ADR-037 回填后收紧）；`RegistryPhone.unit` 保留并由服务层保证等于 `owner.unit`。
- Consequences:
  - 正向：认证/自动绑定的查询与索引沿用；数量无上限；唯一性由库保证。
  - 负向：`tests/support.py:123-129` 等直接 `RegistryPhone.objects.create(unit=…, phone=…)` 的夹具须改为经业主创建（见 module_design"数据迁移"的测试影响清单）；`unit` 冗余需在 owners 接口和导入引擎中统一处理。

### ADR-035: 单元/楼层可空与专有部分标识的兼容
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-091 要求单元、楼层可空，标识按已填层级以"-"拼接，已有标识不变（AC-098-05）；AC-098-01/06 要求户号可为"A-088"并得到标识"车库-A-088"。现状四级全必填，`save()` 恒拼四段（`models.py:20-22`），手工新增校验"各级不得含 `-`"（`views.py:177-181`），唯一约束 `uniq_registry_unit` 与 `specific_part unique`（`models.py:10,15-17`）。
- Options:
  - A. 空层级存空串 `""`（列保持 NOT NULL，加 `blank=True, default=""`），`specific_part` 由 `build_specific_part()` 只拼非空段；导入按 `specific_part` 匹配；保留两个唯一约束。优：MySQL 与 SQLite 的唯一约束行为一致（空串参与比较，`NULL` 不参与）；沿用 M-SA-001 的教训；已有数据不需改值。缺：不同层级组合可能拼出相同标识（如 `(1,"",3,301)` 与 `(1,3,"",301)` 均为"1-3-301"），靠 `specific_part` 唯一约束兜底。
  - B. 空层级存 `NULL`，用函数式/条件唯一索引。缺：MySQL 的 `NULL` 在唯一索引中互不相等，会放过重复；条件索引在 MySQL 上被忽略（M-SA-001）。
  - C. 空层级存占位符（如 `"_"`）。缺：占位符污染标识与显示，且与真实取值冲突。
- Decision: 选 A，并规定：
  1. 导入与单条新增都以 `build_specific_part()` 的结果为匹配键；命中已有记录但四级取值元组不同（上述拼接碰撞）时，该行失败，原因"专有部分标识与已有记录冲突"。
  2. 楼栋、单元、楼层不得含 `-`（沿用 `views.py:180` 的规则并扩展到导入，减少碰撞）；**户号允许含 `-`**，因 AC-098-01/06 明确要求"A-088"。
  3. 加宽列以消除现有隐患：`floor`、`room` 由 16 加宽到 32（现有校验允许 32，`views.py:180`、`:186`；MySQL 严格模式下 17~32 字符会报"Data too long"），`specific_part` 由 100 加宽到 140（4×32+3=131）。加宽迁移无数据风险。
  4. 键比较使用 `casefold()`：MySQL 默认排序规则大小写不敏感，若只在 Python 里区分大小写，同一批里的"a-088"与"A-088"会在 `bulk_create` 时撞唯一约束。此规则对 ASCII 大小写差异生效，属实现层面的细节，记入"开放问题"A-3。
- Consequences: 正向：无需改既有记录；两种数据库一致。负向：标识碰撞靠约束兜底，用户会看到"标识冲突"错误；`-` 规则对楼栋等是"新增到导入的收紧"（现有手工新增本来就禁止）。

### ADR-036: 专有部分类型与面积的存储
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-088（类型固定五值，新建必填）、REQ-FUNC-089（面积平方米、2 位小数、车位必填）、REQ-FUNC-094（既有记录为"未登记"）。
- Options:
  - A. `unit_type` 为可空 `CharField(max_length=10, choices=…)` 存英文代码（`RESIDENCE/APARTMENT/SHOP/PARKING/OTHER`），中文标签由常量映射；`area` 为可空 `DecimalField(max_digits=10, decimal_places=2)`。优：固定集合无需建表；`Decimal` 无二进制浮点误差，MySQL 精确存储；`NULL` 即"未登记"。缺：新增类型需改代码（需求明确本版不扩展，Q-RI-03=A）。
  - B. 类型建字典表、外键引用。缺：为"固定集合"引入表与迁移，超出需求（"管理员扩展"在超出范围清单）。
  - C. 面积存 `FloatField` 或"平方分米整数"。缺：Float 有舍入误差；整数需到处换算，易错。
- Decision: 选 A。数据库层不加 `CHECK`（MySQL 与 SQLite 行为不一致，且既有数据允许 `NULL`）；取值合法性由 `registry/import_spec.py` 的常量与统一校验函数保证（单条接口与导入共用，ADR-041）。面积技术上限为 99,999,999.99 平方米（`max_digits=10`），超出报"面积超出可登记范围"；需求未设上限（开放问题 A-2），此为存储边界而非业务限制。
- Consequences: 正向：精确、可空表达"未登记"。负向：库层无枚举保护，依赖统一校验函数——所有写入入口必须经它。

### ADR-037: 既有 RegistryPhone 数据迁移到业主结构（无名业主保留）
- Status: Proposed（Q1 的落地口径为 PM 给出，**待用户确认**）
- Type: decision
- Context: REQ-FUNC-094 与 US-101 要求既有清册继续可用（AC-101-02 认证行为不变，AC-101-04 允许仅改业主信息）；REQ-FUNC-090 要求姓名必填，但既有 `RegistryPhone` 没有姓名。用户答复（2026-11-10）：系统处于初次使用阶段，由管理员用新模板统一上传全量业主清册，**不需要为既有数据设计"补名"业务流程或界面**。**PM 落地口径（待用户确认）**：迁移不删除任何既有数据（既有 `RegistryUnit` 被 `Membership` 引用）；既有手机号以技术上最简方式保留，即每个手机号对应一位姓名为空的业主；管理员统一上传时按"专有部分 + 手机号"匹配补上姓名。无名业主只作为迁移遗留状态存在，新增/导入/单条编辑仍要求姓名必填（REQ-FUNC-090）。
- Options:
  - A. 每个既有 `RegistryPhone` 回填一位**姓名为 `NULL`** 的业主（一对一）。导入时，行里的手机号命中本专有部分某无名业主，则由该行"吸收"：把姓名写到该无名业主上，行内命中的其他无名业主的手机号并入该业主，空了的无名业主删除。优：不删既有手机号、不凭空编名、不合并不同的人；认证行为不变；`(unit, name)` 唯一约束在 `NULL` 上不冲突（MySQL 与 SQLite 唯一索引都允许多个 `NULL`）。缺：`name` 列可空；导入合并规则多一条"吸收"。
  - B. 每个专有部分回填一位无名业主，持有该专有部分全部既有手机号。优：记录少。缺：可能不同的人被并成一人；统一上传"张三(手机A)、李四(手机B)"时手机号B已被张三占用，会失败。
  - C. 迁移前强制管理员补全姓名。缺：违反 REQ-FUNC-094"不强制回填"，且与"统一上传"的口径不符。
  - D. 用"业主1/业主2"占位名。缺：编造数据，与真实姓名混淆。
  - E. 迁移时删除既有手机号，等待统一上传重建。缺：删数据，破坏认证（`phone_registered` 依赖手机号）与 `Membership` 引用的清册来源；PM 口径明确不得删除。
- Decision: 选 A（PM 落地口径）。不提供任何"补名"页面或流程：无名业主仅在管理端列表显示"（未登记姓名）"，其消除方式只有管理员统一上传（吸收规则，见 module_design MOD-031 plan_import 第 4 步）或在业主对话框中手工填名。迁移分三步（见 module_design"数据迁移"）。
- Consequences:
  - 正向：认证零变化；不删数据；管理员只需上传一次全量文件。
  - 负向：库中存在 `name IS NULL` 的合法业主，所有读写路径要处理；导入合并多一条吸收规则（见 notes：复杂度评估，仅在 plan 阶段多一个分支，不影响迁移）。若用户不认可 PM 口径，改选 B 只需改 0003 回填函数与吸收规则。

### ADR-038: 导入引擎——"计划 + 应用"两阶段、批量写入、单事务
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-093（预检与正式规则一致，修复现有缺陷）、REQ-FUNC-092（合并规则）、REQ-NFUNC-015（20000 行/60 秒）。现有缺陷：预检分支 `continue` 跳过了手机号校验（`views.py:156-157` 对比 `:163-166`）；一行多个手机号中有坏号码时该行既计 `failed` 又计 `imported/updated`（`views.py:162-169`）。
- Options:
  - A. 保留逐行 ORM 写法，只修缺陷。缺：约 6 万次往返，达不到 60 秒（见上节）。
  - B. 计划/应用分离：`plan_import(rows, db_snapshot) -> ImportPlan` 为纯计算；预检返回计划，正式导入在单个事务内批量写入同一个计划。优：预检与正式共用同一份校验代码，无法分叉；可在 SQLite 上断言查询数；超时可整体回滚。缺：需把已有单元/业主/手机号读入内存（20000 行量级，内存可忽略）。
  - C. MySQL `LOAD DATA`/`INSERT … ON DUPLICATE KEY` 原生语句。缺：与 SQLite 测试库不兼容，违背"测试跑在 SQLite"（画像 P4）；合并规则（同名追加、类型冲突）难以用单条 SQL 表达。
- Decision: 选 B。规则与顺序见 module_design MOD-031。关键决定：
  1. **每行独立校验**：新专有部分的每一行必须自带类型（AC-096-02），车位每行必须自带面积（AC-096-07）；多行同一专有部分时，模板示例每行重复类型与面积。已存在的专有部分，文件中类型/面积留空则不修改（AC-099-04）。
  2. **专有部分级一致性**：同一专有部分的各合法行里非空类型不唯一 → 这些行全部失败（AC-096-05）；非空面积不唯一（按数值比较，89.5 与 89.50 视为相同）→ 这些行全部失败，原因"同一专有部分的面积不一致"，与类型冲突同样处理（Q2=A）。
  3. **行级原子**：一行有任一手机号冲突/格式错误，整行失败，该行任何内容都不写入、只计失败一次（AC-100-04）。
  4. **业主级**：同专有部分内姓名（去首尾空格）相同 → 同一业主，手机号并集；姓名不同但手机号已被该专有部分另一位业主占用 → 该行失败（AC-099-07）；同名同号重复行不报错（AC-094-05）；手机号命中本专有部分**无名业主**（迁移遗留，ADR-037）时，该行吸收该无名业主，不算"被另一位业主占用"。
  5. **结果口径**：`imported`/`updated` 为专有部分个数，`rows_ok/rows_failed/rows_total` 为行数；同一专有部分多行时二者不同。AC-094-07 / AC-100-08 的"新增、更新、失败的行数合计 20000"在"每行一个专有部分"的数据下两种口径一致；已确认（Q3=A）20000 行验收样本按"每行一个专有部分"造数（A-4）。
  6. **写入**：单个事务；每批后检查软期限；`IntegrityError` → 回滚并返回 `IMPORT_CONFLICT`。
  7. **审计**：沿用 `REGISTRY_IMPORTED`，detail 含条数与 `dry_run`，不含姓名、手机号（REQ-NFUNC-014、AC-094-06）。预检同样记录（沿用现状 `views.py:170-173`）。
- Consequences: 正向：预检=正式（同一代码）；修复两个缺陷；查询数可测。负向：正式导入全有或全无（超时/冲突时整体回滚），不是"超时前已写入部分"；与"逐行写入，失败行不影响其他行"不冲突——这里的失败行是**校验失败**，不是 DB 异常。

### ADR-039: 导入文件解析与列规范
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-083（csv/xlsx、5 MB、20000 行、第一个工作表、缺列整体拒绝）、REQ-NFUNC-013（Excel/WPS 可打开、编号类按文本）、Q-RI-12=A（旧 5 列文件整体拒绝）。
- 约束来源：`openpyxl>=3.1,<4.0` 已在依赖清单（`backend/requirements.txt:5`）并在用（`views.py:198-209`）；INCREMENTAL 既有栈优先；部署目标为树莓派 4 GB（画像 P7），资源受限。
- 被排除的替代方案：`pandas`（新增体积大的依赖，在 ARM 上安装/内存成本高，且本需求只需逐行读取）；`xlrd`/`.xls`（需求只支持 xlsx/csv，AC-092-04 明确拒绝其他类型）；`openpyxl` 非 `read_only` 模式（整表载入内存，5 MB 压缩的 xlsx 展开后可达数十 MB）。
- Decision（沿用 + 具体规则）：
  1. 8 个必含列：`楼栋、单元、楼层、户号、专有部分类型、专有部分面积（平方米）、业主姓名、手机号`；列顺序不限、多余列忽略；表头比较前去首尾空格，并把全角括号 `（）` 规范为半角，容忍用户改成半角括号；缺任一列 → `400 IMPORT_COLUMNS_MISSING`，`details.columns` 列出缺的列名，提示"请使用新模板"。
  2. xlsx 单元格取文本的规则（`cell_text()`）：字符串去首尾空格；整数 → 十进制整数字符串；`float` 若为整数值 → 整数字符串（避免"3.0"，AC-093-04）、否则取最短往返表示；`None` → 空串；日期等其他类型 → 视为非法值，行失败。前导零一旦被 Excel 当数字吞掉就无法恢复，所以模板把相应列预设为文本格式（ADR-041）。
  3. csv 按 UTF-8（含 BOM）读（沿用 `views.py:194`）。**Excel 中文版"另存为 CSV（逗号分隔）"默认是 GBK**，会解码失败（`文件无法解析`）；不增加编码猜测，在格式说明里提示选"CSV UTF-8"。
  4. 行数统计：全空行跳过且不计入 20000；错误行号用文件中的物理行号（表头为第 1 行）。
  5. 重复表头列：取第一列。
- Consequences: 正向：无新依赖；内存可控。负向：GBK csv 不被接受（风险 R7，靠说明缓解）；表头容错规则是对需求字面的轻微放宽。

### ADR-040: 同步处理的超时方案与分层时限（GR-A-001 condition）
- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-015、Q-RI-22=A（同步等待、显示处理中、上限 60 秒）、Q-RI-23（超时处理留给设计）、REQ-FUNC-083（处理中状态）。详细数据见上文"GR-A-001 condition 处理"。
- Options:
  - A. 同步处理 + 服务端软期限 + 单事务整体回滚 + 分层超时配置（axios 100 s > nginx/gunicorn 90 s > 软期限 60 s）。优：符合已确认的 Q-RI-22=A；超时语义简单（全有或全无）。缺：依赖三处目标机配置，其中两处未核实。
  - B. 后台异步任务 + 轮询。缺：需求已明确"不要求转后台处理"（REQ-NFUNC-015，超出范围清单第 5 项）；仓库的 `apps/jobs` 是定时任务入口，没有任务队列（画像 P3/P7 无队列服务）。
  - C. 前端把文件切成多段分别请求。缺：同一专有部分的多行会跨段，类型冲突、手机号冲突、"新增/更新"判定无法跨段正确计算，预检与正式也会不一致。
- Decision: 选 A。软期限默认 60 秒（配置项 `REGISTRY_IMPORT_TIME_BUDGET_SECONDS`）。超时与各端提示见上文第 3、4 节。
- Consequences: 正向：行为可预测、可测试（把软期限调小即可在测试中触发超时分支）。负向：超过 60 秒的文件整体被拒，管理员需拆分；若 R1 的配置未改，外层超时会先触发，用户看到的是"连接中断"而非友好提示。

### ADR-041: 模板与格式说明——后端单一来源、按需生成、认证下载
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-084（页面说明必须与实际校验规则一致，含 20000 行、车位面积必填等）、REQ-FUNC-085（xlsx + csv，xlsx 含说明页与示例行）、REQ-NFUNC-013（文本格式列）、AC-093-01~05。
- Options:
  - A. 后端 `registry/import_spec.py` 持有列定义、取值、限制常量；校验、模板（xlsx/csv）、"填写说明"工作表、`GET /admin/registry/import/spec` 都读它；模板由 `openpyxl` 按请求生成，管理员鉴权下载。优：说明与规则不可能不同步；类型清单只有一处；可单测"模板能被导入引擎无错解析"。缺：模板请求有少量 CPU（毫秒级）。
  - B. 把静态 xlsx/csv 放进 `frontend/public/`。缺：二进制入库、改规则要手改文件；无鉴权；与校验代码两处维护。
  - C. 前端生成（引入 SheetJS 等）。缺：新增前端依赖；规则又复制到前端。
- Decision: 选 A。
  - 路由：`GET /admin/registry/import/template?file_type=xlsx|csv`、`GET /admin/registry/import/spec`。**参数名用 `file_type` 而非 `format`**：DRF 把 `?format=` 当作渲染器后缀（`URL_FORMAT_OVERRIDE`），传 `xlsx` 会 404。
  - 下载需带 `Authorization` 头，所以前端用 `adminHttp.get(..., { responseType: 'blob' })` 再触发保存；不得把令牌放进 URL（通用经验）。
  - xlsx：第一个工作表"清册导入"= 表头 + 示例行；第二个工作表"填写说明"；楼栋、单元、楼层、户号、专有部分类型、面积、业主姓名、手机号各列预设文本格式 `@`；类型列加下拉数据验证。csv：UTF-8 带 BOM，表头 + 示例行。
  - 示例行（AC-093-01）：一个专有部分占 3 行（含一位无手机号业主）、一个车位（单元楼层留空）。
- Consequences: 正向：规则单一来源。负向：示例行若未删除就上传会被当真实数据导入，靠"填写说明"首行提示 + 预检结果核对缓解（风险 R8）。

### ADR-042: 错误清单下载在前端生成
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-093、AC-100-02（失败行展示行号与原因，可下载为 csv）。导入响应本来就返回全部 `errors`（≤20000 条）。
- Options:
  - A. 前端用响应里的 `errors` 生成 UTF-8 BOM 的 csv Blob 下载。优：无服务端存储、无新接口、无过期清理；不含姓名手机号（只有行号、字段、原因）。缺：刷新页面后清单丢失。
  - B. 服务端保存错误报告并给下载链接。缺：需存储、过期清理、鉴权下载接口，且报告里可能含个人信息。
- Decision: 选 A；页面表格最多渲染前 200 条并提示"完整清单请下载"，避免 20000 行 DOM。
- Consequences: 正向：简单、无隐私落盘。负向：页面刷新后需重新预检。

### ADR-043: 自动绑定的挂接点与依赖方向
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-096（触发：注册验证成功；已注册用户含微信用户首次验证并绑定手机号；清册后补不触发）、C-25（只由已验证手机号触发）、C-26（只有这两个时机）、REQ-NFUNC-014（审计来源"清册自动绑定"）。现状：注册在 `AccountService.register_by_phone`（`accounts/services.py:168-185`）里完成验证码校验并创建用户；绑定手机号在 `IdentityService.bind_phone`（`identity/services.py:47-63`）里校验验证码后设置手机号，若手机号属于他人则走合并分支（`:54-57`）；认证落库在 `MembershipService.certify_owner`（`residency/services.py:14-42`）。依赖现状：`residency.models` 导入 `registry.models`（`residency/models.py:4`），`registry.views` 在函数内延迟导入 `residency.models`（`registry/views.py:83`），`residency` 不导入 `accounts` 或 `identity`；`identity.services` 已导入 `residency.services`（`identity/services.py:13`）。
- Options:
  - A. 在 `AccountService.register_by_phone` 与 `IdentityService.bind_phone` 内部直接调用认证。缺：`accounts` 是底层模块，反向依赖 `residency` 会引入 accounts → residency → registry 的新边，并使 `AccountService` 在所有调用方（含测试夹具）处承担副作用。
  - B. 视图层编排：`RegisterView` 与 `PhoneBindView` 在服务返回成功后调用 `residency.auto_bind.AutoBindService.bind_by_phone(user)`。`AutoBindService` 只依赖 `registry.services`（查手机号→专有部分）和 `residency.services`（认证）。优：触发点恰好是"验证码已通过"的两条成功路径，且不会被登录、管理员改手机号、测试夹具创建用户触发（满足 C-25/C-26）；依赖方向 accounts.views/identity.views → residency → registry → core，无环。缺：需改两个视图和两处响应。
  - C. Django 信号（`post_save` of `User`）。缺：无法区分"验证后写入"与管理员/夹具/合并写入；会在 `User.objects.create(phone=…)` 的测试夹具上误触发；隐式、违反 C-25/C-26。
- Decision: 选 B，并规定：
  1. 注册：`RegisterView.post` 在 `register_by_phone` 之后调用，响应增加 `auto_bound`。
  2. 绑定：`PhoneBindView.post` 仅在 `result["merged"] is False` 时调用（手机号原本属于他人账号的合并分支不触发——该手机号对应账号在注册时已有机会自动绑定，合并不是"首次验证并绑定"；用户已确认 Q4=A）。换绑（`PhoneChangeView`）、手机验证码登录都不触发。
  3. `bind_by_phone` 对清册中该手机号命中的每个专有部分逐个调用 `certify_owner`，每个专有部分独立事务；已是该专有部分产权业主的跳过；同住人由 `certify_owner` 自行升级；`ApiError` 之外的异常记日志并吞掉——**自动绑定失败不得使注册或绑定手机号失败**（用户可走手动认证兜底）。
  4. `certify_owner` 增加关键字参数 `origin`；自动绑定传 `REGISTRY_AUTO`，审计 detail 增加 `origin`、`origin_label="清册自动绑定"`；`Membership.source` 保持 `"REGISTRY"`（该列 `max_length=12`，"REGISTRY_AUTO" 为 13 字符放不下，`residency/models.py:16`；需求也要求"与手动认证结果等价、身份来源均为清册"）。手动路径不传该参数，审计 detail 不变。
  5. 审计与提示中不含他人姓名、手机号（只有被绑定用户自己的 `specific_part`）。
- Consequences: 正向：触发点精确；无新依赖环；失败隔离。负向：`auto_bound` 作为响应附加字段进入两个既有接口契约，两端 api 调用方需展示提示；合并分支不触发已由用户确认（Q4=A）。

### ADR-044: 用户端逐级选择——服务端跳过空层级
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-091（对没有取值的层级自动跳过，不出现空选项）、REQ-FUNC-097（末级显示类型与面积，不显示姓名手机号）、AC-098-02/03（楼栋下全空则整级跳过；混合时空层级专有部分仍可到达）、AC-103-01~03。现状 `RegistryService.options` 按固定顺序返回楼栋→单元→楼层→房号，且用 `if unit_no:` 把空串当"未选"（`registry/services.py:15-35`、`registry/views.py:34-37`）。
- Options:
  - A. 服务端判断下一层：候选集合在某层全为空串则自动跳过并在响应的 `skipped` 中告知；若该层既有非空又有空，返回非空值并置 `has_empty=true`，客户端补一项"无单元/无楼层"，选中后把该层以空串回传。优：Web 与小程序共用同一逻辑；兼容现有响应结构（`level`、`options` 不变，只增字段）。缺：查询参数语义变化（空串表示"选了空"）。
  - B. 客户端取全部专有部分后自己拼层级。缺：数据量大、泄露不必要的信息、两端各实现一遍。
  - C. 改成单个搜索框/平铺列表。缺：偏离 REQ-FUNC-010 的逐级选择交互。
- Decision: 选 A；契约见 module_design IFC-152。末级选项由服务端给出 `label`（如"301（住宅 89.50 ㎡）"，缺项省略，不出现 `null`/空括号，AC-103-02），Web 与小程序共用。
- Consequences: 正向：两端改动小、一致。负向：参数语义变化——已有客户端只会传非空值，不受影响；车库类楼栋下房号可达数千，末级下拉需带搜索（Web 用 `filterable`，小程序 picker 无搜索，列为 Medium 风险）。

## 开放问题 / ASSUMPTION

### 已答复问题（用户 2026-11-10 原话："Q1：初次使用，管理员同一上传业主清册， Q2：A， Q3：按照推荐， Q4：A Q6：B"）

| 编号 | 答复 | 落点 |
|---|---|---|
| Q1 | 系统初次使用，管理员用新模板统一上传全量清册；不设计既有数据的补名业务流程/界面。**PM 落地口径（待用户确认）**：不删既有数据，既有手机号各成一位无名业主，统一上传时按"专有部分 + 手机号"补名 | ADR-037；module_design 数据迁移、plan_import 第 4 步 |
| Q2 | A：同一文件同一专有部分多行面积不一致 → 这些行全部失败，原因"同一专有部分的面积不一致" | ADR-038 第 2 点；module_design 校验表 |
| Q3 | 按推荐 A：响应同时给专有部分口径（`imported/updated`）与行口径（`rows_*`）；20000 行验收样本"每行一个专有部分" | ADR-038 第 5 点；A-4 |
| Q4 | A：账号合并不触发自动绑定 | ADR-043 |
| Q6 | B：REQ-NFUNC-015 的 60 秒验收限定内网入口；外网 VPS nginx/frp 不在本次范围，列为已知限制 | "GR-A-001 condition 处理"第 3、5 节；部署视图 |

（Q5 起草时并入 A-3，编号保留不用。）

### 仍待确认（非阻断）

| 编号 | 内容 |
|---|---|
| C-1 | Q1 的 PM 落地口径（无名业主 + 吸收规则）待用户确认。设计不依赖补名界面，若用户改口径为 B，仅需改迁移回填与吸收规则 |
| C-2 | R1/R2（gunicorn 超时/worker 数、ocap 站点 nginx 体积与超时）仍未核实，由 GROUP_E1 给出核实清单与调整方案（"E1 要求"） |

### ASSUMPTION / 非阻断说明

| 编号 | 内容 | 依据 / 影响 |
|---|---|---|
| A-1 | 已有专有部分被导入行改类型时，若新类型为车位而面积在文件与库中都为空，则该行失败"车位的专有部分面积不能为空"（AC-096-07 字面只写了"新建"，此处推广到更新） | 保证"车位面积必填"在所有路径成立（REQ-FUNC-089）；测试阶段需覆盖 |
| A-2 | 面积无业务上限（需求开放问题），技术边界 99,999,999.99 | ADR-036 |
| A-3 | 姓名/标识比较使用 `casefold()`：ASCII 大小写不同的姓名（如 Tom/tom）视为同一人，以与 MySQL 默认大小写不敏感的唯一索引一致；REQ-FUNC-098 写的是"其余原样" | 仅影响 ASCII 字母的大小写，中文姓名无影响；若用户要求严格区分，需把 `name` 列改为二进制排序规则（MySQL 专有，SQLite 测试库不同步），需另议 |
| A-4 | 20000 行验收样本（AC-094-07、AC-100-07/08）应按"每行一个专有部分"造数；多行同专有部分的场景另用小样本 | Q3 |
| A-5 | 模板与预检结果展示的"示例行"使用明显的虚构手机号段 | 避免真实号码入库 |
| A-6 | 旧端点 `PUT /admin/registry/units/<id>/phones` 在本次**移除**，由 `PUT …/owners` 取代；唯一调用方是 `AdminRegistry.vue`，既有测试须随之改写 | 保留旧端点会允许创建无姓名业主，违反 REQ-FUNC-090 |
| A-7 | 上线后旧 5 列文件被整体拒绝（Q-RI-12=A），上线通知属运营事项 | requirements_spec 开放问题 |
