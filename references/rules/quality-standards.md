# 文档质量标准

> **与 `check-analysis-quality` 的区别：** 本文档定义的是**最终文档**（Markdown）的质量评分体系（百分制，basic/standard/professional），由 `python -m scripts.wiki.postprocess quality` 执行。`check-analysis-quality`（见 [`../workflow/check-analysis-quality.md`](../workflow/check-analysis-quality.md)）是**中间产物**（`module-analysis.json`）的字段完整性门控（二值 pass/fail），由 `validate-analysis` 步骤执行。两者服务于不同阶段，不可混淆。
>
> **Config/Test/Util 豁免说明：** `check-analysis-quality` 对 Config/Test/Util 模块的 `key_insights` 检查有豁免规则。本文档的硬门槛不涉及此豁免——这类模块的最终文档仍需满足源码追溯等基本要求。

所有生成的文档必须满足以下标准：

- **源码追溯是强制要求**：模块文档标题后必须立即包含 `相关源文件`（英文：`Relevant source files`）折叠区块，作为 H1 后的第一个内容块，使用 `<details open>` 默认展开，列出 3-10 个最相关源码文件及行号范围；每个章节末尾必须包含 `[filename](file:///path/to/file.ts#Lx-Ly)` 引用，方便读者跳转到对应源码。
- **禁止链接到整个文件**：所有 `file://` 源码链接必须包含行号范围（`#L起-L止`）。行号来源于 `generation-plan.json` 中 `source_files[].ranges`、`module-analysis.json` 中 `core_source_ranges` 和 `public_interfaces.line/end_line`。未确定行号时，从源码注释/签名位置推导；实在无法确定则使用文件前 50 行作为兜底，不得省略 `#Lx-Ly`。
- **每个模块文档至少包含 1 个视觉元素（Mermaid 图表或结构化表格）**。Config/Util/Test 类模块此要求为可选项。根据内容选择合适的图表类型：
  - `classDiagram` 用于类继承、接口和类型关系
  - `flowchart` 用于流程、工作流和架构概览
  - `sequenceDiagram` 用于交互、API 调用和组件间数据流
  - `stateDiagram` 用于状态机和生命周期转换
- **代码示例必须使用项目的主要语言**（或模块自身语言，多语言项目时），语法正确且具有说明价值。可独立运行的代码示例优先；依赖外部服务（数据库、API）的模块可使用代码片段配以文字说明。SDK/Library 模块应包含调用方语言示例。
- **文档间必须交叉链接**，方便读者在文档网络中导航。
- **内容应解释 WHY（为什么）和 HOW（如何实现）**，而不仅仅是 WHAT（是什么）。包含设计理由、权衡和上下文。
- 使用层级标题（H2/H3/H4）建立清晰的信息架构。
- 使用表格呈现 API、参数和配置选项，便于快速参考。
- 记录边界情况、警告和常见陷阱。

## 源码链接格式

每篇模块文档必须在标题后立即包含源码文件索引。它必须是 H1 后的第一个内容块，前面不能放摘要、分隔线、概述或任何二级标题：

```markdown
<details open><summary>Relevant source files</summary>

- [src/auth/](file:///src/auth/)
  - [service.ts](file:///src/auth/service.ts#L1-L120) - 认证主流程和错误分支
  - [token.ts](file:///src/auth/token.ts#L1-L48) - token 生成与校验

</details>
```

中文文档使用 `相关源文件` 作为 summary 标题：

```markdown
<details open><summary>相关源文件</summary>

- [src/auth/](file:///src/auth/)
  - [service.ts](file:///src/auth/service.ts#L1-L120) - 认证主流程和错误分支
  - [token.ts](file:///src/auth/token.ts#L1-L48) - token 生成与校验

</details>
```

`相关源文件` / `Relevant source files` 必须使用上面的树形列表样式：

- **必须使用 `<details open>` 折叠块**，默认展开状态（`open` 属性不可省略）
- **summary 标题**：英文文档用 `Relevant source files`，中文文档用 `相关源文件`
- **只能使用树形列表格式**，不要使用表格或其他形态
- 目录节点只写目录名（带斜杠后缀），可附带 `file://` 目录链接
- 文件节点必须包含带行号范围的 `file://` 链接（格式：`#L起-L止`）和简短描述
- 不要生成"文件/用途/链接"或"文件路径/说明"表格
- 不要生成 `## 源码索引` / `## 相关源码文件` 章节来替代顶部折叠块

