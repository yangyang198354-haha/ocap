# Project Profile — ocap（业主委员会 Web + 微信小程序）

> PM 扫描生成，用户 2026-11-07 确认（"所有按推荐"）。出处标注：[REPO] = 本仓库扫描；[FREEARK] = /root/myproject/Freeark 扫描（origin: github.com/yangyang198354-haha/Freeark）；[USER] = 用户 2026-11-07 原话；未知 = 待确认。

<file_header>
  <author_agent>pm-orchestrator(draft)</author_agent>
  <timestamp>2026-11-07T22:12:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.2.0</version>
  <status>APPROVED</status>
</file_header>

## P1. 项目概况
- 一句话描述：业主委员会 Web 应用 + 微信小程序（注册登录、业主清册认证、户主/同住人/游客身份管理…）[USER]
- 技术栈（拟沿用 Freeark，[USER]"技术选型、代码复用参考 Freeark"；最终以架构阶段 ADR 为准）：
  | 层 | 技术 | 出处 |
  |---|---|---|
  | Web 后端 | Django 5.2 + DRF (Python 3.12) | [FREEARK] CLAUDE.md、FreeArkWeb/backend/requirements.txt |
  | Web 前端 | Vue 3 + Vite + Element Plus | [FREEARK] CLAUDE.md |
  | 微信小程序 | uni-app (Vue 3) + Pinia，测试 vitest | [FREEARK] miniprogram/package.json |
  | 数据库 | 生产 MySQL / 测试 SQLite | [FREEARK] CLAUDE.md；本项目实例 未知 |
- 运行形态：Web 服务 + 微信小程序
- 权威说明文档：暂无（[REPO] 仓库为空，无 CLAUDE.md / README）

## P2. 文档工作区
- `docs_root`: project_workspace/ocap/
- `docs_layout`: nested
- 是否入库: 是（随代码由用户确认后提交）

## P3. 代码布局
- `code_mode`: greenfield（[REPO] 无代码、无提交）
- 代码目录（OQ-15 用户已确认，见 module_design「代码布局建议」）：
  | 组件 | 目录 | 语言 |
  |---|---|---|
  | Django 后端 | `backend/`（`config/`、`apps/{core,integrations,accounts,registry,residency,committee,identity,approval,resolutions,claims,income,ledger,polls,jobs}/`） | Python |
  | Web 前端 | `frontend/src/`（portal / admin / shared） | Vue 3 + Vite |
  | 微信小程序 | `miniprogram/` | uni-app (Vue 3) |
  | systemd 模板 | `deploy/systemd/` | — |
- 测试位置约定：
  | 组件 | 新测试放在 | 命名 | 框架 |
  |---|---|---|---|
  | 后端 | `backend/apps/<app>/tests/`、跨 app 集成 `backend/tests/integration/` | `test_*.py` | Django test runner |
  | Web 前端 | `frontend/tests/` | `*.spec.js` | vitest |
  | 小程序 | `miniprogram/tests/` | `*.spec.js` | vitest |
- 迁移：每个 app 的 `migrations/` 手写、单 app 范围；`makemigrations --dry-run <app>` 仅辅助对照，产物不提交
- 不可修改的目录：`.claude/**`（只读源套件）、`.trae/skills/**`、`.trae/sdlc/scripts/**`、`.trae/sdlc/suite_config.md`

## P4. 命令（全部在开发机/CI 上运行，严禁连生产；环境事实取自 2026-11-07 本机实测）
| 用途 | 工作目录 | 命令 | 备注 |
|---|---|---|---|
| 版本检查 | 仓库根 | `python --version`；`python -c "import django;print(django.get_version())"` | 本机 Python 3.14.6、Django 6.0.6、DRF 3.17.1（选型目标为 Django 5.2.x，本机未安装 5.2；差异记入开发报告，不自行安装/降级） |
| 静态检查 | 仓库根 | `python -m compileall -q backend` | 无第三方 linter |
| 后端单元/集成/E2E | `backend/` | `python manage.py test --settings=config.test_settings` | Django test runner + SQLite 内存库；测试替身 `apps/integrations/fakes.py` |
| 前端测试 | `frontend/` | `npm test`（vitest run） | 依赖未安装时不自行 `npm install`，如实标 BLOCKED |
| 小程序测试 | `miniprogram/` | `npm test`（vitest run） | 同上 |
- 已知既有失败 / 基线来源：无（greenfield）
- 缺依赖时的处理：如实标 BLOCKED，不安装（本机缺 `openpyxl`、阿里云短信 SDK；后者测试只用 fake）
- 外部服务：测试只经 `apps/integrations/fakes.py`，不得调用真实微信/阿里云/邮件服务

## P5. 质量判定
- FULL_FLOW `gate_mode`: threshold — unit_pass 0.80 / integration_pass 0.90 / critical_path 1.00 / coverage_min 无
- INCREMENTAL `gate_mode`: baseline — 零新增失败
- `inferred_max`: 0.20

