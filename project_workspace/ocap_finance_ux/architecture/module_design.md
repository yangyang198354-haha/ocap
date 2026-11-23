<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-23T22:48:59.9533029+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.1</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_finance_ux/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_finance_ux/requirements/user_stories.md</file>
    <file>backend/apps/ledger/models.py</file>
    <file>backend/apps/ledger/services.py</file>
    <file>backend/apps/ledger/views.py</file>
    <file>backend/apps/ledger/urls.py</file>
    <file>backend/apps/income/models.py</file>
    <file>backend/apps/income/services.py</file>
    <file>backend/apps/claims/models.py</file>
    <file>backend/apps/claims/services.py</file>
    <file>frontend/src/portal/Reports.vue</file>
    <file>frontend/src/portal/Home.vue</file>
    <file>frontend/src/layout/menus.js</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计 — ocap_finance_ux

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求/US | 依赖 |
|---|---|---|---|---|---|
| MOD-192 | 账户模型与余额服务 | 修改 `backend/apps/ledger/models.py`、`backend/apps/ledger/services.py` | 账户实体、默认账户解析、余额与最近流水聚合 | REQ-FUNC-336/337/341、REQ-NFUNC-068 | — |
| MOD-193 | 流水账户归属 | 修改 `backend/apps/ledger/services.py`、`backend/apps/income/models.py`、`backend/apps/income/services.py`、`backend/apps/claims/models.py`、`backend/apps/claims/services.py` | 收入表/报销单账户外键，入账时解析并校验账户 | REQ-FUNC-339、US-328/AC-407-01~04 | MOD-192 |
| MOD-194 | 报表链式生成 | 修改 `backend/apps/ledger/models.py`、`backend/apps/ledger/services.py` | 期初/期末、旧口径标记、作废波及后续期间、重算级联 | REQ-FUNC-335、REQ-NFUNC-068、AC-403-01~06 | MOD-192 |
| MOD-195 | 账户与报表 API | 修改 `backend/apps/ledger/views.py`、`backend/apps/ledger/urls.py` | 账户汇总、管理端账户 CRUD、报表详情账户视角 | REQ-FUNC-333/335/336/337/341、REQ-NFUNC-069 | MOD-192、MOD-194 |
| MOD-196 | 审计动作登记 | 修改 `backend/apps/core/audit.py` | 登记账户创建/修改审计动作 | REQ-NFUNC-071 | — |
| MOD-197 | 数据迁移 | 新建 `backend/apps/ledger/migrations/0004_ledger_account.py`、`0005_ledger_account_backfill.py`、`0006_ledger_report_chain.py`；新建 `backend/apps/income/migrations/0006_income_sheet_account.py`、`backend/apps/claims/migrations/0006_claim_account.py` | 建账户表、加列、幂等回填默认账户、报表旧口径标记 | REQ-FUNC-338、C-370/C-375 | MOD-192、MOD-193、MOD-194 |
| MOD-198 | 门户财务报表页 | 修改 `frontend/src/portal/Reports.vue`；新建 `frontend/src/portal/ReportDetailDialog.vue`、`frontend/src/portal/AccountCard.vue` | 周期筛选、账户卡片与最近 10 笔、动效浮层详情 | REQ-FUNC-333/334/341、REQ-NFUNC-066/067/072 | MOD-195、MOD-201 |
| MOD-199 | 主页账户卡片 | 修改 `frontend/src/portal/Home.vue` | 启用账户余额合计与各账户余额 | REQ-FUNC-340、REQ-NFUNC-072 | MOD-195、MOD-201 |
| MOD-200 | 管理端账户管理 | 新建 `frontend/src/admin/AdminAccounts.vue`；修改 `frontend/src/router/index.js`、`frontend/src/layout/menus.js` | 账户列表、创建、编辑、设置默认、停用 | REQ-FUNC-336、REQ-NFUNC-069/071 | MOD-195、MOD-201 |
| MOD-201 | 前端 API 层 | 修改 `frontend/src/shared/api.js` | 账户汇总与管理端账户接口封装 | REQ-FUNC-336/337/341 | MOD-195 |

