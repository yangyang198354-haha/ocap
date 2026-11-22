<phase_status project="ocap_appeal_center" mode="INCREMENTAL" created="2026-11-22T09:12:00+08:00" updated="2026-11-22T11:05:39+08:00">
  <request time="2026-11-22T09:12:00+08:00"><![CDATA[1.用户登录web 主页， 认证申述和我的申述应该放到同一个二级菜单。但是放到两个tab 里面。2. 我的申述可以看到自己提交的申述的记。包括进行中的和已经处理的。3.处理的能看到结果，管理员的备注。 正在处理的还可以撤回重新编辑了提交。 4. 我的同住人申请页面 申请记录放到另外一个tab，要求和申述的页面一样。5. 我的同住人申请，也要填写自己的实名。6.作为同住人的实名也可以在 我的身份与房屋页面显示。  先整理我的需求，拆分呈用户故事。确认后再开始开发。]]></request>
  <profile version="1.2.0"/>
  <workspace_note>INCREMENTAL + PARTIAL_FLOW：本批次仅执行 GROUP_A（PHASE_01 需求分析、PHASE_02 用户故事拆分），产出需求与用户故事供用户确认；确认后再决定是否进入 GROUP_B 及后续阶段。docs_root 采用本批次独立目录 project_workspace/ocap_appeal_center/（沿用本项目既往批次约定）。</workspace_note>
  <groups>
    <group id="GROUP_A" agent="requirement-analyst" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0">
      <phase id="PHASE_01" status="APPROVED"/><phase id="PHASE_02" status="APPROVED"/>
    </group>
    <group id="GROUP_B" agent="system-architect" status="APPROVED" gate_decision="PASS_WITH_CONDITIONS" retries="0">
      <phase id="PHASE_03" status="APPROVED"/><phase id="PHASE_04" status="APPROVED"/>
    </group>
    <group id="GROUP_C" agent="software-developer" status="APPROVED" gate_decision="PASS" retries="0">
      <phase id="PHASE_05" status="APPROVED"/><phase id="PHASE_06" status="APPROVED"/>
    </group>
    <group id="GROUP_D" agent="test-engineer" status="APPROVED" gate_decision="PASS" retries="0" defect_loops="1">
      <phase id="PHASE_07" status="APPROVED"/><phase id="PHASE_08" status="APPROVED"/><phase id="PHASE_09" status="APPROVED"/>
    </group>
    <group id="GROUP_E1" agent="devops-engineer" status="APPROVED" gate_decision="PASS" retries="0">
      <phase id="PHASE_10" status="APPROVED"/><phase id="PHASE_11a" status="APPROVED"/>
    </group>
    <group id="GROUP_E2" agent="devops-engineer" status="NOT_AUTHORIZED" gate_decision="PENDING" environment="" retries="0">
      <phase id="PHASE_11b" status="PENDING"/>
    </group>
  </groups>
  <artifacts>
    <artifact path="project_workspace/ocap_appeal_center/requirements/requirements_spec.md" version="1.0.0" status="SUPERSEDED" group="GROUP_A">经 GR-A-001 批准；按 D-01~D-04 定向修订后被 2.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/requirements/user_stories.md" version="1.0.0" status="SUPERSEDED" group="GROUP_A">经 GR-A-001 批准；被 2.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/requirements/requirements_spec.md" version="2.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_appeal_center/requirements/user_stories.md" version="2.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_appeal_center/architecture/architecture_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_appeal_center/architecture/module_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_appeal_center/architecture/tech_stack.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_appeal_center/development/implementation_plan.md" version="1.0.0" status="SUPERSEDED" group="GROUP_C">经 GR-C-001 批准；因 DEF-AC-01 缺陷修复被 1.1.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/development/code_review_report.md" version="1.0.0" status="SUPERSEDED" group="GROUP_C">经 GR-C-001 批准；被 1.1.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/development/implementation_plan.md" version="1.1.0" status="SUPERSEDED" group="GROUP_C">返工草稿；经 GR-C-002 批准后由 2.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/development/code_review_report.md" version="1.1.0" status="SUPERSEDED" group="GROUP_C">返工草稿；经 GR-C-002 批准后由 2.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/development/implementation_plan.md" version="2.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_appeal_center/development/code_review_report.md" version="2.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_appeal_center/testing/test_plan.md" version="0.1.0" status="SUPERSEDED" group="GROUP_D">首轮草稿；被复跑版取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/testing/unit_test_report.md" version="0.1.0" status="SUPERSEDED" group="GROUP_D">首轮草稿；被复跑版取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/testing/integration_test_report.md" version="0.1.0" status="SUPERSEDED" group="GROUP_D">首轮草稿（含 DEF-AC-01 失败证据）；被复跑版取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/testing/e2e_test_report.md" version="0.1.0" status="SUPERSEDED" group="GROUP_D">首轮草稿（含 DEF-AC-01 失败证据）；被复跑版取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/testing/test_plan.md" version="0.2.0" status="SUPERSEDED" group="GROUP_D">DEF-AC-01 修复后复跑草稿；经 GR-D-002 批准后由 1.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/testing/unit_test_report.md" version="0.2.0" status="SUPERSEDED" group="GROUP_D">复跑草稿；由 1.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/testing/integration_test_report.md" version="0.2.0" status="SUPERSEDED" group="GROUP_D">复跑草稿；由 1.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/testing/e2e_test_report.md" version="0.2.0" status="SUPERSEDED" group="GROUP_D">复跑草稿；由 1.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/testing/test_plan.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_appeal_center/testing/unit_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_appeal_center/testing/integration_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_appeal_center/testing/e2e_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_appeal_center/deployment/cicd_pipeline.md" version="0.1.0" status="SUPERSEDED" group="GROUP_E1">草稿；经 GR-E1-001 批准后由 1.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/deployment/deployment_plan.md" version="0.1.0" status="SUPERSEDED" group="GROUP_E1">草稿；经 GR-E1-001 批准后由 1.0.0 取代</artifact>
    <artifact path="project_workspace/ocap_appeal_center/deployment/cicd_pipeline.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="project_workspace/ocap_appeal_center/deployment/deployment_plan.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
  </artifacts>
  <legacy_baseline>project_workspace/ocap/requirements/requirements_spec.md 5.0.0（用户 2026-11-16 前确认）、project_workspace/ocap/requirements/user_stories.md 3.0.0，以及 project_workspace/ocap_batch_1118/requirements/ 下 1.0.0 两份产物，作为本次增量的已批准基线。</legacy_baseline>
  <invocations>
    <invocation id="ocap_appeal_center-GROUP_A-1" agent="requirement-analyst" group="GROUP_A" start="2026-11-22T09:12:00+08:00" end="2026-11-22T09:34:39+08:00" result="SUCCESS">PHASE_01/PHASE_02：8 条功能需求、2 条非功能需求、8 个用户故事、29 个 AC。</invocation>
    <invocation id="ocap_appeal_center-GROUP_A-2" agent="requirement-analyst" group="GROUP_A" start="2026-11-22T09:36:12+08:00" end="2026-11-22T09:39:02+08:00" result="SUCCESS">按用户答复 D-01~D-04 定向修订，推断项清零，编号与 AC 数量不变。</invocation>
    <invocation id="ocap_appeal_center-GROUP_B-1" agent="system-architect" group="GROUP_B" start="2026-11-22T09:42:10+08:00" end="2026-11-22T09:43:33+08:00" result="SUCCESS">PHASE_03/PHASE_04：ADR-160~165（6 个，均含 Status）、MOD-168~173（6 个）、IFC-381~392；含数据迁移（0006_appeal_center）与受影响运行单元。</invocation>
    <invocation id="ocap_appeal_center-GROUP_C-1" agent="software-developer" group="GROUP_C" start="2026-11-22T09:45:36+08:00" end="2026-11-22T10:21:32+08:00" result="SUCCESS">PHASE_05/PHASE_06：MOD-168~173 全部实现；29 文件 +386/-135；后端 1159 OK（2 skipped）、前端 562 passed、构建成功；CRITICAL 0 / MAJOR 0 / MINOR 7。</invocation>
    <invocation id="ocap_appeal_center-GROUP_D-1" agent="test-engineer" group="GROUP_D" start="2026-11-22T10:29:15+08:00" end="2026-11-22T10:49:35+08:00" result="PARTIAL_SUCCESS">新增 6 前端 unit + 6 后端 integration + 2 后端 E2E；unit 568/568 PASS；integration 850（846 通过/3 错误/1 skip）FAIL；E2E 75（73 通过/2 错误）FAIL；上报 DEF-AC-01。</invocation>
    <invocation id="ocap_appeal_center-GROUP_C-2" agent="software-developer" group="GROUP_C" start="2026-11-22T10:52:00+08:00" end="2026-11-22T10:58:46+08:00" result="SUCCESS">REWORK（DEF-AC-01）：AUDIT_ACTIONS 增加 APPEAL_WITHDRAWN / RESIDENT_APPLICATION_WITHDRAWN（+1 行）；后端 1167 OK（2 skipped）、前端 568 passed、构建 8.43s、迁移 No changes；文档升至 1.1.0。</invocation>
    <invocation id="ocap_appeal_center-GROUP_D-2" agent="test-engineer" group="GROUP_D" start="2026-11-22T10:58:46+08:00" end="2026-11-22T11:02:47+08:00" result="SUCCESS">DEF-AC-01 修复后复跑：unit 568/568、integration 850（849 pass/1 skip）、E2E 75/75、全量后端 1167 OK（2 skipped）；零新增失败，三层门控 PASSED；四份 testing 产物升 0.2.0。</invocation>
    <invocation id="ocap_appeal_center-GROUP_E1-1" agent="devops-engineer" group="GROUP_E1" start="2026-11-22T11:02:47+08:00" end="2026-11-22T11:05:39+08:00" result="SUCCESS">PHASE_10/PHASE_11a：cicd_pipeline.md（CI 无需修改，P1~P10）与 deployment_plan.md（8 DEPLOY / 8 ROLLBACK，含 0006 迁移门控与回滚人工项）；仅规划，未连接目标环境。</invocation>
  </invocations>
  <gate_reviews>
    <gate_review id="GR-A-001" invocation_id="ocap_appeal_center-GROUP_A-1" decision="PASS_WITH_CONDITIONS" time="2026-11-22T09:36:12+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_appeal_center/requirements/requirements_spec.md" version="1.0.0"/>
        <file path="project_workspace/ocap_appeal_center/requirements/user_stories.md" version="1.0.0"/>
      </reviewed_files>
      <criterion id="A-来源" result="SATISFIED">8 条 REQ-FUNC 均标注用户原文条目或现有代码位置；抽查 menus.js:12/14、residency/models.py:34-68、residency/views.py:345-428、UnitsApplications.vue:1-17 均存在且与描述一致。</criterion>
      <criterion id="A-AC格式" result="SATISFIED">脚本核对 29 条 AC 全部含 Given/When/Then，正则统计 AC_bad=0。</criterion>
      <criterion id="A-推断占比" result="SATISFIED">[INFERRED] 需求 1 条（REQ-FUNC-292），分母 8+2=10，占比 10% ≤ 画像 P5 的 20%；已列入待确认推断项。</criterion>
      <criterion id="A-无技术实现" result="SATISFIED">需求表只描述系统行为与页面元素；接口路径仅作为现状基线引用，未规定实现方案。</criterion>
      <criterion id="A-编号唯一" result="SATISFIED">定义级扫描（REQ-FUNC/C 表格行、US 标题）无跨批次重复：REQ-FUNC-289~296、C-359~361、US-291~298 仅存在于本批次；现有最大编号 288/358/290。</criterion>
      <criterion id="A-覆盖" result="SATISFIED">6 条用户原文逐条映射：1→289、2→290、3→291/292、4→293/294、5→295、6→296；8 个 Must Have 故事覆盖全部功能需求。</criterion>
      <verification><![CDATA[AC 统计：AC_count=29 AC_bad=0；定义级编号扫描：NO_DUP_US，本批次 REQ-FUNC/C 无跨批次冲突；kb_inbox --check-response 返回 RESPONSE_OK。]]></verification>
      <condition>进入 GROUP_B 前须经用户确认：(1) REQ-FUNC-292 撤回后重新提交采用"新记录 + 关联原记录"；(2) 开放问题 Q1 菜单文案与默认 Tab、Q2 备注是否选填、Q3 重提可改房屋与实名、Q4 已撤回记录默认展示。</condition>
    </gate_review>
    <gate_review id="GR-A-002" invocation_id="ocap_appeal_center-GROUP_A-2" decision="PASS" time="2026-11-22T09:39:02+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_appeal_center/requirements/requirements_spec.md" version="2.0.0"/>
        <file path="project_workspace/ocap_appeal_center/requirements/user_stories.md" version="2.0.0"/>
      </reviewed_files>
      <criterion id="A-决策落地" result="SATISFIED">D-01 入口沿用"认证申诉"写入 REQ-FUNC-289 与 AC-291-01；D-02 新记录关联写入 REQ-FUNC-292、AC-294-03/296-03；D-03 备注选填写入 REQ-FUNC-291；D-04 已撤回默认展示写入 REQ-FUNC-292/294。</criterion>
      <criterion id="A-推断占比" result="SATISFIED">推断项 0 条（0 ÷ 10 = 0%），原推断转为确定需求并在执行摘要说明。</criterion>
      <criterion id="A-编号稳定" result="SATISFIED">需求 REQ-FUNC-289~296、C-359~361、US-291~298 编号未变；AC 数量仍为 29，格式复核 AC_bad=0。</criterion>
      <criterion id="A-开放问题" result="SATISFIED">4 个开放问题均补结论与"已评估未采纳"备选，原分析保留，无未决软措辞。</criterion>
      <verification><![CDATA[kb_inbox --check-response 返回 RESPONSE_OK（GROUP_A-2）；决策记录表 4 行；推断标记 0 处（除执行摘要的文字说明）。]]></verification>
    </gate_review>
    <gate_review id="GR-B-001" invocation_id="ocap_appeal_center-GROUP_B-1" decision="PASS_WITH_CONDITIONS" time="2026-11-22T09:45:36+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_appeal_center/architecture/architecture_design.md" version="1.0.0"/>
        <file path="project_workspace/ocap_appeal_center/architecture/module_design.md" version="1.0.0"/>
        <file path="project_workspace/ocap_appeal_center/architecture/tech_stack.md" version="1.0.0"/>
      </reviewed_files>
      <criterion id="B-需求覆盖" result="SATISFIED">module_design 需求覆盖表逐条列出 REQ-FUNC-289~296 与 REQ-NFUNC-059/060，均映射到至少一个 MOD-168~173；脚本统计每条 REQ-FUNC 在 module_design 中出现 1~3 次，无空行。</criterion>
      <criterion id="B-ADR" result="SATISFIED">architecture_design 含 6 个 ADR（ADR-160~165），脚本核对 `### ADR-` 与 `- Status:` 计数均为 6；除 ADR-165 为 constraint-driven 并写明被排除方案与约束来源外，其余均给出 ≥2 方案对比与正负后果。</criterion>
      <criterion id="B-接口" result="SATISFIED">IFC-381~392 均给出方法/路径或类型签名、鉴权方式（M/A + 对象级本人校验）与输入校验/错误码；module_design 给出 AppealView/ApplicationView/HousingResident 的类型定义。</criterion>
      <criterion id="B-迁移与运行单元" result="SATISFIED">module_design 含“数据迁移”小节（0006_appeal_center，10 步操作、历史数据策略、反向 `[MANUAL_ROLLBACK_REQUIRED]`）与“受影响的运行单元 / 构建”（后端 migrate+重启、MySQL、Web 构建、小程序不发布）。</criterion>
      <criterion id="B-引用真实性" result="SATISFIED">PM 亲自 Test-Path 核对 frontend/src/layout/menus.js、router/index.js、portal/Units.vue、units/UnitsAppeal.vue、UnitsMyAppeals.vue、UnitsApplications.vue、UnitsIdentity.vue、backend/apps/residency/views.py、housing.py、migrations/0005_membership_registry_owner.py 全部存在；引用的行号与读取内容一致。</criterion>
      <criterion id="B-禁用项" result="SATISFIED">全文仅以“不使用/禁用”提及 Docker、容器化、pscp、makemigrations；无选中禁用技术的方案；迁移为手写 scoped，符合画像 P6/P8。</criterion>
      <criterion id="B-编号唯一" result="SATISFIED">全仓扫描：ADR-160~165、MOD-168~173、IFC-381~392 在 ocap_appeal_center 之外出现次数均为 0；沿用 PM 指定起点，未复用历史编号。</criterion>
      <criterion id="B-决策落地" result="SATISFIED">D-01 写入 ADR-160 与 IFC-392a/路由旧地址；D-02 写入 ADR-162/IFC-382/385；D-03 写入 ADR-163/IFC-384/388；D-04 写入 ADR-161；C-359/C-360 写入 IFC-381/386 与 pending_slot 释放；C-361 写入 ADR-164。</criterion>
      <criterion id="B-P11" result="SATISFIED">领域与外部依赖出处小节明确“不适用”：本批无新增硬件、算法或闭源 API 调用，既有微信/短信接口未改动。</criterion>
      <finding id="GR-B-001-F01" severity="MINOR">画像 P10 为 system-architect 指定的 /root/myproject/Freeark/CLAUDE.md 在当前工作机不存在，架构师改用仓库内既有架构基线并在 notes 说明；未影响产出正确性。</finding>
      <finding id="GR-B-001-F02" severity="MINOR">ADR-163/A-01 将同住申请驳回原因设计为选填（为兼容旧小程序调用），与申诉“驳回原因必填”口径不同；已在开放问题记录，需用户确认是否接受。</finding>
      <condition>GROUP_C 严格按 module_design 的 MOD-168~173 与 IFC-381~392 实现；不依赖 /root/myproject/Freeark/CLAUDE.md；不得改变 A-01 的选填口径（如用户提出变更须回到 GROUP_B）。</condition>
      <verification><![CDATA[Get-ChildItem 核对三文件存在（13528/22795/3998 字节），文件头 status=DRAFT version=0.1.0（门控后 PM 改为 APPROVED/1.0.0）；`### ADR-`=6、`- Status:`=6；module_design 含需求覆盖表/依赖关系/数据迁移/受影响的运行单元/领域与外部依赖出处 5 个固定小节；kb_inbox --check-response 返回 RESPONSE_OK，--agent 写入 3 条提案。]]></verification>
    </gate_review>
    <gate_review id="GR-C-001" invocation_id="ocap_appeal_center-GROUP_C-1" decision="PASS_WITH_CONDITIONS" time="2026-11-22T10:29:15+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_appeal_center/development/implementation_plan.md" version="1.0.0"/>
        <file path="project_workspace/ocap_appeal_center/development/code_review_report.md" version="1.0.0"/>
      </reviewed_files>
      <criterion id="C-改动范围" result="SATISFIED">PM 亲自 `git status --short`/`git diff --stat`：29 个代码/测试文件与 implementation_plan 清单一致（后端 residency 4 文件 + 迁移 + 4 个后端契约测试；前端 14 个源文件 + 12 个测试；miniprogram/utils/labels.js 仅同步标签）；无无关代码改动。`_kb_inbox.jsonl` 与文档目录为本流程产物，miniprogram/dist 等未跟踪项为既有环境产物。</criterion>
      <criterion id="C-迁移" result="SATISFIED">0006_appeal_center.py 为手写单 app 迁移（10 项操作，含反向 [MANUAL_ROLLBACK_REQUIRED] 注释）；PM 复跑 `makemigrations --check --dry-run residency` → No changes detected；未出现 makemigrations 全量产物（P6/P8）。</criterion>
      <criterion id="C-后端测试" result="SATISFIED">PM 亲自复跑 `cd backend &amp;&amp; python manage.py test --settings=config.test_settings` → Ran 1159 tests in 46.762s，OK (skipped=2)，与基线一致、零新增失败。</criterion>
      <criterion id="C-前端测试与构建" result="SATISFIED">PM 亲自复跑 `npm --prefix frontend test` → Test Files 49 passed，Tests 562 passed；`npm --prefix frontend run build` → ✓ built in 8.30s（仅既有 chunk 体积警告）。</criterion>
      <criterion id="C-需求追溯" result="SATISFIED">implementation_plan 追溯表覆盖 US-291~298 共 29 条 AC，全部 DONE；PM 抽查 US-291（menus.js/AppealCenter.vue）、US-294（AppealWithdrawView/UnitsMyAppeals）、US-295（UnitsApplications 双 Tab）、US-297（UnitsApplicationForm 实名校验）、US-298（housing._latest_resident_names + UnitsIdentity）实际代码均存在且逻辑一致。</criterion>
      <criterion id="C-评审一致性" result="SATISFIED">code_review_report 五维评分均 ≥8，平均 8.6；修正后问题表 7 条 MINOR 与摘要“MINOR 7（已修复 4、OPEN 3）”算术一致；CRITICAL 0、MAJOR 0；无遗留 CRITICAL。</criterion>
      <criterion id="C-安全" result="SATISFIED">撤回/决定接口均有对象级本人或产权业主校验；备注与实名长度校验（≤500/≤64）；审计 detail 不含凭据；无硬编码密钥。</criterion>
      <criterion id="C-禁用项" result="SATISFIED">无 Docker/容器化、无 pscp、无新增第三方依赖；小程序仅标签表同步，无功能改造。</criterion>
      <finding id="GR-C-001-F01" severity="MINOR">IFC-385 的 applicant_name 后端改为“提供时校验、缺省允许空串”（兼容旧小程序），与架构“缺失→400”存在偏差；已在 implementation_plan“架构偏差”与 CR-308 记录。</finding>
      <finding id="GR-C-001-F02" severity="MINOR">旧地址 /units/appeals 可路由且默认“我的申诉”Tab，但菜单无独立项导致侧栏二级无高亮（leaf=null）；满足 AC-291-03，未影响功能。</finding>
      <finding id="GR-C-001-F03" severity="MINOR">miniprogram/utils/labels.js 增加 WITHDRAWN 标签，仅为通过 Web/小程序标签键集合一致性守卫测试，未改变小程序行为。</finding>
      <condition>GROUP_D 须覆盖本批新增行为（撤回、重新提交关联、处理备注、同住申请实名、身份页实名），并以后端“applicant_name 可缺省”为既定契约断言；不得把旧 /units/appeals 无菜单高亮当缺陷。</condition>
      <verification><![CDATA[
PM 独立复跑：
- backend: Ran 1159 tests in 46.762s / OK (skipped=2)
- frontend: Test Files 49 passed (49) / Tests 562 passed (562) / Duration 320.43s
- build: ✓ built in 8.30s
- migration: DJANGO_SECRET_KEY=<dummy> python manage.py makemigrations --check --dry-run residency → No changes detected in app 'residency'
- scope: git diff --stat → 29 files changed, 386 insertions(+), 135 deletions(-)
]]></verification>
    </gate_review>
    <gate_review id="GR-D-001" invocation_id="ocap_appeal_center-GROUP_D-1" decision="FAIL" time="2026-11-22T10:52:00+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_appeal_center/testing/test_plan.md" version="0.1.0"/>
        <file path="project_workspace/ocap_appeal_center/testing/unit_test_report.md" version="0.1.0"/>
        <file path="project_workspace/ocap_appeal_center/testing/integration_test_report.md" version="0.1.0"/>
        <file path="project_workspace/ocap_appeal_center/testing/e2e_test_report.md" version="0.1.0"/>
      </reviewed_files>
      <criterion id="D-单元" result="SATISFIED">PM 复跑 `npm --prefix frontend test` → Test Files 50 passed / Tests 568 passed（基线 562 + 新增 TC-UNIT-1532~1537 共 6 条）；报告 total=568=568+0+0+0+0，通过率 100%，本层门控 PASSED，与 &lt;evidence&gt; 计数行逐字一致。</criterion>
      <criterion id="D-集成" result="NOT_SATISFIED">`cd backend &amp;&amp; python manage.py test tests.integration --settings=config.test_settings` → Ran 850 tests / FAILED (errors=3, skipped=1)，相对基线新增 3 条错误（TC-INT-1502/1503/1505），根因均为 DEF-AC-01；报告 total=846+3+1+0+0=850，本层门控 FAILED。</criterion>
      <criterion id="D-E2E" result="NOT_SATISFIED">全量后端 Ran 1167 tests / FAILED (errors=5, skipped=2)，新增 TC-E2E-1615/1616 同因 DEF-AC-01 失败；critical path 口径=替代（多步 HTTP API），覆盖率 8/8=100%，通过率 0/8，本层门控 FAILED。</criterion>
      <criterion id="D-全量回归" result="NOT_SATISFIED">后端 1160 pass / 5 error / 2 skip；基线 1159 pass / 2 skip；相对基线新增失败 5（3 集成 + 2 E2E），全部由 DEF-AC-01 引起，零既有用例回归。前端 568 passed，构建 ✓ built in 8.37s。</criterion>
      <criterion id="D-追溯" result="SATISFIED">test_plan 含 29 条 AC 映射表与 8 个 Must Have 故事覆盖核对表，无空行；新增后端契约/集成/E2E 用例均能溯源到 US/AC 并打分层标记；前后端分离场景已包含契约测试并列执行。</criterion>
      <criterion id="D-度量" result="SATISFIED">三份报告 total = pass + fail + skip + blocked + not_testable 公式均成立；报告摘要计数与 &lt;evidence&gt; 输出计数行逐字一致；报告时间戳（10:49:35）晚于测试文件最后修改。</criterion>
      <finding id="GR-D-001-F01" severity="CRITICAL">DEF-AC-01：撤回接口写审计时抛 ValueError（未登记动作），申诉/同住申请撤回均返回 500；需回流 GROUP_C 最小修复 backend/apps/core/audit.py 的 AUDIT_ACTIONS。</finding>
      <condition>回流 software-developer（REWORK_AUTHORIZED）仅修复 DEF-AC-01（AUDIT_ACTIONS 增加 “APPEAL_WITHDRAWN” 与 “RESIDENT_APPLICATION_WITHDRAWN”），不得改动其他业务逻辑；修复后 GROUP_D 重新按层执行集成/E2E 并全量回归。defect_loops 当前 1，上限 2。</condition>
      <verification><![CDATA[
PM 复跑与报告比对：
- frontend: Test Files 50 passed (50) / Tests 568 passed (568) → 单元层 PASSED
- backend integration: Ran 850 tests in 24.690s / FAILED (errors=3, skipped=1)
- backend full: Ran 1167 tests / FAILED (errors=5, skipped=2)；1160 通过
- 缺陷定位：backend/apps/core/audit.py:10 AUDIT_ACTIONS 缺两项；audit.py:66-67 抛错；views.py:306 与 :490 为调用点
]]></verification>
    </gate_review>
    <gate_review id="GR-C-002" invocation_id="ocap_appeal_center-GROUP_C-2" decision="PASS" time="2026-11-22T10:58:46+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_appeal_center/development/implementation_plan.md" version="1.1.0"/>
        <file path="project_workspace/ocap_appeal_center/development/code_review_report.md" version="1.1.0"/>
      </reviewed_files>
      <criterion id="C-缺陷修复" result="SATISFIED">DEF-AC-01 已修复：`backend/apps/core/audit.py:10-15` 的 AUDIT_ACTIONS 增加 "APPEAL_WITHDRAWN" 与 "RESIDENT_APPLICATION_WITHDRAWN"；`git diff --stat -- backend/apps/core/audit.py` → 1 file changed, 1 insertion(+)。未改 views.py、前端、测试或接口契约，最小改动成立。</criterion>
      <criterion id="C-后端测试" result="SATISFIED">PM 亲自复跑 `cd backend &amp;&amp; python manage.py test --settings=config.test_settings` → Ran 1167 tests in 45.831s / OK (skipped=2)；GROUP_D 的 TC-INT-1502/1503/1505 与 TC-E2E-1615/1616 恢复通过，零失败。</criterion>
      <criterion id="C-前端测试与构建" result="SATISFIED">PM 亲自复跑 `npm --prefix frontend test` → Test Files 50 passed (50) / Tests 568 passed (568)；`npm --prefix frontend run build` → ✓ built in 8.43s（仅既有 chunk 体积警告）。</criterion>
      <criterion id="C-迁移" result="SATISFIED">`DJANGO_SECRET_KEY=&lt;dummy&gt; python manage.py makemigrations --check --dry-run residency` → No changes detected in app 'residency'；本次未新增迁移。</criterion>
      <criterion id="C-改动范围" result="SATISFIED">`git status --short` 显示本轮返工仅新增 `M backend/apps/core/audit.py`；其余为 GROUP_C-1 既有改动与本流程文档产物，无无关代码改动。</criterion>
      <criterion id="C-追溯" result="SATISFIED">implementation_plan 1.1.0 保留 US-291~298 全部 29 条 AC 的 DONE 追溯，并新增“缺陷修复记录（1.1.0）”表；code_review_report 1.1.0 新增“缺陷修复”小节（DEF → 位置 → 根因 → 修改）。</criterion>
      <verification><![CDATA[
PM 独立复跑（修复后）：
- backend: Ran 1167 tests in 45.831s / OK (skipped=2)
- frontend: Test Files 50 passed (50) / Tests 568 passed (568)
- build: ✓ built in 8.43s
- migration: No changes detected in app 'residency'
- scope: backend/apps/core/audit.py | 1 +（1 file changed, 1 insertion）
- hook: kb_inbox --check-response → RESPONSE_OK invocation_id=ocap_appeal_center-GROUP_C-2 status=SUCCESS；--agent 追加 1 条提案
]]></verification>
    </gate_review>
    <gate_review id="GR-D-002" invocation_id="ocap_appeal_center-GROUP_D-2" decision="PASS" time="2026-11-22T11:02:47+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_appeal_center/testing/test_plan.md" version="0.2.0"/>
        <file path="project_workspace/ocap_appeal_center/testing/unit_test_report.md" version="0.2.0"/>
        <file path="project_workspace/ocap_appeal_center/testing/integration_test_report.md" version="0.2.0"/>
        <file path="project_workspace/ocap_appeal_center/testing/e2e_test_report.md" version="0.2.0"/>
      </reviewed_files>
      <criterion id="D-单元" result="SATISFIED">PM 复跑 `npm --prefix frontend test` → Test Files 50 passed (50) / Tests 568 passed (568)；报告 total=568+0+0+0+0=568，通过率 100%，本层门控 PASSED。</criterion>
      <criterion id="D-集成" result="SATISFIED">PM 复跑 `python manage.py test tests.integration --settings=config.test_settings` → Ran 850 tests in 37.412s / OK (skipped=1)；报告 total=849+0+1+0+0=850，通过率 100%，本层门控 PASSED；TC-INT-1502/1503/1505 恢复通过。</criterion>
      <criterion id="D-E2E" result="SATISFIED">PM 复跑 `python manage.py test tests.e2e --settings=config.test_settings` → Ran 75 tests in 6.966s / OK；critical path 口径=替代（多步 HTTP API），覆盖率 8/8=100%、通过率 8/8=100%，本层门控 PASSED；TC-E2E-1615/1616 恢复通过。</criterion>
      <criterion id="D-全量回归" result="SATISFIED">PM 复跑全量后端 → Ran 1167 tests in 45.831s / OK (skipped=2)（1165 pass + 2 skip）；相对基线（1159 pass/2 skip）零新增失败；前端 568 passed、构建成功。</criterion>
      <criterion id="D-追溯" result="SATISFIED">test_plan 的 29 条 AC 映射与 8 个 Must Have 故事覆盖核对表保持完整；本轮未新增用例，分组/标记与首轮一致；契约测试（test_frontend_contract 等）随集成层执行通过。</criterion>
      <criterion id="D-度量" result="SATISFIED">三份报告 metrics 公式成立；报告摘要与 &lt;evidence&gt; 计数行逐字一致（568 / 850 OK skipped=1 / 75 OK / 1167 OK skipped=2）；报告时间戳 11:01:52 晚于最后一次测试执行。</criterion>
      <verification><![CDATA[
PM 独立复跑（DEF-AC-01 修复后）：
- frontend: Test Files 50 passed (50) / Tests 568 passed (568) / Duration 328.11s
- integration: Ran 850 tests in 37.412s / OK (skipped=1)
- e2e: Ran 75 tests in 6.966s / OK
- backend full: Ran 1167 tests in 45.831s / OK (skipped=2)
- scope: 本轮未新增/修改测试代码与产品代码
- hook: kb_inbox --check-response → RESPONSE_OK invocation_id=ocap_appeal_center-GROUP_D-2 status=SUCCESS；--agent 追加 1 条提案
]]></verification>
    </gate_review>
    <gate_review id="GR-E1-001" invocation_id="ocap_appeal_center-GROUP_E1-1" decision="PASS_WITH_CONDITIONS" time="2026-11-22T11:05:39+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_appeal_center/deployment/cicd_pipeline.md" version="0.1.0"/>
        <file path="project_workspace/ocap_appeal_center/deployment/deployment_plan.md" version="0.1.0"/>
      </reviewed_files>
      <criterion id="E1-产物齐全" result="SATISFIED">cicd_pipeline.md 含“现状与影响 / 流水线概览 / 阶段定义 / 环境矩阵 / 制品管理”5 节；deployment_plan.md 含“变更摘要 / 目标环境与策略 / 预检清单 / 部署步骤 / 回滚步骤 / 不可逆步骤汇总 / 部署后验证 / 部署授权”8 节。</criterion>
      <criterion id="E1-回滚配对" result="SATISFIED">脚本计数：`### DEPLOY-` = 8（001~008），`### ROLLBACK-` = 8（001~008）；回滚按 008→001 逆序排列，每个 DEPLOY 行均标注对应 ROLLBACK；ROLLBACK-005 与 ROLLBACK-001 标 MANUAL_ROLLBACK_REQUIRED 并写明数据风险。</criterion>
      <criterion id="E1-预检" result="SATISFIED">预检 PRE-001~PRE-010 覆盖：部署版本确认、测试复跑、迁移符合 P6、无依赖变更、SSH 可达、资源、服务/端口基线、目标机本地状态保护（.env/venv/var）、迁移现状、备份工具；每项有命令与通过标准。</criterion>
      <criterion id="E1-环境与策略" result="SATISFIED">环境矩阵仅列画像 P7 的测试环境（内网/外网入口、静态目录 /home/yangyang/ocap/web/ocap、MySQL、systemd ocap-backend）；生产不存在；策略 recreate 并给出理由与停机估算；无 Docker/容器/pscp。</criterion>
      <criterion id="E1-验证" result="SATISFIED">部署后验证 V-01~V-12 覆盖服务存活、日志无错误、迁移完成、撤回/列表接口 401、审计动作登记、前端 bundle 与新文案、外网入口、Freeark 未受影响、失败单元与端口归属；每项写命令与成功标准并区分关键/非关键。</criterion>
      <criterion id="E1-迁移门控" result="SATISFIED">DEPLOY-005 设两道门控：待应用迁移恰为 residency.0006_appeal_center；`sqlmigrate` 输出无 UPDATE/INSERT/DELETE/DROP TABLE（仅 DDL）。回滚前统计 WITHDRAWN_ROWS。</criterion>
      <finding id="GR-E1-001-F01" severity="MINOR">现有 CI 的 backend job 使用 `config.test_settings`（MIGRATION_MODULES 禁用迁移），0006 的真实 DDL 不在 CI 中执行；已由 DEPLOY-005 的 `sqlmigrate` 门控与 `makemigrations --check` 预检补偿，本批不修改 CI。</finding>
      <condition>PHASE_11b 前须由用户在本轮对话中明确授权测试环境部署，并由 PM 在 invocation 写入 PRODUCTION_DEPLOY_CONFIRM=true 与环境名“测试”；同时须确认 PRE-001 的部署版本（提交后按 commit 打包，或明确同意从工作区打包）；未取得授权不得执行任何部署命令。</condition>
      <verification><![CDATA[
PM 核验：
- 两文件存在且文件头齐全
- DEPLOY=8、ROLLBACK=8（Select-String 计数）
- 迁移 0006：手写；2 个 AlterField + 8 个 AddField；反向条件可逆
- 画像 P7/P8 核对：仅测试环境、物理机 tar 部署、无容器
- 钩子：kb_inbox --check-response → RESPONSE_OK ocap_appeal_center-GROUP_E1-1 status=SUCCESS
]]></verification>
    </gate_review>
  </gate_reviews>
  <clarifications>
    <clarification id="Q-AC-01" answered_by="用户" time="2026-11-22T09:37:30+08:00">菜单入口文案与默认 Tab：保留"认证申诉"作为入口名，默认选中"认证申诉"Tab（D-01）。</clarification>
    <clarification id="Q-AC-02" answered_by="用户" time="2026-11-22T09:37:30+08:00">撤回后重新提交：新建记录并关联原记录，原记录保留为"已撤回"（D-02）。</clarification>
    <clarification id="Q-AC-03" answered_by="用户" time="2026-11-22T09:37:30+08:00">处理备注：通过与驳回均为选填，驳回原因仍必填（D-03）。</clarification>
    <clarification id="Q-AC-04" answered_by="用户" time="2026-11-22T09:37:30+08:00">已撤回记录在列表中默认展示，标签"已撤回"（D-04）。</clarification>
  </clarifications>
  <checkpoints>
  </checkpoints>
  <escalations>
  </escalations>
  <audit_log>
    <event time="2026-11-22T09:12:00+08:00" type="RUN" actor="pm-orchestrator">PM 本次运行开始。运行模式：主会话模式（用户直接陈述需求并显式加载 Skill: sdlc-orchestrator，非转述）。意图：新需求增量 + PARTIAL_FLOW（仅 GROUP_A，先出需求与用户故事待确认）。已读 .trae/skills/sdlc-shared-protocol/SKILL.md、.trae/sdlc/project_profile.md（1.2.0 APPROVED）、.trae/sdlc/knowledge_base/generic/pm-orchestrator.md、.trae/sdlc/agent-memory/pm-orchestrator/MEMORY.md。preflight：--check-all 返回 0（skills=9 profile=APPROVED），--check-cwd 返回 0。</event>
    <event time="2026-11-22T09:12:00+08:00" type="RUN" actor="pm-orchestrator">初始化本批次工作区 project_workspace/ocap_appeal_center/，登记 6 条用户需求原文；基线编号扫描：最大 REQ-FUNC-288、US-290、C-358，要求本次从 REQ-FUNC-289、US-291、C-359 起且全仓唯一（记忆 P-PM-006）。</event>
    <event time="2026-11-22T09:12:00+08:00" type="INVOCATION" actor="pm-orchestrator">准备调用 requirement-analyst（invocation ocap_appeal_center-GROUP_A-1，PHASE_01/PHASE_02，INCREMENTAL）。</event>
    <event time="2026-11-22T09:34:39+08:00" type="INVOCATION" actor="pm-orchestrator">requirement-analyst 返回 SUCCESS：requirements_spec.md 与 user_stories.md（0.1.0）已写入；hook 校验 RESPONSE_OK，_kb_inbox.jsonl 追加 2 条提案。</event>
    <event time="2026-11-22T09:36:12+08:00" type="GATE" actor="pm-orchestrator">GR-A-001 PASS_WITH_CONDITIONS：8 功能/2 非功能需求、8 故事/29 AC；AC 格式与编号唯一性经 PM 脚本复核通过；条件为进入 GROUP_B 前需用户确认 1 条推断项与 4 个开放问题。</event>
    <event time="2026-11-22T09:36:12+08:00" type="RUN" actor="pm-orchestrator">本批次按 PARTIAL_FLOW 停在 GROUP_A：需求与用户故事已交付待用户确认，未进入 GROUP_B，未修改任何产品代码。</event>
    <event time="2026-11-22T09:37:30+08:00" type="RUN" actor="pm-orchestrator">用户经 AskUserQuestion 答复 4 个开放问题（D-01~D-04），记录到 clarifications。</event>
    <event time="2026-11-22T09:39:02+08:00" type="INVOCATION" actor="pm-orchestrator">requirement-analyst 定向修订返回 SUCCESS（ocap_appeal_center-GROUP_A-2）：推断项清零、新增决策记录，编号与 AC 数量不变；hook 校验 RESPONSE_OK。</event>
    <event time="2026-11-22T09:39:02+08:00" type="GATE" actor="pm-orchestrator">GR-A-002 PASS：决策落地、推断 0%、编号稳定、开放问题全部收敛；requirements_spec.md 与 user_stories.md 2.0.0 批准，GROUP_A 关闭。等待用户决定是否进入 GROUP_B。</event>
    <event time="2026-11-22T09:41:31+08:00" type="RUN" actor="pm-orchestrator">用户本轮明确说"好的，进入 GROUP_B 开始开发"，授权继续 GROUP_B→C→D→E1（部署仍须单独授权）。preflight --check-cwd 返回 0。</event>
    <event time="2026-11-22T09:41:31+08:00" type="INVOCATION" actor="pm-orchestrator">准备调用 system-architect（invocation ocap_appeal_center-GROUP_B-1，PHASE_03/PHASE_04，INCREMENTAL），输入 requirements_spec.md 与 user_stories.md 2.0.0。</event>
    <event time="2026-11-22T09:43:33+08:00" type="INVOCATION" actor="pm-orchestrator">system-architect 返回 SUCCESS（ocap_appeal_center-GROUP_B-1）：architecture_design.md、module_design.md、tech_stack.md（0.1.0/DRAFT）已写入；hook 校验 RESPONSE_OK，_kb_inbox.jsonl 追加 3 条提案。</event>
    <event time="2026-11-22T09:45:36+08:00" type="GATE" actor="pm-orchestrator">GR-B-001 PASS_WITH_CONDITIONS：6 个 ADR、6 个 MOD、IFC-381~392；覆盖 8 条功能需求与 2 条非功能需求；数据迁移与运行单元齐全；编号全仓唯一；引用文件经 PM Test-Path 核实。MINOR findings：F01 画像 P10 文件不可得（改读仓库基线）、F02 同住驳回原因选填口径需用户确认。三份架构产物升为 1.0.0/APPROVED，GROUP_B 关闭。</event>
    <event time="2026-11-22T09:45:36+08:00" type="INVOCATION" actor="pm-orchestrator">准备调用 software-developer（invocation ocap_appeal_center-GROUP_C-1，PHASE_05/PHASE_06，INCREMENTAL），输入需求 2.0.0 与架构 1.0.0。</event>
    <event time="2026-11-22T10:21:32+08:00" type="INVOCATION" actor="pm-orchestrator">software-developer 返回 SUCCESS（ocap_appeal_center-GROUP_C-1）：implementation_plan.md 与 code_review_report.md 已写入；hook 校验 RESPONSE_OK，_kb_inbox.jsonl 追加 3 条提案。</event>
    <event time="2026-11-22T10:29:15+08:00" type="GATE" actor="pm-orchestrator">GR-C-001 PASS_WITH_CONDITIONS：PM 亲自复跑后端 1159 OK（2 skipped）、前端 562 passed、构建成功、迁移一致性无差异；29 文件改动与计划一致；29 条 AC 全部 DONE（抽查 5 个故事）。MINOR findings：F01 applicant_name 后端可缺省（兼容旧小程序）、F02 旧地址无菜单高亮、F03 小程序标签表同步。开发文档升为 1.0.0/APPROVED，GROUP_C 关闭。</event>
    <event time="2026-11-22T10:29:15+08:00" type="INVOCATION" actor="pm-orchestrator">准备调用 test-engineer（invocation ocap_appeal_center-GROUP_D-1，PHASE_07/PHASE_08/PHASE_09，INCREMENTAL）。</event>
    <event time="2026-11-22T10:49:35+08:00" type="INVOCATION" actor="pm-orchestrator">test-engineer 返回 PARTIAL_SUCCESS（ocap_appeal_center-GROUP_D-1）：test_plan 与三份分层报告已写入；前端单元层 568/568 PASS；集成层 846/850（3 错误）、E2E 73/75（2 错误），上报 CRITICAL 缺陷 DEF-AC-01；hook 校验 RESPONSE_OK。</event>
    <event time="2026-11-22T10:52:00+08:00" type="GATE" actor="pm-orchestrator">GR-D-001 FAIL：单元层 SATISFIED；集成/E2E/全量回归 NOT_SATISFIED，5 条新增失败全部由 DEF-AC-01 引起；缺陷回流 GROUP_C（REWORK_AUTHORIZED，defect_loops=1）。GROUP_D 置 REJECTED。</event>
    <event time="2026-11-22T10:52:00+08:00" type="INVOCATION" actor="pm-orchestrator">准备回流 software-developer（invocation ocap_appeal_center-GROUP_C-2，PHASE_05/PHASE_06 REWORK），仅修复 DEF-AC-01：backend/apps/core/audit.py 的 AUDIT_ACTIONS 增加 APPEAL_WITHDRAWN 与 RESIDENT_APPLICATION_WITHDRAWN。</event>
    <event time="2026-11-22T10:58:46+08:00" type="INVOCATION" actor="pm-orchestrator">software-developer 返回 SUCCESS（ocap_appeal_center-GROUP_C-2）：audit.py 增加 2 个审计动作（+1 行）；文档升至 1.1.0/DRAFT；hook 校验 RESPONSE_OK，_kb_inbox.jsonl 追加 1 条提案。</event>
    <event time="2026-11-22T10:58:46+08:00" type="GATE" actor="pm-orchestrator">GR-C-002 PASS：PM 亲自复跑后端 1167 OK（2 skipped，GROUP_D 新增 5 条失败用例全部恢复）、前端 50 文件/568 passed、构建 8.43s、迁移 No changes；本轮仅 audit.py 1 行改动。开发文档升为 2.0.0/APPROVED，1.0.0 与 1.1.0 登记 SUPERSEDED，GROUP_C 关闭。</event>
    <event time="2026-11-22T10:58:46+08:00" type="INVOCATION" actor="pm-orchestrator">准备重跑 test-engineer（invocation ocap_appeal_center-GROUP_D-2，PHASE_07/PHASE_08/PHASE_09），验证 DEF-AC-01 修复后集成/E2E 与全量回归恢复，defect_loops=1。</event>
    <event time="2026-11-22T11:02:47+08:00" type="INVOCATION" actor="pm-orchestrator">test-engineer 返回 SUCCESS（ocap_appeal_center-GROUP_D-2）：unit 568/568、integration 850（849 pass/1 skip）、E2E 75/75、全量后端 1167 OK（2 skipped）；四份 testing 产物升 0.2.0/DRAFT；hook 校验 RESPONSE_OK。</event>
    <event time="2026-11-22T11:02:47+08:00" type="GATE" actor="pm-orchestrator">GR-D-002 PASS：三层门控全部 PASSED，DEF-AC-01 修复后 5 条失败用例全部恢复，零新增失败；critical path 覆盖率与通过率均 8/8。四份 testing 产物升 1.0.0/APPROVED，GROUP_D 关闭。</event>
    <event time="2026-11-22T11:02:47+08:00" type="INVOCATION" actor="pm-orchestrator">准备调用 devops-engineer（invocation ocap_appeal_center-GROUP_E1-1，PHASE_10/PHASE_11a），产出 CI/CD 与部署计划；停在部署授权前，不执行 PHASE_11b。</event>
    <event time="2026-11-22T11:05:39+08:00" type="INVOCATION" actor="pm-orchestrator">devops-engineer 返回 SUCCESS（ocap_appeal_center-GROUP_E1-1）：cicd_pipeline.md 与 deployment_plan.md 已写入；8 DEPLOY / 8 ROLLBACK；仅规划，未连接目标环境；hook 校验 RESPONSE_OK。</event>
    <event time="2026-11-22T11:05:39+08:00" type="GATE" actor="pm-orchestrator">GR-E1-001 PASS_WITH_CONDITIONS：产物齐全、回滚 8/8 逆序配对、预检与验证完整、环境与禁用项符合画像。MINOR F01：CI 测试配置禁用迁移，0006 DDL 不在 CI 执行（由 DEPLOY-005 门控补偿）。两份部署产物升 1.0.0/APPROVED，GROUP_E1 关闭。</event>
    <event time="2026-11-22T11:05:39+08:00" type="RUN" actor="pm-orchestrator">本批次 A→B→C→D→E1 全部完成并门控通过；停在 GROUP_E2 授权前，等待用户本轮对测试环境部署的明确授权。</event>
  </audit_log>
</phase_status>
