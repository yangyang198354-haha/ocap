# system-architect 项目记忆 — ocap
## 已验证
- [M-SA-001] "有效记录唯一"约束要在生产 MySQL 与测试 SQLite 同时生效：用可空槽位列加普通唯一索引，不用条件唯一索引（MySQL 上被忽略） — conf 0.8 · 证据 backend/apps/approval/models.py:40,44 pending_slot · 首见 2026-11-07 · 命中 2
- [M-SA-002] uni-app 运行期换肤：uni.scss 是编译期变量，运行期由页面根组件注入 CSS 变量，再用 uni.setTabBarStyle / uni.setNavigationBarColor 同步原生部分（frontColor 仅支持 #ffffff/#000000，据官方文档）；非 tabBar 页调用 setTabBarStyle 会失败须吞错 — conf 0.6 · 证据 miniprogram/store/theme.js:58-66 · 首见 2026-11-09 · 命中 1
- [M-SA-003] Element Plus 运行期换主色时 --el-color-primary 的 light-3~9、dark-2 梯度不自动派生，须显式输出；深色另加 html.dark 并引入 element-plus/theme-chalk/dark/css-vars.css — conf 0.6 · 证据 frontend/src/main.js:5、frontend/src/theme/generated/themes.css:36 · 首见 2026-11-09 · 命中 1
- [M-SA-004] DRF 查询参数不要用 `format`（会被渲染器后缀拦截），文件类型参数用 `file_type` — conf 0.6 · 证据 registry GR-B-001、IFC-158、TC-INT-105 · 首见 2026-11-10 · 命中 1
- [M-SA-005] Django `bulk_create` 在 MySQL 不回填主键，需按业务键回查；`bulk_update` 不刷新 auto_now — conf 0.6 · 证据 registry GR-B-001、apps/registry/importing.py · 首见 2026-11-10 · 命中 1
- [M-SA-006] `Membership.source` 仅 12 字符，新来源值须 ≤12，否则把来源放进审计 detail — conf 0.6 · 证据 registry GR-B-001、apps/residency/models.py:16 · 首见 2026-11-10 · 命中 1
- [M-SA-007] 新增前端 API 调用前先看 backend/tests/integration/test_frontend_contract.py:30-97：正则只认 `http.`/`adminHttp.` + 字面量路径，路径不带 `?`，管理端接口只能 IsAdmin、用户端只能 IsMember，设计 IFC 时按此写 — conf 0.6 · 证据 test_frontend_contract.py:30-97（git grep）、content GROUP_B-1 · 首见 2026-11-10 · 命中 1
- [M-SA-008] IFC 里类静态方法不要取 list/dict/set 等内建类型名：类体内同名成员遮蔽注解 `list[...]`，Python 3.12/3.13 导入即 TypeError（3.14 延迟注解不报，本地版本新于 CI 时测不出） — conf 0.8 · 证据 content GR-C-002-F01（media.py）、registry GR-D-003-F01 · 首见 2026-11-11 · 命中 2
- [M-SA-009] 凡有"写审计"类 AC，module_design 给"审计落点表"（AC→动作→唯一写入处，含批次/全失败/无任务分支），否则开发只在主路径写审计、漏删除与全人工分支 — conf 0.6 · 证据 content GR-C-002-F03 · 首见 2026-11-11 · 命中 1
## 用户偏好与禁止项
## 待验证
- [P-SA-001] 取微信官方服务端接口文档时，用 `developers.weixin.qq.com/miniprogram/dev/server/API/<分类>/<api_xxx>.md`（带 .md）可拿到干净正文；`/framework/open-ability/*.html` 页面正文过长，WebFetch 只返回导航 — 自记 2026-11-07 · 证据 WebFetch 结果（不可核验）
- [P-SA-002] 小程序"手机号快速验证组件"官方称仅向非个人且已认证主体开放并按次收费，设计上以短信验证码为基线、快速验证做可选开关 — 自记 2026-11-07 · 证据 搜索摘要（非官方原文），开发前复核；官方 getphonenumber 页未写主体与收费
- [P-SA-003] 阿里云验证码短信模板：单变量须 4~6 位、双变量不可自定义，有效期只能写死在模板正文，设计上用启动检查保证与配置有效期一致；平台默认流控与 C-06 同值但窗口算法不同 — 自记 2026-11-07 · 证据 help.aliyun.com 模板规范页与 message-rules 页
- [P-SA-004] 阿里云帮助页 WebFetch 偶发 "Socket is closed"，重试一次即可；api.aliyun.com 错误码页只给名称不给释义，释义标 [UNSOURCED] — 自记 2026-11-07 · 证据 WebFetch 结果
- [P-SA-006] uni-app `rich-text` 会屏蔽节点事件（链接/图片不可点击），小程序要"可点击链接/视频"的富文本应由服务端出结构化块、自定义组件渲染 — 自记 2026-11-10 · 证据 uniapp.dcloud.net.cn/component/rich-text.html（WebFetch 摘要）
- [P-SA-007] 查包信息：npm 用 `registry.npmjs.org/<pkg>/latest`（小）；PyPI 的 `/pypi/<pkg>/json` 超长被截断，改用 `/pypi/<pkg>/<version>/json` 才能看到 upload_time 与轮子文件名 — 自记 2026-11-10 · 证据 WebFetch 结果
- [P-SA-010] 迁移拆分旧版无归属数据时，要提前定义"同人多号吸收并入"规则，否则全量重传会判成冲突 — 自记 2026-11-10 · 证据：设计推演（待真实历史数据迁移复现）
- [P-SA-011] 批量改写带唯一约束的派生列时，新值可能等于另一行的旧值（如 `车库A-088`），单遍更新会中途违反约束；设计为"先全量检测冲突 → 占位值两阶段更新 → 单事务"，MySQL 无事务性 DDL 须在 RunPython 内显式 `transaction.atomic` — 自记 2026-11-11 · 证据 ocap_admin_polish ADR-067（设计推演，待实现与测试验证）
- [P-SA-012] 主题/风格的"仅某一端"覆盖规则要挂在 `<html data-surface>` 之类全局属性上，不能挂布局根类，因 Element Plus 弹层 Teleport 到 body 够不着 — 自记 2026-11-11 · 证据 ocap_admin_polish ADR-075（基线 ADR-026 已述 Teleport）
- [P-SA-013] 设计"替代旧约束"类变更前先 git grep 现有守护测试里对旧约束的断言（如"管理端固定 B"），在 module_design 列出需同步更新的用例清单，避免门控时被判新增失败 — 自记 2026-11-11 · 证据 module_design MOD-073（git grep 实测 4 个前端测试文件）
- [P-SA-014] 渐变背景上放白字：半透明白叠层会变亮、拉低对比度（bento `#DB2777` 端 4.60→3.77），半透明深色叠层恒更暗而不会；本仓库 `scripts/themes/schema.mjs:68` 的 contrast 只收单色 `#RRGGBB`，渐变须"各停点逐一建项 + 测试对插值采样"，`--accent` 恰为 bento 渐变起点色，焦点环在渐变上须改 `--on-hero` — 自记 2026-11-11 · 证据 schema.mjs 的 contrastRatio 本机实算（ocap_admin_polish ADR-075 1.1.0）
