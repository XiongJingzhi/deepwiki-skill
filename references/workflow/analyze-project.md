# analyze-project：分析项目结构

> 工作流analyze-project，检测技术栈、模块结构和入口文件，输出 `cache/structure.json`。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/analyze_project.py <项目路径>` |
| **输入** | 项目源代码目录 |
| **输出** | `cache/structure.json` |
| **前置** | `init-wiki` |
| **后置** | `extract-structure` |

## 检测内容

| 检测项 | 说明 |
|--------|------|
| **技术栈** | 从清单文件（package.json、go.mod、Cargo.toml 等）检测语言、框架和库 |
| **模块** | 综合入口文件、调用链、导入关系、业务能力、目录结构和依赖边界推断模块；目录结构只作为候选信号，不直接等同模块边界 |
| **入口文件** | `src/index.ts`、`main.py`、`cmd/`、`lib/` 等 |
| **现有文档** | `README.md`、`CHANGELOG.md`、内联文档注释、已有的 wiki 文件 |

## 模块拆分原则

模块边界应帮助读者理解系统，而不是机械反映文件夹：

1. **入口优先**：先识别应用入口、CLI 入口、HTTP/WS 路由入口、worker/agent 启动入口，再沿调用链和 import 关系找到它们驱动的内部能力。
2. **应用容器展开**：如果 `app/`、`src/`、`server/` 等目录同时包含入口文件和多个有代码的子目录，不要只生成一个粗粒度 `app` 模块；应拆成入口模块 + 应用内部能力模块。
3. **可拆必拆**：如果一个候选模块内部还能自然拆成多个有代码的子模块，应继续拆分为子模块。
4. **深度封顶**：模块路径最多 3 层，例如允许 `app/modules/graph`，不要继续拆成 `app/modules/graph/nodes`。
5. **依赖边界保留**：`common/`、`shared/`、`pycommon/`、`lib/`、`sdk/` 等被应用模块调用的共享代码，应作为外部/共享依赖模块保留；若其内部也有多个明确子模块，同样遵守 3 层封顶继续拆分。
6. **强依赖聚合**：多个文件虽然分散在不同目录，但由同一入口链路驱动、双向或高密度依赖、共同完成一个能力时，应合并为同一语义模块候选。
7. **弱目录降权**：目录同父关系只是弱信号；不能仅因为同在一个目录就合并，也不能仅因为分属不同目录就拆开。

示例：`app/main.py` 调用 `app/modules/graph/*`、`app/modules/skills/*`，同时依赖 `pycommon/*` 时，合理拆分是：

- `app-main`：应用入口和路由/生命周期装配
- `app-modules-graph`：`app/modules/graph` 工作流/图执行能力
- `app-modules-skills`：`app/modules/skills` Skill 基类与注册能力
- `pycommon`：共享依赖模块

## 注意事项

- **扁平结构项目**：`analyze_project.py` 会自动跳过 `scripts/`、`docs/`、`tests/` 等非业务目录。如仍有误识别，可在 `.deepwiki/config.yaml` 的 `exclude` 中手动补充。
