<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-08T23:38:45+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>testing/test_plan.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

> 复跑说明（ocap-GROUP_D-9，续 -8）：GR-C-007 已批准 DEF-006 / OBS-001 修复；全层按序重跑全部通过，DEF-006 CLOSED，OBS-001 已修复（匿名 401）。以下为 -8 的历史说明：GR-D-006 FAIL 修正。新增 E2E 旅程 TC-E2E-014~016，覆盖补测的 11 个故事中可串成旅程的部分；按实际情况更正 critical path 覆盖说明；DEF-005 CLOSED；新增 DEF-006。REWORK_AUTHORIZED: testing/ 下 4 份文件与三处测试代码目录。

## 摘要

critical path 口径：替代（`backend/tests/e2e/` 的多步 API 旅程用例；项目无浏览器/小程序 E2E 框架。前后端契约由集成层 `test_frontend_contract.py` 与 vitest 路径断言补充，见集成报告）

- 执行时间：2026-11-08 23:36 ~ 23:38（Asia/Shanghai，ocap-GROUP_D-9 最后一次执行）。
- 环境：Linux，Python 3.12.3，Django 5.2.19，DRF 3.18.3，`config.test_settings`，SQLite `:memory:`，fake 短信/邮件/微信。
- 命令：
  - `(cd backend && python manage.py test tests.e2e --settings=config.test_settings)`
  - `(cd backend && python manage.py test tests.smoke --settings=config.test_settings)`
- 本层用例：E2E 旅程 16（13 既有 + 3 新写 TC-E2E-014~016）+ 冒烟 6（既有，回归用）+ 不可测 5 = 27。
- total = pass + fail + skip + blocked + not_testable = 27 = 22 + 0 + 0 + 0 + 5。
- 通过率 = pass/(pass+fail+blocked) = 22/(22+0+0) = 100.00%。
- critical path 覆盖率 = 45 / 69 = 65.22%（有 E2E 旅程用例的 Must Have 故事 / Must Have 故事总数；0.4.0 为 34/69，新增 US-006、010、011、013、025、028、035、042、068、071、073）。
- critical path 通过率 = 16 / 16 = 100.00%（threshold critical_path = 1.00）。
- 判定模式与阈值：FULL_FLOW threshold。
- **本层门控：PASSED**（critical path 通过率 100% ≥ 100%）。
- **关于其余 24 个 Must Have 故事（更正 0.4.0 第 28 行“其余由集成层覆盖”的说法）**：这 24 个故事没有 E2E 旅程用例，是已知缺口，不是“由集成层整体覆盖”——它们各自有真实执行的单元 / 集成 / vitest 用例（逐故事的用例 ID 见 test_plan“US → 用例总表”，69/69 均非空），但没有多步旅程。清单：US-002、003、004、005、007、008、014、017、018、019、020、022、027、036、037、038、039、040、041、043、048、067、069、070。其中 US-002/004/008/070 涉及微信真实链路，真机部分在人工验证清单（MV-001、MV-005、MV-007）。
- 待人工验证：5 条（MV-001、MV-004 ~ MV-007 为微信 / 小程序真机相关），critical path 中含 manual 项，最终状态至多 DELIVERED_WITH_ISSUES（协议 §K）。

## 全量回归

```
$ (cd backend && python manage.py test --settings=config.test_settings)
Ran 212 tests in 7.754s
OK

$ (cd frontend && npx vitest run)      → Test Files 4 passed (4)   Tests 36 passed (36)
$ (cd miniprogram && npx vitest run)   → Test Files 3 passed (3)   Tests 30 passed (30)
```

