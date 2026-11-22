<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-22T09:39:02+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>project_workspace/ocap_appeal_center/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap/requirements/user_stories.md</file>
    <file>project_workspace/ocap_batch_1118/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_01,PHASE_02</phase>
  <status>APPROVED</status>
</file_header>

# 用户故事 — 申诉与同住人申请记录中心（Web 用户端）

## 角色 × 功能矩阵

| 角色 | 申诉入口与记录 | 申诉撤回与重提 | 同住申请入口与记录 | 同住申请实名 | 身份页实名 | 管理端备注 |
|---|---|---|---|---|---|---|
| 注册用户（游客/同住人/产权业主均可） | US-291、US-292、US-293 | US-294 | US-295、US-296 | US-297 | US-298 | — |
| 产权业主（审批同住申请） | — | — | US-296 | US-297 | US-298 | — |
| 管理员（后台审核申诉） | — | — | — | — | — | US-293 |

## 用户故事

### US-291: 申诉入口合并为双 Tab
- 故事：As a 已登录用户, I want to 从同一个"申诉"二级菜单进入，用两个 Tab 分别在"认证申诉"和"我的申诉"之间切换, so that 不用在两个菜单项之间来回跳转。
- 关联需求：REQ-FUNC-289；优先级：Must Have；故事点：3 [ESTIMATE]
- 依赖：无。
- AC-291-01：Given 用户已登录并打开左侧"我的房屋"二级菜单，When 查看菜单项，Then 只出现一个"认证申诉"入口，且不再单独出现"我的申诉"菜单项；点击后默认显示"认证申诉"Tab。
- AC-291-02：Given 用户在"认证申诉"Tab 已选择房屋、填写产权人姓名并选择了 2 份证明，When 切换到"我的申诉"Tab 再切回，Then 已选房屋、姓名与 2 份证明仍在，未被清空。
- AC-291-03：Given 用户直接访问旧地址 `/units/appeals`，When 页面加载完成，Then 仍进入申诉页并自动选中"我的申诉"Tab。

### US-292: 查看我的申诉记录
- 故事：As a 已登录用户, I want to 在"我的申诉"Tab 看到自己提交过的全部申诉及各自进度, so that 我能确认哪些还在处理、哪些已经结束。
- 关联需求：REQ-FUNC-290；优先级：Must Have；故事点：3 [ESTIMATE]
- 依赖：US-291。
- AC-292-01：Given 用户有 2 条待审、1 条已通过的申诉，When 打开"我的申诉"Tab，Then 按提交时间倒序显示 3 条记录，每条包含专有部分、状态标签、提交时间；已通过记录额外显示处理时间。
- AC-292-02：Given 用户从未提交过申诉，When 打开"我的申诉"Tab，Then 显示"暂无申诉"空状态文案，且不显示空表格骨架或报错。
- AC-292-03：Given 用户历史申诉超过 100 条，When 打开"我的申诉"Tab，Then 只显示最近 100 条，页面不卡顿、不报错。

### US-293: 查看处理结果与管理员备注
- 故事：As a 提交过申诉的用户, I want to 在已处理申诉上看到通过/驳回结果、管理员备注与驳回原因, so that 我明白为什么被拒以及下一步怎么做。
- 关联需求：REQ-FUNC-291、REQ-NFUNC-059、REQ-NFUNC-060；优先级：Must Have；故事点：5 [ESTIMATE]
- 依赖：US-292；管理端审核入口（现有 `/admin/appeals`）。
- AC-293-01：Given 管理员以"通过"处理某申诉并填写备注"资料齐全"，When 用户在"我的申诉"Tab 查看该记录，Then 显示结果"通过"与备注"资料齐全"。
- AC-293-02：Given 管理员以"驳回"处理申诉，填写原因"产权证明不清晰"且备注"请补充整页照片", When 用户查看该记录，Then 同时显示驳回原因"产权证明不清晰"与备注"请补充整页照片"。
- AC-293-03：Given 已处理申诉的处理备注为空（含历史数据），When 用户查看该记录，Then 备注位置显示"—"且页面不报错。
- AC-293-04：Given 管理员在审核对话框输入 501 字备注，When 点击确认，Then 提示备注不超过 500 字且不提交处理结果。

### US-294: 撤回待审申诉并重新提交
- 故事：As a 申诉仍在待审的用户, I want to 撤回申诉、修改房屋/姓名/证明后重新提交, so that 我能纠正填错的信息而不用等待被驳回。
- 关联需求：REQ-FUNC-292、REQ-NFUNC-059、C-359、C-360；优先级：Must Have；故事点：5 [ESTIMATE]
- 依赖：US-292。
- AC-294-01：Given 某条申诉状态为"待审"，When 用户打开该记录的撤回操作并确认，Then 该记录状态变为"已撤回"，列表保留该记录，且撤回按钮消失。
- AC-294-02：Given 用户已撤回同一专有部分的申诉，When 再次提交该专有部分的新申诉，Then 提交成功（不再提示"该专有部分已有待审申诉"）。
- AC-294-03：Given 用户撤回后选择"重新提交"，When 修改产权人姓名并上传 1 份新证明后提交，Then 生成一条新的待审申诉，新记录标注"重新提交自 #{原记录编号}"，原记录仍为"已撤回"且可查。
- AC-294-04：Given 某条申诉状态为"通过"或"驳回"，When 用户查看该记录，Then 不显示撤回与重新提交操作。