## 模块详情

### MOD-192 账户模型与余额服务

- 文件：`backend/apps/ledger/models.py`（修改）、`backend/apps/ledger/services.py`（修改）。
- 模型 `LedgerAccount`：

```python
class LedgerAccount(models.Model):
    STATUSES = [("ENABLED", "启用"), ("DISABLED", "停用")]

    name = models.CharField(max_length=64)
    account_no = models.CharField(max_length=32, null=True, blank=True, unique=True)
    status = models.CharField(max_length=8, choices=STATUSES, default="ENABLED")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_admin_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-is_default", "id"]
        indexes = [models.Index(fields=["status"])]
```

- `LedgerEntry` 新增：`account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name="entries")`（迁移完成后非空），并新增索引 `Index(fields=["account", "status", "occurred_on"])`。
- 服务签名：

```python
class AccountService:
    @staticmethod
    def default_account() -> LedgerAccount: ...
    @staticmethod
    def balance(account: LedgerAccount) -> Decimal: ...
    @staticmethod
    def recent_entries(account: LedgerAccount, limit: int = 10) -> list[LedgerEntry]: ...
    @staticmethod
    def summary(*, status: str | None = None, recent: int = 10) -> dict: ...
```

- 规则：余额=有效收入合计−有效支出合计；`recent_entries` 只取 `status="ACTIVE"`，按 `-occurred_on, -id` 排序；`summary` 的 `total_balance` 为所返回账户余额之和。
- 依赖：无。外部依赖：无。

### MOD-193 流水账户归属

- 文件与改动：
  - `backend/apps/income/models.py`：`IncomeSheet` 新增 `account = models.ForeignKey("ledger.LedgerAccount", null=True, blank=True, on_delete=models.PROTECT, related_name="income_sheets")`。
  - `backend/apps/claims/models.py`：`Claim` 新增 `account = models.ForeignKey("ledger.LedgerAccount", null=True, blank=True, on_delete=models.PROTECT, related_name="claims")`。
  - `backend/apps/ledger/services.py`：`post()` 增加关键字参数 `account: LedgerAccount | None = None`；为空时取默认账户。
  - `backend/apps/income/services.py`：`on_approved` 入账时传入 `sheet.account`。
  - `backend/apps/claims/services.py`：`on_approved` 与 `_approve_settlement` 入账时传入 `claim.account`。
- **IFC-417 `LedgerService.post`（服务签名）**：

```python
class LedgerService:
    @staticmethod
    def post(*, direction: str, amount: Decimal, occurred_on: date, entry_type: str,
             summary: str | None = None, source_type: str, source_id: int, seq: int = 0,
             allow_negative: bool = False, account: LedgerAccount | None = None) -> LedgerEntry: ...
```

- 校验：`account` 不存在或 `status != "ENABLED"` → `ApiError("ACCOUNT_UNAVAILABLE", "账户不可用", 409)`，不写入流水（AC-407-04）。
- 输入校验：账户选择来自收入表/报销单的 `account_id`（可选整数）；空值或 `null` 表示默认账户。
- 鉴权：沿用现有视图权限（`IsIncomeMember` / 报销提交视图），不新增对外端点。
- 依赖：MOD-192。

### MOD-194 报表链式生成

- 文件：`backend/apps/ledger/models.py`（修改）、`backend/apps/ledger/services.py`（修改）。
- `LedgerReport` 新增字段：

```python
opening_balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
closing_balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
legacy = models.BooleanField(default=False)
```

`balance` 保留，语义改为“本期结余=本期收入−本期支出”，与报表详情兼容旧字段。

- 服务签名：

