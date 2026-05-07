# DeepWiki System Reference

## Output Layout

`.deepwiki/` contains:

- `config.yaml`: generation settings.
- `cache/project-inventory.json`: directory-level project facts from `prepare-inventory`.
- `cache/semantic-analysis.json`: Agent-authored project understanding.
- `cache/page-plan.json`: Agent-authored page list, menu seed, and generation order.
- `cache/page-context/<page_id>.json`: per-page source excerpts and writing constraints.
- `state/progress.json`: optional generation progress.
- `wiki/`: generated Markdown, `menu.json`, and `doc-map.md`.
- `state/mermaid-errors.json`: optional mmdc validation failure report.

## Cache Contract

`project-inventory.json` is the only mandatory preparation artifact. It must not contain ASTs, call graphs, function signatures, or module analysis.

`semantic-analysis.json` stores the Agent's mental model: purpose, architecture, flows, concepts, semantic modules, risks, extension points, evidence, confidence, and open questions.

`page-plan.json` is the source of truth for pages. Every non-skipped page needs a unique `page_id`, safe Markdown `output_path`, non-empty `source_targets`, and an entry in `generation_order`.

`page-context/<page_id>.json` is regenerated per page before writing. It contains source files, excerpts, related pages, claims to cover, required symbols, and constraints.

## Legacy Policy

Do not use old pipeline cache files in the main path. If old behavior is needed, reimplement the minimal clean helper instead of importing legacy code.

## Output Rules

See `references/rules/quality-standards.md`.
