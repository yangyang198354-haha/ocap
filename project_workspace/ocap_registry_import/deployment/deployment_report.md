<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-11T01:01:31+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>2.0.0</version>
  <input_files><file>deployment/deployment_plan.md</file><file>deployment/cicd_pipeline.md</file><file>project_workspace/ocap_registry_import/phase_status.md</file><file>.trae/skills/ocap-deploy/SKILL.md</file><file>.claude/skills/ocap-deploy/SKILL.md</file></input_files>
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

> 1.1.0 修订：在文末新增「R2 执行记录」（增量重部署，提交 a0a0b3a，依据 deployment_plan 2.0.0 R2 节）。以上 1.0.0 正文为首次部署（2026-11-10）的历史记录，原样保留。

## R2 执行记录（提交 a0a0b3a，DEF-007~012）

### R2-摘要

- 目标环境：测试（树莓派，画像 P7 唯一环境）；连接：外网 `ssh -p 57279 yangyang@47.109.197.217`
- 策略：`recreate`；实际停机：`ocap-backend` 重启 01:00:26 起约 1 秒完成 gunicorn 启动
- 开始/结束：2026-11-11 00:55:10 / 01:01:00
- 发布提交：REL=`a0a0b3ac1eab6c73394e5214a13ee216a8127395`（= `origin/main`）
- 回滚锚点：`ANCHOR_TS=20261111005708`（`snapshots/backend-20261111005708.tar.gz` 169,056 B、`web-20261111005708.tar.gz` 472,375 B）；R2 之前的目标机版本 = 567b137（1.0.0 部署）
- 总步骤 4 / 完成 4 / 失败 0 / 跳过 0（预检 12 项另计）；未触发回滚
- **最终状态：DEPLOYED_SUCCESSFULLY**
- 注意：外网 SSH 通道（阿里云 VPS + frp）对短时间内连续新建连接间歇性返回 `Connection closed`（共 4 次：快照前 2 次、scp/解包前 1 次、同一步骤的 scp 1 次）。均发生在对应步骤执行之前，目标机无变更；间隔 20 秒后重试成功。后续步骤均加间隔。

### R2-授权核对

- 授权来源：invocation `ocap_registry_import-GROUP_E2-2` 的 `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true`、`DEPLOY_ENVIRONMENT=测试`；用户本轮原话"提交并推送，授权部署测试环境"（PM 当轮写入，phase_status 2026-11-11T00:51:07 DEPLOY_AUTH）
- 授权环境名「测试」= deployment_plan 2.0.0 R2-3 环境 = 画像 P7 环境名「测试」
- 计划版本 deployment_plan **2.0.0（APPROVED）** = phase_status 登记版本（GR-E1-002，00:54:39）
- 主机指纹：`ssh-keyscan` 得 ED25519 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，与授权值一致，之后 ssh 使用 `StrictHostKeyChecking=yes` 与该已核对密钥的临时 known_hosts
- 仅执行 R2 节，未执行 1.0.0 的 DEPLOY-001~008；未 commit / push；未 cat `.env`；未触碰 Freeark、nginx、VPS frp；未执行 mysqldump

### R2-预检

| ID | 实际结果 | 通过 |
|---|---|---|
| R2-PRE-001 | `git rev-parse HEAD` = `a0a0b3ac1eab6c73394e5214a13ee216a8127395` | 是 |
| R2-PRE-002 | `git ls-remote origin main` = `a0a0b3ac1eab6c73394e5214a13ee216a8127395` | 是 |
| R2-PRE-003 | `git status --porcelain --untracked-files=all -- backend frontend` 无输出 | 是 |
| R2-PRE-004 | 迁移计数 `0`；requirements/deploy/.github 差异无输出；无 `D`（删除）文件 | 是 |
| R2-PRE-005 | PM venv：`makemigrations --check --dry-run --settings=config.test_settings` → `No changes detected`，exit=0 | 是 |
| R2-PRE-006 | 目标机 `showmigrations --plan` 未应用数 `0`；registry 0001~0004 均 `[X]` | 是 |
| R2-PRE-007 | `ExecStart=… --workers 4 --timeout 90 …`；nginx ocap 站点第 6 行 `proxy_read_timeout 90s;` | 是 |
| R2-PRE-008 | `/` 可用 16G（使用 44%）；`free -m` available 1804 MB（部署前） | 是 |
| R2-PRE-009 | 80/8000/8080 属 Freeark（8000=uvicorn）、9000=gunicorn、8090=ocap nginx；8080 → 200；`systemctl --state=failed` 0 个 | 是 |
| R2-PRE-010 | `ENV_OK`、`SNAP_OK` | 是 |
| R2-PRE-011 | `120M /home/yangyang/ocap/backend`（含 venv）；`var/` 目录不存在（du 无输出行）；快照按计划排除 venv/var/.env | 是（已记录） |
| R2-PRE-012 | 部署前 `importing.py` 24786 B、mtime `2026-11-10 22:47`；`web/ocap/index.html` root:root 2026-11-10 23:26；旧资源 `assets/index-BSZh5-7M.js`；`grep -c number_format import_template.py` = 0（旧版） | 是 |

