<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-16T18:27:05+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0)</file>
    <file>requirements/user_stories.md (1.0.0)</file>
    <file>architecture/architecture_design.md (1.0.0)</file>
    <file>architecture/module_design.md (1.0.0)</file>
    <file>architecture/tech_stack.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：房屋选择结构整理、申诉审核增强、认证姓名核对与席位授予放宽（INCREMENTAL）

## 实现概览

- 模块 8 个（MOD-111~118），全部 DONE。新建产品文件 6 个（后端 5：`registry/shops.py`、`registry/ownership.py`、`registry/management/commands/relocate_shops.py`、`committee/effective.py`、`residency/migrations/0003_appeal_owner_name.py`；前端 1：`admin/parts/ProofThumbs.vue`），修改既有产品文件 20 个（后端 12、Web 前端 5、小程序 3），另有既有测试最小同步 21 个文件（见下表）；未新建测试文件（新功能测试由 test-engineer 写，本批无 smoke 例外）。
- 实现顺序（模块依赖拓扑）：MOD-112（无依赖，`SHOP_BUILDING`）→ MOD-111（依赖 MOD-112、`registry.underground`）→ MOD-113（依赖 MOD-112）→ MOD-114（仅依赖 `registry.models`）→ MOD-115（依赖 MOD-114）→ MOD-116（无项目内新依赖）→ MOD-117/118（依赖 HTTP 契约 IFC-300/306~312）。
- 未新增依赖；未改 `.trae/**`；未连接测试机；未 commit/push。`relocate_shops` 与导出命令只在本地 SQLite 合成数据上自验证（scratch 副本，不入库）。
- `[DEVIATION]`：无。设计未写明、由开发自行决定的取值见"开放问题"中的 `[ASSUMPTION]`。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-112 | `backend/apps/registry/ordering.py` | 修改 | 无 | L | 新增 `SHOP_BUILDING`、`RESERVED_BUILDINGS`；楼栋级层级 0 整数/1 地下车位/2 商铺/3 其他文字，其余层级不变 | DONE |
| 2 | MOD-112 | `backend/apps/registry/services.py` | 修改 | 1 | L | `options()` 仅在 `level==unit_no` 且 `building==商铺` 时返回可选键 `level_label="楼栋/门牌"` | DONE |
| 3 | MOD-111 | `backend/apps/registry/underground.py` | 修改 | 无 | L | `write_backup/verify_backup/_read_backup` 增加带缺省值的关键字参数 `format_name`（旧调用不变）；`write_backup` 的 `plan` 形参改为鸭子类型（只用 `.moves[*].unit_id`） | DONE |
| 4 | MOD-111 | `backend/apps/registry/shops.py` | 新建 | 1、3 | H | `shop_unit_no`、`plan_shop_relocation`（纯函数；最终状态冲突预演；五类冲突）、`apply_shop_relocation`（事务、`select_for_update`、带旧值逐行 update、审计、计数/原信息/指纹核对）、`restore_shop_backup` | DONE |
| 5 | MOD-111 | `backend/apps/registry/management/commands/relocate_shops.py` | 新建 | 4 | M | dry-run 默认；`--apply --backup --expect-changes`；`--restore [--apply]`；退出码 0/1/2/3；输出不含姓名手机号 | DONE |
| 6 | MOD-113 | `backend/apps/registry/exporting.py` | 修改 | 1 | M | 新增 `OutputLocationError`、`pending_shop_units`、`default_output_name`、`check_output_location`（部署根/MEDIA_ROOT/STATIC_ROOT 外；父目录属当前用户且 `mode&0o077==0`；非 POSIX 开发机跳过属主/权限检查） | DONE |
| 7 | MOD-113 | `backend/apps/registry/management/commands/export_registry_import_file.py` | 修改 | 6 | M | `--output` 与 `--output-dir` 二选一；日期命名不覆盖；位置守卫（退出码 3）；商铺未归类守卫（退出码 2，`--allow-unrelocated` 放行并输出 `structure=legacy`） | DONE |
| 8 | MOD-114 | `backend/apps/registry/ownership.py` | 新建 | 无 | M | `normalize_owner_name`、`owner_matches`（Python 内比较）、`append_owner_from_appeal`（锁专有部分行、同名复用、同号属他人抛 `PhoneOwnedByOtherOwner`）、`AppendResult` | DONE |
| 9 | MOD-115 | `backend/apps/residency/models.py` + `migrations/0003_appeal_owner_name.py` | 修改/新建 | 无 | L | `Appeal.owner_name`（手写迁移，`AddField`，可逆） | DONE |
| 10 | MOD-115 | `backend/apps/residency/views.py` | 修改 | 8、9 | H | `CertificationView`（`NAME_REQUIRED`、64 字、统一 `OWNER_NOT_MATCHED`）；`AppealListCreateView`（`owner_name` 必填）；`AppealAdminSerializer`（批量附件、`owner_name`、`nickname`、`has_phone`）；`AdminAppealDecisionView`（同事务追加清册、审计、`registry_update`、`PHONE_OWNED_BY_OTHER`/`REGISTRY_UPDATE_FAILED`） | DONE |
| 11 | MOD-115 | `backend/apps/residency/apps.py` | 修改 | 无 | L | `AppealAttachmentPolicy.can_open`：无关登录用户抛 `ApiError("FORBIDDEN", …, 403)` | DONE |
| 12 | MOD-116 | `backend/apps/committee/effective.py` | 新建 | 无 | L | `effective_q(today)`、`is_effective(seat, today)` | DONE |
| 13 | MOD-116 | `backend/apps/committee/services.py` | 修改 | 12 | M | 4 个"在任"调用点改用谓词；`grant` 结束日 ≤ 今天 → 400；`change` 对未生效席位沿用旧开始日；`ALREADY_SEATED`/`CAP_REACHED` 计数口径不变（含未生效） | DONE |
| 14 | MOD-116 | `backend/apps/committee/views.py` | 修改 | 12 | L | 删除"开始日 < 今天"分支；开始日上界约 5 年；`seat_view` 增 `effective` | DONE |
| 15 | MOD-116 | `backend/apps/accounts/directory.py`、`backend/apps/accounts/views.py` | 修改 | 12 | L | `identity_view` 用 `is_effective`；用户列表席位预取用 `effective_q` | DONE |
| 16 | MOD-117 | `frontend/src/shared/api.js` | 修改 | 10 | L | `certify(unitId, name)`；`createAppeal` 注释新契约 | DONE |
| 17 | MOD-117 | `frontend/src/portal/parts/UnitCascader.vue` | 修改 | 2 | L | 第二级占位取 `level_label`，选楼栋时复位 | DONE |
| 18 | MOD-117 | `frontend/src/portal/Units.vue` | 修改 | 16 | M | 姓名输入与前置校验；`OWNER_NOT_MATCHED` 转申诉（保留已选房屋、带入姓名、不显示清册信息）；申诉：产权人名字、多附件（≤5，jpg/jpeg/png/pdf） | DONE |
| 19 | MOD-117 | `frontend/src/admin/parts/ProofThumbs.vue` | 新建 | 无 | H | 可视区懒加载、并发 ≤3、`createImageBitmap` 降采样、按 id 缓存；点击弹层（大图/上一份/下一份）；pdf 用 iframe 并提供下载入口；Blob URL 释放 | DONE |
| 20 | MOD-117 | `frontend/src/admin/AdminAppeals.vue` | 修改 | 10、19 | M | 申诉编码、账号、昵称（未设置）、产权人名字（未提供）、申诉时间、无手机号提示、缩略图、通过后 `notice` 提示 | DONE |
| 21 | MOD-117 | `frontend/src/admin/AdminSeats.vue` | 修改 | 14 | L | "待生效"标签；提示文案 | DONE |
| 22 | MOD-118 | `miniprogram/utils/api.js`、`components/UnitPicker.vue`、`pages/units/index.vue` | 修改 | 10 | M | `certify(unitId, name)`；第二级文案 `level_label`；姓名输入、转申诉、产权人名字、图片多选（≤5，OQ-06 仅图片） | DONE |
| 23 | — | 既有测试最小同步（见下表） | 修改 | 10~15 | M | 仅因口径变更失效的断言/调用参数 | DONE |

