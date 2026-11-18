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
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（ocap_batch_1118，baseline 模式）

## 摘要

- 执行时间：2026-11-18 11:29–11:42（本机，Python 3.12 + Django 5.2.19，SQLite 内存库 `config.test_settings`；前端 vitest 2.1.9 + jsdom；小程序 vitest）。
- 命令：`(cd backend && $PY manage.py test tests.unit --settings=config.test_settings)`；`(cd frontend && npx vitest run)`（全部 45 个文件，页面级用例计 unit 层）；`(cd miniprogram && npx vitest run --passWithNoTests)`。
- 本层用例（新写 + 改写）：total = pass + fail + skip + blocked + not_testable = 60 = 60 + 0 + 0 + 0 + 0（新写 53：后端 8、前端 45；改写 7）。
- 通过率 = pass/(pass+fail+blocked) = 60/(60+0+0) = 1.00。
- 全层回归：后端 `tests.unit` Ran 236 OK（基线 228 + 新写 8）；前端 45 文件 531/531（基线 482 + 新写 49，0 失败，0 Unhandled Errors）；小程序 18 文件 135/135。
- 判定模式：baseline（零新增失败 + 新写用例全部通过）。**本层门控：PASSED**。

## 执行输出

```
$ (cd backend && $PY manage.py test tests.unit --settings=config.test_settings)
Ran 236 tests in 2.508s
OK
$ (cd frontend && npx vitest run)
 Test Files  45 passed (45)
      Tests  531 passed (531)
$ (cd miniprogram && npx vitest run --passWithNoTests)
 Test Files  18 passed (18)
      Tests  135 passed (135)
```

## 分项结果

### 后端（模块：attachments / resolutions.services / registry.listing）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-1501 | AC-245-04 | jpg/jpeg/png/pdf 合格（魔数匹配）；恰 10MB 合格，10MB+1 → 413 FILE_TOO_LARGE；返回 ValidatedUpload 不落盘（无 abs_path 属性）。 | PASS | — | — |
| TC-UNIT-1502 | AC-245-04 | .docx（申诉用途不允许）、png 扩展名但内容非 png、无扩展名、未知用途 → FILE_TYPE_NOT_ALLOWED；路径穿越文件名只取 basename。 | PASS | — | — |
| TC-UNIT-1503 | AC-244-03、REQ-NFUNC-049(1) | validate_upload 不调用 open()/落盘与 Attachment.objects.create（先校验后落盘）。 | PASS | — | — |
| TC-UNIT-1510 | AC-249-04、AC-249-06 | 已通过/未通过（两种规则）公开；半数同意进行中公开；指定负责人审批中、已撤回（两种规则）不公开。 | PASS | — | — |
| TC-UNIT-1520 | AC-259-01/02/03/04 | (同意,反对,N)→结果：(3,1,5)通过；(2,2,5)未通过；(3,2,6)未通过；(4,1,6)通过；(2,0,4)未通过；记录的 denominator=N，agree/disagree/abstain 与投票一致。 | PASS | — | — |
| TC-UNIT-1521 | AC-259-03/04 | 同意恰为 N/2 不通过，N/2+1（⌊N÷2⌋+1）通过；N=0 无人可通过。 | PASS | — | — |
| TC-UNIT-1530 | AC-254-01、AC-255-01 | 默认键=楼栋/单元/楼层/房号自然顺序；指定 sort 时该列为主键、其余键仍按默认升序、id 为终极并列键；desc 保持等值项原次序。 | PASS | — | — |
| TC-UNIT-1531 | AC-254-02、NFUNC-048 | OrderedUnitPage.count()=总数，逐片取回恰为 id 序列且无重复无遗漏；越界切片为空。 | PASS | — | — |

