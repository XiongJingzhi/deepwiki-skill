# 模块文档组件规范（扩展）

> 本文件包含 P1、P2、P3 和复合组件的完整定义。
> P0 必需组件见 [`module-page-components.md`](module-page-components.md)。

---

## P1 — 高优先级组件

---

### architecture-fit — 架构定位

**触发**：`CodePurpose in [Entry, Agent, Service, Api, Command, Database]` 或模块被 2+ 其他模块依赖，或处于跨层调用链上
**格式**：架构层级说明 + 边界表（`| 维度 | 本模块负责 | 不负责 | 证据 |`）+ 可选 Mermaid flowchart（高亮当前模块）
**所需上下文**：`architecture-skeleton.json`、`module_summary`、`dependency_hints`、`import_relations`
**降级**：用"所在层 / 负责什么 / 不负责什么"三列表格替代图
**源码追溯**：不要求（架构层描述为结构性内容）

**生成规范**：
- 说明模块所在层级、上游输入、下游输出和职责边界
- 明确写出"不负责什么"，避免读者误解模块边界
- 标题示例："在微服务架构中的定位"、"渲染层的位置"

---

### design-patterns — 设计模式

**触发**：文件包含设计模式实现（工厂、策略、适配器、观察者、仓储、中间件链、插件注册、状态机等），或 `patterns` 非空，或 `CodePurpose in [Agent, Service, Dao, Command]`
**格式**：每个模式依次说明：模式名称 → 代码证据 → 解决的问题 → 带来的代价
**所需上下文**：`patterns`、class/function definitions、`call_graph`、`key_insights`
**降级**：若没有明确模式，输出"未发现强设计模式，仅采用直接实现"并跳过详细展开
**源码追溯**：不要求单独章节，但每个模式必须有代码证据（源码片段或链接）

**生成规范**：
- 设计模式只能在有代码证据时命名；没有证据时不要套用标签
- 没有明确模式时跳过，不要为了完整性硬凑
- 标题示例："观察者模式在事件分发中的应用"

---

### performance-tradeoffs — 性能权衡

**触发**：模块复杂度 >= 50，或存在循环/批处理/缓存/网络/文件/数据库 IO，或 `CodePurpose in [Service, Api, Dao, Database, Agent, Command]`
**格式**：
- 性能关注点表：`| 关注点 | 当前实现 | 收益 | 代价 | 证据 |`
- 明确当前不是性能热点时也要说明判断依据

**所需上下文**：`complexity_score`、`call_graph`、`dependency_hints`、`core_files`、核心源码片段
**降级**：若无明显性能敏感路径，输出"当前不是性能热点"和判断依据
**源码追溯**：不要求

**生成规范**：
- 性能权衡要讲收益和代价，不只写"性能更好"
- 标题示例："查询性能优化策略"、"缓存与一致性的权衡"

---

### sequence-diagram — 时序图

**触发**：`CodePurpose in [Api, Service, Agent, Entry, Command]`，或模块有跨组件数据流，或函数调用链深度 >= 3
**格式**：
- 变体 A：Mermaid `sequenceDiagram`（参与者 <= 6）
- 变体 B：流程表格（参与者 > 6 或流水线）
- 变体 C：文字步骤列表（简单线性流程）

**图前文字描述（必须）**：图表前必须有一段 2-4 句的文字描述，概括交互的核心流程（参与者、关键步骤、最终结果）。

**图后分析（必须）**：图表后必须有一段 2-4 句的文字分析，解释图中关键交互的设计意图、异常处理策略或值得注意的实现细节。

**所需上下文**：接口签名、依赖关系、关键函数调用链
**降级**：若参与者 > 8，拆分为多张子图；若 LLM 生成失败，使用流程表格替代
**源码追溯**：不要求

**生成规范**：
- 展示完整的处理链，区分正常路径和异常路径
- 标题示例："HTTP 请求处理时序"、"Agent 决策与工具调用链"、"前端数据加载交互"

**格式选择规则**

| 条件 | 使用格式 |
|------|---------|
| 参与者 <= 6 | Mermaid sequenceDiagram |
| 参与者 > 6 或流水线 | 流程表格 |
| 简单线性流程 | 文字步骤列表 |

**流程表格模板**（根据 archetype 和 CodePurpose 选择）

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

### architecture-diagram — 架构图

**触发**：模块包含 2+ 子模块，或 `CodePurpose in [Entry, Page, Command]`，或文件结构深度 >= 2
**格式**：Mermaid `flowchart TB`

