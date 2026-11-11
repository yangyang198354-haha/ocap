<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T13:31:29+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>2.0.0</version>
  <input_files><file>testing/test_plan.md（1.3.0）</file><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/code_review_report.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（PHASE_08）— 1.2.0（回流 2：DEF-014~016 复测（GC-3 修复后））

## 摘要

- 执行时间：2026-11-11 13:28–13:31（Asia/Shanghai）
- 环境：Python 3.12.3 + Django 5.2.19，仓库原样运行；`config.test_settings`（SQLite 内存库）；真实 DRF 路由与 ORM；外部服务仅用 `apps/integrations/fakes.py` 替身（含 `FakeWechatMpApi`），无真实端点
- 范围：`backend/tests/integration` 全量 342 个（基线 293，**新增 49**：审计 21 + 权限扫描 6 + 公众号适配器与补缺 22；另**更新** 6 个既有用例）；另有 1 个无代码的 BLOCKED 项（TC-INT-395）
- 命令：`(cd backend && python manage.py test tests.integration --settings=config.test_settings)`

**metrics**：total = pass + fail + skip + blocked + not_testable = 343 = 342 + 0 + 0 + 1 + 0
（执行 342 个 = 342 PASS + 0 FAIL；另计 TC-INT-395 BLOCKED 1 项，无可执行代码）

通过率 = pass / (pass + fail + blocked) = 342 / 343 = **99.7%**；判定模式 baseline（零新增失败 + 新写用例全部通过）；**本层门控：PASSED**——新写用例全部通过（TC-INT-388 随 DEF-014 修复转 PASS）；既有用例新增失败 0；唯一 BLOCKED 为 TC-INT-395（无官方文档出处，非缺陷、非新增失败，基线模式不计失败）。

> 回流 2 说明：单元层门控 PASSED 后执行本层；DEF-014 已修复（`posts.py` 递归去前缀）。

## 执行输出

```
$ (cd backend && python manage.py test tests.integration --settings=config.test_settings)
Ran 342 tests in 14.612s
OK

$ (cd backend && python manage.py check --settings=config.test_settings)
System check identified no issues (0 silenced).
$ (cd backend && python manage.py makemigrations --check --dry-run --settings=config.test_settings)
No changes detected
```

## 分项结果

### 契约测试（前端 / 小程序 api.js ↔ 后端路由）

`backend/tests/integration/test_frontend_contract.py`（既有 14 个）本次全部通过：`frontend/src/shared/api.js`、`miniprogram/utils/api.js` 的每个调用（路径 + 方法）均可解析到后端路由并被视图支持；本轮**没有新增或修改**这两个文件中的调用，故无新增契约项。客户端关键调用逻辑另有 vitest 用例（TC-UNIT-341~343、383~409）。

### 管理端内容 API（MOD-054 ↔ MOD-045）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-301~308、310、312（既有） | AC-105-01/02/03、AC-106-01/02/04、AC-107-02、AC-115-02 | 创建 / 列表 / 权限 / 发布缺项 / 发布下线 / 修改审计 / 确认文案与成员可见性 / 删除 | PASS | | |
| TC-INT-309（**更新**） | AC-107-04、AC-109-03 | 宽容模式：危险链接丢弃→201，输出 doc 与渲染 HTML 都不含 javascript:，warnings（LINK/DROPPED/block_index）；未知节点告警；结构 / 限额错误仍 400 带 block_index/block_type | PASS | | |
| TC-INT-311（既有） | AC-111-01 | blocks 顶层媒体 src 去掉 API 前缀 | PASS | | |
| TC-INT-381（新增） | AC-105-03 | 默认标题“未命名内容”（含首尾空白）发布 400 POST_INCOMPLETE、missing=[title]、状态仍 DRAFT；“未命名内容补充说明”可发布 | PASS | | |
| TC-INT-388（新增） | AC-108-01、AC-123-01 | `fmt=blocks` 在引用 / 列表内的图片视频 src 与顶层一致去掉 `/api/v1` 前缀（DEF-014 已修复） | PASS | | |

