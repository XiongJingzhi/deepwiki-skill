# AI 提示词模板

本文件包含用于生成**专业级** Wiki 内容的 AI 提示词模板。

> **质量标准**：参见 [SKILL.md](../SKILL.md) 中的"文档质量标准"章节，此处不再重复。
> **条件章节**：模板中标注 `（条件：…）` 的章节，仅当条件满足时生成。条件不满足时直接跳过，不要生成空壳内容。
> **组件选择**：文档生成前，必须先根据 CodePurpose 选择组件。详见 [`components.md`](components.md)。

## 目录

1. [组件选择流程](#组件选择流程)
2. [代码深度分析](#代码深度分析)
3. [模块文档](#模块文档)
4. [架构文档](#架构文档)
5. [API 文档](#api-文档)
6. [依赖关系分析](#依赖关系分析)
7. [关系图谱](#关系图谱)
8. [首页与快速开始](#首页与快速开始)

---

## 组件选择流程

> **重要**：在生成任何文档之前，必须先执行组件选择流程。
>
> **检测规则**：CodePurpose 检测信号和条件组件触发规则详见 [`codepurpose-detection.md`](codepurpose-detection.md)。
>
> **组件映射**：CodePurpose → 默认组件集详见 [`components.md`](components.md) 的"CodePurpose 组件映射"章节。

### 选择流程

1. **识别 CodePurpose**：根据文件路径和内容特征，参考 [`codepurpose-detection.md`](codepurpose-detection.md) 的检测信号表
2. **选择默认组件集**：根据 CodePurpose 选择必需组件，参考 [`components.md`](components.md) 的映射表
3. **添加条件组件**：根据模块特征（复杂度、依赖数、类定义等）添加条件组件
4. **AI 补充推荐**：对于复杂模块，可让 AI 分析后推荐额外组件

### AI 补充推荐 Prompt

```
分析以下模块，推荐额外需要的文档组件：

模块：{module_name}
CodePurpose：{code_purpose}
复杂度：{complexity}
已选组件：{selected_components}

可选组件：[usage-patterns, decision-table, ...]

返回 JSON：{ "add_components": [...], "reasoning": "..." }
```

---

## 代码深度分析

分析代码文件，提取完整的语义信息：

```
深度分析以下代码文件：

文件: {{ FILE_PATH }}
语言: {{ LANGUAGE }}
CodePurpose: {{ CODE_PURPOSE }}
完整代码内容:
{{ CODE_CONTENT }}

预提取的文档注释（由 extract_docs.py 生成）:
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
2. **条件章节**：参考 templates.md 中的条件标注，仅生成适用的章节。
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

## 源码追溯要求

每个章节末尾必须包含源码引用：

**Section sources**
- [filename.ts](file:///path/to/file.ts#L1-L50)

格式：Markdown，使用中文，代码示例使用项目主要语言。
```

---

## 架构文档

生成系统架构概览：

```
根据以下项目信息生成 **专业级架构文档**：

项目名: {{ PROJECT_NAME }}
技术栈: {{ TECH_STACK }}
模块列表: {{ MODULES }}
入口文件: {{ ENTRY_POINTS }}
代码分析: {{ CODE_ANALYSIS }}
依赖关系分析结果: {{ DEPENDENCY_ANALYSIS }}

---

## 生成要求

### 1. 整体摘要（overview 组件）
- 项目定位和核心价值（1 段）
- 技术选型概述（1 段）
- 架构风格说明（分层/微服务/事件驱动等）

### 2. 系统架构图（architecture-diagram 组件）
Mermaid `flowchart TB`，要求：
- 分层展示（UI 层、业务层、数据层等）
- 每层内的模块用 subgraph 分组
- 箭头标注数据流向和依赖关系
- 不同颜色区分模块类型
- 标注关键接口和协议

### 3. 技术栈（api-table 组件）
| 类别 | 技术 | 版本 | 选型原因 | 文档链接 |

### 4. 模块说明
对每个模块：名称 + 链接、职责描述、核心接口列表、依赖关系。

### 5. 数据流（sequence-diagram 组件，条件：项目涉及 API 调用或跨组件数据传递）
Mermaid `sequenceDiagram`，展示典型场景的完整数据流。

### 6. 模块依赖图（dependency-diagram 组件）
Mermaid `flowchart LR`，展示所有模块间的依赖方向和类型。

### 7. 目录结构（file-structure 组件）
带注释的目录树 + 职责说明。

### 8. 相关文档（nav-links 组件）
各模块文档链接表格、外部依赖文档。

## Mermaid 规范

- 节点 ID 只用字母数字下划线（中文名必须转为拼音或英文 ID）
- 标签用双引号包裹中文：`A["中文标签"]`
- 使用 style 定义不同模块类型的颜色
- 禁止在节点 ID 或 subgraph ID 中直接使用中文字符

## 源码追溯要求

每个章节末尾必须包含源码引用。
```

---

## API 文档

生成 API 参考文档：

```
为以下模块生成 **专业级 API 文档**：

模块名: {{ MODULE_NAME }}
CodePurpose: {{ CODE_PURPOSE }}
代码分析: {{ CODE_ITEMS }}

---

## 生成原则

1. **按组件生成**：根据已选组件列表生成对应章节。
2. **API 文档侧重接口**：以接口签名和调用方式为核心，不重复模块文档的设计理念内容。
3. **代码示例必须可运行**：包含完整的导入、初始化、调用和输出处理。

## 生成要求

### 1. 模块概述（overview 组件，必需）
用途、导入方式、快速示例

### 2. 接口总览表（api-table 组件，必需）
| 接口 | 类型 | 描述 | 源码 |

### 3. 类型定义（api-table 变体，条件：模块导出自定义类型）
对每个类型：签名、字段表格、使用示例

### 4. 函数详解（条件：模块导出函数/方法）
对每个函数：
- 标题 + 源码链接
- 一句话概述 + 详细描述
- 函数签名
- 参数表：| 参数 | 类型 | 必填 | 默认值 | 描述 |
- 返回值表：| 类型 | 描述 |
- 异常表（条件：函数会抛出异常）
- 代码示例

### 5. 类详解（条件：模块导出 class/struct/enum）
- 类描述、classDiagram 继承关系图
- 构造函数、属性表格、方法列表
- 完整使用示例

### 6. 使用模式（usage-patterns 组件，条件：模块复杂度 >= 中等）
2-3 个完整场景

### 7. 相关文档（nav-links 组件，必需）
模块文档、架构文档、外部资源

链接格式: [源码](file://{{ SOURCE_PATH }}#L{{ LINE_NUMBER }})

## 源码追溯要求

每个函数/类章节末尾必须包含源码引用。
```

---

## 依赖关系分析

> 对应 SKILL.md 第 5 步：在深度阅读源码后执行，将孤立的文件分析转化为连贯的架构依赖图。

```
根据以下代码洞察生成 **项目依赖关系图**：

高优先级文件洞察（importance_score >= 0.6）:
{{ HIGH_PRIORITY_INSIGHTS }}

每条洞察格式：
[组件名] | [CodePurpose] | [文件路径] | [重要性评分] | [复杂度] | [依赖项列表]

---

## 分析要求

请生成一份结构化的依赖关系分析，包含以下三个部分：

### 1. 核心依赖关系（core_dependencies）

列出项目中最重要的模块间依赖边，每条依赖包含：
- **from**：来源模块/文件名
- **to**：目标模块/文件名
- **type**：依赖类型
- **importance**：重要性 1-5
- **description**：一句话描述

### 2. 架构分层（architecture_layers）

将所有组件按架构层次归组：
- **name**：层名称
- **level**：层级数字
- **components**：属于该层的组件名列表

### 3. 反向依赖映射（reverse_dependencies）

为每个模块列出依赖它的模块。

### 4. 关键洞察（key_insights）

3-5 条架构观察。

---

## 输出格式

严格按 JSON 结构输出：

```json
{
  "core_dependencies": [...],
  "architecture_layers": [...],
  "reverse_dependencies": {...},
  "key_insights": [...]
}
```
```

---

## 关系图谱

生成文档关系图谱：

```
根据项目结构生成 **文档关系图谱**：

模块列表: {{ MODULES }}
文档列表: {{ DOCS }}

---

## 生成要求

### 1. 全局文档地图（architecture-diagram 变体）
Mermaid `flowchart TB`，展示所有文档之间的关系。

### 2. 模块依赖矩阵（decision-table 变体）
| 模块 | 依赖 | 被依赖 |

### 3. 阅读路径推荐
根据读者角色推荐路径。

### 4. 文档索引
按类别列出所有文档。
```

---

## 首页与快速开始

> `index.md` 和 `getting-started.md` 参考 `templates.md` 中的骨架模板生成。

**生成建议**：
- `index.md`：从 README.md 提取项目简介、核心特性和架构预览。
- `getting-started.md`：从 README 的安装章节和入口文件提取前置条件、安装步骤和最小可运行示例。

---

## 置信度标注规范

> **核心原则**：让 AI 对每条断言标注"证据来源"和"置信度"，区分事实与推断。

### 置信度等级定义

| 等级 | 符号 | 定义 | 证据来源 |
|------|------|------|---------|
| **高置信** | 🟢 | 断言直接来自源码或文档注释 | 源码行号、docstring、JSDoc |
| **中置信** | 🟡 | 断言从代码结构推断 | 类继承关系、方法签名、导入语句 |
| **低置信** | 🔴 | 断言从命名约定或常见模式推断 | 变量名、文件名、目录结构 |

### 标注规则

**规则 1：高置信断言必须附带源码引用**

**规则 2：中置信断言必须说明推断依据**

**规则 3：低置信断言必须标注"待确认"**

**规则 4：禁止无证据来源的高置信断言**
