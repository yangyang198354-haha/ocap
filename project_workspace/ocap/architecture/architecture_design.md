<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-07T20:58:50+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md (5.0.0 APPROVED)</file><file>requirements/user_stories.md (3.0.0 APPROVED)</file><file>architecture/architecture_design.md (0.1.0)</file><file>phase_status.md (clarifications，含 2026-11-07T20:42:22+08:00 架构开放问题答复；GR-B-001)</file></input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：业主委员会 Web 应用 + 微信小程序（ocap）

> 范围：仅架构与模块设计（PHASE_03/04）。不含产品代码，不建代码目录（用户原话："先开始进行架构设计，但是不要开发"）。
> 引用约定：`[CODE: /root/myproject/Freeark/…:行]` = Freeark 现有可工作代码；`[WEB: URL，2026-11-07]` = 联网查到的公开文档；`[ESTIMATE]` = 无依据的估计；`[ASSUMPTION]` = 需求未覆盖、由架构阶段暂定、待用户确认；`[UNSOURCED]` = 找不到出处。
> 微信官方文档页面（developers.weixin.qq.com）部分页面正文过长，WebFetch 只能取到摘要；凡标注"摘要"的事实在开发阶段需对照官方页面原文复核。

**0.2.0 修订说明（0.1.0 → 0.2.0）**
- 落实用户 2026-11-07 的答复（原文："全部按推荐，2. B， 4，我打算以其他组织（业委会）申请"）：OQ-01 = A；OQ-02 = B（阿里云短信）；OQ-03 = A（事务邮件服务，SMTP）；OQ-04：以"其他组织（业委会）"主体申请（备案域名/HTTPS 未答，保留为上线前置条件）；建议值表全部接受；OQ-05 ~ OQ-16 全部按推荐；OQ-15 代码布局接受，允许 `makemigrations --dry-run <app>` 辅助对照、不提交其产物（GR-B-001-F02 关闭）。
- "待用户确认的建议值"改为"已确认值"，与 requirements_spec 5.0.0 的 C-06 / C-07 / C-08 / C-12 / C-18 / C-19 及 REQ-NFUNC-001 一致。
- 与 requirements_spec 5.0.0 新增 REQ-FUNC-064 ~ 068、C-15 ~ C-19 对齐；覆盖范围由 REQ-FUNC-001 ~ 063 扩为 001 ~ 068。
- 新增 ADR-022（阿里云短信适配实现方式）；ADR-004 增加会话有效期语义；ADR-009 改由 C-15 / C-16 决定；ADR-017 的 Django 行为已查证官方文档，去掉 `[UNSOURCED]`。
- 新增开放问题 OQ-17 ~ OQ-26（见末节），均为本次设计中发现的需求缺口或接口层面的暂定处理。
- GR-B-001-F01：本次已完整读完 requirements_spec.md 5.0.0（至第 564 行）与 user_stories.md 3.0.0（至第 1028 行），批次 2 的 AC 与决策记录已逐条参照。

## 架构概览

**风格**：模块化单体（modular monolith）。一个 Django 项目、一个关系库、一个 REST/JSON API（`/api/v1/`），按业务能力拆成 Django app（有界上下文），三个客户端共用同一 API：Web 用户端 + 管理后台（同一个 Vue 3 SPA 的两棵路由树）、微信小程序（uni-app）。无消息队列、无缓存服务、无 WebSocket；定时事项由 systemd timer 驱动的管理命令完成。依据：单小区单业委会（C-11）、数据量小、物理机单机部署（P7）、禁止容器化（P8）、Freeark 同构栈便于复用（C-02）。

**在需求中的位置**（需求 → 架构关键点）：

| 关注点 | 需求 | 架构落点 |
|---|---|---|
| 登录/注册/账号合并/注销 | REQ-FUNC-001~008、017、021、023、024、026~031、064、065、067 | accounts + integrations + identity；ADR-004~011、022 |
| 清册、认证、户主、同住人 | REQ-FUNC-009~015、018~022、032~034 | registry + residency；ADR-006、017 |
| 业委会身份/业主代表/配置 | REQ-FUNC-035、036、052、053、056、057、061、063 | committee；ADR-006、012 |
| 决议/报销/备用金/收入/报表 | REQ-FUNC-037~042、048~051、054、055、058~060、062、066 | approval + resolutions + claims + income + ledger；ADR-012~014 |
| 投票与调查 | REQ-FUNC-043~047 | polls；ADR-015 |
| 管理员账号 | REQ-FUNC-025、068 | accounts（AdminAccount）；ADR-005 |
| 审计、脱敏、验证码限制、会话 | REQ-NFUNC-001~004、REQ-FUNC-064 | core（audit、masking、ratelimit）+ accounts（验证码、令牌）；ADR-004、008、019、020 |

**关键质量属性**（均来自 REQ-NFUNC 或约束）：
- 安全/防滥用：验证码位数/有效期/频率/错误次数限制与密码登录锁定（REQ-NFUNC-001，C-06）；手机号脱敏且仅授权角色可见（REQ-NFUNC-002）；密码规则（C-08）；会话有效期（REQ-FUNC-064）。
- 可审计：关键身份与批次 2 操作留痕（REQ-NFUNC-003/004，C-07），审计表只追加。
- 一致性：每专有部分有且只有一个户主、一人一个业委会/业主代表身份、一人一票、财务口径不重复计入——全部以**数据库唯一约束为最终保障**，应用层加锁只是减少冲突（ADR-017）。
- 可配置/可替换：人数与任期（C-13）、验证码与附件数值（C-06/C-12/C-18）、短信与邮件服务商（C-15/C-16）、开放项 Q30/Q96~Q99/Q110 全部做成配置或适配层。
- 可测试：测试库 SQLite、严禁连生产库（P8）；外部服务（微信、阿里云短信、邮件）只经适配接口，测试用替身。

**C-05 结论（REQ-FUNC-008 可实现性，已由用户确认 OQ-01 = A）**：见 ADR-011。**条件性可实现**——微信开放平台"网站应用微信登录"自带"快速登录"：Windows 微信 ≥ 3.9.11（Mac ≥ 4.0.0）已登录且未锁定时，发起登录会优先提示用当前客户端账号快速登录，无需扫码 [WEB: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html，2026-11-07，页面标注最后编辑 2026-06-25]。用户已确认两点：(1) 是否出现快速登录由微信组件决定，本站不探测本机微信、不自绘"授权"按钮；(2) Mac 同样支持。前提：必须有已审核通过的开放平台**网站应用**（授权回调域须与审核时一致）；该页面未写明对主体类型的要求 [WEB: 同上，2026-11-07]，用户主体为"其他组织（业委会）"（C-17），审核结果未知，REQ-FUNC-002/008 的落地以审核通过为前提。

## 部署视图

画像 P7 尚未确定环境与主机，本节**只列运行单元**，不引入任何环境名，也不指定主机。部署方式沿用 P7：物理机、`git pull` + systemd 重启；无 Docker。

| 运行单元 | 类型 | 说明 | 变更时动作 |
|---|---|---|---|
| RU-1 `ocap-backend.service` | systemd 常驻服务 | Gunicorn（WSGI）托管 Django；无 WebSocket，不需要 ASGI（偏离 Freeark 的 uvicorn，见 ADR-002） | 后端代码/迁移/依赖/环境变量变更后重启 |
| RU-2 `ocap-scheduler.timer` + `ocap-scheduler.service` | systemd timer + oneshot | 每分钟执行 `manage.py run_due_jobs`：截止判定、任期到期、报表自动生成、清理（见 ADR-013） | 任务代码变更后无需常驻重启（下次触发即生效）；unit 文件变更需 `daemon-reload` |
| RU-3 前端静态构建产物 `frontend/dist` | 静态文件 | Web 用户端 + 管理后台 | 前端变更后重新构建并替换 |
| RU-4 小程序包 | 微信平台发布 | uni-app 构建后经微信开发者工具上传、提审、发布 | 小程序变更后重新构建、提审、发布（不经 systemd） |
| RU-5 反向代理（沿用 Freeark 的 nginx 模式 [CODE: /root/myproject/Freeark/CLAUDE.md "systemd 服务清单" 含 nginx]；是否采用待 P7 补齐） | 外部/已有服务 | TLS 终止、静态文件、`/api/` 反代、请求体大小上限；向后端传递真实客户端 IP（见 ADR-008） | 配置变更后 reload |
| RU-6 MySQL（外部依赖，实例位置未知） | 数据库 | 生产 MySQL；测试 SQLite | 迁移由人工按 P6 手写 scoped 迁移后执行 |

