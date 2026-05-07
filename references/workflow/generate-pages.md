# generate-pages

For each page in `page-plan.json`:

```bash
deepwiki page-context <project_path> <page_id>
```

Read the generated page context, inspect additional source if needed, then write the Markdown page to `wiki/<output_path>`.

If evidence is insufficient, write a narrower page and state the limitation.

Follow `references/rules/quality-standards.md` for page shape, source tracing, Mermaid, and cross-link rules.