## 需求追溯

覆盖本次范围 US-193~206（均 Must Have）的全部 79 条 AC。"实现位置"路径前缀：后端 `backend/apps/`，前端 `frontend/src/`，小程序 `miniprogram/`。"DONE"= 代码已实现并经本地自验证（全量后端 822 用例中除一条环境产物失败外全通过 + scratch 冒烟）；客户端交互类 AC 为静态/组件测试级验证，真实浏览器/真机行为未实测（见 code_review_report"自验证结果"）。

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-193 | AC-193-01 | `registry/ordering.py:natural_key`（楼栋级层级）；`registry/services.py:RegistryService.options`（第一级）；`frontend/src/portal/parts/UnitCascader.vue`、`miniprogram/components/UnitPicker.vue`（两端同一接口） | DONE | 数据层顺序由 `relocate_shops` 授权后归类；顺序为数据驱动 |
| US-193 | AC-193-02 | `registry/shops.py:plan_shop_relocation`（类型为商铺的 1 栋记录含 4347 改归"商铺"）；`registry/services.py:options` | DONE | 改库须授权，未对任何环境执行 |
| US-193 | AC-193-03 | `registry/shops.py`（仅 `unit_type == "SHOP"`，C-60） | DONE | scratch 冒烟：类型空/其他/车位/住宅不动 |
| US-193 | AC-193-04 | `registry/ordering.py`（保留名之外的文字楼栋为层级 3） | DONE | scratch：`["1","地下车位","商铺","配套用房"]` |
| US-193 | AC-193-05 | 数据驱动，`options()` 无商铺记录则无该项 | DONE | |
| US-194 | AC-194-01 | `registry/services.py:options`（商铺第二级=`unit_no` 值，自然序）；`registry/shops.py:shop_unit_no`（纯数字补"栋"，OQ-01） | DONE | scratch：`1栋<2栋<10栋<建设南路142号` |
| US-194 | AC-194-02 | `registry/services.py:options`（空层级跳过，既有机制）；`UnitCascader.vue`/`UnitPicker.vue` 既有跳级 | DONE | |
| US-194 | AC-194-03 | `registry/services.py:options`（`unit_id` 逐行输出） | DONE | 选项总数=记录数由数据结构保证；逐条用例由 test-engineer 写 |
| US-194 | AC-194-04 | `UnitCascader.vue:resetBelow('building')`、`UnitPicker.vue:resetBelow('building')`（复位 `level_label`、下级） | DONE | |
| US-195 | AC-195-01 | `registry/shops.py:apply_shop_relocation`（计数核对）；`relocate_shops.py` | DONE | 仅合成数据自验证；授权前不触测试机 |
| US-195 | AC-195-02 | `shops.py`（`lost_origin` 逐条核对 `unit_no == shop_unit_no(备份旧楼栋)`）；备份保留原值 | DONE | |
| US-195 | AC-195-03 | `shops.py:plan_shop_relocation` 冲突预演；`apply_shop_relocation` 抛 `ShopRelocationConflict`；命令退出码 2 | DONE | |
| US-195 | AC-195-04 | `shops.py`（`already_target` 不进 moves） | DONE | scratch：二次 `would_change=0` |
| US-195 | AC-195-05 | `shops.py:restore_shop_backup`；命令 `--restore [--apply]` | DONE | scratch：还原后逐记录相等 |
| US-195 | AC-195-06 | `shops.py`（`update()` 不动 Membership/Appeal；指纹核对） | DONE | 逐场景用例由 test-engineer 写 |
| US-195 | AC-195-07 | 交付说明：数据修正未执行，等待授权；开发期零环境写入 | DONE | 本批未连接测试机、未 ssh |
| US-196 | AC-196-01 | `registry/exporting.py` 既有 `build_export_bundle/verify_export` + `export_registry_import_file.py`（改库后 `precheck_would_create_*`=0） | DONE | scratch 验证 `precheck_would_create_units=0` |
| US-196 | AC-196-02 | 同上（导出自检 `read_rows+plan_import`；原楼栋/门牌在"单元"列，Q-OA-27=A） | DONE | |
| US-196 | AC-196-03 | `exporting.py:check_output_location`（部署根/MEDIA_ROOT/STATIC_ROOT 外、目录 700、文件 0600 沿用 `write_export_file`）；`--output-dir` 日期命名 | DONE | 专用目录由主会话授权时创建（700，`/home/yangyang/ocap_exports/`）；不属代码 |
| US-196 | AC-196-04 | `export_registry_import_file.py`（`--output-dir` 不覆盖已有文件；同秒重复导出退出码 3） | DONE | |
| US-196 | AC-196-05 | 输出只含计数与 id；仓库内无导出文件；测试只用合成数据 | DONE | 发现本机仓库根存在被 gitignore 的历史导出文件，见开放问题 |
| US-196 | AC-196-06 | 既有 `write_export_file`/`import_template` 文本列处理（未改） | DONE | 既有 `test_registry_export_cmd` 覆盖 |
| US-196 | AC-196-07 | 命令位置守卫/未归类守卫在触库前退出；失败不落盘（既有 `.part` 清理） | DONE | |
| US-197 | AC-197-01 | `residency/views.py:AppealAdminSerializer`（`id/owner_name/applicant.account_no/nickname/submitted_at/unit/proof`）；`AdminAppeals.vue` | DONE | |
| US-197 | AC-197-02 | `AdminAppeals.vue`（昵称无则"未设置"） | DONE | |
| US-197 | AC-197-03 | `AppealAdminSerializer`（`owner_name or None`）；`AdminAppeals.vue`（"未提供"） | DONE | |
| US-197 | AC-197-04 | `AppealAdminSerializer`（`mask_phone`，不返回明文） | DONE | |
| US-197 | AC-197-05 | `AdminAppealListView`（`status` 过滤不变，序列化器统一） | DONE | |
| US-198 | AC-198-01 | `ProofThumbs.vue`（弹层、上一份/下一份、关闭不重载列表） | DONE | 浏览器行为未实测 |
| US-198 | AC-198-02 | `ProofThumbs.vue`（pdf 图标+文件名、iframe 预览、下载入口） | DONE | 浏览器行为未实测 |
| US-198 | AC-198-03 | `ProofThumbs.vue`（逐项渲染，数量=`proof` 长度；上限由后端 ≤5） | DONE | |
| US-198 | AC-198-04 | `residency/apps.py:AppealAttachmentPolicy.can_open`（无关登录用户 403；未登录 401 沿用 `IsMemberOrAdmin`） | DONE | OQ-07 待用户确认 |
| US-198 | AC-198-05 | 同上（申请人本人、管理员放行）；资料仅经鉴权下载接口，无公开地址 | DONE | |
| US-199 | AC-199-01 | `residency/views.py:AppealListCreateView.post`（存 `owner_name`）；`Units.vue`、`pages/units/index.vue` | DONE | |
| US-199 | AC-199-02 | 同上（`NAME_REQUIRED` 400，位于附件校验之前） | DONE | |
| US-199 | AC-199-03 | `registry/ownership.py:OWNER_NAME_MAX=64`；视图 `INVALID_VALUE` | DONE | |
| US-199 | AC-199-04 | `Units.vue:certify`、`pages/units/index.vue:certify`（失败时姓名写入申诉表单，已选房屋保留） | DONE | |
| US-200 | AC-200-01 | `residency/views.py:CertificationView` + `registry/ownership.py:owner_matches` | DONE | |
| US-200 | AC-200-02 | `CertificationView`（`NAME_REQUIRED` 400，不发起比对） | DONE | |
| US-200 | AC-200-03 | `CertificationView`（统一 422 `OWNER_NOT_MATCHED`，响应不含清册信息） | DONE | |
| US-200 | AC-200-04 | `owner_matches`（按 `(unit, phone)` 取业主后比姓名，同一业主） | DONE | |
| US-200 | AC-200-05 | `normalize_owner_name`（全角空格→半角、strip；中间空格保留；无模糊） | DONE | scratch：`"　张三 "` 通过，`"张 三"` 不通过 |
| US-200 | AC-200-06 | `owner_matches`（清册姓名为空→False） | DONE | |
| US-200 | AC-200-07 | `CertificationView`（单一错误出口） | DONE | scratch：四种失败响应体逐字相同 |
| US-200 | AC-200-08 | `CertificationView`（限频 30/3600 沿用，先于校验） | DONE | |
| US-200 | AC-200-09 | `residency/auto_bind.py` 等未改 | DONE | |
| US-201 | AC-201-01 | `Units.vue`/`pages/units/index.vue`（转申诉保留房屋与姓名）；`AppealListCreateView` | PARTIAL | 小程序仅图片（OQ-06 偏离 pdf），Web 满足 jpg/png/pdf；已在开放问题标"待用户确认" |
| US-201 | AC-201-02 | `CertificationView` 固定文案；两端提示文案不含清册信息 | DONE | |
| US-201 | AC-201-03 | `AppealListCreateView`（`APPEAL_PENDING` 沿用） | DONE | |
| US-201 | AC-201-04 | `AppealListCreateView`（`ATTACHMENT_LIMIT`）、上传接口 `APPEAL_PROOF` 规格（未改） | DONE | |
| US-202 | AC-202-01 | `CertificationView`（无手机号→`owner_matches` 假→422，不再 409 `PHONE_REQUIRED`）；申诉入口两端开放 | DONE | |
| US-202 | AC-202-02 | `AppealListCreateView`（`PROOF_REQUIRED`） | DONE | |
| US-202 | AC-202-03 | 未改动自动绑定通路（C-61） | DONE | |
| US-202 | AC-202-04 | `owner_matches`（`phone` 为空→False） | DONE | |
| US-203 | AC-203-01 | `AdminAppealDecisionView._append_registry` + `ownership.append_owner_from_appeal` | DONE | scratch 验证 |
| US-203 | AC-203-02 | 同上（无手机号只写姓名，`notice="该产权人无联系电话"`）；`AdminAppeals.vue` 通过前提示、通过后 `warning` | DONE | |
| US-203 | AC-203-03 | `append_owner_from_appeal`（同名复用并追加号码） | DONE | 逻辑已实现；scratch 覆盖"新增/无手机号/同号冲突/历史申诉"，同名追加由 test-engineer 补用例 |
| US-203 | AC-203-04 | `PhoneOwnedByOtherOwner`→409 `PHONE_OWNED_BY_OTHER`，事务回滚 | DONE | scratch：申诉仍 PENDING、无认证、无清册变化 |
| US-203 | AC-203-05 | `_append_registry`（未预期异常→409 `REGISTRY_UPDATE_FAILED`，事务回滚） | DONE | |
| US-203 | AC-203-06 | `_append_registry`（`SKIPPED_NO_OWNER_NAME`，审计注记） | DONE | scratch 验证 |
| US-203 | AC-203-07 | `append_owner_from_appeal` 不调用 `AutoBindService`、不触 `Membership` | DONE | |
| US-203 | AC-203-08 | `_append_registry`（`REGISTRY_UNIT_CHANGED` 审计：申诉编码、unit、`result`、`names_before/after`、脱敏号码；操作人=审计 actor） | DONE | |
| US-203 | AC-203-09 | `AdminAppealDecisionView`（REJECT 分支不调用追加） | DONE | |
| US-204 | AC-204-01 | `CertificationView`（第二套房与首次同路径；认证不写清册） | DONE | |
| US-204 | AC-204-02 | 同上（统一 422，不含清册信息） | DONE | |
| US-204 | AC-204-03 | `owner_matches` | DONE | |
| US-204 | AC-204-04 | `_append_registry`（追加；第一套房 `Membership` 不动） | DONE | |
| US-205 | AC-205-01 | `committee/views.py:AdminSeatListCreateView.post`（删除开始日分支）；`services.py:CommitteeCommands.grant` | DONE | |
| US-205 | AC-205-02 | `grant`（`term_end <= 今天`→400，文案含结束日） | DONE | |
| US-205 | AC-205-03 | 同上（等于今天拒绝、明天成功） | DONE | |
| US-205 | AC-205-04 | `grant`（`ALREADY_SEATED` 在结束日校验之后，含未生效席位） | DONE | |
| US-205 | AC-205-05 | `grant`（`CAP_REACHED`，含未生效席位） | DONE | |
| US-205 | AC-205-06 | `IsAdmin`（未改） | DONE | |
| US-205 | AC-205-07 | 不追溯：未改任何历史决议/投票/审批数据 | DONE | |
| US-206 | AC-206-01 | `committee/effective.py` + `CommitteeQuery.*`、`accounts/directory.py:identity_view`、`accounts/views.py` 用户列表预取 | DONE | scratch：未来席位 `/me` 无"委员"；权限类经 `active_seat` 自动生效 |
| US-206 | AC-206-02 | `expire_due`（未改，只处理 `term_end < today`） | DONE | scratch：未来席位 `expire_due` 返回 0 |
| US-206 | AC-206-03 | `effective_q`（`term_start <= 今天`立即生效） | DONE | |
| US-206 | AC-206-04 | `grant`（`ALREADY_SEATED`/`CAP_REACHED` 保持含未生效，Q-OA-28=A） | DONE | scratch：未来席位占名额并 409 |
| US-206 | AC-206-05 | `effective_q`（`term_start == 今天` 生效） | DONE | |

