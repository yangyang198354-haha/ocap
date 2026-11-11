<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-11T22:34:05.7369915+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>../ocap/architecture/module_design.md</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 模块设计（增量）

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求/US | 依赖 |
|---|---|---|---|---|---|
| MOD-062 | 后端用户目录聚合 | 新建 `backend/apps/accounts/directory.py`；修改 `backend/apps/accounts/serializers.py`、`backend/apps/accounts/views.py` | 计算最高身份、认证套数、清册实名；扩展实名搜索；输出目录字段 | REQ-FUNC-123 ~ 128、REQ-NFUNC-019/020；US-132 ~ 136 | 既有 `residency`、`committee`、`registry` 模型 |
| MOD-063 | Web 后台账号页展示 | 修改 `frontend/src/admin/AdminUsers.vue`、`frontend/src/shared/format.js` | 展示身份、认证状态、实名、上次登录；搜索框支持实名 | REQ-FUNC-123 ~ 127、REQ-NFUNC-019；US-132 ~ 135 | MOD-062（经 IFC-243） |

## 模块详情

### MOD-062 后端用户目录聚合

职责：在不改变现有分页、权限与手机号脱敏行为的前提下，为注册用户列表补充只读目录信息；不写库、不新增表、不改变认证流程。

文件：
- `backend/apps/accounts/directory.py`（新建）：纯计算与查询过滤，不依赖 DRF。
- `backend/apps/accounts/serializers.py`（修改 `AdminUserSerializer`）：增加 `SerializerMethodField`。
- `backend/apps/accounts/views.py`（修改 `AdminUserListView.get`）：固定预取与搜索条件扩展。

#### IFC-243：GET /api/v1/admin/users（变更）

- 鉴权：沿用 `IsAdmin`（`backend/apps/accounts/views.py:386`）。未登录 401；非管理员 403，与现状一致。
- 请求参数：
  - `q: str`，可选，最长 32 字符（超出截断，沿用现状）；匹配账号、昵称、完整手机号、手机号后 4 位，并在本次新增实名匹配。
  - `page: int`，可选，默认 1；非法值按 1 处理（沿用 `page_response`）。
  - `page_size: int`，可选，默认 20，范围 1 ~ 100（沿用 `backend/apps/core/serializers.py:5-13`）。
- 响应 200：

```json
{
  "count": 1,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 1,
      "account_no": "1000000001",
      "phone": "138****0001",
      "nickname": "业主甲",
      "status": "ACTIVE",
      "identity_code": "HEAD",
      "identity_label": "户主",
      "certified_units": 2,
      "real_names": ["张三", "李四"],
      "last_login_at": "2026-11-10T09:05:00+08:00"
    }
  ]
}
```

- 字段类型与语义：
  - `identity_code: "CHAIR" | "VICE_CHAIR" | "MEMBER" | "REPRESENTATIVE" | "HEAD" | "OWNER" | "RESIDENT" | "GUEST"`：最高身份代码。
  - `identity_label: str`：对应中文标签（主任/副主任/委员/业主代表/户主/产权业主/同住人/游客）。
  - `certified_units: int`：当前有效认证的专有部分去重数量，≥0；无认证为 0。
  - `real_names: string[]`：清册实名去重列表，最多与有效产权房屋数相同；非产权业主或未匹配时为空数组 `[]`。
  - `last_login_at: string | null`：ISO8601；从未登录为 `null`。
  - `phone` 保持既有脱敏格式（`MaskedPhoneField`，`backend/apps/accounts/serializers.py:15`）。
- 错误类型：沿用全局 `{code,message,details}` 错误体；权限错误沿用现有机制。
- 输入校验：`q` 截断 32 字符；`page/page_size` 夹取到合法范围；不做额外 SQL 拼接。

#### IFC-244：`DirectoryService.identity_view`

```python
class IdentityView(TypedDict):
    identity_code: str
    identity_label: str

def identity_view(
    *, memberships: Sequence[Membership], seats: Sequence[Seat]
) -> IdentityView: ...
```

- 输入：仅传入调用方已过滤的“当前有效”记录（Membership `ended_at is null`；Seat `status="ACTIVE"` 且 `term_end >= 今天`）。
- 优先级：Seat 按 `POSITION_RANK`（CHAIR 4 > VICE_CHAIR 3 > MEMBER 2 > REPRESENTATIVE 1）取最高；无 Seat 时按 Membership 角色（HEAD 3 > OWNER 2 > RESIDENT 1）；都无则 `GUEST/游客`。
- 纯函数，无数据库访问；无异常分支；空输入返回 `GUEST/游客`。

#### IFC-245：`DirectoryService.certified_units` / `real_names`

```python
def certified_units(*, memberships: Sequence[Membership]) -> int: ...

def real_names(*, user: User, memberships: Sequence[Membership]) -> list[str]: ...
```

