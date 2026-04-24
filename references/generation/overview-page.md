# Overview 生成指南

> **适用工具：** `generate-overview`
> **关联规则：** `../rules/quality-standards.md`、`../rules/components-guide.md`

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

[architecture-diagram 组件：按 archetype 选择图类型和结构，P0 必需]

[分层说明：每层职责一句话，来自第 5 步 RelationshipSummary]

---

## 模块说明

[对每个模块：名称（链接到模块文档）、职责一句话、关键依赖]

---

## 数据流（条件：项目涉及 API 调用或跨组件数据传递）

[sequence-diagram 组件：展示最核心的一条调用链]

---

## 模块依赖图（条件：模块数 ≥ 4）

[dependency-diagram 组件：flowchart LR]

---

## 目录结构（条件：项目目录结构非平凡）

[file-structure 组件]

---

## 文档导航

[nav-links 组件：getting-started.md、doc-map.md、各模块文档入口]
```

---
