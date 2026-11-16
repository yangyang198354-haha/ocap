<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T19:08:09+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0)</file>
    <file>requirements/user_stories.md (1.0.0)</file>
    <file>architecture/architecture_design.md (1.0.0)</file>
    <file>architecture/module_design.md (1.0.0)</file>
    <file>development/implementation_plan.md (1.0.0)</file>
    <file>development/code_review_report.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：房屋选择结构整理、申诉审核增强、认证姓名核对与席位授予放宽（INCREMENTAL）

## 测试策略

- **被测改动**：MOD-111~118（商铺改库命令 `relocate_shops`、楼栋排序与选项 `level_label`、导出命令位置/未归类守卫、姓名归一与追加清册、认证/申诉/附件后端、席位生效谓词与授予放宽、Web 与小程序页面）；GR-C-001 条件 F01（TC-INT-611 依赖仓库根状态）、F02（远程 TC-E2E-337 越出 P4-1）。
- **范围**
  - in scope：US-193~206 全部 79 条 AC 中可自动化的部分；两端 api.js 契约；既有用例的回归（全量）。
  - out of scope：真实浏览器/真机行为（ProofThumbs 的 `createImageBitmap`/`IntersectionObserver`/pdf iframe、小程序真机，见"不可测项"与 e2e_test_report 人工验证清单）；任何连接测试机/真实清册的操作（改库与导出须用户另行授权，C-57；本批**不运行** `backend/tests/remote/**`，仅部署后由 E2 执行）。
- **环境**：venv Python 3.12.3 + Django 5.2.19（`/tmp/claude-0/-root-myproject-ocap/c20123b9-4e57-4ebf-b3eb-04a35210d0d9/scratchpad/venv`）；后端 `config.test_settings`（SQLite 内存库，`MIGRATION_MODULES` 置空，外部服务经 `apps/integrations/fakes.py`）；前端/小程序 vitest（jsdom，uni 桩）。全部合成姓名与手机号（C-59）；备份与导出文件只写 `tempfile` 临时目录（位置守卫用例的"合规目录"为 0700 临时目录）。严禁连接测试机、不 ssh、不 commit、不改产品代码、不读取/移动/删除仓库根用户保留文件（本批 TC-INT-611 修正只比对仓库根**文件名集合**，不读内容）。
- **判定模式与阈值**：INCREMENTAL / baseline（画像 P5）——每层相对基线零新增失败且新写用例全部通过；critical path 覆盖率 1.00；E2E critical path 覆盖前后端契约。
- **基线来源**：PM 实跑（GR-C-001，开发后）：后端 822 中 821 OK + 1 既有环境失败（TC-INT-611，即 GR-C-001-F01）；前端 259/259；小程序 97/97。本批修正 TC-INT-611 后该失败消失。
- **分层机制**（画像 P3/P4）：后端按目录 `backend/tests/{unit,integration,e2e,smoke}/`；前端/小程序 vitest 全量（含 TC-UNIT/TC-MP/既有 jsdom TC-E2E）计入单元层命令输出（vitest 不分目录）。新测试均放在对应目录、`test_*.py` / `*.spec.js` 命名，已验证被分层命令收集（见各层报告的计数增量）。
- **critical path 口径：替代**——无浏览器 E2E 框架，用最高层可执行的多步 HTTP 旅程（含管理命令、真实导入接口、真实令牌与权限）；前后端契约由 `test_frontend_contract.py` 与新增 `test_owner_auth_v2_contract.py` 守护。
- **缺陷能力验证（M-TE-012）**：在 scratchpad 的 `backend/`、`frontend/` 副本上对产品代码做 20 处定向变异（后端 14 + 前端 6），每处都使新用例失败：ownership 比对恒真（5 失败）、`term_start__lte` 去除（5）、商铺不补"栋"（10）、附件 403→False（1）、位置守卫去除（6）、保留名次序互换（4）、权限位检查去除（6）、`unit_no_occupied` 冲突去除（6）、更新行数核对去除（2）、同号冲突不抛错（1）、申诉通过分支（认证+追加）整体跳过（11）、结束日 `<=` 改 `<`（1）、开始日上界去除（1）、未生效席位 change 沿用开始日去除（1）；前端 6 处（认证不带 name、并发上限 30、`level_label` 不读取、"未提供"去除、"待生效"条件取反、pdf 也取缩略图）各使 1 条用例失败。副本在 scratchpad，未入库。

