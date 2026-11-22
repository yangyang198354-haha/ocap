<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-22T11:47:18+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap/requirements/user_stories.md</file>
    <file>project_workspace/ocap_appeal_center/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_01,PHASE_02</phase>
  <status>APPROVED</status>
</file_header>

# 用户故事：导航信息架构整合（Web + 微信小程序）

> 批次：ocap_navigation_ia。本文件为待用户确认草稿（0.1.0/DRAFT）。
> 故事点采用 Fibonacci 相对估算，标 `[ESTIMATE]`，不作为工期承诺。

## 角色 × 功能矩阵

| 角色 | 侧栏菜单 | 身份页 Tab | 认证与申述 | 同住申请 | 下拉菜单 | 小程序导航 |
|---|---|---|---|---|---|---|
| 注册用户（游客） | US-299 | US-300 | US-299 | US-301 | US-302、US-303 | US-304、US-305 |
| 产权业主 | US-299 | US-300、US-307 | US-299 | US-301 | US-302、US-303 | US-304、US-305 |
| 同住人 | US-299 | US-300 | US-299 | US-301 | US-302、US-303 | US-304、US-305 |
| 未登录访客 | — | — | — | — | — | — |

> 说明：本批次为导航与展示层调整，所有注册用户（含游客、产权业主、同住人）看到的菜单结构一致；差异仅在"待我审批"Tab 仅产权业主可见（REQ-FUNC-302）。

## 用户故事

### US-299: Web 侧栏"我的房屋"二级菜单收敛与改名

- 故事：As a 注册用户, I want to 在"我的房屋"下只看到"我的身份与房屋、我的认证与申述、我的同住人申请"三个二级项, so that 我能按身份、申诉、同住申请三类快速找到入口，不再被重复入口干扰
- 关联需求：REQ-FUNC-297、REQ-FUNC-298、REQ-FUNC-299、REQ-FUNC-300、REQ-FUNC-303、REQ-FUNC-304；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-299-01：Given 已登录用户在宽屏 Web 端，When 展开侧栏"我的房屋"一级菜单，Then 自上而下依次显示"我的身份与房屋""我的认证与申述""我的同住人申请"三项，且不显示"认证申诉""认证产权""我的申诉"作为二级项
- AC-299-02：Given 用户直接访问旧地址 `/units/appeal`，When 页面渲染完成，Then 落在"我的认证与申述"页，"我的房屋"一级保持展开且"我的认证与申述"处于高亮，页面标题显示"我的认证与申述"
- AC-299-03：Given 用户从"我的身份与房屋"页点击页面内的申诉按钮，When 跳转完成，Then 进入"我的认证与申述"页并默认选中"认证申诉"Tab，不出现 404
- AC-299-04：Given 用户切换窗口宽度由宽变窄，When 窄屏导航切换条渲染，Then 其二级项名称与顺序与宽屏侧栏完全一致，均为上述三项

### US-300: "我的身份与房屋"页将待审批改为页内 Tab

- 故事：As a 产权业主, I want to 在"我的身份与房屋"页内用 Tab 查看待我审批的同住人申请, so that 不必向下滚动寻找底部卡片，审批入口与房屋信息在同一视线范围内
- 关联需求：REQ-FUNC-301、REQ-FUNC-302；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-300-01：Given 产权业主已登录，When 进入"我的身份与房屋"页，Then 页面顶部显示两个 Tab："我的身份与房屋"（默认选中）与"待我审批的同住人申请"；页面正文中不再出现独立的"待我审批的同住人申请"卡片
- AC-300-02：Given 该产权业主有 2 条待审批申请，When 页面加载完成，Then 第二个 Tab 标题旁显示数量 2；点击该 Tab 后显示 2 条记录，每条包含申请人、房屋、提交时间与"通过""拒绝"按钮
- AC-300-03：Given 当前用户不是任何房屋的产权业主，When 进入"我的身份与房屋"页，Then 不显示"待我审批的同住人申请"Tab，且默认 Tab 内容正常显示
- AC-300-04：Given 产权业主没有待审批申请，When 切换到"待我审批的同住人申请"Tab，Then 显示文案"暂无待审批的同住人申请"，Tab 标题不显示数量角标

### US-301: 保持"我的同住人申请"入口与双 Tab

