<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-17T18:12:16+08:00</timestamp>
  <project_name>ocap_identity_property</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_property/requirements/requirements_spec.md（1.0.0）</file>
    <file>project_workspace/ocap_identity_property/requirements/user_stories.md（1.0.0）</file>
    <file>project_workspace/ocap_identity_property/architecture/architecture_design.md（0.1.0）</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计（INCREMENTAL）

编号延续全仓最大值（`git grep` 核对：ADR-127、MOD-131、IFC-331）：本批 ADR-128~135、MOD-132~138、IFC-332~344。

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-132 | 清册匹配引导服务（后端） | **新建** `backend/apps/residency/phone_match.py`；**新建** `backend/apps/residency/migrations/0004_phone_match_prompt.py`；**修改** `backend/apps/residency/models.py`（加模型）、`views.py`（加 3 个视图）、`urls.py`（加 3 条路由）、`auto_bind.py`（抽出共享函数，类保留）、`services.py`（`certify_owner` 加可选参数） | 持久化待确认状态；实时计算匹配；校验并批量确认认证；记录"不是" | REQ-FUNC-233/234/235/236；US-239/240/241；REQ-NFUNC-043 | MOD-134（展示字段）、registry `RegistryService`、core `RateLimiter`/`AuditService` |
| MOD-133 | 注册 / 首次绑定手机号入口改造（后端） | **修改** `backend/apps/accounts/views.py`（`RegisterView`）、`backend/apps/identity/views.py`（`PhoneBindView`、`PhoneChangeView`） | 取消静默绑定，改为开启待确认状态并在响应中提示 | REQ-FUNC-233/236；US-239/241 | MOD-132 |
| MOD-134 | 房屋明细字段（后端） | **新建** `backend/apps/registry/display.py`；**修改** `backend/apps/residency/housing.py`、`backend/apps/identity/services.py`（改用共享函数，输出不变） | `/me/housing` 增加类型与面积；统一格式化口径 | REQ-FUNC-224/237；US-232、242 | — |
| MOD-135 | Web 导航与路由 | **修改** `frontend/src/layout/menus.js`、`frontend/src/router/index.js`、`frontend/src/portal/Units.vue`、`frontend/src/portal/Home.vue`；**删除** `frontend/src/portal/me/MeIdentity.vue` | 菜单改名与二级项调整、两个地址同页、旧地址兼容、主页大卡片删除与入口调整 | REQ-FUNC-225/226/228/229/231(b)；US-232(AC-232-04)/233/235/236/237(AC-237-05) | MOD-136 |
| MOD-136 | Web 身份与房屋页 | **修改** `frontend/src/portal/units/UnitsIdentity.vue`、`frontend/src/portal/units/UnitsReview.vue`（改为可嵌入卡片）、`frontend/src/stores/housing.js` | 房屋明细、认证产权按钮、无绑定提醒、底部待审批卡片（仅产权业主）、加载失败态 | REQ-FUNC-224/227/228/230/231(a)；REQ-NFUNC-042/045；US-232/234/235/237 | MOD-134（经 IFC-337） |
| MOD-137 | Web 认证产权、同住人申请、引导面板 | **新建** `frontend/src/portal/parts/RegistryMatchPanel.vue`；**修改** `frontend/src/portal/units/UnitsPick.vue`、`UnitsApplications.vue`、`frontend/src/portal/Register.vue`、`frontend/src/portal/me/MePhone.vue`、`frontend/src/shared/api.js` | 认证产权页文案与只做认证、引导面板、同住人申请发起、注册 / 绑定后跳转 | REQ-FUNC-229/232/234/235/236/238；US-236/238/239/240/241/243 | MOD-132（经 IFC-332~334）、MOD-135 |
| MOD-138 | 小程序同步 | **修改** `miniprogram/pages/units/index.vue`、`miniprogram/pages/phone/index.vue`、`miniprogram/pages/index/index.vue`、`miniprogram/utils/api.js`；**新建** `miniprogram/components/RegistryMatchCard.vue` | 与 Web 同步改动 | REQ-FUNC-237；US-242（含 US-232~243 对应部分） | MOD-132、MOD-134（经 IFC-332~334、337） |

## 模块详情

### MOD-132 清册匹配引导服务

