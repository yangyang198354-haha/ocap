<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T00:42:04+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（PHASE_07）

## 摘要

- 执行时间：2026-11-11 00:36–00:42（Asia/Shanghai）
- 环境：Python 3.14.6、Django 6.0.6；`config.test_settings`（SQLite 内存库）；前端/小程序 vitest
- 范围：后端 `tests.unit` 98 个（本批新增 36）+ `frontend/tests/content_api.spec.js` 3 个 + `miniprogram/tests/rich_blocks.spec.js` 2 个
- 命令：
  - `python manage.py test tests.unit --settings=config.test_settings`
  - `npx vitest run tests/content_api.spec.js`（frontend）
  - `npx vitest run tests/rich_blocks.spec.js`（miniprogram）

**metrics**：total = pass + fail + skip + blocked + not_testable = 103 = 103 + 0 + 0 + 0 + 0

通过率 = pass / (pass + fail + blocked) = 103 / 103 = **100%**；本层门控：**PASSED**（baseline 零新增失败）

## 执行输出

```
$ python manage.py test tests.unit --settings=config.test_settings
Ran 98 tests in 0.313s
OK

$ npx vitest run tests/content_api.spec.js   # frontend
Test Files 1 passed (1) / Tests 3 passed (3)

$ npx vitest run tests/rich_blocks.spec.js   # miniprogram
Test Files 1 passed (1) / Tests 2 passed (2)
```

## 分项结果

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-UNIT-301~308 | AC-109-03、AC-110-01、AC-112-03、AC-107-04 | 文档白名单：未知节点/属性、脚本链接、颜色/字号/行距、媒体 UUID、字节上限、标题层级 | PASS |
| TC-UNIT-309~315 | AC-107-01、AC-109-01、AC-109-02、AC-111-01 | 渲染：转义、对齐/加粗、链接安全属性、素材缺失与解析、列表、纯文本 | PASS |
| TC-UNIT-316~320 | AC-113-01~04、AC-128-03 | 分页（分页标记/页长/单页）、文本转文档、媒体提取、平台不支持特征 | PASS |
| TC-UNIT-321~325 | AC-117-02、AC-125-02、AC-127-02 | AES-GCM 加解密、AAD 校验、密钥格式、脱敏与 URL 脱敏 | PASS |
| TC-UNIT-326~328 | AC-112-04、AC-100-01（参数） | 参数默认/范围/非法库值回落、confirmed 标记 | PASS |
| TC-UNIT-329~331 | AC-112-01~03 | 内置模板、令牌校验、自定义模板 CRUD/重名 | PASS |
| TC-UNIT-332~334 | AC-124-01、AC-114-01 | 分镜合并、单段、system 提示语气/篇幅 | PASS |
| TC-UNIT-335~336 | AC-123-01 | Range 解析与非法 Range | PASS |
| TC-UNIT-341~343 | AC-105-01、AC-116-02、AC-128-05 | 前端 API 方法/路径/参数（文章、素材、服务、平台、草稿、导出、用户端） | PASS |
| TC-UNIT-344~345 | AC-108-01、AC-108-04 | 小程序块渲染（段落/标题/图片/引用）与链接复制 | PASS |

## 与基线对比

| 项 | 基线 | 本次 | 结论 |
|---|---|---|---|
| 后端单元 | 62 OK | 98 OK | 新增 36 全通过 |
| 前端新增 | — | 3 passed | 无失败 |
| 小程序新增 | — | 2 passed | 无失败 |

## 失败汇总

无。

## 备注

- 前端/小程序的编辑器工具栏、弹窗确认、撤销/重做属纯 UI 交互，未做组件级断言，已在 test_plan「不可测项」标注。
- 外部服务未调用真实端点，仅使用 `Fakes`。
