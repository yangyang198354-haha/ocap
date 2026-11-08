<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-09T00:18:12+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>deployment/deployment_plan.md (2.0.0 APPROVED)</file>
    <file>deployment/cicd_pipeline.md (2.0.0 APPROVED)</file>
    <file>phase_status.md (GROUP_E1 APPROVED, GR-E1-003)</file>
    <file>.claude/skills/ocap-deploy/SKILL.md</file>
    <file>.claude/agents/project_profile.md (1.3.0, P7/P8/P9)</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：ocap 后端 + Web 前端 + run_due_jobs timer → 测试环境（1.1.0，对应 deployment_plan 2.0.0）

> 1.0.0（2026-11-08 12:35，锚点 20261108123556，DEPLOYED_SUCCESSFULLY）已被本次部署取代。REWORK_AUTHORIZED: project_workspace/ocap/deployment/deployment_report.md。

## 摘要

| 项 | 值 |
|---|---|
| 目标环境 | 测试环境（树莓派 raspberrypi；外网通道 47.109.197.217:57279；对外 https://ai-freeark.xin/ocap/） |
| 部署策略 | recreate（单实例） |
| 开始时间 | 2026-11-08T23:47:07+08:00（本地预检起点）；目标机变更始于 23:48:53（DEPLOY-001） |
| 结束时间 | 2026-11-09T00:18:03+08:00 |
| **回滚锚点 TS** | **`20261108234853`**（`/home/yangyang/ocap/snapshots/backend-20261108234853.tar.gz` 26829425 B、`web-20261108234853.tar.gz` 446862 B；`/etc/nginx/sites-available/ocap.bak_20261108234853`、`freeark.bak_20261108234853`） |
| 部署版本标识 | 本地 `git rev-parse HEAD` = `c0d1f0ae3c2bd8219784c09cd7afe27ee4c5b5f4`；工作树有未提交改动（见下），未 commit / push（用户未授权） |
| 总步骤 | 9（DEPLOY-001~009） |
| 完成 | 7（001、002、003、004、005、006、009） |
| 失败 | 0 |
| 跳过 | 2（007、008：nginx 配置无改动） |
| 最终状态 | **DEPLOYED_SUCCESSFULLY** |

### 版本标识：`git status --short`（部署时 22 项）

- 已修改（17）：`.claude/agent-memory/{pm-orchestrator,test-engineer}/MEMORY.md`、`.claude/skills/ocap-deploy/SKILL.md`、`backend/apps/accounts/services.py`、`backend/apps/core/permissions.py`、`frontend/src/shared/api.js`、`miniprogram/tests/pages.spec.js`、`project_workspace/_kb_inbox.jsonl`、`project_workspace/ocap/{deployment/cicd_pipeline.md, deployment/deployment_plan.md, development/code_review_report.md, development/implementation_plan.md, phase_status.md, testing/e2e_test_report.md, testing/integration_test_report.md, testing/test_plan.md, testing/unit_test_report.md}`
- 未跟踪（5）：`backend/tests/e2e/test_gap_journeys.py`、`backend/tests/integration/test_gap_must_have.py`、`deploy/`（含 `deploy/systemd/ocap-run-due-jobs.{service,timer}`）、`frontend/tests/login.spec.js`、`project_workspace/ocap/pm_escalation_GROUP_D_20261108T2330.md`
- 进入部署包的产品改动：`backend/apps/accounts/services.py`、`backend/apps/core/permissions.py`（GR-C-006/007）、`frontend/src/shared/api.js`、`deploy/systemd/*`。tests、文档、`.claude/` 未打包。
- 建议：部署后由用户确认提交并推送，使目标机内容与远端提交号对应。

## 授权核对

- 授权来源：本次 invocation（ocap-GROUP_E2-2）的 `special_instructions`，含 `PRODUCTION_DEPLOY_CONFIRM=true`，用户原话 "Q2:a"（由 PM 转述）；画像 P7 测试环境"部署需用户确认=是"。
- 授权环境名「测试环境」= deployment_plan 2.0.0 目标环境「测试环境」= 画像 P7 环境名「测试」；画像无生产环境，未触碰其他主机。
- deployment_plan 版本 2.0.0 = phase_status 登记的 APPROVED 版本（`phase_status.md` artifacts：deployment_plan.md 2.0.0 APPROVED；GR-E1-003 PASS_WITH_CONDITIONS，22:46:30）。
- 主机指纹核对：`ssh-keyscan -p 57279 -t ed25519 47.109.197.217 | ssh-keygen -lf -` 输出 `256 SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk (ED25519)`，与画像 P7 一致；`~/.ssh/known_hosts` 已有该主机条目。

## 预检结果

