<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T13:32:21+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>2.0.0</version>
  <input_files><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>architecture/architecture_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>testing/test_plan.md（1.2.0）</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：信息公开与多平台内容中心（US-105~131）— 1.3.0（回流 2：DEF-014~016 复测（GC-3 修复后））

## 修订说明（1.2.0 → 1.3.0）

DEF-014（嵌套媒体 src 前缀）、DEF-015（空链接提示）、DEF-016（AC-128-04 未选平台提示）已由 GROUP_C-3 修复。本版：TC-UNIT-404 更新为“按钮可点击 + `ElMessage.warning('请至少选择一个平台')` 被调用 + 无 `/drafts` 请求”；AC-128-04 由 [部分] 改为已覆盖；TC-INT-388、TC-UNIT-393 复测 PASS；去掉各处 (FAIL) 标记。复测结果：后端 519 OK（unit 138 / integration 342 / e2e 33 / smoke 6）、前端 154/154、小程序 75/75、前端构建通过。

### 修订说明（1.1.0 → 1.2.0，保留）

1.1.0 的 AC 映射存在“只列用例范围、未核对用例是否断言该 AC 的 Then”的问题（GR-C-002：AC-122-03 映射到不断言审计的 TC-INT-316）。本版按代码逐条重建映射：**每个 AC 只列真实断言了其 Then 的用例**；只能覆盖其中一部分的标 **[部分]** 并写明缺口；用例失败的标 **（FAIL）** 并对应缺陷。映射表后附“新增 / 更新用例清单”。

## 测试策略

- 被测改动：MOD-039~063（后端 content app、integrations 客户端与公众号适配器、令牌服务、前端管理端编辑器/平台页、小程序 RichBlocks），对应 architecture / development 2.0.0（ADR-060~063，GR-C-003 修复）。
- In scope：富文本宽容校验与渲染、审计落点、全部管理端点权限扫描、公众号令牌服务与适配器（替身）、导出内容包临时文件、视频全有或全无、worker 心跳、前端编辑器组件（Tiptap 在 jsdom 中真实挂载）、小程序 RichBlocks。
- Out of scope：真实微信/小红书/头条/火山方舟/DeepSeek/即梦调用（画像 P4/P11-3 禁止）；浏览器与小程序真机 UI 交互；微信侧 IP 白名单；**封面 / 正文图片上传（ADR-061）的 HTTP 行为**——无官方文档出处（Q-B1），按协议 §N-2 标 BLOCKED，不自编期望值。
- 环境：Python 3.12.3 + Django 5.2.19（仓库原样，无补丁）；`config.test_settings`（SQLite 内存库、迁移置空）；frontend/miniprogram 使用 vitest 2.1.9 + jsdom + @vue/test-utils（未新增依赖）。Python 3.13 本机无，由 CI 验证。
- 判定模式：INCREMENTAL baseline（零新增失败 + 新写用例全部通过）。基线（调用方给定）：后端 430 = unit 102 / integration 293 / e2e 29 / smoke 6；前端 131；小程序 71。
- 分层：后端按目录（tests.unit / integration / e2e / smoke）；客户端组件与纯函数用例计入单元层；critical path 口径：**替代（完整 API 旅程 `backend/tests/e2e`；项目无浏览器 E2E 框架）**。
- 层间门控（回流 2 复测）：单元层 170/170 PASSED → 集成层 342 PASS + 1 BLOCKED（TC-INT-395，缺官方文档，非缺陷）PASSED → E2E 33/33 PASSED；既有用例新增失败 0。

## AC 映射

