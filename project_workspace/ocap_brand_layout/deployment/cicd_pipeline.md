<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-17T09:21:10+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/e2e_test_report.md</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线：品牌更名 Cyber@红枫岭 + Web 左侧导航布局（INCREMENTAL，仅前端/小程序/风格生成物）

> 结论先行：**`.github/workflows/ci.yml` 无需修改**（本文件不改它）。本批没有新增依赖、服务、环境变量或新的测试层，新增的 11 个 Web 前端 spec 与 1 个小程序 spec 已被现有 vitest 命令的 `tests/**/*.spec.js` 匹配收集；CI 只跑测试与构建、不部署（画像 P7）。

## 现状与影响

现有 CI：`.github/workflows/ci.yml`，GitHub Actions，触发 `push`/`pull_request` 到 `main` 与 `workflow_dispatch`，`concurrency` 取消同分支旧运行，`permissions: contents: read`。三个 job：

| job | 工作目录 | 步骤 |
|---|---|---|
| backend | `backend/` | Python 3.13、装 MySQL 客户端构建依赖、`pip install -r requirements.txt`、`manage.py check --settings=config.test_settings`、`manage.py test --settings=config.test_settings -v 2` |
| frontend | `frontend/` | Node 20、`npm ci`、`node scripts/themes/build.mjs --strict --check`（工作目录 `.`）、`npx vitest run --passWithNoTests`、`npm run build -- --base=/ocap/`（`VITE_API_BASE=/ocap/api/v1`） |
| miniprogram | `miniprogram/` | Node 20、`npm install --no-audit --no-fund --legacy-peer-deps`、`npx vitest run --passWithNoTests` |

本次改动对 CI 的影响逐项核对：

| 项 | 影响 | 依据 |
|---|---|---|
| 新增依赖 | 无。`git status --short -- frontend/package.json frontend/package-lock.json miniprogram/package.json backend/requirements.txt` 输出 0 行；品牌字体为随包 woff2 文件，不是 npm 依赖（ADR-123 方案 A） | 本地只读核对 2026-11-17 |
| 新测试层 | 无。新增 spec 位于 `frontend/tests/`（11 个，`git status` 未跟踪：admin_session、auth_shell、brand、layout_contract、layout_css、layout_e2e、layout_menus、layout_nav、layout_pages、layout_router、user_menu）与 `miniprogram/tests/brand_login.spec.js`，均被 vitest `include: tests/**/*.spec.js` 收集 | `git ls-files --others` |
| 新服务 / 环境变量 | 无 | module_design「受影响的运行单元」 |
| 风格生成物漂移检查 | **已被覆盖**：本批改了 `themes/*.theme.json|web.css|mp.css`，CI 的 `node scripts/themes/build.mjs --strict --check` 会校验生成物（`frontend/src/theme/generated/*`、`miniprogram/theme/generated/*`）与定义一致。本地实测退出码 0 | 本地运行 2026-11-17 |
| 构建 | `npm run build -- --base=/ocap/` 会把 `frontend/src/brand/fonts/OcapBrand-subset.woff2` 打成带哈希产物；CI 已设 `VITE_API_BASE=/ocap/api/v1` | ci.yml:78-81 |
| 后端 job | 不受影响（后端零改动）。画像 P4 登记的 1 条既有失败（`test_tc_int_311_downloaded_template_imports_back`）若仍存在，属既有，不计入本批 | 画像 P4 |
| 运行时长 | 前端 vitest 由 26 个文件/281 条增至 37 个文件/438 条；本机实测整套约 200 秒（含 jsdom 初始化），CI 无超时设置，GitHub Actions 默认 6 小时上限足够，无需改动 | 本地实测 |

不改 CI 的理由：现有三个 job 已覆盖本批全部可自动化的质量门（风格漂移、前端 438 条、小程序 119 条、构建）。

