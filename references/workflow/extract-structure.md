# extract-structure：提取代码结构

> 工作流extract-structure，从 `structure.json` 提取调用图、代码模式和关键时序，输出 `cache/code-structure.json`。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/extract_structure.py <项目路径>` |
| **输入** | `cache/structure.json` |
| **输出** | `cache/code-structure.json` |
| **前置** | `analyze-project` |
| **后置** | `generate-skeleton`、`detect-changes` |

## 输出字段说明

| 字段 | 内容 | 后续用途 |
|------|------|---------|
| `archetype` | 项目原型标签（`spa-frontend` / `web-service` / `cli-tool` / `sdk-library` / `ml-project` / `agent-project` / `fullstack-framework` / `monorepo` / `generic`） | extract-docs 决定分析侧重点与图表类型；`monorepo`（包间依赖关系/共享模块/各子包独立入口/跨包调用链） |
| `call_graph` | `{ "Class.method": { calls, file, line } }` 跨文件调用图 | extract-docs 作为语义分析锚点，synthesize-deps 增强依赖图 |
| `patterns` | 检测到的代码模式（`middleware_chain` / `http_route` / `orm_usage` / `react_component` / `state_management` / `event_system` 等） | extract-docs 指导 AI 聚焦核心模式 |
| `key_sequences` | 从入口点 BFS 生成的近似时序（`participants` / `steps`） | generate-overview 生成 `architecture.md` 时序图的原始数据 |
| `import_relations` | 文件级导入关系图（`{file: {imports: [...]}}`） | synthesize-deps 作为可信基线验证 AI 依赖分析的准确性 |

> **实现说明**：使用 tree-sitter AST 精确解析，覆盖 TS/JS/Python/Go/Rust/Java/Kotlin，不会误匹配字符串或注释中的伪代码结构。

## Monorepo 检测逻辑

当 `analyze-project` 在 `structure.json` 中检测到 `is_monorepo: true` 时，`extract-structure` 自动将 archetype 设为 `monorepo`，并调整分析单位。

**检测文件标记**（满足任一即判定为 monorepo）：
- `pnpm-workspace.yaml` — pnpm workspace 配置
- `lerna.json` — Lerna monorepo 管理配置
- `turbo.json` — Turborepo 配置
- `nx.json` — Nx workspace 配置
- `package.json` 中包含 `workspaces` 字段 — Yarn/npm workspace 原生声明
- `rush.json` — Rush monorepo 配置

| 普通项目 | Monorepo |
|---------|---------|
| 以目录模块为分析单位 | 以 package（子包）为分析单位 |
| `core_files` 覆盖全仓库 | `core_files` 优先覆盖各 package 的入口文件 |
| `import_relations` 为全仓库文件图 | `import_relations` 额外标注跨包引用（`cross_package: true`） |