## AC 映射

用例级别：UNIT / INT / E2E（E2E = 替代口径，后端多步旅程）。运行方式：本项目无硬件，P11-1 为"无"，全部写 `sim`（本机真实执行）。位置前缀：`B:` = `backend/tests/`；`F:` = `frontend/tests/`；`M:` = `miniprogram/tests/`。现有 = 本批前已存在并同步更新过的用例；新写 = 本批新增。

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置（文件::类::方法） | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-193-01 | TC-INT-637、TC-UNIT-656、TC-UNIT-674、TC-MP-510、TC-E2E-516、TC-E2E-519、TC-INT-709/710 | INT/UNIT/E2E | sim | 新写 | B:integration/test_owner_auth_v2_shops.py::ShopOptionsTests::test_tc_int_637…；B:unit/test_owner_auth_v2_rules.py::BuildingOrderTests::test_tc_unit_656…；F:owner_auth_v2.spec.js(UnitCascader)；M:owner_auth_v2.spec.js(UnitPicker)；契约 B:integration/test_owner_auth_v2_contract.py | 改库后清册含 1~10 栋、地下车位、商铺 | GET /units/options 取第一级 | 依次 1…10、地下车位、商铺（12 项），无门牌型楼栋；两端读同一接口 | 合成清册 |
| AC-193-02 | TC-INT-638、TC-INT-626、TC-UNIT-651、TC-E2E-519 | INT/UNIT/E2E | sim | 新写 | 同上 shops / rules | 1 栋内有商铺（4347 类，楼层"负1"） | 逐级选 1 栋；选商铺逐级找该商铺 | 1 栋下无商铺；商铺下可达（找到集合 = 商铺 id 集合） | 同上 |
| AC-193-03 | TC-INT-638、TC-UNIT-651 | INT/UNIT | sim | 新写 | 同上 | 类型空/其他在 1~10 栋内 | 选对应栋 | 仍在原栋，不归入商铺 | 同上 |
| AC-193-04 | TC-INT-641、TC-UNIT-656 | INT/UNIT | sim | 新写 | 同上 | 新增楼栋"配套用房" | 打开第一级 | 排在商铺之后，不丢失 | 同上 |
| AC-193-05 | TC-INT-641 | INT | sim | 新写 | 同上 | 无商铺记录 | 打开第一级 | 无"商铺"项，顺序不变，无报错 | 同上 |
| AC-194-01 | TC-INT-639、TC-UNIT-650/657、TC-UNIT-674 | INT/UNIT | sim | 新写 | 同上 | 商铺原楼栋 1/2/10 与门牌 | 选商铺看第二级 | 1栋<2栋<10栋<门牌；带 `level_label="楼栋/门牌"` | 同上 |
| AC-194-02 | TC-INT-640、TC-UNIT-676、TC-E2E-516 | INT/UNIT/E2E | sim | 新写 | 同上 | 门牌型商铺（无单元无楼层） | 选到门牌 | `skipped=["floor"]`，直接户号 | 同上 |
| AC-194-03 | TC-INT-638 | INT | sim | 新写 | 同上 | 多个商铺 | 逐级遍历 | 找到集合 = 全部商铺 id，无重复无遗漏 | 同上 |
| AC-194-04 | TC-INT-639、TC-UNIT-675、TC-MP-510 | INT/UNIT | sim | 新写 | 同上 | 选商铺后改选 2 栋 | 查看下一级 | 无商铺原楼栋残留；标签复位"单元" | 同上 |
| AC-195-01 | TC-INT-621、TC-INT-626、TC-INT-629、TC-E2E-519 | INT/E2E | sim | 新写 | B:integration/test_owner_auth_v2_shops.py::ShopDryRunTests/ShopApplyTests；B:e2e/test_owner_auth_v2_journeys.py::RelocateExportJourney | 合成清册（含已认证业主与待审申诉） | dry-run → apply(--backup --expect-changes) | 记录总数/业主数/手机号数/有效绑定数前后相等；楼栋"商铺"数 = 修正前商铺数；其余记录逐字段不变；仅 RegistryUnit 与审计两表有写入 | 合成 |
| AC-195-02 | TC-INT-626、TC-E2E-519、TC-UNIT-651 | INT/E2E | sim | 新写 | 同上 | 同上 | apply 后检查 | `lost_origin=0`；unit_no=原楼栋（纯数字补"栋"，门牌原样）；id 类 4347 标识 `商铺1栋负1层1139号` | 合成 |
| AC-195-03 | TC-INT-630/631/632/633、TC-UNIT-653/654 | INT/UNIT | sim | 新写 | B:integration/…shops.py::ShopConflictTests | 构造标识重复/原 unit_no 非空/超长/旧楼栋为空 | dry-run 与 apply | 退出码 2，输出冲突清单，库快照不变，无备份文件 | 合成 |
| AC-195-04 | TC-INT-628、TC-UNIT-652、TC-E2E-519 | INT/UNIT/E2E | sim | 新写 | 同上 | 已执行一次 | 再 dry-run / apply(0) | would_change=0、already_target=5、快照不变 | 合成 |
| AC-195-05 | TC-INT-635、TC-INT-636、TC-INT-627 | INT | sim | 新写 | 同上 ShopRestoreTests/ShopApplyTests | 已备份并 apply | `--restore [--apply]`；备份被篡改/记录非修正后状态 | 还原后逐记录一致（差异 0）、绑定数不变；异常时退出码 2/3 且库不变；备份 0600 且无个人信息 | 合成 |
| AC-195-06 | TC-INT-626、TC-E2E-519 | INT/E2E | sim | 新写 | 同上 | 已认证商铺业主 + 待审申诉 | apply 后 | 绑定记录不变、"我的房屋"名称随之变化、申诉仍待审可审核 | 合成 |
| AC-195-07 | TC-INT-621、TC-INT-622（本地零写证据）；过程性部分见 NT-04 | INT | sim | 新写 | 同上 | — | dry-run | 本地 0 写入；**未连接测试机/未 ssh** 属过程声明，见 NT-04 | — |
| AC-196-01 | TC-INT-645、TC-INT-643/644、TC-E2E-519 | INT/E2E | sim | 新写 | B:integration/…shops.py::ExportGuardTests | 归类后清册 | `--output-dir` 导出 | 计数差 0；预检失败/新增/更新均 0；楼栋列"商铺"行=5、"单元"列为原楼栋/门牌；导出只读；未归类时退出码 2 | 合成 |
| AC-196-02 | TC-E2E-519、TC-INT-645 | E2E/INT | sim | 新写 | B:e2e/…journeys.py::RelocateExportJourney | 导出文件 | 交给 `/admin/registry/import?dry_run=1` | failed=0、imported=0、updated=0，清册不变 | 合成 |
| AC-196-03 | TC-UNIT-662~666/689、TC-INT-645/647；站点 URL 不可取见 NT-03 | UNIT/INT | sim | 新写 | B:unit/test_owner_auth_v2_rules.py::ExportLocationGuardTests；B:integration/…shops.py | 目录 700/755、部署根/MEDIA/STATIC 内 | `check_output_location`、命令 | 700+部署根之外通过；755 或根内被拒（退出码 3，零查询）；文件 0600、名含日期 | 临时目录 |
| AC-196-04 | TC-INT-646 | INT | sim | 新写 | 同上 | 已有日期文件 | 清册变更后再导出 | 旧文件字节不变；同秒重复退出码 3 | 合成 |
| AC-196-05 | TC-INT-622/627/645（输出与备份无姓名/手机号）；真实文件检索见 NT-05 | INT | sim | 新写 | 同上 | — | 检查 stdout/备份 | 只含计数与 id | 合成 |
| AC-196-06 | TC-INT-649；既有 TC-INT-609 | INT | sim | 新写+现有 | 同上；B:integration/test_registry_export_cmd.py | 楼层 08、户号 0801、手机号 13800000000 | 归类后导出 | 单元格文本原值，往返差异 0 | 合成 |
| AC-196-07 | TC-INT-643/647；既有 TC-INT-617/618/619 | INT | sim | 新写+现有 | 同上 | 未归类/位置非法/落盘失败 | 导出 | 未归类退出码 2；位置非法 3 且不触库；失败无残缺文件 | 合成 |
| AC-197-01 | TC-INT-670、TC-INT-715、TC-UNIT-677、TC-E2E-516 | INT/UNIT/E2E | sim | 新写 | B:integration/test_owner_auth_v2_residency.py::AdminAppealListTests；F:owner_auth_v2.spec.js(AdminAppeals) | 申诉 id=123、账号、昵称、产权人名字 | 管理员打开列表 | 编码/账号/昵称/产权人名字/时间/坐落/资料数齐全 | 合成 |
| AC-197-02 | TC-INT-672、TC-UNIT-678 | INT/UNIT | sim | 新写 | 同上 | 无昵称 | 查看 | nickname=null → "未设置" | 合成 |
| AC-197-03 | TC-INT-672、TC-UNIT-678 | INT/UNIT | sim | 新写 | 同上 | 旧申诉 owner_name 空串 | 查看 | owner_name=null → "未提供" | 合成 |
| AC-197-04 | TC-INT-671、TC-UNIT-677 | INT/UNIT | sim | 新写 | 同上 | 申请人有手机号 | 查看 | 仅脱敏，全文无完整号码 | 合成 |
| AC-197-05 | TC-INT-673 | INT | sim | 新写 | 同上 | 一待审一已拒 | status=PENDING | 仅待审，行字段完整 | 合成 |
| AC-198-01 | TC-UNIT-681 | UNIT | sim | 新写 | F:owner_auth_v2.spec.js(AdminAppeals/ProofThumbs) | 3 份资料 | 点第 2 张→弹层→上/下一份→关闭 | 弹层取该资料原图；切换；关闭后列表不重载（浏览器真实行为见 NT-02） | mock Blob |
| AC-198-02 | TC-UNIT-683、TC-UNIT-681 | UNIT | sim | 新写 | 同上 | pdf + 图片 | 查看/点击 pdf | pdf 显示图标+文件名不取缩略图；弹层 iframe + 下载链接 | mock Blob |
| AC-198-03 | TC-INT-674、TC-UNIT-682、TC-UNIT-672 | INT/UNIT | sim | 新写 | 同上 | 5 份资料 | 列表 | 恰 5 个缩略图格；并发 ≤3；页内查询数不随行数增长 | 合成 |
| AC-198-04 | TC-INT-676、TC-INT-675、TC-UNIT-684、TC-E2E-516 | INT/UNIT/E2E | sim | 新写 | 同上 | 未登录/普通用户/无关登录用户 | 访问下载/列表 | 401/403，响应体无资料字节；前端显示错误且无 img | 合成 |
| AC-198-05 | TC-INT-676、TC-INT-677 | INT | sim | 新写 | 同上 | 申请人本人/管理员 | 下载 | 200 且字节一致；列表无公开 url 字段 | 合成 |
| AC-199-01 | TC-INT-666/713/714、TC-UNIT-671、TC-MP-508 | INT/UNIT | sim | 新写 | B:integration/…residency.py::AppealSubmitTests；…contract.py；F、M | 选房+1~5 资料 | 填产权人名字提交 | 201 并保存；两端发送键 = {unit_id, owner_name, proof_ids} | 合成 |
| AC-199-02 | TC-INT-666、TC-UNIT-670、TC-MP-507 | INT/UNIT | sim | 新写 | 同上 | 名字空/空格 | 提交 | 400 NAME_REQUIRED「请输入产权人名字」，无申诉 | 合成 |
| AC-199-03 | TC-INT-666 | INT | sim | 新写 | 同上 | 64/65 字 | 提交 | 64 成功（存归一值）；65 被拒 | 合成 |
| AC-199-04 | TC-UNIT-669、TC-MP-506 | UNIT | sim | 新写 | F、M | 认证失败转申诉 | 进入申诉表单 | 姓名带入产权人名字，已选房屋保留 | 合成 |
| AC-200-01 | TC-INT-650、TC-UNIT-668、TC-MP-505、TC-E2E-516 | INT/UNIT/E2E | sim | 新写 | B:integration/…residency.py::CertificationNameTests | 同一业主姓名+手机号 | 认证 | 201 HEAD；后续 OWNER | 合成 |
| AC-200-02 | TC-INT-651/712、TC-UNIT-667、TC-MP-504 | INT/UNIT | sim | 新写 | 同上 | 缺/空/空格/非字符串 | 认证 | 400 NAME_REQUIRED「请输入姓名」，不发起比对（mock 断言） | 合成 |
| AC-200-03 | TC-INT-652、TC-E2E-516 | INT/E2E | sim | 新写 | 同上 | 姓名错 | 认证 | 422 OWNER_NOT_MATCHED，不含清册姓名/号码 | 合成 |
| AC-200-04 | TC-INT-653 | INT | sim | 新写 | 同上 | 两业主 | 用乙的号输甲的名 | 422；输乙的名 201 | 合成 |
| AC-200-05 | TC-INT-654、TC-UNIT-659 | INT/UNIT | sim | 新写 | 同上 | 全角/首尾/中间空格、张三丰 | 认证 | 归一后通过；中间空格、近似名不通过 | 合成 |
| AC-200-06 | TC-INT-655 | INT | sim | 新写 | 同上 | 清册姓名 None/空 | 认证 | 422 | 合成 |
| AC-200-07 | TC-INT-656 | INT | sim | 新写 | 同上 | 四种失败 | 认证 | 响应字节完全相同 | 合成 |
| AC-200-08 | TC-INT-657 | INT | sim | 新写 | 同上 | 30 次后 | 第 31 次 | 429（前 30 次均 422） | 合成 |
| AC-200-09 | TC-INT-658 | INT | sim | 新写 | 同上 | 清册登记手机号注册 | register | 自动绑定，无姓名；清册姓名为空也绑定 | 合成 |
| AC-201-01 | TC-UNIT-669/671、TC-MP-506/508、TC-INT-668（pdf Web）、TC-E2E-516 | UNIT/INT/E2E | sim | 新写 | F、M、B | 核对失败 | 转申诉并上传 | 保留房屋与姓名；1~5 资料；Web 含 pdf。**小程序 pdf：NT-01（OQ-06，PARTIAL）** | 合成 |
| AC-201-02 | TC-INT-652、TC-UNIT-669、TC-MP-506 | INT/UNIT | sim | 新写 | 同上 | 核对失败 | 看提示 | 不含清册姓名/号码或失败原因区分 | 合成 |
| AC-201-03 | TC-INT-667 | INT | sim | 新写 | 同上 | 已有待审 | 再提交 | 409 APPEAL_PENDING，仅 1 条 | 合成 |
| AC-201-04 | TC-INT-667、TC-UNIT-670/672 | INT/UNIT | sim | 新写 | 同上 | 6 个/.exe/>10MB | 提交/上传 | 400 ATTACHMENT_LIMIT；上传 400/413；无申诉 | 合成 |
| AC-202-01 | TC-INT-661、TC-INT-660、TC-E2E-517 | INT/E2E | sim | 新写 | B:integration/…residency.py::PhonelessAndSecondUnitTests | 无手机号账号 | 认证→申诉 | 422（非 409 PHONE_REQUIRED）；申诉待审 | 合成 |
| AC-202-02 | TC-INT-662、TC-E2E-517 | INT/E2E | sim | 新写 | 同上 | 无资料 | 提交 | 400 PROOF_REQUIRED | 合成 |
| AC-202-03 | TC-INT-663 | INT | sim | 新写 | 同上 | 待审期间绑定手机号 | 绑定 | 不自动认证，申诉仍待审 | 合成 |
| AC-202-04 | TC-INT-661 | INT | sim | 新写 | 同上 | 姓名恰同清册 | 认证 | 422 不认证 | 合成 |
| AC-203-01 | TC-INT-678、TC-E2E-516 | INT/E2E | sim | 新写 | B:integration/…residency.py::AppealDecisionAppendTests | 号码 P9、名字王五、原业主张三 | 通过 | 认证；新增王五+P9；张三与号码、其认证关系不变 | 合成 |
| AC-203-02 | TC-INT-679、TC-E2E-517、TC-UNIT-679 | INT/UNIT/E2E | sim | 新写 | 同上；F | 无手机号 | 通过 | 只写姓名；notice「该产权人无联系电话」；has_phone=false | 合成 |
| AC-203-03 | TC-INT-680 | INT | sim | 新写 | 同上 | 已有同名无号码 | 通过 | 不新增第二个，号码追加（PHONE_ADDED） | 合成 |
| AC-203-04 | TC-INT-681、TC-UNIT-680 | INT/UNIT | sim | 新写 | 同上 | 号码属另一业主 | 通过 | 409 PHONE_OWNED_BY_OTHER，整笔回滚 | 合成 |
| AC-203-05 | TC-INT-682/683、TC-UNIT-680 | INT/UNIT | sim | 新写 | 同上 | 更新失败/半途失败 | 通过 | 409 REGISTRY_UPDATE_FAILED；无部分写入；可重试成功 | 合成 |
| AC-203-06 | TC-INT-684 | INT | sim | 新写 | 同上 | 旧申诉无名字 | 通过 | 认证；清册不变；审计注明 | 合成 |
| AC-203-07 | TC-INT-685/686 | INT | sim | 新写 | 同上 | 追加号码 | 通过 | 他人认证数不变；不调用 AutoBindService。（"新号码恰为另一账号手机号"因手机号唯一不可达，见说明） | 合成 |
| AC-203-08 | TC-INT-678 | INT | sim | 新写 | 同上 | 一次追加 | 查审计 | 申诉编码、更新前后姓名、脱敏手机号（无完整号码）、结果、操作人 | 合成 |
| AC-203-09 | TC-INT-687、TC-E2E-518 | INT/E2E | sim | 新写 | 同上 | 拒绝 | 拒绝完成 | 清册无变化，无 registry_update | 合成 |
| AC-204-01 | TC-INT-664、TC-E2E-518 | INT/E2E | sim | 新写 | B:integration/…residency.py::PhonelessAndSecondUnitTests | 已认证一套房 | 认证第二套 | 422，清册业主与号码逐项不变 | 合成 |
| AC-204-02 | TC-INT-664 | INT | sim | 新写 | 同上 | 清册登记他人 | 提交 | 同上，响应不含清册信息 | 合成 |
| AC-204-03 | TC-INT-665、TC-INT-650 | INT | sim | 新写 | 同上 | 同一业主姓名+号码 | 认证 | 201 | 合成 |
| AC-204-04 | TC-INT-688、TC-E2E-518 | INT/E2E | sim | 新写 | 同上 | 第二套申诉 | 通过 | 追加第二套清册；第一套认证与清册不变 | 合成 |
| AC-205-01 | TC-INT-690/708、TC-E2E-520、TC-UNIT-688 | INT/UNIT/E2E | sim | 新写+现有 | B:integration/test_owner_auth_v2_seats.py；既有 TC-INT-472（已按新口径同步，B:integration/test_product_review_ac.py） | 任期 36 个月，开始日=今天−300 天 | 授予 | 201，开始日/结束日正确，不再提示"不得早于今天" | 合成 |
| AC-205-02 | TC-INT-691、TC-E2E-521 | INT/E2E | sim | 新写 | 同上 | 开始日 2020-01-01 | 授予 | 400「按配置任期，该席位已于 2023-01-01 结束，不能授予」 | 合成 |
| AC-205-03 | TC-INT-692、TC-UNIT-660 | INT/UNIT | sim | 新写 | 同上 | 结束日=今天/明天 | 授予 | 前者被拒后者成功 | 合成 |
| AC-205-04 | TC-INT-693、TC-E2E-520 | INT/E2E | sim | 新写 | 同上 | 已有有效席位 | 补录 | 409 ALREADY_SEATED | 合成 |
| AC-205-05 | TC-INT-694 | INT | sim | 新写 | 同上 | 人数已达上限 | 补录 | 409 CAP_REACHED | 合成 |
| AC-205-06 | TC-INT-695、TC-E2E-521 | INT/E2E | sim | 新写 | 同上 | 非管理员/未登录 | 授予 | 403/401，无席位 | 合成 |
| AC-205-07 | TC-INT-696 | INT | sim | 新写 | 同上 | 已有审批实例 | 补录授予 | 审批实例状态与记录逐项不变 | 合成 |
| AC-206-01 | TC-INT-697/698/699/700/701/702/705、TC-E2E-520、TC-UNIT-660/687 | INT/UNIT/E2E | sim | 新写 | 同上 | 开始日在将来 | /me、委员接口、主任接口、审批人选择、在任名单/分母、用户目录 | 开始日前全部不生效；开始日起生效；列表 effective=false→"待生效" | 合成 |
| AC-206-02 | TC-INT-703、TC-E2E-520 | INT/E2E | sim | 新写 | 同上 | 未来席位 + 已过期席位 | 到期任务 | 未来席位不被置到期；已过期被置到期 | 合成 |
| AC-206-03 | TC-INT-697/690、TC-UNIT-660 | INT/UNIT | sim | 新写 | 同上 | 开始日≤今天 | 授予 | 立即生效 | 合成 |
| AC-206-04 | TC-INT-704 | INT | sim | 新写 | 同上 | 未来席位已授予 | 再授予/他人占名额 | 409 ALREADY_SEATED / CAP_REACHED（Q-OA-28=A） | 合成 |
| AC-206-05 | TC-INT-697/705、TC-UNIT-660 | INT/UNIT | sim | 新写 | 同上 | 开始日=今天 | 授予 | 视为已生效 | 合成 |

