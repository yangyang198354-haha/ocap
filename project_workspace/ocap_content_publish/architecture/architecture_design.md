<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-11T11:27:44+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>phase_status.md (clarifications 含 2026-11-11T11:23:30；GR-C-002 F01~F07；GR-A-003 conditions)</file>
    <file>architecture/architecture_design.md (1.0.0 APPROVED，被本版本返工)</file>
    <file>../ocap_registry_import/architecture/architecture_design.md (编号参照，至 ADR-044)</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：信息公开发布与多平台内容中心（INCREMENTAL）

> 编号接续：全仓已用最大 ADR-044 / MOD-038 / IFC-164（`git grep` project_workspace/*/architecture/ 核实），本次从 **ADR-045 / MOD-039 / IFC-165** 起。
> 本文只做设计到接口签名，不含实现代码。仓库事实以 `文件:行` 引用并已读取核实；GenPlatform 参考实现中的外部接口事实以 `[P11: 文件:行]` 引用（画像 P11-3，文件均在 `/root/myproject/GenPlatform/project_workspace/content_gen_platform/src/backend/apps/` 下，下文省略该前缀）；网页事实标 `[WEB: URL，2026-11-10]`；估计值标 `[ESTIMATE]`；待用户确认的缺省值标"待确认"。
> 用户已放行架构设计，**未放行开发**（1.0.0 时点）。

## 1.1.0 修订

> 触发：GR-C-002 FAIL（2026-11-11T10:55:44+08:00）与用户答复"1. 返工， 2. B， 3. 一起修"（`REWORK_AUTHORIZED`）。只改受影响部分；未列出的 ADR（045~050、052、054~059 的其余条款）沿用 1.0.0 且仍有效。新增外部事实一律按协议 §N 标出处；仓库外官方文档不在 P11 资料内的，标 `[UNSOURCED]` 并以 `CLARIFICATION_NEEDED(CRITICAL)` 上报（见"开放问题"Q-B1），**不凭记忆补全**。

| 变更 | 原因 | 落点 |
|---|---|---|
| 公众号凭据由"手工录入 access_token"改为保存 AppID/AppSecret，服务端自动换取并缓存访问令牌；失效口径重定义 | 用户 2026-11-11 选 B；GR-C-002-F06 | 新增 **ADR-060**；**ADR-051 的公众号条款被 ADR-060 取代**（其余条款沿用）；Q-A1、Q-A3 关闭 |
| 公众号草稿的封面与正文图片 | 用户 2026-11-11 选 B（"补封面与正文图片上传"）；GR-C-002-F06 | 新增 **ADR-061**（`Proposed`，**阻塞于 Q-B1**：端点与字段无出处）；Q-A2 并入 Q-B1 |
| 富文本颜色/粘贴兼容、标题级别、错误定位 | GR-C-002-F04 | 新增 **ADR-062**（服务端宽进严出 + 前端同口径归一化）；修订 ADR-046 的"标题层级""文字色"行的实现口径 |
| 审计落点补齐、导出临时文件、worker 单线程与心跳、行距/媒体/分镜渲染口径 | GR-C-002-F03、F05、F07 | 新增 **ADR-063**；修订 ADR-049 的并发条款、ADR-053 的临时文件条款、ADR-054 的批次审计条款 |
| 数据迁移增加 `content` 0002（平台账户令牌缓存列） | ADR-060 | 部署视图、module_design"数据迁移" |
| F01（`media.py` 类内 `list` 与注解冲突）、F02（前端保存失败仍发布）为实现缺陷 | GR-C-002 | 不涉设计；见 module_design"已知问题（指向开发）" |

## 架构概览

### 本次改动在现有系统中的位置

| 层 | 现状（基线，已核实） | 本次改动 |
|---|---|---|
| 后端 app | `INSTALLED_APPS` 为 14 个 `apps.*`（`backend/config/settings.py:22-38`），无信息公开、富文本、素材库、任务队列相关代码（PM 只读核查 + 本次 `ls backend/apps`） | 新增 `apps.content`（模型 + 服务 + 视图），一套手写单 app 迁移（画像 P6） |
| 鉴权 | `IsAdmin`（`apps/core/permissions.py:19-25`）、`IsMember`（`:28-34`）；游客身份即 `status=ACTIVE` 的普通账号（`permissions.py:13-14`），无单独角色 | 管理接口全部 `IsAdmin`（REQ-FUNC-119，不新增权限类）；展示接口 `IsMember`（REQ-FUNC-100） |
| 审计 | `AuditService.record` 只接受 `AUDIT_ACTIONS` 白名单内的动作，否则抛 `ValueError`（`apps/core/audit.py:10-23,57-59`）；`detail` 经 `_scrub` 脱敏，键名在 `SENSITIVE_KEYS` 内则置 `***`（`audit.py:25,35-52`） | 新增本批动作并登记到白名单；`detail` 本身不放凭据，`_scrub` 作为第二道防线 |
| 附件 | `AttachmentService.store` 一次性 `file.read()`、按用途白名单、魔数校验（`apps/core/attachments.py:16-33,63-90`），文件落 `MEDIA_ROOT`（`settings.py:86` = `backend/var/attachments`），下载由 Django `FileResponse` 经鉴权返回（`attachments.py:112-132`） | **不复用**：素材规格需可配置（OQ-6）、需分块写盘与总量配额、需 Range（视频）。沿用其魔数校验思路与存储根目录，另设 `MEDIA_ROOT/content/` 子目录（ADR-052） |
| 外部服务适配 | `WeChatClient` Protocol + `HttpWeChatClient` + `get_/set_wechat_client`（`apps/integrations/wechat.py:43-48,143-153`）；替身集中在 `apps/integrations/fakes.py`（`FakeWeChatClient` 等，`fakes.py:46`）；测试不得调用真实服务（画像 P4） | 沿用同一模式，新增 4 个 Protocol（LLM、文生图、视频、草稿箱）与对应替身（ADR-051） |
| 定时任务 | systemd oneshot `ocap-run-due-jobs` 每分钟触发 `manage.py run_due_jobs`（`deploy/systemd/ocap-run-due-jobs.{service,timer}`；`apps/jobs/management/commands/run_due_jobs.py`），无队列、无常驻 worker | 新增常驻 worker 单元 `ocap-content-worker`（ADR-049，**待用户决定**） |
| Web 前端 | 管理端 `frontend/src/admin/*.vue`，路由 `/admin` 下 `meta.admin`（`frontend/src/router/index.js:26-40`）；侧栏为 `AdminLayout.vue:7-14` 的 8 个 `router-link`；契约文件 `frontend/src/shared/api.js`（`admin` 对象走 `adminHttp`，如 `api.js:127-128`）；依赖仅 vue/pinia/vue-router/element-plus/axios（`frontend/package.json:12-18`） | 新增 5 个管理页 + 2 个门户页；富文本编辑器引入 Tiptap（ADR-046） |
| 小程序 | uni-app，`pages.json` 11 个页面；`utils/api.js` 为 `http.get/post` 形式；依赖仅 uni-app/pinia/vue（`miniprogram/package.json:12-18`） | 新增 `pages/info/{index,detail}` 与 `components/RichBlocks.vue`（结构化渲染，不用 `rich-text`，ADR-048） |
| 契约测试 | `backend/tests/integration/test_frontend_contract.py:30-61` 用正则解析两份 `api.js` 的 `http./adminHttp.` 调用并逐个 `resolve()`；`${...}` 依次代入 `1` 与 UUID；检查视图支持该方法与权限类相容（`:63-97`） | 新路由必须可被该解析器解析：路径字面量不含查询串，管理接口只用 `IsAdmin`，用户接口只用 `IsMember`（IFC-235/236） |

### 设计要点（一句话）

1. **内容以 ProseMirror JSON 为唯一事实源**，服务端按白名单 schema 校验并自行渲染成 HTML（Web 门户、公众号草稿、导出包）和结构化块（小程序），展示端不接触未经校验的 HTML（ADR-047/048，REQ-NFUNC-018）。
2. **富文本编辑器选 Tiptap 3**，覆盖 Q-CP-03=A 清单全部项（ADR-046）。
3. **所有慢操作（LLM 生成、文生图、AI 视频、一键保存多平台）走"数据库任务表 + 常驻 worker"**，前端轮询任务状态，不新增任何 Python 依赖、不引入 Redis/Celery（ADR-049）；该方案新增一个 systemd 单元，**需用户决定**。
4. **外部服务统一经 Protocol 适配层**；公众号走草稿箱接口，小红书、头条本批为"导出/复制人工粘贴"，适配层保留可替换接口（ADR-051，REQ-FUNC-122）。
5. **凭据 AES-256-GCM 加密存库**，密钥来自环境变量；凭据"只写不读"，异常信息、日志、审计一律脱敏（ADR-050，REQ-NFUNC-016）。
6. **素材存本地盘，对外只给带签名的短时 URL**；视频支持 Range（ADR-052）。
7. **素材规格、配额、视频时长等用户未答复的数值全部做成可配置参数**，缺省值标"待确认"（ADR-058，GR-A-003 condition b）。

### 关键质量属性（引 REQ-NFUNC）

| 属性 | 需求 | 设计落点 |
|---|---|---|
| 凭据不泄露 | REQ-NFUNC-016 | ADR-050：AES-256-GCM、只写不读、`SecretRedactor`、`requests` 异常消息含带 token 的 URL 必须脱敏 |
| 可审计 | REQ-NFUNC-017 | 12 个新增审计动作（IFC-188），同事务写入；视频与一键保存的"完成"由 worker 以任务创建者身份补记 |
| 展示端安全 | REQ-NFUNC-018 | ADR-047：schema 白名单 + 自渲染 + 转义；链接协议白名单；颜色/字号等样式值正则校验；不接受外链图片 |
| 资源受限（树莓派 4 GB，与 Freeark 同机） | 画像 P7；`/root/myproject/Freeark/CLAUDE.md`（树莓派 5、4GB RAM） | ADR-049：无 Redis、无 Celery、worker 串行为主；文件分块读写；zip 用临时文件；素材配额与剩余空间守卫 |
| 不动 Freeark | 画像 P7/P8 | 只改 ocap 单元与 ocap 8090 站点；systemd 单元名前缀 `ocap-` |

## 部署视图

仅画像 P7 存在的环境：**测试**（树莓派 `raspberrypi`，部署需用户确认）。生产环境不存在。

| 组件 | 运行单元 | 环境 | 变化 |
|---|---|---|---|
| Django API（含新增 `apps.content` 视图） | systemd `ocap-backend`（gunicorn `127.0.0.1:9000`，4 个 sync worker，`project_workspace/ocap/deployment/deployment_report.md:80,114`） | 测试 | **重启**；`.env` 新增 4 个键（键名见下，不写值） |
| 内容任务 worker（新） | systemd `ocap-content-worker`（`Type=simple`，常驻，`manage.py run_content_worker`），单元文件 `deploy/systemd/ocap-content-worker.service`（新建，风格同 `ocap-run-due-jobs.service`） | 测试 | **新增并启动**（需用户批准，ADR-049） |
| 到期任务 | `ocap-run-due-jobs.timer` | 测试 | 不变（content 的清理由 worker 自带的 housekeeping 承担，不改 `run_due_jobs`） |
| 数据库迁移 | `manage.py migrate`（`content` 0001 新表；**1.1.0 增 0002**：`content_platformaccount` 加 4 个可空列作令牌缓存，手写、可逆，见 ADR-060 与 module_design"数据迁移"） | 测试 MySQL 库 `ocap` | 随部署执行 |
| 公众号接口出口（**1.1.0 新增**） | worker 进程经本机出口访问 `api.weixin.qq.com`（取令牌与草稿接口，出处见 module_design"领域与外部依赖出处"） | 测试（树莓派经家宽/frp 出口，出口 IP 未知） | 取令牌可能因"服务器出口 IP 未加入公众号白名单"被拒（错误码 40164 的类别映射见 [CODE: backend/apps/integrations/wechat.py:13]）；**IP 白名单属公众号后台配置，不在仓库内**，E2 前由用户确认 |
| 媒体文件 | `/home/yangyang/ocap/backend/var/attachments/content/`（`MEDIA_ROOT` 子目录） | 测试 | 新增目录；**回滚快照 `backend-<TS>.tar.gz` 会把 `var/` 打进去**（画像 P7 快照 `-C /home/yangyang/ocap backend`，`.claude/skills/ocap-deploy/SKILL.md` DEPLOY-001），媒体增长后快照膨胀，E1 须处理 |
| ocap nginx 站点（8090） | `/etc/nginx/sites-available/ocap` | 测试 | `client_max_body_size` 须不小于 `max(图片, 视频)上限 + 2 MB`；配置不在仓库内，需只读核实（见 module_design"受影响的运行单元"）；**不动** Freeark 的 nginx 段以外内容 |
| Web 前端 | `npm run build -- --base=/ocap/` 产物替换 `web/ocap` | 测试 | 重新构建、发布 |
| 小程序 | uni-app 构建与发布（RU-4，不在 ocap-deploy skill 范围） | — | 重新构建；需微信侧发布 |

新增 `.env` 键（只列键名）：`CONTENT_CRED_ENC_KEY`、`CONTENT_CRED_ENC_KEY_PREV`（可选，轮换用）、`CONTENT_MEDIA_PATH_PREFIX`、`CONTENT_PUBLIC_BASE_URL`。

## ADR

### ADR-045: 新增独立后端 app `apps.content`，按职责分文件，不触碰既有 app 的数据模型

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-099~122、REQ-NFUNC-016~018 全部为新增能力，现有代码无相关实现（需求基线"现有系统基线"表）。画像 P3：后端在 `backend/apps/<app>/`；画像 P6：迁移手写、单 app 范围；画像 P8：禁止提交 makemigrations 产物。
- Options（被排除）：① 把模型塞进 `apps.core`——`core` 是平台基础（审计、附件、配置），塞入业务会让 `core` 反向依赖 `accounts` 等，且迁移不再是单 app 范围；② 拆成 4~5 个小 app（post/media/ai/platform）——模型间外键与任务表互相引用，会产生跨 app 迁移依赖，违反"单 app 范围"便利；③ 不新建 app，分散到 `resolutions` 等——语义不符。
- Decision: 新建 `apps.content`，模型与迁移在一个 app 内（`migrations/0001_initial.py` 手写）；代码按职责分文件（richtext、media、posts、jobs、ai_jobs、drafts…，见 module_design）；外部服务适配放 `apps/integrations/`（沿用 `wechat.py` 模式）；对 `apps.core` 只做两处增量修改：`audit.py` 白名单加动作，`settings.py`/`urls.py` 注册。操作人用 `created_by_admin_id: IntegerField`（不建指向 `accounts` 的外键，沿用 `Attachment.owner_id`/`SystemConfig.updated_by_admin_id` 做法，`core/models.py:35,52`，同时不触发 `user_refs` 外键登记检查）。
- Consequences: 正向——迁移风险集中在新表，无既有表改动，回滚即删表；负向——`apps.content` 文件数较多，需 module_design 的依赖层次约束防止互相引用。

### ADR-046: 富文本编辑器选型——Tiptap 3

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-101/102（段落、对齐、颜色、超链接；"基础格式清单"= 标题层级、段落与行距、加粗/斜体/下划线/删除线、对齐、字号、文字色与背景色、超链接、有序/无序列表、引用、分割线、图片、视频、撤销/重做、清除格式；清单外的表格、代码块、公式、表情、卡片本批不纳入，AC-110-04 要求这些功能**不出现**），REQ-FUNC-103（图片/视频插入）、REQ-FUNC-104（分页标记）。Web 前端为 Vue 3 + Element Plus（`frontend/package.json:12-18`）。约束：要能禁用/不装清单外功能；能插入自定义节点（视频、分页标记）；输出结构化文档以便服务端校验（ADR-047）；对公众号草稿 HTML 的兼容性取决于我们自己渲染 HTML（ADR-047），而非编辑器自带 HTML 序列化。
- Options:
  - A. **Tiptap 3**（基于 ProseMirror，无头，MIT）。`@tiptap/vue-3` 3.33.1 对 Vue `^3.0.0` [WEB: https://registry.npmjs.org/@tiptap/vue-3/latest，2026-11-10]；`@tiptap/starter-kit` 3.33.1 依赖含 bold、italic、strike、underline、link、heading、blockquote、bullet/ordered list、horizontal-rule、hard-break、code/code-block 等 [WEB: https://registry.npmjs.org/@tiptap/starter-kit/latest，2026-11-10]；`@tiptap/extension-text-style` 3.33.1 导出 `color`、`font-size`、`line-height`、`background-color` 子路径 [WEB: https://registry.npmjs.org/@tiptap/extension-text-style/latest，2026-11-10]；`@tiptap/extension-text-align` 3.33.1、`@tiptap/extension-image` 3.33.1，均 MIT [WEB: https://registry.npmjs.org/@tiptap/extension-text-align/latest 与 …/extension-image/latest，2026-11-10]。优——功能按扩展逐项装配，清单外功能不装即不出现；自定义节点（Video、PageBreak）是一等公民；文档模型是 JSON，天然适配 ADR-047；活跃维护（3.33.x）。缺——无现成工具栏，需用 Element Plus 自建（约 20 个按钮）；StarterKit 默认带 `code`/`code-block`，须在配置里关闭以满足 AC-110-04；包数量多（见 tech_stack）。
  - B. **Quill 2**（BSD-3-Clause，2.0.3；依赖 lodash-es、parchment、quill-delta、eventemitter3）[WEB: https://registry.npmjs.org/quill/latest，2026-11-10]。优——自带 snow 主题与工具栏，上手快；Delta 格式也是结构化 JSON。缺——Delta 为扁平操作序列，嵌套列表/引用/自定义块（视频、分页标记）需自写 Blot，服务端校验与渲染要多写一层 Delta→树转换；Vue 3 无官方封装；行距、背景色的"清单等价"需自定义 attributor。
  - C. **wangEditor 5**（MIT，5.1.23）[WEB: https://registry.npmjs.org/@wangeditor/editor/latest，2026-11-10]。优——国产、界面接近公众号编辑器，开箱即用工具栏。缺——npm 记录显示 5.1.23 发布于 2022-11-14，`modified` 同日，此后无新版本 [WEB: https://registry.npmjs.org/@wangeditor/editor，2026-11-10]，即近四年未维护；基于 slate 0.72 的旧版本；输出 HTML 为主，服务端要自行解析 HTML（引入 ADR-047 方案 B/C 的复杂度）；自带表格、代码高亮模块须逐个排除。
- Decision: 选 **A（Tiptap 3）**。理由：REQ-FUNC-102 清单可逐项映射到扩展（下表），REQ-NFUNC-018 要求服务端可校验——JSON 文档模型最利于白名单校验，且 C 已停止维护、B 缺少自定义块与 Vue 封装。工具栏用 Element Plus 自建（沿用既有 UI 库）。
- 清单覆盖（Q-CP-03=A）：

| 清单项 | Tiptap 扩展 / 实现 | 说明 |
|---|---|---|
| 标题层级 | `heading`（StarterKit），限 1~4 级 | 服务端校验 level∈1..4 |
| 段落与行距 | `paragraph` + text-style `line-height` | 行距取值 1.0~3.0（校验） |
| 加粗/斜体/下划线/删除线 | StarterKit 的 bold/italic/underline/strike | |
| 对齐 | `@tiptap/extension-text-align`（left/center/right/justify） | 作用于 paragraph、heading |
| 字号 | text-style `font-size` | 10~48px（校验） |
| 文字色/背景色 | text-style `color`、`background-color` | 仅 `#rgb/#rrggbb/#rrggbbaa`（校验） |
| 超链接 | StarterKit 的 link，`protocols` 限 http/https/mailto/tel | 空或明显无效网址不加入（AC-109-03） |
| 有序/无序列表、引用、分割线 | StarterKit 的 list、blockquote、horizontal-rule | |
| 图片 | `@tiptap/extension-image` 改造：节点属性只存 `mediaId`（不存任意 URL） | 来源仅素材库/当场上传（REQ-FUNC-103） |
| 视频 | **自定义** `Video` 节点（`mediaId`） | 仓库内新增扩展 |
| 撤销/重做 | StarterKit 内的历史扩展 | 实现期核对包内是否含 undo/redo，不含则装 `@tiptap/extensions` 的对应项 |
| 清除格式 | `unsetAllMarks` + `clearNodes` 命令 | 工具栏按钮 |
| 分页标记（REQ-FUNC-104） | **自定义** `PageBreak` 节点 | 仓库内新增扩展 |
| **不提供**：表格、代码块、公式、表情、卡片 | 不安装；StarterKit 配置 `code: false, codeBlock: false` | AC-110-04 |

- 与公众号草稿 HTML 的兼容性：编辑器不直接产出发给平台的 HTML；平台用 HTML 由服务端 `render_doc(mode="inline")` 生成（全部样式内联、无 class、无脚本），见 ADR-047、ADR-051。
- 小程序端渲染：小程序不含编辑器，读取同一份 JSON 经服务端转换的"块"结构，由 `RichBlocks.vue` 渲染，见 ADR-048。
- Consequences: 正向——清单可验收、清单外功能天然缺席；JSON 模型贯通 Web/小程序/平台导出。负向——新增 ~9 个 npm 包（见 tech_stack，均 MIT）；工具栏要自建（约 1 人日量级 `[ESTIMATE]`）；Tiptap 3 的 `text-style` 子路径 API 以实现期安装版本为准，若 `line-height` 的存储位置与本文假设（textStyle 标记属性）不同，校验器两处均接受（见 module_design IFC-169）。

### ADR-047: 内容存储格式与净化——ProseMirror JSON 为事实源，服务端按白名单校验并自行渲染

- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-018（含脚本的正文在展示端脚本执行次数=0，其余格式保留，AC-107-04/108-04）；REQ-FUNC-100（保持编辑时格式与版式）；REQ-FUNC-104（样式模板、分页）；REQ-FUNC-117（保存到公众号草稿需要 HTML）。管理员可能粘贴外来内容；也可能绕过前端直接调 API。
- Options:
  - A. **JSON 为事实源 + 自写白名单校验 + 自写渲染器**（Web 得 HTML，小程序得块，平台得内联样式 HTML）。优——不存在"解析不可信 HTML"这一步，渲染对节点类型、属性值都走白名单+转义，REQ-NFUNC-018 由构造保证；同一份 JSON 服务三端，分页位置在服务端一次计算，两端一致（AC-113-02）；无新依赖。缺——要自写并测试校验器与渲染器（约 400~600 行 `[ESTIMATE]`）；前端若升级 Tiptap 新增节点类型，服务端要同步放行。
  - B. **HTML 为事实源 + `nh3`（Rust 版 ammonia 绑定）净化**。`nh3` 0.3.7，MIT，发布 2026-08-23，含 `manylinux_2_17_aarch64` 轮子 [WEB: https://pypi.org/pypi/nh3/0.3.7/json，2026-11-10]。优——成熟库，白名单配置即可。缺——新增原生依赖（Pi 上安装失败则无退路）；小程序端无法使用 HTML（ADR-048）需另写 HTML→块解析；分页要在 HTML 上切分；样式值（`style` 属性）的细粒度校验仍要自写。
  - C. **HTML 为事实源 + 标准库 `html.parser` 自写白名单净化**。优——无依赖。缺——自写 HTML 净化器是公认易出绕过的安全组件；同样存在小程序与分页问题。
  - 不考虑 `bleach`：PyPI 说明"不再维护，不再发布包括安全问题在内的版本"[WEB: https://pypi.org/pypi/bleach/json，2026-11-10]。
- Decision: 选 **A**。存储 `ContentPost.doc`（JSON）；写入时 `validate_doc`（IFC-169）按白名单校验并**规范化**（丢弃未知属性，如图片的 `src`；保留的只有 schema 允许的节点/标记/属性）；读取时 `render_pages`（IFC-170）生成 `html`（Web）或 `blocks`（小程序）。
- 白名单：节点 `doc/paragraph/heading(1-4)/bulletList/orderedList/listItem/blockquote/horizontalRule/hardBreak/image/video/pageBreak/text`；标记 `bold/italic/underline/strike/link/textStyle`；属性值规则（颜色 hex、字号 10~48px、行距 1.0~3.0、对齐四值、`href` 协议 http/https/mailto/tel 且 ≤2048 字符、`mediaId` 必须是 UUID 且存在）。不接受任何外部 `src`、`style`、`class`、`on*`。
- Consequences: 正向——满足 REQ-NFUNC-018 且无新依赖，三端渲染一致；负向——校验器/渲染器是本批最大的自研安全组件，需专项单元测试（含脚本注入、`javascript:` 链接、超深嵌套、超大文档）；上限 `content.post.max_doc_bytes`（缺省 1 MiB，待确认）、深度 12、节点数 20000 防资源耗尽。

### ADR-048: 小程序端展示——结构化块渲染，不用 `rich-text` 与 `web-view`

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-100/101/103/104、US-108（小程序展示加粗/居中/红字/图片，超链接可见可点击；视频可播放，AC-123-01）、US-113（分页与 Web 一致）、REQ-NFUNC-018。
- Options:
  - A. uni-app `rich-text` 组件渲染 HTML。优——一行代码。缺——官方说明 `rich-text` "会屏蔽所有节点的事件，链接和图片无法点击"（App-vue 平台除外）[WEB: https://uniapp.dcloud.net.cn/component/rich-text.html，2026-11-10]，直接违反"超链接可点击"；页面未提及视频支持；不受信标签整节点丢弃。
  - B. `web-view` 加载 H5 页面。优——复用 Web 渲染。缺——需要在微信侧配置业务域名并放置校验文件（本批未被授权改动小程序后台配置，且外网入口依赖 frp/Freeark nginx，不受 ocap 控制）；与小程序原生导航体验割裂。
  - C. **服务端输出块（blocks）+ 小程序自定义组件 `RichBlocks.vue`**（`view/text/image/video` 原生组件逐块渲染）。优——事件可控（链接点击、图片预览）、视频用原生 `video`；与 Web 共用同一 JSON 和分页；无第三方插件。缺——要写一个递归组件；样式只覆盖白名单属性（正好与 ADR-047 一致）。
- Decision: 选 **C**。块结构见 IFC-170（`Block`/`Inline` 类型）。链接点击行为：复制链接到剪贴板并提示"链接已复制，请在浏览器中打开"`[ASSUMPTION A-3]`（小程序内打开任意外链需微信侧业务域名配置，本批未授权）。
- Consequences: 正向——满足 AC-108-01 的"可见可点击"（点击=复制），视频原生播放；负向——"点击跳转"在小程序端降级为复制，需用户确认（开放问题 A-3）；`<image>/<video>` 加载媒体靠带签名 URL（ADR-052）。

### ADR-049: 异步任务执行方式——数据库任务表 + 常驻 worker（systemd）

- Status: Proposed（**新增运行单元与资源占用，需用户决定**）
- Type: decision
- Context: 异步需求：REQ-FUNC-120（AI 视频生成，"异步过程，管理员可看到任务状态"，AC-124-01 "立即返回'生成中'，页面不被阻塞"）；REQ-FUNC-117/118（一键保存多个平台，逐平台结果，失败不影响其他）；REQ-FUNC-105/106（LLM 文案、文生图，可能 10~120 秒）。参考实现的单次耗时：LLM 流式超时 120 s [P11: llm_gateway/providers.py:129]；文生图超时 120 s [P11: image_generator/doubao_image_client.py:33]；公众号草稿请求超时 30 s [P11: publisher/publishers.py:72]；即梦提交/查询超时 30 s [P11: video_generator/jimeng_client.py:119,139]；视频生成本身需轮询 [P11: jimeng_client.py:116-131,133-165]。ocap 现状：gunicorn 4 个 sync worker（`deployment_report.md:80`），`--timeout` 未知（默认 30 s，见 registry_import tech_stack R1）；树莓派 5、4GB RAM，与 Freeark 同机共存（`/root/myproject/Freeark/CLAUDE.md`；画像 P7）；画像 P8 不禁止 Redis/Celery，但无容器。GenPlatform 用 Celery（`video_generator/tasks.py:22`）。
- Options:
  - A. **请求进程内线程**（gunicorn worker 里 `threading.Thread`）。优——无新单元、无新依赖。缺——gunicorn 重启（每次部署都会重启 `ocap-backend`）与 worker 超时回收会直接杀线程，任务永久停在"进行中"；sync worker 被长任务占用不可控；无法限制并发；内存占用叠加在 4 个 worker 上。
  - B. **数据库任务表 + 一个常驻 worker 进程**（`manage.py run_content_worker`，systemd `ocap-content-worker`）。优——零新增 Python 依赖、零新增中间件；任务状态在 MySQL，重启可恢复（租约过期重新入队或标记中断）；单进程串行/小并发，资源可控（`MemoryMax`、`Nice`）；与现有 `run_due_jobs` 同一套 `manage.py` + systemd + `.env` 机制，运维一致；视频用"提交→WAITING_REMOTE→按 `next_run_at` 轮询"的状态机，等待期间不占线程。缺——新增 1 个常驻进程（一份 Django 进程的常驻内存，约 60~100 MB `[ESTIMATE]`，**待 E1 在测试机实测**）；需自写领取/租约/回收逻辑（约 150 行）；吞吐低（串行，管理员极少）。
  - C. **Celery + Redis**（参考 GenPlatform）。优——成熟、重试/定时/并发现成。缺——新增 `celery`、`redis` 两个 Python 依赖与一个系统服务 `redis-server`，再加 worker（可能还需 beat）共 2~3 个常驻单元；prefork 默认并发=CPU 核数（树莓派 5 为 4 核）若不显式 `-c 1` 会起多个子进程；常驻内存估计 150~300 MB `[ESTIMATE]`，与 Freeark 抢 4GB；在管理员极少的场景下收益低；Redis 持久化/升级成为新的运维面。
  - D. **复用现有 `ocap-run-due-jobs` 每分钟 timer**，在 `run_due_jobs` 里顺带处理任务。优——零常驻内存。缺——任务最多等 60 s 才被取走，LLM 文案"点生成等一分钟"体验差；视频轮询粒度 60 s 可接受但 LLM/文生图不行；`run_due_jobs` 是 `oneshot`，`TimeoutStartSec=300`，长任务会堵住下一轮；且要改既有 `jobs` app，扩大改动面。
- Decision: 选 **B**。理由：REQ-FUNC-120 与 AC-124-01 要求不阻塞并可见状态；D 的 60 s 延迟不适合交互式生成；C 的两个新依赖与 2~3 个常驻进程在 4GB 共享机器上不成比例；A 在频繁部署重启下不可靠。B 只增加一个常驻进程，且**所有状态在数据库**，worker 可随时重启。
- 约束与参数：并发固定为 1（**1.1.0：`--concurrency` 已移除，见 ADR-063**；1.0.0 原文为"缺省 1、上限 2"）；任务类型 `LLM_TEXT/IMAGE_GEN/VIDEO_GEN/DRAFT_PUSH`；租约 `lease_seconds=300`（须大于任一单次调用超时）；`RUNNING` 且租约过期的任务由 `requeue_expired` 处理：幂等类（LLM_TEXT、IMAGE_GEN）至多重试 1 次，非幂等类（DRAFT_PUSH 发送中、VIDEO_GEN 提交中）**不自动重试**，置为"状态未知/已中断"，让管理员核对后手动重试（避免重复草稿、重复计费，见 ADR-054/055）；每个任务有最终态（SUCCEEDED/FAILED），视频有总等待上限 `content.video.max_wait_seconds`（缺省 1800 s，待确认），不会永久停在"处理中"；SIGTERM 时完成当前步骤后退出（`TimeoutStopSec=150`）；单元 `MemoryMax=400M` `[ESTIMATE]`、`Nice=10`、`Restart=on-failure`。
- 资源评估汇总（均 `[ESTIMATE]`，**须在 E1 测试机实测 `ps -o rss`/`free -m` 后复核**）：A 0 个新进程但不可靠；**B +1 进程 ≈ 60~100 MB**；C +2~3 进程 ≈ 150~300 MB；D +0 MB 但延迟 ≤60 s。预检标准沿用部署 skill："可用内存 ≥ 500 MB"（`SKILL.md` §4 第 3 项）。
- Consequences: 正向——无新依赖，状态可观测（`JobRun(job_name="content_worker")` 心跳，沿用 `core/models.py:71-75`），部署重启不丢任务；负向——**多一个需要部署和监控的 systemd 单元**，需用户批准；吞吐有限（管理员极少，可接受）；Pi 上 worker 与 gunicorn 竞争 CPU（`Nice=10` 缓解）。

### ADR-050: 凭据加密——AES-256-GCM（`cryptography`），"只写不读"，全链路脱敏

- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-016（平台认证信息、LLM 凭据、视频与文生图账号信息加密保存；界面、接口响应、日志、审计中原文出现次数=0）、REQ-FUNC-116/121、画像 P6（凭据不得硬编码）、用户确认 P3=A（后台录入、加密存库，密钥经环境变量）。现状：`audit.py:25` 的 `SENSITIVE_KEYS` 只按键名脱敏，对值内嵌凭据无效；`requirements.txt` 无加密库（`backend/requirements.txt:1-8`）。参考实现为 AES-256-GCM（GenPlatform `core/encryption.py:1-43`，`BinaryField` 存密文：`settings_vault/models.py:27`）。已知泄露面：公众号接口把 `access_token` 放在 URL 查询串 [P11: publisher/publishers.py:76]，`requests` 的异常消息会带完整 URL。
- Options:
  - A. **`cryptography` 的 `AESGCM`**（AES-256-GCM，12 字节随机 nonce，AAD=行标识）。`cryptography` 50.0.2，许可 Apache-2.0 OR BSD-3-Clause，发布 2026-09-30，含 `manylinux_2_17_aarch64`/`manylinux_2_28_aarch64` 轮子 [WEB: https://pypi.org/pypi/cryptography/50.0.2/json，2026-11-10]。优——AEAD，防篡改，AAD 可绑定记录防止密文被换行使用；与参考实现一致；Pi 上有预编译轮子。缺——新增 1 个原生依赖（Debian 13 系统 Python 的具体版本以目标机为准，未知）。
  - B. `cryptography` 的 `Fernet`。优——API 更简单、自带时间戳与版本。缺——AES-128-CBC + HMAC 组合，无 AAD 绑定记录；与参考实现不一致，无明显收益。
  - C. 仅标准库自组合（HMAC-SHA256 流密码）。缺——标准库没有 AEAD，自行组合加密构造属于不应自研的安全组件，**排除**。
  - D. 凭据只放 `.env`（不入库）。缺——违背用户确认的 P3=A（后台录入）。**排除**。
- Decision: 选 **A**。密文格式 `version(1B) || nonce(12B) || ciphertext+tag`，明文为 JSON（键→值），AAD=`b"ocap.content|<表>|<主键>"`；密钥 `CONTENT_CRED_ENC_KEY`（base64 编码 32 字节），可选 `CONTENT_CRED_ENC_KEY_PREV` 供轮换（解密先试主钥再试旧钥，保存时总用主钥）。密钥缺失/格式错 → 保存凭据的接口返回 `503 CREDENTIAL_VAULT_NOT_CONFIGURED`，**不让整个后端启动失败**（区别于 `DJANGO_SECRET_KEY` 的硬失败，`settings.py:9-18`：内容中心是可选功能，不应因它缺钥让业主端不可用），并增加 Django system check 警告（沿用 `core/checks.py` 的注册方式）；测试设置下按 `DJANGO_ALLOW_EPHEMERAL_SECRET` 同样规则生成进程内随机钥。
- "只写不读"与脱敏规则（REQ-NFUNC-016 的实现点）：
  1. 数据模型只存 `secret_blob`（密文）与 `secret_keys`（已保存的键名列表，非敏感）；任何序列化器**没有**凭据字段，响应中只给 `{key: bool}` 形式的"是否已保存"；
  2. 凭据明文只在 worker/请求处理的局部变量中短暂存在，传给 `*Client` 的构造参数；
  3. `SecretRedactor(secrets)`（IFC-167）：对所有来自外部调用的异常消息、响应片段做**值替换**（把已知凭据值、URL 查询串中的 `access_token=…` 替换为 `***`）后才写入 `ContentJob.error_message`、`DraftPush.error_message`、日志、审计 `detail`；
  4. 审计 `detail` 只写键名与"已更新"标记，不写值；`_scrub` 作为第二道防线；
  5. 日志不记录请求体/URL 全文（只记录平台、状态码、耗时）。
- Consequences: 正向——静态数据加密、记录绑定、可轮换；负向——新增依赖 `cryptography`（见 tech_stack 风险）；**密钥丢失=所有已保存凭据不可恢复**（需管理员重新录入），密钥备份是运维责任；`.env` 须在部署前加键。

### ADR-051: 外部服务适配层——Protocol + Http 实现 + 替身；公众号自动存草稿，小红书/头条人工粘贴，接口可替换

- Status: Proposed；**1.1.0：公众号凭据字段与令牌条款 Superseded by ADR-060**（下方 `wechat_mp` 条的"凭据字段 `access_token`"与 Consequences 中"手工粘贴令牌"作废），其余条款（Protocol 结构、`capability`、小红书/头条人工粘贴、LLM/文生图/视频出处）沿用
- Type: constraint-driven
- Context: 用户确认（画像 P11-3、phase_status 2026-11-10T23:36:07）：P1=A（GenPlatform 参考实现视为资料）、P2=A（小红书、头条本批走导出/复制，接口层预留）、P3=A（测试只用 `fakes.py` 新增替身）、P4=是（GenPlatform 实现线上调用成功过）。REQ-FUNC-117（仅存草稿箱，不做正式发布）、REQ-FUNC-122、C-26/C-30、画像 P4（测试不得调用真实服务）、协议 §N。现有模式：`wechat.py:43-48,143-153` + `fakes.py:46`。
- 被排除方案：① 直接复制 GenPlatform 的 `BasePlatformPublisher`（`publishers.py:19-22`）——它的接口是 `publish(...)`，语义是**正式发布**，且小红书端点为 placeholder [P11: publishers.py:54]、头条为正式发布接口 [P11: publishers.py:121]，都不能当草稿接口；② 为小红书/头条凭记忆写"草稿接口"——无出处，违反协议 §N-1/N-2；③ 公众号采用参考实现的"draft/add 之后立刻 freepublish/submit" [P11: publishers.py:88-92]——违反 REQ-FUNC-117（仅草稿）。
- Decision: 在 `apps/integrations/` 新增 4 组 Protocol（`LlmClient`、`ImageGenClient`、`VideoGenClient`、`DraftAdapter`），各自带 `Http*` 实现、`get_*/set_*` 注入点（同 `wechat.py:143-153`），替身加到 `fakes.py`。`DraftAdapter` 声明 `capability: "AUTO_DRAFT" | "MANUAL_EXPORT"`：
  - `wechat_mp` = AUTO_DRAFT，只调用 `draft/add`：`POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=<token>`，请求体 `{"articles":[{"title","content","author":""}]}`，以响应 JSON 含 `media_id` 判成功，超时 30 s [P11: publisher/publishers.py:76-87]；凭据字段 `access_token` [P11: publishers.py:71]。**不调用** `freepublish/submit`（publishers.py:88-92）。
  - `xiaohongshu`、`toutiao` = MANUAL_EXPORT：服务不发起任何网络调用，生成"需人工粘贴"结果并提供内容包/复制（ADR-053）。后续接入自动草稿时，只需注册新的 `DraftAdapter` 实现并把 `capability` 改为 `AUTO_DRAFT`，其余代码（任务、历史、UI）不变。
  - 视频：即梦 `submit_task`/`poll_status` 的签名、端点、`req_key`、状态映射按 [P11: video_generator/jimeng_client.py:14-17,39-85,87-131,133-165]；文生图按 [P11: image_generator/doubao_image_client.py:30-33,146-185,207-262]；LLM 的 base URL 与 `chat/completions`/`models` 按 [P11: llm_gateway/providers.py:10-11,106,129-154,191,218-243]；连通测试按 Ark `GET /api/v3/models`、10 s 超时、401/429/其他的错误映射 [P11: settings_vault/ark_validator.py:20-21,44,70-98]。
  - 未被 P11 资料覆盖的接口事实一律在 module_design"领域与外部依赖出处"表标 `[UNSOURCED]`，并给出设计上的兜底（见开放问题 Q-A1~Q-A5）。
- Consequences: 正向——升级到真实草稿接口只换适配器；测试完全离线（`FakeLlmClient` 等）；负向——公众号凭据 `access_token` 为"手工粘贴的访问令牌"（参考实现只接受已有 token，获取/续期流程不在 P11 资料内），令牌过期会表现为"认证失效"，需管理员重新录入（Q-A1）。

### ADR-052: 素材存储与访问——本地盘 + 签名短时 URL + Range

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-103/111~114（上传、AI 生成入库、复用、删除保护）、C-29（图片 ≤10 MB 且仅 jpg/jpeg/png；视频 ≤10 MB，格式待 OQ-6；总配额未给）、REQ-FUNC-100（仅登录用户可见）、US-123（视频可播放）。技术约束：浏览器 `<img>/<video>` 与小程序 `<image>/<video>` 无法携带 `Authorization` 头；现有附件下载靠 axios 带头取 Blob（`attachments.py:112-132` 经 `IsMemberOrAdmin`）；`FileResponse` 不处理 Range（视频拖动/部分播放器依赖）；目标机磁盘与 `client_max_body_size` 未知（不在仓库内，registry_import R1）。
- Options:
  - A. **签名短时 URL**：详情接口返回的 HTML/块中的媒体地址带 `?sig=`（Django `TimestampSigner`，salt 固定，值=媒体 id，缺省 1 小时有效）；`GET /content/media/<id>/file` 校验签名后返回文件，视图自己实现单段 Range。优——`<img>/<video>/<image>` 直接可用；无新依赖；URL 只授权单个媒体、限时；推送平台/导出包也可用同机制（更长 TTL）。缺——持有 URL 者在有效期内可取该文件（对"登录可见"是有意放宽到"持链接者"，TTL 限制暴露）；日志中会出现 `sig`。
  - B. **不可猜测的公开 URL**（uuid4 路径，无签名/无过期）。优——最简单。缺——永久有效、无法撤销，且违背"未登录者不展示"的精神。
  - C. **前端取 Blob 再赋 `src`**（Web 用 axios Blob + `URL.createObjectURL`；小程序用 `uni.downloadFile` 带头下载到临时文件）。优——全程鉴权头，无 URL 授权。缺——所有展示点都要写加载器；视频整体下载后才可播放（10 MB 可接受但体验差）；公众号推送与导出包无法使用。
  - D. nginx `X-Accel-Redirect` 内部位置直发文件。优——Range、`sendfile` 由 nginx 处理。缺——需要改 ocap 站点 nginx 配置并重载，且路径别名需与 `MEDIA_ROOT` 对齐；本批尽量不增加 nginx 改动（作为后续优化保留）。
- Decision: 选 **A**，视图内实现 `Range: bytes=a-b` 单段（206/416，`Accept-Ranges: bytes`），响应头 `X-Content-Type-Options: nosniff`、`Cache-Control: private, max-age=300`、`Content-Disposition: inline`。存储：`MEDIA_ROOT/content/<yyyymm>/<uuid>.<ext>`（相对路径入库，沿用 `attachments.py:79-90` 的"uuid 文件名 + 相对路径"做法）；写盘用分块（`UploadedFile.chunks()`），边写边计数与计算 sha256，超限即中止并删除半成品；扩展名+魔数双校验（jpg `FFD8FF`、png `89504E470D0A1A0A`、mp4 的 `ftyp` 位于偏移 4~8，魔数思路沿用 `attachments.py:25-32`）；总量配额与磁盘剩余空间守卫（ADR-058 参数）；AI 生成素材先作为候选（`state=CANDIDATE`）入库，管理员"保存到素材库"后转 `SAVED`，候选超过 `content.media.candidate_ttl_hours`（缺省 24，待确认）由 worker 清理。远程下载（AI 结果 URL）只允许 https、解析后的地址必须是公网地址（拒绝环回、私网、链路本地），禁止自动跟随重定向到未校验地址，限制字节上限与超时（防 SSRF 与磁盘写满，协议 §L）。
- Consequences: 正向——三端统一取图取视频，推送/导出可复用，无新依赖；负向——"持链接者限时可读"是对"仅登录可见"的有意放宽，需用户知晓（开放问题 A-4）；`Range` 自实现需测试（边界：`bytes=0-`、`bytes=-N`、越界）；E1 须核实 nginx `client_max_body_size` 与磁盘（含快照膨胀）。

### ADR-053: 无草稿接口平台的"内容包导出"与"一键复制"——服务端生成 zip，剪贴板由前端写入

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-122、US-130（导出内容包含正文文字、图片文件、视频文件；一键复制正文并提示"已复制"；无图无视频也可导出；导出写审计）。
- Options:
  - A. **服务端生成 zip**（标准库 `zipfile`，临时文件，`FileResponse` 返回；媒体文件用 `ZIP_STORED` 避免对已压缩图片/视频再耗 CPU）。优——无新依赖；一次下载拿到全部文件；审计在服务端一处写入。缺——生成时占临时磁盘（最多一个内容包大小）。
  - B. 前端逐个下载文件 + 前端拼 zip（需 JSZip 等新 npm 依赖）。缺——新依赖、多次请求、审计难以聚合。
  - C. 只给"复制"不给文件。缺——违反 AC-130-02。
- Decision: 选 **A**。包内：`content.txt`（纯文本，段落以空行分隔）、`content.html`（`inline` 模式 HTML，媒体引用改为包内相对路径 `media/xxx`）、`media/` 下的原文件（以序号+原名命名，防重名）、`README.txt`（说明样式需在平台编辑器中重设、列出未保留的样式项）。"一键复制"由 `GET …/copy` 返回 `{text, html}`，前端用 `navigator.clipboard.write`（`text/html` + `text/plain`）写入，失败时回退为选中文本提示手动复制。
- Consequences: 正向——满足 AC-130-01~05；负向——复制富文本依赖浏览器剪贴板权限（HTTP 内网访问 `http://192.168.31.51:8090/` 属非安全上下文，`navigator.clipboard` 可能不可用，需回退方案：`document.execCommand('copy')` 或文本框手动复制，实现期验证）。

