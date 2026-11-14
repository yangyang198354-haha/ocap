<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-14T17:36:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_identity_display/requirements/requirements_spec.md</file>
    <file>backend/apps/identity/services.py</file>
    <file>backend/apps/committee/services.py</file>
    <file>backend/apps/registry/models.py</file>
    <file>frontend/src/portal/Home.vue</file>
    <file>frontend/src/shared/style.css</file>
    <file>miniprogram/pages/index/index.vue</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：用户端身份显示与认证房屋信息（INCREMENTAL）

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-101 | 后端身份与房屋聚合 | 修改 `backend/apps/committee/services.py`、`backend/apps/identity/services.py` | 计算单一最高身份；为 `/me` 补充房屋名称、类型、面积与关系标签 | REQ-FUNC-136~140、REQ-NFUNC-025/026；US-145、US-146 | — |
| MOD-102 | Web 主页身份与认证房屋展示 | 修改 `frontend/src/portal/Home.vue`、`frontend/src/shared/style.css` | 三态身份展示；认证房屋数量 + 逐套明细；空状态 | REQ-FUNC-136/139/140、REQ-NFUNC-024；US-145~147 | MOD-101 |
| MOD-103 | 小程序身份与认证房屋展示 | 修改 `miniprogram/pages/index/index.vue`、`miniprogram/pages/me/index.vue` | 与 Web 同口径的身份文案、认证房屋明细与空状态 | REQ-FUNC-141、REQ-NFUNC-024；US-145、US-146、US-148 | MOD-101 |

## 模块详情

### MOD-101 后端身份与房屋聚合

职责：在不改变认证业务规则的前提下，把“内部角色”映射为用户可见单一身份，并扩展 `/me` 的房屋信息。

文件：
- `backend/apps/committee/services.py`（修改 `CommitteeQuery.identity_labels`）
- `backend/apps/identity/services.py`（修改 `IdentityService.me`）

IFC-247：`CommitteeQuery.identity_labels(user_id: int) -> list[str]`

| 项 | 契约 |
|---|---|
| 输入校验 | `user_id` 为正整数；无对应用户时返回 `["游客"]`，不抛异常（沿用现有行为） |
| 返回值 | 恰好 1 个元素的列表 |
| 优先级 | 有效 `Seat`（`status="ACTIVE"` 且 `term_end >= today`，取 `POSITION_RANK` 最高者）：`主任 / 副主任 / 委员 / 业主代表`；否则有效 `Membership` 中 `HEAD/OWNER` → `产权业主`，仅 `RESIDENT` → `同住人`；都没有 → `游客` |
| 多房屋 | 同一用户存在产权业主与同住人关系时返回 `["产权业主"]`，不并列 |
| 鉴权 | 内部函数，无 HTTP 鉴权；调用方均为已认证上下文（`/me` 为 `IsMember`） |

IFC-248：`GET /api/v1/me`

| 项 | 契约 |
|---|---|
| 鉴权 | 用户 JWT（`IsMember`，`backend/apps/identity/views.py:29-33`） |
| 请求 | 无请求体、无查询参数 |
| 响应 `identities` | `{is_guest: bool, units: IdentityUnitView[], committee: {position: SeatPosition, term_end: date} \| null, labels: string[]}` |
| `IdentityUnitView` | `{unit_id: int, specific_part: str, role: "HEAD" \| "OWNER" \| "RESIDENT", role_label: "产权业主" \| "同住人", unit_type: "RESIDENCE" \| "APARTMENT" \| "SHOP" \| "PARKING" \| "OTHER" \| null, unit_type_label: "住宅" \| "公寓" \| "商铺" \| "车位" \| "其他" \| "未登记", area: str \| null, area_display: string}` |
| `area` 格式 | 两位小数字符串（如 `"89.50"`），未登记为 `null`；由 `Decimal.quantize(Decimal("0.01"))` 生成，避免浮点误差 |
| `area_display` | `"{area} ㎡"`（如 `"89.50 ㎡"`）或 `"未登记"` |
| `is_guest` | `labels == ["游客"]` |
| 排序 | 按 `specific_part` 升序，其次 `unit_id` 升序 |
| 去重 | 同一 `unit_id` 只返回一次；若同一专有部分存在多条有效关系，按 `HEAD/OWNER > RESIDENT` 取一条 |
| 过滤 | 仅 `Membership.ended_at IS NULL`；`Seat` 按有效职务口径 |
| 错误 | 未登录/令牌失效沿用现有 401；无其他新增错误码 |

输入校验（字段来源均为数据库，不接受客户端输入）：`specific_part` 最长 140（`registry/models.py:65`）；`unit_type` 取值限定于 `UNIT_TYPE_CHOICES`（`registry/models.py:10`）；`area` 最大 10 位、2 位小数（`registry/models.py:67`）。

依赖模块：无。外部依赖：无。

### MOD-102 Web 主页身份与认证房屋展示

职责：用 `/me` 的单一身份与房屋明细渲染主页；加载中/失败不显示“游客”。

