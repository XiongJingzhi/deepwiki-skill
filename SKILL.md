---
name: deepwiki
description: 通过深度分析源代码、架构和模块依赖，自动生成结构化项目文档。Use when user requests "生成 wiki"、"创建文档"、"创建项目文档"、"更新 wiki"、"重建 wiki"、"检查 wiki 质量"、"升级文档"、"预览文档"、"预览 wiki"、"启动文档服务". Also use when a project needs automated documentation generation from source code or viewing generated wiki in a browser.
---

# DeepWiki

通过深度分析源代码、架构和模块依赖，自动生成结构化项目文档到 `.deepwiki/` 目录。

> **文档语言**：读取 `.deepwiki/config.yaml` 中 `generation.language`（`zh` / `en` / `both`），所有生成文档使用该语言撰写。默认 `zh`。
> **参考资料**：详细规则见 [`references/`](references/) 目录；工具列表见下方索引表。

## 运行模式

| 用户意图 | 模式 | 入口工具 |
|---------|------|---------|
| 生成/创建文档 | **全量生成** | 从主路径第 1 步开始串行执行，`init-wiki` 只是初始化 |
| 重建 wiki | **增量更新** | 已有 `.deepwiki/` 时从 `analyze-project` / `detect-changes` 继续，不要重新 `init-wiki` |
| 检查 wiki 质量 | **仅质量检查** | `scripts/postprocess.py quality <project_path>/.deepwiki` |
| 更新/升级文档 | **定向重生成** | `scripts/cli.py page-context` → 按 `generate-module-docs` 规则重生成目标页 |
| 预览文档 | **启动本地服务** | `scripts/cli.py serve <project_path>`（默认端口 8742） |

## 工作流

> **执行原则**：`init-wiki`、`analyze-project`、`extract-structure`、`generate-skeleton`、`prepare_module_context`、`detect-changes`、`validate-analysis`、`plan-doc-topology`、`generate-menu`、`finalize-wiki` 有脚本支撑；`extract-docs`、`generate-overview`、`generate-module-docs` 是 Agent 按参考规则生成内容的 AI 阶段，不能当作单个 shell 命令直接运行。

**主路径（全量/增量）：**

```
init-wiki → analyze-project → extract-structure → generate-skeleton
→ prepare_module_context → extract-docs → validate-analysis → plan-doc-topology
→ generate-overview → generate-menu → generate-module-docs → finalize-wiki
```

### 阶段 A — 准备

1. **`init-wiki`**：创建 `.deepwiki/` 目录结构；仅首次生成使用。目录已存在时不要把失败当作生成失败，应继续增量流程或显式 `--force`
2. **`analyze-project`**：项目结构分析，生成模块/入口点/技术栈。可选运行 `refine-modules`（模块边界失真时），**若运行必须在 `generate-skeleton` 之前**
3. **`extract-structure`**：提取代码结构到 `cache/`
4. **`generate-skeleton`**：运行 `scripts/pipeline/generate_skeleton.py <project_path>` 生成 `architecture-skeleton.json` 的确定性字段，然后由 Agent 补齐 `project_nature`、`key_data_flows`

### 阶段 B — 分析注入

5. **`prepare_module_context`**（脚本，`extract-docs` 前置）：生成含签名/exports 的 `context.json`；`extract-docs` 禁止读取任何源码文件
6. **`extract-docs`**：AI 模块语义分析。增量模式下读取 `detect-changes` 结果；全量首次生成时自动处理
7. **`validate-analysis`**：封装 `check-analysis-quality` + `build-evidence-index`，通过后生成 `evidence-index.json`；exit=1 时 Agent 需对失败模块增量补充分析后重跑（见 [`validate-analysis.md`](references/workflow/validate-analysis.md) 重试流程）

### 阶段 C — 规划

8. **`plan-doc-topology`**：生成文档拓扑与编译计划
9. **`generate-overview`**：复用 `synthesize-deps` 依赖综合规则，生成概述页 + 项目上下文摘要
10. **`generate-menu`**（必须）：运行 `scripts/wiki/generate_menu.py <project_path>/.deepwiki/wiki <project_name>` 生成 `wiki/menu.json` 与 `wiki/doc-map.md`，为模块文档提供导航和面包屑

