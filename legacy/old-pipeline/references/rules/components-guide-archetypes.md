# Archetype 覆写规则

> 本文件定义不同项目类型（archetype）对基础组件映射的增删调整。组件选择策略见 [`components-guide.md`](components-guide.md)。
>
> **优先级**：archetype_overrides > CodePurpose 基础映射 > 条件触发。
> - `add` 规则：若 `trigger` 条件满足（`always` 或 CodePurpose 匹配），则添加对应组件。
> - `remove` 规则：若 `trigger` 条件满足，则移除对应组件（不会覆盖 P0 必需组件）。
>   注意：P0 组件的触发条件豁免（如 Test 模块的 overview、无导出模块的 api-table）不受保护，archetype 覆写可基于 trigger 条件跳过这些 P0 组件。

---

### agent-project

**添加**

| 组件 | trigger | 原因 |
|------|---------|------|
| architecture-fit | always | Agent 项目需要先解释调度中心、工具、记忆和执行链路的架构位置 |
| design-rationale | CodePurpose in [Agent, Service, Entry] | Agent 编排逻辑的设计意图比单纯接口更重要 |
| design-patterns | CodePurpose in [Agent, Service] | Agent 项目常见插件注册、策略选择和状态机模式 |
| performance-tradeoffs | CodePurpose in [Agent, Service] | Agent 调度常涉及 token、工具调用和并发权衡 |
| internal-structure | CodePurpose in [Agent, Service] | Agent 模块内部通常有 planner/tool/memory/executor 分工 |
| execution-flow | CodePurpose in [Agent, Service, Entry] | Agent 需要说明从输入到工具调用再到响应的主流程 |
| data-flow | CodePurpose in [Agent, Service] | Agent 需要解释消息、上下文、工具结果和状态如何流动 |
| side-effects | CodePurpose in [Agent, Service] | Agent 常调用工具、写记忆或产生外部副作用 |
| invariants | CodePurpose in [Agent, Service] | Agent 状态、工具调用和记忆一致性需要约束说明 |
| state-diagram | always | Agent 项目状态流转是核心关注点 |
| decision-table | CodePurpose in [Service, Agent] | Agent 决策逻辑适合决策表展示 |

**移除**

| 组件 | trigger | 原因 |
|------|---------|------|
| sequence-diagram | CodePurpose not in [Api, Entry, Service] | Agent 非 API 模块通常无请求-响应时序 |

---

### ml-project

**添加**

| 组件 | trigger | 原因 |
|------|---------|------|
| performance-tradeoffs | CodePurpose in [Service, Database] | ML 项目的数据加载、训练和推理通常性能敏感 |
| design-rationale | CodePurpose in [Service, Config] | 模型、数据和超参数选择需要设计解释 |
| data-flow | CodePurpose in [Service, Database] | ML 模块核心是数据从加载到特征、模型和结果的流动 |
| execution-flow | CodePurpose in [Entry, Service] | 训练/推理流程需要中层执行链路 |
| invariants | CodePurpose in [Service, Config] | 数据 shape、特征和超参数存在关键约束 |
| decision-table | CodePurpose in [Service, Config] | ML 超参数/配置策略适合决策表 |

**移除**

| 组件 | trigger | 原因 |
|------|---------|------|
| sequence-diagram | CodePurpose not in [Api, Entry] | ML 模块通常无请求-响应时序 |

---

### cli-tool

**添加**

| 组件 | trigger | 原因 |
|------|---------|------|
| architecture-fit | CodePurpose in [Entry, Command] | CLI 需要解释命令树、配置加载和输出层边界 |
| design-rationale | CodePurpose in [Entry, Command] | 命令解析和执行分层需要设计说明 |
| execution-flow | CodePurpose in [Entry, Command] | CLI 需要说明参数解析、配置加载、执行和输出链路 |
| side-effects | CodePurpose in [Command] | CLI 命令常写文件、调用网络或修改环境 |
| architecture-diagram | CodePurpose == Entry | CLI 命令树用 flowchart 展示更清晰 |

**移除**

| 组件 | trigger | 原因 |
|------|---------|------|
| state-diagram | CodePurpose not in [Agent] | CLI 工具通常无状态管理 |

---

### sdk-library

**添加**

| 组件 | trigger | 原因 |
|------|---------|------|
| design-rationale | always | SDK 需要解释 API 形状和抽象边界 |
| tradeoff-analysis | CodePurpose in [Api, Service, Util] | SDK API 设计常需要兼顾易用性、兼容性和扩展性 |
| internal-structure | CodePurpose in [Api, Service] | SDK 需要解释 public API、内部 adapter 和 transport 的分工 |
| data-flow | CodePurpose in [Api, Service] | SDK 需要解释调用参数如何变为请求或结果对象 |
| invariants | CodePurpose in [Api, Service, Util] | SDK 需要明确 API 契约和兼容性约束 |
| usage-patterns | always | SDK 使用模式是核心内容 |

**移除**

| 组件 | trigger | 原因 |
|------|---------|------|
| sequence-diagram | CodePurpose not in [Api] | 库函数调用通常不需要时序图 |

---

### monorepo

**添加**

