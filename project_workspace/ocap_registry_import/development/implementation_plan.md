<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T11:12:11+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.2.0 DRAFT)</file>
    <file>architecture/module_design.md (1.0.0 APPROVED)</file>
    <file>architecture/tech_stack.md</file>
  </input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：业主清册导入增强（INCREMENTAL / GROUP_C）

## 实现概览

- 模块数：9（MOD-030 ~ MOD-038），改动文件 25 个（新建 10 / 修改 15）。
- 实现顺序按 module_design 依赖拓扑：MOD-030（模型、迁移、序列化器）→ MOD-031（规格、引擎、模板）→ MOD-033（查询服务）→ MOD-032（管理端 API）→ MOD-034（自动绑定服务）→ MOD-035（触发点）→ MOD-036/037（Web）→ MOD-038（小程序）。
- 引擎按"解析 → 计划（只读纯计算）→ 应用（单事务）"三段实现，dry_run 与正式导入共用 `plan_import`，因此两次数字一致（AC-100-03）。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-030 | `backend/apps/registry/models.py` | 修改 | — | M | `build_specific_part` 只拼非空段；`unit_type/area`；新增 `RegistryOwner`；`RegistryPhone.owner` | DONE |
| 2 | MOD-030 | `backend/apps/registry/migrations/0002_owner_type_area.py` | 新建 | 1 | M | AlterField 层级/标识长度、AddField 类型面积、CreateModel 业主、AddConstraint | DONE |
| 3 | MOD-030 | `backend/apps/registry/migrations/0003_backfill_legacy_owners.py` | 新建 | 2 | M | RunPython 按手机号回填无名业主（可逆） | DONE |
| 4 | MOD-030 | `backend/apps/registry/migrations/0004_phone_owner_required.py` | 新建 | 3 | L | 校验无孤儿手机号后把 `owner` 收紧为非空 | DONE |
| 5 | MOD-030 | `backend/apps/registry/serializers.py` | 修改 | 1 | L | `RegistryOwnerSerializer`、`RegistryUnitAdminSerializer`（含类型标签、业主与完整手机号） | DONE |
| 6 | MOD-031 | `backend/apps/registry/import_spec.py` | 新建 | 1 | M | 列/限制/文案单一来源、`spec_payload`、`validate_unit_fields`、`parse_area`、`parse_unit_type` | DONE |
| 7 | MOD-031 | `backend/apps/registry/importing.py` | 新建 | 6 | H | `read_rows`、`plan_import`、`apply_plan`、`Deadline`、错误类型与行级原子 | DONE |
| 8 | MOD-031 | `backend/apps/registry/import_template.py` | 新建 | 6 | L | xlsx（数据表 + 填写说明）/ csv（UTF-8 BOM）模板 | DONE |
| 9 | MOD-033 | `backend/apps/registry/services.py` | 修改 | 1 | M | `options`（跳空层级、has_empty、房号 label）、`units_by_phone`，保留既有方法 | DONE |
| 10 | MOD-032 | `backend/apps/registry/views.py` | 修改 | 5,7,8,9 | H | IFC-152~159 全部端点、审计、权限与错误码 | DONE |
| 11 | MOD-032 | `backend/apps/registry/urls.py` | 修改 | 10 | L | 新增 6 条路由，删除 `/phones` 路由 | DONE |
| 12 | MOD-034 | `backend/apps/residency/auto_bind.py` | 新建 | 9 | M | `AutoBindService.bind_by_phone`，失败不阻断主流程 | DONE |
| 13 | MOD-034 | `backend/apps/residency/services.py` | 修改 | 12 | L | `certify_owner(..., origin=None)`，审计加 `origin_label` | DONE |
| 14 | MOD-035 | `backend/apps/accounts/views.py` | 修改 | 12 | L | 注册成功后自动绑定，响应加 `auto_bound` | DONE |
| 15 | MOD-035 | `backend/apps/identity/views.py` | 修改 | 12 | L | 首次绑定手机号成功自动绑定；合并场景不绑定 | DONE |
| 16 | MOD-036 | `frontend/src/shared/api.js` | 修改 | 10 | L | owners 全量替换、导入（dry_run、超时 100s）、模板下载、说明 | DONE |
| 17 | MOD-036 | `frontend/src/admin/registryImport.js` | 新建 | — | L | 超时文案、结果文案、错误清单 csv、下载工具 | DONE |
| 18 | MOD-036 | `frontend/src/admin/RegistryImportDialog.vue` | 新建 | 16,17 | H | 格式说明、模板下载、预检→确认→结果、处理中/超时、错误清单 | DONE |
| 19 | MOD-036 | `frontend/src/admin/AdminRegistry.vue` | 修改 | 16,18 | H | 类型/面积筛选与编辑、业主编辑、导入入口 | DONE |
| 20 | MOD-037 | `frontend/src/portal/Units.vue` | 修改 | 10 | H | 动态跳级选择、未划分层可选、末级显示类型面积、申诉引导 | DONE |
| 21 | MOD-037 | `frontend/src/portal/Register.vue` | 修改 | 14 | L | 自动绑定提示（含专有部分标识） | DONE |
| 22 | MOD-037 | `frontend/src/portal/Me.vue` | 修改 | 15 | L | 首次绑定后自动绑定提示 | DONE |
| 23 | MOD-038 | `miniprogram/pages/units/index.vue` | 修改 | 10 | M | 同 MOD-037 的跳级选择与末级标签 | DONE |
| 24 | MOD-038 | `miniprogram/pages/phone/index.vue` | 修改 | 15 | L | 绑定成功后的自动绑定提示 | DONE |
| 25 | MOD-038 | `miniprogram/utils/api.js` | 修改 | — | L | options 返回值注释 | DONE |
| 26 | 测试适配 | `backend/tests/support.py`、`smoke/test_flows_smoke.py`、`integration/test_gap_must_have.py`、`integration/test_residency_api.py`、`e2e/test_gap_journeys.py` | 修改 | 1,10 | M | 适配业主实体与 `/owners` 契约、US-102 覆盖的场景 | DONE |
| 27 | 自验证 | `backend/tests/unit/test_registry_import_smoke.py` | 新建 | 7,10 | L | 导入引擎最小冒烟（预检/正式、幂等、行级错误） | DONE |

