<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T13:32:21+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>2.0.0</version>
  <input_files><file>testing/test_plan.md（1.3.0）</file><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/code_review_report.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（PHASE_07）— 1.2.0（回流 2：DEF-014~016 复测（GC-3 修复后））

## 摘要

- 执行时间：2026-11-11 13:24–13:30（Asia/Shanghai）；报告计数来自**最后一次**执行（TC-UNIT-404 更新后全部重跑）
- 环境：Python 3.12.3 + Django 5.2.19，仓库原样运行（无任何临时补丁）；`config.test_settings`（SQLite 内存库）；vitest 2.1.9 + jsdom。Python 3.13 本机无，由 CI 验证
- 范围：后端 `tests.unit` 138 个（基线 102，**新增 36**）+ 前端内容中心用例 `content_api.spec.js` 3 个（既有）+ `content_editor.spec.js` 23 个（**新增**，其中 TC-UNIT-404 本轮按 DEF-016 修复更新）+ 小程序 `rich_blocks.spec.js` 6 个（既有 2 + **新增 4**）
- 命令：
  - `(cd backend && python manage.py test tests.unit --settings=config.test_settings)`
  - `(cd frontend && npx vitest run --passWithNoTests)`（全量，下表只统计内容中心相关文件）
  - `(cd miniprogram && npx vitest run --passWithNoTests)`

**metrics**：total = pass + fail + skip + blocked + not_testable = 170 = 170 + 0 + 0 + 0 + 0
（后端 138 = 138 + 0；前端内容中心 26 = 26 + 0；小程序 RichBlocks 6 = 6 + 0；138 + 26 + 6 = 170）

通过率 = pass / (pass + fail + blocked) = 170 / 170 = **100%**；判定模式 baseline（零新增失败 + 新写用例全部通过）；**本层门控：PASSED**——新写用例全部通过（TC-UNIT-393 随 DEF-015 修复转 PASS，TC-UNIT-404 更新后 PASS）；既有用例新增失败 0。

> 回流 2 说明：GROUP_C-3 修复 DEF-014/015/016 后三层重跑。TC-UNIT-404 原断言“开始保存”disabled，与 DEF-016 修复后的 AC-128-04 冲突（过期用例），已更新为：按钮可点击；点击后 `ElMessage.warning('请至少选择一个平台')` 被调用；`adminHttp.post` 无 `/drafts` 调用。

## 执行输出

```
$ (cd backend && python manage.py test tests.unit --settings=config.test_settings)
Ran 138 tests in 0.832s
OK

$ (cd frontend && npx vitest run --passWithNoTests)
 ✓ tests/content_api.spec.js (3 tests) 11ms
 ✓ tests/content_editor.spec.js (23 tests)
 Test Files  16 passed (16)
      Tests  154 passed (154)

$ (cd miniprogram && npx vitest run --passWithNoTests)
 ✓ tests/rich_blocks.spec.js (6 tests) 123ms
 Test Files  11 passed (11)
      Tests  75 passed (75)
```

## 分项结果

### 后端：富文本宽容校验与渲染（MOD-041/042，U-lenient，新增 19）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-348 | AC-109-01 | 共享颜色向量 `color_vectors.json`（期望值来自设计规则，不取自被测输出） | PASS | | |
| TC-UNIT-349 | AC-109-01 | rgb()/rgba() 归一化为 #hex；非法颜色丢弃、文字保留；均带 block_index | PASS | | |
| TC-UNIT-350 | AC-109-01 | 空串 / null 样式值不产生警告 | PASS | | |
| TC-UNIT-351 | AC-110-01、ADR-062 | 标题层级>4 钳位为 4 并告警 | PASS | | |
| TC-UNIT-352 | ADR-062（GR-C-002-F04：外链图片丢弃） | 无 mediaId 的图片 / 视频整节点丢弃并告警 | PASS | | |
| TC-UNIT-353 | AC-107-04、AC-108-04 | javascript: / data: 链接丢弃标记、文字保留，输出不含 javascript | PASS | | |
| TC-UNIT-354 | ADR-062（结构错误不放宽） | 未知节点丢弃、结构错误仍抛错 | PASS | | |
| TC-UNIT-355 | ADR-062（限额不放宽） | 超限（字节、嵌套、节点数）仍抛错，不降级 | PASS | | |
| TC-UNIT-356 | ADR-062（warnings 上限） | 警告列表最多 50 条，warning_total 为真实总数 | PASS | | |
| TC-UNIT-358 | AC-109-04 | 块级行距在 web / inline / blocks 三种输出中保留，行内不覆盖块级 | PASS | | |
| TC-UNIT-359 | AC-123-01 | 引用 / 列表内任意深度图片视频的 HTML 与 blocks 渲染 | PASS | | |
| TC-UNIT-360 | AC-108-01 | 下划线 + 删除线合并为一个 text-decoration | PASS | | |
| TC-UNIT-361 | AC-124-01 | 任意深度的段落与媒体提取 | PASS | | |
| TC-UNIT-362~367 | AC-109-01、AC-110-01、AC-107-04 | #hex 不变无告警、字号 / 行距丢弃、严格模式不变、允许的链接协议保留、深层素材缺失就地降级 | PASS | | |

