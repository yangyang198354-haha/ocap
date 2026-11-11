# test-engineer 项目记忆 — ocap
## 已验证
- [M-TE-001] 解析前端 api.js 调用并 resolve 到 DRF 视图 http 方法的契约测试，不依赖浏览器即可发现前端调用后端不支持的方法（客户端调用与路由两侧同时解析，路径/方法漂移低成本可测） — conf 1.0 · 证据 DEF-005、GR-C-004-F02、backend/tests/integration/test_frontend_contract.py、registry GR-D-001 TC-INT-164/165 · 首见 2026-11-08 · 命中 4
- [M-TE-002] AC 写"输错 N 次作废/锁定"时，达到上限后再提交**正确**凭据并断言被拒；只断言第 N 次 429 会漏掉"已锁但旧码仍有效"；修复后仍要保持下一次尝试返回 CODE_LOCKED — conf 0.8 · 证据 DEF-006、GR-D-007-F01、GR-C-007 · 首见 2026-11-08 · 命中 2
- [M-TE-003] test_plan 的 AC 列写具体 AC-NNN-NN / US-NNN；PM 按 AC 前缀机器比对 Must Have 故事，漏映射 GR-D FAIL；交付前自己先跑"故事→用例"总表 — conf 0.8 · 证据 GR-D-006-F01（11 个故事缺映射）、补齐后 69/69 · 首见 2026-11-08 · 命中 2
- [M-TE-004] 门控要求收紧期望状态码（如匿名只接受 401）前，先 grep 全部状态码元组并区分匿名与已登录场景；用错角色 token 可能合理返回 401，不要过度收紧 — conf 0.6 · 证据 GR-C-007 condition · 首见 2026-11-09 · 命中 1
- [M-TE-005] 验证"权限零回归"：把角色×操作矩阵原样放到 git archive HEAD 导出的基线树，同环境各跑一次，两边都通过才算一致；探测列表接口还会暴露基线既有的 500 — conf 0.6 · 证据 backend/tests/integration/test_ui_theme_qa.py(TC-INT-009)、GR-D-001-F01 · 首见 2026-11-09 · 命中 1
- [M-TE-006] vitest 里 `beforeEach(() => mock.mockImplementation(...))` 箭头函数会把 mock 当返回值被当作清理函数调用，要用花括号；含 router-view 的布局组件嵌在自身路由下会渲染两次 — conf 0.6 · 证据 frontend/tests/qa_int_theme.spec.js:33 · 首见 2026-11-09 · 命中 1
- [M-TE-007] 无浏览器时 jsdom 挂真实 App + 真实路由 + 带状态假服务端做 E2E 替代口径；先执行 index.html 内联脚本再挂载，路由单例用例间复位，懒加载跳转用 vi.waitFor — conf 0.6 · 证据 frontend/tests/qa_e2e_theme.spec.js:85 · 首见 2026-11-09 · 命中 1
- [M-TE-008] 共用分页/序列化辅助函数的调用约定变化后，对所有使用方的列表接口按角色冒烟遍历；回归用例放到未修复树确认能失败（5/6 失败，修复后 6/6） — conf 0.6 · 证据 DEF-001、backend/tests/integration/test_admin_appeals_regression.py、GR-D-002 · 首见 2026-11-09 · 命中 1
- [M-TE-009] 导入类测试必须做"同文件预检 vs 正式导入"逐项数字比对，并构造同单元跨行类型冲突的整组失败用例 — conf 0.8 · 证据 registry GR-D-001、TC-INT-122/144/145 · 首见 2026-11-10 · 命中 1
- [M-TE-011] 产品行为由"禁用按钮"改为"可点击并提示"后，旧 disabled 断言成过期用例；缺陷修复回流时 grep 反向断言（disabled / not.toBeCalled）并同步更新 — conf 0.8 · 证据 content DEF-016/TC-UNIT-404、GR-D-003 condition；registry GR-C-002-F01 同类 · 首见 2026-11-11 · 命中 2
- [M-TE-012] 补"修复无专门测试"类缺陷的用例时，把新测试放进 `git archive HEAD` 导出的修复前树运行，确认失败（10/15 失败；DEF-013 用例修复前确定失败），才证明用例能抓住缺陷 — conf 0.8 · 证据 registry DEF-007~011、test_registry_import_query_bounds.py（DEF-013） · 首见 2026-11-11 · 命中 2
- [M-TE-013] 对递归结构（引用/列表嵌套）做序列化后处理（如去 URL 前缀）的接口，用例要含引用内、列表内的节点，只测顶层会漏 — conf 0.6 · 证据 DEF-014、test_content_wechat_and_gaps.py:438 TC-INT-388 · 首见 2026-11-11 · 命中 1
- [M-TE-014] 性能类缺陷（慢查询、每批带全集）的回归用例不断言墙钟耗时，用 `connection.execute_wrapper` 记录每条 SQL 绑定参数个数与查询条数，机器无关 — conf 0.6 · 证据 backend/tests/integration/test_registry_import_query_bounds.py:6,64,109、DEF-013 · 首见 2026-11-11 · 命中 1
- [M-TE-015] Tiptap/ProseMirror 可在 vitest+jsdom 真实挂载并跑命令；需垫 ClipboardEvent（pasteHTML）与 Range.getClientRects，撤销重做用 `vi.useFakeTimers({toFake:["Date"]})` 跨过历史分组间隔 — conf 0.6 · 证据 frontend/tests/content_editor.spec.js（22/23 通过） · 首见 2026-11-11 · 命中 1
- [M-TE-016] DRF `FileResponse` 无 content 属性，ZIP/文件断言读 `b"".join(resp.streaming_content)` — conf 0.6 · 证据 backend/tests/e2e/test_content_flows.py:163,270 · 首见 2026-11-11 · 命中 1
## 用户偏好与禁止项
## 待验证
- [P-TE-001] test_plan 的用例方法名要用 grep `def test_` 对账：0.3.0 计划里有 4 处方法名与代码不符、1 行无对应测试 — 自记 2026-11-08 · 证据 GROUP_D-7 对账（旧版已 SUPERSEDED，不可核验）
- [P-TE-005] 延迟释放资源的下载辅助函数（setTimeout 后 revokeObjectURL）用 vi.useFakeTimers + advanceTimersByTime，finally 恢复真实计时器；jsdom 里 anchor.click 要 spy — 自记 2026-11-11 · 证据 registry_import.spec.js:59 用了 useFakeTimers，spy/finally 细节未核
- [P-TE-006] Fake 类的 reset() 会清空构造参数，替身初始化应先 reset 再赋值 — 自记 2026-11-11 · 证据：content GR-D-001 无对应 finding，未核
