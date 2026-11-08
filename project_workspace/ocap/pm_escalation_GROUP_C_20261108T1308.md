<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-08T13:08:58+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>0.1.0</version>
  <input_files><file>phase_status.md</file><file>development/code_review_report.md</file></input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>DRAFT</status>
</file_header>

# PM 上报 — GROUP_C 完整性复核未通过（GR-C-004）

## 触发原因
- 用户 2026-11-08 要求复核代码是否完整实现。software-developer 完成复核（ocap-GROUP_C-4），结果写在 `development/code_review_report.md` 1.3.0 §8。
- PM 门控 GR-C-004 结论为 **FAIL**：4 条 CRITICAL、9 条 MAJOR 未解决。
- GROUP_C 已有 retries=2，GROUP_D 已有 defect_loops=2，都到了上限（PM 规则 6）。因此按协议 §H 上报，停止，等用户决定。

## 门控记录
- 本次：GR-C-004（见 phase_status.md）。
- 历史：GR-C-001、002、003，GR-D-001 到 005，GR-E2-001。
- 历史 PASS 只证明后端 API 层是通的（后端 120/120），**前后端从来没有联调过**：
  - Web 前端和小程序没有任何测试；
  - API 路径、字段与后端不一致的地方至少有 8 处。

## PM 亲自核验
- 后端：`python manage.py test --settings=config.test_settings`，结果 `Ran 120 tests` / `OK`。分层为 unit 33、integration 71、e2e 10、smoke 6，没有 skip。
- `makemigrations --check --dry-run`：No changes detected。
- 前端 `npm run build`：通过。`npm test`：No test files found，退出码 1。
- 小程序 `npm test`：No test files found，退出码 1。
- 抽查评审结论，以下 5 条全部属实：
  - CR-011：`merge_accounts` 没有调用方；
  - CR-012：`/me` 返回的 identities 是对象，前端却当数组用 `.join`；
  - CR-013：后端没有 `/claims/mine`，`POST /claims` 返回 405；
  - CR-014：前端调用 `/response`，后端是 `/responses`；
  - CR-023：0003 迁移是 makemigrations 自动生成的。

## 未解决问题（摘自 code_review_report.md 1.3.0 §8）

| 级别 | 编号 | 摘要 |
|---|---|---|
| CRITICAL | CR-011 | 账号合并未接入，REQ-FUNC-026/028 缺失，029/030/061/067 不可达 |
| CRITICAL | CR-012 | `/me` 的 identities 契约与前端不一致，首页报错，委员专属入口全部不显示 |
| CRITICAL | CR-013 | 报销/备用金前端调用不存在的接口，缺核销 UI，Web 没有 /claims 入口 |
| CRITICAL | CR-014 | 投票创建缺 kind、字段名错误，提交的路径和字段都不对 |
| MAJOR | CR-015~023 | 管理端路径/方法错误；收入录入与导入规则；备用金核销重复计支出；季报/年报未进定时任务，缺 deploy/systemd；绑定/换手机号无 UI；小程序缺密码登录、资料页不可达；打分范围与结果可见性；决议表单缺字段；迁移违反 P6 |
| MINOR | CR-024~026 | SECRET_KEY / ALLOWED_HOSTS 默认值偏弱；接口与设计有偏离；无前端测试 |

## 可选操作
1. **继续修复（推荐）**：用户明确同意突破重试上限后执行。
   - 带 REWORK_AUTHORIZED 调用 software-developer，修复 CR-011~023；CR-023 改为手写迁移。
   - 然后调用 test-engineer：补前后端契约测试和前端 vitest，重跑 GROUP_D。
   - 再重新部署。
2. **只修 CRITICAL**：只修 CR-011~014，MAJOR 记入遗留问题，交付状态为 DELIVERED_WITH_ISSUES。
3. **接受现状**：记为 OVERRIDDEN，现状部署，全部问题列入遗留。
4. **修改需求**：把部分功能移出本期范围，回到 GROUP_A。
5. **终止**。
