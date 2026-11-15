<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-15T18:45:09+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_product_review/deployment/deployment_plan.md</file>
    <file>project_workspace/ocap_product_review/deployment/cicd_pipeline.md</file>
    <file>project_workspace/ocap_identity_display/deployment/deployment_report.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：产品评审修正（测试环境）

## 摘要

- 目标环境：测试（树莓派 `raspberrypi`，外网 SSH 57279；入口 `https://ai-freeark.xin/ocap/`）
- 策略：recreate（单实例）
- 部署版本：commit `3ffd868e20a12b05ae2d0c0ab550f5ca15e06568`（origin/main，GitHub Actions run 43698549347 三个 job 全绿），用 `git archive` 打包，未从工作区打包
- 开始/结束：2026-11-15 18:33 ~ 18:45（Asia/Shanghai）；服务停机窗口 18:41:24 ~ 18:41:58（约 34 秒，后端）
- 回滚锚点：`ANCHOR_TS=20261115184022`（快照、DB 备份、指纹见 DEPLOY-001）
- 总步骤：计划 DEPLOY-001 ~ 011 共 11；执行 8 / 完成 8 / 失败 0 / 跳过 0；未执行 3（DEPLOY-009 ~ 011，NOT_EXECUTED）
- 未触发回滚
- 最终状态：**DEPLOYED_SUCCESSFULLY**（DEPLOY-001 ~ 008 与 DEPLOY-008 的关键项、非关键项全部有实际输出并通过；V-15、V-16、V-20 ~ V-23 属 DEPLOY-009 ~ 011 范围，未执行）

## 授权核对

- 授权来源：本次 invocation 的 `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true`，授权来源为用户 2026-11-15 本轮消息"确认部署"，由主会话/PM 写入。范围：仅测试环境，仅本次调用有效。
- 授权环境 = 计划环境 = 画像 P7 环境：测试（树莓派，外网 SSH 57279）；画像 P7 无生产环境，未触碰任何其他目标。三者一致。
- 计划版本：deployment_plan.md 1.0.0，文件头 APPROVED；phase_status 登记 GROUP_E1 `status=APPROVED`（PASS_WITH_CONDITIONS），GROUP_D APPROVED。一致。
- UC 结论（来自 invocation）：UC-01 = A 等价，部署 `3ffd868`；UC-02 ~ UC-05 本轮未确认，不执行 DEPLOY-009 ~ 011；UC-06 ~ UC-10 不适用。
- 凭据：数据库口令只经远端 `MYSQL_PWD` 环境变量（由目标机 `.env` 加载），未 cat `.env`，报告与输出中无口令。

## 与计划的差异（必须说明）

1. **版本**：计划基于 `8ba53a8`；本次部署的 `3ffd868` = `8ba53a8` 与 origin（`58558da ~ cdd901f` ocap_identity_display 已于 11-14 单独部署，及 `35ce9f5` 测试修复）的合并，另加纯文档提交。自 `afa1fe8` 到 `3ffd868` 迁移仅有 `residency/0002_closed_status.py`；`backend/requirements.txt`、`frontend/package.json`、`frontend/package-lock.json`、`miniprogram/package.json`、`deploy/` 均无改动（`git diff --name-status afa1fe8 3ffd868` 核实，仅迁移文件一行 `A`）。合并同时改动 `accounts/directory.py`、`residency/housing.py`、`identity/services.py`、`committee/services.py` 与 Web/小程序身份显示（管理端目录与用户端不再显示"户主"）。已按要求把 `apps/accounts/directory.py`、`apps/identity/services.py`、`apps/committee/services.py` 加入 DEPLOY-001 的 sha256 指纹清单。
2. **前端构建基于归档内容**：`git archive 3ffd868` 解到 scratchpad 的独立目录，`node_modules` 软链到仓库的 `frontend/node_modules`，因此未执行 `npm ci`（计划写的是 `npm ci` + build）。构建命令按计划 `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`。
3. **PRE-002 复跑范围**：后端 check、compileall、makemigrations 漂移检查、全量测试，前端 vitest 与构建在本机执行（见预检表）；小程序 vitest 与 `scripts/themes/build.mjs --strict --check` 本次**未在本机复跑**，以 CI run 43698549347 三个 job 全绿作为依据。
4. 本次未执行 DEPLOY-009 ~ 011（见"未执行步骤"）；因此计划中的 V-15、V-16、V-20 ~ V-23 不适用。

