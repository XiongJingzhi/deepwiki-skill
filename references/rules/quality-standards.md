# 输出文档质量规范

在 `generate-pages` 阶段写页面时遵循本规范。

## 必需结构

每个生成的 Markdown 页面必须：

- 以一个 H1 标题开头。
- 在 H1 后立即放置 `<details open><summary>Relevant source files</summary>` 或 `<summary>相关源文件</summary>`。
- 相关源码文件使用树形列表，不使用表格。
- 源码链接使用 `file:///path#Lx-Ly`，必须带行号范围。
- 至少包含一个 H2 章节。
- 解释 WHY 和 HOW，不只写 WHAT。
- 适当链接相关 Wiki 页面。

## 源码块模板

```markdown
<details open>
<summary>相关源文件</summary>

- src/
  - [app.py](file:///src/app.py#L1-L40) `L1-L40` - 运行入口和调度逻辑

</details>
```

## Mermaid 规则

- 每个 Mermaid 图前必须有一段简短文字，说明图展示什么关系或流程。
- 工作流和架构优先使用 `flowchart TD`；交互流程使用 `sequenceDiagram`；类型关系使用 `classDiagram`；状态变化使用 `stateDiagram-v2`。
- 含空格、标点或非 ASCII 文本的标签必须加引号。
- 交付前在安装 `mmdc` 的环境中运行 `deepwiki mermaid <project_path> --validate`。

## 收尾检查

运行：

```bash
deepwiki mermaid <project_path> --validate
deepwiki quality <project_path>
deepwiki finalize <project_path>
```

`finalize` 已包含菜单生成、Mermaid 修复/校验、质量检查和链接检查。
