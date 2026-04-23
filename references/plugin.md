# 插件系统

> 本文档涵盖两部分：插件协议（钩子、加载流程、安全约束），以及开发新插件时的 PLUGIN.md 格式规范。

## 插件协议

插件是**纯指令模式**。Agent **绝不能执行插件提供的代码、脚本或外部命令**。插件仅影响分析和文档的写作方式。

### 钩子（Hooks）

在工作流各阶段应用的文本指令：

| 钩子 | 触发时机 |
|------|---------|
| `on_init` | 分析开始前 |
| `after_analyze` | 分析项目结构后 |
| `before_generate` | 修改生成计划或提示词 |
| `after_generate` | Wiki 创建后的后处理 |
| `on_export` | 导出/格式化阶段 |

### 加载流程

1. 读取 `plugins/_registry.yaml` 查找已启用的插件。
2. 对于每个启用的插件，读取其 `PLUGIN.md` 了解钩子和指令。
3. 对比每个插件的 `min_version` 与 `meta.json` 的 `version` 字段，跳过不兼容的插件并记录警告。
4. 在对应的工作流阶段应用钩子指引。

### 安全约束

- 不得运行插件脚本或二进制文件。
- 不得从网络获取或执行代码。
- `PLUGIN.md` 中的 CLI 命令仅供人工使用，Agent 不得执行。
- 通用技能（SKILL.md 文件）包装为插件后仍然是纯指令模式，不得作为代码执行。

> 插件是内置功能，不支持用户手动安装或升级。

## 开发新插件（PLUGIN.md 格式）

### 安全说明

插件是**纯指令模式**。不要包含需要执行代码、脚本或外部命令的步骤。任何 CLI 命令仅供**人工**使用，Agent 不得执行。

### PLUGIN.md 格式模板

```yaml
---
name: plugin-name
type: generator          # analyzer | generator | integrator | enhancer
version: 1.0.0
description: Short description of what this plugin does
author: Your Name
requires:
  - deepwiki >= 2.0.0
hooks:
  - on_init
  - after_analyze
  - before_generate
  - after_generate
  - on_export
---

# Plugin Name

Description of the plugin.

## What it does

Explain the functionality.

## How to use

Instructions for using this plugin.

## Hooks

### on_init
What happens during initialization.

### after_analyze
What this hook adds to the analysis.

## Configuration

Any configuration options.
```

### 插件类型

| 类型 | 说明 |
|------|------|
| `analyzer` | 增强项目分析（如代码复杂度分析） |
| `generator` | 新增文档类型（如 API 文档） |
| `integrator` | 外部集成（如 GitHub） |
| `enhancer` | 改善现有功能 |

### 可用钩子

| 钩子 | 触发时机 | 典型用途 |
|------|---------|---------|
| `on_init` | 初始化时 | 初始化插件资源 |
| `after_analyze` | 分析后 | 补充分析数据 |
| `before_generate` | 生成前 | 修改提示词/模板 |
| `after_generate` | 生成后 | 后处理输出 |
| `on_export` | 导出时 | 格式转换 |

### 目录结构

```
your-plugin/
├── PLUGIN.md         # 插件清单（必须）
├── scripts/          # 插件脚本（可选，仅供人工执行）
│   └── your_script.py
├── references/       # 参考文档（可选）
└── assets/           # 资源文件（可选）
```
