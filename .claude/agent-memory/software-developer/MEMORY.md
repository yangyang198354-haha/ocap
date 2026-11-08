# software-developer 项目记忆 — ocap
## 已验证
- [M-SD-001] 用户引用注册表 `delete_secondary` 会连无冲突的作答/表决一起删；要"冲突保留主账号、其余并入"用 `custom` handler 并写 `MERGE_ANSWER_DISCARDED` — conf 0.6 · 证据 backend/apps/polls/services.py merge_responses、identity/services.py:162 · 首见 2026-11-08 · 命中 1
- [M-SD-002] 修前后端契约先逐字段对照 `frontend/src/shared/api.js`/`miniprogram/utils/api.js` 与后端 view（action/decision、attachment_ids/proof_ids、options 结构、PUT/PATCH）；小程序无构建环境时用 frontend/node_modules 的 `@vue/compiler-sfc` 编译检查 — conf 1.0 · 证据 CR-012~014、code_review_report §8.8/§9.2 · 首见 2026-11-08 · 命中 3
- [M-SD-003] 去掉 settings 固定 SECRET_KEY 默认值后，test_settings 必须在 `from .settings import *` 之前设置放行开关，否则 CI 因 ImproperlyConfigured 失败 — conf 0.6 · 证据 backend/config/test_settings.py:4 · 首见 2026-11-08 · 命中 1
- [M-SD-004] 写完 service 函数要 grep 其调用点；有函数但未接入入口不算实现需求 — conf 0.6 · 证据 GR-C-004-F01(CR-011 账号合并未接入) · 首见 2026-11-08 · 命中 1
- [M-SD-005] 读接口与写接口不要共用同一权限类，列表/详情视图显式区分读写权限，否则"公开可读"被写权限误伤 — conf 1.0 · 证据 DEF-001/002/004（GR-D-001-F01）、OBS-001（GR-C-007） · 首见 2026-11-07 · 命中 4
## 用户偏好与禁止项
## 待验证
