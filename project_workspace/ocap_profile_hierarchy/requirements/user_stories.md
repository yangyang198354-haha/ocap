<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-21T11:38:05+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_hierarchy/requirements/requirements_spec.md</file>
  </input_files>
  <phase>PHASE_02</phase>
  <status>APPROVED</status>
</file_header>

# 用户故事：个人主页信息层级与实名认证徽章

## 角色 × 功能矩阵

| 角色 | 查看他人主页（Web） | 查看本人“我的”页（小程序） | 实名徽章 |
|---|---|---|---|
| 已登录成员（访客/同住人） | US-273、US-275 | — | US-274 |
| 产权业主（已开启实名） | US-273、US-274、US-275 | US-276 | US-274、US-276 |
| 产权业主（未开启实名）/ 游客 | US-273、US-275 | US-276 | — |

## 用户故事

### US-273: Web 个人主页先展示昵称与实名，再展示身份
- 故事：As a 已登录成员, I want to 在他人个人主页先看到昵称/实名再看到身份标记, so that 我能先确认这个人是谁，再了解其组织身份
- 关联需求：REQ-FUNC-264、REQ-FUNC-267；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-273-01：Given 某产权业主已开启实名（昵称“张三”、实名“杨扬”、身份“业委会主任”）/ When 成员打开该用户个人主页 / Then 主信息区中昵称文本排在实名文本之前、实名文本排在身份标记之前，且身份标记是三者中最后出现的元素
- AC-273-02：Given 某用户未开启实名（`real_name` 为 null）/ When 成员打开其个人主页 / Then 页面只显示昵称与身份标记，昵称仍排在身份标记之前，且不出现实名文本
- AC-273-03：Given 某用户昵称为空 / When 成员打开其个人主页 / Then 显示“未设置昵称”占位，且该占位仍排在身份标记之前，顺序与有昵称时一致

### US-274: 实名展示时附带实名认证徽章
- 故事：As a 已登录成员, I want to 在实名旁看到认证徽章, so that 我能区分“已认证的实名”和普通昵称
- 关联需求：REQ-FUNC-265；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-274-01：Given 某用户实名可见且实名文本已展示 / When 打开其个人主页 / Then 实名文本所在容器内存在一个包含“实名”字样的徽章元素，且徽章与实名文本相邻（同一容器内、中间无其他身份标记）
- AC-274-02：Given 某用户未开启实名或没有实名 / When 打开其个人主页 / Then 页面不存在实名认证徽章，也不存在“实名：”文本

### US-275: 身份标记与实名/昵称在颜色和字体上可区分
- 故事：As a 已登录成员, I want to 一眼区分实名信息与身份标记, so that 我不会把组织职务误认为实名
- 关联需求：REQ-FUNC-266；优先级：Must Have；故事点：2 [ESTIMATE]
- AC-275-01：Given 个人主页同时展示实名徽章与身份标记 / When 渲染完成 / Then 两者计算样式的文字颜色值不同，且字重或字号至少有一项不同
- AC-275-02：Given 个人主页只有身份标记、没有实名 / When 渲染完成 / Then 身份标记仍使用身份专属样式（颜色/字体不随昵称主标题样式变化），且与昵称标题的颜色或字体至少一项不同

### US-276: 小程序“我的”页采用相同信息层级与实名徽章
- 故事：As a 已开启实名的产权业主, I want to 在小程序“我的”页先看到昵称/实名并看到认证徽章, so that 小程序与 Web 的个人信息展示保持一致
- 关联需求：REQ-FUNC-268；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-276-01：Given 某产权业主已开启实名且实名可见 / When 打开小程序“我的”页 / Then 文本顺序为昵称 → 实名 → 身份标记，且实名文本旁存在包含“实名”字样的认证徽章
- AC-276-02：Given 游客或未开启实名的用户 / When 打开小程序“我的”页 / Then 不显示实名文本与认证徽章，仍显示昵称与身份标记，且昵称排在身份标记之前
- AC-276-03：Given 实名数据获取失败 / When 打开小程序“我的”页 / Then 不展示实名文本与认证徽章，昵称与身份标记仍正常展示，页面不出现错误弹窗

## 汇总

| 优先级 | 故事数 | 故事点合计 |
|---|---|---|
| Must Have | 4 | 10 |
| Should Have | 0 | 0 |
| Could Have | 0 | 0 |
