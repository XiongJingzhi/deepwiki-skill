## DeepWiki 是什么

DeepWiki 是一个 [skills.sh](https://skills.sh) 兼容的技能包，让 AI Agent 能够**深度分析你的源代码**，生成**专业级**的结构化文档，包含图表、交叉链接和详细说明。

**使用 DeepWiki 之前：**
- 手写文档很耗时
- 文档很快就过时
- 没有架构图
- 代码引用断开

**使用 DeepWiki 之后：**
- AI 自动生成专业级文档
- 增量更新保持新鲜
- 自动生成 Mermaid 架构图、数据流图、依赖图
- 代码块直接链接到源码
- 深度源代码分析，生成详细内容
- 文档间交叉链接，形成文档网络

---

## 特性

- **智能项目分析** -- 支持 Monorepo、Rust、Go、Python、Node 等深度分析
- **增量更新** -- 仅更新变更文件的文档，节省时间
- **架构图** -- 自动生成 Mermaid 依赖图、类图、序列图
- **代码链接** -- 文档代码块直接链接到源码对应行
- **多语言代码支持** -- 支持 TypeScript、Python、Go、Rust、Java、C# 等
- **知识库导出** -- 输出适合 Confluence、Notion、GitBook 上传的 Markdown

---

## 🚀 快速开始

### 安装

选择你喜欢的方式：

<details open>
<summary><b>📦 美的skill广场下载安装 </b></summary>
</details>


### 使用

安装后，对 AI Agent 说：

```
🤖 "生成 wiki"
🤖 "创建项目文档"
🤖 "更新 wiki"
```

### 插件命令

```bash
# 自然语言指令
📋 "列出插件"
📦 "安装插件 <source>"
📦 "安装 <owner/repo>"  (GitHub 简写)
🔄 "更新插件 <name>"
✅ "启用插件 <name>"
❌ "禁用插件 <name>"

# 命令行高级用法
python scripts/plugin_manager.py list
python scripts/plugin_manager.py install <source>
python scripts/plugin_manager.py update <name>
python scripts/plugin_manager.py enable <name>
```

**安装来源:**
- **GitHub**: `owner/repo` (例如 `vercel-labs/agent-skills`)
- **URL**: `https://example.com/plugin.zip`
- **本地**: `./plugins/my-plugin`

### 插件工作原理

DeepWiki 采用 **指令型插件系统**。当你运行任务时：
1. AI 读取 `plugins/_registry.yaml`
2. AI 读取启用插件的 `PLUGIN.md` 指令
3. AI 在特定的 **Hooks**（如 `before_generate`, `on_export`）**应用插件指令（仅文本）**

**执行模型（安全说明）**：
- 插件为**纯指令**，Agent **不会执行**插件代码或脚本。
- `PLUGIN.md` 中的 CLI 命令仅供人工操作，Agent 不应执行。

### 内置插件

- `code-complexity`: 代码健康度与复杂度分析
- `repo-analytics`: 多维度 Git 分析与健康度评分
- `api-doc-enhancer`: 深度语义 API 文档生成
- `changelog-generator`: 从 Git 生成变更日志

---

## 📁 输出结构

所有内容生成到 `.deepwiki/` 目录：

```
.deepwiki/
├── 📄 config.yaml           # 配置文件
├── 📂 cache/                 # 增量缓存
└── 📂 wiki/                  # Wiki 内容
    ├── index.md
    ├── architecture.md
    ├── modules/
    └── api/
```

> [!TIP]
> 建议将 `.deepwiki/` 添加到您的 `.gitignore` 文件中，以避免将生成的内容提交到代码仓库。

---

## 🏗️ 技能结构

```
deepwiki/
├── 📄 SKILL.md              # 主指令（英文）
├── 📂 scripts/              # Python 工具脚本
├── 📂 references/           # 提示词、模板、国际化
├── 📂 assets/               # 配置模板
└── 📂 plugins/              # 插件目录
    └── _registry.yaml
```

---

## ❓ 常见问题

<details open>
<summary><b>更新 DeepWiki 会删除已有的文档吗？</b></summary>

**不会。** 更新 DeepWiki 只会更新生成规则和模板，**不会**自动删除或修改任何已生成的文档。

```bash
npx skills update trsoliu/deepwiki  # 只更新 DeepWiki 代码
```

</details>

<details open>
<summary><b>如何检查现有文档的质量？</b></summary>

告诉你的 AI Agent：

```
🤖 "检查 wiki 质量"
🤖 "check wiki quality"
```

这会生成一份质量评估报告，显示哪些文档需要升级。

</details>
