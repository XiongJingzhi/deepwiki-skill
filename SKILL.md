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

**外部主路径（9 步，全量/增量）：**

`init-wiki` → `analyze-project` → `extract-structure` → `generate-skeleton`（纯 AI）→ `extract-docs` → `validate-analysis` → `plan-doc-topology` → `generate-overview` → `generate-module-docs`

- `analyze-project` 可吸收 `refine-modules` 作为候选模块优化，不作为必经心智步骤。
- `extract-docs` 在增量模式下读取 `detect-changes` 结果；全量模式可跳过独立变更检测。
- `validate-analysis` 封装 `check-analysis-quality` 与 `build-evidence-index`，通过后生成 `evidence-index.json`。
- `generate-overview` 复用 `synthesize-deps` 的依赖综合规则，并负责全局阅读路径。
- 初始 `generate-menu` 在模块文档前生成 `menu.json` / `doc-map.md`；`generate-module-docs` 结束后再运行 `generate-menu --reconcile`、`finalize quality`、`check-cross-module-consistency` 收尾。
- **fail（exit≠0）**：增量补充分析 → 重跑 `validate-analysis`

**快捷路径：**

- 仅质量检查：直接运行 `finalize.py quality`，跳过所有生成步骤
- 定向重生成：从 `extract-docs` 开始，跳过 `init-wiki` → `detect-changes`


## 工具索引

| 工具 | 详细规则 |
|------|---------|
| `init-wiki` | [references/workflow/init-wiki.md](references/workflow/init-wiki.md) |
| `analyze-project` | [references/workflow/analyze-project.md](references/workflow/analyze-project.md) |
| `extract-structure` | [references/workflow/extract-structure.md](references/workflow/extract-structure.md) |
| `refine-modules` | [references/workflow/refine-modules.md](references/workflow/refine-modules.md)（`analyze-project` 的可选子步骤） |
| `generate-skeleton` | [references/workflow/generate-skeleton.md](references/workflow/generate-skeleton.md)（纯 AI 步骤，无脚本） |
| `detect-changes` | [references/workflow/detect-changes.md](references/workflow/detect-changes.md) |
| `extract-docs` | [references/workflow/extract-docs.md](references/workflow/extract-docs.md) |
| `plan-doc-topology` | [references/workflow/plan-doc-topology.md](references/workflow/plan-doc-topology.md) |
| `validate-analysis` | [references/workflow/validate-analysis.md](references/workflow/validate-analysis.md) |
| `build-evidence-index` | [references/workflow/build-evidence-index.md](references/workflow/build-evidence-index.md)（`validate-analysis` 的子步骤） |
| `parallel-analysis` | [references/workflow/parallel-analysis.md](references/workflow/parallel-analysis.md) |
| `check-analysis-quality` | [references/workflow/check-analysis-quality.md](references/workflow/check-analysis-quality.md)（`validate-analysis` 的子步骤） |
| `synthesize-deps` | [references/workflow/synthesize-deps.md](references/workflow/synthesize-deps.md)（`generate-overview` 的内部规则） |
| `generate-overview` | [references/workflow/generate-overview.md](references/workflow/generate-overview.md) |
| `generate-menu` | [references/workflow/generate-menu.md](references/workflow/generate-menu.md) |
| `generate-module-docs` | [references/workflow/generate-module-docs.md](references/workflow/generate-module-docs.md) |
| `finalize` | [references/workflow/generate-module-docs.md](references/workflow/generate-module-docs.md) | 文档收尾工具（mermaid 修复/质量检查/一致性检查） |
| `self-check` | 脚本：`scripts/cli.py self-check`，检查 skill 包元数据、关键文件、CLI 命令和已跟踪生成物 |
| `check-cross-module-consistency` | 脚本：`scripts/finalize.py consistency`（详见 [`generate-module-docs.md`](references/workflow/generate-module-docs.md)） |
| `codepurpose-detection`（规则） | [references/rules/codepurpose-detection.md](references/rules/codepurpose-detection.md) |
| `file-role-classification`（规则） | [references/rules/file-role-classification.md](references/rules/file-role-classification.md) |
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
│   ├── doc-topology.json
│   ├── generation-plan.json
│   ├── evidence-index.json
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