## E2-001 状态核对

背景：11-14 的 GROUP_E2-001（commit `8ba53a8`）没有返回也没有报告。全部为只读核对，在任何 DEPLOY 步骤之前完成。

| 核对项 | 命令 | 实际结果 | 结论 |
|---|---|---|---|
| 迁移状态 | `showmigrations residency`（加载 `.env`） | `[X] 0001_initial` 仅此一条；`showmigrations --plan` 未应用条数 0（旧代码不含 0002） | **0002 未应用**，E2-001 未执行迁移 |
| 本批新增文件是否存在于目标机 | `ls apps/core/limits.py apps/residency/housing.py apps/jobs/e2e_fixture.py` | 三者均 `No such file` | 8ba53a8 的代码**未上传/未解包** |
| 目标机代码对应版本 | 对 8 个文件做 sha256，并与 `git show <commit>:backend/<file>` 的哈希比对 | `residency/models.py`、`core/config.py`、`committee/services.py`、`residency/services.py` 哈希与 `58558da` 完全一致；与 `8ba53a8` 0/8 一致。另 4 个文件（`accounts/directory.py`、`accounts/views.py`、`claims/views.py`、`identity/services.py`）整文件哈希不同，剥离 CR 后与 `58558da` 版本逐字节相同（diff 0 行）。原因：目标机上有一批文件为 CRLF 行尾（`apps` 下 181 个 `.py` 中 78 个含 CR，既有状况，源自更早的部署） | 目标机代码 = **`58558da`（identity_display，11-14 19:50 部署）内容**，未叠加 8ba53a8 |
| 快照 | `ls snapshots` | 11-14 有两组：`*-20261114100805`（10:08，backend/web/sql/registry-counts，属前一批）与 `*-20261114194943`（19:49，backend/web，属 identity_display 部署）。**没有** 8ba53a8 对应的新快照（19:49 之后至本次之前无新文件） | E2-001 未走到 DEPLOY-001 之后（或未开始） |
| `web/ocap.old-*` | `ls -d web/ocap.old-*` | 不存在；`web/ocap` 修改于 2026-11-14 19:50，bundle 为 `index-0f6Jay-4.js`（identity_display 构建） | 前端未被 E2-001 替换 |
| 服务状态 | `systemctl is-active` | `ocap-backend` active、`ocap-run-due-jobs.timer` active、`ocap-content-worker` active（单元 enabled） | 无异常 |
| 其他 | `.env`/`venv`/`var` 存在，`DJANGO_SECRET_KEY` 非空；`/home/yangyang/ocap` 下仅 `backend web snapshots` | 正常 | 无半部署状态 |

结论：目标机处于 `58558da` 的干净状态，E2-001 未留下任何半部署残留，无需修复。因此 DEPLOY-005 **正常执行**（0002 此前未应用），并非"已应用，跳过"。

## 预检（PRE）

| 编号 | 检查 | 实际结果 | 通过 |
|---|---|---|---|
| PRE-001 | 待部署版本 | `git cat-file -t 3ffd868…` = `commit`；`git rev-parse HEAD origin/main` 均为 `3ffd868e20a1…`；工作区仅 `project_workspace/ocap_product_review/phase_status.md` 有 PM 未提交改动，与包无关；包由 `git archive` 生成 | 是 |
| PRE-002 | 本地测试与构建复跑（归档目录，Python 3.12 / Django 5.2.19 的 PM venv） | `manage.py check`：`no issues`；`compileall`：0；`makemigrations --check --dry-run`：`No changes detected`；后端全量：`Ran 723 tests … OK (skipped=1)`；前端 vitest：`Tests 248 passed (248)`；前端构建：`✓ built in 1m 8s`。小程序 vitest、主题检查未复跑（见差异 3） | 是（部分以 CI 为据） |
| PRE-003 | 迁移符合 P6 | 首行 `# 手写迁移（画像 P6）…`；`Generated by Django` 计数 0；本批新增迁移仅 `residency/0002_closed_status.py` | 是 |
| PRE-004 | 无依赖变更 | `git diff afa1fe8 3ffd868` 对 requirements/package*/deploy 无输出 | 是 |
| PRE-005 | SSH 指纹与主机 | `ssh-keyscan` 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，与画像一致；主机名 `raspberrypi` | 是 |
| PRE-006 | 资源 | `/home` 可用 16G；内存 total 4049 / available 1486 MB | 是 |
| PRE-007 | 服务与端口基线 | 三个服务 active；监听 80/8000/8080/8090/9000；9000 属 gunicorn（ocap），8000 属 uvicorn（Freeark），8080/8090 为同一 nginx（Freeark 站点与 ocap 站点，既有配置）；Freeark 127.0.0.1:8080 返回 `200`。`WORKER_WAS_ACTIVE=active` | 是 |
| PRE-008 | 本地状态保护 | `ENV_OK`、`VENV_OK`、`VAR_OK`、`SECRET_KEY_SET`；`web/ocap` 属主 `yangyang`（非 root）；`$A` 下仅 `backend web snapshots` | 是 |
| PRE-009 | 迁移现状 | 未应用 0；`residency` 仅 `0001_initial [X]` | 是 |
| PRE-010 | 备份工具 | `mysqldump`、`gzip`、`sha256sum` 均在 `/usr/bin` | 是 |
| PRE-011 | nginx 与 Freeark 基线 | `nginx -t`：`syntax is ok` / `test is successful`；外网 `https://ai-freeark.xin/` 返回 `200` | 是 |
| PRE-012 | 执行端 E2E 依赖 | `requests 2.31.0` 可导入（本次不运行远程 E2E，仅核对） | 是 |
| PRE-013 | UC 确认 | UC-01 已确认；UC-02 ~ 05 未确认，故不执行 DEPLOY-009 ~ 011 | 是（按授权范围） |

