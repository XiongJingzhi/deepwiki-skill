# 文档组件指南

> **组件注册表**：完整的组件定义（name、purpose、format、trigger、fallback、required_context）见 [`components-registry.yaml`](components-registry.yaml)。

---

## 目录

1. [组件优先级总览](#组件优先级总览)
2. [CodePurpose 组件映射](#codepurpose-组件映射)
3. [组件选择双层策略](#组件选择双层策略)
4. [降级策略](#降级策略)
5. [组件选择流程](#组件选择流程)
6. [时序图生成规范](#时序图生成规范)
7. [自上而下理解规范](#自上而下理解规范)
8. [中层运行模型规范](#中层运行模型规范)
9. [核心逻辑规范](#核心逻辑规范)

---

## 组件优先级总览

| 优先级 | 组件 |
|:------:|------|
| **P0**（必需） | `relevant-source-files`（固定顶部）, overview（Test/极轻量占位除外）, `sources`（nav-links 之前，Test 可豁免）, nav-links |
| **P0-条件** | api-table（有公开接口/导出时必需；纯配置或内部文件可降级） |
| **P1**（高） | architecture-fit（核心模块、跨层依赖、Entry/Service/Api/Agent 必需或强推荐）, design-rationale（有 key_insights、风险点、扩展点、复杂逻辑时要求）, internal-structure（多文件、多类、多函数协作时要求）, execution-flow（有入口、handler、command 时要求）, data-flow（有 DTO、状态、持久化时要求）, sequence-diagram（有跨组件时序交互时要求）, code-walkthrough（Agent/Service/Api/Command 或核心执行路径必需；轻量 Util/Config 可选）, architecture-diagram |
| **P2**（中） | design-patterns, performance-tradeoffs, tradeoff-analysis, side-effects, invariants, class-diagram, state-diagram, dependency-diagram, er-diagram, decision-table, code-example |
| **P3**（低） | error-table（有对应证据时要求，不要硬凑）, file-structure, usage-patterns |

---

## CodePurpose 组件映射

### 映射表

| CodePurpose | 默认组件集 | sequence-diagram | code-walkthrough |
|-------------|-----------|:----------------:|:----------------:|
| **Entry** | relevant-source-files → overview → architecture-fit → design-rationale → internal-structure → execution-flow → architecture-diagram → sequence-diagram → code-walkthrough → sources → nav-links | ✅ 必需 | 推荐 |
| **Agent** | relevant-source-files → overview → architecture-fit → design-rationale → design-patterns → internal-structure → execution-flow → data-flow → side-effects → invariants → sequence-diagram → code-walkthrough → state-diagram → performance-tradeoffs → sources → nav-links | ✅ 必需 | ✅ 必需 |
| **Page** | relevant-source-files → overview → architecture-fit → design-rationale → internal-structure → execution-flow → data-flow → architecture-diagram → api-table → code-walkthrough → performance-tradeoffs → code-example → sources → nav-links | 可选 | 推荐 |
| **Widget** | relevant-source-files → overview → architecture-fit → design-rationale → internal-structure → data-flow → api-table → code-walkthrough → performance-tradeoffs → code-example → sources → nav-links | - | 推荐 |
| **Service** | relevant-source-files → overview → architecture-fit → design-rationale → design-patterns → internal-structure → execution-flow → data-flow → side-effects → invariants → api-table → sequence-diagram → code-walkthrough → performance-tradeoffs → sources → nav-links | ✅ 必需 | ✅ 必需 |
| **Api** | relevant-source-files → overview → architecture-fit → design-rationale → internal-structure → execution-flow → data-flow → side-effects → invariants → api-table → sequence-diagram → code-walkthrough → performance-tradeoffs → error-table → sources → nav-links | ✅ 必需 | ✅ 必需 |
| **Dao** | relevant-source-files → overview → architecture-fit → design-rationale → internal-structure → data-flow → side-effects → invariants → api-table → code-walkthrough → performance-tradeoffs → sources → nav-links | 可选 | 推荐 |
| **Model** | relevant-source-files → overview → architecture-fit → internal-structure → invariants → class-diagram → api-table → sources → nav-links | - | 可选 |
| **Config** | relevant-source-files → overview → design-rationale → invariants → tradeoff-analysis → api-table → sources → nav-links | - | 可选 |
| **Database** | relevant-source-files → overview → architecture-fit → design-rationale → internal-structure → data-flow → side-effects → invariants → erDiagram → code-walkthrough → performance-tradeoffs → sources → nav-links | 可选 | 推荐 |
| **Util** | relevant-source-files → overview → design-rationale → internal-structure → invariants → api-table → code-walkthrough → code-example → sources → nav-links | - | 推荐 |
| **Command** | relevant-source-files → overview → architecture-fit → design-rationale → internal-structure → execution-flow → side-effects → architecture-diagram → api-table → code-walkthrough → performance-tradeoffs → code-example → sources → nav-links | 可选 | ✅ 必需 |
| **Other** | relevant-source-files → overview → api-table → sources → nav-links | AI 推荐 | AI 推荐 |

> 完整 CodePurpose 类型列表：Entry, Agent, Page, Widget, Service, Api, Dao, Model, Config, Database, Util, Command, Other。详见 [`codepurpose-detection.md`](codepurpose-detection.md)。

### 图例

- ✅ 必需：该 CodePurpose 下必须生成此组件
- 可选：根据实际内容判断是否生成
- AI 推荐：由第二层 AI 分析决定
- `-`：通常不需要

---

## 组件选择双层策略

### 第一层：规则触发（快速、确定性）

**执行时机**：读取 structure.json 后立即执行
**输入**：CodePurpose、复杂度、依赖数、文件结构
**输出**：必需组件列表 + 条件组件候选

规则触发由 [`components-registry.yaml`](components-registry.yaml) 的组件 `trigger` 字段和 `archetype_overrides` 统一维护。本文只说明选择流程，不重复定义条件逻辑。

### 第二层：AI 推荐（补充、语义性）

**执行时机**：深度阅读源码后
**输入**：源码内容、第一层结果、项目上下文
**输出**：推荐组件列表 + 生成参数

```
分析以下模块，推荐应生成的文档组件：

模块：{module_name}
用途：{code_purpose}
复杂度：{complexity}
核心职责：{responsibilities}

已选组件：{selected_components}

可选组件：[architecture-fit, design-rationale, internal-structure, execution-flow, data-flow, side-effects, invariants, design-patterns, performance-tradeoffs, tradeoff-analysis, usage-patterns, error-table, file-structure, decision-table]

请返回 JSON：
{
  "add_components": ["组件名", ...],
  "remove_components": ["组件名", ...],
  "reasoning": "原因说明"
}
```

**Layer 3：Archetype 覆写**

读取当前项目的 archetype，按 `components-registry.yaml` 的 `archetype_overrides` 增删组件：

1. 若 archetype 有对应的 `add` 规则，且 `trigger` 条件满足（`always` 或 CodePurpose 匹配），则添加对应组件
2. 若 archetype 有对应的 `remove` 规则，且 `trigger` 条件满足，则移除对应组件（除非 Layer 1/2 已将其标记为 Required）
3. `remove` 不会覆盖 Required 组件（P0），仅影响 Recommended 和 Optional 组件
   注意：P0 组件的触发条件豁免（如 Test 模块的 overview、无导出模块的 api-table）不受此保护，archetype 覆写可基于 trigger 条件跳过这些 P0 组件。

示例：`agent-project` archetype 下，`state-diagram` 对所有模块添加；`sequence-diagram` 对非 API/Entry/Service 模块移除。

---

## 降级策略

| 组件 | LLM 失败时的降级方案 |
|------|---------------------|
| architecture-fit | 输出"所在层 / 负责什么 / 不负责什么"三列表格 |
| design-rationale | 输出目标、约束、当前方案三段；无法确认时标注"推断" |
| internal-structure | 输出职责分工表 |
| execution-flow | 输出 3-5 步主流程列表 |
| data-flow | 输出输入/转换/输出表 |
| side-effects | 无副作用时明确写"未发现外部副作用" |
| invariants | 输出输入约束和边界假设 |
| design-patterns | 无明确模式时写"未发现强设计模式"，不强行套模式 |
| performance-tradeoffs | 无明显热点时写"当前不是性能热点"和判断依据 |
| tradeoff-analysis | 合并到 design-rationale 的取舍小节 |
| sequence-diagram | 输出流程表格或文字步骤列表 |
| code-walkthrough | 输出精简伪代码 + 关键函数签名 + 分支说明 |
| sources | 汇总各章节 Source 链接和 Section sources，按文件去重排列 |
| architecture-diagram | 输出层次文字列表 |
| class-diagram | 输出接口表格 |
| state-diagram | 输出状态转换文字表格 |
| usage-patterns | 合并到 code-example |
| 其他表格组件 | 使用静态分析结果填充 |

---

## 组件选择流程

> **重要**：在生成任何文档之前，必须先执行组件选择流程。
>
> **检测规则**：CodePurpose 检测信号和条件组件触发规则详见 [`codepurpose-detection.md`](codepurpose-detection.md)。
>
> **组件定义**：各组件的完整定义见 [`components-registry.yaml`](components-registry.yaml)。

1. **识别 CodePurpose**：根据文件路径和内容特征，参考 [`codepurpose-detection.md`](codepurpose-detection.md) 的检测信号表
2. **选择默认组件集**：根据 CodePurpose 选择必需组件，参考上方映射表
3. **添加条件组件**：根据模块特征（复杂度、依赖数、类定义等）添加条件组件
4. **AI 补充推荐**：对于复杂模块，可让 AI 分析后推荐额外组件
5. **排序输出**：模块文档优先按"自上而下理解 → 中层运行模型 → 深入源码 → 操作与导航"排序，而不是按源码文件顺序排序

---

## 时序图生成规范

### 触发条件矩阵

| 模块特征 | 必需 | 推荐 | 跳过 |
|---------|:----:|:----:|:----:|
| API 端点/路由处理 | ✅ | | |
| 中间件链 | ✅ | | |
| Agent 决策流程 | ✅ | | |
| 多 Agent 协作 | ✅ | | |
| 前后端交互 | ✅ | | |
| 数据库操作 | | ✅ | |
| 状态管理 | | ✅ | |
| 简单工具函数 | | | ✅ |

### 格式选择规则

| 条件 | 使用格式 |
|------|---------|
| 参与者 <= 6 | Mermaid sequenceDiagram |
| 参与者 > 6 或流水线 | 流程表格 |
| 简单线性流程 | 文字步骤列表 |

### 流程表格模板

根据模块的 archetype 和 CodePurpose 选择合适的流程表格模板：

**HTTP 请求处理（web-service / fullstack-framework / generic 的 Api 模块）**

| 阶段 | 执行者 | 输入 | 输出 | 说明 |
|------|--------|------|------|------|
| 1 | Middleware | Request | - | 认证校验 |
| 2 | Handler | Request | DTO | 参数解析 |
| 3 | Service | DTO | Entity | 业务处理 |
| 4 | Repository | Entity | Entity | 持久化 |
| 5 | Handler | Entity | Response | 响应构建 |

**Agent 决策流（agent-project 的 Agent 模块）**

| 阶段 | 执行者 | 输入 | 输出 | 说明 |
|------|--------|------|------|------|
| 1 | Agent | 用户输入 | 意图识别 | LLM 解析用户意图 |
| 2 | Planner | 意图 | 任务列表 | 拆分为可执行步骤 |
| 3 | Tool | 任务 + 上下文 | 工具结果 | 调用外部工具/API |
| 4 | Agent | 工具结果 | 最终响应 | 综合结果生成回复 |

**数据处理流水线（ml-project / data-pipeline）**

| 阶段 | 执行者 | 输入 | 输出 | 说明 |
|------|--------|------|------|------|
| 1 | Loader | 原始数据 | DataBatch | 数据加载和分批 |
| 2 | Preprocessor | DataBatch | Features | 清洗、标准化、增强 |
| 3 | Model | Features | Predictions | 推理/训练 |
| 4 | Postprocessor | Predictions | Result | 后处理和格式化 |

**前端渲染流（spa-frontend 的 Page/Widget 模块）**

| 阶段 | 执行者 | 输入 | 输出 | 说明 |
|------|--------|------|------|------|
| 1 | Router | URL | PageProps | 路由匹配和参数解析 |
| 2 | Store | PageProps | State | 获取全局状态 |
| 3 | Component | State + Props | VNode | 渲染组件树 |
| 4 | Effect | State | SideEffect | 副作用处理（API 调用等） |

**CLI 命令执行（cli-tool 的 Command/Entry 模块）**

| 阶段 | 执行者 | 输入 | 输出 | 说明 |
|------|--------|------|------|------|
| 1 | Parser | CLI args | ParsedOpts | 参数解析和验证 |
| 2 | Config | ParsedOpts | Config | 加载配置文件和环境变量 |
| 3 | Command | Config + Args | Result | 执行核心命令逻辑 |
| 4 | Formatter | Result | Output | 格式化输出到终端 |

> 选择原则：优先匹配当前 archetype 的专用模板；未匹配时使用 generic 的 HTTP 请求处理模板或根据模块特征自行设计。

---

## 自上而下理解规范

### 组件分工

| 组件 | 回答的问题 | 适合放在 |
|------|------------|----------|
| architecture-fit | 这个模块在系统哪里，边界是什么 | 概述之后 |
| design-rationale | 为什么这样设计，而不是其他方案 | 核心逻辑之前 |
| design-patterns | 代码里用了什么模式，这个模式解决了什么问题 | 设计思路之后 |
| performance-tradeoffs | 性能上牺牲了什么，换来了什么 | 核心逻辑之后或之前 |
| tradeoff-analysis | 多个维度的综合权衡和何时重看 | 风险/扩展点附近 |

### 写作规则

- 先讲目标和约束，再讲实现；不要一开始就贴代码。
- 明确区分"源码事实"和"设计推断"。推断必须说明依据来自文件名、调用关系、注释、接口形状或依赖方向。
- 设计模式只能在有代码证据时命名；没有证据时不要套用 Factory/Strategy 等标签。
- 性能权衡要讲收益和代价，不只写"性能更好"。
- 每个自上而下组件都应回指至少一个源码证据或结构化缓存字段。

### 推荐顺序

```text
Relevant source files → 概述 → 架构定位 → 设计思路 → 设计模式 → 内部结构 → 执行流程 → 数据流 → 副作用/不变量 → 核心逻辑 → 性能权衡 → 风险与扩展点 → Sources → 相关文档
```

---

## 中层运行模型规范

### 组件分工

| 组件 | 回答的问题 | 常见证据 |
|------|------------|----------|
| internal-structure | 模块内部哪些部分协作，各自负责什么 | 文件结构、类/函数定义、公开接口 |
| execution-flow | 主路径从哪里开始，经过哪些阶段，到哪里结束 | entry_points、call_graph、handler/command/job |
| data-flow | 数据如何输入、校验、转换、存储或输出 | DTO/schema/model/state/event、读写调用 |
| side-effects | 模块会改变哪些外部状态 | DB/file/network/cache/log/event/env |
| invariants | 哪些约束必须一直成立 | validation、error paths、risk_points、state variables |

### 写作规则

- 中层组件不贴长代码，主要用流程表、职责表、数据表和小图解释运行模型。
- 每个中层组件都要承接上层设计，并指向后续核心逻辑中的源码片段。
- `execution-flow` 讲正常主路径，异常路径可简写；错误细节交给 `error-table`。
- `data-flow` 要区分输入数据、内部中间态、持久化数据和输出数据。
- `side-effects` 必须说明触发点和影响范围；如果没有副作用，也要明确写出判断依据。
- `invariants` 要写成可验证约束，不写空泛原则。

---

## 核心逻辑规范

### 触发条件

| 条件 | 必须 | 推荐 | 跳过 |
|------|:----:|:----:|:----:|
| 函数复杂度 >= 50 | ✅ | | |
| CodePurpose in [Agent, Service, Api, Command] | ✅ | | |
| 设计模式实现 | ✅ | | |
| 核心算法 | ✅ | | |
| 入口文件启动流程 | | ✅ | |
| 模块主路径或关键扩展点 | | ✅ | |
| 简单工具函数（<10 行） | | | ✅ |
| 纯数据结构定义 | | | ✅ |

### 格式选择

| 场景 | 格式 |
|------|------|
| 主路径复杂但可抽象 | 先给精简版核心源码或伪代码，再给关键说明 |
| 代码可划分为 2-5 个逻辑块 | 带注释源码片段 + 逐段讲解表格 |
| 代码逻辑连贯，难以分块 | 带注释代码 + 关键变量/分支/调用说明 |
| 重构/优化场景 | 对比讲解 |

### 抽象与注释规则

- 每个模块优先选择 1-3 个核心片段，不复制整文件；单段建议 20-80 行，可按主路径拆分。
- 片段必须代表主执行路径、关键算法、状态转换、外部接口适配或扩展点。
- 每个核心逻辑章节先给一段"精简版核心源码"：可用伪代码或裁剪代码概括主路径，帮助读者先建立模型。
- 精简版之后给"带注释关键源码"：保留真实源码的关键结构，添加中文注释解释关键变量、分支、调用和错误处理。
- 每段真实源码片段前必须写源码范围：`**Source:** [path](file:///path#Lx-Ly) \`Lx-Ly\``。
- 代码块内容必须对应 Source 链接的行范围，不允许只贴代码不标注来源。
- 允许为讲解添加中文注释，但不得改变源码语义；省略非关键代码时用 `// ...` 或 `# ...` 明确标注。
- 代码块后必须包含逐段讲解表：| 片段 | 做什么 | 为什么这样做 | 关键变量/调用 | 风险 |
- 对轻量模块没有足够源码可讲时，输出"实现要点"列表，但仍应给出最小函数签名或伪代码。

---
