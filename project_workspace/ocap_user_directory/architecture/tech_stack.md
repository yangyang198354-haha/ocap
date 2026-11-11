<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-11T22:34:05.7369915+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>architecture/module_design.md</file><file>../ocap/architecture/tech_stack.md</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 技术栈（增量）

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 | Python | 画像 P1/P4：目标 Django 5.2.x，本机 3.14.6 [REPO] | 沿用 | 现有后端栈 | — | 本机 Django 6.0.6 与目标 5.2 有版本差异（画像 P4 已记录），本次不引入新语法 |
| Web 框架 | Django + DRF | Django 5.2（画像 P1）；本机 DRF 3.17.1（画像 P4） | 沿用 | 现有账号接口与分页体系 | REQ-FUNC-123 ~ 128 | 无新增风险 |
| 数据库 | MySQL（测试环境）/ SQLite（本地测试） | 画像 P1/P7 | 沿用 | 现有数据源；本次无迁移 | REQ-FUNC-124/125 | `icontains` 在 MySQL 不能用普通索引，用户量极大时搜索变慢 |
| 前端框架 | Vue 3 + Vite + Element Plus | 画像 P1 [REPO] | 沿用 | 现有后台页面技术栈 | REQ-FUNC-123 ~ 127 | 无新增风险 |
| 前端测试 | vitest | `frontend/package.json` [REPO] | 沿用 | 现有测试框架 | REQ-NFUNC-020 | 无 |
| 后端测试 | Django test runner | 画像 P4 [REPO] | 沿用 | 现有测试框架 | 全部 | 无 |
| 新增第三方依赖 | 无 | — | — | 目录聚合与时间格式化均可由现有标准库/框架完成 | — | — |

**依赖结论：无新增依赖，版本不变。**

## 技术风险

| 等级 | 风险 | 缓解措施 |
|---|---|---|
| Medium | 实名搜索使用 `icontains` 跨清册表，数据量增长后可能变慢 | 分页上限 100；搜索词截断 32 字符；后续如出现性能问题，再评估专用索引或搜索表（本次不做） |
| Low | 每页预取 membership/unit/owners/phones/seats，若遗漏预取会退化为 N+1 | GROUP_C 实现固定 `prefetch_related`；GROUP_D 增加查询数回归用例 |
| Low | 前端时间格式化依赖浏览器时区 | 后端返回 ISO8601，前端统一用共享函数格式化；测试覆盖空值与典型时区 |
