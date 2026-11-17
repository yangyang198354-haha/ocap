<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-17T13:59:19+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>deployment/deployment_plan.md</file>
    <file>deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：品牌更名 Cyber@红枫岭 + Web 左侧导航布局（测试环境，仅 Web 静态产物）

## 摘要

- 目标环境：**测试**（画像 P7 唯一环境）；策略：recreate（静态目录整体替换）
- 开始 / 结束：2026-11-17T13:46:28+08:00 / 2026-11-17T13:58:42+08:00
- 版本标识：HEAD = `113379420269cd7e977e8a314be56b9dd7828ad6`（1133794，与 `git ls-remote origin main` 一致；`git status --short` 仅剩 `phase_status.md` 一处修改，产品代码范围为 0）
- 构建产物：tar SHA256 `1b7b12e169ceedcc27304ced63323ab4e366edf1d0a1f2140dd83cf9a9b0c0cf`（659658 B，两端一致）；`dist/index.html` SHA256 `b451dab982c7c2b2f85845db87d0c384c2d0a3427dffef5a75f22824e73365c6`（1039 B）；`dist` 69 个文件；入口 `index-DoXyBgF2.js`、`index-C-LMq4Cp.css`；字体 `OcapBrand-subset-c41YCxaj.woff2`（SHA256 `c02ca28c…2109`）。以上与计划编制时参考值完全一致。
- **回滚锚点**：`TS=20261117135725`；`/home/yangyang/ocap/snapshots/web-20261117135725.tar.gz`（SHA256 `773678aaa90eaa0456bafc05b55853e3f27677db2a6b34afc165616e3adf24cb`）与 `webhash-20261117135725.sha256`（52 行）。旧线上 `index.html` SHA256 `0c71947a…8754`，入口 `index-8pjlGbdL.js`、`index-DwTVKv1n.css`。
- 步骤：预检 15 项全部通过；DEPLOY 共 5 / 完成 5 / 失败 0 / 跳过 0；验证 V-01~V-14 共 14 / 通过 14；回滚 0 次。
- **最终状态：DEPLOYED_SUCCESSFULLY**
- 人工验证 MV-01~05 未由本报告覆盖（用户部署后执行，critical path 4 项未完成 → 交付至多 DELIVERED_WITH_ISSUES）。

## 授权核对

| 项 | 核对结果 |
|---|---|
| 授权来源 | 本次 invocation `special_instructions`：`PRODUCTION_DEPLOY_CONFIRM=true`，用户 Q3=A「授权部署」（仅对本次调用有效） |
| 环境名 | 授权「测试」= deployment_plan 目标环境「测试」= 画像 P7 环境「测试」，一致 |
| 计划版本 | deployment_plan 1.0.0 = phase_status 登记的 APPROVED 版本（GROUP_E1 APPROVED），一致 |
| 前置 | 画像 P7「部署需用户确认=是」；GROUP_D APPROVED；计划授权条件 3 已满足（提交 1133794 已推送，改记 HEAD） |
| 范围约束 | 未改 nginx / Freeark / backend / 数据库；未重启或 reload 任何服务；未登录、未创建 `e2e_` 账号，只发无令牌只读 GET |

## 预检结果

