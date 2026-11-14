<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-14T17:40:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/architecture/module_design.md</file>
    <file>project_workspace/ocap_identity_display/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：用户端身份显示与认证房屋信息

## 实现概览

- 模块：3 个（MOD-101 后端聚合 → MOD-102 Web → MOD-103 小程序），按依赖拓扑顺序实现。
- 产品代码文件：6 个修改、0 个新建。
- 现有测试调整：仅调整断言旧口径（“户主/多标签”）的用例，最小改动。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-101 | `backend/apps/committee/services.py` | 修改 | — | L | `identity_labels` 返回单一最高身份：有效职务 > 产权业主 > 同住人 > 游客 | DONE |
| 2 | MOD-101 | `backend/apps/identity/services.py` | 修改 | 1 | M | `/me` 的 `units` 增加 role_label、unit_type、unit_type_label、area、area_display；按名称排序、按 unit_id 去重；`is_guest` 改按 labels | DONE |
| 3 | MOD-102 | `frontend/src/portal/Home.vue` | 修改 | 2 | M | 身份三态（加载中/失败重试/成功）；认证房屋数量 + 明细列表 + 空状态 | DONE |
| 4 | MOD-102 | `frontend/src/shared/style.css` | 修改 | 3 | L | 新增 `.home-units` / `.home-unit` 样式 | DONE |
| 5 | MOD-103 | `miniprogram/pages/index/index.vue` | 修改 | 2 | M | 首页身份加载态；新增认证房屋明细卡片与空状态 | DONE |
| 6 | MOD-103 | `miniprogram/pages/me/index.vue` | 修改 | 5 | L | 身份行加载态 | DONE |
| 7 | 回归 | `backend/tests/**`、`frontend/tests/**`、`miniprogram/tests/**` | 修改 | 1-6 | M | 仅更新断言旧口径的用例与夹具 | DONE |

## 需求追溯

| US | AC | 实现位置 | 状态 |
|---|---|---|---|
| US-145 | AC-145-01~06、09 | `committee/services.py:identity_labels`；`identity/services.py:me` | DONE |
| US-145 | AC-145-07、08 | `committee/services.py:identity_labels`（职务优先） | DONE |
| US-145 | AC-145-10 | `committee/services.py:identity_labels`（单元素列表） | DONE |
| US-146 | AC-146-01~05、09 | `identity/services.py:me`（units 字段、排序、去重） | DONE |
| US-146 | AC-146-06~08 | `Home.vue`、`miniprogram/pages/index/index.vue` | DONE |
| US-147 | AC-147-01~03 | `Home.vue` 三态；后端 ended_at 过滤 | DONE |
| US-148 | AC-148-01~04 | `miniprogram/pages/index/index.vue`、`pages/me/index.vue` | DONE |

## 迁移

无。

## 架构偏差

无。

## 开放问题

- [ASSUMPTION] 历史 `initiator_labels` 等已落库文案不回填（架构设计已声明超出范围）。
