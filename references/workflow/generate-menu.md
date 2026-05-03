# generate-menu

`python scripts/wiki/generate_menu.py <wiki目录> [项目名] [--reconcile]`

前置：`generate-overview` | 后置：`generate-module-docs`

输入：`cache/doc-topology.json`、`cache/generation-plan.json`、`cache/structure.json`、`cache/module-analysis.json`、`cache/architecture-skeleton.json`（可选）
输出：`wiki/menu.json`、`wiki/doc-map.md`
生成规则：见 `../generation/docmap-page.md`、`../rules/menu-archetypes.md`

## 输入数据优先级

| 数据源 | 优先级 |
|--------|--------|
| `cache/relationship-summary.json` | 最高 |
| `cache/doc-topology.json`、`cache/generation-plan.json` | 高 |
| `cache/code-structure.json` → `import_relations` | 高 |
| `cache/module-analysis.json` → `dependency_hints` | 高 |
| `cache/module-analysis.json` → `semantic_group` | 中 |
| `cache/code-structure.json` → `patterns` | 中 |
| `cache/structure.json` → 目录聚集度 | 低 |
| `../rules/menu-archetypes.md` | 兜底 |

降级：若 `module-analysis.json` 不存在，直接使用 `import_relations` + `structure.json`。

## 菜单质量检查（仅在发现明显结构问题时做最小修正）

1. 分区命名面向读者（非技术术语）
2. 分区粒度：3-8 个顶层，每组 2-6 模块
3. 读者旅程顺序自然
4. 最多 3 层嵌套（`menu[]` → `items[]` → `items[]`），超过 3 层必须合并

| 情况 | 处理 |
|------|------|
| 某组模块数 < 2 | 并入最相邻主题（除非是项目核心） |
| 某组模块数 > 6 | 拆出子分区 |
| 顶层分区总数 > 8 | 合并语义相近分区 |
| 顶层分区总数 < 3 | 检查是否过度合并 |

## 固定首尾区块

- **首区块**：概览，指向 `overview.md`、`getting-started.md`、`doc-map.md`
- **核心区块**：深入理解，承载 `deep-dive/*.md`；模块多时支持子分组（3 级菜单），第 3 层 `items` 不得再嵌套
- **尾区块**：贡献与扩展（Contributing）

完整 menu.json 结构模板和 5 条格式规则见 [`../generation/docmap-page.md`](../generation/docmap-page.md) → **menu.json 模板** 章节。

## 初始生成：doc-map.md

基于 `menu.json` + `overview.md` 架构信息生成 `wiki/doc-map.md`：文档关系图（Mermaid flowchart）+ 按读者角色推荐阅读路径 + 完整文档索引 + 模块间依赖矩阵。

所有条目必须是可跳转链接 `[文档标题](相对路径.md)`。

完成后更新 `state/progress.json` 的 `phases.menu.status` 为 `completed`。

## 收尾校验：--reconcile

```bash
python scripts/wiki/generate_menu.py <项目目录>/.deepwiki/wiki [项目名称] --reconcile --verbose
```