| # | 检查 | 实际结果 | 通过 |
|---|---|---|---|
| 1 | 主机指纹 | `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk` | 是 |
| 2 | 版本标识 | HEAD `c0d1f0a…`；22 项改动已记录（见上） | 是 |
| 3 | 本地回归 | `manage.py test --settings=config.test_settings`：`Ran 212 tests … OK`（Django 5.2.19）。**与计划写的 278 不符**：本地后端实际为 212 条（`tests/` 全量，0 失败）；278 可能含前端/小程序用例。已列入遗留问题 | 是（0 失败） |
| 4 | 迁移无漂移 | `makemigrations --check --dry-run` → `No changes detected`，退出码 0 | 是 |
| 5 | 无新增迁移文件 | `git diff --name-status a7d7fcd HEAD -- backend/apps \| grep migrations`：3 条 `M`（claims/income/ledger 0003），无 `A` | 是 |
| 6 | 目标机迁移状态 | 未应用条数 `unapplied=0`（`/tmp/mig_before.txt` 已保存于目标机） | 是 |
| 7 | SECRET_KEY 非空 | `SECRET_KEY_SET`（未打印值） | 是 |
| 8 | ALLOWED_HOSTS 非空 | `ALLOWED_HOSTS_SET` | 是 |
| 9 | .env 格式 | 合法行数 / 总行数 = `12/12`；`export ` 行数 0 | 是 |
| 10 | timer 单元尚不存在 | `systemctl list-unit-files "ocap-run-due-jobs*"` 无输出 | 是 |
| 11 | 目标机目录 | 仅 `backend/ snapshots/ web/` | 是 |
| 12 | 磁盘 / 内存 | `/` 可用 16G；内存 available 1786 MB | 是 |
| 13 | 端口归属 | 80/8000/8080/8090/9000 在监听；8000 为 uvicorn（Freeark）；9000 gunicorn（ocap） | 是 |
| 14 | venv 可用 | `Python 3.13.5` | 是 |
| 15 | nginx 语法 | `syntax is ok` / `test is successful` | 是 |
| 16 | Freeark 基线 | `freeark8080=200` | 是 |

## 分步执行

| DEPLOY | 命令摘要 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| 001 | `TS=$(ssh … date +%Y%m%d%H%M%S)`；双引号远端命令：`tar czf backend-$TS / web-$TS`、`cp` 两份 nginx 备份 | 23:48:51 | 7 s | SUCCESS | `ANCHOR_TS=20261108234853`；`exit=0`；4 个文件均存在、非零大小；`tar tzf` 首行 `backend/`、`backend/config/` |
| 002 | 本地 `tar --exclude=__pycache__/venv/.env/var/db.sqlite3/./tests -C backend .` → scp -P 57279 → 远端 `tar xzf` | 00:07:51 | 约数秒 | SUCCESS | 包 82269 B，本地与目标机 sha256 均为 `dc0bd758a8da3482f0cadf3cc1a84888ba16cf72e489f17ad9747066ea2d8d50`；`exit=0`；`ENV_PRESENT`、`VENV_PRESENT` |
| 003 | `pip install --dry-run -r requirements.txt` → `pip install -r requirements.txt` | 00:08:07 | 约 12 s | SUCCESS | `dry_exit=0`；`Requirement already satisfied …`；`exit=0`（无新增依赖） |
| 004 | 加载 `.env` → `manage.py migrate --noinput` → `showmigrations --plan` 与 `mig_before` diff | 00:08:19 | 约 12 s | SUCCESS | `No migrations to apply.`；`MIGRATION_STATE_UNCHANGED`（预期，无迁移应用，未触发 MANUAL_ROLLBACK） |
| 005 | `sudo systemctl restart ocap-backend && sleep 2 && is-active`；`journalctl -n 30` | 00:08:31 | 约 4 s | SUCCESS | `active`；gunicorn 26.2.0，Listening at 127.0.0.1:9000，4 个 sync worker 启动；无 Traceback / ImproperlyConfigured |
| 006 | 本地 `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/`（`✓ built in 23.33s`，仅 chunk>500kB 警告）→ tar → scp → 远端 `rm -rf web/ocap/* && tar xzf` | 00:14:24（构建在 23:48 完成） | 数秒 | SUCCESS | `exit=0`；`index.html` 412 B；资源引用 `/ocap/assets/index-C3bMrqMV.js`、`/ocap/assets/index-bh_uPu0q.css` |
| 007 | nginx 配置更新 | — | — | SKIPPED | 配置无改动；`ocap` 与 `freeark` 站点文件 mtime 仍为 2026-11-08 11:02/11:03 |
| 008 | nginx reload | — | — | SKIPPED | 随 007 跳过，未执行 reload |
| 009 | tar 上传 `deploy/systemd/*` → `install -m 644` → `systemd-analyze verify` → `daemon-reload` → `enable --now ocap-run-due-jobs.timer` | 00:16:19 | 数秒 | SUCCESS | `verify_exit=0`；`Created symlink …/timers.target.wants/ocap-run-due-jobs.timer`；`exit=0`；`enabled`、`active`；list-timers：NEXT `Mon 2026-11-09 00:17:00 CST`（只 enable timer，未 enable service） |