```python
class LedgerService:
    @staticmethod
    def generate(*, period_type: str, year: int, quarter: int | None = None,
                 generated_by_type: str = "MEMBER", generated_by_id: int | None = None,
                 account: LedgerAccount | None = None) -> LedgerReport: ...

    @staticmethod
    def _mark_reports_stale(occurred_on: date) -> None: ...   # 改为覆盖期间及其之后全部期间

    @staticmethod
    def _regenerate_after(report: LedgerReport) -> list[LedgerReport]: ...
```

- 口径：
  - `opening_balance` = 期间开始日之前的有效流水（收入−支出）累计；最早期间为 `0.00`。
  - `closing_balance` = `opening_balance + total_income - total_expense`。
  - 年度报表的 `opening_balance` 等于当年 Q1 的期初，`closing_balance` 等于当年 Q4 的期末，由同一累计公式自然成立。
  - `_mark_reports_stale` 把覆盖期间及其之后所有未标记的报表置 `stale=True`。
  - `_regenerate_after` 在目标报表生成后，按 (year, quarter, period_type) 升序重算已存在且 `legacy=False` 的后续报表，保证链式相等（AC-403-05）。
  - 旧报表在迁移中标记 `legacy=True`；`legacy=True` 的报表不参与级联，重新生成后写为 `legacy=False`。
- 依赖：MOD-192（账户筛选时附加 `account` 条件）。

### MOD-195 账户与报表 API

- 文件：`backend/apps/ledger/views.py`（修改）、`backend/apps/ledger/urls.py`（修改）。

**IFC-409 `GET /api/v1/ledger/accounts/summary`**
- 鉴权：`IsMember`（登录用户可查看，REQ-NFUNC-069）。
- 查询参数：`status: "ENABLED" | "ALL"`（默认 `ALL`）；`recent: int`（默认 10，范围 0–20，0 表示不返回明细）。
- 响应 200：

```json
{
  "total_balance": "90000.00",
  "accounts": [
    {
      "id": 1,
      "name": "第四届业主委员会基本账户",
      "account_no": "",
      "status": "ENABLED",
      "is_default": true,
      "balance": "70000.00",
      "recent_entries": [
        {"id": 9, "occurred_on": "2026-11-01", "direction": "INCOME",
         "amount": "500.00", "entry_type": "INCOME", "summary": "停车费"}
      ]
    }
  ]
}
```

- 校验：`recent` 非整数或越界按 `10` 处理；`status` 非法值按 `ALL` 处理。金额一律两位小数字符串。

**IFC-410 `GET /api/v1/admin/ledger/accounts`**
- 鉴权：`IsAdmin`。
- 查询参数：`page`、`page_size`（沿用 `page_response`）；`status` 可选。
- 响应 200：分页对象 `{count, page, page_size, results:[{id,name,account_no,status,is_default,balance}]}`。

**IFC-411 `POST /api/v1/admin/ledger/accounts`**
- 鉴权：`IsAdmin`。
- 请求：`{ "name": string, "account_no": string | null }`；`name` 去空格后 1–64 字符；`account_no` 去空格后 0–32 字符，空串归一化为 `null`。
- 响应 201：账户对象（同 IFC-410 单项，余额 `0.00`）。
- 错误：字段非法 → `INVALID_VALUE` 400；账户号重复 → `ACCOUNT_NO_EXISTS` 409；未登录 → 401；非管理员 → 403。

**IFC-412 `PATCH /api/v1/admin/ledger/accounts/{account_id}`**
- 鉴权：`IsAdmin`。
- 请求（至少一项）：`{ "name"?: string, "account_no"?: string | null, "status"?: "ENABLED"|"DISABLED", "is_default"?: boolean }`。
- 行为：`is_default=true` 时把其他账户置为非默认（同一事务）；修改账户号/名称不触碰流水与余额（AC-404-03/AC-405-03）；停用不删除（Q-FA-04=A）。
- 响应 200：账户对象。
- 错误：账户存在流水时不允许删除语义（本接口无删除动作）；账户号重复 → `ACCOUNT_NO_EXISTS` 409；账户不存在 → `NOT_FOUND` 404。
- 审计：创建/修改调用 `AuditService.record(action="ACCOUNT_CREATED"|"ACCOUNT_UPDATED", object_type="ledger_account")`，`detail` 含 `before`/`after`（含名称、账户号、状态、是否默认），操作人为管理员（REQ-NFUNC-071）。