图例（位置简称）：U-rich=`backend/tests/unit/test_content_richtext.py`；U-core=`backend/tests/unit/test_content_core.py`；U-lenient=`backend/tests/unit/test_content_richtext_lenient.py`；U-token=`backend/tests/unit/test_wechat_token.py`；I-api=`backend/tests/integration/test_content_api.py`；I-audit=`…/test_content_audit.py`；I-scan=`…/test_content_permissions_scan.py`；I-gaps=`…/test_content_wechat_and_gaps.py`；E-flows=`backend/tests/e2e/test_content_flows.py`；F-api=`frontend/tests/content_api.spec.js`；F-editor=`frontend/tests/content_editor.spec.js`；M-rich=`miniprogram/tests/rich_blocks.spec.js`。级别：U 单元 / I 集成 / E 端到端；运行方式本项目均为 sim（无硬件，P11-1 为“无”）。数值类（P11-2）为“无”。

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置 | 前置→动作→预期（G/W/T）与缺口 | 测试数据 |
|---|---|---|---|---|---|---|---|
| AC-105-01 | TC-INT-301、TC-INT-306、TC-INT-307 | I | sim | 现有 | I-api | 创建→状态 DRAFT，管理员列表可见；成员列表无、详情 404 | D5 工厂用户/内容 |
| AC-105-02 | TC-INT-304、TC-INT-346 | I | sim | 新写+现有 | I-api、I-audit | 发布无审批→PUBLISHED；审计恰新增 1 条且含操作人/对象/时间/结果 | D5 工厂用户/内容 |
| AC-105-03 | TC-INT-303、TC-INT-346、TC-INT-381 | I | sim | 新写+现有 | I-api、I-audit、I-gaps | 标题/正文为空或默认标题“未命名内容”→400 POST_INCOMPLETE，details.missing 指明缺项，状态仍 DRAFT；**[部分]** 页面提示文案属前端，API 返回缺项字段 | D5 工厂用户/内容 |
| AC-106-01 | TC-INT-305、TC-INT-347 | I | sim | 新写+现有 | I-api、I-audit | 已发布内容改正文并重发→门户显示新正文；审计恰新增 1 条“修改” | D5 工厂用户/内容 |
| AC-106-02 | TC-INT-304、TC-INT-348 | I | sim | 新写+现有 | I-api、I-audit | 下线→OFFLINE；成员列表 count=0、详情 404；审计恰新增 1 条 | D5 工厂用户/内容 |
| AC-106-03 | TC-UNIT-407 | U | sim | 新写 | F-editor | 二次确认取消→不发 DELETE、内容仍在；确认后才 DELETE；取消路径无服务端动作，故无审计新增（TC-INT-349 断言删除前后计数） | D5 工厂用户/内容 |
| AC-106-04 | TC-INT-308、TC-INT-349 | I | sim | 新写+现有 | I-api、I-audit | 删除→管理列表消失、成员详情 404；审计恰新增 1 条“删除”，不存在的 id 不写 | D5 工厂用户/内容 |
| AC-107-01 | TC-UNIT-309、TC-UNIT-310、TC-E2E-301、TC-E2E-305 | UE | sim | 新写+现有 | E-flows、U-rich | 加粗/居中/红色/链接→HTML 含对应样式与 href、rel；**[部分]** 点击链接跳转属浏览器行为，见人工清单 M-01 | D5 工厂用户/内容 |
| AC-107-02 | TC-INT-307、TC-INT-306 | I | sim | 现有 | I-api | 成员列表只含已发布，不含草稿/已下线 | D5 工厂用户/内容 |
| AC-107-03 | TC-INT-302、TC-INT-371 | I | sim | 新写+现有 | I-api、I-scan | 未登录访问 /info/posts 与详情→401 UNAUTHORIZED；**[部分]** 页面跳转登录页属前端路由，未做组件测试 | D5 工厂用户/内容 |
| AC-107-04 | TC-UNIT-303、TC-UNIT-353、TC-INT-309、TC-E2E-305 | UIE | sim | 新写+更新+现有 | E-flows、I-api、U-lenient、U-rich | javascript: 链接→严格模式 400；宽容模式丢弃标记；输出 doc 与渲染 HTML 都不含 javascript:，文字/对齐/颜色保留 | D5 工厂用户/内容 |
| AC-108-01 | TC-E2E-301、TC-UNIT-314、TC-UNIT-344、TC-UNIT-345、TC-UNIT-401、TC-UNIT-402、TC-INT-311 | UIE | sim | 新写+现有 | E-flows、I-api、M-rich、U-rich | blocks 含加粗/居中/颜色/图片/链接；小程序组件渲染颜色/背景/字号/加粗并可复制链接；**[部分]** 真机显示见人工清单 M-06 | D5 工厂用户/内容 |
| AC-108-02 | TC-INT-348、TC-E2E-301 | IE | sim | 新写+现有 | E-flows、I-audit | 下线后成员列表/详情不再出现 | D5 工厂用户/内容 |
| AC-108-03 | TC-INT-302、TC-INT-371 | I | sim | 新写+现有 | I-api、I-scan | 未登录→401；**[部分]** 引导登录属小程序页面跳转，未做组件测试 | D5 工厂用户/内容 |
| AC-108-04 | TC-UNIT-353、TC-E2E-305 | UE | sim | 新写 | E-flows、U-lenient | blocks 输出不含 javascript:，其余格式保留 | D5 工厂用户/内容 |
| AC-109-01 | TC-UNIT-309、TC-UNIT-349、TC-UNIT-386、TC-E2E-305、TC-E2E-308 | UE | sim | 新写+现有 | E-flows、F-editor、U-lenient、U-rich | 取色器/粘贴 rgb→文档颜色为 #hex，保存后回显一致；居中保持；**[部分]** 编辑区实际视觉属浏览器，见 M-01 | D4 文档样例/color_vectors.json |
| AC-109-02 | TC-UNIT-304、TC-UNIT-310、TC-UNIT-392 | U | sim | 新写+现有 | F-editor、U-rich | 有效网址→文字带 link 标记；渲染带 href/rel；**[部分]** 预览中点击跳转属浏览器 | D4 文档样例/color_vectors.json |
| AC-109-03 | TC-UNIT-303、TC-INT-309、TC-UNIT-392、TC-UNIT-393 | UI | sim | 新写+更新+现有 | F-editor、I-api、U-rich | 无效网址→链接不被添加并提示“网址无效”（392）；网址为空时同样提示且不添加（393，DEF-015 已修复，PASS） | D4 文档样例/color_vectors.json |
| AC-109-04 | TC-UNIT-358、TC-E2E-301 | UE | sim | 新写+现有 | E-flows、U-lenient | 两段文字各自带独立对齐/行距属性；**[部分]** 回车键分段属编辑器按键行为，见 M-01 | D4 文档样例/color_vectors.json |
| AC-110-01 | TC-UNIT-383、TC-UNIT-384、TC-UNIT-302、TC-UNIT-305、TC-UNIT-308、TC-E2E-308 | UE | sim | 新写+现有 | E-flows、F-editor、U-rich | 工具栏按钮=清单（含标题1~4、对齐、取色器、字号、行距、列表、引用、分割线、图片、视频、撤销、重做、清除格式、链接）；扩展清单一致 | D4 文档样例/color_vectors.json |
| AC-110-02 | TC-UNIT-390 | U | sim | 新写 | F-editor | 加粗+字号+背景色后清除格式→无 marks，文字不变 | D4 文档样例/color_vectors.json |
| AC-110-03 | TC-UNIT-391 | U | sim | 新写 | F-editor | 两步编辑→撤销回上一步→重做回重做后状态 | D4 文档样例/color_vectors.json |
| AC-110-04 | TC-UNIT-383、TC-UNIT-384 | U | sim | 新写 | F-editor | 工具栏文本与扩展清单均不含表格/代码/公式/表情/卡片 | D4 文档样例/color_vectors.json |
| AC-111-01 | TC-UNIT-409、TC-INT-311、TC-E2E-301、TC-E2E-303 | UIE | sim | 新写+现有 | E-flows、F-editor、I-api | 素材选择器选中→editor 插入带 mediaId/src 的图片；发布后门户 <img>、blocks 含 src | D1 内存媒体样本 |
| AC-111-02 | TC-INT-313、TC-E2E-303 | IE | sim | 现有 | E-flows、I-api | 上传→素材库新增 1 条来源 UPLOAD 的图片 | D1 内存媒体样本 |
| AC-111-03 | TC-INT-314、TC-INT-393 | I | sim | 新写+现有 | I-api、I-gaps | svg 或 11 MB→400/413，素材库无新增 | D1 内存媒体样本 |
| AC-112-01 | TC-UNIT-329、TC-INT-310、TC-E2E-301 | UIE | sim | 现有 | E-flows、I-api、U-core | 选用模板→预览/门户按模板字号等令牌渲染，内容文字不变；**[部分]** 模板选择下拉 UI 未测 | D4 文档样例/color_vectors.json |
| AC-112-02 | TC-UNIT-331、TC-INT-340、TC-E2E-301 | UIE | sim | 现有 | E-flows、I-api、U-core | 自定义模板保存→列表出现→选用后渲染一致；**[部分]** 选择器 UI 未测 | D4 文档样例/color_vectors.json |
| AC-112-03 | TC-UNIT-316、TC-E2E-301 | UE | sim | 现有 | E-flows、U-rich | 分页标记→分为 2 页；**[部分]** 编辑器“分页”按钮存在（TC-UNIT-383），插入动作未单测 | D4 文档样例/color_vectors.json |
| AC-112-04 | TC-INT-394、TC-UNIT-331 | UI | sim | 新写+现有 | I-gaps、U-core | 名称为空/空白→400 STYLE_NAME_REQUIRED“模板名称不能为空”，模板列表不变 | D4 文档样例/color_vectors.json |
| AC-113-01 | TC-UNIT-316、TC-E2E-301、TC-UNIT-317 | UE | sim | 现有 | E-flows、U-rich | 1 个分页标记→page_count=2，第 1 页只含标记前内容；**[部分]** “下一页”控件 UI 未测 | D4 文档样例/color_vectors.json |
| AC-113-02 | TC-E2E-301、TC-UNIT-316 | UE | sim | 现有 | E-flows、U-rich | blocks 分页位置与 HTML 一致（page_count=2）；**[部分]** 小程序翻页控件 UI 未测 | D4 文档样例/color_vectors.json |
| AC-113-03 | TC-UNIT-317 | U | sim | 现有 | U-rich | 超过页长→按页长自动分页，末页为剩余内容 | D4 文档样例/color_vectors.json |
| AC-113-04 | TC-UNIT-318、TC-INT-306 | UI | sim | 现有 | I-api、U-rich | 无标记且篇幅短→page_count=1 | D4 文档样例/color_vectors.json |
| AC-114-01 | TC-INT-325、TC-UNIT-334、TC-E2E-302 | UIE | sim | 现有 | E-flows、I-api、U-core | 调用已配置模型→返回文案 | D2 外部服务替身 |
| AC-114-02 | TC-INT-322 | I | sim | 现有 | I-api | 保存模板→列表新增，重名 409，可更新/删除；**[部分]** 选中后自动填入提示词属 UI | D2 外部服务替身 |
| AC-114-03 | TC-INT-326 | I | sim | 现有 | I-api | 空提示词→400 PROMPT_EMPTY，不建任务；**[部分]** 页面文案“请输入提示词”见 AdminContentEditor 未单测 | D2 外部服务替身 |
| AC-114-04 | TC-INT-390 | I | sim | 新写 | I-gaps | 模型失败→任务 FAILED 带原因，不产生内容草稿；**[部分]** 输入保留属前端状态 | D2 外部服务替身 |
| AC-114-05 | TC-INT-326、TC-INT-338 | I | sim | 现有 | I-api | 无可用模型→409 LLM_NOT_CONFIGURED | D2 外部服务替身 |
| AC-115-01 | TC-E2E-302、TC-UNIT-319、TC-UNIT-396、TC-INT-306 | UIE | sim | 新写+现有 | E-flows、F-editor、I-api、U-rich | 生成文案→转文档→放入编辑器替换正文；内容状态 DRAFT | D2 外部服务替身 |
| AC-115-02 | TC-INT-306 | I | sim | 现有 | I-api | 未发布→成员详情 404、列表无 | D2 外部服务替身 |
| AC-115-03 | TC-UNIT-396 | U | sim | 新写 | F-editor | 已有正文→弹“将覆盖当前正文”；取消→正文不变；确认→覆盖 | D2 外部服务替身 |
| AC-116-01 | TC-E2E-304 | E | sim | 现有 | E-flows | 文生图任务成功→返回候选图片；**[部分]** 结果区展示与“插入正文”按钮属 UI | D2 外部服务替身 |
| AC-116-02 | TC-E2E-304、TC-INT-344 | IE | sim | 现有 | E-flows、I-api | 保存到素材库→新增 AI_GENERATED 图片；候选 TTL 清理与引用保护 | D2 外部服务替身 |
| AC-116-03 | TC-INT-313、TC-UNIT-409 | UI | sim | 新写+现有 | F-editor、I-api | 素材库选图→插入正文（选择器+编辑器） | D2 外部服务替身 |
| AC-116-04 | TC-INT-391 | I | sim | 新写 | I-gaps | 文生图失败→任务 FAILED 带原因；素材库与正文不变 | D2 外部服务替身 |
| AC-117-01 | TC-INT-319、TC-INT-323 | I | sim | 现有 | I-api | 配置页可保存 DeepSeek；可选模型默认 LLM_DEEPSEEK；**[部分]** 添加火山方舟/默认选中为 UI | D2 外部服务替身 |
| AC-117-02 | TC-INT-350、TC-INT-319、TC-UNIT-321、TC-UNIT-325 | UI | sim | 新写+现有 | I-api、I-audit、U-core | 凭据保存后响应/列表/可选列表/日志/审计中原文 0 次，只回 secret_saved | D2 外部服务替身 |
| AC-117-03 | TC-INT-319、TC-INT-352、TC-INT-370 | I | sim | 新写+现有 | I-api、I-audit、I-scan | 配置全站一份：另一管理员可见 configured 且无需再配 | D2 外部服务替身 |
| AC-117-04 | TC-INT-350 | I | sim | 新写 | I-audit | 改模型/凭据→审计各恰新增 1 条，detail 仅 changed_fields，无凭据 | D2 外部服务替身 |
| AC-117-05 | TC-INT-326 | I | sim | 现有 | I-api | 未配置→409 LLM_NOT_CONFIGURED | D2 外部服务替身 |
| AC-118-01 | TC-INT-319、TC-INT-351 | I | sim | 新写+现有 | I-api、I-audit | 测试成功→ok=true，进入可选列表 | D2 外部服务替身 |
| AC-118-02 | TC-INT-351 | I | sim | 新写 | I-audit | 测试失败→ok=false+error_code，不进可选列表；**[部分]** “测试失败”页面文案属 UI | D2 外部服务替身 |
| AC-118-03 | TC-INT-351 | I | sim | 新写 | I-audit | 从未测试→可选列表为空 | D2 外部服务替身 |
| AC-118-04 | TC-INT-351 | I | sim | 新写 | I-audit | 成功/失败各恰新增 1 条审计（失败 result=FAILURE） | D2 外部服务替身 |
| AC-119-01 | TC-INT-313、TC-INT-393 | I | sim | 新写+现有 | I-api、I-gaps | 上传 png（5 MB 边界内）→新增 1 条 IMAGE/UPLOAD | D1 内存媒体样本 |
| AC-119-02 | TC-INT-315、TC-INT-393 | I | sim | 新写+现有 | I-api、I-gaps | 上传 mp4（8 MB）→新增 1 条 VIDEO/UPLOAD | D1 内存媒体样本 |
| AC-119-03 | TC-INT-314、TC-INT-336、TC-INT-337、TC-INT-393 | I | sim | 新写+现有 | I-api、I-gaps | svg→400；超限/11 MB→413 FILE_TOO_LARGE；配额→413；素材库无新增 | D1 内存媒体样本 |
| AC-119-04 | TC-INT-393 | I | sim | 新写 | I-gaps | 视频 11 MB→413，素材库无新增；视频规格数值待 OQ-6，按当前 10 MB 默认 | D1 内存媒体样本 |
| AC-120-01 | TC-E2E-304、TC-INT-344 | IE | sim | 现有 | E-flows、I-api | AI 图片保存后素材库出现 AI_GENERATED/IMAGE | D1 内存媒体样本 |
| AC-120-02 | TC-INT-392、TC-INT-313 | I | sim | 新写+现有 | I-api、I-gaps | 来源筛选 AI_GENERATED 只含 AI 素材，不含 UPLOAD | D1 内存媒体样本 |
| AC-120-03 | TC-INT-391、TC-INT-383、TC-INT-385 | I | sim | 新写 | I-gaps | 生成失败→素材库无新增 | D1 内存媒体样本 |
| AC-121-01 | TC-UNIT-409、TC-INT-392、TC-E2E-303 | UIE | sim | 新写+现有 | E-flows、F-editor、I-gaps | 上传与 AI 图片均出现在选择器并可选中插入 | D1 内存媒体样本 |
| AC-121-02 | TC-E2E-303 | E | sim | 现有 | E-flows | 同一素材复用到两条内容→素材库仍 1 条 | D1 内存媒体样本 |
| AC-121-03 | TC-UNIT-408 | U | sim | 新写 | F-editor | 素材库为空→显示“素材库为空”，无报错 | D1 内存媒体样本 |
| AC-122-01 | TC-INT-392、TC-INT-313 | I | sim | 新写+现有 | I-api、I-gaps | 类型+来源组合筛选只返回同时满足者 | D1 内存媒体样本 |
| AC-122-02 | TC-INT-316 | I | sim | 现有 | I-api | 重命名→列表显示新名称，文件不变 | D1 内存媒体样本 |
| AC-122-03 | TC-INT-353、TC-INT-354、TC-INT-316 | I | sim | 新写+现有 | I-api、I-audit | 未被引用→删除成功、文件删除、审计恰新增 1 条；被引用拒绝不写；事务回滚时文件保留 | D1 内存媒体样本 |
| AC-122-04 | TC-INT-317、TC-INT-353、TC-E2E-303 | IE | sim | 新写+现有 | E-flows、I-api、I-audit | 被已发布引用→409 MEDIA_IN_USE，details.posts 列出标题，素材仍在 | D1 内存媒体样本 |
| AC-122-05 | TC-E2E-303 | E | sim | 现有 | E-flows | 引用内容下线/删除后可删除成功 | D1 内存媒体样本 |
| AC-123-01 | TC-UNIT-312、TC-UNIT-399、TC-INT-339、TC-INT-388、TC-E2E-306 | UIE | sim | 新写+现有 | E-flows、I-api、I-gaps、M-rich、U-rich | 视频素材渲染 video src；小程序嵌套视频 src；签名媒体 Range 206；blocks 任意深度 src 前缀一致（388，DEF-014 已修复，PASS）；**[部分]** 真机播放见 M-06 | D1 内存媒体样本 |
| AC-123-02 | TC-INT-315、TC-E2E-306 | IE | sim | 新写+现有 | E-flows、I-api | 当场上传视频→新增 1 条 VIDEO/UPLOAD | D1 内存媒体样本 |
| AC-123-03 | TC-INT-393 | I | sim | 新写 | I-gaps | 视频超限→413，素材库不变 | D1 内存媒体样本 |
| AC-124-01 | TC-INT-333、TC-E2E-304 | IE | sim | 现有 | E-flows、I-api | 已确认文案→建 VIDEO_GEN 任务，立即返回 QUEUED，payload 含分镜 | D2 外部服务替身 |
| AC-124-02 | TC-E2E-304、TC-INT-384、TC-INT-355 | IE | sim | 新写+现有 | E-flows、I-audit、I-gaps | 任务成功→视频（多片段）全部入库 SAVED/AI_GENERATED；完成审计 | D2 外部服务替身 |
| AC-124-03 | TC-INT-345、TC-INT-383、TC-INT-385 | I | sim | 新写+现有 | I-api、I-gaps | 远端失败→任务 FAILED 带原因；多片段中一段下载失败→素材库与文件无新增 | D2 外部服务替身 |
| AC-124-04 | TC-INT-333 | I | sim | 现有 | I-api | 未配置视频服务→409 VIDEO_NOT_CONFIGURED，不建任务 | D2 外部服务替身 |
| AC-124-05 | TC-INT-333、TC-INT-355 | I | sim | 新写+现有 | I-api、I-audit | 文案未确认→409 TEXT_NOT_CONFIRMED，不建任务、不记成功审计 | D2 外部服务替身 |
| AC-124-06 | TC-INT-355 | I | sim | 新写 | I-audit | 发起视频生成→审计 CONTENT_VIDEO_REQUESTED 恰新增 1 条（含 job_id/scenes） | D2 外部服务替身 |
| AC-124-07 | TC-UNIT-403 | U | sim | 新写 | F-editor | 编辑页仅“生成视频”入口，无分镜/裁剪/调序 | D2 外部服务替身 |
| AC-125-01 | TC-INT-352 | I | sim | 新写 | I-audit | 保存即梦账号→其他管理员看到同一份已配置状态 | D2 外部服务替身 |
| AC-125-02 | TC-INT-352 | I | sim | 新写 | I-audit | 账号不回显，响应/列表/他人列表/审计/日志中原文 0 次 | D2 外部服务替身 |
| AC-125-03 | TC-INT-320、TC-INT-352 | I | sim | 新写+现有 | I-api、I-audit | 必填缺失→400 MISSING_FIELDS，已有配置不变 | D2 外部服务替身 |
| AC-126-01 | TC-INT-356、TC-INT-327 | I | sim | 新写+更新 | I-api、I-audit | 添加账户→列表出现；审计恰新增 1 条 | D2 替身 + D3 测试用凭据 |
| AC-126-02 | TC-INT-327、TC-INT-341、TC-INT-356 | I | sim | 新写+更新 | I-api、I-audit | 同平台第二个账户→409 PLATFORM_ACCOUNT_EXISTS | D2 替身 + D3 测试用凭据 |
| AC-126-03 | TC-INT-356、TC-INT-341、TC-UNIT-405 | UI | sim | 新写+更新 | F-editor、I-api、I-audit | 改名/删除各恰新增 1 条审计；列表相应变化 | D2 替身 + D3 测试用凭据 |
| AC-126-04 | TC-INT-327、TC-INT-356、TC-UNIT-405 | UI | sim | 新写+更新 | F-editor、I-api、I-audit | 可添加平台仅 wechat_mp/xiaohongshu/toutiao | D2 替身 + D3 测试用凭据 |
| AC-127-01 | TC-INT-357 | I | sim | 新写 | I-audit | 填写认证信息→审计“认证信息更新”恰新增 1 条，detail 无原文 | D2 替身 + D3 测试用凭据 |
| AC-127-02 | TC-INT-357、TC-INT-379、TC-UNIT-405、TC-UNIT-406 | UI | sim | 新写 | F-editor、I-audit、I-gaps | 响应/日志/审计/推送记录中 appsecret、令牌 0 次；账户页输入框不回显；仅提交已填字段 | D2 替身 + D3 测试用凭据 |
| AC-127-03 | TC-INT-377、TC-INT-329、TC-INT-376、TC-UNIT-380、TC-UNIT-381、TC-UNIT-405 | UI | sim | 新写+现有 | F-editor、I-api、I-gaps、U-token | auth_errcodes 命中→推送 FAILED/AUTH_EXPIRED“认证已失效，请重新认证”、账户 EXPIRED、审计 CONTENT_PLATFORM_AUTH_EXPIRED 恰 1 条；40164 分类为 IP_NOT_WHITELISTED 且不标失效；auth_errcodes 缺省为空（取值无出处，Q-B1）：真实环境的自动标失效仅替身可验，见 M-04 | D2 替身 + D3 测试用凭据 |
| AC-127-04 | TC-INT-378 | I | sim | 新写 | I-gaps | 覆盖更新认证信息→账户恢复 NORMAL，令牌缓存列清空，下次推送重新取令牌并成功 | D2 替身 + D3 测试用凭据 |
| AC-127-05 | TC-INT-358、TC-UNIT-405 | UI | sim | 新写 | F-editor、I-audit | 无独立“检测账户有效性”接口；账户页无检测按钮 | D2 替身 + D3 测试用凭据 |
| AC-128-01 | TC-INT-329、TC-INT-361、TC-INT-373、TC-E2E-302 | IE | sim | 新写+现有 | E-flows、I-api、I-audit、I-gaps | 勾选自动平台→发起保存（取令牌+draft/add），SAVED；仅草稿箱，不发布；封面/正文图片上传 HTTP 行为无出处：TC-INT-395 BLOCKED（[DATA_REQUIRED: 微信官方文档]） | D2 替身 + D3 测试用凭据 |
| AC-128-02 | TC-INT-328、TC-INT-359、TC-E2E-302 | IE | sim | 新写+现有 | E-flows、I-api、I-audit | 无草稿接口平台→MANUAL_REQUIRED（非失败） | D2 替身 + D3 测试用凭据 |
| AC-128-03 | TC-UNIT-320、TC-INT-328、TC-UNIT-397 | UI | sim | 新写+现有 | F-editor、I-api、U-rich | 不能保留的样式在结果 unsupported 中列出（含 style_not_carried）；页面以中文列出 | D2 替身 + D3 测试用凭据 |
| AC-128-04 | TC-INT-330、TC-UNIT-404 | UI | sim | 新写+更新 | F-editor、I-api | 未勾选平台→400 NO_PLATFORM_SELECTED；页面“开始保存”可点击，点击后提示“请至少选择一个平台”且不发请求（TC-UNIT-404 已断言 `ElMessage.warning` 调用与无 `/drafts` 请求；DEF-016 已修复）。已覆盖 | D2 替身 + D3 测试用凭据 |
| AC-128-05 | TC-INT-330 | I | sim | 更新 | I-api | 未确认内容→409 POST_NOT_CONFIRMED | D2 替身 + D3 测试用凭据 |
| AC-128-06 | TC-INT-328、TC-INT-360 | I | sim | 新写+现有 | I-api、I-audit | 未配置认证→该平台 FAILED/NO_CREDENTIALS，不影响其他平台，无外部调用 | D2 替身 + D3 测试用凭据 |
| AC-128-07 | TC-INT-359、TC-INT-360、TC-INT-361、TC-INT-362、TC-INT-363、TC-INT-364 | I | sim | 新写 | I-audit | 每批恰 1 条 CONTENT_DRAFT_PUSHED，含逐平台结果；全人工/无凭据批次入队时写，混合批次 worker 结束时写，中断也写；幂等 | D2 替身 + D3 测试用凭据 |
| AC-129-01 | TC-INT-362、TC-INT-360、TC-UNIT-397 | UI | sim | 新写 | F-editor、I-audit | 失败平台带原因，其他平台结果不受影响；页面中文状态 | D2 替身 + D3 测试用凭据 |
| AC-129-02 | TC-INT-389、TC-INT-342 | I | sim | 新写+现有 | I-api、I-gaps | 失败平台重试且成功→新记录 SAVED，其他平台与原记录不变；非法重试 409 | D2 替身 + D3 测试用凭据 |
| AC-129-03 | TC-INT-335、TC-INT-380 | I | sim | 新写+现有 | I-api、I-gaps | 历史按时间倒序，含平台/结果/时间/操作人 | D2 替身 + D3 测试用凭据 |
| AC-129-04 | TC-INT-380 | I | sim | 新写 | I-gaps | 重试再次失败→仍 FAILED 且为最新失败原因；历史新增 1 条，原记录不变 | D2 替身 + D3 测试用凭据 |
| AC-130-01 | TC-INT-328、TC-INT-359、TC-UNIT-397 | UI | sim | 新写+现有 | F-editor、I-api、I-audit | 无接口平台结果 MANUAL_REQUIRED（“需人工粘贴”）并提供内容包/复制入口 | D1 内存媒体样本 |
| AC-130-02 | TC-INT-365、TC-INT-382 | I | sim | 新写 | I-audit、I-gaps | 内容包含正文、2 张图片、1 个视频；导出前后系统临时目录无新增文件 | D1 内存媒体样本 |
| AC-130-03 | TC-INT-332 | I | sim | 现有 | I-api | 复制载荷 text=正文；unsupported 含 style_not_carried；**[部分]** 剪贴板写入与“已复制”提示属浏览器 API，见人工清单 | D1 内存媒体样本 |
| AC-130-04 | TC-INT-365、TC-INT-366 | I | sim | 新写 | I-audit | 导出成功→审计恰新增 1 条；未确认 409 与构建失败不写 | D1 内存媒体样本 |
| AC-130-05 | TC-INT-366、TC-INT-331 | I | sim | 新写+现有 | I-api、I-audit | 无图片视频→仅含 content.txt/content.html/README.txt，导出成功 | D1 内存媒体样本 |
| AC-131-01 | TC-INT-370、TC-E2E-307 | IE | sim | 新写 | E-flows、I-scan | 任一管理员账号可访问全部 GET 管理接口，无额外权限 | D5 工厂用户/内容 |
| AC-131-02 | TC-INT-369、TC-INT-302、TC-E2E-307 | IE | sim | 新写+现有 | E-flows、I-api、I-scan | 业主/游客访问全部管理路由×方法→403，无写入副作用 | D5 工厂用户/内容 |
| AC-131-03 | TC-INT-368、TC-INT-371、TC-INT-372、TC-E2E-307 | IE | sim | 新写 | E-flows、I-scan | 未登录访问全部管理路由×方法→401，无写入副作用；仅签名媒体路由允许匿名 | D5 工厂用户/内容 |
| AC-131-04 | TC-INT-371 | I | sim | 新写 | I-scan | 用户端 info 接口仅 GET（写方法 405）；**[部分]** 界面无管理入口属前端静态审查 | D5 工厂用户/内容 |

