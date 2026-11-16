<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-15T21:34:39+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>0.1.0</version>
  <input_files><file>phase_status.md</file><file>deployment/deployment_report.md</file></input_files>
  <phase>PHASE_09,PHASE_11b</phase>
  <status>DRAFT</status>
</file_header>

# 上报：缺陷回流已达上限（GROUP_D defect_loops = 2）

## 触发
GROUP_E2-003 远程 HTTP E2E（线上 3ffd868）：Ran 22，19 通过、2 失败（TC-E2E-321、TC-E2E-324）、1 跳过（TC-E2E-332，UC-07）。夹具已清理，PM 只读复核 e2e 计数全 0、清册计数与基线一致。

## 缺陷
| ID | 位置 | 级别 | 说明 |
|---|---|---|---|
| DEF-A | backend/apps/identity/services.py:48；backend/apps/residency/housing.py:41；backend/tests/remote/remote_cases.py:77-83 | MAJOR | /me 与 /me/housing 房屋行排序口径不同（specific_part vs certified_at），违背 AC-157-01"顺序不变"；用例同时期望过期文案"户主" |
| DEF-B | backend/tests/remote/remote_cases.py:114 | MINOR | 期望"户主"，产品按 C-46（原 C-34）显示"产权业主"，属测试期望过期 |

根因：合并 ocap_identity_display 时只调整了默认测试集中的断言，backend/tests/remote 不在 CI 与默认测试命令中，未同步。

## 门控记录
GR-C-merge-001（OVERRIDDEN）、GR-E2-001（PASS_WITH_CONDITIONS）、GR-E2-002（FAIL），见 phase_status.md。

## 可选操作
1. 继续修复（推荐）：第 3 轮回流，RA 注记 AC-157-01/02 → SA 定排序口径并同步编号/ADR 文字 → SD 统一排序 → TE 修正远程用例并补本地跨视图顺序用例；之后重新部署与远程 E2E 需用户另行授权。
2. 只修测试期望（DEF-B 与 DEF-A 的文案部分），排序差异记为遗留问题。
3. 接受现状（OVERRIDDEN），在交付报告中列为遗留。
4. 终止。
