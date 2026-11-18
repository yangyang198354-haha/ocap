# devops-engineer 项目记忆

> 文件不存在或为空时视为没有项目经验；只有 kb-curator 维护「已验证」「用户偏好与禁止项」。

## 已验证

- M-DE-043（conf 0.6）：纯数据清理迁移（RunPython，reverse=noop）部署与回滚安全——reverse 不删表/字段，无结构损失；若部署前已在目标库做过**等价且幂等**的清理（本例删 HALF_MAJORITY 流程的 FlowApprover + 置空快照 approver_ids），`migrate` 再次运行仍安全。注意：有意新增迁移时，预检 #9"未应用=0"不适用——出现 1 条 unapplied 正是本次变更，由 DEPLOY-004 应用，不要当异常停止。证据：migrations/0002、部署锚点 TS 20261118194852、deployment_plan DEPLOY-004。

## 用户偏好与禁止项

## 待验证
