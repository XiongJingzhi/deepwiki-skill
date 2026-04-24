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
│   ├── code-structure.json
│   ├── import-relations.json
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

## 插件协议

> 完整协议说明（钩子类型、加载流程、安全约束）见 [`references/plugin.md`](references/plugin.md)。

插件是**纯指令模式**，Agent 绝不能执行插件代码。加载流程：读取 `plugins/_registry.yaml` → 读取各插件 `PLUGIN.md` → 在对应工作流阶段应用钩子指引（`on_init` / `after_analyze` / `before_generate` / `after_generate` / `on_export`）。

## 脚本位置说明

所有 `scripts/` 脚本均位于 **DeepWiki 技能目录**（本 SKILL.md 所在目录），运行时需以技能目录为工作目录，将项目目录绝对路径作为参数传入。详见 [`references/system-reference.md`](references/system-reference.md)。

## 工作流（8 步）

### 第 1 步：初始化

检查 `.deepwiki/` 是否存在，运行初始化脚本，加载插件并注册钩子。

```bash
python scripts/init_wiki.py <项目目录绝对路径>          # 首次初始化
python scripts/init_wiki.py <项目目录绝对路径> --force  # 强制重建
```

> 完整流程（目录检查、插件加载、版本兼容性）见 [`references/step1-init.md`](references/step1-init.md)。

### 第 2 步：分析

检测技术栈、模块结构和入口文件，输出 `cache/structure.json`。

```bash
python scripts/analyze_project.py <项目目录绝对路径>
```

> 检测内容、扁平结构处理和 `after_analyze` 钩子见 [`references/step2-analyze.md`](references/step2-analyze.md)。

### 第 2.5 步：代码结构提取

从 `structure.json` 提取调用图、代码模式和关键时序，输出 `cache/code-structure.json`。

```bash
python scripts/extract_structure.py <项目目录绝对路径>
```

> 输出字段（`archetype` / `call_graph` / `patterns` / `key_sequences`）见 [`references/step2-analyze.md`](references/step2-analyze.md)。

### 第 3 步：变更检测

对比校验和，确定需要深度阅读的模块列表（含反向依赖传播），自动保存 `cache/checksums.json`。

```bash
python scripts/detect_changes.py <项目目录绝对路径>
```

> 文件分类、模块关联、首次生成 vs 增量更新、反向依赖传播见 [`references/step3-change-detection.md`](references/step3-change-detection.md)。

### 第 4 步：深度阅读源码

读取 `cache/structure.json` 和 `cache/code-structure.json`，按变更筛选文件，预提取文档注释，对每个文件进行语义分析，输出结构化分析结果。

```bash
python scripts/extract_docs.py <文件绝对路径>  # 预提取文档注释（逐文件运行）
```

> 字段用途、图表类型选择、分档读取深度、语义分析流程见 [`references/step4-source-analysis.md`](references/step4-source-analysis.md)。

> **并行调度**：模块总数 > 5 时，使用 subagent 并行批次（每批 3 个模块）。详见 [`references/step4-parallel-strategy.md`](references/step4-parallel-strategy.md)。

### 第 5 步：依赖关系综合

将孤立的文件分析转化为连贯的依赖图，输出结构化的 `RelationshipSummary`，供第 6、7、8 步使用。

> 三阶段漏斗输入选择、6 种依赖类型、AI 综合分析要点、输出格式见 [`references/step5-dependency-synthesis.md`](references/step5-dependency-synthesis.md)。

### 第 6 步：生成概览文档

应用 `before_generate` 钩子，生成 `overview.md`、`getting-started.md`，提取项目上下文摘要供第 8 步使用。

> 文档列表、模板参考、进度追踪、摘要提取见 [`references/step6-overview.md`](references/step6-overview.md)。

### 第 7 步：生成导航菜单与文档地图

基于 `structure.json` 模块列表和架构分层，AI 直接生成 `wiki/menu.json` 和 `wiki/doc-map.md`。

> 生成规则、`menu.json` 模板、`doc-map.md` 内容要求见 [`references/step7-menu-and-docmap.md`](references/step7-menu-and-docmap.md) 和 [`references/templates.md`](references/templates.md)。

### 第 8 步：生成详细文档

为每个模块生成 `modules/<name>.md` 和 `api/<name>.md`，完成后校验菜单，运行质量检查。

```bash
python scripts/generate_menu.py <项目目录绝对路径>/.deepwiki/wiki [项目名称] --reconcile
python scripts/fix_mermaid.py <项目目录绝对路径>/.deepwiki
python scripts/check_quality.py <项目目录绝对路径>/.deepwiki
```

> 统一上下文注入（8.1）、meta.json 更新（8.2）、菜单校验（8.3）、Mermaid 语法修复（8.4）、质量等级与重新生成策略（8.5）见 [`references/step8-execution-strategy.md`](references/step8-execution-strategy.md)。

> 模块优先级排序、并行/串行调度、失败重试、断点续传、降级策略和知识库导出见 [`references/step8-execution-strategy.md`](references/step8-execution-strategy.md)。
