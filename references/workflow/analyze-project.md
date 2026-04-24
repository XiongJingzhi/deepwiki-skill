# analyze-project：分析项目结构

> 工作流analyze-project，检测技术栈、模块结构和入口文件，输出 `cache/structure.json`。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/analyze_project.py <项目路径>` |
| **输入** | 项目源代码目录 |
| **输出** | `cache/structure.json`、`cache/project-digest.md` |
| **前置** | `init-wiki` |
| **后置** | `extract-structure` |

## 检测内容

| 检测项 | 说明 |
|--------|------|
| **技术栈** | 从清单文件（package.json、go.mod、Cargo.toml 等）检测语言、框架和库 |
| **模块** | 目录结构、逻辑分组、入口点 |
| **入口文件** | `src/index.ts`、`main.py`、`cmd/`、`lib/` 等 |
| **现有文档** | `README.md`、`CHANGELOG.md`、内联文档注释、已有的 wiki 文件 |

## 注意事项

- **扁平结构项目**：`analyze_project.py` 会自动跳过 `scripts/`、`docs/`、`tests/` 等非业务目录。如仍有误识别，可在 `.deepwiki/config.yaml` 的 `exclude` 中手动补充。
