<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-18T22:52:50+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_batch_1118/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_02</phase>
  <status>APPROVED</status>
</file_header>

# 用户故事 — ocap_profile_ux

## 角色 × 功能矩阵

| 角色 \ 功能 | 资料页 | 头像 | 席位表格 | 审批流程 | 房屋关系 | profile 页 |
|---|---|---|---|---|---|---|
| 游客（注册未认证） | — | US-261、US-263 | — | — | — | US-270 |
| 同住人 | — | US-261、US-262、US-263 | — | — | — | US-270 |
| 产权业主（已验证） | US-260 | US-261、US-262、US-263 | — | — | — | US-270、US-271、US-272 |
| 管理员 | — | US-262 | US-264、US-265 | US-266、US-267 | US-268、US-269 | US-270 |
| 业委会成员 | — | US-262 | — | US-266 | — | US-270 |

## 用户故事

### US-260: 个人资料页控件垂直对齐
- 故事：As a 注册用户, I want to 昵称、性别、生日与保存按钮在同一行对齐, so that 表单看起来整齐、不误判生日输入框是否可用
- 关联需求：REQ-FUNC-255；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-260-01：Given 用户已登录并打开个人资料页 / When 视口宽度 ≥ 768px 且页面渲染完成 / Then 昵称输入框、性别选择、生日选择、保存按钮四者的垂直中心线偏差 ≤ 2px，且四者可见高度相同
- AC-260-02：Given 已登录用户 / When 视口宽度 < 768px / Then 四个控件整行换行布局，同一行内控件底边对齐，不出现控件重叠或超出卡片边界

### US-261: 未上传头像时展示默认头像
- 故事：As a 注册用户, I want to 在未上传头像时看到默认头像, so that 界面上不会出现空白占位
- 关联需求：REQ-FUNC-256；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-261-01：Given 用户 `avatar_url` 为空 / When 打开个人资料页 / Then 头像位置展示内置默认头像图片，图片请求返回 200，替代文本为"默认头像"
- AC-261-02：Given 用户已上传头像但图片请求失败（404/网络错误）/ When 页面展示头像 / Then 回退显示内置默认头像，不出现破图图标

### US-262: 右上角昵称旁展示头像
- 故事：As a 已登录用户, I want to 在右上角自己的昵称与下拉菜单旁看到头像, so that 我能快速确认当前登录账号
- 关联需求：REQ-FUNC-256；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-262-01：Given 用户已登录 / When 页面顶部用户菜单渲染完成 / Then 昵称左侧显示 24–32px 圆形头像，头像、昵称、下拉箭头的垂直中心线偏差 ≤ 2px
- AC-262-02：Given 用户未上传头像 / When 渲染右上角用户菜单 / Then 显示内置默认头像；点击头像与点击昵称行为一致，展开同一个下拉菜单

### US-263: 头像上传上限放宽到 5 MB
- 故事：As a 产权业主, I want to 上传最大 5 MB 的头像, so that 手机相机拍摄的原图无需压缩即可使用
- 关联需求：REQ-FUNC-257、REQ-NFUNC-051；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-263-01：Given 用户选择 4.9 MB 的 png 文件 / When 点击更换头像 / Then 上传成功并提示"头像已更新"，个人资料页与右上角头像同步刷新
- AC-263-02：Given 用户选择 5.1 MB 的 png 文件 / When 选择文件 / Then 前端提示文案包含"5 MB"且不发起上传请求；绕过前端直接请求上传接口时返回 413 且错误码为 `FILE_TOO_LARGE`
- AC-263-03：Given 用户选择 .gif 或 .exe 文件 / When 选择文件 / Then 提示仅支持 jpg/png，不发起上传请求

