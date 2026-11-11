<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-11T22:48:52.4163452+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>development/implementation_plan.md</file><file>testing/integration_test_report.md</file><file>../ocap_content_publish/deployment/cicd_pipeline.md</file></input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 CI/CD（增量）

## 现状与影响

- 现有 CI：`.github/workflows/ci.yml`，三个 job：Backend（Django check + 全量测试）、Web frontend（主题生成物检查 + vitest + 构建）、Mini program（vitest）。
- 本次改动影响：
  - 后端新增 `apps/accounts/directory.py`，修改 `serializers.py`、`views.py`；新增测试 9 个集成 + 1 个 E2E。测试计数从 520 增至 530，CI 命令无需修改。
  - 前端修改 `AdminUsers.vue`、`format.js`，新增 `tests/admin_users.spec.js`（2 个用例）；CI vitest 自动包含，命令无需修改。
  - 无新依赖、无迁移、无新环境变量、无新服务。
- **结论：不需要修改 `.github/workflows/ci.yml`。** 前端 2 个主题用例在 Windows 开发机因 CRLF / `/tmp` 失败；CI 为 Linux，历史上主题检查通过，本次以 CI 实际结果为准。

## 流水线概览

[Source] → [Django check] → [Backend 全量测试] → [Frontend 安装] → [主题生成物检查] → [Frontend 测试] → [Frontend 构建] → [Mini program 测试]

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | 后端静态检查 | push / PR / 手动 | `cd backend && python manage.py check --settings=config.test_settings` | 退出码 0，`no issues` | abort-and-notify |
| PIPE-02 | 后端全量测试 | 同上，依赖 PIPE-01 | `cd backend && python manage.py test --settings=config.test_settings -v 2` | 退出码 0；本次基线 530 tests OK（9 skipped） | abort-and-notify；禁止跳过失败继续部署 |
| PIPE-03 | 前端安装 | 同上 | `cd frontend && npm ci` | 退出码 0 | abort-and-notify |
| PIPE-04 | 主题生成物检查 | 同上，依赖 PIPE-03 | `node scripts/themes/build.mjs --strict --check` | 退出码 0 | abort-and-notify |
| PIPE-05 | 前端测试 | 同上 | `cd frontend && npx vitest run --passWithNoTests` | 退出码 0；本次新增 2 个用例 | abort-and-notify |
| PIPE-06 | 前端构建 | 同上 | `cd frontend && npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） | 退出码 0，产出 `dist/` | abort-and-notify |
| PIPE-07 | 小程序测试 | 同上 | `cd miniprogram && npm install --legacy-peer-deps && npx vitest run --passWithNoTests` | 退出码 0；基线 75 passed | abort-and-notify |

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机 | 树莓派 192.168.31.51（用户 yangyang，免密 SSH） | 同一主机，经 VPS + frp |
| 访问入口 | `http://192.168.31.51:8090/ocap/` | `https://ai-freeark.xin/ocap/` |
| 后端服务 | `ocap-backend`，gunicorn 127.0.0.1:9000 | 同上 |
| 数据库 | MySQL 192.168.31.98:3306 库 `ocap` | 同上 |
| 部署需用户确认 | 是 | 是 |

生产环境不存在（画像 P7），不设计晋升。

## 制品管理

- 后端制品：用户确认提交并推送到 `origin/main` 后，用 `git archive <commit>:backend` 生成 tar.gz（只含已跟踪文件，不含 `.env`、`venv`、`var`）。
- 前端制品：开发机 `npm ci` + `npm run build -- --base=/ocap/` 生成 `dist/`，打 tar.gz。
- 存储：目标机 `/home/yangyang/ocap_snapshots/<锚点>/` 保留回滚快照；无独立制品库。
- 风险：目标机无 git，版本以 tar SHA256 + 部署报告中的 commit 号定位；不得用未提交工作区打包。