**GR-C-001 条件处置**

| 条件 | 处置 | 位置 |
|---|---|---|
| F01 TC-INT-611 依赖仓库根状态 | 改为运行前后比对仓库根**文件名集合**（只列目录名，不读文件内容、不删除/移动），断言本次运行未新增/移除任何文件；仓库根用户保留文件不受影响（现 `ls` 仍在，mtime 14:00 不变） | `backend/tests/integration/test_registry_export_cmd.py::ExportSuccessTests::test_tc_int_611…` |
| F02 远程 TC-E2E-337 越出 P4-1 | 改为只走"提交申诉 → 管理员列表可见 owner_name 与资料 → 驳回 → 再申诉 → 再驳回"，**不执行通过**；`remote_client.guard` 新增护栏：`/admin/appeals/{id}/decision` 的 `decision` 只允许 `REJECT`，否则抛 GuardError（发请求前拦截）；"申诉通过追加清册/撤销认证"远程路径标 NOT_TESTABLE，由本地 TC-INT-678~688 与 TC-E2E-516/518 覆盖；本批不运行 remote | `backend/tests/remote/remote_cases.py::test_337…`、`remote_client.py::guard` |

## 测试数据需求

- 全部用例使用合成清册、合成姓名（如"张三测""王五""原业主甲"）与合成手机号（`tests/support.next_phone`），不使用真实数据（C-59）；会写入持久存储的只有临时 SQLite 内存库与 `tempfile` 临时目录，无持久化冲突风险（唯一化：`next_account_no`/`next_phone` 计数器）。
- `[DATA_REQUIRED]`：无（本批无 golden data；画像 P11-2 为"无"）。
- 真实清册只读核对（Q-OA-29：107 条商铺计数、楼层写法、冲突预演）依赖用户授权后主会话在测试机只读执行，**不属于本批自动化**，列入人工验证清单。

