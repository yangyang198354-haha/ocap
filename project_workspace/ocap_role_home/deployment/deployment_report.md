<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-25T14:18:30+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.1.0</version>
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

- 目标环境：测试环境（画像 P7：树莓派，内网 nginx `8090`；外网 `https://ai-freeark.xin/ocap/`）。
- 策略：recreate（前端静态目录替换）；后端不重启、无迁移、nginx 配置未改。
- 执行方式：沙箱无法建立到目标机的 SSH 会话（见“首次尝试”），改由用户登录树莓派、按 PM 提供的命令逐步执行并回传输出，PM 核对每条输出；步骤与 `deployment_plan.md` 一致。
- 时间：构建 2026-11-25T13:49:50 开始；替换与验证 2026-11-25T14:13 完成。
- 回滚锚点：`TS=20261125134950`，`/home/yangyang/ocap/snapshots/web-20261125134950.tar.gz`（40 MB，4009 条目，替换前创建）。
- 步骤：构建 1 / 快照 1 / 替换 1 / 验证 8；完成 11 / 失败 0 / 跳过 0。
- 最终状态：**DEPLOYED_SUCCESSFULLY**。

## 授权核对

| 项 | 值 |
|---|---|
| 授权来源 | 用户消息：“提交并推送代码，等待 CI 通过后授权部署到测试环境”；随后“你执行部署，命令给我，我可以登录树莓派，上去给你授权” |
| 条件满足证据 | GitHub Actions run [45552545821](https://github.com/yangyang198354-haha/ocap/actions/runs/45552545821) = `success`，headSha `5a787ec` |
| 授权环境名 | 测试环境 |
| 计划目标环境 / 画像 P7 | 测试（内网 8090）+ 测试（外网 frp 443） |
| 计划版本 | `deployment_plan.md` 1.0.0 APPROVED |
| 结论 | 授权、环境、版本一致；用户明确同意在其登录的树莓派上执行 |

## 首次尝试（失败，无变更）

| 项 | 结果 |
|---|---|
| 内网 SSH `192.168.31.51:22` | `Connection timed out`（沙箱无内网路由） |
| 外网直连 `47.109.197.217:57279` | `Connection timed out` |
| 经沙箱 HTTP 代理 CONNECT | HTTP 200，但隧道返回 `Not allowed at this time`；偶发收到 `SSH-2.0-OpenSSH_10.0p2 Debian-7` 后在 banner 交换阶段断开；域名 `ai-freeark.xin` 解析到同一 IP，结果相同 |
| SSH 凭据 | 沙箱生成部署密钥并由用户在 Pi 授权，但会话在认证前被拒 |
| 目标机变更 | 无；未上传、未替换、未重启 |

## 分步执行

### 第二次：用户在树莓派执行

| 步骤 | 命令（摘要） | 结果 | 输出摘要 |
|---|---|---|---|
| B-01 环境检查 | `node -v`、`npm -v`、`df -h /home` | PASS | Node `v22.22.2`、npm `10.9.7`、可用 14G |
| B-02 拉取源码 | `curl codeload.../tar.gz/5a787ec` + `tar xzf` | PASS | 3.8 MB，解包成功 |
| B-03 安装依赖 | `npm ci` | PASS | 226 packages，23s |
| B-04 构建 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | PASS | `✓ built in 14.96s`，`KEY_HITS=3`，`BUILD_OK` |
| B-05 快照 | `tar czf snapshots/web-20261125134950.tar.gz -C /home/yangyang/ocap web` | PASS | 40 MB，4009 条目；包含替换前 `web/ocap`（87 文件） |
| B-06 替换 | `rm -rf web/ocap` → `mkdir` → `cp -a dist/. web/ocap/` | PASS | `SWAP_OK`；`NEW_FILES=87` |
| B-07 本地状态 | `.env` 前后 `sha256sum` 对比 | PASS | `ENV_UNCHANGED` |
| B-08 入口核对 | 读取 `index.html` 的入口脚本 | PASS | `/ocap/assets/index-CmQu6zIY.js`（旧版为 `index-DmL9mAdT.js`） |

补充：第二次执行前有一次脚本因 `tar tzf | head` 与 `pipefail` 触发 SIGPIPE 提前退出，已确认未发生替换（旧 asset 仍为 `index-DmL9mAdT.js`、HTTP 200），改用 `sed` 后重跑成功。

## 验证结果

| 编号 | 检查项 | 实际结果 | 通过 |
|---|---|---|---|
| V-01 | 内网首页 | `IN_HTTP=200` | 是 |
| V-02 | 内网 JS 资源 | `ASSET_HTTP=200` | 是 |
| V-03 | SPA 深链 `/ocap/units` | `SPA_HTTP=200` | 是 |
| V-04 | 外网首页 | `OUT_HTTP=200` | 是 |
| V-05 | Freeark 未受影响 | `FREARK_HTTP=200` | 是 |
| V-06 | 后端存活 | `ocap-backend=active` | 是 |
| V-07 | nginx 存活 | `nginx=active` | 是 |
| V-08 | 新版本生效 | 入口 `index-CmQu6zIY.js`，`NEW_FILES=87` | 是 |
| V-09 | 角色化首屏人工核对 | 待用户用游客/业主/委员账号查看 | 未执行（非阻断） |

## 回滚记录

| ROLLBACK | 命令 | 结果 | 输出摘要 |
|---|---|---|---|
| — | 未触发 | 未执行 | 全部验证通过，无回滚 |

回滚方式（锚点保留 ≥ 7 天）：

```bash
TS=20261125134950
sudo rm -rf /home/yangyang/ocap/web/ocap
sudo tar xzf "/home/yangyang/ocap/snapshots/web-$TS.tar.gz" -C /home/yangyang/ocap
curl -s -o /dev/null -w 'ROLLBACK_HTTP=%{http_code}\n' http://127.0.0.1:8090/ocap/
```

## 当前系统状态与人工干预建议

- 测试环境 Web 已运行 `main@5a787ec` 构建产物；后端、数据库、nginx 配置与 `.env` 均未变更。
- 回滚快照 `/home/yangyang/ocap/snapshots/web-20261125134950.tar.gz` 保留；确认稳定 7 天后可清理。
- 构建临时目录 `/tmp/ocap_role_home_20261125134950` 可在确认后删除，不影响线上。
- V-09 请用三类测试账号各打开一次 Web 首页，核对角色化模块与顺序；失败按缺陷回流，不在测试机热修。

## 遗留问题

- 微信小程序仅完成构建验证，上传发布（体验版/正式版）不在本次范围，需用户通过微信开发者工具执行。
- 沙箱到目标机的 SSH 通道仍不可用（`Not allowed at this time`）；后续自动部署前需修复 frp/VPS 入口或改用 GitHub Actions 部署工作流（需另行授权）。
- 部署为“用户代执行 + PM 逐步核对”，与全自动 E2 的执行主体不同，但命令、顺序、锚点与验证项与已批准计划一致。
