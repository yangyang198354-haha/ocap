<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-10T23:07:55.7566991+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/user_stories.md</file><file>requirements/requirements_spec.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>architecture/module_design.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：业主清册导入增强（US-092 ~ US-104）

## 测试策略

**被测改动**：MOD-030~038（清册模型扩展、导入引擎、模板与格式说明、逐级选项、清册自动绑定、管理端与用户端交互）。范围覆盖 `backend/apps/{registry,residency,accounts,identity}`、`frontend/src/{admin,portal,shared}`、`miniprogram/{pages,utils}`。

**In scope**
- 管理端：格式说明、模板下载（csv/xlsx）、批量导入（预检与正式）、单条专有部分增改与筛选、单条业主登记（数量不限）。
- 导入引擎：多业主、分号手机号、类型与面积校验、重复导入合并与冲突、错误行报告与一次性计数。
- 用户端：逐级选项跳级与标签、认证比对与申诉入口、注册/首次绑手机号自动绑定。
- 客户端：前端 `registryImport.js` 的结果摘要/错误 CSV/下载与超时文案；前后端字段契约；小程序 units/phone 页面契约。

**Out of scope**
- 真实微信、阿里云短信、邮件服务（按画像 P11-3 只用 `apps/integrations/fakes.py`）。
- 生产/测试机部署行为（GROUP_E1/E2）；浏览器渲染与视觉回归（项目无浏览器 E2E 框架）。
- 20000 行性能压测与 xlsx 解析/模板生成：见"不可测项"。

**环境**：Python 3.14.6 + Django（本机 6.0.6）；`config.test_settings`（SQLite 内存库、`MIGRATION_MODULES` 置空、短信/邮件内存替身、外部服务 fake）；前端 vitest；小程序 vitest。严禁连接生产库或生产服务。

**判定模式与阈值**：INCREMENTAL，baseline 模式（画像 P5）——各层相对基线零新增失败，且新写用例全部通过才进入下一层。基线：GROUP_C 收尾时全量 `Ran 247 tests / OK`（前端 122 用例中 2 个既有环境失败）。

**基线来源**：画像 P4（greenfield 无既有失败）+ GROUP_C 门控实测（后端 247 OK；前端 120 passed/2 failed；小程序 69 passed）。

**分层机制**：目录分层 `backend/tests/{unit,integration,e2e,smoke}`（Django runner 按模块路径选择性执行）；前端/小程序为 vitest，本变更新增用例集中在 `frontend/tests/registry_import.spec.js`。

**critical path 口径**：替代（项目无浏览器 E2E 框架，采用最高层可执行的完整 API 旅程 `tests/e2e`）。

## AC 映射

> 级别：U=单元（单模块/mock）、I=集成（真实 ORM/HTTP 路由器）、E=E2E（多步 API 旅程）、F=前端单元（vitest）。位置缩写：U-RULES=`tests/unit/test_registry_import_rules.py`、I-ENH=`tests/integration/test_registry_import_enhancement.py`、I-CON=`tests/integration/test_frontend_contract.py::RegistryImportContractTests`、E-JRN=`tests/e2e/test_registry_import_journeys.py`、F-RI=`frontend/tests/registry_import.spec.js`。

