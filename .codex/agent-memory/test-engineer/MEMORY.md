# test-engineer 项目记忆

> 文件不存在或为空时视为没有项目经验；只有 kb-curator 维护「已验证」「用户偏好与禁止项」。

## 已验证

- M-TE-042（conf 0.6）："错位泄漏"类缺陷要**双向断言**：不仅测动作被拒，还要断言主体根本不出现在错误的收件箱（`/approval/tasks` count=0），且同时出现在正确的收件箱（`/resolutions?scope=todo` 命中）。写入校验（创建/更新）与数据迁移都要有用例。`test_settings` 禁用迁移（MIGRATION_MODULES→None），所以数据迁移的清理逻辑用 `importlib` 取出函数后直接 `clean(global_apps, None)` 调用验证，不依赖 migrate。证据：tests/integration/test_half_majority_flow_approvers.py、tests/e2e/test_half_majority_no_approver_journey.py。

## 用户偏好与禁止项

## 待验证
