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

## 2. 架构定位（architecture-fit 组件）
- 所在架构层、上下游边界、负责什么、不负责什么
- 当前模块和核心依赖的关系，必要时用 Mermaid flowchart 高亮当前模块

## 3. 设计思路（design-rationale 组件）
- 设计目标、约束条件、当前方案
- 替代方案和取舍，明确哪些是源码事实，哪些是基于代码结构的推断

## 4. 设计模式（design-patterns 组件）
- 识别实际存在的模式或架构套路，并给出代码证据
- 说明该模式解决的问题、收益和代价；不要强行套模式

## 5. 内部结构（internal-structure 组件）
- 模块内部文件、类、函数或子组件如何分工
- 用职责表解释主要协作关系，必要时用 flowchart 展示内部结构

## 6. 执行流程（execution-flow 组件）
- 从入口到输出的主路径，按阶段解释调度、处理和返回
- 正常路径与异常/降级路径分开说明

## 7. 数据流（data-flow 组件）
- 输入、校验、转换、中间态、持久化或输出
- 明确核心数据结构、DTO/schema/state/event 的变化

## 8. 副作用（side-effects 组件）
- 数据库、文件、网络、缓存、事件、日志、环境变量或全局状态变化
- 说明触发点、影响范围和恢复/回滚方式

## 9. 不变量（invariants 组件）
- 模块必须保持的约束、前置条件、后置条件和边界假设
- 说明由谁维护、破坏后果和源码证据

## 10. 公开接口（api-table 组件）
对于每个导出的函数/类/类型：
- 名称、签名、行号
- **详细描述**：做什么、怎么做、什么场景使用（不少于 2 句）
- **参数说明**：每个参数的含义、约束、默认值
- **返回值说明**：返回什么、可能的值、错误情况

## 11. 时序图（sequence-diagram 组件，条件：CodePurpose in [Api, Service, Agent, Entry]）
- 绘制请求/数据处理流程的 sequenceDiagram
- 或生成流程表格（参与者 > 6 时）

## 12. 核心逻辑（code-walkthrough 组件，条件：复杂度 >= 50 或存在核心执行路径）
- 先输出一段精简版核心源码（伪代码或裁剪代码，10-30 行），概括主路径
- 再输出 1-3 段带中文注释的真实关键源码片段，每段建议 20-80 行
- 逐段解释输入、输出、关键变量、关键分支、依赖调用、错误路径、设计取舍和维护风险

## 13. 性能权衡（performance-tradeoffs 组件）
- 热路径、IO、缓存、并发、批处理、算法复杂度和内存占用
- 当前选择的收益、代价、潜在瓶颈和可优化方向

## 14. 综合取舍（tradeoff-analysis 组件）
- 从可维护性、扩展性、一致性、性能和复杂度维度解释取舍
- 指出什么时候应该重新评估当前设计

## 15. 状态管理（state-diagram 组件，条件：有状态管理）
- 状态机或生命周期图

## 16. 依赖关系（dependency-diagram 组件，条件：依赖数 >= 2）
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
4. **模块文档侧重设计理念和核心逻辑理解**：解释"为什么这样设计"，并通过精简源码、注释源码和逐段说明讲清内部实现逻辑和数据流。
5. **核心逻辑必须充分但不堆叠**：只选择代表主路径、核心算法或关键扩展点的代码；先抽象，再贴关键源码，不整文件搬运。
6. **先自上而下，再中层建模，最后深入核心逻辑**：先解释架构定位、设计思路、模式和权衡，再解释内部结构/执行流/数据流，最后进入核心逻辑。
7. **源码追溯必须精确到行范围**：所有源码证据链接必须使用 `file:///<path>#L<start>-L<end>`。若只能定位单行，使用 `#L<line>`；不要只写文件名。

## 生成要求

