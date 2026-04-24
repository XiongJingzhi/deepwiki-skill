# 依赖关系综合

> 本文件描述工作流synthesize-deps的完整规则：从结构化数据中聚合模块依赖图并验证可信性。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | 无（AI 执行） |
| **输入** | `cache/code-structure.json`（`import_relations` 字段）、`cache/module-analysis.json`（`dependency_hints` 字段）、`cache/architecture-skeleton.json`（可选） |
| **输出** | RelationshipSummary（AI 上下文，供后续工具使用） |
| **前置** | `check-analysis-quality`（exit=0） |
| **后置** | `generate-overview` |

## 核心工作流：聚合 + 验证

本步骤采用**聚合 + 验证**模式，而非让 AI 从零重新推理依赖关系。核心思想：AST 提取的结构化数据已经包含了完整的文件级导入关系，AI 的工作是从已有数据中**聚合**模块级依赖图，并对 AI 分析阶段产生的语义标注进行**验证**。

### 步骤 1：读取 AST 可信基线

读取 `cache/code-structure.json` 中的 `import_relations` 字段。这是由 tree-sitter AST 精确解析产出的文件级导入关系图，作为整个依赖综合的**可信基线**。

数据结构示例：
```json
{
  "src/auth/login.py": {
    "imports": [
      { "module": "src/user/service.py", "line": 12 }
    ]
  }
}
```

Monorepo 项目中，跨包引用会额外标注 `cross_package: true`。

### 步骤 2：读取模块依赖标注

读取 `cache/module-analysis.json`，遍历每个模块提取：

- `dependency_hints.imports`：该模块依赖的其他模块（AI 在步骤 4 中识别的语义依赖）
- `dependency_hints.imported_by`：依赖该模块的其他模块（反向依赖标注）

这些是 AI 在模块分析阶段产生的**语义标注**，包含对依赖类型的理解（如 FunctionCall、DataFlow 等），但不一定都有 AST 级别的静态证据。

### 步骤 3：聚合——以 AST 为基准构建依赖图

以 `import_relations` 为基准，构建模块级有向依赖边：

1. **文件→模块映射**：将 `import_relations` 中的文件级 import 关系聚合到模块级（按 `module-analysis.json` 中的模块划分）。
2. **语义补充**：对于每条 AST 基线边，检查 `dependency_hints` 中是否提供了更丰富的语义信息：
   - 如果 `dependency_hints` 为该边标注了具体类型（FunctionCall / DataFlow / Inheritance / Composition），则采用该类型
   - 否则默认类型为 `Import`
3. **遗漏发现**：扫描 `import_relations` 中存在但 `dependency_hints` 未覆盖的跨模块 import 关系，补充为依赖边（类型 `Import`，`importance` 2-3）。

### 步骤 4：验证——标记可信度

对 `dependency_hints` 中的每条语义依赖边，检查是否在 `import_relations` 中有 AST 证据支持：

| 验证结果 | 标记方式 | 处理 |
|---------|---------|------|
| 在 `import_relations` 中找到对应文件级 import | 无额外标记，`importance` 按 dependency_hints 原值 | 正常纳入依赖图 |
| 在 `import_relations` 中**未找到**证据 | 在 `evidence` 字段标记 `low-confidence`，`importance` 降 1 级（最低为 1） | 仍然纳入，但在 `key_insights` 中列出待确认项 |
| `import_relations` 存在依赖但 AI 未识别 | 补充为 `Import` 类型边 | 步骤 3 已处理 |

**方向验证**：确认依赖方向与 `import_relations` 中的实际 import 方向一致（A imports B 意味着 A 依赖 B）。

### 步骤 5：生成架构分层

读取 `cache/architecture-skeleton.json`（若存在）中的 `architecture_layers` 作为分层初始结构：
- 如果 skeleton 存在，在 skeleton 的分层基础上验证和补充细节，无需从零推断
- 如果 skeleton 不存在，根据聚合后的依赖图和模块 `code_purpose` 归纳分层（展示层 → 业务层 → 数据层 → 基础设施层）

### 步骤 6：输出 RelationshipSummary

按下方"输出格式"章节的结构化格式，输出最终的依赖图。对于 `low-confidence` 边和循环依赖，在 `key_insights` 中单独列出。

---

## 输入数据要求

### 必需输入

1. **`cache/code-structure.json`** — `import_relations` 字段（tree-sitter AST 解析结果）
2. **`cache/module-analysis.json`** — 各模块的 `dependency_hints` 字段

### 可选输入

3. **`cache/architecture-skeleton.json`** — `architecture_layers`、`cross_domain_dependencies`（作为分层基线和辅助验证）

### 降级处理

若 `cache/code-structure.json` 不存在，退回使用 `module-analysis.json` 的 `dependency_hints` 构建依赖图，所有边的 `importance` 降 1 级（最低为 1），并在 `key_insights` 中注明"缺乏 AST 验证，依赖图基于 AI 推断"。

若 `cache/module-analysis.json` 不存在，仅使用 `import_relations` 构建纯结构化依赖图（类型全部为 `Import`），跳过语义补充和验证步骤。

---

## 依赖类型定义

| 依赖类型 | 语义含义 | 数据来源 |
|---------|---------|---------|
| `Import` | 模块/文件级导入 | `import_relations` AST 证据 |
| `FunctionCall` | 运行时调用依赖 | `dependency_hints` 语义标注 |
| `Inheritance` | 类型层次关系 | `dependency_hints` 语义标注 |
| `Composition` | Has-a 结构包含 | `dependency_hints` 语义标注 |
| `DataFlow` | 组件间的数据传递 | `dependency_hints` 语义标注 |
| `Module` | 模糊依赖（兜底） | 当具体类型不明确时使用 |

---

## 截断策略

### 常规项目

- 最多处理 150 个文件，每个模块最多展示前 20 个依赖项（防止超大型项目的 Token 溢出）
- 仅处理 `importance_score >= 0.6` 的模块进行深度依赖分析

### Monorepo 特殊截断策略

当 archetype == `monorepo` 时：
- 以 package 为单位截断：每个 package 最多取 30 个高优先级文件（`importance_score >= 0.5`）
- 跨包 import 关系（`cross_package: true`）全量保留，不截断
- 优先保留各 package 的入口文件和对外公开的 API 文件
- 若 package 总数 > 20，对低重要性 package（`importance_score < 0.3`）整体跳过，仅记录其对外接口声明

### 共享包去重分析

对于被多个 package 依赖的共享包（如 `@monorepo/utils`、`@monorepo/config`、`libs/*`）：
- 仅分析一次（通常是第一次被依赖时），生成完整的接口和依赖文档
- 后续消费方 package 在依赖分析中**引用**共享包文档而非重复分析
- 在 `RelationshipSummary.key_insights` 中单独列出"被 ≥3 个 package 依赖的共享包"清单，供 overview 页面展示

---

## 输出格式：RelationshipSummary

结构化输出，包含：

- `core_dependencies`：有向依赖边列表（`from`、`to`、`type`、`importance` 1-5）
- `architecture_layers`：模块分层分组
- `reverse_dependencies`：反向依赖映射（用于增量更新）
- `key_insights`：架构观察、循环依赖警告、低置信度依赖列表

此输出直接用于：

- `overview.md`（generate-overview）的"模块依赖图"章节（Mermaid `flowchart LR`）
- `doc-map.md`（generate-menu）的"依赖矩阵"章节
- 各模块 `modules/<name>.md`（generate-module-docs）的"依赖关系"章节
