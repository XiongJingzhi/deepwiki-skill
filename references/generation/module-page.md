# Module 生成指南

> **适用工具：** `generate-module-docs`
> **关联规则：** `../rules/quality-standards.md`、`../rules/components-guide.md`

---

## 生成指导

## 代码深度分析

分析代码文件，提取完整的语义信息：

```
深度分析以下代码文件：

文件: {{ FILE_PATH }}
语言: {{ LANGUAGE }}
CodePurpose: {{ CODE_PURPOSE }}
完整代码内容:
{{ CODE_CONTENT }}

预提取的文档注释（由 extract_doc_comments.py 生成）:
{{ EXTRACTED_DOCS }}

### 语言术语规范

根据文件扩展名检测源语言，使用对应的术语：

| 语言 | 扩展名 | 函数/方法术语 | 文档注释风格 |
|------|--------|---------------|-------------|
| JavaScript/TypeScript | `.js` `.ts` `.tsx` | function | JSDoc (`/** */`) |
| Python | `.py` | function | docstring (`"""`) |
| Java | `.java` | method | Javadoc (`/** */`) |
| C# | `.cs` | method | XML doc (`///`) |
| Go | `.go` | function / method | `//` comments |
| Rust | `.rs` | fn | `///` / `//!` doc comments |

### 文档注释提取

- **JS/TS/Python/Java/C#**：从文档注释中提取文档。保留 `@param`、`@returns`、`@throws`、`@deprecated` 标签。
- **Go**：从导出标识符前的 `//` 注释中提取文档。注意 `// Deprecated:` 注解。
- **Rust**：从 `///` 和 `//!` 注释中提取文档。保留 `# Examples`、`# Panics`、`# Errors`、`# Safety` 章节。

### 分析原则

- **优先使用预提取结果**：`EXTRACTED_DOCS` 已从源码中提取了签名、参数、返回值和示例。
- **解释 WHY 和 HOW**：不只描述代码做了什么（WHAT），更要解释为什么这样设计（WHY）和如何实现的（HOW）。
- **区分事实与推断**：直接从代码中观察到的信息标记为事实，推断的设计意图标记为推断。

### 组件选择

根据 CodePurpose 选择需要生成的组件：

{{ SELECTED_COMPONENTS }}

请进行 **全面深度分析**，输出所选组件所需的信息：

## 1. 模块概述（overview 组件）
- **核心职责**：详细描述模块解决什么问题，为什么需要这个模块（3-5 句）
- **设计理念**：采用了什么设计模式/架构思想，为什么这样设计
- **在系统中的位置**：与其他模块的关系，在整体架构中扮演什么角色

## 2. 公开接口（api-table 组件）
对于每个导出的函数/类/类型：
- 名称、签名、行号
- **详细描述**：做什么、怎么做、什么场景使用（不少于 2 句）
- **参数说明**：每个参数的含义、约束、默认值
- **返回值说明**：返回什么、可能的值、错误情况

## 3. 时序图（sequence-diagram 组件，条件：CodePurpose in [Api, Service, Agent, Entry]）
- 绘制请求/数据处理流程的 sequenceDiagram
- 或生成流程表格（参与者 > 6 时）

## 4. 核心实现（code-walkthrough 组件，条件：复杂度 >= 50）
- 关键代码片段的逐块讲解
- 设计意图说明

## 5. 状态管理（state-diagram 组件，条件：有状态管理）
- 状态机或生命周期图

## 6. 依赖关系（dependency-diagram 组件，条件：依赖数 >= 2）
- 内部依赖、外部依赖、被依赖

输出格式：结构化 YAML，包含上述所有字段。仅输出 YAML 内容，不要混入 Markdown 格式。
```

---

## 模块文档

生成专业的模块说明文档：

```
根据以下信息生成 **专业级模块文档**：

模块名: {{ MODULE_NAME }}
模块路径: {{ MODULE_PATH }}
CodePurpose: {{ CODE_PURPOSE }}
文件列表: {{ FILE_LIST }}
代码分析结果: {{ CODE_ANALYSIS }}
项目上下文: {{ PROJECT_CONTEXT }}

---

## 组件选择

已选组件: {{ SELECTED_COMPONENTS }}

---

## 生成原则

1. **按组件生成**：根据已选组件列表生成对应章节，不要生成未选中的组件。
2. **条件章节**：仅生成符合当前模块特征的适用章节（各组件标题已标注触发条件）。
3. **内容密度优先**：宁可写好 5 个相关章节，也不要凑满 9 个空壳章节。
4. **模块文档侧重设计理念**：解释"为什么这样设计"，内部实现逻辑和数据流。

## 生成要求

### 1. 概述（overview 组件，必需）
- 用 2-3 段文字描述模块的目的、解决的问题、核心价值
- 说明模块在整体系统架构中的角色
- 包含架构位置图（Mermaid flowchart，高亮当前模块）

### 2. 核心类与函数（class-diagram 组件，条件：模块包含 class/struct/interface 定义）
- classDiagram：展示核心类/接口的属性、方法、关系
- 图表来源引用

### 3. 文件结构（file-structure 组件，条件：模块包含 2+ 源文件）
- 目录树 + 职责表

### 4. 公开接口（api-table 组件，必需）
- 接口总览表：| 接口 | 类型 | 描述 | 源码 |
- 对每个公开接口说明：签名 + 源码链接、参数表格、返回值说明

### 5. 请求/数据处理流程（sequence-diagram 组件，条件：CodePurpose in [Api, Service, Agent]）
- Mermaid sequenceDiagram 或流程表格
- 展示完整的处理链

### 6. 核心实现（code-walkthrough 组件，条件：复杂度 >= 50 或 CodePurpose in [Agent, Service, Api]）
- 关键代码片段 + 逐块讲解表格
- 或带注释代码 + 关键点说明

### 7. 状态管理（state-diagram 组件，条件：有状态管理）
- stateDiagram-v2 展示状态机

### 8. 依赖关系（dependency-diagram 组件，条件：有依赖）
- flowchart LR + 依赖说明表

### 9. 错误处理（error-table 组件，条件：有错误定义）
- 错误类型及触发条件表

### 10. 相关文档（nav-links 组件，必需）
- 架构文档链接、API 参考链接、相关模块文档链接

---

### 源码追溯要求

描述源码行为的章节（概述、公开接口、核心实现、核心类与函数）末尾应包含源码引用，格式：

> **Section sources**
> [filename.ts](file:///path/to/file.ts#L1-L50)

纯导航章节（相关文档）和聚合数据章节（依赖关系、模块依赖图）可豁免此要求。

格式：Markdown，使用中文，代码示例使用项目主要语言。
```

---

> 依赖关系分析由独立管线步骤 `synthesize-deps` 完成，详见 [synthesize-deps.md](../workflow/synthesize-deps.md)。模块文档引用其输出的 `dependency_summary` 字段。

---

### 文档骨架分档

根据模块的 `CodePurpose` 选择对应档位的骨架，避免对所有模块强制相同的 10+ 节结构。

| 档位 | 适用 CodePurpose | 节数 | 说明 |
|------|-----------------|------|------|
| **重型** | Entry, Agent, Service, Api | 8-10 | 完整骨架，含时序图、代码走读、状态管理 |
| **标准** | Page, Widget, Dao, Model, Command, Database | 5-7 | 去掉强时序图和代码走读，保留核心节 |
| **轻量** | Config, Util, Test, Other | 3-4 | 仅 overview + 接口/配置表 + 依赖 + 导航 |

以下骨架标注了每节的适用档位。生成时只渲染对应档位的节。

## 页面骨架

## 模块文档骨架

> **重要**：模块文档的组件选择基于 CodePurpose。详见 [`components-guide.md`](../rules/components-guide.md) 的"CodePurpose 组件映射"章节。

```markdown
# {MODULE_NAME}

> {模块一句话描述}

---

<!-- HEAVY | STANDARD | LIGHT -->
## 概述

[overview 组件：模块职责、设计理念、架构位置]

---

<!-- HEAVY | STANDARD -->
## 核心类与函数（条件：模块包含 class/struct/interface/enum 定义）

[class-diagram 组件：展示类关系]

---

<!-- HEAVY | STANDARD -->
## 文件结构（条件：模块包含 2+ 源文件）

[file-structure 组件：目录树 + 职责表]

---

<!-- HEAVY | STANDARD | LIGHT -->
## 公开接口

[api-table 组件：接口总览表]

---

<!-- HEAVY（或满足触发条件时 STANDARD 也包含） -->
## 请求/数据处理流程（条件：CodePurpose in [Api, Service, Agent, Entry]）

[sequence-diagram 组件：展示处理链]

---

<!-- HEAVY（仅当 complexity >= 50 或 CodePurpose in [Agent, Service, Api] 时） -->
## 核心实现（条件：复杂度 >= 50 或 CodePurpose in [Agent, Service, Api]）

[code-walkthrough 组件：关键代码讲解]

---

<!-- HEAVY（仅当存在状态管理时） -->
## 状态管理（条件：有显式状态管理）

[state-diagram 组件：状态机或生命周期]

---

<!-- HEAVY | STANDARD（仅当存在依赖关系时） -->
## 依赖关系（条件：有内部依赖或被依赖）

[dependency-diagram 组件：依赖图 + 依赖表]

---

<!-- HEAVY（仅当存在错误处理逻辑时） -->
## 错误处理（条件：有自定义错误类型）

[error-table 组件：错误类型 + 处理方式]

---

<!-- HEAVY（仅当存在可独立运行的代码时） -->
## 代码示例

[code-example 组件：使用示例]

---

<!-- HEAVY | STANDARD | LIGHT -->
## 相关文档

[nav-links 组件]

---

[<- 返回模块列表](_index.md) | [API 参考 ->](../api/{MODULE_NAME}.md)
```

### CodePurpose → 组件映射

> 完整映射表详见 [`components-guide.md`](../rules/components-guide.md) 的"CodePurpose 组件映射"章节。

---
