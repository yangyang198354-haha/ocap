# devops-engineer 项目记忆 — ocap_registry_import

> TRAE 不自动注入记忆：本文件由对应 `sdlc-*` 技能在开始时**显式 Read**。
> 只允许 agent 自己追加「待验证」区；「已验证」「用户偏好与禁止项」由 kb-curator 维护。

## 已验证
- [M-DE-006] 无 git 的目标机部署，锚点应记录本地 HEAD + 工作树状态 + tar SHA256，仅时间戳不足以定位版本 — conf 0.6 · 证据 GR-E1-001 / DEPLOY-004 两端 SHA256 一致 · 首见 2026-11-10 · 命中 1
- [M-DE-007] 大文件上传/长任务上线前必须核实 gunicorn `--timeout` 与 nginx `client_max_body_size`/`proxy_read_timeout`，避免 413/504 — conf 0.8 · 证据 GR-B-001-F01 / DEPLOY-003 实测 60→90 / GR-E2-001 · 首见 2026-11-10 · 命中 1
- [M-DE-008] 目标测试 MySQL 使用自签证书，mysqldump 需 `--skip-ssl`（Django 侧 `DB_SSL_DISABLED=1`） — conf 0.6 · 证据 DEPLOY-002 输出 DUMP_EXIT=0（91 行） · 首见 2026-11-10 · 命中 1
- [M-DE-015] 无迁移的只读页面增量，回滚重点是前端静态目录与后端源码快照；新增文件在旧代码中无引用，回滚时可保留 — conf 0.6 · 证据 GR-E1-001 / deployment_plan ROLLBACK-001~004 · 首见 2026-11-11 · 命中 1
- [M-DE-016] 数据迁移上线前先跑只读预览命令，把 conflicts=0 作为 migrate 门控；停服务窗口内完成上传、预检、迁移与启动 — conf 0.6 · 证据 GR-E1-001 / deployment_plan DEPLOY-002~005 · 首见 2026-11-11 · 命中 1
- [M-DE-017] 可逆数据迁移的反向仍可能因迁移后新增数据而冲突：标 MANUAL_ROLLBACK_REQUIRED，并准备 JSON 与整库两级备份 — conf 0.6 · 证据 GR-E1-001 / deployment_plan ROLLBACK-005、DEPLOY-001 · 首见 2026-11-11 · 命中 1
- [M-DE-018] 无迁移的展示层增量可用“快照 → 后端解包重启 → 前端静态替换”四步部署，回滚按逆序用同一时间戳锚点恢复 — conf 0.8 · 证据 GR-E1-001 / GE1-2 / E2 部署成功、锚点 20261114194943 · 首见 2026-11-14 · 命中 1
- [M-DE-044] CI 全量测试 job 已覆盖新增测试目录时无需改 CI；只需确认 Windows 与 Linux 的既有失败差异 — conf 0.6 · 证据 ocap_profile_ux-GROUP_E1-1-1 / .github/workflows/ci.yml:48-49 · 首见 2026-11-19 · 命中 1
- [M-DE-045] 无令牌大文件 POST 同时打内网与反代入口，可用 401/413 无写入验证 nginx client_max_body_size — conf 0.6 · 证据 ocap_batch_1118-GROUP_E2-001-2 / deployment_report V-17 · 首见 2026-11-18 · 命中 1
- [M-DE-046] ocap 测试环境 Web 静态目录是 `/home/yangyang/ocap/web/ocap`；替换用 `ocap.new` → `ocap.old` 交换并保留旧目录，`web/dist` 是错误路径 — conf 0.8 · 证据 ocap_profile_hierarchy DEPLOY-001~004 / ocap_approval_flow DEPLOY-009 `WEB_SWAPPED`、文件数 1539 · 首见 2026-11-21 · 命中 2
- [M-DE-047] 纯前端增量发布前确认构建命令含 `VITE_API_BASE=/ocap/api/v1` 与 `--base=/ocap/`，并在产物中 grep 关键文案作为制品正确性证据 — conf 0.8 · 证据 ocap_profile_hierarchy `built in 5.20s` / ocap_approval_flow `built in 8.40s`、文案各命中 4 · 首见 2026-11-21 · 命中 2
- [M-DE-048] 本仓库小程序根目录即 uni-app 项目根（`manifest.json` 在 `miniprogram/`，无 `src/`）；`npm run build:mp-weixin` 必须显式设 `UNI_INPUT_DIR=<repo>\miniprogram`，可配合 `UNI_OUTPUT_DIR` 输出到临时目录 — conf 0.8 · 证据 ocap_approval_flow E1/E2 两次 `DONE Build complete.`、`APP_JSON_OK` · 首见 2026-11-22 · 命中 2
- [M-DE-049] 审批步骤迁移回滚门控：存在多步流程、`ALL` 策略、`ApprovalStepState.step_order>1` 或部署后产生的 `schema_version=2` 在办实例时，不得自动反向迁移，应标 MANUAL_ROLLBACK_REQUIRED — conf 0.6 · 证据 ocap_approval_flow module_design / DEPLOY-006 实测 0/0/0 / GR-E2-001 · 首见 2026-11-22 · 命中 1
- [M-DE-050] 目标机用 `cp -a` 叠加覆盖代码并以 tar 排除 `.env`/`venv`/`var`，可保留本地状态；迁移前 `showmigrations` 基线与相关表 `mysqldump` 是有效回滚锚点 — conf 0.6 · 证据 ocap_approval_flow DEPLOY-001/005 `.env` 哈希不变、转储 4 表 · 首见 2026-11-22 · 命中 1

## 用户偏好与禁止项

## 待验证
- [P-DE-050] 迁移尚未进入目标机代码时，预检 `migrate --plan` 不会出现新迁移；应让预检只记录基线，把“恰为新迁移 1 行”的门控放到代码覆盖之后（DEPLOY 阶段） — conf 0.6 · 证据：ocap_approval_flow deployment_report R-01 · 缺：第二批次复现