**图前文字描述（必须）**：图表前必须有一段 2-4 句的文字描述，解释架构的核心分层、各层职责和数据流向。

**图后分析（必须）**：图表后必须有一段 2-4 句的文字分析，解读各层级之间的关系、关键设计决策或架构中值得注意的模式。

**所需上下文**：模块列表和依赖关系、文件结构
**降级**：若模块简单，用文字列表描述层次
**源码追溯**：不要求

**生成规范**：
- 展示系统/模块的层次结构
- 高亮当前模块或当前层级
- 标题示例："订单系统的三层架构"、"渲染管线分层"

---

### internal-structure — 内部结构

**触发**：模块包含 2+ 源文件，或 3+ 公开接口，或多个 class/function 协作，或 `CodePurpose in [Agent, Service, Api, Command, Database, Page]`
**格式**：职责分工表（`| 内部单元 | 职责 | 协作者 | 证据 |`）+ 可选内部结构图（Mermaid flowchart）
**所需上下文**：`file-structure`、`public_interfaces`、`call_graph`、`module_summary`
**降级**：单文件模块用"内部结构较简单"加职责列表替代
**源码追溯**：**必需** — 内部结构描述中涉及的类/函数/文件必须在章节末尾引用对应源码

**生成规范**：
- 不贴长代码，主要用职责表和结构图解释内部分工
- 承接上层架构定位，并指向后续核心逻辑中的源码片段
- 说明子组件、文件、类、函数之间的职责分工
- 单文件简单模块可降级为"实现要点"列表
- 标题示例："模块内部协作机制"、"子服务分工"

---

### execution-flow — 执行流程

**触发**：`CodePurpose in [Entry, Agent, Service, Api, Command]`，或存在入口函数/handler/route/command/job/worker，或 `call_graph` 深度 >= 2
**格式**：
- 主流程表：`| 阶段 | 入口/执行者 | 输入 | 输出 | 说明 |`
- 可选 Mermaid flowchart 或 sequenceDiagram
- 正常路径和异常/降级路径分开说明

**所需上下文**：`entry_points`、`call_graph`、`public_interfaces`、`dependency_hints`
**降级**：简单线性模块用 3–5 步文字列表
**源码追溯**：**必需** — 执行流程中涉及的入口函数、调度逻辑必须在章节末尾引用对应源码

**生成规范**：
- 不贴长代码，主要用流程表和小图解释执行链路
- 承接上层设计，并指向后续核心逻辑中的源码片段
- 不进入逐行代码，源码细节留给 `code-walkthrough`
- 区分正常主路径与异常路径，错误细节可交给 `error-table`
- 标题示例："请求处理生命周期"、"任务调度流水线"

---

### data-flow — 数据流

**触发**：`CodePurpose in [Api, Service, Dao, Database, Agent, Page]`，或模块处理 DTO/schema/payload/state/event/record，或存在数据库/文件/网络/队列或状态读写
**格式**：
- 数据流表：`| 阶段 | 数据形态 | 转换/校验 | 去向 | 证据 |`
- 区分输入、中间态、持久化数据和输出

**所需上下文**：`public_interfaces`、`key_sequences`、`dependency_hints`、model/schema definitions
**降级**：无明显数据转换时，说明"该模块主要透传或编排数据"
**源码追溯**：**必需** — 数据转换逻辑、校验函数、持久化调用必须在章节末尾引用对应源码

**生成规范**：
- 不贴长代码，主要用数据流表解释数据转换过程
- 承接上层设计，并指向后续核心逻辑中的源码片段
- 区分输入数据、内部中间态、持久化数据和输出数据
- 标题示例："数据从输入到持久化的流转过程"

---

### api-table — 公开接口

**触发**：模块有公开导出（`public_interfaces` 非空或 `exported symbols >= 1`）；纯配置或内部文件可降级
**格式变体**：
- 接口表：`| 接口 | 类型 | 描述 | 源码 |`
- 枚举表：`| 枚举值 | 显示名 | 检测信号 |`
- 方法表：`| 方法 | 用途 | 默认行为 |`
- 配置表：`| 配置项 | 类型 | 默认值 | 描述 |`

**所需上下文**：导出声明、函数签名、参数类型
**降级**：无
**源码追溯**：**必需** — 每个接口条目必须附带源码链接（`file:///路径#L起-L止`）**禁止**链接到整个文件

