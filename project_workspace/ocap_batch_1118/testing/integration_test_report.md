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
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（ocap_batch_1118，baseline 模式）

## 摘要

- 执行时间：2026-11-18 11:29–11:42（同单元层环境）。上一层（单元）门控 PASSED，故执行集成。
- 命令：`(cd backend && $PY manage.py test tests.integration --settings=config.test_settings)`；契约用例亦随前端 `npx vitest run` 执行。
- 本层用例（新写 + 改写）：total = pass + fail + skip + blocked + not_testable = 90 = 90 + 0 + 0 + 0 + 0（新写 81；改写 9：B1~B7 + F1/F2）。
- 通过率 = pass/(pass+fail+blocked) = 90/(90+0+0) = 1.00。
- 全层回归：后端 `tests.integration` Ran 806 OK（基线 725 + 新写 81）；既有时段相关用例 TC-INT-504 通过，并在冻结"北京时间 2026-11-18 00:30"下复跑 OK（变异回退 `now.date()` 后 FAIL：`'ACTIVE' != 'EXPIRED'`）。
- 契约（画像 P5、M-PM-002）：新增/改动的 api.js 调用（`POST /appeals`(FormData)、`GET /resolutions/{id}/participants`、`GET /admin/registry/unit-options`、`GET /admin/committee/owner-candidates`、`GET /admin/registry/units?sort&order`）经 TC-INT-1130 resolve 到路由并核对视图方法与权限类；字段级契约 TC-INT-1131~1134；既有 `test_frontend_contract.py` 全部路由解析用例通过（含新增调用）。
- 判定模式：baseline。**本层门控：PASSED**。

## 执行输出

```
$ (cd backend && $PY manage.py test tests.integration --settings=config.test_settings)
Ran 806 tests in 60.721s
OK
$ (cd backend && $PY manage.py check --settings=config.test_settings)
System check identified no issues (0 silenced).
$ (cd backend && $PY manage.py makemigrations --check --dry-run --settings=config.test_settings)
No changes detected
```

## 分项结果