| 编号 | 实际结果 | 通过 |
|---|---|---|
| PRE-01 | HEAD 1133794；`git status --short` 仅 `phase_status.md`（非产品代码） | 是 |
| PRE-02 | `git status --short -- backend deploy frontend/package*.json miniprogram/package.json` = 0 行 | 是 |
| PRE-03 | `git ls-files --others --exclude-standard frontend miniprogram themes scripts` = 0 行（本批已提交，无游离文件）；`git check-ignore frontend/dist` 有输出 | 是 |
| PRE-04 | `node scripts/themes/build.mjs --check --strict` EXIT=0 | 是 |
| PRE-05 | 前端 vitest：Test Files 37 passed (37)，Tests 438 passed (438)，226 s。小程序可选项未复跑 | 是 |
| PRE-06 | `✓ built in 42.99s`；woff2 个数 1；`<title>Cyber@红枫岭`；`/ocap/api/v1` 在入口 js 中计数 1；CSS 含 `url(/ocap/assets/OcapBrand-subset-c41YCxaj.woff2)`；dist 与 src 字体 SHA256 相同 | 是 |
| PRE-07 | 首次建连成功（attempt=1）；`known_hosts` 中 `[47.109.197.217]:57279` ED25519 = `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`，与画像一致 | 是 |
| PRE-08 | /home 可用 16 GB；可用内存 1642 MB | 是 |
| PRE-09 | 8000 uvicorn、80/8080 nginx（Freeark）；9000 gunicorn（ocap）、8090 nginx（ocap） | 是 |
| PRE-10 | `backend/ web/ snapshots/`；ENV_OK、VENV_OK、VAR_OK；`snapshots/` 内上批备份均在；`web/` 下另有 `ocap.old-20261115184022`（仅记录，未触碰）。未见同级 `ocap_exports/` | 是 |
| PRE-11 | `web/ocap` 与 `index.html` 属主 `yangyang:yangyang` → `OWN=yangyang:yangyang`，通过格式校验 | 是 |
| PRE-12 | `active`；`MainPID=1201920`；`ActiveEnterTimestamp=Mon 2026-11-16 22:50:39 CST` | 是 |
| PRE-13 | `nginx -t` syntax ok / test successful；Freeark `:8080` 返回 200 | 是 |
| PRE-14 | `sites-available/ocap:32 try_files $uri $uri/ /ocap/index.html;`；`mime.types` woff2 计数 1；`sites-available/ocap` 无 woff/types 覆盖；`sites-enabled/freeark:44` 有 `location ~* \.(…woff|woff2…)$` 静态正则，由 `^~ /ocap/` 前缀块优先匹配，不影响 /ocap/（V-08 实测印证）。仅读取 | 是 |
| PRE-15 | 旧 `index.html` SHA256 `0c71947a8fdb17041eebf94d531723240e4afe02f85d4c98119de100f6c58754`，旧入口 `index-8pjlGbdL.js`、`index-DwTVKv1n.css`，旧文件数 52；公网 `200 text/html 1039` | 是 |

## 分步执行

| DEPLOY | 命令（摘要） | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| DEPLOY-001 | 本地取一次 `TS`；目标机 `sudo tar czf …/web-$TS.tar.gz -C …/ocap web`；生成逐文件哈希清单（`bash -s -- "$TS"`） | 13:57:25 | 约 2 s | SUCCESS | `ANCHOR_TS=20261117135725`，`TS_FORMAT_OK`；快照 1253129 B；清单 52 行 = 旧文件数；快照内 `web/ocap/index.html` 计数 1；快照 SHA256 `773678aa…24cb` |
| DEPLOY-002 | 开发机 `tar -czf "$SCRATCH/frontend_dist_$TS.tar.gz" -C frontend/dist .`（构建见 PRE-06，本步复核产物，`$SCRATCH` 先核验为 `/tmp/ocpkg.*`） | 13:57 | 约 1 s | SUCCESS | tar 659658 B，SHA256 `1b7b12e1…c0cf`；`index.html` SHA256 `b451dab9…65c6`；69 个文件；`WOFF2_PRESENT`、api 前缀计数 1 |
| DEPLOY-003 | `scp -P 57279` 上传到 `/tmp/`；远端 `sha256sum`；解包到 `/tmp/ocap_web_stage_$TS` 并核对 | 13:57:38 | 约 5 s | SUCCESS | `SCP_OK`；目标机 tar SHA256 与本地一致；暂存含 `index.html`；woff2 个数 1；文件数 69；暂存 `index.html` SHA256 = `b451dab9…65c6` |
| DEPLOY-004 | `sudo rm -rf …/web/ocap/* && sudo cp -a /tmp/ocap_web_stage_$TS/. …/web/ocap/ && sudo chown -R yangyang:yangyang …/web/ocap && ls -l && find \| wc -l && sha256sum`（执行前 echo 核对 `TS`、`OWN` 已展开） | 13:57:55 | <1 s | SUCCESS | RC=0；`index.html` 1039 B；文件数 69；SHA256 `b451dab9…65c6` = 本地 |
| DEPLOY-005 | 验证全部通过后：`rm -rf /tmp/ocap_web_stage_$TS && rm -f /tmp/frontend_dist_$TS.tar.gz && ls …` | 13:58:41 | 约 1 s | SUCCESS | 两路径均 `No such file or directory`；快照与哈希清单仍在 |

SSH 通道：ControlMaster 复用；首次建连即成功，无重试、无断连。结束后清理本地 `/tmp/ocpkg.H9SL`、`/tmp/ocs.wcVo`（先校验前缀）；`ssh -O exit` 提示套接字已不存在（ControlPersist 10 分钟已到期，无影响）。

## 验证结果

