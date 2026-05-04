# 批次调度策略

## 何时启用subagent

只有任务单元之间相互独立、写入目标互不覆盖时才启用subagent。适合并行的任务包括：

- `extract-docs`：按模块分析。详见 [`../subagents/extract-docs.md`](../subagents/extract-docs.md)
- `generate-module-docs`：按页面计划项或模块页面生成。详见 [`../subagents/generate-module-docs.md`](../subagents/generate-module-docs.md)
- `quality-fix`：质量修复，按 Basic 文档或失败模块定向重生成。详见 [`../subagents/quality-fix.md`](../subagents/quality-fix.md)

不适合并行的步骤包括初始化、全局结构提取、架构骨架生成、分析校验、文档拓扑规划、菜单生成和 finalize 聚合检查；这些步骤需要全局一致输入或写同一个聚合文件，应串行执行。

| 模块总数 | 策略 |
|---------|------|
| ≤ 5 | 串行（单 Agent 顺序处理） |
| 6–15 | 并行推荐（每批 `{config.generation.scheduling.batch_size}` 个模块） |
| > 15 | 并行必须（按重要性/优先级排序分批，每批 `{config.generation.scheduling.batch_size}` 个） |

## 批次控制

- **Subagent 拆分上限**：任何阶段最多同时拆分 `{config.generation.scheduling.max_subagents}` 个 subagent（默认 6，可按项目调整），不得超出此限制
- **分批串行等待**：若任务总数 > `{config.generation.scheduling.max_subagents}`，必须分批处理；**前一批所有 subagent 全部执行完成后，才能派遣下一批 subagent**，严禁提前启动
- **批次大小**：每批最多 `{config.generation.scheduling.batch_size}` 个模块（默认 6）
- **排序依据**：模块 `importance_score`（extract-docs）或 CodePurpose 优先级（generate-module-docs）降序
- **自动继续**：不暂停，不需要用户确认

## 进度追踪

使用 `state/progress.json` 追踪每个模块的处理状态：

```json
{
  "phases": {
    "<phase>": {
      "status": "in_progress",
      "mode": "subagent",
      "modules": {
        "core": {"status": "completed", "agent": "subagent-1"},
        "auth": {"status": "in_progress", "agent": "subagent-2"},
        "api":  {"status": "pending"}
      }
    }
  }
}
```

状态转换：`pending` → `in_progress` → `completed` / `failed`

## 串行降级

当 subagent 不可用时，自动降级为主 Agent 串行：
- **触发条件**：subagent 启动失败，或输出质量不达标
- **降级后** `mode` 记录为 `"serial"`，无需用户干预

## Subagent 上下文精简

主 Agent 在派遣 subagent 前**必须精简上下文**，避免将全量缓存文件送入 subagent prompt：

| 阶段 | 精简方式 |
|------|---------|
| `extract-docs` | `build_prompt.py extract-docs --cache` 将 `cache/modules/<slug>/context.json` 路径注入 prompt 文件 |
| `generate-module-docs` | `build_prompt.py generate-module-docs --cache` 将单页 `source_files`、输出路径和模块分析注入 prompt 文件 |
| `quality-fix` | `build_prompt.py quality-fix --cache` 将目标页和 `page-context` 命令注入 prompt 文件 |

## Subagent Prompt 文件锁

所有 subagent 阶段（`extract-docs`、`generate-module-docs`、`quality-fix`）都必须走 prompt 文件调度：

1. 主 Agent 先执行对应的 `scripts/subagent/build_prompt.py ... --cache`
2. 确认 `.deepwiki/cache/prompts/manifest.json` 记录了对应 prompt
3. 读取 `.deepwiki/cache/prompts/<type>_<safe_id>.md` 的 FULL content
4. spawn subagent 时只传入该 FULL content，不追加额外解释

DO NOT rewrite、summarize、merge、reinterpret 或 regenerate subagent prompt。若 prompt 文件不存在、manifest 缺失对应项，或主 Agent 跳过读文件步骤，本阶段视为失败，必须先重新生成 prompt 文件。

`extract-docs` 的 subagent prompt 必须由 `scripts/subagent/build_prompt.py extract-docs --module <模块路径> --cache` 生成；禁止主 Agent 人工拼接“读取这些源码文件并分析多个模块”的提示词。一个 extract-docs subagent 只负责一个模块，只写一个 `cache/module-analysis.<slug>.json`。

**禁止将以下文件原样送入 subagent prompt**：
- `cache/module-analysis.json`（全量）— 用 `page-context` 脚本提取单模块条目
- `cache/evidence-index.json`（全量）— 用 `page-context` 脚本提取相关证据
- `cache/generation-plan.json`（全量）— 仅传入对应页面的 `source_files` 和 `ranges`

## 写入安全（并发保障）

**默认策略：中间文件合并**

1. 每个 subagent 写入独立临时文件 `cache/module-analysis.<module_slug>.json`
2. 所有批次完成后，主 Agent 调用 `merge_module_analysis_parts()` 合并为 `module-analysis.json`
3. 合并完成后删除临时文件

若确需每批结束后提前合并，必须使用会读取已有 `module-analysis.json` 作为 base 的合并函数，避免后一批覆盖前一批结果。

优势：无竞态风险，无需文件锁，跨平台兼容。

串行模式（单 Agent）下直接写入 `cache/module-analysis.json`，使用增量追加模式。