共 112 条 AC；其中 23 条含 **[部分]**（缺口均为浏览器/小程序真机的视觉与点击行为，已列入 e2e 报告“人工验证清单”）。AC-128-01 的“封面/正文图片上传”子项见下节 TC-INT-395（BLOCKED）。

## 本轮新增 / 更新用例清单

更新（GR-C-003-F01，既有用例按设计 2.0.0 新口径修订）：

| 用例 | 修订内容 |
|---|---|
| TC-UNIT-332 / TC-UNIT-333 | `build_scenes` 入参由整篇文本改为段落列表；新增 TC-UNIT-346（空列表→POST_INCOMPLETE）、TC-UNIT-347（文档 3 段→3 分镜） |
| TC-INT-309 | 宽容模式：危险链接被丢弃→201，输出 doc 与渲染 HTML 都不含 `javascript:`，返回 warnings（reason/action/block_index）；结构错误（content 非数组等）仍 400 且带 block_index/block_type——**XSS 断言未放宽** |
| TC-INT-327 / TC-INT-330 / TC-INT-341 | 公众号凭据键改为 appid/appsecret；旧键 access_token→400 INVALID_VALUE |
| TC-INT-316 / TC-INT-353 | 素材删除文件改为 on_commit，使用 `captureOnCommitCallbacks(execute=True)` |

