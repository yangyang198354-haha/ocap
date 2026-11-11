<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T00:29:19+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.0.0</version>
  <input_files><file>development/implementation_plan.md</file><file>architecture/module_design.md</file><file>architecture/architecture_design.md</file><file>testing/test_plan.md（待 GROUP_D 生成）</file></input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：信息公开与多平台内容中心（GROUP_C）

## 摘要

- 范围：MOD-039~061，后端 30 个新文件 + 6 个既有文件修改；前端 12 个新文件 + 4 个修改；小程序 4 个新文件 + 3 个修改；1 个 systemd 单元模板。
- 自验证：后端 `Ran 327 tests / OK`；`makemigrations --check` 无漂移；前端 `npm run build` 成功（9.74s）；前端 vitest 124 passed / 2 既有环境失败；小程序 69 passed；临时 API 冒烟 9 项全部符合预期（201/200/400 安全拒绝）。
- 结论：无未解决 CRITICAL；2 条 MAJOR（测试覆盖与真实外部联调）、6 条 MINOR 已在报告中列明。

## 五维评分

| 维度 | 分数 | 依据 |
|---|---|---|
| 正确性 | 8.5 | 112 条 AC 均有实现位置；状态机、分页、重复导入类边界按设计实现；冒烟验证创建/预览/发布/会员读取/非法链接拒绝 |
| 安全性 | 8.5 | 富文本白名单 + html.escape；签名 URL + Range；凭据 AES-GCM + 只写不读 + SecretRedactor；媒体下载拒绝私网/非 https；未发现注入点 |
| 可维护性 | 8.5 | 模块按设计分层，纯函数 richtext 与业务分离；类型/常量集中；少量重复（绝对/相对 URL 处理） |
| 性能 | 8.0 | 任务队列按索引领取、批量上限 5；素材上传分块；列表全部分页；`MediaService` 配额统计为全表求和（素材量大时需优化） |
| 测试 | 7.5 | 既有 327 用例全绿；本批新增功能尚无专属用例（GROUP_D 负责）；前端仅构建校验，无新组件测试 |
| **平均** | **8.2** | — |

## 发现清单

| ID | 级别 | 位置 | 问题 | 处理 |
|---|---|---|---|---|
| CR-001 | MAJOR | `backend/apps/content/ai_jobs.py`、`drafts.py` | 外部服务链路（LLM/文生图/视频/草稿）只有替身接口，尚无自动化用例验证任务状态机与失败分支 | 转 GROUP_D：用 MOD-050 替身覆盖成功/失败/中断/重试 |
| CR-002 | MAJOR | `backend/apps/content/media.py:90-100` | 配额预检按「已用 + 本次文件上限」求和，可能对接近配额的文件过度拒绝；且 `sum()` 全表扫描 | 已记录；GROUP_D 加边界用例，后续可改为增量统计 |
| CR-003 | MINOR | `backend/apps/content/richtext/render.py` | 引用块内的图片/视频被替换为标题文本，非「素材已删除」语义 | 已记录，当前不影响 AC-107/108 的主路径 |
| CR-004 | MINOR | `backend/apps/content/platforms.py:96-100` | 新建账户先以临时 context 加密再重加密，多一次加解密 | 可接受；AAD 必须绑定真实 id |
| CR-005 | MINOR | `frontend/src/admin/AdminContentEditor.vue` | 链接输入使用 `window.prompt`，样式与体验弱；未处理批量选择平台的空账号边界样式 | 可用实现；GROUP_D 只验证行为 |
| CR-006 | MINOR | `frontend/src/admin/AdminContentSettings.vue` | 列表参数以 JSON 文本编辑，输入非法 JSON 时保留文本但不阻断保存 | 后端会 400，前端提示错误 |
| CR-007 | MINOR | `backend/apps/content/conf.py:59-66` | `_valid` 的 int 分支残留 image_exts 死分支 | 不影响行为，可后续清理 |
| CR-008 | MINOR | `backend/apps/content/views_member.py` | 媒体签名校验仅 `verify_media_sig`，未限制 CANDIDATE 的签名访问（设计允许签名即授权） | 与 ADR-052 一致，待用户确认 A-4 |

无 CRITICAL（无越权、无 XSS 注入、无凭据泄露、无不可恢复的数据破坏路径）。

## 安全自查

- **XSS**：`richtext.schema.validate_doc` 白名单节点/属性；`render_html` 对所有文本与属性 `html.escape`；链接仅允许 `http/https/mailto/tel`；`javascript:` 冒烟返回 400 `CONTENT_INVALID_DOC`。
- **凭据**：`CredentialVault` AES-256-GCM + AAD；接口只返回 `secret_saved` 布尔；审计只记录键名；`SecretRedactor` 用于所有外部异常文本。
- **媒体**：`HttpRemoteFetcher` 仅 https、拒绝私网/环回/链路本地、不跟随重定向、超限即停；本地文件响应 `nosniff` + 签名 URL。
- **权限**：管理端全部 `IsAdmin`；用户端 `IsMember`；媒体文件按签名授权（无 Authorization 头）。
- **未发现**：SQL 注入（ORM）、命令注入（无 shell）、路径穿越（storage_path 由服务端生成）。

## 自验证命令与结果

```
python manage.py check --settings=config.test_settings
-> System check identified no issues (0 silenced)

python manage.py makemigrations --check --dry-run --settings=config.test_settings
-> No changes detected

python manage.py test --settings=config.test_settings
-> Ran 327 tests in 4.518s / OK

npm run build -- --base=/ocap/   (frontend)
-> ✓ built in 9.74s（新增 Tiptap 依赖 48 packages）

npx vitest run   (frontend)
-> Tests 2 failed | 124 passed (126)（theme_build / theme.spec 既有环境失败）

npx vitest run   (miniprogram)
-> Test Files 10 passed / Tests 69 passed (69)

临时冒烟（test client，run_syncdb）
-> CREATE 201 / PREVIEW 200 / PUBLISH 200 / MEMBER_DETAIL 200 (page_count=2)
-> BAD_LINK 400 CONTENT_INVALID_DOC / SERVICES 200 / PLATFORMS 200 / SETTINGS 200
```

## 遗留与交接

1. GROUP_D 需按 `testing/` 规划补后端 unit/integration/e2e 与前端/小程序用例，外部服务只用 `Fakes`。
2. `cryptography` 已加入 `backend/requirements.txt`，本机未安装；测试若需真实加解密，应 `pip install -r requirements.txt` 或用 `DJANGO_ALLOW_EPHEMERAL_SECRET` 下的随机钥（测试设置已具备）。
3. 部署（E1）需新增 `ocap-content-worker` 单元、`.env` 4 个键、磁盘/nginx/gunicorn 核实；与 GR-B-001-F02 一致。
4. 前端 `dist/`、`node_modules`、`miniprogram/package-lock.json` 不提交或按团队约定处理（`dist` 已在 .gitignore）。