- 故事：As a 注册用户, I want to 从"我的房屋"第三项进入同住人申请并区分发起与记录, so that 我能继续提交申请并查看进度
- 关联需求：REQ-FUNC-303；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-301-01：Given 用户已登录，When 展开"我的房屋"，Then 第三项为"我的同住人申请"；点击后进入 `/units/applications`，页面包含"发起申请""申请记录"两个 Tab
- AC-301-02：Given 用户位于 `/units/applications`，When 页面加载完成，Then 侧栏"我的同住人申请"处于高亮，其他二级项不高亮

### US-302: 右上角下拉菜单按"个人设置/系统设置"分组

- 故事：As a 注册用户, I want to 在右上角菜单中按个人设置和系统设置两组查找功能, so that 我能更快定位账号相关与界面相关选项
- 关联需求：REQ-FUNC-305、REQ-FUNC-306、REQ-FUNC-307、REQ-FUNC-308、REQ-FUNC-309、REQ-FUNC-310；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-302-01：Given 已登录用户点击右上角昵称，When 下拉菜单展开，Then 显示两个带标题的分组：第一组"个人设置"，条目顺序为"个人资料→绑定手机→设置密码→邮箱验证→账号注销"；第二组"系统设置"，仅含"界面风格"
- AC-302-02：Given 下拉菜单已展开，When 查看菜单条目，Then 菜单中不出现"手机号"与"我的身份与房屋"两项文案；点击"绑定手机"进入 `/me/phone`，页面标题显示"绑定手机"
- AC-302-03：Given 下拉菜单已展开，When 用户点击"界面风格"，Then 进入 `/me/style`，且该入口位于"系统设置"分组内
- AC-302-04：Given 下拉菜单已展开，When 用户分别点击"个人资料""邮箱验证""账号注销"，Then 依次进入 `/me/profile`、`/me/email`、`/me/cancel`，三项目标地址与调整前一致

### US-303: 退出登录位置保持不变

- 故事：As a 注册用户, I want to 在菜单最底部找到退出登录, so that 不会因菜单分组而找不到退出入口
- 关联需求：REQ-FUNC-311；优先级：Must Have；故事点：1 [ESTIMATE]
- AC-303-01：Given 下拉菜单已展开，When 查看菜单底部，Then "退出登录"显示在两个分组之后的最底部，并与上方分组之间有分隔线
- AC-303-02：Given 下拉菜单已展开，When 用户点击"退出登录"，Then 本地会话被清除并跳转到登录页，返回上一页不能恢复登录态

### US-304: 小程序"我的房屋"页改为三个 Tab

- 故事：As a 小程序用户, I want to 在"我的房屋"页用三个 Tab 分别查看身份房屋、认证申述与同住申请, so that 页面结构清晰、无需长距离滚动
- 关联需求：REQ-FUNC-312；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-304-01：Given 用户已登录小程序，When 进入"我的房屋"页，Then 顶部显示三个 Tab："我的身份与房屋""我的认证与申述""我的同住人申请"，默认选中第一个
- AC-304-02：Given 用户在小程序"我的房屋"页，When 切换到"我的认证与申述"，Then 页面显示"认证申诉""我的申诉"两个子 Tab；在"认证申诉"提交成功后自动切到"我的申诉"并可看到新记录
- AC-304-03：Given 用户处于小程序"我的房屋"页，When 切换到"我的身份与房屋"且该用户为产权业主，Then 页面内显示"待我审批"子 Tab，可查看并通过/拒绝申请；非产权业主看不到该子 Tab
- AC-304-04：Given 用户处于小程序"我的房屋"页，When 切换到"我的同住人申请"，Then 显示发起申请与申请记录两部分，提交后记录出现在申请记录中

### US-305: 小程序"我的"页按两组重构

- 故事：As a 小程序用户, I want to 在"我的"页按个人设置和系统设置两组查看入口, so that 与 Web 端的菜单逻辑保持一致
- 关联需求：REQ-FUNC-313；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-305-01：Given 用户已登录小程序，When 进入"我的"页，Then 显示"个人设置"分组（个人资料、绑定手机、邮箱验证、账号注销）与"系统设置"分组（界面风格），两组标题可见
- AC-305-02：Given 用户在小程序"我的"页，When 点击"绑定手机"，Then 进入手机号页，页面标题与入口文案均为"绑定手机"
- AC-305-03：Given 用户未绑定手机，When 查看"个人设置"分组，Then 入口仍显示"绑定手机"，不改成"更换手机号"
- AC-305-04：Given 用户在小程序"我的"页，When 点击"界面风格"，Then 进入主题选择区域并可切换主题，切换即时生效

### US-306: 旧地址与页面刷新兼容

