<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-17T18:12:16+08:00</timestamp>
  <project_name>ocap_identity_property</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_property/requirements/requirements_spec.md（1.0.0）</file>
    <file>project_workspace/ocap_identity_property/requirements/user_stories.md（1.0.0）</file>
    <file>project_workspace/ocap_brand_layout/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：我的身份与房屋整合、认证产权入口与手机号匹配引导认证（INCREMENTAL）

## 架构概览

本批是在现有 Django + DRF（`backend/apps/residency`、`accounts`、`identity`、`registry`）、Vue 3 Web 用户端（`frontend/src/portal`、`layout`、`router`、`stores`）、uni-app 小程序（`miniprogram/pages/units|phone|index`）上的增量改动，不新增运行单元、不引入新依赖（沿用画像 P1 技术栈）。

改动位置分三块：

1. **后端（唯一的新增能力）**：取消"注册 / 首次绑定手机号后静默自动绑定"（`backend/apps/accounts/views.py:117`、`backend/apps/identity/views.py:46-47`），改为"服务端记录一条待确认状态 → 前端引导 → 用户确认 → 服务端重新校验后绑定"。新增 1 张表（`residency.PhoneMatchPrompt`）与 3 个端点（`GET /me/registry-matches`、`POST /me/registry-matches/confirm`、`POST /me/registry-matches/dismiss`）；`/me/housing` 的 `units[]` 增加类型与面积两个只读字段。
2. **Web 用户端**：`/me/identity` 与 `/units` 同一页面；"待我审批的同住人申请"并入该页底部并仅产权业主可见；"选择房屋"改"认证产权"；"申请成为同住人"迁到 `/units/applications`；主页大卡片删除。主要改 `layout/menus.js`、`router/index.js`、`portal/units/*.vue`、`portal/Home.vue`、`portal/Register.vue`、`portal/me/MePhone.vue`、`stores/housing.js`、`shared/api.js`。
3. **小程序**：同批同步，单页（`pages/units/index.vue`）内重排卡片，`pages/phone/index.vue` 与 `pages/index/index.vue` 小改，`utils/api.js` 同步新接口（画像 P6 契约同步）。

关键质量属性（引 REQ-NFUNC）：
- **隐私最小化（REQ-NFUNC-043）**：匹配响应只含 `unit_id`、专有部分坐落名称、类型；不含清册姓名、他人手机号、完整手机号；匹配只用"当前登录用户自己账号上的已验证手机号"，请求中没有"手机号"入参，因此无法探测任意手机号。
- **不绕过认证规则（C-71、REQ-FUNC-235）**：确认接口不信任前端传来的单元列表，服务端以用户当前手机号重新查询清册，请求中任一 `unit_id` 不在匹配集合内即整批拒绝（同一错误出口，REQ-NFUNC-037）；沿用每用户每小时 30 次限频。
- **可见性与权限一致（REQ-NFUNC-042）**：审批接口的后端判定不改（`backend/apps/residency/views.py:299-303`），前端卡片以"当前有效房屋中存在产权业主关系"判定显示。
- **零回归（REQ-NFUNC-044）**：所有既有接口路径、方法、错误码不变；仅 `/me/housing` 的 `units[]` 增字段、注册/绑定手机号响应增字段；两份后端契约测试静态读取前端源码，须随页面改动同步（见 module_design"测试影响"）。

## 部署视图

| 组件 | 运行单元 | 环境（画像 P7） |
|---|---|---|
| Django 后端（新增迁移 `residency/0004`、3 个端点） | systemd `ocap-backend`（gunicorn 127.0.0.1:9000）+ `manage.py migrate` | 测试（树莓派） |
| Web 前端（`frontend/` 构建产物） | nginx 8090 静态目录 `web/`（构建 `npm run build -- --base=/ocap/`） | 测试 |
| 小程序（`miniprogram/`） | 无服务端运行单元；需在微信开发者工具重新构建并发布体验版 | 测试 |

生产环境不存在（画像 P7），本批不涉及。

## ADR

