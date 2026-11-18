<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-18T11:41:59+08:00</timestamp>
  <project_name>ocap_batch_1118</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>development/implementation_plan.md</file>
    <file>requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（ocap_batch_1118，baseline 模式）

critical path 口径：替代（后端多步 API 旅程 TC-E2E-1601~1605 + 前端 jsdom 组件旅程 TC-E2E-1611~1614；项目无浏览器 E2E 框架，画像 P3）。

## 摘要

- 执行时间：2026-11-18 11:29–11:42。上一层（集成）门控 PASSED，故执行 E2E。
- total = pass + fail + skip + blocked + not_testable = 17 = 9 + 0 + 0 + 0 + 8（新写旅程 9：后端 5、前端 4；NOT_TESTABLE = 人工验证项 M-1~M-8）。
- critical path 覆盖率 = 有 E2E 用例的 Must Have 故事 / Must Have 故事总数 = 15/15 = 1.00（US-244~257、US-259；US-252/US-253 的真实观感/命中区域另在人工清单 M-1~M-4，**待人工验证**）。
- critical path 通过率 = pass/(pass+fail+blocked) = 9/(9+0+0) = 1.00。
- **本层门控：PASSED**（baseline：零新增失败、新写全部通过）。注意：critical path 仍有未完成的人工验证（M-1、M-2、M-3），按协议 §K，最终状态至多 DELIVERED_WITH_ISSUES。

## 全量回归

| 范围 | 命令 | 计数 | 相对基线新增失败 |
|---|---|---|---|
| 后端全量 | `(cd backend && $PY manage.py test --settings=config.test_settings)` | Ran 1119 tests，OK（unit 236 / integration 806 / e2e 71 / smoke 6；基线 1025 + 新写 94） | 0 |
| 后端 E2E 层 | `... test tests.e2e` | Ran 71 OK（66 既有 + 5 新） | 0 |
| 后端 smoke | `... test tests.smoke` | Ran 6 OK | 0 |
| 前端全量 | `(cd frontend && npx vitest run)` | 45 文件 / 531 passed（基线 41/482 + 新写 4 文件 49；0 失败，0 Unhandled Errors） | 0 |
| 小程序全量 | `(cd miniprogram && npx vitest run --passWithNoTests)` | 18 文件 / 135 passed | 0 |
| 静态 | `manage.py check`；`makemigrations --check --dry-run`；`compileall backend/tests` | no issues；No changes detected；ok | — |

相对基线新增失败数：0。基线中的 7（B1~B7）+ 9（F1~F9）条预期失败与 8 个 Unhandled Errors 均已改写消除；TC-INT-504 稳定通过。

## 用户旅程