### ADR-054: 一键保存多平台——一次批次一个任务、平台间隔离、"至多一次"发送、未知态需人工核对

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-117（一键保存、各平台样式不能保留的项逐平台提示）、REQ-FUNC-118（逐平台结果、单平台重试、历史）、REQ-FUNC-116（认证失效提示并标记账户）、US-128/129。风险：重复发送会在平台草稿箱产生重复草稿，且 worker 在"远端已成功、本地未落库"之间崩溃时无法判断。
- Options:
  - A. **至少一次**：崩溃后自动重试。优——不丢。缺——可能重复草稿；无法清理（没有已出处的删除草稿接口）。
  - B. **至多一次 + UNKNOWN**：发送前把 `DraftPush.status=SENDING` 落库；任务中断且该行仍为 `SENDING` 时置 `UNKNOWN`，提示"结果未知，请到平台草稿箱核对后重试"；`FAILED/UNKNOWN` 可由管理员单独重试。优——不产生静默重复；与 REQ-FUNC-118 的"单平台重试"一致。缺——极少数情况需要人工核对。
- Decision: 选 **B**。一次"一键保存"= 一个 `batch_id` + 一个 `DRAFT_PUSH` 任务，任务内顺序处理各 AUTO 平台，单平台异常被捕获只影响自己；MANUAL 平台在请求内直接建行并置 `MANUAL_REQUIRED`（不进任务）；批次结束由 worker 写**一条**审计（`CONTENT_DRAFT_PUSHED`，`detail.results=[{platform,status,error_code}]`，AC-128-07）。认证失效（适配器返回 `AUTH_EXPIRED`）→ 行置 `FAILED(error_code=AUTH_EXPIRED)`、账户 `auth_status=EXPIRED`，覆盖更新凭据后恢复 `NORMAL`（AC-127-03/04）。"样式不能保留项"由适配器的 `unsupported_features` 与 ocap 自身限制（如 `pageBreak` 在草稿中被展平、公众号草稿中视频不随正文发送 `[ASSUMPTION A-5]`）合并后写入 `DraftPush.unsupported`。
- Consequences: 正向——无静默重复；每平台结果独立可重试；负向——UNKNOWN 态增加一类状态；公众号草稿中图片/视频能否显示取决于平台对外链媒体的处理（`[UNSOURCED]`，开放问题 Q-A2），失败时管理员可改用内容包。

