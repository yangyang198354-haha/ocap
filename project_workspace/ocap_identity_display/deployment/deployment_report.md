<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-14T19:55:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/deployment/deployment_plan.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>DEPLOYED_SUCCESSFULLY</status>
</file_header>

# 部署报告：用户端身份显示与认证房屋信息

## 摘要

- 目标环境：测试环境（树莓派 `192.168.31.51`，内网 8090 / 外网 `https://ai-freeark.xin/ocap/`）
- 策略：recreate（单实例）
- 开始/结束：2026-11-14 19:49:43 ~ 19:52（Asia/Shanghai）
- 回滚锚点：`20261114194943`
- 总步骤：计划 DEPLOY-001~009，执行 6 步，跳过 3 步（DEPLOY-007/008 nginx 未变更；DEPLOY-009 timer 已于既有部署安装），失败 0
- 最终状态：**DEPLOYED_SUCCESSFULLY**

## 授权核对

- 授权来源：用户本轮消息“commit + push + 部署”。
- 授权环境：测试环境（画像 P7 唯一存在的环境；生产环境不存在）。
- 计划版本：deployment_plan.md 1.0.0 / APPROVED，与 phase_status 一致。

## 分步执行

| DEPLOY | 命令摘要 | 结果 | 输出摘要 |
|---|---|---|---|
| 001 快照 | tar backend/web + nginx 备份 | SUCCESS | `ANCHOR_TS=20261114194943`；backend 28,366,035 B、web 620,390 B |
| 002 后端上传 | tar → scp → 解包 | SUCCESS | `BACKEND_UPLOADED`；`area_display` 命中 1 |
| 003 依赖 | `pip install -r requirements.txt` | SUCCESS | 全部 `Requirement already satisfied` |
| 004 迁移 | `manage.py migrate --noinput` | SUCCESS | `No migrations to apply.` |
| 005 重启 | `systemctl restart ocap-backend` | SUCCESS | `active`；gunicorn 26.2.0 正常启动 |
| 006 前端 | `npm run build -- --base=/ocap/` → scp → 替换 | SUCCESS | `✓ built in 8.02s`；`WEB_DEPLOYED`；assets 以 `/ocap/assets/` 开头 |
| 007/008 nginx | — | SKIPPED | 本次无 nginx 配置变更 |
| 009 timer | — | SKIPPED | `ocap-run-due-jobs*` 已安装（TIMER_COUNT=2），本次未改动 |

## 验证结果

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| 后端存活 | `active` | 是 |
| 后端日志 Traceback 计数 | `0` | 是 |
| 管理端登录接口 | `ADMINLOGIN=400`（错误凭据，非 5xx） | 是 |
| 内网前端 | `INNER_INDEX=200` | 是 |
| 内网静态 | `INNER_ASSET=200` | 是 |
| 外网前端 | `OUTER_INDEX=200` | 是 |
| 外网静态 | `OUTER_ASSET=200` | 是 |
| SPA 回退 | `SPA_FALLBACK=200` | 是 |
| Freeark 基线 | `FREEBASE=200` | 是 |
| 失败单元 | `freeark/ocap` 失败数 `0` | 是 |
| 身份与房屋冒烟 | `LABELS ['产权业主']`；`UNIT_SAMPLE 1栋1单元9层902号 住宅 88.50 ㎡ 产权业主`；unit 字段 8 个齐全 | 是 |

## 回滚记录

未触发回滚。回滚方式见 deployment_plan.md ROLLBACK-004~001，锚点 `20261114194943`。

## 遗留问题

- 目标机 `migrate` 输出提示 `content` app 存在未生成迁移的模型变更。该提示与本次改动无关（本次未改 `content`），为既有漂移；不影响本次身份/房屋功能。建议另立需求处理，避免下次部署误判。
- 小程序包未发布（RU-4），需用户在微信开发者工具构建发布。
- 已知缺口沿用：目标机无 git，回滚依赖 tar 快照；测试环境短信为 console 替身。

## 当前系统状态

后端、Web 前端均已更新至提交 `58558da` 对应版本；服务运行正常，外网可访问。
