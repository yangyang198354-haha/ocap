<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-16T14:09:00+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>4.0.0</version>
  <input_files>
    <file>deployment/deployment_plan.md</file>
    <file>deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：阶段 A（代码部署）

## 摘要

- 目标环境：测试（树莓派，外网 `ssh -p 57279 yangyang@47.109.197.217`）。策略：recreate（后端重启约 1 秒，前端静态目录替换）。
- 部署提交：`15ea79ea51c87d56cd1cd8113cba81007649575a`（已在 origin/main，`git ls-remote` 一致）。
- 开始 / 结束：2026-11-16T13:04 起，DEPLOY-001 开始 13:05:02，DEPLOY-004 完成 13:06:46，验证完成 13:07。
- 回滚锚点：`ANCHOR_TS=20261116130503`
  - 快照 `/home/yangyang/ocap/snapshots/backend-20261116130503.tar.gz`，SHA256 `f84dbfdf164e26a3956acdc3898fe42c9325f142693b5eedc52dd255a893619b`（28563027 字节）
  - 快照 `/home/yangyang/ocap/snapshots/web-20261116130503.tar.gz`，SHA256 `7e6a3160d536c1e834bef7260a8ba5c4ee33ea9c9d03bbde3ef457971b9e977d`（1250011 字节）
  - nginx 备份 `/etc/nginx/sites-available/ocap.bak_20261116130503`、`/etc/nginx/sites-available/freeark.bak_20261116130503`（本批未改 nginx）
- 制品 SHA256：后端包（`git archive 15ea79e:backend`）`fa05de5b1da4a1e9089eb8e09fb62f0d2c1d5608a9b40e229813dc45ae1910c3`，前端包 `27822faaf95c1ed8dc93dbe4a6f878d93c22febb318cacf2d3cd27fcad1cb496`，两端比对一致。
- 总步骤 4（DEPLOY-001~004）/ 完成 4 / 失败 0 / 跳过 0；阶段 B、C、D、E 未授权，未执行。
- **最终状态：DEPLOYED_SUCCESSFULLY（仅阶段 A）**

## 授权核对

- 授权来源：本次 invocation 的 `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true`，目标环境「测试」，范围仅阶段 A；用户原话"授权推送和部署 Q1：A， Q2：A"（phase_status DEPLOY_AUTH 事件 2026-11-16T13:01:51）。
- 授权环境名「测试」= deployment_plan 目标环境「测试」= 画像 P7 环境名「测试」。
- deployment_plan 版本 1.0.0 = phase_status 登记的 APPROVED 版本；cicd_pipeline 1.0.0 同。
- SSH 主机指纹：本机 known_hosts 中 `[47.109.197.217]:57279` 的 ED25519 为 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，与画像 P7 一致。
- 边界：未运行 `relocate_underground_parking` 的任何模式、未 mysqldump、未导出、未建 `e2e_` 夹具、未跑远程 E2E、未 migrate、未 pip install、未改 nginx 与 Freeark。

## 预检结果

| 检查项 | 结果 | 通过 |
|---|---|---|
| PRE-A01 提交类型与祖先 | `commit`；`ANCESTOR_OK`；HEAD = origin/main = 15ea79e | 是 |
| PRE-A02 前端与提交一致 | `SAME`；`git status --short -- frontend backend miniprogram deploy` 无输出 | 是 |
| PRE-A03 迁移无漂移 | Django 5.2.19，`No changes detected`，退出码 0 | 是 |
| PRE-A04 requirements 未变 | `REQ_SAME`（对比 3ffd868，即 ocap_product_review 最近一次部署提交） | 是 |
| PRE-A05 目标机可达与指纹 | `OK`；指纹一致。前 3 次建连被 `Connection closed`，第 4 次成功（M-DE-009 已知间歇，仅对建连重试） | 是 |
| PRE-A06 磁盘/内存 | `/` 可用 16G；内存可用 1441 MB | 是 |
| PRE-A07 端口归属 | 80/8000/8080 为 Freeark，9000/8090 为 ocap | 是 |
| PRE-A08 目录与本地状态 | `backend/ web/ snapshots/`；`ENV_OK`、`VENV_OK`、`VAR_OK` | 是 |
| PRE-A09 SECRET_KEY | `SECRET_KEY_SET`（未打印值） | 是 |
| PRE-A10 未应用迁移 | `UNAPPLIED=0` | 是 |
| PRE-A11 web/ocap 属主 | `yangyang`（非 root，与计划预期的"可能为 root"不同，sudo 仍可用） | 是 |
| PRE-A12 nginx 与 Freeark | `syntax is ok` / `test is successful`；Freeark 8080 返回 200 | 是 |
| PRE-A13 当前版本记录 | 见下方旧版哈希；三个新文件均 `No such file`（证明为新增） | 是 |
| PRE-A14 e2e_fixture | `jobs/e2e_fixture.py` 存在 | 是 |

PRE-A13 旧版 SHA256（回滚后须一致，相对 `backend/apps/`）：

| 文件 | SHA256 |
|---|---|
| registry/services.py | 294c3cdfe78e5e15873429779106707b76d00ce38faa32d553efa17a5e97fd40 |
| registry/views.py | ebd764799f25308c9bdfe4ba82f8169e47ee64c013752bdaedd5b66244998427 |
| registry/urls.py | 9cfe7359bbf0bf9e09e394bcdfa1a19db825736b6381640164b37aad6a8bf87e |
| identity/services.py | f80c0e2c078825ebe8aa98c07c285540389227d63c3250b62656ae03e0829841 |
| residency/housing.py | 1b4623b82169228abb8c66baba626b6e5e6b7412414fb4f4ecf248591f756476 |
| registry/import_template.py | 0abda941923b7d4dd572e84eab9e9ca9d3b58b350a9bf31114936a325f701175 |