### 阶段 D — 生成

11. **`generate-module-docs`**：按页面计划逐页生成模块文档

### 阶段 E — 收尾

12. **`finalize-wiki`**：封装收尾四步（顺序不可颠倒）— 菜单校验 → Mermaid 修复 → 质量检查 → 一致性检查

### 多 Agent 拆分提示

并行阶段 subagent 提示词见 [`references/subagents/`](references/subagents/)，包含：
- [`extract-docs`](references/subagents/extract-docs.md) — 模块分析并行
- [`generate-module-docs`](references/subagents/generate-module-docs.md) — 文档生成并行
- [`quality-fix`](references/subagents/quality-fix.md) — 质量修复并行
- 共享调度框架：[`batch-scheduling.md`](references/rules/batch-scheduling.md)

**可拆分阶段**：
- `extract-docs`：`prepare_module_context` 完成后，按模块拆分；每个 subagent 只读自己的 `cache/modules/<slug>/context.json`，写入 `cache/module-analysis.<slug>.json`
- `generate-module-docs`：`generate-menu` 和可选 `extract_source_snippets` 完成后，按 `generation-plan.json.pages[]` 拆分；每个 subagent 写入自己的 `output_path`
- `quality-fix`：质量检查后，按 Basic 文档或失败页面拆分；同一文档只能分配给一个 subagent

**必须串行阶段**：`init-wiki`、`analyze-project`、`extract-structure`、`generate-skeleton`、`prepare_module_context`、`validate-analysis`、`plan-doc-topology`、`generate-overview`、`generate-menu`、`finalize-wiki`。这些步骤需要全局一致输入、写聚合文件，或负责合并检查。

**触发阈值**：任务数 ≤ 5 时主 Agent 串行；6–15 时建议 subagent 分批；> 15 时必须按 [`batch-scheduling.md`](references/rules/batch-scheduling.md) 分批并行。

### 快捷路径

| 场景 | 操作 |
|------|------|
| 仅质量检查 | 直接运行 `scripts/postprocess.py quality <project_path>/.deepwiki` |
| 定向重生成 | `scripts/cli.py page-context <project_path> <wiki_path>` → 重生成目标页 → `scripts/postprocess.py quality <project_path>/.deepwiki` |
| 收尾四步 | `scripts/wiki/generate_menu.py <wiki_dir> <project_name> --reconcile` → `scripts/postprocess.py mermaid <deepwiki_dir>` → `scripts/postprocess.py quality <deepwiki_dir>` → `scripts/postprocess.py consistency <deepwiki_dir>` |
| 预览文档 | `scripts/cli.py serve <project_path>`，浏览器打开 `http://127.0.0.1:8742` |
| 定向更新单页 | `scripts/cli.py page-context <project_path> <wiki_path>` 获取上下文 → 按 `generate-module-docs` 规则重生成 → `postprocess.py quality` 确认 |

## 工具索引

### Pipeline 脚本

