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
- **全局架构骨架** -- 第 3.5 步生成轻量骨架，确保跨模块文档一致性
- **分析质量门控** -- 第 4.5 步零成本脚本检查，前置拦截低质量输入
- **架构图** -- 自动生成 Mermaid 依赖图、类图、序列图
- **代码链接** -- 文档代码块直接链接到源码对应行
- **多语言代码支持** -- 支持 TypeScript、Python、Go、Rust、Java、Kotlin 等
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

---

## 📁 输出结构

所有内容生成到 `.deepwiki/` 目录：

```
.deepwiki/
├── config.yaml                         # 配置文件
├── meta.json                           # 版本和模块元数据
├── cache/
│   ├── checksums.json                  # 增量变更校验和
│   ├── structure.json                  # 模块结构和技术栈
│   ├── file-hashes.json                # 文件哈希缓存（供增量更新复用）
│   ├── parse-results.json              # tree-sitter AST 摘要缓存
│   ├── code-structure.json             # 调用图、代码模式、关键时序、导入关系
│   ├── architecture-skeleton.json      # AI 生成的全局架构骨架
│   ├── module-analysis.json            # 语义分析结果（接口、洞察、组件）
│   ├── doc-topology.json               # 文档拓扑规划结果
│   ├── generation-plan.json            # 本轮文档编译计划
│   ├── evidence-index.json             # 关键结论到源码证据的索引
│   └── progress.json                   # 分阶段任务状态
└── wiki/
    ├── overview.md                     # 项目概览、架构图、模块列表
    ├── getting-started.md              # 快速开始、安装步骤、示例
    ├── doc-map.md                      # 文档关系图和阅读路径
    ├── menu.json                       # 层级化导航菜单
    ├── modules/                        # 每个模块的深度文档
    └── api/                            # 每个模块的 API 参考
```

> [!TIP]
> 建议将 `.deepwiki/` 添加到您的 `.gitignore` 文件中，以避免将生成的内容提交到代码仓库。

---

## 🏗️ 技能结构

```
deepwiki/
├── SKILL.md              # 主指令（9 步外部工作流）
├── scripts/              # Python 工具脚本
│   ├── init_wiki.py
│   ├── analyze_project.py
│   ├── extract_structure.py
│   ├── detect_changes.py
│   ├── plan_doc_topology.py
│   ├── build_evidence_index.py
│   ├── extract_doc_comments.py
│   ├── check_analysis_quality.py          # Step 4.5
│   ├── check_dependencies.py
│   ├── check_doc_quality.py
│   ├── check_cross_module_consistency.py
│   ├── cli.py                             # 本地统一入口
│   ├── generate_menu.py
│   ├── finalize.py                        # CLI: mermaid/quality/consistency
│   └── fix_mermaid.py
├── references/           # 工作流详细规则和提示词
├── schemas/              # JSON Schema 定义
├── assets/               # 配置模板
└── tests/                # 自动化测试套件
```

---

## 🔧 辅助脚本参考

> 所有脚本均从技能目录运行，项目目录绝对路径作为参数传入。

| 脚本 | 说明 |
|------|------|
| `scripts/cli.py <命令> <路径>` | 本地统一入口，封装 init/analyze/extract-structure/detect-changes/validate-analysis/plan-doc-topology/build-evidence-index/quality/self-check |
| `scripts/check_dependencies.py` | 检查 tree-sitter 与语言绑定等运行依赖 |
| `scripts/validate_skill.py [技能目录]` | 检查 skill 包元数据、关键文件、CLI 命令和已跟踪生成物 |
| `scripts/init_wiki.py <项目路径>` | 初始化 .deepwiki 目录 |
| `scripts/analyze_project.py <项目路径>` | 分析结构和技术栈 |
| `scripts/extract_structure.py <项目路径>` | 提取调用图、模式、导入关系 |
| `scripts/plan_doc_topology.py <项目路径>` | 生成 `doc-topology.json` 与 `generation-plan.json` |
| `scripts/detect_changes.py <项目路径>` | 增量变更检测 |
| `scripts/extract_doc_comments.py <文件路径>` | 从源码提取文档注释（tree-sitter） |
| `scripts/check_analysis_quality.py <项目路径>` | **Step 4.5**：分析质量门控 |
| `scripts/cli.py validate-analysis <项目路径>` | 对外推荐入口：运行分析质量门控，通过后构建 `evidence-index.json` |
| `scripts/build_evidence_index.py <项目路径>` | 从模块分析缓存生成 `evidence-index.json` |
| `scripts/finalize.py quality <.deepwiki路径>` | 文档质量检查 |
| `scripts/finalize.py consistency <.deepwiki路径>` | 跨模块一致性检查 |
| `scripts/finalize.py mermaid <.deepwiki路径>` | 修复 Mermaid 语法错误 |
| `scripts/generate_menu.py <wiki目录> [项目名]` | 生成 menu.json（支持 `--reconcile`） |

---

## ❓ 常见问题

<details open>
<summary><b>更新 DeepWiki 会删除已有的文档吗？</b></summary>

**不会。** 更新 DeepWiki 只会更新生成规则和模板，**不会**自动删除或修改任何已生成的文档。

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

<details open>
<summary><b>文档生成中途中断，可以续传吗？</b></summary>

**可以。** `cache/progress.json` 记录每个模块的处理状态（`pending / in_progress / completed / failed`），重新运行"更新 wiki"时 Agent 会自动从未完成的模块继续。

</details>
