<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-07T23:57:31+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.2.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/tech_stack.md</file>
    <file>development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告（PHASE_06 CODE_REVIEW）

## 1. 结论

- CRITICAL：0
- MAJOR：3（原有遗留，均有明确原因与后续动作，见 §4）
- MINOR：7
- 缺陷回流：GR-D-001 的 4 个 MAJOR（DEF-001~004）已全部 FIXED，见 §7。
- 自验证：编译、系统检查、冒烟测试、迁移检查、三层全量测试全部通过。
- 评审结论：**可重新进入 GROUP_D 复跑**（无 CRITICAL；遗留 MAJOR 3 条未超过门控上限）。

## 2. 自验证证据

### 2.1 编译

```
> python -m compileall -q backend
COMPILE_EXIT=0
```

### 2.2 系统检查

```
> python manage.py check --settings=config.test_settings
System check identified no issues (0 silenced).
CHECK_EXIT=0
```

### 2.3 冒烟测试

```
> python manage.py test tests.smoke --settings=config.test_settings
...... 
Ran 6 tests in 0.096s
OK
Destroying test database for alias 'default'...
```

### 2.4 迁移检查

```
> python manage.py makemigrations --check --dry-run
No changes detected
MIGRATION_CHECK_EXIT=0
```

前序 `migrate --check` 输出 `No migrations to apply`。

## 3. 五维评分（5 分制）

| 维度 | 分数 | 依据 |
|---|---|---|
| 正确性 | 4.0 | 6 项端到端冒烟流程真实通过；统一错误体与状态码一致；金额两位小数；决议/投票/审批状态机有约束兜底。扣分：前端与小程序未经运行验证；结算复用 EXPENSE 为假设。 |
| 可维护性 | 4.0 | 按 app 分层（models/services/views/serializers/urls），业务规则集中在 services；权限与附件策略独立；命名与错误码统一。扣分：部分管理端页面为紧凑实现，交互简化。 |
| 安全性 | 4.0 | 全部业务端点默认登录；角色与房屋关系校验；防自批；验证码限流与锁定；审计白名单；密码规则与防枚举；外部凭据只读环境变量。扣分：未做渗透测试；并发与越权矩阵依赖后续 D 组用例。 |
| 性能 | 3.5 | 列表分页、批量导入上限、数据库索引与唯一约束；审计写入不阻塞主流程。扣分：未做压测；xlsx 全量解析在内存中完成。 |
| 测试完备性 | 3.0 | 后端有 6 个真实执行的冒烟用例覆盖主链路。扣分：单元/集成/E2E 三层测试由 GROUP_D 负责；前端与小程序无自动化测试。 |
| **综合** | **3.7** | 满足进入测试阶段的条件。 |

## 4. 问题清单

### MAJOR

| ID | 位置 | 问题 | 原因与后续动作 |
|---|---|---|---|
| CR-001 | `frontend/`、`miniprogram/` | 前端与小程序未安装依赖、未构建、无组件测试，运行时行为未经真实执行验证。 | 用户约束“不安装依赖、不改全局环境”；已做路由/接口静态核对，交付前需在允许安装的环境执行 `npm install && npm run build` 并补组件测试。 |
| CR-002 | `backend/apps/*/migrations/0001_initial.py` | 迁移为 `makemigrations` 自动生成，不完全符合画像 P6“手写最小化、按 app 分范围”的约定。 | 为在有限时间内完成 14 个 app 的可运行基线；已人工核对字段、索引与唯一约束，并通过 `makemigrations --check` 与 `migrate`。后续若上线前要求手写迁移，可按 app 拆分复核。 |
| CR-003 | `backend/config/settings.py` | 实际运行 Django 6.0.6 / DRF 3.17.1，高于画像目标的 Django 5.2。 | 本机既有环境，用户要求不降级；代码未使用 6.0 专属 API。需在 CI/部署环境固定到画像版本后复跑。 |

### MINOR

| ID | 位置 | 问题 | 处理 |
|---|---|---|---|
| CR-004 | `miniprogram/pages/profile-setup/index.vue` | 小程序端未上传头像，仅保存昵称。 | 已收敛为只保存昵称；头像上传依赖附件接口，后续在 Web 端或补 `uni.uploadFile`。 |
| CR-005 | `frontend/src/admin/AdminSeats.vue` | “变更职位”在 MEMBER/CHAIR 间切换，未提供完整职位下拉。 | 记录为交互简化，后续补 VICE_CHAIR 选项与生效日期。 |
| CR-006 | `backend/apps/registry/services.py`、`apps/integrations/aliyun_sms.py` | openpyxl 与阿里云 SDK 缺失时降级（503 / `SDK_MISSING`）。 | 符合 P11 外部依赖不可用时的失败可见原则；部署前安装依赖即可。 |
| CR-007 | `backend/apps/jobs/` | 定时任务仅提供 `run_due_jobs` 命令，未接入系统调度。 | 由 E1 部署计划配置 cron/计划任务。 |
| CR-008 | `backend/apps/approval/services.py` | 并发决定同一审批实例未做压力测试。 | 依赖 `pending_slot` 唯一约束与事务；由 D 组补并发用例。 |
| CR-009 | `frontend/src/shared/http.js` | 错误提示直接使用后端 `message`，未做本地化兜底。 | 后端错误体统一中文；保留 `details.retry_after` 拼接。 |
| CR-010 | `backend/apps/claims/views.py` | 结算（SETTLEMENT）复用 EXPENSE 审批作用域。 | 架构未单列结算流程，标 `[ASSUMPTION] A-01`，需求确认后可拆分。 |