无 MISSING。1 条 PARTIAL（AC-201-01 小程序 pdf）：原因为设计已知偏离（ADR-116/OQ-06，微信 `wx.chooseMessageFile` 无仓库内资料，`[UNSOURCED]`），待用户确认。

## 既有测试最小同步（REWORK_AUTHORIZED，GR-B-001 条件）

仅改因本批口径变更而失效的断言/调用参数；未删除、未跳过任何用例；未新增用例文件。"原"= 变更前，"新"= 变更后。行号为改后文件行号（`git diff -U0` 核对）。

| 文件:行 | 原断言 / 调用 | 新断言 / 调用 | 原因 |
|---|---|---|---|
| `backend/tests/e2e/test_gap_journeys.py:65-72` | `POST /certifications {"unit_id"}`；422 `PHONE_NOT_IN_REGISTRY` | 补 `name`；422 `OWNER_NOT_MATCHED`；管理员改清册后用新业主姓名认证 | IFC-306 强制姓名；统一错误码 |
| `backend/tests/e2e/test_identity_display_journey.py:46,66-67` | 认证缺 `name` | 补 `name="杨扬"`（夹具业主名） | IFC-306 |
| `backend/tests/e2e/test_journeys.py:37,53-54,78-79,84` | 认证缺 `name`；422 `PHONE_NOT_IN_REGISTRY`；申诉缺 `owner_name` | 补 `name`/`owner_name`；422 `OWNER_NOT_MATCHED` | IFC-306/307 |
| `backend/tests/e2e/test_product_review_journeys.py:83,117` | 申诉缺 `owner_name` | 补 `owner_name` | IFC-307 |
| `backend/tests/e2e/test_registry_import_journeys.py:139-141,149-150,162` | 认证缺 `name`；422 `PHONE_NOT_IN_REGISTRY` | 补 `name`（"老业主"/"王芳"）；422 `OWNER_NOT_MATCHED` | IFC-306 |
| `backend/tests/e2e/test_rework_journeys.py:32-33` | 认证缺 `name` | 补 `name` | IFC-306 |
| `backend/tests/e2e/test_unit_sort_filters_journeys.py:112-114,131-136,222-223` | 认证缺 `name`；422 `PHONE_NOT_IN_REGISTRY` | 补 `name`（对应夹具业主名）；422 `OWNER_NOT_MATCHED` | IFC-306 |
| `backend/tests/integration/test_admin_appeals_regression.py:11-12,37` | `ITEM_KEYS` 无 `owner_name`；`applicant` 键集 `{id,account_no,phone}` | `ITEM_KEYS` 含 `owner_name`；`applicant` 键集含 `nickname`、`has_phone` | IFC-308 新增字段（键集合精确断言） |
| `backend/tests/integration/test_gap_must_have.py:278-279,290-291,316-317,404-405,438-443,893-899` | 认证缺 `name`；422 `PHONE_NOT_IN_REGISTRY`；无手机号 409 `PHONE_REQUIRED`（AC-002-04） | 补 `name`；422 `OWNER_NOT_MATCHED`；无手机号现为 422 `OWNER_NOT_MATCHED`（`/me` 仍不受限的断言保留） | IFC-306；设计"既有测试影响"登记 |
| `backend/tests/integration/test_product_review_ac.py:44-45,876-877` | 申诉缺 `owner_name` | 补 `owner_name` | IFC-307 |
| `backend/tests/integration/test_product_review_ac.py:831-846`（TC-INT-472） | 开始日早于今天 → 400 "任期开始日不得早于今天" | 配置任期后：昨天开始日授予成功 201；超久远开始日 → 400 且提示"不能授予" | REQ-FUNC-199（设计登记） |
| `backend/tests/integration/test_product_review_gap_stories.py:84-90,105-107,119-120` | 认证缺 `name`；422 `PHONE_NOT_IN_REGISTRY`；申诉缺 `owner_name` | 补 `name`/`owner_name`；422 `OWNER_NOT_MATCHED` | IFC-306/307 |
| `backend/tests/integration/test_registry_import_enhancement.py:154-159,263-264,278-279,405-406,563-564,652,661-662,793,839-847,849-851,853-858,862-863,869` | 认证缺 `name`；422 `PHONE_NOT_IN_REGISTRY`（含文案"手机号与清册不一致，可提交产权申诉"）；无手机号 409 `PHONE_REQUIRED` + 文案"请先绑定手机号" | 补 `name`；422 `OWNER_NOT_MATCHED` + 新固定文案；无手机号 422 且 `appeal_available` 为真 | IFC-306 |
| `backend/tests/integration/test_registry_sort_options.py:129,135-136` | 认证缺 `name`；422 `PHONE_NOT_IN_REGISTRY` | 补 `name`；422 `OWNER_NOT_MATCHED` | IFC-306 |
| `backend/tests/integration/test_residency_api.py:46,53-55,61-66,71,79,85,102,118-119,139-140,151-152,165-168` | 认证缺 `name`；申诉缺 `owner_name`；422 `PHONE_NOT_IN_REGISTRY` | 补 `name`/`owner_name`；422 `OWNER_NOT_MATCHED` | IFC-306/307 |
| `backend/tests/integration/test_rework_cr011_024.py:373-374,383-387`（设计引用的 :376 不准，实际为 :383 起的"无关普通用户"断言） | 申诉缺 `owner_name`；无关登录用户下载申诉附件 → 404 | 补 `owner_name`；→ 403 且响应体不含资料字节 | ADR-112 / OQ-07 |
| `backend/tests/remote/remote_cases.py:328-329` | `POST /appeals` 缺 `owner_name` | 补 `owner_name="e2e_申诉人"` | IFC-307（远程用例未运行，见开放问题风险） |
| `backend/tests/smoke/test_flows_smoke.py:79,82,90,92` | 认证缺 `name`；422 `PHONE_NOT_IN_REGISTRY` | 补 `name="业主甲"`；422 `OWNER_NOT_MATCHED` | IFC-306 |
| `backend/tests/unit/test_registry_ordering.py:68-76`（TC-UNIT-619） | 楼栋序 `["1","10","A区","地下车位"]`；`natural_key("地下车位","building")[0]==2` | `["1","10","地下车位","A区"]`；楼栋级层级 1，文字楼栋层级 3 | ADR-108 |
| `frontend/tests/product_review_ui.spec.js:104`（TC-UNIT-524） | 直接点击"认证产权" | 先填入姓名输入框再点击 | 认证前端先校验姓名非空 |
| `miniprogram/tests/api.spec.js:86-92`（TC-MP-008，设计引用 :90） | `api.certify(9)`；`createAppeal` 无 `owner_name` | `api.certify(9, '张三')`，断言请求体含 `name`；`createAppeal` 含 `owner_name` | IFC-314 |
| `miniprogram/tests/product_review_ui.spec.js:32-34`（TC-UNIT-551） | 页面"没有任何文本输入框" | 仅有两个文本框（姓名、产权人名字），无专有部分编号输入 | REQ-FUNC-193/192 新增姓名类输入 |