## 需求追溯

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-092 | AC-092-01 | `import_spec.spec_payload` + `RegistryImportDialog.vue`（描述表、列规则表、说明与示例） | DONE | 页面直接展示文件类型、5 MB/20000 行、首个工作表、列规则与示例 |
| US-092 | AC-092-02 | `views.UnitOptionsView`/`AdminUnit*`/`AdminRegistry*` + `IsAdmin`/`IsMember` | DONE | 非管理员 403、未登录 401 |
| US-092 | AC-092-03 | `importing.read_rows`（>20000 抛 `IMPORT_FILE_INVALID`） | DONE | 文案"文件行数超过 20000"；解析阶段即失败，不落库 |
| US-092 | AC-092-04 | `views.AdminRegistryImportView.post`（扩展名白名单） | DONE | "仅支持 xlsx 或 csv" |
| US-092 | AC-092-05 | `views.AdminRegistryImportView.post`（`MAX_FILE_BYTES`） | DONE | 413 + "文件超过 5 MB" |
| US-093 | AC-093-01 | `import_template.build_xlsx` | DONE | 数据表 4 行示例（一单元 3 行、无手机号业主、车位）+ 第二个"填写说明"工作表；xlsx 生成路径因环境缺 `openpyxl` 未运行验证 |
| US-093 | AC-093-02 | `import_template.build_csv` | DONE | UTF-8 BOM，Excel 打开中文不乱码 |
| US-093 | AC-093-03 | `importing.read_rows` + `_fill_merged_cells`（普通模式读取，合并区域左上角值填充，按表头名映射，仅首个工作表） | DONE | DEF-008 修复后合并单元格非首行也取到值；隐藏列/第二个工作表不受影响；已用 venv 构造含合并单元格工作簿验证 |
| US-093 | AC-093-04 | `importing.cell_text` + `import_template.build_xlsx`（楼栋/单元/楼层/户号/手机号列 number_format="@"）+ `import_spec.spec_payload.notes`（CSV 提示） | DONE | DEF-007：模板列为文本格式，Excel 键入 0801 保持文本；文本原样保留，浮点整数显示为 "3"；CSV 无法控制 Excel 行为，以说明文案提示 |
| US-093 | AC-093-05 | `AdminRegistryTemplateView`（`IsAdmin`） | DONE | 非管理员 403 |
| US-093 | AC-093-06 | `importing.ImportColumnsMissing` | DONE | "缺少列：…，请使用新模板" |
| US-094 | AC-094-01 | `importing.plan_import` / `apply_plan`（业主按行累积） | DONE | 同一专有部分多行、业主数量不限；手机号逐个落库供认证比对 |
| US-094 | AC-094-02 | 同上（无业主数量上限） | DONE | 无 "10 个" 限制；200 位业主由 GROUP_D 压测覆盖 |
| US-094 | AC-094-03 | `importing._parse_row`（按英文分号拆分、去重） | DONE | "138…;139…" → 一位业主两个号码 |
| US-094 | AC-094-04 | `AdminRegistryImportView`（`IsAdmin`） | DONE | 非管理员 403，事务未开启 |
| US-094 | AC-094-05 | `_plan_row`（姓名 casefold 匹配已有计划业主） | DONE | 同名同行不重复建业主/手机号 |
| US-094 | AC-094-06 | `views` 审计 `REGISTRY_IMPORTED` | DONE | detail 仅含条数与 dry_run，不含姓名/手机号/文件名 |
| US-094 | AC-094-07 | `read_rows` 上限 + `Deadline` 全程校验 | PARTIAL | 逻辑支持 20000 行与 60 秒期限；实际性能需 GROUP_D 用 20000 行样本实测 |
| US-094 | AC-094-08 | `_parse_row`（手机号选填） | DONE | 空手机号不报错 |
| US-094 | AC-094-09 | `_parse_row`（姓名 strip 后 1~64） | DONE | "业主姓名不能为空" |
| US-095 | AC-095-01 | `AdminUnitOwnersView.put`（列表全量替换） | DONE | 无数量限制；不再有 "10 个" 提示 |
| US-095 | AC-095-02 | `RegistryOwnerSerializer`（姓名 + 完整手机号） | DONE | 管理端 `/admin/registry/**` 返回明文（US-019） |
| US-095 | AC-095-03 | `AdminUnitOwnersView._prepare` + `PHONE_RE` | DONE | 先全量校验后写库，原业主不变 |
| US-095 | AC-095-04 | 同上（`IsAdmin`） | DONE | 403 |
| US-095 | AC-095-05 | 删除 `RegistryOwner`（级联手机号），不改 `Membership` | DONE | 既有身份保留；后续认证按新清册比对 |
| US-095 | AC-095-06 | 既有 `core.masking`（用户端/申诉/审计）+ 管理端明文 | DONE | 本次未新增明文暴露面；审计不记录姓名/手机号 |
| US-095 | AC-095-07 | `_prepare`（空姓名 + 新业主 → 400） | DONE | "业主姓名不能为空" |
| US-095 | AC-095-08 | `_prepare`（手机号可为空列表） | DONE | 业主保留、手机号为空 |
| US-096 | AC-096-01 | `plan_import`（类型/面积写入 `PlannedUnit`/`PlannedUnitUpdate`） | DONE | 面积空 → 未登记 |
| US-096 | AC-096-02 | `plan_import`（新专有部分 `final_type is None`） | DONE | "专有部分类型为空" |
| US-096 | AC-096-03 | `parse_unit_type` | DONE | 文案含允许取值 |
| US-096 | AC-096-04 | `parse_area` | DONE | 非数值/≤0 / >2 位小数 / 超上限分别给出文案 |
| US-096 | AC-096-05 | `plan_import`（同组类型集合 >1 → 全组失败） | DONE | 不写入该专有部分 |
| US-096 | AC-096-06 | `ImportColumnsMissing` | DONE | 整个文件拒绝并列出缺列 |
| US-096 | AC-096-07 | `plan_import`（`PARKING` 且最终面积空） | DONE | 其余类型面积可空 |
| US-097 | AC-097-01 | `AdminUnitListView.post` + `updateRegistryUnit` | DONE | 201 返回完整行 |
| US-097 | AC-097-02 | `post`（类型白名单） | DONE | "请选择专有部分类型" |
| US-097 | AC-097-03 | `post`/`patch` 的 `_area_value` | DONE | "专有部分面积格式不正确" |
| US-097 | AC-097-04 | `AdminUnitListView.get`（`unit_type` 筛选） | DONE | 另支持 `UNSET` |
| US-097 | AC-097-05 | 同上（`IsAdmin`） | DONE | 403 |
| US-097 | AC-097-06 | `_audit(...)` → `REGISTRY_UNIT_CHANGED` | DONE | detail 含 change/专有部分 id；不触碰 Membership |
| US-097 | AC-097-07 | `post`（车位无面积） | DONE | "车位须填写专有部分面积" |
| US-097 | AC-097-08 | `post`（住宅面积可空） | DONE | 列表显示"未登记" |
| US-098 | AC-098-01 | `models.build_specific_part` | DONE | "车库-A-088" |
| US-098 | AC-098-02 | `services.options`（skipped）+ `Units.vue`/小程序（不渲染被跳过层级） | DONE | 直接展示户号 |
| US-098 | AC-098-03 | `services.options.has_empty` + 两个客户端"未划分单元/楼层"选项 | DONE | 不出现空白项，但空单元/空楼层仍可选中到达 |
| US-098 | AC-098-04 | `validate_unit_fields`（共享） | DONE | 单元/楼层为空不报错 |
| US-098 | AC-098-05 | `build_specific_part` 与非空段一致 | DONE | 四级完整时与旧规则结果相同 |
| US-098 | AC-098-06 | `plan_import` 车位路径 + `_create_owners`/`_create_phones` | DONE | 冒烟用例覆盖同类路径（CSV） |
| US-099 | AC-099-01 | `plan_import` + `_plan_row`（`plan.touched` 计 updated） | DONE | 新增业主计入"更新"计数，不删除既有业主 |
| US-099 | AC-099-02 | `_plan_row`（同名业主追加手机号） | DONE | 业主总数不变 |
| US-099 | AC-099-03 | `plan_import`（`changed` 字段 + `changes` 输出） | DONE | 前端展示被修改字段 |
| US-099 | AC-099-04 | `plan_import`（文件空值保留既有值） | DONE | 不覆盖 |
| US-099 | AC-099-05 | 导入只增不删业主 | DONE | 既有业主与已认证身份保留 |
| US-099 | AC-099-06 | 同组类型冲突 | DONE | 见 AC-096-05 |
| US-099 | AC-099-07 | `_plan_row`（手机号属不同姓名业主） | DONE | "手机号已登记给同一专有部分的另一位业主" |
| US-099 | AC-099-08 | `_parse_row` strip + casefold 比较 | DONE | "张伟 " 合并；"张伟（二）"新增 |
| US-100 | AC-100-01 | `?dry_run=1` 复用 `plan_import`；`RegistryImportDialog` | DONE | 预检显示新增/更新/业主/失败，未写库；确认后结果一致 |
| US-100 | AC-100-02 | `ImportPlan.summary.errors` + 错误表格 + csv 下载 | DONE | 表格列（行号/字段/原因）+ 可下载 csv |
| US-100 | AC-100-03 | 同一 `plan_import` | DONE | 两次失败行数与原因一致 |
| US-100 | AC-100-04 | `_plan_row` 单行一次返回错误 | DONE | 一行只计一次失败 |
| US-100 | AC-100-05 | `formatImportResult` + 表格 | DONE | 纯文字与表格，无 JSON |
| US-100 | AC-100-06 | `IsAdmin` | DONE | 403 |
| US-100 | AC-100-07 | `Deadline` + 前端 busy 状态 | PARTIAL | 30/60 秒期限逻辑具备；20000 行实测由 GROUP_D 完成 |
| US-100 | AC-100-08 | 同上 + 错误清单下载 | PARTIAL | 同上 |
| US-101 | AC-101-01 | `AdminRegistry.vue`（`unit_type_label \|\| '未登记'`、`area \|\| '未登记'`） | DONE | 列表显示"未登记" |
| US-101 | AC-101-02 | `options` 对空类型/面积的输出 | DONE | 既有认证行为不变（回归测试通过） |
| US-101 | AC-101-03 | 导入/单条补录只更新类型面积 | DONE | 业主与 `Membership` 不受影响 |
| US-101 | AC-101-04 | `AdminRegistry.saveEdit`（类型/面积为空则不发该字段）+ `patch` 不强制 | DONE | 仅改业主可保存 |
| US-102 | AC-102-01 | `accounts.views.RegisterView` + `AutoBindService` | DONE | 注册即认证，首到为 HEAD、来源 REGISTRY |
| US-102 | AC-102-02 | `RegistryService.units_by_phone` 全量遍历 | DONE | 每个专有部分独立认证 |
| US-102 | AC-102-03 | `MembershipService.certify_owner` 既有户主优先 | DONE | 已有 HEAD 时新用户为普通业主 |
| US-102 | AC-102-04 | `bind_by_phone` 无命中返回空 | DONE | 不提示错误 |
| US-102 | AC-102-05 | 注册在验证码校验之后才调用绑定 | DONE | 失败不产生身份 |
| US-102 | AC-102-06 | `identity.views.PhoneBindView` | DONE | 微信用户首次绑定触发 |
| US-102 | AC-102-07 | `certify_owner` 对 RESIDENT 升级 | DONE | 同住人升级不报错 |
| US-102 | AC-102-08 | `Register.vue`/`Me.vue`/小程序提示 + 审计 `origin_label` | DONE | 提示含专有部分标识；审计不含他人姓名/手机号（比脱敏更严格） |
| US-102 | AC-102-09 | 清册写入路径不调用 `AutoBindService` | DONE | 后补手机号不触发绑定 |
| US-102 | AC-102-10 | 非微信用户首次绑定手机号 | DONE | 同 AC-102-06 路径 |
| US-103 | AC-103-01 | `services.options`（label = 户号（类型 面积）） | DONE | 两端末级均用 label |
| US-103 | AC-103-02 | 同上（无类型/面积时 label = 户号） | DONE | 无"未登记/null/空括号" |
| US-103 | AC-103-03 | 同上（不含业主字段） | DONE | 仅类型/面积 |
| US-103 | AC-103-04 | `UnitOptionsView`（`IsMember`） | DONE | 未登录 401 |
| US-104 | AC-104-01 | 既有 `PHONE_NOT_IN_REGISTRY` + 两端提示与申诉入口 | DONE | 提示"手机号与清册不一致，可提交产权申诉" |
| US-104 | AC-104-02 | 既有产权申诉流程（未改动） | DONE | 回归通过 |
| US-104 | AC-104-03 | 既有"请先绑定手机号"（未改动） | DONE | 回归通过 |
| US-104 | AC-104-04 | 补录手机号后手动认证走既有比对 | DONE | 补录不自动触发绑定 |

