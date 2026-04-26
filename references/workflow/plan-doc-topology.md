# plan-doc-topology：规划文档拓扑

> `plan-doc-topology` 从确定性缓存中生成文档知识树和本轮编译计划，输出 `cache/doc-topology.json` 与 `cache/generation-plan.json`。

## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/plan_doc_topology.py <项目路径>` |
| **输入** | `cache/structure.json`、`cache/code-structure.json`（可选增强）、`cache/module-analysis.json`、`cache/evidence-index.json`（可选增强） |
| **输出** | `cache/doc-topology.json`、`cache/generation-plan.json` |
| **前置** | `validate-analysis` |
| **后置** | `generate-overview`、初始 `generate-menu`、`generate-module-docs` |

## 目标

这个阶段不直接写 Markdown，而是先回答两个问题：

1. 文档树应该怎么组织
2. 本轮哪些页面需要编译

## 最小页面集合

默认至少生成以下页面计划：

- `overview`
- `getting-started`
- `doc-map`
- `concepts/architecture.md`
- `concepts/development-guide.md`
- `deep-dive/<topic>.md`
- `reference/api-surface.md`

原则：

- 一个菜单项默认只对应一个 Markdown 文件。
- 同一源码模块的核心逻辑、公开接口、流程、风险和扩展点合并到同一页，不再默认拆成 `module` 与 `api` 两页。
- 目录只表达读者视角：自上而下理解项目、深入理解源码主路径与内部机制、最后查阅参考资料。

## 降级

- 若 `code-structure.json` 缺失，可仅基于 `structure.json` 生成基础拓扑
- 若模块分析尚不完整，应先回到 `validate-analysis` 补齐质量门控；只有在调试或灾备场景下才生成最小页面集合
