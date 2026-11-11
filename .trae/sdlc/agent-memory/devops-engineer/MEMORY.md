# devops-engineer 项目记忆 — ocap_registry_import

> TRAE 不自动注入记忆：本文件由对应 `sdlc-*` 技能在开始时**显式 Read**。
> 只允许 agent 自己追加「待验证」区；「已验证」「用户偏好与禁止项」由 kb-curator 维护。

## 已验证
- [M-DE-006] 无 git 的目标机部署，锚点应记录本地 HEAD + 工作树状态 + tar SHA256，仅时间戳不足以定位版本 — conf 0.6 · 证据 GR-E1-001 / DEPLOY-004 两端 SHA256 一致 · 首见 2026-11-10 · 命中 1
- [M-DE-007] 大文件上传/长任务上线前必须核实 gunicorn `--timeout` 与 nginx `client_max_body_size`/`proxy_read_timeout`，避免 413/504 — conf 0.8 · 证据 GR-B-001-F01 / DEPLOY-003 实测 60→90 / GR-E2-001 · 首见 2026-11-10 · 命中 1
- [M-DE-008] 目标测试 MySQL 使用自签证书，mysqldump 需 `--skip-ssl`（Django 侧 `DB_SSL_DISABLED=1`） — conf 0.6 · 证据 DEPLOY-002 输出 DUMP_EXIT=0（91 行） · 首见 2026-11-10 · 命中 1
- [M-DE-015] 无迁移的只读页面增量，回滚重点是前端静态目录与后端源码快照；新增文件在旧代码中无引用，回滚时可保留 — conf 0.6 · 证据 GR-E1-001 / deployment_plan ROLLBACK-001~004 · 首见 2026-11-11 · 命中 1

## 用户偏好与禁止项

## 待验证