## 迁移

| 文件 | 内容 | 可逆 |
|---|---|---|
| `0002_owner_type_area.py` | AlterField（unit_no/floor/room/specific_part）、AddField（unit_type/area）、CreateModel（RegistryOwner）、AddField（RegistryPhone.owner, null=True）、AddConstraint（uniq_registry_owner_name） | 是 |
| `0003_backfill_legacy_owners.py` | RunPython：为每个无业主手机号创建无名业主并回填 owner；反向先置空再删除无名业主 | 是 |
| `0004_phone_owner_required.py` | RunPython 校验无孤儿后 AlterField（owner 非空） | 是 |

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| 无 | — | — | — |

## 开放问题

- `[ASSUMPTION]` 既有专有部分在文件中未填类型且原类型为空时不判错（仅新专有部分强制类型）；如需对既有记录也强制，需 GROUP_B 明确。
- `[ASSUMPTION]` `updated` 计数口径为"本次被改动的既有专有部分数（含业主/手机号变化）"（AC-099-01）。
- 环境缺 `openpyxl`（`requirements.txt` 已声明）：xlsx 解析/模板生成返回 503 `IMPORT_UNAVAILABLE`，CSV 全链路可用；xlsx 路径待环境安装后由 GROUP_D 验证。
</file_header>