| AC | 用例 ID | 级别 | 现有/新写 | 位置（文件::类::方法） | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|
| AC-092-01 | TC-UNIT-107 | U | 新写 | U-RULES::ImportSpecContractTests::test_tc_unit_107_spec_payload_matches_page_copy | 无 | 读取 spec payload | 含 .csv/.xlsx、5 MB、20000 行、首工作表与 8 列规则 | 内置常量 |
| AC-092-01 | TC-INT-101 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_101_spec_payload | 管理员令牌 | GET /admin/registry/import/spec | 200，字段与页面文案一致 | 管理员账号 |
| AC-092-01 | TC-INT-164 | I | 新写 | I-CON::test_tc_int_164_client_calls_resolve | 仓库源码 | 解析前端/小程序 api.js 调用并解析 Django 路由 | 4 条新调用全部可解析 | 源码文本 |
| AC-092-02 | TC-INT-102 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_102_non_admin_denied | 注册用户/游客 | 访问 6 个管理端端点 | 401/403，无清册数据 | 普通用户令牌 |
| AC-092-03 | TC-INT-103 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_103_too_many_rows_rejected | 管理员令牌 | 上传 20001 数据行 | 400，提示"文件行数超过 20000"，清册 0 条 | 20001 行 csv |
| AC-092-04 | TC-INT-104 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_104_bad_extension_and_oversize | 管理员令牌 | 上传 .xls / 6 MB csv | 400"仅支持 xlsx 或 csv" / 413"文件超过 5 MB" | 假扩展名、>5 MB |
| AC-092-05 | TC-INT-104 | I | 新写 | 同上 | 同上 | 上传超 5 MB 文件 | 413 FILE_TOO_LARGE | 6 MB bytes |
| AC-093-01 | TC-UNIT-110、TC-INT-105（csv 部分）；xlsx 分支 [BLOCKED] | U/I | 新写 | U-RULES::CsvTemplateTests::test_tc_unit_110_…；I-ENH::SpecAndTemplateTests::test_tc_int_105_csv_template | 管理员令牌 | 下载 csv 模板 | UTF-8 BOM、8 列表头、多业主/空手机号/车位示例；xlsx 工作簿结构未验证 | 内置示例 |
| AC-093-02 | TC-UNIT-110 | U | 新写 | 同上 | 无 | 读取 csv 模板字节 | 以 BOM 开头，Excel 打开中文不乱码 | 内置示例 |
| AC-093-03 | [NOT_TESTABLE] | — | — | — | — | — | xlsx 解析依赖 openpyxl，本机未安装（画像 P4 不自行安装） | — |
| AC-093-04 | TC-UNIT-105、TC-UNIT-101 | U | 新写 | U-RULES::UnitFieldRuleTests::test_tc_unit_105_cell_text_normalization；ParseAreaTests::test_tc_unit_101_valid_areas | 无 | 传入 int/float/Decimal/date 单元格 | "0801" 与 "13800000000" 保形，无 "3.0"；面积两位小数 | 3.0、Decimal("89.50") |
| AC-093-05 | TC-INT-102 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_102_non_admin_denied | 普通用户 | GET template | 401/403 | 普通用户令牌 |
| AC-093-06 | TC-INT-106 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_106_old_template_rejected | 管理员令牌 | 上传旧 5 列模板 | 400 IMPORT_COLUMNS_MISSING，details.columns 含 3 列，"请使用新模板" | 旧表头 csv |
| AC-094-01 | TC-INT-107 | I | 新写 | I-ENH::MultiOwnerImportTests::test_tc_int_107_six_owners_with_four_phones | 管理员令牌 | 同单元 6 行导入 | 1 单元 6 业主，4 个手机号各可认证 | 6 行/4 手机号 |
| AC-094-02 | TC-INT-108 | I | 新写 | I-ENH::MultiOwnerImportTests::test_tc_int_108_two_hundred_owners | 管理员令牌 | 同单元 200 行 | 200 业主，无"超过 10 个" | 200 行 |
| AC-094-03 | TC-INT-109 | I | 新写 | I-ENH::MultiOwnerImportTests::test_tc_int_109_semicolon_phones | 管理员令牌 | 手机号 "138…;139…" | 1 业主 2 手机号 | 分号写法 |
| AC-094-04 | TC-INT-102 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_102_non_admin_denied | 普通用户 | POST import | 401/403，清册 0 条 | 普通用户令牌 |
| AC-094-05 | TC-INT-110 | I | 新写 | I-ENH::MultiOwnerImportTests::test_tc_int_110_duplicate_rows_merge | 管理员令牌 | 两行同姓名同手机号 | 1 业主 1 手机号，无重复 | 同姓名两行 |
| AC-094-06 | TC-INT-112 | I | 新写 | I-ENH::MultiOwnerImportTests::test_tc_int_112_import_audit_has_no_pii | 管理员令牌 | 导入后查审计 | REGISTRY_IMPORTED 含计数，无姓名/手机号明文 | 1 单元 1 业主 |
| AC-094-07 | [NOT_TESTABLE] | — | — | — | — | — | 缺 20000 行合法样本与 60 秒计量口径（见不可测项 P-01） | — |
| AC-094-08 | TC-INT-111 | I | 新写 | I-ENH::MultiOwnerImportTests::test_tc_int_111_empty_phone_ok_and_empty_name_failed | 管理员令牌 | 王芳手机号为空 | 导入成功，手机号为空，不报错 | 空手机号行 |
| AC-094-09 | TC-INT-111 | I | 新写 | 同上 | 管理员令牌 | 姓名为空 + 合法手机号 | 该行失败"业主姓名不能为空"，其他行成功 | 空姓名行 |
| AC-095-01 | TC-INT-113 | I | 新写 | I-ENH::SingleEntryTests::test_tc_int_113_put_twelve_owners | 管理员+单元 | PUT 12 位业主 | 200，12 位业主，无 10 个上限提示 | 12 人名单 |
| AC-095-02 | TC-INT-113 | I | 新写 | 同上 | 同上 | 重新 GET | 姓名与完整手机号回显 | 12 人名单 |
| AC-095-03 | TC-INT-114 | I | 新写 | I-ENH::SingleEntryTests::test_tc_int_114_invalid_phone_rejected | 已有业主 | PUT 非法手机号 | 400"手机号格式不正确"，原业主不变 | "12345" |
| AC-095-04 | TC-INT-102 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_102_non_admin_denied | 普通用户 | PUT owners | 401/403 | 普通用户令牌 |
| AC-095-05 | TC-INT-117 | I | 新写 | I-ENH::SingleEntryTests::test_tc_int_117_delete_owner_keeps_certification | 业主已认证 | 删除该业主后再认证 | 既有 membership 保留；清册中该手机号不再比对通过 | 已认证账号 |
| AC-095-06 | TC-INT-118 | I | 新写 | I-ENH::SingleEntryTests::test_tc_int_118_me_masks_phone_and_hides_name | 已认证用户 | GET /me | 手机号 "138****0000" 形式，无业主姓名 | 已认证账号 |
| AC-095-07 | TC-INT-115 | I | 新写 | I-ENH::SingleEntryTests::test_tc_int_115_empty_name_rejected | 已有业主 | PUT 姓名为空 | 400"业主姓名不能为空"，原业主不变 | 空姓名 |
| AC-095-08 | TC-INT-116 | I | 新写 | I-ENH::SingleEntryTests::test_tc_int_116_owner_without_phone | 管理员+单元 | PUT 王芳无手机号 | 200，回显王芳且手机号为空 | 空手机号 |
| AC-096-01 | TC-INT-119 | I | 新写 | I-ENH::TypeAndAreaImportTests::test_tc_int_119_import_four_types | 管理员令牌 | 4 单元 4 类型导入 | 类型正确，面积 89.50/60.00/未登记/12.50 | 4 行 |
| AC-096-02 | TC-INT-120 | I | 新写 | I-ENH::TypeAndAreaImportTests::test_tc_int_120_type_validation | 管理员令牌 | 新单元类型为空 | 该行失败"专有部分类型为空" | 空类型行 |
| AC-096-03 | TC-INT-120、TC-UNIT-103 | I/U | 新写 | 同上；U-RULES::ParseAreaTests::test_tc_unit_103_unit_type_labels | 管理员令牌 | 类型"别墅" | 失败并列出允许范围 5 个值 | "别墅" |
| AC-096-04 | TC-INT-121、TC-UNIT-102 | I/U | 新写 | I-ENH::TypeAndAreaImportTests::test_tc_int_121_area_validation；U-RULES::ParseAreaTests::test_tc_unit_102_… | 管理员令牌 | 面积 abc/-5/0/12.345 | 各行失败并给出"大于 0""最多 2 位小数"原因 | 4 个非法值 |
| AC-096-05 | TC-INT-122 | I | 新写 | I-ENH::TypeAndAreaImportTests::test_tc_int_122_type_conflict_in_group | 管理员令牌 | 同单元两行类型不同 | 两行均失败"同一专有部分的类型不一致"，不写入 | 住宅+商铺 |
| AC-096-06 | TC-INT-123 | I | 新写 | I-ENH::TypeAndAreaImportTests::test_tc_int_123_missing_type_column | 管理员令牌 | 缺"专有部分类型"列 | 400 IMPORT_COLUMNS_MISSING 含该列，清册 0 条 | 7 列 csv |
| AC-096-07 | TC-INT-124 | I | 新写 | I-ENH::TypeAndAreaImportTests::test_tc_int_124_parking_requires_area | 管理员令牌 | 车位空面积 / 住宅空面积 | 前者失败"车位的专有部分面积不能为空"，后者成功 | 2 行 |
| AC-097-01 | TC-INT-125、TC-E2E-104 | I/E | 新写 | I-ENH::SingleUnitAdminTests::test_tc_int_125_create_and_update_unit；E-JRN::test_tc_e2e_104_single_unit_lifecycle | 管理员令牌 | POST 商铺 120.25 | 201，label"商铺"，area"120.25" | 商铺行 |
| AC-097-02 | TC-INT-126 | I | 新写 | I-ENH::SingleUnitAdminTests::test_tc_int_126_create_requires_type | 管理员令牌 | POST 不带类型 | 400"请选择专有部分类型" | 无类型 |
| AC-097-03 | TC-INT-127 | I | 新写 | I-ENH::SingleUnitAdminTests::test_tc_int_127_invalid_area_rejected | 已有单元 | PATCH 面积 abc/1.234 | 400"专有部分面积格式不正确"，原值不变 | 2 个非法值 |
| AC-097-04 | TC-INT-128、TC-E2E-104 | I/E | 新写 | I-ENH::SingleUnitAdminTests::test_tc_int_128_filter_by_type；E-JRN::test_tc_e2e_104 | 混合数据 | GET units?unit_type=PARKING/SHOP | 仅返回对应类型 | 住宅+车位+商铺 |
| AC-097-05 | TC-INT-102 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_102_non_admin_denied | 普通用户 | POST/PATCH units | 401/403 | 普通用户令牌 |
| AC-097-06 | TC-INT-129、TC-E2E-104 | I/E | 新写 | I-ENH::SingleUnitAdminTests::test_tc_int_129_change_is_audited | 已认证单元 | 改类型/面积 | REGISTRY_UNIT_CHANGED 审计写入，认证不受影响 | 已认证账号 |
| AC-097-07 | TC-INT-130、TC-E2E-104 | I/E | 新写 | I-ENH::SingleUnitAdminTests::test_tc_int_130_parking_area_required_and_residence_optional | 管理员令牌 | POST 车位空面积 | 400"车位须填写专有部分面积"，清册 0 条 | 车位无面积 |
| AC-097-08 | TC-INT-130 | I | 新写 | 同上 | 管理员令牌 | POST 住宅空面积不登记业主 | 201，面积为 null（前端显示"未登记"） | 住宅无面积 |
| AC-098-01 | TC-INT-131、TC-UNIT-106 | I/U | 新写 | I-ENH::OptionTests::test_tc_int_131_parking_specific_part；U-RULES::UnitFieldRuleTests::test_tc_unit_106_… | 管理员令牌 | 新增 车库/A-088 | specific_part="车库-A-088"，无多余分隔符 | 车库行 |
| AC-098-02 | TC-INT-132、TC-INT-165 | I | 新写 | I-ENH::OptionTests::test_tc_int_132_options_skip_empty_levels；I-CON::test_tc_int_165_response_fields | 已登录用户 | GET options?building=车库 | level=room，skipped=["unit_no","floor"]，直接列户号 | 车库数据 |
| AC-098-03 | TC-INT-133 | I | 新写 | I-ENH::OptionTests::test_tc_int_133_options_has_empty_and_reachable_shop | 混合楼栋 | GET options?building=1 | 单元选项无空值，has_empty 标记，商铺可达 | 住宅+空单元商铺 |
| AC-098-04 | TC-INT-134、TC-UNIT-104 | I/U | 新写 | I-ENH::OptionTests::test_tc_int_134_import_missing_levels；U-RULES::test_tc_unit_104_… | 管理员令牌 | 缺楼栋/缺户号行；单元楼层为空行 | 缺必填失败并指明字段；单元/楼层为空不报错 | 3 行 |
| AC-098-05 | TC-INT-135、TC-UNIT-106 | I/U | 新写 | I-ENH::OptionTests::test_tc_int_135_legacy_four_levels | 既有四级单元 | 查看标识与逐级选择 | 与旧规则一致（1-2-3-301） | 四级单元 |
| AC-098-06 | TC-INT-136 | I | 新写 | I-ENH::OptionTests::test_tc_int_136_import_parking_row | 管理员令牌 | 车位 1 行（赵云空手机号） | imported=1，failed=0，业主登记 | 车位行 |
| AC-099-01 | TC-INT-137、TC-E2E-102 | I/E | 新写 | I-ENH::ReimportTests::test_tc_int_137_reimport_adds_owner；E-JRN::test_tc_e2e_102 | 已有张伟/李娜 | 再导入王强 | 3 位业主，updated=1 | 3 业主 |
| AC-099-02 | TC-INT-138 | I | 新写 | I-ENH::ReimportTests::test_tc_int_138_same_name_appends_phone | 张伟手机号 A | 再导入张伟手机号 B | 仍 1 位业主，手机号 A+B | 同名不同号 |
| AC-099-03 | TC-INT-139、TC-E2E-102 | I/E | 新写 | I-ENH::ReimportTests::test_tc_int_139_type_area_update_listed | 住宅 89.50 | 再导入公寓 90.00 | 类型面积更新，changes 列出两字段 | 类型冲突值 |
| AC-099-04 | TC-INT-140 | I | 新写 | I-ENH::ReimportTests::test_tc_int_140_empty_type_area_keeps_existing | 已有类型面积 | 再导入空类型面积 | 原值不变 | 空值行 |
| AC-099-05 | TC-INT-141、TC-E2E-102 | I/E | 新写 | I-ENH::ReimportTests::test_tc_int_141_import_never_deletes_owners | 李娜已认证 | 文件中不含李娜 | 业主与认证保留 | 已认证账号 |
| AC-099-06 | TC-INT-122 | I | 新写 | I-ENH::TypeAndAreaImportTests::test_tc_int_122_type_conflict_in_group | 同文件类型冲突 | 导入 | 按 AC-096-05 拒绝该单元 | 住宅+商铺 |
| AC-099-07 | TC-INT-142 | I | 新写 | I-ENH::ReimportTests::test_tc_int_142_phone_conflict_other_owner | 张伟持手机号 A | 李娜使用手机号 A | 该行失败"手机号已登记给同一专有部分的另一位业主" | 冲突手机号 |
| AC-099-08 | TC-INT-143 | I | 新写 | I-ENH::ReimportTests::test_tc_int_143_trailing_space_same_name | 已有张伟 | 导入"张伟 "与"张伟（二）" | 前者合并，后者新增，共 2 位 | 带空格/带标记 |
| AC-100-01 | TC-INT-144 | I | 新写 | I-ENH::DryRunTests::test_tc_int_144_dry_run_no_write_and_same_numbers | 管理员令牌 | 预检后正式导入 | 预检不写库；两者 imported/updated/owners/failed 一致 | 14 行混合 |
| AC-100-02 | TC-INT-145、TC-UNIT-113 | I/F | 新写 | I-ENH::DryRunTests::test_tc_int_145_error_rows_reported；F-RI::registryImport helpers::TC-UNIT-113 | 含错文件 | 预检 + 导出错误 CSV | 第 7/12/15 行原因正确；CSV 表头"行号,字段,原因"并转义引号 | 3 类错误 |
| AC-100-03 | TC-INT-144 | I | 新写 | 同上 | 含错文件 | 先预检再正式 | 失败行数与原因完全一致，合法行写入 | 14 行混合 |
| AC-100-04 | TC-INT-146 | I | 新写 | I-ENH::DryRunTests::test_tc_int_146_bad_phone_row_counted_once | 一行 3 个手机号其中 1 个非法 | 预检 | failed=1，该行不计 imported/updated | 3 手机号 |
| AC-100-05 | TC-UNIT-111、TC-INT-165 | F/I | 新写 | F-RI::registryImport helpers::TC-UNIT-111；I-CON::test_tc_int_165 | 导入结果对象 | 生成摘要文案 | 纯文字"共 100 行：新增 98 个…失败 0 行"，无 JSON 原文 | 结果对象 |
| AC-100-06 | TC-INT-102 | I | 新写 | I-ENH::SpecAndTemplateTests::test_tc_int_102_non_admin_denied | 普通用户 | POST import?dry_run | 401/403 | 普通用户令牌 |
| AC-100-07 | TC-UNIT-112、[NOT_TESTABLE 性能] | F | 新写 | F-RI::TC-UNIT-112 | 超时错误 | 生成提示 | "导入超时，请缩小文件后重试"；20000 行 60 秒未测 | ECONNABORTED |
| AC-100-08 | [NOT_TESTABLE] | — | — | — | — | — | 缺 20000 行含 10% 错误样本与 60 秒计量口径（P-02） | — |
| AC-101-01 | TC-INT-147 | I | 新写 | I-ENH::LegacyCompatibilityTests::test_tc_int_147_legacy_unit_listed_unset | 既有空类型单元 | GET units?unit_type=UNSET | 返回该单元，类型/面积为 null | 旧单元 |
| AC-101-02 | TC-INT-148 | I | 新写 | I-ENH::LegacyCompatibilityTests::test_tc_int_148_legacy_certification_unchanged | 既有单元+手机号 | 手机号认证 | 行为与上线前一致，201 | 旧单元 |
| AC-101-03 | TC-INT-149、TC-E2E-102 | I/E | 新写 | I-ENH::LegacyCompatibilityTests::test_tc_int_149_backfill_keeps_membership | 已认证旧单元 | 补录类型面积 | 更新成功，业主与认证保留 | 已认证账号 |
| AC-101-04 | TC-INT-150 | I | 新写 | I-ENH::LegacyCompatibilityTests::test_tc_int_150_edit_owners_without_type | 未登记类型单元 | 仅改业主保存 | 200，不强制补类型面积 | 旧单元 |
| AC-102-01 | TC-INT-151、TC-E2E-101 | I/E | 新写 | I-ENH::AutoBindTests::test_tc_int_151_register_auto_binds_head | 清册手机号 | 注册并验证 | membership HEAD/REGISTRY，/me label"户主" | 张伟手机号 |
| AC-102-02 | TC-INT-152 | I | 新写 | I-ENH::AutoBindTests::test_tc_int_152_register_binds_all_units | 同号登记 3 单元 | 注册 | 3 条 membership，各为 HEAD，相互独立 | 3 单元同号 |
| AC-102-03 | TC-INT-153、TC-E2E-101 | I/E | 新写 | I-ENH::AutoBindTests::test_tc_int_153_second_owner_keeps_single_head | 已有户主 | 第二位业主注册 | 角色 OWNER，"产权业主"；head_slot 唯一 | 2 位业主 |
| AC-102-04 | TC-INT-154 | I | 新写 | I-ENH::AutoBindTests::test_tc_int_154_register_without_registry_phone | 清册无此号 | 注册 | 201，membership 0，不报错 | 随机手机号 |
| AC-102-05 | 现有 test_auth_api.py::test_wrong_code_then_locked | I | 现有 | backend/tests/integration/test_auth_api.py | 验证码错误 | 提交注册 | 注册失败，无账号与身份 | 错误验证码 |
| AC-102-06 | TC-INT-155 | I | 新写 | I-ENH::AutoBindTests::test_tc_int_155_wechat_bind_phone_auto_binds | 微信新用户 | 首次绑定清册手机号 | auto_bound 含该单元，HEAD | FakeWeChatClient |
| AC-102-07 | TC-INT-156 | I | 新写 | I-ENH::AutoBindTests::test_tc_int_156_resident_upgraded | 已是同住人 | 自动绑定 | 升级为产权业主，不报错 | 同住人账号 |
| AC-102-08 | TC-INT-157 | I | 新写 | I-ENH::AutoBindTests::test_tc_int_157_auto_bind_audit_and_no_pii | 自动绑定成功 | 查审计与 /me | CERTIFY_BY_REGISTRY + origin_label"清册自动绑定"，无姓名/手机号明文 | 张伟手机号 |
| AC-102-09 | TC-INT-158 | I | 新写 | I-ENH::AutoBindTests::test_tc_int_158_later_registry_add_does_not_bind | 已注册无清册号 | 管理员补手机号 | membership 0；手动认证可 201 | 已注册账号 |
| AC-102-10 | TC-INT-166 | I | 新写 | I-ENH::AutoBindTests::test_tc_int_166_phone_bind_without_wechat_auto_binds | 已注册未绑手机号 | 首次绑定清册号 | auto_bound 含该单元，HEAD，写审计 | 非微信账号 |
| AC-103-01 | TC-INT-159、TC-E2E-101 | I/E | 新写 | I-ENH::OptionLabelAndAppealTests::test_tc_int_159_room_labels | 301 住宅 89.50 | GET options 末级 | label 含"301""住宅""89.50 ㎡" | 301 单元 |
| AC-103-02 | TC-INT-159 | I | 新写 | 同上 | 302 类型面积为空 | GET options | label 仅"302"，无"未登记"/"null"/空括号 | 302 单元 |
| AC-103-03 | TC-INT-159 | I | 新写 | 同上 | 车位 12.50 | GET options | label 含"车位""12.50 ㎡"，不含姓名/手机号 | 车位单元 |
| AC-103-04 | TC-INT-160 | I | 新写 | I-ENH::OptionLabelAndAppealTests::test_tc_int_160_options_require_login | 游客 | GET options | 401，无类型面积 | 无令牌 |
| AC-104-01 | TC-INT-161、TC-E2E-103 | I/E | 新写 | I-ENH::OptionLabelAndAppealTests::test_tc_int_161_phone_mismatch_points_to_appeal | 业主无手机号，用户手机号不在清册 | POST /certifications | 422 PHONE_NOT_IN_REGISTRY，details.appeal_available | 王芳空手机号 |
| AC-104-02 | 现有 test_residency_api.py::test_appeal_requires_proof_and_admin_approve_makes_owner | I | 现有 | backend/tests/integration/test_residency_api.py | 已提交申诉 | 管理员审核通过 | 认证为产权业主，无户主时成为 HEAD | 申诉数据 |
| AC-104-03 | TC-INT-162 | I | 新写 | I-ENH::OptionLabelAndAppealTests::test_tc_int_162_certify_requires_phone | 账号未绑手机号 | POST /certifications | 400/409"请先绑定手机号" | 无手机号账号 |
| AC-104-04 | TC-INT-163、TC-INT-158 | I | 新写 | I-ENH::OptionLabelAndAppealTests::test_tc_int_163_admin_adds_phone_then_certify | 管理员补录手机号 | 同一用户再认证 | 201 HEAD，无需申诉；不自动绑定 | 补录手机号 |