**职责**：见总览。核心规则：状态 PENDING 才可匹配与确认；匹配集合永远由"当前账号手机号 + 清册"实时计算；前端传来的 `unit_ids` 只被视为"用户勾选"，必须是匹配集合子集。

**模型**（`backend/apps/residency/models.py`，新增）

```python
class PhoneMatchPrompt(models.Model):
    STATUSES = [("PENDING", "待确认"), ("DISMISSED", "已选不是"), ("DONE", "已确认"), ("EXPIRED", "已失效")]

    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="phone_match_prompt")
    status = models.CharField(max_length=12, choices=STATUSES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
```

`status` 最长 `DISMISSED`（9 字），取 `max_length=12`（项目教训：新增枚举值先核长度）。不存手机号、不存清册信息、不存单元快照（ADR-128）。

**服务**（`backend/apps/residency/phone_match.py`，新建）

IFC-335：
```python
@dataclass(frozen=True)
class MatchUnit:
    unit_id: int
    specific_part: str
    unit_type_label: str          # 复用 apps.registry.display，未登记为 "未登记"

@dataclass(frozen=True)
class ConfirmItem:
    unit_id: int
    specific_part: str
    ok: bool
    role: str | None              # ok 时 "HEAD" | "OWNER"
    code: str | None              # 未成功时的错误码，如 "ALREADY_CERTIFIED"

class PhoneMatchService:
    @staticmethod
    def open_prompt(user) -> int:
        """触发点调用：user.phone 刚通过验证码校验。计算"该手机号登记且 user 尚非产权业主"的专有部分数 n；
        n>0 → 建立/重置 PhoneMatchPrompt 为 PENDING（resolved_at=None）并返回 n；n=0 → 不建行（已有行不改），返回 0。
        不向外抛异常（失败记日志并返回 0），不得影响注册/绑定主流程。"""

    @staticmethod
    def pending_matches(user) -> list[MatchUnit]:
        """状态非 PENDING、用户无手机号、或实时匹配为空 → []。匹配集合 = RegistryService.units_by_phone(user.phone)
        排除 user 已是产权业主者；按 unit_sort_key 自然顺序（apps.registry.ordering）。"""

    @staticmethod
    def confirm(user, unit_ids: list[int]) -> list[ConfirmItem]:
        """前置：已通过限频。状态须为 PENDING，否则 ApiError("MATCH_NOT_PENDING", "当前没有待确认的清册匹配", 409)。
        校验集合 = RegistryService.units_by_phone(user.phone)（含用户已是产权业主者）；unit_ids 中任一不在集合内 →
        ApiError("OWNER_NOT_MATCHED", "未能通过清册核对", 422)，整批不执行。
        逐套：已是产权业主 → ConfirmItem(ok=False, code="ALREADY_CERTIFIED")；否则在独立 transaction.atomic()（savepoint）内
        MembershipService.certify_owner(user.id, unit_id, "REGISTRY", origin="REGISTRY_AUTO",
        detail_extra={"phone_masked": mask_phone(user.phone)})，成功 ok=True、role；其它 ApiError/异常按套捕获并记 code（未知异常 code="FAILED"），
        不影响其余套。处理完把状态置 DONE、resolved_at=now（无论成功几套）。"""

    @staticmethod
    def dismiss(user) -> None:
        """PENDING → DISMISSED；其它状态或无行时为空操作（幂等）。"""

    @staticmethod
    def expire(user) -> None:
        """PENDING → EXPIRED（换手机号、账号合并时调用）；其它状态为空操作。"""
```

`auto_bind.py`：把现有 `bind_by_phone` 的逐套 savepoint 循环抽成模块级函数 `certify_units(user, units, origin) -> list[AutoBound]` 供 `bind_by_phone` 自身与 `PhoneMatchService.confirm` 共用其 savepoint 写法；`AutoBindService.bind_by_phone` 保持签名与行为不变但**不再被任何视图调用**（保留理由见 ADR-130）。

`services.py`：`MembershipService.certify_owner(user_id, unit_id, source, origin=None, detail_extra: dict | None = None) -> str`，`detail_extra` 合并进审计 `detail`（缺省 `None`，旧调用不受影响；M-SA-015）。

**HTTP 接口**（`backend/apps/residency/views.py`、`urls.py`，挂在 `/api/v1/`，与 `me/housing` 同级）

