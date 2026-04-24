# 依赖关系综合

> 本文件描述工作流第 5 步的完整规则：从源码分析结果中综合提取模块依赖图。

## 输入选择（三阶段漏斗）

1. **按重要性排序** — 从 `high_priority_files`（`importance_score >= 0.6`）开始，再扩展到 `core_files`（`>= 0.5`）。
2. **阈值过滤** — 仅处理 `importance_score >= 0.6` 的文件进行关系分析，过滤低价值工具文件噪音。
3. **数量截断** — 最多处理 150 个文件，每个文件最多展示前 20 个依赖项（防止超大型项目的 Token 溢出）。

## 依赖提取（静态层）

从第 4 步的语义分析结果中，提取每个文件已识别的 `import`/`use`/`require` 声明，构建有向依赖边：

| 依赖类型 | 语义含义 | 典型静态证据 |
|---------|---------|------------|
| `Import` | 模块/文件级导入 | `import`、`use`、`require` 语句 |
| `FunctionCall` | 运行时调用依赖 | 跨模块函数调用 |
| `Inheritance` | 类型层次关系 | `extends`、`implements`、子类模式 |
| `Composition` | Has-a 结构包含 | 字段引用、持有类型 |
| `DataFlow` | 组件间的数据传递 | API 载荷、共享状态、消息传递 |
| `Module` | 模糊依赖（兜底） | 当具体类型不明确时使用 |

## AI 综合分析

在静态提取的基础上，参考 `references/prompts.md` 中的"依赖关系分析"模板，综合推断：

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

- `architecture.md`（第 6 步）的"模块依赖图"章节（Mermaid `flowchart LR`）
- `doc-map.md`（第 7 步）的"依赖矩阵"章节
- 各模块 `modules/<name>.md`（第 8 步）的"依赖关系"章节

## 可信基线验证

第 2.5 步产出的 `cache/import-relations.json` 提供了基于静态分析的文件级导入关系。在 AI 综合分析时，应将此作为**可信基线**进行交叉验证：

1. **导入一致性校验**：AI 推断的模块间 `Import` 类型依赖边，必须能在 `import-relations.json` 中找到对应的文件级 import 语句支持。找不到静态证据的依赖边应降低 `importance` 或标记为"推断依赖"。
2. **遗漏补充**：如果 `import-relations.json` 中存在跨模块的 import 关系但 AI 未识别，应补充为依赖边（类型 `Import`，`importance` 2-3）。
3. **方向验证**：确认 AI 推断的依赖方向与 `import-relations.json` 中的实际 import 方向一致（A imports B 意味着 A 依赖 B，而非反向）。
