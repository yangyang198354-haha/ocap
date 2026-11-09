# Claude SDLC → Codex 迁移说明

源版本：SDLC Agent Suite **v3.8**。本文说明 Codex 分发的组成、验证方式与已知限制；逐文件哈希与源提交记录在 `.codex/sdlc/migration_manifest.json`。

## 分发内容

| 内容 | 落点 | 说明 |
|---|---|---|
| 8 个角色 | `.codex/agents/*.toml` | `name` / `description` / `developer_instructions`；保留源文档全部编号章节 |
| PM 主会话入口 | `AGENTS.md`、`.codex/sdlc/pm-orchestrator.md` | 在当前主会话执行；不存在 `codex --agent` |
| 协议、画像、模板、知识库 | `.codex/sdlc/` | 由 `.claude/agents/` 迁移；哈希逐项登记 |
| 角色项目记忆 | `.codex/agent-memory/{role}/MEMORY.md` | SessionStart / SubagentStart hook 注入前 200 行；缺失时显式读取 |
| 运行时适配 | `.codex/sdlc/runtime_adapter.md` | 工具映射、Windows/POSIX 命令、权限继承、hook 兜底 |
| **生命周期 hook** | `scripts/codex_sdlc/hook_runtime.py` | `memory` / `pre-agent` / `web` / `tools` / `stop` 五种模式；`.codex/hooks.json` 通过仓库根解析后调用 |
| agent-builder 文档读取 | `scripts/codex_sdlc/fetch_docs.py` | 固定 8 个官方页面，检查完整 URL 与每次重定向；不接受自定义 URL、查询参数或搜索词 |
| 迁移工具 | `scripts/codex_sdlc/migrate.py` | `build` 生成到 `output/codex-migration/`；`install` 校验 hash、备份后安装 |
| 验证工具 | `scripts/codex_sdlc/verify_migration.py`、`test_hooks.py`、`probe_runtime.py` | 静态覆盖校验、离线行为测试、只读运行时探测 |

## 验证

```text
python scripts/codex_sdlc/test_hooks.py
python scripts/codex_sdlc/verify_migration.py
python scripts/codex_sdlc/probe_runtime.py --output output/codex-runtime-probe.json
```

- `test_hooks.py`：离线覆盖 cwd 守卫、角色边界、记忆位置与截断、响应校验与补齐次数（含 PM 的 `<pm_report>`、按角色的 `<evidence>` 必填）、apply_patch 写路径守卫、脱敏、去重、transcript fallback、URL/重定向拒绝。不依赖 Codex CLI。
- `verify_migration.py`：核对源/目标 hash（换行归一化）、TOML 结构、章节完整性、结构化返回、路径引用（画像、记忆、`.agents/skills/` 允许缺失）、两份 PM 定义一致，并在 PATH 上有 `codex` 时用 `codex execpolicy check` 逐条核对规则（否则标 SKIPPED）。`.claude/settings.json` 缺失时回退 `settings.example.json`；`--no-write` 只打印结果。
- `probe_runtime.py`：只读查询 app-server 的 `features.hooks` 与 hook 列表，不信任 hook、不启动模型回合。
- 以上均不能证明 hook 已在真实会话中触发；`migration_manifest.json` 的 `runtime_activation` 保持 `PENDING_USER_HOOK_TRUST_AND_REAL_SESSION_VALIDATION`，直到完成下节验收。

## 未完成的运行时验收

1. **信任**：在仓库根运行 Codex，打开 `/hooks` 审阅并信任 `.codex/hooks.json` 中的定义；重新加载会话以读取最新角色定义。
2. **真实生命周期**：新会话调用一个阶段子代理，用最小非生产任务核验 SubagentStart 记忆注入、PreToolUse 目录拒绝、SubagentStop 响应补齐与收件箱写入；不得用模拟事件代替。
3. **工具强隔离缺口**：Codex 自定义角色没有 Claude `tools` 的等价完整白名单，托管 WebSearch 不经过 PreToolUse。需求/架构保留公开搜索；其他角色与 agent-builder 依靠提示词、能力开关、受覆盖的工具 hook 和受限读取脚本共同约束，不能宣称所有特殊路径都被拦截。
4. **失败行为**：hook 异常沿用 fail-open 并给出可见提示，不是 fail-closed 安全边界；PM 仍须核对返回、必读清单与收件箱。
5. **写路径守卫**：PreToolUse 只能解析 apply_patch 的目标路径；`exec_command` 内的 shell 写入无法拦截，§A 的产物目录边界仍由 PM 门控核对。

## 维护与回退

```text
python scripts/codex_sdlc/migrate.py build    # 生成到 output/codex-migration/
python scripts/codex_sdlc/migrate.py install  # 逐文件校验、备份、安装
```

`build` 从 `.claude/agents/INSTALL.md` 解析版本号，因此先同步 Claude 源。`install` 不删除目录、不改全局设置、不覆盖已有 Codex 项目记忆；回退按清单恢复旧文件。知识库、画像与模板的建议改动应先人工合并。

平台依据：[自定义子代理](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[hooks 与信任](https://learn.chatgpt.com/docs/hooks)、[命令规则](https://learn.chatgpt.com/docs/agent-configuration/rules)。