新增（后端 unit +36、integration +49、e2e +4；前端 +23；小程序 +4）：

| 范围 | 用例 | 主题 |
|---|---|---|
| U-lenient | TC-UNIT-348~356、358~367 | 共享颜色向量（`backend/tests/data/color_vectors.json`，rgb/rgba/非法值）、空串/null 样式、标题>4、无 mediaId 媒体、javascript:/data: 链接、超限仍抛错、警告上限 50、块级行距/嵌套媒体/下划线+删除线渲染、段落与媒体提取 |
| U-token | TC-UNIT-368~382 | 缓存命中/提前量刷新、expires_in 缺省、invalidate、缺凭据不发请求、单飞锁（持锁超时 TOKEN_BUSY、他人已刷新则复用、过期锁可抢、失败释放）、强制刷新冷却、覆盖凭据期间丢弃结果、errcode 分类、错误信息不含 secret/令牌 |
| U-core | TC-UNIT-346、347 | 分镜入参 |
| I-audit | TC-INT-346~366 | 审计断言：AC-105-02、106-01/02/04、117-04、118-04、122-03、124-06、126-01/03、127-01、128-07（含全人工/无凭据批次恰 1 条、逐平台结果、中断、幂等、worker）、130-04；凭据原文在响应/日志/审计 0 次（AC-117-02、125-02、127-02） |
| I-scan | TC-INT-367~372 | 遍历 `content/urls.py` 全部管理路由×全部方法：未登录 401、业主/游客 403、无写入副作用（快照 content 全表 + AuditLog + SystemConfig + 媒体目录）；任一管理员可访问；用户端 info 未登录 401；匿名路由仅签名媒体 |
| I-gaps | TC-INT-373~394 | 公众号适配器（默认不发上传请求、令牌错误刷新重发至多一次、超时不重发、40164 不标失效、auth_errcodes 命中标失效并写审计、覆盖凭据恢复 NORMAL、不泄露 secret/令牌）；重试再次失败/重试成功；默认标题发布被拒；导出内容包临时目录无残留（成功/中断/异常）；视频多片段全有或全无与远端失败；worker 心跳 ≤1/60 秒与 `--concurrency` 已移除；blocks 媒体 src 前缀一致性（FAIL，DEF-014）；LLM/文生图失败；类型+来源筛选；11 MB 边界；空模板名 |
| E-flows | TC-E2E-305~308 | critical path：305 编辑（rgb 颜色、javascript: 链接、引用内图片、外链图片）→ 保存（warnings）→ 再保存 → 发布 → 门户 HTML 与小程序 blocks 读取；306 上传视频→插入→发布→两端读取→签名地址 200/Range 206（US-123）；307 未登录/游客/业主整条管理链路被拒无写入、管理员同链路成功（US-131）；308 基础格式清单全部项 保存无 warnings→发布→渲染（US-110/109） |
| F-editor | TC-UNIT-383~409（含 385~387、394~397、403~409） | 工具栏清单、扩展清单、取色器（含真实编辑器）、粘贴守卫（纯函数 + 真实 ProseMirror 粘贴）、清除格式、撤销重做、链接校验、保存失败不发布/不确认（F02）、warnings 替换文档、覆盖确认取消、推送结果中文状态、无分镜入口、平台页（失效提示/不回显/无检测入口）、删除二次确认、素材选择器空态与选中插入 |
| M-rich | TC-UNIT-399~402 | 引用/列表内任意深度图片与视频 src、块级与行内行距、下划线+删除线合并、颜色/字号/加粗 |

