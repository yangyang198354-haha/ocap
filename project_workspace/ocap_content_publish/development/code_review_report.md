<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T13:20:58+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>3.0.0</version>
  <input_files><file>development/implementation_plan.md (1.1.0)</file><file>architecture/module_design.md (2.0.0)</file><file>architecture/architecture_design.md (2.0.0)</file><file>development/code_review_report.md (1.0.0 APPROVED，被本版本返工)</file><file>phase_status.md (GR-C-002)</file></input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：信息公开与多平台内容中心（GROUP_C，返工 1.1.0）

## 摘要

- 返工范围：GR-C-002 的 F01~F07（F06 按用户选 B 实现 ADR-060；ADR-061 仅签名/stub/关闭的开关）。
- `git diff --stat`（本次涉及的产品代码，不含 `project_workspace/` 与工作区既有的 `backend/apps/registry/importing.py` 及未跟踪的 `test_registry_import_query_bounds.py`）：修改 24 个已跟踪文件（后端 18：content 15 + `core/audit.py` + `integrations/{draft,fakes}.py`；前端 5；小程序 1）+ 新建 6 个（`0002_platformaccount_token_cache.py`、`wechat_token.py`、`wechat_mp.py`、`colors.js`、`contentText.js`、`pasteGuard.js`）。其余 `git status` 中的文件（`project_workspace/`、`.claude/agent-memory/system-architect/`、`backend/apps/registry/importing.py`、`backend/tests/integration/test_registry_import_query_bounds.py`）非本次改动。完整清单见 implementation_plan"改动清单"。
- 五维平均分：**8.1**（MOD 级评分见下）。
- 问题统计：**CRITICAL 0（本轮新发现 0；GR-C-002-F01 已 FIXED）／MAJOR 3（OPEN）／MINOR 5**。
- 自验证结论：Python 3.12.3 + Django 5.2.19 下后端**原样**可导入并运行（无任何临时补丁），全量 430 用例中 **425 通过、5 失败**；5 个失败全部是有意的行为变化导致的既有用例过期（逐条说明见"现有测试调整"），**相对基线 430 全绿不是"零新增失败"，需 test-engineer 更新后才能满足 baseline 门控**。前端 131 / 小程序 71 全部通过，前端构建成功。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC |
|---|---|
| backend/apps/core/audit.py | MOD-056 / IFC-188 |
| backend/apps/content/models.py、migrations/0002_platformaccount_token_cache.py | MOD-039 / IFC-165 |
| backend/apps/content/conf.py | MOD-041 / IFC-168 |
| backend/apps/content/richtext/{schema,render,convert,__init__}.py | MOD-042 / IFC-169~171 |
| backend/apps/content/media.py | MOD-044 / IFC-173 |
| backend/apps/content/jobs.py | MOD-046 / IFC-176 |
| backend/apps/integrations/wechat_mp.py | MOD-063 / IFC-239 |
| backend/apps/content/wechat_token.py | MOD-062 / IFC-240 |
| backend/apps/integrations/draft.py | MOD-049 / IFC-180 |
| backend/apps/integrations/fakes.py | MOD-050 / IFC-181 |
| backend/apps/content/posts.py | MOD-045 / IFC-175 |
| backend/apps/content/ai_jobs.py | MOD-052 / IFC-184 |
| backend/apps/content/{platforms,drafts,export_pack}.py | MOD-053 / IFC-185~187 |
| backend/apps/content/views_admin.py | MOD-054 / IFC-191/193/198/203/206 |
| backend/apps/content/management/commands/run_content_worker.py | MOD-057 / IFC-189 |
| frontend/src/admin/editor/{colors,pasteGuard}.js | MOD-059 / IFC-241、IFC-242 |
| frontend/src/admin/editor/{contentText.js,RichEditor.vue,Toolbar.vue,extensions/Video.js}、AdminContentEditor.vue、AdminPlatforms.vue | MOD-059 / IFC-237 |
| miniprogram/components/RichBlocks.vue | MOD-061 / IFC-238 |

## 自验证结果

环境：`/tmp/claude-0/-root-myproject-ocap/c20123b9-4e57-4ebf-b3eb-04a35210d0d9/scratchpad/venv/bin/python`（Python 3.12.3，Django 5.2.19）；未安装任何新包。

