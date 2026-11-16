<phase_status project="ocap_owner_auth_v2" mode="INCREMENTAL" created="2026-11-16T16:37:13+08:00" updated="2026-11-16T22:17:55+08:00">
  <request time="2026-11-16T16:37:13+08:00"><![CDATA[新的变更需求：1. 用户登录后，在我的房屋进行产权认证， 选择房屋，然后再楼栋的下拉菜单中产权车位排到最后。它应该派代1-10栋之后。 然后所有类型是商铺的，也应该提取出来，楼栋里面现实商铺。包括那些只有门牌号，没有单元信息的商铺，一起组织一下结构，让第一层楼栋选择非常整洁： 住宅的10个楼栋，地下车位，商铺 三大类就可以了。同时也要反向生成批量导入文件，保存在服务器上，我以后有用。 2.管理员登录管理后台后，在申述页面只能看到用户的id， 和要申述的专有部分坐落。我希望能有现实申述的编码，申述人的账号，姓名，申述的时候要提交产权人名字。，申述的时间，以及提交资料的缩略图。点开就能看到弹出的图片。2。 如果用户登录阿仔我的房屋认证产权，除了选择楼栋，单元漏乘，户号以外，还要输入姓名。只有姓名、绑定的手机号和业主清册上这个业主信息对应的时候，才会自动绑定。如果不一致就导入到申述的流程上传资料。 特别是微信一键登录没有取得手机号码的，只输入名字，那就必须要上传产权证明。 一旦申诉成功，认证3为业主的，就需要把对应的新的产权人名字，联系电话更新到业主清册中。3. 如果一个业主已经认证了一个专有部分，并绑认证绑定了手机号码（不管是微信登录后绑定，还是直接用手机号注册）。那么他认证第二个部分的时候，如果手机号和第二个部分不一致，（第二个专有部分没有记录手机号、或者是一个别的号码）那么就以新的号码为准，更新业主清册的数据。4.管理员在登录管理后台后， 在业委会席位，授予席位时，不应该以授予时间早于当前作为限制，只要未来还有任期，就可以授予。  先整理需求，确认逻辑没有问题，然后梳理用户故事让我确认。]]></request>
  <request_context><![CDATA[PM 只读核查（2026-11-16T16:37:13+08:00）：
- 测试库清册按楼栋×类型（只读计数，无个人信息）：1栋~10栋 为 住宅/公寓，其中 1、2、5、6、9、10 栋另有商铺 14/14/13/8/14/16 条（共 79）；另有 27 个门牌型楼栋（如 建设南路142号、枫林路124号附1号、未标注A/B、建设南路176号6栋、枫林路140号1栋）各 1~2 条商铺（共 28）；地下车位 1391 条车位。商铺共 107 条，单元全部为空。
- 上一批 ocap_unit_sort_filters 用户决定 id=4347（1栋负1层1139号，商铺）保留在 1栋下（phase_status clarifications）；本批"所有商铺提取"与之相关。
- 现行楼栋排序（backend/apps/registry/ordering.py）：数字楼栋 → 文字楼栋 → 地下车位最后。
- 后台申诉页 frontend/src/admin/AdminAppeals.vue：状态筛选 + 列表，有通过/拒绝按钮与附件链接（:27 el-link 文件名）；Appeal 模型 backend/apps/residency/models.py:31-41（user、unit、status、submitted_at、decided_*、reject_reason），无"产权人姓名"字段。
- 产权认证：backend/apps/residency/services.py:45 certify_owner；清册匹配按手机号（RegistryService.phone_registered / units_by_phone）。
- 席位授予：backend/apps/committee/views.py:66-67 "任期开始日不得早于今天"。
- 导出命令 export_registry_import_file 已存在（上一批），可只读导出导入文件。]]></request_context>
  <profile version="1.5.0"/>
  <workspace_note>独立增量项目，文档在 project_workspace/ocap_owner_auth_v2/（nested）。用户要求：先整理需求、确认逻辑无问题，再梳理用户故事确认；本轮只做 PHASE_01。</workspace_note>
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
    <artifact path="project_workspace/ocap_owner_auth_v2/requirements/requirements_spec.md" version="0.1.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/requirements/requirements_spec.md" version="0.2.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/requirements/requirements_spec.md" version="1.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/requirements/user_stories.md" version="0.1.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/requirements/user_stories.md" version="1.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/architecture/architecture_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/architecture/module_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/architecture/tech_stack.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/development/implementation_plan.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/development/code_review_report.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/testing/test_plan.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/testing/unit_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/testing/integration_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/testing/e2e_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/deployment/cicd_pipeline.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/deployment/deployment_plan.md" version="1.0.0" status="APPROVED" group="GROUP_E1"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/deployment/deployment_report.md" version="1.0.0" status="SUPERSEDED" group="GROUP_E2"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/deployment/deployment_report.md" version="2.0.0" status="SUPERSEDED" group="GROUP_E2"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/deployment/deployment_report.md" version="3.0.0" status="APPROVED" group="GROUP_E2"/>
    <artifact path="project_workspace/ocap_owner_auth_v2/delivery_report.md" version="1.0.0" status="APPROVED" group="PM"/>
  </artifacts>
  <legacy_baseline/>
  <invocations>
    <invocation id="ocap_owner_auth_v2-GROUP_A-001" agent="requirement-analyst" result="SUCCESS" end="2026-11-16T16:43:54+08:00" start="2026-11-16T16:37:13+08:00"/>
  <invocation id="ocap_owner_auth_v2-GROUP_A-002" agent="requirement-analyst" result="SUCCESS" end="2026-11-16T17:16:22+08:00" start="2026-11-16T17:11:54+08:00"/>
  <invocation id="ocap_owner_auth_v2-GROUP_B-001" agent="system-architect" result="SUCCESS" end="2026-11-16T18:03:34+08:00" start="2026-11-16T17:49:19+08:00"/>
  <invocation id="ocap_owner_auth_v2-GROUP_C-001" agent="software-developer" result="PARTIAL_SUCCESS" end="2026-11-16T18:41:15+08:00" start="2026-11-16T18:03:34+08:00"/>
  <invocation id="ocap_owner_auth_v2-GROUP_D-001" agent="test-engineer" result="PARTIAL_SUCCESS" end="2026-11-16T19:20:14+08:00" start="2026-11-16T18:41:15+08:00"/>
  <invocation id="ocap_owner_auth_v2-GROUP_E1-001" agent="devops-engineer" result="SUCCESS" end="2026-11-16T19:30:54+08:00" start="2026-11-16T19:22:21+08:00"/>
  <invocation id="ocap_owner_auth_v2-GROUP_E2-001" agent="devops-engineer" result="SUCCESS" end="2026-11-16T19:47:10+08:00" start="2026-11-16T19:35:01+08:00"/>
  <invocation id="ocap_owner_auth_v2-GROUP_E2-002" agent="devops-engineer" result="SUCCESS" end="2026-11-16T21:59:32+08:00" start="2026-11-16T21:37:39+08:00"/>
  <invocation id="ocap_owner_auth_v2-GROUP_E2-003" agent="devops-engineer" result="SUCCESS" end="2026-11-16T22:08:09+08:00" start="2026-11-16T22:01:57+08:00"/>
  <invocation id="ocap_owner_auth_v2-GROUP_Z-001" agent="kb-curator" result="SUCCESS" end="2026-11-16T22:11:23+08:00" start="2026-11-16T22:08:37+08:00"/>
  </invocations>
  <gate_reviews>
    <gate_review id="GR-A-001" invocation_id="ocap_owner_auth_v2-GROUP_A-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T16:43:54+08:00">
      <reviewed_files><file path="project_workspace/ocap_owner_auth_v2/requirements/requirements_spec.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-A 来源" result="SATISFIED">抽查：accounts/models.py:20 仅 nickname（无实名）属实；committee/services.py:31-34 active_seat 仅看 term_end 属实；residency/auto_bind.py 存在；committee/views.py:66-67 属实。</criterion>
      <criterion id="J-A INFERRED" result="SATISFIED">2/19=10.5%。</criterion>
      <criterion id="J-A 无技术实现" result="SATISFIED">代码位置仅在基线与来源。</criterion>
      <criterion id="J-A 逻辑核查" result="SATISFIED">"逻辑问题与冲突" L-01~L-24，开放问题 Q-OA-01~26 均带推荐项；3 个阻断（Q-OA-01/02/12）。</criterion>
      <finding id="GR-A-001-F01" severity="MINOR">ocap 基线 requirements_spec 仅 grep 相关行（notes 自述），产出未见出错。</finding>
      <finding id="GR-A-001-F02" severity="MINOR">Q-OA-26 部分可由 PM 已有只读计数回答（107 条商铺均 SHOP、无"商铺"楼栋、门牌型楼栋全为商铺、单元全空），定稿时并入。</finding>
      <condition>用户答复 Q-OA-01/02/12（阻断）及其他问题后 RA 定稿 0.2.0 并写 PHASE_02 用户故事。</condition>
    </gate_review>
    <gate_review id="GR-A-002" invocation_id="ocap_owner_auth_v2-GROUP_A-002" decision="PASS_WITH_CONDITIONS" time="2026-11-16T17:16:22+08:00">
      <reviewed_files><file path="project_workspace/ocap_owner_auth_v2/requirements/requirements_spec.md" version="0.2.0"/><file path="project_workspace/ocap_owner_auth_v2/requirements/user_stories.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-A G/W/T" result="SATISFIED">79 条 AC，grep Given=79；US-193~206。</criterion>
      <criterion id="J-A INFERRED" result="SATISFIED">1/20=5%（REQ-NFUNC-035 审计日志）。</criterion>
      <criterion id="J-A 来源" result="SATISFIED">抽查 committee/services.py ALREADY_SEATED/CAP_REACHED（:107、:113）存在；用户答复已映射到"已决问题"表。</criterion>
      <finding id="GR-A-002-F01" severity="MINOR">ocap 基线 requirements_spec 仍未通读（部分行截断，notes 自述）。</finding>
      <condition>用户确认故事与 Q-OA-27/28 后批准 1.0.0；Q-OA-29 数据核对随 B 段只读授权执行。</condition>
    </gate_review>
    <gate_review id="GR-B-001" invocation_id="ocap_owner_auth_v2-GROUP_B-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T18:03:34+08:00">
      <reviewed_files><file path="project_workspace/ocap_owner_auth_v2/architecture/architecture_design.md" version="0.1.0"/><file path="project_workspace/ocap_owner_auth_v2/architecture/module_design.md" version="0.1.0"/><file path="project_workspace/ocap_owner_auth_v2/architecture/tech_stack.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-B 覆盖" result="SATISFIED">需求覆盖表 REQ-FUNC-185~200 无空行（agent 自检 + PM 抽看）。</criterion>
      <criterion id="J-B ADR" result="SATISFIED">ADR-106~116：Status 11、Options 11。</criterion>
      <criterion id="J-B 小节" result="SATISFIED">module_design.md:420 数据迁移、:440 受影响的运行单元。</criterion>
      <criterion id="J-B 引用真实" result="SATISFIED">git grep "term_end__gte|term_end >=" = 6 处，与设计一致；registry/models.py:23-31 _segment 纯数字补后缀属实（支撑 OQ-01）；core/attachments.py:112-132 无权返回 NotFound 属实；residency 迁移现止于 0002（新 0003 合理）。</criterion>
      <criterion id="J-B P8" result="SATISFIED">无新依赖（缩略图客户端降采样，不加 Pillow）；改库为独立命令、不进部署。</criterion>
      <finding id="GR-B-001-F01" severity="MINOR">引用 test_rework_cr011_024.py:376 处为管理员下载 200 断言，并非"无关用户 404"断言，GROUP_C 须自行 grep 定位受 OQ-07 影响的断言。</finding>
      <finding id="GR-B-001-F02" severity="MINOR">OQ-06（小程序申诉资料本批仅图片，偏离 AC-201-01 的 pdf）、OQ-01（纯数字楼栋补"栋"）、OQ-04（席位开始日上界 5 年）为设计假设，需用户确认；先按设计实现。</finding>
      <condition>GROUP_C：既有测试因口径变更失效的断言（约 15 处 PHONE_NOT_IN_REGISTRY、ordering、TC-INT-472、miniprogram api.spec.js:90、OQ-07）仅最小同步并逐条登记；remote 用例同步 name/owner_name；E1 须注明小程序发布不在画像 P7 内，需用户手动发布。</condition>
    </gate_review>
    <gate_review id="GR-C-001" invocation_id="ocap_owner_auth_v2-GROUP_C-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T18:41:15+08:00">
      <reviewed_files><file path="project_workspace/ocap_owner_auth_v2/development/implementation_plan.md" version="0.1.0"/><file path="project_workspace/ocap_owner_auth_v2/development/code_review_report.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-C MOD 实现" result="SATISFIED">新建 committee/effective.py、registry/{shops,ownership}.py、relocate_shops 命令、residency 0003 迁移、ProofThumbs.vue；修改 20 个产品文件，与 implementation_plan 一致。</criterion>
      <criterion id="J-C 追溯抽查" result="SATISFIED">US-193（ordering.py RESERVED_BUILDINGS 地下车位1/商铺2/其他3）、US-195（shops.py:75/83/146/199）、US-200（residency/views.py:62-74 name 必填、owner_matches(unit,name,user.phone)、OWNER_NOT_MATCHED）、US-203（ownership.py:51 append_owner_from_appeal）、US-205/206（committee/effective.py effective_q）均与代码相符。</criterion>
      <criterion id="J-C 迁移 P6" result="SATISFIED">0003_appeal_owner_name.py 手写（首行注释，无 Generated by Django），SD 自证可逆。</criterion>
      <criterion id="J-C PM 复跑" result="SATISFIED">后端 822：821 OK + 1 FAIL（TC-INT-611，环境性既有失败：断言仓库根不存在 registry_import_underground_parking.xlsx，而该文件为用户经授权取回并保留的导出文件，与本批代码无关）；前端 259/259、构建通过；小程序 97/97。相对基线零新增产品失败。</criterion>
      <criterion id="J-C 客户端" result="SATISFIED">P4 规定的前端 vitest+build、小程序 vitest 均通过；小程序 build:mp-weixin 为既有工具链问题（M-SD-006），不在 P4 命令中。</criterion>
      <verification><![CDATA[venv Python 3.12.3 + Django 5.2.19
(cd backend && manage.py check) -> System check identified no issues (0 silenced).
(cd backend && manage.py test --settings=config.test_settings) -> Ran 822 tests / FAILED (failures=1)：仅 test_tc_int_611（仓库根存在被忽略的导出文件）
(cd frontend && npx vitest run --passWithNoTests) -> 25 files / 259 passed；npm run build -- --base=/ocap/ -> built in 42.36s
(cd miniprogram && npx vitest run --passWithNoTests) -> 14 files / 97 passed]]></verification>
      <finding id="GR-C-001-F01" severity="MAJOR">TC-INT-611（上批 test-engineer 所写）依赖仓库根状态，与用户保留在仓库根的导出文件冲突，属测试缺陷；GROUP_D 修正为只断言"本次运行未在仓库根产生新文件"（如运行前后比对），不得删除用户文件。</finding>
      <finding id="GR-C-001-F02" severity="MAJOR">R-01：remote TC-E2E-337 对测试环境真实房屋提交并通过申诉，本批起会向真实清册追加产权人，越出画像 P4-1；GROUP_D 须改为不越界（不执行通过步骤或标 NOT_TESTABLE 并写人工验证清单），本批未运行 remote。</finding>
      <finding id="GR-C-001-F03" severity="MINOR">小程序无法在开发机构建（既有）；E1 须写明小程序由用户在 HBuilderX/微信开发者工具构建并手动发布，旧版小程序认证将收到 400。</finding>
      <condition>GROUP_D：处理 F01、F02；为 MOD-111~118 补全新测试（商铺改库全路径、导出守卫、认证四种失败响应一致、申诉追加清册与回滚、附件 403/401、席位 effective 六处调用点、契约含两端 api.js 新字段）；AC-201-01 小程序 pdf 按 OQ-06 记 PARTIAL。</condition>
    </gate_review>
    <gate_review id="GR-D-001" invocation_id="ocap_owner_auth_v2-GROUP_D-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T19:20:14+08:00">
      <reviewed_files><file path="project_workspace/ocap_owner_auth_v2/testing/test_plan.md" version="0.1.0"/><file path="project_workspace/ocap_owner_auth_v2/testing/unit_test_report.md" version="0.1.0"/><file path="project_workspace/ocap_owner_auth_v2/testing/integration_test_report.md" version="0.1.0"/><file path="project_workspace/ocap_owner_auth_v2/testing/e2e_test_report.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-D 复跑一致" result="SATISFIED">PM 复跑：unit 203、integration 675、e2e 61、smoke 6（=945）全部 OK；前端 281；小程序 104；与报告一致。TC-INT-611 已改为不依赖仓库根，现通过。</criterion>
      <criterion id="J-D 故事覆盖" result="SATISFIED">test_plan"故事覆盖核对"含 US-193~206 全部 14 个。</criterion>
      <criterion id="J-D 契约" result="SATISFIED">新增 test_owner_auth_v2_contract.py（TC-INT-709~719）+ 既有 test_frontend_contract.py，契约专项 37 条 OK。</criterion>
      <criterion id="J-D 未越界" result="SATISFIED">remote TC-E2E-337 改为只提交/驳回，并在 remote_client 加护栏（git diff 已核）；未运行 remote；产品代码 diff 仍为 GR-C-001 时的 20 个文件；仓库根用户文件未动（600、336459 字节、mtime 14:00:13）。</criterion>
      <criterion id="J-D 注水" result="SATISFIED">新测试仅 1 处条件 skipTest（非 POSIX 平台，本机不触发）。</criterion>
      <finding id="GR-D-001-F01" severity="MINOR">DEF-024（既有）：席位 term_start 为不存在日期时 500（committee/views.py:63）；不阻塞，列遗留。</finding>
      <finding id="GR-D-001-F02" severity="MINOR">报告文件头时间戳取自略早的 date 输出（agent 自述）。</finding>
      <condition>critical path 待人工验证 4 项（M-01 小程序 pdf=OQ-06 已确认推迟、M-02 浏览器缩略图/预览失败下载入口、M-03 目标机导出目录权限、M-05 真实清册 107 条 dry-run）纳入 E1/E2；最终状态至多 DELIVERED_WITH_ISSUES。</condition>
    </gate_review>
    <gate_review id="GR-E1-001" invocation_id="ocap_owner_auth_v2-GROUP_E1-001" decision="PASS_WITH_CONDITIONS" time="2026-11-16T19:30:54+08:00">
      <reviewed_files><file path="project_workspace/ocap_owner_auth_v2/deployment/cicd_pipeline.md" version="0.1.0"/><file path="project_workspace/ocap_owner_auth_v2/deployment/deployment_plan.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-E1 DEPLOY/ROLLBACK" result="SATISFIED">DEPLOY-001~015 与 ROLLBACK-001~015；MANUAL_ROLLBACK_REQUIRED 标注 9 处（含迁移回退丢 owner_name :226、改库还原）。</criterion>
      <criterion id="J-E1 迁移回滚" result="SATISFIED">0003 为 AddField CharField(blank=True, default="")（NOT NULL）属实；计划要求先 migrate residency 0002 再恢复旧代码（:54、:226）。</criterion>
      <criterion id="J-E1 环境与禁用项" result="SATISFIED">仅测试环境；Freeark nginx 仅备份（:169）、不碰 freeark 服务（:247）；保留上批两份备份（:127 预检核对存在，回滚禁删）。</criterion>
      <criterion id="J-E1 独立授权" result="SATISFIED">A~E 五段；导出目录部署根同级 700/600，留服务器；不可经站点取得以内容类型与大小判定（:371）。</criterion>
      <criterion id="J-E1 无副作用" result="SATISFIED">本机 / 下无新文件；仅写 deployment/ 与自身记忆。</criterion>
      <finding id="GR-E1-001-F01" severity="MINOR">部分输入文件仅读部分章节（notes 自述：test_plan 前 60 行、tech_stack 开头）。</finding>
      <condition>授权 A 前：用户选定小程序发布顺序（推荐 R1）；是否推送 68bc477/c32684b 并核对 CI。</condition>
    </gate_review>
    <gate_review id="GR-E2-001" invocation_id="ocap_owner_auth_v2-GROUP_E2-001" decision="PASS" time="2026-11-16T19:47:10+08:00">
      <reviewed_files><file path="project_workspace/ocap_owner_auth_v2/deployment/deployment_report.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-E2 阶段 A" result="SATISFIED">DEPLOYED_SUCCESSFULLY；ANCHOR_TS=20261116193651；residency_appeal 备份 600；migrate 仅 0003；验证通过 19:39:44（可发布新版小程序）。</criterion>
      <criterion id="J-E2 阶段 B" result="SATISFIED">relocate_shops dry-run：total 5742、shop_units 107、would_change 107、conflicts 0、second_level_values 33；4347→商铺1栋负1层1139号；无个人信息。</criterion>
      <verification><![CDATA[curl https://ai-freeark.xin/ocap/ -> 200，入口 index-8pjlGbdL.js（与报告一致）
curl /ocap/api/v1/admin/appeals -> 401；/ocap/api/v1/units/options -> 401
ssh 只读：ocap-backend active；showmigrations residency -> [X] 0001/0002/0003_appeal_owner_name
目标机 apps/registry/shops.py sha256 前 16 位 900d1cfd72fd8073 = git show c32684b:backend/apps/registry/shops.py
snapshots 下 shops-* 0 个；/home/yangyang/ocap_exports 不存在（阶段 C/D 未执行）]]></verification>
    </gate_review>
    <gate_review id="GR-E2-002" invocation_id="ocap_owner_auth_v2-GROUP_E2-002" decision="PASS" time="2026-11-16T21:59:32+08:00">
      <reviewed_files><file path="project_workspace/ocap_owner_auth_v2/deployment/deployment_report.md" version="1.1.0"/></reviewed_files>
      <criterion id="J-E2 阶段 C" result="SATISFIED">moved=107、lost_origin=0；units 5742 / owners 7862 / phones 4301 / 有效 Membership 3 前后相等；幂等 would_change=0；备份 ocapdb-registry-20261116213837.sql、shops-20261116213837.jsonl 均 600。</criterion>
      <criterion id="J-E2 阶段 D" result="SATISFIED">导出自检 diff_*=0、rows_failed=0、roundtrip_mismatches=0；站点请求返回 SPA index（text/html 1039），不可取得。</criterion>
      <verification><![CDATA[PM 只读 ssh + manage.py shell：
total 5742；building="商铺" 107；"地下车位" 1391
第一级选项：1栋…10栋、地下车位、商铺（共 12 项，三大类）
options(building="商铺") -> level=unit_no，33 项（1栋、2栋、5栋、6栋、9栋、10栋、圣灯路155号、建设南路142号…）
id=4347 -> 商铺 / 1栋 / 负1 / 商铺1栋负1层1139号
stat: 700 /home/yangyang/ocap_exports；600 registry_import_20261116-213927.xlsx；ocap-backend active]]></verification>
    </gate_review>
    <gate_review id="GR-E2-003" invocation_id="ocap_owner_auth_v2-GROUP_E2-003" decision="PASS_WITH_CONDITIONS" time="2026-11-16T22:08:09+08:00">
      <reviewed_files><file path="project_workspace/ocap_owner_auth_v2/deployment/deployment_report.md" version="2.1.0"/></reviewed_files>
      <criterion id="J-E2 阶段 E" result="SATISFIED">远程 Ran 22：19 PASS / 2 FAIL（既有 DEF-B，remote_cases.py:77、114）/ 1 SKIP；本批新增失败 0；TC-E2E-337 只提交/驳回通过；只读补证：第一级 12 项、商铺 33 项、地下车位 负2/负1、/admin/appeals 无令牌 401。</criterion>
      <verification><![CDATA[PM 只读 ssh：OCAP_E2E_FIXTURE=1 manage.py e2e_fixture status -> e2e 全 0；RegistryUnit 5742 / RegistryOwner 7862 / RegistryPhone 4301；ocap-backend active
本机 / 下无残留归档]]></verification>
      <finding id="GR-E2-003-F01" severity="MINOR">认证负例（错误姓名 422 OWNER_NOT_MATCHED、四种失败响应一致）因 remote_client 写白名单不含 POST /certifications 未在目标机验证；本地集成测试已覆盖，列人工验证项。</finding>
      <condition>遗留：DEF-B（远程用例期望"户主"）下批修；remote 护栏是否开放认证负例下批评估；人工项 M-01/M-02/M-06 与认证 422 自测。</condition>
    </gate_review>
  </gate_reviews>
  <clarifications>
    <clarification time="2026-11-16T17:11:54+08:00" answered_by="用户"><![CDATA[用户原话："B1:A, B2:A, B3:B,  其他问题全部按照推荐。"
映射：Q-OA-12=A（取消项 4 自动更新，第二套房与首次认证同规则，申诉通过后更新清册）；Q-OA-01=A（商铺下一级为原楼栋/门牌，再楼层、户号）；Q-OA-02=B（原地改库，楼栋改为"商铺"，标识随之变化，需冲突检查、备份、另行授权）；其余 Q-OA-03~11、13~26 与 I-01~I-10 按★推荐。
PM 注：Q-OA-02=B 时原楼栋/门牌信息须在库内保留以支撑 Q-OA-01=A 的第二级（由设计决定承载方式）；Q-OA-03=A 4347 归入商铺。上一批"本地提交"问题按推荐 A 处理：已提交 68bc477（未推送）。]]></clarification>
    <clarification time="2026-11-16T17:49:19+08:00" answered_by="用户"><![CDATA[用户原话："新问题按照推荐。 故事确认，开始开发"。Q-OA-27=A（导出时原楼栋/门牌写入"单元"列）；Q-OA-28=A（未来起始日席位授予即占名额、阻止重复授予）；REQ-NFUNC-035（审计日志）随故事确认；放行开发（GROUP_B→C→D）。]]></clarification>
    <clarification time="2026-11-16T18:42:39+08:00" answered_by="用户"><![CDATA[用户原话："OQ 全部按推荐"。OQ-01=纯数字楼栋补"栋"；OQ-04=席位开始日上界 5 年；OQ-06=A 小程序申诉本批仅图片，pdf 下批；OQ-07=附件无关用户 403。implementation_plan 开放问题中"待用户确认"均已确认。]]></clarification>
    <clarification time="2026-11-16T19:22:21+08:00" answered_by="用户"><![CDATA[用户原话："Q1:A, Q2:A, Q3 A"。Q1=A 本地提交不推送（c32684b）；Q2=A DEF-024 留下一批；Q3=A 制作测试环境部署计划（仅计划）。]]></clarification>
    <clarification time="2026-11-16T19:33:19+08:00" answered_by="用户"><![CDATA[用户原话："Q1:A, Q2:R1, Q3 授权 A、B 段"。推送并核对 CI；小程序顺序 R1（用户先构建提审、A 验证通过后发布）；授权阶段 A、B。小程序正式版指向哪个后端用户未答。]]></clarification>
    <clarification time="2026-11-16T21:37:39+08:00" answered_by="用户"><![CDATA[用户原话："授权C段 N=107，D也授权"。]]></clarification>
    <clarification time="2026-11-16T22:01:57+08:00" answered_by="用户"><![CDATA[用户原话："小程序没有发布，之前旧的，新的都没有发布。现在是开发测试阶段。如果我发布了我会告诉你。开始E段"。小程序从未正式发布，无存量用户受新后端影响；R1 顺序不再构成过渡期风险。授权阶段 E。本批两份新备份保留期未答。]]></clarification>
    <clarification time="2026-11-16T22:13:19+08:00" answered_by="用户"><![CDATA[用户原话："备份保留到11月23日，所有改动 commit + push"。本批备份 ocapdb-registry-20261116213837.sql、residency_appeal-20261116193651.sql、shops-20261116213837.jsonl 保留至 2026-11-23；全部改动（含 ocap_product_review 3 个旧文件）提交并推送。]]></clarification>
    <clarification time="2026-11-16T22:17:55+08:00" answered_by="用户"><![CDATA[用户原话："人工验证都看了，没问题"。M-02（申诉缩略图/大图）、认证 422 自测、M-06（小程序开发版姓名输入）用户人工核对通过。]]></clarification>
  </clarifications>
  <checkpoints/>
  <escalations/>
  <audit_log>
    <event time="2026-11-16T16:37:13+08:00" type="RUN" actor="pm-orchestrator">主会话模式（用户直接陈述需求，判定规则 3）。新批次 ocap_owner_auth_v2；PM 只读 ssh 统计清册楼栋×类型（无个人信息）。</event>
    <event time="2026-11-16T16:37:13+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（GROUP_A-001，仅 PHASE_01）</event>
    <event time="2026-11-16T16:43:54+08:00" type="GATE" actor="pm-orchestrator">GR-A-001 PASS_WITH_CONDITIONS；等待用户答复逻辑问题。</event>
    <event time="2026-11-16T17:11:54+08:00" type="RUN" actor="pm-orchestrator">上一批剩余文件按用户"其他问题全部按照推荐"（含提交问题推荐 A）本地提交 68bc477，未推送。</event>
    <event time="2026-11-16T17:11:54+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（GROUP_A-002，定稿 PHASE_01 + 写 PHASE_02）</event>
    <event time="2026-11-16T17:16:22+08:00" type="GATE" actor="pm-orchestrator">GR-A-002 PASS_WITH_CONDITIONS；等待用户确认故事。</event>
    <event time="2026-11-16T17:49:19+08:00" type="GATE" actor="pm-orchestrator">用户确认故事；GROUP_A APPROVED（1.0.0）。</event>
    <event time="2026-11-16T17:49:19+08:00" type="INVOCATION" actor="pm-orchestrator">调用 system-architect（GROUP_B-001）</event>
    <event time="2026-11-16T18:03:34+08:00" type="GATE" actor="pm-orchestrator">GR-B-001 PASS_WITH_CONDITIONS；架构三件 1.0.0 APPROVED。基线：15ea79e..HEAD 无代码改动，沿用 ocap_unit_sort_filters GR-D-001 复跑结果（后端 822、前端 259、小程序 97）。</event>
    <event time="2026-11-16T18:03:34+08:00" type="INVOCATION" actor="pm-orchestrator">调用 software-developer（GROUP_C-001）</event>
    <event time="2026-11-16T18:41:15+08:00" type="GATE" actor="pm-orchestrator">GR-C-001 PASS_WITH_CONDITIONS；开发两件 1.0.0 APPROVED。</event>
    <event time="2026-11-16T18:41:15+08:00" type="INVOCATION" actor="pm-orchestrator">调用 test-engineer（GROUP_D-001）</event>
    <event time="2026-11-16T19:20:14+08:00" type="GATE" actor="pm-orchestrator">GR-D-001 PASS_WITH_CONDITIONS；测试四件 1.0.0 APPROVED。暂停于 E1 前向用户汇报。</event>
    <event time="2026-11-16T19:22:21+08:00" type="RUN" actor="pm-orchestrator">经用户当轮同意本地提交 c32684b（73 文件），未推送。</event>
    <event time="2026-11-16T19:22:21+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（GROUP_E1-001，仅计划）</event>
    <event time="2026-11-16T19:30:54+08:00" type="GATE" actor="pm-orchestrator">GR-E1-001 PASS_WITH_CONDITIONS；部署两件 1.0.0 APPROVED。等待用户：推送、小程序顺序、阶段 A 授权。</event>
    <event time="2026-11-16T19:33:19+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">用户本轮明确授权：push main + 测试环境阶段 A（含 migrate residency 0003）与阶段 B（relocate_shops dry-run 只读）。C~E 未授权。</event>
    <event time="2026-11-16T19:35:01+08:00" type="RUN" actor="pm-orchestrator">git push origin main：15ea79e..c32684b；CI run 43858790019 success（Backend / Web frontend / Mini program）。</event>
    <event time="2026-11-16T19:35:01+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（GROUP_E2-001，阶段 A、B）</event>
    <event time="2026-11-16T19:47:10+08:00" type="GATE" actor="pm-orchestrator">GR-E2-001 PASS（阶段 A、B）。等待用户授权 C。</event>
    <event time="2026-11-16T21:37:39+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">用户本轮原话"授权C段 N=107，D也授权"：阶段 C（mysqldump + relocate_shops --apply --expect-changes 107）与阶段 D（导出到 /home/yangyang/ocap_exports/，留服务器）。E 未授权。</event>
    <event time="2026-11-16T21:37:39+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（GROUP_E2-002，阶段 C、D）</event>
    <event time="2026-11-16T21:59:32+08:00" type="GATE" actor="pm-orchestrator">GR-E2-002 PASS（阶段 C、D）；报告 2.0.0 APPROVED。等待用户授权 E。</event>
    <event time="2026-11-16T22:01:57+08:00" type="DEPLOY_AUTH" actor="pm-orchestrator">用户本轮原话"开始E段"：阶段 E（只读冒烟、e2e_ 夹具、P4-1 远程 E2E、清理）。</event>
    <event time="2026-11-16T22:01:57+08:00" type="INVOCATION" actor="pm-orchestrator">调用 devops-engineer（GROUP_E2-003，阶段 E）</event>
    <event time="2026-11-16T22:08:09+08:00" type="GATE" actor="pm-orchestrator">GR-E2-003 PASS_WITH_CONDITIONS；GROUP_E2 APPROVED；报告 3.0.0。</event>
    <event time="2026-11-16T22:08:37+08:00" type="RUN" actor="pm-orchestrator">delivery_report.md 写入，最终状态 DELIVERED_WITH_ISSUES。</event>
    <event time="2026-11-16T22:08:37+08:00" type="INVOCATION" actor="pm-orchestrator">调用 kb-curator（GROUP_Z-001，PHASE_12）</event>
    <event time="2026-11-16T22:11:23+08:00" type="RUN" actor="pm-orchestrator">kb-curator 完成：晋升 14、合并 6、保留 1、通用候选 0；写入 .claude/agent-memory（PM 核实 .trae 与 generic 无改动）。</event>
    <event time="2026-11-16T22:13:19+08:00" type="RUN" actor="pm-orchestrator">经用户当轮同意提交并推送全部改动（推送仅触发 CI，画像 P7 CI 不部署）。</event>
    <event time="2026-11-16T22:17:55+08:00" type="RUN" actor="pm-orchestrator">人工验证项全部由用户确认通过；最终状态仍为 DELIVERED_WITH_ISSUES（DEF-B、DEF-024 等遗留下批）。</event>
  </audit_log>
</phase_status>
