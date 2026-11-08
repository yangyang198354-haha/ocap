<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-08T23:38:58+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/user_stories.md</file><file>requirements/requirements_spec.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

> 复跑说明（ocap-GROUP_D-9，续 -8）：GR-C-007 收尾：DEF-006 CLOSED（TC-INT-106 PASS）、OBS-001 已修复；TC-INT-125/130/146 匿名断言收紧为只接受 401；全层重跑全部通过（后端 212/212，Web 36/36，小程序 30/30）。以下为 -8 的历史说明：GR-D-006 FAIL 修正。PM 按 AC 前缀比对 69 个 Must Have 故事，发现 US-006/010/013/025/028/035/042/068/070/071/073 共 11 个故事无 AC 映射（GR-D-006-F01）。本版逐 AC 补映射、补写新用例（后端集成 49、E2E 旅程 3、Web vitest 3、小程序 vitest 3），并追加 US → 用例总表（§US→用例总表）；DEF-005 复跑 TC-INT-082 通过，标 CLOSED；新用例暴露 DEF-006。REWORK_AUTHORIZED: testing/ 下 4 份文件与 backend/tests/**、frontend/tests/**、miniprogram/tests/**。
>
> 前次说明（ocap-GROUP_D-7，续 -6）：GROUP_C-5 修复 CR-011 ~ 024 后的返工。本版新增后端合并/核销/报表/录入/契约用例，新增 Web 与小程序 vitest，并按 AC-059-02/03/05 更新两条旧用例（TC-UNIT-021、TC-INT-057）。REWORK_AUTHORIZED: project_workspace/ocap/testing/ 下 4 份文件。

## 测试策略

- 被测改动：GROUP_C（含 GROUP_C-5 返工）交付的 Django 后端、Web 前端（`frontend/src`）、小程序（`miniprogram/`）。后端（`backend/`，13 个 app：core / integrations / accounts / registry / residency / committee / identity / approval / resolutions / claims / income / ledger / polls / jobs）。
- 范围（in scope）：后端 HTTP API、领域规则（金额、脱敏、密码、限流、导入、投票统计、决议判定、席位）、认证与权限、跨模块流程（审批 ↔ 决议/报销/收入，收入/支出 ↔ 台账，投票 ↔ 到期任务）。
- 范围（out of scope）：uni-app 运行时与微信真机行为（vitest 用 `miniprogram/tests/stubs/uni-app.js` 桩，标 NOT_TESTABLE 并入人工验证清单）；浏览器真实渲染/视觉（vitest + jsdom 只测挂载与交互逻辑）；真实微信 / 阿里云短信 / SMTP（画像 P11-3，只用 `apps/integrations/fakes.py`）；测试机 MySQL 与部署。
- 环境：Linux，Python 3.12.3，Django 5.2.19，DRF 3.18.3（PM 会话临时 venv）；配置 `config.test_settings`，SQLite `:memory:`；Node v22.23.3，vitest 2.1.9（jsdom）；短信 `FakeSmsGateway`，邮件 locmem。
- 分层：
  - 单元：`backend/tests/unit/`，单模块 / 纯函数，不经过 HTTP；
  - 集成：`backend/tests/integration/`，DRF APIClient + 真实 ORM / 路由 / 权限，跨模块；
  - E2E：`backend/tests/e2e/`，多步用户旅程经真实 HTTP API 串联。
- 判定模式：FULL_FLOW threshold（画像 P5）：unit_pass 0.80、integration_pass 0.90、critical_path 1.00。各层通过后再进入下一层。
- 基线来源：画像 P4 ——后端 120/120 通过（2026-11-08）；前端与小程序此前无用例。FULL_FLOW threshold 判定，基线用于区分既有/新增失败。本次改动前先实跑一次：后端全量 160 个全部通过（含 TC-INT-082，DEF-005 已由 GR-C-006 修复）；本次新增后端 52 个（集成 49、E2E 3）与 vitest 6 个（Web 3、小程序 3）。
- critical path 口径：替代——项目无浏览器/小程序 E2E 框架，用 `backend/tests/e2e/` 的多步 API 旅程作为最高层可执行端到端级用例；前后端契约由 `test_frontend_contract.py`（集成层）与 vitest 路径断言共同覆盖（画像 P5 补充）。
- vitest 分层归属（Django 无 tag，分层按目录；vitest 按文件）：`frontend/tests/api.spec.js`、`auth.store.spec.js`、`miniprogram/tests/api.spec.js`、`store.spec.js`（单模块，HTTP 层 mock）→ **单元层**；`frontend/tests/pages.spec.js`、`frontend/tests/login.spec.js`、`miniprogram/tests/pages.spec.js`（挂载真实 .vue 组件 + 真实 api.js/store，仅 mock http 层）→ **集成层**。mock 只打在 http 模块（Web：`vi.mock('@/shared/http')`；小程序：`uni.request/uploadFile` 桩），未 mock 被测的 api.js、store 或页面本身。
- 集成层实际可执行后端用例 148 个（71 既有 + 77 新写；表中 TC-INT-071 已作废；0.5.0 新增 TC-INT-101~149 共 49 个，位于 `backend/tests/integration/test_gap_must_have.py`）。E2E 旅程 16 个（0.5.0 新增 TC-E2E-014~016，位于 `backend/tests/e2e/test_gap_journeys.py`）。Web vitest 新增 `frontend/tests/login.spec.js`（TC-WEB-031~033，集成层）；小程序 `pages.spec.js` 追加 TC-MP-028~030（集成层）。
- GR-C-005 condition 核对：①AC-059-03/05 两条旧用例已按 AC 更新（TC-UNIT-021、TC-INT-057），并新增 TC-UNIT-034/035、TC-INT-073；②前后端契约测试 TC-INT-074~084（路由与方法 3 个、字段 8 个，覆盖 identities、claims、polls responses、income sheets）；③Web/小程序 vitest：TC-WEB-001~030、TC-MP-001~027（store、api 路径、关键页面挂载）；④§9 建议用例：合并冲突 TC-INT-085~089、核销补差/退款/恰好相等 TC-INT-090~094、generate_due 幂等 TC-UNIT-037~039 与 TC-INT-095、逐条录入与重复导入 TC-INT-096~099、管理员下载附件 TC-INT-100、缺 SECRET_KEY TC-UNIT-040~043。



## AC 映射

> 说明：`AC-xxx-*` 表示该用例断言该故事下与本用例主题对应的 AC（完整 AC 清单见 `requirements/user_stories.md`）。`现有/新写` 列中"新写"均为本次 GROUP_D 新增。

### 单元层（TC-UNIT）

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置（文件::类::方法） | 前置/动作/预期 | 测试数据 |
|---|---|---|---|---|---|---|---|
| AC-049-*、AC-061-* | TC-UNIT-001 | 单元 | sim | 新写 | test_core_rules.py::MoneyTests::test_none_is_zero | None → `money()` 返回 "0.00" | 无 |
| AC-049-*、AC-061-* | TC-UNIT-002 | 单元 | sim | 新写 | test_core_rules.py::MoneyTests::test_two_decimals_half_up | 1.005→"1.01"、300.5→"300.50"、0.004→"0.00" | Decimal 字面量 |
| AC-049-* | TC-UNIT-003 | 单元 | sim | 新写 | test_core_rules.py::MoneyTests::test_negative_keeps_sign | -12.345 → "-12.35" | Decimal |
| AC-033-* | TC-UNIT-004 | 单元 | sim | 新写 | test_core_rules.py::MaskingTests::test_phone_masked | 11 位手机号 → 前 3 后 4，中间 4 个 *；非法 → "****" | 13800138000 |
| AC-033-* | TC-UNIT-005 | 单元 | sim | 新写 | test_core_rules.py::MaskingTests::test_email_masked | 邮箱首字母可见其余 *；非法 → "****" | alice@example.com |
| AC-009-*、AC-032-* | TC-UNIT-006 | 单元 | sim | 新写 | test_core_rules.py::PasswordRuleTests::test_reject_short | 2 位密码 → ApiError `PASSWORD_RULE_VIOLATION` | "a1" |
| AC-009-* | TC-UNIT-007 | 单元 | sim | 新写 | test_core_rules.py::PasswordRuleTests::test_reject_digits_only | 纯数字 8 位被拒 | "12345678" |
| AC-009-* | TC-UNIT-008 | 单元 | sim | 新写 | test_core_rules.py::PasswordRuleTests::test_reject_weak | 常见弱口令被拒 | "password1" |
| AC-009-* | TC-UNIT-009 | 单元 | sim | 新写 | test_core_rules.py::PasswordRuleTests::test_accept_strong | 合规密码不抛错 | "Ocap2026pass" |
| AC-040-* | TC-UNIT-010 | 单元 | sim | 新写 | test_core_rules.py::AddMonthsTests::test_month_end_clamped | 1-31 +1 月 → 2-29/2-28，12-31 +2 → 次年 2-28 | date 字面量 |
| AC-040-* | TC-UNIT-011 | 单元 | sim | 新写 | test_core_rules.py::AddMonthsTests::test_year_rollover | +12 月跨年同日 | date |
| AC-032-* | TC-UNIT-012 | 单元 | sim | 新写 | test_core_rules.py::RateLimiterTests::test_hit_limit_and_deny | 限 2 次，第 3 次拒绝且 retry_after ≥1 | 独立 key |
| AC-032-* | TC-UNIT-013 | 单元 | sim | 新写 | test_core_rules.py::RateLimiterTests::test_register_failure_locks | 连续失败达上限 → 锁定；reset 后解锁 | 独立 key |
| AC-032-* | TC-UNIT-014 | 单元 | sim | 新写 | test_core_rules.py::RateLimiterTests::test_rate_limited_error_shape | code=CODE_RATE_LIMITED、429、details.retry_after | 30 秒 |
| AC-049-* | TC-UNIT-015 | 单元 | sim | 新写 | test_domain_rules.py::ClaimAmountRuleTests::test_accept_two_decimals | "300.50" → Decimal("300.50") | 金额字符串 |
| AC-049-* | TC-UNIT-016 | 单元 | sim | 新写 | test_domain_rules.py::ClaimAmountRuleTests::test_reject_three_decimals | 三位小数 → `INVALID_VALUE` | "300.555" |
| AC-049-* | TC-UNIT-017 | 单元 | sim | 新写 | test_domain_rules.py::ClaimAmountRuleTests::test_reject_zero_and_overflow | 0 与超上限被拒 | "0"、"1000000.01" |
| AC-049-* | TC-UNIT-018 | 单元 | sim | 新写 | test_domain_rules.py::ClaimAmountRuleTests::test_reject_non_numeric | 非数字被拒 | "abc" |
| AC-059-* | TC-UNIT-019 | 单元 | sim | 新写 | test_domain_rules.py::IncomeParseRuleTests::test_parse_ok_with_comma_amount | 千分位金额解析为 1000.50，total=1 | CSV 行 |
| AC-059-* | TC-UNIT-020 | 单元 | sim | 新写 | test_domain_rules.py::IncomeParseRuleTests::test_missing_column | 缺列 → `IMPORT_COLUMNS_MISSING` | 3 列 CSV |
| AC-059-03 | TC-UNIT-021 | 单元 | sim | 现有（0.4.0 按 AC 更新） | test_domain_rules.py::IncomeParseRuleTests::test_row_error_ratio_over_2_percent | 错误率 >2% 也不整体拒绝：total=43、有效 40、错误行号 [42,43,44] | 40 正常 +3 错误 |
| AC-059-* | TC-UNIT-022 | 单元 | sim | 新写 | test_domain_rules.py::IncomeParseRuleTests::test_row_error_ratio_within_2_percent | 错误率 ≤2% 时导入 61 行并返回 1 条错误 | 60 正常 +1 错误 |
| AC-055-* | TC-UNIT-023 | 单元 | sim | 新写 | test_domain_rules.py::PollQuestionRuleTests::test_accept_valid | 两选项题目校验通过 | 题目 JSON |
| AC-055-* | TC-UNIT-024 | 单元 | sim | 新写 | test_domain_rules.py::PollQuestionRuleTests::test_reject_single_option | 单选项被拒 | 题目 JSON |
| AC-055-* | TC-UNIT-025 | 单元 | sim | 新写 | test_domain_rules.py::PollQuestionRuleTests::test_reject_duplicate_keys | 重复选项 key 被拒 | 题目 JSON |
| AC-057-* | TC-UNIT-026 | 单元 | sim | 新写 | test_domain_rules.py::PollResultRuleTests::test_percentage_uses_responses | 3 份应答、AGREE 2 → count=2、66.7%、33.3% | 3 用户 + 1 题 |
| AC-046-*、AC-065-* | TC-UNIT-027 | 单元 | sim | 新写 | test_domain_rules.py::ResolutionJudgeRuleTests::test_half_majority_passed | 3 人 2 同意 → PASSED，denominator=3 | 3 委员席位 |
| AC-046-* | TC-UNIT-028 | 单元 | sim | 新写 | test_domain_rules.py::ResolutionJudgeRuleTests::test_half_majority_failed | 1 同意 1 反对 1 弃权 → REJECTED | 3 票 |
| AC-065-* | TC-UNIT-029 | 单元 | sim | 新写 | test_domain_rules.py::ResolutionJudgeRuleTests::test_judge_not_due | 未到期 → NOT_DUE，状态不变 | deadline +1h |
| AC-065-* | TC-UNIT-030 | 单元 | sim | 新写 | test_domain_rules.py::ResolutionJudgeRuleTests::test_judge_twice_idempotent | 二次判定 → ALREADY_DECIDED | 3 票同意 |
| AC-039-* | TC-UNIT-031 | 单元 | sim | 新写 | test_domain_rules.py::CommitteeRuleTests::test_member_vs_representative | 委员 is_member=true、代表 false，代表 is_representative=true，分母 1 | 2 席位 |
| AC-027-* | TC-UNIT-032 | 单元 | sim | 新写 | test_domain_rules.py::HeadPromotionRuleTests::test_promote_owner_when_head_vacant | 户主空缺 → OWNER 晋升 HEAD 且 head_slot=1 | 1 户 1 业主 |
| AC-027-* | TC-UNIT-033 | 单元 | sim | 新写 | test_domain_rules.py::HeadPromotionRuleTests::test_no_owner_no_promotion | 无 OWNER → 返回 None | 空户 |
| AC-059-02 | TC-UNIT-034 | 单元 | sim | 新写 | test_domain_rules.py::IncomeParseRuleTests::test_duplicate_rows_in_file_skipped | 文件内重复行跳过并给行号 3；备注不同不影响判重 | CSV 行 |
| AC-059-05 | TC-UNIT-035 | 单元 | sim | 新写 | test_domain_rules.py::IncomeParseRuleTests::test_all_rows_skipped | 全部行错误：records=[]、errors=2、不抛错 | CSV 行 |
| AC-059-03 | TC-UNIT-036 | 单元 | sim | 新写（同一测试方法内的附属断言，不单独计数） | （同 TC-UNIT-021 附属断言） | 错误原因均为 INVALID_FIELD | CSV 行 |
| AC-061-01/02 | TC-UNIT-037 | 单元 | sim | 新写 | test_rework_rules.py::GenerateDueIdempotencyTests::test_generates_prev_quarter_and_prev_year_once | generate_due 生成上一季度与上一年度各一份，重复调用不新增 | 台账数据 |
| AC-061-01 | TC-UNIT-038 | 单元 | sim | 新写 | 同::test_first_quarter_uses_previous_year_q4 | 一季度时取上一年 Q4 | 固定日期 |
| AC-061-02 | TC-UNIT-039 | 单元 | sim | 新写 | 同::test_stale_report_regenerated_only_for_affected_period | 账目变化后仅重算过期周期 | 台账数据 |
| CR-024（REQ-NFUNC 安全配置） | TC-UNIT-040 | 单元 | sim | 新写 | test_rework_rules.py::SecretKeyStartupTests::test_missing_secret_key_refuses_to_start | 缺 DJANGO_SECRET_KEY → ImproperlyConfigured | 环境变量隔离 |
| CR-024 | TC-UNIT-041 | 单元 | sim | 新写 | 同::test_empty_secret_key_refuses_to_start | 空值同样拒绝启动 | 环境变量隔离 |
| CR-024 | TC-UNIT-042 | 单元 | sim | 新写 | 同::test_provided_secret_key_starts_with_safe_default_hosts | 提供密钥可启动，ALLOWED_HOSTS 默认 localhost,127.0.0.1 | 环境变量隔离 |
| CR-024 | TC-UNIT-043 | 单元 | sim | 新写 | 同::test_debug_allows_ephemeral_key | DEBUG 下允许进程内随机密钥 | 环境变量隔离 |

### 单元层（vitest，Web/小程序）

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置 | 前置/动作/预期 |
|---|---|---|---|---|---|---|
| US-036/041（CR-012） | TC-WEB-001~005 | 单元 | sim | 新写 | frontend/tests/auth.store.spec.js（含 it.each 的 TC-WEB-002 共 8 个用例） | fetchMe 取 GET /me；identities 取 labels；职位枚举 CHAIR/VICE_CHAIR/MEMBER 的 isCommittee/isChairOrVice；游客不抛错；旧数组结构不抛 TypeError；setAuth/logout |
| US-049~059、012、014、026（CR-013~016、019） | TC-WEB-006~016 | 单元 | sim | 新写 | frontend/tests/api.spec.js（11） | 报销/预借/核销、投票作答 /responses、绑定换绑、改密、收入表逐条录入、撤销认证、附件、申诉 proof_ids、登录；全量 api 函数各发 1 次合法请求 |
| US-003/012/014/049/051/052~057（CR-013/014/019/020） | TC-MP-001~011 | 单元 | sim | 新写 | miniprogram/tests/api.spec.js（11） | 前缀/令牌/头、claims、polls、手机号、登录、申诉、上传、401 处理、全量函数健全性 |
| US-041 | TC-MP-012~013 | 单元 | sim | 新写 | miniprogram/tests/store.spec.js（2） | fetchMe 保存 profile 与 identities 对象；无令牌不请求；setAuth/clear |

### 集成层（TC-INT）

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置（文件::类::方法） | 前置/动作/预期 | 测试数据 |
|---|---|---|---|---|---|---|---|
| AC-001-01/03 | TC-INT-001 | 集成 | sim | 新写 | test_auth_api.py::RegistrationAndLoginTests::test_register_with_sms_code | 取码→注册 201，status ACTIVE，/me 含"游客" | 唯一手机号 |
| AC-001-04 | TC-INT-002 | 集成 | sim | 新写 | 同::test_duplicate_phone_returns_409 | 已注册手机号取码 → 409 `PHONE_ALREADY_REGISTERED` | 已有用户 |
| AC-001-02 | TC-INT-003 | 集成 | sim | 新写 | 同::test_wrong_code_then_locked | 连续错码 5 次后 429 `CODE_LOCKED` | 错误码 000000 |
| AC-001-05 | TC-INT-004 | 集成 | sim | 新写 | 同::test_code_resend_rate_limited | 60 秒内重发 → 429 `CODE_RATE_LIMITED` | 同一手机号 |
| AC-003-01 | TC-INT-005 | 集成 | sim | 新写 | 同::test_login_by_code | 已注册手机号取 LOGIN 码 → 200 且返回 token | 验证码登录 |
| AC-003-03/04 | TC-INT-006 | 集成 | sim | 新写 | 同::test_login_by_password_and_lockout | 设密码后连续 4 次错密 400，第 5 次 429 `LOGIN_LOCKED`，正确密码仍 429 | 密码 "Ocap2026pass" |
| AC-005-*、AC-009-* | TC-INT-007 | 集成 | sim | 新写 | 同::test_login_by_password_after_set | 设置密码后密码登录成功返回 token | 同上 |
| AC-069-* | TC-INT-008 | 集成 | sim | 新写 | 同::test_logout_revokes_token | 登出 204，旧 token 访问 /me → 401 | 注册用户 |
| AC-004-01、AC-008-* | TC-INT-009 | 集成 | sim | 新写 | 同::test_miniapp_login_unavailable_without_sdk | 无微信 SDK 环境调用小程序登录 → 503 `WECHAT_UNAVAILABLE`（环境降级证据） | mock code |
| AC-030-* | TC-INT-010 | 集成 | sim | 新写 | ProfileTests::test_edit_profile_and_forbidden_field | PATCH 昵称成功；改 identity_label → 400 `FIELD_NOT_EDITABLE` | 注册用户 |
| AC-030-* | TC-INT-011 | 集成 | sim | 新写 | 同::test_nickname_length_validated | 31 字符昵称 → 400 `INVALID_VALUE` | "x"*31 |
| AC-030-*、C-12 | TC-INT-012 | 集成 | sim | 新写 | 同::test_avatar_upload_and_reject_bad_type | PNG 上传 201；exe → 400 | 伪造 PNG 字节流 |
| AC-007-*、AC-017-* | TC-INT-013 | 集成 | sim | 新写 | 同::test_email_verify_and_login_by_email | 邮箱验证码验证成功；清限流后邮箱登录返回同一 user id | owner@example.com |
| AC-031-* | TC-INT-014 | 集成 | sim | 新写 | 同::test_cancel_account_requires_code | CANCEL 码注销 204，旧 token 401 | 独立手机号 |
| AC-011-*、AC-034-* | TC-INT-015 | 集成 | sim | 新写 | AdminAuthTests::test_admin_login_and_audit | 管理员登录 200，可读 audit-logs | boss/Admin12345 |
| AC-011-* | TC-INT-016 | 集成 | sim | 新写 | 同::test_admin_login_wrong_password | 错误密码 400 | boss2 |
| AC-011-*、AC-034-* | TC-INT-017 | 集成 | sim | 新写 | 同::test_member_token_cannot_call_admin | 普通用户 token 访问管理接口 → 403 | 注册用户 |
| AC-020-* | TC-INT-018 | 集成 | sim | 新写 | test_residency_api.py::RegistryAndCertificationTests::test_unit_options_paged_by_level | 传 building 返回 level=unit_no；再传 unit_no/floor 返回 level=room | 1 个清册单元 |
| AC-019-* | TC-INT-019 | 集成 | sim | 新写 | 同::test_admin_registry_import_dry_run_and_commit | dry_run 导入 0 条；正式导入 2 条 | 2 行 CSV |
| AC-018-*、AC-021-*、AC-023-* | TC-INT-020 | 集成 | sim | 新写 | 同::test_admin_unit_phones_then_certify_as_head | 管理员维护手机号后认证 201 且 role=HEAD | 1 单元 1 手机号 |
| AC-022-*、AC-026-* | TC-INT-021 | 集成 | sim | 新写 | 同::test_certification_phone_mismatch_422 | 手机号不在清册 → 422 `PHONE_NOT_IN_REGISTRY` 且 details.appeal_available | 他户手机号 |
| AC-022-*、AC-023-* | TC-INT-022 | 集成 | sim | 新写 | 同::test_second_owner_becomes_owner_and_duplicate_rejected | 第二位认证 role=OWNER；重复认证 409 `ALREADY_CERTIFIED` | 1 单元 2 手机号 |
| AC-021-* | TC-INT-023 | 集成 | sim | 新写 | 同::test_unit_not_found | unit_id=999999 → 404 `NOT_FOUND` | 不存在 ID |
| AC-026-* | TC-INT-024 | 集成 | sim | 新写 | AppealTests::test_appeal_requires_proof_and_admin_approve_makes_owner | 无凭证 400 `PROOF_REQUIRED`；带凭证申诉 201；管理员核准后产生 HEAD 成员 | 伪造 PNG 附件 |
| AC-026-* | TC-INT-025 | 集成 | sim | 新写 | 同::test_appeal_reject_requires_reason | 拒绝无理由 400；带理由成功 REJECTED | 同上 |
| AC-024-*、AC-029-* | TC-INT-026 | 集成 | sim | 新写 | ResidentTests::test_owner_approves_and_removes_resident | 申请 201 → 户主待审 1 条 → 同意 → 产生 RESIDENT → 移除 204 后无有效成员 | 户主 + 申请人 |
| AC-024-* | TC-INT-027 | 集成 | sim | 新写 | 同::test_only_owner_can_decide | 非该户产权业主审批 → 403 | 陌生人 token |
| AC-029-* | TC-INT-028 | 集成 | sim | 新写 | 同::test_resident_can_leave | 同住人主动离开 204 | 预置 RESIDENT |
| AC-027-*、AC-036-* | TC-INT-029 | 集成 | sim | 新写 | MembershipRevokeTests::test_revoke_head_promotes_owner_and_ends_seat | 撤销户主后 OWNER 晋升 HEAD，原委员席位失效 | 户主 + 业主 + 席位 |
| AC-037-* | TC-INT-030 | 集成 | sim | 新写 | SeatTests::test_grant_requires_owner_and_returns_seat | 非业主授予 422 `NOT_AN_OWNER`；业主授 CHAIR 201 | 项目配置任期 |
| AC-040-* | TC-INT-031 | 集成 | sim | 新写 | 同::test_config_cap_reports_over_cap | cap_member=0 且已有 1 委员 → over_cap=true | 配置 + 席位 |
| AC-038-* | TC-INT-032 | 集成 | sim | 新写 | 同::test_revoke_seat | 删除席位 204，状态 REVOKED | 1 席位 |
| AC-040-* | TC-INT-033 | 集成 | sim | 新写 | 同::test_cap_enforced_on_grant | cap_vice=0 时授予副主任 → 409/422 | 配置 |
| AC-043-*、AC-045-* | TC-INT-034 | 集成 | sim | 新写 | test_approval_resolution_api.py::ApprovalFlowTests::test_designated_flow_requires_committee_approver | 指定非委员为审批人 → 422 `APPROVER_NOT_COMMITTEE_MEMBER` | 普通用户 ID |
| AC-043-*、AC-046-* | TC-INT-035 | 集成 | sim | 新写 | 同::test_half_majority_only_for_resolution | EXPENSE 配 HALF_MAJORITY → 400 `INVALID_VALUE` | 管理端流程 |
| AC-043-* | TC-INT-036 | 集成 | sim | 新写 | 同::test_flow_options_visible_to_committee | 普通用户读流程 403；委员读 200 且 1 条 | EXPENSE 流程 |
| AC-045-*、AC-047-* | TC-INT-037 | 集成 | sim | 新写 | DesignatedResolutionTests::test_designated_approve_then_public | 主任发起 201 → 指定人同意 → 状态 APPROVED → 其他业主可读详情 | 主任 + 委员 |
| AC-047-* | TC-INT-038 | 集成 | sim | 新写 | 同::test_public_list_visible_to_any_member | 主任发起→指定人拒绝→普通业主 GET 公开列表 200 且 count=1（**实际 403，DEF-001**） | 同上 |
| AC-044-*、AC-048-* | TC-INT-039 | 集成 | sim | 新写 | 同::test_pending_detail_forbidden_to_stranger | 审批中决议被陌生人读取 → 403 `FORBIDDEN` | 游民 token |
| AC-045-* | TC-INT-040 | 集成 | sim | 新写 | 同::test_non_approver_cannot_decide | 非审批人审批 → 403 | 陌生人 token |
| AC-045-* | TC-INT-041 | 集成 | sim | 新写 | 同::test_todo_list_for_approver | 审批人待办 1 条，主任 0 条 | 同上 |
| AC-048-* | TC-INT-042 | 集成 | sim | 新写 | 同::test_withdraw_and_resubmit | 撤回 WITHDRAWN → 重提 PENDING、revision=2 | 主任 token |
| AC-046-*、AC-065-* | TC-INT-043 | 集成 | sim | 新写 | HalfMajorityResolutionTests::test_deadline_window_validated | 截止时间 5 分钟后 → 400 `VOTE_WINDOW_TOO_SHORT` | 4 委员 |
| AC-046-* | TC-INT-044 | 集成 | sim | 新写 | 同::test_vote_requires_committee_and_once | 非委员投票 403；委员同意 200；重复投票 409 `ALREADY_VOTED` | 游民 + 委员 |
| AC-046-*、AC-065-* | TC-INT-045 | 集成 | sim | 新写 | 同::test_judge_after_deadline_passes | 3 委员同意，未到期仍 PENDING；到期后 run_due_jobs → APPROVED，agree=3，denominator=4 | 3 票 |
| AC-046-* | TC-INT-046 | 集成 | sim | 新写 | 同::test_vote_after_deadline_blocked | 截止后投票 → 409 `VOTE_CLOSED` | 过期 deadline |
| AC-049-* | TC-INT-047 | 集成 | sim | 新写 | test_finance_polls_api.py::ClaimTests::test_amount_precision_and_validation | 300.50 创建 201；300.555 与 0 → 400 `INVALID_VALUE` | 委员 + 指定审批 |
| AC-050-* | TC-INT-048 | 集成 | sim | 新写 | 同::test_approve_claim | 指定审批同意 → claim APPROVED | 同上 |
| AC-067-* | TC-INT-049 | 集成 | sim | 新写 | 同::test_self_approval_forbidden | 自批流程创建/审批 → 400/403/422（前置拦截） | 申请人即审批人 |
| AC-048-*、AC-049-* | TC-INT-050 | 集成 | sim | 新写 | 同::test_withdraw_and_resubmit | 撤回 WITHDRAWN → 重提金额 280.00、revision=2 | 报销单 |
| AC-051-* | TC-INT-051 | 集成 | sim | 新写 | 同::test_settlement_requires_income_member | 普通业主 403；业委会成员 201 且 type=SETTLEMENT | 备用金结算 |
| AC-051-* | TC-INT-052 | 集成 | sim | 新写 | 同::test_advance_and_settlement | 备用金预借 → 核销（/claims/advances、/claims/settlements）流程 | 同上 |
| AC-049-* | TC-INT-053 | 集成 | sim | 新写 | 同::test_stranger_cannot_view_claim | 陌生人读报销详情 → 403 | 游民 token |
| AC-049-*、AC-064-* | TC-INT-054 | 集成 | sim | 新写 | 同::test_admin_can_list_claims | 管理员列表 count=1 | 管理端 token |
| AC-058-*、AC-059-* | TC-INT-055 | 集成 | sim | 新写 | IncomeTests::test_import_totals_and_validation | 导入 1 行 → total 300.50，import_summary.imported=1 | 收入 CSV |
| AC-058-* | TC-INT-056 | 集成 | sim | 新写 | 同::test_import_requires_committee | 非委员导入 → 403 `FORBIDDEN` | 普通业主 |
| AC-059-* | TC-INT-057 | 集成 | sim | 新写 | 同::test_import_row_error_ratio | 错误率 >2% → 400 `IMPORT_ROW_ERRORS` | 40+3 行 |
| AC-059-* | TC-INT-058 | 集成 | sim | 新写 | 同::test_import_missing_columns | 缺列 → 400 `IMPORT_COLUMNS_MISSING` | 单列 CSV |
| AC-060-* | TC-INT-059 | 集成 | sim | 新写 | 同::test_submit_approve_and_void | 提交 PENDING → 审批 APPROVED → 作废 VOIDED | 收入表 |
| AC-060-* | TC-INT-060 | 集成 | sim | 新写 | 同::test_submit_empty_sheet | 空表提交 → 409 `INCOME_SHEET_EMPTY` | 空收入表 |
| AC-063-* | TC-INT-061 | 集成 | sim | 新写 | 同::test_approved_sheets_visible_to_any_member | 普通业主读已生效收入表 → 200（**实际 403，DEF-002**） | 已审批收入表 |
| AC-061-* | TC-INT-062 | 集成 | sim | 新写 | LedgerTests::test_generate_totals_and_precision | 生成台账 201，收入 300.50 / 支出 100.00 / 结余 200.50 | 已审批收入 + 报销 |
| AC-063-* | TC-INT-063 | 集成 | sim | 新写 | 同::test_report_visible_to_any_member | 普通业主读台账列表 200 count=1（**实际 403，DEF-002**） | 同上 |
| AC-062-* | TC-INT-064 | 集成 | sim | 新写 | 同::test_regenerate_same_period | 同期二次生成 201 且 version ≥2（**实际 409 LEDGER_LOCKED，DEF-003**） | 同上 |
| AC-061-* | TC-INT-065 | 集成 | sim | 新写 | 同::test_non_committee_cannot_generate | 普通业主生成台账 → 403 `FORBIDDEN` | 普通业主 |
| AC-052-* | TC-INT-066 | 集成 | sim | 新写 | PollTests::test_only_chair_or_vice_creates | 主任创建 201；普通委员创建 403 | 主任 + 委员 |
| AC-052-* | TC-INT-067 | 集成 | sim | 新写 | 同::test_deadline_window | 截止 5 分钟后 → 400 `VOTE_WINDOW_TOO_SHORT` | 同上 |
| AC-052-*、AC-056-* | TC-INT-068 | 集成 | sim | 新写 | 同::test_vote_and_duplicate | 委员应答 201；重复 409 `ALREADY_VOTED` | 委员 token |
| AC-055-*、AC-056-* | TC-INT-069 | 集成 | sim | 新写 | 同::test_invalid_option_rejected | 非法选项 → 400 `INVALID_VALUE` | 选项 NOPE |
| AC-054-*、AC-056-* | TC-INT-070 | 集成 | sim | 新写 | 同::test_owner_participates_in_survey | 产权业主应答调查 → 201（**实际 403，DEF-004**） | 普通业主 |
| AC-052-*、AC-053-* | TC-INT-071 | （作废） | — | — | 集成层无独立用例，业主代表应答由 TC-E2E-009 覆盖 | 不计入集成层计数 | — |
| AC-057-* | TC-INT-072 | 集成 | sim | 新写 | 同::test_results_after_close | 未截止读结果 409 `NOT_CLOSED`；截止后 200 且计数 1 | 1 应答 |
| AC-059-05 | TC-INT-073 | 集成 | sim | 新写 | test_finance_polls_api.py::IncomeTests::test_import_all_rows_skipped_creates_nothing | 全部行错误 → 200，sheet=None，imported=0、failed=2，不建表 | fixture 现造 |
| US-041/036（CR-012） | TC-INT-074 | 集成 | sim | 新写 | test_frontend_contract.py::FieldContractTests::test_me_identities_is_object_and_frontend_reads_existing_keys | /me 的 identities 为对象；前端读取的 labels/committee/profile 键均存在 | fixture 现造 |
| US-040 | TC-INT-075 | 集成 | sim | 新写 | 同::test_web_auth_store_position_values_match_backend_enum | Web store 的职位值与后端枚举一致 | fixture 现造 |
| US-049/050/051（CR-013） | TC-INT-076 | 集成 | sim | 新写 | 同::test_claims_payload_fields_match_backend | 报销/预借/核销字段被后端接受，scope=mine 列表字段齐全 | fixture 现造 |
| US-049（CR-013） | TC-INT-077 | 集成 | sim | 新写 | 同::test_old_claim_payload_shapes_are_rejected | 旧请求结构被拒（回归） | fixture 现造 |
| US-052~057（CR-014） | TC-INT-078 | 集成 | sim | 新写 | 同::test_polls_create_and_responses_contract | 创建体与 /responses、answers[{question_id,value}] 契约 | fixture 现造 |
| US-058/059（CR-016） | TC-INT-079 | 集成 | sim | 新写 | 同::test_income_sheet_contract | 收入表逐条录入 records/voucher_ids 契约 | fixture 现造 |
| US-012/014/028（CR-019） | TC-INT-080 | 集成 | sim | 新写 | 同::test_phone_bind_change_contract | bind/change 请求字段与响应 {merged,phone,token,user} | fixture 现造 |
| US-001/003/070（CR-020） | TC-INT-081 | 集成 | sim | 新写 | 同::test_login_and_register_responses_carry_token_user_and_is_new | 登录/注册响应含 token/user/is_new | fixture 现造 |
| 画像 P5 前后端契约 | TC-INT-082 | 集成 | sim | 新写 | 同::RouteContractTests::test_web_api_routes_exist_and_support_method | Web api.js 每个调用可解析路由且视图支持该方法（**失败：DEF-005**） | fixture 现造 |
| 画像 P5 | TC-INT-083 | 集成 | sim | 新写 | 同::RouteContractTests::test_miniprogram_api_routes_exist_and_support_method | 小程序 api.js 同上 | fixture 现造 |
| 画像 P5（CR-013/014/015） | TC-INT-084 | 集成 | sim | 新写 | 同::RouteContractTests::test_known_bad_paths_from_gr_c_004_are_gone | GR-C-004 错误路径不再被前端调用 | fixture 现造 |
| AC-012-01 / AC-072-01 | TC-INT-085 | 集成 | sim | 新写 | test_rework_cr011_024.py::AccountMergeTests::test_bind_phone_merges_and_keeps_primary_answer | 绑定他人手机号 → 合并，答卷冲突保留主账号并写 MERGE_ANSWER_DISCARDED | fixture 现造 |
| AC-072-02 | TC-INT-086 | 集成 | sim | 新写 | 同::test_bind_phone_merge_moves_secondary_only_answer | 仅副账号作答 → 并入，票数不变 | fixture 现造 |
| AC-012-03 | TC-INT-087 | 集成 | sim | 新写 | 同::test_bind_free_phone_does_not_merge | 未被占用手机号仅绑定 | fixture 现造 |
| AC-012-02 | TC-INT-088 | 集成 | sim | 新写 | 同::test_bind_wrong_code_does_not_merge | 验证码错误不合并 | fixture 现造 |
| AC-014-01 / AC-072-01 | TC-INT-089 | 集成 | sim | 新写 | 同::test_change_phone_merges_into_new_phone_account | 换绑合并，以新号账号为主 | fixture 现造 |
| AC-051-* | TC-INT-090 | 集成 | sim | 新写 | 同::SettlementLedgerTests::test_advance_approved_counts_before_settlement | 预借通过未核销时计入支出 | fixture 现造 |
| AC-051-03 | TC-INT-091 | 集成 | sim | 新写 | 同::test_settle_owe_more_pays_difference | 预借 1000/报销 1200 → 差额 +200，支出合计 1200 | fixture 现造 |
| AC-051-02 | TC-INT-092 | 集成 | sim | 新写 | 同::test_settle_refund_returns_cash | 预借 1000/报销 800 → 差额 -200，支出合计 800 | fixture 现造 |
| AC-051-01 | TC-INT-093 | 集成 | sim | 新写 | 同::test_settle_exact_equal_keeps_expense | 恰好相等 → 差额 0，支出 1000 不重复 | fixture 现造 |
| AC-051-04/06 | TC-INT-094 | 集成 | sim | 新写 | 同::test_settle_requires_reimbursement_and_rejects_resettle | 未关联报销单被拒；已核销不可再核销 | fixture 现造 |
| AC-061-01/02 | TC-INT-095 | 集成 | sim | 新写 | 同::LedgerJobTests::test_run_due_jobs_generates_reports_idempotently | run_due_jobs 生成上季/上年报表，重复运行不重复 | fixture 现造 |
| AC-058-01/08 | TC-INT-096 | 集成 | sim | 新写 | 同::IncomeEntryTests::test_single_entry_creates_one_sheet | 逐条录入创建 DRAFT 收入表，合计正确 | fixture 现造 |
| AC-058-02/03 | TC-INT-097 | 集成 | sim | 新写 | 同::test_single_entry_rejects_bad_amount_and_non_committee | 三位小数 400；非成员 403 | fixture 现造 |
| AC-059-02 | TC-INT-098 | 集成 | sim | 新写 | 同::test_import_skips_duplicate_rows_in_file | 文件内重复行跳过并给行号 | fixture 现造 |
| AC-059-02/05 | TC-INT-099 | 集成 | sim | 新写 | 同::test_import_skips_rows_duplicating_pending_sheet | 与 PENDING 表重复行跳过；全部重复不建表 | fixture 现造 |
| US-026（CR-015） | TC-INT-100 | 集成 | sim | 新写 | 同::AdminAttachmentDownloadTests::test_admin_downloads_appeal_proof | 管理员可下载申诉附件；无关用户 404；未登录 401 | fixture 现造 |
| AC-006-01 | TC-INT-101 | 集成 | sim | 新写 | test_gap_must_have.py::WebPhoneLoginTests::test_code_login_returns_token_for_registered_phone | 已注册手机号 + 有效验证码 → 200，令牌可访问 /me 且为同一用户。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-006-02 | TC-INT-102 | 集成 | sim | 新写 | test_gap_must_have.py::WebPhoneLoginTests::test_password_login_by_phone_identifier | 设置密码后，用手机号 + 正确密码登录成功。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-006-03 | TC-INT-103 | 集成 | sim | 新写 | test_gap_must_have.py::WebPhoneLoginTests::test_password_login_failure_message_is_uniform | 未设密码 / 手机号未注册 / 密码错误三种情形，返回相同的 code 与 message（不泄露账号是否存在）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-006-04 | TC-INT-104 | 集成 | sim | 新写 | test_gap_must_have.py::WebPhoneLoginTests::test_wrong_login_code_rejected | 错误验证码 → 400 CODE_INVALID，且未签发令牌。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-006-04 | TC-INT-105 | 集成 | sim | 新写 | test_gap_must_have.py::WebPhoneLoginTests::test_expired_login_code_rejected | 验证码超过有效期 → 400 CODE_EXPIRED。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-006-04 | TC-INT-106 | 集成 | sim | 新写 | test_gap_must_have.py::WebPhoneLoginTests::test_login_code_invalidated_after_five_wrong_attempts | 同一验证码输错 5 次作废；之后即使输入正确验证码也不能登录。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-006-04 | TC-INT-107 | 集成 | sim | 新写 | test_gap_must_have.py::WebPhoneLoginTests::test_password_wrong_five_times_locks_account | 密码连续输错 5 次锁定（429 LOGIN_LOCKED，含 retry_after；锁定时长 15 分钟）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-010-01 | TC-INT-108 | 集成 | sim | 新写 | test_gap_must_have.py::SingleAccountAcrossEntriesTests::test_web_and_miniprogram_phone_logins_reach_same_account_and_identity | 产权业主分别以 Web 验证码登录、小程序（EXTENDED 会话）验证码登录、密码登录 → 同一 user id，身份均含“户主”。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-010-02 | TC-INT-109 | 集成 | sim | 新写 | test_gap_must_have.py::SingleAccountAcrossEntriesTests::test_wechat_bind_phone_then_wechat_and_phone_logins_same_account | 微信登录（新建账号）→ 绑定未被占用手机号 → 再微信登录 / 手机号登录 → 同一账号。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-010-03 | TC-INT-110 | 集成 | sim | 新写 | test_gap_must_have.py::SingleAccountAcrossEntriesTests::test_second_account_for_same_phone_rejected | 同一手机号不能再创建第二个账号：取注册码 409；微信账号绑定该号 → 合并为一个账号（总数不增加）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-070-01/02 | TC-INT-111 | 集成 | sim | 新写 | test_gap_must_have.py::SingleAccountAcrossEntriesTests::test_first_wechat_login_is_new_then_not_new_and_profile_kept | 首次小程序微信登录 is_new=true；保存昵称后再次微信登录 is_new=false，昵称保持用户最后设置的值。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-070-03 | TC-INT-112 | 集成 | sim | 新写 | test_gap_must_have.py::SingleAccountAcrossEntriesTests::test_phone_login_is_never_new | 已有账号手机号登录响应 is_new=false（不触发头像昵称设置页）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-070-04 | TC-INT-113 | 集成 | sim | 新写 | test_gap_must_have.py::SingleAccountAcrossEntriesTests::test_web_scan_first_login_takes_wechat_nickname_without_setup | Web 扫码首次微信登录 → 昵称取微信昵称（FakeWeChatClient 返回“微信用户”），不经头像昵称设置页。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-013-01 | TC-INT-114 | 集成 | sim | 新写 | test_gap_must_have.py::ReRegisterAfterCancelTests::test_reregister_creates_fresh_guest_account | 注销后同号注册 → 新 user id，身份“游客”，原户主身份/昵称不恢复，新旧账号无关联。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-013-02 | TC-INT-115 | 集成 | sim | 新写 | test_gap_must_have.py::ReRegisterAfterCancelTests::test_reregister_owner_must_certify_again | 原产权业主注销后同号注册 → 需重新清册认证（认证前无户主；认证 201 后才获得身份）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-013-03 | TC-INT-116 | 集成 | sim | 新写 | test_gap_must_have.py::ReRegisterAfterCancelTests::test_register_with_active_phone_rejected | 手机号账号未注销 → 注册被拒（409 PHONE_ALREADY_REGISTERED）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-025-02 | TC-INT-117 | 集成 | sim | 新写 | test_gap_must_have.py::GuestTests::test_guest_can_apply_for_certification_and_resident_binding | 游客可提交清册认证（201）与同住人申请（201）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-025-03 | TC-INT-118 | 集成 | sim | 新写 | test_gap_must_have.py::GuestTests::test_guest_cannot_do_owner_only_actions | 游客审批同住人申请 / 移除同住人 / 读取待审列表 → 403。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-028-01 | TC-INT-119 | 集成 | sim | 新写 | test_gap_must_have.py::ChangePhoneTests::test_change_to_free_phone_keeps_all_identities | 新号未属任何账号 → 更换成功，不合并，户主身份保留。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-028-02 | TC-INT-120 | 集成 | sim | 新写 | test_gap_must_have.py::ChangePhoneTests::test_change_with_wrong_new_code_changes_nothing | 新号验证码错误 → 400/429，原手机号与身份不变。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-028-04 | TC-INT-121 | 集成 | sim | 新写 | test_gap_must_have.py::ChangePhoneTests::test_old_phone_cannot_login_after_change | 更换成功后旧号登录失败（404 PHONE_NOT_REGISTERED），新号登录进入同一账号。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-035-01 | TC-INT-122 | 集成 | sim | 新写 | test_gap_must_have.py::RegistryPhoneChangeAfterCertificationTests::test_modify_registry_phone_keeps_owner | 管理员把清册手机号改成其他号码 → 用户仍是该专有部分的有效产权业主。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-035-02 | TC-INT-123 | 集成 | sim | 新写 | test_gap_must_have.py::RegistryPhoneChangeAfterCertificationTests::test_delete_registry_phone_keeps_head | 管理员把清册手机号全部删除 → 户主身份仍在。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-035-03 | TC-INT-124 | 集成 | sim | 新写 | test_gap_must_have.py::RegistryPhoneChangeAfterCertificationTests::test_certification_after_change_compares_new_registry | 清册手机号改动后，他人用原号码认证 → 422 PHONE_NOT_IN_REGISTRY 且可申诉；新号码持有者认证成功。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-035-04 | TC-INT-125 | 集成 | sim | 新写 | test_gap_must_have.py::RegistryPhoneChangeAfterCertificationTests::test_non_admin_cannot_modify_registry_phones | 普通用户 / 业委会成员修改清册手机号 → 403；未登录 → 401（已收紧），清册不变。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-042-01 | TC-INT-126 | 集成 | sim | 新写 | test_gap_must_have.py::RepresentativeGrantTests::test_grant_to_owner_succeeds_and_user_becomes_participant | 产权业主被赋予 → 201；/me 显示业主代表；之后发起的代表投票自动含其参与；审计新增 SEAT_GRANTED（AC-042-06）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-042-02 | TC-INT-127 | 集成 | sim | 新写 | test_gap_must_have.py::RepresentativeGrantTests::test_grant_to_resident_or_guest_rejected | 同住人 / 游客被赋予 → 422 NOT_AN_OWNER。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-042-03 | TC-INT-128 | 集成 | sim | 新写 | test_gap_must_have.py::RepresentativeGrantTests::test_grant_over_cap_rejected | 业主代表人数已达上限（cap_rep=1） → 409 CAP_REACHED。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-042-04 | TC-INT-129 | 集成 | sim | 新写 | test_gap_must_have.py::RepresentativeGrantTests::test_grant_to_committee_member_rejected | 已持有委员席位者不可再被赋予业主代表（不可兼任）→ 409 ALREADY_SEATED。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-042-05 | TC-INT-130 | 集成 | sim | 新写 | test_gap_must_have.py::RepresentativeGrantTests::test_non_admin_cannot_grant | 普通业主 / 主任赋予业主代表 → 403；未登录 → 401（已收紧），无席位产生。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-068-01 | TC-INT-131 | 集成 | sim | 新写 | test_gap_must_have.py::InFlightIdentityInvalidationTests::test_initiator_seat_revoked_resolution_stays_pending_and_flow_continues | 发起人业委会身份被撤销 → 决议仍为审批中；原指定审批人仍可审批通过。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-068-02 | TC-INT-132 | 集成 | sim | 新写 | test_gap_must_have.py::InFlightIdentityInvalidationTests::test_approver_seat_revoked_cannot_approve_and_claim_stays_pending | 指定审批人身份被撤销 → 审批 403；报销单保持审批中，不自动转交。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-068-03 | TC-INT-133 | 集成 | sim | 新写 | test_gap_must_have.py::InFlightIdentityInvalidationTests::test_withdraw_and_resubmit_with_valid_flow_after_approvers_invalid | 审批人全部失效后，发起人撤回并选新的有效流程重新提交 → 重新进入审批中。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-068-04 | TC-INT-134 | 集成 | sim | 新写 | test_gap_must_have.py::InFlightIdentityInvalidationTests::test_expired_representative_cannot_respond_but_earlier_answer_and_denominator_kept | 业主代表 R1 已提交、R2 任期到期后提交被拒 403；R1 的答卷保持，分母（participant_count）仍为发起时的 2。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-068-05 | TC-INT-135 | 集成 | sim | 新写 | test_gap_must_have.py::InFlightIdentityInvalidationTests::test_public_resolution_still_shows_initiator_label_after_seat_revoked | 已公开决议在发起人身份失效后仍可读，且仍存在发起人信息（不被抹除）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-068-06 | TC-INT-136 | 集成 | sim | 新写 | test_gap_must_have.py::InFlightIdentityInvalidationTests::test_invalidated_user_cannot_use_privileged_actions | 身份失效者发起决议 / 发起投票 / 审批 → 403。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-068-07 | TC-INT-137 | 集成 | sim | 新写 | test_gap_must_have.py::InFlightIdentityInvalidationTests::test_invalidated_initiator_can_withdraw_own_but_others_cannot | 发起人身份已失效仍可撤回自己的在途决议（WITHDRAWN）；其他委员 / 管理员撤回他人事项被拒。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-071-01 | TC-INT-138 | 集成 | sim | 新写 | test_gap_must_have.py::MultiApproverTests::test_any_one_of_two_approvers_passes | 流程指定 P1、P2，P1 同意 → 申请 APPROVED。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-071-02 | TC-INT-139 | 集成 | sim | 新写 | test_gap_must_have.py::MultiApproverTests::test_second_approver_after_decision_rejected_state_unchanged | P1 已通过后 P2 再通过 / 拒绝 → 409 ALREADY_DECIDED，状态与金额不变。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-071-03 | TC-INT-140 | 集成 | sim | 新写 | test_gap_must_have.py::MultiApproverTests::test_only_self_in_flow_rejects_claim_advance_and_income | 流程审批人只有申请人本人 → 报销 / 预借 / 收入表提交均 422 NO_ELIGIBLE_APPROVER，且不创建申请。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-071-04 | TC-INT-141 | 集成 | sim | 新写 | test_gap_must_have.py::MultiApproverTests::test_submitter_with_another_approver_cannot_self_approve | 审批人为 M 与 P → 提交成功（PENDING）；M 自批 403 SELF_APPROVAL_FORBIDDEN；P 批准成功。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-071-05 | TC-INT-142 | 集成 | sim | 新写 | test_gap_must_have.py::MultiApproverTests::test_chair_designated_self_may_approve_resolution | 主任发起指定负责人审批的决议，负责人就是本人 → 允许审批通过，状态 APPROVED。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-071-06 | TC-INT-143 | 集成 | sim | 新写 | test_gap_must_have.py::MultiApproverTests::test_chair_not_designated_cannot_approve_resolution | 指定负责人是另一人 Q，主任 D 审批 → 403 FORBIDDEN，决议保持 PENDING。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-073-01 | TC-INT-144 | 集成 | sim | 新写 | test_gap_must_have.py::AdminPasswordResetTests::test_admin_resets_other_admin_password | A 重置 B → 204；B 旧密码登录 400，新密码登录 200；B 的旧令牌失效；审计 ADMIN_PASSWORD_RESET。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-073-02 | TC-INT-145 | 集成 | sim | 新写 | test_gap_must_have.py::AdminPasswordResetTests::test_member_cannot_reset_admin_password | 普通用户 / 产权业主 / 业委会成员调用重置接口 → 403，被重置者密码不变。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-073-03 | TC-INT-146 | 集成 | sim | 新写 | test_gap_must_have.py::AdminPasswordResetTests::test_anonymous_cannot_reset_and_no_self_service_entry | 未登录访客重置 → 401；系统没有管理员自助注册 / 找回入口（对应路径 404/405）。 | fixture 现造（next_phone / make_owner / make_seat / make_flow / FakeWeChatClient） |
| AC-002-02 | TC-INT-147 | 集成 | sim | 新写 | test_gap_must_have.py::WebWechatScanTests::test_second_scan_enters_existing_account | 同一微信再次扫码 → 进入已有账号，不新建账号 | FakeWeChatClient |
| AC-002-03 | TC-INT-148 | 集成 | sim | 新写 | test_gap_must_have.py::WebWechatScanTests::test_invalid_state_or_wechat_error_creates_no_account | 二维码失效（state 无效）或微信侧失败 → 重定向带 error，不创建账号、不发 ticket | FakeWeChatClient |
| AC-002-04 | TC-INT-149 | 集成 | sim | 新写 | test_gap_must_have.py::WebWechatScanTests::test_wechat_user_without_phone_must_bind_phone_before_certification | 未验证手机号的微信用户做清册认证 → 409 PHONE_REQUIRED；/me 不受限 | FakeWeChatClient |

### 集成层（vitest，页面挂载）

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置 | 前置/动作/预期 |
|---|---|---|---|---|---|---|
| US-041（CR-012） | TC-WEB-017~018 | 集成 | sim | 新写 | frontend/tests/pages.spec.js | 首页：委员显示 labels/昵称/手机号与“收入表”入口；游客显示“游客” |
| US-049~051（CR-013） | TC-WEB-019~024 | 集成 | sim | 新写 | 同 | Claims.vue 挂载按 scope=mine 拉取、报销先传发票再提交、预借、核销差额文案（少补/刚好核销） |
| US-052~057（CR-014） | TC-WEB-025~027 | 集成 | sim | 新写 | 同 | PollDetail 按题型渲染、一键提交 /responses、选答题、已作答回填、截止后查看结果 |
| US-012/014/017（CR-019） | TC-WEB-028~030 | 集成 | sim | 新写 | 同 | Me.vue 绑定/换绑（合并换令牌）、改密 PUT /me/password、注销带 phone+code |
| US-041/045/049~057/012/014/003 | TC-MP-014~027 | 集成 | sim | 新写 | miniprogram/tests/pages.spec.js | 小程序首页身份与待办、claims 表单、投票详情、手机号页、密码/验证码登录（uni 桩） |
| AC-006-01/02/04（0.5.0） | TC-WEB-031 | 集成 | sim | 新写 | frontend/tests/login.spec.js | Login.vue：发码 POST /auth/codes {purpose:LOGIN}；验证码登录 POST /auth/login/code；令牌保存 |
| AC-006-02 | TC-WEB-032 | 集成 | sim | 新写 | 同 | 密码登录 POST /auth/login/password {identifier,password,remember_me}；令牌保存 |
| AC-006-03/04 | TC-WEB-033 | 集成 | sim | 新写 | 同 | 失败提示后端统一文案；锁定附“900 秒后重试”；不保存令牌 |
| AC-070-01 | TC-MP-028 | 集成 | sim | 新写 | miniprogram/tests/pages.spec.js | ProfileSetup：onChooseAvatar 回填预览；save → PATCH /me/profile { nickname } → 进首页 |
| AC-070-01 | TC-MP-029 | 集成 | sim | 新写 | 同 | 保存失败 toast 后端文案且不跳转；skip 进首页 |
| AC-070-03 | TC-MP-030 | 集成 | sim | 新写 | 同 | 登录响应 is_new=false 不进设置页 |
| AC-070-01（既有） | TC-MP-027 | 集成 | sim | 现有 | 同 | 登录响应 is_new=true → 进设置页（已在 0.4.0 表中，此处补溯源到 AC-070-01） |

### E2E 层（TC-E2E）

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置（文件::类::方法） | 前置/动作/预期 | 测试数据 |
|---|---|---|---|---|---|---|---|
| AC-001-01/03、AC-021-*、AC-023-*、AC-030-* | TC-E2E-001 | E2E | sim | 新写 | test_journeys.py::OwnerOnboardingJourneyTests::test_register_certify_and_profile | 取码注册 → /me 游客 → 认证 HEAD → /me 含"户主" → 改昵称 | 唯一手机号 + 清册单元 |
| AC-024-*、AC-029-* | TC-E2E-002 | E2E | sim | 新写 | ResidentJourneyTests::test_owner_approves_then_removes_resident | 同住人申请 → 户主待审 → 同意 → /me 含"同住人" → 移除后消失 | 户主 + 申请人 |
| AC-026-* | TC-E2E-003 | E2E | sim | 新写 | AppealJourneyTests::test_appeal_restores_owner_identity | 认证 422 → 上传凭证申诉 → 管理员核准 → /me 含"户主" | 凭证 PNG |
| AC-044-*、AC-045-*、AC-047-* | TC-E2E-004 | E2E | sim | 新写 | DesignatedResolutionJourneyTests::test_resolution_approve_and_public_read | 主任发起 → 审批人待办 1 → 同意 APPROVED → 详情可读 → 公开列表可读（**列表 403，DEF-001**） | 主任 + 委员 |
| AC-046-*、AC-047-*、AC-065-* | TC-E2E-005 | E2E | sim | 新写 | HalfMajorityResolutionJourneyTests::test_vote_then_expire_and_publish | 3 委员同意 → 改过期 → run_due_jobs → APPROVED，result.agree=3 | 4 委员 |
| AC-049-*、AC-050-*、AC-058-*、AC-059-*、AC-060-*、AC-061-* | TC-E2E-006 | E2E | sim | 新写 | FinanceCommitteeJourneyTests::test_income_expense_and_ledger | 导入收入 → 提交审批 → 同意 → 报销 100 → 审批 → 台账生成 300.50/100.00/200.50 | CSV + 报销单 |
| AC-063-* | TC-E2E-007 | E2E | sim | 新写 | FinanceTransparencyJourneyTests::test_any_member_reads_reports | 已生效收入表 + 台账；普通业主读收入表列表（**403，DEF-002**）与台账列表 | 委员 + 业主 |
| AC-052-*、AC-053-*、AC-057-* | TC-E2E-008 | E2E | sim | 新写 | PollJourneyTests::test_committee_poll_lifecycle | 主任创建 → 委员应答 201 → 过期 → 结果 count=1 | 主任 + 委员 |
| AC-054-*、AC-055-*、AC-056-* | TC-E2E-009 | E2E | sim | 新写 | PollRepresentationJourneyTests::test_owner_and_representative_can_respond | 代表应答 201（**403，DEF-004**）→ 业主应答 201 | 代表席位 + 业主 |
| AC-001-*、AC-009-*、AC-031-* | TC-E2E-010 | E2E | sim | 新写 | AccountLifecycleJourneyTests::test_register_password_login_and_cancel | 注册 → 设密码 → 密码登录 → CANCEL 码注销 204 → /me 401 | 独立手机号 |
| AC-012-01、AC-015-*、AC-016-*、AC-066-*、AC-072-01 | TC-E2E-011 | E2E | sim | 新写 | test_rework_journeys.py::AccountMergeJourneyTests::test_wechat_user_binds_registered_phone_and_merges | 手机号注册户主 A；仅微信的 W 绑定 A 手机号 → 合并，答卷保留 A，新令牌身份=户主+同住人，旧令牌 401，审计可查 | fixture 现造 |
| AC-049-*、AC-050-*、AC-051-*、AC-061-*、AC-063-* | TC-E2E-012 | E2E | sim | 新写 | 同::AdvanceSettlementJourneyTests::test_advance_reimbursement_settlement_and_public_report | 预借 1000 → 报销 1200 → 核销 → 报表支出合计 1200，普通业主可见 | fixture 现造 |
| AC-058-*、AC-060-*、AC-061-*、AC-062-* | TC-E2E-013 | E2E | sim | 新写 | 同::IncomeManualEntryJourneyTests::test_manual_entry_submit_approve_report_then_void | 逐条录入 → 提交审批 → 生效计入报表 → 作废后重新生成，收入归零 | fixture 现造 |
| AC-006-01、AC-010-01、AC-013-01/02、AC-025-01、AC-028-01/04、AC-035-03 | TC-E2E-014 | E2E | sim | 新写 | test_gap_journeys.py::AccountIdentityLifecycleJourneyTests::test_register_certify_change_phone_cancel_reregister_and_recertify | 注册 → 游客 → 认证户主 → 换号（身份保留，旧号不可登录，新号同账号）→ 注销 → 同号再注册为全新游客 → 清册未改时认证 422 → 管理员改清册为新号 → 认证 201 HEAD | 独立手机号 + 清册单元 + 管理员 |
| AC-042-01/05、AC-068-01/02/04、AC-071-01 | TC-E2E-015 | E2E | sim | 新写 | 同::RepresentativeInFlightJourneyTests::test_grant_representatives_vote_then_seat_revoked_in_flight | 管理员赋予 2 名代表 → 主任发起代表投票与决议 → R1 作答 → 撤销 R2 后作答 403 → 撤销主任后决议仍 PENDING 且审批人可通过；participant_count 仍为 2 | 主任 + 审批人 + 2 代表 |
| AC-011-*、AC-073-01/02 | TC-E2E-016 | E2E | sim | 新写 | 同::AdminPasswordResetJourneyTests::test_admin_creates_admin_then_resets_password | 管理员 A 建 B → B 登录 → 普通用户重置 403 → A 重置 → B 旧令牌 401、旧密码 400、新密码 200 | 两名管理员 + 普通用户 |

另有冒烟层 `backend/tests/smoke/test_flows_smoke.py` 6 个既有用例（现有，回归用，不单独溯源），计入 E2E 层报告。

## GR-D-006-F01：11 个故事逐 AC 映射（0.5.0）

> 步骤：先 `git grep` 查 `backend/tests`、`frontend/tests`、`miniprogram/tests` 是否已覆盖；已覆盖的补映射行（标"现有"），缺口补写新用例（标"新写"）并执行。结果列为本次（2026-11-08 23:24 ~ 23:25）实测。

| US | AC | 用例（现有 / 新写） | 位置 | 预期 | 结果 |
|---|---|---|---|---|---|
| US-006 | AC-006-01 | TC-INT-101（新写）；TC-INT-005（现有）；TC-WEB-031（新写） | test_gap_must_have.py::WebPhoneLoginTests::test_code_login_returns_token_for_registered_phone；login.spec.js | 有效验证码 → 200，令牌访问 /me 为同一用户；Web 页发码与提交字段正确 | PASS |
| US-006 | AC-006-02 | TC-INT-102（新写）；TC-INT-007（现有）；TC-WEB-032 | 同类::test_password_login_by_phone_identifier | 手机号 + 正确密码 → 200 | PASS |
| US-006 | AC-006-03 | TC-INT-103；TC-WEB-033 | 同类::test_password_login_failure_message_is_uniform | 未设密码 / 未注册 / 密码错误 三种情形 code=LOGIN_FAILED、message=统一文案，且三者完全相同 | PASS |
| US-006 | AC-006-04 | TC-INT-104（错码 400 CODE_INVALID）、105（过期 CODE_EXPIRED）、**106（同一验证码输错 5 次作废）**、107（密码 5 次错锁定 15 分钟 retry_after=900）；现有 TC-INT-003/006、TC-UNIT-012~014；TC-WEB-033 | 同类 | 错码/过期被拒；5 次错后该码作废，再用正确码不得换取令牌；密码锁定 900 秒 | 104、105、107 PASS；106 PASS（DEF-006 已 CLOSED）。未直接执行：“同一手机号 30 分钟内累计输错 10 次锁定”（仅 TC-UNIT-013 覆盖通用限流机制） |
| US-010 | AC-010-01 | TC-INT-108（新写）；TC-E2E-014、TC-E2E-011 | 同文件::SingleAccountAcrossEntriesTests::test_web_and_miniprogram_phone_logins_reach_same_account_and_identity | Web 验证码 / 小程序（remember_me）验证码 / 密码登录 → 同一 user id，/me 均含“户主” | PASS |
| US-010 | AC-010-02 | TC-INT-109（新写，FakeWeChatClient） | 同类::test_wechat_bind_phone_then_wechat_and_phone_logins_same_account | 微信新账号绑定空闲手机号 → 再微信登录 is_new=false 同 id；手机号登录同 id | PASS |
| US-010 | AC-010-03 | TC-INT-110（新写）；TC-INT-002（现有） | 同类::test_second_account_for_same_phone_rejected | 已有手机号取注册码 409；微信账号绑定该号 → 合并，ACTIVE 用户数不增加 | PASS |
| US-013 | AC-013-01 | TC-INT-114；TC-E2E-014 | 同文件::ReRegisterAfterCancelTests::test_reregister_creates_fresh_guest_account | 新 user id；labels=["游客"]；昵称为空；无 Membership；旧账号 CANCELLED 且手机号已释放；旧令牌 401 | PASS |
| US-013 | AC-013-02 | TC-INT-115；TC-E2E-014 | 同类::test_reregister_owner_must_certify_again | 再注册后无有效成员关系；重新认证 201 role=HEAD | PASS |
| US-013 | AC-013-03 | TC-INT-116；TC-INT-002（现有） | 同类::test_register_with_active_phone_rejected | 409 PHONE_ALREADY_REGISTERED | PASS |
| US-025 | AC-025-01 | TC-INT-001（现有）；TC-INT-117；TC-E2E-001（现有） | 同文件::GuestTests::test_guest_can_apply_for_certification_and_resident_binding | /me is_guest=true，labels=["游客"] | PASS |
| US-025 | AC-025-02 | TC-INT-117；TC-E2E-001/002（现有） | 同类 | 游客可提交同住人申请 201 与清册认证 201 | PASS |
| US-025 | AC-025-03 | TC-INT-118；TC-INT-027（现有） | 同类::test_guest_cannot_do_owner_only_actions | 游客审批同住人申请、移除同住人 → 403；产权业主读待审列表 200 | PASS |
| US-028 | AC-028-01 | TC-INT-119；TC-E2E-014 | 同文件::ChangePhoneTests::test_change_to_free_phone_keeps_all_identities | 换到空闲号：merged=false，手机号更新，户主身份保留 | PASS |
| US-028 | AC-028-02 | TC-INT-120 | 同类::test_change_with_wrong_new_code_changes_nothing | 新号错码 → 400/429，原手机号与身份不变 | PASS |
| US-028 | AC-028-03 | TC-INT-089（现有） | test_rework_cr011_024.py::AccountMergeTests::test_change_phone_merges_into_new_phone_account | 新号属他人账号 → 合并，以新号账号为主 | PASS |
| US-028 | AC-028-04 | TC-INT-121；TC-E2E-014 | 同类::test_old_phone_cannot_login_after_change | 旧号登录 404 PHONE_NOT_REGISTERED，库中无该号用户；新号登录同一账号 | PASS |
| US-035 | AC-035-01 | TC-INT-122 | 同文件::RegistryPhoneChangeAfterCertificationTests::test_modify_registry_phone_keeps_owner | 清册号改动后成员关系仍有效，/me 含“户主” | PASS |
| US-035 | AC-035-02 | TC-INT-123 | 同类::test_delete_registry_phone_keeps_head | 清册号全部删除后仍是 HEAD | PASS |
| US-035 | AC-035-03 | TC-INT-124；TC-E2E-014 | 同类::test_certification_after_change_compares_new_registry | 原号码认证 422 PHONE_NOT_IN_REGISTRY 且 appeal_available；新号码认证 201 | PASS |
| US-035 | AC-035-04 | TC-INT-125 | 同类::test_non_admin_cannot_modify_registry_phones | 普通用户 / 委员 403；未登录 401（已收紧）；清册不变 | PASS |
| US-042 | AC-042-01 | TC-INT-126；TC-E2E-015；TC-E2E-009、TC-INT-030（现有） | 同文件::RepresentativeGrantTests::test_grant_to_owner_succeeds_and_user_becomes_participant | 201；/me 含“业主代表”；之后发起的代表投票参与者含该用户 | PASS |
| US-042 | AC-042-02 | TC-INT-127 | 同类::test_grant_to_resident_or_guest_rejected | 同住人 / 游客 → 422 NOT_AN_OWNER | PASS |
| US-042 | AC-042-03 | TC-INT-128；TC-INT-033（现有，副主任上限） | 同类::test_grant_over_cap_rejected | cap_rep=1 时第二人 409 CAP_REACHED | PASS |
| US-042 | AC-042-04 | TC-INT-129 | 同类::test_grant_to_committee_member_rejected | 委员再被赋予 → 409 ALREADY_SEATED，席位数不变 | PASS |
| US-042 | AC-042-05 | TC-INT-130；TC-E2E-015 | 同类::test_non_admin_cannot_grant | 普通业主 / 主任 403；未登录 401（已收紧）；无席位产生 | PASS |
| US-042 | AC-042-06 | TC-INT-126 | 同类 | 审计 SEAT_GRANTED 增加 1 条 | PASS |
| US-068 | AC-068-01 | TC-INT-131；TC-E2E-015 | 同文件::InFlightIdentityInvalidationTests::test_initiator_seat_revoked_resolution_stays_pending_and_flow_continues | 撤销发起人席位后决议仍 PENDING，审批人仍可通过 → APPROVED | PASS |
| US-068 | AC-068-02 | TC-INT-132 | 同类::test_approver_seat_revoked_cannot_approve_and_claim_stays_pending | 审批人席位撤销后审批 403；实例与报销单仍 PENDING，审批人名单不变 | PASS |
| US-068 | AC-068-03 | TC-INT-133 | 同类::test_withdraw_and_resubmit_with_valid_flow_after_approvers_invalid | 撤回后以新流程重提 → PENDING、revision=2 | PASS |
| US-068 | AC-068-04 | TC-INT-134；TC-E2E-015 | 同类::test_expired_representative_cannot_respond_but_earlier_answer_and_denominator_kept | 任期到期代表作答 403；R1 答卷保持；participant_count 仍为 2，R2 仍在参与人名单 | PASS |
| US-068 | AC-068-05 | TC-INT-135 | 同类::test_public_resolution_still_shows_initiator_label_after_seat_revoked | 已公开决议 initiator.labels 仍含“主任” | PASS |
| US-068 | AC-068-06 | TC-INT-136；TC-INT-044（现有，非委员投票 403） | 同类::test_invalidated_user_cannot_use_privileged_actions | 失效者发起决议、发起投票、审批均 403 | PASS |
| US-068 | AC-068-07 | TC-INT-137 | 同类::test_invalidated_initiator_can_withdraw_own_but_others_cannot | 其他委员/管理员撤回被拒，状态仍 PENDING；发起人撤回 → WITHDRAWN | PASS |
| US-070 | AC-070-01 | TC-INT-111（is_new=true）；TC-MP-027（现有，is_new → 设置页）；TC-MP-028、029（新写，保存/失败/稍后）；**微信头像昵称填写组件：NOT_TESTABLE（TC-E2E-NT-005，MV-007）** | test_gap_must_have.py::SingleAccountAcrossEntriesTests；miniprogram/tests/pages.spec.js | 首登 is_new=true；设置页保存 PATCH /me/profile；资料页显示头像昵称属真机验证（MV-007） | 可测部分 PASS；组件部分 NOT_TESTABLE |
| US-070 | AC-070-02 | TC-INT-111 | 同类::test_first_wechat_login_is_new_then_not_new_and_profile_kept | 保存昵称后再次微信登录 is_new=false，昵称保持 | PASS |
| US-070 | AC-070-03 | TC-INT-112；TC-MP-026（现有）、TC-MP-030 | 同类::test_phone_login_is_never_new | 手机号登录 is_new=false，客户端进首页不进设置页 | PASS |
| US-070 | AC-070-04 | TC-INT-113 | 同类::test_web_scan_first_login_takes_wechat_nickname_without_setup | Web 扫码首登昵称=微信昵称（fake） | PASS |
| US-071 | AC-071-01 | TC-INT-138；TC-E2E-015 | 同文件::MultiApproverTests::test_any_one_of_two_approvers_passes | P1 同意 → APPROVED | PASS |
| US-071 | AC-071-02 | TC-INT-139 | 同类::test_second_approver_after_decision_rejected_state_unchanged | P2 再通过/拒绝 → 409 ALREADY_DECIDED，状态 APPROVED、金额 200.00 不变 | PASS |
| US-071 | AC-071-03 | TC-INT-140；TC-INT-049（现有） | 同类::test_only_self_in_flow_rejects_claim_advance_and_income | 报销 / 预借 422 NO_ELIGIBLE_APPROVER，无 PENDING 申请；收入表提交 409/422 且不进 PENDING | PASS |
| US-071 | AC-071-04 | TC-INT-141 | 同类::test_submitter_with_another_approver_cannot_self_approve | 提交 201 PENDING；M 自批 403 SELF_APPROVAL_FORBIDDEN；P 批准 APPROVED | PASS |
| US-071 | AC-071-05 | TC-INT-142 | 同类::test_chair_designated_self_may_approve_resolution | 主任自指定可审批，APPROVED | PASS |
| US-071 | AC-071-06 | TC-INT-143；TC-INT-040（现有） | 同类::test_chair_not_designated_cannot_approve_resolution | 主任非指定负责人 → 403 FORBIDDEN，决议仍 PENDING | PASS |
| US-073 | AC-073-01 | TC-INT-144；TC-E2E-016 | 同文件::AdminPasswordResetTests::test_admin_resets_other_admin_password | 重置 204；旧密码 400；新密码 200；B 旧令牌 401；审计 ADMIN_PASSWORD_RESET | PASS |
| US-073 | AC-073-02 | TC-INT-145；TC-E2E-016 | 同类::test_member_cannot_reset_admin_password | 普通用户 / 业主 / 主任 403；被重置者原密码仍可登录 | PASS |
| US-073 | AC-073-03 | TC-INT-146 | 同类::test_anonymous_cannot_reset_and_no_self_service_entry | 未登录 401（OBS-001 已修复）；/admin/auth/register、forgot-password、reset-password 路径 404/405 | PASS |

观察 OBS-001：**已修复**（GR-C-007，`IsAdmin` 匿名 401、已登录普通会员 403）。TC-INT-125/130/146 的匿名断言已收紧为只接受 401，全部 PASS；TC-INT-106（DEF-006）PASS，DEF-006 CLOSED。

## US → 用例总表（69 个 Must Have，0.5.0）

> 生成方法：解析本文件各表中 AC / US 列，按 AC 前缀 `AC-NNN-*`、`US-NNN`、`US-AAA~BBB`、`US-A/B/C` 展开到故事，再用 `git grep` 人工核对 11 个补测故事。单元 / 集成列为后端 Django 用例，vitest 列为 Web / 小程序用例，E2E 列为 `tests/e2e` 多步旅程（冒烟与不可测不计入）。`—` 表示该层无用例。
> 汇总：**69 / 69 个 Must Have 故事至少有 1 个真实执行的用例**（无 NOT_TESTABLE 单独支撑的故事）；其中 45 个有 E2E 旅程（critical path 覆盖率 45 / 69 = 65.22%），其余 24 个没有 E2E 旅程：US-002、003、004、005、007、008、014、017、018、019、020、022、027、036、037、038、039、040、041、043、048、067、069、070，均由单元 / 集成 / vitest 用例覆盖，属已知缺口。

| US | 标题 | 单元 | 集成（后端） | vitest | E2E |
|---|---|---|---|---|---|
| US-001 | Web 端手机号 + 验证码注册 | — | INT-001~004,081 | — | E2E-001,010 |
| US-002 | Web 端微信扫码登录 | — | INT-113,147~149 | — | — |
| US-003 | 小程序端手机号登录 | — | INT-005~006,081 | MP-001~011,014~027 | — |
| US-004 | 小程序端微信一键登录 | — | INT-009,109,111 | — | — |
| US-005 | Web 端账号 + 密码登录 | — | INT-007 | — | — |
| US-006 | Web 端手机号登录（验证码或密码） | — | INT-003,005~007,101~107 | WEB-031~033 | E2E-014 |
| US-007 | Web 端邮箱验证码登录与邮箱验证 | — | INT-013 | — | — |
| US-008 | Windows 微信桌面版一键授权登录 | — | INT-009 | — | — |
| US-009 | 登录后设置密码 | UNIT-006~009 | INT-007 | — | E2E-010 |
| US-010 | 手机号为账号唯一标识（三入口同一账号） | — | INT-002,085,088,108~110 | — | E2E-011,014 |
| US-011 | 管理员独立登录管理后台 | — | INT-015~017 | — | E2E-016 |
| US-012 | 微信绑定的手机号已属他人账号时合并 | — | INT-080,085,087~088 | MP-001~011,014~027；WEB-028~030 | E2E-011 |
| US-013 | 账号注销后同一手机号可作为全新账号再注册 | — | INT-002,014,114~116 | — | E2E-010,014 |
| US-014 | 已认证用户更换手机号遇他人账号时合并 | — | INT-080,089 | MP-001~011,014~027；WEB-028~030 | — |
| US-015 | 账号合并时的资料与凭据规则 | — | — | — | E2E-011 |
| US-016 | 账号合并时的身份冲突规则 | — | — | — | E2E-011 |
| US-017 | 选填邮箱重复时先验证者获得，修改后需重新验证 | — | INT-013 | WEB-028~030 | — |
| US-018 | 保存业主清册 | — | INT-020 | — | — |
| US-019 | 管理员批量导入与单条修改清册 | — | INT-019 | — | — |
| US-020 | 逐级选择专有部分 | — | INT-018 | — | — |
| US-021 | 手机号与清册一致时直接认证为产权业主 | — | INT-020,023 | — | E2E-001 |
| US-022 | 仅清册一致或申诉通过方可成为产权业主 | — | INT-021~022 | — | — |
| US-023 | 第一位认证的产权业主为户主 | — | INT-020,022 | — | E2E-001 |
| US-024 | 申请成为同住人与产权业主审批 | — | INT-026~027 | — | E2E-002 |
| US-025 | 游客身份与可执行操作 | — | INT-001,027,117~118 | — | E2E-001~002,014 |
| US-026 | 产权认证申诉与管理员审核 | — | INT-021,024~025,100 | — | E2E-003 |
| US-027 | 户主注销时由认证时间最早的产权业主接任 | UNIT-032~033 | INT-029 | — | — |
| US-028 | 已认证用户更换手机号 | — | INT-080,089,119~121 | — | E2E-014 |
| US-029 | 同住人申请被拒、产权业主移除、同住人退出 | — | INT-026,028 | — | E2E-002 |
| US-035 | 清册手机号被修改或删除后已认证身份保留 | — | INT-020~021,122~125 | — | E2E-014 |
| US-036 | 管理员手动撤销产权业主认证 | — | INT-029,074 | WEB-001~005 | — |
| US-030 | 修改个人资料 | — | INT-010~012 | — | E2E-001 |
| US-031 | 注销账号 | — | INT-014 | — | E2E-010 |
| US-037 | 管理员赋予业委会身份 | — | INT-030 | — | — |
| US-038 | 管理员撤销或变更业委会身份与业主代表身份 | — | INT-032 | — | — |
| US-039 | 业委会/业主代表身份的唯一性、不可兼任与自动失效 | UNIT-031 | — | — | — |
| US-040 | 管理员配置业委会与业主代表的人数上限与任期 | UNIT-010~011 | INT-031,033,075 | — | — |
| US-041 | 身份在个人信息中只读显示 | — | INT-074 | WEB-001~005,017~018；MP-012~027 | — |
| US-042 | 管理员赋予业主代表身份 | — | INT-030~031,033,126~130 | — | E2E-009,015 |
| US-043 | 管理员配置审批流程 | — | INT-034~036 | — | — |
| US-044 | 主任/副主任发起业委会决议 | — | INT-039 | — | E2E-004 |
| US-045 | 决议审批方式一——指定负责人审批 | — | INT-034,037,040~041 | MP-014~027 | E2E-004 |
| US-046 | 决议审批方式二——半数人员同意通过 | UNIT-027~028 | INT-035,043~046 | — | E2E-005 |
| US-047 | 审批结束的决议对所有已登录用户公开 | — | INT-037~038 | — | E2E-004~005 |
| US-048 | 撤回、被拒后重新提交与通过后不可修改 | — | INT-039,042,050 | — | — |
| US-049 | 业委会成员发起报销或备用金申请 | UNIT-001~003,015~018 | INT-047,050,053~054,076~077 | WEB-006~016,019~024；MP-001~011,014~027 | E2E-006,012 |
| US-050 | 审批报销/备用金并自动计入支出 | — | INT-048,076 | WEB-006~016,019~024；MP-014~027 | E2E-006,012 |
| US-051 | 备用金事后核销 | — | INT-051~052,076,090~094 | WEB-006~016,019~024；MP-001~011,014~027 | E2E-012 |
| US-052 | 主任/副主任发起业主代表投票 | — | INT-066~068,078 | WEB-006~016,025~027；MP-001~011,014~027 | E2E-008 |
| US-053 | 业主代表投票的结论判定 | — | INT-078 | WEB-006~016,025~027；MP-001~011,014~027 | E2E-008 |
| US-054 | 主任/副主任发起调查 | — | INT-070,078 | WEB-006~016,025~027；MP-001~011,014~027 | E2E-009 |
| US-055 | 一次投票/调查含多道题与可定制题型 | UNIT-023~025 | INT-069,078 | WEB-006~016,025~027；MP-001~011,014~027 | E2E-009 |
| US-056 | 参与者在手机上一键提交意见 | — | INT-068~070,078 | WEB-006~016,025~027；MP-001~011,014~027 | E2E-009 |
| US-057 | 投票/调查结果在截止后以汇总形式公开 | UNIT-026 | INT-072,078 | WEB-006~016,025~027；MP-001~011,014~027 | E2E-008 |
| US-058 | 业委会成员单条录入收入表 | — | INT-055~056,079,096~097 | WEB-006~016 | E2E-006,013 |
| US-059 | 业委会成员批量导入收入表 | UNIT-019~022,034~036 | INT-055,057~058,073,079,098~099 | WEB-006~016 | E2E-006 |
| US-060 | 收入表审批生效与作废 | — | INT-059~060 | — | E2E-006,013 |
| US-061 | 系统自动生成季度/年度财务报表 | UNIT-001~002,037~039 | INT-062,065,095 | — | E2E-006,012~013 |
| US-062 | 业委会成员手动重新生成报表 | — | INT-064 | — | E2E-013 |
| US-063 | 所有已登录用户可查看财务报表 | — | INT-061,063 | — | E2E-007,012 |
| US-065 | 半数同意决议在表决截止时间结束时判定通过/未通过 | UNIT-027,029~030 | INT-043,045 | — | E2E-005 |
| US-066 | 账号合并时业委会/业主代表身份保留较高者 | — | — | — | E2E-011 |
| US-067 | 财务类事项申请人不得审批自己的申请 | — | INT-049 | — | — |
| US-068 | 身份失效时在途事项保持不变 | — | INT-029,044,131~137 | — | E2E-015 |
| US-069 | 登录会话有效期与"记住我" | — | INT-008 | — | — |
| US-070 | 小程序首次微信登录后设置头像昵称 | — | INT-081,111~113 | MP-027~030 | — |
| US-071 | 审批中的多审批人规则与自批边界 | — | INT-034,040,048~049,138~143 | — | E2E-015 |
| US-072 | 账号合并时处理进行中的投票、调查与待办 | — | INT-085~086,089 | — | E2E-011 |
| US-073 | 管理员重置其他管理员的密码 | — | INT-015,017,144~146 | — | E2E-016 |


## 测试数据需求

- 唯一手机号：`tests/support.py::next_phone()` 生成 `139xxxxxxxx`；账号 `next_account_no()` 生成 `8xxxxxxxxx`。
- 清册单元：`make_unit()` 生成唯一 `specific_part`，避免 unique 冲突；可以 `phones` 指定关联手机号。
- 角色数据：`make_owner()` 创建 HEAD 成员；`make_resident()` 创建 RESIDENT；`make_seat()` 创建 ACTIVE 席位。
- 审批流程：`make_flow()` 直接创建 `ApprovalFlow` + `FlowApprover`，scope ∈ RESOLUTION / EXPENSE / INCOME。
- 验证码：短信码从 `FakeSmsGateway.shared().sent` 读取；邮件码从 `django.core.mail.outbox` 读取；同一手机号 60 秒重发限制在测试中通过删除 `RateLimit` 行规避（仅测试数据清理）。
- 附件：`SimpleUploadedFile` 伪造 PNG 字节流（`\x89PNG\r\n\x1a\n` + 填充），不依赖真实图片。
- `[DATA_REQUIRED: 微信小程序登录 code / openid]`：无真实凭据，相关 AC 不可测（见下表）。
- `[DATA_REQUIRED: xlsx 收入表样例]`：本机缺 `openpyxl`，xlsx 导入路径未执行。
- 微信替身：`FakeWeChatClient`（`apps/integrations/fakes.py`）经 `set_wechat_client()` 注入，用例在 `addCleanup` 中复位为 None，避免跨用例污染；Web 扫码回调用 `create_wechat_state()` 生成 state。
- vitest 数据：全部为内联固定对象（`frontend/tests/helpers.js`、`http.mock.js`、`miniprogram/tests/helpers.js`），不写持久存储。

## 不可测项

| AC | 原因 |
|---|---|
| AC-002-*、AC-004-*、AC-008-*（微信扫码 / 小程序一键登录真实链路） | 无微信 SDK 与真实凭据；画像 P11-3 只允许 fake。登记为 TC-E2E-NT-001，见人工验证清单 MV-001。0.5.0：经 FakeWeChatClient 可测的部分（回调、ticket 兑换、再次扫码同账号、state 失效、PHONE_REQUIRED、首次登录 is_new）已由 TC-INT-109/111/113/147~149 真实执行。 |
| AC-070-01 中“通过微信头像昵称填写能力（`open-type=chooseAvatar`、`type=nickname`）选择头像”（US-070） | 该组件仅在微信真机/开发者工具提供，vitest 只能调用页面的 `onChooseAvatar` 回调（TC-MP-028）。登记为 TC-E2E-NT-005，MV-007。 |
| 小程序 uni-app 运行时（页面渲染、tabBar 跳转、`uni.chooseImage`/`uploadFile` 真机行为） | vitest 只用桩，无 HBuilderX/uni 构建环境；登记 TC-E2E-NT-002，MV-004。 |
| 微信开发者工具/真机下小程序登录与手机号授权 | 需真实微信环境；TC-E2E-NT-003，MV-005。 |
| 小程序端到端业务流程（登录 → 报销/投票 → 绑定手机号）真机走查 | 同上；TC-E2E-NT-004，MV-006。 |
| AC-019-*、AC-059-*（xlsx 导入） | 本机 venv 未装 `openpyxl`（画像 P4 不自行安装）；已测 CSV 路径；MV-002。 |
| 浏览器真实渲染 / 视觉（Web） | 无浏览器 E2E 框架；vitest + jsdom 仅覆盖挂载与交互；MV-003。 |
| 短信、邮件、微信真实发送/回调 | 画像 P11-3 禁止真实调用。 |