文件：
- `frontend/src/portal/Home.vue`（修改）
- `frontend/src/shared/style.css`（修改：新增 `.home-units` 明细样式）

IFC-249：主页身份文案

| 项 | 契约 |
|---|---|
| 数据来源 | `useAuthStore().me`、`identities.labels`、`loading`（`frontend/src/stores/auth.js:6-15`） |
| 加载中 | `me === null && loading` → 身份显示“加载中…”；认证房屋数量显示“—” |
| 失败 | `me === null && !loading && meError` → 身份显示“加载失败，请重试”，并提供重试按钮重新调用 `auth.fetchMe()` |
| 成功 | `labels.join('、')`；空数组时显示“游客” |
| 鉴权 | 页面已在登录态路由内；`/me` 401 由 `frontend/src/shared/http.js` 统一处理 |

IFC-250：认证房屋明细

| 项 | 契约 |
|---|---|
| 数量 | `auth.me.identities.units.length`；未加载显示“—”，加载成功且为 0 显示 0 |
| 明细行 | 每行展示 `specific_part`、`unit_type_label`、`area_display`、`role_label` |
| 排序 | 直接使用后端顺序，前端不再排序 |
| 空状态 | 数量 0 时显示“暂无已认证房屋” |
| 展示位置 | 主页统计卡保留“认证房屋”数量；其下新增全宽卡片“认证房屋”，逐行展示明细 |
| 输入校验 | 字段缺失时 `unit_type_label` 回退“未登记”、`area_display` 回退“未登记”、`role_label` 回退“产权业主” |

依赖模块：MOD-101（IFC-248）。外部依赖：无。

### MOD-103 小程序身份与认证房屋展示

职责：与 Web 使用同一 `/me` 契约，展示相同身份与房屋明细。

文件：
- `miniprogram/pages/index/index.vue`（修改）
- `miniprogram/pages/me/index.vue`（修改）

IFC-251：小程序首页身份与房屋

| 项 | 契约 |
|---|---|
| 数据来源 | `useAuthStore().me`、`auth.fetchMe()`（`miniprogram/store/auth.js`） |
| 身份 | `me` 为空显示“加载中…”；成功时 `labels.join('、')`，空数组显示“游客” |
| 数量 | 统计卡“认证房屋”使用 `units.length`；`me` 为空显示“—” |
| 明细 | 统计卡下方新增“认证房屋”卡片，逐行展示 `specific_part`、`unit_type_label`、`area_display`、`role_label` |
| 空状态 | 数量 0 时显示“暂无已认证房屋” |
| “我的”页 | 身份行使用同一 `labels`，`me` 为空显示“加载中…” |
| 鉴权 | 沿用小程序 `http` 拦截器；无新增鉴权 |

依赖模块：MOD-101（IFC-248）。外部依赖：无。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-136 | US-145 | MOD-101（IFC-247/248）、MOD-102、MOD-103 |
| REQ-FUNC-137 | US-145 | MOD-101 |
| REQ-FUNC-138 | US-145 | MOD-101 |
| REQ-FUNC-139 | US-146 | MOD-101、MOD-102、MOD-103 |
| REQ-FUNC-140 | US-146 | MOD-101 |
| REQ-FUNC-141 | US-148 | MOD-102、MOD-103 |
| REQ-NFUNC-024 | US-147 | MOD-102、MOD-103 |
| REQ-NFUNC-025 | US-146 | MOD-101 |
| REQ-NFUNC-026 | US-145、US-146、US-147 | MOD-101 |

## 依赖关系

- MOD-102 → MOD-101（读取 IFC-248）
- MOD-103 → MOD-101（读取 IFC-248）

已检查：无循环依赖。

## 数据迁移

无。本次不新增/修改数据库字段，不产生迁移。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 操作 |
|---|---|---|
| systemd `ocap-backend` | 后端 Python 代码变更 | 重启（部署时由 E2 执行，需另行授权） |
| Web 前端 | `Home.vue`、`style.css` 变更 | 重新构建静态产物并发布（同上） |
| 微信小程序 | 首页与“我的”页变更 | 重新构建小程序包并由用户侧发布 |
| 定时任务 / 消息队列 | 无 | — |

## 领域与外部依赖出处

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| MOD-101 | 身份优先级与枚举：HEAD/OWNER/RESIDENT | `[CODE: backend/apps/residency/models.py:8]` |
| MOD-101 | 有效职务过滤与排序：POSITION_RANK、term_end | `[CODE: backend/apps/committee/services.py:11、31-34]`，职务枚举 `committee/models.py:27` |
| MOD-101 | 专有部分类型枚举与面积精度 | `[CODE: backend/apps/registry/models.py:10、66-67]` |
| MOD-101 | `/me` 现有响应结构 | `[CODE: backend/apps/identity/services.py:17-45]` |
| MOD-102 | 主页现有身份与统计卡 | `[CODE: frontend/src/portal/Home.vue:9、107-108]` |
| MOD-103 | 小程序现有身份与统计卡 | `[CODE: miniprogram/pages/index/index.vue:8、80-85]` |
