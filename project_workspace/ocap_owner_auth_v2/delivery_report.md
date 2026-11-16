<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-16T22:08:09+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
  <version>1.0.0</version>
  <input_files><file>phase_status.md</file><file>deployment/deployment_report.md</file><file>testing/e2e_test_report.md</file></input_files>
  <phase>PHASE_01,PHASE_02,PHASE_03,PHASE_04,PHASE_05,PHASE_06,PHASE_07,PHASE_08,PHASE_09,PHASE_10,PHASE_11a,PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 交付报告：商铺归类、认证姓名核对、申诉审核增强、席位授予放宽

## 项目概览
- 需求：选房第一级整理为 1~10栋 / 地下车位 / 商铺 三类并反向生成导入文件；后台申诉列表显示编号、账号、昵称、产权人名字、时间与资料缩略图；认证须姓名+手机号与清册同一业主一致，否则走申诉，申诉通过追加清册；席位只要任期未结束即可授予。
- 模式：INCREMENTAL；画像版本 1.5.0
- 起止：2026-11-16T16:37:13+08:00 → 2026-11-16T22:08:09+08:00
- 最终状态：**DELIVERED_WITH_ISSUES**（人工验证项与既有 DEF-B 未关闭）

## 阶段执行摘要
| GROUP | 阶段 | 代理 | 状态 | 门控 | 重试 | 回流 |
|---|---|---|---|---|---|---|
| A | 01–02 | requirement-analyst | APPROVED | GR-A-001/002 PASS_WITH_CONDITIONS（逻辑核查 + 用户逐项答复） | 0 | — |
| B | 03–04 | system-architect | APPROVED | GR-B-001 PASS_WITH_CONDITIONS | 0 | — |
| C | 05–06 | software-developer | APPROVED | GR-C-001 PASS_WITH_CONDITIONS | 0 | — |
| D | 07–09 | test-engineer | APPROVED | GR-D-001 PASS_WITH_CONDITIONS | 0 | 0 |
| E1 | 10–11a | devops-engineer | APPROVED | GR-E1-001 PASS_WITH_CONDITIONS | 0 | — |
| E2 | 11b（A~E 逐段授权） | devops-engineer | APPROVED | GR-E2-001/002 PASS、GR-E2-003 PASS_WITH_CONDITIONS | 0 | — |

## 质量指标（baseline，PM 亲自复跑）
| 指标 | 值 | 目标 | 达标 |
|---|---|---|---|
| 单元/集成/E2E 新增失败 | 0（后端 unit 203、integration 675、e2e 61、smoke 6 全 OK） | 0 | ✅ |
| 前端 / 小程序 | 281/281、104/104 | 零新增失败 | ✅ |
| Must Have 故事有已执行用例 | 14/14 | 全部 | ✅ |
| 未解决 CRITICAL | 0 | 0 | ✅ |
| CI（Python 3.13） | run 43858790019 success | 通过 | ✅ |
| 测试环境远程 E2E | 22：19 PASS / 2 FAIL（既有 DEF-B）/ 1 SKIP | 本批新增失败 0 | ✅ |

## 交付物
- 文档：requirements（1.0.0）、architecture（1.0.0）、development（1.0.0）、testing（1.0.0）、deployment cicd_pipeline / deployment_plan（1.0.0）、deployment_report（3.0.0）。
- 代码：c32684b（已推送 origin/main）。

## 测试环境变更记录
- 代码：ANCHOR_TS=20261116193651；迁移 residency 0003_appeal_owner_name 已应用。
- 数据：107 条商铺楼栋 → "商铺"，原楼栋/门牌写入单元，丢失 0；总数 5742、业主 7862、手机号 4301、有效绑定 3 前后不变；id=4347 → 商铺1栋负1层1139号。
- 导出：/home/yangyang/ocap_exports/registry_import_20261116-213927.xlsx（目录 700、文件 600，留服务器，站点不可取得）。
- 含个人信息的备份（目标机 snapshots/，600）：ocapdb-registry-20261116213837.sql（用户决定保留至 2026-11-23）；shops-20261116213837.jsonl（无姓名手机号）；residency_appeal-20261116193651.sql。上批两份保留至 2026-11-23。

## 遗留问题
| 问题 | 来源 | 级别 | 建议 |
|---|---|---|---|
| DEF-B：远程用例期望"户主" | ocap_product_review | MINOR | 用户已定下批修 |
| DEF-024：席位开始日为不存在日期时 500 | GR-D-001 | MINOR（既有） | 用户已定下批修 |
| 远程护栏不含 POST /certifications，认证负例未在目标机验证 | GR-E2-003 | MINOR | 下批评估或人工自测 |
| 小程序申诉仅图片（OQ-06） | 用户确认 | — | 下批做 pdf |
| 小程序无法在开发机构建 | M-SD-006 | MINOR（既有） | 用户用 HBuilderX / 微信开发者工具 |

## 待人工验证
- M-02：浏览器打开后台申诉页查看缩略图、点开大图（含 pdf 预览失败时的下载入口）。
- M-06：新版小程序认证需填姓名（小程序新旧版均未正式发布，无存量用户影响）。
- 认证 422 自测：用错误姓名认证，提示"姓名与手机号未能通过清册核对…"。

## 部署
- 计划：deployment/deployment_plan.md；E2 已执行，环境：测试；阶段 A~E 均经用户当轮逐段授权；结果 DEPLOYED_SUCCESSFULLY。

## 安全
- 导出文件与备份只在目标机，权限 600；报告与文档无姓名、手机号、凭据。