## 缺陷修复（DEF-007~012）

用户授权交付后回流（REWORK_AUTHORIZED）。均为最小改动，无迁移。

| DEF | 级别 | 根因 | 改动（文件:函数） | 自验证 |
|---|---|---|---|---|
| DEF-007 | MAJOR | `build_xlsx` 所有单元格为 General，Excel 键入 0801 被存成数字 801 | `import_template.py`：`build_xlsx` 对 A/B/C/D/H 列设 `column_dimensions[col].number_format="@"`（整列，新输入行继承）并对示例行单元格设 "@"；`_NOTES`、`import_spec.spec_payload["notes"]` 增补"请勿用 Excel 直接另存 csv 改写编号，推荐使用 xlsx 模板" | 读回模板：第 2 行 A-D、H 列 "@"，E-G 为 General，D 列 column format "@" |
| DEF-008 | MAJOR | `read_rows` 用 `read_only=True`，该模式无 `merged_cells`，合并区域非首行读到空值 | `importing.py`：`read_rows` 改普通模式 `load_workbook(data_only=True)`，新增 `_fill_merged_cells(grid, ranges)`，把左上角值填入区域内其余单元格（范围按实际网格截断，避免超大合并区域越界） | 构造 A2:A4 合并的工作簿：读出 3 行楼栋均为"1栋"，"0801"保持文本；20000 行 + 超大合并区域 J2:J20001 读取 4.78 s（预算 60 s） |
| DEF-009 | MINOR | `auto_bind` 遇非 ALREADY_CERTIFIED 的 ApiError 或其他异常即 `break`，后续专有部分不再绑定 | `auto_bind.py`：`break` 改 `continue`；每个单元的 `certify_owner` 包 `transaction.atomic()` savepoint，单个失败只回滚自身 | 全量后端测试通过；见"开放问题"中测试缺口 |
| DEF-010 | MINOR | `bool(request.data.get("dry_run"))` 把表单 "false"/"0" 当真 | `views.py`：`AdminRegistryImportView.post` 表单值改为 `str(...).lower() in {"1","true"}`，与查询参数一致 | 全量后端测试通过 |
| DEF-011 | MINOR | `_fill_names` 的 `bulk_update` 含 `updated_at` 但 bulk 不触发 `auto_now`，字段未赋值 | `importing.py`：`_fill_names` 赋 `owner.updated_at = timezone.now()` | 全量后端测试通过 |
| DEF-012 | MINOR | `downloadBlob` 在 `click()` 后立即 `revokeObjectURL`，部分浏览器取消下载 | `frontend/src/admin/registryImport.js`：`setTimeout(() => URL.revokeObjectURL(url), 1000)` | 前端构建成功；现有 1 条用例因同步断言失败，见下 |