### ADR-055: AI 视频生成流程——提交 → 轮询 → 下载入库；文案切分为有限个分镜；每个片段一个素材

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-120/121、US-124/125；本批不提供分镜编辑/裁剪/调序（超出范围第 5 项）。即梦客户端以 `scenes`（含 `scene_index/duration_sec/transition/scene_prompt/narration`）提交，返回 `task_id`；轮询返回状态与 `video_urls`（片段 URL 列表）[P11: video_generator/jimeng_client.py:87-131,133-165]。字段取值范围（时长、transition 枚举）不在 P11 登记资料中；参考实现的邻近文件 `scene_generator.py:23-24,103-104` 使用时长 2~10 秒、`cut/fade/push_pull`，**不是 P11 登记的资料**，只作设计参考并标 `[UNSOURCED]`。
- Options:
  - A. **单分镜**：整篇文案作为一个 `scene_prompt`。优——最简。缺——长文案超出即梦提示长度限制的可能性未知 `[UNSOURCED]`，且片段单一。
  - B. **按段落切成至多 N 个分镜**（`N=content.video.max_scenes`，缺省 5，`duration_sec=content.video.scene_seconds` 缺省 5，`transition="cut"`），每段的文字同时作 `scene_prompt` 与 `narration`；超过 N 段则按字数均衡合并。优——无需再调 LLM；确定性强、可测试。缺——画面质量依赖段落写法；N、时长、transition 取值需用户确认。
  - C. 先调 LLM 生成分镜脚本（参考实现做法）。缺——多一次付费调用与失败面，超出"无分镜编辑"的本批范围。
