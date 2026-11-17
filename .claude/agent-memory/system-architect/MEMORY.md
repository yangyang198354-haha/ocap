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
- [M-SA-010] DRF 列表增加跨表派生字段优先固定 prefetch + 应用层计算，并用“每页查询数不随行数增长”测试守 N+1；跨表搜索用 Exists 避免 distinct 放大 — conf 0.6 · 证据 GR-B-001-F02 / TC-INT-397 · 首见 2026-11-11 · 命中 1
- [M-SA-011] 共享展示型聚合函数被多个输出面复用时，改口径前枚举全部消费方，在“唯一来源”（identity_view）改一次再批量调整下游断言，不在调用处分别打补丁 — conf 0.8 · 证据 GR-B-001 / GB-3 / IFC-247；product_review 合并 TC-INT-478/480；backend/apps/accounts/directory.py identity_view · 首见 2026-11-14 · 命中 2
- [M-SA-012] 需单独授权的数据修正不放 Django 数据迁移（部署每次跑 migrate --noinput，测试 MIGRATION_MODULES 置空测不到）；用默认 dry-run 的 management command，apply 要求 --backup 与 --expect-changes — conf 0.6 · 证据 .agents/skills/ocap-deploy/SKILL.md:149、unit_sort_filters ADR-101 · 首见 2026-11-16 · 命中 1
- [M-SA-013] 改 RegistryUnit.building 会经 build_specific_part 重算 specific_part，且有标识与四元组两道唯一约束；批量改归属须按最终状态预演两类冲突，冲突即整批停止；改写唯一派生列新值可能等于另一行旧值，用先检测+占位值两阶段+单事务 — conf 0.8 · 证据 backend/apps/registry/models.py build_specific_part、ADR-101、M-SD-023（独立观察） · 首见 2026-11-11 · 命中 2
- [M-SA-014] 同一用户在同一专有部分可有 OWNER+RESIDENT 两条有效 Membership：/me 按专有部分去重，/me/housing 不去重；统一排序只排房屋行输出，不动传给 identity_view 的 memberships 顺序 — conf 0.6 · 证据 backend/tests/integration/test_identity_display.py:118-123 · 首见 2026-11-16 · 命中 1
- [M-SA-015] 改私有函数签名前先 git grep 测试对它的直接导入（如 _parse_amount），新增参数带缺省值保持旧调用兼容 — conf 0.6 · 证据 backend/tests/unit/test_domain_rules.py、test_product_review_rules.py 直接导入 · 首见 2026-11-13 · 命中 1
- [M-SA-016] 需求写“Web 已有明细/入口”时读页面核对；报表 API 的支出事由违反 OQ-08（show_expense_reason 配置），新增移动端入口前先在服务端脱敏 — conf 0.6 · 证据 product_review GR-B-001-F01、backend/apps/ledger/views.py、backend/apps/core/config.py · 首见 2026-11-13 · 命中 1
- [M-SA-017] 导出/备份文件不能放进部署根（/home/yangyang/ocap/）内：预检要求该目录仅 backend/web/snapshots，回滚会 rm -rf backend；放同级目录（ocap_exports，700）并在命令里做位置守卫 — conf 0.8 · 证据 SKILL.md:93、owner_auth_v2 ADR-110、deployment_report DEPLOY-010/012 实际执行 · 首见 2026-11-16 · 命中 2
- [M-SA-018] 附件无权访问现为 404；需求要 401/403 时在附件策略 `can_open`（如 residency/apps.py）内对“已登录无权者”抛 403，不动通用 open；先自行 grep 现有 404 断言（GR-B-001-F01：引用的 test_rework_cr011_024.py:376 并非 404 断言） — conf 0.6 · 证据 core/attachments.py、owner_auth_v2 ADR-112、GR-B-001-F01 · 首见 2026-11-16 · 命中 1
- [M-SA-019] 把原楼栋写入 unit_no 时纯数字要补“栋”，否则 build_specific_part 会生成“商铺1单元…” — conf 0.6 · 证据 backend/apps/registry/models.py `_SUFFIXES`、owner_auth_v2 ADR-106 · 首见 2026-11-16 · 命中 1
- [M-SA-020] 页内分区改二级菜单：默认分区沿用旧路径、其余加子路径并用路由 `props:{section}`，旧书签与既有路径断言不变；同组件在兄弟路由间复用实例，宿主须 watch(section) — conf 0.6 · 证据 ADR-119、frontend/src/router/index.js:8,39-46（开发已按此落地，GR-C-003 通过） · 首见 2026-11-17 · 命中 1
- [M-SA-021] 宽窄屏分流的路由守卫用 matchMedia 时，jsdom 无该 API，约定缺失按窄屏，否则既有"点击底栏我的→/me"类用例会变 — conf 0.6 · 证据 ADR-120、frontend/src/router/index.js:26 · 首见 2026-11-17 · 命中 1
- [M-SA-022] 新增 SVG 配图等 .vue 不得写颜色字面量（theme.spec 守护），颜色经 scoped CSS 取 var(--accent)；UnitCascader 不回显初值 id，跨页预填房屋不可行，只能预填姓名 — conf 0.6 · 证据 frontend/src/portal/parts/UnitCascader.vue:40、ocap_ui_theme ADR-029 · 首见 2026-11-17 · 命中 1
- [M-SA-023] 给 /me/housing 等被契约测试用 assertEqual 锁定字段集的接口加字段前，先 git grep 该集合（test_frontend_contract.py:582-585），并在 module_design 列出要改的断言；页面循环变量名（item/unit/r）会被 reads() 扫描，新组件用别的变量名 — conf 0.6 · 证据 ocap_identity_property ADR-131、git grep 核验 · 首见 2026-11-17 · 命中 1
- [M-SA-024] "触发时机一次性、之后清册变化不得触发"的引导类需求，用"服务端状态行（触发点有匹配才建行）+ 匹配实时查询"，不存快照也不做无状态查询；代价是 PENDING 期间清册新增同号会出现（须列 ASSUMPTION） — conf 0.6 · 证据 ocap_identity_property ADR-128（architecture_design.md:45-54、:129） · 首见 2026-11-17 · 命中 1
## 用户偏好与禁止项
## 待验证
- [P-SA-001] 取微信官方服务端接口文档时，用 `developers.weixin.qq.com/miniprogram/dev/server/API/<分类>/<api_xxx>.md`（带 .md）可拿到干净正文；`/framework/open-ability/*.html` 页面正文过长，WebFetch 只返回导航 — 自记 2026-11-07 · 证据 WebFetch 结果（不可核验）
- [P-SA-002] 小程序"手机号快速验证组件"官方称仅向非个人且已认证主体开放并按次收费，设计上以短信验证码为基线、快速验证做可选开关 — 自记 2026-11-07 · 证据 搜索摘要（非官方原文），开发前复核；官方 getphonenumber 页未写主体与收费
- [P-SA-003] 阿里云验证码短信模板：单变量须 4~6 位、双变量不可自定义，有效期只能写死在模板正文，设计上用启动检查保证与配置有效期一致；平台默认流控与 C-06 同值但窗口算法不同 — 自记 2026-11-07 · 证据 help.aliyun.com 模板规范页与 message-rules 页
- [P-SA-004] 阿里云帮助页 WebFetch 偶发 "Socket is closed"，重试一次即可；api.aliyun.com 错误码页只给名称不给释义，释义标 [UNSOURCED] — 自记 2026-11-07 · 证据 WebFetch 结果
- [P-SA-006] uni-app `rich-text` 会屏蔽节点事件（链接/图片不可点击），小程序要"可点击链接/视频"的富文本应由服务端出结构化块、自定义组件渲染 — 自记 2026-11-10 · 证据 uniapp.dcloud.net.cn/component/rich-text.html（WebFetch 摘要）
- [P-SA-007] 查包信息：npm 用 `registry.npmjs.org/<pkg>/latest`（小）；PyPI 的 `/pypi/<pkg>/json` 超长被截断，改用 `/pypi/<pkg>/<version>/json` 才能看到 upload_time 与轮子文件名 — 自记 2026-11-10 · 证据 WebFetch 结果
- [P-SA-010] 迁移拆分旧版无归属数据时，要提前定义"同人多号吸收并入"规则，否则全量重传会判成冲突 — 自记 2026-11-10 · 证据：设计推演（待真实历史数据迁移复现）
- [P-SA-013] 设计"替代旧约束"类变更前先 git grep 现有守护测试里对旧约束的断言（如"管理端固定 B"），在 module_design 列出需同步更新的用例清单，避免门控时被判新增失败 — 自记 2026-11-11 · 证据 module_design MOD-073（git grep 实测 4 个前端测试文件）
- [P-SA-014] 渐变背景上放白字：半透明白叠层会变亮、拉低对比度（bento `#DB2777` 端 4.60→3.77），半透明深色叠层恒更暗而不会；本仓库 `scripts/themes/schema.mjs:68` 的 contrast 只收单色 `#RRGGBB`，渐变须"各停点逐一建项 + 测试对插值采样"，`--accent` 恰为 bento 渐变起点色，焦点环在渐变上须改 `--on-hero` — 自记 2026-11-11 · 证据 schema.mjs 的 contrastRatio 本机实算（ocap_admin_polish ADR-075 1.1.0）
- [P-SA-017] uni-app 文档中 `uni.chooseFile` 小程序不支持，`wx.chooseMessageFile` 仅 mp-weixin（参数在微信文档），小程序传 pdf 须核微信官方文档，否则本批只做图片 — 自记 2026-11-16 · 证据 [WEB: https://uniapp.dcloud.net.cn/api/media/file.html，2026-11-16]（WebFetch 摘要，未核对微信原文）