## 不可测项

| 编号 | AC | 原因 |
|---|---|---|
| NT-01 | AC-201-01（小程序 pdf 部分） | OQ-06：小程序申诉资料本批仅图片（`uni.chooseImage`），pdf 仅 Web；微信 `wx.chooseMessageFile` 无仓库内资料 `[UNSOURCED]`。Web 的 pdf 路径有用例（TC-INT-668、TC-UNIT-683）；记 PARTIAL，待用户确认。 |
| NT-02 | AC-198-01/02 的真实浏览器行为 | jsdom 无 `createImageBitmap`/`IntersectionObserver`/真实 iframe pdf 预览（CR-001）；组件逻辑已覆盖（并发、懒加载桩、弹窗、权限错误、对象地址释放），真实渲染须 E2 部署后人工核对一页 20 条×5 文件。 |
| NT-03 | AC-196-03 的"通过站点 URL 无法取得文件"与目标机目录 700/文件 600 | 依赖目标机部署与真实导出（须用户另行授权，C-57）；本地已验证位置守卫与 0600/700 校验逻辑。 |
| NT-04 | AC-195-07 / AC-196-07 的"未授权时不连接测试机、对任何环境写入数为 0"过程声明 | 过程性验收：本批 test-engineer 未 ssh、未连接测试机、未运行 `backend/tests/remote/**`（见报告命令清单），本地改库只在 SQLite 内存库；非自动化断言。 |
| NT-05 | AC-196-05 的"检索仓库、测试数据、报告与日志检索不到真实文件及其姓名手机号" | 真实文件在授权后才产生；本批已断言命令输出/备份不含姓名手机号（TC-INT-622/627/645），并确认本批测试数据全合成。 |

