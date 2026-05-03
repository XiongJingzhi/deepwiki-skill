# plan-doc-topology

`python scripts/pipeline/plan_doc_topology.py <项目路径>`

前置：`validate-analysis` | 后置：`generate-overview`、`generate-menu`（初始）、`generate-module-docs`

输入：`cache/structure.json`、`cache/module-analysis.json`（+ `code-structure.json`、`evidence-index.json` 可选增强）
输出：`cache/doc-topology.json`、`cache/generation-plan.json`

脚本自动生成确定性计划；仅在复杂 Monorepo 需要定制页面分组时 AI 介入调整 `doc-topology.json`。

## 最小页面集合

默认包含：
- `overview`、`getting-started`、`doc-map`
- `concepts/architecture.md`、`concepts/development-guide.md`
- `deep-dive/<topic>.md`（模块少时平铺）或 `deep-dive/<子目录>/<topic>.md`（模块多时分组，最多 2 级）
- `reference/api-surface.md`

规则：一个菜单项对应一个 Markdown 文件；同一模块的核心逻辑、接口、流程、风险和扩展点合并到同一页；`wiki/` 下最多 2 层子目录。

## 降级

- `code-structure.json` 缺失：仅基于 `structure.json` 生成基础拓扑
- 模块分析不完整：先回到 `validate-analysis` 补齐质量门控

