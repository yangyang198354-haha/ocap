# test-engineer 项目记忆 — ocap_registry_import

> TRAE 不自动注入记忆：本文件由对应 `sdlc-*` 技能在开始时**显式 Read**。
> 只允许 agent 自己追加「待验证」区；「已验证」「用户偏好与禁止项」由 kb-curator 维护。

## 已验证
- [M-TE-009] 导入类测试必须做“同文件预检 vs 正式导入”逐项数字比对，并构造同单元跨行类型冲突的整组失败用例 — conf 0.8 · 证据 GR-D-001 / TC-INT-122、144、145 / commit 9c66dce · 首见 2026-11-10 · 命中 1
- [M-TE-010] 前后端契约测试应同时解析客户端源码调用路径与 Django 路由，可低成本发现路径/方法漂移 — conf 0.6 · 证据 GR-D-001 / TC-INT-164、165 · 首见 2026-11-10 · 命中 1
- [M-TE-017] 列表派生字段测试要同时覆盖值正确与查询数不随行数增长；跨表搜索必须加同记录负向用例 — conf 0.6 · 证据 GR-D-001 / TC-INT-395、TC-INT-397 · 首见 2026-11-11 · 命中 1
- [M-TE-018] 验证“多端显示一致”时，同时断言管理端列表、房屋关系输出与 /me 读取同一存储列 — conf 0.6 · 证据 GR-D-001 / TC-INT-421 / test_specific_part_display_consistency.py · 首见 2026-11-11 · 命中 1
- [M-TE-019] 组件测试须同时覆盖“数据未返回”和“请求失败”两态，防止加载中/失败被误显示为游客 — conf 0.6 · 证据 GR-D-001 / GD-2 / TC-WEB-503、504 · 首见 2026-11-14 · 命中 1
- [M-TE-043] 小批次 critical path 可用一条跨模块 API 旅程替代浏览器 E2E，报告首行声明"替代"口径并单列人工验证项 — conf 0.7 · 证据 ocap_profile_ux-GROUP_D-1-1 / TC-E2E-1501 / ocap_role_home GR-D-001 / critical path 6/6 / TC-WEB-601~605 · 首见 2026-11-19 · 命中 2
- [M-TE-044] 重命名共享常量时只改 import 不改模板会静默留下未定义引用；前端界面测试必须在模板渲染层断言文案，而不是只测常量表 — conf 0.6 · 证据 ocap_approval_flow DEF-001 / TC-INT-1304 / GR-D-001 · 首见 2026-11-22 · 命中 1
- [M-TE-045] 判定基线失败前先确认被测文件是否本批次修改，再用 `git log -1 -- <file>` 取证，避免把预存在问题误计为新增失败 — conf 0.6 · 证据 ocap_approval_flow test_tc_int_964 / `git log -1 -- miniprogram/pages/phone/index.vue` / GR-D-001 · 首见 2026-11-22 · 命中 1
- [M-TE-046] usePaging 的 filters 只接受 ref/computed，传函数会被 unref 后展开为空对象、筛选静默失效；列表页筛选测试必须断言请求参数 — conf 0.85 · 证据 ocap_finance_ux DEF-001 / TC-WEB-1402 / GR-D-001 · 首见 2026-11-23 · 命中 1
- [M-TE-047] 本项目 config.test_settings 以模型直建表、不执行迁移（Apply all migrations: none），迁移回填类 AC 必须转人工验证 — conf 0.8 · 证据 ocap_finance_ux US-327 NOT_TESTABLE / test_plan M-01 · 首见 2026-11-23 · 命中 1
- [M-TE-048] Element Plus el-option 的 value 不支持 null，空选项用空串并在 API 调用层归一化 — conf 0.7 · 证据 ocap_finance_ux DEF-001 修复 / 前端 53 文件通过 · 首见 2026-11-23 · 命中 1
- [M-TE-049] 路由表“未登记即抛错”的测试替身可把“不得请求某接口”变成强断言，比只断言 UI 不存在更能防多请求回归 — conf 0.7 · 证据 ocap_role_home GR-D-001 / TC-WEB-601、604 / TC-INT-601 · 首见 2026-11-25 · 命中 1
- [M-TE-050] 双端各存一份模块顺序常量时，补一组两端相同角色的顺序断言（含代表兼户主），可在不改架构下显性化漂移风险 — conf 0.6 · 证据 ocap_role_home GR-D-001 / TC-WEB-603、TC-INT-603 / CR-004 · 首见 2026-11-25 · 命中 1

## 用户偏好与禁止项

## 待验证
- [P-TE-001] 多账户场景的重复判定必须按目标账户隔离，并补一条“跨账户同日期同金额同类别同说明”的负向用例；account 为空的历史数据应视为默认账户范围 — 证据 TC-INT-2001/2002、TC-UNIT-2002 · 首见 2026-11-24
- [P-TE-002] 审批中批次的状态守卫要在单元层覆盖（作废 409、撤回置 WITHDRAWN 且无台账），避免 UI 按钮命中有守卫的接口时被误判为可用 — 证据 TC-UNIT-2004、TC-INT-2005 · 首见 2026-11-24
- [P-TE-003] jsdom 无法测对比度/等宽布局/横向滚动，采用“DOM 结构断言 + SFC 样式源断言 + 人工视觉清单”分层覆盖；报告必须列 manual 项 — 证据 TC-WEB-2001/2009、M-01～M-04 · 首见 2026-11-24