注：AC-203-07 中"追加的新号码恰为另一已存在账号 V 的已验证手机号"在现数据模型下不可达（用户手机号唯一，追加的是申诉人自己的号码），故以"他人认证数不变 + 不调用 AutoBindService"两个可观测不变量覆盖（TC-INT-685/686）。

## 故事覆盖核对

每个 Must Have 故事至少 1 个**真实执行**的用例（均已在本批最后一次全量运行中通过，见各层报告）。

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-193 | TC-INT-637/638/641、TC-UNIT-656/651、TC-UNIT-674、TC-MP-510、TC-E2E-516/519 | UNIT/INT/E2E |
| US-194 | TC-INT-639/640、TC-UNIT-650/657、TC-UNIT-675/676、TC-E2E-516/519 | UNIT/INT/E2E |
| US-195 | TC-INT-621~636、TC-UNIT-651~655、TC-E2E-519 | UNIT/INT/E2E |
| US-196 | TC-INT-643~649、TC-UNIT-662~666/689、TC-E2E-519 | UNIT/INT/E2E |
| US-197 | TC-INT-670~673/715、TC-UNIT-677/678、TC-E2E-516 | UNIT/INT/E2E |
| US-198 | TC-INT-674~677、TC-UNIT-681~686、TC-E2E-516 | UNIT/INT/E2E |
| US-199 | TC-INT-666/713/714、TC-UNIT-669~672、TC-MP-506~508、TC-E2E-516/517 | UNIT/INT/E2E |
| US-200 | TC-INT-650~660/712、TC-UNIT-667/668/659、TC-MP-504/505、TC-E2E-516 | UNIT/INT/E2E |
| US-201 | TC-INT-652/667/668、TC-UNIT-669~672、TC-MP-506/508（小程序 pdf：NT-01） | UNIT/INT/E2E |
| US-202 | TC-INT-660~663、TC-E2E-517 | INT/E2E |
| US-203 | TC-INT-678~687、TC-UNIT-679/680、TC-E2E-516/517/518 | UNIT/INT/E2E |
| US-204 | TC-INT-664/665/688、TC-E2E-518 | INT/E2E |
| US-205 | TC-INT-690~696/708、TC-UNIT-688、TC-E2E-520/521 | UNIT/INT/E2E |
| US-206 | TC-INT-697~705、TC-UNIT-660/687、TC-E2E-520 | UNIT/INT/E2E |

