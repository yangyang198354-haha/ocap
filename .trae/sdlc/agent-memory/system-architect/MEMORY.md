# system-architect 项目记忆 — ocap_registry_import

> TRAE 不自动注入记忆：本文件由对应 `sdlc-*` 技能在开始时**显式 Read**。
> 只允许 agent 自己追加「待验证」区；「已验证」「用户偏好与禁止项」由 kb-curator 维护。

## 已验证
- [M-SA-004] DRF 查询参数不要用 `format`（会被渲染器后缀拦截），文件类型参数用 `file_type` — conf 0.6 · 证据 GR-B-001 / module_design IFC-158 / TC-INT-105 · 首见 2026-11-10 · 命中 1
- [M-SA-005] Django `bulk_create` 在 MySQL 不回填主键，需按业务键回查；`bulk_update` 不刷新 auto_now — conf 0.6 · 证据 GR-B-001 / apps/registry/importing.py 计划与应用实现 · 首见 2026-11-10 · 命中 1
- [M-SA-006] `Membership.source` 仅 12 字符，新来源值须 ≤12，否则把来源放进审计 detail — conf 0.6 · 证据 GR-B-001 / apps/residency/models.py:16 · 首见 2026-11-10 · 命中 1
- [M-SA-010] DRF 列表增加跨表派生字段优先固定 prefetch + 应用层计算，并用“每页查询数不随行数增长”测试守 N+1；跨表搜索用 Exists 避免 distinct 放大 — conf 0.6 · 证据 GR-B-001-F02 / TC-INT-397 · 首见 2026-11-11 · 命中 1
- [M-SA-011] 共享展示型聚合函数被多个输出面复用时，改口径前须枚举全部消费方，避免只改首页遗漏决议/报销文案 — conf 0.6 · 证据 GR-B-001 / GB-3 / module_design IFC-247 · 首见 2026-11-14 · 命中 1

## 用户偏好与禁止项

## 待验证
- [P-SA-005] 迁移拆分旧版无归属数据时，要提前定义“同人多号吸收并入”规则，否则全量重传会判成冲突 — 自记 2026-11-10 · 证据：设计推演（待真实历史数据迁移复现）