- Decision: 选 **B**。流程：创建任务时校验"已配置视频服务"（AC-124-04）与"文案已确认"（AC-124-05：视频只能基于一篇内容的"已确认文案"发起——管理员在编辑器中点"确认文案"（IFC-197）后记录文案摘要，文案之后被改动则需重新确认；见 IFC-218）；状态机 `QUEUED → RUNNING(提交) → WAITING_REMOTE(轮询) → RUNNING(下载) → SUCCEEDED/FAILED`；`task_id` 一拿到立即落库（此前崩溃→"提交状态未知"，不自动重试，避免重复计费）；轮询间隔 `content.video.poll_interval_seconds`（缺省 15）；总等待上限 `content.video.max_wait_seconds`（缺省 1800）；成功后逐个片段 URL 走远程下载守卫（ADR-052）并入库为 `AI_GENERATED/SAVED` 视频素材（体积上限 `content.media.ai_video_max_bytes`，缺省 50 MiB，待确认——C-29 的 10 MB 针对上传，AI 视频是否同限用户未答复）；**不拼接片段**（不引入 ffmpeg，树莓派 CPU 与依赖成本）。
- Consequences: 正向——确定性、可离线测试（`FakeVideoGenClient`）；负向——分镜策略为 `[ASSUMPTION A-6]`；多片段时每个片段是独立素材，管理员自行选用；即梦账号与计费行为无法在测试中验证（仅替身）。

