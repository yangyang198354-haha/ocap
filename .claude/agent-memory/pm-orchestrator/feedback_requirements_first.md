---
name: feedback-requirements-first
description: ocap 项目：需求分批输入、逐阶段放行；用户明确放行前不进入下一大阶段（2026-11-07 已放行架构设计，未放行开发）
metadata:
  type: feedback
---

需求分批输入。流程：每批需求先整理（PHASE_01），用户确认后再整理成用户故事（PHASE_02）。后续大阶段需用户逐一明确放行：
- 2026-11-07 用户原话："先开始进行架构设计，但是不要开发" → 已放行 GROUP_B；**未放行 GROUP_C（开发）**。

**Why:** 用户原话（2026-11-07）："先整理这些需求。确认后再整理成用户故事。但是不要开始设计、开发。我把所有的需求输入完毕后。我让开始再开始。" 之后又逐步放行。

**How to apply:** GROUP_B 门控通过后停住，不调用 software-developer，等用户明确说开始开发。调用 requirement-analyst 时拆成两步（先 PHASE_01，用户确认后 PHASE_02）。技术选型、代码复用参考用户 GitHub 上的 Freeark 项目（yangyang198354-haha/Freeark，本地 /root/myproject/Freeark）。提交 git 需用户在当轮明确同意（用户曾说"提交"一次，不可复用）。