## P6. 开发约定
- 数据迁移：沿用 Freeark——手写 scoped 迁移，禁用 makemigrations 全量产物 [FREEARK][USER 确认]
- 鉴权与权限模型：注册用户分游客 / 产权业主（户主）/ 同住人 [USER]；后台管理员角色 未知
- 其他：未知

## P7. 环境、CI 与部署
- 部署方式：物理机部署（tar 打包 → scp → 解包 → 迁移 → systemd 重启），非容器 [FREEARK][USER 2026-11-08]
- CI：GitHub Actions，仓库 `github.com/yangyang198354-haha/ocap`，分支 `main`，工作流 `.github/workflows/ci.yml`；CI 只跑测试与构建，不部署 [USER 2026-11-08]
- 环境矩阵：
  | 环境 | 主机 | 服务 | 数据库 | 访问入口 | 部署需用户确认 |
  |---|---|---|---|---|---|
  | 测试（内网） | 树莓派 192.168.31.51（用户 yangyang，免密 SSH） | gunicorn `127.0.0.1:9000`（systemd `ocap-backend`）+ nginx `8090` | MySQL 192.168.31.98:3306 独立库 `ocap` | `http://192.168.31.51:8090/ocap/` | 是 |
  | 测试（外网） | 同上，经 Freeark 的 frp 通道（Pi nginx `8080` + VPS 443） | 复用 Freeark nginx 的 `^~ /ocap/` 前缀反代 | 同上 | `https://ai-freeark.xin/ocap/` | 是 |
  | 生产 | 无 | — | — | — | — |
- 同机共存约束：树莓派上已有 Freeark（uvicorn:8000、nginx:80/8080、frpc），ocap 不得占用其端口、服务名、代码目录、数据库库名；修改 Freeark 的 nginx 配置前必须备份 [USER 2026-11-08]
- 测试环境短信：`SMS_GATEWAY_BACKEND=console`（替身，短信服务未就绪）[USER 2026-11-08]

## P8. 禁用项
| 禁用的技术 / 操作 | 原因 |
|---|---|
| 测试连接生产数据库 | 协议 §L-4 |
| Docker / 任何容器化方案 | 沿用 Freeark 约定 [USER 确认] |
| pscp 逐文件上传部署 | 沿用 Freeark 约定 |
| makemigrations 全量产物 | 沿用 Freeark 约定 |

## P9. 版本控制与远程操作权限
- 分支策略：未知（[REPO] 当前分支 master，尚无提交）
- 谁执行 commit / push：子代理不执行；PM 在每阶段结束列出待提交文件，用户确认后由主会话提交 [USER 确认]
- 子代理是否可 ssh / 部署：否

## P10. 额外必读
| Agent | 额外文件 |
|---|---|
| requirement-analyst | /root/myproject/Freeark/docs/requirements/v1.8.0_miniprogram_owner_account/requirements_spec.md、/root/myproject/Freeark/project_workspace/FreeArk_OwnerMgmt/requirements_spec.md（仅作参考，ocap 需求以用户原文为准） |
| system-architect | /root/myproject/Freeark/CLAUDE.md |
| software-developer | 同上 |
| test-engineer | |
| devops-engineer | |

## P11. 领域与外部依赖
### P11-1 专用硬件
无
### P11-2 领域算法
无
### P11-3 闭源 / 内部 API（架构阶段已定类别；具体端点/字段以官方文档为准，代码中标注出处）
| API | 文档 | 现有调用代码 | 测试替身 | 凭据位置 | 调用限制 |
|---|---|---|---|---|---|
| 微信小程序登录 / 手机号快速验证 | 微信官方文档（未在仓库）；SDK 字段 [UNSOURCED] | 参考 Freeark：`FreeArkWeb/backend/freearkweb/api/views_miniapp.py`、`miniprogram/pages/login/index.vue` | `apps/integrations/fakes.py`（FakeWeChatClient） | 环境变量（位置待定，不写值） | 5 秒超时；不得真实调用 |
| 微信开放平台网站扫码登录 | 微信官方文档（未在仓库） | 无 | `FakeWeChatClient` | 环境变量 | 5 秒超时；不得真实调用 |
| 短信验证码（阿里云短信，C-15/OQ-02=B） | 阿里云官方文档/官方 SDK `alibabacloud_dysmsapi20170525`；SDK 调用方式 [UNSOURCED] | 无（SDK 缺失，测试用 fake） | `FakeSmsGateway` | 环境变量 | 计费；平台流控 1/分钟、5/小时、10/天 |
| 邮件服务（事务邮件 SMTP，C-16/OQ-03=A） | Django EmailBackend | 无 | `FakeEmailGateway` / locmem backend | 环境变量 | 厂商未定 |
