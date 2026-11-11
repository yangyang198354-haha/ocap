<phase_status project="ocap_content_publish" mode="INCREMENTAL" created="2026-11-10T23:12:27+08:00" updated="2026-11-11T00:56:52+08:00">
  <request time="2026-11-10T23:12:27+08:00"><![CDATA[现在输入一批新需求。管理员在web 后端可以发布信息公开。可以向微信公众号web 版一样在前端辫子文字，能够设计段落，对其，颜色。超链接。要求和微信公众号编辑页面功能等价。 二，可以通过agent 编辑帖文。在web 上发布后，可以一键保存到公众号，小红书，头条账户的草稿箱里。 这些账户需要提前保存账户信息和认证信息。  agent 可以生成图文并茂的文字和材料。 agent 的 llm 也可以配置，使用国内的火山方舟模型或者deepseek模型，具体可以参考我genplatform 里面的设计。  生成的信息有文字，视频，图文等等。要求文字信息可以配置类似css，分段，分页的美感设计。还可以由素材库，生成的蔬菜库都可以保存复用。具体参考gentplatform。 按照这个思路补全我的需求。让管理员可以工作这些功能编辑图文，视频资料，并且通过大语言模型和提示词生成文案。一键发布到多个平台。 先整理需求，确认后再才分用户故事]]></request>
  <request_context><![CDATA[PM 只读核查（2026-11-10T23:12:27+08:00）：
- ocap 现有代码中无"信息公开/公告/富文本编辑器"实现（git grep 信息公开|公告|notice|announcement|richtext|wangeditor|quill|tinymce 于 backend、frontend/src、miniprogram 无相关命中）。
- 参考实现 /root/myproject/GenPlatform/project_workspace/content_gen_platform：apps/{llm_gateway,publisher,media_library,settings_vault,content,video_generator,image_generator}；需求 requirements/requirements_spec.md（模块二 LLM 文案、模块三 多平台发布、模块四 视频生成）；docs/features/llm_selection/requirements.md（火山/DeepSeek 选择）。
- 本批需求涉及新的闭源 API（微信公众号草稿箱、小红书、今日头条、火山方舟、DeepSeek），画像 P11-3 尚未登记，进入 GROUP_B 前须补 P11-3 并经用户确认。]]></request_context>
  <profile version="1.4.0" changed="2026-11-10T23:36:07+08:00" note="P11-3 新增 7 个外部服务；对已批准的 GROUP_A 产物无影响（需求未断言接口事实）"/>
  <workspace_note>独立增量项目，文档在 project_workspace/ocap_content_publish/（nested）；代码按画像 P3 in-repo。用户要求：先只整理需求（PHASE_01），确认后再拆用户故事（PHASE_02）；未放行前不进入设计/开发。</workspace_note>
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
    <group id="GROUP_E1" agent="devops-engineer" status="PENDING" gate_decision="PENDING" retries="0">
      <phase id="PHASE_10" status="PENDING"/><phase id="PHASE_11a" status="PENDING"/>
    </group>
    <group id="GROUP_E2" agent="devops-engineer" status="NOT_AUTHORIZED" environment=""/>
  </groups>
  <artifacts>
    <artifact path="project_workspace/ocap_content_publish/requirements/requirements_spec.md" version="0.1.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_content_publish/requirements/requirements_spec.md" version="0.2.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_content_publish/requirements/requirements_spec.md" version="0.3.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_content_publish/requirements/requirements_spec.md" version="1.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_content_publish/requirements/user_stories.md" version="0.1.0" status="SUPERSEDED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_content_publish/requirements/user_stories.md" version="1.0.0" status="APPROVED" group="GROUP_A"/>
    <artifact path="project_workspace/ocap_content_publish/architecture/architecture_design.md" version="0.1.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_content_publish/architecture/architecture_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_content_publish/architecture/module_design.md" version="0.1.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_content_publish/architecture/module_design.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_content_publish/architecture/tech_stack.md" version="0.1.0" status="SUPERSEDED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_content_publish/architecture/tech_stack.md" version="1.0.0" status="APPROVED" group="GROUP_B"/>
    <artifact path="project_workspace/ocap_content_publish/development/implementation_plan.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_content_publish/development/code_review_report.md" version="1.0.0" status="APPROVED" group="GROUP_C"/>
    <artifact path="project_workspace/ocap_content_publish/testing/test_plan.md" version="1.1.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_content_publish/testing/test_plan.md" version="1.0.0" status="SUPERSEDED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_content_publish/testing/unit_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_content_publish/testing/integration_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
    <artifact path="project_workspace/ocap_content_publish/testing/e2e_test_report.md" version="1.0.0" status="APPROVED" group="GROUP_D"/>
  </artifacts>
  <legacy_baseline/>
  <invocations>
    <invocation id="ocap_content_publish-GROUP_A-1" agent="requirement-analyst" start="2026-11-10T23:12:27+08:00" end="2026-11-10T23:16:17+08:00" result="SUCCESS"/>
    <invocation id="ocap_content_publish-GROUP_A-2" agent="requirement-analyst" start="2026-11-10T23:21:10+08:00" end="2026-11-10T23:24:01+08:00" result="SUCCESS"/>
  <invocation id="ocap_content_publish-GROUP_A-3" agent="requirement-analyst" start="2026-11-10T23:26:59+08:00" end="2026-11-10T23:30:39+08:00" result="SUCCESS"/>
  <invocation id="ocap_content_publish-GROUP_B-1" agent="system-architect" start="2026-11-10T23:36:07+08:00" end="2026-11-10T23:58:22+08:00" result="SUCCESS"/>
    <invocation id="ocap_content_publish-GROUP_C-1" agent="software-developer" start="2026-11-11T00:10:34+08:00" end="2026-11-11T00:29:19+08:00" result="SUCCESS"/>
    <invocation id="ocap_content_publish-GROUP_D-1" agent="test-engineer" start="2026-11-11T00:30:00+08:00" end="2026-11-11T00:42:52+08:00" result="SUCCESS"/>
  </invocations>
  <gate_reviews>
    <gate_review id="GR-A-001" invocation_id="ocap_content_publish-GROUP_A-1" decision="PASS_WITH_CONDITIONS" time="2026-11-10T23:16:17+08:00">
      <reviewed_files><file path="project_workspace/ocap_content_publish/requirements/requirements_spec.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-A-来源" result="SATISFIED">抽查 3 条：REQ-FUNC-110 引 GenPlatform llm_selection/requirements.md:25（仅列 last_test_ok 的 provider，属实）；REQ-FUNC-114 引 media_library/models.py:17-39（类型 image/video/audio、来源 ai_generated/uploaded，属实）；REQ-FUNC-118 引 requirements_spec.md:77-81（REQ-FUNC-012/013 发布状态与历史，属实）。基线引用 frontend/src/router/index.js:26-32 /admin 路由、ocap requirements_spec.md:93 REQ-FUNC-025 属实；用户原话引用与 request 一致。</criterion>
      <criterion id="J-A-GWT" result="SATISFIED">本次仅 PHASE_01，无用户故事；AC 的 G/W/T 在 PHASE_02 门控核对。</criterion>
      <criterion id="J-A-无技术实现" result="SATISFIED">grep wangeditor/quill/tinymce/celery/redis/CharField/JSONField/Django/Vue 无命中；加密算法明确留给架构阶段。</criterion>
      <criterion id="J-A-INFERRED" result="SATISFIED">4/24 = 16.7%（requirements_spec.md:17），≤ 0.20；I-1~I-4 已汇总于"待确认推断项"。</criterion>
      <criterion id="J-A-文件头" result="SATISFIED">0.1.0 DRAFT，timestamp 2026-11-10T23:13:08+08:00 真实；phase=PHASE_01；未写 user_stories.md（符合用户要求）。</criterion>
      <criterion id="J-A-闭源API" result="SATISFIED">五个外部平台能力均标 [UNSOURCED]，未断言；C-26 要求 GROUP_B 前补 P11-3。</criterion>
      <finding id="GR-A-001-F01" severity="MINOR">漏读画像 P10 的两份 Freeark 参考需求（agent notes 自述）；本批需求不依赖其内容，产出无误。下次调用点名要求先读。</finding>
      <finding id="GR-A-001-F02" severity="MINOR">6 个阻断问题（Q-CP-01~06）未答复，REQ-FUNC-102、107、117 验收口径未定稿。</finding>
      <condition>需求文件保持 DRAFT，待用户答复 Q-CP-01~18 后由 requirement-analyst 修订为 0.2.0；用户确认需求后再调用 PHASE_02 拆用户故事。</condition>
      <condition>进入 GROUP_B 前，PM 须与用户确认画像 P11-3 新增条目（公众号草稿箱、小红书、头条、火山方舟、DeepSeek 的文档位置、测试替身、凭据位置）。</condition>
    </gate_review>
    <gate_review id="GR-A-002" invocation_id="ocap_content_publish-GROUP_A-2" decision="PASS_WITH_CONDITIONS" time="2026-11-10T23:24:01+08:00">
      <reviewed_files><file path="project_workspace/ocap_content_publish/requirements/requirements_spec.md" version="0.2.0"/></reviewed_files>
      <criterion id="J-A-来源" result="SATISFIED">抽查：REQ-FUNC-121 引 GenPlatform requirements_spec.md:99（即梦账号配置，属实）；REQ-FUNC-122 来源 Q-CP-04=B 与 clarifications 一致；REQ-FUNC-110/114/118、REQ-NFUNC-018 来源改为 [U-答复]，与 PM 映射一致并保留 OQ-5 待确认。</criterion>
      <criterion id="J-A-INFERRED" result="SATISFIED">0/27 = 0%（requirements_spec.md:18）。</criterion>
      <criterion id="J-A-无技术实现" result="SATISFIED">grep wangeditor/quill/tinymce/celery/redis/CharField/JSONField/Django/Vue 无命中；无凭据模式命中。</criterion>
      <criterion id="J-A-必读" result="SATISFIED">notes 列出 Freeark 两份参考需求已读，GR-A-001-F01 已处理。</criterion>
      <criterion id="J-A-文件头" result="SATISFIED">0.2.0 DRAFT，timestamp 2026-11-10T23:21:58+08:00 真实；未写 user_stories.md。</criterion>
      <finding id="GR-A-002-F01" severity="MINOR">阻断问题 Q-CP-19（视频生成服务）未答复，REQ-FUNC-120/121 验收口径未定；新增非阻断 Q-CP-20（文生图服务）、Q-CP-14 数值仍开放。</finding>
      <condition>需求保持 DRAFT；用户答复 Q-CP-19 并确认需求后，再调用 PHASE_02（如答复引起需求变化，先在 PHASE_02 同次调用中修订 spec 为 0.3.0）。</condition>
      <condition>GROUP_B 前须确认画像 P11-3 新增条目（公众号、小红书、头条、火山方舟、DeepSeek、视频服务、文生图服务）。</condition>
    </gate_review>
    <gate_review id="GR-A-003" invocation_id="ocap_content_publish-GROUP_A-3" decision="PASS_WITH_CONDITIONS" time="2026-11-10T23:30:39+08:00">
      <reviewed_files><file path="project_workspace/ocap_content_publish/requirements/requirements_spec.md" version="0.3.0"/><file path="project_workspace/ocap_content_publish/requirements/user_stories.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-A-来源" result="SATISFIED">抽查：Q-CP-14=A 引 ocap requirements_spec.md:241 C-12、:247 C-18（PM 核实：C-18 单个≤10 MB、格式为图片或 pdf，无视频口径，与 agent 说明一致）；AC-117-01 默认 DeepSeek 与 Q-CP-15=A 一致；AC-107-01 已登录用户含游客与 Q-CP-02=B 一致。</criterion>
      <criterion id="J-A-GWT" result="SATISFIED">grep "^- AC-" = 112，不含 Given/When/Then 结构的 0 条；故事 27 个（US-105~131），US 编号在其他工作区无冲突（git grep）。</criterion>
      <criterion id="J-A-覆盖" result="SATISFIED">REQ-FUNC-099~122 逐条 grep user_stories.md，无缺失；门户/小程序展示分别由 US-107、US-108 覆盖；非管理员被拒 AC-131-02/03。</criterion>
      <criterion id="J-A-无技术实现" result="SATISFIED">grep wangeditor/quill/tinymce/celery/redis/CharField/JSONField/Django/Vue/endpoint//api/ 无命中；外部平台接口事实未写入 AC。</criterion>
      <criterion id="J-A-INFERRED" result="SATISFIED">0/27 = 0%。</criterion>
      <criterion id="J-A-文件头" result="SATISFIED">spec 0.3.0（2026-11-10T23:28:00+08:00）、stories 0.1.0（2026-11-10T23:29:43+08:00），DRAFT，时间真实。</criterion>
      <finding id="GR-A-003-F01" severity="MINOR">视频单文件上限暂按 C-18 的 10 MB 写入 C-29 与 AC-119-04、AC-123-03，但 C-18 无视频口径；OQ-6（视频格式清单与大小）与素材总配额仍开放，待用户确认。</finding>
      <finding id="GR-A-003-F02" severity="MINOR">本次未重读画像 P10 两份 Freeark 需求（GROUP_A-2 已读，产出不依赖），不影响产出。</finding>
      <condition>GROUP_B 前：PM 与用户确认画像 P11-3 新增 7 个外部服务（公众号草稿箱、小红书、头条、火山方舟 LLM、DeepSeek、即梦、火山方舟图像生成）的文档位置、测试替身、凭据位置；OQ-6 与素材配额如仍未答复，GROUP_B 须将其设计为可配置参数。</condition>
    </gate_review>
    <gate_review id="GR-B-001" invocation_id="ocap_content_publish-GROUP_B-1" decision="PASS_WITH_CONDITIONS" time="2026-11-10T23:58:22+08:00">
      <reviewed_files><file path="project_workspace/ocap_content_publish/architecture/architecture_design.md" version="0.1.0"/><file path="project_workspace/ocap_content_publish/architecture/module_design.md" version="0.1.0"/><file path="project_workspace/ocap_content_publish/architecture/tech_stack.md" version="0.1.0"/></reviewed_files>
      <criterion id="J-B-覆盖" result="SATISFIED">REQ-FUNC-099~122 逐条 grep module_design.md 无缺失；MOD-039~061、IFC-165~238。</criterion>
      <criterion id="J-B-ADR" result="SATISFIED">grep "^### ADR-" = 15（ADR-045~059）；ADR-049 列 A/B/C/D 四方案（含 Celery+Redis 对比与内存估计）。</criterion>
      <criterion id="J-B-小节" result="SATISFIED">module_design.md:923 数据迁移（content 0001 手写，仅新建表，回滚 MANUAL_ROLLBACK_REQUIRED + mysqldump）；:931 受影响的运行单元；:947 领域与外部依赖出处。</criterion>
      <criterion id="J-B-P11出处" result="SATISFIED">出处表 [P11:] 超过 10 条，PM 抽查 10 条全部与原文一致：publishers.py:71、72、76-79、83-87、88-92（freepublish 排除）；providers.py:10-11、106-107、129、132-140；ark_validator.py:20-21；doubao_image_client.py:30、37-44、249-262；jimeng_client.py:14-17、35、102-110、133-140。[UNSOURCED] 项（令牌续期、错误码、媒体嵌入、取值范围）均为行为细节，已转可配置参数/开放问题，不改 IFC 签名。</criterion>
      <criterion id="J-B-引用真实" result="SATISFIED">backend/apps/core/permissions.py:19-34 IsAdmin/IsMember 属实；deploy/systemd/ocap-run-due-jobs.service、backend/apps/jobs/ 存在。</criterion>
      <criterion id="J-B-P8" result="SATISFIED">docker/celery/redis/pscp/makemigrations 命中仅为对比方案与"不引入"声明；无容器；迁移手写。</criterion>
      <finding id="GR-B-001-F01" severity="MAJOR">D-1（ADR-049 新增常驻 systemd 单元 ocap-content-worker，内存 60~100 MB 为估计值）与 D-2（ADR-050 新增依赖 cryptography，密钥 CONTENT_CRED_ENC_KEY 须用户备份）需用户决定；否决任一项须回 GROUP_B 修订。</finding>
      <finding id="GR-B-001-F02" severity="MAJOR">目标机磁盘容量、gunicorn --timeout、ocap 8090 站点 client_max_body_size / proxy_read_timeout 未核实（与 ocap_registry_import GR-B-001-F01 同类）；回滚快照会打包 backend/var 媒体目录导致膨胀。</finding>
      <finding id="GR-B-001-F03" severity="MINOR">开放问题 Q-A1~A4、假设 A-1~A-8（含 A-4 签名短时 URL 放宽可见性、A-8"确认文案"口径）与 A-7 数值缺省待用户确认。</finding>
      <finding id="GR-B-001-F04" severity="MINOR">架构师指出画像 P3/P4 已过时：deploy/systemd/ 与 frontend/tests/ 已存在（PM 核实 deploy/systemd/ocap-run-due-jobs.service 存在）；画像修订待用户确认。</finding>
      <condition>GROUP_C 前：用户对 D-1、D-2 作出决定（否决则回 GROUP_B）；Q-A1~A4、A-1~A-8 用户确认或授权按缺省。</condition>
      <condition>GROUP_C：新增 npm 依赖须同步提交 frontend/package-lock.json；新增 API 路径须通过 backend/tests/integration/test_frontend_contract.py；迁移手写，文件头不得含 "Generated by Django"；外部调用仅限出处表所列。</condition>
      <condition>GROUP_E1：deployment_plan 给出目标机只读核实清单（磁盘、gunicorn timeout、nginx client_max_body_size/proxy_read_timeout）与 ocap-content-worker 单元、.env 4 个新键、快照排除 backend/var 的方案；不触碰 Freeark。</condition>
    </gate_review>
    <gate_review id="GR-C-001" invocation_id="ocap_content_publish-GROUP_C-1" decision="PASS_WITH_CONDITIONS" time="2026-11-11T00:29:19+08:00">
      <reviewed_files><file path="project_workspace/ocap_content_publish/development/implementation_plan.md" version="1.0.0"/><file path="project_workspace/ocap_content_publish/development/code_review_report.md" version="1.0.0"/></reviewed_files>
      <criterion id="J-C-MOD 全部实现" result="SATISFIED">MOD-039~061：9 模型 + 手写 0001 迁移；vault/conf/richtext/styles/media/posts/jobs/services_config/prompts/ai_jobs/platforms/drafts/export_pack/views/urls/handlers/worker 均存在；前端 12 新文件与小程序 4 新文件存在（文件清单见 implementation_plan 架构落地对照）。</criterion>
      <criterion id="J-C-需求追溯" result="SATISFIED">implementation_plan 需求追溯表 112 行，覆盖 US-105~131 全部 AC（脚本生成：AC_COUNT=112，ROWS=112，无 MISSING）；状态全部 DONE，无 PARTIAL。</criterion>
      <criterion id="J-C-迁移" result="SATISFIED">`makemigrations --check --dry-run --settings=config.test_settings` → No changes detected；0001 手写、无 "Generated by Django"、仅新建 9 表。</criterion>
      <criterion id="J-C-客户端构建与测试" result="SATISFIED">PM 复跑：frontend `npm run build -- --base=/ocap/` → ✓ built in 9.74s；frontend vitest 124 passed / 2 failed（既有 theme_build、theme.spec）；miniprogram vitest 69 passed（页面数断言已更新为 13）。</criterion>
      <criterion id="J-C-无 CRITICAL" result="SATISFIED">code_review_report 评分 8.2，CRITICAL 0；MAJOR 2（外部链路无专属用例、配额统计保守）均转 GROUP_D。</criterion>
      <criterion id="J-C-PM 复跑" result="SATISFIED">PM 亲自执行 `python manage.py test --settings=config.test_settings` → Ran 327 tests / OK；`check` → 0 issues；临时 API 冒烟 CREATE 201 / PREVIEW 200 / PUBLISH 200 / MEMBER_DETAIL 200 / BAD_LINK 400。</criterion>
      <criterion id="J-C-范围" result="SATISFIED">git status 仅 backend/apps/content 等新增与设计相关文件；新增依赖 cryptography 与 7 个 @tiptap 包，已在 requirements/package + lock 中；未改 Freeark 相关。</criterion>
      <finding id="GR-C-001-F01" severity="MAJOR">外部服务链路（LLM/文生图/视频/草稿）尚无专属自动化用例，任务状态机与失败/中断分支未验证（CR-001）。</finding>
      <finding id="GR-C-001-F02" severity="MAJOR">素材配额预检「已用 + 本次上限」为保守估算且全表求和（CR-002），缺边界用例。</finding>
      <finding id="GR-C-001-F03" severity="MINOR">引用块内媒体降级为标题文本（CR-003）；前端链接使用 window.prompt（CR-005）；`conf._valid` 残留死分支（CR-007）。</finding>
      <condition>GROUP_D：按 testing/test_plan 覆盖 112 条 AC（重点：富文本 XSS/链接/分页、媒体魔数与配额、任务成功/失败/中断/重试、草稿 AUTH_EXPIRED/NO_CREDENTIALS/MANUAL、一键保存与导出内容包、权限 401/403）；外部服务只用 Fakes；前端/小程序补关键交互用例；全量回归零新增失败。</condition>
      <verification><![CDATA[backend full: Ran 327 tests in 4.518s / OK
makemigrations --check: No changes detected
check: System check identified no issues (0 silenced)
frontend build: ✓ built in 9.74s
frontend vitest: Tests 2 failed | 124 passed (126)（既有 theme 环境失败）
miniprogram vitest: Test Files 10 passed / Tests 69 passed (69)
smoke: CREATE 201 / PREVIEW 200 / PUBLISH 200 / MEMBER_DETAIL 200 (pages=2) / BAD_LINK 400 CONTENT_INVALID_DOC]]></verification>
    </gate_review>
    <gate_review id="GR-D-001" invocation_id="ocap_content_publish-GROUP_D-1" decision="PASS_WITH_CONDITIONS" time="2026-11-11T00:42:52+08:00">
      <reviewed_files><file path="project_workspace/ocap_content_publish/testing/test_plan.md" version="1.0.0"/><file path="project_workspace/ocap_content_publish/testing/unit_test_report.md" version="1.0.0"/><file path="project_workspace/ocap_content_publish/testing/integration_test_report.md" version="1.0.0"/><file path="project_workspace/ocap_content_publish/testing/e2e_test_report.md" version="1.0.0"/></reviewed_files>
      <criterion id="J-D-AC 追溯" result="SATISFIED">test_plan AC 映射 112 行（AC-105-01~AC-131-04），每行有用例 ID 或 [部分]/[不可测] 标注；抽查 AC-107-04→TC-UNIT-309/TC-INT-309、AC-128-06→TC-INT-328、AC-130-02→TC-INT-331。</criterion>
      <criterion id="J-D-真实执行" result="SATISFIED">PM 复跑：backend 全量 Ran 402 / OK；unit 98、integration 272、e2e 26、smoke 6；frontend 127 passed/2 既有失败；miniprogram 71 passed。报告计数与最后执行一致。</criterion>
      <criterion id="J-D-分层门控" result="SATISFIED">单元 103/103（含前端 3、小程序 2）、集成 272/272、E2E 26/26；全量相对基线 327 新增失败 0。</criterion>
      <criterion id="J-D-critical path" result="SATISFIED">e2e 报告首行"critical path 口径：替代（API 旅程）"；24 个 Must Have 故事均有 E2E/最高层旅程覆盖（US-105~117、119~121、123~128、130/131），覆盖率 24/24=100%，通过率 100%。</criterion>
      <criterion id="J-D-契约" result="SATISFIED">既有 test_frontend_contract 在新增 40+ api.js 调用后仍通过；新增 TC-UNIT-341~343 校验前端/小程序路径与方法。</criterion>
      <criterion id="J-D-metrics" result="SATISFIED">三份报告均给出 total = pass + fail + skip + blocked + not_testable（103/272/26），算术成立。</criterion>
      <criterion id="J-D-写权限" result="SATISFIED">仅新增 backend/tests/{unit,integration,e2e} 与 frontend/miniprogram tests、testing/ 四份文档；未改产品代码。修正测试夹具自身的 FakeDraftAdapter 初始化与文档断言。</criterion>
      <criterion id="J-D-故事覆盖" result="SATISFIED">test_plan 故事覆盖核对 24 个 Must Have + 3 个 Should Have 均有已执行用例，无空行。</criterion>
      <finding id="GR-D-001-F01" severity="MAJOR">前端编辑器工具栏（清除格式/撤销重做/弹窗确认）与小程序空素材态无组件级测试，仅 API/纯函数覆盖（对应 test_plan [部分]/[不可测]）。</finding>
      <finding id="GR-D-001-F02" severity="MINOR">真实平台（公众号/小红书/头条/火山/DeepSeek/即梦）联调被 P4 禁止，仅替身；需用户在测试环境手工验证（e2e 报告 M-04/M-05）。</finding>
      <finding id="GR-D-001-F03" severity="MINOR">视频失败分支、草稿重试再次失败、平台账户删除、失效恢复未单独用例（接口已实现）。</finding>
      <condition>GROUP_E1：部署计划需覆盖 content 0001 迁移、`ocap-content-worker` 单元、`.env` 4 键（含 CONTENT_CRED_ENC_KEY 备份）、磁盘/nginx/gunicorn 核实、快照排除 backend/var；部署后按 e2e 报告 M-01~M-06 人工验证前端交互与真实平台联调。</condition>
      <verification><![CDATA[backend unit: Ran 98 tests / OK
backend integration: Ran 272 tests / OK
backend e2e: Ran 26 tests / OK
backend full: Ran 402 tests in 6.721s / OK
frontend: Tests 2 failed | 127 passed (129)（既有 theme 环境失败）
miniprogram: Test Files 11 passed / Tests 71 passed (71)
new: backend unit 36 / integration 35 / e2e 4；frontend 3；miniprogram 2]]></verification>
    </gate_review>
    <gate_review id="GR-D-002" invocation_id="ocap_content_publish-GROUP_D-1" decision="PASS" time="2026-11-11T00:56:52+08:00">
      <reviewed_files><file path="project_workspace/ocap_content_publish/testing/test_plan.md" version="1.1.0"/><file path="project_workspace/ocap_content_publish/testing/integration_test_report.md" version="1.0.0"/></reviewed_files>
      <criterion id="复审缺口-前端" result="SATISFIED">RichEditor 加载/切换媒体时用 mediaUrls 回填 image/video src（含 watch 同步）；AI 视频结果按 video 渲染并使用正确 kind 插入。frontend build ✓ built in 13.38s。</criterion>
      <criterion id="复审缺口-测试" result="SATISFIED">新增 TC-INT-336~345：413 超限、配额、429 限流、Range 206/416、样式 PUT/DELETE、平台删除、草稿重试、中断 UNKNOWN/INTERRUPTED、候选 TTL、视频远端失败；10/10 通过。</criterion>
      <criterion id="回归" result="SATISFIED">backend 全量 Ran 412 / OK（基线 327，新增失败 0）；frontend 127/129（2 既有失败）；miniprogram 71；makemigrations 无漂移。</criterion>
      <condition>无新增条件；原 GR-D-001 的 E1 部署与人工验证条件继续有效。</condition>
      <verification><![CDATA[backend full: Ran 412 tests in 6.124s / OK
integration: Ran 282 tests / OK
frontend build: ✓ built in 13.38s
frontend vitest: Tests 2 failed | 127 passed (129)
miniprogram: Test Files 11 passed / Tests 71 passed (71)
new: TC-INT-336~345 (10)]]></verification>
    </gate_review>
  </gate_reviews>
  <clarifications>
    <clarification time="2026-11-10T23:21:10+08:00" responder="用户"><![CDATA[用户原话："Q4=B; Q5=B，其他都按推荐"
映射：Q-CP-01=B（Web 门户+小程序）；Q-CP-02=B（已登录任意用户）；Q-CP-03=A（基础格式清单）；Q-CP-04=B（有接口的自动保存，无接口的导出复制人工粘贴）；Q-CP-05=B（纳入 AI 视频生成，视频服务由用户指定——用户尚未指定，需追问）；Q-CP-06=A（AI 文生图+素材库选图）；Q-CP-07=A；Q-CP-08=A；Q-CP-09=A；Q-CP-10=A；Q-CP-11=A；Q-CP-12=A；Q-CP-13=C；Q-CP-14：不得删除被已发布内容引用的素材（A）、当场上传自动入库（A），格式/大小/配额数值无推荐项、用户未给出 → 仍开放；Q-CP-15=A（全站一份、默认 DeepSeek）；Q-CP-16=B；Q-CP-17=A（仅草稿箱）；Q-CP-18=A。
I-1~I-4 推断项：PM 曾在汇报中请用户确认，用户答"其他都按推荐"，PM 理解为一并接受（PM 解读，在 0.2.0 汇报中向用户复述）。
画像 P11-3 新增条目（文档位置、测试替身）：用户未答复，GROUP_B 前仍须确认。]]></clarification>
    <clarification time="2026-11-10T23:26:59+08:00" responder="用户"><![CDATA[用户原话："Q19=A，其他按推荐，需求确认，拆用户故事"
映射：Q-CP-19=A（即梦，能力 [UNSOURCED] 待 P11-3）；Q-CP-20=A（火山方舟图像生成模型，[UNSOURCED]）；Q-CP-14=A（图片沿用 ocap C-12、视频沿用 C-18 口径；总配额用户仍未给数值 → 保持开放、非阻断）；OQ-5 确认：I-1~I-4 由用户接受。用户确认需求（0.2.0 + 上述答复），放行 PHASE_02。设计/开发未放行。]]></clarification>
    <clarification time="2026-11-10T23:33:47+08:00" responder="用户"><![CDATA[用户原话："开始架构设计" → 放行 GROUP_B。PM 依据 GR-A-003 condition 与 PM §2（需求出现 P11 信号须先确认 P11 补充稿）暂不调用 system-architect，先请用户确认画像 P11-3 补充稿。
PM 只读核查 GenPlatform 参考实现：publisher/publishers.py:54 小红书端点注释为 "# placeholder"（非可用实现）；:121 头条调用为正式发布接口，不是草稿；:76 公众号 draft/add 有调用；llm_gateway/providers.py:10-11 DeepSeek/火山方舟；video_generator/jimeng_client.py；image_generator/doubao_image_client.py。]]></clarification>
    <clarification time="2026-11-10T23:36:07+08:00" responder="用户"><![CDATA[用户原话："P1=A; P2=A; P3=A; P4=是，开始架构设计"。画像 P11-3 已按此写入，画像 1.3.0 → 1.4.0。GROUP_B 放行。]]></clarification>
    <clarification time="2026-11-11T00:03:45+08:00" responder="用户"><![CDATA[用户原话："D1=同意; D2=同意; 其余按缺省"。D-1 同意新增 ocap-content-worker；D-2 同意新增 cryptography，用户自行备份 CONTENT_CRED_ENC_KEY；Q-A1 管理员手工录入 access_token；Q-A4 文生图与 LLM 方舟密钥分开配置；A-1~A-8 与 A-7 数值缺省按设计。画像 P3/P4 过时修订、PM 只读 ssh 核实：用户未答复，暂不执行。开发未放行。]]></clarification>
  </clarifications>
  <checkpoints/>
  <escalations/>
  <audit_log>
    <event time="2026-11-10T23:12:27+08:00" type="RUN" actor="pm-orchestrator">运行模式：主会话。依据：用户直接陈述新需求（判定规则 3）。已读 shared_protocol.md、project_profile.md 1.3.0、knowledge_base/generic/pm-orchestrator.md、PM 记忆。</event>
    <event time="2026-11-10T23:12:27+08:00" type="INVOCATION" actor="pm-orchestrator">调用 requirement-analyst（ocap_content_publish-GROUP_A-1），仅 PHASE_01（用户要求先整理需求，确认后再拆故事）。</event>
    <event time="2026-11-10T23:16:17+08:00" type="GATE" actor="pm-orchestrator">GR-A-001 PASS_WITH_CONDITIONS（PHASE_01 内容门控）；需求文件保持 DRAFT，等待用户答复 Q-CP-01~18 与确认。</event>
    <event time="2026-11-10T23:21:10+08:00" type="INVOCATION" actor="pm-orchestrator">用户答复 Q-CP-01~18；调用 requirement-analyst（ocap_content_publish-GROUP_A-2）按答复修订 requirements_spec 为 0.2.0，仍仅 PHASE_01。</event>
    <event time="2026-11-10T23:24:01+08:00" type="GATE" actor="pm-orchestrator">GR-A-002 PASS_WITH_CONDITIONS；requirements_spec 0.2.0 保持 DRAFT，等待用户答复 Q-CP-19 并确认需求。</event>
    <event time="2026-11-10T23:26:59+08:00" type="INVOCATION" actor="pm-orchestrator">用户确认需求并放行 PHASE_02；调用 requirement-analyst（ocap_content_publish-GROUP_A-3）：spec 落答复为 0.3.0 + 写 user_stories 0.1.0。</event>
    <event time="2026-11-10T23:30:39+08:00" type="GATE" actor="pm-orchestrator">GR-A-003 PASS_WITH_CONDITIONS；GROUP_A APPROVED，requirements_spec 与 user_stories 文件头改为 APPROVED 1.0.0。GROUP_B 未放行。</event>
    <event time="2026-11-10T23:33:47+08:00" type="RUN" actor="pm-orchestrator">用户放行 GROUP_B；调用前须确认画像 P11-3 补充稿（7 个外部服务），已向用户提问，GROUP_B 保持 PENDING。</event>
    <event time="2026-11-10T23:36:07+08:00" type="INVOCATION" actor="pm-orchestrator">画像升至 1.4.0（P11-3）；调用 system-architect（ocap_content_publish-GROUP_B-1）。</event>
    <event time="2026-11-10T23:58:22+08:00" type="GATE" actor="pm-orchestrator">GR-B-001 PASS_WITH_CONDITIONS（内容门控）；D-1/D-2 待用户决定，文档保持 DRAFT，GROUP_B=AWAITING_REVIEW。</event>
    <event time="2026-11-11T00:03:45+08:00" type="GATE" actor="pm-orchestrator">用户决定 D-1/D-2 同意、其余按缺省；GROUP_B APPROVED，三份架构文档文件头改为 APPROVED 1.0.0。GROUP_C 未放行。</event>
  <event time="2026-11-11T00:05:52+08:00" type="RUN" actor="pm-orchestrator"><![CDATA[用户当轮授权"提交，并且push"并要求先合并远端。推送前检查：.github/workflows/ci.yml 仅 push/PR 触发测试与构建，无部署 job（画像 P7 一致）。git fetch：origin/main 新增 4 个提交（ocap_registry_import 开发/测试/部署，在其他机器完成）；与本地仅 project_workspace/_kb_inbox.jsonl 冲突，按"远端全量 + 本地新增 7 行"合并（77 行，id 无重复）；远端无与本批 REQ-FUNC-099~122/US-105~131/ADR-045~059/MOD-039~061/IFC-165~238 冲突的编号。rebase 后提交 b0a0159 已推送 96be0b8..b0a0159。注意：远端改动了 test_frontend_contract.py、support.py、frontend/src/shared/api.js、registry 等，架构文档中对这些文件的行号引用（基于 03b4b28）可能偏移，GROUP_C 调用时须要求开发按当前代码重新核对。]]></event>
    <event time="2026-11-11T00:29:19+08:00" type="INVOCATION" actor="pm-orchestrator">GROUP_C-1 结束（software-developer，SUCCESS）：MOD-039~061 实现；implementation_plan 112 AC 全追溯、code_review_report 8.2 分；后端 327 OK、迁移无漂移、前端构建成功、小程序 69 passed。</event>
    <event time="2026-11-11T00:29:19+08:00" type="GATE" actor="pm-orchestrator">GR-C-001 PASS_WITH_CONDITIONS，GROUP_C APPROVED（PHASE_05/06）。PM 复跑后端 327 OK、check 无问题、API 冒烟通过；MAJOR 2（外部链路无专属用例、配额统计保守）转 GROUP_D；条件见 GR-C-001。</event>
    <event time="2026-11-11T00:42:52+08:00" type="INVOCATION" actor="pm-orchestrator">GROUP_D-1 结束（test-engineer，SUCCESS）：新增后端 75 个用例（unit 36 / integration 35 / e2e 4）+ 前端 3 + 小程序 2；testing/ 四份 1.0.0。实测 unit 98、integration 272、e2e 26，全量 402 OK；frontend 127 passed/2 既有失败；miniprogram 71 passed。</event>
    <event time="2026-11-11T00:42:52+08:00" type="GATE" actor="pm-orchestrator">GR-D-001 PASS_WITH_CONDITIONS，GROUP_D APPROVED（PHASE_07/08/09）。PM 复跑 backend 402 OK、frontend 127/129、miniprogram 71；critical path 24/24。条件转 GROUP_E1（迁移/worker/.env/磁盘与 nginx 预检、人工验证清单）。</event>
    <event time="2026-11-11T00:56:52+08:00" type="REWORK" actor="pm-orchestrator">复审后修复：1) RichEditor 用 mediaUrls 回填图片/视频 src（初始加载 + watch 同步），AI 视频结果按 video 渲染并以 media_type 插入；2) 新增 TC-INT-336~345 覆盖 413/配额/429/Range 206-416/样式 PUT-DELETE/平台删除/草稿重试/中断/候选 TTL/视频失败。前端 build 成功；后端 412 OK、makemigrations 无漂移。</event>
    <event time="2026-11-11T00:56:52+08:00" type="GATE" actor="pm-orchestrator">GR-D-002 PASS（复审修复）。test_plan 升至 1.1.0（新增补充覆盖表）；GROUP_C/ GROUP_D 维持 APPROVED；交付状态不变。</event>
  </audit_log>
</phase_status>