- `certified_units`：对有效 Membership 的 `unit_id` 去重计数。
- `real_names`：仅取角色为 `HEAD`/`OWNER` 的有效 Membership；要求 `user.phone` 非空；在对应专有部分已预取的清册业主中，找出手机号等于 `user.phone` 的业主，收集其姓名；按 Membership 顺序（`certified_at, id`）去重，保留首次出现顺序；无匹配返回 `[]`。
- 不额外查询数据库：使用预取的 `membership.unit.owners` 与 `owner.phones`。

#### IFC-246：`DirectoryService.filter_by_real_name`

```python
def filter_by_real_name(qs: QuerySet[User], q: str) -> QuerySet[User]: ...
```

- 语义：在 `qs` 上追加“实名匹配”条件，与现有条件为 OR 关系由调用方组合。
- 实现契约：使用 `Exists` 子查询，条件为存在一条有效 Membership，满足：
  - `user_id = 外层 User.id`；
  - `role in ("HEAD", "OWNER")`；
  - `ended_at is null`；
  - 同一清册手机号记录满足 `phone = 外层 User.phone` 且 `owner.name__icontains = q`。
- 不产生重复行（`Exists` 不放大结果集），无需 `distinct()`。
- `q` 为空时返回原 `qs`。

### MOD-063 Web 后台账号页展示

职责：在现有“账号”页注册用户表中展示新增列；不新增页面或路由。

文件：
- `frontend/src/admin/AdminUsers.vue`（修改）：新增 4 列；搜索框占位文案追加“实名”。
- `frontend/src/shared/format.js`（修改）：新增 `formatDateTime(value: string | null): string`，把 ISO8601 按浏览器本地时区格式化为 `YYYY-MM-DD HH:mm`，空值返回空字符串。

展示规则（对应 US-132 ~ 135）：
- 身份列：`identity_label`。
- 认证列：`certified_units > 0 ? \`已认证（${certified_units} 套）\` : '未认证'`。
- 实名列：`real_names.length ? real_names.join('、') : '—'`。
- 上次登录列：`formatDateTime(last_login_at) || '从未登录'`。
- 手机号继续使用后端脱敏值，不在前端还原。
- 列宽：身份 110、认证 130、实名 140、上次登录 160；保留既有列与分页组件。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-123 最高身份 | US-132 | MOD-062（IFC-244）、MOD-063 |
| REQ-FUNC-124 认证数量 | US-132 | MOD-062（IFC-245）、MOD-063 |
| REQ-FUNC-125 清册实名 | US-133 | MOD-062（IFC-245）、MOD-063 |
| REQ-FUNC-126 上次登录时间 | US-134 | MOD-062（IFC-243 字段）、MOD-063 |
| REQ-FUNC-127 原列/搜索 + 实名搜索 | US-135 | MOD-062（IFC-243/246）、MOD-063 |
| REQ-FUNC-128 撤销后一致性 | US-136 | MOD-062（有效记录过滤）、MOD-063 |
| REQ-NFUNC-019 权限与隐私 | US-132、US-135 | MOD-062（IsAdmin、脱敏）、MOD-063（只展示脱敏值） |
| REQ-NFUNC-020 列表响应时限 | US-135 | MOD-062（固定预取） |

## 依赖关系

- MOD-063 → MOD-062（调用 IFC-243）
- MOD-062 → 既有 `apps.residency.models.Membership`、`apps.committee.models.Seat`、`apps.registry.models.RegistryUnit/RegistryOwner/RegistryPhone`
- MOD-062 → 既有 `apps.core.serializers.page_response`、`apps.core.masking.MaskedPhoneField`
- 已检查：无循环依赖。

## 数据迁移

无。本次不新增/修改任何表、字段、索引或约束。

## 受影响的运行单元 / 构建

| 运行单元 | 变更 | 操作 |
|---|---|---|
| `ocap-backend`（gunicorn 127.0.0.1:9000） | `AdminUserListView` 响应增加计算字段与实名搜索 | 重新发布代码后重启服务 |
| Web 前端静态产物 | 账号页新增 4 列与时间格式化 | 重新构建并发布静态文件 |
| `ocap-content-worker`、定时任务、小程序 | 无改动 | 无需操作 |
| 数据库 | 无迁移 | 无需操作 |

## 测试建议（供 GROUP_D 使用）

- 后端集成：最高身份优先级（含过期席位）、认证套数去重、实名匹配/空手机号/未匹配/多姓名去重、撤销后不再展示、实名搜索命中/未命中、非管理员 403、原搜索行为不变、分页大小与排序不变、查询数固定（每页不随行数增长）。
- 前端：新增 4 列渲染与空值文案；`formatDateTime` 对空值与 ISO 字符串的输出。
- 回归：后端全量 `python manage.py test --settings=config.test_settings` 零新增失败；前端 `npm test` 零新增失败。

## 领域与外部依赖出处

不适用（画像 P11 无新增硬件、算法或闭源 API；本次仅使用仓库内现有模型与接口）。
