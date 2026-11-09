# test-engineer 项目记忆 — ocap
## 已验证
- [M-TE-001] 解析前端 api.js 调用并 resolve 到 DRF 视图 http 方法的契约测试，不依赖浏览器即可发现前端调用后端不支持的方法 — conf 1.0 · 证据 DEF-005、GR-C-004-F02、backend/tests/integration/test_frontend_contract.py · 首见 2026-11-08 · 命中 3
- [M-TE-002] AC 写"输错 N 次作废/锁定"时，达到上限后再提交**正确**凭据并断言被拒；只断言第 N 次 429 会漏掉"已锁但旧码仍有效"；修复后仍要保持下一次尝试返回 CODE_LOCKED — conf 0.8 · 证据 DEF-006、GR-D-007-F01、GR-C-007 · 首见 2026-11-08 · 命中 2
- [M-TE-003] test_plan 的 AC 列写具体 AC-NNN-NN / US-NNN；PM 按 AC 前缀机器比对 Must Have 故事，漏映射 GR-D FAIL；交付前自己先跑"故事→用例"总表 — conf 0.8 · 证据 GR-D-006-F01（11 个故事缺映射）、补齐后 69/69 · 首见 2026-11-08 · 命中 2
- [M-TE-004] 门控要求收紧期望状态码（如匿名只接受 401）前，先 grep 全部状态码元组并区分匿名与已登录场景；用错角色 token 可能合理返回 401，不要过度收紧 — conf 0.6 · 证据 GR-C-007 condition · 首见 2026-11-09 · 命中 1
## 用户偏好与禁止项
## 待验证
- [P-TE-001] test_plan 的用例方法名要用 grep `def test_` 对账：0.3.0 计划里有 4 处方法名与代码不符、1 行无对应测试 — 自记 2026-11-08 · 证据 GROUP_D-7 对账（旧版已 SUPERSEDED，不可核验）
- [P-TE-002] 验证"权限零回归"时，把新写的角色×操作矩阵原样复制到 `git archive HEAD` 导出的基线树（scratchpad，同一 venv）各跑一次，两边都通过才算与改动前一致；探测列表接口时顺带暴露了基线即存在的 GET /admin/appeals 500 — 自记 2026-11-09 · 证据 ocap_ui_theme GROUP_D TC-INT-009、DEF-001
- [P-TE-003] vitest 的 `beforeEach(() => mock.mockImplementation(...))` 箭头函数会把 mock 函数当返回值，被当作清理函数无参调用而报"未预期的请求 undefined"，beforeEach 里要用花括号；含 `<router-view>` 的布局组件若又嵌在自身路由下会渲染两次 — 自记 2026-11-09 · 证据 frontend/tests/qa_int_theme.spec.js 调试记录
- [P-TE-004] 无浏览器时用 jsdom 挂载真实 App + 真实路由 + 假服务端做 E2E 替代口径；整页加载语义要先执行 index.html 的内联脚本（vm/new Function）再挂载，路由是单例须在用例间复位；懒加载页面跳转要用 vi.waitFor 等路径变化 — 自记 2026-11-09 · 证据 frontend/tests/qa_e2e_theme.spec.js