### ADR-128: 手机号匹配结果如何在注册后与稍后取得，以及"不是"的状态记录
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-233、234、236、REQ-NFUNC-043、C-71，用户答复 Q-IP-09=A、Q-IP-11=A、Q-IP-12=A。触发时机仅为"手机号注册成功"和"已注册用户首次绑定手机号成功（非合并）"；用户可能刷新页面、关闭浏览器后稍后回到"认证产权"页（AC-241-03）；用户选"不是"后不再强制弹出；清册事后新增手机号、更换手机号不得触发（C-25/C-26 基线，AC-239-05、AC-239-09）。现状：匹配结果只在注册/绑定响应的 `auto_bound` 中一次性返回（`accounts/views.py:117`），刷新即丢失；无任何用户级状态字段。
- Options:
  - A 仅在注册/绑定响应中返回匹配列表，前端放内存或 sessionStorage。优：无后端存储、无迁移。缺：刷新或换设备即丢，无法满足"稍后进入认证产权页再取得"（AC-241-03）；响应中携带完整列表，且确认时仍需另行服务端校验；"不是"状态只能放本机，换设备会再次引导。
  - B 无状态实时查询：新增 `GET /me/registry-matches` 每次按 `user.phone` 查清册，"不是"记在前端 localStorage。优：无迁移。缺：无法区分"注册/首次绑定时触发"与"之后清册新增手机号"——用户一进认证产权页就会看到事后补录的匹配，违反 C-26/AC-239-09；"不是"不跨设备。
  - C 服务端持久化"待确认"状态行（用户一行，状态 PENDING / DISMISSED / DONE / EXPIRED），匹配列表每次按当前手机号实时查询（不存快照）。优：触发资格由服务端在触发点一次性确定（触发点没有匹配则不建行，之后清册新增不会触发）；刷新、换设备都能取回；"不是"跨设备一致；确认时可再次校验"状态 PENDING + 实时匹配"。缺：新增 1 张表与迁移；实时查询意味着 PENDING 期间清册新增同号码的专有部分也会出现在列表（该号码已通过用户本人验证，且仍须用户逐套勾选确认，影响可接受）。
  - D 与 C 相同，但额外把触发时的 `unit_id` 列表存为快照（JSON 列或子表）。优：触发后清册变化完全不影响列表。缺：多一个 JSON 列或子表；MySQL/SQLite 双环境对 JSON 的行为差异增加风险 `[ESTIMATE]`；收益仅覆盖 PENDING 期间的极端边界。
- Decision: 选 C。新增模型 `residency.PhoneMatchPrompt`（`user` 一对一、`status`、`created_at`、`resolved_at`），在 `RegisterView` 与 `PhoneBindView`（非合并）成功后由 `PhoneMatchService.open_prompt(user)` 查询"该手机号登记且用户尚非其产权业主"的专有部分，**有结果才建/更新为 PENDING**，响应增加 `registry_match: {pending: bool, count: int}`（不含任何坐落或姓名）供前端决定是否强制跳转；前端取明细一律走 `GET /me/registry-matches`。用户选"不是"→ `DISMISSED`；确认（含部分成功）→ `DONE`；更换手机号或发生账号合并时 → `EXPIRED`（AC-239-05、AC-239-12）。强制跳转只发生一次（注册/绑定响应之后）；之后再登录不强制弹出，用户进入"认证产权"页时若状态仍为 PENDING 则以面板形式被动显示匹配（覆盖 AC-241-03）。因为 REQ-FUNC-233/234 要求"触发资格在触发点确定、之后可取回、状态跨设备"，A、B 无法满足；D 的额外收益不抵 JSON 跨库风险。
- Consequences: 正向：满足刷新/稍后可取回、"不是"跨设备、清册后补不触发；不泄露快照。负向：新增一张表和迁移（见 module_design"数据迁移"）；PENDING 期间清册新增同号码专有部分会进入列表（已在开放问题登记）；`GET` 对每次进入认证产权页多一次查询（仅 PENDING 用户才查清册，其余直接返回空）。