## 验证结果

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| `systemctl is-active ocap-backend nginx` | `active` / `active` | 是 |
| 后端日志（部署后 00:08 起） | `grep -Ec 'Traceback\|ERROR\|ImproperlyConfigured'` = `0` | 是 |
| timer 已注册 | `Mon 2026-11-09 00:19:00 CST 51s … ocap-run-due-jobs.timer ocap-run-due-jobs.service`（NEXT 有值，LAST 已触发） | 是 |
| 手动执行一次 service | `exit=0`；`Result=success`；`ExecMainStatus=0` | 是 |
| 任务日志 | `run_due_jobs ok: {'polls_closed': 0, 'resolutions_judged': 0, 'seats_expired': 0, 'reports_generated': 2, 'tokens_purged': 0, 'codes_purged': 0, 'states_purged': 0, 'tickets_purged': 0, 'audit_purged': 0}`；`Finished …`；ERROR/Traceback 计数 0 | 是 |
| 登录接口（错误凭据，账号 `nobody_20261108234853`） | `{"code":"LOGIN_FAILED",…} HTTP=400` | 是 |
| 管理员登录端点 | `admin_login=400` | 是 |
| 内网前端 / 静态 | 开发机（云主机）不在 192.168.31.x 网段，直连 `http://192.168.31.51:8090` 为 000（不可达，非服务问题）。改在目标机上请求 `127.0.0.1:8090`：`8090=200 text/html`；`static=200 1129731` | 是（经目标机本机替代） |
| 外网前端 | `https://ai-freeark.xin/ocap/` → `200 text/html 412` | 是 |
| 外网静态 | `…/ocap/assets/index-C3bMrqMV.js` → `200 application/javascript 1129731` | 是 |
| SPA 回退 | `…/ocap/admin/login` → `200 text/html 412`（同 index.html） | 是 |
| Freeark 首页 | `https://ai-freeark.xin/` → `200`；目标机 `127.0.0.1:8080` → `200` | 是 |
| 失败单元 | `systemctl --state=failed` 无输出（无 freeark-*、ocap-* 失败单元） | 是 |
| Freeark 服务 | frpc `active`；11 个 `freeark-*.service` 全部 `active running`，4 个 `freeark-*.timer` `active waiting`；本次未对其做任何操作 | 是 |
| 端口归属 | 9000 gunicorn（ocap）；8000 uvicorn（Freeark）；8080、8090 为 nginx | 是 |

## 回滚记录

无需回滚：所有 DEPLOY 步骤成功，验证全部通过。

回滚方式（如用户后续决定回滚）：按 deployment_plan 2.0.0 逆序，先 ROLLBACK-009（卸载 timer），再 ROLLBACK-006（恢复 `web-20261108234853.tar.gz`）、ROLLBACK-002 + ROLLBACK-005（恢复 `backend-20261108234853.tar.gz` 并重启）；本次未应用迁移，ROLLBACK-004 不需要。nginx 未改动，不需要 ROLLBACK-007/008。

## 当前系统状态

- ocap-backend.service：active，gunicorn 26.2.0，127.0.0.1:9000，4 workers；代码为本地工作树打包版本（HEAD c0d1f0a + 未提交改动）。
- 前端静态：`/home/yangyang/ocap/web/ocap/`，入口 `index-C3bMrqMV.js`。
- `ocap-run-due-jobs.timer`：enabled、active，每分钟触发。
- nginx 与 Freeark：未改动、未重启；Freeark 全部服务正常。
- 数据库 `ocap`：迁移状态与部署前一致（无新应用）。
- 回滚快照与 nginx 备份保留在目标机（≥ 7 天）。

## 遗留问题

1. **不可逆数据影响（已发生，需知悉）**：timer 启用后每分钟运行 `run_due_jobs`，会生成季报/年报并清理过期数据；手动执行一次（00:16:47）输出 `reports_generated: 2`，其余清理计数为 0。这些变更不随 ROLLBACK-009 撤销 `[MANUAL_ROLLBACK_REQUIRED: 已生成的季报/年报与已清理的过期数据不可由卸载 timer 恢复]`。
2. **版本未入库**：部署对象含未提交改动，目标机无提交号对应。建议用户确认后 commit 并 push（子代理不执行，画像 P9）。
3. **测试条数口径**：计划预检写"278/278"，本地实跑后端为 212 条全部通过；请 PM 核对 278 的来源（可能含前端 vitest / 小程序用例）后修正文档。
4. **目标机旧文件残留**：解包不删除旧文件，`/home/yangyang/ocap/backend/tests/` 为上一次部署遗留，本次未打包 tests；无害，未清理。
5. 内网地址 192.168.31.51:8090 无法从本部署主机直连，已用目标机本机请求替代；如需严格验证，请在内网主机上访问。
6. 短信为 `console` 替身，微信未配置，上线前补 `WECHAT_*`；小程序 RU-4 未部署。
7. 前端主 chunk 1.13 MB（gzip 374 KB），建议后续 code-splitting，不影响功能。