| 工具 | 说明 |
|------|------|
| `init-wiki` | [init-wiki.md](references/workflow/init-wiki.md) |
| `analyze-project` | [analyze-project.md](references/workflow/analyze-project.md) |
| `extract-structure` | [extract-structure.md](references/workflow/extract-structure.md) |
| `refine-modules` | [refine-modules.md](references/workflow/refine-modules.md)（可选） |
| `generate-skeleton` | [generate-skeleton.md](references/workflow/generate-skeleton.md) |
| `detect-changes` | [detect-changes.md](references/workflow/detect-changes.md) |
| `prepare_module_context` | `scripts/pipeline/prepare_module_context.py`（`extract-docs` 前置） |
| `build_prompt` | `scripts/subagent/build_prompt.py`（从模板生成 subagent 系统提示词） |
| `extract-docs` | [extract-docs.md](references/workflow/extract-docs.md) |
| `validate-analysis` | [validate-analysis.md](references/workflow/validate-analysis.md)（含 `check-analysis-quality` + `build-evidence-index`） |
| `plan-doc-topology` | [plan-doc-topology.md](references/workflow/plan-doc-topology.md) |
| `extract_source_snippets` | `scripts/pipeline/extract_source_snippets.py`（`generate-module-docs` 前置，可选） |
| `generate-overview` | [generate-overview.md](references/workflow/generate-overview.md) |
| `generate-menu` | [generate-menu.md](references/workflow/generate-menu.md) |
| `generate-module-docs` | [generate-module-docs.md](references/workflow/generate-module-docs.md) |
| `finalize-wiki` | [finalize-wiki.md](references/workflow/finalize-wiki.md)（封装收尾四步） |
| `finalize` | `scripts/postprocess.py <command>`（mermaid / quality / consistency） |

### AI 工作流与规范

| 文档 | 链接 |
|------|------|
| `synthesize-deps` | [synthesize-deps.md](references/workflow/synthesize-deps.md)（`generate-overview` 内部规则） |
| `codepurpose-detection` | [codepurpose-detection.md](references/rules/codepurpose-detection.md) |
| `module-analysis-spec` | [module-analysis-spec.md](references/rules/module-analysis-spec.md) |
| `planning-output-spec` | [planning-output-spec.md](references/rules/planning-output-spec.md) |

### 辅助脚本

| 命令 | 说明 |
|------|------|
| `scripts/cli.py serve` | 启动本地文档预览服务 |
| `scripts/cli.py page-context` | 提取指定 wiki 页面的模块分析上下文 |
| `scripts/cli.py self-check` | 检查 skill 包元数据、关键文件、CLI 命令 |

## 运行环境

| 依赖 | 版本要求 | 用途 | 缺失时行为 |
|------|---------|------|----------|
| Python | >= 3.9 | 所有脚本运行时 | 必须 |
| Python 包 | `pyyaml>=6.0`, `jsonschema>=4.0` | 配置读取、schema 校验 | 必须；安装: `pip install -e .` |
| Python 包 | `tree-sitter>=0.23.0` 及语言绑定 | `extract_structure.py` 代码解析 | 必须；安装: `pip install -e .` |
| Node.js | >= 16 | mmdc CLI 运行时 | 可选；Mermaid 校验自动跳过 |
| `@mermaid-js/mermaid-cli` | 最新版 | `postprocess.py mermaid --validate` | 可选；`check_mmdc_available()` 检测后降级 |

> **安装 Python 依赖：** `pip install -e .`（安装 `pyproject.toml` 中声明的全部依赖）
> **安装 mmdc（可选）：** `npm install -g @mermaid-js/mermaid-cli`
> 安装后 Mermaid AI 修复可进入阶段 2（mmdc 校验 → AI 定向修复）；未安装时仅执行正则修复。

## 不适用场景

- 项目文件极少（< 5 个文件）时，手写文档更快
- 已有完善文档体系且不需要自动化更新时
- 仅需要单个函数/文件说明时（直接请 AI 解释即可）

## 输出结构

```
.deepwiki/
├── config.yaml
├── meta.json
├── state/                     # 流程状态
│   ├── checksums.json
│   ├── file-hashes.json
│   └── progress.json
├── cache/                     # AI 认知上下文
│   ├── structure.json
│   ├── parse-results.json
│   ├── code-structure.json
│   ├── architecture-skeleton.json
│   ├── module-analysis.json
│   ├── doc-topology.json
│   ├── generation-plan.json
│   ├── evidence-index.json
│   └── snippets/             # 预提取源码片段（可选）
└── wiki/
    ├── overview.md
    ├── getting-started.md
    ├── doc-map.md
    ├── menu.json
    ├── concepts/         # 理解项目
    ├── deep-dive/        # 深入理解
    └── reference/        # 参考资料
```

> 所有输出文件的完整用途说明见 [`references/system-reference.md`](references/system-reference.md)。