### 后端：公众号令牌服务（MOD-062，U-token，新增 15）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-368 | AC-128-01 | 首次取令牌加密入库，再次命中缓存不再请求；缓存是密文 | PASS | | |
| TC-UNIT-369 | AC-128-01 | 提前量 300 秒：≤300 秒刷新，>300 秒命中 | PASS | | |
| TC-UNIT-370~373 | AC-128-01、AC-128-06 | expires_in 缺失按 7200；invalidate 清全部缓存列；缺凭据不发请求；非公众号账户 ValueError | PASS | | |
| TC-UNIT-374~377 | AC-128-01 | 单飞：他人持锁超时 TOKEN_BUSY 且不取；他人已刷新则复用；过期锁可抢并释放；取令牌失败也释放锁 | PASS | | |
| TC-UNIT-378 | AC-128-01 | 强制刷新冷却（60 秒内 TOKEN_BUSY，之后可刷新） | PASS | | |
| TC-UNIT-379 | AC-127-04 | 取令牌期间凭据被覆盖→结果丢弃不入库 | PASS | | |
| TC-UNIT-380~381 | AC-127-03 | errcode 分类：缺省 auth_errcodes 为空、40164→IP_NOT_WHITELISTED（IP 优先）、配置后命中 AUTH_REJECTED；各类错误映射 | PASS | | |
| TC-UNIT-382 | AC-127-02 | 所有错误信息不含 appsecret / 令牌 | PASS | | |

### 后端：既有模块（保险库、参数、样式、分镜、Range、富文本 301~320）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-UNIT-301~320（既有） | AC-107-04、AC-109-03、AC-110-01、AC-112-03、AC-113-01~04 等 | 白名单校验、渲染、分页、文本转文档、媒体提取 | PASS |
| TC-UNIT-321~331（既有） | AC-117-02、AC-125-02、AC-112-01/02 | AES-GCM、脱敏、参数、样式模板 | PASS |
| TC-UNIT-332、333（**更新**） | AC-124-01 | `build_scenes` 入参改为段落列表：合并到上限、单段 | PASS |
| TC-UNIT-346、347（**新增**） | AC-124-01 | 空段落列表→POST_INCOMPLETE；3 段文档→3 分镜（旧实现恒 1 个） | PASS |
| TC-UNIT-334~336（既有） | AC-114-01、AC-123-01 | 提示语气 / 篇幅、Range 解析 | PASS |
| 其余后端既有单元 | — | 基线 102 个中的非内容中心部分（核心规则、登录、审批等）；全部通过 | PASS |