IFC-332 `GET /api/v1/me/registry-matches`
- 鉴权：`IsMember`（与 `MyHousingView` 一致，`views.py:34-37`）；只作用于 `request.user`，无手机号/用户标识入参。
- 输入校验：无入参（忽略所有查询参数）。
- 响应 200：`{"pending": bool, "total": int, "units": [{"unit_id": int, "specific_part": str, "unit_type_label": str}]}`；不含清册姓名、手机号、面积。状态非 PENDING 或无匹配时 `{"pending": false, "total": 0, "units": []}`（不报错、不区分原因）。
- 错误：未登录 401（既有）。

IFC-333 `POST /api/v1/me/registry-matches/confirm`
- 鉴权：`IsMember`；先 `RateLimiter.hit(f"certify:{user.id}", limit=30, window_seconds=3600)`，与 `CertificationView` 共用键（`views.py:41-43`），超限 `RateLimited` 429。
- 请求：`{"unit_ids": list[int]}`；校验：必须是非空列表、元素为整数（`bool`、字符串数字之外的非 int 拒绝）、去重后 1~500 个；否则 400 `INVALID_VALUE`"缺少专有部分"。**请求不含姓名、手机号。**
- 响应 200：`{"succeeded": int, "failed": int, "results": [{"unit_id": int, "specific_part": str, "ok": bool, "role": "HEAD" | "OWNER" | null, "code": str | null}]}`；`role` 不向用户端展示"户主"字样（前端以"产权业主"呈现，C-75）。
- 错误：409 `MATCH_NOT_PENDING`；422 `OWNER_NOT_MATCHED`（与手动认证同码，details 不含清册信息，REQ-NFUNC-037）；429 `CODE_RATE_LIMITED`；400 `INVALID_VALUE`。

IFC-334 `POST /api/v1/me/registry-matches/dismiss`
- 鉴权：`IsMember`；请求体忽略；响应 204；幂等（无行或非 PENDING 亦 204）。

### MOD-133 入口改造

- IFC-336 `POST /api/v1/auth/register`（`RegisterView`，鉴权沿用"无需登录"：注册接口，验证码即凭据；输入校验沿用 `PHONE_RE`、6 位数字验证码，`accounts/views.py:106-111`）。响应 201 在原字段基础上：`auto_bound` 恒为 `[]`（弃用）；新增 `registry_match: {"pending": bool, "count": int}`，`count = PhoneMatchService.open_prompt(user)`。取消 `AutoBindService.bind_by_phone` 调用。
- `POST /api/v1/me/phone/bind`（`PhoneBindView`，鉴权 `IsMember`，输入校验沿用）：非合并时同样调用 `open_prompt(request.user)`；合并成功（`merged=True`）时 `registry_match = {"pending": false, "count": 0}` 并调用 `PhoneMatchService.expire(request.user)`；`auto_bound` 恒 `[]`。
- `POST /api/v1/me/phone/change`（`PhoneChangeView`）：成功后调用 `PhoneMatchService.expire(request.user)`（合并后令牌已换，`request.user` 为旧账号，其行不再有意义，一并过期；响应结构不变）。
- 依赖：MOD-132。外部依赖：无（验证码校验仍在 `IdentityService`，P11-3 的短信/微信调用方式不变）。

### MOD-134 房屋明细字段

IFC-338（`backend/apps/registry/display.py`，新建）：
```python
def unit_type_label(unit) -> str: ...        # unit.get_unit_type_display() 或 "未登记"
def area_text(unit) -> str | None: ...       # Decimal 两位小数字符串；无面积 None
def area_display(unit) -> str: ...           # f"{area_text} ㎡" 或 "未登记"
```
`IdentityService._unit_view`（`identity/services.py:30-38`）改调这三个函数，输出逐字不变；`housing_view`（`residency/housing.py:60-70`）每套增加 `unit_type_label`、`area_display`。

IFC-337 `GET /api/v1/me/housing`（既有 `MyHousingView`，鉴权 `IsMember`、无入参，不变）`units[]` 新增只读字段：`unit_type_label: str`、`area_display: str`（缺失时均为"未登记"）。`HousingUnit` TypedDict 同步加两个字段。需 `select_related("unit")` 已存在（`housing.py:44`），无新增查询。

### MOD-135 Web 导航与路由