## 分步执行

所有命令经 ControlMaster 复用的单个 SSH 连接发出（路径在 `/tmp/ocsE2`，短目录，M-DE-010），期间无断线。时间为 Asia/Shanghai。

| DEPLOY | 命令摘要 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| 001 | 取锚点；指纹；backend/web 快照；mysqldump；清册计数；校验 | 18:40:22 | 约 1 分钟 | SUCCESS | `ANCHOR_TS=20261115184022`；指纹 7 个文件已存于 `snapshots/fingerprint-20261115184022.txt`；backend 快照 299,785 B（排除 venv/var/.env）；web 快照 619,356 B；`DUMP_EXIT=0`，sql.gz 330,360 B，尾行 `-- Dump completed on 2026-11-15 18:40:33`；`REGISTRY_BASE 5742 7862 4301`；快照内新增文件计数 0（grep 五个新文件）；SHA256 见下 |
| 002 | `git archive 3ffd868:backend` 打包；前端构建并打包；scp；两端 SHA256 | 约 18:37（本地打包）/ 18:40（上传） | 数十秒 | SUCCESS | 包内 `venv/var/.env/__pycache__` 计数 0；5 个新文件齐全；前端 bundle `assets/index-CbVinVRe.js`、`index-DwTVKv1n.css`，`/ocap/assets/` 引用计数 2；两端 SHA256 一致（见下） |
| 003 | 先停 `ocap-content-worker`，再停 `ocap-backend` | 18:41:20 | 4 秒 | SUCCESS | 两者 `inactive`；timer 未动 |
| 004 | 解包后端到 `backend/`（叠加，不 rm） | 18:41:3x | 数秒 | SUCCESS | `UNTAR_RC=0`；5 个新文件存在；`LOCAL_STATE_INTACT`；`pip install --dry-run` 全部 `Requirement already satisfied`，无新包；5 个文件的 sha256 与归档目录对应文件逐一一致 |
| 005 | `check`；门控 1、2；`migrate --noinput` | 约 18:41:4x | 数秒 | SUCCESS | `check`：no issues；门控 1 恰一行 `[ ]  residency.0002_closed_status`；门控 2 `sqlmigrate` 全为 `(no-op)`，DDL 计数 `0`；`Applying residency.0002_closed_status... OK`，`MIGRATE_RC=0`；`showmigrations residency`：`[X] 0001_initial`、`[X] 0002_closed_status` |
| 006 | 启动 `ocap-backend`、`ocap-content-worker` | 18:41:58 | 约 6 秒 | SUCCESS | 两者 `active`；gunicorn 26.2.0 监听 127.0.0.1:9000，4 个 worker 启动；日志无 Traceback/ERROR；worker 18:42:01 启动 |
| 007 | 解包前端到 `web/ocap.new`，改名切换，chown | 18:42 | 数秒 | SUCCESS | `FE_RC=0`；`web/ocap/index.html` 1039 B，引用 `index-CbVinVRe.js`（旧为 `index-0f6Jay-4.js`）；`web/ocap.old-20261115184022` 已保留 |
| 008 | 部署后只读验证 V-01 ~ V-14 | 18:42:21 | 约 3 分钟 | SUCCESS | 见"验证结果" |
| 009 | 夹具 setup | — | — | **NOT_EXECUTED** | 原因：UC-02 ~ 05 未经本轮确认 |
| 010 | 远程 HTTP E2E | — | — | **NOT_EXECUTED** | 同上；未设置 `OCAP_E2E_PASSWORD`，未建任何 `e2e_` 夹具，未发出任何 E2E 请求 |
| 011 | 夹具 cleanup 与验收 | — | — | **NOT_EXECUTED** | 同上；DEPLOY-009 未执行，无数据需清理（`status` 显示 e2e 计数全 0） |

