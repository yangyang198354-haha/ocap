<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-20T00:32:00+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>deployment/deployment_plan.md</file>
    <file>deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：ocap_profile_ux（测试环境）

## 摘要

- 目标环境：测试（树莓派 192.168.31.51；MySQL 库 `ocap`）。接入方式：内网 SSH 22。
- 线上变更窗口：2026-11-20T00:28:32+08:00（DEPLOY-001 锚点）至 2026-11-20T00:30:10+08:00。
- 回滚锚点：`TS=20261120002832`。四份制品已核验存在且非空：`snapshots/backend-20261120002832.tar.gz`、`snapshots/web-20261120002832.tar.gz`、`sites-available/ocap.bak_20261120002832`、`sites-available/freeark.bak_20261120002832`。
- 版本标识：本地 HEAD = `origin/main` = `7756f4345cea0553dd7d7c70e9a2b88d478ed3f2`；工作树仅剩未跟踪的小程序构建物与本地产物（未入库）。
- 步骤：计划 9 个；执行 7 个（DEPLOY-001~006、009）；跳过 2 个（DEPLOY-007/008：nginx 配置无改动）；失败 0；回滚 0。
- 验证：V-01~V-12 全部通过。
- **最终状态：DEPLOYED_SUCCESSFULLY**（MV-01~MV-04 人工验收仍待在测试环境执行）。

## 授权核对

- 用户本轮原话：“那就就 提交，推送， CI 全绿后授权部署到测试环境”。
- 环境 = “测试环境” = 画像 P7 的测试环境（192.168.31.51 / https://ai-freeark.xin/ocap/）；授权带前置条件“CI 全绿”。
- 前置条件核验：CI run `44566113275`（head `7756f43`）三个作业全部 success（Backend、Web frontend vitest+build、Mini program）。
- 说明：首个提交 `2f522a0` 的 CI 因新增“我的主页”菜单项破坏既有 8 项菜单契约而失败；已回退该菜单项并在 `7756f43` 重新推送，CI 全绿后才执行部署。

## 预检结果

| 项 | 实际结果 | 通过 |
|---|---|---|
| 1 版本标识 | HEAD=`7756f43`，已推送并与远端一致 | 是 |
| 2 磁盘 | `/home` 可用 16G | 是 |
| 3 内存 | available 1549 MB | 是 |
| 4 端口归属 | 80/8000/8080 属 Freeark；8090/9000 属 ocap | 是 |
| 5 目标机目录 | 仅 `backend/`、`web/`、`snapshots/` | 是 |
| 6 env 文件 | `ENV_OK`（未读取内容） | 是 |
| 7 迁移漂移 | 本地 `makemigrations --check` 无变更 | 是 |
| 8 依赖可装 | `pip install --dry-run` 全部已满足 | 是 |
| 9 迁移状态 | 部署前未应用 0 条；解包后新增 `accounts.0004` 1 条，随 DEPLOY-004 应用 | 是 |
| 10 nginx 语法 | syntax ok / test successful | 是 |
| 11 Freeark 基线 | 8080 → 200 | 是 |
| 12 SECRET_KEY / ALLOWED_HOSTS | 均非空（`SECRET_KEY_SET`、`HOSTS_SET`） | 是 |
| 13 timer 单元 | **偏差**：`ocap-run-due-jobs.{service,timer}` 已存在且 enabled/active（计划预期不存在），DEPLOY-009 按幂等重装处理 | 偏差已记录 |

## 执行步骤

| 步骤 | 结果 | 说明 |
|---|---|---|
| DEPLOY-001 | SUCCESS | 生成 2 份 tar 快照 + 2 份 nginx 备份，锚点 `20261120002832` |
| DEPLOY-002 | SUCCESS | 后端整包 tar 上传解包；`0004_user_profile_fields.py` 已落盘；`.env` 保留 |
| DEPLOY-003 | SUCCESS | 依赖全部已满足（dry-run 与实装均退出 0） |
| DEPLOY-004 | SUCCESS | `Applying accounts.0004_user_profile_fields... OK`；迁移前计划存于 `/tmp/mig_pre_deploy.txt` |
| DEPLOY-005 | SUCCESS | `ocap-backend` active；gunicorn 26.2.0 启动，4 worker，无 Traceback |
| DEPLOY-006 | SUCCESS | 前端 `VITE_API_BASE=/ocap/api/v1`、`--base=/ocap/` 构建通过；`web/ocap` 全量替换 |
| DEPLOY-007/008 | SKIPPED | nginx 配置本次无改动，无需 reload |
| DEPLOY-009 | SUCCESS | 重装 timer 单元，`systemd-analyze verify` 通过，enabled + active，NEXT 正常 |

## 部署后验证

| 编号 | 检查 | 实际结果 |
|---|---|---|
| V-01 | 后端存活 | active |
| V-02 | 后端日志 | 近 6 分钟 Traceback 计数 0 |
| V-03 | 错误凭据登录 | `LOGIN:400` |
| V-04 | 新接口鉴权 | `GET /api/v1/users/1/profile` → 401 |
| V-05 | 迁移状态 | `accounts.0004_user_profile_fields` 为 `[X]` |
| V-06 | 内网前端 | `WEB:200 text/html` |
| V-07 | SPA 回退 | `/ocap/admin/login` → 200 |
| V-08 | 内网主资源 | `assets/index-FOHQlGou.js` → 200，1,152,477 B |
| V-09 | 外网前端 | `https://ai-freeark.xin/ocap/` → 200 |
| V-10 | 外网主资源 | 同主资源 → 200，1,152,477 B（与内网一致） |
| V-11 | Freeark 未受影响 | 8080 → 200；无失败 systemd 单元 |
| V-12 | timer 手动执行 | `Result=success`、`ExecMainStatus=0`（真实执行到期任务） |

## 偏差与风险

1. 预检第 13 项偏差：timer 单元在部署前已存在并启用；本次按幂等重装，ROLLBACK-009 仍可卸载，但“严格逆操作”的前提不成立（回滚会移除部署前已存在的 timer）。已记录，交由用户决定是否接受。
2. DEPLOY-004 属 `[MANUAL_ROLLBACK_REQUIRED]`：回滚 `accounts.0004` 会删除 `signature`、`real_name_visible` 两列及其数据。
3. DEPLOY-009 手动执行一次 timer 已真实运行到期任务/清理，该副作用不随回滚撤销。
4. 回滚可用性：锚点 `20261120002832` 的 4 份制品已核验；如后续需要回滚，按 deployment_plan §7 逆序执行（004 → 002 → 005，再 006/007/009）。

## 人工验收（待执行）

- MV-01：个人资料页四控件同一水平线；生日控件不再偏低。
- MV-02：默认头像在右上角与个人资料页正常显示；更换 4.9MB 头像成功、5.1MB 被拦截。
- MV-03：管理端席位表格 10 列、楼栋/单元/职位过滤、失效折叠条数与展开内容正确；房屋关系姓名（含同住人）/电话后四位/专有部分搜索正确。
- MV-04：他人 profile 页可访问且不泄露敏感字段；已验证产权业主（含业委会成员）可开启实名展示；签名档保存与展示正常。
