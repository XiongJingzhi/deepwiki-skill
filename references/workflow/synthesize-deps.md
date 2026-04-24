# 依赖关系综合

> 本文件描述工作流synthesize-deps的完整规则：从源码分析结果中综合提取模块依赖图。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | 无（AI 执行） |
| **输入** | `cache/module-analysis.json`、`cache/code-structure.json`（`import_relations` 字段）、`cache/architecture-skeleton.json`（可选） |
| **输出** | RelationshipSummary（AI 上下文，供后续工具使用） |
| **前置** | `check-analysis-quality`（exit=0） |
| **后置** | `generate-overview` |

## 优先读取模块分析缓存

在执行依赖综合之前，**首先**检查 `cache/module-analysis.json` 是否存在：

### 路径 A：缓存存在（推荐路径）

读取 `cache/module-analysis.json`，为每个模块提取：
- `dependency_hints.imports`：该模块依赖的其他模块（构成有向依赖边的基础）
- `dependency_hints.imported_by`：依赖该模块的其他模块（辅助反向依赖图）
- `files[].key_insights`：设计意图说明（用于 AI 语义补充，理解依赖背后的 Why）

以上作为**基础输入**，替代"三阶段漏斗"中从上下文窗口读取分析结果的部分。AI 在此基础上做语义补充和交叉验证（见下方"可信基线验证"章节）。

### 路径 B：缓存不存在（降级路径）

若 `cache/module-analysis.json` 不存在（首次运行旧版本或写入失败），退回"三阶段漏斗"逻辑——从 AI 上下文窗口中读取步骤 5 的分析结果。

### 路径 C：同时读取架构骨架（推荐与路径 A 叠加使用）

若 `cache/architecture-skeleton.json` 存在（generate-skeleton 生成），将其作为**验证基线**叠加使用：

- `cross_domain_dependencies`：AI 综合出的依赖边应与骨架方向一致，冲突时以 `code-structure.json` 的 `import_relations` 为最终裁决
- `architecture_layers`：作为分层分组的初始结构，AI 只需验证和补充细节，无需从零推断
- **效果**：步骤 6 从"从零综合"变为"验证修正"，AI 工作量减少约 50%

---

## 输入选择（三阶段漏斗）


1. **按重要性排序** — 从 `high_priority_files`（`importance_score >= 0.6`）开始，再扩展到 `core_files`（`>= 0.5`）。
2. **阈值过滤** — 仅处理 `importance_score >= 0.6` 的文件进行关系分析，过滤低价值工具文件噪音。
3. **数量截断** — 最多处理 150 个文件，每个文件最多展示前 20 个依赖项（防止超大型项目的 Token 溢出）。

**Monorepo 特殊截断策略**：当 archetype == `monorepo` 时：
- 以 package 为单位截断：每个 package 最多取 30 个高优先级文件（`importance_score >= 0.5`）
- 跨包 import 关系（`cross_package: true`）全量保留，不截断
- 优先保留各 package 的入口文件和对外公开的 API 文件
- 若 package 总数 > 20，对低重要性 package（`importance_score < 0.3`）整体跳过，仅记录其对外接口声明

**共享包去重分析**：对于被多个 package 依赖的共享包（如 `@monorepo/utils`、`@monorepo/config`、`libs/*`）：
- 仅分析一次（通常是第一次被依赖时），生成完整的接口和依赖文档
- 后续消费方 package 在依赖分析中**引用**共享包文档而非重复分析
- 在 `RelationshipSummary.key_insights` 中单独列出"被 ≥3 个 package 依赖的共享包"清单，供 overview 页面展示

## 依赖提取（静态层）

从extract-docs的语义分析结果中，提取每个文件已识别的 `import`/`use`/`require` 声明，构建有向依赖边：

| 依赖类型 | 语义含义 | 典型静态证据 |
|---------|---------|------------|
| `Import` | 模块/文件级导入 | `import`、`use`、`require` 语句 |
| `FunctionCall` | 运行时调用依赖 | 跨模块函数调用 |
| `Inheritance` | 类型层次关系 | `extends`、`implements`、子类模式 |
| `Composition` | Has-a 结构包含 | 字段引用、持有类型 |
| `DataFlow` | 组件间的数据传递 | API 载荷、共享状态、消息传递 |
| `Module` | 模糊依赖（兜底） | 当具体类型不明确时使用 |

## AI 综合分析

在静态提取的基础上，参考 `../generation/module-page.md` 中的"依赖关系分析"模板，综合推断：

- **核心模块间的依赖** → 生成有向依赖边列表
- **关键数据流** → 标记 `DataFlow` 类型的边
- **架构分层** → 将模块按层次归组（展示层 → 业务层 → 数据层 → 基础设施层）
- **潜在的循环依赖** → 以警告形式标记

## 输出格式：RelationshipSummary

结构化输出，包含：

- `core_dependencies`：有向依赖边列表（`from`、`to`、`type`、`importance` 1-5）
- `architecture_layers`：模块分层分组
- `key_insights`：架构观察与循环依赖警告

此输出直接用于：

- `architecture.md`（generate-overview）的"模块依赖图"章节（Mermaid `flowchart LR`）
- `doc-map.md`（generate-menu）的"依赖矩阵"章节
- 各模块 `modules/<name>.md`（generate-module-docs）的"依赖关系"章节

## 可信基线验证

extract-structure 产出的 `cache/code-structure.json` 中的 `import_relations` 字段提供了基于 tree-sitter AST 精确解析的文件级导入关系。在 AI 综合分析时，应将此作为**可信基线**进行交叉验证：

1. **导入一致性校验**：AI 推断的模块间 `Import` 类型依赖边，必须能在 `code-structure.json` 的 `import_relations` 中找到对应的文件级 import 语句支持。找不到静态证据的依赖边应降低 `importance` 或标记为"推断依赖"。
2. **遗漏补充**：如果 `import_relations` 中存在跨模块的 import 关系但 AI 未识别，应补充为依赖边（类型 `Import`，`importance` 2-3）。
3. **方向验证**：确认 AI 推断的依赖方向与 `import_relations` 中的实际 import 方向一致（A imports B 意味着 A 依赖 B，而非反向）。