IFC-339 `frontend/src/layout/menus.js`：
```js
PORTAL_MENU[units] = {
  key: 'units', label: '我的房屋', audience: 'all', match: ['/units', '/me/identity'],
  children: [
    { key: 'units.identity',     label: '我的身份与房屋', to: '/units', activeOn: ['/me/identity'], badge: 'pendingReview' },
    { key: 'units.pick',         label: '认证产权',       to: '/units/pick' },
    { key: 'units.appeal',       label: '认证申诉',       to: '/units/appeal' },
    { key: 'units.applications', label: '我的同住人申请', to: '/units/applications' },
    { key: 'units.appeals',      label: '我的申诉',       to: '/units/appeals' }
  ]
}
PORTAL_USER_MENU[me.identity] = { key: 'me.identity', label: '我的身份与房屋', to: '/me/identity' }
export const LEGACY_UNITS_HASH: Record<string, string> = { '#appeal': '/units/appeal' }   // 删去 '#review'
```
`resolveActive`/`isPathMatch`/`nextOpenKey` 签名与实现不改（`menus.js:93-124` 已支持 `activeOn`）。

IFC-340 `frontend/src/router/index.js`：
- `me/identity` → `component: UnitsPage, props: { section: 'identity' }`（复用文件顶部已有的 `UnitsPage` 动态导入，`router/index.js:9`）。
- `units/review` → `{ path: 'units/review', redirect: { path: '/units', hash: '#review' } }`；从 `['review','pick','appeal','applications','appeals']` 的映射中去掉 `'review'`。
- `units` 路由 `beforeEnter` 只处理 `#appeal`（因 `LEGACY_UNITS_HASH` 已无 `#review`）。
- `/units/pick` 路径不变（旧地址兼容，AC-236-03）。

`Units.vue`：`VIEWS` 去掉 `review`、导入去掉 `UnitsReview`（卡片改为被 `UnitsIdentity` 嵌入）。
`Home.vue`：删除大卡片 `section.home-units`（`Home.vue:39-54` 范围，含 `unitRows` 逐套渲染）；"认证房屋"小卡片（`stats` 首项）改为可点击进入 `/units`，数量为 0 时说明文案处显示"去认证产权"链接指向 `/units/pick`；`pendingReview` 链接 `to="/units#review"`；快捷入口"认证我的房屋"改 `to: '/units/pick'`。
鉴权：路由均在 `PortalLayout` 子路由下，沿用 `router.beforeEach` 登录守卫（`router/index.js:92-98`）。

### MOD-136 Web 身份与房屋页

IFC-341 `frontend/src/stores/housing.js`（`useHousingStore`）新增：
```js
state: { housingError: false, ... }         // loadHousing 失败置 true、成功置 false；UnitsIdentity 据此显示"加载失败，请重试"，不显示"暂无已认证房屋"
getters: { ownsAnyUnit: (s) => s.housing.units.some((u) => u.role === 'HEAD' || u.role === 'OWNER') }
```
`loadHousing` 抛错行为不变（调用方已 `ElMessage` 处理），仅在 `catch` 前后设置标志。

`UnitsIdentity.vue`：标题"我的身份与房屋"；汇总身份；逐套行 = 名称 + 类型 + 面积 + 关系标签（读 `unit.unit_type_label`、`unit.area_display`，ADR-131）；保留"退出"与同住人名单、"移除"；"认证产权"按钮（`router.push('/units/pick')`，所有人可见）；`housing.units` 为空且无加载失败时显示提醒"您还没有认证任何专有部分，请先认证产权"+入口；底部 `<UnitsReview v-if="store.ownsAnyUnit" />`；挂载时 `store.loadHousing()` 与 `store.loadLists()`，完成后若 `route.hash === '#review'` 且卡片存在则 `document.getElementById('review')?.scrollIntoView?.()`（jsdom 无该方法须容错）。
`UnitsReview.vue`：去掉对外层 `.card` 的独占性假设，保持 `id="review"`，其余逻辑不变（`unitApi.decideResidentApplication`、`store.refresh()`）。
权限说明：前端判定仅控制显示；后端 `ResidentApplicationToReviewView` 只返回当前用户产权单元上的申请，审批接口 403（`views.py:279-286,299-303`），不改。

### MOD-137 Web 认证产权、同住人申请、引导面板