## 分步执行

| DEPLOY | 命令 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| DEPLOY-001 | 本地取 `TS` 后单条双引号远端命令：sudo tar 快照 backend、web；cp 两份 nginx 备份；ls、sha256sum | 13:05:02 | 5.3 s | SUCCESS | `ANCHOR_TS=20261116130503`；2 份 tar（28563027 / 1250011 字节）+ 2 份 nginx 备份（883 / 3318 字节）均存在；SHA256 见摘要 |
| DEPLOY-002 | `git archive --format=tar.gz 15ea79e:backend` → scp 到 `/tmp/` → 远端 `sha256sum` 比对 → `tar xzf … -C /home/yangyang/ocap/backend` | 13:05:15 | 约 15 s | SUCCESS | 两端 SHA256 均为 `fa05de5b…10c3`；解包退出码 0；5 个新增文件存在；`filter-options` 在 urls.py 中计数 1；`LOCAL_STATE_INTACT`（.env、venv、var 均在）；`git show --diff-filter=D` 无删除文件 |
| DEPLOY-003 | `sudo systemctl restart ocap-backend && sleep 3 && systemctl is-active ocap-backend`；`journalctl -n 30` | 13:05:31 | 约 4 s | SUCCESS | `active`；新主进程 1177899 启动，4 个 worker 就绪，监听 127.0.0.1:9000；日志尾部无 Traceback/ERROR |
| DEPLOY-004 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/`（构建前后 `git status -- frontend` 干净）→ tar → scp → 远端 SHA256 比对 → `sudo rm -rf web/ocap/* && sudo tar xzf … && sudo chown -R yangyang:yangyang` | 13:05:38 | 构建 41.7 s，替换 1 s | SUCCESS | 构建退出码 0（仅 vite 大 chunk 警告）；两端 SHA256 `27822faa…b496` 一致；`index.html` 与 `assets/` 存在；入口 js 为 `index-W5V17xyS.js` |

收尾：删除了目标机 `/tmp` 下本次上传的两个包与 `/tmp/mig_before.txt`；本机临时目录已清除。`/tmp/frontend_dist_20261110232450.tar.gz` 是更早批次的遗留，未触碰。

## 验证结果

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| 后端存活 | `active` | 是 |
| 后端日志（近 5 分钟） | `Traceback|ERROR` 命中 0 行 | 是 |
| 新路由存在且鉴权 `GET /api/v1/admin/registry/units/filter-options`（目标机 127.0.0.1:9000，无令牌） | 401（非 404，新代码已生效） | 是 |
| 选房接口鉴权 `GET /api/v1/units/options`（无令牌） | 401 | 是 |
| 登录接口可用（错误凭据，`nobody_20261116130503`） | 400 | 是 |
| 无未应用迁移 | `0` | 是 |
| 内网前端 `http://192.168.31.51:8090/ocap/`（目标机 curl） | 200 `text/html`（127.0.0.1:8090 同） | 是 |
| 内网静态 `/ocap/assets/index-W5V17xyS.js` | 200，1144081 字节 | 是 |
| 外网前端 `https://ai-freeark.xin/ocap/` | 200 `text/html` | 是 |
| 外网静态 `https://ai-freeark.xin/ocap/assets/index-W5V17xyS.js` | 200 `application/javascript` | 是 |
| SPA 回退 `https://ai-freeark.xin/ocap/admin/login` | 200 `text/html` | 是 |
| 新前端已替换 | 外网 index.html 引用 `index-W5V17xyS.js` = 本地 `frontend/dist/index.html` 引用 | 是 |
| Freeark 未受影响 | `https://ai-freeark.xin/` 200；目标机 8080 返回 200；`systemctl --state=failed` 无输出（无 freeark-*、ocap-* 失败单元） | 是 |
| 端口归属 | 9000 gunicorn（ocap）、8000 uvicorn（Freeark）；8080/8090 为 nginx（无 sudo 时 ss 不显示进程名，监听存在） | 是 |
| 命令未被自动执行 | `underground-*.jsonl`、`export_*.xlsx` 均 `No such file` | 是 |

## 回滚记录

无。所有步骤成功，未触发回滚。

## 当前系统状态与人工干预建议

- 目标机运行 15ea79e 的后端代码与对应前端构建；数据库未改动（无迁移，未执行 relocate/export）。
- 此刻库内地下车位记录仍在原楼栋（1 栋下负层），选房第一级"地下车位"尚不会出现，要等阶段 C。MV-05 需在阶段 C 之后验证。
- 若需回滚阶段 A：使用锚点 `20261116130503`，按 deployment_plan 的 ROLLBACK-004（前端）、ROLLBACK-002（叠加解包后端并删除 5 个新增文件，之后核对上方旧版哈希）、ROLLBACK-003（重启）执行。

## 遗留问题

1. 阶段 B（dry-run）、C（apply，改库）、D（导出）、E（夹具与远程 E2E）尚未授权。按 GR-D-001 条件，顺序应为 B → C → D。
2. 人工清单 MV-04（后台"业主清册"下拉与空状态为中文）可在现在由用户用浏览器验证；MV-05 在阶段 C 后；MV-03 按计划未主动制造并发。
3. `[INFERRED]` 偏差：计划预期 `web/ocap` 可能属 root，实际属 yangyang；不影响结果，ROLLBACK-004 仍使用 sudo。
4. 外网 SSH 建连对连续新连接有间歇断开（本次 3 次失败后成功），与 M-DE-009 一致，后续阶段继续用 ControlMaster。
5. 阶段 A 前遗留：E1 阶段在本机 `/` 下留下的两个空归档（`/ocap_backend_15ea79e….tar.gz`、`/frontend_dist.tar.gz`）仍在，本次未删除（不在 E2 授权范围，由用户处理）。

---

# 部署报告：阶段 B（relocate_underground_parking dry-run，只读）

> 版本 1.1.0 追加。阶段 A 各节内容未改动。

## 摘要（阶段 B）

- 目标环境：测试（外网 `ssh -p 57279`，ControlMaster 复用，本机套接字目录 `/tmp/ocs.U41S`，用后已关闭并删除）。策略：不适用（只读，无变更、无停机）。
- 开始 / 结束：2026-11-16T13:35 起（建连重试至成功），预检 13:38:56，DEPLOY-005 13:39:03，完成 13:39:12。
- 回滚锚点：无新增（本阶段不改目标机）。阶段 A 锚点 `ANCHOR_TS=20261116130503` 仍有效。
- 步骤：预检 PRE-B01、PRE-B02、备份文件不存在核对；DEPLOY-005 执行 2 次（第 2 次仅 `--list-limit 1`，核对结果稳定）。失败 0。
- **最终状态：DEPLOYED_SUCCESSFULLY（阶段 B，只读，库与目标机无变更）**。但结果含需用户决策的点，见"汇报要点"。

## 授权核对（阶段 B）

- 授权来源：本次 invocation 的 `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true`，目标环境「测试」，范围仅阶段 B，用户原话"授权 B 段"。
- 授权环境名「测试」= deployment_plan 目标环境「测试」= 画像 P7 环境名「测试」。deployment_plan 版本 1.0.0 = phase_status 登记的 APPROVED 版本。
- 主机指纹：本机 known_hosts 中 `[47.109.197.217]:57279` 的 ED25519 为 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，与画像 P7 一致。
- 边界：未使用 `--apply`、`--restore`、`--backup`；未 mysqldump；未执行 export_registry_import_file；未建 `e2e_` 夹具；未跑远程 E2E；未写库、未改代码、未在目标机写任何文件（`.env` 仅被 shell 加载，未打印）。本机未向 `/` 写文件。

## 预检结果（阶段 B）

| 检查项 | 结果 | 通过 |
|---|---|---|
| 目标机建连 | 连续 5 次 `Connection closed`，第 6 次尝试成功（M-DE-009 已知间歇，只对建连重试，此时尚未执行任何目标机命令） | 是 |
| PRE-B01 阶段 A 已完成 | `apps/registry/exporting.py`、`apps/registry/underground.py` 存在；`ocap-backend` 为 `active` | 是 |
| PRE-B02 命令可加载 | `relocate_underground_parking --help` 与 `export_registry_import_file --help` 均退出 0，输出 `CMD_OK`（仅 `--help`，未执行导出） | 是 |
| 目标机无遗留备份 | `snapshots/` 下 `underground-*` 个数 0（命令未被自动执行，dry-run 后同样为 0） | 是 |

## 分步执行（阶段 B）

| DEPLOY | 命令 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| DEPLOY-005 | `cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_underground_parking --list-limit 200; echo "EXIT=$?"`（无 `--apply`） | 13:39:03 | 约 2 s | SUCCESS | `EXIT=0`；共 211 行输出，其中 200 行 `move|…` 明细（受 `--list-limit 200` 限制，实际应有 1391 条，见下） |
| DEPLOY-005（复核） | 同命令，`--list-limit 1` | 约 13:39:10 | 约 2 s | SUCCESS | `EXIT=0`；汇总计数与第一次完全相同（total_units=5742 等），证明只读、结果稳定 |

命令汇总输出（原样，不含姓名与手机号）：

```
total_units=5742
candidates=1391
already_target=0
would_change=1391
conflicts=0
negative_floor_non_parking=1
other_building_negative_parking=0
old_building|1栋|1391
floor|负1|1119|recognized
floor|负2|272|recognized
EXIT=0
```

## 结果解读（用户要求的汇报项）

| 项 | 实际值 |
|---|---|
| 清册专有部分总数 `total_units` | 5742 |
| 被识别为"地下车位待迁移"的候选 `candidates` | 1391 |
| 已在目标楼栋 `already_target` | 0（目标楼栋"地下车位"目前尚无记录） |
| **would-change 数 N** | **1391** |
| 冲突数 `conflicts` | **0**（无标识冲突、无四元组冲突，故无冲突清单） |
| 楼层写法清单 | `负1` 1119 条（recognized）；`负2` 272 条（recognized）；合计 1391 = candidates |
| unrecognized 写法 | 无（未出现 unrecognized 行） |
| 含 `-` 的写法（GR-D-001-F02：`-1`/`-2`） | **未出现**。实际写法为中文"负1/负2"，F02 条件不触发 |
| 待改记录所在楼栋的实际取值 | `1栋`（带"栋"字，不是裸 `1`），1391 条全部如此（`old_building|1栋|1391`） |
| 其他楼栋是否也有被识别记录 | 否。`other_building_negative_parking=0`；`old_building` 清单只有 `1栋` 一项 |
| `negative_floor_non_parking` | **1**：有 1 条负层但类型不是 PARKING 的记录，命令不会改它。命令只输出计数，不输出 id（未另行查库，也不在授权范围内）。需用户确认其不属于修正范围 |

`move` 明细样例（仅 unit id 与专有部分标识；输出共 200 行，受 `--list-limit` 限制）：

- `move|9|1栋负2层484号|地下车位负2层484号`
- `move|13|1栋负1层577号|地下车位负1层577号`
- `move|19|1栋负1层707号|地下车位负1层707号`
- 末条 `move|1003|1栋负1层90号|地下车位负1层90号`

核对：所有展示的 `move` 旧标识均为"1栋负N层…号"，新标识为"地下车位负N层…号"，格式与 `build_specific_part` 的规则一致。1391 条中其余 1191 条未在输出中展开（需要 `--list-limit 1391` 再跑一次，仍是只读，若用户需要全量明细请另行指示）。

## 汇报要点（供 PM / 用户决策，未自行处理）

1. 进入阶段 C 的条件满足：`conflicts=0`、无 unrecognized、无含 `-` 的写法、`other_building_negative_parking=0`。
2. 阶段 C 的 `--expect-changes` 取值应为 **N = 1391**（本次 dry-run 的 `would_change`）。
3. 需用户确认的一点：`negative_floor_non_parking=1`（1 条负层但非车位的记录不会被修改）。
4. 提示：本次 apply 将一次改动 1391 条记录的楼栋与专有部分标识，属较大批量；计划中的 DEPLOY-006（mysqldump，`--skip-ssl`）与 PRE-C01~C03 仍须在阶段 C 开始时执行。预估事务耗时 [INFERRED] 在数秒量级，实际未测。
5. 说明：dry-run 只验证了识别与冲突预演，MV-03（MySQL 并发）仍按计划未主动制造。

## 回滚记录（阶段 B）

无。DEPLOY-005 对应 ROLLBACK-005 为无操作（只读），不涉及。

## 当前系统状态（阶段 B 结束）

- 目标机运行阶段 A 部署的 15ea79e；数据库未改动；`snapshots/` 下无 `underground-*.jsonl`、无 `export_*.xlsx`。
- 本机：SSH 控制连接已关闭，临时目录 `/tmp/ocs.U41S` 已删除（其中的 dry-run 输出文件无个人信息，随目录一并删除）。

## 遗留问题（阶段 B）

1. 阶段 C（apply，改库）、D（导出）、E（夹具与远程 E2E）仍未授权。C 需用户基于上表确认 N=1391 并另行授权。
2. 外网 SSH 建连间歇断开再次出现（本次连续 5 次失败后成功），与 M-DE-009 一致。
3. 阶段 A 遗留的本机 `/` 下两个空归档文件仍未处理（不在授权范围）。

---

# 部署报告：阶段 C（地下车位归属修正，改库）

> 版本 2.1.0 追加（DRAFT）。阶段 A、B 内容未改动。

## 摘要（阶段 C）

- 目标环境：测试（外网 `ssh -p 57279`，ControlMaster 复用，套接字目录 `/tmp/ocs.MKXi`，结束后已关闭并删除；建连第 1、2 次 `Connection closed`，第 3 次成功，仅对建连重试）。策略：不适用于单次库内事务（服务不重启，无停机）。
- 开始 / 结束：2026-11-16T13:46 起，预检 13:48:45，DEPLOY-006 13:49:01~13:49:05，DEPLOY-007 13:49:10~13:49:19，验证完成约 13:49:40。
- 回滚锚点：数据锚点 `DATA_TS=20261116134900`（库表 mysqldump + 备份 JSONL）；阶段 A 代码锚点 `ANCHOR_TS=20261116130503` 仍有效。
- 步骤：PRE-C01~C03 与 apply 前 dry-run 复核，DEPLOY-006、DEPLOY-007。总 2 / 完成 2 / 失败 0 / 跳过 0。
- **最终状态：DEPLOYED_SUCCESSFULLY（阶段 C）**。库内 1391 条地下车位已改楼栋为"地下车位"，D、E 阶段未执行。

## 授权核对（阶段 C）

- 授权来源：本次 invocation 的 `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true`，目标环境「测试」，范围仅阶段 C（PRE-C01~C03、DEPLOY-006、DEPLOY-007，N=1391）；用户原话"4347 选 A；授权 C 段，N=1391"。
- 授权环境名「测试」= deployment_plan 目标环境「测试」= 画像 P7 环境名「测试」。deployment_plan 版本 1.0.0 = phase_status 登记的 APPROVED 版本。
- 主机指纹：本机 known_hosts 中 `[47.109.197.217]:57279` 的 ED25519 为 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，与画像 P7 一致。
- 授权口径：REWORK_AUTHORIZED 仅限本文件追加阶段 C 一节并升 2.1.0 / DRAFT，A、B 内容未改。
- 边界：未执行导出（阶段 D）、未建 `e2e_` 夹具、未跑远程 E2E（阶段 E）、未改代码、未 migrate、未碰 Freeark 库或服务、未重启任何服务。mysqldump 文件与备份 JSONL 内容未被读取或输出，仅记录路径、大小、SHA256。

## 预检结果（阶段 C）

| 检查项 | 结果 | 通过 |
|---|---|---|
| PRE-C01 mysqldump 可用 | `/usr/bin/mysqldump` | 是 |
| PRE-C02 表名核对 | `registry_registryunit`、`registry_registryowner`、`registry_registryphone`、`residency_membership`（与计划预期一致，[INFERRED] 已实测确认） | 是 |
| PRE-C03 空间与路径 | `/` 可用 16G（45% 已用）；`snapshots/` 下无 `underground-*`（`No such file`） | 是 |
| PRE-C04 N 与 dry-run 一致 | apply 前再跑 dry-run：`would_change=1391`、`conflicts=0`，与用户确认的 N=1391 相同（见下） | 是 |

apply 前基线（只读，仅计数，13:48:45；无姓名、手机号）：

| 项 | 值 |
|---|---|
| total_units | 5742 |
| owners / phones | 7862 / 4301 |
| 已认证 Membership 有效绑定（`ended_at` 为空）/ Membership 总数 | 2 / 2 |
| building="地下车位" 计数 | 0 |
| building="1栋" 且 unit_type=PARKING 且 floor 以"负"开头 | 1391 |
| id=4347 | 楼栋 `1栋`、类型 `SHOP`、楼层 `负1`（用户决定不纳入） |

apply 前 dry-run 复核（13:48:51）：`total_units=5742`、`candidates=1391`、`already_target=0`、`would_change=1391`、`conflicts=0`、`negative_floor_non_parking=1`、`other_building_negative_parking=0`、`old_building|1栋|1391`、`floor|负1|1119|recognized`、`floor|负2|272|recognized`、`EXIT=0`。满足停止条件之外（would_change=1391 且 conflicts=0），继续。

## 分步执行（阶段 C）

| DEPLOY | 命令 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| DEPLOY-006 | 本地取 `TS2` 一次；`ssh host bash -s -- <TS2>`（脚本经 stdin 传入）：`umask 077`；加载 `.env`；校验 `DB_NAME=ocap`；`MYSQL_PWD` 环境变量传口令（未入 argv，未写值）；`mysqldump --skip-ssl --single-transaction --no-tablespaces ocap` 仅 4 张表；`chmod 600` | 13:49:01 | 约 4 s | SUCCESS | `DATA_TS=20261116134900`；文件 `/home/yangyang/ocap/snapshots/ocapdb-registry-20261116134900.sql`，权限 `600`，1682257 字节；每表各 1 条 `INSERT INTO`（共 4）；末行 `-- Dump completed on 2026-11-16 13:49:04`；SHA256 `7d87249b0cf52cda0c2c13e44f1d0f7611f01faba9763ae6e200c7dbfe272d33` |
| DEPLOY-007 | `cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && venv/bin/python manage.py relocate_underground_parking --apply --backup /home/yangyang/ocap/snapshots/underground-20261116134900.jsonl --expect-changes 1391 --list-limit 1; echo EXIT=$?`（本地展开后 echo 核对再执行） | 13:49:10 | 约 9 s（含 SSH） | SUCCESS | `EXIT=0`；`moved=1391`；`backup_records=1391`；`before_*`/`after_*` 逐项相等（units 5742、owners 7862、phones 4301、active_memberships 2）；命令内部核对通过未触发回滚 |

备份 JSONL：`/home/yangyang/ocap/snapshots/underground-20261116134900.jsonl`，权限 `600`，360351 字节，文件 SHA256 `6f806df17663000951b2e66804920e5af704aacb1e445d88f55ea3fd830de1b4`。命令自身输出的 `backup_sha256=adbe61d7d26315f047e97d043952cd76d8fd55a94d54f47cbcd163f760887e8c` 是文件末行记录的"前面全部行字节"的内容摘要，与整文件 SHA256 口径不同，二者并不矛盾。

注：计划预期的 `differences=0` 行未出现在 apply 输出中（命令只输出 `before_*`/`after_*`；其内部核对以退出码 0 表示通过）。以独立只读计数补证，见下。

## 验证结果（阶段 C）

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| total_units 不变 | 5742（前 5742） | 是 |
| owners / phones 不变 | 7862 / 4301（前后相同） | 是 |
| building="地下车位" 计数 = 1391 | 1391（前 0） | 是 |
| "1栋"下 PARKING 负层计数 = 0 | 0（前 1391） | 是 |
| 已认证 Membership 有效绑定总数前后相等 | 2 = 2（Membership 总数亦为 2） | 是 |
| id=4347 未被改动 | 仍为 `1栋` / `SHOP` / `负1` | 是 |
| 再跑 dry-run 幂等 | `would_change=0`、`already_target=1391`、`conflicts=0`、`EXIT=0` | 是 |
| ocap-backend active | `active` | 是 |
| `/ocap/api/v1/units/options` 未登录 | 目标机 127.0.0.1:9000 `/api/v1/units/options` 返回 401 | 是 |
| 后端日志（近 5 分钟） | `Traceback|ERROR` 命中 0 行 | 是 |
| 失败单元 | `systemctl --state=failed` 0 条（无 freeark-*、ocap-*） | 是 |
| 备份文件权限 | 两个文件均 `600` | 是 |

## 回滚记录（阶段 C）

无。DEPLOY-007 成功，未触发回滚，未执行 `--restore`。

## 当前系统状态与人工干预建议（阶段 C）

- 目标机运行 15ea79e 代码；库内 1391 条地下车位已改为 building="地下车位"，specific_part 同步改为"地下车位负N层…号"；总数与有效绑定数不变；4347 商铺仍为 1栋。服务未重启。
- 目标机新增文件（均含个人信息或备份，仅留目标机，权限 600，未传出）：`snapshots/ocapdb-registry-20261116134900.sql`、`snapshots/underground-20261116134900.jsonl`。保留期由用户决定。
- 若需还原数据（属再次改库，须用户决定）：按 ROLLBACK-007，先 `--restore <BK>`（只读）核对，再 `--restore <BK> --apply`；整库级兜底为 sql 文件的覆盖式导入，仅由人评估后执行。默认建议保留修正，仅在需要时回滚代码。
- MV-05（小程序真机与 Web 比较"选择房屋"四级顺序，地下车位排在最后）现可由用户验证。阶段 D（导出）、E 仍须各自授权；D 的预期是 `relocated_units=0`、`precheck_would_create_*` 为 0。

## 遗留问题（阶段 C）

1. 阶段 D、E 未授权，未执行。
2. `negative_floor_non_parking=1`（即 id=4347 商铺）保持原状，由用户已决定不纳入。
3. apply 输出无 `differences` 行，与计划预期文字略有差异，已用独立计数与二次 dry-run 补证；建议计划后续版本修订该预期。
4. 外网 SSH 建连间歇断开（本阶段 2 次后成功），与 M-DE-009 一致。
5. 本机 `/` 下仍有阶段 A 前遗留的两个空归档（`/ocap_backend_15ea79e….tar.gz`、`/frontend_dist.tar.gz`），未处理（不在授权范围）。
6. 本机 `/tmp/ocs.570r`、`/tmp/ocs.gY6Q`、`/tmp/ocs.uuyJ` 为更早会话遗留的 SSH 套接字目录，非本次创建，未触碰。

---

# 部署报告：阶段 D（导出导入文件，只读）

> 版本 3.1.0 追加（DRAFT）。阶段 A、B、C 内容未改动。

## 摘要（阶段 D）

- 目标环境：测试（外网 `ssh -p 57279`，ControlMaster 复用，套接字目录 `/tmp/ocs.kFuX`，结束后已关闭并删除；前 6+ 次建连 `Connection closed`，随后成功，仅对建连重试，此时未执行任何目标机命令）。策略：不适用（只读导出，无停机）。
- 开始 / 结束：2026-11-16T13:55 起；DEPLOY-008 13:56:21，DEPLOY-009 约 13:58，DEPLOY-010 14:00:30。
- 回滚锚点：无新增（目标机仅有一个临时文件，已删除）。`TS3=20261116135620`。
- 步骤 3（DEPLOY-008~010）/ 完成 3 / 失败 0 / 跳过 0。
- **最终状态：DEPLOYED_SUCCESSFULLY（阶段 D）**。未出现 gaps，未使用 `--allow-gaps`。

## 授权核对（阶段 D、E 共用）

- 授权来源：本次 invocation 的 `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true`，目标环境「测试」，范围阶段 D + 阶段 E，用户原话"授权D 、E 段"。
- 授权环境名「测试」= deployment_plan 目标环境「测试」= 画像 P7 环境名「测试」。deployment_plan 版本 1.0.0 = phase_status 登记的 APPROVED 版本。
- 主机指纹：本机 known_hosts 中 `[47.109.197.217]:57279` 的 ED25519 为 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，与画像 P7 一致。
- 授权口径：REWORK_AUTHORIZED 仅限本文件追加阶段 D、E 并升 3.1.0 / DRAFT，A~C 正文未改（仅改文件头 timestamp/version/status）。
- 边界：未改代码、未 migrate、未 apply/restore、未改清册、未碰 Freeark；写库仅限 `e2e_` 夹具，已清理。

## 预检结果（阶段 D）

| 检查项 | 结果 | 通过 |
|---|---|---|
| PRE-D01 gaps | 导出输出 `gaps_units=0`、`gaps_unnamed_owners=0` | 是 |
| PRE-D02 本地落点安全 | `registry_import_underground_parking.*` 不存在；`git check-ignore -v` 命中 `.gitignore:14` | 是 |
| 目标机无遗留 `export_*` | `No such file` | 是 |
| ocap-backend | `active` | 是 |

## 分步执行（阶段 D）

| DEPLOY | 命令 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| DEPLOY-008 | `cd /home/yangyang/ocap/backend && set -a && . ./.env && set +a && umask 077 && venv/bin/python manage.py export_registry_import_file --output /home/yangyang/ocap/snapshots/export_20261116135620.xlsx; echo EXIT=$?; stat; sha256sum`（本地展开后 echo 核对，无 `--allow-gaps`） | 13:56:21 | 约 1 s | SUCCESS | `EXIT=0`；`db_units=5742 / db_owners_named=7862 / db_phones_distinct=4256`，`file_*` 同值，`diff_*=0`；`relocated_units=0`、`gaps_*=0`；`precheck_rows_failed=0`、`precheck_would_create_units/owners/phones=0`、`precheck_would_update_units=0`；`roundtrip_mismatches=0`；`output_bytes=336459`；权限 `600`；SHA256 `70ed019c8f60b3d7a763f9397288a2624955c08ed4b9c8e365e9d412ee938dc1` |
| DEPLOY-009 | `scp -P 57279 yangyang@…:<X> ./registry_import_underground_parking.xlsx`（`umask 077`）；`chmod 600`；`sha256sum`；`git check-ignore -v`；`git status --short \| grep …` | 约 13:57 | 约 2 s | SUCCESS | 仓库根 `/root/myproject/ocap/registry_import_underground_parking.xlsx`，336459 字节，权限 `600`；本地 SHA256 `70ed019c…38dc1` 与远端一致；`.gitignore:14` 命中；`git status` 无该文件（`NOT_TRACKED_OK`） |
| DEPLOY-010 | `rm -f <X>; ls <X>; ls snapshots/export_*`（路径核对仅此一个文件，仅在本地 SHA256 核对通过后执行） | 14:00:30 | 约 1 s | SUCCESS | 两个 `ls` 均 `No such file or directory`（命令总退出码 2 来自最后的 `ls`，预期） |

## 验证结果（阶段 D）

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| 自检：`rows_failed=0`（`precheck_rows_failed`） | 0 | 是 |
| 自检：计数与库一致 | `diff_units/owners_named/phones_distinct=0`（5742/7862/4256） | 是 |
| 自检：`roundtrip_mismatches=0` | 0 | 是 |
| 阶段 C 后导出不产生新建 | `relocated_units=0`、`precheck_would_create_*=0`（AC-187-05） | 是 |
| 文件权限 | 目标机 600；本地 600 | 是 |
| SHA256 两端一致 | `70ed019c…38dc1` | 是 |
| gitignore 命中且不被跟踪 | 是 | 是 |
| 目标机临时文件已删除 | 不存在 | 是 |
| 本地只读抽查（`python3 -I`，直接解析 xlsx 的 XML，未输出姓名/手机号） | 表头 8 列；数据行 7862；去重专有部分 5742；楼栋="地下车位" 的专有部分 1391（负1 1119、负2 272，数据行 1454 全部类型"车位"）；楼栋="1栋" 且楼层以"负"开头的专有部分 1 个（对应 id=4347，4 行数据均为"商铺"，仍为 1栋） | 是 |

说明：命令输出的 `db_phones_distinct=4256`（去重手机号）与阶段 C 计数的 `phones=4301`（RegistryPhone 行数）口径不同，不矛盾。

## 回滚记录（阶段 D）

无。

## 当前系统状态（阶段 D）

- 目标机：无导出临时文件，库未变。本机仓库根存在含个人信息的 `registry_import_underground_parking.xlsx`（0600，已 gitignore，不提交、不上传）。保管与保留期由用户决定。

---

# 部署报告：阶段 E（P4-1 远程 HTTP E2E，仅 e2e_ 夹具）

## 摘要（阶段 E）

- 目标环境：测试。入口 `https://ai-freeark.xin/ocap/`（HTTP 测试不经 SSH）；夹具创建与清理经 SSH。
- 开始 / 结束：2026-11-16T14:00:50 起（夹具 setup），套件 14:01:33~14:03:02，补证夹具第 2 轮 14:05:16~14:06:56，最终复核 14:08:31。
- 步骤：DEPLOY-011（setup 2 轮）、DEPLOY-012（22 条用例 + 补证）、DEPLOY-013（cleanup 2 轮）。总 3 / 完成 3 / 失败 0 / 跳过 0。
- 夹具口令：由本地进程内生成，经 stdin 传远端，不落盘、不进 argv、不写入本报告。夹具所选房屋：id 7、8、10（1栋住宅，均无有效房屋关系），不涉及地下车位。
- **最终状态：DEPLOYED_SUCCESSFULLY（阶段 E）**。夹具已清理；远程套件 2 条失败均为既有 DEF-B，本批新增失败 0。

## 分步执行（阶段 E）

| DEPLOY | 命令 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| 基线（只读） | `e2e_fixture status`；`_free_units(3)` | 14:01:04 | 约 3 s | SUCCESS | e2e 全 0；`registry_counts` RegistryUnit 5742 / RegistryOwner 7862 / RegistryPhone 4301；`claim_amount_max=1000000.00`；空闲住宅 id 7、8、10 |
| DEPLOY-011（第 1 轮） | `printf '%s' "$PW" \| ssh … 'IFS= read -r OCAP_E2E_PASSWORD; export …; … OCAP_E2E_FIXTURE=1 venv/bin/python manage.py e2e_fixture setup --units 3 --bulk-users 25 --bulk-resolutions 25'` | 14:00:50 | 约 10 s | SUCCESS | `SETUP_EXIT=0`；status：users 35、admins 1、memberships 9、seats 3、resolutions 25、flows 2；`registry_counts` 与基线相同 |
| DEPLOY-012 | `OCAP_E2E_BASE_URL=https://ai-freeark.xin/ocap/ python3 backend/tests/remote/run_remote.py -v`（口令经环境变量，未设 `OCAP_E2E_ALLOW_LOCAL`、`OCAP_E2E_SLOW`） | 14:01:33 | 89.0 s | PARTIAL（见下） | `Ran 22 tests`；`FAILED (failures=2, skipped=1)`；`RUN_EXIT=1` |
| DEPLOY-013（第 1 轮） | `e2e_fixture cleanup`（dry-run）→ `cleanup --execute` → `status`；只读核对计数。失败也会清理（脚本 `trap EXIT`） | 14:03:03 | 约 7 s | SUCCESS | dry-run `DRY_EXIT=0`，`would_delete` 仅 e2e 数据；`EXEC_EXIT=0`，删除 users 35、admins 1、memberships 12、seats 3、resolutions 25、appeals 2、resident_applications 3、claims 1、approval_instances 1、attachments 4、tokens 13、flows 7；status e2e 全 0；`REGISTRY_NOW 5742 7862 4301 underground 1391` |
| DEPLOY-011（第 2 轮，补证用，同命令，`--bulk-users 0 --bulk-resolutions 0`） | 同上 | 14:05:16 | 约 5 s | SUCCESS | `SETUP_EXIT=0`；users 10、admins 1、memberships 9、seats 3、flows 2 |
| 补证探测（只读 GET） | `probe_options.py`：经 `tests.remote.remote_client.Remote`（沿用其护栏）请求 `/units/options` | 14:06:47 | 约 4 s | SUCCESS | 见下表 |
| DEPLOY-013（第 2 轮） | 同第 1 轮 | 14:06:51 | 约 5 s | SUCCESS | `EXEC_EXIT=0`；删除 memberships 9、seats 3、flows 4、users 10、admins 1；status e2e 全 0；`REGISTRY_NOW 5742 7862 4301 underground 1391` |

夹具循环说明：共 3 次 setup/cleanup 循环，每次均清理，清理后 e2e 计数为 0、清册计数为 5742 / 7862 / 4301、"地下车位" 1391。
1. 循环 1（14:00:50~14:03:10）：运行远程套件；随后的探测脚本因我的脚本错误（导入了不存在的类名 `Client`）未发出任何请求，夹具已按计划清理。
2. 循环 2（14:05:16~14:05:29，users 10、`--bulk-users 0 --bulk-resolutions 0`）：探测脚本只发出了未登录 `/units/options`（401），随后请求管理端 `filter-options` 时被套件护栏 `guard()` 拒绝（未发出该请求），脚本中止，trap 触发清理。
3. 循环 3（约 14:06:3x~14:06:56，同参数）：移除该管理端请求后重跑探测，成功；随后清理（上表「补证探测」与「DEPLOY-013 第 2 轮」即此次）。

> 上表中 DEPLOY-011「第 2 轮」/ DEPLOY-013「第 2 轮」的详细数字取自循环 2 的日志（users 10、memberships 9、seats 3、flows 2→4）；循环 3 数字相同。

## 验证结果：远程套件（TC-E2E-320 ~ 341，共 22 条）

通过 19、失败 2、跳过 1（19 + 2 + 1 = 22）；通过率 = 19 / (19 + 2) = 90.5%。

| 用例 | 结果 | 归属 | 说明 |
|---|---|---|---|
| TC-E2E-320、322、323、325、326、327、328、329、330、331、333、334、335、336、337、338、339、340、341 | PASS | — | 含 329（模板预检只读，清册总数前后不变）、328（有报表可验，未 SKIP） |
| TC-E2E-321 | **FAIL** | **既有 DEF-B**（ocap_product_review，"户主"文案过期） | 断言 `sorted(labels) == ["同住人","户主"]`，实际 `['产权业主','同住人']`（remote_cases.py:77）。与本批改动（排序、清册过滤、地下车位）无关 |
| TC-E2E-324 | **FAIL** | **既有 DEF-B** | 断言 `identity_label == "户主"`，实际 `产权业主`（remote_cases.py:114）。同一文案过期原因 |
| TC-E2E-332 | SKIP | 设计内（慢用例，需 `OCAP_E2E_SLOW=1`，等待 31 分钟） | 本轮未启用 |

- 本批新增失败：0。DEF-A（排序）：套件无对应失败；对应远程可验点见下表补证。
- 未修改任何测试代码。

## 验证结果：本批新增可验点（套件未覆盖，只读 HTTP 补证）

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| 未登录 `GET /ocap/api/v1/units/options` | 401（外网入口） | 是 |
| e2e_owner_a 登录后第一级楼栋顺序 | 共 38 项；`1栋…10栋` 为数字序（1,2,…,10，非字典序 `10栋` 在 `2栋` 前）；"地下车位"在第 38 位（最后） | 是 |
| `?building=地下车位` 下一级 | `level` 为楼层（单元级为空被跳过，`skipped` 含 `unit_no`），选项 `[负2, 负1]`，顺序 负2 在 负1 之前 | 是 |
| `?building=1栋` 下一级 | `1单元`、`2单元`，不再出现负层 | 是 |
| 未登录 filter-options（管理端） | 未做：套件护栏 `guard()` 不允许对 `/admin/registry/units/filter-options` 发 GET；阶段 A 已在目标机内验证 401 | 不适用（沿用护栏，不绕过） |
| 后台清册地下车位 count | 未做：该列表含业主姓名/手机号，护栏范围外；阶段 C 已用独立计数证明 1391 | 不适用 |

补充说明：第 3 级"房号"（room）选项未逐条请求；探测脚本在第 3 级误传 `unit_no=负2`（该级本应传 `floor=负2`），收到空列表，属脚本传参错误，不是产品缺陷，已按 `RegistryService.options` 源码核对（unit_no 为空时被跳过，第二级返回楼层）。

## 验证结果：清理与基线（阶段 E 结束）

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| e2e_ 计数 | `e2e_fixture status` 全部为 0（users/admins/flows/memberships/seats/appeals/… 均 0） | 是 |
| 清册计数 | RegistryUnit 5742 / RegistryOwner 7862 / RegistryPhone 4301，与基线相同 | 是 |
| "地下车位"计数 | 1391 | 是 |
| `claim_amount_max` | 1000000.00（未改） | 是 |
| ocap-backend | `active` | 是 |
| 后端日志（近 15 分钟） | `Traceback|ERROR` 命中 0 | 是 |
| 失败单元 | 0 | 是 |
| 目标机 `export_*` 文件 | 0 | 是 |
| 外网 | `https://ai-freeark.xin/` 200；`https://ai-freeark.xin/ocap/` 200；目标机 `/api/v1/units/options` 401 | 是 |

观察：第 1 轮 cleanup 的 dry-run `would_delete.flows=3`，execute 实际 `flows=7`（含套件创建后被软停用的流程；第 2 轮 2→4 同理），属 e2e 流程的软停用行也被清理，均为 e2e_ 数据，计数核对通过，非问题。

## 回滚记录（阶段 D、E）

无。DEPLOY-010、013 对应 ROLLBACK 为设计内无操作。

## 当前系统状态（阶段 D、E 结束）

- 目标机运行 15ea79e；库内 1391 条地下车位在"地下车位"楼栋，4347 仍为 1栋商铺；e2e_ 数据已清空；目标机 `snapshots/` 保留阶段 A 快照、`ocapdb-registry-20261116134900.sql`、`underground-20261116134900.jsonl`（均含个人信息，权限 600，保留期由用户决定）。
- 本机：仓库根 `registry_import_underground_parking.xlsx`（0600，gitignore，不提交）；SSH 套接字目录已关闭删除；`/tmp/claude-0/.../scratchpad` 下有 `run_e2e.sh`、`run_probe.sh`、`probe_options.py` 与日志（日志不含口令与姓名手机号，口令从未写盘）。

## 遗留问题（阶段 D、E）

1. 既有 DEF-B：TC-E2E-321、324 期望文案"户主"，实际"产权业主"，需回流修正测试期望（ocap_product_review 范围）；子代理无测试代码写权限，未改。
2. TC-E2E-332（31 分钟慢用例）未运行。
3. MV-04、MV-05（浏览器/小程序人工验证）、MV-03（并发）仍待用户。MV-05 可在阶段 C 之后进行；本次 `/units/options` 已证明服务端顺序，客户端展示仍须人工看。
4. 远程套件缺少对 `units/options` 逐级顺序的用例，建议新增（本次用只读 HTTP 补证）。
5. 含个人信息的本地导出文件与目标机备份文件的保留/销毁由用户决定。
6. 本机 `/` 下仍有阶段 A 前遗留的空归档（`/ocap_backend_15ea79ea….tar.gz` 等），未处理。
7. 外网 SSH 建连间歇断开再次出现（本阶段首次建连约 7 次失败后成功），与 M-DE-009 一致。
