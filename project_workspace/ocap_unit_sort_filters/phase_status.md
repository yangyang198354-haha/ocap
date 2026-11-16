<phase_status project="ocap_unit_sort_filters" mode="INCREMENTAL" created="2026-11-16T11:00:21+08:00" updated="2026-11-16T14:53:28+08:00">
  <request time="2026-11-16T11:00:21+08:00"><![CDATA[现在有两个需求变更：1.用户登录后再我的房屋，选择房屋时， 楼栋，单元，楼层，户号的排序方式必须统一，之前已经改了楼层的。按照数字顺序排列，但是楼栋，单元还不是。 这个需要统一排序方法。负一、负二层的车位是挂在1栋下面的。选择车位体验很差。应该在选楼栋的地方选择地下车位。选饿着再选负一、负二层。工作区有一个导入文件。把这个导入文件改对。同时数据库里面的数据也修改正确。3。管理员进入后台后，业主清册页面应当设置多个过滤器，比如楼栋，单元放好，类型，还有产权业主姓名，电话。 另外专有部分表示搜索页保留。现在的按类型收缩下拉框里面写的是"select"， 新增、调整的过滤器应当用中文。 先整理我的需求，拆分成用户故事，我确认后开始开发。]]></request>
  <request_context><![CDATA[PM 只读核查（2026-11-16T11:00:21+08:00）：
- 逐级选项 RegistryService.options（backend/apps/registry/services.py:38-75）：building 用 sorted() 文本排序（:52）；unit_no 文本排序、floor 用 _floor_sort_key 数值排序（负层在前，:9-19、:58-59）；户号 qs.order_by("room") 文本排序（:68）。前端级联组件 frontend/src/portal/parts/UnitCascader.vue。
- 后台清册 frontend/src/admin/AdminRegistry.vue:7-12：仅"专有部分标识搜索"输入框 + 类型下拉（选项 全部类型/未登记类型/各类型）；后端 AdminUnitListView（backend/apps/registry/views.py:75-90）仅支持 q（specific_part 模糊）与 unit_type。
- 仓库及本机未找到清册导入用的数据文件（xlsx/csv）；"工作区的导入文件"位置待用户提供。真实数据在测试机 MySQL 库 ocap。
- 相关遗留：ocap_product_review 上报 pm_escalation_GROUP_D_20261115T2134.md（DEF-A：/me 与 /me/housing 房屋行排序口径不同），待用户决定。]]></request_context>
  <profile version="1.5.0"/>
  <workspace_note>独立增量项目，文档在 project_workspace/ocap_unit_sort_filters/（nested）；代码按画像 P3 in-repo。用户要求本轮只做 GROUP_A（需求+用户故事），确认后再开发。</workspace_note>
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
    <group id="GROUP_E2" agent="devops-engineer" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" environment="测试" stage="A~E 完成"/>
  </groups>
  <artifacts>
    <artifact path="project_workspace/ocap_unit_sort_filters/requirements/requirements_spec.md" version="0.1.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/requirements/user_stories.md" version="0.1.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/requirements/requirements_spec.md" version="0.2.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/requirements/requirements_spec.md" version="1.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/requirements/user_stories.md" version="0.2.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/requirements/user_stories.md" version="1.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/architecture/architecture_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/architecture/module_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/architecture/tech_stack.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/development/implementation_plan.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/development/code_review_report.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/testing/test_plan.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/testing/unit_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/testing/integration_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/testing/e2e_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/deployment/cicd_pipeline.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/deployment/deployment_plan.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/deployment/deployment_report.md" version="1.0.0" status="SUPERSEDED" group="GROUP_E2"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/deployment/deployment_report.md" version="2.0.0" status="SUPERSEDED" group="GROUP_E2"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/deployment/deployment_report.md" version="3.0.0" status="SUPERSEDED" group="GROUP_E2"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/deployment/deployment_report.md" version="4.0.0" status="APPROVED" group="GROUP_E2"/>
    <artifact path="project_workspace/ocap_unit_sort_filters/delivery_report.md" version="1.0.0" status="APPROVED" group="PM"/>
  </artifacts>
  <legacy_baseline/>
  <invocations>
    <invocation id="ocap_unit_sort_filters-GROUP_A-001" agent="requirement-analyst" start="2026-11-16T11:00:21+08:00" end="2026-11-16T11:04:17+08:00" result="SUCCESS"/>
  <invocation id="ocap_unit_sort_filters-GROUP_A-002" agent="requirement-analyst" result="SUCCESS" end="2026-11-16T11:16:12+08:00" start="2026-11-16T11:11:59+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_B-001" agent="system-architect" result="SUCCESS" end="2026-11-16T11:59:25+08:00" start="2026-11-16T11:43:21+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_C-001" agent="software-developer" result="SUCCESS" end="2026-11-16T12:18:10+08:00" start="2026-11-16T11:59:25+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_D-001" agent="test-engineer" result="SUCCESS" end="2026-11-16T12:43:37+08:00" start="2026-11-16T12:18:10+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_E1-001" agent="devops-engineer" result="SUCCESS" end="2026-11-16T12:54:34+08:00" start="2026-11-16T12:47:56+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_E2-001" agent="devops-engineer" result="SUCCESS" end="2026-11-16T13:24:07+08:00" start="2026-11-16T13:04:00+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_E2-002" agent="devops-engineer" result="SUCCESS" end="2026-11-16T13:44:08+08:00" start="2026-11-16T13:27:32+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_E2-003" agent="devops-engineer" result="SUCCESS" end="2026-11-16T13:53:17+08:00" start="2026-11-16T13:45:41+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_E2-004" agent="devops-engineer" result="SUCCESS" end="2026-11-16T14:32:33+08:00" start="2026-11-16T13:55:08+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_Z-001" agent="kb-curator" result="SUCCESS" end="2026-11-16T14:39:02+08:00" start="2026-11-16T14:33:05+08:00"/>
  <invocation id="ocap_unit_sort_filters-GROUP_Z-002" agent="kb-curator" result="SUCCESS" end="2026-11-16T14:53:28+08:00" start="2026-11-16T14:52:30+08:00"/>
  </invocations>
  <gate_reviews>
    <gate_review id="GR-A-001" invocation_id="ocap_unit_sort_filters-GROUP_A-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T11:04:17+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/requirements/requirements_spec.md" version="0.1.0"/><file path="project_workspace/ocap_unit_sort_filters/requirements/user_stories.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-A 来源" result="SATISFIED">抽查 REQ-FUNC-173（用户原文"楼栋，单元，楼层，户号的排序方式必须统一"存在；services.py:51-52 building sorted() 文本排序，:68 order_by("room")）、REQ-FUNC-175（UnitCascader.vue 与 miniprogram/components/UnitPicker.vue 均存在）、REQ-FUNC-181 引用基线 REQ-FUNC-095（ocap_registry_import requirements_spec.md:105 存在）。</criterion>
      <criterion id="J-A G/W/T" result="SATISFIED">user_stories.md 36 条 AC 均为 Given/When/Then（grep Given=36）。</criterion>
      <criterion id="J-A 无技术实现" result="SATISFIED">代码位置仅出现在"现有系统基线"与来源列。</criterion>
      <criterion id="J-A INFERRED" result="SATISFIED">2/13=15.4% ≤ 0.20；已汇总在"待确认推断项"A 表；原文理解 I-01~I-07 在 B 表。</criterion>
      <finding id="GR-A-001-F01" severity="MINOR">漏读必读：画像 P10 两份 Freeark 需求文档仅 ls、ocap_registry_import user_stories.md 未读、requirements_spec 仅 grep（agent notes 自述）；产出未见因此出错。再犯点名（M-PM-001）。</finding>
      <finding id="GR-A-001-F02" severity="MINOR">行号偏差：REQ-FUNC-173 来源 services.py:52 实为 :51-52（:52 为 return）。</finding>
      <condition>CRITICAL 开放问题 Q-SF-01（导入文件位置）、Q-SF-02（地下车位楼栋取值）及 Q-SF-03~12、I-01~07 须经用户答复，RA 按答复定稿（0.2.0）后再批准；GROUP_B 不得在此之前启动。</condition>
    </gate_review>
    <gate_review id="GR-A-002" invocation_id="ocap_unit_sort_filters-GROUP_A-002" decision="PASS_WITH_CONDITIONS" time="2026-11-16T11:16:12+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/requirements/requirements_spec.md" version="0.2.0"/><file path="project_workspace/ocap_unit_sort_filters/requirements/user_stories.md" version="0.2.0"/></reviewed_files>
      <criterion id="J-A 来源" result="SATISFIED">抽查：REQ-FUNC-184 引用 AC-157-01/02 在 ocap_product_review/requirements/user_stories.md:129-130 存在；identity/services.py:48 按 specific_part 排序、residency/housing.py:41 按 certified_at 排序属实；REQ-FUNC-178 来源为用户答复 Q-SF-01=B（clarifications 有原话）。</criterion>
      <criterion id="J-A G/W/T" result="SATISFIED">48 条 AC，grep Given=48。</criterion>
      <criterion id="J-A INFERRED" result="SATISFIED">0/14=0%。</criterion>
      <criterion id="J-A 无技术实现" result="SATISFIED">代码位置仅在基线与来源列。</criterion>
      <criterion id="GR-A-001 条件" result="SATISFIED">开放问题已按用户答复转为"已决问题"；行号 F02 已修正；剩余 Q-SF-02b/13/14/15 均非阻断。</criterion>
      <finding id="GR-A-002-F01" severity="MINOR">P10 Freeark 两份参考文档仅读前部（notes 自述），产出未引用、无误。</finding>
      <condition>用户确认故事（含 Q-SF-13/14/15 复核）后 PM 批准为 1.0.0；AUTH-01（只读导出）、AUTH-02（库内原地更新）须用户在执行当轮单独授权，GROUP_B 设计需把两者设计为独立可授权步骤。</condition>
    </gate_review>
    <gate_review id="GR-B-001" invocation_id="ocap_unit_sort_filters-GROUP_B-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T11:59:25+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/architecture/architecture_design.md" version="0.1.0"/><file path="project_workspace/ocap_unit_sort_filters/architecture/module_design.md" version="0.1.0"/><file path="project_workspace/ocap_unit_sort_filters/architecture/tech_stack.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-B 覆盖" result="SATISFIED">module_design.md:334-350 覆盖 REQ-FUNC-173~184、REQ-NFUNC-032/033、C-51/52/55/56，无空行。</criterion>
      <criterion id="J-B ADR" result="SATISFIED">ADR-097~105 均有 Status 与 Options（grep "- Options" = 9）；ADR-098、104 标 constraint-driven 并列被排除方案。</criterion>
      <criterion id="J-B 接口与小节" result="SATISFIED">IFC-285~298 有类型签名；"数据迁移"(module_design.md:367，无迁移)与"受影响的运行单元"(:380) 小节存在。</criterion>
      <criterion id="J-B 引用真实" result="SATISFIED">核实 registry/services.py:51-52、identity/services.py:48、residency/housing.py:41、registry/models.py specific_part unique 与 uniq_registry_unit、ocap-deploy SKILL.md:149 migrate --noinput、test_identity_display.py:118-125、management/commands/registry_specific_part_preview.py 均存在。</criterion>
      <criterion id="J-B P8" result="SATISFIED">无新依赖、无容器、无迁移、测试不连测试机库；AUTH-01/02 为独立命令、不进部署流程。</criterion>
      <finding id="GR-B-001-F01" severity="MINOR">P10 /root/myproject/Freeark/CLAUDE.md 仅读前 80 行（notes 自述），产出无误。</finding>
      <finding id="GR-B-001-F02" severity="MINOR">OQ-03（C-55 与 Q-SF-13=B 冲突）已由用户后续答复"A"解决：文件放仓库根、加 .gitignore、不提交，与 C-55/AC-187-06 一致；设计正文仍写"是否提交由用户另定"，以 clarifications 为准。</finding>
      <condition>GROUP_C：在 .gitignore 加入导出文件忽略规则（建议文件名 registry_import_underground_parking.xlsx，同时覆盖 .csv）；同步 test_identity_display.py:118-125 等因排序口径变更而失效的既有断言（逐条在 implementation_plan 说明）；OQ-01 --allow-gaps、OQ-02 写法列表按设计实现。</condition>
    </gate_review>
    <gate_review id="GR-C-001" invocation_id="ocap_unit_sort_filters-GROUP_C-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T12:18:10+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/development/implementation_plan.md" version="0.1.0"/><file path="project_workspace/ocap_unit_sort_filters/development/code_review_report.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-C MOD 全部实现" result="SATISFIED">MOD-104~110：ordering.py、services.py、identity/services.py、housing.py、views.py+urls.py、AdminRegistry.vue+api.js、underground.py、exporting.py、两条命令均存在。</criterion>
      <criterion id="J-C 改动范围" result="SATISFIED">git status：改 9 个（含 .gitignore）、新建 5 个后端文件，与 implementation_plan 一致；其余未提交改动为既有 ocap_product_review 文档与 agent 记忆。</criterion>
      <criterion id="J-C 追溯抽查" result="SATISFIED">implementation_plan.md:42 起 24 行覆盖 US-183~192；抽查 US-183（services.py sorted_values/natural_key）、US-187（exporting.py:60/121/171、import_template.py:41）、US-188（underground.py:234 O_EXCL 0600 备份、:298 apply_relocation 校验备份 sha256）、US-189（views.py _apply_unit_filters、Exists 子查询）、US-192（identity/services.py:49、housing.py:63 unit_sort_key）均与代码相符。</criterion>
      <criterion id="J-C 客户端构建与测试" result="SATISFIED">PM 亲跑 frontend vitest 与 build、miniprogram vitest，见 verification。</criterion>
      <criterion id="J-C PM 复跑零新增失败" result="SATISFIED">后端 723/723 OK，与基线一致。</criterion>
      <criterion id="J-C 迁移 P6" result="SATISFIED">makemigrations --check：No changes detected；无新迁移文件。</criterion>
      <criterion id="J-C 评审算术" result="SATISFIED">code_review_report.md:18-19：310/35=8.86，MINOR 4，无 CRITICAL/MAJOR。</criterion>
      <verification><![CDATA[venv Python 3.12.3 + Django 5.2.19，仓库根
(cd backend && manage.py check) -> System check identified no issues (0 silenced).
(cd backend && makemigrations --check --dry-run) -> No changes detected
(cd backend && manage.py test --settings=config.test_settings) -> Ran 723 tests in 73.153s / OK
(cd frontend && npx vitest run --passWithNoTests) -> Test Files 24 passed (24) / Tests 248 passed (248)
(cd frontend && npm run build -- --base=/ocap/) -> built in 44.47s
(cd miniprogram && npx vitest run --passWithNoTests) -> Test Files 14 passed (14) / Tests 97 passed (97)
git check-ignore -v registry_import_underground_parking.{xlsx,csv} -> .gitignore:14 / .gitignore:15 命中]]></verification>
      <finding id="GR-C-001-F01" severity="MINOR">本次新增代码无任何新测试（ordering、过滤 API、两条命令、AdminRegistry 页），由 GROUP_D 补齐；CR-001~004 ASSUMPTION 需测试覆盖。</finding>
      <condition>GROUP_D：为 CR-001~004 涉及行为写用例；契约测试须覆盖新路由 admin/registry/units/filter-options 与新增查询参数；AUTH-01/02 命令在 SQLite 测试库覆盖 dry-run/apply/冲突停止/幂等/restore/--allow-gaps 全路径。</condition>
    </gate_review>
    <gate_review id="GR-D-001" invocation_id="ocap_unit_sort_filters-GROUP_D-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T12:43:37+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/testing/test_plan.md" version="0.1.0"/><file path="project_workspace/ocap_unit_sort_filters/testing/unit_test_report.md" version="0.1.0"/><file path="project_workspace/ocap_unit_sort_filters/testing/integration_test_report.md" version="0.1.0"/><file path="project_workspace/ocap_unit_sort_filters/testing/e2e_test_report.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-D 复跑一致" result="SATISFIED">PM 复跑与报告一致：unit 185、integration 576、e2e 55、smoke 6（合计 822=723+99 新写），前端 259（248+11），小程序 97，全部 OK。</criterion>
      <criterion id="J-D 故事覆盖" result="SATISFIED">test_plan.md:111-124 US-183~192 每行均有已执行用例。</criterion>
      <criterion id="J-D 契约" result="SATISFIED">test_registry_filters_contract.py（4 条）解析 api.js registryFilterOptions/registryUnits 与 AdminRegistry.vue 参数名并逐个对应后端；既有 test_frontend_contract.py 通过。</criterion>
      <criterion id="J-D baseline" result="SATISFIED">各层相对基线零新增失败；skip 0；新测试中 mock 仅用于导出失败注入（test_registry_export_cmd.py:239/249/259）与前端 http 层，未打在被测逻辑上。</criterion>
      <criterion id="J-D 冻结点" result="SATISFIED">新测试文件最晚修改 12:25:47，报告写于 12:31–12:37。</criterion>
      <criterion id="J-D 产品代码未改" result="SATISFIED">backend/apps + frontend/src diff 151+/32- 与 GR-C-001 时相同（183 行）。</criterion>
      <verification><![CDATA[venv Python 3.12.3 + Django 5.2.19，仓库根
(cd backend && manage.py test tests.unit) -> Ran 185 tests / OK
(cd backend && manage.py test tests.integration) -> Ran 576 tests / OK
(cd backend && manage.py test tests.e2e) -> Ran 55 tests / OK
(cd backend && manage.py test tests.smoke) -> Ran 6 tests / OK
(cd frontend && npx vitest run --passWithNoTests) -> Test Files 25 passed (25) / Tests 259 passed (259)
(cd miniprogram && npx vitest run --passWithNoTests) -> Test Files 14 passed (14) / Tests 97 passed (97)
仓库根无 *.xlsx/*.csv/*.jsonl 残留]]></verification>
      <finding id="GR-D-001-F01" severity="MINOR">requirements_spec.md、architecture_design.md 未全文读取（notes 自述），产出未见出错。</finding>
      <finding id="GR-D-001-F02" severity="MINOR">O-01：若测试库负层楼层写成 "-1"/"-2"，导出自检会拒绝落盘（TC-INT-620）；AUTH-01 前须先跑 relocate dry-run 查看楼层写法清单。</finding>
      <condition>E1/E2：人工验证 MV-01~05（含 AUTH-01/02 真实数据执行与 MySQL 并发保护 MV-03）纳入部署计划；执行顺序为 部署 → relocate dry-run（看写法与冲突）→ 经授权 apply（AUTH-02）→ 经授权导出（AUTH-01），避免 AC-187-05 的并存问题。</condition>
    </gate_review>
    <gate_review id="GR-E1-001" invocation_id="ocap_unit_sort_filters-GROUP_E1-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T12:54:34+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/deployment/cicd_pipeline.md" version="0.1.0"/><file path="project_workspace/ocap_unit_sort_filters/deployment/deployment_plan.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-E1 DEPLOY/ROLLBACK" result="SATISFIED">DEPLOY-001~013 与 ROLLBACK-001~013 各 13 个（grep 去重计数）；DEPLOY-007 apply 标 [MANUAL_ROLLBACK_REQUIRED]（deployment_plan.md:243、408）。</criterion>
      <criterion id="J-E1 环境与策略" result="SATISFIED">仅测试环境（P7 57279 通道与指纹，:55-66）；不 migrate、不 pip、不改 nginx 与 Freeark 服务（:158），nginx 仅备份（:124-125）。</criterion>
      <criterion id="J-E1 预检与验证" result="SATISFIED">阶段 A~D 预检（:74-106）；部署后验证与远程 E2E 限 e2e_ 账号并强制 cleanup（:281-317）。</criterion>
      <criterion id="J-E1 独立授权" result="SATISFIED">授权点总表 A~E（:22），AUTH-02=C、AUTH-01=D，先改库后导出。</criterion>
      <criterion id="J-E1 凭据" result="SATISFIED">mysqldump 口令经 .env 读入 MYSQL_PWD，计划内无凭据值（grep 无命中）。</criterion>
      <finding id="GR-E1-001-F01" severity="MAJOR">流程事故：子代理用嵌套 heredoc 写计划，导致本机执行了非预期命令，在 / 留下 /ocap_backend_15ea79e….tar.gz（45B）与 /frontend_dist.tar.gz（20B），PM 核查均为空归档；~/.ssh/known_hosts 未变（最后修改 2026-11-09），git 状态无意外变化；未见远端操作迹象。子代理删除被安全检查拦截，交由用户处理。产物本身不受影响。</finding>
      <finding id="GR-E1-001-F02" severity="MINOR">architecture_design.md、test_plan.md 未全文读取（notes 自述）。</finding>
      <condition>E2 前：用户同意是否推送 15ea79e 并核对 CI；每个授权点（A~E）须用户当轮单独授权；用户处理 / 下两个残留空归档。</condition>
    </gate_review>
    <gate_review id="GR-E2-001" invocation_id="ocap_unit_sort_filters-GROUP_E2-001" decision="PASS" time="2026-11-16T13:24:07+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/deployment/deployment_report.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-E2 状态" result="SATISFIED">阶段 A DEPLOYED_SUCCESSFULLY；预检 14、验证 15 项均有实际输出；ANCHOR_TS=20261116130503。</criterion>
      <criterion id="J-E2 PM 只读核验" result="SATISFIED">见 verification。</criterion>
      <verification><![CDATA[curl https://ai-freeark.xin/ocap/ -> 200，入口 index-W5V17xyS.js（与报告一致）
curl .../api/v1/admin/registry/units/filter-options -> 401（路由存在，需鉴权）；对照不存在路径 -> 404
curl .../api/v1/units/options -> 401
ssh（只读）: systemctl is-active ocap-backend -> active
目标机 apps/registry/ordering.py sha256 前 16 位 583a3ee3d856ca24 = git show 15ea79e:backend/apps/registry/ordering.py
目标机 snapshots: backend-20261116130503.tar.gz、web-20261116130503.tar.gz 存在]]></verification>
    </gate_review>
    <gate_review id="GR-E2-002" invocation_id="ocap_unit_sort_filters-GROUP_E2-002" decision="PASS" time="2026-11-16T13:44:08+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/deployment/deployment_report.md" version="1.1.0"/></reviewed_files>
      <criterion id="J-E2 阶段 B" result="SATISFIED">deployment_report.md:159-197：total 5742、would_change=1391、conflicts=0、old_building|1栋|1391、负1 1119 / 负2 272 均 recognized、other_building_negative_parking=0、negative_floor_non_parking=1。</criterion>
      <verification><![CDATA[PM 只读 ssh + manage.py shell（只读 ORM 查询，不输出姓名/手机号）：
非车位负层记录 1 条：id=4347 1栋负1层1139号 SHOP 1栋 负1
building="地下车位" 现有 0 条（未写库）；snapshots 下 underground-* 0 个
注：PM 重试循环因末条 grep -c 计数 0 返回 1 未 break，只读查询重复执行 5 次，无副作用（见 SELF_CORRECTION）。]]></verification>
      <condition>阶段 C 前须用户：确认 N=1391、决定 id=4347（负1层商铺）是否纳入、授权 apply（含 mysqldump 备份）。</condition>
    </gate_review>
    <gate_review id="GR-E2-003" invocation_id="ocap_unit_sort_filters-GROUP_E2-003" decision="PASS" time="2026-11-16T13:53:17+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/deployment/deployment_report.md" version="2.1.0"/></reviewed_files>
      <criterion id="J-E2 阶段 C" result="SATISFIED">apply moved=1391，before/after units 5742、owners 7862、phones 4301、有效 Membership 2 均相等；幂等 dry-run would_change=0；mysqldump 与备份 JSONL 均 0600。</criterion>
      <verification><![CDATA[PM 只读 ssh + manage.py shell：
total 5742；building="地下车位" 1391；1栋下 PARKING 负层 0；id=4347 仍 1栋 SHOP 负1
RegistryService.options() 楼栋顺序：1栋…10栋（数字序）→ 文字楼栋 → 地下车位（最后）
options(building="地下车位") -> level=floor（单元跳过），选项 ['负2','负1']
snapshots: -rw------- 1682257 ocapdb-registry-20261116134900.sql；-rw------- 360351 underground-20261116134900.jsonl]]></verification>
    </gate_review>
    <gate_review id="GR-E2-004" invocation_id="ocap_unit_sort_filters-GROUP_E2-004" decision="PASS_WITH_CONDITIONS" time="2026-11-16T14:32:33+08:00">
      <reviewed_files><file path="project_workspace/ocap_unit_sort_filters/deployment/deployment_report.md" version="3.1.0"/></reviewed_files>
      <criterion id="J-E2 阶段 D" result="SATISFIED">导出自检 diff_*=0、precheck_rows_failed=0、roundtrip_mismatches=0；两端 sha256 一致；目标机临时文件已删。</criterion>
      <criterion id="J-E2 阶段 E" result="SATISFIED">远程 Ran 22：19 PASS / 2 FAIL / 1 SKIP；2 FAIL 为既有 DEF-B（remote_cases.py:77、114 期望"户主"）；DEF-A 无失败；本批可验点经只读 HTTP 补证（楼栋数字序、地下车位最后、下一级 负2/负1）。</criterion>
      <verification><![CDATA[本机：registry_import_underground_parking.xlsx 权限 600、336459 字节、sha256 70ed019c8f60b3d7a763f9397288a2624955c08ed4b9c8e365e9d412ee938dc1（与报告一致）；git check-ignore 命中；git status 无该文件
目标机只读：OCAP_E2E_FIXTURE=1 manage.py e2e_fixture status -> e2e 各项全 0；RegistryUnit 5742 / RegistryOwner 7862 / RegistryPhone 4301；claim_amount_max 1000000.00
snapshots 下 export_* 0 个；ocap-backend active]]></verification>
      <finding id="GR-E2-004-F01" severity="MINOR">deployment_report 3.1.0 文件头 timestamp 为估算值（agent 自述），违反 §B 真实时间要求。</finding>
      <finding id="GR-E2-004-F02" severity="MINOR">devops-engineer 用 cat &gt;&gt; 追加 MEMORY.md 未先 Read；探测脚本错误导致夹具循环 3 次（每次均清理，无影响）。</finding>
      <condition>遗留：DEF-B（ocap_product_review 远程用例期望文案过期）仍开放；远程套件缺 units/options 逐级顺序用例；MV-03（MySQL 并发）、MV-04、MV-05 待人工核对。</condition>
    </gate_review>
  </gate_reviews>
  <clarifications>
    <clarification time="2026-11-16T11:09:11+08:00" answered_by="用户"><![CDATA[用户原话："Q1： 我忘了这个文件没有在repo track，之前我用管理员页面的批量导入上传过一次，你能从服务器找到？ 。 Q2：A， Q3：A， Q4：A。 其他都按照推荐"
映射：Q-SF-02=A（楼栋取值"地下车位"）；Q-SF-03=A；Q-SF-04=A（中文数字负层与阿拉伯数字等价）；Q-SF-05=A 两端都改；Q-SF-06=A 已认证房屋列表纳入同一口径（并入 ocap_product_review DEF-A）；Q-SF-07=A 类型车位且楼层为负层；Q-SF-08=A 原地更新、标识冲突停止上报（执行仍须另行授权）；Q-SF-09=A；Q-SF-10=B 不加楼层；Q-SF-11=A 地下车位排在编号楼栋之后；Q-SF-12=A 不设性能指标；I-01~I-07 视为确认（"其他都按照推荐"）。
Q-SF-01 未决：PM 核查结果——导入接口只在内存读取上传文件、不落盘（backend/apps/registry/views.py:292-306），审计只记统计；只读 ssh 在测试机 /home/yangyang、/tmp、/var/tmp 搜索 xlsx/csv，仅有 Freeark 文件，未找到清册导入文件。已追问用户。]]></clarification>
    <clarification time="2026-11-16T11:11:59+08:00" answered_by="用户"><![CDATA[用户原话："Q1：B"。Q-SF-01=B：在测试机从现有清册只读导出、按导入模板格式生成新的导入文件（地下车位已改正）；文件含个人信息，不入库；导出执行须用户另行授权。]]></clarification>
    <clarification time="2026-11-16T11:43:21+08:00" answered_by="用户"><![CDATA[用户原话："Q13：B， 放到工作区根目录，提交进repo跟踪。 Q14：A ， Q15：对。 全部确认，开始开发"
Q-SF-13=B：生成文件放仓库根并提交跟踪（PM 提示：仓库 yangyang198354-haha/ocap 为 PUBLIC，文件含业主姓名与手机号；提交/推送时须用户当轮再次确认，见汇报）。Q-SF-14=A；Q-SF-15=确认。故事确认，放行开发（GROUP_B→C→D）。]]></clarification>
    <clarification time="2026-11-16T11:45:11+08:00" answered_by="用户"><![CDATA[用户原话："A"（针对 PM 提示公开仓库含个人信息的选项）。Q-SF-13 修订：导入文件放仓库根目录，加入 .gitignore，不提交。替代上一条"提交进 repo 跟踪"。GROUP_C 须把 .gitignore 规则纳入改动，GROUP_B 门控核对设计未要求提交。]]></clarification>
    <clarification time="2026-11-16T12:47:56+08:00" answered_by="用户"><![CDATA[用户原话："Q1:A, Q2:A"。Q1=A 只提交本批文件（主会话已提交 15ea79e，未推送；_kb_inbox.jsonl 含 ocap_product_review 行，未纳入）；Q2=A 制作测试环境部署计划（GROUP_E1，仅计划，不部署）。]]></clarification>
    <clarification time="2026-11-16T13:01:51+08:00" answered_by="用户"><![CDATA[用户原话："授权推送和部署 Q1：A， Q2：A"。推送 main（含 976817d、15ea79e）并核对 CI；授权部署阶段 A（代码部署到测试环境）。阶段 B~E 未授权。]]></clarification>
    <clarification time="2026-11-16T13:45:41+08:00" answered_by="用户"><![CDATA[用户原话："4347 选 A；授权 C 段，N=1391"。id=4347（1栋负1层1139号，商铺）不纳入修正，保留在 1栋下。]]></clarification>
    <clarification time="2026-11-16T14:52:30+08:00" answered_by="用户"><![CDATA[用户原话："1.都写。 2.不推送。 3.A， 4 授权删除。 5.A 6.看了没问题"。通用候选 M-PM-003、M-TE-012、M-DE-022 确认写入；不推送（是否提交待确认）；目标机两份含个人信息备份保留 7 天（至 2026-11-23）后删除；本机 / 下两个空归档已由 PM 删除；DEF-B 下一批修，ocap_product_review 上报保持开放；MV-04、MV-05 用户已人工核对通过。]]></clarification>
  </clarifications>
  <checkpoints/>
  <escalations/>
  <audit_log>
    <event time="2026-11-16T11:00:21+08:00" type="RUN" actor="pm-orchestrator">主会话模式：用户直接陈述需求（判定规则 3）。已读 shared_protocol.md、project_profile.md(1.5.0)、generic/pm-orchestrator.md。</event>
    <event time="2026-11-16T11:00:21+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（ocap_unit_sort_filters-GROUP_A-001，PHASE_01–02）</event>
    <event time="2026-11-16T11:04:17+08:00" type="GATE" actor="pm-orchestrator">GR-A-001 PASS_WITH_CONDITIONS（2 MINOR）；产物保持 DRAFT 0.1.0，待用户答复开放问题与确认故事后 RA 定稿再批准。kb_inbox 已有本次 2 条记录（hook 生效）。</event>
    <event time="2026-11-16T11:09:11+08:00" type="RUN" actor="pm-orchestrator">PM 只读 ssh（P9 允许）在测试机搜索 xlsx/csv：未找到清册导入文件。</event>
    <event time="2026-11-16T11:11:59+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（GROUP_A-002）按用户答复定稿</event>
    <event time="2026-11-16T11:16:12+08:00" type="SELF_CORRECTION" actor="pm-orchestrator">GROUP_A-002 调用中 PM 误称 AC-157-01/02 位于 ocap_identity_display/user_stories.md，实际在 ocap_product_review/requirements/user_stories.md:129-130；RA 已按实际位置引用，PM 已 grep 核实。</event>
    <event time="2026-11-16T11:16:12+08:00" type="GATE" actor="pm-orchestrator">GR-A-002 PASS_WITH_CONDITIONS（1 MINOR）；产物 0.2.0 DRAFT，待用户确认后批准。</event>
    <event time="2026-11-16T11:43:21+08:00" type="GATE" actor="pm-orchestrator">用户确认故事；GROUP_A APPROVED，requirements_spec / user_stories 升 1.0.0。</event>
    <event time="2026-11-16T11:43:21+08:00" type="INVOCATION" actor="pm-orchestrator">调用 system-architect（GROUP_B-001）</event>
    <event time="2026-11-16T11:59:25+08:00" type="GATE" actor="pm-orchestrator">GR-B-001 PASS_WITH_CONDITIONS；架构三件升 1.0.0 APPROVED。PM 基线（HEAD 976817d，Python 3.12.3 + Django 5.2.19）：后端 Ran 723 OK；前端 vitest 248/248；小程序 97/97。</event>
    <event time="2026-11-16T11:59:25+08:00" type="INVOCATION" actor="pm-orchestrator">调用 software-developer（GROUP_C-001）</event>
    <event time="2026-11-16T12:18:10+08:00" type="GATE" actor="pm-orchestrator">GR-C-001 PASS_WITH_CONDITIONS；开发两件升 1.0.0 APPROVED。</event>
    <event time="2026-11-16T12:18:10+08:00" type="INVOCATION" actor="pm-orchestrator">调用 test-engineer（GROUP_D-001）</event>
    <event time="2026-11-16T12:43:37+08:00" type="GATE" actor="pm-orchestrator">GR-D-001 PASS_WITH_CONDITIONS；测试四件升 1.0.0 APPROVED。按用户逐阶段放行习惯，暂停于 GROUP_E1 前，向用户汇报。</event>
    <event time="2026-11-16T12:47:56+08:00" type="RUN" actor="pm-orchestrator">经用户当轮同意（Q1=A），主会话提交 15ea79e（40 文件），未推送。</event>
    <event time="2026-11-16T12:47:56+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（GROUP_E1-001，仅计划）</event>
    <event time="2026-11-16T12:54:34+08:00" type="EXCEPTION" actor="pm-orchestrator">devops-engineer（E1-001）嵌套 heredoc 误执行本机命令，产生 / 下两个空 tar.gz；PM 只读核查无远端影响；未代为删除，报告用户。</event>
    <event time="2026-11-16T12:54:34+08:00" type="GATE" actor="pm-orchestrator">GR-E1-001 PASS_WITH_CONDITIONS；部署两件升 1.0.0 APPROVED。等待用户授权 E2（按授权点逐段）。</event>
    <event time="2026-11-16T13:01:51+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">用户本轮明确授权：push main + 测试环境阶段 A（DEPLOY-001~004 及只读冒烟）。仅本次有效；B~E 未授权。</event>
    <event time="2026-11-16T13:04:00+08:00" type="RUN" actor="pm-orchestrator">git push origin main：3ffd868..15ea79e；CI run 43807677398 success（Backend / Mini program / Web frontend 全部 success）。</event>
    <event time="2026-11-16T13:04:00+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（GROUP_E2-001，仅阶段 A）</event>
    <event time="2026-11-16T13:24:07+08:00" type="GATE" actor="pm-orchestrator">GR-E2-001 PASS（阶段 A）。阶段 B~E 待用户逐段授权。</event>
    <event time="2026-11-16T13:27:32+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">用户本轮原话"授权 B 段"：仅阶段 B（DEPLOY-005 relocate dry-run，只读）。C~E 未授权。</event>
    <event time="2026-11-16T13:27:32+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（GROUP_E2-002，仅阶段 B）</event>
    <event time="2026-11-16T13:44:08+08:00" type="SELF_CORRECTION" actor="pm-orchestrator">PM 只读核验的 ssh 重试循环以 "... ; ls | grep -c underground" 结尾，计数 0 时返回码 1，&amp;&amp; break 不触发，只读查询重复 5 次（无写入）。与 M-PM-003 同类：重试循环的成功判据不要依赖 grep -c 返回码。</event>
    <event time="2026-11-16T13:44:08+08:00" type="GATE" actor="pm-orchestrator">GR-E2-002 PASS（阶段 B）；报告 2.0.0 APPROVED，1.0.0 SUPERSEDED。等待用户就阶段 C 决定。</event>
    <event time="2026-11-16T13:45:41+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">用户本轮原话"4347 选 A；授权 C 段，N=1391"：仅阶段 C（DEPLOY-006 mysqldump 备份 + DEPLOY-007 apply，--expect-changes 1391）。D、E 未授权。</event>
    <event time="2026-11-16T13:45:41+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（GROUP_E2-003，仅阶段 C）</event>
    <event time="2026-11-16T13:53:17+08:00" type="GATE" actor="pm-orchestrator">GR-E2-003 PASS（阶段 C 改库完成）；报告 3.0.0 APPROVED。等待用户授权 D、E。</event>
    <event time="2026-11-16T13:55:08+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">用户本轮原话"授权D 、E 段"：阶段 D（DEPLOY-008~010 导出、取回仓库根、删除目标机临时文件）与阶段 E（DEPLOY-011~013 e2e_ 夹具、远程 HTTP E2E、清理）。</event>
    <event time="2026-11-16T13:55:08+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（GROUP_E2-004，阶段 D、E）</event>
    <event time="2026-11-16T14:32:33+08:00" type="GATE" actor="pm-orchestrator">GR-E2-004 PASS_WITH_CONDITIONS（阶段 D、E）；GROUP_E2 APPROVED；报告 4.0.0。</event>
    <event time="2026-11-16T14:33:05+08:00" type="RUN" actor="pm-orchestrator">delivery_report.md 写入，最终状态 DELIVERED_WITH_ISSUES。</event>
    <event time="2026-11-16T14:33:05+08:00" type="INVOCATION" actor="pm-orchestrator">调用 kb-curator（GROUP_Z-001，PHASE_12）</event>
    <event time="2026-11-16T14:39:02+08:00" type="RUN" actor="pm-orchestrator">kb-curator 完成：34 条晋升、8 条加证据、3 条通用候选（M-PM-003、M-TE-012、M-DE-022）待用户确认；补同步 .trae→.claude 遗漏的 18 条。</event>
    <event time="2026-11-16T14:52:30+08:00" type="RUN" actor="pm-orchestrator">经用户授权删除 /ocap_backend_15ea79e….tar.gz、/frontend_dist.tar.gz（核实 / 下无残留）。MV-04/05 用户确认通过。</event>
    <event time="2026-11-16T14:52:30+08:00" type="INVOCATION" actor="pm-orchestrator">调用 kb-curator（GROUP_Z-002，GENERIC_KB_CONFIRMED）</event>
    <event time="2026-11-16T14:53:28+08:00" type="RUN" actor="pm-orchestrator">kb-curator 写入 generic 三条（pm-orchestrator/test-engineer/devops-engineer 各 +1 行），PM grep 核实无项目专有名词。</event>
  </audit_log>
</phase_status>