设计"既有测试影响"中提及、实测无需改动的：`test_frontend_contract.py:619`（成员侧申诉字段集，未改）；席位夹具（开始日均为今天或更早，仍生效）；上批命令测试 `test_underground_*`、`test_registry_export_cmd`（零新增失败，除下述环境产物外）。

## 迁移

`backend/apps/residency/migrations/0003_appeal_owner_name.py`：`AddField(appeal.owner_name, CharField(max_length=64, blank=True, default=""))`，依赖 `0002_closed_status`，手写、单 app，文件头注释"手写迁移（画像 P6）"，不含 "Generated by Django"。可逆：已在 scratch SQLite 上 `migrate residency 0002`（Unapplying OK）后再正向 `migrate`（OK）。`makemigrations --check --dry-run` 在置空 `MIGRATION_MODULES` 的 scratch 设置下对 residency 无漂移（仓库内其他 app 的既有 `Alter field id` 漂移与本批无关，未触碰）。测试环境数据修正（商铺 107 条）不走迁移，由 `relocate_shops` 执行（ADR-107）。

## 架构偏差

无。（审计 `detail` 键名采用 module_design IFC-309 的 `names_before/names_after/phone_masked`，与 ADR-114 正文的 `owner_before/owner_after/phone_after` 不同，以 module_design 为准，不视为偏差。）

