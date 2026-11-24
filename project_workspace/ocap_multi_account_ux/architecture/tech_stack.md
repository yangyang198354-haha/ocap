<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-24T22:22:09+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>0.1.0</version>
  <input_files><file>project_workspace/ocap_multi_account_ux/architecture/architecture_design.md</file><file>project_workspace/ocap_multi_account_ux/architecture/module_design.md</file><file>backend/requirements.txt</file><file>frontend/package.json</file><file>miniprogram/package.json</file><file>.trae/sdlc/project_profile.md</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

## 技术选型表

本次为 INCREMENTAL 改动，不新增任何第三方依赖，全部沿用现有技术栈。

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言（后端） | Python | 3.12（画像 P1 `[FREEARK]`） | 沿用 | 现有后端运行时 | 全部 | 本机实测为 3.14.6（画像 P4），与 3.12 目标存在差异，记录不自行降级 |
| Web 框架 | Django | `Django>=5.2,<6.0`（[requirements.txt](file:///c:/Users/胖子熊/MyProject/ocap/backend/requirements.txt)） | 沿用 | 审批、模型、迁移均在 Django ORM 内 | 全部 | 本机实测 Django 6.0.6 与目标 5.2 不一致；测试以 `config.test_settings` 为准 |
| API 框架 | Django REST Framework | `djangorestframework>=3.15,<4.0`（requirements.txt） | 沿用 | 现有 APIView/分页/错误结构 | 全部 | 低 |
| 数据存储 | MySQL（测试/生产测试机）/ SQLite（测试设置） | 画像 P7；`mysqlclient>=2.2` | 沿用 | 账户、台账、审批均在现有库 | 全部 | 新增列均为可空，迁移风险低 |
| Excel/CSV 解析 | openpyxl | `openpyxl>=3.1,<4.0`（requirements.txt） | 沿用 | 历史支出与收入导入模板/解析 | REQ-FUNC-353/356/357 | 本机缺包时导入相关测试按画像 P4 标 BLOCKED，不安装 |
| Web 前端框架 | Vue 3 + Vite | `vue ^3.5.13`、`vite ^6.0.1`（[package.json](file:///c:/Users/胖子熊/MyProject/ocap/frontend/package.json)） | 沿用 | 现有页面与构建链 | REQ-FUNC-351～362 | 低 |
| UI 组件库 | Element Plus | `element-plus ^2.8.7`（package.json） | 沿用 | `el-select`/`el-button`/`el-upload` 均为既有组件 | 全部 Web | 按钮对比度依赖主题 CSS 变量，需按 AC-410 实测定值 |
| 前端状态 | Vue Composition API（组件内 state） | 随 Vue 3 | 沿用 | 本次账户选择为页面级状态，不引入全局 store（ADR-188/191） | REQ-FUNC-359/360 | 低 |
| HTTP 客户端 | axios | `axios ^1.7.9`（package.json） | 沿用 | `shared/api.js` 既有封装 | 全部 Web | 低 |
| 前端测试 | vitest + @vue/test-utils + jsdom | `vitest ^2.1.9`、`@vue/test-utils ^2.4.6`、`jsdom ^25.0.1`（package.json） | 沿用 | 现有 `frontend/tests/*.spec.js` | 全部 Web | 低 |
| 小程序框架 | uni-app（Vue 3） | `@dcloudio/uni-app ^3.0.0-4060620250520001`（[package.json](file:///c:/Users/胖子熊/MyProject/ocap/miniprogram/package.json)） | 沿用 | 现有小程序工程 | REQ-FUNC-364/365 | picker 在 H5/微信端表现差异需两端测试 |
| 小程序测试 | vitest + @vue/test-utils | `vitest ^2.1.9`（package.json） | 沿用 | 现有 `miniprogram/tests/*.spec.js` | REQ-NFUNC-078 | 低 |
| 进程管理 | systemd + gunicorn | `gunicorn>=22.0`（requirements.txt）；画像 P7 | 沿用 | 现有部署形态 | 全部后端 | 低 |
| CI/CD | GitHub Actions（只测试与构建，不部署） | 画像 P7 | 沿用 | 现有工作流 | 全部 | 低 |
| 部署方式 | tar 打包 + scp + 迁移 + systemd 重启 | 画像 P7 | 沿用 | 物理机部署，无容器（P8 禁用 Docker） | 全部 | 低 |
| 新增依赖 | 无 | — | — | 读时聚合、审批复用、组件复用均可在现有依赖内完成 | 全部 | 无许可证/维护新增风险 |

### 数值与精度说明

非算法项目，无定点格式或精度预算需求。金额沿用既有 `Decimal(max_digits=14, decimal_places=2)` 与 `money()` 输出（`backend/apps/core/money.py`）；报表按账户聚合复用 `_aggregate` 相同的 `Decimal` 求和口径，不引入浮点运算。

## 技术风险

| 等级 | 风险 | 说明 | 缓解措施 |
|---|---|---|---|
| High | 历史支出导入审批改造导致既有测试语义变化 | 现有 `backend/tests/integration/test_history_expense_api.py`、`backend/tests/e2e/test_history_expense_journey.py` 断言"导入即入账、审批实例为 0"；新需求要求审批后才入账 | GROUP_C 同步改写受影响用例的预期；GROUP_D 以修改后的用例为准并补充"审批中零台账"断言；报告中列明被修改用例清单，避免"基线零新增失败"被误判 |
| Medium | 读时聚合的查询成本随报表页增长 | 每页一次台账范围扫描 + Python 分桶（OQ-B-05） | 只查当前页 `min(start)~max(end)` 范围；按账户+状态过滤走既有索引；上线后如报表页数据量增大再评估缓存（ADR-187 备选 C） |
| Medium | 审批通过回调在事务提交后执行，账户可能已停用 | `ApprovalEngine` 在实例提交后调用回调（`approval/services.py`）；账户停用会令 `LedgerService.post` 抛 `ACCOUNT_UNAVAILABLE` | 与 claims 现有行为一致，不新增状态（OQ-B-02）；测试只覆盖正常路径，操作规范要求审批前不随意停用账户 |
| Medium | 账户选择组件被多处复用时的重复请求与默认值竞争 | 每实例独立加载启用账户 | 组件只在挂载时请求一次；`loaded` 事件携带默认账户，页面以 `v-model` 单一来源；AC-423/424 覆盖两端默认一致 |
| Low | Element Plus 按钮禁用态对比度不足 | 主题默认禁用透明度可能低于 3:1 | 使用现有 `--muted`/`--line` 变量的显式样式；GROUP_D 以 AC-410-01/02 的对比度口径做 UI 检查 |
| Low | 小程序 picker 在 H5 与微信端交互差异 | uni-app picker 两端渲染不同 | 测试只断言数据与提交参数（默认账户、仅启用账户、未选阻止提交），不断言具体弹层样式 |
| Low | 迁移回滚丢失新批次账户关联 | 新增列为可空、无回填；回滚删除列 | 回滚前备份数据库；迁移说明标注不可恢复的数据（MOD-207） |