**生成规范**：
- 标题示例："用户认证 API 参考"、"事件总线公开接口"、"配置管理接口一览"
- 接口总览表列出所有公开导出
- 对每个公开接口说明：签名 + 源码链接、参数表格（`| 参数 | 类型 | 描述 | 默认值 |`）、返回值说明
- **类/组件**（type 为 `class`）必须在总览表之外单独展开描述，内容包括：
  - 类名 + 继承关系（如 `class WikiHandler(BaseHTTPRequestHandler)`）
  - 源码链接
  - 职责概述（一两句话说明该类解决什么问题）
  - 关键方法/属性列表（表格：`| 方法/属性 | 签名 | 说明 |`）
  - 设计要点（线程安全、单例模式、懒加载等关键设计决策）

---

---

## P2 — 中优先级组件

---

### nav-links — 相关文档

**触发**：模块被 2+ 其他模块依赖，或 `CodePurpose in [Entry, Agent, Service, Api, Command]`，或模块复杂度 >= 40
**格式**：Markdown 表格或链接列表
**所需上下文**：相关文档路径
**降级**：跳过不生成
**源码追溯**：不要求（纯导航章节豁免）

**生成规范**：
- 包含架构文档链接、相关深入理解页、参考索引链接
- **链接必须可跳转**：使用有效的 wiki 内部链接格式 `[标题](相对路径.md)`
- **不要使用** code 标签包裹路径、纯文本链接
- 链接格式规范见 [`quality-standards.md`](../rules/quality-standards.md) "相关文档链接"章节

---

### tradeoff-analysis — 综合取舍

**触发**：`risk_points` 非空，或 `extension_points` 非空，或模块复杂度 >= 40，或 `CodePurpose in [Agent, Service, Api, Database, Command]`
**格式**：取舍表：`| 维度 | 当前选择 | 收益 | 代价 | 何时重看 |`（至少覆盖可维护性、扩展性、复杂度、性能中的两个维度）
**所需上下文**：`risk_points`、`extension_points`、`key_insights`、`dependency_hints`
**降级**：合并到 `design-rationale` 的"替代方案与取舍"小节
**源码追溯**：不要求

**生成规范**：
- 标题示例："架构扩展性 vs 实现复杂度的权衡"

---

### side-effects — 副作用

**触发**：存在数据库写入/文件写入/网络请求/缓存更新/事件发布/日志/进程环境修改，或 `CodePurpose in [Api, Service, Dao, Database, Agent, Command]`
**格式**：副作用表：`| 副作用 | 触发点 | 影响范围 | 恢复/回滚方式 | 证据 |`
**所需上下文**：`call_graph`、`dependency_hints`、`key_insights`、核心源码片段
**降级**：若无外部副作用，明确标注"未发现外部副作用"，并说明依据
**源码追溯**：不要求

**生成规范**：
- 必须说明触发点和影响范围；如果没有副作用，也要明确写出判断依据
- 标题示例："外部状态变更与回滚策略"

---

### invariants — 不变量

**触发**：`risk_points` 非空，或模块包含状态机/权限/校验/事务/缓存一致性/配置约束，或 `CodePurpose in [Agent, Service, Api, Dao, Database, Config]`
**格式**：约束表：`| 约束 | 类型 | 由谁维护 | 破坏后果 | 证据 |`
**所需上下文**：`risk_points`、`public_interfaces`、state variables、validation/error paths
**降级**：若未发现强不变量，输出关键输入约束和边界假设
**源码追溯**：不要求

**生成规范**：
- 只写可验证约束，不写泛泛原则
- 标题示例："数据一致性保障"、"权限校验约束"

---

### class-diagram — 类图

**触发**：模块导出 class/struct/interface，或存在继承关系（extends/implements）
**格式**：Mermaid `classDiagram`

**图前文字描述（必须）**：图表前必须有一段 2-4 句的文字描述，概述类的核心关系（继承、组合、依赖）和设计意图。

**图后分析（必须）**：图表后必须有一段 2-4 句的文字分析，解读类关系中的设计考量、关键抽象或值得注意的实现细节。

**所需上下文**：类定义和属性、方法签名、继承关系
**降级**：若无继承关系，用接口表格代替
**源码追溯**：**必需** — 展示的每个类/接口/结构体必须引用对应源码定义

**生成规范**：
- 展示核心类/接口的属性、方法、关系
- 标题示例："核心领域模型"、"实体关系与继承结构"

---

### state-diagram — 状态图

**触发**：`CodePurpose == Agent`，或显式状态管理（useState/useReducer/状态模式），或生命周期方法（onMount/onDestroy 等）
**格式**：Mermaid `stateDiagram-v2`

