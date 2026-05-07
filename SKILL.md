---
name: deepwiki
description: 通过 Agent 自主探索源码并生成结构化项目 Wiki。适用于“生成 wiki”“创建项目源码文档”“创建项目文档”“更新 wiki”“分析项目并生成文档”“预览项目 wiki”“启动文档服务”等请求。
---

# DeepWiki

DeepWiki 将项目文档生成到 `.deepwiki/`。脚本只负责收集轻量事实和校验最终输出；Agent 负责理解项目、规划页面和撰写文档。

## 主流程

```text
init-wiki → prepare-inventory → agentic-analysis → plan-pages
→ generate-menu → generate-pages → finalize-wiki
```

## 命令

在本 skill 目录运行。安装后，`deepwiki <command>` 等价于 `python -m scripts.cli <command>`。

| 阶段 | 命令 / Agent 动作 |
| --- | --- |
| `init-wiki` | `deepwiki init <project_path>` |
| `prepare-inventory` | `deepwiki prepare-inventory <project_path>` |
| `agentic-analysis` | Agent 写入 `.deepwiki/cache/semantic-analysis.json` |
| `plan-pages` | Agent 写入 `.deepwiki/cache/page-plan.json`，再运行 `deepwiki validate-page-plan <project_path>` |
| `generate-menu` | `deepwiki generate-menu <project_path>` |
| `generate-pages` | 对每个页面运行 `deepwiki page-context <project_path> <page_id>`，再写入 Markdown |
| `finalize-wiki` | `deepwiki finalize <project_path>` |
| 仅质量检查 | `deepwiki quality <project_path>` |
| 仅 Mermaid 检查 | `deepwiki mermaid <project_path> --validate` |
| 预览 | `deepwiki serve <project_path>` |

## 规则

- `.deepwiki/cache/project-inventory.json` 是唯一强制准备产物。
- `agentic-analysis`、`plan-pages`、`generate-pages` 阶段由 Agent 按需直接阅读源码。
- 文档生成以 `.deepwiki/cache/page-plan.json` 中的页面为拆分单位。
- 不依赖旧缓存文件，例如 `structure.json`、`module-analysis.json`、`generation-plan.json`。
- 写页面时遵循 `references/rules/quality-standards.md`。
- `finalize-wiki` 失败时必须停止，并报告失败检查项。

## 参考资料

- 工作流细节：`references/workflow/*.md`
- 缓存契约：`references/system-reference.md`
- 输出规范：`references/rules/quality-standards.md`
