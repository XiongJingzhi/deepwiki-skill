# Module 生成指南（Core）

> **适用步骤：** `generate-module-docs`（所有模块必读）
> 各组件详细规范（触发条件、格式、生成写法）见 [`module-page-components.md`](module-page-components.md)。

---


> **适用工具：** `generate-module-docs`
> **关联规则：** `../rules/quality-standards.md`、`../rules/components-guide.md`

---

## 文档语言

读取项目 `.deepwiki/config.yaml` 中 `generation.language` 的值（`zh` / `en` / `both`），所有文档内容（章节标题、正文、表格、注释说明）必须使用该语言撰写。代码标识符和专有名词保持原文。默认为 `zh`。详见 [`module-page-components.md`](module-page-components.md) "文档语言"章节。

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

根据 CodePurpose 选择需要生成的组件（触发条件的权威定义见 [`module-page-components.md`](module-page-components.md) 各组件的触发条件）：

{{ SELECTED_COMPONENTS }}

请进行 **全面深度分析**，按各组件的生成规范输出信息。各组件的详细生成规范、格式要求和降级策略见 [`module-page-components.md`](module-page-components.md)。

> **组件触发条件**：以 [`module-page-components.md`](module-page-components.md) 为唯一权威源。本文档不重复列出各组件的触发条件。

输出格式：结构化 YAML，包含所选组件所需的全部字段。仅输出 YAML 内容，不要混入 Markdown 格式。
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

> 详细写作规则见 [`components-guide.md`](../rules/components-guide.md)，各组件的触发条件、格式和降级见 [`module-page-components.md`](module-page-components.md)。

- **按组件生成**：只生成 `SELECTED_COMPONENTS` 中的章节，不生成未选组件。
- **相关源文件（强制首节）**：无论 `SELECTED_COMPONENTS` 内容如何，`相关源文件` 必须作为 H1 标题之后的第一个内容块，前面不得放置任何其他内容（摘要、分隔线、概述、表格等）。使用 `<details open><summary>相关源文件</summary>` 默认展开折叠块，内含 3–10 个带 `file://` 链接（含 `#L起-L止` 行号范围）的源码文件树形列表。详细格式和模板见 [`module-page-components.md`](module-page-components.md) "relevant-source-files" 章节。
- **复合组件优先**：当多个基础组件同时触发且存在对应复合组件时（如 `code-walkthrough` + `sequence-diagram` → `core-flow-walkthrough`），优先使用复合组件，避免内容分散。复合组件定义见 [`module-page-components.md`](module-page-components.md) "复合组件"章节。
- **内容密度优先**：宁可写好 5 个相关章节，也不要凑满 9 个空壳章节。
- **排版顺序**：相关源文件 → 自上而下理解（overview / architecture-diagram / architecture-fit / design-rationale / design-patterns）→ 中层运行模型（internal-structure / execution-flow / data-flow / side-effects / invariants）→ 深入源码（code-walkthrough）→ 接口与图表（api-table / class-diagram / state-diagram / ...）→ 相关文档。不要按源码文件顺序排。
- **章节标题语义化（强制）**：禁止直接使用组件名作为章节标题（如"概述"、"核心逻辑"、"执行流程"、"公开接口"、"内部结构"、"数据流"）。每个章节标题必须反映模块的实际功能含义，如"认证与鉴权核心流程"、"缓存读写与失效策略"、"用户认证 API 参考"。各组件的标题示例见 [`module-page-components.md`](module-page-components.md)。
- **标题简洁化**：模块文档 H1 标题只保留核心功能含义，禁止使用"深入理解"、"基础介绍"、"全面解析"等冗余修饰词。标题格式：直接用功能名称（如"认证与鉴权"），不加任何前缀后缀。
- **来源链接（强制）**：所有源码证据必须使用 `file:///<path>#L起-L止` 格式，行号范围不可省略，禁止链接到整个文件。行号来源：优先使用 `source_files[].ranges` 中的 `start_line`/`end_line`，其次从 `core_source_ranges` 和 `public_interfaces.line/end_line` 推导。
- **图表必须有文字分析**：所有包含 Mermaid 图表的组件（`architecture-diagram`、`sequence-diagram`、`class-diagram`、`state-diagram`、`dependency-diagram`、`er-diagram`）必须在图表前有 2-4 句概述描述，图表后有 2-4 句分析解读。不得只输出标题 + 代码块。
- **源码追溯（强制，缺失则质量降为 basic）**：以下组件必须在章节内包含 `file://` 源码引用，否则质量检查将降级为 basic：
  - `code-walkthrough`：每段源码片段前写 `**Source:** [path](file:///path)`，代码块内容必须与该文件对应
  - `internal-structure` / `execution-flow` / `data-flow`：章节末尾引用涉及的函数/类/文件源码
  - `api-table`：每个接口条目附带源码链接（`file:///路径#L起-L止`），禁止链接整个文件
  - `class-diagram`：每个类引用源码定义
  - `error-table`：每个错误类型引用源码定义