```
(cd backend && python manage.py check --settings=config.test_settings)
-> System check identified no issues (0 silenced).

(cd backend && python manage.py makemigrations --check --dry-run --settings=config.test_settings)
-> No changes detected

(cd backend && python -m compileall -q .)  -> 无输出（通过）

(cd backend && python manage.py test --settings=config.test_settings)        # 无任何临时补丁
-> Ran 430 tests in 27.153s / FAILED (failures=4, errors=1)
   分层：unit 102（1 FAIL）／integration 293（3 FAIL + 1 ERROR）／e2e 29 OK／smoke 6 OK
   失败项（全部为有意行为变化，见"现有测试调整"）：
   FAIL  tests.unit.test_content_core.SceneTests.test_tc_unit_333_single_paragraph
   FAIL  tests.integration.test_content_api.PostApiTests.test_tc_int_309_invalid_doc_rejected
   FAIL  tests.integration.test_content_api.AiAndDraftTests.test_tc_int_327_platform_account_crud_and_mask
   ERROR tests.integration.test_content_api.AiAndDraftTests.test_tc_int_330_draft_requires_confirmed_and_selection
   FAIL  tests.integration.test_content_api.BranchCoverageTests.test_tc_int_341_platform_account_delete
   （含既有 test_frontend_contract.py：通过）

(cd frontend && npx vitest run --passWithNoTests)
-> Test Files 15 passed (15) / Tests 131 passed (131)
(cd frontend && npm run build -- --base=/ocap/)
-> ✓ built in 31.61s
(cd miniprogram && npx vitest run --passWithNoTests)
-> Test Files 11 passed (11) / Tests 71 passed (71)
```

首轮前端测试曾因 `frontend/tests/theme.spec.js`（.vue 文件禁止颜色字面量，ADR-029）失败 1 项，已把调色板移到 `colors.js` 并改写注释后复跑全绿。

补充自验证（**不入库**，脚本在会话临时目录 `…/c20ec81e-1d59-412a-9a62-f130112cd4d7/scratchpad/scratchtests/scratch_content.py`，17 个用例 OK）：共享颜色向量、宽容模式规则与 block_index、渲染三项、分镜、令牌缓存/提前量/冷却/强制刷新/锁忙/凭据覆盖失效/IP 与 auth 分类、适配器重发一次/NETWORK 不重发/IP 不重发/NO_CREDENTIALS、`mark_expired` 只写一次审计、全人工批次与无凭据批次各 1 条审计、worker 经 `--once` 的混合批次恰 1 条审计（含 3 行）、素材删除审计、默认标题、导出前后 `tempfile.gettempdir()` 无新增文件、`--concurrency` 报错、视频全有或全无、心跳用当前时间。前端：`colors.js` 共享向量全部一致；`pasteGuard.js`、`RichEditor.vue` 经临时 vitest（已删除）验证——`rgb()/rgba()` 解析为十六进制、`<h5>` 降为段落、外链 `<img>` 被移除并发出 `paste-dropped`。

**未验证**：
- Python 3.13（本机只有 3.12；CI 为 3.13）。F01 的根因（类体内成员遮蔽内建）在 3.12 已能复现并已消除，3.13 行为同 3.12，但仍须 CI 复核。
- 0002 迁移未在 MySQL 上执行（P8 禁止连接测试机库）；`makemigrations --check` 无漂移。
- 小程序 `uni build -p mp-weixin`（记忆 M-SD-006：开发机工具链不可用，不属本次改动引入）。
- 任何真实微信接口（P11-3 禁止）；`HttpWechatMpApi` 仅有代码对照出处，无自动化覆盖。

## 按模块评审

### MOD-044 素材库（F01、F03）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-009 | CRITICAL | media.py（原 :179/:212） | GR-C-002-F01：类体内 `list` 遮蔽内建，3.12/3.13 导入即 TypeError | FIXED（改名 `list_items`，调用点 views_admin 同步；未加 `from __future__ import annotations`） |
| CR-010 | MINOR | media.py:delete | 文件删除放在 `transaction.on_commit`，Django `TestCase` 内不会执行回调，测试需 `captureOnCommitCallbacks(execute=True)` | OPEN（行为符合设计"提交前不删文件"） |