| 组件 | trigger | 原因 |
|------|---------|------|
| architecture-fit | always | Monorepo 文档需要先说明包所在层级和边界 |
| tradeoff-analysis | always | Monorepo 包边界和复用策略本质上是取舍问题 |
| internal-structure | always | Monorepo 需要解释包内结构和跨包协作方式 |
| dependency-diagram | always | Monorepo 包间依赖关系是核心关注点 |

### Mono-repo 子项目文档拆分策略

对于 monorepo 项目的 workspace 包，根据复杂度决定文档粒度：

| 子项目特征 | 文档策略 | 判定标准 |
|-----------|---------|---------|
| 复杂子项目 | 拆分为多个子模块文档 | 文件数 ≥ 10、有独立内部架构、包含 3+ 内部模块 |
| 中等子项目 | 单独一个模块文档 | 有一定复杂度但内部结构简单 |
| 简单子项目 | 合并为单个模块文档 | 工具库、配置包、类型定义包、常量包等 |

拆分时优先按子项目内部的目录结构或功能域划分子模块，每个子模块文档应覆盖一个独立的功能点。

---

### web-service

**添加**

| 组件 | trigger | 原因 |
|------|---------|------|
| architecture-fit | CodePurpose in [Api, Service, Dao, Database] | Web 服务需要解释 Controller/Service/DAO/DB 分层边界 |
| design-rationale | CodePurpose in [Api, Service] | 业务服务和 API 层需要解释设计意图 |
| performance-tradeoffs | CodePurpose in [Api, Service, Dao, Database] | Web 服务常涉及请求延迟、数据库 IO 和缓存权衡 |
| internal-structure | CodePurpose in [Api, Service, Dao, Database] | Web 服务需要解释 handler/service/repository 的内部协作 |
| execution-flow | CodePurpose in [Api, Service] | Web 服务需要说明请求进入后的主处理链 |
| data-flow | CodePurpose in [Api, Service, Dao, Database] | Web 服务需要解释 DTO、实体、响应和持久化之间的数据流 |
| side-effects | CodePurpose in [Api, Service, Dao, Database] | Web 服务常写数据库、缓存、日志或调用外部服务 |
| invariants | CodePurpose in [Api, Service, Dao, Database] | Web 服务常有权限、事务和数据一致性约束 |
| error-table | CodePurpose in [Api, Service] | Web 服务错误处理是核心关注点 |
| decision-table | CodePurpose in [Config] | Web 服务配置策略适合决策表 |

**移除**

| 组件 | trigger | 原因 |
|------|---------|------|
| state-diagram | CodePurpose not in [Agent] | Web 服务通常无复杂状态管理 |

---

### fullstack-framework

**添加**

| 组件 | trigger | 原因 |
|------|---------|------|
| architecture-fit | always | 全栈框架需要解释前端、服务端和数据层边界 |
| design-rationale | CodePurpose in [Page, Api, Service, Entry] | 全栈模块常涉及渲染位置、数据获取和路由设计取舍 |
| execution-flow | CodePurpose in [Page, Api, Service, Entry] | 全栈模块需要说明路由、数据获取、渲染和响应链路 |
| data-flow | CodePurpose in [Page, Api, Service] | 全栈模块需要解释客户端状态、服务端数据和响应之间的流动 |
| side-effects | CodePurpose in [Api, Service] | 服务端模块通常有数据库、缓存或外部 API 副作用 |
| architecture-diagram | CodePurpose == Entry | 全栈框架需要清晰的分层架构图 |
| code-example | CodePurpose in [Page, Widget] | 前端组件需要使用示例 |

**移除**

| 组件 | trigger | 原因 |
|------|---------|------|
| er-diagram | CodePurpose in [Page, Widget] | 前端组件无实体关系 |

---

### spa-frontend

**添加**

| 组件 | trigger | 原因 |
|------|---------|------|
| architecture-fit | CodePurpose in [Page, Widget, Service] | 前端模块需要说明页面、组件和状态层边界 |
| design-rationale | CodePurpose in [Page, Widget, Service] | 前端组件拆分和状态放置需要设计解释 |
| performance-tradeoffs | CodePurpose in [Page, Widget, Service] | 前端渲染、状态订阅和副作用有明显性能权衡 |
| internal-structure | CodePurpose in [Page, Widget, Service] | 前端模块需要解释组件、hooks、store 和 service 的分工 |
| execution-flow | CodePurpose in [Page, Widget, Service] | 前端模块需要说明渲染、事件、副作用和更新链路 |
| data-flow | CodePurpose in [Page, Widget, Service] | 前端模块核心是 props、state、store 和 API 数据流 |
| side-effects | CodePurpose in [Page, Widget, Service] | 前端模块常有 effect、网络请求、路由和存储副作用 |
| invariants | CodePurpose in [Page, Widget, Service] | 前端状态和 props 契约需要明确约束 |
| state-diagram | CodePurpose in [Service, Page, Widget] | 前端状态管理是核心关注点 |
| code-example | CodePurpose in [Widget, Page] | UI 组件需要使用示例 |

**移除**

| 组件 | trigger | 原因 |
|------|---------|------|
| sequence-diagram | CodePurpose not in [Api, Service] | 前端模块通常无请求-响应时序 |

---

### generic

无覆写，直接使用 CodePurpose 基础映射。
