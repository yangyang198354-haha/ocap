<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T22:40:47.9999127+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file></input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 代码评审报告

## 摘要

- 本次改动：6 个文件（1 个新建、5 个修改），约 127 行新增。`git diff --stat`（仅本次范围）：
  - `backend/apps/accounts/directory.py`（新建，约 70 行）
  - `backend/apps/accounts/serializers.py` +14
  - `backend/apps/accounts/views.py` +20/-3
  - `frontend/src/admin/AdminUsers.vue` +18/-2
  - `frontend/src/shared/format.js` +5
  - `backend/tests/...` 未改动
- 五维平均分：8.9 / 10（MOD-062 8.8、MOD-063 9.0）。
- 问题统计：CRITICAL 0 / MAJOR 0 / MINOR 3（均 OPEN，已注明原因）。

## 文件 → MOD/IFC 映射

| 文件 | MOD | IFC |
|---|---|---|
| `backend/apps/accounts/directory.py` | MOD-062 | IFC-244、IFC-245、IFC-246 |
| `backend/apps/accounts/serializers.py` | MOD-062 | IFC-243（响应字段） |
| `backend/apps/accounts/views.py` | MOD-062 | IFC-243（预取、搜索） |
| `frontend/src/shared/format.js` | MOD-063 | IFC-243（时间展示） |
| `frontend/src/admin/AdminUsers.vue` | MOD-063 | IFC-243（四列展示） |

## 自验证结果

| 命令 | 工作目录 | 输出尾部 | 结论 |
|---|---|---|---|
| `python manage.py check --settings=config.test_settings` | `backend/` | `System check identified no issues (0 silenced).` | 通过 |
| `python manage.py test --settings=config.test_settings` | `backend/` | `Ran 520 tests in 10.122s` / `OK (skipped=9)` | 通过，零新增失败 |
| `npm run test -- --run` | `frontend/` | `Test Files 2 failed | 14 passed (16)`；`Tests 2 failed | 152 passed (154)` | 2 个失败为既有 Windows 环境问题（主题生成物 CRLF、`/tmp` 不存在），与本次改动无关 |
| `npm run build` | `frontend/` | `✓ built in 7.50s`（仅有既有 chunk 体积提示） | 通过 |
| 临时端到端自检（Django shell + APIClient，测试库） | `backend/` | `STATUS 200`；`identity_code=MEMBER`、`identity_label=委员`、`certified_units=1`、`real_names=['张三']`、`phone=138****0001`；按实名搜索命中、按手机号搜索命中、未命中 `count=0` | 通过 |

未验证项：无（前端构建与测试均已运行；既有 2 个失败按基线单列）。

## 按模块评审

### MOD-062 后端用户目录聚合

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-028 | MINOR | `backend/apps/accounts/serializers.py:to_representation` | 目录字段依赖视图的固定预取；若未来有其他调用方直接使用该序列化器，会退化为 N+1 | OPEN（当前仅 `AdminUserListView` 使用；已在实现计划与架构风险中记录） |
| CR-029 | MINOR | `backend/apps/accounts/directory.py:real_name_q` | 实名搜索使用 `icontains` 跨清册表，数据量很大时 MySQL 无法利用普通索引 | OPEN（分页上限 100、q 截断 32 字符；架构已登记为中风险，后续按需优化） |

实现要点核对：
- 最高身份：Seat 按 `POSITION_RANK`、Membership 按 `ROLE_RANK` 取最高；过期/非 ACTIVE 席位在预取与函数内双重过滤。
- 认证套数：有效 Membership 的 `unit_id` 去重计数。
- 实名：仅 HEAD/OWNER，同一清册记录手机号精确匹配，姓名去重保序。
- 实名搜索：`Exists` 子查询，同一 `unit__phones` 关联同时约束 `phone` 与 `owner.name`（满足 GR-B-001-F01）；不产生重复行，无需 `distinct()`。
- 权限沿用 `IsAdmin`，手机号沿用 `MaskedPhoneField`。

### MOD-063 Web 后台账号页展示

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-030 | MINOR | `frontend/src/shared/format.js:formatDateTime` | 采用字符串截取（依赖后端按 `Asia/Shanghai` 输出 ISO8601），不是浏览器时区换算；与需求 AC-134-01 的时区一致 | OPEN（实现计划已标 [ASSUMPTION]；如需多时区展示再统一改造） |

实现要点核对：
- 四列展示：身份、认证（已认证 N 套/未认证）、实名（顿号并列/—）、上次登录（YYYY-MM-DD HH:mm/从未登录）。
- 原有账号、手机号、昵称、状态列与分页组件未改；搜索占位追加“实名”。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无。

## 缺陷修复

无（首次实现）。

## 现有测试调整

无。既有测试全部通过；前端 2 个失败为改动前已存在的 Windows 环境问题，未修改测试。
