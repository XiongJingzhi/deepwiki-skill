---
name: deepwiki
description: 通过 Agent 自主探索源码，生成结构化项目 Wiki。Use when user requests "生成 wiki"、"创建项目源码文档"、"创建项目文档"、"更新 wiki"、"预览项目 wiki"、"启动文档服务".
---

# DeepWiki

Generate project documentation into `.deepwiki/` with a lightweight, agentic workflow.

## Main Path

```text
init-wiki → prepare-inventory → agentic-analysis → plan-pages
→ generate-menu → generate-pages → finalize-wiki
```

Scripts collect lightweight facts and verify final output. The Agent explores, understands, plans, and writes.

## Commands

Run from this skill directory. If installed, `deepwiki <command>` is equivalent to `python -m scripts.cli <command>`.

| Stage | Command or action |
| --- | --- |
| `init-wiki` | `deepwiki init <project_path>` |
| `prepare-inventory` | `deepwiki prepare-inventory <project_path>` |
| `agentic-analysis` | Agent writes `.deepwiki/cache/semantic-analysis.json` |
| `plan-pages` | Agent writes `.deepwiki/cache/page-plan.json`, then run `deepwiki validate-page-plan <project_path>` |
| `generate-menu` | `deepwiki generate-menu <project_path>` |
| `generate-pages` | For each planned page, run `deepwiki page-context <project_path> <page_id>`, then write the Markdown page |
| `finalize-wiki` | `deepwiki finalize <project_path>` |
| Preview | `deepwiki serve <project_path>` |

## Rules

- Use `.deepwiki/cache/project-inventory.json` as the only mandatory preparation artifact.
- Let the Agent inspect source files directly during `agentic-analysis`, `plan-pages`, and `generate-pages`.
- Split generation by page from `.deepwiki/cache/page-plan.json`.
- Do not depend on old cache files such as `structure.json`, `module-analysis.json`, or `generation-plan.json`.
- Stop on `finalize-wiki` failure and report the failed check.

## References

- Workflow details: `references/workflow/*.md`
- Cache contract: `references/system-reference.md`
