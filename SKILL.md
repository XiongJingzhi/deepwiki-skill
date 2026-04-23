---
name: deepwiki
description: 通过深度分析源代码、架构和模块依赖，自动生成结构化项目文档。Use when user requests "生成 wiki"、"创建文档"、"创建项目文档"、"更新 wiki"、"重建 wiki"、"检查 wiki 质量"、"升级文档". Also use when a project needs automated documentation generation from source code.
---

# DeepWiki

通过深度分析源代码、架构和模块依赖，自动生成结构化项目文档到 `.deepwiki/` 目录。

> **参考资料**：详细规则和附加指南见 [`references/`](references/) 目录。

## 运行模式

收到请求后，先判断用户意图，选择对应模式：

| 用户意图 | 模式 | 执行步骤 |
|---------|------|----------|
| 生成 wiki / 创建文档 / 创建项目文档 | **全量生成** | 完整执行第 1-8 步 |
| 重建 wiki | **增量更新** | 执行第 1-8 步，第 3 步变更检测自动跳过未变更模块 |
| 检查 wiki 质量 | **仅质量检查** | 仅执行第 8.4 步（`check_quality.py`），不重新生成 |
| 更新 wiki / 升级文档 | **定向重生成** | 跳过第 1-3 步，从**第 4 步**开始，仅处理指定模块 |

> 「仅质量检查」和「定向重生成」不需要重新初始化或重新分析，直接从对应步骤开始执行。

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
│   └── progress.json
└── wiki/
    ├── index.md
    ├── architecture.md
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

## 插件协议

> 完整协议说明（钩子类型、加载流程、安全约束）见 [`references/plugin.md`](references/plugin.md)。

插件是**纯指令模式**，Agent 绝不能执行插件代码。加载流程：读取 `plugins/_registry.yaml` → 读取各插件 `PLUGIN.md` → 在对应工作流阶段应用钩子指引（`on_init` / `after_analyze` / `before_generate` / `after_generate` / `on_export`）。

## 脚本位置说明

所有 `scripts/` 脚本均位于 **DeepWiki 技能目录**（本 SKILL.md 所在目录），运行时需以技能目录为工作目录，将项目目录绝对路径作为参数传入。详见 [`references/system-reference.md`](references/system-reference.md)。

## 工作流（8 步）

### 第 1 步：初始化

- 检查项目目录下 `.deepwiki/` 是否存在。
  - **不存在**：从**技能目录**运行 `python scripts/init_wiki.py <项目目录绝对路径>` 创建目录结构（`config.yaml`、`cache/`、`wiki/`）。
  - **需要重新初始化**：添加 `--force` 参数强制覆盖已有 `.deepwiki/` 目录（会保留已有 wiki 文件，重建缓存和配置）。
  - **已存在**：读取项目目录下的 `config.yaml` 和 `cache/structure.json` 获取增量更新上下文。检查 `meta.json` 的版本兼容性。
- 从技能目录的 `plugins/_registry.yaml` 加载已启用的插件，读取每个插件的 `PLUGIN.md`，注册钩子。对比每个插件的 `min_version` 与 `meta.json` 的 `version` 字段，跳过不兼容的插件并记录警告。
- 应用 `on_init` 钩子指引。

### 第 2 步：分析

- 从**技能目录**运行 `python scripts/analyze_project.py <项目目录绝对路径>` 检测：
  - **技术栈**：从清单文件（package.json、go.mod、Cargo.toml 等）检测语言、框架和库
  - **模块**：目录结构、逻辑分组、入口点
  - **入口文件**：`src/index.ts`、`main.py`、`cmd/`、`lib/` 等
  - **现有文档**：`README.md`、`CHANGELOG.md`、内联文档注释、已有的 wiki 文件
- 脚本运行后会**自动**将分析结果写入 `<项目目录>/.deepwiki/cache/structure.json`（如目录不存在会自动创建）。**运行完成后，必须读取该文件确认内容已成功保存**，再继续下一步。
- 应用 `after_analyze` 插件钩子（纯文本指引）优化分析结果。
- **扁平结构项目**：`analyze_project.py` 会自动跳过 `scripts/`、`plugins/`、`docs/`、`tests/` 等非业务目录。如仍有误识别，可在 `.deepwiki/config.yaml` 的 `exclude` 中手动补充。

### 第 3 步：变更检测

> 完整规则（文件分类、模块关联、首次生成 vs 增量更新、反向依赖传播）见 [`references/step3-change-detection.md`](references/step3-change-detection.md)。

- 从**技能目录**运行 `python scripts/detect_changes.py <项目目录绝对路径>` 对比当前文件校验和与 `cache/checksums.json`。脚本运行后会**自动保存**当前校验和。
- 根据变更类型（新增/修改/删除）和模块映射，确定**需要深度阅读的模块列表**（含反向依赖传播）。

### 第 4 步：深度阅读源码

**首先读取 `cache/structure.json`**，获取第 2 步分析结果中的核心数据：