### 0. 相关源码文件（Relevant source files，必需）
- 页面标题后必须立即生成一个可折叠区块，标题固定为 `Relevant source files`；这是 H1 后的第一个内容块，不要在它前面放摘要、分隔线、概述、截图式表格或 `## 源码索引` 标题。
- 列出 3-10 个和本页最相关的源码文件，按重要性排序。
- 每一项必须包含：源码链接、行号范围、为什么相关。
- 链接格式固定为：`[src/path/file.ext](file:///src/path/file.ext#L12-L48)`。
- 行号范围必须来自 `public_interfaces.line/end_line`、`core_source_ranges`、`parse-results.json` / `code-structure.json.definitions`，或从本轮读取的源码片段中精确计算。
- 文件必须按目录组织成**树形列表**，不要使用表格，不要生成"文件/用途/行数/链接"、"文件/说明"或"源码索引"这类表格。
- 目录节点只写目录名，文件节点保留源码链接、行号范围和说明；说明文字不要改写或移到单独列。

模板：

```markdown
<details open>
<summary>Relevant source files</summary>

- src/
  - auth/
    - [service.ts](file:///src/auth/service.ts#L24-L88) `L24-L88` - 认证主流程和错误分支
    - [token.ts](file:///src/auth/token.ts#L10-L43) `L10-L43` - token 生成与校验
  - config/
    - [settings.ts](file:///src/config/settings.ts#L1-L32) `L1-L32` - 环境变量配置管理

</details>
```

### 1. 概述（overview 组件，必需）
- 用 2-3 段文字描述模块的目的、解决的问题、核心价值
- 说明模块在整体系统架构中的角色
- 包含架构位置图（Mermaid flowchart，高亮当前模块）

### 2. 核心类与函数（class-diagram 组件，条件：模块包含 class/struct/interface 定义）
- classDiagram：展示核心类/接口的属性、方法、关系
- 图表来源引用

### 3. 架构定位（architecture-fit 组件，条件：核心模块或跨层依赖）
- 说明模块所在层级、上游输入、下游输出和职责边界
- 边界表：| 维度 | 本模块负责 | 不负责 | 证据 |
- 可选架构位置图，高亮当前模块

### 4. 设计思路（design-rationale 组件，条件：核心模块、复杂模块或 key_insights 非空）
- 设计目标、约束条件、当前方案
- 替代方案与取舍表：| 方案 | 收益 | 代价 | 为什么当前没选 |
- 所有推断必须标注依据

### 5. 设计模式（design-patterns 组件，条件：存在明确模式证据）
- 模式/套路名称、代码证据、解决的问题、带来的代价
- 没有明确模式时跳过，不要为了完整性硬凑

### 6. 内部结构（internal-structure 组件，条件：模块包含多个文件、类、函数或公开接口）
- 职责分工表：| 内部单元 | 职责 | 协作者 | 证据 |
- 可选内部结构图，展示文件、类或子组件间协作
- 单文件简单模块可降级为"实现要点"

### 7. 执行流程（execution-flow 组件，条件：存在入口、handler、command、job、worker 或调用链）
- 主流程表：| 阶段 | 入口/执行者 | 输入 | 输出 | 说明 |
- 正常路径和异常/降级路径分开描述
- 不进入逐行代码，源码细节留给"核心逻辑"

### 8. 数据流（data-flow 组件，条件：处理 DTO、schema、payload、state、event 或持久化数据）
- 数据流表：| 阶段 | 数据形态 | 转换/校验 | 去向 | 证据 |
- 区分输入、中间态、持久化数据和输出

### 9. 副作用（side-effects 组件，条件：存在外部写入、网络、缓存、事件、日志或环境变化）
- 副作用表：| 副作用 | 触发点 | 影响范围 | 恢复/回滚方式 | 证据 |
- 若未发现外部副作用，明确说明判断依据

### 10. 不变量（invariants 组件，条件：存在状态、校验、事务、权限、缓存一致性或风险点）
- 约束表：| 约束 | 类型 | 由谁维护 | 破坏后果 | 证据 |
- 只写可验证约束，不写泛泛原则

### 11. 文件结构（file-structure 组件，条件：模块包含 2+ 源文件）
- 目录树 + 职责表

### 12. 公开接口（api-table 组件，必需）
- 接口总览表：| 接口 | 类型 | 描述 | 源码 |
- 对每个公开接口说明：签名 + 源码链接、参数表格、返回值说明

### 13. 请求/数据处理流程（sequence-diagram 组件，条件：CodePurpose in [Api, Service, Agent]）
- Mermaid sequenceDiagram 或流程表格
- 展示完整的处理链

