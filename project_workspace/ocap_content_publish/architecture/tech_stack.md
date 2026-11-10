<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-10T23:55:06+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md (0.1.0 DRAFT)</file>
    <file>architecture/module_design.md (0.1.0 DRAFT)</file>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型：信息公开发布与多平台内容中心（INCREMENTAL）

> 增量原则：沿用画像 P1 技术栈。**新增依赖共 1 个 Python 包、7 个 npm 包（含 1 个自动安装的对等依赖），0 个中间件，1 个 systemd 单元**。未安装任何依赖（本阶段只设计）。画像 P8 禁用项（Docker、pscp、makemigrations 产物、改 Freeark）均未出现在选中方案中；被排除的 Celery/Redis 不在 P8 禁用清单内，是因资源与必要性被排除（ADR-049）。
> 版本出处：`[REPO 文件:行]` 为仓库依赖清单；`[WEB: URL，2026-11-10]` 为 npm/PyPI 官方仓库 JSON；查不到写"未知"。本机（Claude 主会话云主机）没有 ocap 的 venv，已安装版本无法 `pip show` 取证，实际版本以目标机为准（未知）。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 / 后端框架 | Python + Django 5.2.x + DRF 3.x | `Django>=5.2,<6.0`（`backend/requirements.txt:1`）、`djangorestframework>=3.15,<4.0`（`:2`）；CI Python 3.13（`.github/workflows/ci.yml:31`）；测试机 Django 5.2.19（画像 P4） | 沿用 | 既有栈；迁移须在 5.2.x 下手写/校验，不得用 6.x（画像 P4、CR-023） | 全部 | 低 |
| 数据存储 | MySQL（测试环境库 `ocap`）/ SQLite 内存库（测试） | `mysqlclient>=2.2`（`requirements.txt:7`） | 沿用 | 9 张新表，`JSONField`/`BinaryField` 在两种后端均可用（`AuditLog.detail` 已用 JSONField，`core/models.py:18`） | REQ-FUNC-099~122 | 中：见 R6 |
| 凭据加密 | **`cryptography`（`AESGCM`，AES-256-GCM）** | 拟用 `cryptography>=42.0,<51.0`；PyPI 最新 50.0.2，发布 2026-09-30，要求 Python `!=3.9.0,!=3.9.1,>=3.9`，许可 `Apache-2.0 OR BSD-3-Clause`，含 `manylinux_2_17_aarch64`/`manylinux_2_28_aarch64`/`manylinux_2_34_aarch64` 轮子 [WEB: https://pypi.org/pypi/cryptography/json 与 …/50.0.2/json，2026-11-10]；`<51` 上界与下界 `>=42` 为本设计假设 `[ASSUMPTION]`（AESGCM 接口长期稳定），实现期以 CI 与目标机 `pip install --dry-run` 为准 | **新增**（Python） | ADR-050：需要 AEAD 且标准库没有；与参考实现一致（GenPlatform `core/encryption.py`）。CI（Python 3.13，x86_64）与树莓派 aarch64 均有预编译轮子 | REQ-NFUNC-016、REQ-FUNC-116/121 | 中：R1（原生依赖、密钥丢失不可恢复）。维护风险低（pyca 项目，活跃） |
| HTTP 客户端（外部服务） | `requests` | `requests>=2.31`（`requirements.txt:3`） | 沿用（已有，`wechat.py` 使用 urllib；本批用 requests 做流式 SSE 与带超时的下载） | 不引入 `httpx`/`tenacity`（参考实现使用它们，ocap 无）；LLM 流式用 `stream=True` 逐行读；文生图一次性重试用自写 2 次循环 | REQ-FUNC-105、106、117、120 | 低 |
| 请求签名（即梦） | 标准库 `hmac`/`hashlib`/`time` | Python 标准库 | 沿用 | 算法按 [P11: video_generator/jimeng_client.py:39-85] 在 `videogen.py` 内实现，无需火山 SDK | REQ-FUNC-120、121 | 中：R4（签名细节只能靠替身之外的真实联调验证，P4 禁止测试调用真实服务，只能靠对照参考实现代码 + 单元测试固定输入输出） |
| zip 导出 | 标准库 `zipfile`、`tempfile` | 标准库 | 沿用 | ADR-053；无需 JSZip | REQ-FUNC-122 | 低 |
| 任务队列 / 异步 | **数据库任务表 + 常驻 worker（systemd `ocap-content-worker`，`manage.py run_content_worker`）** | 无新增库；gunicorn `>=22.0`（`requirements.txt:8`）；部署实测 gunicorn 26.2.0（`project_workspace/ocap/deployment/deployment_report.md:80`） | **新增运行单元**，无新依赖 | ADR-049：无 Redis/Celery，状态在 MySQL，重启可恢复 | REQ-FUNC-117、118、120 | 高：R2（需用户批准，+1 常驻进程，内存待实测） |
| 缓存 / 消息 | 无 | — | — | 不引入 Redis；限流沿用 `RateLimiter`（`core/ratelimit.py`，数据库实现） | — | — |
| 富文本存储与渲染 | 自研 `richtext` 模块（白名单校验 + HTML/块渲染 + 分页） | 标准库 | 新增（自研代码，无第三方依赖） | ADR-047：不用 `nh3`/`bleach`；JSON 为事实源 | REQ-NFUNC-018、REQ-FUNC-100~104 | 中：R3（自研安全组件） |
| 媒体存储 | 本地盘 `MEDIA_ROOT/content/` + Django `signing` 签名 URL | Django 内置；`MEDIA_ROOT`=`backend/var/attachments`（`backend/config/settings.py:86`） | 沿用 | ADR-052；无对象存储 | REQ-FUNC-103、111~114 | 高：R5（磁盘、快照膨胀、nginx 体积限制） |
| Web 前端框架 | Vue 3 + Vite + Element Plus + axios + Pinia + vue-router | `vue ^3.5.13`、`element-plus ^2.8.7`、`axios ^1.7.9`、`pinia ^2.1.7`、`vue-router ^4.4.5`、`vite ^6.0.1`（`frontend/package.json:13-27`） | 沿用 | 工具栏用 Element Plus 自建 | 全部 | 低 |
| 富文本编辑器 | **Tiptap 3**（ProseMirror 无头编辑器） | 见下表，全部 3.33.1 | **新增**（npm） | ADR-046 | REQ-FUNC-101~104 | 中：R7 |
| 小程序 | uni-app (Vue 3) + Pinia | `@dcloudio/uni-app ^3.0.0-4060620250520001`、`vue ^3.5.13`（`miniprogram/package.json:13,17`） | 沿用，**无新增依赖** | ADR-048：自写 `RichBlocks.vue`，不装 parse 类插件 | REQ-FUNC-100、104 | 中：R8 |
| 测试 | 后端 Django test runner（SQLite）；前端/小程序 vitest | `vitest ^2.1.9`、`@vue/test-utils ^2.4.6`、`jsdom ^25.0.1`（`frontend/package.json:21-26`；`miniprogram/package.json:24-27`） | 沿用 | 外部服务只经 `fakes.py` 新增替身（画像 P4、P11-3） | 全部 | 低 |
| 进程管理 / 容器化 | systemd（`ocap-backend`、新增 `ocap-content-worker`）+ nginx；**不用容器** | 画像 P7/P8 | 沿用 + 新增 1 个单元 | 与 `ocap-run-due-jobs.service` 同风格（`deploy/systemd/`） | REQ-FUNC-120 | 见 ADR-049 |
| CI/CD | GitHub Actions `.github/workflows/ci.yml`（只测试与构建） | 画像 P7；前端 `npm ci`（`ci.yml:69`，要求 `frontend/package-lock.json` 同步更新）；小程序 `npm install --legacy-peer-deps`（`ci.yml:99`） | 沿用 | 新增 npm 依赖后必须提交更新后的 `frontend/package-lock.json`，否则 `npm ci` 失败；小程序无新增依赖 | — | 中：R9 |
| 部署方式 | 物理机：tar → scp → 迁移 → systemd 重启；不用容器 | 画像 P7；`.claude/skills/ocap-deploy/SKILL.md` | 沿用 | 增加：安装并启动 worker 单元、`.env` 加 4 键、核实 nginx/gunicorn/磁盘 | 全部 | 中：R5 |

### 新增依赖逐个说明

**Python（`backend/requirements.txt` 新增 1 行）**

| 包 | 版本 / 出处 | 许可证 | 理由 | 维护与安全风险 | 无该依赖的替代 |
|---|---|---|---|---|---|
| `cryptography` | `>=42.0,<51.0`；最新 50.0.2（2026-09-30）[WEB: https://pypi.org/pypi/cryptography/50.0.2/json，2026-11-10] | Apache-2.0 OR BSD-3-Clause（同上） | AES-256-GCM（ADR-050）。标准库无 AEAD；自行组合属于不应自研的安全组件 | 活跃项目，原生扩展（Rust/C）；aarch64 manylinux 轮子齐全（同上）；Debian 13 目标机 Python 版本未知，需 `pip install --dry-run` 预检；如需源码编译会拉取 Rust 工具链，**禁止**在树莓派上源码编译（出现时视为部署失败，改用轮子或固定版本） | 无（D 方案"只放 `.env`"违背用户确认的 P3=A） |

**npm（`frontend/package.json` `dependencies` 新增；全部版本 3.33.1，全部 MIT）**

| 包 | 版本 / 出处 | 用途 | 说明 |
|---|---|---|---|
| `@tiptap/vue-3` | 3.33.1；peer: `vue ^3.0.0`、`@tiptap/pm 3.33.1`、`@tiptap/core 3.33.1`、`@floating-ui/dom ^1.0.0`；optional: bubble-menu、floating-menu [WEB: https://registry.npmjs.org/@tiptap/vue-3/latest，2026-11-10] | Vue 3 绑定 | 版本与 `core`/`pm` **精确匹配** |
| `@tiptap/core` | 3.33.1，peer `@tiptap/pm 3.33.1` [WEB: https://registry.npmjs.org/@tiptap/core/latest，2026-11-10] | 编辑器内核 | 显式写入依赖，锁定同一版本 |
| `@tiptap/pm` | 3.33.1，依赖 prosemirror-* 13 个包 [WEB: https://registry.npmjs.org/@tiptap/pm/latest，2026-11-10] | ProseMirror 聚合 | 其中含 `prosemirror-tables`，但**不安装 table 扩展**，界面不出现表格（AC-110-04） |
| `@tiptap/starter-kit` | 3.33.1，依赖含 bold/italic/strike/underline/link/heading/lists/blockquote/horizontal-rule/hard-break 等 [WEB: https://registry.npmjs.org/@tiptap/starter-kit/latest，2026-11-10] | 基础格式 | 配置关闭 `code`、`codeBlock` |
| `@tiptap/extension-text-align` | 3.33.1，peer `@tiptap/core` [WEB: https://registry.npmjs.org/@tiptap/extension-text-align/latest，2026-11-10] | 对齐 | |
| `@tiptap/extension-text-style` | 3.33.1，导出子路径 `color`/`font-size`/`line-height`/`background-color` [WEB: https://registry.npmjs.org/@tiptap/extension-text-style/latest，2026-11-10] | 文字色、背景色、字号、行距 | |
| `@tiptap/extension-image` | 3.33.1，peer `@tiptap/core 3.33.1` [WEB: https://registry.npmjs.org/@tiptap/extension-image/latest，2026-11-10] | 图片节点（改造为只存 `mediaId`） | |
| `@floating-ui/dom`（对等依赖，npm 自动安装） | 1.8.0，MIT [WEB: https://registry.npmjs.org/@floating-ui/dom/latest，2026-11-10] | `@tiptap/vue-3` 的 peer | 不手动写入 |

> 撤销/重做、`Video`、`PageBreak`：撤销/重做由 StarterKit 依赖的 `@tiptap/extensions` 提供（实现期核对是否随 StarterKit 装入，不装则补装同版本）；`Video`、`PageBreak` 为仓库内自写扩展，不新增包。
> 许可证说明：Tiptap 核心与上列扩展均为 MIT；Tiptap 的"云/Pro 扩展"为商业许可，本批**不使用**任何 `@tiptap-pro` 包。
> 小程序（`miniprogram/package.json`）、后端其余依赖：**无新增**。

## 数值与精度

画像 P11-2（领域算法）为"无"，不适用算法精度预算。本批涉及的数值均为"容量/时限"类可配置参数，见 module_design IFC-168 缺省值表（每项标注"已确认 / 待确认 / 出处"）。核心约束：

- 文件大小以字节整数存储（`BigInteger`），配额用字节整数比较，不用浮点。
- 样式令牌：`line_height` 保存为 1~2 位小数的浮点，仅用于展示，不参与业务计算。
- 视频/图片时长、分辨率不做服务端解析（无 ffprobe/Pillow 依赖），只校验扩展名、魔数与字节数。

## 技术风险

### High

| 编号 | 风险 | 缓解 |
|---|---|---|
| R2 | **新增常驻进程**（ADR-049）：树莓派 4GB 与 Freeark 共享内存；内存估计 60~100 MB 为 `[ESTIMATE]`，尚无实测；worker 异常退出会让生成/保存任务停滞 | 需用户批准（D-1）；`MemoryMax=400M`、`Nice=10`、`Restart=on-failure`；E1 预检要求可用内存 ≥ 500 MB（SKILL §4 第 3 项）并在部署后实测 `ps -o rss`；`JobRun(content_worker)` 心跳可观测；租约过期自动回收；任务有最终态。若用户否决，退回方案 D（≤60 s 延迟）并重做 ADR-049 |
| R5 | **磁盘与体积限制未核实**：目标机磁盘总量/剩余、gunicorn `--timeout`、ocap 8090 站点 `client_max_body_size`/`proxy_read_timeout` 均不在仓库内；回滚快照 `tar` 含 `var/`（DEPLOY-001），素材增长后快照膨胀；总配额未经用户确认 | E1 在 deployment_plan 写只读核实清单（`df -h /home`、`ss`、nginx 配置读取、`ocap-backend.service` 的 `ExecStart`），子代理不 ssh（P9），由 PM 只读 ssh 或 E2 预检执行；快照改为排除 `backend/var`（或单独备份）；配额缺省 1 GiB 与磁盘剩余下限 512 MiB 双重守卫（均待确认）；nginx 仅改 ocap 8090 站点，改前备份，`nginx -t` 后 `reload`，不碰 Freeark |

### Medium

| 编号 | 风险 | 缓解 |
|---|---|---|
| R1 | `cryptography` 为原生依赖：目标机 Python 版本/pip 版本未知，无轮子时会触发源码编译；**密钥丢失=已保存凭据全部不可恢复** | 预检 `pip install --dry-run -r requirements.txt`（SKILL §4 第 8 项）；`CONTENT_CRED_ENC_KEY` 由用户保管并备份，E1 部署文档写明；密钥缺失时只让凭据保存接口返回 503，不影响业主端；支持 `CONTENT_CRED_ENC_KEY_PREV` 轮换 |
| R3 | 自研 `richtext` 校验器/渲染器是安全关键代码，绕过即 XSS | 单元测试专项：脚本标签/事件属性/`javascript:` 链接/`data:` 链接/超深嵌套/超大文档/未知节点/非法颜色与字号；渲染一律 `html.escape`；展示端不使用未校验 HTML（Web 只 `v-html` 服务端渲染结果）；GROUP_D 加入"含脚本片段正文"的端到端用例（AC-107-04/108-04） |
| R4 | 外部接口按参考实现编写但**测试只能用替身**（P4）：公众号草稿、即梦签名/状态映射、方舟文生图的真实行为无法在测试中验证；参考实现中部分细节 `[UNSOURCED]`（Q-A1~A3、A-5、A-6） | 客户端实现尽量薄；签名函数用固定输入输出做单元测试（用参考实现同样输入对比）；真实联调由用户在 E2 后手工验证并反馈；`content.wechat_mp.auth_errcodes` 等做成可配置，避免改代码 |
| R6 | 迁移风险：MySQL DDL 不可事务回滚；`BinaryField`/`JSONField` 的 MySQL 行为；唯一索引长度 | 手写迁移、仅新建表；`makemigrations --check` 无漂移；回滚前 `mysqldump` content_* 表并备份媒体目录（`[MANUAL_ROLLBACK_REQUIRED]`，见 module_design"数据迁移"） |
| R7 | Tiptap 3 的 `text-style` 子路径 API 与行距存储位置以实现期安装版本为准；9 个包版本须精确一致（`@tiptap/*` peer 为精确版本）；`npm ci` 要求锁文件同步 | 全部固定同一版本 3.33.1（`^` 不用于 `@tiptap/*`）；服务端校验器对 `lineHeight` 两处位置均接受（IFC-169）；提交更新后的 `frontend/package-lock.json`；CI 的 `npm ci` 与 `npm run build` 为门槛 |
| R8 | 小程序内超链接降级为"复制"（A-3）；`<video>` 对签名 URL 的 Range 行为在 iOS/安卓上差异；小程序媒体域名白名单（微信侧配置）可能影响 `<image>/<video>` 加载 | 视图实现单段 Range 并测试；用户确认 A-3；开发者在真机验证并反馈；域名配置属微信侧，本批不改 |
| R9 | CI 前端 `npm ci` 要求锁文件同步；小程序 `package-lock.json` 不提交（画像 P4） | 开发阶段更新并提交前端锁文件；小程序无新增依赖，无此问题 |
| R10 | 公众号 `access_token` 为手工录入且有时效（Q-A1）：真实使用中会频繁出现"认证已失效"；`requests` 异常消息含带 token 的 URL，若未脱敏会写入错误信息 | ADR-050 的 `SecretRedactor` 强制用于所有错误文本；单元测试用含 token 的 URL 构造异常断言输出不含 token；Q-A1 待用户说明线上做法 |

### Low

| 编号 | 风险 | 缓解 |
|---|---|---|
| R11 | 浏览器剪贴板 API 在 HTTP 内网地址（非安全上下文）不可用 | 复制失败回退 `execCommand('copy')`/手动选中；实现期在内网入口验证 |
| R12 | 管理端侧栏增至 12 项，拥挤 | 本批不处理；后续可分组折叠 |
| R13 | AI 生成素材 URL 有效期未知，下载失败 | 任务内立即下载；失败任务显示原因，管理员可重试 |
| R14 | 签名 URL 出现在 nginx 访问日志 | TTL 缺省 1 小时、仅限单个媒体；不含会话凭据；A-4 待用户确认 |