- 全量计数：total = 278 = 278 pass + 0 fail + 0 skip + 0 blocked + 0 not_testable（后端 212 = 212 + 0；Web 36；小程序 30）。通过率 278/278 = 100.00%。
- 与分层一致：单元 74 + 集成 182 + 本层可执行 22 = 278（后端 42 + 148 + 16 + 6 = 212；Web 19 + 17 = 36；小程序 13 + 17 = 30）。
- 基线对比：基线后端全量 160/160 通过。本次后端全量 212/212 通过，既有 160 个用例全部仍通过；**相对基线新增失败 0 条**。TC-INT-106 在 DEF-006 修复后 PASS。前端、小程序无基线。

## 用户旅程

### TC-E2E-001: 注册 → 认证户主 → 完善资料
- 关联：US-001 / US-021 / US-023 / US-030；环境：test_settings + fake SMS。
- 步骤：请求 REGISTER 码（202）→ 注册（201）→ `GET /me`（游客）→ 清册认证（201，HEAD）→ `GET /me`（户主）→ PATCH 资料（200）。
- 结果：PASS。

### TC-E2E-002: 同住人申请 → 户主审批 → 移除
- 关联：US-024 / US-029。
- 步骤：申请（201）→ 户主待审列表（1 条）→ 同意（200）→ 同住人 `/me`（含"同住人"）→ 户主移除（204）→ `/me` 不再含"同住人"。
- 结果：PASS。

### TC-E2E-003: 认证失败 → 申诉 → 管理员核准
- 关联：US-026。
- 步骤：认证（422 `PHONE_NOT_IN_REGISTRY`）→ 上传凭证（201）→ 申诉（201）→ 管理员核准（200）→ `/me` 含"户主"。
- 结果：PASS。

### TC-E2E-004: 指定审批决议 → 公开可查
- 关联：US-044 / US-045 / US-047。
- 步骤：主任发起（201）→ 审批人待办 1 条 → 同意（APPROVED）→ 其他业主读详情（200）→ 公开列表（200）。
- 结果：PASS（DEF-001 已修复）。

### TC-E2E-005: 半数表决决议 → 到期判定 → 结果公开
- 关联：US-046 / US-047 / US-065。
- 步骤：主任发起（201）→ 3 委员同意（200）→ 截止时间改过期 → `run_due_jobs` → 状态 APPROVED、`result.agree=3` → 其他业主持有可读详情。
- 结果：PASS。

### TC-E2E-006: 收入导入审批 → 报销审批 → 台账生成
- 关联：US-049 / US-050 / US-058 / US-059 / US-060 / US-061。
- 步骤：CSV 导入（201，300.50）→ 提交审批 → 同意（APPROVED）→ 报销 100.00 创建（201）→ 同意 → 生成台账（201，收入 300.50 / 支出 100.00 / 结余 200.50）。
- 结果：PASS。

### TC-E2E-007: 财务报表对任意登录用户可见
- 关联：US-063。
- 步骤：预置已生效收入表 → 生成台账（201）→ 普通业主读收入表列表与台账报表（200）。
- 结果：PASS（DEF-002 已修复）。

### TC-E2E-008: 业委会投票闭环
- 关联：US-052 / US-053 / US-057。
- 步骤：主任创建投票（201）→ 委员应答（201）→ 截止改过期 → 结果（200，首选项 count=1）。
- 结果：PASS。

### TC-E2E-009: 业主代表 / 产权业主参与投票调查
- 关联：US-054 / US-055 / US-056。
- 步骤：主任创建调查（201）→ 业主代表应答（201）→ 产权业主应答（201）。
- 结果：PASS（DEF-004 已修复）。

### TC-E2E-010: 注册 → 设置密码 → 密码登录 → 注销
- 关联：US-001 / US-009 / US-031。
- 步骤：注册（201）→ 设置密码（204）→ 密码登录（200）→ CANCEL 码（202）→ 注销（204）→ 旧 token `/me`（401）。
- 结果：PASS。

