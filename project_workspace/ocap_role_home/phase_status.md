<phase_status project="ocap_role_home" mode="INCREMENTAL" created="2026-11-25T12:03:24+08:00" updated="2026-11-25T14:27:00+08:00">
  <request><![CDATA[Use Skill: sdlc-orchestrator 按照上述的方案，开始整理需求，拆分用户故事。我确认后开始开发。
2026-11-25 用户确认：q-rh-01 好；q-rh-02 不隐藏；q-rh-03 好；开始 sdlc 开发流程。

方案基线（已与用户确认）：
- 角色：游客、同住人、产权业主、业主代表、业委会委员；同住人与产权业主同版式（房屋只读、无“待我处理”）。
- 游客保留财务公开。
- 业主代表“待我表决”仅指业主达标口径的投票；公开决议包含业委会决议与业主代表决议。
- 多重身份按能力渲染；“待我处理（同住人申请）”在任一 HEAD/OWNER 房屋且有未审批申请时显示，单独成卡、多套房合并、数量为 0 隐藏。
- 删除 4 张统计卡、Hero 重复徽章与重复快捷入口宫格；数字只出现在对应模块标题。
- Web 三主题共用 4 栏 Bento 骨架；小程序与 Web 模块顺序一致、单列卡片流。]]></request>
  <profile version="1.3.0">docs_root=project_workspace/ocap_role_home/（增量批次）；画像 APPROVED；preflight --check-all 返回 0。</profile>
  <groups>
    <group id="GROUP_A" agent="requirement-analyst" status="APPROVED" gate_decision="PASS" retries="0">
      <phase id="PHASE_01" status="APPROVED"/><phase id="PHASE_02" status="APPROVED"/>
    </group>
    <group id="GROUP_B" agent="system-architect" status="APPROVED" gate_decision="PASS" retries="0">
      <phase id="PHASE_03" status="APPROVED"/><phase id="PHASE_04" status="APPROVED"/>
    </group>
    <group id="GROUP_C" agent="software-developer" status="APPROVED" gate_decision="PASS" retries="0">
      <phase id="PHASE_05" status="APPROVED"/><phase id="PHASE_06" status="APPROVED"/>
    </group>
    <group id="GROUP_D" agent="test-engineer" status="APPROVED" gate_decision="PASS" retries="0" defect_loops="0">
      <phase id="PHASE_07" status="APPROVED"/><phase id="PHASE_08" status="APPROVED"/><phase id="PHASE_09" status="APPROVED"/>
    </group>
    <group id="GROUP_E1" agent="devops-engineer" status="APPROVED" gate_decision="PASS" retries="0">
      <phase id="PHASE_10" status="APPROVED"/><phase id="PHASE_11a" status="APPROVED"/>
    </group>
    <group id="GROUP_E2" agent="devops-engineer" status="APPROVED" gate_decision="PASS" retries="1" environment="测试环境">
      <phase id="PHASE_11b" status="APPROVED"/>
    </group>
  </groups>
  <artifacts>
    <artifact path="project_workspace/ocap_role_home/requirements/requirements_spec.md" version="1.0.1" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_role_home/requirements/user_stories.md" version="1.0.1" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_role_home/architecture/architecture_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_role_home/architecture/module_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_role_home/architecture/tech_stack.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_role_home/development/implementation_plan.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_role_home/development/code_review_report.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_role_home/testing/test_plan.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_role_home/testing/unit_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_role_home/testing/integration_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_role_home/testing/e2e_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_role_home/deployment/cicd_pipeline.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="project_workspace/ocap_role_home/deployment/deployment_plan.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="project_workspace/ocap_role_home/deployment/deployment_report.md" version="1.1.0" status="APPROVED" group="GROUP_E2"/>
    <artifact path="project_workspace/_kb_distillation/distill_20261125T1426.md" version="1.0.0" status="APPROVED" group="PHASE_12"/>
  </artifacts>
  <legacy_baseline/>
  <invocations>
    <invocation id="ocap_role_home-GROUP_A-001" agent="requirement-analyst" group="GROUP_A" start="2026-11-25T12:03:24+08:00" end="2026-11-25T12:09:30+08:00" result="SUCCESS"/>
    <invocation id="ocap_role_home-GROUP_A-002" agent="requirement-analyst" group="GROUP_A" start="2026-11-25T13:15:00+08:00" end="2026-11-25T13:21:00+08:00" result="SUCCESS"/>
    <invocation id="ocap_role_home-GROUP_B-001" agent="system-architect" group="GROUP_B" start="2026-11-25T12:15:30+08:00" end="2026-11-25T12:19:00+08:00" result="SUCCESS"/>
    <invocation id="ocap_role_home-GROUP_C-001" agent="software-developer" group="GROUP_C" start="2026-11-25T12:21:00+08:00" end="2026-11-25T12:40:30+08:00" result="SUCCESS"/>
    <invocation id="ocap_role_home-GROUP_D-001" agent="test-engineer" group="GROUP_D" start="2026-11-25T12:42:00+08:00" end="2026-11-25T13:04:30+08:00" result="SUCCESS"/>
    <invocation id="ocap_role_home-GROUP_E1-001" agent="devops-engineer" group="GROUP_E1" start="2026-11-25T13:04:40+08:00" end="2026-11-25T13:07:00+08:00" result="SUCCESS"/>
    <invocation id="ocap_role_home-GROUP_E2-001" agent="devops-engineer" group="GROUP_E2" start="2026-11-25T13:19:30+08:00" end="2026-11-25T13:21:20+08:00" result="FAILURE"/>
    <invocation id="ocap_role_home-GROUP_E2-002" agent="devops-engineer" group="GROUP_E2" start="2026-11-25T13:49:50+08:00" end="2026-11-25T14:13:00+08:00" result="SUCCESS"/>
  </invocations>
  <gate_reviews>
    <gate_review id="GR-A-001" invocation_id="ocap_role_home-GROUP_A-001" decision="PASS" time="2026-11-25T12:10:00+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_role_home/requirements/requirements_spec.md" version="1.0.0"/>
        <file path="project_workspace/ocap_role_home/requirements/user_stories.md" version="1.0.0"/>
      </reviewed_files>
      <criterion id="J-A-来源" result="SATISFIED">10 条功能中 9 条引用用户原话与已确认方案；REQ-FUNC-375 引用用户“包含微信小程序/两端一致”；INFERRED 0 条（0 ÷ 11 = 0%），低于画像上限 20%。</criterion>
      <criterion id="J-A-AC" result="SATISFIED">7 个故事共 20 条 AC，全部 Given/When/Then；Then 含具体模块顺序、隐藏条件、请求是否发起、数量与跳转目标。证据：user_stories.md AC-354-01~AC-360-02。</criterion>
      <criterion id="J-A-无技术实现" result="SATISFIED">正文未写框架/组件/接口设计，仅引用现有页面与身份字段作为基线。</criterion>
      <criterion id="J-A-覆盖" result="SATISFIED">REQ-FUNC-366~375 均有至少 1 个 US：366→354/355/359，367→355，368→356/359，369→357，370→358/359，371→354/355/357，372→354/355/356/358，373→358，374→354/356/358，375→360；REQ-NFUNC-079 由 US-360 与各故事共同覆盖。证据：user_stories.md 角色矩阵。</criterion>
      <criterion id="J-A-编号" result="SATISFIED">全仓扫描 REQ-FUNC 366~375、REQ-NFUNC-079、US-354~360、AC-354~360、C-390~396 均无新增重号（脚本扫描未见这些编号冲突）。</criterion>
      <criterion id="J-A-多重身份" result="SATISFIED">US-359 与 AC-359-01~03 覆盖委员/代表兼户主、单卡合并、数量为 0 隐藏，符合用户确认口径。</criterion>
      <condition>开放问题 Q-RH-01（是否展示参与率）、Q-RH-02（空态策略）、Q-RH-03（游客是否看账户明细）为非阻断项，按需求默认口径进入 GROUP_B；用户如不同意需在开发前提出。</condition>
      <verification><![CDATA[
ls 两个产物存在；文件头 version=1.0.0 status=APPROVED。
python 去重扫描：新编号 366~375 / 354~360 / 390~396 无新增冲突。
      ]]></verification>
    </gate_review>
    <gate_review id="GR-A-002" invocation_id="ocap_role_home-GROUP_A-002" decision="PASS" time="2026-11-25T13:22:00+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_role_home/requirements/requirements_spec.md" version="1.0.1"/>
        <file path="project_workspace/ocap_role_home/requirements/user_stories.md" version="1.0.1"/>
      </reviewed_files>
      <criterion id="J-A-决策落定" result="SATISFIED">Q-RH-01/02/03 已由用户拍板：不展示参与率；投票与公开决议无数据保留空态（任务类仍 0 隐藏）；游客只看账户合计与报表。已写入 REQ-FUNC-369/372 备注、C-397、决策记录 D-RH-01~03，并同步 AC-354-01、AC-357-01。</criterion>
      <criterion id="J-A-编号" result="SATISFIED">仅新增 C-397 与 D-RH-01~03，无 REQ/US/AC 编号变化；7 故事 / 20 AC / 27 点不变。</criterion>
      <condition>GROUP_A 定稿 1.0.1，可进入 GROUP_B。</condition>
      <verification><![CDATA[
grep 校验：requirements_spec.md 含 C-397、决策记录；user_stories.md 含“不显示参与率”“保留空态”。
      ]]></verification>
    </gate_review>
    <gate_review id="GR-B-001" invocation_id="ocap_role_home-GROUP_B-001" decision="PASS" time="2026-11-25T12:19:30+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_role_home/architecture/architecture_design.md" version="1.0.0"/>
        <file path="project_workspace/ocap_role_home/architecture/module_design.md" version="1.0.0"/>
        <file path="project_workspace/ocap_role_home/architecture/tech_stack.md" version="1.0.0"/>
      </reviewed_files>
      <criterion id="J-B-覆盖" result="SATISFIED">REQ-FUNC-366~375 全部在 module_design「需求覆盖表」有对应 MOD：366/367/368/369/370→MOD-215/216/218/219，371→216/219，372→216/219，373→216/219，374→216/217/219，375→216/217/219。</criterion>
      <criterion id="J-B-无循环依赖" result="SATISFIED">依赖图仅 MOD-216→MOD-215/MOD-217、MOD-219→MOD-218 与只读 HTTP；两端互不引用，无环。</criterion>
      <criterion id="J-B-ADR" result="SATISFIED">8 个 ADR 均有 Status/Type/Context(REQ)/Decision/Consequences：ADR-196、ADR-198 为 decision 型且各列 2~3 个方案对比；ADR-195/197/199/200/201 为 constraint-driven 并写明被排除方案与约束来源（C-390/C-391/C-393/C-397/D-RH-03）。</criterion>
      <criterion id="J-B-接口类型" result="SATISFIED">IFC-436/437/438/439/440/441/442/443/444 均给出类型或样式契约；HTTP 契约表 IFC-445~452 均写鉴权（IsMember/IsCommitteeMember）与降级/错误。</criterion>
      <criterion id="J-B-迁移与运行单元" result="SATISFIED">module_design 含「数据迁移：无」与「受影响的运行单元 / 构建」表（Web 构建、主题生成、小程序构建、后端无变更）。</criterion>
      <criterion id="J-B-引用真实" result="SATISFIED">PM 抽查引用：frontend/src/stores/auth.js:7-18、Home.vue:2-107、style.css:178-219、miniprogram/store/auth.js:6-12、backend/apps/ledger/views.py:41-44、approval/views.py:220-221、content/views_member.py:14-15、scripts/themes/build.mjs:188-191 均存在且内容相符。</criterion>
      <criterion id="J-B-P8" result="SATISFIED">未引入 Docker、未新增依赖、未设计生产环境；仅重建现有前端静态产物。</criterion>
      <condition>A-01（业主代表决议以已截止 REP_VOTE 投票呈现）、A-02（财务分层以 D-RH-03 为准）、A-03（逐角色顺序档案）为非阻断 ASSUMPTION；GROUP_C 按 module_design 的顺序表与 HTTP 契约实现，GROUP_D 按对应 AC 验证。</condition>
      <verification><![CDATA[
python 解析三份文件头：architecture_design/module_design/tech_stack 均为 version=1.0.0 status=APPROVED；
ls 三文件存在；
grep 覆盖表含 REQ-FUNC-366~375；
引用代码行抽查与仓库一致。
      ]]></verification>
    </gate_review>
    <gate_review id="GR-C-001" invocation_id="ocap_role_home-GROUP_C-001" decision="PASS" time="2026-11-25T12:41:08+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_role_home/development/implementation_plan.md" version="1.0.0"/>
        <file path="project_workspace/ocap_role_home/development/code_review_report.md" version="1.0.0"/>
      </reviewed_files>
      <criterion id="J-C-追溯" result="SATISFIED">implementation_plan 需求追溯覆盖 US-354~360 全部 22 条 AC，状态均 DONE；逐条给出实现位置（Home.vue/index.vue 的 profile、bodyModules、loadRepVotes、publicFeed 等）。</criterion>
      <criterion id="J-C-自验证" result="SATISFIED">PM 亲跑：`cd frontend &amp;&amp; npm run build -- --base=/ocap/` → “✓ built in 8.90s”；`npx vitest run` → 57 files / 607 tests passed；`cd miniprogram &amp;&amp; UNI_INPUT_DIR=. npx uni build -p mp-weixin --outDir /tmp/mp-dist` → “DONE Build complete.”；`npm test` → 22 files / 154 tests passed。</criterion>
      <criterion id="J-C-范围" result="SATISFIED">`git diff --stat -- frontend/src frontend/tests miniprogram/pages miniprogram/store miniprogram/tests` 为 18 files / +536 −293；无后端、依赖、路由、数据库改动；未见无关文件。</criterion>
      <criterion id="J-C-偏差" result="SATISFIED">3 条偏差均在 implementation_plan「架构偏差」登记：DEV-1 Hero 占位、DEV-2 小程序管理快捷仅两项、DEV-3 小程序构建需 UNI_INPUT_DIR（既有工程布局）。</criterion>
      <criterion id="J-C-缺陷" result="SATISFIED">CRITICAL 0；MAJOR 1 已修复（数据加载改 allSettled）；MINOR 3（修复 2，遗留 1 为两端顺序常量漂移风险，已由 ADR-200 接受并下传 GROUP_D）。</criterion>
      <criterion id="J-C-测试调整" result="SATISFIED">13 个既有 spec 的调整均因新行为（删除统计卡/宫格、标题与文案变化、任务 0 隐藏）而必要，逐条原因见 code_review_report「现有测试调整」。</criterion>
      <condition>D-RH-01 不展示参与率、D-RH-02 内容类保留空态/任务类 0 隐藏、D-RH-03 游客只看合计，均已在代码与测试中落实。A-01~A-03 假设继续下传 GROUP_D。</condition>
      <verification><![CDATA[
三份实现/评审文档存在且文件头 version=1.0.0 status=APPROVED；
前端 build 与 607 项测试通过；小程序 build 与 154 项测试通过；
git diff 范围限定在两端前端源码与既有测试。
      ]]></verification>
    </gate_review>
    <gate_review id="GR-D-001" invocation_id="ocap_role_home-GROUP_D-001" decision="PASS" time="2026-11-25T13:06:00+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_role_home/testing/test_plan.md" version="1.0.0"/>
        <file path="project_workspace/ocap_role_home/testing/unit_test_report.md" version="1.0.0"/>
        <file path="project_workspace/ocap_role_home/testing/integration_test_report.md" version="1.0.0"/>
        <file path="project_workspace/ocap_role_home/testing/e2e_test_report.md" version="1.0.0"/>
      </reviewed_files>
      <criterion id="J-D-复跑" result="SATISFIED">PM 亲跑：`cd frontend &amp;&amp; npx vitest run` → Test Files 58 passed (58) / Tests 613 passed (613)；`cd miniprogram &amp;&amp; npm test` → 23 passed (23) / 157 passed (157)。定向复核：`npx vitest run tests/home_role.spec.js tests/layout_contract.spec.js` → 12 passed；`npx vitest run tests/home_role.spec.js tests/approval_flow_contract.spec.js` → 6 passed。与报告摘要逐字一致。</criterion>
      <criterion id="J-D-分层阈值" result="SATISFIED">判定模式 baseline（零新增失败）：unit 18/18、integration 9/9、e2e 替代 9/9，均 100%，三层门控 PASSED；全量相对基线（57/607、22/154）新增失败 0。</criterion>
      <criterion id="J-D-故事覆盖" result="SATISFIED">test_plan「故事覆盖核对」6 个 Must Have 故事（US-354~359）均有已执行用例，无空行：354→TC-WEB-601/TC-INT-601，355→TC-WEB-604，356→TC-WEB-501/916/605/TC-INT-603，357→TC-WEB-602/606，358→TC-WEB-603/017，359→TC-WEB-603/606。</criterion>
      <criterion id="J-D-契约" result="SATISFIED">多客户端契约存在且复跑通过：`frontend/tests/layout_contract.spec.js` 6/6（本次补充 `/approval/tasks`、`/polls`、`/polls/{id}`、`/ledger/accounts/summary`、`/info/posts` 全部解析到 `backend/**/urls.py`）；小程序 `approval_flow_contract.spec.js` 3/3。后端全解析用例 `test_frontend_contract.py` 因本机未安装 Django 标 BLOCKED（环境），已在集成报告与人工清单 M-04 登记。</criterion>
      <criterion id="J-D-基线归因" result="SATISFIED">报告逐条说明 13 个既有 spec 的调整均因新行为（删统计卡/宫格、标题文案、任务 0 隐藏），非新增失败；CR-004 的常量漂移风险由 TC-WEB-603/604/606 与 TC-INT-601/603 双向锁定，本轮未发现漂移。</criterion>
      <criterion id="J-D-证据" result="SATISFIED">四份报告均含命令与输出尾部，计数行来自 13:03:56 最后一次 Web 全量与 12:56:37 小程序全量；报告 mtime（13:00~13:04）晚于测试文件 mtime（home_role ≤12:59:20、layout_contract 12:52、MP 12:48）。</criterion>
      <criterion id="J-D-范围" result="SATISFIED">`git status --short` 仅见 frontend/tests、miniprogram/tests 与 testing/ 文档变更；未修改产品代码、后端、依赖或数据库。</criterion>
      <condition>人工清单 M-01（三主题 ≥768px 无横向溢出）、M-02（小程序单列与 Tab 外观）、M-03（DEV-2 小程序管理快捷两项）、M-04（测试环境补跑后端契约）。A-01~A-03 假设与 CR-004 MINOR 风险继续下传 GROUP_E1；E2 仍为 NOT_AUTHORIZED。</condition>
      <verification><![CDATA[
cd frontend && npx vitest run → 58 files / 613 tests passed
cd miniprogram && npm test → 23 files / 157 tests passed
cd frontend && npx vitest run tests/home_role.spec.js tests/layout_contract.spec.js → 12 passed
cd miniprogram && npx vitest run tests/home_role.spec.js tests/approval_flow_contract.spec.js → 6 passed
ls -l --time-style=full-iso：报告 13:00–13:04，测试文件 ≤12:59:20
      ]]></verification>
    </gate_review>
    <gate_review id="GR-E1-001" invocation_id="ocap_role_home-GROUP_E1-001" decision="PASS" time="2026-11-25T13:07:15+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_role_home/deployment/cicd_pipeline.md" version="1.0.0"/>
        <file path="project_workspace/ocap_role_home/deployment/deployment_plan.md" version="1.0.0"/>
      </reviewed_files>
      <criterion id="J-E1-输入" result="SATISFIED">架构/模块/技术栈/实施计划与三份测试报告均 1.0.0 APPROVED；GROUP_D = APPROVED、GR-D-001 PASS，满足测试门控后才产出部署计划。</criterion>
      <criterion id="J-E1-环境与策略" result="SATISFIED">只列画像 P7 存在的测试环境（树莓派 nginx 8090 / frp 443）；不存在生产环境故无晋升；策略 recreate（前端静态目录原子替换），理由为单实例、无后端/数据变更，预计停机 0–5 秒。</criterion>
      <criterion id="J-E1-CI" result="SATISFIED">沿用现有 3 个 CI job，本次无新依赖/新测试层/新环境变量，新增用例由既有 vitest 自动收集，结论“无需修改 CI”；已注明 CI 仅在 `main` 触发（用户合并）与“CI 未构建小程序”的既有缺口及处理方式。</criterion>
      <criterion id="J-E1-步骤与回滚" result="SATISFIED">DEPLOY-001~005 与 ROLLBACK-001~005 一一对应且逆序；依赖顺序 构建→打包→上传→解包→替换；回滚为可执行命令，未使用 `git reset --hard`/`git clean`/`git stash`，只清理自建的 `ocap.new`、临时 tar 与本地 dist，不触碰 `.env`、`venv`、`var`。</criterion>
      <criterion id="J-E1-预检与验证" result="SATISFIED">预检含提交已推送到远端（用户执行）、回滚锚点目录快照及文件数、本地状态哈希、磁盘、构建工具、制品文案与引用完整性、小程序构建验证、变更范围与授权核对；部署后 V-01~V-10 含内/外网可达、制品版本、后端存活、日志无新错误、本地状态未变与三类账号人工核对。</criterion>
      <criterion id="J-E1-不可逆" result="SATISFIED">目标环境无不可逆步骤（无迁移、无重启、无数据写入）；小程序上传发布明确排除并提示外部可见；旧目录保留 7 天由用户确认清理。</criterion>
      <criterion id="J-E1-证据" result="SATISFIED">PM 复核：`node scripts/themes/build.mjs --strict --check` 退出码 0；`VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` → `✓ built in 9.16s`；产物关键词命中 3 个 JS 文件。未连接目标环境、未执行任何部署命令。</criterion>
      <criterion id="J-E1-范围" result="SATISFIED">未修改 CI 配置与产品代码；仅新增 deployment/ 两份计划文档；无凭据写入。</criterion>
      <condition>E2（PHASE_11b）保持 NOT_AUTHORIZED：必须由用户当轮明确授权“测试环境”部署，PM 将授权写入 invocation `special_instructions` 后才能执行；人工 V-09（三类账号首屏核对）与 M-01/M-02 视觉核对需用户参与。</condition>
      <verification><![CDATA[
node scripts/themes/build.mjs --strict --check → THEME_EXIT=0
cd frontend && VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/ → ✓ built in 9.16s
grep 关键词 frontend/dist/assets/*.js → 3 个文件命中
      ]]></verification>
    </gate_review>
    <gate_review id="GR-E2-001" invocation_id="ocap_role_home-GROUP_E2-001" decision="FAIL" time="2026-11-25T13:21:30+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_role_home/deployment/deployment_report.md" version="1.0.0"/>
      </reviewed_files>
      <criterion id="E2-授权核对" result="SATISFIED">报告中记录了用户条件授权来源、CI run 45552545821 success（headSha 5a787ec）、授权环境名与画像 P7/计划环境名一致、计划版本 1.0.0 APPROVED；授权判定成立。</criterion>
      <criterion id="E2-预检" result="FAILED">内网 192.168.31.51:22 与直连外网 47.109.197.217:57279 均连接超时；经沙箱 HTTP 代理 CONNECT 可建立 TCP 并收到 SSH banner，但 ssh banner 交换超时；沙箱无 SSH 私钥、无 ssh-agent，无法完成 publickey 认证。</criterion>
      <criterion id="E2-无变更" result="SATISFIED">预检阶段停止，未上传、未创建锚点/暂存目录、未改 nginx、未重启服务；目标机无变更，无需回滚。</criterion>
      <criterion id="E2-报告" result="SATISFIED">deployment_report.md 1.0.0 含摘要、授权核对、分步执行、验证结果、回滚记录、当前系统状态与人工干预建议；未执行的步骤未标 SUCCESS；无凭据。</criterion>
      <condition>最终状态 DEPLOYMENT_FAILED。重试需用户二选一：提供授权本次使用的部署私钥并确认外网通道可完成 SSH 握手，或由用户在具备内网/密钥的机器上按 deployment_plan.md 手工执行；重试前确认授权仍然有效。代码已合并到 main（5a787ec）且 CI 全绿，测试环境仍为旧版本。</condition>
      <verification><![CDATA[
gh run view 45552545821 → conclusion=success；三 job success；headSha=5a787ecc648aac2336b36cbfe5aa599ba1202956
ssh 192.168.31.51:22 → Connection timed out
ssh 47.109.197.217:57279（直连）→ Connection timed out
nc -X connect -x 127.0.0.1:18080 47.109.197.217 57279 → SSH-2.0-OpenSSH_10.0p2 Debian-7（TCP 可达，认证不可用）
ls /root/.ssh → 空；ssh-add -l → 无 agent；未发现可用私钥
      ]]></verification>
    </gate_review>
    <gate_review id="GR-E2-002" invocation_id="ocap_role_home-GROUP_E2-002" decision="PASS" time="2026-11-25T14:19:00+08:00">
      <reviewed_files>
        <file path="project_workspace/ocap_role_home/deployment/deployment_report.md" version="1.1.0"/>
      </reviewed_files>
      <criterion id="E2-执行" result="SATISFIED">沙箱 SSH 不可用，用户登录树莓派按 PM 提供的命令执行；构建 `✓ built in 14.96s`、`KEY_HITS=3`、`SWAP_OK`、`NEW_FILES=87`、`ENV_UNCHANGED`，入口由 `index-DmL9mAdT.js` 变为 `index-CmQu6zIY.js`。</criterion>
      <criterion id="E2-验证" result="SATISFIED">`IN_HTTP=200`、`ASSET_HTTP=200`、`SPA_HTTP=200`、`OUT_HTTP=200`、`FREARK_HTTP=200`；`ocap-backend` 与 `nginx` 均 active。</criterion>
      <criterion id="E2-锚点" result="SATISFIED">回滚锚点 `TS=20261125134950`，快照 `/home/yangyang/ocap/snapshots/web-20261125134950.tar.gz` 40 MB / 4009 条目，替换前创建；报告含可执行回滚命令。</criterion>
      <criterion id="E2-范围" result="SATISFIED">仅替换 `/home/yangyang/ocap/web/ocap`；`.env` 哈希前后一致；后端未重启、无迁移、nginx 配置未改；Freeark 外网入口 200。</criterion>
      <criterion id="E2-报告" result="SATISFIED">deployment_report.md 1.1.0 记录首次失败（无变更）、第二次分步执行、V-01~V-09、回滚方式与遗留问题；无凭据。</criterion>
      <condition>V-09（三类账号角色化首屏人工核对）待用户执行；小程序上传发布不在范围；沙箱到目标机 SSH 通道仍需修复后才能全自动 E2。</condition>
      <verification><![CDATA[
Node v22.22.2 / npm 10.9.7 / 可用 14G
✓ built in 14.96s；KEY_HITS=3；BUILD_OK
SNAPSHOT 40M / 4009 条目；SWAP_OK；NEW_FILES=87；ENV_UNCHANGED
/ocap/assets/index-CmQu6zIY.js
IN_HTTP=200 ASSET_HTTP=200 SPA_HTTP=200 OUT_HTTP=200 FREARK_HTTP=200
ocap-backend=active nginx=active
DEPLOYED TS=20261125134950
      ]]></verification>
    </gate_review>
  </gate_reviews>
  <clarifications>
    <clarification id="Q-RH-OPEN" status="RESOLVED">用户 2026-11-25 决策：Q-RH-01 不展示参与率；Q-RH-02 不隐藏（公开类保留空态，任务类仍 0 隐藏）；Q-RH-03 游客只看账户合计与报表入口。见需求的决策记录 D-RH-01~03。</clarification>
  </clarifications>
  <checkpoints/>
  <escalations/>
  <audit_log>
    <event time="2026-11-25T12:03:24+08:00" type="RUN" actor="pm-orchestrator">主会话模式（用户直接指令 “Use Skill: sdlc-orchestrator 按照上述的方案，开始整理需求，拆分用户故事。我确认后开始开发。”）。已读 sdlc-orchestrator、project_profile 1.3.0；preflight --check-all → PREFLIGHT_OK profile=APPROVED。建立增量工作区 project_workspace/ocap_role_home/，用户要求 GROUP_A 后停等确认。</event>
    <event time="2026-11-25T12:09:30+08:00" type="GATE" actor="pm-orchestrator">GR-A-001 决策 PASS；requirements_spec 与 user_stories 1.0.0 APPROVED；10 功能 / 1 非功能 / 0 INFERRED；7 故事 / 20 AC / 27 点；开放问题 Q-RH-01~03 非阻断。</event>
    <event time="2026-11-25T12:10:00+08:00" type="CHECKPOINT" actor="pm-orchestrator">按用户要求停在 GROUP_A：等待用户确认需求与故事后再进入 GROUP_B/C。GROUP_B~E 保持 PENDING，E2 NOT_AUTHORIZED。</event>
    <event time="2026-11-25T13:22:00+08:00" type="GATE" actor="pm-orchestrator">用户确认 Q-RH-01~03；定向修订 requirements_spec / user_stories 至 1.0.1；GR-A-002 PASS；开放问题全部 RESOLVED。用户指令“开始 sdlc 开发流程”。</event>
    <event time="2026-11-25T12:19:30+08:00" type="INVOCATION" actor="system-architect">ocap_role_home-GROUP_B-001 完成：8 个 ADR（2 decision / 6 constraint-driven）、5 个 MOD、9 个前端 IFC + 8 个复用 HTTP 接口；无数据迁移；影响 Web 构建、主题生成与小程序构建。产出三份 0.1.0 DRAFT。</event>
    <event time="2026-11-25T12:19:30+08:00" type="GATE" actor="pm-orchestrator">GR-B-001 PASS；architecture_design / module_design / tech_stack 升为 1.0.0 APPROVED；GROUP_B 完成，进入 GROUP_C。A-01~A-03 作为非阻断假设随开发下传。</event>
    <event time="2026-11-25T12:40:30+08:00" type="INVOCATION" actor="software-developer">ocap_role_home-GROUP_C-001 完成：MOD-215/216/217/218/219 全部 DONE；18 个前端源码/测试文件改动 +536/−293；无后端/依赖/路由/迁移变更；3 条架构偏差已登记。产出 implementation_plan 与 code_review_report 0.1.0 DRAFT。</event>
    <event time="2026-11-25T12:41:08+08:00" type="GATE" actor="pm-orchestrator">GR-C-001 PASS；两份开发文档升为 1.0.0 APPROVED；PM 亲跑 Web 构建 + 607 项测试、小程序构建 + 154 项测试均通过；GROUP_C 完成，进入 GROUP_D。</event>
    <event time="2026-11-25T13:04:30+08:00" type="INVOCATION" actor="test-engineer">ocap_role_home-GROUP_D-001 完成：新增 Web TC-WEB-601~606、小程序 TC-INT-601~603，扩展契约用例覆盖首页 5 组调用；三层均 PASSED；全量 58/613、23/157，零新增失败；无产品缺陷；backend 契约用例因缺 Django BLOCKED。产出四份 0.1.0 DRAFT。</event>
    <event time="2026-11-25T13:06:00+08:00" type="GATE" actor="pm-orchestrator">GR-D-001 PASS；test_plan 与三份测试报告升为 1.0.0 APPROVED；critical path 替代口径覆盖 6/6 Must Have 故事；GROUP_D 完成，进入 GROUP_E1（E2 保持 NOT_AUTHORIZED）。</event>
    <event time="2026-11-25T13:07:00+08:00" type="INVOCATION" actor="devops-engineer">ocap_role_home-GROUP_E1-001 完成：现有 CI 无需修改；产出 cicd_pipeline.md 与 deployment_plan.md（recreate 静态替换、DEPLOY/ROLLBACK 各 5 步、目标环境无不可逆步骤）；未连接或修改任何目标环境，等待用户部署授权。</event>
    <event time="2026-11-25T13:07:20+08:00" type="GATE" actor="pm-orchestrator">GR-E1-001 PASS；两份部署文档升为 1.0.0 APPROVED；PM 复核主题校验退出码 0、构建 9.16s、制品关键词命中 3 个 JS；GROUP_E1 完成；E2 仍为 NOT_AUTHORIZED，需用户当轮明确授权测试环境部署。</event>
    <event time="2026-11-25T13:09:00+08:00" type="DECISION" actor="user">用户选择暂不部署：先由用户提交/推送并合并到 main，待 CI 全绿后再单独授权测试环境部署；GROUP_E2 保持 NOT_AUTHORIZED。</event>
    <event time="2026-11-25T13:17:30+08:00" type="RUN" actor="pm-orchestrator">用户新指令：提交并推送代码，等待 CI 通过后授权部署到测试环境。代码已在本地提交 5a787ec，快进推送 origin/main（9a754e4..5a787ec）。</event>
    <event time="2026-11-25T13:20:00+08:00" type="DEPLOY_AUTH" actor="user">条件授权：CI 通过后部署到测试环境。证据：GitHub Actions run 45552545821 conclusion=success，headSha=5a787ec；授权环境名=测试环境，与画像 P7 及 deployment_plan 一致。</event>
    <event time="2026-11-25T13:21:20+08:00" type="EXCEPTION" actor="devops-engineer">E2 预检失败：沙箱无内网路由（192.168.31.51:22 超时）、无 SSH 私钥/agent；外网 47.109.197.217:57279 仅可经 HTTP 代理建立 TCP 并收到 SSH banner，无法完成认证。目标机未发生任何变更，DEPLOYMENT_FAILED，无需回滚。</event>
    <event time="2026-11-25T14:13:00+08:00" type="INVOCATION" actor="devops-engineer">ocap_role_home-GROUP_E2-002 成功：用户在树莓派代执行 PM 提供的命令；构建 5a787ec、快照 20261125134950、替换 web/ocap、内网/外网验证全部 200；最终 DEPLOYED_SUCCESSFULLY。</event>
    <event time="2026-11-25T14:19:00+08:00" type="GATE" actor="pm-orchestrator">GR-E2-002 PASS；deployment_report.md 升为 1.1.0 APPROVED；GROUP_E2/PHASE_11b 完成；V-09 人工核对待用户执行，其余 SDLC 阶段结束。</event>
    <event time="2026-11-25T14:26:00+08:00" type="INVOCATION" actor="kb-curator">PHASE_12：处理 ocap_role_home 11 条经验，晋升 8 / 合并 2；日志 349 条 committed；历史积压 71 条保留待下次处理。</event>
  </audit_log>
</phase_status>
