# generate-pages

对 `page-plan.json` 中的每个页面运行：

```bash
deepwiki page-context <project_path> <page_id>
```

读取生成的页面上下文，必要时继续检查源码，然后把 Markdown 写入 `wiki/<output_path>`。

如果源码证据不足，生成范围更窄的页面，并明确说明限制。页面格式、源码追溯、Mermaid 和交叉链接规则见 `references/rules/quality-standards.md`。