### TC-E2E-011: 微信账号绑定已注册手机号 → 合并
- 关联：US-012 / US-015 / US-016 / US-066 / US-072（AC-012-01、AC-072-01）；环境：test_settings + fake SMS。
- 步骤：A 手机号注册并认证户主（201）→ W 仅微信、同住人 → 主任创建调查 → A、W 都作答（201）→ W 取 BIND_PHONE 码并绑定 A 的手机号 → `merged=true` 并返回新令牌 → `/me` 身份为 {A 户主, W 同住人}、标签含"户主" → 旧令牌 `/me` 401 → 详情 `my_response`=["同意"]（保留 A 的）→ 手机号验证码登录得同一 user id → 管理员审计含 ACCOUNTS_MERGED、MERGE_ANSWER_DISCARDED。
- 结果：PASS。

### TC-E2E-012: 备用金预借 → 报销 → 核销 → 公开报表
- 关联：US-049 / US-050 / US-051 / US-061 / US-063（AC-051-03）。
- 步骤：预借 1000 并审批通过 → 报销 1200 并审批通过 → 核销（差额 +200）→ 生成报表 → 普通业主读报表，支出合计 1200（非 2200/2400）。
- 结果：PASS。

### TC-E2E-013: 逐条录入收入 → 审批生效 → 报表 → 作废重算
- 关联：US-058 / US-060 / US-061 / US-062。
- 步骤：逐条录入（201，DRAFT）→ 提交审批 → 同意生效 → 报表含该收入 → 作废 → 手动重新生成，收入归零。
- 结果：PASS。

### TC-E2E-014: 账号与身份生命周期（注册 → 认证 → 换号 → 注销 → 再注册 → 重新认证）
- 关联：US-006 / US-010 / US-013 / US-025 / US-028 / US-035（AC-006-01、AC-010-01、AC-013-01/02、AC-025-01、AC-028-01/04、AC-035-03）；环境：test_settings + fake SMS。
- 步骤：注册（201）→ `/me` is_guest → 清册认证（201，HEAD）→ 换号（merged=false）→ 旧号用户不存在 → 新号验证码登录得同一 user id 且含“户主” → CANCEL 码注销（204）→ 同号再注册（201，新 user id，labels=["游客"]）→ 清册仍为旧号：认证 422 `PHONE_NOT_IN_REGISTRY` → 管理员把清册改为新号 → 认证 201 role=HEAD。
- 结论：PASS。

### TC-E2E-015: 业主代表赋予 → 代表投票 → 身份失效后在途事项保持
- 关联：US-042 / US-068 / US-071（AC-042-01/05、AC-068-01/02/04、AC-071-01）。
- 步骤：管理员配置任期与 cap_rep=2 → 赋予 2 名业主代表（201）→ 主任发起决议（指定审批人）与代表投票（participant_count=2）→ R1 作答（201）→ 撤销 R2 席位（204）后 R2 作答 403 → 撤销主任席位（204）→ 决议仍 PENDING → 审批人通过（APPROVED）→ 投票答卷数 1、participant_count 仍为 2。
- 结论：PASS。

### TC-E2E-016: 管理员创建管理员 → 重置密码
- 关联：US-011 / US-073（AC-073-01/02）。
- 步骤：A 创建 B（201）→ B 登录（200）→ 普通用户重置 B 密码 403 → A 重置（204）→ B 旧令牌访问 `/admin/audit-logs` 401 → 旧密码登录 400 → 新密码登录 200 并可访问审计日志。
- 结论：PASS。

### 冒烟 tests.smoke（既有 6 个）
- 命令输出：`Ran 6 tests in 0.243s  OK`。结果：PASS（6）。