### US-264: 席位与业主代表持有人按列展示
- 故事：As a 管理员, I want to 在席位表格中分列看到持有人的昵称、姓名、联系电话、专有部分坐落与类型, so that 无需从一行拼接文本中辨认信息
- 关联需求：REQ-FUNC-258、C-81、C-82；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-264-01：Given 管理员打开业委会席位页 / When 表格渲染完成 / Then 表头包含昵称、姓名、联系电话、专有部分坐落、专有部分类型、职位、状态、任期开始、任期结束、操作，共 10 列，且原有 5 列内容与改动前一致
- AC-264-02：Given 某席位持有人为尚未注册的清册业主 / When 查看该行 / Then 昵称列显示"-"，姓名、专有部分坐落、专有部分类型列显示其清册信息，联系电话列按脱敏规则显示（如 138****1234）
- AC-264-03：Given 某席位已绑定注册用户 / When 查看该行 / Then 昵称列显示昵称或账号（昵称为空时），专有部分信息取绑定用户的认证房产

### US-265: 席位列表过滤与失效折叠
- 故事：As a 管理员, I want to 按楼栋、单元、职位过滤并默认折叠资格失效席位, so that 默认视图只呈现当前有效的治理成员
- 关联需求：REQ-FUNC-258；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-265-01：Given 管理员打开席位页 / When 未设置任何过滤 / Then 表格仅展示状态为 ACTIVE 且处于任期内的席位；非 ACTIVE 席位收进默认折叠的"资格失效/已结束"区域，区域标题显示条数
- AC-265-02：Given 管理员展开"资格失效/已结束"区域 / When 区域展开 / Then 每个席位显示其状态文案（已撤销/已到期/资格失效/已变更/已合并）与结束原因（如有）
- AC-265-03：Given 管理员选择楼栋"1栋"、单元"1单元"、职位"主任" / When 应用过滤 / Then 表格只显示同时满足三个条件的席位；清空任一条件后对应约束解除；过滤条件变化时页码重置为第 1 页
- AC-265-04：Given 非管理员访问席位接口 / When 请求 `/admin/committee/seats` / Then 返回 403，不返回任何持有人数据

### US-266: 查看审批流程详情
- 故事：As a 管理员, I want to 展开或进入单个审批流程查看审批人与配置明细, so that 我知道每类事项由谁审批
- 关联需求：REQ-FUNC-259；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-266-01：Given 管理员打开审批流程页 / When 点击某流程的"查看详情" / Then 展示名称、适用范围、审批方式、启用状态与审批人清单（含每人昵称与身份），半数同意流程显示"无需设置审批人"
- AC-266-02：Given 非管理员 / When 请求流程详情 / Then 返回 403

### US-267: 编辑审批流程
- 故事：As a 管理员, I want to 编辑审批流程的名称、审批人与启用状态, so that 人员变动时无需删除重建流程
- 关联需求：REQ-FUNC-259；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-267-01：Given 管理员在流程详情中选择"编辑" / When 修改名称与审批人后保存 / Then 列表立即显示新名称，详情中审批人清单与新选择一致，且审计日志新增一条流程变更记录
- AC-267-02：Given 管理员把流程改为半数同意方式 / When 保存 / Then 审批人清单清空且详情显示"无需设置审批人"
- AC-267-03：Given 该流程存在待审批实例 / When 管理员尝试删除流程 / Then 系统仅停用流程（现状行为保持），不删除历史实例

### US-268: 房屋关系按楼栋/单元/楼层过滤
- 故事：As a 管理员, I want to 按专有部分的楼栋、单元、楼层过滤房屋关系, so that 我能按楼栋查看整体认证情况
- 关联需求：REQ-FUNC-260；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-268-01：Given 管理员打开用户房屋关系页 / When 依次选择楼栋"1栋"、单元"1单元"、楼层"9层" / Then 列表只显示同时满足条件的记录，且记录数与该组合的实际认证数一致
- AC-268-02：Given 已设置楼栋过滤 / When 选择单元下拉 / Then 单元选项仅包含该楼栋下存在的单元；楼层选项按数值升序排列
- AC-268-03：Given 管理员清空全部过滤条件 / When 刷新 / Then 恢复显示全部有效关系，页码回到第 1 页

