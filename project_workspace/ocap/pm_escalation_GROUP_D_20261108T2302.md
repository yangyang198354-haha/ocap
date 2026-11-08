<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-08T23:02:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>0.1.0</version>
  <input_files><file>phase_status.md</file><file>testing/test_plan.md</file><file>testing/e2e_test_report.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>DRAFT</status>
</file_header>

# PM 上报：GROUP_D 重测未通过（GR-D-006）

## 触发原因
- GR-C-005 返工之后，test-engineer 做了完整重测（ocap-GROUP_D-6 因 API 限额中断，ocap-GROUP_D-7 续跑完成）。
- PM 门控 GR-D-006 的结论是 **FAIL**。
- GROUP_D 的 retries=2、defect_loops=2，都已达到上限（PM 规则 6），按协议 §H 上报。

## PM 亲自复跑结果（与报告一致）

| 部分 | 结果 |
|---|---|
| 后端 unit | 42 OK |
| 后端 integration | 99（1 个失败） |
| 后端 e2e | 13 OK |
| 后端 smoke | 6 OK |
| 后端全量 | 160（1 个失败） |
| Web vitest | 33/33 |
| 小程序 vitest | 27/27 |
| 合计 | 220 个用例，219 个通过 |

各层门控都满足阈值：

| 层 | 结果 | 阈值 |
|---|---|---|
| 单元 | 74/74 | 0.80 |
| 集成 | 126/127 = 0.9921 | 0.90 |
| critical path | 13/13 = 1.00 | 1.00 |

## 未通过项
1. **【MAJOR】11 个 Must Have 故事没有任何用例映射。** §J-D 要求每个 Must Have 故事至少有 1 个真实执行的用例。下列故事在 test_plan 中都没有映射：

   | 故事 | 内容 |
   |---|---|
   | US-006 | Web 手机号登录 |
   | US-010 | 三入口同一账号 |
   | US-013 | 注销后重新注册 |
   | US-025 | 游客权限 |
   | US-028 | 更换手机号 |
   | US-035 | 清册手机号被改后身份保留 |
   | US-042 | 赋予业主代表 |
   | US-068 | 身份失效时在途事项不变 |
   | US-070 | 小程序首次登录设置头像昵称 |
   | US-071 | 多审批人与自批边界 |
   | US-073 | 管理员重置管理员密码 |

   其中部分故事可能已有测试，只是没有映射，需要 test-engineer 逐一核对。没有测试的要补写用例；US-070 涉及真机，标为 NOT_TESTABLE 并列入人工验证清单。

2. **【MINOR】DEF-005。** `frontend/src/shared/api.js:132` 的 `registryUnit()` 发 GET 请求，但后端 `AdminUnitDetailView` 不支持 GET。这个函数没有任何调用方，属于死代码。不过它导致全量回归有 1 个失败，推送后 CI 会变红。修复只需删掉这一行，或者在后端补一个 GET 详情接口。

## 可选操作
1. **再修一轮（推荐）**：需要用户明确同意突破上限。
   - 调用 software-developer 修 DEF-005（删除死代码）；
   - 调用 test-engineer 补齐 11 个故事的映射与用例；
   - PM 复跑、门控，然后进入部署（E1 收尾 → E2，需用户当轮授权）。
2. **只修 DEF-005，接受映射缺口**：GR-D-006 记为 OVERRIDDEN，11 个故事列入遗留问题，最终状态 DELIVERED_WITH_ISSUES，然后部署。
3. **全部接受现状并部署**：记为 OVERRIDDEN，CI 会有 1 个失败。
4. **终止**。