**图前文字描述（必须）**：图表前必须有一段 2-4 句的文字描述，概述状态转换的核心路径和触发条件。

**图后分析（必须）**：图表后必须有一段 2-4 句的文字分析，解读状态机的关键转换条件、异常状态处理或状态设计中的注意事项。

**所需上下文**：状态变量定义、状态转换触发条件
**降级**：用文字列表描述状态和转换条件
**源码追溯**：不要求

**生成规范**：
- 标题示例："订单状态流转"、"连接池生命周期"

---

### dependency-diagram — 依赖关系

**触发**：模块有内部依赖或被其他模块依赖，或依赖数 >= 2
**格式**：Mermaid `flowchart LR` + 依赖说明表

**图前文字描述（必须）**：图表前必须有一段 2-4 句的文字描述，说明模块间依赖的主要方向和关键依赖关系。

**图后分析（必须）**：图表后必须有一段 2-4 句的文字分析，解读依赖拓扑中的关键路径、循环依赖风险或依赖设计的合理性。

**所需上下文**：import 语句、模块依赖关系
**降级**：用依赖表格代替
**源码追溯**：不要求（聚合数据章节豁免）

**生成规范**：
- 展示模块间的依赖方向
- 标题示例："模块依赖拓扑"、"跨包依赖关系图"

---

### er-diagram — ER 图

**触发**：`CodePurpose == Database`，或模块定义了 ORM 模型/SQL 表/Prisma schema
**格式**：Mermaid `erDiagram`

**图前文字描述（必须）**：图表前必须有一段 2-4 句的文字描述，概述核心实体及其关系类型。

**图后分析（必须）**：图表后必须有一段 2-4 句的文字分析，解读实体关系的设计考量、索引策略或数据模型的扩展性。

**所需上下文**：实体/模型定义、外键关系、字段/列定义
**降级**：实体超过 8 个时仅展示核心实体；无外键时使用简单表结构列表；复杂关系用 Markdown 表格替代
**源码追溯**：不要求

**生成规范**：
- 展示实体关系、表结构和外键约束
- 标题示例："用户与订单实体关系"、"配置数据模型"

---

### decision-table — 决策表

**触发**：存在多层处理策略，或有条件分支逻辑，或需要对比不同方案
**格式**：Markdown 表格
**所需上下文**：决策条件、各分支结果
**降级**：用列表替代
**源码追溯**：不要求

**生成规范**：
- 展示策略选择、条件分支、决策逻辑
- 标题示例："认证策略选择矩阵"、"缓存淘汰决策逻辑"

---

### code-example — 代码示例

**触发**：模块复杂度 >= 低，或公开接口 >= 1
**格式**：代码块 + 场景说明
**所需上下文**：模块公开接口、典型使用场景
**降级**：若 LLM 无法生成，仅输出基本调用示例
**源码追溯**：不要求

**生成规范**：
- 优先使用项目主要语言；多语言项目可选择模块自身语言
- SDK/Library 模块应包含调用方语言示例
- 标题示例："快速上手示例"、"典型使用场景"

---

## P3 — 低优先级组件

---

### error-table — 错误处理

**触发**：模块定义自定义错误类型，或函数签名包含 throws/Result/Error，或 `CodePurpose in [Api, Service, Agent, Dao]`
**格式**：Markdown 表格（错误类型 / 触发条件 / 处理方式 / 来源）
**所需上下文**：错误类型定义、异常抛出点
**降级**：若无显式错误定义，跳过
**源码追溯**：**必需** — 每个错误类型和处理方式必须引用对应源码中的错误定义和处理逻辑

**生成规范**：
- 标题示例："异常处理与降级策略"

---

### file-structure — 文件结构

**触发**：模块包含 2+ 源文件
**格式**：目录树 + 职责表
**所需上下文**：文件列表、每个文件的导出内容
**降级**：单文件模块用一句话说明
**源码追溯**：不要求

**生成规范**：
- 标题示例："认证服务目录组织"、"数据层文件结构"

---

### usage-patterns — 使用模式

**触发**：模块复杂度 >= 中等，或公开接口 >= 3，或 `CodePurpose in [SDK, Util, Service]`
**格式**：场景描述 + 代码 + 预期结果
**所需上下文**：模块公开接口、业务场景
**降级**：用多个 `code-example` 代替
**源码追溯**：不要求

**生成规范**：
- 展示典型使用场景和模式
- 标题示例："文件上传典型用法"、"事件总线订阅模式"

---

## 复合组件

