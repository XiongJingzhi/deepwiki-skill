# generate-menu：生成导航菜单与文档地图

> generate-menu 有两个调用点：模块文档生成前创建初始 `menu.json` / `doc-map.md`，模块文档生成后用 `--reconcile` 校验并修正菜单。外部 9 步流程中，初始菜单是 `generate-overview` 与 `generate-module-docs` 之间的内部子步骤，reconcile 是 `generate-module-docs` 的收尾子步骤。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/generate_menu.py <wiki目录> [项目名] [--reconcile]` |
| **输入** | `cache/doc-topology.json`、`cache/generation-plan.json`、`cache/structure.json`、`cache/module-analysis.json`、`cache/architecture-skeleton.json`（可选） |
| **输出** | `wiki/menu.json`、`wiki/doc-map.md` |
| **前置** | `generate-overview` |
| **后置** | `generate-module-docs` |
| **生成规则** | 见 `../generation/docmap-page.md`、`../rules/menu-archetypes.md` |

## 初始生成：menu.json

> `build_menu()` 支持 `cache_dir` 参数，并优先读取 `doc-topology.json` / `generation-plan.json`。缺少文档拓扑时，自动读取 `module-analysis.json` 的 `semantic_group` 和 `architecture-skeleton.json` 的 `module_groups` 进行数据驱动分组。当分析数据存在时，分区名来自项目理解，而非固定模板。

### 输入数据（按优先级顺序读取）

| 数据源 | 作用 | 优先级 |
|--------|------|--------|
| `cache/doc-topology.json`、`cache/generation-plan.json` | 文档页面拓扑和本轮编译计划 | **最高** |
| `cache/code-structure.json` → `import_relations` | 模块间依赖强度，最客观的聚合信号 | **高** |
| `cache/module-analysis.json` → `dependency_hints` | 步骤 5 已提炼的依赖摘要（若 import-relations 缺失时替代） | 高 |
| `cache/module-analysis.json` → `semantic_group` | AI 的语义主题标注，验证并命名分组 | 中 |
| `cache/code-structure.json` → `patterns` | 同类 pattern 的模块有结构亲缘，可辅助归组 | 中 |
| `cache/structure.json` → 目录聚集度 | 同父目录的模块有弱亲缘关系，作为辅助信号 | 低 |
| `../rules/menu-archetypes.md` | 当前 archetype 的分组思路（孤岛模块兜底） | 兜底 |

> **降级**：若 `module-analysis.json` 不存在，直接使用 `code-structure.json` 的 `import_relations` + `structure.json`，跳过语义分组层。

---

### 三层分组算法（Python 脚本自动执行）

> 以下三层算法已内置于 `generate_menu.py`，由 Python 脚本自动执行，无需 AI 手动计算。

**层1：依赖数据聚类 — `_cluster_by_import_relations()`**

已在 Python 脚本中使用 Union-Find 算法实现，从 `code-structure.json` 的 `import_relations` 构建模块依赖图并自动聚类：
1. 互相存在双向引用、或共同被第三个模块大量引用的模块 → 候选聚合组
2. 同父目录且有共同依赖的模块 → 加强候选信号
3. 按依赖强度从高到低排列候选组

核心逻辑（脚本自动完成）：
- 将文件级 import 归并为模块级依赖，计算 `dep_weight(A, B)`
- 强依赖对（`dep_weight(A, B) >= 2` 或双向 `>= 3`）通过 Union-Find 合并为候选组
- 候选组 > 6 模块时按 `dep_weight` 拆分；组内仅 1 模块时标记为"孤岛"

**层2：语义标注验证 — `_cluster_by_semantic_group()`**

已在 Python 脚本中实现，自动读取 `module-analysis.json` 的 `semantic_group` 字段验证和命名候选组：
- `semantic_group` **相同** 且有依赖关系 → 确认聚合，使用 `semantic_group` 值作为分区名
- `semantic_group` **不同** 但依赖强度高 → 以依赖数据为准；取两者语义的公共上位词命名
- `semantic_group` **相同** 但无依赖关系 → 平行列出（同主题但独立模块）
- `semantic_group_confidence` 为 `low` → 降低该标注权重，更多依赖层1数据决策

`semantic_group_override: true` 的条目自动获得 `high` 置信度，其分组命名直接作为依据。菜单生成后，脚本自动将 override 修正结果回写到 `cache/architecture-skeleton.json`。

#### 层2 决策矩阵（脚本内部逻辑参考）

| 依赖强度 | semantic_group 相同？ | confidence | 操作 |
|---------|---------------------|-----------|------|
| 强（weight ≥ 2） | 是 | high | 确认聚合，用 semantic_group 值命名分组 |
| 强（weight ≥ 2） | 否 | 任意 | 以依赖数据为准合并，取两者语义的公共上位词重命名 |
| 弱（weight = 1） | 是 | high | 平行列出，不强行合并 |
| 弱（weight = 1） | 是 | low | 孤岛，层3兜底 |
| 无依赖 | 是 | high | 平行列出 |
| 无依赖 | 否/low | 任意 | 孤岛，层3兜底 |

**层3：孤岛兜底（规则参考）**

`../rules/menu-archetypes.md` 保留为孤岛模块的兜底参考。当 Python 脚本生成的分组中出现孤岛模块时，优先按当前 `archetype` 的常见语义主题、模块的 `code_purpose` 和 `module_summary` 选择最接近的主题。

---

## 菜单质量检查

Python 脚本已自动按 `doc-topology.json`、依赖聚类和 `semantic_group` 生成 `menu.json`。默认不再进行 AI 微调；只在发现明显结构问题时，才按以下标准做最小修正：
1. 检查分区命名是否面向读者（非技术术语）
2. 检查分区粒度（3-8 个顶层，每组 2-6 模块）
3. 检查读者旅程顺序是否自然
4. 仅修正明显错误，不重新设计文档拓扑

### 粒度收敛规则

完成分组后做如下检查：

| 情况 | 处理 |
|------|------|
| 某组模块数 < 2 | 考虑并入最相邻主题（除非该模块是项目核心且独立性高） |
| 某组模块数 > 6 | 考虑拆出子分区（如"核心业务"拆为"订单流程"/"支付流程"） |
| 顶层分区总数 > 8 | 合并语义相近的分区 |
| 顶层分区总数 < 3 | 检查是否过度合并，考虑拆分大组 |

---

### 固定首尾区块

所有菜单必须包含：
- **首区块**：概览，指向 `overview.md`、`getting-started.md`、`doc-map.md`
- **核心区块**：能力导览与内部实现，承载 `capabilities/*.md` 与 `internals/*.md`。每个菜单项默认对应一个 Markdown 文件，页面内整合核心逻辑、接口、流程、风险和扩展点
- **尾区块**：贡献与扩展（Contributing），指向贡献指南或扩展接口文档

---

> `menu.json` 完整结构模板和 AI 生成菜单的 5 条格式规则见 [`../generation/docmap-page.md`](../generation/docmap-page.md) → **menu.json 模板** 章节。

**为什么要先于详细文档生成菜单**：菜单定义了每个模块文档在导航层级中的位置（所属分组、前后顺序）。详细文档生成时可以引用自身在菜单中的位置来生成精确的面包屑导航和前后文档链接，使文档网络更加连贯。

---

## 初始生成：doc-map.md

基于 `menu.json` 的导航结构和 `overview.md` 的架构信息，生成 `wiki/doc-map.md`：

| 内容 | 数据来源 |
|------|---------|
| 文档关系图（Mermaid flowchart） | `menu.json` 层级结构 |
| 推荐阅读路径 | 按读者角色（新手/架构师/API 使用者） |
| 完整文档索引 | `structure.json` 模块列表 + `menu.json` |
| 模块间依赖矩阵 | `cache/code-structure.json`、`cache/module-analysis.json.dependency_hints` 或依赖综合摘要 |

模板参考：`../generation/docmap-page.md` → 文档地图。

完成后更新 `cache/progress.json` 的 `phases.menu.status` 为 `completed`。

## 收尾校验：--reconcile

`generate-module-docs` 全部完成后，必须再次运行：

```bash
python scripts/generate_menu.py <项目目录>/.deepwiki/wiki [项目名称] --reconcile --verbose
```

该模式只校验和修正已有 `menu.json`，确保菜单包含实际生成的模块/API 页面，不负责重新设计文档拓扑。

