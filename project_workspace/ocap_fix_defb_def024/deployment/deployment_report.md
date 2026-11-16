<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-16T22:53:30+08:00</timestamp>
  <project_name>ocap_fix_defb_def024</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_owner_auth_v2/deployment/deployment_plan.md</file><file>project_workspace/ocap_owner_auth_v2/deployment/deployment_report.md</file><file>project_workspace/ocap_fix_defb_def024/phase_status.md</file></input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：测试环境后端增量（DEF-024 / DEF-025 / DEF-B）

## 摘要
- 目标环境：测试（树莓派，外网 SSH 57279 通道）；策略：recreate（单实例 gunicorn，重启约 1 秒）。
- 开始 / 结束：2026-11-16T22:49:22+08:00 / 22:53:13+08:00。
- 部署提交：`1da2bb87ba55f6cb7687edf2312fec1abdbcd619`（与 `git ls-remote origin main` 一致，CI run 43889399997 success）。
- 回滚锚点：`ANCHOR_TS=20261116225010`（目标机 `backend-20261116225010.tar.gz`、`web-20261116225010.tar.gz`、`prehash-20261116225010.sha256`、两份 nginx 备份）；部署前目标机后端 = c32684b（5 个被改文件哈希逐一一致）。
- 步骤（沿用 owner_auth_v2 计划阶段 A 的后端部分与阶段 E）：总 9 / 完成 9 / 失败 0 / 跳过 0（跳过的是计划中的 migrate、前端替换、nginx，属授权范围外，不计入）。
- **最终状态：DEPLOYED_SUCCESSFULLY**

## 授权核对
- 授权来源：本次 invocation 的 `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true`，目标环境「测试」，用户本轮原话「Q1:A, Q2:A」。
- 授权环境名「测试」= 沿用计划（owner_auth_v2 deployment_plan 1.0.0）的目标环境「测试」= 画像 P7 环境名「测试」。
- 计划版本：owner_auth_v2 deployment_plan 1.0.0（phase_status 登记为 legacy_baseline，用户 2026-11-16T22:47:05+08:00 确认沿用，仅阶段 A 后端部分与阶段 E）。
- 授权范围内：后端代码替换 + 重启 + `e2e_` 夹具与远程套件。范围外且未执行：migrate、前端替换、nginx 改动、任何改库（夹具除外）。

## 预检（全部只读，通过）
| 项 | 结果 |
|---|---|
| 待部署提交 | `git cat-file -t` = commit；c32684b 是其祖先；已在远端（ls-remote 一致）；无依赖/前端/小程序/deploy 目录改动、无删除文件、无新增 apps 文件 |
| SSH 指纹 | ED25519 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，known_hosts 与 ssh-keyscan 均与画像 P7 一致；`CONNECT_OK attempt=1` |
| 目标机当前版本（回滚锚点核对） | accounts/claims/committee/polls/resolutions 5 个 views.py 的 sha256 与 c32684b 版本逐一一致 |
| 资源 | /home 可用 16G；可用内存 1508 MB |
| 端口 | 80/8000/8080 为 Freeark，9000/8090 为 ocap |
| 本地状态与备份 | `.env`、`venv`、`var` 均在；上批两份保留备份（ocapdb-registry-20261116134900.sql、underground-20261116134900.jsonl）存在且全程未触碰；`DJANGO_SECRET_KEY` 非空 |
| 迁移 | `showmigrations --plan` 未应用 0；e2e_fixture 命令存在；nginx `-t` 通过；Freeark 8080 返回 200；ocap-backend active；web/ocap 属主 yangyang |
| 夹具基线 | `e2e_fixture status` 全 0；清册 5742 / 7862 / 4301；商铺 107；地下车位 1391；申诉 2；空闲房屋 id 7、8、10 |

