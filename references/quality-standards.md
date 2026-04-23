# 文档质量标准

所有生成的文档必须满足以下标准：

- **源码追溯是强制要求**：每个章节末尾必须包含 `[filename](file:///path/to/file.ts#L1-L50)` 引用，方便读者跳转到对应源码。
- **每个模块文档至少包含 1 个 Mermaid 图表**。根据内容选择合适的图表类型：
  - `classDiagram` 用于类继承、接口和类型关系
  - `flowchart` 用于流程、工作流和架构概览
  - `sequenceDiagram` 用于交互、API 调用和组件间数据流
  - `stateDiagram` 用于状态机和生命周期转换
- **代码示例必须使用项目的主要语言**，完整且可运行（包含导入、初始化、调用和输出处理）。
- **文档间必须交叉链接**，方便读者在文档网络中导航。
- **内容应解释 WHY（为什么）和 HOW（如何实现）**，而不仅仅是 WHAT（是什么）。包含设计理由、权衡和上下文。
- 使用层级标题（H2/H3/H4）建立清晰的信息架构。
- 使用表格呈现 API、参数和配置选项，便于快速参考。
- 记录边界情况、警告和常见陷阱。

## 源码链接格式

每个章节末尾必须包含源码引用：

```markdown
**Section sources**
- [filename.ts](file:///path/to/file.ts#L1-L50)
- [another.ts](file:///path/to/another.ts#L20-L80)
```

代码块标题应包含内联源码链接：

```markdown
### `functionName` [源码](file:///path/to/file.ts#L42)
```

## Mermaid 图表选择指南

| 内容类型 | 推荐图表 | 使用场景 |
|---------|---------|---------|
| 类/接口层级 | `classDiagram` | 文档化 OOP 结构、类型关系、继承 |
| 流程/工作流 | `flowchart TB` | 逐步逻辑、请求处理、构建流水线 |
| 组件交互 | `sequenceDiagram` | API 调用序列、客户端-服务端通信、事件流 |
| 状态转换 | `stateDiagram-v2` | 连接生命周期、认证流程、表单验证状态 |
| 模块依赖 | `flowchart LR` | 导入关系图、服务依赖图 |
| 系统架构 | `flowchart TB` + subgraph | 带分组组件的高层系统概览 |

## 交叉链接要求

- 模块文档必须链接到：架构位置、API 参考、依赖模块。
- API 文档必须链接到：父模块文档、使用示例、相关类型定义。
- architecture.md 必须链接到：所有模块文档和文档地图。
- index.md 必须链接到：架构文档、快速开始和所有模块文档。

## 质量等级

`check_quality.py` 基于行数、章节数、图表和示例综合评分，得出 `basic / standard / professional` 三级。

> 插件内部的 API 文档质量评级与此独立，可能出现不同结果，属正常情况。
