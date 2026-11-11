<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-12T00:23:44.1229271+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>deployment/deployment_plan.md</file>
    <file>deployment/cicd_pipeline.md</file>
    <file>testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 部署报告：管理端打磨（测试环境）

## 摘要

- 目标环境：测试环境（树莓派 192.168.31.51，外网 `https://ai-freeark.xin/ocap/`）。
- 策略：recreate；部署窗口约 00:21:20 ~ 00:23:00（Asia/Shanghai），停机约 31 秒（00:21:44 停止 → 00:22:15 启动）。
- 回滚锚点：`TS=20261112002120`。
- 版本：`3825aac19010829ce901fd06be41fb50dbb8613b`（已推送 `origin/main`）。
- 总步骤：计划 8 个 DEPLOY；完成 8；失败 0；跳过 0（nginx 配置未变，未重新加载）。
- 最终状态：**DEPLOYED_SUCCESSFULLY**。

## 授权核对

- 授权来源：用户本轮消息「提交推送 部署」。
- 授权环境 = 计划环境 = 画像 P7 环境名：测试环境（测试环境“部署需用户确认=是”）。
- 计划版本：`deployment_plan.md` 1.0.0 / APPROVED（phase_status GROUP_E1 已批准）。
- 提交状态：`d8ca96f`、`3825aac` 已推送到 `origin/main`；部署制品由 `3825aac` 生成。

## 分步执行

| DEPLOY | 命令摘要 | 开始 | 耗时 | 结果 | 输出摘要 |
|---|---|---|---|---|---|
| 001 快照与备份 | tar backend/web + nginx 备份 + mysqldump + dumpdata registryunit | 00:21:20 | ~10s | SUCCESS | backend tar 28,335,841B、web tar 617,822B、SQL gz 329,175B、registry JSON 1,977,131B；SHA256 已记录 |
| 002 停止后端 | `sudo systemctl stop ocap-backend` | 00:21:44 | ~2s | SUCCESS | `inactive` |
| 003 上传后端 | `git archive 3825aac backend` → scp → tar 解包 | 00:21:50 | ~10s | SUCCESS | 两端 SHA256 一致 `64efd626…f3873d`；两个迁移文件存在；`.env`/`venv`/`var` 未覆盖 |
| 004 迁移前核对 | `manage.py registry_specific_part_preview --limit 20` | 00:22:00 | ~5s | SUCCESS | `total=5742 would_change=5742 conflicts=0 floor_omitted=24 review=27` |
| 005 数据库迁移 | `manage.py migrate --noinput` | 00:22:05 | ~8s | SUCCESS | `accounts.0003 ... OK`；`registry.0005 ... OK`；`total=5742 would_change=5742 review=27` |
| 006 启动后端 | `sudo systemctl start ocap-backend` | 00:22:15 | ~3s | SUCCESS | `active`；gunicorn 26.2.0 监听 127.0.0.1:9000；日志无 Traceback |
| 007 发布前端 | `npm run build -- --base=/ocap/` → tar → scp → sudo 替换 `web/ocap` | 00:22:30 | ~30s | SUCCESS | `index.html` 1,064B；引用 `/ocap/assets/index-CMaF0O1p.js`；目录已 chown 回 yangyang |
| 008 部署后验证 | 见下表 | 00:22:50 | ~1min | SUCCESS | 见验证结果 |

## 验证结果

| 检查项 | 实际结果 | 通过 |
|---|---|---|
| V-01 外网入口 | `https://ai-freeark.xin/ocap/` → 200 | 是 |
| V-02 后端服务 | `ocap-backend` active；启动后 10 分钟日志 Traceback 数 = 0 | 是 |
| V-03 迁移状态 | `registry 0005`、`accounts 0003` 均为 `[X]` | 是 |
| V-04 重生成幂等 | `registry_specific_part_preview` → `total=5742 would_change=0 conflicts=0 floor_omitted=24 review=27` | 是 |
| V-05 管理员偏好接口 | 未登录 `GET /api/v1/admin/me/theme` → 401（路由存在，鉴权生效） | 是（鉴权部分） |
| V-06 专有部分新格式 | DB 抽查：`圣灯路155号1层`、`建设南路142号1层`、`建设南路146号整栋` | 是 |
| V-07 搜索行为 | 由 TC-INT-422 自动化覆盖；线上待管理员登录后确认 | 部分（自动化已过） |
| V-08 导入说明 | 前端新 bundle 已发布；管理员登录后可见“后缀规则/示例” | 待用户确认 |
| V-09 前端 bundle 与入口 | index 引用 `index-CMaF0O1p.js`；该资源 HTTPS 200；`/ocap/admin/login` 200 | 是 |
| V-10 人工视觉走查 | 待用户执行 M-01~M-05 | 待人工 |
| Freeark 未受影响 | `https://ai-freeark.xin/` → 200；8080 正常；无 failed units | 是 |
| 端口归属 | 9000/8090 属 ocap；8000/8080 属 Freeark | 是 |
| timer | `ocap-run-due-jobs.timer` enabled / active | 是 |

## 偏差与异常

1. **前端目录属主为 root**：首次 `rm` 因权限失败（旧产物未变动），改用 `sudo rm/tar` 并 `chown -R yangyang:yangyang /home/yangyang/ocap/web/ocap` 后成功；后续部署可直接由 yangyang 清理。
2. **SSH 通道短暂中断**：迁移后一次长命令连接被关闭；改为分步短命令重试后恢复，未影响部署状态。已核验服务与数据。
3. **nginx 配置未变**：未执行 reload，Freeark 与 ocap 入口均正常。

## 回滚参考

- 锚点 `TS=20261112002120`；快照位于 `/home/yangyang/ocap/snapshots/`：
  - `backend-20261112002120.tar.gz`
  - `web-20261112002120.tar.gz`
  - `ocap-20261112002120.sql.gz`
  - `registry-units-20261112002120.json`
  - nginx 备份 `/etc/nginx/sites-available/ocap.bak_20261112002120`、`freeark.bak_20261112002120`
- 如需回滚：停服务 → `migrate registry 0004`、`migrate accounts 0002`（数据迁移标 MANUAL_ROLLBACK_REQUIRED）→ 解包 backend 快照 → 启动 → 解包 web 快照。

## 遗留问题

- 人工视觉走查 M-01~M-05（15 页 × 3 风格、OQ-11 高亮形态、窄屏 44px、减少动态效果）待用户完成。
- V-07/V-08 需管理员登录后目视确认；自动化测试已覆盖。
- CR-301/302/305 等非阻断项见交付报告。