外部服务（非本系统运行单元，经 `integrations` 适配）：微信（小程序 + 开放平台网站应用）、阿里云短信（C-15）、事务邮件服务 SMTP（C-16）。
不设：Redis、Celery、Channels、Docker 容器、独立的消息队列。

## 外部平台前置条件（影响可实现性与上线，非代码问题）

用户主体决定：小程序与开放平台以"其他组织（业委会）"申请（C-17，OQ-04）。备案域名与 HTTPS 用户未答，作为上线前置条件保留。

| 项 | 需要 | 状态 / 官方依据 |
|---|---|---|
| 域名、ICP 备案、HTTPS 证书 | 小程序 request 合法域名（须 HTTPS）、开放平台网站应用授权回调域、Web 站点 | 用户未答（保留）。小程序须备案后方可上架一事仅见于社区帖子，非官方原文 [WEB: https://developers.weixin.qq.com/community/develop/article/doc/0008403911c1107ec14043aef66813，2026-11-07，搜索摘要，未取得原文]，以官方备案指引为准。"合法域名须 HTTPS"的出处 [UNSOURCED]，开发时对照官方"服务器域名"配置页 |
| 小程序（主体：其他组织） | AppID/AppSecret；微信认证；服务器出口 IP 加入白名单；request 合法域名 | 官方：政府、媒体、其他组织类账号"需认证成功后方可提交发布审核"；其他组织免费认证范围列有城市居民委员会、农村村民委员会等，**未列业主委员会**，其余类型需付审核服务费（金额页面未写）；一般其他组织材料为《组织机构代码证》及相关登记/批准证明，页面自述各节清单不完全一致，须向审核方确认 [WEB: https://developers.weixin.qq.com/miniprogram/product/renzheng.html，2026-11-07]。IP 白名单见 stable_token 错误码 40164 [WEB: https://developers.weixin.qq.com/miniprogram/dev/server/API/mp-access-token/api_getstableaccesstoken.md，2026-11-07，摘要] |
| 开放平台开发者账号 + 已审核网站应用 + 授权回调域 | REQ-FUNC-002/008 | 官方登录文档只写"注册开发者账号并拥有已审核通过的网站应用"，**未写主体类型要求与开发者资质认证细节** [WEB: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html，2026-11-07]；"其他组织"可否通过审核：未知 |
| 小程序与网站应用绑定同一开放平台账号 | 才能用 unionid 打通同一微信用户 | 增强项，非必须；状态未知 |
| "手机号快速验证组件" | **可选开关，默认关闭**（`wechat.phone_quick_verify_enabled=false`） | 官方 API 页"适用范围"仅列小程序、小游戏，"其他未明确声明的账号类型，如无特殊说明，均不可调用此接口" [WEB: https://developers.weixin.qq.com/miniprogram/dev/server/API/user-info/phone-number/api_getphonenumber.md，2026-11-07]；"仅非个人且已认证主体可用、按次收费"出自搜索摘要，未取得官方原文，开启前由用户复核。**小程序完成组织认证后可开启**；基线用短信验证码验证手机号（ADR-010） |
| 阿里云短信（C-15） | RAM 子账号 AccessKey（最小权限）；已审核的短信签名与验证码模板 | 官方"资质材料说明"列出企业、事业单位、个人，证件示例为社会信用代码证书/企业营业执照/事业单位法人证书；**未提及"其他组织"与业主委员会** [WEB: https://help.aliyun.com/zh/sms/user-guide/qualification-application-description，2026-11-07]。业委会是否具备可用证件（如统一社会信用代码证书）由用户确认，见 OQ-20。模板规范：必须含"验证码/校验码…"字样且写明平台/用途/有效期之一；仅支持单变量（4~6 位字母/数字）与不可自定义的双变量；不得含链接、联系方式 [WEB: https://help.aliyun.com/zh/sms/user-guide/verification-code-template-specifications，2026-11-07]。因不能自定义第二个变量，**有效期写死在模板正文**，须与 `code.sms.ttl_seconds` 一致（ADR-022） |
| 阿里云平台默认流控 | 无需配置，但需知晓 | 验证码短信同一签名下同一号码默认 1 条/分钟、5 条/小时、10 条/天（中国内地），分钟与小时按自然时间窗口，天按滚动 24 小时；另有同一号码跨发送方 40 条/天；请求提交成功即计数，与回执无关 [WEB: https://help.aliyun.com/zh/sms/user-guide/message-rules，2026-11-07]。与 C-06 数值相同，但窗口算法不同，平台可能先于本系统拒绝，适配器须映射为限流错误（IFC-011） |
| 事务邮件服务（C-16，SMTP） | 发信域名/发信地址验证、SMTP 凭据 | 具体厂商未选（OQ-03 只定了类别）；接口为 Django 标准 SMTP 后端，厂商差异只体现在环境变量。域名验证等要求因厂商而异，**未核实** |
| 反向代理请求体上限 | ≥ 附件单文件上限 10 MB + 表单开销 | 附件逐个上传（IFC-004），不做多文件同请求，因此上限按 12 MB 配置即可 `[ESTIMATE]` |

## 已确认值（C-06 / C-07 / C-08 / C-12 / C-18 / C-19 / REQ-FUNC-064）

以下数值已由用户确认（"建议值表全部接受"，requirements_spec 5.0.0 已写入对应 C-xx）。全部做成配置项（环境变量或 `SystemConfig` 表，见 module_design"配置项清单"），改值不需发版；其中审计保留期限提供管理端修改入口（IFC-009）。

| 编号 | 项 | 已确认值 | 依据（保留） |
|---|---|---|---|
| C-06 | 短信验证码位数 | 6 位纯数字 | NIST SP 800-63B §5.1.3.2：带外密钥至少 20 bit 熵，6 位数字约 19.9 bit，需配合限次 [WEB: https://pages.nist.gov/800-63-3/sp800-63b.html，2026-11-07，该页标明已被 SP 800-63-4 取代]；与阿里云验证码模板变量 4~6 位限制相容 |
| C-06 | 有效期 | 短信 5 分钟；邮件 10 分钟 | NIST：带外验证 10 分钟内完成方有效（同上）；短信取更严的 5 分钟 `[ESTIMATE]` |
| C-06 | 发送频率 | 同一目标（手机号/邮箱）两次发送间隔 ≥ 60 秒；≤ 5 条/小时、≤ 10 条/天；同一来源 IP ≤ 30 条/小时 | `[ESTIMATE]`，行业惯例；同时控短信成本 |
| C-06 | 错误次数上限 | 单个验证码错误 5 次作废；同一目标 30 分钟内累计错误 10 次，锁定该目标 30 分钟 | `[ESTIMATE]`；NIST §5.2.2 连续失败 ≤ 100 为上限，取值更严（同上） |
| C-06（延伸） | 密码登录连续失败 | 同一账号/手机号连续 5 次错误锁定 15 分钟 | 已并入 REQ-NFUNC-001 |
| C-07 | 审计日志保留期限 | 默认 24 个月，可调整，**不得低于 6 个月**（低于 6 个月的设置被拒绝，AC-034-04） | 《网络安全法》要求网络日志留存不少于六个月 [WEB: https://www.cac.gov.cn/2016-11/07/c_1119867116_2.htm 与搜索摘要，2026-11-07]；24 个月 `[ESTIMATE]` |
| C-08 | 密码规则 | 长度 8~64；至少含字母和数字；不得全为数字；不得是常见弱口令；不得与手机号、账号相同；设置需二次输入确认；哈希用 Django 默认 PBKDF2-SHA256 | NIST §5.1.1.1~5.1.1.2（同上）；"字母+数字"是对 NIST 的有意偏离，用户已接受；弱口令表使用 Django 内置 `CommonPasswordValidator`（无新依赖） |
| C-12 | 决议附件 | 每份 ≤ 10 个；单个 ≤ 10 MB；合计 ≤ 50 MB；格式 pdf、jpg/jpeg、png、docx、xlsx；类型以文件实际内容为准，拒收 svg/html/可执行文件 | 上限同时是 DoS 防线 |
| C-18 | 其他附件与头像 | 申诉产权证明 ≤ 5 个；报销发票 ≤ 10 个；收入凭证 ≤ 10 个；单个 ≤ 10 MB；格式为"图片或 pdf"；头像 ≤ 2 MB，jpg/png | "图片"的具体格式需求未列，暂按 jpg/jpeg/png 实现 `[ASSUMPTION]`，见 OQ-18 |
| C-19 | 手机号范围 | 仅中国大陆 11 位手机号，格式 `^1[3-9]\d{9}$` | 用户"全部按推荐"确认；账号标识 `account_no`（10 位非连续随机数字）属技术实现，不写入需求 |
| REQ-FUNC-064 | 会话有效期 | Web 用户端闲置 30 分钟退出，"记住我"保持 7 天；小程序默认 7 天；管理员闲置 30 分钟、无"记住我"；注销后既有会话立即失效 | Web 用户端取值沿用 Freeark 的 1800 s / 604800 s [CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/freearkweb/settings.py:320,326]，但 Freeark 的 7 天是"闲置 7 天"，ocap 的 AC-069-03 写"登录已满 7 天要求重新登录"，故本设计采用**绝对 7 天**（ADR-004，OQ-17） |

## ADR

### ADR-001: 总体架构风格：模块化单体
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-001~068 覆盖账号、清册、业委会、审批、财务、投票六块；C-11 单小区；P7 物理机单机、systemd；P8 禁止容器化。团队规模与运维能力有限，需求仍在分批追加。
- Options:
  - A 模块化单体（单 Django 项目，按业务拆 app，单库）。优：事务一致性（账号合并、户主接任、财务口径都需要跨模块事务）；运维一个服务；与 Freeark 同构可复用。缺：模块边界靠约定维持，需用依赖规则（module_design 的依赖图）+ 代码评审守住。
  - B 微服务（账号服务、审批服务、财务服务…）。优：独立伸缩。缺：账号合并/注销要跨服务分布式事务；单机物理部署下收益为零；运维成本高 `[ESTIMATE]`。
- Decision: 选 A。理由：账号合并（REQ-FUNC-026~030、061、067）、户主接任（REQ-FUNC-020）、身份失效级联（REQ-FUNC-053、063）都是跨上下文强事务操作；C-11 单小区无伸缩诉求；P7/P8 偏好最简部署。
- Consequences: 正向：事务简单、单进程部署、联调简单。负向：模块间耦合需要靠"依赖方向只能向下"的规则守住（见 module_design 依赖图）；单体意味着任何后端变更都重启整个服务。

### ADR-002: 技术栈基线沿用 Freeark（偏离项单列）
- Status: Proposed
- Type: constraint-driven
- Context: C-02、P1。约束来源：C-02（"整体技术选型……参考 Freeark"）、P1（Django 5.2 + DRF / Vue 3 + Vite + Element Plus / uni-app + Pinia + vitest / MySQL 生产、SQLite 测试）、P8（禁 Docker）。
- 被排除方案：Java/Spring、Node(NestJS)、React/Taro、PostgreSQL 作为生产库——均违反 C-02 的"参考 Freeark"且无需求依据；容器化部署——P8 禁止。
- Decision: 沿用 Freeark 栈。**偏离项**（均有理由）：(1) Web 服务器用 Gunicorn（WSGI）而非 Freeark 的 uvicorn(ASGI)——ocap 无 WebSocket 需求，Freeark 选 ASGI 是因 Channels [CODE: /root/myproject/Freeark/FreeArkWeb/backend/requirements.txt 中 "uvicorn[standard]" 与 "channels" 注释]；(2) 不引入 Redis/Channels/MQTT/LangGraph/RAG 等 Freeark 的业务特有依赖；(3) 不设 `django-cors-headers`：Web 经同域反代，小程序不受浏览器 CORS 约束，开发期用 Vite 代理；(4) 新增 `openpyxl`（清册/收入表 xlsx 导入）和 `requests`（Freeark 代码已用但其 requirements.txt 未显式列出，见 tech_stack）；(5) 新增阿里云短信官方 SDK `alibabacloud_dysmsapi20170525`（ADR-022）。
- Consequences: 正向：可复制改造 Freeark 的认证、微信登录、小程序 http/auth store、测试脚手架（清单见 module_design"代码复用"）。负向：继承 Freeark 的前端大版本约束（见 tech_stack 风险）；Freeark 的赛博朋克 UI 与业委会场景不匹配，**界面层基本不复用**。

### ADR-003: 独立仓库与代码复用方式
- Status: Proposed
- Type: decision
- Context: C-02 要求"代码复用"；用户明确 ocap 是独立仓库（invocation 指示）；P3 greenfield。
- Options:
  - A 复制改造：从 Freeark 拷贝所需文件到 ocap，文件头注明来源与 commit，之后独立演化。优：无运行期耦合、可按业委会场景大改。缺：Freeark 上的后续修复不会自动同步。
  - B 抽公共包/子模块（git submodule 或私有 pip/npm 包）。优：修复可同步。缺：Freeark 代码与其业务（设备、能耗）深度耦合，抽取成本高；两仓库发布节奏绑定。
  - C 完全重写，仅参考设计。优：干净。缺：重复造轮子，丢失 Freeark 已在生产验证的微信登录与滑动会话实现。
- Decision: 选 A，只复制"认证与微信接入、小程序基础设施、测试脚手架"三类（清单见 module_design"代码复用"），其余参考不复制。
- Consequences: 正向：ocap 完全独立可演进。负向：复制进来的代码要自带测试；Freeark 以后修同类缺陷需人工评估是否回灌。

### ADR-004: 登录凭据机制：服务端不透明令牌 + 两种会话期限
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-001~008、017（注销后立即生效）、REQ-FUNC-053/063（身份失效后不得再执行相关操作）、REQ-FUNC-064（会话有效期，US-069）、REQ-NFUNC-001。
- Options:
  - A 服务端令牌（数据库存哈希，可单点撤销）——即 Freeark 的 `SlidingWindowTokenAuthentication` 思路 [CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/api/authentication.py:40]。优：账号注销、合并、管理员禁用时可立即吊销；Web 与小程序一致；已有可复用实现。缺：每请求一次库查询（写 `last_active_at` 可节流）。
  - B JWT（无状态）。优：无库查询。缺：注销/合并/身份失效后令牌仍有效至过期，需另建黑名单，等于有状态；与 REQ-FUNC-017"确认后立即生效"、AC-069-06 冲突。
  - C Django Session Cookie。优：框架自带。缺：小程序不适合 Cookie；CSRF 处理在 SPA+小程序混合场景增加复杂度（Freeark 曾因此移除 SessionAuthentication，见 settings.py:303-312 注释）。
- Decision: 选 A，与 Freeark 的不同点：(1) 令牌库中只存 SHA-256 哈希，不存明文；(2) 允许同一用户多令牌（多端同时登录），不像 Freeark 的 `Token.get_or_create` 每用户一个令牌；(3) **两种会话期限**（REQ-FUNC-064）：
  - `IDLE`（`extended=false`）：闲置超过 `session.idle_seconds`（1800）即失效，每次有效请求后重新计时（AC-069-01/02）；适用 Web 用户端未勾选"记住我"与管理员（管理员无"记住我"，AC-069-05）。
  - `EXTENDED`（`extended=true`）：自签发起满 `session.extended_seconds`（604800，即 7 天）绝对失效，期间不因闲置失效（AC-069-03/04）；适用 Web 勾选"记住我"与小程序（`session.miniapp_extended=true`，小程序登录一律签发 EXTENDED）。这与 Freeark 的"7 天闲置"不同（Freeark 在 authentication.py 与 settings.py:320-326 中把延长会话也按闲置计），原因见"已确认值"表最后一行，OQ-17 请用户确认。
  令牌只走 `Authorization: Token <key>` 头，**任何端点禁止 `?token=` 传凭据**（通用经验）。
- Consequences: 正向：注销/合并时 `DELETE FROM accounts_auth_token WHERE user_id=…` 即全端下线；可审计。负向：需自实现令牌模型（不能直接用 `rest_framework.authtoken`，其为每用户一令牌且明文存储）；`IDLE` 的 `last_active_at` 写库要节流（沿用 Freeark 的 300 s 节流思路，settings.py:332），因此闲置判断存在最多 300 s 的误差窗口（偏向放行），验收时 AC-069-01 的"第 31 分钟被拒"需以节流阈值内可接受的容差测试 `[ESTIMATE]`；`EXTENDED` 无此问题。

### ADR-005: 管理员与普通用户分离为两种主体
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-025：管理员"不是注册用户"，独立账号+密码，管理后台不提供注册入口；REQ-FUNC-068：已有管理员可重置其他管理员密码（US-073）；US-011 AC-011-02：普通用户（含产权业主）登录管理后台须被拒。Freeark 用同一用户表加 `role` 字段 [CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/api/models.py:7-17]。
- Options:
  - A 独立表 `AdminAccount`（账号+密码，不含手机号/微信/身份），独立登录端点，令牌带 `principal_type=ADMIN`。优：从结构上杜绝"普通用户提权为管理员"和"管理员出现在业主身份链里"；账号合并/注销流程无需处理管理员。缺：多一张表、一套登录。
  - B 同一用户表加 `is_admin`/`role`（Freeark 做法）。优：少一张表。缺：管理员可能同时带手机号、微信、产权身份，合并/注销规则要特判；一个字段错误即越权。
  - C 使用 Django 自带 admin 站点作管理后台。优：零开发。缺：业务后台（审批流程配置、赋予身份、清册导入、审计）需要定制界面，且与 SPA 登录体系割裂。
- Decision: 选 A。管理员密码重置范围限于"已有管理员重置他人密码"，首个管理员由命令行初始化（REQ-FUNC-068，OQ-09 已决）；管理员自助找回密码、禁用管理员账号不在范围内。重置时同步吊销目标管理员的全部令牌，并写审计 `ADMIN_PASSWORD_RESET`（需求未规定重置是否审计，属架构暂定 `[ASSUMPTION]`，OQ-23）。
- Consequences: 正向：权限判定一眼可读；REQ-NFUNC-003 管理员登录审计单独成线。负向：需要管理员自身的账号管理 UI 与 `create_admin` 初始化命令；所有管理员密码丢失且无其他管理员时只能走命令行 `create_admin` 重建。

### ADR-006: 权限模型：基于"关系"的派生角色，而非用户表上的角色字段
- Status: Proposed
- Type: decision
- Context: 同一用户在不同专有部分身份不同（Q2=B）；游客/同住人/产权业主/户主按专有部分计；业委会委员/主任/副主任、业主代表为全局唯一身份且互斥（REQ-FUNC-053）；权限需随身份失效即时变化（REQ-FUNC-063）。
- Options:
  - A 关系表 + 派生角色：`UnitMembership(user, unit, role)` 与 `CommitteeSeat(user, position, term)`；权限类每次请求现查（带请求级缓存）。优：与需求语义一一对应；身份失效立即生效；无同步问题。缺：每请求 1~2 次小查询。
  - B 用户表上存 `role` 字段（Freeark 三角色 RBAC [CODE: /root/myproject/Freeark/CLAUDE.md "三角色 RBAC"]）。优：简单。缺：表达不了"每专有部分一个身份""任期到期"，需大量派生字段并保持同步，极易与事实不一致。
  - C Django Group/Permission 表。优：框架自带。缺：权限是全局的，无法表达"某专有部分的产权业主才能审批该部分同住人申请"这类对象级规则。
- Decision: 选 A。权限判定集中在 `committee`/`residency` 两个模块的"查询服务"，DRF 权限类只调用它们。游客 = 无任何有效 `UnitMembership` 的已登录用户（派生，不入库）。
- Consequences: 正向：身份即事实，不会漂移；REQ-FUNC-036 的"个人信息显示身份"直接从关系表聚合。负向：列表类接口需注意 N+1，需 `select_related`/批量预取；权限规则分散在两个服务里，需统一的权限矩阵测试（module_design 的"权限矩阵"）。

### ADR-007: 账号合并与注销的数据策略
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-017/027（注销：删除个人资料与凭据、解除身份、历史业务记录匿名保留、同号可作为全新账号再注册）；REQ-FUNC-026/028~030、061、067（合并：以手机号账号为准、空项补充、身份取高、业委会/业主代表身份取高、同一投票/调查两账号均作答时保留主账号答卷并审计、其余待办归合并后账号）。
- Options（注销）:
  - A 墓碑化：保留用户行，清空手机号/邮箱/昵称/头像/密码/微信标识，置 `status=CANCELLED`；业务表外键仍指向它，展示时显示"已注销用户"。优：外键完整、历史记录自然匿名、手机号唯一约束自动释放。缺：用户表含墓碑行。
  - B 物理删除用户行，业务表外键置空。优：表干净。缺：外键需可空、需遍历所有引用表、遗漏即报错或丢记录。
- Options（合并）:
  - C 通过"用户引用注册表"把次要账号的所有外键改指向主账号（遇唯一冲突按各表登记的策略处理），再删除次要账号行。优：各模块自行登记引用，合并模块不必硬编码所有表。缺：新表忘登记会漏迁——用启动期一致性检查（遍历所有指向 User 的外键，未登记即报错）兜底。
  - D 次要账号保留为墓碑并记 `merged_into`。优：可回溯。缺：需求 AC-015-03 说"W 作为独立账号不再存在"。
- Decision: 注销选 A；合并选 C。审计日志对操作者/对象存**快照字符串与整数 id，不设外键**，因此不受行删除影响。REQ-FUNC-067 已确认（OQ-07 已决）：同一投票/调查两账号均作答时 `keep_primary` 并写审计 `MERGE_ANSWER_DISCARDED`；其余待办 `move_all`。各引用表的冲突策略在 module_design"合并引用登记表"中逐表列出，其中**审批快照中的审批人 id 列表**（`approval_instance.flow_snapshot`）不是外键，必须有自定义处理器（否则合并后次要账号的待办审批任务丢失，违反 AC-072-04）。
- Consequences: 正向：REQ-FUNC-027 的"新账号与已注销账号无任何关联"成立（新建全新用户行）。负向：合并是整个系统中最复杂的事务，必须在单个数据库事务内按固定顺序加锁（按用户 id 升序锁两个用户行）并有专项测试；需求只写了投票/调查，合并时决议表决（`resolutions_vote`）等同类冲突按同一策略处理属架构暂定 `[ASSUMPTION]`（OQ-21）。

### ADR-008: 验证码存储与限流：数据库实现，不引入 Redis
- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-001、C-06；多 Gunicorn worker 下进程内计数不可靠；Freeark 的进程内节流字典依赖 `--workers 1` [CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/api/authentication.py:7-8 模块注释与 :19-23 缓存注释]。
- Options:
  - A 数据库表 `VerificationCode` + `RateLimitCounter` + `Lockout`。优：多 worker 安全；无新运行单元；可审计；测试用 SQLite 即可。缺：写库频繁（量级小，可忽略）。
  - B Redis。优：天然 TTL 与原子计数。缺：新增运行单元（P7 无 Redis 约定）；测试需替身。
  - C 进程内字典。优：最简。缺：多 worker 与重启后失效，违背 REQ-NFUNC-001 的防暴力破解目的。
- Decision: 选 A。验证码以 `HMAC-SHA256(server_secret, target|purpose|code)` 存储，不存明文；比较用常量时间；验证成功立即标记 consumed；错误计数与过期判断在同一事务内。发送频率（间隔、小时、日、IP）用 `RateLimiter.hit`；"同一目标 30 分钟累计错 10 次锁 30 分钟"与"密码连续错 5 次锁 15 分钟"用 `RateLimiter.register_failure` + `core_lockout`（"连续"指成功登录后清零）。**同一来源 IP** 取反向代理传递的真实客户端地址：仅当直连地址属于受信代理（配置 `TRUSTED_PROXY_ADDRS`）时才采信 `X-Forwarded-For` 的最右一跳，否则用直连地址，防止伪造请求头绕过 IP 限流。
- Consequences: 正向：行为可测、可审计、可调参。负向：需要定期清理过期行（RU-2 的清理任务）；在 MySQL 默认隔离级别下"错误计数+1"需用 `UPDATE … SET attempts=attempts+1` 原子更新避免并发漏计；阿里云建议在发送验证码前加图形验证（见 OQ-19），本设计的 IP/号码限流不能替代，存在短信盗刷残余风险。

### ADR-009: 短信与邮件经适配层接入，服务商已定
- Status: Proposed
- Type: constraint-driven
- Context: C-15（短信验证码使用阿里云短信）、C-16（邮件验证码使用事务邮件服务）；用户确认 OQ-02 = B、OQ-03 = A。画像 P11-3 中短信/邮件两行仍写"服务商未定/未知"，需 PM 同步更新（见 `<notes>`）。约束来源：用户已选定服务商；但接口仍须稳定于服务商之上，以便测试替身与日后换商。
- 被排除方案：OQ-02 = A 腾讯云短信（原推荐项，用户改选 B）、C 聚合/代理通道、D 仅控制台替身（仅用于开发/测试）；直接把服务商 SDK 调用写进业务代码——换商与测试成本高；引入多服务商聚合 SDK——无依据且增加依赖。
- Decision: 保持 `SmsGateway` 与 `EmailGateway` 两个**本系统自定义的窄接口**（IFC-011/IFC-012），业务只依赖接口；配置项 `SMS_GATEWAY=console|aliyun`、`EMAIL_BACKEND` 选实现；开发/测试默认 `console`/`locmem` 替身（不外发）。短信实现 `AliyunSmsGateway`（ADR-022）；邮件直接使用 Django 的 SMTP 邮件后端（零新依赖），具体厂商未选，不影响契约。
- Consequences: 正向：测试不触发真实收费；日后换商只新增适配器类。负向：阿里云短信的签名/模板需先通过审核（周期未知）；各家错误码不同，统一映射到 `SmsSendError(kind, retryable)`；短信模板有效期写死，与 `code.sms.ttl_seconds` 必须一致（启动检查）。

### ADR-010: 微信接入：自写薄适配器直连官方 HTTP 接口，不用第三方 SDK
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-002/004（扫码与小程序一键登录）、REQ-FUNC-008、REQ-FUNC-065（小程序首次登录后头像昵称设置）、REQ-FUNC-011/026（微信用户需验证手机号）。C-17：主体为其他组织（业委会）。P11-3：微信文档在需求阶段未提供，架构阶段联网补出处。
- Options:
  - A 自写适配器 `WeChatClient`，用 `requests` 调官方接口（Freeark 已有同类实现 [CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/api/views_miniapp.py:137-174]）。优：依赖最少；接口稳定且只用 5 个端点；可精确控制超时（5 s）与错误映射。缺：官方接口变更需自己跟进。
  - B 第三方 SDK（wechatpy、weixin-python 等）。优：封装更全。缺：维护活跃度需逐个核实 `[ESTIMATE]`；多一层抽象；我们只用到很小子集。
- Decision: 选 A。用到的官方接口及出处见 module_design"领域与外部依赖出处"：`jscode2session`、`cgi-bin/stable_token`、`wxa/business/getuserphonenumber`、`sns/oauth2/access_token`、`sns/userinfo`、Web `qrconnect` + `WxLogin.js`。**手机号快速验证为可选**（`wechat.phone_quick_verify_enabled`，默认关；小程序完成组织认证后可开启），基线用短信验证码验证手机号。`access_token` 用 `stable_token`（多 worker 无需共享缓存：未强制刷新时重复调用返回同一令牌）。**小程序与 Web 的 openid 不同**，只有两个应用绑定在同一开放平台账号下才有 `unionid`；有 `unionid` 时用它把同一微信用户的两个入口归并到同一账号（`[ASSUMPTION]`，增强项）；没有时二者先是两个游客账号，在验证同一手机号时由 REQ-FUNC-026 的合并规则归并。**REQ-FUNC-065（OQ-05 = A 已决）**：小程序首次微信登录（响应 `is_new=true`）后，客户端进入头像昵称设置页，用微信 `chooseAvatar` 与昵称输入组件让用户确认，再经 IFC-033（头像转存）与 IFC-032（保存昵称）保存；再次登录（`is_new=false`）不进入，也不会覆盖用户已改的头像昵称。
- Consequences: 正向：依赖小、可测（`WeChatClient` 可整体替身）。负向：未取得凭据前无法联调；`sns/userinfo` 与小程序昵称头像的现行返回内容（官方 2021-10 起不再返回性别地区 [WEB: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Authorized_Interface_Calling_UnionID.html，2026-11-07]；小程序昵称需通过"头像昵称填写"组件取得，`getUserProfile` 已不可用，社区帖说明，开发时对照官方页复核）使 REQ-FUNC-016"取用微信昵称"在小程序侧变为"引导用户确认"（已由 REQ-FUNC-065 写入需求）；用户跳过设置页时的处理需求未规定，暂按"不再提示、昵称为空时显示系统生成的占位名"实现 `[ASSUMPTION]`（OQ-24）。

### ADR-011: REQ-FUNC-008"微信桌面版快速登录"的实现方式（C-05 结论）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-008（4.1.0 已按 OQ-01 = A 改写）、C-05、AC-008-01~03。
- Options:
  - A 使用开放平台网站应用的内嵌登录组件 `WxLogin`（默认开启 `fast_login`）：由微信客户端在满足条件时提示快速登录，否则展示二维码。优：官方能力 [WEB: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html，2026-11-07]；与扫码登录同一回调、同一账号规则（AC-008-01 末句）。缺：无法探测本机是否开启桌面版；无法自绘"授权"按钮；依赖网站应用审核（主体"其他组织"能否通过未知）。
  - B 自行探测本机微信（URL Scheme、本地代理/插件）。优：理论上可自绘入口。缺：无任何官方出处 `[UNSOURCED]`，且浏览器无法安全探测本机应用；会触发安全与合规风险。
  - C 放弃 REQ-FUNC-008。优：零风险。缺：不满足已批准需求。
- Decision: 选 A（用户确认 OQ-01 = A）。快速登录出现与否完全由微信组件决定；AC-008-02 的"微信未提示时页面正常展示二维码、不出现自绘授权按钮"天然成立；Mac ≥ 4.0.0 同样支持。本站不实现 B。
- Consequences: 正向：不引入任何非官方机制；需求措辞已与实现一致。负向：快速登录出现与否取决于用户本机微信版本与状态，测试只能人工验证（E2E 标 NOT_TESTABLE + 人工清单，US-008 备注已写明）；网站应用审核未通过则 REQ-FUNC-002/008 无法上线（风险见 tech_stack）。

### ADR-012: 审批做成通用引擎，主体模块只持有业务数据
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-038/042/049/054/055/058/060/062/066 都要求"配置的审批流程、发起时选用、审批人只能来自业委会成员、撤回/拒绝后重提、审批人身份失效后事项悬挂由发起人撤回、多审批人任一通过、财务类不得自审"。
- Options:
  - A 通用审批引擎 `approval`：`ApprovalFlow`（管理员配置）、`ApprovalInstance`（提交时把流程**快照**成实例）、`ApprovalAction`；决议/报销/备用金/核销/收入表各自持有业务数据，通过 `(subject_type, subject_id)` 关联实例。优：规则（不得自审、审批人资格、撤回、快照）只写一次；配置变更不影响在途事项。缺：多一层间接。
  - B 每个业务模块各写一套审批状态机。优：模块自包含。缺：规则重复 3 份，Q105（财务不得自审而决议不回避）这类差异易写乱。
- Decision: 选 A。引擎只管"谁、何时、同意/拒绝"，**不**管业务后果；业务后果由主体模块在引擎回调（`on_approved/on_rejected/on_withdrawn`）里完成，且回调与引擎状态变更在同一事务内。"半数同意"表决不走引擎的"单人通过"路径，而由 `resolutions` 模块的投票表与截止判定实现（ADR-013），但仍使用引擎的实例/快照/撤回壳。已确认的规则（REQ-FUNC-066，OQ-06 a/b/d 已决）：(a) 多审批人时**任一人通过即通过**，事项一经处理其他审批人不能再处理（AC-071-01/02）；(b) 财务类（报销、备用金含核销、收入表）提交时，快照审批人中去掉申请人本人后若没有**当前在任**的可审批人，拒绝提交（AC-071-03）；(d) 决议"指定负责人"方式下发起人若同是被指定负责人，允许自批（AC-071-05）。
- Consequences: 正向：REQ-FUNC-062 的"财务类不得自审"在引擎一处用 `scope` 判定。负向：回调需幂等（判定任务可能重复触发）；多审批人"任一拒绝"如何处理需求未规定（REQ-FUNC-066 备注），本设计取"第一个处理动作（通过或拒绝）即终结该实例"`[ASSUMPTION]`（OQ-22）。

### ADR-013: 时间驱动事项：systemd timer + 管理命令 + 读时惰性判定
- Status: Proposed
- Type: decision
- Context: 需要到点执行的事项：半数同意决议的表决截止判定（REQ-FUNC-060）、投票/调查截止（REQ-FUNC-043/044/047）、业委会/业主代表任期到期失效（REQ-FUNC-053、Q44=C）、季度/年度报表自动生成（REQ-FUNC-050）、审计与验证码过期数据清理（C-07、ADR-008）。
- Options:
  - A systemd timer 每分钟触发 `manage.py run_due_jobs`（oneshot），任务幂等；同时在**读取/提交路径上做惰性判定**（访问一份已过截止时间却仍处于表决中的决议/投票时，先执行同一个幂等判定函数）。优：不新增常驻进程与队列；与 P7"systemd"一致；惰性判定保证即使定时器延迟，用户看到的状态也正确。缺：粒度 1 分钟。
  - B Celery + Redis。优：成熟。缺：新增 Redis 与 worker 两个运行单元；规模不需要。
  - C 进程内线程/APScheduler。优：无外部依赖。缺：多 worker 重复执行、重启丢任务。
  - D 常驻循环服务（Freeark task-scheduler 做法 [CODE: /root/myproject/Freeark/systemctl/freeark-task-scheduler.service:18]）。优：与 Freeark 同构。缺：需自管循环、崩溃重启与漂移；timer 更简单可靠。
- Decision: 选 A。幂等靠"条件更新"：`UPDATE … SET status='PASSED' WHERE id=? AND status='VOTING'` 返回影响行数为 1 者才执行后续动作，不依赖 `select_for_update`（SQLite 不支持锁，测试一致性好）。
- Consequences: 正向：任务可重复执行；测试可直接调用函数传入"当前时间"。负向：时钟必须可信（以服务器时间为准，客户端提交时间一律忽略）；timer 停摆期间由惰性判定兜底，但**报表自动生成与清理会延后**。

### ADR-014: 财务口径：追加式台账 + 备用金核销在创建报销单时声明关联
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-041、058、050：备用金预借审批通过即计入支出；核销只按差额（实际花费合计 − 预借额）调整；与该核销关联的凭票报销单不得再次计入；收入表生效前不计入、作废后不再计入；报表按发生日期归期。OQ-08 已决（REQ-FUNC-050）：备用金预借与核销调整取各自审批通过日；报表明细默认不显示支出事由。
- Options:
  - A 追加式台账 `LedgerEntry`：只写入、不改历史金额，状态仅 `ACTIVE/VOIDED`。报销单**创建时**可声明"用于核销备用金 X"（`settles_advance_id`）；带该声明的报销单审批通过时**不入账**；核销审批通过时入账一条调整额 = Σ(关联报销单金额) − 预借额。优：已生成的季度/年度报表不会被事后"反冲"悄悄改动；规则一次可读；无重复计入。缺：一张已审批通过的"独立报销单"不能事后再挂到某备用金上。
  - B 报销单一律入账；核销审批通过时反冲（作废）关联报销单的入账并入账差额。优：报销单可事后关联。缺：反冲会修改过去期间的台账，已生成报表需整体失效重算，且容易在撤回/驳回路径上出错。
- Decision: 选 A。核销只能关联"创建时声明用于该备用金核销、且已审批通过、尚未被其他核销占用"的报销单（Q107=A 要求关联报销单已审批通过）。台账入账的"发生日期"：报销单取其发生日期字段；备用金预借与核销调整取各自审批通过日（OQ-08 已决）。差额为负表示多余现金退回（支出冲减），为正表示不足部分补报。报表变更：台账条目作废或新增落在已生成报表的期间内时，置该报表 `stale=true` 并提示"有变更，请重新生成"。
- Consequences: 正向：口径单一、可对账（Σ台账 = 报表）。负向：需要在创建报销单页面让用户选择"这是用于核销备用金 X 的报销"（多一个选项）；退回现金登记需求未规定谁登记（REQ-FUNC-058 备注），本设计只记录差额，不建"退款登记"流程。

### ADR-015: 投票/调查的数据与结果模型
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-043~047：多题、题型清单（同意/反对/弃权、打分 1~5、单选、多选、文本）、必答逐题设置、实名记录、一人一票、截止时间必填且不可改、业主代表投票参与者与分母在发起时刻固定（Q103=A）、发起时业主代表为 0 不得发起（Q111 已决 A）、截止后公开汇总、仅"同意/反对/弃权"题判通过。
- Options:
  - A 规范化表：`Poll`/`PollQuestion`/`PollResponse`/`PollAnswer`（答案值用 JSON 列）+ 截止时把汇总**快照**写入 `Poll.result_snapshot`；业主代表投票另存 `PollParticipant` 快照。优：公开汇总读快照，不暴露明细、不因后续身份变化而变；一人一票由 `unique(poll, user)` 保证。缺：JSON 答案不便做 SQL 聚合（量小，应用层聚合）。
  - B 每题一张答案表（按题型分表）。优：可 SQL 聚合。缺：5 种题型 5 张表，迁移与代码量大 `[ESTIMATE]`。
- Decision: 选 A。通过判定：`agree × 2 > denominator`（严格过半，弃权不计同意；`denominator` = 发起时刻参与者数）。调查的参与资格（仅产权业主 / 产权业主+同住人）在**提交时**实时判定（调查参与者名单需求未要求固定）。
- Consequences: 正向：结果可复现、可审计。负向：一份问卷题目数量上限需求未给（Q97），技术防线暂设 50 题并做成配置；合并时 `polls_response`/`polls_participant` 的冲突处理见 ADR-007。

### ADR-016: 附件存储：服务器本地私有目录 + 鉴权下载
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-019（产权证明）、037（决议附件）、040（发票附件）、048（收入凭证）、016（头像）、REQ-FUNC-041/Q59（报销明细仅发起人/审批人/管理员可见）、REQ-NFUNC-002（个人信息保护）。数值已确认：C-12（决议附件）、C-18（其余附件与头像）。
- Options:
  - A 本地磁盘私有目录（不在 Web 根下），元数据入库，下载经鉴权接口（可选 `X-Accel-Redirect` 交给反向代理）。优：无新外部依赖；与物理机部署一致；权限可按所属对象判定。缺：备份需随库一起做；单机磁盘容量。
  - B 对象存储（OSS/COS）+ 预签名 URL。优：容量与 CDN。缺：新增外部服务与费用；P7 未提及。
  - C 数据库 BLOB。优：事务一致。缺：库膨胀、备份慢。
  - （Freeark 做法：`MEDIA_ROOT` 由 nginx 直接公开 `/media/` [CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/freearkweb/settings.py:351-359]，对头像可以，对发票/产权证明**不可接受**，故不照搬。）
- Decision: 选 A。校验：扩展名白名单 + 文件头（魔数）核对 + 大小 + 按用途的数量/合计上限（见 module_design"附件规格表"）；存储名用随机 UUID，不用原文件名；下载响应带 `X-Content-Type-Options: nosniff` 与 `Content-Disposition`。上传一律**逐个文件**走 IFC-004 再按 id 关联，使反向代理的请求体上限只需覆盖单文件。
- Consequences: 正向：权限严格。负向：备份策略（P7 待定）必须覆盖该目录；决议附件在决议公开后对所有登录用户可下载，需下载权限与决议可见性同步。

### ADR-017: 数据库可移植性与并发约束（MySQL 生产 / SQLite 测试）
- Status: Proposed
- Type: constraint-driven
- Context: P1/P8：生产 MySQL、测试 SQLite；约束来源：Django 官方文档——`Index.condition` 在 MySQL 与 MariaDB 上"被忽略，因二者不支持条件索引"，`UniqueConstraint.condition` 与之有相同的数据库限制 [WEB: https://docs.djangoproject.com/en/5.2/ref/models/indexes/ 与 https://docs.djangoproject.com/en/5.2/ref/models/constraints/，2026-11-07]；`select_for_update` 在 SQLite 上无效（框架行为，开发时复核）。
- 被排除方案：依赖部分唯一索引实现"每专有部分仅一个有效户主"；依赖行锁作为唯一正确性保证。
- Decision: 采用"槽位列"技巧：需要"有效记录唯一"的表加可空列 `xxx_slot SMALLINT NULL`，有效时置 1、失效时置 NULL，并对 `(分组键, xxx_slot)` 建普通唯一索引（MySQL/SQLite 都允许多个 NULL）。涉及：`UnitMembership.head_slot`（每专有部分一个户主）、`UnitMembership.active_slot`（每用户每专有部分一个有效身份）、`CommitteeSeat.active_slot`（每用户一个有效业委会/业主代表身份）、`PollResponse(poll,user)`（普通唯一）。应用层用事务 + 捕获 `IntegrityError` 重试；MySQL 上再叠加 `select_for_update` 降低冲突，但**正确性不依赖它**。
- Consequences: 正向：同一套约束在 SQLite 测试中也真实生效，AC-023-04（并发认证只产生一个户主）可被测试。负向：槽位列需要在所有状态转换处同步维护——统一封装在模型方法里，禁止直接 `update()` 绕过。

### ADR-018: 前端结构：一个 Vue SPA 含用户端与管理后台两棵路由树；小程序独立
- Status: Proposed
- Type: decision
- Context: C-01（Web + 小程序，另含管理后台）；管理员与用户令牌主体不同（ADR-005）。
- Options:
  - A 单 SPA，`/` 用户端、`/admin` 管理后台，按路由懒加载；两套 Pinia store（`useAuthStore`、`useAdminAuthStore`）、两个 axios 实例。优：一个构建产物、一份基础设施；管理后台代码按路由拆包，不进入用户端首屏。缺：用户端包能"看到"管理后台路由表（只有路由名，无数据；越权由后端拦截）。
  - B 两个独立 SPA。优：完全隔离。缺：两份构建与部署，公共组件需抽取。
- Decision: 选 A。小程序（uni-app）独立工程，不含管理后台（管理员只用 Web，REQ-FUNC-025）。
- Consequences: 正向：部署与维护简单。负向：必须保证管理后台所有数据接口都由后端按 `AdminAccount` 校验，前端路由守卫仅是体验层。

### ADR-019: 审计日志：数据库追加表，保留期限可配置并由定时任务清理
- Status: Proposed
- Type: decision
- Context: REQ-NFUNC-003/004：记录操作人、对象、时间、结果；范围含认证、户主产生/接任、同住人审批、注销、申诉审核、清册导入与修改、账号合并（含答卷丢弃）、邮箱归属变更、管理员登录、撤销认证、业委会身份与配置变更、决议/报销/备用金/收入表的发起与审批、投票/调查发起、报表生成；C-07 已确认：默认 24 个月，可调整但不得低于 6 个月。
- Options:
  - A 数据库表 `AuditLog`（只追加；操作者与对象存快照字段，不设外键）；管理员后台可查询；超期由 RU-2 清理。优：可查询、可按期限清理、与业务事务同提交。缺：占库（量级小）。
  - B 仅写文件日志（logging）。优：简单。缺：难查询；难按期限清理；不是业务可见的审计。
  - C 外部日志系统（ELK）。优：强大。缺：新运行单元，P7 未提及。
- Decision: 选 A。审计写入与业务写入同一事务（失败即回滚，避免"做了没记"）；审计内容中的手机号一律脱敏存储，不存明文、不存验证码、不存令牌。保留期限以**月**为单位配置（`audit.retention_months`，默认 24，下限 6，经 IFC-009 由管理员修改，低于 6 的值被拒绝并提示，AC-034-04）。
- Consequences: 正向：满足可追溯与留存。负向：审计表有写放大；同事务写入意味着审计写失败会使业务失败（有意为之）；"月"到"天"的清理边界按日历月计算（用标准库按年月运算回退 N 个月，不引入 `python-dateutil` 等新依赖）。

### ADR-020: 个人信息：手机号明文存库，输出层统一脱敏
- Status: Proposed
- Type: constraint-driven
- Context: REQ-NFUNC-002（脱敏 138****0000；仅授权角色可见；选择专有部分时看不到他人手机号；唯一例外：管理员维护清册时可见明文）。约束来源：清册比对与短信发送都需要明文手机号。
- 被排除方案：库内加密存储手机号——比对与发送需要解密，收益有限且引入密钥管理（P7 未定义密钥存放位置）；仅哈希——无法发送短信、管理员无法查看清册明文。
- Decision: 存明文；所有序列化输出走统一的 `MaskedPhoneField`；只有清册维护接口（`/admin/registry/...`）使用 `PlainPhoneField`，且该接口受 `AdminAccount` 保护。日志、审计、异常信息一律用脱敏值。依赖磁盘/库级别的加密由部署侧决定（P7 待定，OQ-10）。
- Consequences: 正向：规则单点、易测试（单测遍历所有序列化器断言无明文手机号）。负向：库被拖库则手机号泄露，缓解依赖部署侧加密与访问控制。

### ADR-021: API 约定：REST/JSON、版本前缀、统一错误与分页
- Status: Proposed
- Type: constraint-driven
- Context: 约束来源：DRF（P1）、Freeark 既有习惯（`{detail: …}` 错误体、`/api/miniapp/` 命名空间 [CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/api/views_miniapp.py:8-15]）、通用经验（接口契约写清列表/单对象、分页方式）。
- 被排除方案：GraphQL（无需求依据）；沿用 Freeark 的 `/api/miniapp/` 与 `/api/` 分命名空间——ocap 三个客户端共用一套接口，不需要按端分。
- Decision: 所有接口 `/api/v1/…`；成功响应直接返回资源对象或 `{count, page, page_size, results: []}`（页码分页，`page_size` 默认 20、最大 100）；错误体统一为 `{"code": "UPPER_SNAKE", "message": "中文提示", "details": {"字段": ["原因"]}}`（`details` 可省略）；状态码：400 校验失败、401 未登录/令牌失效、403 无权限、404 不存在**或无权知悉**、409 状态冲突、413 文件过大、429 限流、502/503 上游（微信/短信/邮件）失败。金额一律字符串化的十进制（如 `"1234.50"`），时间一律带时区 ISO 8601。
- Consequences: 正向：前端/小程序/测试统一处理。负向：与 Freeark 的 `detail` 键不同，复制其前端 http 封装时需改错误解析（见代码复用表）。

### ADR-022: 阿里云短信适配的实现方式（官方 SDK）
- Status: Proposed
- Type: decision
- Context: C-15（短信验证码使用阿里云短信）、REQ-FUNC-001/003/006、REQ-NFUNC-001；IFC-011 是本系统自定义的窄接口，需要一个 `AliyunSmsGateway` 实现。阿里云 `SendSms` 的请求字段（`PhoneNumbers`、`SignName`、`TemplateCode`、`TemplateParam`（JSON 字符串）、`OutId`）与响应字段（`Code`=`OK` 为成功、`Message`、`BizId`、`RequestId`）已在官方文档核实 [WEB: https://help.aliyun.com/zh/sms/developer-reference/api-dysmsapi-2017-05-25-sendsms，2026-11-07]；错误码名称列表见官方错误码页（页面只给名称，未给释义）[WEB: https://api.aliyun.com/document/Dysmsapi/2017-05-25/errorCode，2026-11-07]。
- Options:
  - A 官方 Python SDK `alibabacloud_dysmsapi20170525`（PyPI 最新 4.6.0，Apache-2.0，requires_python ≥ 3.7，2026-07-01 发布；直接依赖 `alibabacloud-tea-openapi` 与 `darabonba-core` [WEB: https://pypi.org/pypi/alibabacloud-dysmsapi20170525/json，2026-11-07]；包名与"Python ≥ 3.7"见官方仓库 README [WEB: https://github.com/aliyun/alibabacloud-python-sdk/blob/master/dysmsapi-20170525/README.md，2026-11-07]）。优：请求签名、重试、序列化由官方维护，本系统不自写签名算法。缺：新增第三方依赖（含传递依赖，数量**未知**，以安装后 `pip freeze` 为准）；SDK 的类名/方法名本次未取得原文（README 把用法放在 `docs/0-Usage-EN.md`，未读到）`[UNSOURCED]`。
  - B 自写签名的 HTTPS 调用（`requests`）。优：零新依赖。缺：需自实现阿里云请求签名，签名算法本次无出处 `[UNSOURCED]`，实现错误即全部短信失败；维护成本高。
  - C 阿里云"号码认证服务"的短信验证码接口（官方文档存在 `SendSmsVerifyCode` 页，仅见搜索结果标题 [WEB: https://help.aliyun.com/zh/pnvs/developer-reference/api-dypnsapi-2017-05-25-sendsmsverifycode，2026-11-07，搜索摘要，未读原文]）。缺：属于另一产品，校验逻辑在阿里云侧，与 C-06 的本系统限流/锁定规则和邮件验证码的统一实现冲突；用户选定的是"阿里云短信"（C-15）。
- Decision: 选 A，并把 SDK 的全部使用限制在 `integrations/aliyun_sms.py` 一个文件内（SDK 在函数内延迟导入，使开发/测试在 `SMS_GATEWAY=console` 时不需要凭据）。SDK 具体调用方式在 PHASE_05 开发时对照官方 `docs/0-Usage-EN.md` 与 README 确认，**不得凭记忆写**。凭据 `ALIYUN_ACCESS_KEY_ID/SECRET` 只从环境变量读取，建议使用 RAM 子账号并仅授予发送短信权限（错误码 `isp.RAM_PERMISSION_DENY` 表明平台按 RAM 鉴权 [WEB: 同错误码页]）。验证码模板用**单变量 `code`**（6 位数字，满足模板规范的 4~6 位 [WEB: https://help.aliyun.com/zh/sms/user-guide/verification-code-template-specifications，2026-11-07]），所有用途（注册/登录/绑定/换号/注销）共用一个模板，有效期文字固定为"5 分钟"，由启动检查 `ALIYUN_SMS_TEMPLATE_TTL_MINUTES == code.sms.ttl_seconds / 60` 保证一致。
- Consequences: 正向：不自写签名；适配器单文件，易替换。负向：多一个依赖及其传递依赖（供应链面，见 tech_stack 风险）；签名/模板审核能否通过取决于业委会主体资质（OQ-20，High 风险）；平台默认流控与本系统限流窗口算法不同，需映射 `isv.BUSINESS_LIMIT_CONTROL` 等为 429（IFC-011）。

## 开放问题 / ASSUMPTION

### A. 已决（用户 2026-11-07 答复："全部按推荐，2. B， 4，我打算以其他组织（业委会）申请"，phase_status clarifications 20:42:22）

| 编号 | 决定 | 落点 |
|---|---|---|
| OQ-01 | A：REQ-FUNC-008 按"微信组件提示快速登录"理解，Mac 同样支持 | ADR-011；IFC-028/029；REQ-FUNC-008、C-05 |
| OQ-02 | B：阿里云短信 | ADR-009、ADR-022；IFC-011；C-15 |
| OQ-03 | A：事务邮件服务（SMTP）；具体厂商未选，不影响契约 | ADR-009；IFC-012；C-16 |
| OQ-04 | 主体"其他组织（业委会）"；备案域名/HTTPS 未答，保留为上线前置条件 | "外部平台前置条件"表；C-17 |
| OQ-05 | A：首次微信登录后进入头像昵称设置页 | ADR-010；IFC-027/032/033；REQ-FUNC-065 |
| OQ-06 | a 任一通过即通过；b 财务类无他人可审批则拒绝提交；c 业主代表为 0 不可发起业主代表投票；d 指定负责人方式下发起人同为负责人可自批 | ADR-012、ADR-015；IFC-082/083/130；REQ-FUNC-066、043、062 |
| OQ-07 | 合并时同一投票/调查保留主账号答卷并审计，其余待办归合并后账号 | ADR-007；IFC-075；REQ-FUNC-067 |
| OQ-08 | 备用金预借/核销调整取审批通过日；报表明细默认不显示支出事由 | ADR-014；IFC-120；REQ-FUNC-050 |
| OQ-09 | 已有管理员可重置他人密码；首个管理员由命令行初始化 | ADR-005；IFC-036/141；REQ-FUNC-068 |
| OQ-10 | 部署侧约定：凭据全部来自环境变量，仓库不含任何凭据；密钥存放、磁盘加密、备份、日志轮转细节待 P7 补齐 | 技术/部署类，不写入需求 |
| OQ-11 | 仅"注册时填写且从未修改"的未验证邮箱可用于邮箱验证码登录；修改过的先登录后验证；多账号同填的未验证邮箱一律拒绝 | IFC-025/034；REQ-FUNC-007、031 |
| OQ-12 | 清册列：楼栋、单元、楼层、户号、手机号（分号分隔）；收入列同 REQ-FUNC-048 字段；金额两位小数；重复 = 日期+金额+类别+来源说明全同 | IFC-042、IFC-111；REQ-FUNC-018、048、059 |
| OQ-13 | 收入表（一批）为审批与作废单位 | MOD-011；REQ-FUNC-049 |
| OQ-14 | 已撤回的决议不公开；发起人账号有效即可撤回自己的事项 | IFC-090；REQ-FUNC-039、063 |
| OQ-15 | 代码布局、测试位置、迁移作业方式接受；允许 `makemigrations --dry-run <app>` 辅助对照、不提交其产物（GR-B-001-F02 关闭） | module_design"代码布局" |
| OQ-16 | A：统一文案"账号或密码错误；若从未设置过密码，请使用验证码登录" | IFC-024；REQ-FUNC-003/005/006 |
| 建议值表 | 全部接受 | "已确认值"表；C-06/07/08/12/18；REQ-FUNC-064 |
| 开放问题 C 节：手机号范围 | 仅中国大陆 11 位 | C-19；IFC-020/022 |

### B. 保留为配置/预留的需求开放项（不自定数值，不阻断）

Q30 申诉处理时限（仅记录提交时间，不做超时动作）；Q96 报销/备用金金额上限（`claim.amount_max` 可空，空 = 无业务上限，仅有字段精度防线）；Q97 题目数量上限（`poll.max_questions`，技术防线暂 50）；Q98 余项（各字段必填项、提示内容形式、"来源说明"可否含个人信息；金额精度、列、重复判定已由 OQ-12 确定）；Q99 成员空缺时"半数"分母（`vote.denominator_mode = ACTIVE | CONFIGURED_CAP`，默认 ACTIVE，每份决议判定时把实际分母写入结果）；Q110 半数同意决议截止时间（用户未单独确认；暂定发起时必填且至少晚于当前 `vote.min_window_minutes`，默认 60 `[ESTIMATE]`，该数值属技术配置）。Q111 已决（OQ-06-c）。需求"观察"项（不规定、本设计保持预留）：用户跳过小程序头像昵称页（见 OQ-24）、多审批人"任一拒绝"（OQ-22）、合并时被丢弃答卷的通知、管理员重置密码审计（OQ-23）、管理员自助找回/禁用、清册导入校验规则与重复处理、备案域名/HTTPS 现状、退回现金登记人。

### C. 架构阶段新提出的 ASSUMPTION / 待用户确认（OQ-17 ~ OQ-26）

| 编号 | 问题 / 暂定处理 | 影响 |
|---|---|---|
| OQ-17 | "记住我"7 天与小程序 7 天按**自登录起绝对 7 天**实现（AC-069-03/04 "登录已满 7 天要求重新登录"）；Freeark 是"闲置 7 天"滑动。若用户想要滑动 7 天，只需改 `EXTENDED` 的判定为闲置计时 | ADR-004；REQ-FUNC-064 |
| OQ-18 | C-18 的"图片"未列格式，暂按 jpg/jpeg/png；手机拍照常见的 HEIC、webp 暂不接受（微信选图通常转为 jpg，Web 端上传 HEIC 会被拒）。是否需要放开 | 申诉证明、发票、凭证 |
| OQ-19 | 阿里云官方建议在发送验证码前加图形验证等防盗刷措施（平台自带的发送频率限制仅企业认证账号可设）[WEB: https://help.aliyun.com/zh/sms/user-guide/verification-code-scams-and-message-flooding-1，2026-11-07]。需求（REQ-NFUNC-001）只规定频率/有效期/错误次数，未要求图形验证。暂不做；如需要应作为新需求提出 | 短信成本、盗刷风险 |
| OQ-20 | 阿里云短信签名需主体资质；官方资质页只列企业、事业单位、个人，未提业主委员会 [WEB: 见前置条件表]。微信小程序"其他组织"认证也需材料且业委会不在免费清单内。**请用户确认业委会是否持有统一社会信用代码证书等可用证件**；若无法取得短信资质，注册/登录/认证/注销全部不可用，需回需求阶段另议（例如改由已有资质的主体代为开通） | 上线前置条件，High |
| OQ-21 | 合并时需求只规定投票/调查答卷；决议表决（`resolutions_vote`）、业主代表投票参与者快照（`polls_participant`）、审批流程审批人名单与审批快照、同住人申请等冲突，暂按"冲突保留主账号、其余归合并后账号"处理（module_design"合并引用登记表"） | REQ-FUNC-067 |
| OQ-22 | 多审批人"任一拒绝"：暂定第一个处理动作（通过或拒绝）即终结实例，其余审批人不能再处理（与 AC-071-02 一致） | REQ-FUNC-066 |
| OQ-23 | 管理员重置密码：暂定同步吊销目标管理员全部令牌并写审计 `ADMIN_PASSWORD_RESET`；不允许重置自己（走"其他管理员"字面）；新密码规则同 C-08（不得与用户名相同） | REQ-FUNC-068 |
| OQ-24 | 小程序用户跳过头像昵称设置页：暂定仅在 `is_new=true` 的那一次登录触发，之后不再提示，昵称为空时展示"用户"+账号后 4 位占位 | REQ-FUNC-065 |
| OQ-25 | 纯微信账号（未验证手机号）注销：REQ-FUNC-017 要求验证码二次确认且"无前提条件"，但这类账号没有可发验证码的手机号。暂定：先绑定手机号（IFC-071）再注销，注销接口对无手机号账号返回 409 `PHONE_REQUIRED`；备选是允许已验证邮箱收验证码。请用户选择 | REQ-FUNC-017 |
| OQ-26 | 收入表导入文件的"凭证附件"列无法承载文件；暂定导入时忽略该列，导入产生草稿（未带 `flow_id`）或直接待审批（带 `flow_id`）；要补凭证须使用草稿。AC-059-01 要求"导入后进入待审批"，故带流程时直接待审批、无凭证 | REQ-FUNC-048、059 |

### D. 上线前置条件汇总（非代码，影响可上线性）
1. 用户确认阿里云短信签名/模板的主体资质（OQ-20）。
2. 小程序（其他组织）完成微信认证并通过备案；开放平台网站应用通过审核（REQ-FUNC-002/008 以此为前提）。
3. 备案域名与 HTTPS（用户未答）；小程序 request 合法域名；服务器出口 IP 加入微信白名单。
4. 邮件发信域名/地址验证与 SMTP 凭据（厂商未选）。
5. 画像 P7 补齐环境/主机/CI，P11-3 同步更新短信=阿里云短信、邮件=事务邮件服务 SMTP，并登记测试替身（`integrations/fakes.py`）。