### TC-E2E-1601: 注册 → 逐级选房 → 申诉不全被拒且无残留 → 一次提交完整申诉 → 管理员通过 → 身份页姓名与共有产权人
- 关联：US-244/245/247/248（AC-244-02、AC-245-01~05、AC-247-01、AC-248-01）；环境：后端 Django test runner（SQLite 内存库、临时 MEDIA_ROOT、fakes）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 注册新用户；GET /units/options 逐级到户号 | 200，楼栋 ["1栋"]，户号含 unit_id | 与期望一致 | PASS |
| 2 | multipart 缺名字 / 缺文件 / 6 个文件 / 含 .docx | 400 NAME_REQUIRED / PROOF_REQUIRED / ATTACHMENT_LIMIT / FILE_TYPE_NOT_ALLOWED；Appeal=0、Attachment=0、磁盘文件=0 | 与期望一致 | PASS |
| 3 | multipart 完整提交（png + pdf） | 201；Appeal=1、Attachment=2、磁盘=2 | 与期望一致 | PASS |
| 4 | GET /appeals/mine；管理员 GET /admin/appeals | 本人 1 条；管理员行 owner_name=业主甲，proof=2 | 与期望一致 | PASS |
| 5 | 管理员 APPROVE；GET /me/housing | summary=OWNER；real_names=["业主甲"]；units[0].co_owners=["业主乙"]；响应不含业主乙手机号 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-1602: 授予未注册清册业主席位 → 决议公开与进度 → 注册并经手机号匹配认证自动绑定 → 投票 → 判定
- 关联：US-249/250/251/256/257/258/259（AC-256-01、AC-257-01/03/05、AC-259-06、AC-250-07、AC-249-04、AC-251-01）；环境：后端 Django test runner（SQLite 内存库、临时 MEDIA_ROOT、fakes）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 管理员 unit-options 逐级选房，owner-candidates 取候选 | 候选 [("业主甲", registered=False, seated=False)]；手机号脱敏 | 与期望一致 | PASS |
| 2 | POST /admin/committee/seats {registry_owner_id}；GET config | 201 bind_state=PENDING_BIND；half_majority_hint: denominator=4、pending_bind=1、need_agree=3、can_pass=true | 与期望一致 | PASS |
| 3 | 主任 POST /resolutions（半数同意）；游客 GET 公开列表 | 列表含该决议 status=PENDING，participation={voted:0, expected:4}，发起人 display_name=主任甲 | 与期望一致 | PASS |
| 4 | 2 位委员 AGREE；游客 GET participants 与详情 | count=2；每项键恰为 display_name/avatar_url/voted_at；participation={voted:2, expected:4} | 与期望一致 | PASS |
| 5 | 业主甲注册后尝试表决；GET /me/registry-matches；confirm | 表决 403 FORBIDDEN；pending=true；succeeded=1；/me committee.position=MEMBER；seat.user 绑定；expected 仍为 4 | 与期望一致 | PASS |
| 6 | 业主甲 AGREE；participants | count=3 | 与期望一致 | PASS |
| 7 | 截止后 run_due_jobs；游客 GET 详情 | APPROVED，result.denominator=4、agree=3；participation={voted:3, expected:4}；审计含 SEAT_GRANTED/SEAT_BOUND/RESOLUTION_DECIDED | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-1603: 冲突保持待绑定、清册改名失效、撤销待绑定后按新 N 判定
- 关联：US-257/258/259（AC-257-06、AC-258-02/03、AC-259-07）；环境：后端 Django test runner（SQLite 内存库、临时 MEDIA_ROOT、fakes）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 授予两位未注册业主甲、乙席位 | 均 PENDING_BIND，占用名额 | 与期望一致 | PASS |
| 2 | 业主甲账号已持有副主任席位后认证其专有部分 | 认证 201；甲席位 bind_state=CONFLICT，审计 SEAT_BIND_CONFLICT；既有席位不变 | 与期望一致 | PASS |
| 3 | 管理员 PUT 乙所在专有部分业主改名 | 乙席位 INVALIDATED，end_reason=REGISTRY_CHANGED | 与期望一致 | PASS |
| 4 | 主任与委员投同意；GET 详情 | participation.expected=4（含冲突待绑定席位） | 与期望一致 | PASS |
| 5 | 管理员 DELETE 冲突席位；GET 详情；截止判定 | expected=3；APPROVED，denominator=3，agree=2 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-1604: 管理员浏览清册：选项接口、默认顺序、翻页一致、表头排序、权限
- 关联：US-254/255/246（AC-254-01/02、AC-255-01/02/05）；环境：后端 Django test runner（SQLite 内存库、临时 MEDIA_ROOT、fakes）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 预置 23 套（打乱）；GET unit-options 逐级 | 楼栋 ["1栋","2栋"]；楼层按数值升序 | 与期望一致 | PASS |
| 2 | 默认列表 vs 3 页逐页汇总 | 逐页汇总 = 全量顺序，共 23 条无重复 | 与期望一致 | PASS |
| 3 | sort=floor asc/desc | 楼层数值升/降序 | 与期望一致 | PASS |
| 4 | sort=room desc 第 1 页（5 条） | 房号 ["122","121","120","119","118"]（全量最大，非仅当前页） | 与期望一致 | PASS |
| 5 | 不带 sort 再取全量；非管理员访问 | 顺序回到默认；用户令牌 403 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-1605: 身份页隐私：产权业主 / 同住人 / 他人 / 游客
- 关联：US-247/248（AC-247-04、AC-248-03）；环境：后端 Django test runner（SQLite 内存库、临时 MEDIA_ROOT、fakes）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 产权业主甲 GET /me/housing | real_names=["唯一姓名甲"]，co_owners=["唯一姓名乙"] | 与期望一致 | PASS |
| 2 | 同住人 GET /me/housing | real_names=[]；co_owners 含甲、乙全名 | 与期望一致 | PASS |
| 3 | 他人、游客 GET /me/housing | 响应中"唯一姓名"出现 0 次 | 与期望一致 | PASS |
| 4 | 他人、游客访问 registry/units、owner-candidates、unit-options | 均 403 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-1611: 申诉页：逐级选房、"55"检索、暂存 → 缺名字被拒 → 补全提交
- 关联：US-244/245/246（AC-246-01、AC-244-01/02、AC-245-02）；环境：frontend vitest + jsdom（真实页面/路由/api.js，带状态假服务端）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 逐级选到户号下拉并输入"55" | 选项 55、551、552、553、155（60 不显示）；选 552(unit_id 102) 后显示"住宅 · 89.5 ㎡" | 与期望一致 | PASS |
| 2 | 选 2 个文件 | "已选 2 份"；服务器附件上传数 0 | 与期望一致 | PASS |
| 3 | 未填名字点击提交 | 提示"请输入产权人名字"；服务器申诉 0 | 与期望一致 | PASS |
| 4 | 补名字再提交 | 服务器恰 1 条申诉 {unit_id:"102", owner_name:"业主甲", files:["a.png","b.pdf"]}；附件上传 0；提示成功；暂存清空 | 与期望一致 | PASS |
| 5 | 卸载后重新进入 | "已选 0 份" | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-1612: 公开决议列表 → 点击卡片进入详情 → 参与人
- 关联：US-249/250/251/252（AC-249-04、AC-250-01、AC-251-01、AC-252-01）；环境：frontend vitest + jsdom（真实页面/路由/api.js，带状态假服务端）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 进入 /resolutions | 2 张卡片；进行中卡片显示"进行中""已参与 4 / 7 · 57%"；已结束卡片显示"已结束" | 与期望一致 | PASS |
| 2 | 点击进行中卡片标题链接 | 路由为 /resolutions/31 | 与期望一致 | PASS |
| 3 | 详情页 | 显示标题、"已参与 4 人"与 4 位参与人昵称；无"同意/反对/弃权"个人选项；无"无权查看" | 与期望一致 | PASS |
| 4 | 返回列表 | 2 张卡片 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-1613: 左侧导航：展开 → 进入二级页选中 → 切换一级自动收起 → Esc
- 关联：US-253（AC-253-01/02/05）；环境：frontend vitest + jsdom（真实页面/路由/api.js，带状态假服务端）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 点击"我的房屋" | aria-expanded=true，二级项出现 | 与期望一致 | PASS |
| 2 | 点击"认证申诉" | 路由 /units/appeal；仅该二级项 is-active | 与期望一致 | PASS |
| 3 | 点击"决议" | "我的房屋"收起，"决议"展开（同时至多一个） | 与期望一致 | PASS |
| 4 | 在二级项上按 Esc | 二级收起，焦点回到"决议"按钮 | 与期望一致 | PASS |
- 结论：PASS