DEPLOY-001 备份文件 SHA256（目标机 `/home/yangyang/ocap/snapshots/`）：

| 文件 | SHA256 |
|---|---|
| `backend-20261115184022.tar.gz` | `a4a00ff95af5ea9c3e2a16199497ca5e1309aaebc4a12dc1f6345c57f9209c72` |
| `web-20261115184022.tar.gz` | `1e7db48b3a531dcddda3ca5a0c3169d973f65828d08fd3d7ed1f918862cdcc47` |
| `ocap-20261115184022.sql.gz` | `5f24f02e469752004bed58edd2e0a58a35105ad1c3ef04fc77ba0d7674677e99` |
| `registry-counts-20261115184022.txt` | `376100d4bd06eb72b2a8c8d1fc0bd511c23efdbd5c2fe7e6bcfce06459dc9dd4` |
| `fingerprint-20261115184022.txt`（部署前指纹，含 directory/identity/committee） | `2f2788590265b7ca74d11e826dda9e2d52828a329866d37f7f6d281d52de7665` |

上传包 SHA256（两端一致）：后端 `566dcac01d4db3ce29a037c590f8eace6ebb419b3e72b63ca4189530e0920c75`；前端 `ae1e0bf98c12adedc7b3e545759393c4c5831fd58584656698b417ca0e56c398`。

部署前指纹（回滚核验基准，前 20 位）：`residency/models.py 566022fbb164…`、`core/config.py 52acdbe77b53…`、`accounts/views.py 7eb519244362…`、`claims/views.py 6e1072edcd18…`、`accounts/directory.py 4d27e838bac4…`、`identity/services.py 3e87c9432bd5…`、`committee/services.py 9411560c54d4…`（完整值在目标机指纹文件中）。注意其中部分为 CRLF 行尾，叠加回滚后可原样还原。

## 验证结果（DEPLOY-008）

| 检查项 | 实际结果 | 级别 | 通过 |
|---|---|---|---|
| V-01 后端存活 | `active` | 关键 | 是 |
| V-02 worker 与 timer | `ocap-content-worker active`、`ocap-run-due-jobs.timer active`；timer 触发的一次性任务 18:44:02 `Finished`（部署后自动补跑正常） | 非关键 | 是 |
| V-03 日志无新错误 | 自 18:41:58 起 `grep -Ec 'Traceback\|ERROR'` = `0`（worker 同为 `0`；18:45 复查仍为 0） | 关键 | 是 |
| V-04 迁移状态 | 未应用数 `0`；`residency` `[X] 0001`、`[X] 0002` | 关键 | 是 |
| V-05 清册计数不变 | `REGISTRY_BASE 5742 7862 4301` → `REGISTRY_NOW 5742 7862 4301` | 关键 | 是 |
| V-06 新路由未登录 401 | 外网 `…/me/housing` 401、`…/system/limits` 401、`…/me` 401 | 关键 | 是 |
| V-07 登录接口 | 错误凭据：`400 {"code":"LOGIN_FAILED"…}`；非法 `client`：`400 {"code":"INVALID_VALUE","message":"client 不合法"}` | 关键 | 是 |
| V-08 管理端登录接口 | `POST …/admin/auth/login`（错误口令）= `400` | 非关键 | 是 |
| V-09 外网前端首页 | `200` | 关键 | 是 |
| V-10 前端静态与 bundle | 外网 `index.html` 引用 `index-CbVinVRe.js`/`index-DwTVKv1n.css`；外网 asset `200` 1,144,008 B；内网（从目标机访问 `192.168.31.51:8090`）index `200 text/html`、asset `200` 1,144,008 B；bundle 名与 DEPLOY-002 记录一致 | 关键 | 是 |
| V-11 SPA 回退与新页 | `/ocap/admin/login` `200 text/html`；`/ocap/admin/content/styles` `200 text/html` | 非关键 | 是 |
| V-12 Freeark 未受影响 | 外网 `https://ai-freeark.xin/` `200`；目标机 `127.0.0.1:8080` `200` | 关键 | 是 |
| V-13 失败单元与端口归属 | `systemctl --state=failed`：`0 loaded units listed`；9000 gunicorn（ocap）、8000 uvicorn（Freeark）、8080/8090 同属 nginx（既有共用实例，8080=Freeark 站点、8090=ocap 站点） | 关键 | 是 |
| V-14 夹具命令可用且无 e2e 数据 | `e2e_fixture status` 退出 0：`e2e` 全部计数 0；`registry_counts` 5742/7862/4301；`claim_amount_max = "1000000.00"` | 关键 | 是 |
| V-15 夹具选房前置 | 未执行（属 DEPLOY-009 范围，UC-02 未确认） | — | NOT_EXECUTED |
| V-16 窗口内无进行中半数决议 | 未执行（UC-03 未确认） | — | NOT_EXECUTED |
| V-20 ~ V-22 远程 E2E / 清理验收 / 期间异常 | 未执行（DEPLOY-010、011 未执行） | — | NOT_EXECUTED |
| V-23 人工验证 H-1 ~ H-9 | 不由 E2 执行；留给用户 | — | NOT_EXECUTED |