### ADR-129: 确认接口形态与服务端重新校验
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-235、C-71、REQ-NFUNC-043、REQ-NFUNC-037，US-240（AC-240-02 可取消勾选、AC-240-04 部分失败给出成功/失败套数、AC-240-06 未登记手机号的专有部分被拒、限频 30 次/小时）。现有手动认证 `POST /certifications` 要求 `unit_id` + `name`（`backend/apps/residency/views.py:49-69`），一次只认证一个专有部分。
- Options:
  - A 复用 `POST /certifications`，增加 `via_phone_match: true` 时免姓名。优：不新增端点。缺：在已有认证入口上加"免姓名"旁路，一旦判定写错即成为绕过姓名核对的通道（直接违背 C-71）；一次仅一套，12 套要 12 次请求且每次计入限频；响应契约被污染。
  - B 新增 `POST /me/registry-matches/confirm`，入参 `unit_ids: list[int]`（仅作为"用户勾选"），服务端以当前账号手机号 `RegistryService.units_by_phone` 重新计算匹配集合并校验：状态必须 PENDING；`unit_ids` 必须是匹配集合子集，任一不在集合内 → 整批拒绝 422 `OWNER_NOT_MATCHED`（与手动认证同一错误出口，不泄露清册信息）；通过后逐套在独立 savepoint 内调用 `MembershipService.certify_owner`（沿用先到先得户主规则与审计），按套返回结果。优：认证规则不变且旁路面最小（入参无姓名、无手机号）；支持勾选与部分失败；限频与手动认证共用 `certify:{user.id}` 键。缺：新增一个端点与一个服务类。
  - C 无入参的"全部确认"端点：服务端对当前全部匹配一次性认证。优：最简单、没有前端传参风险。缺：不满足 AC-240-02（取消勾选）与 Q-IP-17（已选套数提示）。
- Decision: 选 B。端点路径、校验与错误见 module_design IFC-333。理由：唯一同时满足"可取消勾选、部分失败可核对、服务端不信任前端单元列表、不改手动认证通路"（REQ-FUNC-235、C-71）的方案。审计沿用 `MembershipService.certify_owner(..., origin="REGISTRY_AUTO")`（审计来源文案仍为"清册自动绑定"，`backend/apps/residency/services.py:65-66`），并追加脱敏手机号到审计 detail。
- Consequences: 正向：认证规则、户主先到先得、同住人升级、审计全部复用；限频口径一致。负向：整批拒绝策略意味着前端传了非法 `unit_id` 时用户看不到部分成功（正常 UI 不会发生，视为异常路径）；一次请求内多套逐套提交事务，请求耗时随套数线性增长（设请求体上限 500 套，见 IFC-333）。

### ADR-130: 取消静默绑定后注册 / 绑定手机号响应的兼容策略
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-236、REQ-NFUNC-044（注册与绑定手机号接口的路径、方法、字段、错误码不变）。现响应含 `auto_bound` 数组（`accounts/views.py:117`、`identity/views.py:46-47`），前端三处读取（`Register.vue:54`、`MePhone.vue:66`、`miniprogram/pages/phone/index.vue:68`）。
- Options:
  - A 删除 `auto_bound` 字段。优：语义干净。缺：属于响应字段删除，违反 REQ-NFUNC-044 的"字段不变"；旧缓存的前端包读取 `result.auto_bound || []` 虽安全，但契约测试、其他调用方不可知。
  - B 保留 `auto_bound`，恒返回空数组 `[]`，新增 `registry_match: {pending, count}`。优：旧调用方不报错；字段只增不删。缺：存在一个"永远为空"的字段，需注释说明并在后续批次移除。
  - C 新开版本化路由。优：彻底隔离。缺：路径变更违反 REQ-NFUNC-044，工作量大，无收益。
- Decision: 选 B。`auto_bound` 恒为 `[]`（注释标注"已弃用，恒空，保留仅为兼容"），不再调用 `AutoBindService.bind_by_phone`；类 `AutoBindService` 保留（现有单元测试直接导入并调用它：`backend/tests/unit/test_registry_import_defects.py:14,117`；另有测试 patch 它来断言"不被调用"：`test_owner_auth_v2_residency.py:580-583`），其逐套 savepoint 循环抽出为共享函数供 `PhoneMatchService.confirm` 复用。
- Consequences: 正向：旧客户端兼容，字段只增不减。负向：残留一个恒空字段；约 5 个后端测试文件中对 `auto_bound` 非空的断言必须改为"为空 + `registry_match.pending` 为真 + 未建立 Membership"（module_design 测试影响列出）。

