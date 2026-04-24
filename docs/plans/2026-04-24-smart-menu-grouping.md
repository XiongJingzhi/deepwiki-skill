# Smart Menu Grouping 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现数据驱动的菜单分组：步骤4标注语义主题，步骤7用三层算法（依赖数据→语义标注→原型思路）生成高质量 menu.json。

**Architecture:** 在 module-analysis.json 写入 semantic_group；步骤7读取 import-relations + module-analysis + code-structure 三个数据源，AI 自主分组而非填槽位；menu-archetypes.md 提供各原型的分组经验作为兜底。

**Tech Stack:** JSON Schema, Markdown references 文档

---

### Task 1: schema 新增 semantic_group 字段
**Files:** Modify `schemas/module-analysis-schema.json`（在 ModuleAnalysis 的 required 和 properties 中插入新字段）

在 `"dependency_hints"` 属性之后插入 `semantic_group` 和 `semantic_group_confidence` 两个字段，并在 `required` 数组末尾追加 `"semantic_group"`。

```bash
git add schemas/module-analysis-schema.json
git commit -m "feat: add semantic_group to module-analysis schema"
```

---

### Task 2: step4 持久化章节新增 semantic_group 写入要求
**Files:** Modify `references/step4-source-analysis.md`（在"每个模块必须写入的字段"表格末尾添加两行）

在字段表格末尾追加：
```
| `semantic_group` | AI 对该模块的语义主题标注（自由文字，如"认证与鉴权"、"消息路由"）——依据代码实际内容命名，不受 CodePurpose 枚举约束 |
| `semantic_group_confidence` | 语义分组置信度（`high`=有明显语义边界 / `low`=AI 不确定，步骤 7 分组时降低权重） |
```

```bash
git add references/step4-source-analysis.md
git commit -m "feat: step4 now writes semantic_group to module-analysis"
```

---

### Task 3: 新建 references/menu-archetypes.md
**Files:** Create `references/menu-archetypes.md`

为每种 archetype 提供分组思路（不是固定模板，是经验参考）。格式：
- 分组思路：这类项目常见的语义主题有哪些
- 粒度建议：顶层分区数、每组子项数
- 反模式警告：容易犯的错误分组方式

覆盖 7 种 archetype：`web-service`、`sdk-library`、`spa-frontend`、`cli-tool`、`ml-project`、`fullstack-framework`、`generic`。

```bash
git add references/menu-archetypes.md
git commit -m "feat: add menu-archetypes.md with grouping heuristics per archetype"
```

---

### Task 4: 重写 step7-menu-and-docmap.md（三层分组算法）
**Files:** Modify `references/step7-menu-and-docmap.md`（全文重写 7.1 章节）

将现有的单句"读取 modules 字段生成菜单"替换为完整的三层分组算法指引：
1. **层1（数据聚类）**：读 import-relations.json + module-analysis 的 dependency_hints，构建依赖强度，互相高度依赖的模块为候选聚合组
2. **层2（语义验证）**：用 semantic_group 验证/命名候选组；不同 semantic_group 但强依赖的以依赖数据为准；相同 semantic_group 但无依赖关系的平行列出
3. **层3（兜底）**：无强依赖的孤岛模块，读取 menu-archetypes.md 中对应 archetype 的分组思路，决定归属
4. **粒度收敛规则**：<2 个模块的组考虑合并；>6 个模块的组考虑拆子分区

同时引用 `references/menu-archetypes.md` 和 `references/templates.md` → menu.json 模板。

```bash
git add references/step7-menu-and-docmap.md
git commit -m "feat: step7 uses 3-layer data-driven grouping algorithm"
```

---

### Task 5: templates.md 补全 menu.json 模板章节
**Files:** Modify `references/templates.md`（在文末"Mermaid 规范"章节之前插入新章节）

补全当前被 step7 引用但实际不存在的 `menu.json 模板` 章节，包含：
- `menu.json` 完整 JSON 结构示例（含 sections/groups/items 三层结构）
- AI 生成菜单的 5 条规则（按读者旅程排序、语义命名、避免路径命名、层级不超过3级、固定首尾区块）
- 增量更新时的 `"planned": true` 标记规范

```bash
git add references/templates.md
git commit -m "feat: add missing menu.json template section to templates.md"
```
