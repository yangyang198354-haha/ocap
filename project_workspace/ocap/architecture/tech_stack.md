<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-07T21:06:02+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md (5.0.0 APPROVED)</file><file>architecture/architecture_design.md (0.2.0)</file><file>architecture/module_design.md (0.2.0)</file><file>architecture/tech_stack.md (0.1.0)</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型：业主委员会 Web 应用 + 微信小程序（ocap）

> 0.2.0 修订：(1) 短信确定为阿里云短信（C-15），新增官方 SDK `alibabacloud_dysmsapi20170525`（ADR-022）；邮件确定为事务邮件服务 SMTP（C-16），厂商未选；(2) Django 5.2 LTS 支持期已查证；`requests` 版本与许可证已查证；(3) 风险表按用户决定（主体=其他组织、OQ 已决）重排，新增资质/盗刷/传递依赖风险；(4) `makemigrations --dry-run` 辅助对照已获用户允许。
> 版本出处说明：Freeark 的后端依赖多为未固定版本（`>=` 或无约束），因此"沿用版本"一栏写 Freeark 的约束写法；ocap 新仓库**必须在首次安装后固定到具体版本**（`pip freeze` / `package-lock.json`），固定值在 PHASE_05 填写。包仓库最新版本取自 2026-11-07 查询（PyPI JSON 页、`npm view`），仅作参照。本机没有 `pip`，Python 包最新版本来自 PyPI 网页，不是本机实测。
> 引用约定：`[CODE: …]` Freeark 仓库；`[WEB: URL，2026-11-07]` 联网；`[LOCAL]` 本机命令输出；"未知"= 未能核实。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言（后端） | Python | 3.12（Freeark 生产/CLAUDE.md 声明 [CODE: /root/myproject/Freeark/CLAUDE.md 技术栈表]；本机 `python3 --version` = 3.12.3 [LOCAL]） | 沿用 | C-02；Django 5.2 与 DRF 均支持 | 全部 | 低 |
| 后端框架 | Django | 约束 `django>=5.2.0` [CODE: /root/myproject/Freeark/FreeArkWeb/backend/requirements.txt:2]；PyPI 最新 6.1.3（BSD-3-Clause，requires_python ≥ 3.12）[WEB: https://pypi.org/pypi/Django/json，2026-11-07]。**ocap 选 5.2.x**（官方支持表：5.2 LTS，最新补丁 5.2.19，**安全修复支持到 2028 年 4 月** [WEB: https://www.djangoproject.com/download/，2026-11-07]），具体补丁版本在 PHASE_05 固定 | 沿用 | 与 Freeark 同大版本，便于复制 `authentication.py` 等；DRF 3.18.3 已声明支持 5.2/6.0/6.1 [WEB: https://pypi.org/pypi/djangorestframework/json，2026-11-07] | 全部 | 中：不跟进 6.x 新特性；2028-04 前需规划升级到下一 LTS |
| API 框架 | Django REST Framework | 无约束 [CODE: …/requirements.txt:3]；PyPI 最新 3.18.3（BSD-3-Clause）[WEB: https://pypi.org/pypi/djangorestframework/json，2026-11-07] | 沿用 | C-02；序列化、权限类、分页 | 全部 | 低 |
| 数据存储（生产） | MySQL（InnoDB，utf8mb4） | 实例版本未知（P1/P7：生产 MySQL，主机待定）；驱动 `mysqlclient` 无约束 [CODE: …/requirements.txt:12]，最新版本未查（未知） | 沿用 | C-02、P1 | 全部 | 中：Django 官方文档说明 MySQL/MariaDB 不支持条件索引，`condition` 被忽略 [WEB: https://docs.djangoproject.com/en/5.2/ref/models/indexes/，2026-11-07]，故改用槽位列（ADR-017）；`CheckConstraint`/`JSONField` 行为仍需双库验证；`mysqlclient` 需系统 `libmysqlclient-dev` 编译，目标机架构未定 |
| 数据存储（测试） | SQLite（内存库） | Python 内置 `sqlite3`（版本随 Python，未单独核实） | 沿用 | P1/P8：测试禁连生产库 [CODE: /root/myproject/Freeark/FreeArkWeb/backend/freearkweb/freearkweb/test_settings.py:1-25] | 全部 | 中：无 `select_for_update`，并发正确性靠唯一约束（ADR-017） |
| 应用服务器 | Gunicorn（WSGI，sync/gthread worker） | PyPI 最新 26.2.0（MIT，requires_python ≥ 3.10）[WEB: https://pypi.org/pypi/gunicorn/json，2026-11-07]；Freeark 用 uvicorn/waitress，本项目偏离 | **新增**（替代 Freeark 的 uvicorn） | 无 WebSocket，WSGI 足够；多 worker 安全（限流与验证码用 DB，ADR-008）；Linux 物理机部署（P7） | 全部 | 低；若目标机为 Windows 则不可用（P7 未定，需确认）——此时改用 Freeark 已用的 `waitress>=3.0.0` [CODE: …/requirements.txt:19] |
| 反向代理 | nginx（沿用 Freeark 模式） | 未知（P7 未定是否采用） | 沿用（待 P7 确认） | TLS 终止、静态资源、请求体上限（12 MB）、传递真实客户端 IP（IP 限流依赖，ADR-008）；附件下载可用 `X-Accel-Redirect`（可选） | REQ-FUNC-002/008/019/037/040/048、REQ-NFUNC-001 | 低 |
| 配置读取 | python-dotenv | 无约束 [CODE: …/requirements.txt:5] | 沿用 | 凭据一律环境变量/`.env`，不入库（协议 §L-2） | — | 低 |
| HTTP 客户端（后端） | requests | PyPI 最新 2.34.2（Apache-2.0，requires_python ≥ 3.10）[WEB: https://pypi.org/pypi/requests/json，2026-11-07]；Freeark 代码在用 `requests` [CODE: …/api/views_miniapp.py:34]，但其 requirements.txt 未显式列出（传递依赖），ocap **必须显式列出并固定** | 新增（显式） | 微信 HTTP 调用；5 秒超时（ADR-010） | REQ-FUNC-002~004、008 | 低 |
| Excel/CSV 导入 | openpyxl | 最新 3.1.5（MIT，requires_python ≥ 3.8，上次发布 2024-06-28）[WEB: https://pypi.org/pypi/openpyxl/json，2026-11-07]；CSV 用标准库 `csv` | **新增** | 清册与收入表导入 xlsx（REQ-FUNC-018、059）；只读模式 | REQ-FUNC-018、048、059 | 中：发布节奏慢（最近一次 2024-06），需关注安全公告；对恶意 xlsx（压缩炸弹）要限制文件大小与行数（已在 IFC-042/111 约束） |
| 密码哈希 | Django 默认 PBKDF2-SHA256 | 随 Django | 沿用 | 无新依赖；C-08 | REQ-FUNC-023 | 低：较 Argon2 抗 GPU 弱，量级小可接受；如需 Argon2 须新增 `argon2-cffi` |
| 邮件 | Django SMTP 邮件后端（标准库）+ 事务邮件服务（厂商未选） | 随 Django | 沿用 | 零新依赖；C-16（OQ-03 = A 已决，仅定类别）；厂商不同只影响 `EMAIL_*` 环境变量 | REQ-FUNC-007、031 | 中：到达率与发信域名验证因厂商而异（未核实）；厂商确定前无法联调 |
| 短信 | **阿里云短信**（C-15，OQ-02 = B），经 `SmsGateway`/`AliyunSmsGateway` 适配，官方 SDK `alibabacloud_dysmsapi20170525` | PyPI 最新 4.6.0（Apache-2.0，requires_python ≥ 3.7，2026-07-01 发布）；直接依赖 `alibabacloud-tea-openapi>=0.4.4,<1.0.0`、`darabonba-core>=1.0.0,<2.0.0` [WEB: https://pypi.org/pypi/alibabacloud-dysmsapi20170525/json，2026-11-07]；传递依赖数量：未知 | **新增**（ADR-022） | 官方维护的请求签名与序列化，不自写签名算法；SDK 只在 `integrations/aliyun_sms.py` 内使用；SDK 调用方式开发前对照官方 `docs/0-Usage-EN.md`（本次未读到，[UNSOURCED]） | REQ-FUNC-001/003/006、REQ-NFUNC-001 | **高**：签名/模板需主体资质审核，官方资质页未提及业主委员会（OQ-20）；多一组传递依赖（供应链面）；平台默认流控（1/分钟、5/小时、10/天）窗口算法与本系统不同 |
| 微信接入 | 官方 HTTP 接口，自写适配器，不用 SDK | — | 新增（自写） | ADR-010 | REQ-FUNC-002~004、008、065 | 中：见"技术风险" |
| 前端框架 | Vue 3 | Freeark `^3.5.13` [CODE: /root/myproject/Freeark/FreeArkWeb/frontend/package.json:25]；npm 最新 3.5.45（MIT）[LOCAL: `npm view vue version`，2026-11-07] | 沿用 | C-02 | 全部 | 低 |
| 前端构建 | Vite | Web：Freeark `^6.0.1` [CODE: …/frontend/package.json:36]；小程序：`^5.2.8` [CODE: /root/myproject/Freeark/miniprogram/package.json:27]；npm 最新 8.3.6（MIT）[LOCAL]。**ocap 沿用 Freeark 的主版本（Web 6.x、小程序 5.x，因 uni-app 构建链对 Vite 主版本敏感）** | 沿用 | 复用已验证的构建链，避免 uni-app 与 Vite 新大版本不兼容 | 全部 | 中：与最新大版本差距大；升级需单独评估 |
| Web UI 库 | Element Plus | Freeark `^2.8.7` [CODE: …/frontend/package.json:22]；npm 最新 2.14.8（MIT）[LOCAL] | 沿用 | C-02；管理后台表格/表单/上传 | REQ-FUNC-018、035、054、057 等 | 低 |
| 路由 / 状态 | vue-router、Pinia | vue-router Freeark `^4.4.5` [CODE: …/frontend/package.json:28]，npm 最新 5.4.0；Pinia Freeark `^2.1.7` [CODE: /root/myproject/Freeark/miniprogram/package.json:15]，npm 最新 4.1.0（MIT）[LOCAL]。**沿用 Freeark 主版本** | 沿用 | 与小程序 store 代码保持一致，便于复制 | 全部 | 低 |
| Web HTTP 客户端 | axios | Freeark `^1.7.9` [CODE: …/frontend/package.json:15]；npm 最新 1.21.0（MIT）[LOCAL] | 沿用 | 统一错误解析与令牌注入 | 全部 | 低 |
| 前端金额计算 | decimal.js | npm 最新 10.6.0（MIT）[LOCAL: `npm view decimal.js version`，2026-11-07] | **新增（可选）** | 金额展示与客户端校验禁止浮点（REQ-FUNC-040/048）；若前端只展示后端字符串而不计算，可不引入 | REQ-FUNC-040、048、050 | 低 |
| 小程序框架 | uni-app (Vue 3) + Pinia | Freeark 固定 `@dcloudio/uni-app 3.0.0-alpha-5010320260611001`（`dist-tags.vue3` 现为 3.0.0-alpha-5030620261105001；`latest` 标签指向 2.0.2 老主线，**不要用 latest**）[CODE: /root/myproject/Freeark/miniprogram/package.json:11；LOCAL `npm view @dcloudio/uni-app dist-tags`，2026-11-07]。ocap 先沿用 Freeark 的固定版本 | 沿用 | C-02；复用 `utils/http.js`、`store/auth.js`、测试脚手架 | REQ-FUNC-003、004、045、064、065 | 中：Vue3 线仍为 alpha 标签；固定精确版本，升级前在微信开发者工具真机验证 |
| 前端 Excel | （不引入） | — | — | Freeark 前端含 `xlsx`，但 ocap 的导入在后端做，前端只上传文件，减少依赖与供应链面 | — | — |
| 测试（后端） | Django test runner + SQLite | 随 Django [CODE: /root/myproject/Freeark/CLAUDE.md "测试运行器"] | 沿用 | P4/P8；外部服务一律用 `integrations/fakes.py` 替身，不调用真实微信/阿里云/邮件（协议 §N-4） | 全部 | 低 |
| 测试（前端/小程序） | vitest + @vue/test-utils + jsdom | Freeark：vitest `^2.1.9`、@vue/test-utils `^2.4.x`、jsdom `^24`/`^25` [CODE: …/frontend/package.json:34-37；/root/myproject/Freeark/miniprogram/package.json:22-28]；vitest 最新 5.1.0 [LOCAL]。沿用 2.x | 沿用 | P1 | 全部 | 低 |
| 数据库迁移 | 手写 scoped 迁移；允许 `makemigrations --dry-run <app>` 辅助对照，不提交其产物 | — | 沿用（P6）；dry-run 由用户 2026-11-07 允许（OQ-15） | P6/P8；GR-B-001-F02 已关闭 | 全部 | 低 |
| 进程管理 | systemd（`ocap-backend.service`、`ocap-scheduler.timer/.service`） | 目标机 systemd 版本未知 | 沿用 | P7；ADR-013 | REQ-FUNC-050、053、060 | 低：timer 的 `OnCalendar=*:0/1` 粒度 1 分钟 |
| 容器化 | **不使用** | — | — | P8 禁止 Docker / 容器化 | — | — |
| CI/CD | 未定 | — | — | P7"待定"，E1 阶段前须补齐；本设计不假设 CI 系统 | — | 中 |
| 部署方式 | 物理机，`git pull` + systemd 重启；前端构建产物替换；小程序走微信发布 | — | 沿用 | P7；**禁止 pscp 逐文件上传**（P8） | — | 低 |
| 对象存储 / 缓存 / 消息队列 | **不使用** Redis、Celery、MQ、OSS | — | — | ADR-008/013/016：规模小，避免新运行单元 | — | — |

### 新增第三方依赖汇总（greenfield 的新增项，含理由与许可证/维护风险）

| 依赖 | 理由 | 许可证 | 维护风险 |
|---|---|---|---|
| gunicorn | 替代 uvicorn 的 WSGI 服务器 | MIT [WEB: PyPI，2026-11-07] | 低，活跃 |
| openpyxl | xlsx 导入 | MIT [WEB: PyPI，2026-11-07] | 中，2024-06 后无新版本 |
| requests（显式化） | 微信 HTTP | Apache-2.0 [WEB: https://pypi.org/pypi/requests/json，2026-11-07] | 低，活跃（最新 2.34.2） |
| alibabacloud_dysmsapi20170525 | 阿里云短信官方 SDK（ADR-022）；直接依赖 `alibabacloud-tea-openapi`、`darabonba-core` | Apache-2.0 [WEB: https://pypi.org/pypi/alibabacloud-dysmsapi20170525/json，2026-11-07]；传递依赖的许可证：未知，PHASE_05 安装后逐个核对 | 低（2026-07-01 仍有发布）；传递依赖数量与安全公告未核实 |
| decimal.js（可选） | 前端金额 | MIT [LOCAL: npm view，2026-11-07] | 低 |

未新增：邮件服务商 SDK（走标准 SMTP）；微信 SDK（ADR-010 不用）；Redis/Celery。

### 数值类型与精度（本项目的"数值口径"，非算法项目）

| 项 | 规定 |
|---|---|
| 金额 | 后端 `Decimal`，数据库 `DECIMAL(14,2)`；JSON 用字符串；业务单位元；禁止 `float`；核销差额 = Σ关联报销 − 预借额，可为负；收入表金额最多两位小数（OQ-12） |
| 过半判定 | 整数运算 `agree * 2 > denominator`，不使用浮点除法 |
| 时间 | 服务器 UTC 存储（`USE_TZ=True`），展示按 Asia/Shanghai；截止判定只用服务器时间；会话期限以服务器时间计 |
| 季度/年度归期 | 按自然季度（1-3、4-6、7-9、10-12 月）和自然年，用 `occurred_on` 日期，不涉及时区；备用金预借与核销调整的 `occurred_on` 取各自审批通过日（OQ-08） |
| 验证码 | 6 位纯数字，用 `secrets` 模块（密码学安全随机数）生成；满足阿里云验证码模板单变量 4~6 位的限制（ADR-022） |
| 审计保留期限 | 以日历月计，默认 24，下限 6（C-07） |

## 技术风险

### High

| 风险 | 缓解措施 |
|---|---|
| **短信签名/模板的主体资质未知（OQ-20）**：阿里云官方资质页列出企业、事业单位、个人，证件示例为社会信用代码证书等，未提及"其他组织"与业主委员会 [WEB: https://help.aliyun.com/zh/sms/user-guide/qualification-application-description，2026-11-07]。无短信通道则注册/登录/手机号认证/注销全部不可用 | 立即请用户确认业委会持有的证件（如统一社会信用代码证书）并尽早提交资质申请；开发期用 `console` 替身网关继续联调；若确认无法取得，回需求阶段另议（例如由已有资质的主体代为开通）；不要在资质未通过时承诺上线 |
| **微信认证与开放平台网站应用审核未知（C-17、OQ-04）**：其他组织类小程序必须认证后才能提交发布审核，免费清单列有居民委员会/村民委员会但未列业主委员会，须付费或补材料；开放平台网站应用对"其他组织"的要求官方登录页未写 [WEB: https://developers.weixin.qq.com/miniprogram/product/renzheng.html，2026-11-07] | 用户尽早向微信审核方确认材料与费用；REQ-FUNC-002/008 以网站应用审核通过为前提，不通过则降级（保留手机号/邮箱登录），不影响其余模块；小程序备案/域名/HTTPS 作为上线前置条件 |
| **账号合并事务复杂**（ADR-007）：涉及用户、成员关系、席位、问卷作答、审批快照、待办等多表；漏登记引用会导致数据丢失或合并失败 | `UserReferenceRegistry` + 启动期一致性检查；"合并引用登记表"逐表列出策略；合并专项测试矩阵（同房取高、双户主不可能、同级席位、问卷双作答、审批快照替换、事务回滚）；上线前在测试库上用造数据演练 |

### Medium

| 风险 | 缓解措施 |
|---|---|
| **短信盗刷**：阿里云官方建议发送前加图形验证，且平台自带的发送频率限制仅企业认证账号可设 [WEB: https://help.aliyun.com/zh/sms/user-guide/verification-code-scams-and-message-flooding-1，2026-11-07]；需求只规定频率/有效期/错误次数（OQ-19） | 应用层已按 C-06 限制号码与 IP 频率；IP 取值只信任受信代理（ADR-008）；监控阿里云账单与告警；需要图形验证时作为新需求提出 |
| **阿里云 SDK 用法本次未核实**，其传递依赖数量与许可证未知（ADR-022） | SDK 只在 `aliyun_sms.py` 内使用且延迟导入；PHASE_05 先读官方 `docs/0-Usage-EN.md`；安装后 `pip freeze` 固定版本，逐个核对许可证与安全公告 |
| 阿里云平台流控窗口（分钟/小时按自然窗口）与本系统滚动窗口不同，平台可能先拒绝 | 适配器把 `isv.BUSINESS_LIMIT_CONTROL` 等映射为 429；用户界面提示稍后重试；联调人工验证（无法自动化，协议 §N-4） |
| 短信模板有效期写死，改 `code.sms.ttl_seconds` 会与模板文字不一致 | 启动检查 `ALIYUN_SMS_TEMPLATE_TTL_MINUTES * 60 == code.sms.ttl_seconds`；改有效期须同时重新申请模板 |
| MySQL 与 SQLite 行为差异（`CheckConstraint`、NULL 唯一、`select_for_update`、JSON 查询） | 约束不依赖条件唯一索引（ADR-017，已有官方文档出处）；迁移评审时在两种库各跑一次；并发场景以唯一约束 + 重试保证；MySQL 专项测试只能在非生产 MySQL 实例上由人工执行（P7 未定，列入人工验证清单） |
| 微信接口细节随平台变化（昵称头像获取方式、快速登录出现条件）；多份官方文档正文过长，本次只取得摘要 | `WeChatClient` 单点封装；开发阶段对照官方原文复核"领域与外部依赖出处"表并更新；微信相关用例使用 `FakeWeChatClient`，真实联调标 NOT_TESTABLE + 人工清单（协议 §N-4） |
| 手机号快速验证组件的可用主体与收费说法未获官方原文证实 | 默认关闭（`wechat.phone_quick_verify_enabled=false`），基线走短信验证；小程序完成组织认证后由用户复核官方说明再开启 |
| 会话期限语义：7 天按"绝对 7 天"实现，与 Freeark 的"闲置 7 天"不同（OQ-17）；IDLE 的活动时间写库节流使闲置判断有最多 300 s 误差 | 请用户确认 OQ-17；验收用例对 IDLE 边界留节流容差（ADR-004） |
| 定时器停摆时报表自动生成与清理延后（ADR-013） | 状态判定有读时惰性兜底；`systemd` 的 `OnFailure`/日志监控；`run_due_jobs` 返回非零码便于告警 |
| uni-app Vue3 线为 alpha 标签；Vite/Pinia/vitest 与 npm 最新主版本有差距 | 固定精确版本；升级单独立项；复用 Freeark 已验证组合 |
| 附件与导入文件的安全（恶意文件、超大文件、zip 炸弹） | 魔数校验 + 白名单 + 大小/行数上限；随机存储名；下载 `nosniff`；不在 Web 根下存放；反向代理限制请求体 12 MB；附件逐个上传 |
| 备份：附件目录与数据库需成套备份（P7 未定） | 作为部署前置条件（OQ-10）交用户；设计不依赖具体备份工具 |
| 令牌被盗后可直接更换手机号（IFC-072 不要求二次验证旧号） | 需求仅要求验证新号；建议后续迭代评估增加旧号/密码二次确认（需用户决定，未加入需求） |
| 纯微信账号（未验证手机号）无法发注销验证码（OQ-25） | 暂定先绑定手机号再注销；请用户选择备选（已验证邮箱收码） |

### Low

| 风险 | 缓解措施 |
|---|---|
| PBKDF2 抗 GPU 能力弱于 Argon2 | 密码仅为可选登录方式（验证码为主）；如需提升再引入 `argon2-cffi` |
| `requests`、`alibabacloud_dysmsapi20170525` 等版本在 PHASE_05 前未固定 | 首次安装时固定并写入 requirements |
| 1 分钟定时器粒度 | 需求无秒级截止要求；服务器侧读时判定补足 |
| "图片"格式范围（OQ-18）：HEIC/webp 暂不接受 | 请用户确认；放开只需扩充附件规格表白名单与魔数检查 |
