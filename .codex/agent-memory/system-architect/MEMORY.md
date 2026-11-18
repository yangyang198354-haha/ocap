# system-architect 项目记忆

> 文件不存在或为空时视为没有项目经验；只有 kb-curator 维护「已验证」「用户偏好与禁止项」。

## 已验证

- M-SA-028（conf 0.6）：决议审批 mode 枚举互斥——DESIGNATED（审批人逐个 decide）与 HALF_MAJORITY（全体投票判定）是两条不同处置路径，二者的"审批人"字段互斥。设计/契约必须规定 HALF_MAJORITY 不得携带审批人并在流程创建处强制；否则审批人进入 `flow_snapshot.approver_ids`，既让决议错误地漏入 `/approval/tasks` 审批待办，又在用户点"同意"时被 `ApprovalEngine.decide()` 的 USE_VOTE_ENDPOINT 守卫拒绝（错位缺陷）。证据：apps/approval/views.py `_validate_flow_payload`、services.py:93 decide 守卫、commit f1f1800。关联 [[M-SD-040]]。

## 用户偏好与禁止项

## 待验证
