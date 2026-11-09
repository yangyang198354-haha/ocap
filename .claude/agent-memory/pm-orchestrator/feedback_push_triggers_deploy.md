---
name: feedback-push-triggers-deploy
description: 推送任何仓库（尤其跨项目批量推送）前，先读该仓库画像 P7/P8 与 .github/workflows 的 push 触发条件；push 触发生产部署时，"推送"授权不等于部署授权
metadata:
  type: feedback
---

推送任何仓库前，先读该仓库的 `.claude/agents/project_profile.md` P7/P8，并检查 `.github/workflows/*.yml` 中 `on: push` 是否会触发部署 job。会触发生产部署时，必须单独向用户说明"这次 push 会部署生产"，取得 E2 同级的当轮授权后才推；否则改推非 main 分支或不推。

**Why:** 2026-11-09 批量分发 SDLC 套件 v3.9 时，用户说"提交并推送"，PM 没读 GenPlatform 画像就推了 main。GenPlatform 画像 P7 明确写"git push origin main 本身就是一次生产部署"，P8 禁止未授权 push main。结果触发了 run 42552003937 的 deploy-physical-prod（production 环境无审批保护），部署完成，冒烟测试 3 PASS / 1 FAIL（前端首页无 HTML）。取消 run 的尝试被权限策略拒绝。

**How to apply:** 跨项目批量 commit/push 前，对每个仓库逐个做推送前检查（画像 P7/P8、workflow 触发条件、environment 保护规则），把"会触发部署的仓库"单列出来请用户分别确认。相关：[[Requirements first]]。