**插件缓存优先**：若 `.deepwiki/cache/api-analysis.json` 存在（由 `api-doc-enhancer` 插件在 `after_analyze` 阶段生成），优先读取其 `exports` 字段作为接口提取的基础，再进行语义补充，避免重复分析。

- **`core_files`**：所有 `importance_score >= 0.5` 的文件列表（已按评分降序排列）。这些是最值得分析的源文件。
- **`high_priority_files`**：所有 `importance_score >= 0.6` 的文件列表，用于关系分析和深度分析的精确过滤。
- **`modules`**：每个模块的 `importance_score`、`core_files` 列表和 `core_files_count`。
- **`file_types`**：扩展名 → 文件数，用于构建项目概览。
- **`directories`**：目录结构和重要性评分，用于理解项目布局。

**根据第 3 步变更检测结果，筛选待处理文件**：

- 首次生成（无变更记录）：处理所有模块的核心文件。
- 增量更新：仅处理变更文件所属模块的核心文件。对于被其他变更模块依赖的模块（反向依赖），也应纳入处理范围。

**预提取文档注释**：对每个待处理的核心文件，从**技能目录**运行 `python scripts/extract_docs.py <文件绝对路径>` 预提取结构化注释（函数签名、参数、返回值、类定义）。将提取结果作为语义分析的起点注入 `{{ EXTRACTED_DOCS }}` 变量，减少重复提取工作。若文件无文档注释则跳过。

> **文件角色分类规则**（双层分类：路径模式 + 语义推断）和**分档读取深度策略**（按 `complexity_score` 决定深度分析/标准分析/快速浏览）见 [`references/step4-source-analysis.md`](references/step4-source-analysis.md)。

**对每个文件进行语义分析**：
1. 按双层分类规则确定文件角色（`Entry`/`Service`/`Api`/`Dao` 等）
2. 理解语义：追踪函数调用、控制流、数据流、错误处理和设计模式
3. 提取公共接口、内部逻辑和模块依赖
4. 参考 `references/prompts.md` 获取分析提示词模板（代码深度分析 / 模块文档 / 依赖分析）
5. 为每个模块输出结构化分析结果，供第 5 步和第 8 步使用

### 第 5 步：依赖关系综合

> 完整规则（三阶段漏斗输入选择、6 种依赖类型表、AI 综合分析要点、RelationshipSummary 输出格式）见 [`references/step5-dependency-synthesis.md`](references/step5-dependency-synthesis.md)。

此步骤将孤立的文件分析转化为连贯的依赖图，输出结构化的 `RelationshipSummary`，供第 6 步 `architecture.md`、第 7 步 `doc-map.md` 和第 8 步各模块文档的依赖章节使用。

### 第 6 步：生成概览文档

应用 `before_generate` 钩子，先生成全局概览文档。这些文档不依赖具体模块的详细文档，基于第 2-5 步的分析结果即可产出：

| 文档 | 模板参考 | 内容要点 |
|------|---------|---------|
| `index.md` | `references/templates.md` → 首页 | 项目概述、技术栈徽章、快速导航、模块列表 |
| `architecture.md` | `references/templates.md` → 架构 | 系统架构图（Mermaid）、技术栈、模块依赖关系、架构分层（来自第 5 步输出） |
| `getting-started.md` | `references/templates.md` → 快速开始 | 前置条件、安装步骤、第一个示例、常见问题 |

> **概要上下文提取**：概览文档生成完毕后，从中提取一份精简的"项目上下文摘要"（约 1-3KB），包含：
> - 项目定位和技术栈（1-2 句）
> - 架构分层和各层职责（一句话/层）
> - 每个模块在架构中的角色和一句话描述
> 这份摘要将在第 8 步作为 subagent 的共享上下文注入，避免每个 subagent 重复读取完整概览文档。

每生成完一个文档即更新 `cache/progress.json` 的 `phases.overview.documents` 中对应文件的状态为 `completed` 或 `failed`，确保中断后可从断点恢复。阶段 6 完成后，更新 `phases.overview.status` 为 `completed`。

### 第 7 步：生成导航菜单与文档地图

基于第 6 步的概览文档和 `structure.json` 的模块列表，由 **AI 直接生成** `menu.json`（因为模块文档尚未生成，脚本无法扫描到不存在的文件）。

#### 7.1：AI 生成 menu.json

读取 `cache/structure.json` 中的模块列表（`modules` 字段），结合第 6 步概览文档中的架构分层，直接生成 `wiki/menu.json`。

> `menu.json` 结构模板和 AI 生成菜单的 5 条规则见 [`references/templates.md`](references/templates.md) → **menu.json 模板** 章节。

#### 7.2：AI 生成 doc-map.md

基于 `menu.json` 的导航结构和 `architecture.md` 的架构信息，生成 `wiki/doc-map.md`：

