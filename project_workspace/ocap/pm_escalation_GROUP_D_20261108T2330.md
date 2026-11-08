<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-08T23:30:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>0.1.0</version>
  <input_files><file>phase_status.md</file><file>testing/integration_test_report.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>DRAFT</status>
</file_header>

# PM 上报：GROUP_D 发现安全缺陷 DEF-006（GR-D-007）

## 触发原因
- GR-D-006 指出的覆盖缺口已经补齐：69 个 Must Have 都有执行过的用例。补测时新写的 TC-INT-106 暴露了一个产品缺陷 DEF-006（MAJOR，安全类）。
- 这个缺陷需要回流到 GROUP_C 修复，但 defect_loops 已经是 3，超过默认上限（PM 规则 6），所以上报，由用户决定是否继续。

## PM 核验
- 复跑结果：278 个用例中 277 个通过。分布如下：
  - 后端：unit 42、integration 148（其中 1 个失败）、e2e 16、smoke 6
  - Web：36
  - 小程序：30
- 各层门控：单元 74/74，集成 181/182，critical path 16/16。
- DEF-006：PM 读过 `backend/apps/accounts/services.py:113-137`。`verify_code` 在比对 HMAC 之前没有检查 `row.attempts >= code.max_wrong_per_code`，锁定时也没有设置 `consumed_at`。结果是：第 5 次输错返回 429，之后再输入正确的验证码，仍然返回 200 并签发 token。这违反 AC-006-04，影响注册、登录、绑定/更换手机号、注销所有用到验证码的流程。

## 其他发现
- OBS-001（MINOR）：匿名请求管理端接口返回 403；AC-073-03 写的是"要求登录"，应该返回 401（`core/permissions.py:19-23`）。
- AC-006-04 中"30 分钟内累计输错 10 次锁定手机号"这一条，没有在登录端点上测过。

## 可选操作
1. **修复 DEF-006 后重测（推荐）**：可以一并修 OBS-001。PM 复跑并门控，之后进入部署。
2. **接受 DEF-006 带病部署**：记为 OVERRIDDEN，作为安全遗留项。测试环境内外网都能访问，因此**不推荐**。
3. **终止**。
