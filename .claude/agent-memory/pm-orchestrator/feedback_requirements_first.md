---
name: feedback-requirements-first
description: ocap 项目：需求分批输入，未经用户明确说"开始"前只做需求整理（PHASE_01/02），不进入设计、开发
metadata:
  type: feedback
---

需求分批输入。流程：每批需求先整理（PHASE_01），用户确认后再整理成用户故事（PHASE_02）；不得启动 GROUP_B 及以后的阶段，直到用户明确说"开始"。

**Why:** 用户原话（2026-11-07）："先整理这些需求。确认后再整理成用户故事。但是不要开始设计、开发。我把所有的需求输入完毕后。我让开始再开始。"

**How to apply:** 调用 requirement-analyst 时拆成两步（先 PHASE_01，用户确认后 PHASE_02），special_instructions 注明"增量追加需求、不做技术设计"；GROUP_A 门控通过后停住，不调用 system-architect。技术选型、代码复用参考用户 GitHub 上的 Freeark 项目（yangyang198354-haha/Freeark，本地 /root/myproject/Freeark）。
