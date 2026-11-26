<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-27T06:55:00+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_typography_unify/architecture/tech_stack.md</file>
    <file>project_workspace/ocap_typography_unify/testing/e2e_test_report.md</file>
    <file>.trae/sdlc/project_profile.md</file>
    <file>.trae/skills/ocap-deploy/SKILL.md</file>
    <file>.github/workflows/ci.yml</file>
  </input_files>
  <phase>PHASE_10</phase>
  <status>APPROVED</status>
</file_header>

# CI/CD 流水线 — Web 端字体与标题统一

## 现状与影响

现有 CI：`.github/workflows/ci.yml`，含两个 job：
- `Backend (Django tests)`：`manage.py check` + `manage.py test`（MySQL 测试库）。**本次无后端改动，不受影响。**
- `Web frontend (vitest + build)`：`npm ci` → `node scripts/themes/build.mjs --strict --check`（主题生成态漂移校验）→ `npx vitest run --passWithNoTests`。

本次改动对 CI 的影响：

| 改动 | 对 CI 的影响 | 是否需改 CI |
|---|---|---|
| 新增测试 `frontend/tests/typography_tokens.spec.js`（9 项） | 被既有 `npx vitest run` 自动覆盖（P4 vitest 聚合，`--passWithNoTests`） | 否 |
| 生成态 `frontend/src/theme/generated/themes.css` 重建 | 由既有 `build.mjs --strict --check` 校验源==生成态，已本地重建一致 | 否 |
| 无新增第三方依赖（`package.json` 未变） | `npm ci` 不受影响 | 否 |
| 无新服务、无新环境变量、无新测试层目录 | — | 否 |

结论：**无需修改 CI**。唯一风险：预存失败 `product_review_ui.spec.js` TC-UNIT-577 在 CI 上同样存在（基线即失败），与本次改动无关；不属本次引入，留待后续单独修复（CR-404）。

## 流水线概览

```
[Source push/PR]
  → [Theme check: build.mjs --strict --check]
  → [Install: npm ci]
  → [Test: vitest run（单元+集成+E2E 一次聚合）]
  → [Build: Vite --base=/ocap/]
  → [Package: frontend_dist.tar.gz]
  → [Deploy: 测试环境 192.168.31.51 静态替换]（需用户授权，手动触发）
  → [Smoke: 部署后验证清单]
```

## 阶段定义

| PIPE | 阶段 | 触发条件 | 命令 | 成功标准 | 失败处理 |
|---|---|---|---|---|---|
| PIPE-01 | Source | push / PR 到 main | — | 提交在远端 | abort |
| PIPE-02 | Theme check | PIPE-01 | `node scripts/themes/build.mjs --strict --check`（frontend 工作目录经 CI 配置） | 退出码 0，无漂移 | abort-and-notify |
| PIPE-03 | Install | PIPE-02 | `npm ci`（frontend） | 退出码 0 | abort-and-notify |
| PIPE-04 | Test | PIPE-03 | `npx vitest run --passWithNoTests`（frontend） | 相对基线零新增失败（预存 TC-UNIT-577 除外） | abort-and-notify |
| PIPE-05 | Build | PIPE-04 | `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`（frontend） | 退出码 0，产物含统一标题文案 | abort-and-notify |
| PIPE-06 | Package | PIPE-05 | `tar -czf frontend_dist.tar.gz -C frontend/dist .` | 生成 tar 包 | abort-and-notify |
| PIPE-07 | Deploy（测试环境） | 手动，需用户授权 | 见 deployment_plan DEPLOY-001~004 | 静态替换成功 | 失败逆序回滚 |
| PIPE-08 | Smoke | PIPE-07 | 部署后验证清单 | 全部通过 | 部分失败→评估回滚 |

> 禁止"跳过失败继续部署"。测试失败只允许 abort-and-notify。

## 环境矩阵

| 配置项 | 测试环境（画像 P7 唯一环境） |
|---|---|
| 地址 | `192.168.31.51:8090`（nginx）；外网 `https://ai-freeark.xin/ocap/`（经 Freeark frp） |
| 实例数 | 1（单实例静态站点） |
| 资源 | 树莓派；磁盘 ≥2G、内存 ≥500M（预检阈值） |
| 外部依赖 | 后端 gunicorn `127.0.0.1:9000`（本次不变）；MySQL `192.168.31.98:3306`（本次不变） |
| 配置来源 | 前端构建期 `VITE_API_BASE=/ocap/api/v1`、`--base=/ocap/`；后端 `.env`（本次不触碰） |
| 部署需确认 | 是（每次均需用户明确授权；画像 P7） |

> 画像 P7 无 staging / 生产环境，故不设计晋升流程。

## 制品管理

- **存储位置**：开发机构建 `frontend/dist` → 打包 `frontend_dist.tar.gz` → scp 到目标机 `/tmp/`；目标机静态目录 `/home/yangyang/ocap/web/ocap`。
- **命名**：快照按时间戳 `web-$TS.tar.gz` 存于 `/home/yangyang/ocap/snapshots`（回滚锚点）；静态替换用 `ocap.new_$TS` → `ocap.old_$TS` 交换并保留旧目录（记忆 M-DE-046）。
- **晋升条件**：无多环境晋升；测试环境部署后验证通过即完成。
- **构建方式**：目标机无 git，采用"开发机本地构建 + 上传产物 + 目标机静态替换"（记忆 M-DE-018）。风险：产物正确性依赖本地构建命令与 `VITE_API_BASE`/`--base` 参数，须按 M-DE-047 在产物中 grep 关键文案佐证。