**Tiptap 在 jsdom 的可行性**：Tiptap/ProseMirror 可在 jsdom 中真实挂载并执行命令；仅需测试内垫片（`Range.getClientRects`、`ClipboardEvent`，均写在测试文件内，不改产品代码）。因此前端用例使用真实编辑器而非最小挂载，无需因此降级为 [部分]；各 [部分] 仅为浏览器视觉/点击行为。

## 测试数据需求

- D1 媒体样本：内存构造 PNG（`89504E47…`）、MP4（偏移 4..8=`ftyp`）、11 MB 超限样本在用例内拼接，不落盘入库；媒体文件写入各用例独立临时 `MEDIA_ROOT`，teardown 删除。
- D2 外部服务替身：`FakeLlmClient`、`FakeImageGenClient`、`FakeVideoGenClient`、`FakeWechatMpApi`、`FakeDraftAdapter`、`FakeRemoteFetcher`（均在 `apps/integrations/fakes.py`），每个用例 setUp 注入、tearDown 复位（`set_*(None)`）。**不调用真实端点。**
- D3 测试用凭据：用例内的占位串（如 `APPSECRET-ADAPTER-VERYSECRET`），仅用于断言“泄露为 0”，不是真实凭据；`CONTENT_CRED_ENC_KEY` 由测试设置提供。
- D4 `backend/tests/data/color_vectors.json`：前后端共享颜色归一化向量（期望值来自设计 IFC-169 规则，非被测代码输出）。
- D5 工厂：管理员/业主/游客均由 `tests/support.py` 工厂生成，数据库为内存库，写入持久存储的唯一字段均由工厂唯一化。
- `[DATA_REQUIRED: 微信官方文档]`：公众号封面上传、正文图片上传的端点/字段/限制，以及 `auth_errcodes` / `token_errcodes` 的真实取值（Q-B1）。