### US-295: 同住人申请页拆分为双 Tab
- 故事：As a 想申请成为同住人的用户, I want to 在"发起申请"和"申请记录"两个 Tab 之间切换, so that 申请入口与历史记录互不干扰。
- 关联需求：REQ-FUNC-293；优先级：Must Have；故事点：2 [ESTIMATE]
- 依赖：无。
- AC-295-01：Given 用户已登录并进入"我的同住人申请"，When 页面打开，Then 显示"发起申请"与"申请记录"两个 Tab，默认选中"发起申请"。
- AC-295-02：Given 用户在"发起申请"Tab 已选择房屋，When 切换到"申请记录"Tab 再切回，Then 已选房屋仍保留。
- AC-295-03：Given 用户点击"提交申请"，When 提交成功，Then 页面自动切换到"申请记录"Tab，且新记录以"待审"状态出现在列表首位。

### US-296: 查看同住申请记录并撤回重提
- 故事：As a 提交过同住人申请的用户, I want to 查看全部申请记录、处理结果与审批人备注，并在待审时撤回重提, so that 我能跟踪申请进度并及时纠正信息。
- 关联需求：REQ-FUNC-294、REQ-NFUNC-059、REQ-NFUNC-060、C-359、C-360；优先级：Must Have；故事点：5 [ESTIMATE]
- 依赖：US-295、US-297。
- AC-296-01：Given 用户有 1 条待审、1 条已驳回的同住申请，When 打开"申请记录"Tab，Then 按提交时间倒序显示 2 条记录，字段与"我的申诉"一致（专有部分、状态、提交/处理时间），驳回记录显示驳回原因与审批人备注。
- AC-296-02：Given 某条同住申请为"待审"，When 用户撤回并确认，Then 状态变为"已撤回"，撤回按钮消失；同一房屋可再次提交新申请。
- AC-296-03：Given 已撤回申请选择"重新提交"，When 修改本人实名与房屋后提交，Then 生成新的待审申请且关联原记录，原记录保持"已撤回"。
- AC-296-04：Given 用户没有任何同住申请，When 打开"申请记录"Tab，Then 显示"暂无同住人申请"空状态文案。

### US-297: 同住人申请填写本人实名
- 故事：As a 申请成为同住人的用户, I want to 填写本人实名并让它随申请一起提交, so that 产权业主能确认申请人真实身份。
- 关联需求：REQ-FUNC-295、REQ-NFUNC-060；优先级：Must Have；故事点：3 [ESTIMATE]
- 依赖：US-295。
- AC-297-01：Given 用户在"发起申请"Tab 已选择房屋但未填写实名，When 点击"提交申请"，Then 提示请输入本人实名且不发起提交。
- AC-297-02：Given 用户填写 65 字实名，When 点击提交，Then 提示实名不超过 64 字且不发起提交。
- AC-297-03：Given 用户填写实名"张三"并提交，When 产权业主打开待审列表，Then 该申请显示申请人实名"张三"（同时保留账号信息）。
- AC-297-04：Given 历史同住申请无实名数据，When 产权业主查看该申请，Then 实名位置显示"—"且页面不报错。

### US-298: 身份与房屋页展示同住人实名
- 故事：As a 用户, I want to 在"我的身份与房屋"看到自己或同住人的实名, so that 房屋成员身份清晰可核对。
- 关联需求：REQ-FUNC-296、REQ-NFUNC-060；优先级：Must Have；故事点：3 [ESTIMATE]
- 依赖：US-297（同住申请实名数据）。
- AC-298-01：Given 用户以同住人身份通过申请加入某房屋，When 打开"我的身份与房屋"，Then 该房屋一栏显示身份"同住人"且显示本人实名。
- AC-298-02：Given 产权业主打开"我的身份与房屋"并展开某房屋的同住人列表，When 同住人存在实名，Then 每位同住人显示实名、昵称/账号与加入时间。
- AC-298-03：Given 某同住人无实名（历史数据），When 业主查看同住人列表，Then 实名位置显示"—"，其余信息正常展示。
- AC-298-04：Given 用户没有任何已认证房屋，When 打开"我的身份与房屋"，Then 显示"暂无已认证房屋"，且不因无实名数据报错。

## 汇总

| 优先级 | 故事数 | 故事点合计 |
|---|---|---|
| Must Have | 8 | 29 |
| Should Have | 0 | 0 |
| Could Have | 0 | 0 |
| 合计 | 8 | 29 |