### TC-E2E-1614: 管理端清册：默认顺序 → 表头升降序 → 重置
- 关联：US-254/255（AC-254-01、AC-255-01/03/04）；环境：frontend vitest + jsdom（真实页面/路由/api.js，带状态假服务端）；假服务端为独立自然数序实现

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 进入页面 | 顺序 1栋1单元2层201、1栋1单元10层1001、1栋2单元10层1001、2栋…、10栋…（2 在 10 之前） | 与期望一致 | PASS |
| 2 | 点"楼层"两次（升→降） | 楼层列 10,10,3,2,1,1 | 与期望一致 | PASS |
| 3 | 再点一次 | 切回升序 1,1,2,3,10,10 | 与期望一致 | PASS |
| 4 | 点"房号"两次 | 首行房号 1001（降序最大） | 与期望一致 | PASS |
| 5 | 点"重置" | 回默认顺序，表头无方向指示；类型表头不可排序 | 与期望一致 | PASS |
- 结论：PASS

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| 无 | — | 本轮未发现产品缺陷 | — | — |

观察项（非缺陷，供 PM 评估）：
1. 已结束决议的结果标签 UI 文案为"通过/未通过"，AC-249-01 字面写"已通过"；需求 REQ-FUNC-244 写"保留通过/未通过结果标签"，按需求口径通过（TC-UNIT-1310）。
2. CR-012：`apps/claims/services.py:19,40` 的 `claim.decided_at.date()` 仍取 UTC 日期（不在本批授权范围，未测、未改），建议另立缺陷。
3. 手机号匹配确认路径的 `CERTIFY_BY_REGISTRY` 审计 detail 不含 `registry_owner_id`、用户 ID 授予路径的 `SEAT_GRANTED` 审计不含 `holder`（implementation_plan 已登记 [DEVIATION]）；`SEAT_BOUND` 审计含 via 与 holder，已由 TC-INT-1030~1032 断言。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-1 | AC-252-02、AC-253-02/03/06、REQ-NFUNC-047 | 在测试环境/本地构建的 Web 上，分别切换三套界面风格（neon/bento/terminal），悬停并按下公开决议、我发起的、待我表决与投票/调查卡片；展开/收起左侧"我的房屋/决议"，切换选中二级项；窄屏（<768px）切换条切换选中项 | 卡片悬停抬升+阴影、按下缩放；展开/收起平滑过渡(≤400ms)；选中项指示条出现，原选中撤销、仅 1 项；三套风格均可见、不错位、文字可读 | 桌面浏览器 + 手机宽度模拟；三套风格账号偏好 | 是（US-252、US-253 Must Have） |
| M-2 | AC-252-05、AC-253-04 | 操作系统开启"减少动态效果"后重复 M-1 的悬停、按下、展开、选中 | 无位移与过渡动画（动画数 0），点击与展开/选中功能照常 | 桌面浏览器 + 系统减少动效设置 | 是 |
| M-3 | AC-252-01、AC-252-03 | 点击决议卡片的空白处、状态标签、进度条、发起人文字（三个决议页与投票/调查页）；点击卡片内的附件链接/按钮 | 前者均进入 /resolutions/{id}（或 /polls/{id}）；附件链接/按钮只触发自身动作，不进入正文 | 桌面浏览器 | 是 |
| M-4 | AC-252-04、AC-246-05 | 键盘：Tab 聚焦卡片并按 Enter；专有部分下拉用方向键选择并回车确认 | 进入同一详情页且有可见焦点样式；下拉可键盘选中 | 桌面浏览器 | 否（辅助） |
| M-5 | AC-250-06 | 用读屏软件聚焦参与进度条 | 朗读"已参与 4 / 7，同意 3，反对 1，弃权 0"（aria-label 已由 TC-UNIT-1313 断言） | NVDA/VoiceOver | 否（辅助） |
| M-6 | AC-244-02（部署侧） | 部署后经 nginx（ocap 站点与 Freeark `^~ /ocap/` 块）真实上传 5×10MB 的申诉（FormData） | 提交成功 201；不被 413/超时拦截（client_max_body_size ≥ 55MB，gunicorn timeout 足够） | 测试环境 nginx（部署阶段，P4-1 `e2e_` 账号） | 否 |
| M-7 | 迁移 committee 0002 / residency 0005 | 在测试机 MySQL 上 `manage.py migrate` 并核对 `Seat.user` 可空、新字段与 uniq_seat_active_per_owner；演练回滚前撤销待绑定席位 | 迁移成功可逆；既有席位 user 非空不受影响 | 测试机 MySQL（部署阶段，用户授权后） | 否 |
| M-8 | AC-244-03 | 真实浏览器：选 2 个文件后刷新/关闭页面，在网络面板观察 | 全程无附件上传请求；重新进入暂存区为空 | 桌面浏览器 | 否 |