IFC-342 `frontend/src/portal/parts/RegistryMatchPanel.vue`：
```ts
// props: 无（自行取数）；emits: 'resolved'（确认完成或选"不是"后）
// 内部状态：matches: {unit_id:number, specific_part:string, unit_type_label:string}[]；selected: Set<number>（默认全选，含折叠部分，Q-IP-17=A）；expanded: boolean
// 展示：>10 套时前 10 套直接显示，其余折叠，"展开更多（还有 N 套）"；确认按钮旁"已选 N 套"；已选 0 套时"是，确认认证"禁用
// 询问文案：`我们发现您的手机号登记在 ${specific_part}（${unit_type_label}）名下，您是该专有部分的业主吗？`；多套时列表（循环变量用 `match`，不得用 item/unit/r，见测试影响）
// 动作：mount → meApi.registryMatches()；pending=false 时不渲染；确认 → meApi.confirmRegistryMatches([...selected])，按 results 提示"认证成功…"或"成功 X 套，未成功 Y 套"，之后 auth.fetchMe() + store.refresh()；"不是" → meApi.dismissRegistryMatches()
```
IFC-343 `frontend/src/shared/api.js`（`meApi` 新增，调用写字面量路径且不带 `?`，以满足契约正则 `test_frontend_contract.py:30-33`）：
```js
registryMatches: () => get('/me/registry-matches'),
confirmRegistryMatches: (unitIds) => post('/me/registry-matches/confirm', { unit_ids: unitIds }),
dismissRegistryMatches: () => post('/me/registry-matches/dismiss', {})
```
`miniprogram/utils/api.js` 同三项（`http.get` / `http.post`）。`register` 与 `bindPhone` 返回值读取新字段 `registry_match`。

`UnitsPick.vue`：标题"认证产权"；姓名框标签"您本人的姓名"、占位"请输入您本人的姓名（须与业主清册登记的姓名一致）"；去掉"申请成为同住人"按钮与相关说明、说明文字不含"户主"；增加一行链接"如需申请成为同住人，请前往「我的同住人申请」"→ `/units/applications`（Q-IP-15=A 暂定）；顶部渲染 `<RegistryMatchPanel />`（仅 PENDING 时可见，用户选"不是"或确认后消失）。`certify` 逻辑（姓名必填、`OWNER_NOT_MATCHED` 转申诉并带入姓名）不变。
`UnitsApplications.vue`：上方发起区（`UnitCascader` + "申请成为同住人"按钮，未选房屋时禁用；说明"申请成为同住人无需输入姓名，同住人须先有产权业主，由产权业主审批"；提交调用既有 `unitApi.createResidentApplication({ unit_id })`，成功提示"申请已提交，等待产权业主审批"并 `store.loadLists()`，409 错误提示沿用 `errorText(e)`）；下方列表不变。
`Register.vue`：`submit` 中删除 `auto_bound` 分支；若 `result.registry_match?.pending` 为真则 `ElMessage.success('注册成功')` 后 `router.replace('/units/pick')`，否则原行为（`router.replace('/')`）。
`MePhone.vue`：`afterPhoneChange` 删除"已根据你的手机号自动认证"提示；非合并且 `result.registry_match?.pending` 为真时 `router.push('/units/pick')`，其余提示不变（"手机号已更新"/"账号已合并…"）。

### MOD-138 小程序同步