### ADR-131: 房屋明细（类型、面积）的数据来源
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-224、REQ-FUNC-237(a)、REQ-NFUNC-044。类型与面积现仅在 `/me` 的 `identities.units`（`backend/apps/identity/services.py:30-38`），`/me/housing` 的 `units[]` 没有（`backend/apps/residency/housing.py:23-30`）；"我的身份与房屋"页与小程序"我的房屋"页都以 `/me/housing` 为数据源，且需要同住人名单。
- Options:
  - A 在 `/me/housing` 的 `units[]` 增加 `unit_type_label`、`area_display`（两个只读字段，口径与 `/me` 一致：未登记显示"未登记"），格式化逻辑抽到 `apps/registry/display.py` 供两处共用。优：页面单一数据源、加载失败可统一处理（AC-232-05）；字段只增不减。缺：改一个后端序列化，并同步更新严格相等的契约断言（`backend/tests/integration/test_frontend_contract.py:582-585` 对 `set(unit)` 用 `assertEqual`）。
  - B 前端按 `unit_id` 把 `/me/housing` 与 `auth.me.identities.units` 合并。优：不动后端。缺：两个请求两个失败面，`auth.me` 未加载时短暂缺列；小程序需重复同样的合并；顺序与过滤口径需前端自行保持一致。
- Decision: 选 A。理由：REQ-FUNC-224/237 要求两端显示同一口径、AC-232-05 要求失败时统一显示"加载失败"；单一数据源最稳。
- Consequences: 正向：Web 与小程序都只读 `/me/housing`；格式化逻辑只有一份。负向：触及 `/me/housing` 序列化与一个严格相等的契约测试；两个页面源码读取型契约测试（`reads(text, ["unit"]) ⊆ set(unit)`）要求页面只读这些字段。

### ADR-132: `/me/identity` 与 `/units` 同页显示及左侧导航高亮
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-225、US-233；用户答复 Q-IP-01=A（两个地址都保留并直接显示同一页面，不跳转）、Q-IP-16 暂定 A（经右上角入口进入也展开"我的房屋"并高亮二级项）。现状：`/me/identity` → `MeIdentity.vue`，`/units` → `Units.vue`（`props.section='identity'`）（`frontend/src/router/index.js:29,36-40`）；导航匹配由 `layout/menus.js` 的 `resolveActive`/`isPathMatch` 决定，一级项"我的房屋"仅匹配 `/units` 前缀（`menus.js:7`）。
- Options（被排除）: 一个地址、另一个地址 `redirect`（用户答复 Q-IP-01=A 已否决，地址栏须保持所访问的地址，后退一次回到点击前页面）；另写一个包装组件（多一个文件而路由已能用同一组件两条记录，符合 ADR-119 同组件多路由的既有做法，`router/index.js:9-10`）。
- Decision: 路由层让 `me/identity` 也指向 `UnitsPage`（`props: { section: 'identity' }`）；`menus.js` 中一级项 `units` 的 `match` 增加 `'/me/identity'`，二级项 `units.identity` 增加 `activeOn: ['/me/identity']`（`resolveActive` 已支持 `activeOn`，`menus.js:106-109`）。不动 `PORTAL_USER_MENU` 的 `to`，仅把标签 `我的身份` 改为 `我的身份与房屋`（窄屏"我的"总览页 `Me.vue` 与右上角 `PortalUserMenu.vue` 都遍历该常量，自动同步）。`MeIdentity.vue` 不再被路由使用，删除（其唯一路由引用在 `router/index.js:29`）。
- Consequences: 正向：两个地址、一个组件、一个名字；高亮与展开与 `/units` 一致，无需改 `SideNav.vue`。负向：窄屏在 `/me/identity` 下会出现"我的房屋"的二级切换条（因 `active.node.children` 存在，`PortalLayout.vue:18`），这是 Q-IP-16=A 的自然结果。

