<phase_status project="ocap_registry_import" mode="INCREMENTAL" created="2026-11-10T15:52:12+08:00" updated="2026-11-10T22:04:35+08:00">
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
    <group id="GROUP_C" agent="software-developer" status="PENDING" gate_decision="PENDING" retries="0">
      <phase id="PHASE_05" status="PENDING"/><phase id="PHASE_06" status="PENDING"/>
    </group>
    <group id="GROUP_D" agent="test-engineer" status="PENDING" gate_decision="PENDING" retries="0" defect_loops="0">
      <phase id="PHASE_07" status="PENDING"/><phase id="PHASE_08" status="PENDING"/><phase id="PHASE_09" status="PENDING"/>
    </group>
    <group id="GROUP_E1" agent="devops-engineer" status="PENDING" gate_decision="PENDING" retries="0">
      <phase id="PHASE_10" status="PENDING"/><phase id="PHASE_11a" status="PENDING"/>
    </group>
    <group id="GROUP_E2" agent="devops-engineer" status="NOT_AUTHORIZED" environment=""/>
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
  </artifacts>
  <legacy_baseline/>
  <invocations>
    <invocation id="ocap_registry_import-GROUP_A-1" agent="requirement-analyst" start="2026-11-10T15:53:00+08:00" end="2026-11-10T15:57:02+08:00" result="SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_A-2" agent="requirement-analyst" start="2026-11-10T21:13:55+08:00" end="2026-11-10T21:19:15+08:00" result="SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_A-3" agent="requirement-analyst" start="2026-11-10T21:26:27+08:00" end="2026-11-10T21:30:18+08:00" result="SUCCESS"/>
    <invocation id="ocap_registry_import-GROUP_B-1" agent="system-architect" start="2026-11-10T21:40:11+08:00" end="2026-11-10T21:55:29+08:00" result="CLARIFICATION_NEEDED"/>
    <invocation id="ocap_registry_import-GROUP_B-2" agent="system-architect" start="2026-11-10T22:00:57+08:00" end="2026-11-10T22:04:35+08:00" result="SUCCESS"/>
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
  </audit_log>
</phase_status>