### 源码链接显示格式

源码链接必须遵循以下格式，确保前端渲染正确：

**正确示例：**
```markdown
[build_evidence_index](file:///E:/Python/deepwiki-skill/scripts/quality/build_evidence_index.py#L51-L84)
```

显示效果：`build_evidence_index` + `L51-L84`

**错误示例：**
```markdown
[_page_prefix_for_module (L47-48)](file:///...)  # ❌ 不要在链接文本中包含行号
[L30-44](file:///...)                             # ❌ 不要只显示行号
```

### 章节来源引用

每个章节末尾必须包含源码引用，使用行内样式，与前文同行或紧接在章节末尾：

```markdown
**来源**：[filename.ts](file:///path/to/filename.ts#L10-L25) · [another.ts](file:///path/to/another.ts#L30-L45)
```

代码块标题应包含内联源码链接：

```markdown
**源码：** [path/to/file.ts](file:///path/to/file.ts#L50-L80)
```

### 相关文档链接

相关文档链接必须使用有效的 wiki 内部链接，确保可以跳转：

**正确示例：**
```markdown
- [认证模块](deep-dive/auth.md) - 用户认证流程详解
- [配置参考](reference/config.md) - 完整配置项说明
```

**错误示例：**
```markdown
- `references/workflow/validate-analysis.md`  # ❌ 不要使用 code 标签包裹链接
- shared-foundation deep-dive                   # ❌ 不要使用纯文本
```

### Mermaid 图前文字描述（强制要求）

任何 Mermaid 图表组件前，**必须**有一段简短文字描述（2-4 句），解释图表展示的核心流程或关系。读者在不查看图表的情况下也能通过文字描述理解大致内容。

**格式**：在 ````mermaid` 代码块之前，用普通段落描述图表的核心内容。

## Mermaid 图表选择指南

| 内容类型 | 推荐图表 | 使用场景 |
|---------|---------|---------|
| 实体关系 | `erDiagram` | 数据库模型、ORM 实体、表结构 |
| 类/接口层级 | `classDiagram` | 文档化 OOP 结构、类型关系、继承 |
| 流程/工作流 | `flowchart TB` | 逐步逻辑、请求处理、构建流水线 |
| 组件交互 | `sequenceDiagram` | API 调用序列、客户端-服务端通信、事件流 |
| 状态转换 | `stateDiagram-v2` | 连接生命周期、认证流程、表单验证状态 |
| 模块依赖 | `flowchart LR` | 导入关系图、服务依赖图 |
| 系统架构 | `flowchart TB` + subgraph | 带分组组件的高层系统概览 |

## 交叉链接要求

- 深入理解页必须链接到：架构位置、相关深入理解页、参考索引。
- 参考资料页必须链接到：相关深入理解页、使用示例、相关类型定义。
- overview.md 必须链接到：核心深入理解页和文档地图。
- overview.md 必须链接到：架构文档、快速开始和继续开发指南。

## 质量等级与评分

> 完整的评分体系（评分公式、文档类型 Profile、等级阈值、硬门槛、动态期望值、置信度标注等）见 [`quality-standards-scoring.md`](quality-standards-scoring.md)。生成文档时仅需了解硬门槛和格式要求（见上方），评分公式仅供质量检查参考。

### 硬门槛（生成时必须满足）

- **源码追溯是模块文档和 API 文档的硬门槛**。概览文档和快速开始文档此要求为推荐项。缺少时，模块/API 文档质量等级上限为 `basic`。
- **源码链接全部失效时**，同样降级为 `basic`。
- **`key_insights` 全部为空时**（模块分析深度不足），质量等级上限为 `standard`。

## 模板设计原则

### 组件化组装

```
文档 = 骨架 + 组件集合

骨架：定义文档的基本结构（标题、分隔线、必需章节）
组件：根据 CodePurpose 和模块特征动态选择
```

### 条件章节规则

标注 `（条件：…）` 的章节，仅当条件满足时生成。条件不满足时直接跳过，不要生成空壳内容。

### 语言适配

所有代码示例使用**项目的主要编程语言**。将通用占位符替换为目标项目的实际语法。

### 组件引用

> 组件优先级和选配规则见 [`module-page-components.md`](../generation/module-page-components.md)（P0 权威定义）、[`module-page-extended.md`](../generation/module-page-extended.md)（P1/P2/P3 定义）和 [`components-guide.md`](components-guide.md)（使用指南）。

---
