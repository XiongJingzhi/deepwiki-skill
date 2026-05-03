# generate-overview

前置：`plan-doc-topology`、`validate-analysis` | 后置：`generate-menu`（初始）、`generate-module-docs`

输入：`cache/structure.json`、`cache/code-structure.json`、`cache/module-analysis.json`、`cache/doc-topology.json`、`cache/architecture-skeleton.json`（可选）
输出：`wiki/overview.md`、`wiki/getting-started.md`
生成规则：见 `../generation/overview-page.md`、`../generation/getting-started-page.md`

## 骨架复用

若 `cache/architecture-skeleton.json` 存在，先读取并直接复用：

| 骨架字段 | 用于 overview.md 的章节 |
|---------|---------------------|
| `project_nature` | 第一段项目定位描述 |
| `architecture_style` | 架构风格说明 |
| `architecture_layers` | 系统架构分层图（Mermaid flowchart） |
| `module_groups` | 模块列表分组展示 |
| `key_data_flows` | 关键数据流章节 |

## 依赖综合摘要读取

1. 若 `cache/relationship-summary.json` 存在，直接读取
2. 若不存在，执行 `synthesize-deps` 规则完整流程，结果自动缓存
3. 降级：若骨架不存在，从 `code-structure.json`、`module-analysis.json.dependency_hints` 和 `structure.json` 生成

## 文档内容

| 文档 | 模板 | 内容 |
|------|------|------|
| `overview.md` | `../generation/overview-page.md` | 项目定位、技术栈、系统架构图、分层说明、模块列表、依赖图（条件）、文档导航 |
| `getting-started.md` | `../generation/getting-started-page.md` | 前置条件、安装步骤、第一个示例、常见问题 |

每生成完一个文档即更新 `state/progress.json` 对应文件状态；全部完成后更新 `phases.overview.status` 为 `completed`。

## 概要上下文摘要

生成完毕后提取精简摘要（约 1-3KB）注入 generate-module-docs：项目定位和技术栈（1-2 句）+ 架构分层和各层职责（一句话/层）+ 每个模块的角色描述。