| 内容 | 数据来源 |
|------|---------|
| 文档关系图（Mermaid flowchart） | `menu.json` 层级结构 |
| 推荐阅读路径 | 按读者角色（新手/架构师/API 使用者） |
| 完整文档索引 | `structure.json` 模块列表 + `menu.json` |
| 模块间依赖矩阵 | 第 5 步 `core_dependencies` 输出 |

模板参考：`references/templates.md` → 文档地图。

更新 `cache/progress.json` 的 `phases.menu.status` 为 `completed`。

> **为什么要先于详细文档生成菜单**：菜单定义了每个模块文档在导航层级中的位置（所属分组、前后顺序）。详细文档生成时可以引用自身在菜单中的位置来生成精确的面包屑导航和前后文档链接，使文档网络更加连贯。

### 第 8 步：生成详细文档

参考 `references/templates.md` 中的模板，为每个模块生成详细文档：

| 文档 | 模板参考 | 内容要点 |
|------|---------|----------|
| `modules/<name>.md` | `references/templates.md` → 模块 | 模块职责、核心接口、设计模式、依赖关系、代码示例 |
| `api/<name>.md` | `references/templates.md` → API 参考 | 函数签名、类型定义、参数说明、返回值、使用示例 |

**模块生成顺序**：按第 2 步分析结果的 `importance_score` 降序排列，高优先级模块优先处理。

**增量更新**：仅重新生成第 3 步检测到有变更的模块文档（含反向依赖传播的模块）。未变更模块的现有文档保持不变。

#### 8.1：生成模块文档

无论使用 subagent 并行还是主 Agent 串行，每个模块的生成任务都接收以下统一上下文：

| 上下文 | 来源 | 用途 |
|--------|------|------|
| 项目上下文摘要 | 第 6 步产出 | 理解项目定位和技术栈 |
| 该模块的导航位置 | `menu.json` | 生成面包屑和前后导航链接 |
| 该模块的源码分析数据 | 第 4 步深度阅读结果 | 生成接口文档和代码示例 |
| 该模块的依赖关系 | 第 5 步输出 | 生成依赖关系章节 |
| 配置要求 | `config.yaml` | 语言、图表开关、源码链接等 |

> 并行/串行调度规则、批次控制、失败重试见 [`references/step8-execution-strategy.md`](references/step8-execution-strategy.md)。

#### 8.2：保存

- 将所有 wiki 文件写入 `.deepwiki/wiki/`。
- 更新 `meta.json` 的时间戳和每个模块的元数据。

#### 8.3：菜单校验（reconcile）

所有详细文档生成完毕后，从**技能目录**运行 `generate_menu.py --reconcile` 校验并修正 `menu.json`（详细行为规则见 [`references/system-reference.md`](references/system-reference.md) → reconcile 模式说明）：

```bash
python scripts/generate_menu.py <项目目录绝对路径>/.deepwiki/wiki [项目名称] --reconcile
```

应用 `after_generate` 插件钩子。应用 `on_export` 插件钩子（用于知识库导出、格式转换等后处理）。更新 `cache/progress.json` 的 `phases.details.status` 为 `completed`。

#### 8.4：文档质量检查

从**技能目录**运行质量检查，确认生成的文档符合质量标准（源码链接、Mermaid 图表、章节完整性）：

```bash
python scripts/check_quality.py <项目目录绝对路径>/.deepwiki
```

质量等级说明：

| 退出码 | 等级 | 含义 | 处理方式 |
|--------|------|------|----------|
| 0 | 全部 Professional / Standard | 达标 | 流程正常结束 |
| 1 | 存在 Basic 文档（占比 ≤50%） | 警告 | 告知用户；对 Basic 模块重新生成 |
| 2 | Basic 文档超过 50% | 严重 | 必须对所有 Basic 模块重新执行第 4 步起的子流程 |

**退出码 1 / 2 时的重新生成策略**（无需重新初始化或分析，直接从第 4 步继续）：

1. 加 `--verbose` 查看具体 Basic 文档的缺失项（源码链接、图表、章节数不足等）
2. 将这些模块在 `cache/progress.json` 中对应条目状态重置为 `pending`
3. **跳过第 1-3 步**，直接从**第 4 步**（深度阅读）重新执行 → 第 8.1 步（生成），仅针对 Basic 模块
4. 重新生成后再次运行 `check_quality.py` 确认达标
5. 若二次生成仍为 Basic，记录到 `meta.json` 的 `quality_issues` 字段并告知用户，不再强制重试

## 大型项目处理与降级策略

> 模块优先级排序、自动批次处理、断点续传、降级策略和知识库导出见 [`references/step8-execution-strategy.md`](references/step8-execution-strategy.md)。

- 模块超过 10 个时，按优先级分批处理（`core` > `api` > `module` > `utility` > `config` > `test`）
- subagent 可用时并行（每批 ≤ 3 个），不可用时自动降级为串行
- 失败模块自动降级读取深度重试一次，仍失败则记录到 `meta.json` 的 `failed_modules`
- 遇到任何异常（文件过大、接口缺失、图表复杂）均降级处理而非跳过
