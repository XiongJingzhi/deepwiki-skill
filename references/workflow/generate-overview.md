# generate-overview：生成概览文档

> generate-overview 基于确定性缓存、架构骨架、模块分析和依赖综合规则生成全局概览文档。这些文档不依赖具体模块的详细文档，可直接产出。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | 无（AI 执行） |
| **输入** | `cache/structure.json`、`cache/code-structure.json`、`cache/module-analysis.json`、`cache/doc-topology.json`、`cache/architecture-skeleton.json`（可选） |
| **输出** | `wiki/overview.md`、`wiki/getting-started.md` |
| **前置** | `plan-doc-topology`、`validate-analysis` |
| **后置** | 初始 `generate-menu`、`generate-module-docs` |
| **生成规则** | 见 `../generation/overview-page.md`、`../generation/getting-started-page.md` |

## 优先复用架构骨架

若 `cache/architecture-skeleton.json` 存在（generate-skeleton 生成），在生成概览文档前先读取骨架，直接复用以下内容：

| 骨架字段 | 用于概览文档的哪个章节 |
|---------|---------------------|
| `project_nature` | `overview.md` 的第一段项目定位描述 |
| `architecture_style` | `overview.md` 的"架构风格"说明 |
| `architecture_layers` | `overview.md` 的"系统架构"分层图（Mermaid flowchart） |
| `module_groups` | `overview.md` 的模块列表，按分组展示 |
| `key_data_flows` | `overview.md` 的"关键数据流"章节 |

**效果**：直接使用骨架内容，AI 只需补充细节和排版，token 消耗减少 30-40%。

**降级处理**：若骨架不存在，从 `code-structure.json`、`module-analysis.json.dependency_hints` 和 `structure.json` 生成依赖综合摘要。

## 概览文档列表

| 文档 | 模板参考 | 内容要点 |
|------|---------|---------|
| `overview.md` | `../generation/overview-page.md` → 概览文档 | 项目定位、技术栈、系统架构图、分层说明、模块列表、依赖图（条件）、文档导航 |
| `getting-started.md` | `../generation/overview-page.md` → 快速开始 | 前置条件、安装步骤、第一个示例、常见问题 |

每生成完一个文档即更新 `cache/progress.json` 的 `phases.overview.documents` 中对应文件的状态为 `completed` 或 `failed`，确保中断后可从断点恢复。全部概览文档完成后，更新 `phases.overview.status` 为 `completed`。

## 概要上下文摘要提取

概览文档生成完毕后，从中提取一份精简的"项目上下文摘要"（约 1-3KB），包含：

- 项目定位和技术栈（1-2 句）
- 架构分层和各层职责（一句话/层）
- 每个模块在架构中的角色和一句话描述

这份摘要将在generate-module-docs作为 subagent 的共享上下文注入，避免每个 subagent 重复读取完整概览文档。
