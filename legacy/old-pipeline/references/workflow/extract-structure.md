# extract-structure

`python -m scripts.analysis.extract_structure <项目路径>`

前置：`analyze-project` | 后置：`generate-skeleton`、`detect-changes`

输入：`cache/structure.json`
输出：`cache/code-structure.json`

## 输出字段

| 字段 | 内容 |
|------|------|
| `archetype` | 项目原型标签（`spa-frontend` / `web-service` / `cli-tool` / `sdk-library` / `ml-project` / `agent-project` / `fullstack-framework` / `monorepo` / `generic`） |
| `call_graph` | `{ "Class.method": { calls, file, line } }` 跨文件调用图 |
| `patterns` | 检测到的代码模式（`middleware_chain` / `http_route` / `orm_usage` / `react_component` / `state_management` / `event_system` 等） |
| `key_sequences` | 从入口点 BFS 生成的近似时序（`participants` / `steps`） |
| `import_relations` | 文件级导入关系图（`{file: {imports: [...]}}`） |