契约测试（协议 §J-D、规则 17）：`backend/tests/integration/test_frontend_contract.py`（既有，路径/方法/权限，两端 api.js 全量）+ `backend/tests/integration/test_owner_auth_v2_contract.py`（新写，TC-INT-709~719，字段级：两端 certify/createAppeal 声明与调用方键、管理端页面读取字段 ⊆ 后端响应、`level_label`、`effective`、已删除错误码不再被引用）；客户端关键调用逻辑另有 vitest 用例（TC-UNIT-667~688、TC-MP-504~510）。

## 用例统计（本批新写）

| 层 | 后端 | 前端 | 小程序 | 合计 |
|---|---|---|---|---|
| UNIT | 18（TC-UNIT-650~666、689） | 22（TC-UNIT-667~688） | 7（TC-MP-504~510） | 47 |
| INT | 99（TC-INT-621~719：shops 29、residency 40、seats 19、contract 11） | — | — | 99 |
| E2E | 6（TC-E2E-516~521） | — | — | 6 |
| 合计 | 123 | 22 | 7 | 152 |

另修改既有用例 2 条（TC-INT-611、远程 TC-E2E-337，及 `remote_client.guard` 护栏）；回归用现有用例 = 本批前全部既有用例（后端 822、前端 259、小程序 97）。
