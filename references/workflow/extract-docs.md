# extract-docs

前置：`prepare_module_context`（必须）、`generate-skeleton`（可选）| 后置：`validate-analysis`

## 生成 subagent 提示词

```bash
python scripts/subagent/build_prompt.py extract-docs --project <项目路径> --module <模块路径> --cache
```

模板文件：[`../subagents/extract-docs.md`](../subagents/extract-docs.md)。
输出位置：`.deepwiki/cache/prompts/extract-docs_<module_slug>.md`。

## 并发调用 subagent 规则

共享调度框架：[`../rules/batch-scheduling.md`](../rules/batch-scheduling.md)。

## 合并 module-analysis.json

所有 subagent 批次完成后，合并临时文件：

```python
from scripts.core.common import merge_module_analysis_parts
from scripts.core.common import CACHE_SCHEMA_VERSION
cache = Path("<项目路径>") / ".deepwiki" / "cache"
parts = sorted(cache.glob("module-analysis.*.json"))
if parts:
    merged = merge_module_analysis_parts(cache, parts)
    merged["cache_schema_version"] = CACHE_SCHEMA_VERSION
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