### 前端（模块：UnitsAppeal / UnitCascader+unitSearch / UnitsIdentity / Resolutions / ParticipantList / ResolutionDetail / style.css / SideNav / AdminRegistry / AdminSeats）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-1201 | AC-244-01 | 选 2 个合格文件（jpg 与 pdf）→ 页面显示 2 个暂存文件（文件名、类型、大小、"移除"），任何 POST 请求数 = 0，不出现"已上传" | PASS | — | — |
| TC-UNIT-1202 | AC-244-03 | 已暂存 2 个文件后离开页面（卸载）再进入 → 暂存区为空；整个过程没有任何上传请求（服务器因该次选择产生的文件数 0） | PASS | — | — |
| TC-UNIT-1203 | AC-244-04 | 暂存 3 个文件，移除其中第 2 个 → 剩 2 个（顺序保持），服务器上附件新增数仍为 0 | PASS | — | — |
| TC-UNIT-1204 | AC-245-01/02/03 | 三项缺一不发请求，逐项提示——未选房屋"请选择到具体户"；名字空或全空格"请输入产权人名字"；名字超 64 字提示超长；无文件"请至少选择 1 份产权证明"；提交按钮始终可点 | PASS | — | — |
| TC-UNIT-1205 | AC-245-04 | 12MB 的 jpg 不入暂存并提示"单个文件不超过10MB"；.docx 提示"仅支持 jpg/png/pdf"；已有 5 份再选第 6 份提示"最多 5 份"；恰 10MB 合格 | PASS | — | — |
| TC-UNIT-1206 | AC-245-05 | 提交请求因网络中断失败 → 提示失败原因，已选房屋、名字与已暂存文件全部保留；修改后再次提交成功（第 2 次请求带同样的文件）并清空 | PASS | — | — |
| TC-UNIT-1207 | AC-245-06 | 服务端拒绝（409 已有待审申诉）→ 提示既有错误文案，暂存内容保留，可修改后重试；只发了 1 次请求 | PASS | — | — |
| TC-UNIT-1208 | AC-244-02、AC-245-02 | 成功提交只发 1 次 POST /appeals（FormData：unit_id=7、owner_name 已去首尾空格、files 全部），且选择阶段与提交前都没有 /attachments 请求 | PASS | — | — |
| TC-UNIT-1210 | AC-246-01/02/03 | 输入"55"→ 前缀项 55、551、552、553 排最前（原序），包含项 155 在后，60 不显示（括号里的面积 155 不误命中）；清空恢复全部；"zzz"无匹配 → 空；大小写不敏感 | PASS | — | — |
| TC-UNIT-1211 | AC-246-05 | 楼栋、单元、楼层、户号四级下拉均 filterable 且无匹配文案"无匹配项"；逐级选到户号后四个下拉都出现 | PASS | — | — |
| TC-UNIT-1212 | AC-246-01/02/03 | 户号下拉输入"55"→ 选项依次 55、551、552、553、155，60 不显示；点击 552 选中 552 并显示"住宅 · 89.5 ㎡"；清空输入恢复全部；输入"zzz"选项为空且已选结果不变、不报错 | PASS | — | — |
| TC-UNIT-1213 | AC-246-05 | 每一级输入只过滤该级候选，其他级不受影响（楼栋输入"1"→ 1、10、11 前缀项在前、2 不显示；单元级选项不变） | PASS | — | — |
| TC-UNIT-1214 | AC-246-04 | 三页（认证产权、认证申诉、我的同住人申请）使用同一 UnitCascader 且不传 fetcher；更换上一级后下一级及户号清空（update:modelValue=null）并重新加载 | PASS | — | — |
| TC-UNIT-1215 | IFC-364 | 传入 fetcher 时用 fetcher 取数（管理端 admin.unitOptions），不再调用成员端 /units/options | PASS | — | — |
| TC-UNIT-1220 | AC-247-01/02/03 | 汇总身份行显示"真实姓名：业主甲"；多个姓名用"、"连接；游客/同住人/缺失（real_names=[] 或旧响应无该字段）显示"—"，不以昵称"合成用户"代替 | PASS | — | — |
| TC-UNIT-1221 | AC-248-01/02/04/05 | 每套房屋行显示各自"共有产权人"：有则列全名（只有姓名，无手机号与"未注册"标注），无则"无"，不串行；旧响应缺字段显示"无"不报错 | PASS | — | — |
| TC-UNIT-1301 | AC-250-01 | 7 人应参与、已参与 4（同意 3、反对 1）→ 4 / 7 · 57%；着色 57%（同意≈43%、反对≈14%），留白≈43% | PASS | — | — |
| TC-UNIT-1302 | AC-250-02/03 | 全部 7 人参与 → 100%、条无留白；无人参与 → 0 / 7 · 0%、条全留白，无 NaN | PASS | — | — |
| TC-UNIT-1303 | AC-250-04 | 应参与人数为 0 → empty=true（不画条，显示"暂无表决人"），无 NaN；无 participation（旧响应）同样 empty | PASS | — | — |
| TC-UNIT-1304 | AC-250-07、AC-259-05 | 在任席位 7（含 1 待绑定），6 位可投票者均已表决（同意 4、反对 1、弃权 1）→ 6 / 7 · 86%（不是 100%），着色：同意≈57%、反对≈14%、弃权≈14%，留白≈14% | PASS | — | — |
| TC-UNIT-1305 | REQ-NFUNC-050 | 既有 voteShare 导出与返回结构不变（Home.vue 在用） | PASS | — | — |
| TC-UNIT-1310 | AC-249-01/02 | 已结束半数同意卡片显示"发起人：发起人甲 · 主任"、规则"半数同意"、"截止 2026-12-01 18:00"、"已结束"并保留"通过"结果标签（UI 既有文案为"通过/未通过"）；指定负责人无截止时间显示"指定负责人""无截止时间"，没有"截止"空白 | PASS | — | — |
| TC-UNIT-1311 | AC-249-03 | 昵称为空时接口给账号编号作 display_name，卡片显示账号编号与身份，不是空白也不是单独的"发起人" | PASS | — | — |
| TC-UNIT-1312 | AC-249-04 | 进行中的半数同意决议标"进行中"，不显示"已通过/未通过"标签 | PASS | — | — |
| TC-UNIT-1313 | AC-250-01/03/04/05/06 | 卡片进度条文案——"已参与 4 / 7 · 57%"；无人参与"已参与 0 / 7 · 0%"；应参与 0 "暂无表决人"且不画条；指定负责人"由指定负责人审批"；无障碍标签含"已参与 4 / 7，同意 3，反对 1，弃权 0" | PASS | — | — |
| TC-UNIT-1314 | AC-249-05、AC-252-01 | 公开决议、我发起的、待我表决三个路由使用同一页面组件；卡片标题是指向 /resolutions/{id} 的链接，CSS 把它拉伸为整卡点击区 | PASS | — | — |
| TC-UNIT-1315 | AC-252-03、AC-252-04 | 卡片内其他链接/按钮提升到拉伸层之上（z-index:1）不触发整卡跳转；卡片 :focus-within 有可见焦点样式；链接是原生 <a>（Tab 聚焦 + Enter 进入） | PASS | — | — |
| TC-UNIT-1316 | AC-252-06 | 投票/调查页每项含指向 /polls/{id} 的 .poll-link，CSS 同样整卡拉伸 | PASS | — | — |
| TC-UNIT-1320 | AC-251-01/02 | 3 人参与 → "已参与 3 人"与 3 行（昵称+参与时间；无头像显示默认头像占位）；页面文本不含投票选项、手机号 | PASS | — | — |
| TC-UNIT-1321 | AC-251-03/04 | 无人参与显示"暂无人参与"；指定负责人显示"无表决参与人"且不显示列表与"已参与" | PASS | — | — |
| TC-UNIT-1322 | AC-251-01/03/04、AC-249-04 | 半数同意详情调用 participants 并显示列表；参与人接口失败降级为"暂无人参与"（详情仍显示）；指定负责人不请求参与人接口，显示"无表决参与人" | PASS | — | — |
| TC-UNIT-1330 | AC-252-05、AC-253-04 | 所有 transition/animation/@keyframes 与卡片悬停位移都在 prefers-reduced-motion: no-preference 块内（"减少动效"下新增动画数 0） | PASS | — | — |
| TC-UNIT-1331 | AC-252-02、NFUNC-047 | 新增 transition/animation 单次时长均 ≤ 400ms，总错峰延迟 ≤ 360ms；JS 高度动画 ≤ 400ms | PASS | — | — |
| TC-UNIT-1332 | AC-253-02/03/06 | 选中强调与展开动效只使用主题变量（var(--accent) 等），无颜色字面量；二级项（宽屏侧栏 .side-sub-item 与窄屏切换条 .sub-nav-item）使用同类 .is-active 指示条 | PASS | — | — |
| TC-UNIT-1340 | AC-253-01 | 点击一级项"我的房屋"→ 立即展开二级项（aria-expanded=true）；二级 ul 带高度过渡（0 → 实际高度，内联 height 过渡 280ms，≤400ms），结束后清理内联样式；再次点击收起同样有过渡 | PASS | — | — |
| TC-UNIT-1341 | AC-253-04 | 系统"减少动效"开启（matchMedia reduce 命中）→ 展开/收起无高度动画（不设 transition/height 内联样式），功能照常（aria-expanded 与 DOM 存在性变化） | PASS | — | — |
| TC-UNIT-1342 | AC-253-02、AC-253-05 | 同时至多展开一个；选中二级项仅 1 个带 is-active 且 aria-current；二级项带错峰序号 --i；Esc 收起并把焦点还给一级按钮（既有行为不变） | PASS | — | — |
| TC-UNIT-1401 | AC-254-01、AC-255-04 | 初次进入（未点击表头）请求不带 sort/order（服务端默认升序）；只有楼栋、单元、楼层、房号四个表头可排序，类型/面积/业主/专有部分/操作表头不可排序 | PASS | — | — |
| TC-UNIT-1402 | AC-255-01 | 点击"楼层"表头 → 以楼层为主排序键升序请求（sort=floor&order=asc），再点 → 降序（order=desc），再点 → 切回升序；表头显示当前方向指示（ascending/descending 类） | PASS | — | — |
| TC-UNIT-1403 | AC-255-02、AC-255-03 | 房号降序后翻页与改过滤条件都保持排序（sort=room&order=desc 随请求带上，页码生效）；排序变化回到第 1 页 | PASS | — | — |
| TC-UNIT-1404 | AC-255-03 | 点击"重置"→ 清除过滤与排序（请求不再带 sort/order，即默认升序），表头指示清除 | PASS | — | — |
| TC-UNIT-1405 | IFC-361 | sort-change 取消排序（order=null）→ 不带 sort/order；四列 prop 恰为后端白名单 building/unit_no/floor/room | PASS | — | — |
| TC-UNIT-1410 | AC-258-01/04 | 第 1 行显示昵称（#id），第 2 行显示"1栋1单元9层902号 · 业主乙"+"待绑定"，冲突行显示"待处理冲突"；页面不出现手机号明文 | PASS | — | — |
| TC-UNIT-1411 | AC-258-02 | 待绑定席位与已绑定席位一样提供"变更为"与"撤销"，撤销确认框用清册业主姓名，成功后 DELETE /admin/committee/seats/{id} | PASS | — | — |
| TC-UNIT-1412 | Q-B18-33、AC-259 | config.half_majority_hint 的 pending_bind>0 时顶部提示"当前待绑定 2 人，半数同意决议至少需 3 票同意"；can_pass=false 另提示"当前半数同意决议无法通过"；仅提示不禁用任何按钮；pending_bind=0 不提示 | PASS | — | — |