## 5. 逐项自检（对照 §J GROUP_C）

| 条件 | 结果 | 证据 |
|---|---|---|
| MOD 全部实现 | 满足 | MOD-001~022 对应 app、Web 与管理端路由、小程序页面均已落盘 |
| 无未解决 CRITICAL | 满足 | §4 CRITICAL=0 |
| MAJOR 遗留 ≤3 且逐条原因 | 满足 | CR-001~003 均给出原因与后续动作 |
| PM 复跑无新增失败 | 待 PM 核验 | §2 命令与输出可供复跑 |
| 迁移符合 P6 | 部分（见 CR-002） | 自动生成但通过 `--check`，字段与约束已核对 |
| 改动范围与 implementation_plan 一致 | 满足 | 改动集中在 `backend/`、`frontend/`、`miniprogram/`、`development/` |
| 未使用无出处的闭源 API/寄存器 | 满足 | 外部调用仅微信/短信/邮件公开接口，均有 `# [P11: ...]` 出处注释 |

## 6. 建议 GROUP_D 优先覆盖

1. 认证与限流：验证码错误次数/锁定、防枚举、Token 过期与续期。
2. 房屋关系：重复认证冲突、首位户主、撤销后的接任、同住人越权。
3. 审批：DESIGNATED / HALF_MAJORITY 边界、防自批、撤回/重提、并发决定。
4. 财务：金额精度、收入表导入错误率阈值、报表周期锁定、作废后台账。
5. 权限矩阵：未登录 401、非成员 403、委员/主任差异、管理员端点。
6. 前端/小程序：在允许安装依赖的环境中构建并验证登录、认证、决议、投票主链路。

## 7. 缺陷修复（ocap-GROUP_C-2）

依据 GR-D-001，带 `REWORK_AUTHORIZED` 修复 4 个 MAJOR 产品缺陷：

| DEF | 位置 | 根因 | 修改说明 | 状态 |
|---|---|---|---|---|
| DEF-001 | `apps/resolutions/views.py::ResolutionListCreateView` | GET 与 POST 共用 `IsChairOrVice`，读接口被写权限约束 | `get_permissions` 按方法分离：GET → `IsMember`，POST → `IsChairOrVice` | FIXED |
| DEF-002 | `apps/income/views.py::IncomeSheetListView/IncomeSheetDetailView`、`apps/ledger/views.py::LedgerReportListCreateView/LedgerReportDetailView` | 财务读接口误用 `IsIncomeMember`，普通登录用户 403 | 列表/明细 GET 改 `IsMember`；收入导入、提交、台账生成仍限 `IsIncomeMember` | FIXED |
| DEF-003 | `apps/ledger/services.py::LedgerService.generate` | 同周期直接抛 `LEDGER_LOCKED`，与"手动重新生成、版本 +1"冲突 | 同周期改为覆盖原行：重算金额与内容、`version += 1`、刷新 `generated_at`，审计记录版本 | FIXED |
| DEF-004 | `apps/polls/models.py`、`migrations/0002_poll_kind_scope_question_type.py`、`views.py`、`services.py` | 应答仅限业委会成员；Poll 缺 kind/scope/参与人快照，Question 缺题型 | 新增 `kind` / `survey_scope` / `participant_count` / `result_snapshot` 与 `qtype` / `required`；代表投票快照现任代表；调查按范围、代表投票按快照校验参与资格；同意-反对-弃权返回分母与通过判定 | FIXED |

### 7.1 自验证

```
> python manage.py test tests.unit tests.integration tests.e2e --settings=config.test_settings -v 1
Ran 115 tests in 0.980s

OK
```

```
> python manage.py makemigrations --check --dry-run --settings=config.test_settings
No changes detected
```

分层结果：unit 33/33 OK、integration 72/72 OK、e2e 10/10 OK；相对修复前 106 通过 + 9 失败，9 条失败全部转绿，无回退。

### 7.2 遗留 MAJOR（未超过 3 条）

CR-001、CR-002、CR-003 维持原状，原因与后续动作见 §4；本次回流未引入新的 CRITICAL/MAJOR/MINOR。

文档版本：1.0.0 → 1.1.0（MINOR）；旧版本 1.0.0 登记为 SUPERSEDED。
