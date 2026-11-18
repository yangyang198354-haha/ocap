# software-developer 项目记忆

> 文件不存在或为空时视为没有项目经验；只有 kb-curator 维护「已验证」「用户偏好与禁止项」。

## 已验证

- M-SD-040（conf 0.6）：模式/枚举字段的互斥约束要在**写入端**校验，且创建（POST）与更新（PUT）两条写路径共用同一校验函数，补一处即覆盖两处（本例 `_validate_flow_payload`：HALF_MAJORITY 带 approver_ids → 400，并强制返回 `[]`）。被下游当作路由依据的**快照字段**（`flow_snapshot.approver_ids` 同时被 `TaskListView` 过滤和 `decide()` 守卫使用）一旦含脏值就产生"错位"缺陷；因此既要堵写入，又要写**数据迁移**清理历史快照与关联表，不能只改校验。证据：apps/approval/views.py、migrations/0002_clean_half_majority_approvers.py、commit f1f1800。关联 [[M-SA-028]]。

## 用户偏好与禁止项

## 待验证