### MOD-042 富文本引擎（F04、F07）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8.5/10 | 9/10 | 8/10 | 7.5/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-011 | MINOR | richtext/schema.py:_norm_node | 严格/宽容两种模式共用一个函数并用 `ctx is None` 区分，分支较多；已用共享函数 `_to_line_height`/`_absent` 收敛 | OPEN |
| CR-012 | MINOR | richtext/schema.py | 顺带修复 `{"type": []}`（不可哈希类型）会 `TypeError`→500 的既有缺陷（现按 `TYPE` 处理） | FIXED |

安全：白名单未放宽。归一化后的颜色再次满足 `COLOR_RE`（`normalize_color` 内断言）；`javascript:` 链接在宽容模式下丢弃标记，输出中不存在；外链/`data:` 图片整节点丢弃，不下载不转存；结构/限额错误仍 400 并带 `block_index`/`block_type`。

### MOD-062 / MOD-063 公众号令牌与接口客户端（F06 / ADR-060）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 8.5/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-013 | MAJOR | wechat_token.py、conf.py | `auth_errcodes`/`token_errcodes` 取值无出处（Q-B1），缺省 `[]`：真实环境 AppSecret 错误只表现为 `UPSTREAM`，**不会自动标失效**（AC-127-03 仅替身可验）；草稿令牌类错误只在 HTTP 401/403 或"令牌取自缓存且有非零 errcode"时重取一次 | OPEN（等待用户提供官方文档，Q-B1；建议处理时机：用户给文档后回 GROUP_B 定稿 ADR-061 再增量开发） |
| CR-014 | MINOR | wechat_token.py:get_token_ex | 未抢到锁时在 worker 内 `time.sleep` 至多 10 秒（常量 `LOCK_WAIT_SECONDS`/`LOCK_POLL_SECONDS` 可被测试替换）；worker 单线程，阻塞可接受 | OPEN |

安全：令牌与凭据均不入日志/审计/序列化；`token_*` 列不被任何序列化器输出（`platforms._out` 只输出 `secret_saved`）；HTTP 层异常只用 `SecretRedactor([secret, token])` 与 `redact_url` 构造，`raise … from None` 避免异常链回显 URL；`PlatformAccountService.update` 只写本次改动列，避免整行 `save()` 覆盖 worker 并发写入的令牌列。

### MOD-049 / MOD-050 草稿适配器与替身
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8.5/10 | 7.5/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-015 | MAJOR | draft.py:WechatMpDraftAdapter.save_draft | ADR-061 封面/正文图片上传**未实现**（阻塞 Q-B1）：开关缺省关闭；`HttpWechatMpApi.upload_*` 抛 `NotImplementedError("UNSOURCED: Q-B1")`；若管理员在设置页误开开关，推送将返回 `IMAGE_UPLOAD_FAILED` 而不发草稿。公众号草稿若在真实账户下要求封面，当前也无法满足 | OPEN（同 CR-013，等待 Q-B1） |
| CR-016 | MINOR | draft.py:set_draft_adapter | 既有行为：`set_draft_adapter(platform, None)` 是把适配器从注册表删除而非恢复默认，之后 `get_draft_adapter` 抛 `KeyError`。本次未改（设计 IFC-180 如此描述） | OPEN |

### MOD-053 平台账户 / 草稿 / 导出（F03、F05）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8.5/10 | 9/10 | 8/10 | 8/10 | 8.5/10 |

无新增问题。要点：`start_batch` 在 `transaction.atomic` 内建行并入队，无自动行时同事务写 1 条批次审计；`audit_batch` 以 `AuditLog(action, object_id)` 幂等，`detail` 不含 `error_message`；`build_zip` 用 `tempfile.TemporaryFile`，任何异常 `close` 后重抛，审计在 zip 构建成功后写入。

### MOD-052 / MOD-046 / MOD-057（F07）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8.5/10 | 9/10 | 9/10 | 8/10 | 8/10 |