### ADR-133: "待我审批的同住人申请"并入身份页底部及旧地址兼容
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-227、228、REQ-NFUNC-042，US-234/235，Q-IP-04=A、Q-IP-13=A。现状：独立二级页 `UnitsReview.vue`，菜单项与页面对所有人可见（`menus.js:10`）；主页链接 `/units/review`（`Home.vue:12`）；旧地址 `/units#review` 在路由守卫中重定向到 `/units/review`（`menus.js:91`、`router/index.js:36-40`）；侧栏角标由 `badge: 'pendingReview'` 驱动（`menus.js:10`）。
- Options:
  - A 把 `UnitsReview.vue` 作为子组件嵌入 `UnitsIdentity.vue` 底部，仅当有效房屋中存在 `HEAD`/`OWNER` 角色时渲染；删除二级项 `units.review`，把 `badge` 移到 `units.identity`；`/units/review` 改为 `redirect` 到 `/units#review`，`LEGACY_UNITS_HASH` 删去 `#review` 项（`/units#review` 本身就是目的地），由 `UnitsIdentity` 在数据加载后按路由 `hash === '#review'` 滚动到卡片。优：卡片逻辑与既有测试（`UnitsReview` 组件）可原样复用；旧地址都落到同一页；定位逻辑只有一处。缺：`UnitsIdentity` 增加对 `UnitsReview` 的引用和滚动逻辑。
  - B 保留 `/units/review` 为独立路由与页面，仅把菜单项隐藏并在身份页放链接。优：改动最小。缺：不满足用户"放到页面底部"的原意，且卡片内容分散在两处。
  - C 以 query 参数 `?focus=review` 定位而非 hash。优：不依赖 hash。缺：旧书签 `/units#review` 仍需额外映射；与现有 hash 兼容约定（brand_layout REQ-FUNC-215）不一致。
- Decision: 选 A。非产权业主到 `/units/review` 或 `/units#review` 时落到身份页且无该卡片（AC-235-03）。显示判定只用于展示；权限仍由后端 403 把关（`views.py:301-303`，REQ-NFUNC-042）。主页链接改为 `to="/units#review"`。
- Consequences: 正向：用户原意满足、卡片集中、旧书签不 404。负向：侧栏二级项从 6 个变 5 个、`LEGACY_UNITS_HASH` 的值变化会让前端既有用例（`frontend/tests/layout_menus.spec.js:65`、`layout_router.spec.js:123-127`、`layout_e2e.spec.js:187,233-235`）需同步更新；`reviewLoaded`/`toReview` 在 `housing` store 中仍由 `loadLists()` 驱动，身份页需在挂载时调用它。

### ADR-134: "申请成为同住人"迁至 `/units/applications`，接口不变
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-229、232、238、C-72、US-236/238/243；用户答复 Q-IP-05=C、Q-IP-15 与 Q-IP-18 暂定 A。现状：两个按钮并排在 `UnitsPick.vue:11-12`，申请逻辑 `applyResident`（`UnitsPick.vue:55-57`），接口 `POST /resident-applications`（`frontend/src/shared/api.js:48`；校验 409 三类错误 `backend/apps/residency/views.py:255-262`）。
- Options（被排除）: 同页分区（Q-IP-05=A，用户未选）；另设"申请成为同住人"二级菜单（Q-IP-05=B，未选）；改后端接口或错误口径（C-72 禁止）。
- Decision: 后端不改。`UnitsApplications.vue` 上方新增发起区（复用 `portal/parts/UnitCascader.vue` + "申请成为同住人"按钮 + 说明），下方沿用申请列表（页面标题、菜单名不变，Q-IP-18=A 暂定）；`UnitsPick.vue` 去掉同住人按钮与相关说明、标题与菜单标签改为"认证产权"、姓名框改文案、加指向 `/units/applications` 的提示链接（Q-IP-15=A 暂定）。
- Consequences: 正向：接口与规则零改动，风险集中在前端页面文案与归属。负向：`UnitCascader.vue` 现在被两个页面各用一次（`UnitCascader` 无初值回显能力，保持不变）；前端、后端契约测试按"页面源码读取字段名"的断言，新增页面的循环变量须避开 `item.`/`unit.`/`r.` 三个被扫描的前缀（见 module_design 测试影响）。

