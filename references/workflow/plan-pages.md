# plan-pages

Agent action: write `.deepwiki/cache/page-plan.json`.

Then validate:

```bash
deepwiki validate-page-plan <project_path>
```

Each page needs `page_id`, `title`, `output_path`, `page_type`, `purpose`, `source_targets`, `depends_on`, and `status`.

Use safe relative Markdown paths only.
