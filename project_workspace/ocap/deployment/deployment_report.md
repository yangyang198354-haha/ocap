<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-08T12:45:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>deployment/deployment_plan.md (1.0.0 APPROVED)</file>
    <file>deployment/cicd_pipeline.md (1.1.0 APPROVED)</file>
    <file>phase_status.md (GROUP_E1 APPROVED)</file>
    <file>.trae/sdlc/project_profile.md (P7/P8/P9)</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：ocap 后端 + Web 前端 → 测试环境

## 摘要

| 项 | 值 |
|---|---|
| 目标环境 | 测试环境（树莓派 192.168.31.51，对外 ai-freeark.xin/ocap/） |
| 部署策略 | recreate（单实例） |
| 开始时间 | 2026-11-08 12:35 +08:00 |
| 结束时间 | 2026-11-08 12:44 +08:00 |
| 回滚锚点 | `20261108123556`（backend + web tar 快照 + nginx 配置备份） |
| 总步骤 | 8（DEPLOY-001~008，跳过 DEPLOY-007/008 因 nginx 配置未变） |
| 完成 | 6（001~006） |
| 失败 | 0 |
| 跳过 | 2（007 更新 nginx 配置、008 reload nginx） |
| 最终状态 | **DEPLOYED_SUCCESSFULLY** |

## 授权核对

- 授权来源：用户本轮消息原话「授权在树莓派部署后端和web」，下一轮「确认部署」确认。
- 授权环境名 = 计划环境名 = 画像 P7 环境名：测试环境（树莓派 192.168.31.51）。
- deployment_plan 版本 = phase_status 登记的 APPROVED 版本：1.0.0。
- special_instructions 含 `PRODUCTION_DEPLOY_CONFIRM=true`。

## 分步执行

| DEPLOY | 命令摘要 | 结果 | 输出摘要 |
|---|---|---|---|
| 001 快照 | `tar czf backend-$TS.tar.gz`、`web-$TS.tar.gz`；备份 nginx 配置 | SUCCESS | 锚点 `20261108123556`；backend 26M、web 437K |
| 002 后端上传 | `tar czf ocap_backend.tar.gz`（排除 venv/.env/var/db.sqlite3）→ scp → `tar xzf` | SUCCESS | 93KB；`manage.py` 就位 |
| 003 依赖 | `venv/bin/pip install -r requirements.txt` | SUCCESS | Requirement already satisfied（无新增依赖） |
| 004 迁移 | `manage.py migrate --noinput`（首次 No migrations to apply，检测到 claims/income/ledger 模型变更未生成迁移） | SUCCESS | 生成 3 个迁移（索引重命名 + line_no 移除 default + Meta ordering）并应用：claims.0003 OK、income.0003 OK、ledger.0003 OK |
| 005 重启后端 | `sudo systemctl restart ocap-backend` | SUCCESS | gunicorn 26.2.0，监听 127.0.0.1:9000，4 workers，无 Traceback |
| 006 前端 | `npm run build -- --base=/ocap/`（VITE_API_BASE=/ocap/api/v1）→ tar → scp → 替换 web/ocap/* | SUCCESS | 构建 12.59s；index.html 就位 |
| 007 nginx 配置 | 跳过（配置未变，此前已设好 `^~ /ocap/`） | SKIPPED | — |
| 008 nginx reload | 跳过（配置未变） | SKIPPED | — |

> **迁移补充说明**：DEPLOY-004 首次执行发现 claims/income/ledger 三个 app 的模型有未反映到迁移的变更（G-001~G-014 设计对齐修复引入）。经 dry-run 核验均为安全操作（索引重命名、Meta ordering、line_no 移除 default=1），生成 3 个 0003 迁移文件并提交推送（commit c275c46），随后应用成功。标 `[MANUAL_ROLLBACK_REQUIRED: 索引重命名可逆；line_no 移除 default 可逆；无数据丢失风险]`。

## 验证结果

| 检查项 | 命令/URL | 实际结果 | 通过 |
|---|---|---|---|
| 后端存活 | `systemctl is-active ocap-backend` | `active` | ✓ |
| 后端日志 | `journalctl -u ocap-backend --since '-2 min'` | 无 error/traceback | ✓ |
| 内网 API | `POST http://127.0.0.1:9000/api/v1/admin/auth/login`（错密） | HTTP 400（端点可达） | ✓ |
| 内网前端 | `GET http://192.168.31.51:8090/ocap/` | HTTP 200 | ✓ |
| 内网静态 | `GET http://192.168.31.51:8090/ocap/assets/index-Dzhu8-sm.js` | HTTP 200 | ✓ |
| 外网前端 | `GET https://ai-freeark.xin/ocap/` | HTTP 200 | ✓ |
| 外网静态 | `GET https://ai-freeark.xin/ocap/assets/index-Dzhu8-sm.js` | HTTP 200 | ✓ |
| SPA 回退 | `GET https://ai-freeark.xin/ocap/admin/login` | HTTP 200 | ✓ |
| Freeark 首页 | `GET https://ai-freeark.xin/` | HTTP 200 | ✓ |
| Freeark 服务 | `systemctl --state=failed | grep freeark` | 无失败服务 | ✓ |

## 回滚记录

无需回滚。所有步骤成功，验证全通过。

锚点快照保留在 `/home/yangyang/ocap/snapshots/`（`backend-20261108123556.tar.gz`、`web-20261108123556.tar.gz`），nginx 备份在 `/etc/nginx/sites-available/ocap.bak_20261108123556` 与 `freeark.bak_20261108123556`。

## 当前系统状态

- ocap-backend.service：active（gunicorn 26.2.0，4 workers，127.0.0.1:9000）
- ocap nginx：8090 端口，静态 + API 反代正常
- Freeark：未受影响，所有 freeark-* 服务正常
- 数据库：ocap 库，迁移至最新（含 claims/income/ledger 0003）

## 遗留问题

1. **RU-2 定时任务**：测试环境未创建 `ocap-scheduler.timer`，`run_due_jobs` 不会自动执行。建议补齐 systemd timer。
2. **短信/微信真实服务**：测试环境 `SMS_GATEWAY_BACKEND=console`，微信未配置；上线前需补齐 `WECHAT_*` 环境变量。
3. **小程序 RU-4**：本次未部署微信小程序（经微信开发者工具提审发布，不经 systemd）。
4. **前端 chunk 体积**：`index-Dzhu8-sm.js` 1.13MB（gzip 374KB），vite 警告超过 500KB；建议后续 code-splitting，不影响功能。