### US-269: 房屋关系按姓名/电话/专有部分搜索
- 故事：As a 管理员, I want to 按姓名、电话或专有部分搜索, so that 我能快速定位某个人或某套房
- 关联需求：REQ-FUNC-260、C-82；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-269-01：Given 管理员输入业主姓名"张三" / When 执行搜索 / Then 返回该姓名关联的全部有效房屋关系（含同住人），姓名匹配为包含匹配
- AC-269-02：Given 管理员输入手机号后 4 位"1234" / When 执行搜索 / Then 返回匹配的房屋关系，结果中的电话仍按脱敏规则显示
- AC-269-03：Given 管理员输入专有部分关键字"1-1-902" / When 执行搜索 / Then 返回该专有部分对应的全部关系记录（户主与同住人）
- AC-269-04：Given 搜索词包含不存在的内容 / When 执行搜索 / Then 返回空列表并显示"暂无匹配记录"空状态，不报错

### US-270: 查看他人 profile 页
- 故事：As a 已登录用户, I want to 点击他人昵称或头像进入其 profile 页, so that 我能了解对方昵称、身份与签名
- 关联需求：REQ-FUNC-261、REQ-NFUNC-052；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-270-01：Given 用户在任意展示用户昵称或头像的位置点击该用户 / When 跳转到其 profile 页 / Then 页面展示昵称、头像（无头像时默认头像）、身份文案与签名档
- AC-270-02：Given 访问某用户 profile 页 / When 查看页面内容 / Then 页面不出现手机号、邮箱、生日、证件号等敏感字段
- AC-270-03：Given 访客未登录 / When 直接访问 profile 页地址 / Then 重定向到登录页，登录后回到该 profile 页
- AC-270-04：Given 用户查看自己的 profile 页 / When 页面加载 / Then 展示"编辑资料"入口（进入个人资料页），他人的 profile 页不显示该入口

### US-271: 产权业主控制实名展示
- 故事：As a 已验证身份的产权业主, I want to 选择是否在 profile 页显示实名, so that 我能控制个人真实姓名的可见范围
- 关联需求：REQ-FUNC-262、C-83；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-271-01：Given 已验证产权业主首次使用 / When 打开个人资料页或 profile 设置 / Then 实名展示开关默认为关闭，其 profile 页不显示真实姓名
- AC-271-02：Given 已验证产权业主打开实名展示开关 / When 他人访问其 profile 页 / Then 页面在昵称旁或身份区域显示实名，其他敏感信息仍不展示
- AC-271-03：Given 未认证用户或同住人 / When 打开个人资料设置 / Then 不显示实名展示开关，或开关置灰并提示"仅已验证产权业主可设置"
- AC-271-04：Given 产权业主关闭实名展示开关 / When 他人刷新其 profile 页 / Then 实名立即不再展示（无需重新登录）

### US-272: 编辑与展示签名档
- 故事：As a 注册用户, I want to 编辑我的签名档, so that 他人访问我的 profile 时能看到我的自我介绍
- 关联需求：REQ-FUNC-263、I-4；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-272-01：Given 用户在个人资料页输入 60 字签名并保存 / When 打开自己的 profile 页 / Then 签名档按原文展示，换行保留，70 字以上输入被截断或提示"签名档不超过 100 字"
- AC-272-02：Given 用户清空签名档并保存 / When 他人访问其 profile 页 / Then 签名区域显示"这个人很懒，什么都没写"空状态文案
- AC-272-03：Given 用户输入包含 HTML 标签或脚本的签名 / When 保存并展示 / Then 内容以纯文本转义展示，不执行脚本

## 汇总

| 优先级 | 故事数 | 故事点合计 |
|---|---|---|
| Must Have | 13 | 43 |
| Should Have | 0 | 0 |
| 合计 | 13 | 43 |
