# software-developer 项目记忆 — ocap
## 已验证
## 用户偏好与禁止项
## 待验证
- [P-SD-001] 用户引用注册表里 `delete_secondary` 会连无冲突的作答/表决一起删；需要"冲突保留主账号、其余并入"时用 `custom` handler 并写 `MERGE_ANSWER_DISCARDED` — 自记 2026-11-08 · 证据 backend/apps/polls/services.py merge_responses、临时脚本验证
- [P-SD-002] 修前后端契约问题时，先逐个对照 `frontend/src/shared/api.js`/`miniprogram/utils/api.js` 与后端 view 的字段（本项目出现过 action/decision、attachment_ids/proof_ids、options 结构、PUT/PATCH 不一致）；小程序无构建环境时可用 frontend/node_modules 的 `@vue/compiler-sfc` 做 .vue 编译检查 — 自记 2026-11-08 · 证据 code_review_report §8.8、§9.2
- [P-SD-003] 去掉 settings 固定 SECRET_KEY 默认值时，test_settings 必须在 `from .settings import *` 之前设置放行开关，否则 CI 的 check/test 会因 ImproperlyConfigured 失败 — 自记 2026-11-08 · 证据 backend/config/test_settings.py
