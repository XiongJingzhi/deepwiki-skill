# Overview 生成指南

> **适用工具：** `generate-overview`
> **关联规则：** `../rules/quality-standards.md`、`../rules/components-guide.md`

---

## 文档语言

读取项目 `.deepwiki/config.yaml` 中 `generation.language` 的值（`zh` / `en` / `both`），所有文档内容（章节标题、正文、表格、注释说明）必须使用该语言撰写。代码标识符和专有名词保持原文。默认为 `zh`。

---

## 生成指导

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
- 根据项目 archetype 选择对应的架构图模板：

  | archetype | 图类型 | 结构 |
  |-----------|--------|------|
  | web-service, fullstack-framework | `flowchart TB` | 分层架构：UI → API → 业务 → 数据 |
  | agent-project | `flowchart TB` | hub-and-spoke：Agent 中心，tools/modules 放射 |
  | cli-tool | `flowchart LR` | 命令树：入口 → 子命令 → 处理器 |
  | ml-project | `flowchart LR` | pipeline：数据采集 → 预处理 → 训练 → 推理 |
  | sdk-library | `flowchart TB` | feature-based：按功能域组织，无层级 |
  | monorepo | `flowchart TB` | package topology：包间依赖拓扑 |
  | spa-frontend | `flowchart TB` | 页面-组件-状态：pages → components → store |
  | generic | `flowchart TB` | 分层架构（默认） |

- 用 subgraph 分组（若适用）
- 箭头标注数据流方向和关键接口/协议
- 不同模块类型用颜色区分
- 模块数 < 4 或项目极小时，可简化为纯文本架构描述

### 3. 技术栈（api-table 组件）
| 类别 | 技术 | 版本（若有） | 说明 | 文档链接（若有） |

> 仅显示有数据支撑的列。"版本"和"文档链接"仅当 package.json / Cargo.toml / go.mod 等配置文件中有明确值时填写。技术栈少于 5 项时使用简化 3 列格式（类别 | 技术 | 说明）。

### 4. 模块说明
对每个模块：名称 + 链接、职责描述、核心接口列表、依赖关系。

### 5. 数据流（根据 archetype 选择合适的图类型）

| archetype | 推荐图类型 | 说明 |
|-----------|-----------|------|
| web-service, fullstack-framework, generic | `sequenceDiagram` | 请求 → 中间件 → 处理器 → 数据库 → 响应 |
| agent-project | `flowchart LR` | 用户输入 → Agent → 工具调用 → 响应 |
| ml-project, data-pipeline | `flowchart LR` | 数据输入 → 预处理 → 模型 → 输出 |
| cli-tool | `flowchart LR` | 参数解析 → 配置加载 → 命令执行 → 输出 |
| spa-frontend | `sequenceDiagram` | 用户交互 → 组件 → Store → API → 响应 |
| sdk-library | 文字描述 + 代码示例 | 库函数调用流程不适合图表化 |
| monorepo, microservice | `flowchart TB` | 跨服务/跨包调用拓扑 |

> 项目涉及 API 调用或跨组件数据传递时生成。模块数 < 4 或数据流简单时可省略。

### 6. 模块依赖图（根据 archetype 选择合适的展示方式）

| archetype | 推荐图类型 | 说明 |
|-----------|-----------|------|
| monorepo | `flowchart TB`（按 workspace 分组） | 包间依赖拓扑是核心 |
| microservice | `flowchart LR`（按服务分组） | 服务间通信关系 |
| web-service, fullstack-framework | `flowchart LR`（按层分组） | 分层依赖方向 |
| agent-project | `flowchart LR`（按 Agent/Tool 分组） | Agent-Tool 调用拓扑 |
| 其他 | `flowchart LR` | 通用依赖方向图 |

> 模块数 < 4 时可省略此节，依赖信息已在"模块说明"节体现。

### 7. 目录结构（file-structure 组件）
带注释的目录树 + 职责说明。

### 8. 相关文档（nav-links 组件）
各模块文档链接表格、外部依赖文档。

## Mermaid 规范

- 节点 ID 只用字母数字下划线（中文名必须转为拼音或英文 ID）
- 标签用双引号包裹中文：`A["中文标签"]`
- **引号嵌套规则**：外层使用双引号 `"..."`，内部如需引用文本则使用单引号 `'...'`。例：`A["fn('arg1', 'arg2')"]`。禁止在双引号标签内嵌套双引号。
- 使用 style 定义不同模块类型的颜色
- 禁止在节点 ID 或 subgraph ID 中直接使用中文字符

## 源码追溯要求

每个章节末尾必须包含源码引用。
```

---

---

## 页面骨架

## 概览文档骨架

> 对应输出文件 `overview.md`。以架构为主线，融入项目定位和文档导航。

```markdown
# {PROJECT_NAME}

[徽章：技术栈、版本、语言等]

> {一句话定位}

---

## 项目概述

[overview 组件：项目解决的核心问题、适用场景、关键设计理念]

---

## 技术栈

[api-table 组件：语言/框架/工具 三列表格]

---

<!-- 架构图类型根据 archetype 选择，见上方模板表 -->
## 系统架构

[架构概述文字（2-4 句，描述架构核心分层和数据流）]

[architecture-diagram 组件：按 archetype 选择图类型和结构，P0 必需]

[分层说明：每层职责一句话，来自 `architecture-skeleton.json`、`code-structure.json` 或依赖综合摘要]

---

## 模块说明

[对每个模块：名称（链接到模块文档）、职责一句话、关键依赖]

---

## 数据流（条件：项目涉及数据传递且模块数 ≥ 4，图类型按 archetype 选择）

[sequence-diagram 或 flowchart 组件：按上方 archetype 图类型表选择，展示最核心的一条数据流]

---

## 模块依赖图（条件：模块数 ≥ 4，图类型按 archetype 选择）

[dependency-diagram 组件：按上方 archetype 图类型表选择展示方式]

---

## 目录结构（条件：项目目录结构非平凡）

[file-structure 组件]

---

## 文档导航

[nav-links 组件：getting-started.md、doc-map.md、各模块文档入口]
```

---
