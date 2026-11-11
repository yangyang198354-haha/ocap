<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T00:56:52+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.1.0</version>
  <input_files><file>requirements/user_stories.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>architecture/module_design.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：信息公开与多平台内容中心（US-105~131）

## 测试策略

- 被测改动：MOD-039~061（后端 content app、integrations 4 个客户端、前端管理端/门户、小程序 info 页）。
- In scope：富文本校验/渲染/分页、内容状态机、样式模板、素材库与配额/魔数、权限、LLM/文生图/视频/草稿任务（替身）、平台账户、一键保存/重试/历史、内容包导出、参数。
- Out of scope：真实微信/小红书/头条/火山方舟/DeepSeek/即梦调用（画像 P4 禁止，只用 `Fakes`）；浏览器/小程序真机 UI 交互；Tiptap 工具栏逐按钮行为；微信侧域名白名单。
- 环境：Django test runner + SQLite 内存库（`config.test_settings`）、`MIGRATION_MODULES` 置空；前端/小程序 vitest。
- 判定模式：INCREMENTAL baseline（零新增失败）。基线：后端 327 OK、前端 124 passed/2 既有失败、小程序 69 passed。
- critical path 口径：替代（完整 API 旅程 `tests/e2e`）。

## AC 映射

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置 |
|---|---|---|---|---|---|
| AC-105-01 | TC-INT-301、TC-INT-303、TC-INT-304、TC-E2E-301 | E | sim | 新写 | `US-105` 对应测试文件 |
| AC-105-02 | TC-INT-301、TC-INT-303、TC-INT-304、TC-E2E-301 | E | sim | 新写 | `US-105` 对应测试文件 |
| AC-105-03 | TC-INT-301、TC-INT-303、TC-INT-304、TC-E2E-301 | E | sim | 新写 | `US-105` 对应测试文件 |
| AC-106-01 | TC-INT-304、TC-INT-305、TC-INT-307、TC-INT-308 | I | sim | 新写 | `US-106` 对应测试文件 |
| AC-106-02 | TC-INT-304、TC-INT-305、TC-INT-307、TC-INT-308 | I | sim | 新写 | `US-106` 对应测试文件 |
| AC-106-03 | [部分] TC-INT-308（API 删除）；二次确认属前端交互，无组件测试 | I | sim | 新写 | `US-106` 对应测试文件 |
| AC-106-04 | TC-INT-304、TC-INT-305、TC-INT-307、TC-INT-308 | I | sim | 新写 | `US-106` 对应测试文件 |
| AC-107-01 | TC-INT-306、TC-INT-307、TC-E2E-301 | E | sim | 新写 | `US-107` 对应测试文件 |
| AC-107-02 | TC-INT-306、TC-INT-307、TC-E2E-301 | E | sim | 新写 | `US-107` 对应测试文件 |
| AC-107-03 | TC-INT-306、TC-INT-307、TC-E2E-301 | E | sim | 新写 | `US-107` 对应测试文件 |
| AC-107-04 | TC-INT-306、TC-INT-307、TC-E2E-301 | E | sim | 新写 | `US-107` 对应测试文件 |
| AC-108-01 | TC-E2E-301、TC-UNIT-344、TC-UNIT-345 | U | sim | 新写 | `US-108` 对应测试文件 |
| AC-108-02 | TC-E2E-301、TC-UNIT-344、TC-UNIT-345 | U | sim | 新写 | `US-108` 对应测试文件 |
| AC-108-03 | TC-E2E-301、TC-UNIT-344、TC-UNIT-345 | U | sim | 新写 | `US-108` 对应测试文件 |
| AC-108-04 | TC-E2E-301、TC-UNIT-344、TC-UNIT-345 | U | sim | 新写 | `US-108` 对应测试文件 |
| AC-109-01 | [部分] TC-UNIT-309、TC-E2E-301（渲染）；编辑器工具栏无组件测试 | U | sim | 新写 | `US-109` 对应测试文件 |
| AC-109-02 | [部分] TC-UNIT-310、TC-E2E-301（渲染）；点击跳转 UI 未测 | U | sim | 新写 | `US-109` 对应测试文件 |
| AC-109-03 | [部分] TC-UNIT-303、TC-INT-309（校验）；工具栏提示未测 | I | sim | 新写 | `US-109` 对应测试文件 |
| AC-109-04 | [部分] TC-UNIT-301、TC-E2E-301；回车分段属编辑器 UI | U | sim | 新写 | `US-109` 对应测试文件 |
| AC-110-01 | [部分] TC-UNIT-301~320（服务端格式能力）；工具栏清单未组件测试 | U | sim | 新写 | `US-110` 对应测试文件 |
| AC-110-02 | [部分] 清除格式属前端工具栏，无自动化 | I | sim | 新写 | `US-110` 对应测试文件 |
| AC-110-03 | [部分] 撤销/重做属前端工具栏，无自动化 | I | sim | 新写 | `US-110` 对应测试文件 |
| AC-110-04 | [部分] 工具栏不含表格/代码等，属前端静态审查 | I | sim | 新写 | `US-110` 对应测试文件 |
| AC-111-01 | TC-INT-311、TC-INT-313、TC-INT-317、TC-E2E-301、TC-E2E-303 | E | sim | 新写 | `US-111` 对应测试文件 |
| AC-111-02 | TC-INT-311、TC-INT-313、TC-INT-317、TC-E2E-301、TC-E2E-303 | E | sim | 新写 | `US-111` 对应测试文件 |
| AC-111-03 | TC-INT-311、TC-INT-313、TC-INT-317、TC-E2E-301、TC-E2E-303 | E | sim | 新写 | `US-111` 对应测试文件 |
| AC-112-01 | [部分] TC-UNIT-329、TC-E2E-301（预览 HTML）；模板选择 UI 未测 | U | sim | 新写 | `US-112` 对应测试文件 |
| AC-112-02 | [部分] TC-UNIT-331（模板 CRUD）；选择器 UI 未测 | U | sim | 新写 | `US-112` 对应测试文件 |
| AC-112-03 | [部分] TC-UNIT-316、TC-E2E-301（分页）；编辑器插入按钮未测 | U | sim | 新写 | `US-112` 对应测试文件 |
| AC-112-04 | TC-UNIT-329~331、TC-E2E-301 | U | sim | 新写 | `US-112` 对应测试文件 |
| AC-113-01 | TC-UNIT-316~318、TC-E2E-301 | U | sim | 新写 | `US-113` 对应测试文件 |
| AC-113-02 | TC-UNIT-316~318、TC-E2E-301 | U | sim | 新写 | `US-113` 对应测试文件 |
| AC-113-03 | TC-UNIT-316~318、TC-E2E-301 | U | sim | 新写 | `US-113` 对应测试文件 |
| AC-113-04 | TC-UNIT-316~318、TC-E2E-301 | U | sim | 新写 | `US-113` 对应测试文件 |
| AC-114-01 | TC-INT-325、TC-INT-326、TC-INT-334、TC-UNIT-332~334 | I | sim | 新写 | `US-114` 对应测试文件 |
| AC-114-02 | TC-INT-325、TC-INT-326、TC-INT-334、TC-UNIT-332~334 | I | sim | 新写 | `US-114` 对应测试文件 |
| AC-114-03 | TC-INT-325、TC-INT-326、TC-INT-334、TC-UNIT-332~334 | I | sim | 新写 | `US-114` 对应测试文件 |
| AC-114-04 | TC-INT-325、TC-INT-326、TC-INT-334、TC-UNIT-332~334 | I | sim | 新写 | `US-114` 对应测试文件 |
| AC-114-05 | TC-INT-325、TC-INT-326、TC-INT-334、TC-UNIT-332~334 | I | sim | 新写 | `US-114` 对应测试文件 |
| AC-115-01 | TC-INT-306、TC-E2E-302 | E | sim | 新写 | `US-115` 对应测试文件 |
| AC-115-02 | TC-INT-306、TC-E2E-302 | E | sim | 新写 | `US-115` 对应测试文件 |
| AC-115-03 | [部分] 覆盖当前正文的确认属前端交互，无自动化 | I | sim | 新写 | `US-115` 对应测试文件 |
| AC-116-01 | [部分] TC-E2E-304（文生图任务成功）；结果区 UI 未测 | E | sim | 新写 | `US-116` 对应测试文件 |
| AC-116-02 | TC-E2E-304、TC-INT-313 | E | sim | 新写 | `US-116` 对应测试文件 |
| AC-116-03 | [部分] TC-INT-313（素材上传）；从素材库选图 UI 未测 | I | sim | 新写 | `US-116` 对应测试文件 |
| AC-116-04 | [部分] 生成失败分支未单独覆盖（替身支持 fail_code） | I | sim | 新写 | `US-116` 对应测试文件 |
| AC-117-01 | TC-INT-319、TC-INT-321、TC-UNIT-321~324 | I | sim | 新写 | `US-117` 对应测试文件 |
| AC-117-02 | TC-INT-319、TC-INT-321、TC-UNIT-321~324 | I | sim | 新写 | `US-117` 对应测试文件 |
| AC-117-03 | TC-INT-319、TC-INT-321、TC-UNIT-321~324 | I | sim | 新写 | `US-117` 对应测试文件 |
| AC-117-04 | TC-INT-319、TC-INT-321、TC-UNIT-321~324 | I | sim | 新写 | `US-117` 对应测试文件 |
| AC-117-05 | TC-INT-319、TC-INT-321、TC-UNIT-321~324 | I | sim | 新写 | `US-117` 对应测试文件 |
| AC-118-01 | [部分] TC-INT-319（API 测试成功）；前端提示未测 | I | sim | 新写 | `US-118` 对应测试文件 |
| AC-118-02 | [部分] 失败提示未测（替身可编程失败） | I | sim | 新写 | `US-118` 对应测试文件 |
| AC-118-03 | [部分] TC-INT-319（未测试配置不可选，由 llm_options 保证） | I | sim | 新写 | `US-118` 对应测试文件 |
| AC-118-04 | TC-INT-319、TC-INT-321 | I | sim | 新写 | `US-118` 对应测试文件 |
| AC-119-01 | TC-INT-313、TC-INT-314、TC-INT-315 | I | sim | 新写 | `US-119` 对应测试文件 |
| AC-119-02 | TC-INT-313、TC-INT-314、TC-INT-315 | I | sim | 新写 | `US-119` 对应测试文件 |
| AC-119-03 | TC-INT-313、TC-INT-314、TC-INT-315 | I | sim | 新写 | `US-119` 对应测试文件 |
| AC-119-04 | TC-INT-313、TC-INT-314、TC-INT-315 | I | sim | 新写 | `US-119` 对应测试文件 |
| AC-120-01 | [部分] TC-E2E-304（候选保存）；素材库 UI 展示未测 | E | sim | 新写 | `US-120` 对应测试文件 |
| AC-120-02 | [部分] TC-INT-313（来源筛选 API）；AI 来源筛选未单独用例 | I | sim | 新写 | `US-120` 对应测试文件 |
| AC-120-03 | TC-E2E-304 | E | sim | 新写 | `US-120` 对应测试文件 |
| AC-121-01 | TC-INT-311、TC-E2E-303 | E | sim | 新写 | `US-121` 对应测试文件 |
| AC-121-02 | TC-INT-311、TC-E2E-303 | E | sim | 新写 | `US-121` 对应测试文件 |
| AC-121-03 | [不可测] 素材库为空时的前端空态，无组件测试 | I | sim | 新写 | `US-121` 对应测试文件 |
| AC-122-01 | TC-INT-316、TC-INT-317、TC-E2E-303 | E | sim | 新写 | `US-122` 对应测试文件 |
| AC-122-02 | TC-INT-316、TC-INT-317、TC-E2E-303 | E | sim | 新写 | `US-122` 对应测试文件 |
| AC-122-03 | TC-INT-316、TC-INT-317、TC-E2E-303 | E | sim | 新写 | `US-122` 对应测试文件 |
| AC-122-04 | TC-INT-316、TC-INT-317、TC-E2E-303 | E | sim | 新写 | `US-122` 对应测试文件 |
| AC-122-05 | TC-INT-316、TC-INT-317、TC-E2E-303 | E | sim | 新写 | `US-122` 对应测试文件 |
| AC-123-01 | TC-INT-315、TC-E2E-303 | E | sim | 新写 | `US-123` 对应测试文件 |
| AC-123-02 | TC-INT-315、TC-E2E-303 | E | sim | 新写 | `US-123` 对应测试文件 |
| AC-123-03 | TC-INT-315、TC-E2E-303 | E | sim | 新写 | `US-123` 对应测试文件 |
| AC-124-01 | TC-INT-333、TC-E2E-304 | E | sim | 新写 | `US-124` 对应测试文件 |
| AC-124-02 | TC-E2E-304（视频成功入库） | E | sim | 新写 | `US-124` 对应测试文件 |
| AC-124-03 | [部分] 视频远端失败分支未单独覆盖 | I | sim | 新写 | `US-124` 对应测试文件 |
| AC-124-04 | TC-INT-333、TC-E2E-304 | E | sim | 新写 | `US-124` 对应测试文件 |
| AC-124-05 | TC-INT-333（未确认文案 409） | I | sim | 新写 | `US-124` 对应测试文件 |
| AC-124-06 | [部分] TC-E2E-304（任务创建）；审计记录未断言 | E | sim | 新写 | `US-124` 对应测试文件 |
| AC-124-07 | TC-INT-333、TC-E2E-304 | E | sim | 新写 | `US-124` 对应测试文件 |
| AC-125-01 | TC-INT-320、TC-E2E-304 | E | sim | 新写 | `US-125` 对应测试文件 |
| AC-125-02 | TC-INT-320、TC-E2E-304 | E | sim | 新写 | `US-125` 对应测试文件 |
| AC-125-03 | TC-INT-320、TC-E2E-304 | E | sim | 新写 | `US-125` 对应测试文件 |
| AC-126-01 | TC-INT-327、TC-INT-328 | I | sim | 新写 | `US-126` 对应测试文件 |
| AC-126-02 | TC-INT-327、TC-INT-328 | I | sim | 新写 | `US-126` 对应测试文件 |
| AC-126-03 | [部分] TC-INT-327（改名）；删除接口已实现但未单独用例 | I | sim | 新写 | `US-126` 对应测试文件 |
| AC-126-04 | TC-INT-327、TC-INT-328 | I | sim | 新写 | `US-126` 对应测试文件 |
| AC-127-01 | TC-INT-327、TC-INT-329 | I | sim | 新写 | `US-127` 对应测试文件 |
| AC-127-02 | TC-INT-327、TC-INT-329 | I | sim | 新写 | `US-127` 对应测试文件 |
| AC-127-03 | TC-INT-327、TC-INT-329 | I | sim | 新写 | `US-127` 对应测试文件 |
| AC-127-04 | [部分] 失效恢复 NORMAL 未单独用例 | I | sim | 新写 | `US-127` 对应测试文件 |
| AC-127-05 | TC-INT-327、TC-INT-329 | I | sim | 新写 | `US-127` 对应测试文件 |
| AC-128-01 | TC-INT-328、TC-INT-329、TC-INT-330、TC-E2E-302 | E | sim | 新写 | `US-128` 对应测试文件 |
| AC-128-02 | TC-INT-328、TC-INT-329、TC-INT-330、TC-E2E-302 | E | sim | 新写 | `US-128` 对应测试文件 |
| AC-128-03 | TC-INT-328、TC-INT-329、TC-INT-330、TC-E2E-302 | E | sim | 新写 | `US-128` 对应测试文件 |
| AC-128-04 | TC-INT-328、TC-INT-329、TC-INT-330、TC-E2E-302 | E | sim | 新写 | `US-128` 对应测试文件 |
| AC-128-05 | TC-INT-328、TC-INT-329、TC-INT-330、TC-E2E-302 | E | sim | 新写 | `US-128` 对应测试文件 |
| AC-128-06 | TC-INT-328、TC-INT-329、TC-INT-330、TC-E2E-302 | E | sim | 新写 | `US-128` 对应测试文件 |
| AC-128-07 | TC-INT-328、TC-INT-329、TC-INT-330、TC-E2E-302 | E | sim | 新写 | `US-128` 对应测试文件 |
| AC-129-01 | TC-INT-329、TC-INT-335 | I | sim | 新写 | `US-129` 对应测试文件 |
| AC-129-02 | [部分] 重试接口已实现，未单独用例 | I | sim | 新写 | `US-129` 对应测试文件 |
| AC-129-03 | TC-INT-329、TC-INT-335 | I | sim | 新写 | `US-129` 对应测试文件 |
| AC-129-04 | [部分] 重试再次失败未单独用例 | I | sim | 新写 | `US-129` 对应测试文件 |
| AC-130-01 | TC-INT-331、TC-INT-332、TC-E2E-302 | E | sim | 新写 | `US-130` 对应测试文件 |
| AC-130-02 | TC-INT-331、TC-INT-332、TC-E2E-302 | E | sim | 新写 | `US-130` 对应测试文件 |
| AC-130-03 | [部分] TC-INT-332（复制载荷）；剪贴板写入属浏览器 API | I | sim | 新写 | `US-130` 对应测试文件 |
| AC-130-04 | TC-INT-331、TC-INT-332、TC-E2E-302 | E | sim | 新写 | `US-130` 对应测试文件 |
| AC-130-05 | TC-INT-331、TC-INT-332、TC-E2E-302 | E | sim | 新写 | `US-130` 对应测试文件 |
| AC-131-01 | TC-INT-302 | I | sim | 新写 | `US-131` 对应测试文件 |
| AC-131-02 | TC-INT-302 | I | sim | 新写 | `US-131` 对应测试文件 |
| AC-131-03 | TC-INT-302 | I | sim | 新写 | `US-131` 对应测试文件 |
| AC-131-04 | [部分] 非管理员界面无入口属前端静态审查 | I | sim | 新写 | `US-131` 对应测试文件 |

