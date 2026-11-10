# system-architect 项目记忆 — ocap
## 已验证
- [M-SA-001] "有效记录唯一"约束要在生产 MySQL 与测试 SQLite 同时生效：用可空槽位列加普通唯一索引，不用条件唯一索引（MySQL 上被忽略） — conf 0.8 · 证据 backend/apps/approval/models.py:40,44 pending_slot · 首见 2026-11-07 · 命中 2
- [M-SA-002] uni-app 运行期换肤：uni.scss 是编译期变量，运行期由页面根组件注入 CSS 变量，再用 uni.setTabBarStyle / uni.setNavigationBarColor 同步原生部分（frontColor 仅支持 #ffffff/#000000，据官方文档）；非 tabBar 页调用 setTabBarStyle 会失败须吞错 — conf 0.6 · 证据 miniprogram/store/theme.js:58-66 · 首见 2026-11-09 · 命中 1
- [M-SA-003] Element Plus 运行期换主色时 --el-color-primary 的 light-3~9、dark-2 梯度不自动派生，须显式输出；深色另加 html.dark 并引入 element-plus/theme-chalk/dark/css-vars.css — conf 0.6 · 证据 frontend/src/main.js:5、frontend/src/theme/generated/themes.css:36 · 首见 2026-11-09 · 命中 1
## 用户偏好与禁止项
## 待验证
- [P-SA-001] 取微信官方服务端接口文档时，用 `developers.weixin.qq.com/miniprogram/dev/server/API/<分类>/<api_xxx>.md`（带 .md）可拿到干净正文；`/framework/open-ability/*.html` 页面正文过长，WebFetch 只返回导航 — 自记 2026-11-07 · 证据 WebFetch 结果（不可核验）
- [P-SA-002] 小程序"手机号快速验证组件"官方称仅向非个人且已认证主体开放并按次收费，设计上以短信验证码为基线、快速验证做可选开关 — 自记 2026-11-07 · 证据 搜索摘要（非官方原文），开发前复核；官方 getphonenumber 页未写主体与收费
- [P-SA-003] 阿里云验证码短信模板：单变量须 4~6 位、双变量不可自定义，有效期只能写死在模板正文，设计上用启动检查保证与配置有效期一致；平台默认流控与 C-06 同值但窗口算法不同 — 自记 2026-11-07 · 证据 help.aliyun.com 模板规范页与 message-rules 页
- [P-SA-004] 阿里云帮助页 WebFetch 偶发 "Socket is closed"，重试一次即可；api.aliyun.com 错误码页只给名称不给释义，释义标 [UNSOURCED] — 自记 2026-11-07 · 证据 WebFetch 结果
- [P-SA-005] 新增前端 API 调用前先看 backend/tests/integration/test_frontend_contract.py:30-61：正则只认 `http.`/`adminHttp.` + 字面量路径，路径不能带 `?`，管理端接口只能 IsAdmin、用户端只能 IsMember，设计 IFC 时就按此约束写 — 自记 2026-11-10 · 证据 test_frontend_contract.py:30-33,63-97
- [P-SA-006] uni-app `rich-text` 会屏蔽节点事件（链接/图片不可点击），小程序要"可点击链接/视频"的富文本应由服务端出结构化块、自定义组件渲染 — 自记 2026-11-10 · 证据 uniapp.dcloud.net.cn/component/rich-text.html（WebFetch 摘要）
- [P-SA-007] 查包信息：npm 用 `registry.npmjs.org/<pkg>/latest`（小）；PyPI 的 `/pypi/<pkg>/json` 超长被截断，改用 `/pypi/<pkg>/<version>/json` 才能看到 upload_time 与轮子文件名 — 自记 2026-11-10 · 证据 WebFetch 结果
