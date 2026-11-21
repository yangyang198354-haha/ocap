<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-21T11:48:10+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_hierarchy/architecture/module_design.md</file>
    <file>project_workspace/ocap_profile_hierarchy/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：个人主页信息层级与实名认证徽章

## 实现概览

2 个生产模块（MOD-164 Web、MOD-165 小程序）+ 2 个测试模块（MOD-166、MOD-167）。按依赖拓扑：MOD-164 与 MOD-165 互不依赖，可并行；测试模块依赖对应生产模块。无后端改动、无迁移、无新依赖。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-164 | `frontend/src/portal/UserProfile.vue` | 修改 | IFC-378 | L | 重排昵称 → 实名+徽章 → 身份；新增 `.real-name`/`.verified-badge`/`.identity-tag` 样式 | DONE |
| 2 | MOD-165 | `miniprogram/pages/me/index.vue` | 修改 | IFC-377 | L | 调用 `api.profile()` 获取实名；重排展示；失败降级 | DONE |
| 3 | MOD-166 | `frontend/tests/profile_ux.spec.js` | 修改 | MOD-164 | L | 新增 TC-UNIT-1509/1510 | DONE |
| 4 | MOD-167 | `miniprogram/tests/identity_display.spec.js` | 修改 | MOD-165 | L | 新增 TC-MP-504/505 | DONE |

## 需求追溯

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-273 | AC-273-01 | `frontend/src/portal/UserProfile.vue` `.profile-meta`（昵称 → `.real-name` → `.identity-tag`） | DONE | 顺序由模板顺序保证 |
| US-273 | AC-273-02 | 同上，`v-if="profile.real_name"` | DONE | 无实名时只渲染昵称与身份 |
| US-273 | AC-273-03 | 同上，`profile.nickname \|\| '未设置昵称'` | DONE | 占位仍在主标题位 |
| US-274 | AC-274-01 | `UserProfile.vue` `.real-name` 内 `.verified-badge` | DONE | 文案“✓ 已实名认证”，与实名同容器 |
| US-274 | AC-274-02 | `v-if="profile.real_name"` 同时控制实名与徽章 | DONE | 无实名时不渲染 |
| US-275 | AC-275-01 | `UserProfile.vue` `.real-name`（`var(--text)`、650）/ `.identity-tag`（muted info tag） | DONE | 颜色与字重均不同 |
| US-275 | AC-275-02 | 同上，`.identity-tag` 独立 class | DONE | 身份样式不继承主标题 |
| US-276 | AC-276-01 | `miniprogram/pages/me/index.vue` 主信息区 + `load()` 的 `api.profile()` | DONE | 顺序：昵称 → 实名 → 徽章 → 身份 |
| US-276 | AC-276-02 | `v-if="realName"` 控制实名与徽章 | DONE | 未开启实名时后端返回空 |
| US-276 | AC-276-03 | `load()` 中 `api.profile()` 独立 try/catch，失败置空 | DONE | 不弹提示，昵称与身份保留 |

## 迁移

无。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| 小程序身份标签内保留“身份：”前缀（如“身份：产权业主”） | IFC-380（原文案为 label） | 避免标签失去上下文，同时兼容既有 TC-MP-503 的“身份：产权业主”断言 | 仅文案，不影响顺序、样式与 AC |
| Web 认证徽章使用 `el-tag` 的 success 类型而非单独组件 | ADR-158 已选方案 A | 按设计执行，无偏差 | — |

## 开放问题

无。
