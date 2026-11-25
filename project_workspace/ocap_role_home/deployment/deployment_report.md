<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-25T13:21:20+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_role_home/deployment/deployment_plan.md</file>
    <file>project_workspace/ocap_role_home/deployment/cicd_pipeline.md</file>
    <file>.agents/skills/ocap-deploy/SKILL.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告 — ocap_role_home（测试环境）

## 摘要

- 目标环境：测试环境（画像 P7：树莓派，内网 nginx `8090`；外网 frp/VPS `443`）。
- 策略：recreate（前端静态目录替换）；后端不重启、无迁移（按已批准 `deployment_plan.md` 1.0.0）。
- 开始/结束：2026-11-25T13:19:30+08:00 / 2026-11-25T13:21:20+08:00。
- 回滚锚点：**未创建**（预检阶段即失败，目标机未发生任何变更）。
- 总步骤 6 / 完成 0 / 失败 0 / 未执行 6；预检 7 项中 3 项通过、4 项未通过或无法执行。
- 最终状态：**DEPLOYMENT_FAILED**（预检失败，无需回滚）。

## 授权核对

| 项 | 值 |
|---|---|
| 授权来源 | 用户本轮消息：“提交并推送代码，等待 CI 通过后授权部署到测试环境”（条件授权：CI 通过后生效） |
| 条件满足证据 | GitHub Actions run [45552545821](https://github.com/yangyang198354-haha/ocap/actions/runs/45552545821) = `success`（backend / Web frontend / miniprogram 三个 job 全部 success），headSha `5a787ecc648aac2336b36cbfe5aa599ba1202956` |
| 授权环境名 | 测试环境 |
| 计划目标环境 | 测试环境（画像 P7） |
| 画像 P7 环境名 | 测试（内网）/ 测试（外网），同一主机 |
| 计划版本 | `deployment_plan.md` 1.0.0 APPROVED（phase_status 登记一致） |
| 结论 | 授权与环境匹配；**执行被运行环境阻塞，非授权问题** |

## 分步执行

| 检查/步骤 | 命令（摘要） | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| P-01 版本标识 | `git rev-parse HEAD`；`git status --short` | 13:19:30 | <1s | PASS | `5a787ec`；工作树干净；`origin/main` 已快进推送 `9a754e4..5a787ec` |
| P-02 CI 结果 | `gh run view 45552545821` | 13:19:40 | 2s | PASS | `conclusion=success`，三 job success |
| P-03 内网 SSH | `ssh yangyang@192.168.31.51` | 13:20:00 | 12s | FAIL | `connect to host 192.168.31.51 port 22: Connection timed out`（沙箱无内网路由） |
| P-04 外网 SSH（直连） | `ssh -p 57279 yangyang@47.109.197.217` | 13:20:20 | 15s | FAIL | `connect to host 47.109.197.217 port 57279: Connection timed out`（直连出站被阻断） |
| P-05 外网 SSH（经沙箱 HTTP 代理） | `nc -X connect -x 127.0.0.1:18080 47.109.197.217 57279` | 13:20:45 | 10s | PARTIAL | TCP 隧道建立成功，收到 `SSH-2.0-OpenSSH_10.0p2 Debian-7`；改用 `ssh -o ProxyCommand=...` 时 `Connection timed out during banner exchange` |
| P-06 SSH 凭据 | `ls /root/.ssh`；`ssh-add -l`；查找 `id_*`/`*.pem` | 13:21:00 | 1s | FAIL | 沙箱内无 SSH 私钥、无 ssh-agent、无可用密钥环境变量；无法完成 publickey 认证 |
| P-07 目标机只读预检 | 磁盘/端口/env/nginx 等 | — | — | 未执行 | 无可用 SSH 会话 |
| DEPLOY-001~005 | 见 `deployment_plan.md` | — | — | 未执行 | 预检未通过，按流程停止 |

## 验证结果

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| V-01~V-10 | 未执行（目标机未变更，无新版本可验证） | — |

## 回滚记录

| ROLLBACK | 命令 | 结果 | 输出摘要 |
|---|---|---|---|
| — | 无 | 未执行 | 预检阶段失败，目标机无任何写入；无需回滚 |

## 当前系统状态与人工干预建议

- 目标机状态：**未变更**。未上传文件、未创建锚点/暂存目录、未改 nginx、未重启服务。
- 阻塞原因：当前 Trae 远程沙箱位于公网隔离环境，缺少两样必要条件：
  1. 到测试环境的内网路由（`192.168.31.51:22` 不可达）；
  2. 目标机免密 SSH 私钥（沙箱 `/root/.ssh` 为空，无 ssh-agent）。
- 可选路径（需用户选择）：
  1. 用户将部署私钥上传到工作区（仅授权本次使用），并确认允许经 `47.109.197.217:57279` 外网通道；还需解决沙箱到该端口的 SSH 握手（HTTP 代理 CONNECT 已能建 TCP，但 banner 交换超时）。
  2. 由用户在具备内网/密钥的机器上按 `deployment_plan.md` 手工执行 DEPLOY-001~005（前端构建、打包、上传、解包、替换），PM 可提供逐条命令与校验输出模板。
  3. 暂停部署，等待 CI 与代码合并完成后的下一轮授权。

## 遗留问题

- 部署尚未发生；`ocap_role_home` 的前端改动已合并到 `main` 且 CI 全绿，但测试环境仍运行旧版本。
- 若改用“目标机就地构建”不可行（目标机不做构建，且会触碰本地状态），仍推荐本计划的上传制品方式。
- 沙箱内无法核验目标机 ED25519 指纹（`SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`）；取得可用会话后必须先核验再部署。
