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
- [M-SD-012] 导入接口拆为"解析→只读计划→单事务应用"，dry_run 与正式导入共用计划函数可保证结果一致 — conf 0.8 · 证据 registry GR-C-001/GR-D-001、TC-INT-144/145、commit 9c66dce · 首见 2026-11-10 · 命中 1
- [M-SD-013] 客户端测试无法运行时先按 CI 同参数安装依赖（miniprogram 用 --legacy-peer-deps）；Windows 主题测试的行尾/绝对路径差异按既有环境失败单列 — conf 0.6 · 证据 registry GR-C-001 · 首见 2026-11-10 · 命中 1
- [M-SD-014] 改变既有行为（同步清理改延迟、禁用按钮改可点击并提示）前先 grep 测试里对该行为的断言，改动同时提示 test-engineer，避免回归失败到自验证才暴露 — conf 0.8 · 证据 registry GR-C-002-F01（DEF-012 使 TC-UNIT-114 过期）、content DEF-016/TC-UNIT-404 · 首见 2026-11-11 · 命中 2
- [M-SD-015] 会员端 blocks 的媒体 src 去 API 前缀必须递归处理引用块/列表嵌套，由客户端拼接基址，否则小程序重复拼接 — conf 0.6 · 证据 DEF-014、posts.py:217-230、TC-INT-388 · 首见 2026-11-11 · 命中 1
- [M-SD-016] 分批（chunk）查询每批只带本批自己的键；把全集过滤条件带进每批会让耗时变 O(批数×全集)，更稳是按单一键分批、应用端做复合键过滤 — conf 0.6 · 证据 DEF-013、commits 6fbd24d/3980890 · 首见 2026-11-11 · 命中 1
- [M-SD-017] 类体内定义名为 list 的 staticmethod 会让同类体 `list[...]` 注解在 Python 3.12/3.13 报 TypeError（3.14 不暴露）；改名，不用 `from __future__ import annotations` 掩盖；本机版本高于 CI 时在较低版本复跑 — conf 0.8 · 证据 content GR-C-002-F01、registry GR-D-003-F01 · 首见 2026-11-11 · 命中 2
- [M-SD-018] frontend 的 theme.spec.js 扫描全部 .vue（含注释）里的 `#hex`/`rgb(`/`hsl(` 字面量；调色板等颜色常量放 .js 文件 — conf 0.6 · 证据 frontend/tests/theme.spec.js:40-49、frontend/src/admin/editor/colors.js · 首见 2026-11-11 · 命中 1
- [M-SD-019] Tiptap 解析 HTML 时 style.color 被规范成 rgb()，textStyle 标记会带 `fontSize:""`/`color:null`；服务端宽容校验须把 null/空串当"未设置"，否则每次保存都产生警告 — conf 0.6 · 证据 richtext/schema.py `_absent`:67、GR-C-002-F04 · 首见 2026-11-11 · 命中 1
- [M-SD-020] 后端测试在 scratch 复制的 backend 中运行时，需让 ../frontend 与 ../miniprogram 可见（符号链接），否则契约测试类读不到文件而报错 — conf 0.6 · 证据 test_frontend_contract.py 以仓库根相对路径读 frontend/miniprogram、registry DEF-013 自验证 · 首见 2026-11-11 · 命中 1
- [M-SD-021] openpyxl `read_only=True` 没有 merged_cells，要展开合并单元格须用普通模式读取（20000 行×8 列实测约 4.8 s，在 60 s 预算内） — conf 0.6 · 证据 registry DEF-008（GR-C-002 J-C-DEF-008 PM 构造合并单元格 xlsx 复核）、apps/registry/importing.py:243 · 首见 2026-11-11 · 命中 1
## 用户偏好与禁止项
## 待验证
- [P-SD-004] 富文本渲染函数应同时接受 dataclass 与 dict 令牌，避免调用方传 JSON 时 AttributeError — 自记 2026-11-11 · 证据：content GR-C-001 无对应 finding，渲染入口未核实