- `miniprogram/pages/units/index.vue`（单页，ADR-135）：卡片顺序为 (1) 引导卡片（`<RegistryMatchCard>`，PENDING 时置顶）；(2) 我的身份与房屋（逐套名称/类型/面积/关系、退出、同住人与移除、"认证产权"按钮——滚动到本页"认证产权"卡片；无有效房屋时提醒文案同 Web）；(3) 认证产权（标题改名，姓名占位改为"请输入您本人的姓名（须与业主清册登记的姓名一致）"，去掉"申请成为同住人"按钮，保留"认证"）；(4) 认证申诉；(5) 我的同住人申请（上方发起区：`UnitPicker` + 按钮，未选房号时 toast"请先选择房号"；下方列表）；(6) 我的申诉；(7) 待我审批的同住人申请，仅 `housing.units` 含 `HEAD`/`OWNER` 时渲染，位于最底部。变量命名遵守契约测试读取规则（循环变量 `unit`/`r`/`item` 仅读取既有字段）。
- IFC-344 `miniprogram/components/RegistryMatchCard.vue`：与 `RegistryMatchPanel` 同逻辑（折叠 >10 套、默认全选、"已选 N 套"、"是，确认认证"/"不是"），数据经 `api.registryMatches()`、`api.confirmRegistryMatches`、`api.dismissRegistryMatches`；`emit('resolved')` 后页面 `refresh()`。
- `miniprogram/pages/phone/index.vue`：`done(result)` 删除"已绑定并按清册自动认证 N 个专有部分"；非合并且 `result.registry_match?.pending` → `uni.navigateTo({ url: '/pages/units/index' })`，否则 toast"已完成"。
- `miniprogram/pages/index/index.vue`：删除"认证房屋"逐套明细（`index.vue:39-42` 的 `v-for`），保留数量并点击 `go('/pages/units/index')`；待审批链接保持 `go('/pages/units/index?review=1')`（该页已有 `id="review"` 卡片，非产权业主无该卡片）。
- 鉴权：小程序沿用 `Authorization` 令牌与 `IsMember` 端点（同 Web）。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-224 | US-232 | MOD-134、MOD-136 |
| REQ-FUNC-225 | US-233 | MOD-135 |
| REQ-FUNC-226 | US-232（AC-232-04） | MOD-135 |
| REQ-FUNC-227 | US-234 | MOD-136 |
| REQ-FUNC-228 | US-235 | MOD-135、MOD-136 |
| REQ-FUNC-229 | US-236、US-243 | MOD-135、MOD-137 |
| REQ-FUNC-230 | US-237 | MOD-136 |
| REQ-FUNC-231 | US-237、US-232(AC-232-03) | MOD-135、MOD-136 |
| REQ-FUNC-232 | US-238 | MOD-137 |
| REQ-FUNC-233 | US-239 | MOD-132、MOD-133 |
| REQ-FUNC-234 | US-239 | MOD-132、MOD-137 |
| REQ-FUNC-235 | US-240 | MOD-132、MOD-137 |
| REQ-FUNC-236 | US-241 | MOD-133、MOD-137 |
| REQ-FUNC-237 | US-242 | MOD-138（含 MOD-132、134 的接口） |
| REQ-FUNC-238 | US-243 | MOD-137 |
| REQ-NFUNC-042 | US-234、US-240 | MOD-136（显示）、既有后端 403 |
| REQ-NFUNC-043 | US-239、US-240、US-242 | MOD-132、MOD-137、MOD-138 |
| REQ-NFUNC-044 | 全部 | 全部 MOD + 测试同步 |
| REQ-NFUNC-045 | US-236、US-238 | MOD-135、MOD-137、MOD-138 |

## 依赖关系

- MOD-133 → MOD-132（调用 IFC-335 `PhoneMatchService.open_prompt` / `expire`）
- MOD-132 → MOD-134（调用 IFC-338 展示函数）
- MOD-136 → MOD-134（读取 IFC-337 响应字段，HTTP）
- MOD-137 → MOD-132（HTTP IFC-332/333/334）；MOD-137 → MOD-135（路由 `/units/pick`、`/units/applications`）
- MOD-135 → MOD-136（路由挂载 `UnitsPage` → `UnitsIdentity`）
- MOD-138 → MOD-132、MOD-134（HTTP IFC-332/333/334/337）
- 后端内：`residency.phone_match` → `registry.services`、`registry.display`、`residency.services`、`core.ratelimit`、`core.audit`、`core.masking`；`accounts.views`/`identity.views` → `residency.phone_match`（`identity` 已依赖 `residency`，`identity/views.py:12-13`，不新增反向依赖）。
- 已检查：无循环依赖。

## 数据迁移

- **有**：`backend/apps/residency/migrations/0004_phone_match_prompt.py`，**手写**、单 app（residency），文件头不得含 "Generated by Django"（画像 P6/P8）；依赖 `("residency", "0003_appeal_owner_name")` 与 `accounts` 最新迁移（以 `ls backend/apps/accounts/migrations` 为准，开发时核对）。
- 内容：`CreateModel PhoneMatchPrompt`（`id`、`user` OneToOne→`accounts.User`、`status` CharField(12)、`created_at`、`resolved_at`）。无索引追加（`user` 唯一约束已覆盖查询）。
- 可逆：是（`DeleteModel`），迁移前后均不改其它表。
- 数据风险：无存量数据转换；**不回填**既有用户（已静默绑定者不追溯，C-58）；新表不含个人信息。测试环境 `MIGRATION_MODULES` 置空，测试以模型直接建表，迁移文件需用 `makemigrations --check` 之外的方式人工核对（画像 P4 禁止提交 makemigrations 产物）。