**可选改进（不属本次改动，不修改文件，留给用户决定）**：
1. 在 frontend job 的构建步骤后加一行断言 `ls dist/assets/OcapBrand-subset-*.woff2`，防止字体被误删后构建仍通过（当前由 `brand.spec.js` 与 Vite 对缺失 `url()` 的构建报错间接保证）。
2. CI 不构建小程序（`npm run build:mp-weixin` 在本机基线即失败，GR-C-001-F04；微信发布不在画像 P7 内），小程序只做 vitest；如要补，须先修复工具链，另批处理。
3. `frontend/tests/layout_contract.spec.js` 只读 `api.js` 两份契约文件，不依赖 git 历史，浅克隆不影响（本地读文件实现，未跑 CI 验证）。

## 流水线概览

```
[Source push/PR → main]
  ├─ backend:     Checkout → Python 3.13 → 依赖 → check → test（本批无变化）
  ├─ frontend:    Checkout → Node 20 → npm ci → 风格漂移检查 → vitest → build（--base=/ocap/，含 woff2）
  └─ miniprogram: Checkout → Node 20 → npm install → vitest
                                         ↓（全部绿 + 用户确认）
[Deploy 测试环境：不在 CI 内，按 ocap-deploy skill 人工/E2 执行，见 deployment_plan.md] → [部署后只读冒烟] → [MV-01~05 人工验收]
```

画像 P7：CI 只跑测试与构建，不部署；E2E 在本项目为 jsdom 整 App 旅程（`layout_e2e.spec.js`）已含在 frontend 的 vitest 中，远程 HTTP E2E（P4-1）只在部署后由 E2 执行，本批后端无变化，不适用（见 deployment_plan）。

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR 到 `main`；手动 `workflow_dispatch` | `actions/checkout@v4`（默认浅克隆） | 检出成功 | abort-and-notify（GitHub 默认通知提交者） |
| PIPE-02 | Backend 静态检查 + 单元/集成 | 同 PIPE-01 | `python manage.py check --settings=config.test_settings`；`python manage.py test --settings=config.test_settings -v 2`（`backend/`） | 退出码 0；既有失败按画像 P4 单列 | abort-and-notify，后续 job 不依赖它（三个 job 并行），任一失败即 PR 红 |
| PIPE-03 | Frontend 风格漂移检查 | 同上 | `node scripts/themes/build.mjs --strict --check`（仓库根） | 退出码 0（定义校验通过、对比度 ≥4.5、生成物无漂移） | abort-and-notify；修复方式：本地重跑 `node scripts/themes/build.mjs --strict` 并提交生成物 |
| PIPE-04 | Frontend Unit + Integration + jsdom E2E | 同上 | `npx vitest run --passWithNoTests`（`frontend/`） | 退出码 0；本批基线 37 个文件 / 438 条全绿（`--passWithNoTests` 不再掩盖缺口：此前已知缺口 M-DE-004 因前端已有用例而不适用） | abort-and-notify；不重试（非偶发） |
| PIPE-05 | Frontend Build | PIPE-04 成功 | `npm run build -- --base=/ocap/`，环境 `VITE_API_BASE=/ocap/api/v1`（`frontend/`） | 退出码 0；产物含 `OcapBrand-subset-*.woff2`；大 chunk 体积提示不算失败 | abort-and-notify |
| PIPE-06 | Mini program Unit | 同 PIPE-01 | `npx vitest run --passWithNoTests`（`miniprogram/`，依赖 `--legacy-peer-deps`） | 退出码 0；本批基线 16 个文件 / 119 条全绿 | abort-and-notify |
| PIPE-07 | Package / 制品 | **不在 CI 内**：目标机部署由 E2 在开发机本地构建打包 | `VITE_API_BASE=/ocap/api/v1 npm --prefix frontend run build -- --base=/ocap/`；`tar -czf <SCRATCH>/frontend_dist.tar.gz -C frontend/dist .` | 见 deployment_plan DEPLOY-002（两端 SHA256 一致） | 失败即停止，目标机无变更 |
| PIPE-08 | Deploy 测试环境 | 用户当轮授权 + PM 写入 `PRODUCTION_DEPLOY_CONFIRM=true` 与环境名「测试」（画像 P7：部署需用户确认=是） | 见 deployment_plan DEPLOY-001~005 | 见 deployment_plan | abort-and-rollback（逆序 ROLLBACK），不得"跳过失败继续部署" |
| PIPE-09 | 部署后冒烟 | PIPE-08 成功 | 只读 HTTP 与目标机只读命令，见 deployment_plan「部署后验证」 | 全部项有实际结果且达标 | 部分失败 → `DEPLOYED_WITH_ISSUES`，由用户决定是否回滚；不自动重试写操作（只读检查可重试至多 3 次，间隔数秒，用于网络抖动） |
| PIPE-10 | E2E / 人工验收 | PIPE-09 之后，由用户执行 | MV-01~05（e2e_test_report 人工验证清单），见 deployment_plan | 用户逐项确认 | 未完成则交付状态至多 DELIVERED_WITH_ISSUES（GR-D-002-F01） |

