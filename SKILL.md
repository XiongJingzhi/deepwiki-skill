---
name: deepwiki
description: 通过深度分析源代码、架构和模块依赖，自动生成结构化项目文档。Use when user requests "生成 wiki"、"创建文档"、"创建项目文档"、"更新 wiki"、"重建 wiki"、"检查 wiki 质量"、"升级文档". Also use when a project needs automated documentation generation from source code.
---

# DeepWiki

通过深度分析源代码、架构和模块依赖，自动生成结构化项目文档到 `.deepwiki/` 目录。

> **参考资料**：详细规则见 [`references/`](references/) 目录；工具列表见下方索引表。

## 运行模式

| 用户意图 | 模式 | 入口工具 |
|---------|------|---------|
| 生成/创建文档 | **全量生成** | `init-wiki` |
| 重建 wiki | **增量更新** | `init-wiki`（`detect-changes` 自动跳过未变更模块） |
| 检查 wiki 质量 | **仅质量检查** | `finalize.py quality`（直接运行，不重新生成） |
| 更新/升级文档 | **定向重生成** | `extract-docs`（跳过 `init-wiki` → `detect-changes`） |

## 工作流

**主路径（全量/增量）：**

`init-wiki` → `analyze-project` → `extract-structure` → `refine-modules` → `generate-skeleton`（纯 AI）→ `detect-changes` → `extract-docs` → `check-analysis-quality`

- **pass（exit=0）**：→ `synthesize-deps` → `generate-overview` → `generate-menu` → `generate-module-docs` → `check-cross-module-consistency` → 完成
- **fail（exit≠0）**：增量补充分析 → 重跑 `check-analysis-quality`

**快捷路径：**

- 仅质量检查：直接运行 `finalize.py quality`，跳过所有生成步骤
- 定向重生成：从 `extract-docs` 开始，跳过 `init-wiki` → `detect-changes`


## 工具索引

| 工具 | 详细规则 |
|------|---------|
| `init-wiki` | [references/workflow/init-wiki.md](references/workflow/init-wiki.md) |
| `analyze-project` | [references/workflow/analyze-project.md](references/workflow/analyze-project.md) |
| `extract-structure` | [references/workflow/extract-structure.md](references/workflow/extract-structure.md) |
| `refine-modules` | [references/workflow/refine-modules.md](references/workflow/refine-modules.md) |
| `generate-skeleton` | [references/workflow/generate-skeleton.md](references/workflow/generate-skeleton.md)（纯 AI 步骤，无脚本） |
| `detect-changes` | [references/workflow/detect-changes.md](references/workflow/detect-changes.md) |
| `extract-docs` | [references/workflow/extract-docs.md](references/workflow/extract-docs.md) |
| `parallel-analysis` | [references/workflow/parallel-analysis.md](references/workflow/parallel-analysis.md) |
| `check-analysis-quality` | [references/workflow/check-analysis-quality.md](references/workflow/check-analysis-quality.md) |
| `synthesize-deps` | [references/workflow/synthesize-deps.md](references/workflow/synthesize-deps.md) |
| `generate-overview` | [references/workflow/generate-overview.md](references/workflow/generate-overview.md) |
| `generate-menu` | [references/workflow/generate-menu.md](references/workflow/generate-menu.md) |
| `generate-module-docs` | [references/workflow/generate-module-docs.md](references/workflow/generate-module-docs.md) |
| `finalize` | [references/workflow/generate-module-docs.md](references/workflow/generate-module-docs.md) | 文档收尾工具（mermaid 修复/质量检查/一致性检查） |
| `check-cross-module-consistency` | 脚本：`scripts/finalize.py consistency`（详见 [`generate-module-docs.md`](references/workflow/generate-module-docs.md)） |
| `codepurpose-detection`（规则） | [references/rules/codepurpose-detection.md](references/rules/codepurpose-detection.md) |
| `analysis-output-spec`（规范） | [references/rules/analysis-output-spec.md](references/rules/analysis-output-spec.md) |

## 不适用场景

- 项目文件极少（< 5 个文件）时，手写文档更快
- 已有完善文档体系且不需要自动化更新时
- 仅需要单个函数/文件说明时（直接请 AI 解释即可）

## 输出结构

```
.deepwiki/
├── config.yaml
├── meta.json
├── cache/
│   ├── checksums.json
│   ├── structure.json
│   ├── file-hashes.json
│   ├── parse-results.json
│   ├── code-structure.json
│   ├── architecture-skeleton.json
│   ├── module-analysis.json
│   └── progress.json
└── wiki/
    ├── overview.md
    ├── getting-started.md
    ├── doc-map.md
    ├── menu.json
    ├── modules/
    │   ├── _index.md
    │   └── <module-name>.md
    └── api/
        ├── _index.md
        └── <module-name>.md
```

> 所有输出文件的完整用途说明见 [`references/system-reference.md`](references/system-reference.md)。
