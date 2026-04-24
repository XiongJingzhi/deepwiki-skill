# Getting Started 生成指南

> **适用工具：** `generate-overview`
> **关联规则：** `../rules/quality-standards.md`、`../rules/components.md`

---

## 生成指导

## 首页与快速开始

> `index.md` 和 `getting-started.md` 参考 `templates.md` 中的骨架模板生成。

**生成建议**：
- `index.md`：从 README.md 提取项目简介、核心特性和架构预览。
- `getting-started.md`：从 README 的安装章节和入口文件提取前置条件、安装步骤和最小可运行示例。

---

## 置信度标注规范

> **核心原则**：让 AI 对每条断言标注"证据来源"和"置信度"，区分事实与推断。

### 置信度等级定义

| 等级 | 符号 | 定义 | 证据来源 |
|------|------|------|---------|
| **高置信** | 🟢 | 断言直接来自源码或文档注释 | 源码行号、docstring、JSDoc |
| **中置信** | 🟡 | 断言从代码结构推断 | 类继承关系、方法签名、导入语句 |
| **低置信** | 🔴 | 断言从命名约定或常见模式推断 | 变量名、文件名、目录结构 |

### 标注规则

**规则 1：高置信断言必须附带源码引用**

**规则 2：中置信断言必须说明推断依据**

**规则 3：低置信断言必须标注"待确认"**

**规则 4：禁止无证据来源的高置信断言**

---

## Archetype 感知：差异化章节模板

根据 `cache/code-structure.json` 中的 `archetype` 字段，差异化"基本用法"章节的内容侧重和额外必需章节：

| Archetype | "基本用法"章节重点 | 额外必需章节 |
|-----------|----------------|------------|
| `sdk-library` | install → import → 调用核心 API → 查看输出 | **集成指南**（如何添加到已有项目、框架兼容性） |
| `agent-project` | 配置 LLM provider → 创建 Agent → 发送首条消息 | **配置说明**（API Key、工具注册、记忆后端） |
| `fullstack-framework` | scaffolding → 创建第一个路由 → 启动开发服务器 | **项目结构说明**（约定目录和命名规范） |
| `cli-tool` | 安装 → 运行 `--help` → 执行核心命令 | **配置文件说明**（配置文件位置和基本选项） |
| `ml-project` | 数据准备 → 训练 → 推理最小示例 | **环境依赖说明**（CUDA版本、数据集格式） |
| `spa-frontend` | clone → install → `npm run dev` → 访问首页 | **环境变量说明**（API 地址、认证配置） |
| `web-service` | 启动服务 → 调用第一个端点 → 查看响应 | **数据库初始化**（migrate 命令和初始数据） |
| `monorepo` | clone → install → 运行某个 package | **工作区命令速查**（如何只构建/测试某个 package） |
| `generic` | 使用通用模板（与现有骨架相同） | 无额外要求 |

---

## 页面骨架

## 快速开始骨架

```markdown
# 快速开始

> 在几分钟内启动并运行 {PROJECT_NAME}

---

## 前置条件

[api-table 变体：依赖表格]

---

## 安装

### 通过包管理器安装（推荐）

[code-example 组件：安装命令]

### 从源码安装

[code-example 组件：克隆 + 构建]

### 验证安装

[code-example 组件：版本检查]

---

## 基本用法

<!-- archetype 感知：根据上方"Archetype 感知章节差异"表格选择对应模板 -->
[code-example 组件：最小可运行示例（内容依 archetype 差异化）]

<!-- 条件章节：根据 archetype 生成对应的额外必需章节（见上方表格的"额外必需章节"列） -->
[对应 archetype 的额外必需章节（generic 时跳过）]

---

## 下一步

[nav-links 组件：指向相关文档]

---

## 常见问题

[Q&A 格式：安装问题、配置问题]
```

---
