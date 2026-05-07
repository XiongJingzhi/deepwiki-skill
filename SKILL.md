---
name: deepwiki
description: 通过 Agent 自主探索源码，生成结构化项目 Wiki。Use when user requests "生成 wiki"、"创建项目源码文档"、"创建项目文档"、"更新 wiki"、"预览项目 wiki"、"启动文档服务".
---

# DeepWiki

DeepWiki generates project documentation in `.deepwiki/` with an agentic workflow.

## Workflow

```text
init-wiki → prepare-inventory → agentic-analysis → plan-pages
→ generate-menu → generate-pages → finalize-wiki
```

Scripts collect lightweight facts and verify final output. The Agent explores, understands, plans, and writes.

The previous script-heavy pipeline is archived in `legacy/old-pipeline/` for reference only.
