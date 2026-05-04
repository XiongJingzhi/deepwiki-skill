# parallel-analysis：并行批次调度策略

> 本文档补充 `extract-docs.md`，定义模块分析阶段的并行执行规则。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | 无（调度策略文档，由 AI 执行） |
| **输入** | `cache/structure.json`（模块列表+重要性评分）、`cache/modules/<slug>/context.json` |
| **输出** | `cache/module-analysis.<slug>.json`（subagent 临时文件），主 Agent 合并为 `cache/module-analysis.json` |
| **前置** | `prepare_module_context`、`detect-changes`（增量时） |
| **后置** | `validate-analysis` |

## 批次调度

> 统一的批次调度规则（并行/串行策略、进度追踪、串行降级、写入安全）见 [`../rules/batch-scheduling.md`](../rules/batch-scheduling.md)。
>
> extract-docs 阶段适用以下特定规则：
> - **排序依据**：`structure.json` 中模块 `importance_score` 降序
> - **progress.json 字段**：`phases.analysis`

## 模块独立性说明

extract-docs 语义分析每个模块**天然独立**——分析模块 A 不需要模块 B 已完成分析。
（注：`validate-analysis` 和依赖综合规则才需要等 `extract-docs` 全部完成）

## subagent 任务模板

```
任务：分析模块 {module_name}（路径：{module_path}）
上下文文件：
  - cache/modules/{module_slug}/context.json
提示词：
  - 先运行 python scripts/subagent/build_prompt.py extract-docs --project <项目路径> --module {module_path} --cache
  - 再读取 .deepwiki/cache/prompts/extract-docs_{module_slug}.md 的完整内容作为 subagent prompt
输出要求：遵循 workflow/extract-docs.md
  - 完成后写入 cache/module-analysis.{module_slug}.json
  - 禁止直接写入 cache/module-analysis.json
  - 每个模块必须写入字段见 extract-docs.md 表格
```

## 进度追踪

extract-docs 阶段使用 `state/progress.json` 的 `phases.analysis` 字段，状态格式和转换规则见 [`../rules/batch-scheduling.md`](../rules/batch-scheduling.md#进度追踪)。