## 不可测项

| AC / 项 | 原因 |
|---|---|
| AC-128-01 的“封面/正文图片上传”子项（TC-INT-395，BLOCKED） | `[DATA_REQUIRED: 微信官方文档]`：端点、字段、格式与大小限制无出处（协议 §N-2、ADR-061）；`HttpWechatMpApi.upload_*` 为 `NotImplementedError` 占位，开关缺省关闭；仅验证了“缺省关闭时不发上传请求”（TC-INT-373）。写入人工验证清单 M-04 |
| 真实平台联调 | 微信草稿、小红书/头条人工流程、火山方舟/DeepSeek/即梦真实行为属画像 P4/P11-3 禁止；仅替身。`auth_errcodes` 缺省为空，真实环境 HTTP 200 的令牌失效不会自动标失效，只能联调验证（M-04） |
| 浏览器/真机交互 | 点击跳转、回车分段、剪贴板写入、视频播放、翻页控件等，见 e2e 报告人工验证清单 M-01~M-07 |
| Python 3.13 | 本机无 3.13；由 CI 验证（GR-C-002-F01 的根因是 3.12/3.13 在类体求值注解） |

## 故事覆盖核对

每个 Must Have 故事至少 1 个**真实执行并通过**的用例（按故事逐个核对；含失败用例的故事另有通过用例）：

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-105 | TC-INT-301、TC-INT-306、TC-INT-307、TC-INT-304、TC-INT-346、TC-INT-303、TC-INT-381 | I |
| US-106 | TC-INT-305、TC-INT-347、TC-INT-304、TC-INT-348、TC-UNIT-407、TC-INT-308、TC-INT-349 | U/I |
| US-107 | TC-UNIT-309、TC-UNIT-310、TC-E2E-301、TC-E2E-305、TC-INT-307、TC-INT-306、TC-INT-302、TC-INT-371、TC-UNIT-303、TC-UNIT-353、TC-INT-309 | U/I/E |
| US-108 | TC-E2E-301、TC-UNIT-314、TC-UNIT-344、TC-UNIT-345、TC-UNIT-401、TC-UNIT-402、TC-INT-311、TC-INT-348、TC-INT-302、TC-INT-371、TC-UNIT-353、TC-E2E-305 | U/I/E |
| US-109 | TC-UNIT-309、TC-UNIT-349、TC-UNIT-386、TC-E2E-305、TC-E2E-308、TC-UNIT-304、TC-UNIT-310、TC-UNIT-392、TC-UNIT-303、TC-INT-309、TC-UNIT-393、TC-UNIT-358、TC-E2E-301 | U/I/E |
| US-110 | TC-UNIT-383、TC-UNIT-384、TC-UNIT-302、TC-UNIT-305、TC-UNIT-308、TC-E2E-308、TC-UNIT-390、TC-UNIT-391 | U/E |
| US-111 | TC-UNIT-409、TC-INT-311、TC-E2E-301、TC-E2E-303、TC-INT-313、TC-INT-314、TC-INT-393 | U/I/E |
| US-112 | TC-UNIT-329、TC-INT-310、TC-E2E-301、TC-UNIT-331、TC-INT-340、TC-UNIT-316、TC-INT-394 | U/I/E |
| US-113 | TC-UNIT-316、TC-E2E-301、TC-UNIT-317、TC-UNIT-318、TC-INT-306 | U/I/E |
| US-114 | TC-INT-325、TC-UNIT-334、TC-E2E-302、TC-INT-322、TC-INT-326、TC-INT-390、TC-INT-338 | U/I/E |
| US-115 | TC-E2E-302、TC-UNIT-319、TC-UNIT-396、TC-INT-306 | U/I/E |
| US-116 | TC-E2E-304、TC-INT-344、TC-INT-313、TC-UNIT-409、TC-INT-391 | U/I/E |
| US-117 | TC-INT-319、TC-INT-323、TC-INT-350、TC-UNIT-321、TC-UNIT-325、TC-INT-352、TC-INT-370、TC-INT-326 | U/I |
| US-119 | TC-INT-313、TC-INT-393、TC-INT-315、TC-INT-314、TC-INT-336、TC-INT-337 | I |
| US-120 | TC-E2E-304、TC-INT-344、TC-INT-392、TC-INT-313、TC-INT-391、TC-INT-383、TC-INT-385 | I/E |
| US-121 | TC-UNIT-409、TC-INT-392、TC-E2E-303、TC-UNIT-408 | U/I/E |
| US-123 | TC-UNIT-312、TC-UNIT-399、TC-INT-339、TC-INT-388、TC-E2E-306、TC-INT-315、TC-INT-393 | U/I/E |
| US-124 | TC-INT-333、TC-E2E-304、TC-INT-384、TC-INT-355、TC-INT-345、TC-INT-383、TC-INT-385、TC-UNIT-403 | U/I/E |
| US-125 | TC-INT-352、TC-INT-320 | I |
| US-126 | TC-INT-356、TC-INT-327、TC-INT-341、TC-UNIT-405 | U/I |
| US-127 | TC-INT-357、TC-INT-379、TC-UNIT-405、TC-UNIT-406、TC-INT-377、TC-INT-329、TC-INT-376、TC-UNIT-380、TC-UNIT-381、TC-INT-378、TC-INT-358 | U/I |
| US-128 | TC-INT-329、TC-INT-361、TC-INT-373、TC-E2E-302、TC-INT-328、TC-INT-359、TC-UNIT-320、TC-UNIT-397、TC-INT-330、TC-UNIT-404、TC-INT-360、TC-INT-362、TC-INT-363、TC-INT-364 | U/I/E |
| US-130 | TC-INT-328、TC-INT-359、TC-UNIT-397、TC-INT-365、TC-INT-382、TC-INT-332、TC-INT-366、TC-INT-331 | U/I |
| US-131 | TC-INT-370、TC-E2E-307、TC-INT-369、TC-INT-302、TC-INT-368、TC-INT-371、TC-INT-372 | I/E |

