# plan-pages

Agent 动作：写入 `.deepwiki/cache/page-plan.json`。

随后校验：

```bash
deepwiki validate-page-plan <project_path>
```

每个页面必须包含 `page_id`、`title`、`output_path`、`page_type`、`purpose`、`source_targets`、`depends_on` 和 `status`。

只使用安全的相对 Markdown 路径，不使用绝对路径或 `..`。