集成边界：申诉 API ↔ attachments/磁盘（BA）；席位 ↔ registry/residency 认证三入口 ↔ 审计（BS）；决议 ↔ committee 分母口径（BR）；身份页 ↔ registry/residency（BH）；前端 api.js/页面 ↔ 后端路由（BC）；jobs ↔ 本地日期（BT）。

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-1001 | AC-244-02 | 一次 multipart 提交 → 201，新增 1 条申诉、2 个附件均 LINKED 到该申诉，磁盘 2 个文件，owner_name 已去空格。 | PASS | — | — |
| TC-INT-1002 | REQ-NFUNC-050 | 小程序 JSON 分支（先 /attachments 上传再 proof_ids 提交）行为不变，201 且附件关联到申诉。 | PASS | — | — |
| TC-INT-1003 | AC-245-01 | 未登录提交 → 401，无记录无文件。 | PASS | — | — |
| TC-INT-1004 | AC-245-01 | 缺专有部分（缺 unit_id 与非整数）→ 400 INVALID_VALUE；不存在的专有部分 → 404；申诉 0、附件 0、磁盘 0。 | PASS | — | — |
| TC-INT-1005 | AC-245-02 | 缺名字、全空格 → 400 NAME_REQUIRED；65 字 → 400 INVALID_VALUE；边界 64 字成功；失败时无残留。 | PASS | — | — |
| TC-INT-1006 | AC-245-03 | 未带任何文件 → 400 PROOF_REQUIRED；无记录。 | PASS | — | — |
| TC-INT-1007 | AC-245-04 | 6 个文件 → 400 ATTACHMENT_LIMIT；无残留；恰 5 个成功并关联 5 个附件。 | PASS | — | — |
| TC-INT-1008 | AC-245-04 | 含 1 个 10MB+1 字节的 png → 413 FILE_TOO_LARGE；含 .docx → 400 FILE_TYPE_NOT_ALLOWED； | PASS | — | — |
| TC-INT-1009 | AC-245-06 | 已有本人本专有部分待审申诉时再提交 → 409 APPEAL_PENDING，附件、申诉、磁盘文件新增数 = 0。 | PASS | — | — |
| TC-INT-1010 | AC-245-06（边界） | 已是该专有部分产权业主 → 409 ALREADY_CERTIFIED，无残留。 | PASS | — | — |
| TC-INT-1011 | AC-245-05、REQ-NFUNC-049(1) | 第 2 个文件落盘时异常 → 事务回滚，已落盘的第 1 个文件被清理：Appeal=0、Attachment=0、磁盘文件=0（不出现"有文件无申诉"）；之后用户修改重提成功。 | PASS | — | — |
| TC-INT-1020 | AC-256-01、AC-258-04 | 授予未注册清册业主 → 201，席位 user=None、bind_state=PENDING_BIND、holder 含专有部分与姓名， | PASS | — | — |
| TC-INT-1021 | AC-256-02、REQ-NFUNC-046(4) | 同一专有部分两位业主 → 候选两位姓名，手机号脱敏（无完整号码）；seated/registered 标注； | PASS | — | — |
| TC-INT-1022 | AC-256-03、AC-258-02 | 委员上限 6、已有 6 个有效席位（其中 1 个待绑定）→ 再授予 409 CAP_REACHED、席位数不变；撤销待绑定后再授予成功。 | PASS | — | — |
| TC-INT-1023 | AC-256-04 | 业主甲已有有效席位，再授予另一职位 → 409 ALREADY_SEATED，席位新增数 0。 | PASS | — | — |
| TC-INT-1024 | AC-256-05 | 被授予的清册业主已注册并认证（手机号回退口径）→ 席位直接对应该用户，不处于待绑定，/me 委员身份显示。 | PASS | — | — |
| TC-INT-1025 | AC-256-06 | 任期未配置 → 409 TERM_NOT_CONFIGURED；开始日使结束日不晚于今天 → 400 INVALID_VALUE；均无席位新增。 | PASS | — | — |
| TC-INT-1026 | AC-256-07 | 普通用户 403、未登录 401；user_id 与 registry_owner_id 都给/都不给 → 400；registry_owner_id 非整数(bool/字符串) → 400；不存在 → 404；席位新增 0。 | PASS | — | — |
| TC-INT-1030 | AC-257-01、AC-257-05 | 待绑定期间业主甲新注册（未认证）无任何委员权限（表决 403）；手动认证（姓名+手机号一致）成功后 | PASS | — | — |
| TC-INT-1031 | AC-257-02 | 业主甲经申诉（owner_name=业主甲，手机号不在清册）被管理员通过 → 同样绑定并生效，via=APPEAL。 | PASS | — | — |
| TC-INT-1032 | AC-257-03 | 手机号匹配引导确认认证成功 → 同样绑定并生效，via=PHONE_MATCH。 | PASS | — | — |
| TC-INT-1033 | AC-257-04 | 同一专有部分另一位业主乙（另一手机号）认证 → 业主甲的待绑定席位不变，业主乙不获得任何席位角色。 | PASS | — | — |
| TC-INT-1034 | AC-257-06 | 绑定时该用户已持有另一有效席位 → 绑定失败、待绑定席位保持（bind_state=CONFLICT）、审计 SEAT_BIND_CONFLICT，用户既有席位不变；认证本身仍成功。 | PASS | — | — |
| TC-INT-1035 | AC-257-07、NFUNC-049(3) | 同一业主甲两个号码对应两个账号；第一个认证绑定后，第二个再认证 → 席位持有人不变，不重复绑定（SEAT_BOUND 仍 1 条）。 | PASS | — | — |
| TC-INT-1036 | AC-257-08 | 待绑定业主代表席位，业主甲认证后身份为业主代表，不具备业委会权限（表决 403、不属 is_member）。 | PASS | — | — |
| TC-INT-1037 | AC-257-09 | 授予日起 12 个月、第 3 个月才绑定（授予开始日=今天−90 天）→ 绑定后 term_start/term_end 不变； | PASS | — | — |
| TC-INT-1040 | AC-258-01、AC-258-04 | 列表第 1 行已绑定用户（昵称），另 1 行待绑定清册业主（专有部分 · 姓名，状态 PENDING_BIND）；响应无手机号明文；查询数不随行数增长。 | PASS | — | — |
| TC-INT-1041 | AC-258-02 | 待绑定席位可"变更职位"（新席位保留持有人记录、仍待绑定，原席位 REPLACED 释放原职位名额，审计 SEAT_CHANGED）。 | PASS | — | — |
| TC-INT-1042 | AC-258-03 | 清册改名（PUT owners 使业主甲不再是该专有部分业主）→ 待绑定席位 INVALIDATED，原因"清册变化"，审计 SEAT_INVALIDATED 1 条；已绑定席位不受影响。 | PASS | — | — |
| TC-INT-1043 | AC-258-03 | 删除专有部分 → 其业主的待绑定席位失效并审计。 | PASS | — | — |
| TC-INT-1044 | AC-258-03、NFUNC-049 | reconcile_registry_seats 幂等；业主姓名未变的待绑定席位不被误失效。 | PASS | — | — |
| TC-INT-1060 | AC-249-04、AC-249-06 | 公开列表含已结束 A 与进行中半数同意 B；不含指定负责人审批中 C、已撤回 D；游客身份用户可见 B。 | PASS | — | — |
| TC-INT-1061 | AC-249-04、AC-249-06 | 游客打开进行中半数同意 B 详情 200；指定负责人审批中 C 与已撤回 D 详情 403、响应不暴露内容；发起人仍可看 C；未登录 401。 | PASS | — | — |
| TC-INT-1062 | AC-249-01、AC-249-03 | initiator.display_name=昵称，labels 保留；昵称为空时为账号编号（不空白）；列表与详情一致。 | PASS | — | — |
| TC-INT-1063 | AC-251-06、NFUNC-046(3) | 列表与详情响应都不含 votes 键、不含任何 voter 标识或 choice（"谁投了什么"出现数 0）；只有聚合 vote_counts。 | PASS | — | — |
| TC-INT-1064 | AC-251-06 | 进行中半数同意已有 2 人投票（1 同意、1 反对），普通产权业主打开详情 200：vote_counts 同意 1/反对 1/弃权 0，participation.voted=2。 | PASS | — | — |
| TC-INT-1065 | AC-250-01 | 在任席位 7（无待绑定），已参与 4（同意 3、反对 1）→ participation={voted:4, expected:7}，vote_counts 3/1/0。 | PASS | — | — |
| TC-INT-1066 | AC-250-02/03/04 | 全部 7 人参与 → voted 7/expected 7；无人参与 → voted 0/expected 7（无 NaN 来源）；应参与人数为 0（无席位）→ expected 0。 | PASS | — | — |
| TC-INT-1067 | AC-250-05、AC-259-08 | 指定负责人决议 participation=None 且无 vote_counts。 | PASS | — | — |
| TC-INT-1068 | AC-250-07、AC-259-05 | 在任席位共 7（1 待绑定、6 可投票），6 位可投票者均已表决（同意 4、反对 1、弃权 1）→ participation={voted:6, expected:7}（不是 6/6）， | PASS | — | — |
| TC-INT-1069 | AC-259-05 | 已结束决议 participation.expected 取结果记录里的 denominator（判定时的 N），不随之后席位变化。 | PASS | — | — |
| TC-INT-1070 | M-SA-010 | 公开列表的投票统计整页一次查询，查询数不随决议行数增长（5 条比 1 条最多多 附件列表 每行 1 次的既有查询）。 | PASS | — | — |
| TC-INT-1071 | AC-251-01/02、NFUNC-046(3) | 3 人参与（第 3 人无头像、无昵称）→ count=3，每项键恰为 display_name/avatar_url/voted_at，按参与时间升序； | PASS | — | — |
| TC-INT-1072 | AC-251-03/04 | 无人参与 → count 0、results []；指定负责人（可见者）→ mode=DESIGNATED、count 0、results []。 | PASS | — | — |
| TC-INT-1073 | AC-251-05、AC-249-06、NFUNC-046 | 未登录 401（暴露 0）、管理员令牌 403；不可见决议（指定负责人审批中/已撤回）对陌生人 403，对发起人 200；不存在 404。 | PASS | — | — |
| TC-INT-1074 | AC-251-01 | 参与人只统计当前轮次（revision）的投票；上一轮次的投票不列。 | PASS | — | — |
| TC-INT-1080 | AC-259-01 | 在任 N=5（含 1 待绑定，4 可投票），同意 3、反对 1 → 3×2=6>5 通过；应投总数 5、同意 3、反对 1、弃权 0。 | PASS | — | — |
| TC-INT-1081 | AC-259-02 | N=5（含 1 待绑定），同意 2、反对 2 → 4 不大于 5，未通过，应投总数 5。 | PASS | — | — |
| TC-INT-1082 | AC-259-03 | N=6（含 1 待绑定，5 可投票），同意 3、反对 2 → 6 不大于 6 未通过（对照：待绑定若不计入分母 N=5 则 6>5 本可通过）； | PASS | — | — |
| TC-INT-1083 | AC-259-04 | N=4（含 2 待绑定，2 可投票），2 人全部同意 → 2×2=4 不大于 4，未通过；通过所需 ⌊4÷2⌋+1=3 票不可能达到。 | PASS | — | — |
| TC-INT-1084 | AC-259-06 | 待绑定席位持有人在截止前完成认证并绑定 → N 仍为 5，其可投票；投同意后已参与 +1，应参与人数仍为 5。 | PASS | — | — |
| TC-INT-1085 | AC-259-07、AC-258-02 | N=5（含 1 待绑定），投票同意 3、反对 1；截止前管理员撤销待绑定席位 → 判定 N=4，3×2=6>4 通过，应投总数 4。 | PASS | — | — |
| TC-INT-1086 | AC-259-08 | 口径为 CONFIGURED_CAP（主任1、副主任1、委员5 合计 7），含 1 待绑定委员，同意 3、反对 3 → N=7 不随待绑定变化，6 不大于 7 未通过； | PASS | — | — |
| TC-INT-1087 | AC-259-09 | 待绑定的业主代表席位 1 个、委员类 N=5（无待绑定委员类）→ N=5，业主代表不计入分母（仅占业主代表名额）。 | PASS | — | — |
| TC-INT-1088 | AC-257-05、US-258 | 待绑定席位无投票资格（同手机号已注册但未认证的用户表决 403）；存在 user 为空的待绑定业主代表席位时， | PASS | — | — |
| TC-INT-1100 | AC-247-01 | 产权业主（已验证手机号与清册业主"业主甲"登记号码一致）→ real_names=["业主甲"]。 | PASS | — | — |
| TC-INT-1101 | AC-247-02 | 2 套房登记同一姓名 → real_names 只出现 1 次（去重保序）；两个不同姓名按房屋序各 1 次。 | PASS | — | — |
| TC-INT-1102 | AC-247-03、NFUNC-046(1) | 游客、仅同住人、清册姓名为空的产权业主 → real_names=[]；响应中不含昵称代替，也不含清册里其他业主姓名。 | PASS | — | — |
| TC-INT-1103 | AC-247-04、AC-248-03 | 用户 B 的 /me/housing、/me、公开决议响应中出现用户 A 真实姓名（合成唯一串）次数 = 0。 | PASS | — | — |
| TC-INT-1104 | AC-248-01、AC-248-04 | 清册登记业主甲、乙，用户是业主甲 → co_owners=["业主乙"]（不含本人）；乙尚未注册仍显示姓名，无手机号、无注册状态字段。 | PASS | — | — |
| TC-INT-1105 | AC-248-02 | 清册只登记 1 位业主（本人）→ co_owners=[]（页面显示"无"）。 | PASS | — | — |
| TC-INT-1106 | AC-248-03、NFUNC-046(2) | 本专有部分的同住人看到共有产权人全名（含业主甲、乙）；游客、未认证该专有部分的用户读取 /me/housing 无该专有部分任何业主姓名； | PASS | — | — |
| TC-INT-1107 | AC-248-05、M-SA-010 | 2 套房各 1 位共有产权人，每行只显示各自的；/me/housing 查询数不随房屋数增长（2 套 vs 6 套）。 | PASS | — | — |
| TC-INT-1110 | AC-254-01 | 录入顺序打乱的 4 条（1栋2单元10层1001、1栋1单元2层201、1栋1单元10层1001、2栋1单元1层101）→ 未带排序参数时顺序为 | PASS | — | — |
| TC-INT-1111 | AC-254-02、NFUNC-048 | 共 3 页（5 条每页 2）依次翻页汇总 → 行数=总数、无重复、整体顺序等于一次取全量的顺序；楼层 2 在 10 之前。 | PASS | — | — |
| TC-INT-1112 | AC-254-03 | 楼栋=1栋 过滤时只含 1栋记录并仍按同一顺序；楼栋过滤+降序排序同样限定在过滤结果内。 | PASS | — | — |
| TC-INT-1113 | AC-254-04 | 含"地下车位""商铺"楼栋与负层时，默认顺序与既有 unit_sort_key 规则完全一致（不新增写法），地下车位在数字楼栋之后、商铺最后，负层在 1 层之前。 | PASS | — | — |
| TC-INT-1114 | AC-255-01 | sort=floor&order=desc → 楼层 10（B、C 同层，按默认楼栋/单元序 B,C）在前，再 3、2、1；order=asc 切回升序；两态切换。 | PASS | — | — |
| TC-INT-1115 | AC-255-01 | 楼栋/单元/楼层/房号四列各自升降序结果为主键自然顺序（楼栋 10 在 2 之后）。 | PASS | — | — |
| TC-INT-1116 | AC-255-02、NFUNC-048 | 房号降序，第 1 页（每页 2）为全部数据中房号最大的两条（不是仅当前页排序）；逐页汇总 = 全量排序，无重复遗漏。 | PASS | — | — |
| TC-INT-1117 | AC-255-04、IFC-361 | sort 非白名单（type/area/owner/注入串）→ 400 INVALID_QUERY；order 非 asc/desc → 400；仅给 order 不给 sort → 400；响应无记录。 | PASS | — | — |
| TC-INT-1118 | AC-255-03、AC-255-05 | 排序与过滤叠加（楼栋=1栋 + 房号降序）保持过滤范围；用户端令牌与未登录带 sort 请求 → 403/401，记录暴露 0。 | PASS | — | — |
| TC-INT-1119 | IFC-351、AC-256-01 | 管理端 /admin/registry/unit-options 响应形状同成员端 /units/options（level/skipped/has_empty/options），不含业主姓名与手机号； | PASS | — | — |
| TC-INT-1130 | AC-244-02、AC-251-01、AC-256-02 | api.js 中 5 个新增/改动调用均存在，并 resolve 到预期视图、支持该方法、权限类与所用令牌相容。 | PASS | — | — |
| TC-INT-1131 | AC-244-02 | UnitsAppeal.vue 的 FormData 键（form.append 读取）真实以 multipart 提交 → 201 并保存 owner_name、关联文件； | PASS | — | — |
| TC-INT-1132 | AC-251-01、AC-249-01、AC-250-01 | ParticipantList.vue 读取的 p.* 与 ResolutionDetail 读取的 data.*、Resolutions.vue 读取的 item.initiator.* / participation.* / vote_counts.* | PASS | — | — |
| TC-INT-1133 | AC-256-02、AC-255-01 | SeatHolderPicker.vue 读取的 o.* / data.owners 与后端候选响应一致；AdminRegistry.vue 可排序列 prop 全属后端 sort 白名单， | PASS | — | — |
| TC-INT-1134 | AC-247-01、AC-248-01、AC-258-01、Q-B18-33 | UnitsIdentity.vue 读 housing.real_names / unit.co_owners，AdminSeats.vue 读 row.holder.* / bind_state / hint.*， | PASS | — | — |
| TC-INT-1140 | GR-C-001 | 北京时间 00:30 运行 run_due_jobs → term_end=本地昨天(2026-11-17) 的席位 EXPIRED 并写 SEAT_EXPIRED 审计；term_end=本地今天 仍 ACTIVE（到期当日仍有效）。 | PASS | — | — |
| TC-INT-1141 | GR-C-001 | 同一时刻 POST /jobs/expire-committee-seats（管理员）→ expired=1，本地昨天的席位 EXPIRED，今天的 ACTIVE；非管理员 403。 | PASS | — | — |
| TC-INT-1142 | AC-257-09 | 待绑定席位（user 为空）到期同样按本地日期失效，之后认证不再绑定。 | PASS | — | — |

