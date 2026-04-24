# plan-doc-topology：规划文档拓扑

> `plan-doc-topology` 从确定性缓存中生成文档知识树和本轮编译计划，输出 `cache/doc-topology.json` 与 `cache/generation-plan.json`。

## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/plan_doc_topology.py <项目路径>` |
| **输入** | `cache/structure.json`、`cache/code-structure.json`（可选增强） |
| **输出** | `cache/doc-topology.json`、`cache/generation-plan.json` |
| **前置** | `extract-docs` |
| **后置** | `check-analysis-quality`、`generate-overview`、`generate-menu`、`generate-module-docs` |

## 目标

这个阶段不直接写 Markdown，而是先回答两个问题：

1. 文档树应该怎么组织
2. 本轮哪些页面需要编译

## 最小页面集合

默认至少生成以下页面计划：

- `overview`
- `getting-started`
- `doc-map`
- `modules/<module>.md`
- `api/<module>.md`

## 降级

- 若 `code-structure.json` 缺失，可仅基于 `structure.json` 生成基础拓扑
- 若模块分析尚不完整，也应先生成最小页面集合，后续页面内容阶段再补充深度
