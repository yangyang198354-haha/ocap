<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T00:56:52+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>requirements/user_stories.md</file><file>development/implementation_plan.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（PHASE_09）

## 摘要

critical path 口径：替代（完整 API 旅程 `backend/tests/e2e`；项目无浏览器 E2E 框架）

- 执行时间：2026-11-11 00:36–00:42
- 范围：`backend/tests/e2e` 全量 26 个，本批新增 4 个（TC-E2E-301~304）
- 命令：`python manage.py test tests.e2e --settings=config.test_settings`

**metrics**：total = pass + fail + skip + blocked + not_testable = 26 = 26 + 0 + 0 + 0 + 0

通过率 = 26 / 26 = **100%**；critical path 覆盖率 = 24 / 24 = **100%**；critical path 通过率 = **100%**；本层门控：**PASSED**

## 全量回归

| 命令 | 计数 | 相对基线新增失败 |
|---|---|---|
| `python manage.py test --settings=config.test_settings`（backend） | `Ran 412 tests in 6.124s` / `OK` | **0**（基线 327 + 新增 85） |
| `npx vitest run`（frontend） | `Tests 2 failed \| 127 passed (129)` | **0**（2 个既有 theme 环境失败） |
| `npx vitest run`（miniprogram） | `Test Files 11 passed / Tests 71 passed (71)` | **0**（基线 69 + 新增 2） |

分层：unit 98、integration 282、e2e 26、smoke 6，合计 412。

## 用户旅程

### TC-E2E-301: 富文本 → 自定义样式 → 发布 → Web/小程序阅读 → 下线

- 关联：US-105/106/107/108/109/110/111/112/113/119/121/131
- 步骤：创建自定义样式模板 → 创建含加粗/居中/图片/分页的正文 → 发布 → 会员 Web 详情（2 页、font-size:20px、`<img>`）→ `fmt=blocks`（src 相对路径、theme）→ 下线 → 会员 404
- 结果：PASS

### TC-E2E-302: 模型配置 → 生成文案 → 确认 → 一键保存（自动 + 人工）→ 内容包

- 关联：US-114/115/117/118/125/126/127/128/129/130
- 步骤：保存 DeepSeek 密钥 → 测试连通 → 可选模型 1 个 → AI 文案任务 → 生成结果转文档 → 确认文案 → 发布 → 勾选公众号（替身 SAVED）+ 小红书（人工）→ 历史状态 SAVED / MANUAL_REQUIRED → 导出 ZIP 含生成文案
- 结果：PASS

### TC-E2E-303: 素材复用与删除保护

- 关联：US-120/121/122/123
- 步骤：上传 PNG → 复用到两条内容并发布 → 素材仅 1 条 → 删除被拒（列出 2 条内容）→ 下线一条仍拒绝 → 全部下线后删除成功
- 结果：PASS

### TC-E2E-304: AI 文生图与视频生成入库

- 关联：US-116/124
- 步骤：配置图像/视频服务 → 文生图任务（替身 URL + 远程下载替身）→ 候选素材保存到素材库 → 确认文案 → 视频任务提交（Wait）→ 轮询完成 → 视频入库（AI_GENERATED）
- 结果：PASS

## 缺陷

无。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-01 | AC-109-01~04、AC-110-01~04 | 在管理端编辑器实际设置对齐/颜色/链接/清除格式/撤销重做 | 与公众号编辑页等价，保存后回显一致 | 浏览器（Chrome/Edge） | 否 |
| M-02 | AC-115-03 | 编辑器已有手写内容时点击"放入编辑器"并取消/确认 | 取消不覆盖；确认覆盖 | 浏览器 | 否 |
| M-03 | AC-121-03 | 素材库为空时打开"从素材库插入" | 显示"素材库为空"且不报错 | 浏览器 | 否 |
| M-04 | 真实平台 | 用真实公众号 access_token 保存草稿；小红书/头条导出内容包后人工粘贴 | 公众号草稿箱出现内容；人工平台可粘贴 | 真实平台账号（不纳入自动化） | 否 |
| M-05 | AC-124-02/03 | 配置真实即梦账号发起视频生成，观察成功/失败 | 成功入库视频；失败显示原因 | 即梦账号与额度 | 否 |
| M-06 | AC-108-01、AC-123-01 | 小程序真机查看含图片/视频的信息公开 | 图片/视频可显示与播放，链接复制提示 | 微信开发者工具/真机 | 否 |
