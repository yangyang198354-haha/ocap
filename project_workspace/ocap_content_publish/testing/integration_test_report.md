<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T00:56:52+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（PHASE_08）

## 摘要

- 执行时间：2026-11-11 00:36–00:42
- 环境：`config.test_settings`；真实 DRF 路由与 ORM；外部服务替身（LLM/图/视频/草稿/远程下载）
- 范围：`backend/tests/integration` 全量 282 个，本批新增 45 个（TC-INT-301~345）
- 命令：`python manage.py test tests.integration --settings=config.test_settings`

**metrics**：total = pass + fail + skip + blocked + not_testable = 282 = 282 + 0 + 0 + 0 + 0

通过率 = 282 / 282 = **100%**；本层门控：**PASSED**

## 执行输出

```
$ python manage.py test tests.integration --settings=config.test_settings
Ran 282 tests in 3.2s
OK
```

## 分项结果

### 管理端内容 API（MOD-054 ↔ MOD-045）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-301~302 | AC-105-01、AC-131-02/03 | 创建/列表不含 doc；401/403 权限 | PASS |
| TC-INT-303~305 | AC-105-03、AC-106-01、AC-106-02 | 发布缺标题/正文、发布/下线、已发布修改审计 | PASS |
| TC-INT-306~308 | AC-107-02、AC-106-04、AC-115-01/02 | 确认文案、会员可见性、删除、列表仅已发布 | PASS |
| TC-INT-309~312 | AC-107-04、AC-112-03、AC-098-02（blocks） | 非法链接 400、预览不落库、blocks 媒体相对路径、非法状态查询 | PASS |

### 素材库（MOD-044）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-313~315 | AC-119-01~04、AC-123-02 | PNG/MP4 上传、类型/来源筛选、svg/伪魔数拒绝 | PASS |
| TC-INT-316~318 | AC-122-02/03、AC-122-04、AC-116-02 | 重命名/删除、已发布引用拒绝并列出标题、签名 URL 必需与 nosniff | PASS |

### 服务配置与提示词（MOD-051）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-319~321 | AC-117-02/03、AC-118-01、AC-125-03 | 保存凭据只回布尔、测试连通、可选模型、缺字段 400、非 LLM 不可测 | PASS |
| TC-INT-322 | AC-114-02 | 提示词模板 CRUD/重名 409 | PASS |
| TC-INT-323~324 | AC-112-01（参数）、AC-117-01 | 参数读写、非法键 400 | PASS |

### AI 任务与草稿推送（MOD-052/053 ↔ MOD-046/049）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-325~326 | AC-114-01/03/04/05、AC-115-01 | 文案任务成功/空提示/未配置模型 | PASS |
| TC-INT-327~328 | AC-126-01/02、AC-127-01/02、AC-128-02/06 | 平台账户唯一、凭据掩码；人工平台 MANUAL_REQUIRED、无凭据 FAILED | PASS |
| TC-INT-329~330 | AC-127-03、AC-128-01/04/05、AC-129-01 | 草稿 SAVED/AUTH_EXPIRED→EXPIRED；未确认 409、空选择 400 | PASS |
| TC-INT-331~332 | AC-130-02/05、AC-130-03 | 内容包 ZIP 含文本/HTML/README；复制载荷 | PASS |
| TC-INT-333~335 | AC-124-04/05、AC-118/129（历史） | 视频未配置/未确认 409，确认后建任务；任务筛选；历史空 | PASS |

### 分支与异常覆盖（复审后新增 TC-INT-336~345）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-336 | AC-119-03 | 图片超过上限 → 413 `FILE_TOO_LARGE` | PASS |
| TC-INT-337 | AC-119-03 | 配额不足 → 413 `MEDIA_QUOTA_EXCEEDED` | PASS |
| TC-INT-338 | AC-114-01 | 内容 AI 限流 → 429 `CODE_RATE_LIMITED` | PASS |
| TC-INT-339 | AC-123-01 | 签名 URL Range 206 与非法 Range 416 | PASS |
| TC-INT-340 | AC-112-02 | 样式模板 PUT/DELETE API 与列表移除 | PASS |
| TC-INT-341 | AC-126-03 | 平台账户删除后列表置空、可重新创建 | PASS |
| TC-INT-342 | AC-129-01/02 | 失败草稿重试 → 新 PENDING；再次重试 409 | PASS |
| TC-INT-343 | AC-129（中断） | SENDING→UNKNOWN、PENDING→FAILED(INTERRUPTED) | PASS |
| TC-INT-344 | AC-120（候选） | 过期候选清理；被内容引用的候选保留 | PASS |
| TC-INT-345 | AC-124-03 | 视频远端失败 → `REMOTE_FAILED` | PASS |

### 契约（MOD-058）

- 既有 `test_frontend_contract.py` 对 `api.js` 的全量调用解析在新增 40+ 调用后仍通过（后端全量 412 OK）。

## 与基线对比

| 项 | 基线 | 本次 | 结论 |
|---|---|---|---|
| 集成层 | 237 OK | 282 OK | 新增 45 全通过 |
| 后端全量 | 327 OK | 412 OK | 新增失败 0 |

## 失败汇总

无。

## 备注（部分覆盖）

- 前端交互（工具栏、弹窗确认、重试按钮）仅验证 API 契约，未做组件测试。
- 真实平台联调被 P4 禁止，草稿/视频/图片的真实错误码仅按参考实现映射。
