# software-developer 项目记忆 — ocap_registry_import

> TRAE 不自动注入记忆：本文件由对应 `sdlc-*` 技能在开始时**显式 Read**。
> 只允许 agent 自己追加「待验证」区；「已验证」「用户偏好与禁止项」由 kb-curator 维护。

## 已验证
- [M-SD-012] 导入接口拆为“解析→只读计划→单事务应用”，dry_run 与正式导入共用计划函数可保证结果一致 — conf 0.8 · 证据 GR-C-001 / GR-D-001 / TC-INT-144、145 / commit 9c66dce · 首见 2026-11-10 · 命中 1
- [M-SD-013] 客户端测试无法运行时先按 CI 同参数安装依赖（miniprogram 用 --legacy-peer-deps）；Windows 主题测试的行尾/绝对路径差异按既有环境失败单列 — conf 0.6 · 证据 GR-C-001 / miniprogram 69 passed / frontend 124 passed、2 failed · 首见 2026-11-10 · 命中 1
- [M-SD-022] 跨表搜索用 Exists + 同一关联别名同时约束两个字段，避免跨记录误匹配 — conf 0.6 · 证据 GR-B-001-F01 / TC-INT-395 / directory.py:real_name_q · 首见 2026-11-11 · 命中 1
- [M-SD-023] 批量改写带唯一约束的派生列时，新值可能等于另一行的旧值：先全量检测，再用占位值两阶段更新，整个过程放单事务 — conf 0.6 · 证据 GR-C-001 / TC-INT-403 / ADR-067 · 首见 2026-11-11 · 命中 1
- [M-SD-024] 仅作用于某一端的主题覆盖要挂在 html 级属性（如 data-surface）上，不要挂布局根类：组件库弹层 Teleport 到 body — conf 0.6 · 证据 GR-C-001 / ADR-075 / bento.web.css 管理端作用域 · 首见 2026-11-11 · 命中 1
- [M-SD-025] 管理端与用户端主题偏好使用独立设备键与独立账号接口；共用会互相覆盖 — conf 0.6 · 证据 GR-C-001 / adminStore.js:ADMIN_DEVICE_KEY / TC-UNIT-504 · 首见 2026-11-11 · 命中 1

## 用户偏好与禁止项

## 待验证