### ADR-135: 小程序同步方式（单页重排 vs 拆分子页）
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-237、US-242；现状小程序"我的房屋"为单页 6 张卡片（`miniprogram/pages/units/index.vue:4-69`），无新的页面路由约束；小程序注册由微信登录 + 绑定手机号承载（`pages/phone/index.vue`），无独立注册页。
- Options:
  - A 单页内重排卡片顺序：身份与房屋明细（含类型/面积、同住人、"认证产权"按钮与无绑定提醒）、匹配引导卡片（仅 PENDING 时显示）、认证产权、认证申诉、我的同住人申请（含发起区）、我的申诉、待我审批（仅产权业主，置底）。优：不动 `pages.json`，不新增页面路由，沿用 `onShow(refresh)` 数据流（`units/index.vue:131`）。缺：页面更长。
  - B 拆成多个子页面对应 Web 的二级菜单。优：与 Web 结构一致。缺：新增页面需改 `pages.json`、导航与测试大量重写；超出 REQ-FUNC-237 范围（"小程序业务页面其他重排"属超出范围）。
- Decision: 选 A。手机号绑定成功且 `registry_match.pending` 为真时，`pages/phone/index.vue` 用 `uni.navigateTo` 进入 `/pages/units/index`，该页 `onShow` 拉取 `GET /me/registry-matches` 展示引导卡片（置顶）。首页 `pages/index/index.vue` 的"认证房屋"逐套明细并入"我的房屋"页，首页保留数量与进入链接。
- Consequences: 正向：小程序无新路由；与 Web 共用同一组接口。负向：页面更长；小程序的引导是"页内置顶卡片"而非独立页，交互与 Web 略有差异（AC-242-04 只要求出现引导确认，满足）。

## 开放问题 / ASSUMPTION

1. **[用户待确认] Q-IP-15~18 按推荐项 A 设计**：Q-IP-15 认证产权页含"如需申请成为同住人，请前往「我的同住人申请」"链接；Q-IP-16 经 `/me/identity` 进入时左侧展开并高亮；Q-IP-17 匹配超过 10 套时折叠部分也默认勾选且确认按钮旁显示"已选 N 套"；Q-IP-18 "我的同住人申请"页标题与菜单名不变、发起区在列表上方。用户改答后只改对应页面文案与 UI 结构，不影响后端。
2. **[ASSUMPTION] PENDING 期间清册新增同号码专有部分会出现在列表**（ADR-128 负向后果）：选择实时查询而非快照；若用户要求"触发后清册变化完全不影响"，改用 ADR-128 的方案 D（多一个 JSON 列或子表）。
3. **[ASSUMPTION] 强制跳转只发生一次**：注册/首次绑定响应之后若用户未操作（关闭浏览器），再次登录不强制弹出，仅在"认证产权"页以面板形式显示（对应 Q-IP-11=A "不再强制弹出"的合理外推；US-241 AC-241-03 只要求"仍无关系且提醒仍在"）。
4. **[ASSUMPTION] `GET /me/registry-matches` 不限频**：其只读且只查本人手机号，无探测风险；确认接口与手动认证共用 30 次/小时限频。
5. **[ASSUMPTION] 确认请求体上限 500 个 `unit_ids`**：需求要求"不设硬上限"指界面展示，请求体上限仅作防滥用的健壮性保护，远大于现实的一号多户数量。
6. **P11-3 微信/短信接口**：本批不改调用方式；绑定手机号的验证码校验仍走既有 `IdentityService.bind_phone`，设计未触及任何闭源 API。
7. **审计中的手机号脱敏**：需求 AC-240-05 要求审计含脱敏手机号，而现有 `certify_owner` 审计 detail 不含手机号（`backend/apps/residency/services.py:63-67`）；设计新增可选参数 `detail_extra`（带缺省，旧调用不变），由确认流程传入 `{"phone_masked": mask_phone(user.phone)}`（`apps/core/masking.py` 已有 `mask_phone`，`identity/views.py:6` 已导入）。