### 14. 核心逻辑（code-walkthrough 组件，条件：复杂度 >= 50、CodePurpose in [Agent, Service, Api, Command] 或存在核心执行路径）
- **精简版核心源码**：先给 10-30 行伪代码或裁剪代码，概括主执行路径，让读者先看懂骨架。
- **带注释关键源码**：再给 1-3 段真实源码片段，每段 20-80 行；添加中文注释解释关键变量、分支、调用、状态变化、错误处理和输出。
- **源码范围**：每段真实源码片段前必须写 `Source: [path](file:///path#Lx-Ly) \`Lx-Ly\``，代码块内容必须与该行范围对应。
- **逐段解释**：代码块后必须提供表格：| 片段 | 做什么 | 为什么这样做 | 关键变量/调用 | 风险 |
- **重要解释**：补充说明核心算法、关键条件、依赖调用、错误路径、边界情况、设计取舍和维护注意事项。
- 若源码过长，先给精简伪代码/裁剪片段，再说明省略了哪些非关键细节；不要整文件搬运。

### 15. 性能权衡（performance-tradeoffs 组件，条件：存在热路径、IO、缓存、批处理、并发或复杂度较高）
- 性能关注点表：| 关注点 | 当前实现 | 收益 | 代价 | 证据 |
- 明确当前不是性能热点时，也要说明判断依据

### 16. 综合取舍（tradeoff-analysis 组件，条件：risk_points 或 extension_points 非空）
- 取舍表：| 维度 | 当前选择 | 收益 | 代价 | 何时重看 |
- 至少覆盖可维护性、扩展性、复杂度、性能中的两个维度

### 17. 状态管理（state-diagram 组件，条件：有状态管理）
- stateDiagram-v2 展示状态机

### 18. 依赖关系（dependency-diagram 组件，条件：有依赖）
- flowchart LR + 依赖说明表

### 19. 错误处理（error-table 组件，条件：有错误定义）
- 错误类型及触发条件表

### 20. 相关文档（nav-links 组件，必需）
- 架构文档链接、相关深入理解页/参考索引链接

### 21. Sources（sources 组件，必需，Test 类模块可豁免）

- 汇总本页各章节中实际引用过的所有源码文件和行号范围
- 来源：各章节 `Source:` 链接和 `Section sources` 链接的并集
- 按文件路径去重排列，每项包含 file:// 链接（含行号范围）和一句话说明

---

### 源码追溯要求

页面必须包含三级源码追溯：

1. 页面顶部 `Relevant source files` 折叠区块，列出本页最相关源码文件和行范围。
2. 描述源码行为的章节（概述、公开接口、核心逻辑、核心类与函数）末尾应包含源码引用。
3. 页面末尾 `Sources` 区块（nav-links 之前），汇总本页所有实际引用过的源码文件和行号范围。

章节源码引用格式：