### 取舍记录（DEF-008）
read_only 模式内存低但不暴露 merged_cells；改普通模式后 5 MB / 20000 行文件实测解析 4.78 s，远低于 60 s 预算，内存为全量单元格对象（20000×8 级别，可接受）。备选"read_only + 手工解析 sheet XML 的 mergeCells"实现更复杂、风险更高，未采用。并发导入加锁、`shared/api.js` 反向依赖、`miniprogram/package-lock.json`、小程序发布均不在范围，未改动。

### 现有测试受影响（须 test-engineer 调整）
`frontend/tests/registry_import.spec.js` 的 `TC-UNIT-114 / AC-100-02`（第 61 行）同步断言 `revokeObjectURL` 被调用，DEF-012 改为延迟释放后该断言失败（前端 vitest 125/126）。按约束不改测试代码；建议用 `vi.useFakeTimers()` 并 `vi.advanceTimersByTime(1000)` 后断言。

### 开放问题（本次新增）
- 缺少针对 DEF-007~011 的专门用例（合并单元格 xlsx、文本格式模板、auto_bind 单元失败后继续、dry_run 表单 "false"、补填姓名 updated_at），建议 test-engineer 补。
- `[ASSUMPTION]` 文本格式列仅覆盖楼栋/单元/楼层/户号/手机号；面积列保持 General。
- `[ASSUMPTION]` revoke 延迟取 1000 ms。