## 受影响的运行单元 / 构建

- 后端：`manage.py migrate`（residency 0004）后重启 systemd `ocap-backend`。
- Web 前端：重新构建 `npm run build -- --base=/ocap/` 并发布静态目录（`web/`）。
- 小程序：重新构建并在微信开发者工具上传体验版（无服务端单元）。
- 无新增 systemd 服务、定时任务、环境变量；无 nginx 变更。
- **受影响的后端契约与回归测试（M-PM-006，只改前端也须跑后端全量，画像 P4）**：
  - `backend/tests/integration/test_frontend_contract.py`：`:30-97` 路由正则读取 `api.js`（新增 3 个调用须字面量路径、无 `?`，经 `IsMember`）；`:582-585` 严格相等的 `/me/housing` 单元字段集合须加 `unit_type_label`、`area_display`；`:588-610` 读取 `Units.vue` 拆分源（含 `UnitsReview.vue`、`UnitsIdentity.vue` 等）的字段检查——`reads(text, ["unit"])`、`["r"]`、`["item"]`、`["item.applicant"]`、`["item.unit"]` 须是接口字段子集，新代码中这些变量名只读既有字段，引导面板循环变量用 `match`；`:450-453`、`:557`、`:633` 的 Units/小程序 units 源码检查；`:118-122` 全量扫描所有 `.vue`。
  - `backend/tests/integration/test_owner_auth_v2_contract.py`：`:23-32,56-58` 读取 `Units.vue` 与 `portal/units/*.vue`、小程序 `pages/units/index.vue`、`UnitPicker.vue`。
  - 断言 `auto_bound` 非空的后端用例须改为"空 + `registry_match.pending` + 无 Membership"并补确认用例：`backend/tests/e2e/test_gap_journeys.py:32`、`test_gap_must_have.py:270-285`、`test_registry_import_enhancement.py:746,806`、`test_registry_import_xlsx_defects.py:149`；`test_owner_auth_v2_residency.py:580-583`（patch `AutoBindService.bind_by_phone`，类保留则仍通过）；`backend/tests/unit/test_registry_import_defects.py:14,117`（直接测 `AutoBindService`，保留则不受影响）。
  - 前端 vitest（改名、二级项数量、`#review` 映射、`MeIdentity` 删除）：`layout_menus.spec.js`（`:41,51,65,131,143,164`）、`layout_e2e.spec.js`（`:187,210,233-235`）、`layout_nav.spec.js`（`:130,226,251`）、`layout_pages.spec.js`（`:27,33,141,221,229-232,240-259,285,390,488`）、`layout_router.spec.js`（`:123-127,180`）、`owner_auth_v2.spec.js`、`product_review_ui.spec.js`（`:24-28,86-109,161-202`）、`user_menu.spec.js`（`:60,114`）。
  - 小程序 vitest：`owner_auth_v2.spec.js`、`pages.spec.js`、`product_review_core.spec.js`、`product_review_ui.spec.js`（含"选择房屋""申请成为同住人""auto_bound"文案断言，以 `git grep` 为准）。
- 新增用例位置（画像 P3）：`backend/tests/{unit,integration,e2e}/test_phone_match_*.py`、`frontend/tests/identity_property_*.spec.js`、`miniprogram/tests/identity_property_*.spec.js`。

## 领域与外部依赖出处

画像 P11 非"无"，本批判定如下：

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| IFC-336、`/me/phone/bind` | 验证码校验与手机号写入沿用既有 `IdentityService.bind_phone`，不触碰微信/阿里云调用 | [CODE: backend/apps/identity/views.py:40-48] |
| MOD-132 `units_by_phone` | 手机号→清册专有部分的查询口径 | [CODE: backend/apps/registry/services.py:17-22] |
| MOD-132 `certify_owner` | 户主先到先得、同住人升级、审计 | [CODE: backend/apps/residency/services.py:45-77] |
| 小程序绑定手机号 | 微信手机号快速验证本批不改 | 不适用（未触及 P11-3 的调用方式） |

本批没有新增或修改任何闭源 API 的端点、字段或调用顺序。
