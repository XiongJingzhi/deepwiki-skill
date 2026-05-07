# extract-docs

前置：`prepare_module_context`（必须）、`generate-skeleton`（可选）| 后置：`validate-analysis`

## 串行模式

当用户输入“串行生成文档”、明确说“不派遣 subagent”或同义表达时，本阶段禁止生成 subagent prompt、禁止调用 `spawn_agent`。主 Agent 必须按模块列表顺序读取各模块 `cache/modules/<slug>/context.json`，逐项补充 `cache/module-analysis.json`，并将进度记录为 `mode: "serial"`。

## 生成 subagent 提示词

```bash
python scripts/subagent/build_prompt.py extract-docs --project <项目路径> --module <模块路径> --cache
```

模板文件：[`../subagents/extract-docs.md`](../subagents/extract-docs.md)。
输出位置：`.deepwiki/cache/prompts/extract-docs_<module_slug>.md`。

⛔ **禁止手写 extract-docs subagent 提示词**。必须使用上面的 `build_prompt.py` 为每个模块生成 prompt。不得把多个模块合并到一个 extract-docs subagent，也不得在 prompt 中要求 subagent 读取源码文件。

## Prompt 文件即唯一输入

派遣每个 subagent 前，主 Agent 必须：

1. 执行上方 `build_prompt.py extract-docs ... --cache`
2. 确认 `.deepwiki/cache/prompts/manifest.json` 中存在该模块的 `extract-docs` 记录
3. 必须读取生成的 prompt 文件完整内容：`.deepwiki/cache/prompts/extract-docs_<module_slug>.md`
4. 使用该完整内容作为 subagent prompt，不添加额外说明

禁止手写、摘要、改写或重新解释 subagent prompt。跳过此步骤视为本阶段失败。

## 并发调用 subagent 规则

共享调度框架：[`../rules/batch-scheduling.md`](../rules/batch-scheduling.md)。

## 合并 module-analysis.json

所有 subagent 批次完成后，合并临时文件：

```python
from scripts.core.common import merge_module_analysis_parts
from datetime import datetime, timezone
import json
from pathlib import Path

cache = Path("<项目路径>") / ".deepwiki" / "cache"
parts = sorted(cache.glob("module-analysis.*.json"))
if parts:
    merged = merge_module_analysis_parts(cache, parts)
    merged["generated_at"] = datetime.now(timezone.utc).isoformat()
    (cache / "module-analysis.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for p in parts:
        p.unlink()
```

串行模式（单 Agent）下直接写入 `cache/module-analysis.json`，无需合并。

## 降级（context.json 不存在）

⛔ 停止执行，输出：`⛔ [extract-docs] context.json 缺失，请先运行 prepare_module_context.py <项目路径>`

如果自动分析管线未能正确识别模块结构，主 Agent 应先修正 `cache/structure.json` 或重新运行 `prepare_module_context.py`，再重新生成每个模块的 extract-docs prompt。不要通过“让 subagent 直接读源码”绕过 `context.json`，这会破坏并发写入安全和分析质量门控。
