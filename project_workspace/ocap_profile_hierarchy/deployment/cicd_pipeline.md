<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-21T12:17:20+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>.github/workflows/ci.yml</file>
    <file>project_workspace/ocap_profile_hierarchy/testing/unit_test_report.md</file>
    <file>project_workspace/ocap_profile_hierarchy/testing/integration_test_report.md</file>
    <file>project_workspace/ocap_profile_hierarchy/testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：个人主页信息层级与实名认证徽章

## 现状与影响

现有 CI：`.github/workflows/ci.yml`，含 3 个 job：
- `backend`：Django system check + 全量测试（`python manage.py test --settings=config.test_settings`）。
- `frontend`：主题定义检查、`npx vitest run --passWithNoTests`、生产构建。
- 小程序 job：安装依赖、vitest、`uni build -p mp-weixin`。

本次影响：仅 Web/小程序前端与测试；新增测试文件会被既有 vitest glob 自动收集。**无需修改 CI 配置**。后端无改动，`backend` job 仅作回归。

## 流水线概览

[Source] → [Lint/主题检查] → [Build] → [Unit/Integration] → [Package] → [Deploy（人工授权）] → [Smoke] → [E2E-替代]

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| P1 | Source | push / PR / 手动 | `actions/checkout@v4` | 退出码 0 | abort-and-notify |
| P2 | 主题检查 | 同 P1 | `node scripts/themes/build.mjs --strict --check` | 退出码 0 | abort |
| P3 | Build（Web） | P2 通过 | `npm ci && npm run build`（frontend） | 退出码 0，生成 `dist/` | abort |
| P4 | 测试（Web） | P3 后 | `npx vitest run --passWithNoTests` | 新增用例全过；相对基线零新增失败（基线 5 条环境失败） | abort |
| P5 | 测试（小程序） | 同 P1 | `npm ci && npx vitest run`；构建时设 `UNI_INPUT_DIR`/`UNI_OUTPUT_DIR` | 138 条通过、构建成功 | abort |
| P6 | 测试（后端回归） | 同 P1 | `python manage.py test --settings=config.test_settings` | 无新增失败 | abort |
| P7 | Package | 全部测试通过 + 用户授权 | 本地打 tar（含提交号/TS） | SHA256 已记录 | abort |
| P8 | Deploy（测试环境） | 用户本轮明确授权 | 见 `deployment_plan.md` | 每步预期命中 | 按计划回滚 |
| P9 | Smoke | P8 完成 | 只读 curl / 文件存在性检查 | 全部通过 | 触发回滚 |
| P10 | E2E-替代 | P9 通过 | 多步组件旅程用例（已在 CI P4/P5 执行） | 2/2 通过 | abort |

## 环境矩阵

| 配置项 | 测试（内网） | 测试（外网） |
|---|---|---|
| 主机 | 树莓派 192.168.31.51 | 同左，经 frp |
| 入口 | `http://192.168.31.51:8090/ocap/` | `https://ai-freeark.xin/ocap/` |
| 静态目录 | `/home/yangyang/ocap/web/dist` | 同左 |
| 后端 | systemd `ocap-backend`（本次不改、不重启） | 同左 |
| 部署方式 | tar 打包 → scp → 解包（画像 P7） | 同左 |
| 部署需确认 | 是 | 是 |

生产环境不存在（画像 P7）；不使用 Docker/容器。

## 制品管理

- 存储位置：目标机 `/home/yangyang/ocap/web/dist`（直接替换），无制品库。
- 命名：本地 `web_dist_<short-sha>_<TS>.tar.gz`；远端 `/tmp/web_dist_<short-sha>_<TS>.tar.gz`。
- 晋升条件：CI 全绿 + 用户本轮部署授权。
- 风险：目标机本地构建/直接替换，无版本目录并存；依赖锚点快照回滚（见部署计划）。
