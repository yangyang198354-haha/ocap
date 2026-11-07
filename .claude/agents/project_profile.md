# Project Profile — ocap（业主委员会 Web + 微信小程序）

> PM 扫描生成，用户 2026-11-07 确认（"所有按推荐"）。出处标注：[REPO] = 本仓库扫描；[FREEARK] = /root/myproject/Freeark 扫描（origin: github.com/yangyang198354-haha/Freeark）；[USER] = 用户 2026-11-07 原话；未知 = 待确认。

<file_header>
  <author_agent>pm-orchestrator(draft)</author_agent>
  <timestamp>2026-11-07T16:58:05+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
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
- 代码目录：待架构阶段确定（倾向仿 Freeark：backend/、frontend/、miniprogram/ 于仓库根）
- 测试位置约定：未知（待架构阶段确定）
- 不可修改的目录：无

## P4. 命令
- 全部 未知（无代码）。建议参照 Freeark：Django test runner + SQLite 测试库；小程序 vitest。
- 缺依赖时的处理：如实标 BLOCKED，不安装

## P5. 质量判定
- FULL_FLOW `gate_mode`: threshold — unit_pass 0.80 / integration_pass 0.90 / critical_path 1.00 / coverage_min 无
- INCREMENTAL `gate_mode`: baseline — 零新增失败
- `inferred_max`: 0.20

## P6. 开发约定
- 数据迁移：沿用 Freeark——手写 scoped 迁移，禁用 makemigrations 全量产物 [FREEARK][USER 确认]
- 鉴权与权限模型：注册用户分游客 / 产权业主（户主）/ 同住人 [USER]；后台管理员角色 未知
- 其他：未知

## P7. 环境、CI 与部署
- 部署方式：沿用 Freeark——物理机部署，git pull + systemd 服务重启 [FREEARK][USER 确认]
- 环境（dev/staging/production）、主机、CI：待定（以后再补；补齐前 E1 不能出部署计划）

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
### P11-3 闭源 / 内部 API（需求中出现的外部服务；用户 2026-11-07 决定架构阶段再补资料，需求阶段不涉及对接细节）
| API | 文档 | 现有调用代码 | 测试替身 | 凭据位置 | 调用限制 |
|---|---|---|---|---|---|
| 微信小程序登录 / 手机号快速验证 | 未知 | 可能参考 [FREEARK] miniprogram/pages/login/index.vue、api/views_miniapp.py | 未知 | 未知 | 未知 |
| 微信开放平台网站扫码登录 | 未知 | 未知 | 未知 | 未知 | 未知 |
| 短信验证码服务（服务商未定） | 未知 | 未知 | 未知 | 未知 | 计费 |
| 邮件服务（邮箱登录/验证用） | 未知 | 未知 | 未知 | 未知 | 未知 |