### 改写的既有集成用例（B1~B7、F1、F2）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-487 (B1) | AC-256-01 | AdminSeats.vue 发 registry_owner_id、不再含 user_id（test_frontend_contract.py） | PASS | — | — |
| TC-INT-488 (B2) | AC-247-01、AC-248-01 | /me/housing 顶层加 real_names、单元加 co_owners（test_frontend_contract.py） | PASS | — | — |
| TC-INT-713 (B3) | AC-244-02 | Web 读 form.append 键集 {unit_id,owner_name,files}，小程序 JSON 键不变（test_owner_auth_v2_contract.py） | PASS | — | — |
| TC-INT-957 (B4) | AC-248-01 | 单元字段集加 co_owners（test_phone_match_api.py） | PASS | — | — |
| TC-INT-477 (B5) | AC-247-01 | 顶层集合加 real_names（test_product_review_ac.py） | PASS | — | — |
| test_resident_and_guest_get_empty_aggregates (B6) | AC-247-03 | 游客响应体含 real_names=[]（test_product_review_api.py） | PASS | — | — |
| TC-INT-585 (B7) | AC-255-01 | 查询参数集加 sort/order，另断言非法值 400、合法值 200（test_registry_filters_contract.py） | PASS | — | — |
| TC-INT-921 (F1) | AC-244-02、AC-251-01、AC-256-02 | 覆盖清单改为 submitAppeal，并纳入 participants/unitOptions/ownerCandidates（layout_contract.spec.js） | PASS | — | — |
| TC-INT-923 (F2) | IFC-363 | api.js 导出集合基线加 4 个新函数（layout_contract.spec.js） | PASS | — | — |

## 与基线对比（baseline 模式）

| 失败项 | 基线 | 本次 | 结论 |
|---|---|---|---|
| B1~B7（TC-INT-487/488/713/957/477、test_resident_and_guest_get_empty_aggregates、TC-INT-585） | 7 条预期失败 | 全部通过 | 已改写为新行为断言 |
| F1/F2（layout_contract TC-INT-921/923） | 2 条预期失败 | 通过 | 已改写 |
| TC-INT-504（时段相关） | 北京时间 00:00–08:00 失败 | 白天通过；冻结 00:30 复跑通过 | 时区缺陷已修复，稳定 |
| 其余 | — | 全部通过 | 无新增失败 |

新增失败：0。

## 失败汇总（需路由给开发）

无。