### ADR-056: LLM 配置、选用与连通测试语义

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-109（火山方舟或 DeepSeek，全站一份，默认 DeepSeek，未配置不得生成）、REQ-FUNC-110（连通测试，仅测试成功的配置可选用）、US-117/118、画像 P11-3。约束来源：用户答复 Q-CP-15=A；参考实现的 provider 设计（`llm_selection/design.md`，`providers.py`）。
- 被排除方案：每位管理员各自配置（Q-CP-15 未选）；把可选模型清单做成数据库配置表（参考实现 OPEN-02 已选代码常量，`providers.py:13-27` 注释）。
- Decision: 数据模型 `ServiceConfig` 以 `service_type`（`LLM_DEEPSEEK`、`LLM_VOLCANO`、`IMAGE_ARK`、`VIDEO_JIMENG`）为唯一键，全站一份。LLM 的 base URL 固定为常量 [P11: providers.py:10-11]，不允许配置；`model` 为字符串参数，提示清单取自代码常量 [P11: providers.py:18-27 的 FALLBACK_MODELS]，也允许手填（校验 `^[A-Za-z0-9._:/-]{1,64}$`），因模型会下线。默认模型：`LLM_DEEPSEEK` 为 `deepseek-chat`（出处同上）；"默认"= 有 `is_default=true` 的那份，从未设置则 DeepSeek。连通测试 = `GET {base}/models`，`Authorization: Bearer <key>`，10 s 超时，200→成功，401→`KEY_INVALID`，429→`QUOTA_EXCEEDED`，其余/网络→`UNREACHABLE` [P11: settings_vault/ark_validator.py:20-21,44,70-98；DeepSeek 的 `/models` 路径见 providers.py:106]。凭据或模型一变更，`last_test_ok` 重置为空（须重新测试，AC-118-03）。`GET /admin/content/llm/options` 只返回 `last_test_ok=true` 的配置。生成使用流式 `stream=true` 的 `chat/completions`，按 `data:` 行累积 `choices[0].delta.content`，遇 `[DONE]` 结束 [P11: providers.py:129-154,218-243]。
- Consequences: 正向——与参考实现一致，测试成功才可用；负向——DeepSeek 对 401/429 的语义套用 Ark 的映射为 `[ASSUMPTION]`（HTTP 通用语义，P11 未单独登记）；"文生图服务"在 REQ-FUNC 中无独立配置需求，本设计按 REQ-FUNC-106 + REQ-NFUNC-016 增加 `IMAGE_ARK` 配置（开放问题 Q-A4）。

### ADR-057: 样式模板与分页——令牌化白名单 + 服务端分页

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-104（内置若干套 + 管理员可自定义并保存；预览；分页含"阅读按篇幅分页（页长由模板配置）"与"编辑器分页标记"，Q-CP-12=A、Q-CP-13=C）、US-112/113（两端分页位置一致；一页内容不拆块）。内置套数与页长默认值用户未给（OQ-2）。
- Options:
  - A. **令牌化模板**：模板=一组白名单样式令牌（`font_family_key`、`font_size`、`line_height`、`paragraph_spacing`、`text_color`、`heading_color`、`link_color`、`quote_border_color`、`accent_color`、`page_chars`），各自校验类型与范围；渲染器据令牌输出 CSS 变量（Web）/内联样式（草稿）/样式对象（小程序）。优——无自由 CSS，不引入样式注入面（与 REQ-NFUNC-018 一致）；三端可同值渲染。缺——表达力受令牌集限制。
  - B. 模板=一段自由 CSS 文本。缺——样式注入（`url()`、`expression`、覆盖整页）、小程序无法使用 CSS 文本。
- Decision: 选 **A**。内置模板作为**代码常量**（`BUILTIN_TEMPLATES`，主键形如 `builtin:classic`），不入库、不需数据迁移；缺省 3 套（简洁/公告/正式，待确认）。自定义模板入库（`StyleTemplate`）。`ContentPost.style_key` 为 `builtin:<name>` 或 `custom:<id>`；模板被删除时文章回落到缺省内置模板。分页由 `paginate_doc(doc, page_chars)` 在服务端完成：先按 `pageBreak` 节点切；再在顶层块之间累计字符数，达到 `page_chars` 即换页，**不拆分单个块**；`page_chars` 缺省 1500（待确认），范围 200~20000。字体族只允许 `sans`/`serif` 两个键映射到系统字体栈（不加载网络字体）。
- Consequences: 正向——两端分页位置一致（同一服务端结果）；无样式注入面；负向——令牌集是产品取舍，需用户确认；超长单块（如一个很长的段落）无法在页内再拆分。

### ADR-058: 用户未答复的数值做成可配置参数（OQ-2 / OQ-6 / 总配额）