补充：目标机本次 `migrate` 输出无"content 漂移"提示（11-14 部署报告曾提到该提示；本次未出现，未做进一步排查）。前端 bundle 中仍有"户主"字样的 chunk 为 `AdminMemberships`、`Units`、`labels`、`confirm`（成员关系管理/房屋角色等语境，非目录显示），属预期，未做功能性复核。

## 回滚记录

未触发回滚。DEPLOY-001 ~ 008 全部成功。回滚锚点 `20261115184022` 与全部回滚材料（backend/web 快照、`ocap-20261115184022.sql.gz`、`registry-counts`、`fingerprint`、`web/ocap.old-20261115184022`）均在目标机。回滚需按计划 ROLLBACK-008 起逆序，并在 ROLLBACK-004 恢复旧代码**之前**执行 ROLLBACK-005（`migrate residency 0001`）；执行前核验 `TS` 与快照文件。

## 未执行步骤

| 步骤 | 状态 | 原因 |
|---|---|---|
| DEPLOY-009 夹具 setup | NOT_EXECUTED | UC-02 ~ 05 未经本轮确认 |
| DEPLOY-010 远程 HTTP E2E | NOT_EXECUTED | UC-02 ~ 05 未经本轮确认 |
| DEPLOY-011 夹具 cleanup | NOT_EXECUTED | 依赖 DEPLOY-009；未建 e2e 数据，`status` 全 0 |
| 小程序构建/发布 | 不在范围 | UC-08 人工 |

## 当前系统状态与人工干预建议

后端、定时任务、内容 worker、Web 前端均在 `3ffd868` 对应版本运行；迁移 `residency.0002_closed_status` 已应用；清册计数未变；Freeark 未受影响。无需人工干预。

## 遗留问题

- 远程 HTTP E2E（22 条，TC-E2E-320 ~ 341）仍未执行：待用户确认 UC-02 ~ 05 后另行授权，由 DEPLOY-009 ~ 011 执行。此前 GR-D-003 已把这 22 条标 BLOCKED，本次部署后其前置条件（V-14 夹具命令可用、无 e2e 数据）已满足。
- 小程序包未构建/发布（UC-08，人工；`uni build` 未验证，GR-C-001-F02）。
- 目标机 `apps` 下约 78 个 `.py` 为 CRLF 行尾（既有）；本次叠加解包只覆盖本包内文件，其余保持原样。功能不受影响，建议下次评估是否统一。
- 快照与备份保留 ≥ 7 天后再人工清理：`web/ocap.old-20261115184022`、`snapshots/*-20261115184022.*`。
- 本次未复跑小程序 vitest 与主题检查（以 CI 为据）。
- 本次 `3ffd868` 部署后，建议用户提交 `phase_status.md` 与本报告（子代理不执行 commit/push，画像 P9）。