- 故事：As a 注册用户, I want to 继续用旧链接或刷新当前页进入对应功能, so that 书签与历史链接不会失效
- 关联需求：REQ-FUNC-314；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-306-01：Given 用户已登录，When 在地址栏输入 `/units/appeal` 或 `/units/appeals`，Then 落到"我的认证与申述"页，分别默认选中"认证申诉""我的申诉"Tab，均不出现 404
- AC-306-02：Given 产权业主已登录，When 输入 `/units/review` 并加载完成，Then 落到"我的身份与房屋"页并选中"待我审批的同住人申请"Tab；非产权业主访问同一地址时停在默认 Tab，页面不报错
- AC-306-03：Given 用户已登录，When 输入 `/me/identity` 并加载完成，Then 显示"我的身份与房屋"页，侧栏"我的房屋"展开且对应项高亮
- AC-306-04：Given 用户位于任一菜单目标页，When 按 F5 刷新，Then 页面正常渲染且菜单高亮与刷新前一致

### US-307: 待审批角标与 Tab 数量一致

- 故事：As a 产权业主, I want to 侧栏角标与页内 Tab 显示相同的待办数量, so that 我知道还剩多少申请要处理
- 关联需求：REQ-FUNC-315；优先级：Should Have；故事点：2 [ESTIMATE]
- AC-307-01：Given 产权业主有 3 条待审批申请，When 页面加载完成，Then 侧栏"我的身份与房屋"显示角标 3，页内"待我审批的同住人申请"Tab 标题显示数量 3
- AC-307-02：Given 用户在 Tab 内通过 1 条申请，When 操作成功，Then 侧栏角标与 Tab 数量同时变为 2，无需手动刷新整页

### US-308: 下拉菜单动效放慢到可感知

- 故事：As a 注册用户, I want to 下拉菜单展开和收起有清晰但不拖沓的过渡, so that 菜单不会瞬间闪现、点错条目
- 关联需求：REQ-NFUNC-061；优先级：Should Have；故事点：2 [ESTIMATE]
- AC-308-01：Given 系统未开启"减少动效"，When 用户点击昵称展开菜单，Then 展开过渡时长在 350~500ms 之间（建议 400ms），可见渐入或下滑过程，不出现单帧闪现
- AC-308-02：Given 系统未开启"减少动效"，When 用户将鼠标悬停在昵称上，Then 停留 150~200ms 后才展开；移开鼠标后菜单在 350~500ms 内收起
- AC-308-03：Given 系统开启"减少动效"，When 用户展开或收起菜单，Then 菜单立即显示或隐藏，不执行过渡动画

### US-309: Web 与小程序菜单文案一致

- 故事：As a 注册用户, I want to 在 Web 与小程序看到同一套菜单名称, so that 切换端时不需要重新理解入口含义
- 关联需求：REQ-NFUNC-062；优先级：Must Have；故事点：1 [ESTIMATE]
- AC-309-01：Given Web 与小程序均已更新，When 对比两端菜单，Then 功能名称与 C-363 完全一致，包括"我的身份与房屋""我的认证与申述""我的同住人申请""个人设置""系统设置""绑定手机"
- AC-309-02：Given 任一端将"认证申诉"用作一级或二级菜单文案，When 检查菜单文案，Then 判定不符合；"认证申诉"只允许作为"我的认证与申述"页内的 Tab 名称

### US-310: 信息架构调整不丢失既有入口

- 故事：As a 注册用户, I want to 在调整后的结构里仍能找到原有的全部功能, so that 改版不影响我办理业务
- 关联需求：REQ-NFUNC-063；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-310-01：Given 用户从新菜单出发，When 逐项查找功能入口，Then 个人资料编辑、绑定手机、设置密码、邮箱验证、账号注销、界面风格、申诉提交、我的申诉、同住申请、待我审批十项功能均可在不超过两次点击内到达
- AC-310-02：Given 用户正在某个二级页面，When 窗口由宽屏切到窄屏或反向切换，Then 当前页面不跳转丢失，导航自动展开对应一级并高亮当前项
- AC-310-03：Given 用户以游客身份登录，When 查看菜单，Then 三类二级菜单与下拉菜单入口均可见，仅"待我审批"Tab 与需要产权业主权限的操作不显示或被拒绝

## 汇总

| 优先级 | 故事数 | 故事点合计 |
|---|---|---|
| Must Have | 10 | 27 |
| Should Have | 2 | 4 |
| 合计 | 12 | 31 |