- Status: Proposed
- Type: constraint-driven
- Context: GR-A-003 condition：OQ-6（视频格式清单与大小）与素材总配额用户未答复 → 设计为可配置参数、给缺省值并标"待用户确认"；OQ-2 列出的响应时间、并发、正文大小、保留期、视频时长/数量、模板套数/页长、生成参数项同样未给。
- 被排除方案：把数值写死在代码/校验器里（改值需发版）；新建参数表与管理 UI 之外的第二套配置机制（`SystemConfig` 已是现有机制，`core/config.py:12-41`）。
- Decision: 参数以 `SystemConfig`（键值，`core/models.py:48-52`）存储，键统一前缀 `content.`；默认值与校验规则集中在 `apps/content/conf.py`（`CONTENT_DEFAULTS`/`CONTENT_RULES`），读取走 `ContentSettings.get`（先 `SystemConfig.get`，缺省回落代码默认）；管理端提供 `GET/PUT /admin/content/settings`（IsAdmin，逐键范围校验，改动写审计 `SYSTEM_CONFIG_CHANGED` 沿用已有动作）。**不改** `core/config.py` 的 `EDITABLE_KEYS` 与 `SystemConfigView`。缺省值与状态见 module_design IFC-168 表，凡无用户依据者标"待确认"。
- Consequences: 正向——用户答复后只改一个参数、无需发版；负向——参数多（约 28 项），UI 须标示"待确认"项；校验器必须在读与写两侧都生效，防止 `SystemConfig` 被直接改成非法值。

### ADR-059: 前后端入口与契约——沿用现有路由与 api.js 约定；信息公开独立于"决议公开"

- Status: Proposed
- Type: constraint-driven
- Context: 画像 P6（新增路由/API 必须同步 `frontend/src/shared/api.js` 与 `miniprogram/utils/api.js`）、契约测试（见"架构概览"表最后一行）、OQ-3（信息公开与决议公开关系未说明，暂按独立功能）。
- 被排除方案：把信息公开并入 `Resolutions.vue`（OQ-3 未授权）；管理端新建独立前端工程（违背现有结构）。
- Decision: 管理端新增 `frontend/src/admin/` 下 5 个页面（内容列表与编辑器、素材库、AI 服务与提示词模板与参数、平台账户、内容中心设置）并在 `router/index.js` 的 `/admin` 子路由与 `AdminLayout.vue` 导航中登记；门户新增 `/info`、`/info/:id`，入口放在 `Home.vue` 的卡片区（不改底部 Tab）；小程序新增 `pages/info/index`、`pages/info/detail`，入口放在 `pages/index/index` 卡片区。`api.js` 里调用一律写成 `http.get('/…')`/`adminHttp.post('/…')` 字面量形式，路径不含查询串（查询参数走 params 选项），以满足契约测试的正则（`test_frontend_contract.py:30-33`）。媒体地址（`<img src>`）不经 `api.js`，由后端在响应中给出相对 API 前缀的路径。
- Consequences: 正向——契约测试可自动覆盖新路由；负向——管理端侧栏增至 12 项，导航拥挤（可后续折叠分组，不属本批）。

### ADR-060: 公众号访问令牌——服务端用 AppID/AppSecret 换取，加密落库缓存，单飞刷新，失效后重取一次（1.1.0 新增）

- Status: Proposed（取代 ADR-051 中公众号凭据字段与令牌条款、Q-A1 的"管理员手工录入 access_token"）
- Type: decision
- Context: REQ-FUNC-116（认证信息预先保存、不回显、失效提示并标记，不提供独立检测）、REQ-FUNC-117（公众号自动存草稿）、REQ-NFUNC-016（凭据原文出现次数=0）、REQ-NFUNC-017；用户 2026-11-11 原话"2. B"（保存 AppID/AppSecret 自动换取令牌）；GR-C-002-F06（令牌约定期失效、`auth_errcodes` 缺省为空使 HTTP 200 的令牌错误不标失效）。现状：适配器凭据字段为 `access_token`（`backend/apps/integrations/draft.py:61`），失效判定仅 HTTP 401/403 + `auth_errcodes`（`draft.py:80-90`，`conf.py:36` 缺省 `[]`）。**可作出处的现有调用**：`GET https://api.weixin.qq.com/cgi-bin/token`，参数 `grant_type=client_credential`、`appid`、`secret`，响应 `access_token`、`expires_in`、`errcode` [CODE: backend/apps/integrations/wechat.py:97-103]；令牌提前 300 秒视为过期 [CODE: wechat.py:94]；`expires_in` 缺省 7200 [CODE: wechat.py:103]；`errcode` 40164 归类为 `IP_NOT_WHITELISTED` [CODE: wechat.py:13,59-62]。该现有调用用的是小程序的 AppID，PM 指令（2026-11-11）确认其可作为公众号取令牌的出处。加密保险库沿用 [CODE: backend/apps/content/vault.py]。
- Options:
  - A. **数据库加密缓存 + 条件更新"单飞"锁 + 提前量刷新 + 令牌类错误后强制重取一次**。优——令牌跨进程/跨重启复用（部署会重启 worker，`--once` 与常驻 worker 也可能并存），取令牌次数最少；缓存列加密，满足 REQ-NFUNC-016；锁与冷却在库里，多进程一致；失效判定集中。缺——要 0002 迁移（4 个可空列）；要自写单飞与冷却逻辑（约 80 行 `[ESTIMATE]`）。
  - B. **进程内存缓存**（沿用 `HttpWeChatClient._token_cache` 模式，`wechat.py:94-103`）。优——无迁移、最简。缺——worker 每次重启丢缓存；多进程各自取令牌，无法跨进程限频与冷却，多进程取令牌之间的相互影响无出处 `[UNSOURCED]`；失败重取逻辑仍要自写。
  - C. **不缓存，每次推送前换令牌**。优——无状态。缺——每个批次每个平台每次重试都多一次外部调用；取令牌的频次限制无出处 `[UNSOURCED]`，批量/重试时风险上升。
  - D. **手工录入令牌**（1.0.0 的 Q-A1 决定）。缺——令牌会过期，真实使用中反复失效（GR-C-002-F06）；已被用户 2026-11-11 推翻。**排除**。
- Decision: 选 **A**。
  1. **凭据**：`wechat_mp` 的 `credential_fields = (appid, appsecret)`，均必填、均"只写不读"（AC-127-02 要求认证信息原文出现次数=0，AppID 也不回显），沿用 `CredentialVault` 加密到 `PlatformAccount.secret_blob`（AAD 不变）。
  2. **令牌缓存**：`PlatformAccount` 新增 `token_blob`（加密的 `{"access_token": …}`，AAD `ocap.content|content_platformaccount_token|<pk>`，与凭据密文 AAD 不同，防止两列密文互换）、`token_expires_at`、`token_refreshed_at`、`token_lock_until`，均可空；令牌明文只存在于局部变量与 HTTP 层。
  3. **有效判定**：`token_expires_at - margin > now`；`margin` 缺省 300 秒（出处同上，做成 `content.wechat_mp.token_margin_seconds`）；`expires_in` 缺失或非正整数按 7200（出处同上）。
  4. **单飞刷新**：需要刷新时先以条件 `UPDATE`（`token_lock_until IS NULL OR token_lock_until < now`）抢锁，锁时长 = 请求超时 + 15 秒；抢到者调用接口、写缓存、释放锁；没抢到者每 0.5 秒轮询缓存，至多 10 秒，仍无令牌则返回 `TOKEN_BUSY`（可重试的 FAILED，**不标失效**）。不依赖 `select_for_update`（SQLite 测试与 MySQL 通用，与 ADR-049 的领取方式一致）。
  5. **失效后重取一次**：草稿接口返回"令牌类错误"时，强制刷新并重发**至多一次**。"令牌类错误"= HTTP 401/403，或 `errcode` ∈ `content.wechat_mp.token_errcodes`；该配置项**缺省为空（`[UNSOURCED]`，Q-B1）**，为空时采用保守兜底：令牌取自缓存（非本次新取）且响应为明确错误（有非零 `errcode`、无 `media_id`）才重取一次。**超时/连接中断（未收到响应）不重发**，避免重复草稿（ADR-054）。强制刷新受冷却限制：`content.wechat_mp.refresh_cooldown_seconds`（缺省 60）内同一账户已刷新过、且缓存令牌与失效令牌不同，则直接复用缓存中较新的令牌，不再调用接口。
  6. **错误分类与"失效"口径**（REQ-FUNC-116/AC-127-03 的判定口径，取代 Q-A3）：**"认证失效"＝服务端用已保存的 AppID/AppSecret 无法取得令牌，且原因属"凭据被拒"类**（如 AppSecret 错误或被重置）。判定只看配置化的错误码清单，因为具体码无出处：

     | 情形 | 判定依据 | `DraftOutcome` | 账户 `auth_status` |
     |---|---|---|---|
     | 未保存 appid 或 appsecret | 本地判断 | `FAILED` / `NO_CREDENTIALS` | `UNSET`（已有口径） |
     | 取令牌返回 `errcode` ∈ `content.wechat_mp.auth_errcodes` | 配置，缺省 `[]` `[UNSOURCED]`（Q-B1） | `AUTH_EXPIRED` | → `EXPIRED`，提示"认证已失效，请重新认证"（AC-127-03）；覆盖更新凭据后 → `NORMAL`（AC-127-04） |
     | 取令牌返回 `errcode` ∈ `content.wechat_mp.ip_errcodes` | 配置，缺省 `[40164]`，出处 [CODE: wechat.py:13] | `FAILED` / `IP_NOT_WHITELISTED`，提示"服务器出口 IP 未加入公众号 IP 白名单" | **不变**（改凭据无法修复，不标失效） |
     | 取令牌其他非零 `errcode`、无 `access_token`、非 JSON | 响应 | `FAILED` / `UPSTREAM`，消息带 `errcode` 与脱敏后的错误描述（字段名无出处 `[UNSOURCED]`，读不到则只带 `errcode`；≤200 字符） | 不变 |
     | 网络错误/超时（取令牌或发草稿） | 异常 | `FAILED` / `NETWORK`（消息经脱敏） | 不变 |
     | 他进程持锁超过 10 秒 | 本地 | `FAILED` / `TOKEN_BUSY` | 不变 |
     | 草稿接口令牌类错误，重取后第二次仍失败 | 以第二次响应为准，再按上表分类 | 同上 | 同上 |

     在 `auth_errcodes` 缺省为空期间，AppSecret 错误会表现为 `UPSTREAM`（管理员能在失败原因里看到 `errcode`/`errmsg`），**不会自动标失效**；用户提供真实错误码后只改配置，不改代码（Q-B1 清单第 4 项）。
  7. **泄露面**：取令牌的 `secret` 在查询串中（出处同上）。所有 `requests` 异常与响应片段只经 `SecretRedactor([appsecret, access_token])` 后才进入 `DraftPush.error_message`、日志、审计（ADR-050 规则不变）；日志只记 `redact_url(url)`。
  8. **不复用 `HttpWeChatClient.stable_access_token`**：它是小程序 AppID/Secret 的内存缓存（`wechat.py:92-104`），凭据来源与存放方式不同；复用会把公众号凭据塞进 `settings`，违背"后台录入、加密存库"（P3=A）。
- Consequences: 正向——手工粘贴令牌的流程消失；令牌复用与失败重取有明确边界，重启不丢缓存；认证失效与 IP 白名单问题分开提示，管理员知道该改什么。负向——`auth_errcodes`/`token_errcodes` 的真实取值仍无出处，缺省为空时"自动标失效"在真实环境不会触发（只有替身测试可验证 AC-127-03），依赖 Q-B1；新增 0002 迁移与 4 个列；出口 IP 白名单是用户在微信侧的配置，本批不可代办；令牌缓存列是新增的加密敏感数据，密钥丢失时缓存作废、自动重取（可恢复，不同于凭据）。