无新增问题。要点：分镜按 `extract_paragraphs`；视频片段先 CANDIDATE，全成功后同事务转 SAVED，失败 `MediaService.discard` 回收；`heartbeat` 用 `timezone.now()`；worker 去掉 `--concurrency`，`JobRun` 心跳 ≤ 60 秒/次。

### MOD-059 / MOD-061 前端与小程序（F02、F04、F07）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 8.5/10 | 8.5/10 | 8/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-017 | MAJOR | frontend/tests、miniprogram/tests | 本次新增的前端/小程序逻辑（`colors.js`、`pasteGuard.js`、`contentText.js`、`saveDraft` 返回值与发布/确认中止、RichBlocks 行距/装饰线）**没有入库的自动化用例**（开发不新增测试，仅用临时脚本验证）；`rich_colors.spec.js`/`rich_paste_guard.spec.js`/`rich_blocks.spec.js` 追加用例留给 GROUP_D | OPEN（GROUP_D） |
| CR-018 | MINOR | frontend/src/admin/editor/pasteGuard.js | 与 IFC-242 偏差：保留带 `data-media-id` 的 `<video>`（编辑器自身输出），见 implementation_plan"架构偏差" | OPEN（需 GROUP_B 确认或接受） |
| CR-019 | MINOR | AdminContentEditor.vue:saveDraft | 保存带警告时用服务端返回的规范化文档替换编辑器内容，编辑光标位置会重置 | OPEN |

安全：颜色字面量均不在 `.vue` 中（遵守 ADR-029 守护测试）；`v-html` 仍只渲染服务端转义输出；粘贴守卫基于 `DOMParser`，不发网络请求。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

共 3 条（CR-013、CR-015、CR-017），不超过 3 条，仍逐条说明：
- CR-013 / CR-015：外部事实无出处（Q-B1，协议 §N-2，不得自行补全）；建议时机：用户提供微信官方文档、登记画像 P11-3 后，GROUP_B 定稿 ADR-061，再增量开发。
- CR-017：开发职责不含新增测试；建议时机：本轮 GROUP_D。

## 缺陷修复

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| GR-C-002-F01 | media.py:`MediaService.list_items`（原 `list`）；views_admin.py:`MediaListView.get` | 类体内 `staticmethod` 名 `list` 遮蔽后文注解 `list[...]`，3.12/3.13 在类体求值注解时报 TypeError（3.14 延迟注解不暴露） | 改名 `list_items` 并改唯一调用点；Python 3.12 下全量测试原样运行 |
| GR-C-002-F02 | AdminContentEditor.vue:`saveDraft`/`publish`/`confirmText` | `saveDraft` 吞掉异常且无返回值，调用方不知失败 | `saveDraft` 返回 true/false；失败即中止发布/确认；400 `CONTENT_INVALID_DOC` 带位置提示 |
| GR-C-002-F03 | media.py:`MediaService.delete`；drafts.py:`DraftPushService.start_batch/audit_batch`、`DraftPushHandler`；platforms.py:`mark_expired`；audit.py | 审计动作登记了但漏调用；批次审计只在 worker 中且按任务汇总 | 按 IFC-188 落点表补齐三处审计，批次审计按 `batch_id` 汇总全部行、幂等 |
| GR-C-002-F04 | richtext/schema.py（`validate_doc_ex`、`normalize_color`）；posts.py；views_admin.py；Toolbar.vue、RichEditor.vue、colors.js、pasteGuard.js、contentText.js | 样式类问题一律整篇 400；颜色为文本框；粘贴来源的 `rgb()`/外链图片/`h5` 无处理 | 服务端宽进严出 + warnings；前端取色器、粘贴守卫、标题 1–4 级、提示文案 |
| GR-C-002-F05 | export_pack.py:`build_zip` | `NamedTemporaryFile(delete=False)` 永不删除 | 匿名 `TemporaryFile`，异常路径关闭 |
| GR-C-002-F06 | wechat_mp.py、wechat_token.py、draft.py、platforms.py、models.py、0002、conf.py、fakes.py、AdminPlatforms.vue | 令牌手工录入会过期；失效口径依赖无出处的 errcode | 按 ADR-060 实现 AppID/AppSecret + 加密缓存 + 单飞 + 强制刷新重发一次 + IP 白名单分类；ADR-061 仅占位（见 CR-013/015） |
| GR-C-002-F07 | render.py、RichBlocks.vue、convert.py、ai_jobs.py、jobs.py、run_content_worker.py、posts.py、AdminContentEditor.vue | 见 GR-C-002 F07 清单 | 行距、深层媒体、装饰线合并、分镜按段落、下载全有或全无、单线程 worker、心跳 60 秒/当前时间续租、默认标题、延后 revoke、中文状态 |