### 改写的既有 unit 用例（REWORK_AUTHORIZED，旧断言 → 新断言见 test_plan"REWORK 改写清单"）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-541 (F8) | AC-256-01/02 | 赋予席位对话框改为逐级选房+选清册业主，提交 registry_owner_id（product_review_ui.spec.js） | PASS | — | — |
| TC-UNIT-669 (F4) | AC-245-01 | 未选房屋提交按钮可点并提示"请选择到具体户"（owner_auth_v2.spec.js） | PASS | — | — |
| TC-UNIT-670 (F5) | AC-245-03 | 提示改为"请至少选择 1 份产权证明"，不发请求（owner_auth_v2.spec.js） | PASS | — | — |
| TC-UNIT-671 (F6) | AC-244-01/02 | 选文件只暂存，一次 POST /appeals(FormData)（owner_auth_v2.spec.js） | PASS | — | — |
| TC-UNIT-672 (F7) | AC-245-04 | 第 6 份提示"最多 5 份"，选择阶段 0 请求（owner_auth_v2.spec.js） | PASS | — | — |
| TC-UNIT-865 (F3) | AC-252-05/AC-253-04 | @media 宽度条件仍只有 768px 一对，另放行 prefers-reduced-motion: no-preference（layout_css.spec.js） | PASS | — | — |
| 决议卡片三段比例 (F9) | AC-250-01、AC-249-01 | 条宽分母改为 participation.expected，断言"已参与 10 / 20 · 50%"与"进行中"（ui_blocks.spec.js） | PASS | — | — |

## 与基线对比（baseline 模式）

| 失败项 | 基线（GROUP_C 自验证 HEAD c3a10ce+改动） | 本次 | 结论 |
|---|---|---|---|
| 前端 F3/F4~F7/F8/F9（TC-UNIT-865、669~672、541、ui_blocks 卡片） | 7 条失败 + 8 个 Unhandled Errors | 全部通过，0 Errors | 已按新行为改写（预期失败，有意的行为变更） |
| 其余前端 | 通过 | 通过 | 无新增失败 |
| 后端 unit | 通过 | 通过 | 无新增失败 |
| 小程序 | 135/135 | 135/135 | 无新增失败 |

新增失败：0。

## 失败汇总（需路由给开发）

无。观察项（非缺陷）：卡片"已结束"决议的结果标签沿用既有文案"通过/未通过"，AC-249-01 字面写"已通过"，需求 REQ-FUNC-244 写"保留通过/未通过结果标签"，按需求口径测试（TC-UNIT-1310）。
