# P0 文档生成规范（精简版）

> 本文件从 `module-page-core.md`、`module-page-components.md`、`quality-standards.md`、`components-guide.md` 提炼而出，包含所有 P0 必需规则。

---

## 1. 文档结构（强制）

H1 标题之后、任何其他内容之前，**必须**放置 `相关源文件` 折叠块：

```markdown
# 模块功能标题

<details open><summary>相关源文件</summary>

- [src/module/](file:///项目绝对路径/src/module/)
  - [file1.py](file:///项目绝对路径/src/module/file1.py#L10-L50) — 功能描述
  - [file2.py](file:///项目绝对路径/src/module/file2.py#L30-L80) — 功能描述

</details>
```

**规则**：
- 使用 `<details open>` 标签（`open` 不可省略）
- 列出 3–10 个最相关源码文件
- 每个文件**必须**带 `#L起-L止` 行号范围（禁止链接整个文件）
- 目录节点带 `/` 后缀，文件节点缩进
- 链接文本只显示文件名，不含行号

## 2. 源码链接格式（硬门槛）

所有 `file://` 链接必须包含行号范围：

```
[文件名](file:///绝对路径/文件名.ext#L10-L50)
```

- 行号来源：优先使用 `generation-plan.json` 中的 `source_files[].ranges`
- ranges 为空时从 `core_source_ranges` 和 `public_interfaces.line/end_line` 推导
- **缺少源码追溯 → 文档质量上限为 basic**（硬门槛）

### 章节内源码引用

代码块前必须标注来源：

```markdown
**Source:** [path/to/file.py](file:///path/to/file.py#L50-L80)

\`\`\`python
# 代码内容
\`\`\`
```

章节末尾必须包含引用：

```markdown
**来源**：[file1.py](file:///path/file1.py#L10-L25) · [file2.py](file:///path/file2.py#L30-L45)
```

## 3. 章节标题规则（强制）

- **禁止**使用组件名作为标题：`概述`、`核心逻辑`、`执行流程`、`公开接口`、`内部结构`、`数据流`、`设计思路`
- **必须**使用语义化标题，反映模块实际功能：
  - ✅ `认证与鉴权核心流程`、`上下文压缩与记忆管理`、`模型适配器调度策略`
  - ❌ `概述`、`核心组件`、`数据流`

## 4. P0 必需组件

### relevant-source-files — 相关源文件（无条件必需）

- 位置：H1 后第一个块
- 格式：`<details open>` 折叠块（见第 1 节）
- 不可省略

### overview — 模块定位（CodePurpose ≠ Test 时必需）

- 2–3 段文字描述：模块目的、解决的问题、在系统中的角色
- 可含 Mermaid flowchart 高亮当前模块（可选）

### design-rationale — 设计思路

**触发条件**（满足任一即生成）：
- `CodePurpose in [Entry, Agent, Service, Api, Command, Database]`
- 模块复杂度 >= 30
- `key_insights` 非空

**格式**：
1. 设计目标
2. 约束条件
3. 当前方案
4. 替代方案取舍表：`| 方案 | 收益 | 代价 | 为什么当前没选 |`

### code-walkthrough — 核心代码走查（无条件必需）

**格式**：先给精简伪代码（10–30 行）概括主路径，再给 1–3 段真实源码片段（每段 20–80 行）+ 逐段讲解表：

```markdown
**Source:** [file.py](file:///path/file.py#L50-L80)

\`\`\`python
# 带中文注释的关键源码
\`\`\`

| 片段 | 做什么 | 为什么这样做 | 关键变量/调用 | 风险 |
|------|--------|-------------|-------------|------|
| L50-60 | ... | ... | ... | ... |
```

**降级**：纯常量/类型别名模块可缩为 3–5 行关键代码 + 一句话说明。

## 5. 排版顺序

```
相关源文件 → 模块定位（overview）→ 设计思路 → 内部运行模型 → 代码走查 → 接口与图表 → 相关文档
```

不要按源码文件顺序排列。内容密度优先：宁可写好 5 个相关章节，也不要凑满 9 个空壳。

## 6. Mermaid 图表要求

每个 Mermaid 图表必须：
1. **图前**：2–4 句文字描述，解释图表核心内容
2. **图表**：选择正确类型（flowchart=流程、sequenceDiagram=交互、classDiagram=类继承、stateDiagram-v2=状态机）
3. **图后**：2–4 句分析解读

禁止只输出标题 + 代码块。

## 7. 交叉链接

- 深入理解页必须链接到：架构文档、相关深入理解页、参考索引
- 链接必须使用有效格式：`[标题](相对路径.md)`
- 禁止使用 code 标签包裹路径或纯文本

## 8. H1 标题规则

- 只保留核心功能含义
- 禁止使用"深入理解"、"基础介绍"、"全面解析"等冗余修饰
- 格式：直接用功能名称（如"认证与鉴权"），不加前缀后缀