## 现有测试调整

本次**没有修改任何测试代码**。以下 5 个既有用例因有意的行为变化失败，需 test-engineer 更新（行为依据均为 architecture 2.0.0）：

1. `tests.unit.test_content_core.SceneTests.test_tc_unit_333_single_paragraph`：`build_scenes` 入参由整篇文本改为段落列表（IFC-184 1.1.0），传字符串时被按字符迭代。同文件 `test_tc_unit_332_build_scenes_merges_to_limit` 碰巧仍通过（字符串迭代后合并到上限），但也应改为传段落列表；并补"空列表→POST_INCOMPLETE"。
2. `tests.integration.test_content_api.PostApiTests.test_tc_int_309_invalid_doc_rejected`：非法链接（`javascript:`）在宽容模式下改为"丢弃链接标记 + `warnings`"，返回 201 而非 400（ADR-062）。应改断言：201、`warning_total==1`、保存后的 doc 中无 link 标记；另加结构类错误（如 `content` 非数组）仍 400 且带 `block_index`/`block_type`。
3. `test_tc_int_327_platform_account_crud_and_mask`、`test_tc_int_341_platform_account_delete`：公众号凭据键由 `access_token` 改为 `appid`/`appsecret`（旧键返回 400 `INVALID_VALUE`，`details.key`）。
4. `test_tc_int_330_draft_requires_confirmed_and_selection`：同上（创建账户时用旧键，随后取 `account["id"]` 报 KeyError）。

另提示：`MediaService.delete` 的文件删除改为 `transaction.on_commit`，涉及文件是否被删的用例需 `captureOnCommitCallbacks(execute=True)`。

## DEF-014~016 修复（2.1.0）

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-014 | posts.py:`PostService.render_for_member` | 前缀剥离只遍历 `page["blocks"]` 顶层，`children`（引用）与 `items`（列表项为块列表）里的媒体 src 漏处理，小程序再拼 BASE 后成 /api/v1/api/v1/… | 递归 `_strip`（children、items 逐项），非 dict 跳过 |
| DEF-015 | RichEditor.vue:`requestLink` | `!url` 把 prompt 取消(null)与确定但空('')合并为静默 | 仅 `url === null` 静默；空串走"网址无效"提示 |
| DEF-016 | AdminContentEditor.vue:`pushDrafts`、按钮 | 按钮被 `:disabled` 禁用，用户得不到文案提示 | 按钮可点；未选平台提示"请至少选择一个平台"并不发请求 |

自评审：改动共 3 文件约 +20/-4 行，无 CRITICAL/MAJOR/MINOR 新增（CR 新增 0）；五维不变（Correctness 9、Security 9、Performance 9、Maintainability 9、Testability 9）。

自验证（Python 3.12 venv，原样无补丁）：
- 后端 `manage.py check` → no issues；`makemigrations --check --dry-run` → No changes detected；全量 `Ran 519 tests ... OK`（TC-INT-388 转通过）。
- 前端 `vitest run`：154 中 153 通过、1 失败；`npm run build -- --base=/ocap/` 成功；TC-UNIT-393 转通过。
- 小程序 `vitest run`：75/75 通过。

现有测试调整（未改测试代码，留给 test-engineer）：`frontend/tests/content_editor.spec.js` 的 TC-UNIT-404（“未勾选任何平台时‘开始保存’不可用，不发起保存”）断言按钮 disabled，与 DEF-016（AC-128-04 要求可点击并提示）冲突，现失败；应改为：按钮可点击，点击后 `ElMessage.warning('请至少选择一个平台')` 被调用且 `adminHttp.post` 未调用。这是本次唯一新增失败，且由已授权的 DEF-016 有意行为变化导致。
