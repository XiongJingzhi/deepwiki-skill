# generate-module-docs

前置：`generate-overview`、初始 `generate-menu`、`extract_source_snippets` | 后置：`finalize-wiki`

## 串行模式

当用户输入“串行生成文档”、明确说“不派遣 subagent”或同义表达时，本阶段禁止生成 subagent prompt、禁止调用 `spawn_agent`。主 Agent 必须按 `generation-plan.json.pages[]` 顺序逐页生成模块文档，直接写入每个页面的 `output_path`，并将进度记录为 `mode: "serial"`。

## 生成 subagent 提示词

```bash
python scripts/subagent/build_prompt.py generate-module-docs --project <项目路径> --page <page_id> --cache
```

模板文件：[`../subagents/generate-module-docs.md`](../subagents/generate-module-docs.md)。
输出位置：`.deepwiki/cache/prompts/generate-module-docs_<safe_page_id>.md`。

## Prompt 文件即唯一输入

派遣每个 subagent 前，主 Agent 必须：

1. 执行上方 `build_prompt.py generate-module-docs ... --cache`
2. 确认 `.deepwiki/cache/prompts/manifest.json` 中存在该页面的 `generate-module-docs` 记录
3. 必须读取生成的 prompt 文件完整内容：`.deepwiki/cache/prompts/generate-module-docs_<safe_page_id>.md`
4. 使用该完整内容作为 subagent prompt，不添加额外说明

禁止手写、摘要、改写或重新解释 subagent prompt。不要用 `generation-plan.json`、`page-context` 输出或本 workflow 文档自行拼接提示词。跳过此步骤视为本阶段失败。

## 并发调用 subagent 规则

[`../rules/batch-scheduling.md`](../rules/batch-scheduling.md)。

本阶段只处理 `generation-plan.json.pages[]` 中有 `affected_modules` / `source_modules` 的模块页面。`overview`、`getting-started`、`doc-map`、`concept:*`、`reference:*` 页面应按各自工作流生成，不进入 `generate-module-docs` subagent。

每个页面任务在派遣前必须先确认 `generation-plan.json.pages[]` 中存在：
- `page_id`
- `output_path`
- `affected_modules` 或 `source_modules`（非空）
- `source_files`

生成提示词时使用：

```bash
python scripts/subagent/build_prompt.py generate-module-docs --project <项目路径> --page <page_id> --cache
```

生成的 prompt 会注入目标 `output_path` 和绝对写入路径。不要把完整 `generation-plan.json` 原样塞给 subagent。

## 失败重试

1. 失败模块标记为 `failed`，继续处理下一个
2. 全部完成后对 `failed` 模块重试一次
3. 重试时降低读取深度一档，生成简版文档
4. 重试仍失败 → 记录到 `state/progress.json` 对应模块状态为 `failed`

## 内容降级

| 情况 | 降级行为 |
|------|---------|
| 文件超过 `max_file_size` | 生成"概述 + 入口点清单"占位文档 |
| 接口信息不足 | 生成"概述 + 文件结构"简版文档 |
| Mermaid 语法复杂 | 退化为表格形式 |
| 行号无法确定 | 先从 `public_interfaces.line/end_line`、`core_source_ranges` 推导；仍无法确定则退化为文件级链接 |
| 依赖关系无法推断 | 仅记录静态 import |
| 中途中断 | 保存已完成部分，写入 progress.json |
| subagent 失败 | 降级为主 agent 串行处理 |