**IFC-413 `GET /api/v1/ledger/reports/{report_id}`（扩展）**
- 鉴权：`IsMember`（沿用 `backend/apps/ledger/views.py:55-62`）。
- 查询参数：`account_id`（可选整数）。
- 响应 200 新增字段：`opening_balance`、`closing_balance`、`legacy`；无 `account_id` 时取快照值，`legacy=True` 时 `opening_balance`/`closing_balance` 为 `null` 且 `detail` 保持旧数据。
- 带 `account_id` 时：按该账户在该期间内的有效流水实时计算 `total_income`、`total_expense`、`opening_balance`、`closing_balance`、`detail`；账户不存在 → `NOT_FOUND` 404；账户停用仍可查看历史。
- 错误：报表不存在 → `NOT_FOUND` 404。

**IFC-414 `GET /api/v1/ledger/reports`（扩展）**
- 已有 `period_type`、`year` 过滤保持（`backend/apps/ledger/views.py:18-26`），响应摘要新增 `opening_balance`、`closing_balance`、`legacy`。
- 排序沿用模型 `ordering = ["-year", "-period_type", "-quarter"]`（`backend/apps/ledger/models.py:53`），满足“年度优先、季度 Q4→Q1”。

- 依赖：MOD-192、MOD-194。

### MOD-196 审计动作登记

- 文件：`backend/apps/core/audit.py`（修改）。
- 在 `AUDIT_ACTIONS` 中新增 `"ACCOUNT_CREATED"`、`"ACCOUNT_UPDATED"`；`AuditService.record` 对未登记动作抛错，缺登记会导致 500。

### MOD-197 数据迁移

- 迁移文件与操作见「数据迁移」小节。
- 依赖：MOD-192、MOD-193、MOD-194。

### MOD-198 门户财务报表页

- 文件：`frontend/src/portal/Reports.vue`（重写页面结构）、`frontend/src/portal/ReportDetailDialog.vue`（新建）、`frontend/src/portal/AccountCard.vue`（新建）。

**IFC-415 `AccountCard`（组件契约）**

```ts
interface AccountEntry {
  id: number; occurred_on: string; direction: 'INCOME' | 'EXPENSE'
  amount: string; entry_type: string; summary: string | null
}
interface AccountSummary {
  id: number; name: string; account_no: string; status: 'ENABLED' | 'DISABLED'
  is_default: boolean; balance: string; recent_entries: AccountEntry[]
}
// props: { account: AccountSummary }
```

- 展示：名称、账户号（空则不显示占位行）、余额（2 位小数）、最近 10 笔（日期、方向、金额、类型/摘要）；无流水显示“暂无收支记录”（AC-409-05）；停用账户加“已停用”标签。

**IFC-416 `ReportDetailDialog`（组件契约）**

```ts
interface ReportDetail {
  id: number; period_type: 'QUARTER' | 'YEAR'; year: number; quarter: number | null
  total_income: string; total_expense: string; balance: string
  opening_balance: string | null; closing_balance: string | null
  legacy: boolean; stale: boolean
  detail: Array<{ direction: 'INCOME' | 'EXPENSE'; occurred_on: string; entry_type: string
                  summary: string | null; amount: string }>
}
// props: { modelValue: boolean; reportId: number | null; triggerEl: HTMLElement | null }
// emits: { 'update:modelValue': (v: boolean) => void }
```

