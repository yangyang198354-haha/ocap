<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-15T11:51:18+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_identity_display/requirements/user_stories.md</file>
    <file>project_workspace/ocap_identity_display/architecture/module_design.md</file>
    <file>project_workspace/ocap_product_review/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_product_review/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_product_review/architecture/module_design.md</file>
    <file>project_workspace/ocap_product_review/development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 合并解决记录（本地 8ba53a8 ocap_product_review ⟵ origin/main 35ce9f5 ocap_identity_display）

规则来源：用户 2026-11-15 答复 Q4=A。未执行 commit / merge --continue / stash / push / reset；仅编辑并 `git add`。

## 1. 逐文件解决

| 文件 | HEAD 侧要点 | origin 侧要点 | 采用方式 | 依据 |
|---|---|---|---|---|
| backend/apps/committee/services.py `identity_labels` | `[职务, 最高房屋身份]` 并列，按 ROLE_RANK 取最高（ADR-080/IFC-274） | 单一最高身份：职务 > 产权业主（HEAD/OWNER）> 同住人 > 游客 | 整段采用 origin（`active_seat` 本就带任期校验，保留 ADR-082 口径）；不再导入 ROLE_RANK | 规则1、REQ-FUNC-136、C-34、IFC-247 |
| backend/apps/identity/services.py `me` | 内联 units；`active_seat`（ADR-082）；`summary=identity_view(...)` | `_units()`（unit_type/area 等明细、去重排序）；`active_seat` | 并集：units 用 origin 的 `_units`；保留 `active_seat`、memberships/seats 查询与 `summary` | 规则2、3、IFC-262、IFC-248 |
| backend/tests/integration/test_registry_import_xlsx_defects.py | 示例行 4→6 的 specific_part 集合断言 | 去掉该断言，期望 6 行/4 个新增 | 采用 origin 的 6 行修复，保留集合断言（6 行示例下仍成立，已实跑通过，期望集合未变） | 规则5 |
| backend/tests/integration/test_specific_part_display_consistency.py | unit_row 键集合 4 键 | 8 键（含 unit_type 等） | 取并集，即 8 键 | 规则5 |
| frontend/src/portal/Home.vue | `identitySummary.label`、pendingReview 入口 | identityText（加载中/失败）、meError、retryMe、unitRows | 并集：`identityText` 在有数据时取 `auth.identitySummary.label`，加载中/失败/重试沿用 origin；保留 pendingReview | 规则1、2、3、4 |
| miniprogram/pages/index/index.vue | `identitySummary.label`、pendingReview | identityText、认证房屋卡（unit_type/area） | 并集：身份取 `identitySummary.label`；新增 `meError`（失败显示"加载失败，请重试"并可点重试），认证房屋卡沿用 origin | 规则1、2、3 |
| miniprogram/pages/me/index.vue | "汇总身份"+ housingUnits 列表 | "身份：" labels.join | 并集：文案 `身份：{{ identitySummary.label }}`（保持与 origin 测试一致），保留 housingUnits 列表 | 规则2、4 |
| miniprogram/store/auth.js | `isCommittee`、`identitySummary` getter | state 加 `loading` | 并集 | 规则2、3 |

## 2. 规则4：summary 与 identity_view / ROLE_RANK 调整（有冲突，已按规则1调整）

product_review 的 `identity_view`（`backend/apps/accounts/directory.py`）输出 `HEAD → "户主"`，与规则1（用户端不出现"户主"）冲突，且 `/me`、`/me/housing`、管理端目录三处共用它。改动：

- `identity_view`：HEAD/OWNER 一律 `identity_code="OWNER"`、`identity_label="产权业主"`；RESIDENT 不变；新增 `ROLE_LABELS`（用户可见文案）。`ROLE_RANK` 仍保留，仅用于同级取优。
- `backend/apps/residency/housing.py`（`/me/housing`）：`units[].role_label` 由 `get_role_display()`（"户主"）改为 `ROLE_LABELS`，使用户端房屋行也不出现"户主"。
- `frontend/src/stores/auth.js`、`miniprogram/store/auth.js` 的 `identitySummary` 在响应缺 `summary` 时回退到 `labels` 拼接（labels 恒为单元素），避免缺 summary 时误显示"游客"。
- 结果：同一用户在首页、"我的"、`/me/housing`、管理端目录显示同一文案（TC-INT-441 三处一致仍通过）。
- 影响：
  - ADR-080：决定段"labels 仍为 `[职务?, 最高房屋身份]`"与 IFC-274 的"`[职务?, 房屋身份?]`、同级取 certified_at 最早"被 origin 的 C-34 单一身份取代（`labels` 现恒为单元素）；写入报销 `applicant_labels`、决议 `initiator_labels`、收入 `creator_labels` 的新快照形态变为单一身份（旧记录不回填）。
  - IFC-262：`summary.code` 取值由 {职务码, HEAD, OWNER, RESIDENT, GUEST} 变为 {职务码, OWNER, RESIDENT, GUEST}；`units[].role_label` 取值变为 {产权业主, 同住人}；`labels` 变单元素；键集合不变。IFC-244（user_directory）的"户主"优先级同步失效，管理端目录显示"产权业主"。
  - ADR-082 不变。
  - 内部角色 HEAD/OWNER（业务规则）不变，管理端"户主"筛选项（AdminMemberships.vue）属管理端，未改。
  - 建议 GROUP_B 在后续迭代更新 ADR-080、IFC-262/274、IFC-244（本次不得改 APPROVED 文档）。