共 112 条 AC；`[部分]` 表示自动化只覆盖服务端或纯函数部分，`[不可测]` 见下节。

## 测试数据需求

- 媒体样本：内存构造 PNG（89504E47…）、JPG（FFD8FF）、MP4（偏移 4..8 = ftyp）、非法 svg/文本。
- 外部服务：`FakeLlmClient`、`FakeImageGenClient`、`FakeVideoGenClient`、`FakeDraftAdapter`、`FakeRemoteFetcher`，每个用例 setUp 注入、tearDown 复位。
- 凭据：`CONTENT_CRED_ENC_KEY` 由测试设置生成临时钥；不写真实凭据。
- 数据唯一化：管理员/用户/媒体均由工厂生成，媒体文件在 `MEDIA_ROOT/content/` 下以 UUID 命名。

## 不可测项

| AC | 原因 |
|---|---|
| AC-121-03 | 素材库为空的前端空态，无组件测试（无浏览器 E2E 框架） |
| 真实平台联调 | 微信草稿、小红书/头条人工流程、火山方舟/DeepSeek/即梦的真实行为属 P4 禁止；仅替身 |
| 编辑器交互细节 | 工具栏清除格式、撤销/重做、弹窗确认等纯前端交互未做组件测试 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-105 | TC-INT-301/303/304、TC-E2E-301 | I/E |
| US-106 | TC-INT-304/305/307/308 | I |
| US-107 | TC-INT-306/307、TC-E2E-301 | I/E |
| US-108 | TC-E2E-301、TC-UNIT-344/345 | U/E |
| US-109 | TC-UNIT-301~320、TC-E2E-301 | U/E |
| US-110 | TC-UNIT-301~320、TC-E2E-301 | U/E |
| US-111 | TC-INT-311/313/317、TC-E2E-301/303 | I/E |
| US-112 | TC-UNIT-329~331、TC-E2E-301 | U/E |
| US-113 | TC-UNIT-316~318、TC-E2E-301 | U/E |
| US-114 | TC-INT-325/326/334、TC-UNIT-332~334 | U/I |
| US-115 | TC-INT-306、TC-E2E-302 | I/E |
| US-116 | TC-E2E-304、TC-INT-313 | I/E |
| US-117 | TC-INT-319/321、TC-UNIT-321~324 | U/I |
| US-119 | TC-INT-313/314/315 | I |
| US-120 | TC-E2E-304 | E |
| US-121 | TC-INT-311、TC-E2E-303 | I/E |
| US-123 | TC-INT-315、TC-E2E-303 | I/E |
| US-124 | TC-INT-333、TC-E2E-304 | I/E |
| US-125 | TC-INT-320、TC-E2E-304 | I/E |
| US-126 | TC-INT-327/328 | I |
| US-127 | TC-INT-327/329 | I |
| US-128 | TC-INT-328/329/330、TC-E2E-302 | I/E |
| US-130 | TC-INT-331/332、TC-E2E-302 | I/E |
| US-131 | TC-INT-302 | I |

Should Have：US-118 → TC-INT-319/321；US-122 → TC-INT-316/317、TC-E2E-303；US-129 → TC-INT-329/335。

## 补充覆盖（复审后新增，v1.1.0）

| 用例 | 覆盖 AC / 分支 |
|---|---|
| TC-INT-336 | AC-119-03 图片超限 413 `FILE_TOO_LARGE` |
| TC-INT-337 | AC-119-03 配额不足 413 `MEDIA_QUOTA_EXCEEDED` |
| TC-INT-338 | AC-114-01 内容 AI 限流 429 `CODE_RATE_LIMITED` |
| TC-INT-339 | AC-123-01 签名媒体 Range 206 / 416 |
| TC-INT-340 | AC-112-02 样式模板 PUT/DELETE API |
| TC-INT-341 | AC-126-03 平台账户删除 |
| TC-INT-342 | AC-129-01/02 草稿重试与非法重试 409 |
| TC-INT-343 | AC-129 中断：SENDING→UNKNOWN、PENDING→FAILED(INTERRUPTED) |
| TC-INT-344 | AC-120 候选素材 TTL 清理与引用保护 |
| TC-INT-345 | AC-124-03 视频远端失败 `REMOTE_FAILED` |