- 交互：打开时请求 IFC-413；Esc 与关闭按钮可关闭；关闭后焦点回到 `triggerEl`；过渡 240–320 ms；`prefers-reduced-motion: reduce` 时禁用位移动画（REQ-NFUNC-066）；加载失败时浮层内显示原因与“重试”，不自动关闭（AC-402-05）；360 px 宽不出现横向滚动（AC-402-03）。
- 浮层内提供“账户视角”选择（全部账户 / 指定账户），带 `account_id` 重新请求 IFC-413（ADR-179）。

**页面结构（Reports.vue）**
- 顶部：周期类型筛选 `全部 | 仅年报 | 仅季报`，默认“全部”；切换筛选调用 `resetAndLoad()` 回到第 1 页（AC-401-04）。
- 账户卡片区：调用 IFC-409（`status=ALL&recent=10`），横向/网格排列。
- 报表列表：保留“重新生成”入口与过期标签；点击条目打开 IFC-416 浮层（不再渲染底部详情卡片）。
- 空状态：所选筛选无数据时显示“暂无已生成报表”（AC-401-05）。
- 依赖：MOD-195、MOD-201。

### MOD-199 主页账户卡片

- 文件：`frontend/src/portal/Home.vue`（修改）。
- 调用 IFC-409（`status=ENABLED&recent=0`）；卡片展示启用账户余额合计与各账户名称、余额，点击跳转 `/reports`（AC-408-01/03）。
- 加载失败时卡片内显示“加载失败”与重试，不影响其他区块（AC-408-04）。

### MOD-200 管理端账户管理

- 文件：新建 `frontend/src/admin/AdminAccounts.vue`；修改 `frontend/src/router/index.js`（新增 `/admin/finance/accounts`）、`frontend/src/layout/menus.js`（“财务”分组新增“账户管理”）。
- 交互：列表（IFC-410）→ 新建/编辑对话框（IFC-411/412）；账户号重复时展示后端 `ACCOUNT_NO_EXISTS` 文案“账户号已存在”（AC-404-02）；名称/账户号必填提示（AC-404-04）；提供“设为默认”和“停用/启用”。
- 权限：路由位于管理端布局下，未登录跳转 `/admin/login`（`frontend/src/router/index.js:100-106`）。

### MOD-201 前端 API 层

- 文件：`frontend/src/shared/api.js`（修改）。
- 新增封装：

```js
export const accountApi = {
  summary: (params) => get('/ledger/accounts/summary', params), // { status?: 'ENABLED'|'ALL', recent?: number }
  adminList: (params) => adminHttp.get('/admin/ledger/accounts', { params }),
  create: (data) => adminHttp.post('/admin/ledger/accounts', data),
  update: (id, data) => adminHttp.patch(`/admin/ledger/accounts/${id}`, data)
}
```

- `ledgerApi.reportDetail(id, accountId)` 增加可选 `account_id` 参数。
- 依赖：MOD-195。

## 需求覆盖表

| REQ | US | MOD | IFC |
|---|---|---|---|
| REQ-FUNC-333 | US-322 | MOD-198、MOD-195 | IFC-414 |
| REQ-FUNC-334 | US-323 | MOD-198、MOD-195 | IFC-416、IFC-413 |
| REQ-FUNC-335 | US-324 | MOD-194、MOD-195 | IFC-413、IFC-414 |
| REQ-FUNC-336 | US-325 | MOD-192、MOD-195、MOD-200 | IFC-410/411/412 |
| REQ-FUNC-337 | US-326 | MOD-192、MOD-195 | IFC-409 |
| REQ-FUNC-338 | US-327 | MOD-197 | 迁移 0005 |
| REQ-FUNC-339 | US-328 | MOD-193 | IFC-417（服务签名） |
| REQ-FUNC-340 | US-329 | MOD-199 | IFC-409 |
| REQ-FUNC-341 | US-330 | MOD-198、MOD-195 | IFC-409、IFC-415 |
| REQ-NFUNC-066 | US-323 | MOD-198 | IFC-416 |
| REQ-NFUNC-067 | US-323/330 | MOD-198、MOD-199、MOD-200 | — |
| REQ-NFUNC-068 | US-324/326/327 | MOD-192、MOD-194、MOD-197 | IFC-409/413 |
| REQ-NFUNC-069 | US-325/326 | MOD-195、MOD-200 | IFC-409/410/411/412 |
| REQ-NFUNC-070 | US-323/330 | MOD-198、MOD-195 | IFC-409/413 |
| REQ-NFUNC-071 | US-325/327 | MOD-195、MOD-196 | IFC-411/412 |
| REQ-NFUNC-072 | US-330 | MOD-198、MOD-199 | IFC-415 |

