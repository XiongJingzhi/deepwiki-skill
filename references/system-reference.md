# DeepWiki 系统参考

## 输出结构

`.deepwiki/` 包含：

- `config.yaml`：生成设置。
- `cache/project-inventory.json`：`prepare-inventory` 生成的目录级项目事实。
- `cache/semantic-analysis.json`：Agent 编写的项目语义分析。
- `cache/page-plan.json`：Agent 编写的页面清单、菜单种子和生成顺序。
- `cache/page-context/<page_id>.json`：逐页生成前准备的源码片段和写作约束。
- `state/progress.json`：可选的生成进度。
- `state/mermaid-errors.json`：可选的 Mermaid 校验失败报告。
- `wiki/`：生成的 Markdown、`menu.json` 和 `doc-map.md`。

## 缓存契约

`project-inventory.json` 是唯一强制准备产物。它只保存低解释度事实，不包含 AST、调用图、函数签名或模块深度分析。

`semantic-analysis.json` 保存 Agent 对项目的理解：项目目的、架构模型、运行流程、核心概念、语义模块、风险、扩展点、源码证据、置信度和未决问题。

`page-plan.json` 是页面生成的事实来源。每个非 skipped 页面都需要唯一 `page_id`、安全的 Markdown `output_path`、非空 `source_targets`，并出现在 `generation_order` 中。

`page-context/<page_id>.json` 在写每个页面前生成，包含源码文件、源码摘录、相关页面、待覆盖结论、必须链接的符号和约束。

## 遗留策略

主流程不使用旧 pipeline 缓存文件。如确需旧行为，重新实现最小干净工具，不从遗留代码中 import。

## 输出规则

见 `references/rules/quality-standards.md`。

页面组件注册表见 `references/rules/components-registry.yaml`。
