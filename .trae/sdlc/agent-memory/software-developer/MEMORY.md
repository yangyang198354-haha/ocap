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
- [M-SD-026] 跨端展示字段由后端统一提供 display 文案，可避免 Web 与小程序各自实现空值与精度规则 — conf 0.6 · 证据 GR-C-001 / IFC-248 / 后端 572、前端 185、小程序 78 项通过 · 首见 2026-11-14 · 命中 1
- [M-SD-041] 列表派生字段在批量序列化层预取关联集合（如 RegistryPhone），避免逐行 related manager 造成 N+1 — conf 0.6 · 证据 ocap_profile_ux-GROUP_C-1-1 / tests/integration/test_batch1118_seats.py:301 · 首见 2026-11-19 · 命中 1
- [M-SD-042] 给隐私白名单接口加字段前先搜索测试中的反向字段断言，契约优先于便利 — conf 0.6 · 证据 ocap_profile_ux-GROUP_C-1-2 / CR-006 / TC-INT-1071 · 首见 2026-11-19 · 命中 1
- [M-SD-043] 报表链式口径用“生成时按期间起点前累计 + 作废标记覆盖期间及之后 + 生成后按期间升序重算 legacy=False 报表”，读取零计算；报表量增长时改条件批量更新 — conf 0.75 · 证据 ocap_finance_ux GR-C-001 / TC-UNIT-1404、1405 / TC-E2E-1401 · 首见 2026-11-23 · 命中 1
- [M-SD-044] 非空外键改造时在模型 save() 对未指定外键回退默认行，可让存量脚本/直接 create 在迁移后继续工作，避免大范围改测试 — conf 0.75 · 证据 ocap_finance_ux GR-C-001 / TC-UNIT-1403 / 全量 1206 通过 · 首见 2026-11-23 · 命中 1
- [M-SD-045] 本仓库 test_requirements_numbering 要求 REQ/US/AC/C 编号跨批次全局唯一，需求编号规划必须扫描全部 project_workspace — conf 0.9 · 证据 ocap_finance_ux SELF_CORRECTION / test_requirements_numbering.py / user_stories 1.0.1 · 首见 2026-11-23 · 命中 1
- [M-SD-046] uni-app HBuilderX 根目录布局的仓库直接跑 build:mp-weixin 会因默认 `src/` 报 ENOENT；用 `UNI_INPUT_DIR=.` 指向项目根 — conf 0.7 · 证据 ocap_role_home GR-C-001 / DEV-3 / 沙箱与树莓派均 `DONE Build complete.` · 首见 2026-11-25 · 命中 1
- [M-SD-047] 重复使用同一 CSS 语义类承载不同语义卡片会让既有测试误判；角色化首页按“任务类型”区分类名可同时满足新旧断言 — conf 0.6 · 证据 ocap_role_home GR-C-001 / CR-002 / 两端全量零新增失败 · 首见 2026-11-25 · 命中 1

## 用户偏好与禁止项

## 待验证
- [P-SD-043] 新增审计动作必须同步登记 `AUDIT_ACTIONS`，否则 `AuditService.record` 抛 ValueError 使接口 500 — 自记 2026-11-22 · 证据 DEF-AC-01 / audit.py:10-15