## 依赖关系

- MOD-193 → MOD-192（调用 `LedgerService.post` 时解析账户）
- MOD-194 → MOD-192（账户筛选条件）
- MOD-195 → MOD-192、MOD-194（`AccountService`、`LedgerService.generate`）
- MOD-197 → MOD-192、MOD-193、MOD-194（模型字段）
- MOD-196 独立
- MOD-198 → MOD-195、MOD-201
- MOD-199 → MOD-195、MOD-201
- MOD-200 → MOD-195、MOD-201

已检查：无循环依赖。

## 数据迁移

| 迁移 | 内容 | 可逆性 | 数据风险与处理 |
|---|---|---|---|
| `ledger/0004_ledger_account` | 创建 `LedgerAccount`；`LedgerEntry.account` 可空外键与索引；`LedgerReport` 增加 `opening_balance`、`closing_balance`（可空）、`legacy`（默认 False） | 结构可逆 | 新增可空列，不阻塞写入 |
| `ledger/0005_ledger_account_backfill` | `RunPython`：`get_or_create` 默认账户（`name="第四届业主委员会基本账户"`、`is_default=True`、`account_no=None`）；把 `account_id IS NULL` 的全部流水归属默认账户；把既有 `LedgerReport` 置 `legacy=True` | 反向 `noop`（不回滚已归属数据） | 幂等：重复执行不新增账户、不重复归属；迁移前后有效收支合计差额须为 0.00 |
| `ledger/0006_ledger_entry_account_not_null` | `AlterField` 把 `LedgerEntry.account` 改为非空、`on_delete=PROTECT` | 不可逆（需快照） | 要求 0005 已回填；部署前数据库快照（C-375） |
| `income/0006_income_sheet_account` | `IncomeSheet.account` 可空外键 | 可逆 | 新单据未选账户时服务端回落默认账户 |
| `claims/0006_claim_account` | `Claim.account` 可空外键 | 可逆 | 同上 |

迁移按画像 P6 手写、单应用范围；不使用 `makemigrations` 全量产物（P8）。迁移依赖顺序：`ledger.0006` 依赖 `ledger.0005`；`income.0006` 与 `claims.0006` 依赖 `ledger.0004`（仅引用模型，不依赖回填完成）。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 操作 |
|---|---|---|
| `ocap-backend`（gunicorn） | 新增模型/迁移/接口 | 部署时执行迁移并 `systemctl restart ocap-backend` |
| 定时报表生成（`generate_due`） | 改为链式口径，无新进程 | 无需额外配置 |
| Web 前端静态产物 | Reports.vue/Home.vue/管理端新增页面 | `npm run build` 后替换 nginx 静态目录，构建需带 `VITE_API_BASE=/ocap/api/v1` 与 `--base=/ocap/`（PM 记忆 P-PM-007） |
| 微信小程序 | 不改动 | 无 |

## 领域与外部依赖出处

本次改动不新增闭源 API 调用、硬件访问或领域数值算法，P11 中与本次相关的微信/短信接口未被触碰。故本表不适用（无条目）。

如实现阶段需要引用现有 `LedgerService` 行为，出处为 `[CODE: backend/apps/ledger/services.py:30-107]`；报表期间边界出处 `[CODE: backend/apps/ledger/services.py:15-27]`。
