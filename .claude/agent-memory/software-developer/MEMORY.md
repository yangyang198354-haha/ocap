# software-developer 项目记忆 — ocap
## 已验证
- [M-SD-001] 用户引用注册表 `delete_secondary` 会连无冲突的作答/表决一起删；要"冲突保留主账号、其余并入"用 `custom` handler 并写 `MERGE_ANSWER_DISCARDED` — conf 0.6 · 证据 backend/apps/polls/services.py merge_responses、identity/services.py:162 · 首见 2026-11-08 · 命中 1
- [M-SD-002] 修前后端契约先逐字段对照 `frontend/src/shared/api.js`/`miniprogram/utils/api.js` 与后端 view（action/decision、attachment_ids/proof_ids、options 结构、PUT/PATCH）；小程序无构建环境时用 frontend/node_modules 的 `@vue/compiler-sfc` 编译检查 — conf 1.0 · 证据 CR-012~014、code_review_report §8.8/§9.2 · 首见 2026-11-08 · 命中 3
- [M-SD-003] 去掉 settings 固定 SECRET_KEY 默认值后，test_settings 必须在 `from .settings import *` 之前设置放行开关，否则 CI 因 ImproperlyConfigured 失败 — conf 0.6 · 证据 backend/config/test_settings.py:4 · 首见 2026-11-08 · 命中 1
- [M-SD-004] 写完 service 函数要 grep 其调用点；有函数但未接入入口不算实现需求 — conf 0.6 · 证据 GR-C-004-F01(CR-011 账号合并未接入) · 首见 2026-11-08 · 命中 1
- [M-SD-005] 读接口与写接口不要共用同一权限类，列表/详情视图显式区分读写权限，否则"公开可读"被写权限误伤 — conf 1.0 · 证据 DEF-001/002/004（GR-D-001-F01）、OBS-001（GR-C-007） · 首见 2026-11-07 · 命中 4
## 用户偏好与禁止项
## 待验证
- [P-SD-001] 小程序 `uni build -p mp-weixin` 在开发机因 uni alpha 工具链失败（`vueOptions` 错误，需 `UNI_INPUT_DIR=.`），`git archive HEAD` 基线同样失败；不要把它当作改动引入的问题，改用 `@vue/compiler-sfc` 编译检查并如实标未验证 — 自记 2026-11-09 · 证据 ocap_ui_theme code_review_report 自验证表
- [P-SD-002] 跨工程换肤脚本放仓库根 `scripts/themes`，vitest 可直接 import 其 `.mjs`（frontend 测试已验证），用于在临时目录构造新风格做"新增不改页面"回归 — 自记 2026-11-09 · 证据 frontend/tests/theme.spec.js
- [P-SD-004] 设计原型类需求追溯表只要写了“简化版”就不能标 DONE；先逐区块列“接口有/无数据”再实现，无数据的区块用空态而不是编造（GR-C-001-F01 FAIL 的根因） — 自记 2026-11-09 · 证据 GR-C-001
- [P-SD-005] el-dialog 内容 teleport 到 body，页面测试用 `document.body.querySelector` 查对话框控件，并先调用页面的 open 方法再 flushPromises — 自记 2026-11-09 · 证据 frontend/tests/ui_blocks.spec.js
- [P-SD-003] jsdom 会把 style 属性里的 `--x:#abc` 规范化成 `--x: #abc`，断言 CSS 变量注入用正则 `\s*`，不要用 toContain 精确串 — 自记 2026-11-09 · 证据 miniprogram/tests/theme.spec.js
