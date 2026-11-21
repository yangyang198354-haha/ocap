# pm-orchestrator 项目记忆 — ocap_registry_import

> TRAE 不自动注入记忆：本文件由对应 `sdlc-*` 技能在开始时**显式 Read**。
> 只允许 agent 自己追加「待验证」区；「已验证」「用户偏好与禁止项」由 kb-curator 维护。

## 已验证

## 用户偏好与禁止项

## 待验证
- [P-PM-005] 原型/视觉类需求的门控应对照原型核对样式量与首页结构，不只看测试通过 — 自记 2026-11-10 · 证据：`ocap_ui_theme` GR-C-001（本项目 phase_status 无法核验）
- [P-PM-006] 新批次约束编号 C-NN 必须全仓唯一：`backend/tests/integration/test_requirements_numbering.py` TC-INT-480 固定断言仅存在两组历史重复（C-21~24、C-25/26），新增重复会直接让 CI 后端 job 失败；出稿前先扫 `project_workspace/*/requirements/requirements_spec.md` 取最大编号 — 自记 2026-11-21 · 证据：CI run 44866643038 失败、run 44866876013 通过
- [P-PM-007] 部署计划的静态目录应以目标机实际为准（ocap 为 `/home/yangyang/ocap/web/ocap`，不是 `web/dist`），且前端构建必须带 `VITE_API_BASE=/ocap/api/v1` 与 `--base=/ocap/` — 自记 2026-11-21 · 证据：E2 预检与 DEPLOYED_SUCCESSFULLY 报告