> 复合组件将多个基础组件组合为一个内聚单元，提供比单独使用更强的表达能力。当子组件同时触发时，优先使用复合组件而非分散输出。

### architecture-overview — 架构概览

**组合**：`overview` + `architecture-diagram`
**触发**：模块包含 2+ 子模块，或 `CodePurpose in [Entry, Page, Command]`，或文件结构深度 >= 2
**格式**：2–3 段模块概述 + Mermaid flowchart（高亮当前模块）
**排版**：描述在前，图在后；图表前必须有 2-4 句文字概述架构核心分层和数据流向（同 architecture-diagram 图前描述要求）
**降级**：模块极简单时仅保留 overview 文字描述

---

### core-flow-walkthrough — 核心流程图解

**组合**：`code-walkthrough` + `sequence-diagram`
**触发**：`CodePurpose in [Api, Service, Agent, Entry, Command]`，或模块有跨组件交互且函数调用链深度 >= 3
**格式**：带注释关键源码片段 + 逐段讲解表格 + Mermaid sequenceDiagram（或流程表格）
**排版**：先给源码讲解（code-walkthrough），再配时序图展示完整调用链；时序图参与者与源码中的函数/类对应
**降级**：调用链简单时仅保留 code-walkthrough；参与者 > 8 时用流程表格替代时序图

---

### structure-class-diagram — 内部结构图解

**组合**：`internal-structure` + `class-diagram`
**触发**：模块导出 class/struct/interface，且存在继承或组合关系
**格式**：职责分工表 + Mermaid classDiagram（或接口表格）
**排版**：先给职责分工表（internal-structure），再配类图展示继承/组合/依赖关系
**降级**：无继承关系时用接口表格替代类图

---

### runtime-model — 运行模型

**组合**：`execution-flow` + `data-flow`
**触发**：`CodePurpose in [Api, Service, Agent, Entry, Command]`，且模块同时有执行阶段和数据转换
**格式**：合并表 `| 阶段 | 执行者 | 输入数据 | 输出数据 | 核心操作 | 说明 |` + 可选 Mermaid flowchart
**排版**：用一张表同时展示"谁在做什么"和"数据如何流转"，避免两表分开展示造成的上下文割裂
**降级**：数据转换不明显时仅保留 execution-flow

---

### api-with-examples — 接口与示例

**组合**：`api-table` + `code-example`
**触发**：模块有公开导出且复杂度 >= 低
**格式**：接口签名表 + 紧跟每个接口的调用示例
**排版**：每个接口条目后附一个精简代码块（3-10 行），而非单独的"使用模式"章节
**降级**：纯配置模块仅有 api-table

---

### design-decisions — 设计决策

**组合**：`design-rationale` + `tradeoff-analysis`
**触发**：模块复杂度 >= 40，或 `CodePurpose in [Agent, Service, Api, Database, Command]`，或 `risk_points` 非空
**格式**：设计目标 → 约束条件 → 当前方案 → 替代方案与取舍表（合并 design-rationale 的"替代方案"和 tradeoff-analysis 的"维度取舍"为一张表）
**排版**：统一为一个"设计决策"章节，目标/约束/方案为叙述，取舍为表格，避免拆成两个相近章节
**降级**：设计意图无法从源码确认时标注"推断"

---

### state-constraints — 状态与约束

**组合**：`side-effects` + `invariants`
**触发**：`CodePurpose == Agent`，或模块包含状态机/事务/缓存一致性/权限校验
**格式**：副作用表 + 约束表（合并在同一章节内）
**排版**：先列副作用（外部状态变更），再列不变量（必须维护的约束），两者自然形成"变更 + 保护"的对照
**降级**：无外部副作用时仅保留 invariants

---

### module-topology — 模块拓扑

**组合**：`file-structure` + `dependency-diagram`
**触发**：模块包含 3+ 源文件且存在内部依赖关系
**格式**：目录树 + Mermaid flowchart LR（文件间依赖方向图）
**排版**：先展示目录结构，再配依赖图说明文件间的调用方向
**降级**：文件间无依赖时仅保留 file-structure

---

### data-model — 数据模型

**组合**：`data-flow` + `er-diagram`
**触发**：`CodePurpose in [Dao, Database]`，或模块定义 ORM 模型/SQL 表/Prisma schema
**格式**：数据流转表 + Mermaid erDiagram（或表结构列表）
**排版**：先展示数据如何在各阶段流转（data-flow），再展示底层实体关系（er-diagram）
**降级**：实体超过 8 个时仅展示核心实体；无外键时用表结构列表替代 er-diagram