## 测试数据需求

- 全部测试数据在用例内构造，使用 `next_phone()` / `next_account_no()` 或固定测试号段（137/138/139 前缀），不写持久存储；每次运行由 SQLite 内存库重建，无重复运行冲突。
- 导入文件由 `csv_bytes()` 现生成，不落地。
- 微信登录使用 `apps.integrations.fakes.FakeWeChatClient`；短信使用 `FakeSmsGateway`（`config.test_settings` 的 `SMS_GATEWAY_BACKEND=memory`）。
- 管理员：`make_admin()`；注册用户：`register()`（验证码从 FakeSmsGateway 读取）。
- [DATA_REQUIRED: 20000 行合法样本 / 20000 行含 10% 错误样本（AC-094-07、AC-100-07、AC-100-08）] —— 当前未提供，见不可测项。
- [DATA_REQUIRED: 可复现的 xlsx 模板/数据文件（AC-093-01/03/04 的 xlsx 分支）] —— 依赖 `openpyxl`，本机未安装且画像 P4 禁止自行安装。

## 不可测项

| AC | 原因 |
|---|---|
| AC-093-01（xlsx 模板结构部分） | BLOCKED：`openpyxl` 未安装（`ModuleNotFoundError`），画像 P4 明确"缺依赖不自行安装"。csv 模板分支已实测。 |
| AC-093-03 | BLOCKED：xlsx 解析路径依赖 `openpyxl`，同上。 |
| AC-093-04（xlsx 单元格部分） | BLOCKED：xlsx 读取路径未执行；单元格归一化规则已由 TC-UNIT-105 在 `cell_text` 层验证。 |
| AC-094-07 | NOT_TESTABLE：无 20000 行合法样本，且 60 秒计量口径依赖测试机硬件（Q-RI-23 默认口径）；未做压测。 |
| AC-100-07 | NOT_TESTABLE：同上（预检 20000 行计时）；超时提示文案由 TC-UNIT-112 覆盖。 |
| AC-100-08 | NOT_TESTABLE：需 20000 行含约 10% 错误样本与 60 秒计量口径，样本未提供。 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-092 | TC-UNIT-107、TC-INT-101、TC-INT-102、TC-INT-103、TC-INT-104、TC-INT-164、TC-E2E-101 | U/I/E |
| US-093 | TC-UNIT-110、TC-INT-105、TC-INT-106、TC-INT-102、TC-E2E-101（xlsx 分支见不可测项） | U/I/E |
| US-094 | TC-INT-107、TC-INT-108、TC-INT-109、TC-INT-110、TC-INT-111、TC-INT-112、TC-E2E-101 | I/E |
| US-095 | TC-INT-113 ~ TC-INT-118、TC-E2E-102 | I/E |
| US-096 | TC-INT-119 ~ TC-INT-124、TC-UNIT-102、TC-UNIT-103、TC-E2E-101、TC-E2E-102 | U/I/E |
| US-097 | TC-INT-125 ~ TC-INT-130、TC-E2E-104 | I/E |
| US-098 | TC-INT-131 ~ TC-INT-136、TC-UNIT-104、TC-UNIT-106、TC-E2E-101 | U/I/E |
| US-099 | TC-INT-137 ~ TC-INT-143、TC-E2E-102 | I/E |
| US-102 | TC-INT-151 ~ TC-INT-158、TC-INT-166、TC-E2E-101、TC-E2E-103 | I/E |
| US-103 | TC-INT-159、TC-INT-160、TC-E2E-101 | I/E |
| US-104 | TC-INT-161 ~ TC-INT-163、TC-E2E-103 | I/E |

Should Have（不参与 critical path 统计）：US-100 → TC-INT-144~146、TC-UNIT-111~113、TC-INT-165；US-101 → TC-INT-147~150、TC-E2E-102。