### 前端 / 小程序（vitest）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-341~343（既有，F-api） | AC-105-01、AC-116-02、AC-128-05 | API 路径 / 方法 / 参数 | PASS | | |
| TC-UNIT-383 | AC-110-01、AC-110-04 | 工具栏按钮 = 基础格式清单；标题 1~4；2 个取色器；字号、行距输入；不含表格 / 代码 / 公式 / 表情 / 卡片 | PASS | | |
| TC-UNIT-384 | AC-110-01、AC-110-04 | 真实 Tiptap 扩展清单含全部格式扩展，不含 table / code / 公式 | PASS | | |
| TC-UNIT-385 | AC-109-01 | 取色器：#hex 直接设置；rgb() 归一化；非法值不设置并清除 | PASS | | |
| TC-UNIT-386 | AC-109-01 | 真实编辑器经取色器设置颜色→文档为 #ff0000，update 事件携带 | PASS | | |
| TC-UNIT-387 | AC-109-01 | `toHexColor` 与服务端口径一致，非法输入返回 null | PASS | | |
| TC-UNIT-388 | AC-109-01 | 粘贴守卫纯函数：rgb 归一化、非法颜色声明删除文字保留、外链 / data 图片丢弃计 2、脚本 / iframe 移除、带 data-media-id 的图片保留 | PASS | | |
| TC-UNIT-389 | AC-109-01 | 真实 ProseMirror 粘贴：颜色成 #008000、外链图片不进文档并触发 paste-dropped | PASS | | |
| TC-UNIT-390 | AC-110-02 | 加粗 + 字号 + 背景色后“清除格式”→无 marks，文字不变 | PASS | | |
| TC-UNIT-391 | AC-110-03 | 两步编辑→撤销一次→重做一次，内容依次回到上一步与重做后 | PASS | | |
| TC-UNIT-392 | AC-109-03 | 无效网址（javascript: / 无协议 / ftp）→不添加链接，提示“网址无效”×3；有效地址添加成功 | PASS | | |
| TC-UNIT-393 | AC-109-03 | 网址为空（点“确定”未填）→不添加链接并提示“网址无效”；取消静默（DEF-015 已修复） | PASS | | |
| TC-UNIT-394 | AC-105-02、GR-C-002-F02 | 保存失败（400 CONTENT_INVALID_DOC）→不发布、不确认文案，提示带位置“第 1 个块（段落）” | PASS | | |
| TC-UNIT-395 | AC-105-02、AC-109-01 | 保存成功才发布 / 确认；先 PATCH 后 POST；带 warnings 时用规范化文档替换并提示 | PASS | | |
| TC-UNIT-396 | AC-115-03 | 已有正文→先确认“将覆盖当前正文，是否继续？”；取消正文不变；确认才覆盖 | PASS | | |
| TC-UNIT-397 | AC-128-03、AC-129-01、AC-130-01 | 推送结果中文：失败 / 需人工粘贴 / 认证已失效 / 不能保留“分页、版式样式”；无英文状态码 | PASS | | |
| TC-UNIT-398 | AC-129-01 | 状态 / 原因 / 警告文案映射纯函数 | PASS | | |
| TC-UNIT-403 | AC-124-07 | 视频生成仅“生成视频”入口，无分镜 / 裁剪 / 调序 | PASS | | |
| TC-UNIT-404（**更新**） | AC-128-04 | 未勾选平台→“开始保存”可点击（disabled=false）；点击后 `ElMessage.warning('请至少选择一个平台')` 被调用；无 `/drafts` 请求（DEF-016 已修复） | PASS | | |
| TC-UNIT-405 | AC-126-04、AC-127-02/03/05 | 平台页仅 3 个平台；失效账户显示“失效”和重新认证提示；认证输入框不回显；无检测入口 | PASS | | |
| TC-UNIT-406 | AC-127-02 | 覆盖认证信息只提交已填字段并重新加载 | PASS | | |
| TC-UNIT-407 | AC-106-03 | 删除二次确认取消→不发 DELETE、内容仍在；确认后才删 | PASS | | |
| TC-UNIT-408 | AC-121-03 | 素材库为空→显示“素材库为空”，无报错 | PASS | | |
| TC-UNIT-409 | AC-121-01、AC-111-01 | 上传与 AI 图片均可选，选中后触发 selected 并插入正文（mediaId / src） | PASS | | |
| TC-UNIT-344、345（既有，M-rich） | AC-108-01 | 小程序段落 / 标题 / 图片 / 引用渲染；点击链接复制并提示 | PASS | | |
| TC-UNIT-399（新增，M-rich） | AC-123-01 | 引用 / 列表内（含多层）图片 3 张、视频 1 个的 src 均带 API 基址，无重复前缀 | PASS | | |
| TC-UNIT-400（新增） | AC-109-04 | 块级与行内行距分别作用于块与文字；对齐 | PASS | | |
| TC-UNIT-401（新增） | AC-108-01 | 下划线 + 删除线合并为一个 text-decoration；链接默认下划线与删除线合并 | PASS | | |
| TC-UNIT-402（新增） | AC-108-01 | 颜色 / 背景 / 字号 / 加粗 / 斜体 | PASS | | |

> Tiptap/ProseMirror 在 jsdom 中**可以真实挂载**（仅需测试文件内的 `Range.getClientRects`、`ClipboardEvent` 垫片），因此上表为真实编辑器断言，不是最小挂载替代。

## 与基线对比（baseline 模式）

| 项 | 基线 | 本次 | 新增用例 | 既有用例新增失败 | 结论 |
|---|---|---|---|---|---|
| 后端 unit | 102 | 138 | +36（全部 PASS） | 0 | 通过 |
| 前端 vitest（全量） | 131 | 154 | +23（全部 PASS） | 0（基线 131 全部通过） | 通过 |
| 小程序 vitest（全量） | 71 | 75 | +4（全部 PASS） | 0 | 通过 |

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| — | 无失败。DEF-015 已修复（TC-UNIT-393 PASS）；DEF-016 已修复（TC-UNIT-404 更新后 PASS） | — | — |

## 备注

- 外部服务一律使用 `apps/integrations/fakes.py` 替身，无真实端点调用；测试文件内的垫片不改产品代码。
- 前后端颜色归一化共享同一份向量文件（后端读取 `backend/tests/data/color_vectors.json`），前端用例覆盖同一规则的代表值。