GR-E1-002 条件：部署前只读 `stat -c '%U' /home/yangyang/ocap/web/ocap /home/yangyang/ocap/web/ocap/index.html` → `root` / `root`，故 R2-DEPLOY-003 的 `rm` 与 `tar` 均加 `sudo`。

### R2-分步执行

| 步骤 | 命令（摘要，变量已展开） | 开始 | 结果 | 输出尾部 |
|---|---|---|---|---|
| R2-DEPLOY-001 快照 | `TS=$($OCAP_SSH 'date +%Y%m%d%H%M%S')`；`sudo tar czf …/snapshots/backend-$TS.tar.gz -C /home/yangyang/ocap --exclude=backend/venv --exclude=backend/var --exclude=backend/.env --exclude=__pycache__ backend && sudo tar czf …/web-$TS.tar.gz -C /home/yangyang/ocap web` | 00:57:05 | SUCCESS | `ANCHOR_TS=20261111005708`；`backend-…tar.gz` 169056 B；`web-…tar.gz` 472375 B；`grep -c apps/registry/importing.py` = `1`；rc=0 |
| R2-DEPLOY-002 后端 | `git archive --format=tar.gz -o /tmp/ocap_backend_$TS.tar.gz a0a0b3a:backend`；`sha256sum`；`scp -P 57279 …`；远端 `sha256sum` 后 `tar xzf … -C /home/yangyang/ocap/backend` | 00:57:26（上传 00:57:55，解包 00:58:30） | SUCCESS | 两端 SHA256 = `05c8806638c8a8f839ddc550b5cbecf16a8050e1302425bd4194cf64a05a73d8`；排除检查（.env/venv/var）= `0`；`tar_rc=0`；`ENV_KEPT`；`grep -c number_format` = `2`（新代码） |
| R2-DEPLOY-003 前端 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/`；`tar -czf /tmp/frontend_dist_$TS.tar.gz -C frontend/dist .`；scp；远端 `sudo rm -rf …/web/ocap/* && sudo tar xzf … -C …/web/ocap` | 00:58:37（上传 00:59:28，替换 01:00:04） | SUCCESS | `✓ built in 25.26s`，build_rc=0；两端 SHA256 = `c53e788f11629503c3039e4dc4a0df86aa28b1f0a0172c91e13002417189ca06`；`index.html` 存在（root:root 644，938 B）；引用 `assets/index-B6HXhS2D.js`；assets 32 个文件；vite 大 chunk 警告不影响功能 |
| R2-DEPLOY-004 重启 | `sudo systemctl restart ocap-backend && sleep 3 && systemctl is-active ocap-backend`；`sudo journalctl -u ocap-backend -n 40 --no-pager` | 01:00:23 | SUCCESS | `active`；日志：`Starting gunicorn 26.2.0`、`Listening at: http://127.0.0.1:9000`、`Using worker: sync`、4 个 `Booting worker`；无 Traceback |

本地临时文件：`/tmp/ocap_backend_20261111005708.tar.gz`、`/tmp/frontend_dist_20261111005708.tar.gz`；目标机 `/tmp/` 同名两个文件保留（未清理，随系统 tmp 回收）。

### R2-验证结果

| ID | 检查项 | 实际结果 | 通过 |
|---|---|---|---|
| V-01 | 后端存活 | `active` | 是 |
| V-02 | 近 5 分钟日志 Traceback/OperationalError 计数 | `0` | 是 |
| V-03 | 迁移状态 | registry 0001~0004 全部 `[X]`；未应用条数 `0` | 是 |
| V-04 | 内网前端（目标机本地 `127.0.0.1:8090/ocap/`） | `200` | 是 |
| V-05 | 外网前端 `https://ai-freeark.xin/ocap/` | `200` | 是 |
| V-06 | SPA 回退 `/ocap/admin/login` | `200` | 是 |
| V-07 | `/ocap/api/v1/admin/registry/import/spec` | `401`（路由存在，需认证） | 是 |
| V-08 | `/ocap/api/v1/admin/registry/import/template` | `401`（未认证不返回文件） | 是 |
| V-10 | Freeark 未受影响 | `https://ai-freeark.xin/` → `200`；目标机 `127.0.0.1:8080` → `200`；`systemctl --state=failed` = 0 个单元；8000 仍为 uvicorn，8080/8090 nginx，9000 gunicorn | 是 |
| V-11 | 新静态资源 | 外网页面引用 `assets/index-B6HXhS2D.js`；`GET /ocap/assets/index-B6HXhS2D.js` → `200`；与旧哈希 `index-BSZh5-7M.js` 不同 | 是 |
| V-12 | 代码版本已生效 | `grep -c number_format apps/registry/import_template.py` = `2`（部署前 `0`） | 是 |

部署后内存：`free -m` available 1730 MB（部署前 1804 MB）。

### R2-回滚记录

无（4 个 R2-DEPLOY 全部成功，未触发 R2-ROLLBACK）。回滚锚点保留：`ANCHOR_TS=20261111005708`，核验与命令见 deployment_plan 2.0.0 R2-6（后端用叠加解包，前端 web 目录用 `sudo` 恢复，因 `web/ocap` 属 root）。

### R2-当前系统状态与人工验证采样命令

- 系统：`ocap-backend` active（gunicorn 4 workers，`--timeout 90`）；前端为 a0a0b3a 构建；nginx 未改动未 reload；Freeark 未动。
- 人工项 M-04~M-06（用户在页面导入 20000 行 xlsx）**本次未执行**，由用户操作；PM 只读采样命令（连接选项同上，`$OCAP_SSH` 为 `ssh -p 57279 yangyang@47.109.197.217`）：

```bash
# 采样前基线
$OCAP_SSH 'systemctl show ocap-backend -p MemoryCurrent -p MemoryPeak -p MemoryMax; free -m; ps -eo pid,rss,cmd --sort=-rss | grep "[g]unicorn" | head -6'
# 导入期间每 2 秒采样 gunicorn 各 worker RSS 之和（KB），最长 90 秒，输出峰值
$OCAP_SSH 'peak=0; for i in $(seq 1 45); do s=$(ps -eo rss,cmd | grep "[g]unicorn" | awk "{t+=\$1} END{print t+0}"); [ "$s" -gt "$peak" ] && peak=$s; sleep 2; done; echo PEAK_RSS_KB=$peak'
# 采样后
$OCAP_SSH 'systemctl show ocap-backend -p MemoryCurrent -p MemoryPeak; free -m; sudo journalctl -u ocap-backend --since "-10 min" --no-pager | grep -Ei "Traceback|WORKER TIMEOUT|killed|oom" | tail -5'
```

### R2-遗留问题

1. M-04~M-06（真实 HTTP 20000 行 xlsx 导入、耗时与内存峰值）待用户在页面执行；GR-D-002-F01 与 GR-E2-001-F01 仍然开放，引擎级/SQLite 口径不得外推为目标机 HTTP 端到端达标。
2. 外网 SSH 通道对短时间连续新建连接有间歇性断开（见 R2-摘要），后续 PM 采样脚本建议加连接间隔或使用 `ControlMaster` 复用连接。
3. `web/ocap` 属主为 root（1.0.0 以 sudo 写入）；重新部署前端须继续使用 sudo，否则会产生半删除状态。
4. 目标机 `/tmp` 与 `snapshots/` 保留 R2 产物（快照保留 ≥ 7 天，清理需用户确认）。
5. 部署后 `index.html` 权限由 666 变为 644（解包 umask 所致），nginx 读取正常，无功能影响。