## 分步执行
| 步骤 | 命令（摘要） | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| DEPLOY-001 快照 | `bash -s -- "$TS" < d001.sh`：backend 快照（排除 venv/var/.env/__pycache__，M-DE-011）、web 快照、两份 nginx 备份、5 个文件的 prehash | 22:50:10 | 约 1 s | SUCCESS | `ANCHOR_TS=20261116225010`；backend tar 454246 B（sha256 94e6659d…c42c5）、web tar 1253129 B（sha256 773678aa…24cb）；prehash 5 行；`D001_DONE` |
| DEPLOY-003a 打包上传 | 本机 `git archive --format=tar.gz "$C:backend"`；scp 到目标机 /tmp | 22:50:15 | 约 7 s | SUCCESS | 包内 `.env`/`venv`/`var` 条目 0；两端 sha256 一致 `ca63832b…54a2c` |
| DEPLOY-003b 解包 | `tar xzf /tmp/ocap_backend_<C>.tar.gz -C /home/yangyang/ocap/backend` | 22:50:29 | <1 s | SUCCESS | `UNPACK_OK`；`LOCAL_STATE_INTACT`；5 个文件哈希 = git 1da2bb8 版本 |
| DEPLOY-004（替换为门控）`migrate --plan` | `manage.py migrate --plan`（加载 .env） | 22:50:30 | 约 3 s | SUCCESS | `No planned migration operations.`（为空，继续；未执行 migrate） |
| DEPLOY-005 重启 | `sudo systemctl restart ocap-backend && sleep 3 && systemctl is-active` | 22:50:38 | 约 4 s | SUCCESS | `active`；gunicorn 1 master + 4 worker 正常启动，日志无 Traceback |
| 阶段 A 只读冒烟 | `bash -s < smoke.sh`（见验证结果） | 22:50:55 | 约 5 s | SUCCESS | 见下表 |
| 阶段 E-1 夹具 setup（DEPLOY-013） | 同一进程内 `trap cleanup EXIT` 保护；口令本地生成经 stdin 传入；`e2e_fixture setup --units 3 --bulk-users 25 --bulk-resolutions 25` | 22:51:29 | 约 4 s | SUCCESS | `SETUP_EXIT=0`；status：users 35、admins 1、memberships 9、seats 3、resolutions 25、flows 2；`registry_counts` 与基线相同 |
| 阶段 E-2 远程套件（DEPLOY-014） | `OCAP_E2E_BASE_URL=https://ai-freeark.xin/ocap/ python3 -I backend/tests/remote/run_remote.py -v`（口令仅在环境变量中；未设 ALLOW_LOCAL/SLOW） | 22:51:33 | 77.6 s | SUCCESS | `Ran 22 tests in 77.565s`；`OK (skipped=1)`；`RUN_EXIT=0` |
| 阶段 E-3 cleanup（DEPLOY-015，由 trap 保证） | `cleanup`（dry-run）→ `cleanup --execute` → `status`；命令已核对含 `OCAP_E2E_FIXTURE=1` | 22:52:51 | 约 6 s | SUCCESS | `DRY_EXIT=0`、`EXEC_EXIT=0`、`STATUS_EXIT=0`；删除 tokens 13、attachments 4、approval_actions 2、approval_instances 1、claims 1、resolutions 25、appeals 2、resident_applications 3、memberships 11、seats 3、flows 7、users 35、admins 1，均为 `e2e_` 数据；status 全 0 |

收尾：目标机上传的 `/tmp/ocap_backend_<C>.tar.gz` 已删除；本机打包目录已清理；ssh ControlMaster 已关闭。未执行任何回滚。

## 验证结果
### 部署后只读验证
| 检查项 | 实际结果 | 通过 |
|---|---|---|
| ocap-backend 存活 | `active`（部署后与套件结束后各查一次） | 是 |
| 日志无新错误 | 自重启起 `Traceback|ERROR` 计数 0（两次查） | 是 |
| 新路由与鉴权（目标机内、无令牌） | POST /certifications 401；POST /appeals 401；GET /admin/appeals 401；GET /units/options 401；POST /admin/committee/seats 401（DEF-024 路由存在且受鉴权保护） | 是 |
| 登录接口 | 用户密码登录错误凭据 400；管理员登录错误凭据 400 | 是 |
| 迁移 | 未应用 0 | 是 |
| 本次改动文件 | 5 个 views.py 哈希均与 prehash 不同（已替换），且等于 git 1da2bb8 | 是 |
| 内网前端 | 127.0.0.1:8090/ocap/ 200 | 是 |
| 外网 | `https://ai-freeark.xin/ocap/` 200；`/ocap/admin/login` 200；`https://ai-freeark.xin/` 200 | 是 |
| Freeark 未受影响 | 8080 返回 200；`systemctl --state=failed` 0 个；8000 仍为 uvicorn（Freeark） | 是 |
| 端口归属 | 9000 gunicorn（ocap）；8000 uvicorn；8080、8090 nginx | 是 |
| 本地状态保留 | `.env`、`venv`、`var` 在；上批两份保留备份仍在（权限未变） | 是 |