### ADR-061: 公众号草稿的封面与正文图片——端点与字段无出处，先定结构、功能开关默认关闭，待 Q-B1 定稿（1.1.0 新增）

- Status: Proposed（**阻塞于 Q-B1**；定稿前不得实现带 `[UNSOURCED]` 标记的接口）
- Type: decision
- Context: 用户 2026-11-11 选 B 时要求"补封面与正文图片上传"；GR-C-002-F06 提示公众号草稿可能需要封面素材编号、正文图片可能需先上传到微信侧才能显示——**这只是 PM 依据自身知识的提示，不是出处**。仓库内唯一的草稿接口出处只有 `title`、`content`、`author` 三个字段 [P11: GenPlatform publisher/publishers.py:76-79]，用户确认该调用线上成功过（画像 P11-3、P4=是）。上传素材、封面字段、草稿接口对图片 URL 的处理，在 P11 资料与仓库代码中均无出处（`git grep` 仓库无相关调用）。依协议 §N-2，影响接口契约的事实（端点、字段、错误码）不得自行补全。
- Options（按"如何处置未决事实"分，选项文字同 Q-B1）:
  - A. **用户把微信官方文档相关页面存入仓库**（如 `docs/p11/wechat_mp/`），登记为 P11 资料后按资料定稿。优——契约完整、可核对。缺——需用户整理文档。
  - B. **用户逐项口头确认**端点/字段/错误码/限制（清单见 Q-B1）。优——快。缺——无文档可复核，出处只能记为"用户确认"。
  - C. **降级**：封面改为管理员在账户设置里手工填一个已有的封面素材编号；正文图片本批不上传，仍以带长期签名的外链出现。优——用户工作量最小，不依赖上传接口。缺——"封面素材编号在草稿接口里叫什么字段"仍须用户确认；图片能否显示仍是 `[UNSOURCED]`；与用户"补图片上传"的原意不符。
  - D. **分阶段**：本批只实现 ADR-060（令牌自动获取）+ 现有已出处的草稿请求（仅 title/content/author）；封面/图片上传做成适配器内的**关闭状态扩展点**，由用户在测试环境真实联调后依据结果提供资料再启用。优——不阻塞令牌部分；P4 证据表明至少某种账户下三字段足以成功。缺——封面/图片能力本批不交付，与用户原意不符。
- Decision（暂定，待用户在 Q-B1 选择）: **推荐 A**。在用户选定前，设计只固定"不依赖未决事实"的部分：适配器内部结构（取令牌 → 〔可选〕上传封面 → 〔可选〕上传正文图片并改写 HTML 中的图片地址 → 发草稿），两个〔可选〕步骤由 `content.wechat_mp.upload_cover`、`content.wechat_mp.upload_content_images`（缺省均 `false`）开关控制；对应的 `WechatMpApi.upload_cover` / `upload_content_image` 方法与 `DraftArticle` 的封面字段在 module_design 中**全部标 `[UNSOURCED]`，只有签名占位，开发不得实现 HTTP 细节**。封面选取规则（设计口径，不涉外部事实）：文档中按出现顺序的第一张图片；无图片时是否报错由配置 `content.wechat_mp.require_cover`（缺省 `false`）控制，报错码 `COVER_REQUIRED`（`FAILED`）。正文图片改写：`DraftPayload.html_for(url_overrides)` 以"素材 id → 微信侧地址"映射重新渲染，未映射的素材保持原签名外链。
- Consequences: 正向——令牌部分（ADR-060）不被阻塞；任何选项落地后改动局限在 `WechatMpApi` 两个方法、`DraftArticle` 一个字段和一个配置开关。负向——封面/图片上传的真实行为在资料到位前无法验证（P4 禁止测试调用真实端点，只能依靠替身）；用户选 A/B/C 之一后须回 GROUP_B 补一次出处并去掉 `[UNSOURCED]`。

### ADR-062: 富文本颜色、粘贴与错误提示——服务端"宽进严出"归一化，前端同口径预归一化（1.1.0 新增）

- Status: Proposed（修订 ADR-047 的"校验失败即 400"口径在样式类属性上的适用范围；白名单本身不放宽）
- Type: decision
- Context: REQ-FUNC-101/102（颜色、标题、图片的编辑能力）、REQ-FUNC-103（图片仅来自素材库/当场上传）、REQ-NFUNC-018（展示端脚本执行次数=0，其余格式保留）；GR-C-002-F04：`schema.py` 的 `COLOR_RE` 只收 `#hex`（`backend/apps/content/richtext/schema.py:11,30-33`），粘贴内容里常见的 `rgb()`/`rgba()` 颜色、无 `mediaId` 的外链图片（`schema.py:125-129`）、标题级别 >4（`schema.py:107-108`）都会让**整篇保存 400**；前端工具栏颜色是文本框（`frontend/src/admin/editor/Toolbar.vue:24`）。Tiptap 对粘贴 HTML 的解析行为为 PM 推断，需实测（F04 括号）。
- Options:
  - A. **服务端宽容归一化（样式类与可丢弃类问题丢弃/归一化并返回 `warnings`，结构类与资源类问题仍 400）＋前端同口径预归一化**。优——保存不再因粘贴杂质整篇失败；服务端是权威，绕过前端的请求同样被约束；前端预归一化让用户在编辑器里看到的就是将被保存的结果。缺——两端各有一份颜色归一化实现，需共享测试向量；API 对非法样式由"拒绝"变为"丢弃并提示"，与 1.0.0 的严格测试口径不同（严格版 `validate_doc` 保留，视图改用宽容版）。
  - B. **只在前端归一化**，服务端保持严格。优——服务端无变化。缺——粘贴路径不止编辑器（API 直调、将来其他入口）；前端遗漏任何一种情形仍整篇 400。
  - C. **服务端保持严格，前端只提示**。缺——用户仍无法保存粘贴内容，F04 不解决。
- Decision: 选 **A**。归一化与丢弃规则（服务端权威，前端对同一表格取同样结果）：

  | 输入 | 处理 | 提示 |
  |---|---|---|
  | `color`/`backgroundColor`：`#rgb`/`#rrggbb`/`#rrggbbaa` | 原样保留 | — |
  | `rgb(r, g, b)`、`rgba(r, g, b, a)`（逗号形式，通道 0~255 整数，`a` ∈ [0,1]） | 归一化为 `#rrggbb`；`a`<1 时为 `#rrggbbaa` | `NORMALIZED` |
  | 其他颜色写法（颜色名、`hsl()`、`var()`、`url()`、百分比、空格语法等） | **丢弃该属性**，文字保留 | `DROPPED` |
  | `fontSize`/`lineHeight`（含块级行距）越界、非 `px`、非数字 | 丢弃该属性（不做 `pt`/`em` 换算） | `DROPPED` |
  | 标题级别 >4 | 钳为 4 | `CLAMPED` |
  | 链接 `href` 协议不在 http/https/mailto/tel 或含空白/超长 | 丢弃 `link` 标记，文字保留 | `DROPPED` |
  | 图片/视频节点 `mediaId` 缺失或非 UUID（含外链图片、`data:` 图片） | **丢弃该节点**，不转存、不下载 | `DROPPED` |
  | 未知节点类型 | 丢弃该节点（含子树） | `DROPPED` |
  | 深度/节点数/字符数/字节数超限、根不是 `doc`、`content` 非数组、`text` 非字符串 | **仍然 400**（结构类/资源类） | `CONTENT_INVALID_DOC` |

  **外链图片的处理决定：丢弃并提示，不转存。** 理由：转存需要服务端下载公网地址（SSRF 与版权风险，ADR-052 的远程下载守卫只授权给 AI 生成结果）和管理员逐张确认的新交互，超出本批范围；管理员通过素材库或当场上传插入图片即可（REQ-FUNC-103）。**XSS 安全不下降**：归一化后的颜色再次过 `COLOR_RE`（只可能是 `#hex`）；丢弃只会减少内容；`on*`/`style`/`class`/外部 `src` 本来就被白名单剔除；链接协议白名单不变。
  **前端**：粘贴时在 Tiptap 的 `transformPastedHTML` 阶段先把 `rgb()/rgba()` 归一化、移除无 `mediaId` 的 `<img>`，并把丢弃数量用 `ElMessage` 提示；编辑器标题限制为 1~4 级（StarterKit `heading.levels=[1,2,3,4]`，粘贴的 `<h5>/<h6>` 因此降为段落）；工具栏颜色改为 Element Plus 取色器（已有依赖，输出 `#rrggbb`）。
  **错误提示要指明位置**：仍然 400 的 `CONTENT_INVALID_DOC` 增加 `details.block_index`（顶层块序号，从 0 起）与 `details.block_type`；宽容路径返回的 `warnings[]` 同样带 `block_index`。前端据此提示"正文第 N 个段落/块：<中文原因>"，保存**失败时不得继续发布/确认**（F02）。
- Consequences: 正向——粘贴 Word/网页内容不再整篇失败；安全白名单不变；位置可定位。负向——颜色归一化两份实现（后端 Python、前端 JS）须用同一份测试向量（module_design IFC-169/241）；"丢弃"是静默损失内容的一种，靠 `warnings` 与前端提示补偿；Tiptap 粘贴实际产出需开发实测并补用例。

### ADR-063: 运行与审计口径修订——批次审计落点、素材删除审计、导出临时文件、worker 单线程与心跳、渲染口径（1.1.0 新增）