- US-118（Should Have）：TC-INT-319、TC-INT-351
- US-122（Should Have）：TC-INT-392、TC-INT-313、TC-INT-316、TC-INT-353、TC-INT-354、TC-INT-317、TC-E2E-303
- US-129（Should Have）：TC-INT-362、TC-INT-360、TC-UNIT-397、TC-INT-389、TC-INT-342、TC-INT-335、TC-INT-380

## 缺陷与产品行为观察（本轮）

三个缺陷均已修复并复测：DEF-014→TC-INT-388 PASS；DEF-015→TC-UNIT-393 PASS；DEF-016→TC-UNIT-404（更新）PASS。无新缺陷。下表保留原始描述作为记录。

| 编号 | 级别 | 现象 | 复现用例 |
|---|---|---|---|
| DEF-014 | MAJOR | `fmt=blocks` 只对顶层块去掉 `CONTENT_MEDIA_PATH_PREFIX`（posts.py:216-221 仅遍历 `page["blocks"]` 顶层）；引用/列表内的图片、视频 src 仍为 `/api/v1/content/media/…`，小程序 `mediaUrl` 再拼 `BASE=/api/v1` → `/api/v1/api/v1/…`，嵌套媒体无法加载 | TC-INT-388（已修复 PASS） |
| DEF-015 | MINOR | 编辑器“链接”在网址为空（点“确定”未填写）时静默返回（RichEditor.vue:146 `if (!url) return`），未提示“网址无效”，与 AC-109-03 不符；取消输入静默是正确的 | TC-UNIT-393（已修复 PASS） |
| 观察（未立 DEF） | — | `token_errcodes` 缺省为空时，缓存令牌 + 任意非零 errcode 的 draft/add 失败会被当作令牌错误并尝试强制刷新；若刚好处于 60 秒刷新冷却内，用户看到的是 `TOKEN_BUSY`（“令牌刷新冷却中”）而非真实 errcode。属 ADR-060 第 5 条保守兜底的副作用，建议在拿到官方 errcode 后复核（Q-B1）；TC-INT-380 改用 NETWORK 失败避开该路径 | — |
