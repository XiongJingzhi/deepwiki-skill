# 第 2 步：分析

> 工作流第二步，检测技术栈、模块结构和入口文件，输出 `cache/structure.json`。

从**技能目录**运行以下命令：

```bash
python scripts/analyze_project.py <项目目录绝对路径>
```

脚本完成后会**自动**将分析结果写入 `<项目目录>/.deepwiki/cache/structure.json`。**运行完成后，必须读取该文件确认内容已成功保存**，再继续下一步。

## 检测内容

| 检测项 | 说明 |
|--------|------|
| **技术栈** | 从清单文件（package.json、go.mod、Cargo.toml 等）检测语言、框架和库 |
| **模块** | 目录结构、逻辑分组、入口点 |
| **入口文件** | `src/index.ts`、`main.py`、`cmd/`、`lib/` 等 |
| **现有文档** | `README.md`、`CHANGELOG.md`、内联文档注释、已有的 wiki 文件 |

## 注意事项

- **扁平结构项目**：`analyze_project.py` 会自动跳过 `scripts/`、`plugins/`、`docs/`、`tests/` 等非业务目录。如仍有误识别，可在 `.deepwiki/config.yaml` 的 `exclude` 中手动补充。
- 应用 `after_analyze` 插件钩子（纯文本指引）优化分析结果。

---

# 第 2.5 步：代码结构提取

> 工作流第二步半，从 `structure.json` 提取调用图、代码模式和关键时序，输出 `cache/code-structure.json`。

从**技能目录**运行以下命令：

```bash
python scripts/extract_structure.py <项目目录绝对路径>
```

脚本读取 `cache/structure.json`，输出 `cache/code-structure.json`。若 `structure.json` 不存在则报错中止。

## 输出字段说明

| 字段 | 内容 | 后续用途 |
|------|------|---------|
| `archetype` | 项目原型标签（`spa-frontend` / `web-service` / `cli-tool` / `sdk-library` / `ml-project` / `agent-project` / `fullstack-framework` / `generic`） | 第 4 步决定分析侧重点与图表类型 |
| `call_graph` | `{ "Class.method": { calls, file, line } }` 跨文件调用图 | 第 4 步作为语义分析锚点，第 5 步增强依赖图 |
| `patterns` | 检测到的代码模式（`middleware_chain` / `http_route` / `orm_usage` / `react_component` / `state_management` / `event_system` 等） | 第 4 步指导 AI 聚焦核心模式 |
| `key_sequences` | 从入口点 BFS 生成的近似时序（`participants` / `steps`） | 第 6 步生成 `architecture.md` 时序图的原始数据 |
| `import_relations` | 文件级导入关系图（`{file: {imports: [...]}}`） | 第 5 步作为可信基线验证 AI 依赖分析的准确性 |

额外输出文件：`cache/import-relations.json`（与 `code-structure.json` 中的 `import_relations` 字段内容一致）。

> **注意**：基于正则启发式，覆盖 TS/JS/Python/Go/Rust/Java，结果是近似值供 AI 参考锚点，非权威来源。
