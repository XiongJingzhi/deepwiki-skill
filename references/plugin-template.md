# 插件模板

本文档描述创建 DeepWiki 插件的 PLUGIN.md 格式。

## 安全说明

插件是**纯指令模式**。不要包含需要执行代码、脚本或外部命令的步骤。任何 CLI 命令仅供**人工**使用，Agent 不得执行。

## PLUGIN.md 格式

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
  - on_init              # Run on initialization
  - after_analyze        # Run after project analysis
  - before_generate      # Run before content generation
  - after_generate       # Run after content generation
  - on_export            # Run on export
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

## 插件类型

| Type | Description |
|------|-------------|
| `analyzer` | Enhance project analysis (e.g., code complexity) |
| `generator` | Add new doc types (e.g., API docs) |
| `integrator` | External integrations (e.g., GitHub) |
| `enhancer` | Improve existing features |

## 可用钩子

| Hook | Timing | Use Case |
|------|--------|----------|
| `on_init` | 初始化时 | Setup plugin resources |
| `after_analyze` | 分析后 | Add analysis data |
| `before_generate` | 生成前 | Modify prompts/templates |
| `after_generate` | 生成后 | Post-process output |
| `on_export` | 导出时 | Convert to other formats |

## 目录结构

```
your-plugin/
├── PLUGIN.md         # Plugin manifest (required)
├── scripts/             # Plugin scripts (optional)
│   └── your_script.py
├── references/          # Reference docs (optional)
└── assets/              # Assets (optional)
```

> Plugins should focus on source code analysis and documentation quality. Output format conversion plugins are not recommended.