### 远程套件（TC-E2E-320 ~ 341，共 22 条）
total = pass + fail + skip：22 = 21 + 0 + 1；通过率 21/21 = 100%。
| 用例 | 结果 | 说明 |
|---|---|---|
| TC-E2E-321、324（DEF-B） | **PASS（由失败变为通过）** | "户主"期望已同步为"产权业主"，部署后实跑通过 |
| 其余 19 条（320、322、323、325~331、333~341 中除 332） | PASS | 与上次一致 |
| TC-E2E-332 | SKIP | 设计内：31 分钟慢用例，需 `OCAP_E2E_SLOW=1`，本轮不启用 |

结果对比上次（owner_auth_v2 阶段 E：19 通过 / 2 失败 / 1 跳过）：2 条 DEF-B 转为通过，其余不变，无新增失败。

### 清理后核对（只读）
| 检查项 | 实际 | 通过 |
|---|---|---|
| e2e 各项计数 | users/admins/flows/memberships/seats/appeals/resident_applications/claims/resolutions/approval_instances/attachments/tokens 等全 0 | 是 |
| 清册 | RegistryUnit 5742 / RegistryOwner 7862 / RegistryPhone 4301（= 基线） | 是 |
| 商铺 / 地下车位 | 107 / 1391 | 是 |
| 申诉总数 | 2（= 基线，非 `e2e_` 数据未变） | 是 |

## 回滚记录
未触发回滚。如需回滚（尚未执行）：叠加解包 `backend-20261116225010.tar.gz`（`--exclude=backend/.env --exclude=backend/venv --exclude=backend/var`）后核对 `prehash-20261116225010.sha256` 全部 OK，再重启 ocap-backend；本次无新增文件、无迁移。

## 偏差与说明
1. DEPLOY-001 的 backend 快照按 M-DE-011 排除 venv/var/.env（计划原文为整目录打包），既减小体积也使"叠加解包回滚"不会触碰本地状态；快照内容仅源码与测试文件。
2. 计划 DEPLOY-004 在本次替换为只读 `migrate --plan` 门控（授权范围明确不 migrate），结果为空，满足继续条件。
3. 补证 DEF-024：按指令未发 `term_start=2026-02-30` 写请求（护栏 `WRITE_ALLOWLIST` 对 `/admin/committee/seats` 仅为 `e2e_` 夹具负例；且用户要求跳过写请求），仅以目标机内无令牌 401 确认路由存在。DEF-024/025 的 400 行为由本地集成测试 TC-INT-720/721、730~739 覆盖；目标机上的 400 返回未经 HTTP 实测。
4. 计数脚本中"有效绑定数"查询因字段名不符报 FieldError（只读，无副作用），本次用申诉总数 2 与清册三项、商铺、地下车位核对基线；有效绑定数未复核。
5. 夹具 setup 的输出含账号编号与脱敏手机号，未写入本报告；报告不含姓名、手机号、口令。

## 当前系统状态
目标机后端 = 提交 1da2bb8（5 个 views.py 已更新），前端仍为 owner_auth_v2 阶段 A 构建；residency 0003 及此前迁移已应用，无新迁移；e2e_ 数据已清空；清册与非 `e2e_` 数据未变；`ocap-backend` active；Freeark 与 nginx 未改动。

## 遗留问题
1. DEF-024/025 的 400 响应未在目标机经 HTTP 实测（见偏差 3），本地测试已覆盖。
2. TC-E2E-332 慢用例未跑（设计内）。
3. 认证姓名核对 422 的目标机补证仍受护栏限制（`POST /certifications` 不在 WRITE_ALLOWLIST，owner_auth_v2 遗留问题，未改变）。
4. 回滚快照与 nginx 备份保留 ≥ 7 天；用户要求保留到 2026-11-23 的上批两份备份未被触碰。
