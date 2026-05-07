# analyze-project

`python -m scripts.analysis.analyze_project <项目路径>`

前置：`init-wiki` | 后置：`extract-structure`

## 输出

**`cache/structure.json`**

```jsonc
{
  "project_name": "string",
  "project_type": ["string"],
  "languages": ["string"],
  "archetype": "string",
  "entry_points": ["string"],
  "modules": [{ "name", "path", "files", "type", "importance_score", "core_files", "core_files_count" }],
  "core_files": [{ "path", "importance_score", "complexity_score", "important_lines_count" }],
  "high_priority_files": [{ /* 同 core_files */ }],
  "docs_found": ["string"],
  "stats": { "total_files", "code_files", "core_files_count", "high_priority_files_count", "total_modules" },
  "context_budget": {},
  "analyzed_at": "ISO8601"
}
```