> **Section sources**
> [filename.ts](file:///path/to/file.ts#L1-L50)

核心逻辑源码片段格式：

````markdown
**Source:** [src/auth/service.ts](file:///src/auth/service.ts#L24-L88) `L24-L88`

```ts
// 这里的代码必须对应 L24-L88 的裁剪片段
```
````

纯导航章节（相关文档）和聚合数据章节（依赖关系、模块依赖图）可豁免此要求。

格式：Markdown，使用中文，代码示例使用项目主要语言。
```

---

> 依赖关系分析复用内部依赖综合规则，详见 [synthesize-deps.md](../workflow/synthesize-deps.md)。模块文档应从 `module-analysis.json.dependency_hints`、`code-structure.json.import_relations` 和概览阶段的依赖综合摘要中提取依赖说明。

---

### 文档骨架分档

根据模块的 `CodePurpose` 选择对应档位的骨架，避免对所有模块强制相同的 10+ 节结构。

| 档位 | 适用 CodePurpose | 节数 | 说明 |
|------|-----------------|------|------|
| **重型** | Entry, Agent, Service, Api | 10-14 | 完整骨架，含架构定位、设计思路、中层运行模型、时序图、核心逻辑、状态管理 |
| **标准** | Page, Widget, Dao, Model, Command, Database | 7-10 | 保留架构定位/设计思路、中层运行模型和核心逻辑；时序图按条件生成 |
| **轻量** | Config, Util, Test, Other | 3-5 | overview + 配置/接口/实现要点 + 相关文档；仅在有证据时补设计思路 |

以下骨架标注了每节的适用档位。生成时只渲染对应档位的节。

## 页面骨架

## 模块文档骨架

> **重要**：模块文档的组件选择基于 CodePurpose。详见 [`components-guide.md`](../rules/components-guide.md) 的"CodePurpose 组件映射"章节。

```markdown
# {MODULE_NAME}

<details open>
<summary>Relevant source files</summary>

[source-file-list 组件：3-10 个源码文件，按目录组织成树形列表；目录节点只写目录名；文件节点包含 file:// 链接、Lx-Ly 行范围和相关原因；不要使用表格]

</details>

---

> {模块一句话描述}

---

<!-- HEAVY | STANDARD | LIGHT -->
## 概述

[overview 组件：模块职责、设计理念、架构位置]

---

<!-- HEAVY | STANDARD -->
## 架构定位（条件：核心模块或跨层依赖）

[architecture-fit 组件：所在层级、职责边界、上下游关系]

---

<!-- HEAVY | STANDARD（轻量模块有明确 key_insights 时也包含） -->
## 设计思路

[design-rationale 组件：目标、约束、当前方案、替代方案与取舍]

---

<!-- HEAVY | STANDARD（仅当存在明确模式证据时） -->
## 设计模式

[design-patterns 组件：模式名称、代码证据、解决的问题、代价]

---

<!-- HEAVY | STANDARD -->
## 内部结构（条件：模块包含多个文件、类、函数或公开接口）

[internal-structure 组件：职责分工、内部协作关系、可选结构图]

---

<!-- HEAVY | STANDARD（存在入口、handler、command、job、worker 或调用链时） -->
## 执行流程

[execution-flow 组件：主路径阶段、输入输出、异常/降级路径]

---

<!-- HEAVY | STANDARD（处理 DTO/schema/payload/state/event/持久化数据时） -->
## 数据流

[data-flow 组件：输入、转换、校验、中间态、持久化或输出]

---

<!-- HEAVY | STANDARD（存在外部写入、网络、缓存、事件、日志或环境变化时） -->
## 副作用

[side-effects 组件：副作用、触发点、影响范围、恢复方式]

---

<!-- HEAVY | STANDARD（存在状态、校验、事务、权限、缓存一致性或风险点时） -->
## 不变量

[invariants 组件：必须成立的约束、维护者、破坏后果、证据]

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
## 核心逻辑（条件：复杂度 >= 50、CodePurpose in [Agent, Service, Api, Command] 或存在核心执行路径）

> **章节名自适应**：Config 模块改用"配置逻辑"，Dao/Database 模块改用"数据访问逻辑"，Util 模块改用"实现要点"，Agent/Service/Api/Command 模块优先使用"核心逻辑"。

[code-walkthrough 组件：精简版核心源码 + Source 链接（file://...#Lx-Ly）+ 带注释关键源码 + 逐段讲解表格 + 重要解释]

---

<!-- HEAVY | STANDARD（仅当存在性能敏感路径或复杂度较高时） -->
## 性能权衡

[performance-tradeoffs 组件：热路径、IO/缓存/并发/复杂度、收益与代价]

---

<!-- HEAVY | STANDARD（risk_points 或 extension_points 非空时） -->
## 综合取舍

[tradeoff-analysis 组件：可维护性、扩展性、一致性、性能、复杂度之间的取舍]

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

> **语言选择**：代码示例优先使用项目主要语言；多语言项目可选择模块自身语言或最相关的语言。SDK/Library 模块应包含调用方语言示例。

[code-example 组件：使用示例]

---

<!-- HEAVY | STANDARD | LIGHT -->
## Sources

[sources 组件：汇总本页各章节实际引用过的所有源码文件和行号范围，按文件去重排列；每项包含 file:// 链接和一句话说明；Test 类模块可豁免]

---

<!-- HEAVY | STANDARD | LIGHT -->
## 相关文档

[nav-links 组件]

---

[<- 返回文档地图](../doc-map.md) | [参考资料 ->](../reference/api-surface.md)
```

### CodePurpose → 组件映射

> 完整映射表详见 [`components-guide.md`](../rules/components-guide.md) 的"CodePurpose 组件映射"章节。

---