- Status: Proposed（修订 ADR-049 的并发条款、ADR-053 的临时文件条款、ADR-054 的批次审计条款、ADR-047 的渲染覆盖面）
- Type: constraint-driven
- Context（约束来源）: REQ-NFUNC-017 与 AC-122-03、AC-128-07、AC-130-04（审计）；画像 P7（树莓派与 Freeark 同机共存，资源受限）；GR-C-002-F03、F05、F07。被排除方案：为审计另建审计表（`AuditService` 已满足，`audit.py:61-79`）；为 `--concurrency` 实现多线程（本批无并发需求，且会放大令牌单飞与 SQLite 测试的复杂度）；导出包落盘后由定时清理（有窗口期残留、且要新增清理任务）。
- Decision:
  1. **素材删除审计（AC-122-03）**：`MediaService.delete` 在删除成功时写 `CONTENT_MEDIA_DELETED`（已在 1.0.0 登记，但漏调用），与删行同一事务，文件在提交后删除；被引用而拒绝删除不写审计。方法签名改为接收 `admin`（需要操作人名称）。
  2. **批次审计（AC-128-07）**：**每个批次恰好 1 条** `CONTENT_DRAFT_PUSHED`，`object_id` 为 `batch_id`，`detail.results` 含该批次**全部**行（人工/无凭据/自动）的 `{platform, mode, status, error_code}`。批次中没有需入队的自动行（全为人工或无凭据）时，由 `start_batch` 在同一事务内直接写；有任务时由 worker 在任务结束（含 `on_interrupted`）时按 `batch_id` 重新汇总全部行后写，而不是只汇总本任务的行。单平台重试自成 1 个新批次、同样写 1 条。
  3. **新增审计动作** `CONTENT_PLATFORM_AUTH_EXPIRED`（ADR-060 中系统把账户置为失效属于状态变更，由任务创建者身份记录）；12 项扩为 13 项，见 module_design IFC-188。
  4. **导出临时文件（F05）**：改用匿名临时文件（`tempfile.TemporaryFile`，在 POSIX 上创建即解除目录项，关闭或进程退出自动回收，进程被杀也不残留），`zipfile` 直接写文件对象，返回前 `seek(0)`，由 `FileResponse` 在响应结束时关闭；构建失败在 `finally` 中关闭。旧版本已在测试机 `/tmp` 留下的 `tmp*.zip` 属一次性清理，由运维只读核对后手工处理（E1）。
  5. **worker 单线程（F07）**：**移除 `--concurrency` 参数**，worker 固定单线程串行（取代 ADR-049 的"缺省 1、上限 2"）。理由：参数从未生效；管理员极少；串行使令牌单飞、任务领取、SQLite 测试都更简单；资源受限（画像 P7）。
  6. **心跳频率与租约（F07）**：`JobRun(job_name="content_worker")` 至多每 **60 秒**写一次（另在启动与停止时各写一次），不再每个轮询周期（2 秒）写；`JobContext.heartbeat()` 以**当前时间**（而非任务开始时间）延长租约，处理器在阶段边界调用（草稿推送每个平台前/每次上传前、视频每个片段下载前）。监控判定"心跳过期"阈值取 180 秒（3 个周期）。
  7. **渲染口径（F07）**：段落/标题的 `lineHeight` 渲染为块元素的 `line-height`（三种输出一致）；引用块与列表内的图片/视频与顶层一样解析 `src` 并渲染（任意深度，素材已删除时在原位置渲染"[素材已删除]"）；下划线与删除线同时存在时合并为一个 `text-decoration: underline line-through`。
  8. **视频分镜数据口径（F07）**：分镜按**文档段落**切分（`extract_paragraphs(doc)`），而不是对 `render_text` 的结果按 `\n\n` 切（`render_text` 以单个 `\n` 连接，导致恒为 1 个分镜，`backend/apps/content/richtext/render.py:242-273`）；`render_text` 输出保持不变（`text_confirmed_hash` 依赖其输出，改动会使已确认文案失效）。多片段下载**全有或全无**：任一片段下载/入库失败则删除本任务已入库的片段并 `Fail("DOWNLOAD_FAILED")`；各片段 URL 与 `task_id` 保留在 `ContentJob.state`，便于日后做"仅重新下载"（本批不做）。
  9. **默认标题（AC-105-03）**：发布校验把前端默认占位标题 `未命名内容` 视为标题缺失（`POST_INCOMPLETE`，`details.missing=["title"]`）；占位字符串为服务端常量，前端从同一常量值创建（口径点，不新增接口）。
- Consequences: 正向——审计 AC 全部有明确的落点与断言点；导出不再残留文件；worker 写库频率降低 30 倍（对 MySQL/SD 卡友好）；分镜数据口径可测。负向——删除 `--concurrency` 是行为变化（systemd 单元模板未使用该参数，无影响）；"全有或全无"会在最后一个片段失败时丢弃已付费生成的前几个片段（可靠性换取确定性，后续可做"仅重新下载"）；`未命名内容` 成为保留标题，真想用该标题的内容需改名。

## 开放问题 / ASSUMPTION

| 编号 | 类型 | 内容 | 影响 | 建议 |
|---|---|---|---|---|
| Q-A1 | **已关闭（1.1.0）** | 原问题"令牌如何获取与续期"：用户 2026-11-11 选 B，改为 AppID/AppSecret 自动换取，见 ADR-060 | — | — |
| Q-A2 | **并入 Q-B1（1.1.0）** | 公众号草稿图片/封面/视频嵌入 | — | 见 Q-B1 |
| Q-A3 | **已改写（1.1.0）** | "认证失效"口径已在 ADR-060 重新定义；错误码清单并入 Q-B1 第 4 项 | — | 见 Q-B1 |
| **Q-B1** | **`CLARIFICATION_NEEDED`（CRITICAL，阻塞 ADR-061 与 ADR-060 的错误码配置）** | 公众号 B 方案影响接口契约的事实**无出处**（协议 §N-2；不联网，§N-3）。需要的事实：(1) 封面素材：上传端点、请求/响应字段、格式与大小限制，以及草稿接口里封面字段的名称与是否必填；(2) 正文图片：是否必须先上传到微信侧、上传端点与响应里的图片地址字段、限制；(3) 草稿接口对视频的处理（A-5 假设"不随正文发送"）；(4) 错误码：取令牌时"AppSecret 错误/被重置/AppID 错误"的码（填 `auth_errcodes`）、草稿接口"令牌无效/过期"的码（填 `token_errcodes`）；(5) 是否有删除草稿接口（用于清理重复草稿，目前无）。已有出处、**无需**再问：取令牌端点与参数（[CODE: wechat.py:97-103]）、40164=IP 不在白名单（[CODE: wechat.py:13]）、`draft/add` 的 title/content/author 与 `media_id` 成功判定（[P11: publishers.py:76-87]） | ADR-061（封面/正文图片）、ADR-060 的 `auth_errcodes`/`token_errcodes` 真实取值、AC-127-03 的真实环境触发、AC-128-01 的真实效果 | 选项（推荐 A）：**A** 用户把微信官方文档相关页面（获取令牌及全局错误码、新增草稿、素材上传/正文图片上传）保存进仓库某路径，登记为 P11 资料；**B** 用户逐项确认上述 (1)~(5)；**C** 降级：封面由管理员在账户设置里手工填一个已有封面素材编号，正文图片本批不上传（仍须确认草稿接口里封面字段的名称）；**D** 分阶段：本批只交付令牌自动获取 + 现有已出处的草稿请求，封面/图片上传留为关闭的扩展点，待测试环境联调结果出来再补资料。**提示：P4=是 表明 GenPlatform 仅发 title/content/author 的调用线上成功过，PM 提示的"封面必填"尚未被证实** |
| Q-B2 | ASSUMPTION（1.1.0） | 现有 `content` 0001 尚未部署到任何环境（部署未授权），因此无含 `access_token` 的存量平台账户；0002 仍带一个只读 `secret_keys` 的数据步骤，把缺少 appid/appsecret 的公众号账户置 `UNSET`，以防万一 | ADR-060 | 用户或 PM 确认测试机未部署过内容中心 |
| Q-B3 | ASSUMPTION（1.1.0） | 公众号出口 IP 白名单由用户在微信侧配置；树莓派出口 IP 未知，且经家宽可能变化 | ADR-060；真实可用性 | 用户确认；E2 前验证 |
| Q-B4 | ASSUMPTION（1.1.0） | 外链图片粘贴一律"丢弃并提示"，不做转存（ADR-062） | AC-103 相关体验 | 用户确认；如需转存须另立需求 |
| Q-B5 | ASSUMPTION（1.1.0） | `warnings` 作为 POST/PATCH/preview 响应的附加字段（不改路径与契约测试，不影响既有前端） | IFC-191/193/198 | 无需确认 |
| Q-A4 | ASSUMPTION | 文生图服务的凭据配置（REQ-FUNC 无独立条目）：新增 `IMAGE_ARK` 配置项，与 LLM 的火山方舟密钥分开保存（两者是否可共用同一密钥 `[UNSOURCED]`） | REQ-FUNC-106、REQ-NFUNC-016；无对应用户故事 | 用户确认：另设配置 / 复用火山方舟 LLM 密钥 |
| A-1 | ASSUMPTION | 小红书、头条"认证信息"字段：本批它们不自动保存，仍允许保存一个可选的预留凭据字段 `credential`（加密存储，当前版本不被使用），以满足 REQ-FUNC-116 "每个平台账户预先保存认证信息"；具体认证形式待以后接入时按资料定义 | REQ-FUNC-116 | 用户确认是否需要保存 |
| A-2 | ASSUMPTION | 管理员修改"已发布"文章即时生效（审计动作"修改"），不设影子草稿；界面按钮称"保存并重新发布" | REQ-FUNC-099、US-106 | 用户确认 |
| A-3 | ASSUMPTION | 小程序内超链接"点击=复制链接并提示" | AC-108-01 | 用户确认；如需直接跳转，要先在微信侧配置业务域名 |
| A-4 | ASSUMPTION | 媒体访问用签名短时 URL（持链接者限时可读），而非每次校验登录 | REQ-FUNC-100 与 ADR-052 | 用户确认可接受 |
| A-5 | ASSUMPTION | 公众号草稿正文不嵌入视频；`pageBreak` 在草稿/导出中展平；这两项作为"不能保留的样式"逐平台提示 | REQ-FUNC-117、AC-128-03 | 用户确认；平台对视频的真实支持需资料 |
| A-6 | ASSUMPTION | AI 视频分镜策略：按段落切成至多 5 段、每段 5 秒、转场 `cut`（均可配置，`transition` 取值未出现在 P11 资料中） | REQ-FUNC-120 | 用户确认或补资料 |
| A-7 | ASSUMPTION（待确认缺省值） | 数值缺省：图片 10 MiB、视频上传 10 MiB（C-29/OQ-6）、AI 视频 50 MiB、素材总配额 1 GiB、磁盘剩余下限 512 MiB、文档上限 1 MiB、页长 1500 字、内置样式 3 套、LLM 生成参数（语气 3 档、篇幅 3 档、温度）、候选素材保留 24 小时、任务保留 30 天、AI 任务限流 30 次/小时/管理员（均 `[ESTIMATE]`，ADR-058） | OQ-2、OQ-6 | 用户逐项确认或授权按缺省 |
| A-8 | ASSUMPTION | "确认文案"的定义（REQ-FUNC-108、AC-124-05、AC-128-05 的"已确认"）：管理员在编辑器点"确认文案"，系统记录当时纯文本的摘要；之后文案被改动则需重新确认；已发布/已下线的内容视为已确认。视频生成要求文案已确认；一键保存要求内容已确认或已发布 | REQ-FUNC-108、117、120 | 用户确认该口径 |
| D-1 | **需用户决定** | ADR-049：是否同意新增常驻 systemd 单元 `ocap-content-worker`（+1 进程，约 60~100 MB `[ESTIMATE]`）；否决则退回方案 D（≤60 s 延迟）或 A（不可靠），需重做 ADR-049 | 异步任务 | 推荐 B |
| D-2 | **需用户决定** | ADR-050：新增依赖 `cryptography`；`.env` 须在部署前新增 `CONTENT_CRED_ENC_KEY` 并**自行备份**（丢失=凭据不可恢复） | 凭据加密 | 推荐同意 |
| E-1 | 运维核实（E1/E2 阶段） | 目标机 gunicorn `--timeout`、ocap 8090 站点 `client_max_body_size`、磁盘总量/剩余、快照是否含 `var/`（见 module_design"受影响的运行单元"） | 上传、导出、部署 | 子代理不 ssh（P9），由 PM 只读核实或 E2 预检 |

**1.1.0 结论（取代 1.0.0 此处"不触发 `CLARIFICATION_NEEDED`"的结论）**：公众号 B 方案**确有影响接口契约的事实无出处**（封面/正文图片上传的端点与字段、草稿接口的封面字段、相关错误码，见 Q-B1），依协议 §N-2 本次返回 `CLARIFICATION_NEEDED(CRITICAL)`。已有出处且已设计完的部分：取令牌（[CODE: wechat.py:97-103]）、令牌缓存与单飞、失败分类、IP 白名单类别（[CODE: wechat.py:13]）、`draft/add` 的 title/content/author（[P11: publishers.py:76-87]）。依赖未决事实的接口签名在 module_design 中均标 `[UNSOURCED]`，开发不得实现其 HTTP 细节。其余 GR-C-002 返工项（ADR-062、ADR-063）不依赖未决事实，可直接开发。即梦、方舟文生图、LLM 的出处沿用 1.0.0，核对未变。