### 审计落点（MOD-045/044/051/053/055 ↔ core.audit，I-audit，新增 21）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-346 | AC-105-02、AC-105-03 | 发布→恰 1 条审计（操作人 / 对象 / 时间 / 结果）；不完整被拒不写 | PASS |
| TC-INT-347 | AC-106-01 | 已发布改正文→门户显示新正文，恰 1 条“修改”；草稿阶段不写 | PASS |
| TC-INT-348 | AC-106-02 | 下线→恰 1 条；成员列表 0、详情 404；重复下线 409 不重复写 | PASS |
| TC-INT-349 | AC-106-04 | 删除→恰 1 条；不存在的 id 404 不写 | PASS |
| TC-INT-350 | AC-117-02、AC-117-04 | 服务配置：改模型 / 凭据各恰 1 条（detail 仅 changed_fields）；凭据原文在响应 / 列表 / 可选列表 / 日志 / 审计 0 次 | PASS |
| TC-INT-351 | AC-118-01~04 | 连通测试成功 / 失败各恰 1 条（失败 result=FAILURE）；未测 / 失败配置不进可选列表 | PASS |
| TC-INT-352 | AC-125-01~03 | 即梦账号不回显；他人管理员可见同一份；必填缺失 400 且已有配置不变；原文 0 次 | PASS |
| TC-INT-353 | AC-122-03、AC-122-04 | 未被引用的素材删除→恰 1 条审计、文件删除（`captureOnCommitCallbacks`）；被引用 409 不写 | PASS |
| TC-INT-354 | AC-122-03 | 删除事务回滚（审计失败）时文件保留、素材行仍在、无审计 | PASS |
| TC-INT-355 | AC-124-05、AC-124-06 | 未确认 409 不记成功；发起恰 1 条 CONTENT_VIDEO_REQUESTED（job_id / scenes）；完成补记 1 条 | PASS |
| TC-INT-356 | AC-126-01~04 | 添加 / 改名 / 删除各恰 1 条；同平台第二个 409；平台只有 3 个 | PASS |
| TC-INT-357 | AC-127-01、AC-127-02 | 认证信息更新恰 1 条且 detail 无原文；响应 / 列表 / 日志 / 审计中 appid、appsecret 0 次 | PASS |
| TC-INT-358 | AC-127-05 | 无独立“检测账户有效性”接口 | PASS |
| TC-INT-359 | AC-128-07、AC-130-01 | 全人工批次入队时恰 1 条批次审计，含逐平台结果，无 job | PASS |
| TC-INT-360 | AC-128-06、AC-128-07 | 无凭据批次：失败行 + 人工行，恰 1 条 result=FAILURE，无外部调用 | PASS |
| TC-INT-361 | AC-128-01、AC-128-07 | 混合批次：入队不写，处理器结束写 1 条含全部行；重复汇总幂等；无 appsecret | PASS |
| TC-INT-362 | AC-129-01、AC-128-07 | 自动平台失败→批次审计 FAILURE，逐平台 error_code，detail 不含 error_message | PASS |
| TC-INT-363 | AC-128-07 | worker 中断：SENDING→UNKNOWN，批次审计恰 1 条，再次回收不重复 | PASS |
| TC-INT-364 | AC-128-07 | 经 `run_content_worker --once` 端到端混合批次恰 1 条，任务 SUCCEEDED | PASS |
| TC-INT-365 | AC-130-02、AC-130-04 | 导出恰 1 条；包含正文 + 2 图 + 1 视频；未确认 409 不写；复制载荷不写 | PASS |
| TC-INT-366 | AC-130-04、AC-130-05 | 纯文字内容包仅 3 个文件；构建失败不写审计 | PASS |