## 环境矩阵

只列画像 P7 中存在的环境：**测试**。生产为"无"，不设计晋升。

| 配置项 | 测试 |
|---|---|
| 主机 | 树莓派 `raspberrypi`；外网 SSH `-p 57279 yangyang@47.109.197.217`（VPS + frp，密钥认证，ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk`）；内网 `yangyang@192.168.31.51:22` |
| 实例数 | 后端 gunicorn 单实例 `127.0.0.1:9000`；nginx 8090；Freeark 反代 `^~ /ocap/` |
| 本批变更的运行单元 | 仅 Web 静态目录 `/home/yangyang/ocap/web/ocap`；后端/DB/systemd/nginx 配置不变 |
| 资源 | 磁盘/内存下限沿用 ocap-deploy 预检：/home 可用 ≥ 2 GB、可用内存 ≥ 500 MB（静态包约 2.3 MB，远小于下限） |
| 外部依赖 | MySQL 库 `ocap`（不触碰）；本批不涉及任何外部 API（P11-3） |
| 配置来源 | 构建期：`VITE_API_BASE=/ocap/api/v1`（命令行环境变量，非凭据）；运行期 `backend/.env`（不触碰、不读取） |
| 访问入口 | 内网 `http://192.168.31.51:8090/ocap/`；外网 `https://ai-freeark.xin/ocap/` |
| 部署需确认 | 是 |
| 数据库 | 无变更、无迁移 |

## 制品管理

- 画像无制品库。制品 = 开发机本地构建的 `frontend_dist.tar.gz`（`frontend/dist` 内容），上传到目标机 `/tmp/` 后解包到 `web/ocap`；**不是**目标机本地构建，因此目标机不需要 Node。
- 命名与版本标识：`frontend_dist.tar.gz` 本身不含版本号，版本标识 = 本地 `git rev-parse HEAD` + `git status --short` 摘要 + tar 的 SHA256（两端一致）。**本批改动尚未提交**（HEAD=`3df752be…` 之上有未提交的 44 个修改、1 个暂存删除、20 个未跟踪项，PM 提交前部署），所以 HEAD 不能单独定位版本；E2 必须记录 tar SHA256 与 `frontend/dist/index.html` 引用的入口文件名（`index-*.js`、`index-*.css`）。建议用户部署验证后提交（push 另需同意，画像 P9）。
- 回滚制品：目标机 `snapshots/web-<TS>.tar.gz`（DEPLOY-001 生成，保留 ≥ 7 天）。
- 晋升条件：无多环境晋升；进入部署的条件 = PIPE-03/04/05/06 在本机全绿（deployment_plan 预检 PRE-01~PRE-06）+ 用户当轮授权。
- 风险（"开发机构建、未入库制品"）：同一提交在不同机器构建的 chunk 哈希可能不同；构建环境变量不同会改变产物（实测：缺 `VITE_API_BASE` 时产物把接口前缀写成 `/api/v1`，目标机上会全部 404，见 deployment_plan 预检 PRE-05），因此命令必须带 `VITE_API_BASE=/ocap/api/v1`。
- 小程序：不产出部署制品，不在本流水线内（微信开发者工具构建/预览，MV-03）。
