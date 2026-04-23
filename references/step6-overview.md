# 第 6 步：生成概览文档

> 工作流第六步，应用 `before_generate` 钩子后，基于第 2-5 步的分析结果生成全局概览文档。这些文档不依赖具体模块的详细文档，可直接产出。

## 概览文档列表

| 文档 | 模板参考 | 内容要点 |
|------|---------|---------|
| `index.md` | `references/templates.md` → 首页 | 项目概述、技术栈徽章、快速导航、模块列表 |
| `architecture.md` | `references/templates.md` → 架构 | 系统架构图（Mermaid）、技术栈、模块依赖关系、架构分层（来自第 5 步输出） |
| `getting-started.md` | `references/templates.md` → 快速开始 | 前置条件、安装步骤、第一个示例、常见问题 |

每生成完一个文档即更新 `cache/progress.json` 的 `phases.overview.documents` 中对应文件的状态为 `completed` 或 `failed`，确保中断后可从断点恢复。阶段 6 完成后，更新 `phases.overview.status` 为 `completed`。

## 概要上下文摘要提取

概览文档生成完毕后，从中提取一份精简的"项目上下文摘要"（约 1-3KB），包含：

- 项目定位和技术栈（1-2 句）
- 架构分层和各层职责（一句话/层）
- 每个模块在架构中的角色和一句话描述

这份摘要将在第 8 步作为 subagent 的共享上下文注入，避免每个 subagent 重复读取完整概览文档。