### 权限扫描（MOD-054 全部路由，I-scan，新增 6）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-367 | AC-131-01~03 | 自动枚举 `content/urls.py` 全部 `admin/content/*` 路由 × 视图实现的每个方法（≥30 路由 / ≥42 对；新增路由自动纳入，参数样本缺失即失败） | PASS |
| TC-INT-368 | AC-131-03 | 未登录：全部路由 × 方法→401 UNAUTHORIZED；content 全表 + AuditLog + SystemConfig + 媒体目录前后快照一致（无写入副作用） | PASS |
| TC-INT-369 | AC-131-02 | 游客与业主：全部路由 × 方法→403 FORBIDDEN，响应只含 code / message；无写入副作用 | PASS |
| TC-INT-370 | AC-131-01 | 另一管理员账号访问全部 GET 管理接口（≥14）均非 401 / 403 / 5xx | PASS |
| TC-INT-371 | AC-107-03、AC-108-03、AC-131-03 | 用户端 info 三个入口：未登录 401、管理员令牌 403、普通用户 200；写方法 405 | PASS |
| TC-INT-372 | AC-131-03 | 未登录可访问的内容路由仅限带签名的媒体文件；无 / 错 / 他人签名 403，正确签名 200 | PASS |

### 公众号适配器与补缺（MOD-063/062 ↔ MOD-053，I-gaps，新增 22）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-373 | AC-128-01 | 上传开关缺省关闭；默认只发 fetch_token + add_draft，无任何上传请求；SAVED | PASS | | |
| TC-INT-374 | AC-128-01 | 缓存令牌 + 令牌类错误（errcode / HTTP 401）→强制刷新并重发恰一次成功；连续两次失败也只重发这一次（add_draft 共 2 次） | PASS | | |
| TC-INT-375 | AC-128-01 | 超时 / 连接中断（NETWORK）不重发（add_draft 1 次）；账户保持 NORMAL，无失效审计 | PASS | | |
| TC-INT-376 | AC-127-03 | 40164：取令牌时与 draft/add 时均分类 IP_NOT_WHITELISTED，账户保持 NORMAL，不写失效审计，不重发 | PASS | | |
| TC-INT-377 | AC-127-03 | auth_errcodes 命中→FAILED / AUTH_EXPIRED“认证已失效，请重新认证”，账户 EXPIRED，审计 CONTENT_PLATFORM_AUTH_EXPIRED 恰 1 条；再推送不重复写；账户列表显示 EXPIRED | PASS | | |
| TC-INT-378 | AC-127-04 | 覆盖认证信息→账户恢复 NORMAL、令牌缓存列全部清空、下次推送重新取令牌并成功 | PASS | | |
| TC-INT-379 | AC-127-02 | 响应（历史 / 账户列表）、日志、审计、推送记录中 appsecret 与访问令牌 0 次；缓存与密文列不含明文 | PASS | | |
| TC-INT-380 | AC-129-03、AC-129-04 | 重试再次失败：仍 FAILED 且为最新失败原因；历史新增 1 条（倒序，最新在前）；原记录不变 | PASS | | |
| TC-INT-381 | AC-105-03 | 见上 | PASS | | |
| TC-INT-382 | AC-130-02 | 导出内容包前后 `tempfile.gettempdir()` 无新增文件：成功、客户端中断、`ZipFile.write` 异常、审计异常四条路径 | PASS | | |
| TC-INT-383 | AC-124-03、AC-120-03 | 视频多片段第 2 段下载失败→DOWNLOAD_FAILED；素材库行数与媒体文件均无新增；无完成审计 | PASS | | |
| TC-INT-384 | AC-124-02 | 两段都成功→恰新增 2 条 VIDEO / AI_GENERATED / SAVED，写 1 条完成审计 | PASS | | |
| TC-INT-385 | AC-124-03、AC-120-03 | 服务返回失败→run_one 落库 FAILED / REMOTE_FAILED，含失败原因；素材库无新增；API 返回同样状态 | PASS | | |
| TC-INT-386 | GR-C-002-F07 | worker 心跳（JobRun）≤ 每 60 秒 1 次：58 秒 1 次、62 秒 2 次、122 秒 3 次 | PASS | | |
| TC-INT-387 | GR-C-002-F07 | `--concurrency` 已移除（传入报 CommandError，帮助中无）；`--once` 最终状态 STOPPED | PASS | | |
| TC-INT-388 | AC-123-01 | 见上 | PASS | | |
| TC-INT-389 | AC-129-02 | 失败平台重试成功→新记录 SAVED（retry_of 指向原记录），其他平台与原失败记录不变 | PASS | | |
| TC-INT-390 | AC-114-04 | 模型失败→任务 FAILED / UPSTREAM 带原因；不产生内容草稿 | PASS | | |
| TC-INT-391 | AC-116-04、AC-120-03 | 文生图失败→任务 FAILED / UPSTREAM；素材库与正文不变 | PASS | | |
| TC-INT-392 | AC-120-02、AC-122-01 | 类型 + 来源组合筛选只返回同时满足者 | PASS | | |
| TC-INT-393 | AC-111-03、AC-119-01~04、AC-123-03 | 11 MB 图片 / 视频→413 FILE_TOO_LARGE，素材库无新增；5 MB 图片、8 MB 视频可上传为 UPLOAD | PASS | | |
| TC-INT-394 | AC-112-04 | 样式名称为空 / 空白→400 STYLE_NAME_REQUIRED“模板名称不能为空”，模板列表不变 | PASS | | |
| **TC-INT-395** | AC-128-01（子项） | 公众号封面上传、正文图片上传的 HTTP 行为 | **BLOCKED** | 无可执行用例 | **环境 / 资料缺失：`[DATA_REQUIRED: 微信官方文档]`**（端点、字段、限制无出处，协议 §N-2；`HttpWechatMpApi.upload_*` 为 NotImplementedError 占位，开关缺省关闭）。写入人工验证清单 M-04 |