## 3. 因合并语义调整的测试断言

| 文件:行 | 原断言 | 新断言 | 理由 |
|---|---|---|---|
| backend/tests/unit/test_product_review_rules.py:112,118,123 | `identity_code == "HEAD"`（2 处）；文档串"职务>户主>…" | `== "OWNER"`；文档串更新 | 规则1/4 |
| backend/tests/integration/test_product_review_api.py:49,81 | summary `{"code":"HEAD","label":"户主"}` | `{"code":"OWNER","label":"产权业主"}` | 规则1/4 |
| 同上 :52 | 房屋行 role_label "户主" | "产权业主" | 规则1 |
| 同上 :82,83 | labels `["户主"]`；role_label 集合含"户主" | `["产权业主"]`；含"产权业主" | 规则1 |
| 同上 :93 | summary.code "HEAD" | "OWNER" | 规则4 |
| 同上 :354 | `identity_labels == ["副主任","产权业主"]` | `["副主任"]` | 规则1：职务直接显示，不并列 |
| backend/tests/integration/test_product_review_ac.py:304,321,334（及 :330 文档串） | 房屋行 "户主" | "产权业主" | 规则1 |
| 同上 :326,328（summary 与管理端目录标签） | `{"code":"HEAD","label":"户主"}`、`"户主"` | OWNER/产权业主 | 规则1/4 |
| 同上 :376 | 候选 identity_label "户主" | "产权业主" | 规则1/4 |
| backend/tests/integration/test_admin_user_directory.py:89,108 | 目录 identity_label "户主" | "产权业主" | 规则4（管理端目录与用户端同口径） |
| backend/tests/integration/test_frontend_contract.py:142 | units[0].role_label "户主" | "产权业主" | 规则1 |
| backend/tests/e2e/test_product_review_journeys.py:98 | 三处身份集合 `{"户主"}` | `{"产权业主"}` | 规则1/4 |

前端、小程序测试无需调整（vitest 全绿）。

## 4. 未解决（与合并规则无关，已停止，未改动）

后端全量 723 条中 2 条失败，为文档编号冲突，非合并规则所致：
- `tests.integration.test_requirements_numbering.test_tc_int_478_ac_176_01_no_duplicate_definitions`：`REQ-FUNC-136`（等）在 ocap_identity_display 与另一迭代的需求文档中重复定义。
- `...test_tc_int_480_ac_176_03_constraint_collisions_have_batch_prefix_notes`：C-34~38 在 ocap_identity_display 与 ocap_admin_polish / ocap_user_directory 之间出现冲突，期望集合不含该组合。
- 原因：两条独立线（ocap_identity_display 使用 REQ-FUNC-136~141、C-34~38，与 ocap_user_directory 的编号相撞）。修复需改 APPROVED 需求文档编号或更新该测试的白名单/批次前缀说明，超出本次授权，请 PM 决定（回流 GROUP_A 重编号，或授权更新 TC-INT-478/480）。

## 5. 自验证

```
(cd backend && $PY -m compileall -q . && $PY manage.py check --settings=config.test_settings)
  System check identified no issues (0 silenced).
(cd backend && $PY manage.py test --settings=config.test_settings)
  Ran 723 tests in 62.495s
  FAILED (failures=2)   # 仅 TC-INT-478 / TC-INT-480（见 §4）
(cd frontend && npx vitest run --passWithNoTests)
  Test Files  24 passed (24) / Tests  248 passed (248)
(cd frontend && npm run build -- --base=/ocap/)
  ✓ built in 41.23s
(cd miniprogram && npx vitest run --passWithNoTests)
  Test Files  14 passed (14) / Tests  97 passed (97)
git diff --name-only --diff-filter=U   -> 空
grep -rn '^<<<<<<<\|^>>>>>>>' backend frontend/src miniprogram   -> 无输出
```
test_tc_int_311 已通过（含在 723 条内，不在失败列表）。

## 6. 五维自评（简版）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 9/10 |

- Correctness：规则1~5全部落实；2 条编号测试未解决（非本次范围），故扣分。
- Maintainability：HEAD/OWNER 合并为 code=OWNER 属语义调整，须由 GROUP_B 更新 ADR-080/IFC-262/274/244 的文字（见 §2），否则文档与代码不一致。
- 无新增依赖、无迁移、无凭据。