执行时间 13:58:07~13:58:35，均在 DEPLOY-005 之前。

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| V-01 后端未重启 | `active`；`MainPID=1201920`、`ActiveEnterTimestamp=Mon 2026-11-16 22:50:39 CST`，与 PRE-12 相同 | 是 |
| V-02 后端日志无新错误 | 近 5 分钟 `grep -ciE 'Traceback\|ERROR'` = `0` | 是 |
| V-03 线上 index.html = 本地构建 | 公网 `sha256sum` = `b451dab9…65c6` = 本地 `dist/index.html` | 是 |
| V-04 内网入口（目标机内 127.0.0.1:8090） | `200 text/html` | 是 |
| V-05 公网入口 | `200 text/html 1039`，大小 = 本地 1039 B | 是 |
| V-06 页面标题 | `<title>Cyber@红枫岭</title>` | 是 |
| V-07 入口 js/css | js：`200 application/javascript 1151578`，SHA256 `09b54fe8…9906` = 本地；css：`200 text/css 409486`，SHA256 `23c1bfe1…af16` = 本地 | 是 |
| V-08 woff2 与 Content-Type | 公网 `200 font/woff2 12044`，SHA256 `c02ca28cb597dce5fcf98fa3c63de4a54604aeec43b5c3021f700150a3422109`；内网 `HTTP/1.1 200 OK`、`Content-Type: font/woff2`、`Content-Length: 12044`。Content-Type 符合预期，无需 nginx 建议 | 是 |
| V-09 CSS 字体路径 | `url(/ocap/assets/OcapBrand-subset-c41YCxaj.woff2)` = `$W` | 是 |
| V-10 深链刷新（8 条） | `/me/profile`、`/units/review`、`/resolutions/mine`、`/admin/finance/limit`、`/admin/users/registered`、`/admin/content/services/prompts`、`/admin/login`、`/login` 均 `200 text/html 1039`，SHA256 前缀 `b451dab982c7c2b2` = index.html | 是 |
| V-11 接口前缀与鉴权（无令牌 GET） | `GET /ocap/api/v1/me` → `401 application/json` | 是 |
| V-12 Freeark 与端口 | 公网 `https://ai-freeark.xin/` `200`；`systemctl --state=failed` 为 `0 loaded units`；8000 uvicorn（Freeark）、8080 nginx、8090 nginx、9000 gunicorn（ocap）；8080/8090 为 nginx 无 pid 显示（未用 sudo 查看），归属与 PRE-09 一致 | 是 |
| V-13 目标机落盘 | `yangyang:yangyang 755 web/ocap`；`index.html` 644；文件数 69；本次快照 `web-20261117135725.tar.gz` 存在 | 是 |
| V-14 本地状态 | `LOCAL_STATE_INTACT`（`.env`、`venv`、`var`）；`ocapdb-registry-20261116134900.sql`、`underground-20261116134900.jsonl` 仍在；`web/ocap.old-20261115184022` 未动 | 是 |

14 / 14 通过。

## 回滚记录

无。未发生任何步骤失败，未执行 ROLLBACK。需要回滚时按 deployment_plan ROLLBACK-004，锚点 `TS=20261117135725`，快照与哈希清单已核实存在，保留 ≥ 7 天。

## 当前系统状态与人工干预建议

不适用（未暂停、未回滚）。目标机当前：Web 静态目录为本批新版（69 个文件），后端未重启，nginx / Freeark / 数据库未触碰。

## 遗留问题

1. **人工验证 MV-01~05**：由用户在公网入口强制刷新（Ctrl+F5）后执行；MV-05 的 Content-Type 部分已由 V-08 完成。MV-03 为小程序，不在本次部署内。critical path 项未完成前交付至多 DELIVERED_WITH_ISSUES。
2. 旧页面标签引用的旧哈希 chunk 将 404 回退为 index.html，刷新即恢复（计划已列的通性影响）。
3. 偏差说明：计划 PRE-05/06 的构建在预检阶段完成，DEPLOY-002 只做打包与复核，没有重复构建（产物 SHA256 与计划参考值一致）；因提交已完成，PRE-03 的"34 个未跟踪源文件"改为 0 个未跟踪文件，属计划授权条件 3 预期的版本标识改记。
4. 小程序 `build:mp-weixin` 基线失败（GR-C-001-F04）、画像 P4 基线过期（GR-C-001-F03）仍为 PM 待处理项，与本次部署无关。
5. 快照约 1.2 MB 内含 `web/ocap.old-20261115184022`；`snapshots/` 累积旧快照，建议用户择期清理（本次未删除任何既有文件）。
6. 报告与输出中无凭据。
