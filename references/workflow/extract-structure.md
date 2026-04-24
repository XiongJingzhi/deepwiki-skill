# extract-structure：提取代码结构

> 工作流extract-structure，从 `structure.json` 提取调用图、代码模式和关键时序，输出 `cache/code-structure.json`。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/extract_structure.py <项目路径>` |
| **输入** | `cache/structure.json` |
| **输出** | `cache/code-structure.json`、`cache/import-relations.json` |
| **前置** | `analyze-project` |
| **后置** | `generate-skeleton`、`detect-changes` |

## 输出字段说明

| 字段 | 内容 | 后续用途 |
|------|------|---------|
| `archetype` | 项目原型标签（`spa-frontend` / `web-service` / `cli-tool` / `sdk-library` / `ml-project` / `agent-project` / `fullstack-framework` / `generic`） | extract-docs 决定分析侧重点与图表类型 |
| `call_graph` | `{ "Class.method": { calls, file, line } }` 跨文件调用图 | extract-docs 作为语义分析锚点，synthesize-deps 增强依赖图 |
| `patterns` | 检测到的代码模式（`middleware_chain` / `http_route` / `orm_usage` / `react_component` / `state_management` / `event_system` 等） | extract-docs 指导 AI 聚焦核心模式 |
| `key_sequences` | 从入口点 BFS 生成的近似时序（`participants` / `steps`） | generate-overview 生成 `architecture.md` 时序图的原始数据 |
| `import_relations` | 文件级导入关系图（`{file: {imports: [...]}}`） | synthesize-deps 作为可信基线验证 AI 依赖分析的准确性 |

额外输出文件：`cache/import-relations.json`（与 `code-structure.json` 中的 `import_relations` 字段内容一致）。

> **实现说明**：使用 tree-sitter AST 精确解析，覆盖 TS/JS/Python/Go/Rust/Java/Kotlin，不会误匹配字符串或注释中的伪代码结构。
