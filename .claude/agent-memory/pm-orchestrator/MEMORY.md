# pm-orchestrator 项目记忆 — ocap
## 已验证
- [M-PM-001] software-developer 会以"任务小"为由跳过画像 P10 的额外必读 Freeark/CLAUDE.md；调用时在 special_instructions 点名并说明原因（点名后 GR-C-007 已读） — conf 0.8 · 证据 GR-C-004-F03、GR-C-006-F01、GR-C-007 · 首见 2026-11-08 · 命中 2
- [M-PM-002] 后端 API 测试全过不代表前后端可用；GROUP_D 门控要求有解析前端 api.js 并 resolve 到后端路由的契约测试 — conf 1.0 · 证据 GR-C-004-F02、DEF-005、GR-C-006 · 首见 2026-11-08 · 命中 3
- [M-PM-003] 写 phase_status 的 python 脚本不与 `grep -c` 用 && 串联（计数 0 返回码 1，脚本静默不执行）；替换后打印每处匹配数并核对状态 — conf 0.6 · 证据 phase_status SELF_CORRECTION 2026-11-08T23:41:59 · 首见 2026-11-08 · 命中 1
## 用户偏好与禁止项
- [Requirements first](feedback_requirements_first.md) — 需求分批、阶段逐一放行；提交与部署需当轮确认
## 待验证