### TC-E2E-NT-001 ~ 005: 不可测项
- TC-E2E-NT-001：微信扫码 / 小程序一键登录真实链路（AC-002/004/008）→ NOT_TESTABLE，MV-001。（经 FakeWeChatClient 可测部分已由 TC-INT-109/111/113/147~149 真实执行。）
- TC-E2E-NT-002：uni-app 运行时页面渲染与 `uni.chooseImage/uploadFile` 真机行为 → NOT_TESTABLE，MV-004。
- TC-E2E-NT-003：微信开发者工具/真机登录与手机号授权 → NOT_TESTABLE，MV-005。
- TC-E2E-NT-004：小程序业务流程真机走查（登录 → 报销 / 投票 → 绑定手机号）→ NOT_TESTABLE，MV-006。
- TC-E2E-NT-005：US-070 AC-070-01 中通过微信头像昵称填写能力（`open-type=chooseAvatar`、`type=nickname`）选择头像并在资料页显示 → NOT_TESTABLE，MV-007。vitest 已覆盖页面回调与保存请求（TC-MP-028/029）。

## 缺陷

无未关闭缺陷。DEF-006 已 CLOSED（见下）。

## 缺陷状态（历史与本次）

- DEF-005：**CLOSED**（GR-C-006 删除 `registryUnit`；TC-INT-082 本次 PASS，`git grep "registryUnit("` 在 `frontend/src` 无命中）。
- DEF-006：**CLOSED**（GR-C-007：`verify_code` 使达到上限的验证码作废；TC-INT-106 本次 PASS，全量 212/212）。
- OBS-001：**已修复**（`IsAdmin` 匿名 401、已登录普通会员 403）；TC-INT-125/130/146 断言收紧为只接受 401，全部 PASS。历史描述：管理端接口对未登录访客返回 403 `需要管理员权限`，而 AC-073-03 写“要求登录”；`backend/apps/core/permissions.py:19-23`。

## 缺陷复核（历史）

DEF-001 ~ 004（已 FIXED）本次回归未复现：对应 TC-INT-038、061、063、064、070 与 TC-E2E-004、007、009 均通过。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-001 | AC-002/004/008（TC-E2E-NT-001；TC-INT-009 仅验证降级） | 在配置真实微信 AppID/Secret 的环境，用微信扫码 / 小程序一键登录 | 首次创建游客账号；已绑定手机号的微信登录进入原账号；昵称取自微信 | 真实微信开放平台与小程序账号 | 是 |
| MV-002 | AC-019、AC-059（xlsx 路径） | 安装 openpyxl 后，用 xlsx 清册与收入表各导入一次 | 与 CSV 一致：行数、金额合计、错误/重复行提示 | 具备 openpyxl 的后端环境 | 否 |
| MV-003 | Web 全部 AC（视觉与浏览器行为） | 浏览器打开 Web 端，按 US 走查登录、报销/核销、投票、手机号绑定/换绑、管理端撤销认证 | 页面与 API 行为一致，无控制台报错 | Chrome + 测试环境后端 | 是 |
| MV-004 | TC-E2E-NT-002 | 微信开发者工具/HBuilderX 构建小程序，进入"报销/备用金"，选发票上传并提交 | `uni.chooseImage`+`uploadFile` 成功，POST /claims/reimbursements 带 invoice_ids，列表出现新单 | HBuilderX + 微信开发者工具 + 测试环境后端 | 是 |
| MV-005 | TC-E2E-NT-003 | 真机登录，验证码登录新账号（is_new）→ 进入头像昵称页；已有账号密码登录 | 新账号进资料页；老账号进首页；手机号授权/绑定可合并 | 真机微信 | 是 |
| MV-006 | TC-E2E-NT-004 | 真机走查：登录 → 投票作答与查看结果 → 绑定手机号（合并）→ 申诉带证明 | 各页面跳转（含 tabBar switchTab）正确；合并后换用新令牌 | 真机微信 + 测试环境后端 | 是 |
| MV-007 | AC-070-01 / TC-E2E-NT-005 | 真机微信小程序首次微信登录 → 进入“完善资料”页 → 点“选择头像”用微信头像，在昵称框用微信昵称填写能力 → 保存 | 保存后资料页显示所选头像与昵称；再次微信登录不再进入该页（AC-070-02） | 真机微信 + 测试环境后端 | 是 |
