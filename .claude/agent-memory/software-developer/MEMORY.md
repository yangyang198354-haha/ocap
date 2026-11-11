# software-developer 项目记忆 — ocap
## 已验证
- [M-SD-001] 用户引用注册表 `delete_secondary` 会连无冲突的作答/表决一起删；要"冲突保留主账号、其余并入"用 `custom` handler 并写 `MERGE_ANSWER_DISCARDED` — conf 0.6 · 证据 backend/apps/polls/services.py merge_responses、identity/services.py:162 · 首见 2026-11-08 · 命中 1
- [M-SD-002] 修前后端契约先逐字段对照 `frontend/src/shared/api.js`/`miniprogram/utils/api.js` 与后端 view（action/decision、attachment_ids/proof_ids、options 结构、PUT/PATCH）；小程序无构建环境时用 frontend/node_modules 的 `@vue/compiler-sfc` 编译检查 — conf 1.0 · 证据 CR-012~014、code_review_report §8.8/§9.2 · 首见 2026-11-08 · 命中 3
- [M-SD-003] 去掉 settings 固定 SECRET_KEY 默认值后，test_settings 必须在 `from .settings import *` 之前设置放行开关，否则 CI 因 ImproperlyConfigured 失败 — conf 0.6 · 证据 backend/config/test_settings.py:4 · 首见 2026-11-08 · 命中 1
- [M-SD-004] 写完 service 函数要 grep 其调用点；有函数但未接入入口不算实现需求 — conf 0.6 · 证据 GR-C-004-F01(CR-011 账号合并未接入) · 首见 2026-11-08 · 命中 1
- [M-SD-005] 读接口与写接口不要共用同一权限类，列表/详情视图显式区分读写权限，否则"公开可读"被写权限误伤 — conf 1.0 · 证据 DEF-001/002/004（GR-D-001-F01）、OBS-001（GR-C-007） · 首见 2026-11-07 · 命中 4
- [M-SD-006] 小程序 `uni build -p mp-weixin` 在开发机因 uni alpha 工具链失败，git archive HEAD 基线同样失败；不当作改动引入，改用 `@vue/compiler-sfc` 编译检查并如实标"未验证" — conf 0.6 · 证据 ocap_ui_theme code_review_report.md:51 · 首见 2026-11-09 · 命中 1
- [M-SD-007] 仓库根 `scripts/themes` 的 .mjs 可被 frontend vitest 直接 import，用于在临时目录构造新风格做"新增风格不改业务页面"回归 — conf 0.6 · 证据 frontend/tests/theme.spec.js、theme_build.spec.js · 首见 2026-11-09 · 命中 1
- [M-SD-008] jsdom 会把 style 属性里的 `--x:#abc` 规范成 `--x: #abc`，断言 CSS 变量注入用带 `\s*` 的正则 — conf 0.6 · 证据 miniprogram/tests/theme.spec.js:86,90 · 首见 2026-11-09 · 命中 1
- [M-SD-009] 追溯表里写了"简化版"的需求不能标 DONE；做设计原型类需求先逐区块列接口有无数据，有数据实现，无数据做空态不编造 — conf 0.6 · 证据 GR-C-001-F01 · 首见 2026-11-09 · 命中 1
- [M-SD-010] el-dialog 内容 teleport 到 body；页面测试先调用页面 open 方法并 flushPromises，再用 document.body.querySelector 查控件 — conf 0.6 · 证据 frontend/tests/ui_blocks.spec.js · 首见 2026-11-09 · 命中 1
- [M-SD-011] 辅助函数（如分页序列化）改成传 `context=` 后，grep 全部调用方并检查每个手写序列化类 `__init__` 签名，否则运行时 500 — conf 0.8 · 证据 DEF-001、backend/apps/residency/views.py:116、GR-C-003 · 首见 2026-11-09 · 命中 2
## 用户偏好与禁止项
## 待验证
- [P-SD-001] frontend 的 theme.spec.js 扫描全部 .vue（含注释）里的 `#hex`/`rgb(`/`hsl(` 字面量；调色板等颜色常量放 .js 文件 — 自记 2026-11-11 · 证据 frontend/tests/theme.spec.js:44-49、colors.js COLOR_PALETTE
- [P-SD-002] Tiptap 解析 HTML 时 `element.style.color` 被规范成 rgb()，且 textStyle 标记会带 `fontSize:""`/`color:null`；服务端宽容校验须把 null/空串当"未设置"，否则每次保存都产生警告 — 自记 2026-11-11 · 证据 richtext/schema.py `_absent`、RichEditor.vue SafeColor
- [P-SD-003] 类体内定义名为 list 的 staticmethod 会让同类体里的 `list[...]` 注解在 Python 3.12/3.13 报 TypeError，3.14 延迟注解不暴露；改名而非加 `from __future__ import annotations` — 自记 2026-11-11 · 证据 GR-C-002-F01
