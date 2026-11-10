<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-10T23:28:26+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files><file>deployment/deployment_plan.md</file><file>deployment/cicd_pipeline.md</file><file>project_workspace/ocap_registry_import/phase_status.md</file><file>.trae/skills/ocap-deploy/SKILL.md</file></input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：业主清册导入增强 → 测试环境

## 摘要

- 目标环境：测试（内网 `192.168.31.51:8090/ocap/`，外网 `https://ai-freeark.xin/ocap/`）
- 策略：`recreate`（单实例，后端 restart 停机约 1 秒，前端静态切换秒级）
- 开始：2026-11-10 23:22（预检）｜部署：23:24:50｜结束：23:28:26
- 回滚锚点：`ANCHOR_TS=20261110232450`（`snapshots/backend-20261110232450.tar.gz` 26 MB、`web-...tar.gz` 458 KB、两份 nginx 备份、`ocap-backend.service.bak_20261110232450`）
- 部署内容：本地 HEAD `567b137`（已推送，`origin/main` 哈希一致）
- 总步骤 8 / 完成 8 / 失败 0 / 跳过 0
- **最终状态：DEPLOYED_SUCCESSFULLY**

## 授权核对

- 授权来源：invocation `ocap_registry_import-GROUP_E2-1` 的 PM `special_instructions`
- 用户原话：上一轮"做部署计划，部署到测试环境"；本轮"A"（选择 A：先提交并推送，再部署）
- `PRODUCTION_DEPLOY_CONFIRM=true`（画像 P7 该环境"部署需用户确认=是"）
- 授权环境名 = 计划环境名 = 画像 P7 环境名：**测试环境（树莓派 192.168.31.51 / ai-freeark.xin）**
- 计划版本：`deployment_plan.md` **1.0.0（APPROVED）** = phase_status 登记版本

## 分步执行

| DEPLOY | 命令摘要 | 开始 | 结果 | 输出摘要 |
|---|---|---|---|---|
| 001 快照 | 目标机 tar 备份 backend/web + nginx + unit | 23:24:50 | SUCCESS | `ANCHOR_TS=20261110232450`；backend 26 MB、web 458 KB、unit 536 B |
| 002 三表备份 | `mysqldump --skip-ssl ... registry_registryunit registry_registryphone` | 23:25:10 | SUCCESS | `DUMP_EXIT=0`，91 行（owner 表迁移前不存在；基线 0 单元 / 0 手机号，无数据风险） |
| 003 参数调整 | `sed --timeout 60→90`；nginx 加 `proxy_read_timeout 90s` | 23:25:25 | SUCCESS | `--timeout 90`；`nginx test successful`；nginx `active` |
| 004 后端上传 | tar 排除 venv/.env/var；scp；校验 SHA256；解包 | 23:25:40 | SUCCESS | 两端 SHA256 = `34f354a7…94fda`；`EXTRACT_OK`；`ENV_KEPT` |
| 005 依赖 | `venv/bin/pip install -r requirements.txt` | 23:26:05 | SUCCESS | `PIP_EXIT=0`；openpyxl **3.1.5** |
| 006 迁移 | `manage.py migrate --noinput` | 23:26:15 | SUCCESS | `registry.0002 OK / 0003 OK / 0004 OK`；showmigrations 四条 `[X]` |
| 007 前端 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`；上传解包 | 23:26:30 | SUCCESS | `✓ built in 7.33s`；dist tar 471,081 B；`index.html` 与 assets 已替换 |
| 008 重启 | `systemctl restart ocap-backend` | 23:27:13 | SUCCESS | `active`；gunicorn 26.2.0，4 workers，无 Traceback |

## 验证结果

| ID | 检查项 | 实际结果 | 通过 |
|---|---|---|---|
| V-01 | 后端存活 | `active` | ✅ |
| V-02 | 近 5 分钟日志 | `Traceback=0`、`OperationalError=0` | ✅ |
| V-03 | 迁移状态 | `0001~0004` 全部 `[X]` | ✅ |
| V-04 | 内网前端 | `http://192.168.31.51:8090/ocap/` → 200 | ✅ |
| V-05 | 外网前端 | `https://ai-freeark.xin/ocap/` → 200 | ✅ |
| V-06 | SPA 回退 | `/ocap/admin/login` → 200 | ✅ |
| V-07 | 新路由 | `/ocap/api/v1/admin/registry/import/spec` → 401（内网/外网均非 404） | ✅ |
| V-08 | xlsx 模板（只读） | `LEN 6419`、`ZIP True`、sheets `['清册导入','填写说明']`（openpyxl 3.1.5） | ✅ |
| V-09 | 20000 行预检抽样（只读，不写库） | 合法：parse 0.15s + plan 1.15s = **1.30s**；含 10% 错误：0.15 + 0.86 = **1.01s**，errors=2000、imported=18000 | ✅（引擎级） |
| V-10 | Freeark 未受影响 | `https://ai-freeark.xin/` → 200；`systemctl --state=failed` 0 个 | ✅ |
| V-11 | 前端静态资源 | `assets/index-BSZh5-7M.js` → 200 | ✅ |

## 回滚记录

无（8 个 DEPLOY 全部成功，未触发 ROLLBACK）。

## 当前系统状态与人工干预建议

- 系统正常：`ocap-backend` active、nginx active、Freeark 服务未动。
- 目标机新增持久变更：`ocap-backend.service` 的 `--timeout 90`、`/etc/nginx/sites-available/ocap` 的 `proxy_read_timeout 90s;`（均有 `20261110232450` 备份，可随 ROLLBACK-003 恢复）。
- 目标机 `/tmp` 保留 `ocap_backend_20261110232450.tar.gz`、`frontend_dist_20261110232450.tar.gz`；快照目录保留 backend/web/nginx/unit 备份 ≥ 7 天。

## 遗留问题

1. V-09 为**引擎级**（`read_rows` + `plan_import`，直接读 MySQL，不写库），未做真实 HTTP 5 MB 上传 + nginx/gunicorn 端到端计时；HTTP 端到端仍建议由用户在页面用真实 20000 行文件验证一次。
2. 迁移 0003 在空库（0 单元 / 0 手机号）上执行，未产生回填数据；生产类数据量的迁移行为未在本次验证。
3. 未执行小程序构建与发布（RU-4，不在本计划范围）。
4. 20000 行性能结果 1.3s 远低于 60 秒，建议把本次测量写入性能 AC 的正式证据（test-engineer 报告回填需其重新执行，PM 已在 GR-D-001 条件中记录）。
