<phase_status project="ocap_registry_import" mode="INCREMENTAL" created="2026-11-10T15:52:12+08:00" updated="2026-11-10T23:33:31+08:00">
  <request time="2026-11-10T15:52:12+08:00"><![CDATA[管理员业主清册导入，批量导入支持哪些文件，是否有格式要求。能否在页面有一个模板下载？ 这个模板要灵活，因为一个专有部分可能登记多个产权业主，可能一个，两个，三个，特别的可能五六个甚至更多。数量上不应该受限。单个导入，或者批量导入，都应该记录专有部分类型，比如住宅，公寓，商铺，车位，专有部分面积等等。增加这个需求，先整理需求和用户故事。确认后再开始开发]]></request>
  <request_context><![CDATA[PM 只读核查的现状（2026-11-10）：
- backend/apps/registry/views.py:20 IMPORT_COLUMNS = 楼栋、单元、楼层、户号、手机号；多个手机号用英文分号分隔（views.py:172）。
- views.py:124-129 仅支持 .csv / .xlsx，≤5 MB；views.py:136 ≤5000 行；只读 xlsx 第一个工作表。
- views.py:100 单条"登记手机号"接口限制最多 10 个手机号。
- backend/apps/registry/models.py：RegistryUnit 只有楼栋/单元/楼层/户号/specific_part；RegistryPhone 只有手机号，没有业主姓名、专有部分类型、面积。
- frontend/src/admin/AdminRegistry.vue：有"批量导入"和"新增"按钮，没有模板下载，页面上也没有格式说明。
- 既有需求：project_workspace/ocap/requirements/requirements_spec.md REQ-FUNC-009、REQ-FUNC-018。]]></request_context>
  <profile version="1.3.0"/>
  <workspace_note>独立增量项目，文档在 project_workspace/ocap_registry_import/（nested）；代码按画像 P3 in-repo。用户要求：本次只做需求与用户故事，确认后再开发。</workspace_note>
  <groups>
    <group id="GROUP_A" agent="requirement-analyst" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0">
      <phase id="PHASE_01" status="APPROVED"/><phase id="PHASE_02" status="APPROVED"/>
    </group>
    <group id="GROUP_B" agent="system-architect" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0">
      <phase id="PHASE_03" status="APPROVED"/><phase id="PHASE_04" status="APPROVED"/>
    </group>
    <group id="GROUP_C" agent="software-developer" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0">
      <phase id="PHASE_05" status="APPROVED"/><phase id="PHASE_06" status="APPROVED"/>
    </group>
    <group id="GROUP_D" agent="test-engineer" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0" defect_loops="0">
      <phase id="PHASE_07" status="APPROVED"/><phase id="PHASE_08" status="APPROVED"/><phase id="PHASE_09" status="APPROVED"/>
    </group>
    <group id="GROUP_E1" agent="devops-engineer" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0">
      <phase id="PHASE_10" status="APPROVED"/><phase id="PHASE_11a" status="APPROVED"/>
    </group>
    <group id="GROUP_E2" agent="devops-engineer" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0" environment="测试环境（树莓派 192.168.31.51 / ai-freeark.xin）">
      <phase id="PHASE_11b" status="APPROVED"/>
    </group>
    <group id="GROUP_Z" agent="kb-curator" status="APPROVED" gate_decision="PASS" retries="0">
      <phase id="PHASE_12" status="APPROVED"/>
    </group>
  </groups>
  <artifacts>
    <artifact path="project_workspace/ocap_registry_import/requirements/requirements_spec.md" version="0.1.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_registry_import/requirements/user_stories.md" version="0.1.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_registry_import/requirements/requirements_spec.md" version="0.2.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_registry_import/requirements/user_stories.md" version="0.2.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_registry_import/requirements/requirements_spec.md" version="1.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_registry_import/requirements/user_stories.md" version="1.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_registry_import/architecture/architecture_design.md" version="0.1.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_registry_import/architecture/architecture_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_registry_import/architecture/module_design.md" version="0.1.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_registry_import/architecture/module_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_registry_import/architecture/tech_stack.md" version="0.1.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_registry_import/architecture/tech_stack.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_registry_import/development/implementation_plan.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_registry_import/development/code_review_report.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_registry_import/testing/test_plan.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_registry_import/testing/unit_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_registry_import/testing/integration_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_registry_import/testing/e2e_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_registry_import/deployment/cicd_pipeline.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="project_workspace/ocap_registry_import/deployment/deployment_plan.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="project_workspace/ocap_registry_import/deployment/deployment_report.md" version="1.0.0" status="APPROVED" group="GROUP_E2"/>
    <artifact path="project_workspace/ocap_registry_import/delivery_report.md" version="1.0.0" status="APPROVED" group="PM"/>
    <artifact path="project_workspace/_kb_distillation/distill_20261110T2332.md" version="1.0.0" status="APPROVED" group="GROUP_Z"/>
  </artifacts>
  <legacy_baseline/>
  <invocations>
    <invocation id="ocap_registry_import-GROUP_A-1" agent="requirement-analyst" start="2026-11-10T15:53:00+08:00" end="2026-11-10T15:57:02+08:00" result="SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_A-2" agent="requirement-analyst" start="2026-11-10T21:13:55+08:00" end="2026-11-10T21:19:15+08:00" result="SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_A-3" agent="requirement-analyst" start="2026-11-10T21:26:27+08:00" end="2026-11-10T21:30:18+08:00" result="SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_B-1" agent="system-architect" start="2026-11-10T21:40:11+08:00" end="2026-11-10T21:55:29+08:00" result="CLARIFICATION_NEEDED"/>
    <invocation id="ocap_registry_import-GROUP_B-2" agent="system-architect" start="2026-11-10T22:00:57+08:00" end="2026-11-10T22:04:35+08:00" result="SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_C-1" agent="software-developer" start="2026-11-10T22:26:18+08:00" end="2026-11-10T22:52:00+08:00" result="PARTIAL_SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_D-1" agent="test-engineer" start="2026-11-10T22:55:00+08:00" end="2026-11-10T23:09:46+08:00" result="PARTIAL_SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_E1-1" agent="devops-engineer" start="2026-11-10T23:14:10+08:00" end="2026-11-10T23:16:12+08:00" result="SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_E2-1" agent="devops-engineer" start="2026-11-10T23:22:00+08:00" end="2026-11-10T23:29:12+08:00" result="SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_Z-1" agent="kb-curator" start="2026-11-10T23:30:35+08:00" end="2026-11-10T23:33:31+08:00" result="SUCCESS"/>
  </invocations>
  <gate_reviews>
    <gate_review id="GR-A-001" invocation_id="ocap_registry_import-GROUP_A-3" decision="PASS_WITH_CONDITIONS" time="2026-11-10T21:30:18+08:00">
      <reviewed_files><file path="project_workspace/ocap_registry_import/requirements/requirements_spec.md" version="0.3.0"/><file path="project_workspace/ocap_registry_import/requirements/user_stories.md" version="0.3.0"/></reviewed_files>
      <criterion id="J-A-来源" result="SATISFIED">抽查 3 条：REQ-FUNC-087 引 views.py:100（10 个手机号上限，属实）；REQ-FUNC-093 引 views.py:156-169（预检跳过手机号校验、坏手机号同时计失败与导入，属实）；REQ-FUNC-098 引 residency/views.py:44-50（PHONE_NOT_IN_REGISTRY + appeal_available，属实）。用户原话引用与 clarifications 一致。</criterion>
      <criterion id="J-A-GWT" result="SATISFIED">grep "^- AC-" = 87；不含 Given/When/Then 的 0 条。</criterion>
      <criterion id="J-A-无技术实现" result="SATISFIED">grep CharField/Decimal/openpyxl/celery 无命中。</criterion>
      <criterion id="J-A-INFERRED" result="SATISFIED">0/21 = 0%（requirements_spec.md:32），≤ 0.20。</criterion>
      <criterion id="J-A-文件头" result="SATISFIED">两份 0.3.0 DRAFT，timestamp 2026-11-10T21:27:17+08:00 为真实时间；门控后改 APPROVED 1.0.0。</criterion>
      <finding id="GR-A-001-F01" severity="MINOR">Q-RI-23（60 秒计量口径与超时处理）非阻断开放：AC-100-07/08 按默认口径（测试环境、单管理员无并发）写入，超时处理未定义。</finding>
      <condition>GROUP_B 须为 20000 行 / 60 秒（REQ-NFUNC-015）给出超时处理与前端提示方案，并在 architecture_design 中说明；Q-RI-23 口径若用户另行调整，以用户为准。</condition>
    </gate_review>
    <gate_review id="GR-B-001" invocation_id="ocap_registry_import-GROUP_B-2" decision="PASS_WITH_CONDITIONS" time="2026-11-10T22:04:35+08:00">
      <reviewed_files><file path="project_workspace/ocap_registry_import/architecture/architecture_design.md" version="0.2.0"/><file path="project_workspace/ocap_registry_import/architecture/module_design.md" version="0.2.0"/><file path="project_workspace/ocap_registry_import/architecture/tech_stack.md" version="0.2.0"/></reviewed_files>
      <criterion id="J-B-覆盖" result="SATISFIED">module_design.md 需求覆盖表：REQ-FUNC-083~098 共 16 条、REQ-NFUNC-011~015 均有 MOD，无空行。</criterion>
      <criterion id="J-B-无环" result="SATISFIED">依赖关系节：accounts.views/identity.views → residency.auto_bind → registry.services → registry.models → core；registry→residency 仅既有延迟导入 registry/views.py:83（PM 核实存在）。</criterion>
      <criterion id="J-B-ADR" result="SATISFIED">ADR-034~044 共 11 个，均有 Status；抽查 ADR-034 有 A/B/C 三方案与取舍。</criterion>
      <criterion id="J-B-接口与小节" result="SATISFIED">IFC-152~164；含"数据迁移"（registry 0002~0004 手写，0003 不删数据，回滚 MANUAL_ROLLBACK_REQUIRED 并要求 mysqldump）与"受影响的运行单元"小节。</criterion>
      <criterion id="J-B-引用真实" result="SATISFIED">PM 核实：tests/support.py:123-129 make_unit；residency/models.py:4；accounts/views.py:85 RegisterView；identity/views.py:35 PhoneBindView；identity/services.py:54-57 合并分支；frontend/src/shared/http.js:25 timeout 15000；miniprogram/pages/units、phone 存在；ocap-deploy SKILL.md:272-276 ROLLBACK-004。</criterion>
      <criterion id="J-B-P8" result="SATISFIED">grep Docker/celery/redis/pscp：仅 tech_stack.md:18、architecture_design.md:134 声明不使用；无新增依赖。</criterion>
      <finding id="GR-B-001-F01" severity="MAJOR">R1/R2 High：目标机 gunicorn --timeout（默认 30s）与 ocap 8090 站点 nginx client_max_body_size（默认 1m）/proxy_read_timeout 未核实；现状下 5 MB 上传与 60 秒处理可能失败。</finding>
      <finding id="GR-B-001-F02" severity="MINOR">GROUP_B-2 未重读画像 P10 /root/myproject/Freeark/CLAUDE.md 与 user_stories.md（B-1 已读，本次仅答复修订，产出无误）。</finding>
      <finding id="GR-B-001-F03" severity="MINOR">ADR-037 采用 PM 落地口径（既有手机号保留为无名业主、统一上传按手机号补名），已告知用户，待用户确认。</finding>
      <condition>GROUP_C：按 module_design"数据迁移"节同步修改所列既有测试与夹具，保持零新增失败；迁移手写、文件头不得含 "Generated by Django"；axios 导入请求单独设超时（≥ 60 秒，按 ADR-040）。</condition>
      <condition>GROUP_E1：deployment_plan 给出 R1/R2 只读核实清单（由 PM 只读 ssh 执行或作为 E2 预检）与调整方案，仅限 ocap-backend 单元与 ocap 8090 站点；不触碰 Freeark 服务/端口/nginx 与 VPS；迁移前 mysqldump registry 三表。</condition>
    </gate_review>
    <gate_review id="GR-C-001" invocation_id="ocap_registry_import-GROUP_C-1" decision="PASS_WITH_CONDITIONS" time="2026-11-10T22:52:00+08:00">
      <reviewed_files><file path="project_workspace/ocap_registry_import/development/implementation_plan.md" version="1.0.0"/><file path="project_workspace/ocap_registry_import/development/code_review_report.md" version="1.0.0"/></reviewed_files>
      <criterion id="J-C-MOD 全部实现" result="SATISFIED">MOD-030~038 均有代码：models.py + 0002~0004；import_spec/importing/import_template.py；services.py options/units_by_phone；views.py IFC-152~159 七条路由；residency/auto_bind.py + certify_owner(origin)；accounts/views.py、identity/views.py 触发点；frontend AdminRegistry/RegistryImportDialog/Units/Register/Me/api.js；miniprogram pages/units、pages/phone、utils/api.js。</criterion>
      <criterion id="J-C-需求追溯" result="SATISFIED">implementation_plan 需求追溯表覆盖 US-092~104 全部 Must Have AC；仅 AC-094-07、AC-100-07、AC-100-08 标 PARTIAL（性能需 GROUP_D 实测），原因已写明；无 MISSING。</criterion>
      <criterion id="J-C-客户端构建与测试" result="SATISFIED">PM 复跑：frontend `npm run build` → built in 7.36s；frontend `npx vitest run` → 120 passed / 2 failed（theme_build.spec.js 行尾差异、theme.spec.js Windows 路径，均属既有环境失败，git status 无 themes 改动）；miniprogram 按 ci.yml 同参数安装后 `npx vitest run` → 69 passed (69)。</criterion>
      <criterion id="J-C-无未解决 CRITICAL" result="SATISFIED">报告统计 CRITICAL 2（CR-001 新业主手机号未落库、CR-002 手机号改属新建业主丢失），均已 FIXED；无 [UNRESOLVED-CRITICAL]。遗留 MAJOR 2 条（xlsx 未验证、性能未实测），均写明原因与处理时机，≤3。</criterion>
      <criterion id="J-C-PM 复跑" result="SATISFIED">PM 亲自执行：`python manage.py test --settings=config.test_settings` → Ran 247 tests / OK（无新增失败）；`makemigrations --check --dry-run` → No changes detected；`check` → 0 issues。</criterion>
      <criterion id="J-C-迁移与范围" result="SATISFIED">3 个手写迁移（0002 结构、0003 可逆回填、0004 收紧非空），文件头无 "Generated by Django"；git diff 22 个已跟踪文件 + 10 个新建，全部落在 backend/frontend/miniprogram 与 development/，无无关文件。</criterion>
      <finding id="GR-C-001-F01" severity="MAJOR">xlsx 解析与模板生成路径未验证（本机缺 openpyxl）。AC-093-01/03/04 与 AC-096/098 的 xlsx 分支目前只有代码与 503 降级证据。</finding>
      <finding id="GR-C-001-F02" severity="MAJOR">20000 行 / 60 秒三项性能 AC 未实测（AC-094-07、AC-100-07、AC-100-08）。</finding>
      <finding id="GR-C-001-F03" severity="MINOR">前端 2 个既有 vitest 失败未修复（主题模块行尾与 Windows 路径），不影响本次改动，但会长期使 `npm test` 退出码非 0。</finding>
      <condition>GROUP_D：测试环境已安装 requirements.txt（含 openpyxl）后必须真实执行 xlsx 用例；用 20000 行样本实测三项性能 AC；补 Web 与小程序新增交互（跳级选择、has_empty、导入预检/结果）的用例与前后端契约测试；小程序测试按 ci.yml 的 `npm install --legacy-peer-deps` 运行。</condition>
      <verification><![CDATA[backend: Ran 247 tests in 3.251s / OK
makemigrations --check: No changes detected
frontend build: ✓ built in 7.36s
frontend vitest: Tests 2 failed | 120 passed (122)（既有主题环境失败）
miniprogram vitest: Test Files 10 passed (10) / Tests 69 passed (69)]]></verification>
    </gate_review>
    <gate_review id="GR-D-001" invocation_id="ocap_registry_import-GROUP_D-1" decision="PASS_WITH_CONDITIONS" time="2026-11-10T23:09:46+08:00">
      <reviewed_files><file path="project_workspace/ocap_registry_import/testing/test_plan.md" version="1.0.0"/><file path="project_workspace/ocap_registry_import/testing/unit_test_report.md" version="1.0.0"/><file path="project_workspace/ocap_registry_import/testing/integration_test_report.md" version="1.0.0"/><file path="project_workspace/ocap_registry_import/testing/e2e_test_report.md" version="1.0.0"/></reviewed_files>
      <criterion id="J-D-AC 追溯" result="SATISFIED">test_plan AC 映射表 87 行（AC-092-01~AC-104-04），每行有用例 ID 或 [NOT_TESTABLE]/[BLOCKED] 原因；抽查 AC-094-09 → TC-INT-111、AC-099-08 → TC-INT-143、AC-102-10 → TC-INT-166，测试文件内 docstring 与用例一一对应。</criterion>
      <criterion id="J-D-真实执行" result="SATISFIED">PM 复跑：backend 全量 `Ran 327 tests in 3.842s / OK`；分层 unit 62、integration 237、e2e 22、smoke 6；frontend `Tests 2 failed | 124 passed (126)`；miniprogram `Tests 69 passed (69)`。报告计数行与最后一次执行输出一致；无"未运行标 PASS"。</criterion>
      <criterion id="J-D-分层门控" result="SATISFIED">INCREMENTAL baseline：单元 66/66、集成 237/237、E2E 22/22；每层新写用例全部通过后才进入下一层，全量回归相对基线 247 新增失败 0。</criterion>
      <criterion id="J-D-critical path" result="SATISFIED">e2e_test_report 首行为"critical path 口径：替代（完整 API 旅程）"；Must Have 故事 11/11 均有已执行的 E2E 旅程（US-092~099、US-102~104），覆盖率 11/11=100%，通过率 100%。</criterion>
      <criterion id="J-D-契约测试" result="SATISFIED">TC-INT-164 解析前端与小程序 api.js 的新调用（路径+方法）并全部解析到 Django 路由；TC-INT-165 校验后端响应键与前端读取字段一致；前端另有 4 个 vitest 用例（TC-UNIT-111~114）真实执行通过。</criterion>
      <criterion id="J-D-metrics" result="SATISFIED">三份报告均给出 total = pass + fail + skip + blocked + not_testable 公式（66、237、22），算术成立；通过率分母含 blocked，未把不可测项计入分母。</criterion>
      <criterion id="J-D-冻结" result="SATISFIED">冻结核对：测试文件最后修改时间（rules 22:56:26、spec.js 23:00:50、contract 23:01:52、enhancement 23:06:12、journeys 23:07:19）均早于报告（23:08:37~23:09:32）；全量回归 327 在最后一次测试修改之后执行。</criterion>
      <criterion id="J-D-写权限与范围" result="SATISFIED">新增/修改仅 backend/tests/{unit,integration,e2e} 与 frontend/tests/registry_import.spec.js、testing/ 四份文档；未改产品代码（git status 中无 apps/、src/、pages/ 变更）。</criterion>
      <criterion id="J-D-故事覆盖" result="SATISFIED">test_plan"故事覆盖核对"11 行无空行，每行列出已执行用例；无 [NOT_TESTABLE] 的 Must Have 故事。</criterion>
      <finding id="GR-D-001-F01" severity="MAJOR">xlsx 解析/模板生成仍未执行（AC-093-01 xlsx 部分、AC-093-03、AC-093-04 xlsx 部分）：本机 `openpyxl` 仍缺失，画像 P4 要求"不自行安装依赖"，故标 BLOCKED 并进人工验证清单 M-01~M-03，GROUP_C condition 未闭环。</finding>
      <finding id="GR-D-001-F02" severity="MAJOR">AC-094-07、AC-100-07、AC-100-08 三项 20000 行 / 60 秒性能未实测：无 20000 行样本，标 NOT_TESTABLE 并进人工验证清单 M-04~M-06。</finding>
      <finding id="GR-D-001-F03" severity="MINOR">AC-095-05"同号再次比对不通过"以 TC-INT-117 的等价证据覆盖（手机号唯一，无法构造同号账号），已在报告注明，A 级证据弱于直接复现。</finding>
      <finding id="GR-D-001-F04" severity="MINOR">前端 2 个既有 vitest 失败（theme 行尾、Windows 路径）仍在，未修复且不在本次范围；`npm test` 退出码仍非 0。</finding>
      <condition>GROUP_E1：在部署计划/CI 中显式包含 `pip install -r requirements.txt`（含 openpyxl）并在测试环境补跑 xlsx 用例（M-01~M-03）；发布前用 20000 行样本实测 M-04~M-06 并回填 e2e_test_report 的人工验证结果；不因此放宽 AC-093-01/03/04 与 AC-094-07/AC-100-07/08。</condition>
      <verification><![CDATA[backend unit: Ran 62 tests in 0.302s / OK
backend integration: Ran 237 tests in 2.860s / OK
backend e2e: Ran 22 tests in 0.633s / OK
backend full: Ran 327 tests in 3.842s / OK
frontend: Test Files 2 failed | 11 passed (13); Tests 2 failed | 124 passed (126)
miniprogram: Test Files 10 passed (10); Tests 69 passed (69)
new: backend unit 10 / integration 66 / e2e 4；frontend 4]]></verification>
    </gate_review>
    <gate_review id="GR-E1-001" invocation_id="ocap_registry_import-GROUP_E1-1" decision="PASS_WITH_CONDITIONS" time="2026-11-10T23:16:12+08:00">
      <reviewed_files><file path="project_workspace/ocap_registry_import/deployment/cicd_pipeline.md" version="1.0.0"/><file path="project_workspace/ocap_registry_import/deployment/deployment_plan.md" version="1.0.0"/></reviewed_files>
      <criterion id="J-E1-DEPLOY/ROLLBACK 映射" result="SATISFIED">grep 核实 DEPLOY-001~008 共 8 个、ROLLBACK-001~008 共 8 个，每个 DEPLOY 行均有对应"回滚：ROLLBACK-NNN"；顺序为快照→三表备份→条件参数→后端→依赖→迁移→前端→重启，依赖顺序正确。</criterion>
      <criterion id="J-E1-预检完整" result="SATISFIED">PRE-001~012 覆盖部署内容可追溯、SSH/sudo、磁盘/内存、端口归属、.env 存在、依赖 dry-run、迁移计划、数据基线、R2 nginx 容量、R1 gunicorn 超时、Freeark 基线、快照目录可写；GR-B-001-F01 的 R1/R2 已落为 PRE-009/PRE-010 + 条件步骤 DEPLOY-003。</criterion>
      <criterion id="J-E1-环境与策略" result="SATISFIED">仅使用画像 P7 的测试环境（192.168.31.51 内网 / ai-freeark.xin 外网，无生产）；策略 recreate 的单实例理由成立；未设计 staging 晋升或 canary。</criterion>
      <criterion id="J-E1-无 P8 禁用" result="SATISFIED">部署文档 grep：无 Docker/容器/pscp/makemigrations 操作；回滚明确禁止 git reset/clean/stash（仅部署计划第 29 行以禁用语句出现）。</criterion>
      <criterion id="J-E1-回滚不破坏本地状态" result="SATISFIED">回滚依赖目标机整目录 tar 快照（含 .env 与 venv），ROLLBACK-004 恢复后显式检查 ENV_KEPT；未使用覆盖式 git 同步；nginx/unit 改动前均备份。</criterion>
      <criterion id="J-E1-远端变量引用" result="SATISFIED">命令统一使用 &lt;TS&gt; 占位符，E2 时以 DEPLOY-001 输出的具体时间戳替换；数据库命令在远端 source .env 后使用远端变量，凭据不落盘不打印；开发机 SHA256 改用 Get-FileHash（Windows）。</criterion>
      <criterion id="J-E1-CI 影响" result="SATISFIED">读取 .github/workflows/ci.yml 三 job；结论"无需修改"有依据（openpyxl 已在 requirements.txt:5、无新服务/环境变量）；未凭空重建流水线。</criterion>
      <finding id="GR-E1-001-F01" severity="MAJOR">PRE-001 当前不满足：`git status --short` 显示 22 个已修改 + 18 个新增文件均未提交，HEAD 03b4b28 不含本次实现，且本机到 GitHub 的代理连接失败（`127.0.0.1:443` 拒绝）。E2 前需用户确认提交/推送，或显式批准"工作树快照"降级（记录 HEAD+status+tar SHA256）。</finding>
      <finding id="GR-E1-001-F02" severity="MINOR">xlsx 与 20000 行性能条件依赖 E2 的只读核验 V-08/V-09（目标机 venv 已装 openpyxl 后执行），结果需回填 e2e_test_report M-01~M-06。</finding>
      <finding id="GR-E1-001-F03" severity="MINOR">DEPLOY-003 若 R1（gunicorn --timeout）不满足需交互式 `systemctl edit --full`；E2 自动化执行到此处将暂停等待用户完成编辑。</finding>
      <condition>E2：必须由用户在下一轮明确确认（引用本轮原话并写明环境=测试环境、计划版本=1.0.0）；先解决 PRE-001（提交/推送或批准工作树降级）；部署后完成 V-08/V-09 并回填测试报告；不触碰 Freeark 服务/端口/nginx 与 VPS。</condition>
      <verification><![CDATA[产物存在：deployment/cicd_pipeline.md、deployment/deployment_plan.md（均 1.0.0 DRAFT→APPROVED）
DEPLOY 8 / ROLLBACK 8（grep 标题计数）
预检 12 项（PRE-001~012）
不可逆步骤 3 行（DEPLOY-006、DEPLOY-002/ROLLBACK-002、前端代码覆盖）
环境：仅画像 P7 测试环境；无生产
CI：.github/workflows/ci.yml 三 job 已读，结论无需修改
E1 未连接目标环境（按技能规则）]]></verification>
    </gate_review>
    <gate_review id="GR-E2-001" invocation_id="ocap_registry_import-GROUP_E2-1" decision="PASS_WITH_CONDITIONS" time="2026-11-10T23:29:12+08:00">
      <reviewed_files><file path="project_workspace/ocap_registry_import/deployment/deployment_report.md" version="1.0.0"/></reviewed_files>
      <criterion id="J-E2-授权核对" result="SATISFIED">报告"授权核对"节：用户原话"做部署计划，部署到测试环境"+"A"；PRODUCTION_DEPLOY_CONFIRM=true；环境名与计划/画像 P7 一致；计划版本 1.0.0=APPROVED。</criterion>
      <criterion id="J-E2-真实执行" result="SATISFIED">8 个 DEPLOY 均有命令摘要、开始时间与输出摘要（锚点 20261110232450、DUMP_EXIT=0、SHA256 两端一致、openpyxl 3.1.5、迁移 0002~0004 OK、built 7.33s、gunicorn active）；未执行步骤未标 SUCCESS。</criterion>
      <criterion id="J-E2-PM 复核" result="SATISFIED">PM 只读复跑：`systemctl is-active ocap-backend`=active、`nginx`=active；`showmigrations registry` 0001~0004 全 [X]；`GET /ocap/`=200；`GET /ocap/api/v1/admin/registry/import/spec`=401（路由存在）。</criterion>
      <criterion id="J-E2-回滚与状态" result="SATISFIED">未触发回滚；快照/三表备份/nginx/unit 备份齐全；目标机仅两处持久参数变更（--timeout 90、proxy_read_timeout 90s）且有备份。</criterion>
      <criterion id="J-E2-安全" result="SATISFIED">报告与证据无凭据；mysqldump 使用远端 .env 变量，未打印密码；Freeark 服务与配置未重启/未修改（failed units 0、首页 200）。</criterion>
      <finding id="GR-E2-001-F01" severity="MINOR">V-09 为引擎级只读抽样（20000 行 1.30s / 1.01s），未做真实 HTTP 5MB 上传的端到端计时；需用户在页面用 20000 行文件实测一次（M-04~M-06 的 HTTP 口径）。</finding>
      <finding id="GR-E2-001-F02" severity="MINOR">迁移 0003 在空库执行（基线 0 单元/0 手机号），未验证有数据时的回填耗时与结果。</finding>
      <condition>交付后：用户在测试环境页面完成一次真实 20000 行导入（预检 + 正式）确认 60 秒内完成；小程序发布（RU-4）另行处理；deployment_report 的 V-09 引擎级结论不得外推为 HTTP 端到端已达标。</condition>
      <verification><![CDATA[ocap-backend=active；nginx=active
showmigrations registry: 0001~0004 全部 [X]
https://ai-freeark.xin/ocap/ = 200
https://ai-freeark.xin/ocap/api/v1/admin/registry/import/spec = 401
V-08 xlsx: LEN 6419 / ZIP True / ['清册导入','填写说明']
V-09: VALID 1.30s；WITH_10PCT_ERRORS 1.01s（errors=2000）]]></verification>
    </gate_review>
  </gate_reviews>
  <clarifications>
    <clarification time="2026-11-10T21:13:55+08:00" responder="用户"><![CDATA[用户原话："Q-RI-02 手机号选填，如果用户用这个手机号注册并且认证成功，可以自动绑定这个专有部分。Q-RI-04 车位面积必须填。Q-RI-06 同一专有部分导入，只要产权业主名字不同，就认为是同意部分的多个产权人。Q-RI-10 文件上线5 MB 20000行。 Q-RI-11： 要显示面积。 Q-RI-12：A， 其他按照推荐"
映射：Q-RI-01=A；Q-RI-02=手机号选填+注册且认证成功的手机号自动绑定专有部分（新）；Q-RI-03=A；Q-RI-04=车位面积必填（其他类型按推荐选填）；Q-RI-05=B；Q-RI-06=按业主姓名区分同一专有部分的多位产权人；Q-RI-07=A；Q-RI-08=A；Q-RI-09=A；Q-RI-10=5 MB / 20000 行；Q-RI-11=显示类型与面积（C）；Q-RI-12=A。]]></clarification>
    <clarification time="2026-11-10T21:26:27+08:00" responder="用户"><![CDATA[用户原话："Q-RI-18=B，Q-RI-22 上限 60 秒，其他按推荐"。映射：Q-RI-13=A、14=A、15=A、16=A、17=A、18=B、19=A、20=A、21=A、22=A（同步等待，上限 60 秒）。]]></clarification>
    <clarification time="2026-11-10T22:00:57+08:00" responder="用户"><![CDATA[GROUP_B-1 问题。用户原话："Q1：初次使用，管理员同一上传业主清册， Q2：A， Q3：按照推荐， Q4：A Q6：B"
映射：Q1=系统为初次使用，清册由管理员用新模板统一上传全量数据，不需要为既有数据设计补名流程。PM 落地口径（待用户确认）：迁移不删除任何既有数据；既有手机号按技术上最简方式保留为无名业主，管理员统一上传时按手机号匹配补上姓名（即 A 的机制，但不作为业务流程设计）。Q2=A；Q3=A；Q4=A；Q6=B（60 秒验收限定内网入口）。]]></clarification>
  </clarifications>
  <checkpoints/>
  <escalations/>
  <audit_log>
    <event time="2026-11-10T15:52:12+08:00" type="RUN" actor="pm-orchestrator">主会话模式（用户直接陈述需求）。新增量项目 ocap_registry_import；用户要求先出需求与用户故事，确认后再开发。另：ocap_admin_entry 相关 Q1–Q3 仍待用户答复，本项目不包含。</event>
    <event time="2026-11-10T15:53:00+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst ocap_registry_import-GROUP_A-1（PHASE_01–02）。</event>
    <event time="2026-11-10T15:57:02+08:00" type="GATE" actor="pm-orchestrator">GROUP_A-1 SUCCESS（REQ-FUNC-083~095、REQ-NFUNC-011~014、C-21~24、US-092~101、54 AC）。PM 预审：文件头 DRAFT；54/54 AC 为 G/W/T；INFERRED 3/17=17.6%；抽查 views.py:100、:156-157、:163-169 出处属实；无技术实现内容。阻断问题 Q-RI-01/03/05 待用户答复，正式门控待答复后作出。</event>
    <event time="2026-11-10T21:13:55+08:00" type="INVOCATION" actor="pm-orchestrator">用户答复 Q-RI-01~12，调用 requirement-analyst ocap_registry_import-GROUP_A-2 按答复修订（REWORK 自身 DRAFT 产物）。</event>
    <event time="2026-11-10T21:19:15+08:00" type="GATE" actor="pm-orchestrator">GROUP_A-2 SUCCESS（0.2.0：REQ-FUNC 16 / NFUNC 4 / US-092~104 / 80 AC）。PM 预审：80/80 AC 为 G/W/T；INFERRED 1/20=5%；抽查 residency/views.py:44-50、residency/services.py:14-20 出处属实；无技术实现。新问题 Q-RI-13~22（Q-RI-18 阻断）待用户答复。</event>
    <event time="2026-11-10T21:26:27+08:00" type="INVOCATION" actor="pm-orchestrator">用户答复 Q-RI-13~22，调用 requirement-analyst ocap_registry_import-GROUP_A-3 写入答复、关闭开放问题。</event>
    <event time="2026-11-10T21:30:18+08:00" type="GATE" actor="pm-orchestrator">GR-A-001 PASS_WITH_CONDITIONS，GROUP_A APPROVED（requirements 两份 1.0.0；0.1.0/0.2.0 SUPERSEDED）。GROUP_B 待用户放行。</event>
    <event time="2026-11-10T21:40:11+08:00" type="INVOCATION" actor="pm-orchestrator">用户本轮原话"开始架构"：调用 system-architect ocap_registry_import-GROUP_B-1（PHASE_03–04），带入 GR-A-001 condition。</event>
    <event time="2026-11-10T21:55:29+08:00" type="RUN" actor="pm-orchestrator">GROUP_B-1 CLARIFICATION_NEEDED：architecture 三份 0.1.0 DRAFT 已写（ADR-034~044、MOD-030~038、IFC-152~164），CRITICAL Q1（既有手机号迁移为无名业主）、Q2（同文件同专有部分面积冲突）及 NORMAL Q3、Q4、Q6 转问用户；PM 核实 http.js:25 axios 超时 15000ms、小程序 units/phone 页面存在。</event>
    <event time="2026-11-10T22:00:57+08:00" type="INVOCATION" actor="pm-orchestrator">带用户答复调用 system-architect ocap_registry_import-GROUP_B-2 修订 architecture 0.1.0。</event>
    <event time="2026-11-10T22:04:35+08:00" type="GATE" actor="pm-orchestrator">GR-B-001 PASS_WITH_CONDITIONS，GROUP_B APPROVED（architecture 三份 1.0.0；0.1.0 SUPERSEDED，0.2.0 为门控评审版本）。GROUP_C 待用户放行。</event>
    <event time="2026-11-10T22:07:39+08:00" type="RUN" actor="pm-orchestrator">用户本轮原话"git commit push， 我再另外一台机去开发"：提交 cf7f11e（需求、架构、phase_status、kb_inbox），凭据扫描无命中；推送 dfd188e..cf7f11e 成功。ci.yml 仅 push/PR/workflow_dispatch 触发 CI，无部署步骤。GROUP_C 未开始，用户将在另一台机器续跑。</event>
    <event time="2026-11-10T22:26:18+08:00" type="RUN" actor="pm-orchestrator">主会话模式（用户原话"我今天在cluade 有新增加的需求，也做了架构，但是没有开发。Use Skill: sdlc-orchestrator 你继续开发测试"）。续跑 ocap_registry_import：A/B 已 APPROVED，从 GROUP_C 继续。已读 shared_protocol §A–§T、project_profile 1.2.0、generic/pm-orchestrator.md、PM MEMORY.md（空模板）；preflight --check-cwd=CWD_OK、--check-all=PREFLIGHT_OK skills=9 profile=APPROVED。</event>
    <event time="2026-11-10T22:52:00+08:00" type="INVOCATION" actor="pm-orchestrator">GROUP_C-1 结束（software-developer，PARTIAL_SUCCESS）：MOD-030~038 全部实现，32 个代码/测试文件（22 改 + 10 新建）；implementation_plan.md 与 code_review_report.md 1.0.0；CRITICAL 2 已修复，遗留 MAJOR 2（xlsx 未验证、性能未实测）。preflight --check-all=PREFLIGHT_OK；kb_inbox --check-response=RESPONSE_OK（PARTIAL_SUCCESS，无 kb_proposals）。</event>
    <event time="2026-11-10T22:52:00+08:00" type="GATE" actor="pm-orchestrator">GR-C-001 PASS_WITH_CONDITIONS，GROUP_C APPROVED。PM 复跑：后端 Ran 247 tests / OK、makemigrations 无变更、check 0 issues；frontend build 成功、vitest 120 passed/2 既有环境失败；miniprogram 安装依赖后 69 passed。条件：GROUP_D 必须真实执行 xlsx 用例、20000 行性能 AC、补前后端契约与新增交互用例。</event>
    <event time="2026-11-10T22:55:00+08:00" type="INVOCATION" actor="pm-orchestrator">调用 test-engineer ocap_registry_import-GROUP_D-1（PHASE_07–09），带入 GR-C-001 condition。</event>
    <event time="2026-11-10T23:09:46+08:00" type="RUN" actor="pm-orchestrator">PM 校正历史时间：GROUP_C 的 invocation/GR-C-001/审计时间原记为 23:52（晚于实际发生顺序，且为未来时间），按真实工作顺序改为 22:52；无其他字段变更。</event>
    <event time="2026-11-10T23:09:46+08:00" type="INVOCATION" actor="pm-orchestrator">GROUP_D-1 结束（test-engineer，PARTIAL_SUCCESS）：新增后端 80 个用例（unit 10 / integration 66 / e2e 4）+ 前端 4 个；testing/ 四份 1.0.0。实测 unit 66/66、integration 237/237、e2e 22/22，全量 327 OK（基线 247，新增失败 0）；frontend 124 passed/2 既有失败；miniprogram 69 passed。xlsx 与 20000 行性能未执行（openpyxl 缺失、无样本），转人工验证清单 M-01~M-06。</event>
    <event time="2026-11-10T23:09:46+08:00" type="GATE" actor="pm-orchestrator">GR-D-001 PASS_WITH_CONDITIONS，GROUP_D APPROVED（PHASE_07/08/09 APPROVED）。PM 复跑全量 Ran 327 / OK；critical path 口径=替代（API 旅程），Must Have 故事 11/11 覆盖、通过率 100%；缺陷 0。条件转 GROUP_E1：部署/CI 安装 requirements.txt 后补跑 xlsx 用例、发布前实测三项性能 AC。</event>
    <event time="2026-11-10T23:14:10+08:00" type="INVOCATION" actor="pm-orchestrator">用户当轮指令"做部署计划，部署到测试环境"；调用 devops-engineer ocap_registry_import-GROUP_E1-1（PHASE_10/11a），带入 GR-B-001（R1/R2 只读核实、迁移前 mysqldump registry 三表）与 GR-D-001（安装 requirements 后补跑 xlsx、性能实测）条件。</event>
    <event time="2026-11-10T23:16:12+08:00" type="GATE" actor="pm-orchestrator">GR-E1-001 PASS_WITH_CONDITIONS，GROUP_E1 APPROVED（PHASE_10/11a）。cicd_pipeline 与 deployment_plan 均 1.0.0；DEPLOY 8/ROLLBACK 8、预检 12 项、不可逆 3 处、策略 recreate；CI 无需修改。MAJOR：PRE-001 未满足（实现未提交且 GitHub 不可达），E2 前需用户决策。E2 保持 NOT_AUTHORIZED，等待用户下一轮确认。</event>
    <event time="2026-11-10T23:20:57+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">授权来源（用户当轮原文）：上一轮"做部署计划，部署到测试环境" + 本轮"A"（选择 A：先提交并推送，再部署）。环境=测试环境（192.168.31.51，外网 ai-freeark.xin/ocap/），计划=deployment_plan.md v1.0.0（APPROVED）。用户已授权本会话执行 git add/commit/push。</event>
    <event time="2026-11-10T23:20:57+08:00" type="BLOCKER" actor="pm-orchestrator">PRE-001 阻塞：已提交 9c66dce（47 files, +12922/-275）且工作树干净；`git push origin main` 失败——git 配置 socks5h://127.0.0.1:10808 无监听，直连 github.com:443 超时（120s），SSH 22 可达但 id_ed25519/deploy_key/ib_deploy_key 均 Permission denied。E2 未执行任何目标机命令，目标环境无变更。等待用户启动代理后重试 push，或批准 B 降级。</event>
    <event time="2026-11-10T23:29:12+08:00" type="INVOCATION" actor="pm-orchestrator">GROUP_E2-1 结束（devops-engineer，SUCCESS）：8/8 DEPLOY 成功，锚点 20261110232450，最终状态 DEPLOYED_SUCCESSFULLY；V-01~V-11 通过（V-09 为引擎级只读）。</event>
    <event time="2026-11-10T23:29:12+08:00" type="GATE" actor="pm-orchestrator">GR-E2-001 PASS_WITH_CONDITIONS，GROUP_E2 APPROVED（PHASE_11b）。PM 复核 active/200/401/迁移全应用；无回滚；遗留：真实 HTTP 20000 行端到端计时待用户页面实测、0003 空库回填未验证数据量场景。</event>
    <event time="2026-11-10T23:33:31+08:00" type="INVOCATION" actor="pm-orchestrator">GROUP_Z-1 结束（kb-curator，SUCCESS）：未处理 17 条 → 16 条；晋升 14、保留 2、淘汰 0、通用候选 0；记忆写入 RA/SA/SD/TE/DE/PM 六个 MEMORY.md；无 pending_patch。</event>
    <event time="2026-11-10T23:33:31+08:00" type="DELIVERY" actor="pm-orchestrator">PHASE_01~12 全部 APPROVED；delivery_report.md 1.0.0；最终状态 DELIVERED_WITH_ISSUES（遗留：真实 HTTP 20000 行端到端计时、xlsx 上传解析、2 个既有前端失败）。测试环境已部署（锚点 20261110232450）。</event>
  </audit_log>
</phase_status>