### 既有集成用例（含本轮更新）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-313~318、336~339、344（既有） | AC-119-01~04、AC-122-02/04、AC-123-02 | 上传 / 魔数 / 超限 / 配额 / 重命名删除 / 签名 / Range / 候选清理 | PASS |
| TC-INT-319~324（既有） | AC-117-01~03、AC-118-01、AC-125-03 | 服务配置 / 提示词 / 参数 | PASS |
| TC-INT-325、326、334、338（既有） | AC-114-01/03/05 | 文案任务、空提示词、未配置、限流 | PASS |
| TC-INT-327、330、341（**更新**） | AC-126-01~04、AC-128-04/05 | 公众号凭据键改为 appid / appsecret（旧键 access_token→400 INVALID_VALUE）；改名 / 删除；未确认 409 | PASS |
| TC-INT-328、329、331、332、333、335、340、342、343、345（既有） | AC-128-01~03/06、AC-130-01~03/05、AC-124-01/04/05、AC-129-01~03、AC-112-02 | 人工平台 / 无凭据、推送成功与失效、内容包、复制载荷、视频前置校验、历史、样式模板 API、重试、中断、视频失败 | PASS |
| 其余既有集成（基线 293 中非本批） | — | 登录、审批、清册导入等 | PASS |

## 与基线对比（baseline 模式）

| 项 | 基线 | 本次 | 新增用例 | 既有用例新增失败 | 结论 |
|---|---|---|---|---|---|
| 后端 integration | 293 | 342 | +49（全部 PASS） | 0 | 通过 |
| 5 个过期既有用例（GR-C-003-F01） | 4 失败 + 1 通过但需更新 | 全部更新并通过 | — | — | TC-INT-309 的 XSS 断言未放宽 |

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| — | 无失败。DEF-014 已修复（TC-INT-388 PASS） | — | — |
| TC-INT-395 | BLOCKED：缺微信官方文档 | — | 非缺陷，等待 Q-B1 |