## 开放问题

| 编号 | 类别 | 内容 | 状态 |
|---|---|---|---|
| OQ-01 | `[ASSUMPTION]` | 纯数字原楼栋写入 `unit_no` 时补"栋"（`1→1栋`），实现于 `registry/shops.py:shop_unit_no`（单点，改此函数即可） | **待用户确认** |
| OQ-04 | `[ASSUMPTION]` | 席位开始日上界"今天起 5 年"（`committee/views.py:TERM_START_MAX_DAYS = 5*366`） | **待用户确认** |
| OQ-06 | `[ASSUMPTION]` | 小程序申诉资料仅图片（`uni.chooseImage`），pdf 仅 Web；AC-201-01 小程序部分 PARTIAL | **待用户确认** |
| OQ-07 | `[ASSUMPTION]` | 无关已登录用户下载申诉附件 404 → 403（`residency/apps.py`） | **待用户确认** |
| A-01 | `[ASSUMPTION]` | `shops.py` 中旧楼栋为空、`unit_no` 非空、新值超 32 字的商铺只记入冲突（不进 `moves`），整批停止 | 开发自定，供评审 |
| A-02 | `[ASSUMPTION]` | `export_registry_import_file --output-dir` 文件名为本地时间秒级；同一秒内再次导出按"不覆盖"退出码 3 | 开发自定 |
| A-03 | `[ASSUMPTION]` | `seat_view.effective` 在 GET/POST/PATCH 响应中一致返回 | 开发自定 |
| A-04 | `[ASSUMPTION]` | `ProofThumbs.vue` 在无 `createImageBitmap`/`IntersectionObserver` 的环境降级为直接用 Blob / 立即加载；目标浏览器版本仓库内无登记（tech_stack 同） | 未实测 |
| R-01 | 风险（给 PM/test-engineer） | `backend/tests/remote/remote_cases.py` 的 TC-E2E-337 对测试环境真实房屋 `FIX["u1"]` 提交申诉并"通过"，本批后通过会向**真实清册追加**产权人，可能越出画像 P4-1（不得改动已导入业主清册）。本批仅补 `owner_name` 参数使其可调用，**未运行**；建议 GROUP_D/E2 改用 e2e 专属专有部分或将该用例标 NOT_TESTABLE | 待 PM 决定 |
| R-02 | 环境 | 开发机仓库根存在 git 忽略的历史导出文件 `registry_import_underground_parking.xlsx`（含个人信息可能性，mtime 2026-11-16 14:00，早于本批），使上批用例 `test_registry_export_cmd...test_tc_int_611` 失败。本批改动前后均失败（全新检出的 scratch 副本中该用例通过）。未删除（非本批产物，且 C-59），请 PM/用户处理该文件后复跑 | 待 PM 处理 |
| S-01 | stub | 无 `TODO(IFC-NNN)` / `[UNSOURCED]` 项（本批不涉及闭源 API，P11 出处表无新增） | — |
| N-01 | 发布 | 小程序须重新构建并发布（旧版认证将得 400）；`uni build -p mp-weixin` 在开发机因 uni alpha 工具链失败已知（记忆 M-SD-006），本次用 vitest + `@vue/compiler-sfc` 编译检查代替，见 code_review_report | 提示 E1 |