## DEF-013 修复（2.1.0，REWORK_AUTHORIZED：用户 2026-11-11 "3. 一起修"）

| DEF | 级别 | 根因 | 改动（文件:函数） | 自验证 |
|---|---|---|---|---|
| DEF-013 | MAJOR | 提交 6fbd24d 把 `_create_owners` 回查改为按 unit_id 分批，但每批仍带全部业主姓名 `.filter(name__in=names)`（20000 行时每条查询约 20000 个参数 × 40 批），SQLite 解析/匹配开销 O(批数×姓名数)，TC-E2E-302/303 超 60 s 返回 504 IMPORT_TIMEOUT | `backend/apps/registry/importing.py:_create_owners`：每批只 `filter(unit_id__in=batch)`，`(unit_id, name)` 在 Python 端用 `wanted` 集合过滤；单条查询参数数 ≤ 500，保留避免 "too many SQL variables" 的目标 | 见 code_review_report DEF-013 小节 |

其他 6fbd24d 分批点检查（`_load_states`、`_create_units`、`_fill_names`、`_move_phones`、`_delete_owners`、`_create_phones`）：每批只带本批自身的键（specific_part / owner_id / phone_id / unit 的 owner id），不存在"每批带全集"问题，未改动。仅 `_load_states` 的 `prefetch_related("owners__phones")` 会按 ≤500 个 unit 展开 owner id（每户业主数少，当前远低于 SQLite 32766 上限），记为观察项不改。

无迁移、不改测试代码、不改 apps/content。
