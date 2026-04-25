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
7. [核心代码讲解规范](#核心代码讲解规范)

---

## 组件优先级总览

| 优先级 | 组件 |
|:------:|------|
| **P0**（必需） | overview（Test 除外）, api-table（有公开导出时）, nav-links |
| **P1**（高） | sequence-diagram, code-walkthrough, architecture-diagram |
| **P2**（中） | class-diagram, state-diagram, dependency-diagram, er-diagram, decision-table, code-example |
| **P3**（低） | error-table, file-structure, usage-patterns |

---

## CodePurpose 组件映射

### 映射表

| CodePurpose | 默认组件集 | sequence-diagram | code-walkthrough |
|-------------|-----------|:----------------:|:----------------:|
| **Entry** | overview → architecture-diagram → sequence-diagram → nav-links | ✅ 必需 | 可选 |
| **Agent** | overview → sequence-diagram → code-walkthrough → state-diagram → nav-links | ✅ 必需 | ✅ 必需 |
| **Page** | overview → architecture-diagram → api-table → code-example → nav-links | 可选 | 可选 |
| **Widget** | overview → api-table → code-example → nav-links | - | 可选 |
| **Service** | overview → api-table → sequence-diagram → code-walkthrough → nav-links | ✅ 必需 | ✅ 必需 |
| **Api** | overview → api-table → sequence-diagram → code-walkthrough → error-table → nav-links | ✅ 必需 | ✅ 必需 |
| **Dao** | overview → api-table → nav-links | 可选 | 可选 |
| **Model** | overview → class-diagram → api-table → nav-links | - | - |
| **Config** | overview → api-table → nav-links | - | - |
| **Database** | overview → erDiagram → nav-links | 可选 | 可选 |
| **Util** | overview → api-table → code-example → nav-links | - | 可选 |
| **Command** | overview → architecture-diagram → api-table → code-example → nav-links | 可选 | 可选 |
| **Other** | overview → api-table → nav-links | AI 推荐 | AI 推荐 |

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

可选组件：[usage-patterns, error-table, file-structure, decision-table]

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
| sequence-diagram | 输出流程表格或文字步骤列表 |
| code-walkthrough | 仅输出代码块 + 函数签名 |
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

## 核心代码讲解规范

### 触发条件

| 条件 | 必须 | 推荐 | 跳过 |
|------|:----:|:----:|:----:|
| 函数复杂度 >= 50 | ✅ | | |
| CodePurpose in [Agent, Service, Api, Command] | ✅ | | |
| 设计模式实现 | ✅ | | |
| 核心算法 | ✅ | | |
| 入口文件启动流程 | | ✅ | |
| 简单工具函数（<10 行） | | | ✅ |
| 纯数据结构定义 | | | ✅ |

### 格式选择

| 场景 | 格式 |
|------|------|
| 代码可划分为 3-6 个逻辑块 | 格式A：代码块 + 逐块讲解表格 |
| 代码逻辑连贯，难以分块 | 格式B：带注释代码 + 关键点说明 |
| 重构/优化场景 | 格式C：对比讲解 |

---
