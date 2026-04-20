---
name: deepwiki
description: 通过深度分析源代码、架构和模块依赖，自动生成结构化项目文档。Use when user requests "生成 wiki"、"创建文档"、"创建项目文档"、"更新 wiki"、"重建 wiki"、"检查 wiki 质量"、"升级文档". Also use when a project needs automated documentation generation from source code.
---

# DeepWiki

通过深度分析源代码、架构和模块依赖，自动生成结构化项目文档到 `.deepwiki/` 目录。

## 不适用场景

- 项目文件极少（< 5 个文件）时，手写文档更快
- 已有完善文档体系且不需要自动化更新时
- 仅需要单个函数/文件说明时（直接请 AI 解释即可）

## 文档质量标准

所有生成的文档必须满足以下标准：

- **源码追溯是强制要求**：每个章节末尾必须包含 `[filename](file:///path/to/file.ts#L1-L50)` 引用，方便读者跳转到对应源码。
- **每个模块文档至少包含 1 个 Mermaid 图表**。根据内容选择合适的图表类型：
  - `classDiagram` 用于类继承、接口和类型关系
  - `flowchart` 用于流程、工作流和架构概览
  - `sequenceDiagram` 用于交互、API 调用和组件间数据流
  - `stateDiagram` 用于状态机和生命周期转换
- **代码示例必须使用项目的主要语言**，完整且可运行（包含导入、初始化、调用和输出处理）。
- **文档间必须交叉链接**，方便读者在文档网络中导航。
- **内容应解释 WHY（为什么）和 HOW（如何实现）**，而不仅仅是 WHAT（是什么）。包含设计理由、权衡和上下文。
- 使用层级标题（H2/H3/H4）建立清晰的信息架构。
- 使用表格呈现 API、参数和配置选项，便于快速参考。
- 记录边界情况、警告和常见陷阱。

### 源码链接格式

每个章节末尾必须包含源码引用：

```markdown
**Section sources**
- [filename.ts](file:///path/to/file.ts#L1-L50)
- [another.ts](file:///path/to/another.ts#L20-L80)
```

代码块标题应包含内联源码链接：

```markdown
### `functionName` [源码](file:///path/to/file.ts#L42)
```

### Mermaid 图表选择指南

| 内容类型 | 推荐图表 | 使用场景 |
|---------|---------|---------|
| 类/接口层级 | `classDiagram` | 文档化 OOP 结构、类型关系、继承 |
| 流程/工作流 | `flowchart TB` | 逐步逻辑、请求处理、构建流水线 |
| 组件交互 | `sequenceDiagram` | API 调用序列、客户端-服务端通信、事件流 |
| 状态转换 | `stateDiagram-v2` | 连接生命周期、认证流程、表单验证状态 |
| 模块依赖 | `flowchart LR` | 导入关系图、服务依赖图 |
| 系统架构 | `flowchart TB` + subgraph | 带分组组件的高层系统概览 |

### 交叉链接要求

- 模块文档必须链接到：架构位置、API 参考、依赖模块。
- API 文档必须链接到：父模块文档、使用示例、相关类型定义。
- architecture.md 必须链接到：所有模块文档和文档地图。
- index.md 必须链接到：架构文档、快速开始和所有模块文档。

## 语言检测

生成文档前，从项目清单文件检测主要编程语言：

| 清单文件 | 对应语言 |
|---------|---------|
| `package.json` | JavaScript / TypeScript |
| `requirements.txt`、`pyproject.toml`、`setup.py` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml`、`build.gradle` | Java / Kotlin |
| `*.csproj` | C# |
| `Gemfile` | Ruby |
| `composer.json` | PHP |

使用检测到的语言编写所有代码示例、类型定义和 API 签名。如果项目是多语言混合的，以主导语言（源文件最多）编写示例，并在相关处注明其他语言。

- TypeScript 项目：包含类型注解、泛型和接口定义
- Python 项目：包含类型提示、docstring 和装饰器模式
- Go 项目：包含错误处理惯用写法和接口实现
- Rust 项目：包含所有权模式和 `Result`/`Option` 用法
- Java/Kotlin 项目：包含注解、泛型和设计模式示例
- C# 项目：包含特性、异步模式和接口实现

如果未找到清单文件，通过源文件扩展名推断主要语言：
- `.ts` / `.tsx` -> TypeScript
- `.js` / `.jsx` -> JavaScript
- `.py` -> Python
- `.go` -> Go
- `.rs` -> Rust
- `.java` / `.kt` -> Java / Kotlin
- `.cs` -> C#
- `.rb` -> Ruby
- `.php` -> PHP

支持的语言：TypeScript、JavaScript、Python、Go、Rust、Java、Kotlin、C#、Ruby、PHP。

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

- `config.yaml` -- 生成设置（语言、排除规则、功能开关）
- `meta.json` -- 生成器版本、时间戳、每个模块的元数据（质量等级、章节数、最后更新时间）
- `cache/checksums.json` -- 文件哈希值，用于增量变更检测
- `cache/structure.json` -- 解析后的项目结构（模块、入口点、技术栈）
- `cache/progress.json` -- 分阶段任务状态机（overview/menu/details 三阶段，每模块 pending/in_progress/completed/failed，含 subagent/serial 模式标记）
- `wiki/index.md` -- 项目首页，含概述、徽章、导航、快速开始
- `wiki/architecture.md` -- 系统架构图、技术栈、模块依赖
- `wiki/getting-started.md` -- 前置条件、安装、第一个示例
- `wiki/doc-map.md` -- 文档关系图、阅读路径、依赖矩阵（第 7 步基于 menu.json 生成）
- `wiki/menu.json` -- 层级化导航菜单（概览 → 模块 → 更多），自动由 `generate_menu.py` 生成
- `wiki/modules/` -- 每个项目模块一个文件，含深度分析
- `wiki/api/` -- 每个模块的 API 参考，含签名、类型和示例

## 插件协议

插件是**纯指令模式**。Agent **绝不能执行插件提供的代码、脚本或外部命令**。插件仅影响分析和文档的写作方式。

**钩子**（在工作流各阶段应用的文本指令）：
- `on_init` -- 分析开始前的指引
- `after_analyze` -- 分析项目结构后的指引
- `before_generate` -- 修改生成计划或提示词
- `after_generate` -- Wiki 创建后的后处理指引
- `on_export` -- 导出/格式化指引

**加载流程**：
1. 读取 `plugins/_registry.yaml` 查找已启用的插件。
2. 对于每个启用的插件，读取其 `PLUGIN.md` 了解钩子和指令。
3. 在对应的工作流阶段应用钩子指引。

**安全约束**：
- 不得运行插件脚本或二进制文件。
- 不得从网络获取或执行代码。
- `PLUGIN.md` 中的 CLI 命令仅供人工使用，Agent 不得执行。
- 通用技能（SKILL.md 文件）包装为插件后仍然是纯指令模式，不得作为代码执行。

> 插件是内置功能，不支持用户手动安装或升级。开发新插件请参考 `references/plugin-template.md` 中的格式规范。

## 脚本位置说明

> **重要**：本技能中所有 `scripts/` 脚本均位于 **DeepWiki 技能目录**（即本 `SKILL.md` 所在目录），而非当前项目目录。Agent 运行任何脚本时，需以**技能目录为工作目录**，并将**项目目录的绝对路径**作为参数传入。
>
> 技能目录可通过本文件加载时的路径推断（例如 `~/.agents/skills/deepwiki/`，实际以加载本 SKILL.md 的路径为准）。
>
> 调用示例（`$SKILL_DIR` = 技能目录，`$PROJECT_DIR` = 目标项目目录绝对路径）：
> ```bash
> cd $SKILL_DIR
> python scripts/init_wiki.py $PROJECT_DIR
> python scripts/analyze_project.py $PROJECT_DIR
> python scripts/detect_changes.py $PROJECT_DIR
> python scripts/check_quality.py $PROJECT_DIR/.deepwiki
> ```

## 工作流（8 步）

### 第 1 步：初始化

- 检查项目目录下 `.deepwiki/` 是否存在。
  - **不存在**：从**技能目录**运行 `python scripts/init_wiki.py <项目目录绝对路径>` 创建目录结构（`config.yaml`、`cache/`、`wiki/`）。
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

> 此步骤在分析之后、深度阅读之前执行。通过对比文件校验和确定哪些模块发生了变更，避免在未变更的模块上浪费 Token，使增量更新真正生效。

- 从**技能目录**运行 `python scripts/detect_changes.py <项目目录绝对路径>` 对比当前文件校验和与 `cache/checksums.json`。脚本运行后会**自动保存**当前校验和。
- 文件分类：
  - **新增文件** -> 排入完整文档生成队列
  - **修改文件** -> 排入文档更新队列
  - **删除文件** -> 将现有文档标记为废弃
- 根据 `cache/structure.json` 中的模块与文件映射，将变更文件关联到具体模块，确定**需要深度阅读的模块列表**。
- **首次生成**：`cache/checksums.json` 为空时，所有模块都排入完整文档生成队列，等效于全量生成。
- **增量更新**：仅对有文件变更的模块执行深度阅读和文档更新，显著节省大型项目的处理时间。
- **反向依赖传播**：脚本自动分析模块间的导入关系，当模块 A 变更时，将依赖 A 的其他模块也排入更新队列。输出 `affected_modules` 和 `reverse_affected_modules` 字段。

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

#### 文件角色分类（双层分类）

在读取每个文件之前，先按以下两层规则确定文件的角色标签，角色标签将用于生成文档时的针对性描述：

**第一层：路径/文件名模式快速分类**（优先，无需读文件内容）

| 角色标签 | 路径/文件名信号 | 示例 |
|---------|---------------|------|
| `Entry` | 文件名为 main、index、app、mod | `main.py`、`index.ts` |
| `Agent` | 路径或文件名含 `agent` | `src/agent/planner.ts` |
| `Page` | 路径含 `/pages/`、`/views/`、`/screens/` | `pages/home.tsx` |
| `Widget` | 路径含 `/components/`、`/widgets/`、`/ui/` | `components/Button.vue` |
| `Api` | 路径含 `/api/`、`/endpoint/`、`/controller/` | `api/user.ts` |
| `Service` | 路径或文件名含 `service` | `services/auth.ts` |
| `Dao` | 路径含 `/dao/`、`/repository/`、`/persistence/` | `dao/user.repo.ts` |
| `Model` | 路径含 `/models/`、`/entities/`、`/data/` | `models/user.ts` |
| `Config` | 路径含 `/config/`、文件名含 `config`、扩展名为 `.toml/.yaml/.env` | `config/database.yaml` |
| `Database` | 扩展名为 `.sql`、路径含 `/database/`、`/db/`、`/migrations/` | `migrations/001_init.sql` |
| `Util` | 路径含 `/utils/`、`/helpers/`、文件名含 `util`、`helper` | `utils/format.ts` |
| `Test` | 文件名含 `.test.`、`.spec.`、路径含 `/__tests__/` | `user.test.ts` |

**第二层：语义推断**（仅在第一层无法确定时使用，即标签为 `Other`/未知时）

当路径规则无法确定角色时，读取文件内容的前 1,000 字符，根据以下信号推断：
- 含大量 HTTP 路由注册（`app.get`、`router.post`、`@GetMapping`）→ `Api`
- 含数据库查询（`SELECT`、`.query(`、`ORM.find`）→ `Dao`
- 含 UI 渲染逻辑（`render(`、`return <`、`template:`）→ `Widget` 或 `Page`
- 含配置常量（大量 `const CONFIG_`、`env.`）→ `Config`

#### 分档读取深度

根据 `complexity_score` 和 `important_lines_count` 决定每个文件的分析深度，避免在低价值文件上浪费 Token：

| complexity_score | important_lines_count | 分析深度 | 操作 |
|-----------------|----------------------|---------|------|
| > 50 | 任意 | **深度分析** | 读取全文，追踪函数调用，提取完整接口表 |
| 20–50 | ≥ 10 | **标准分析** | 读取前 8,000 字节 + 所有重要代码行，提取主要接口 |
| 20–50 | < 10 | **快速浏览** | 读取前 3,000 字节，仅提取导出声明 |
| < 20 | 任意 | **快速浏览** | 读取前 2,000 字节，记录模块职责即可 |

> **重要行优先保留**：当文件需要截断时，优先保留含 `export`、`def`、`fn`、`class`、`import`、`interface`、`@decorator` 的行（即 `important_lines_count` 统计的行类型）。

**按以下优先级读取源文件**：

1. **入口文件优先**：先读取 `entry_points` 中的文件，理解项目启动流程。
2. **高优先级文件优先**：从 `high_priority_files` 列表（`importance_score >= 0.6`）按评分降序进行深度分析。
3. **核心文件次之**：从 `core_files` 列表中按 `importance_score` 降序读取，应用分档深度策略。
4. **模块内读取顺序**：对每个模块，先读其 `core_files` 中的文件，再读其他文件。

**对每个文件进行语义分析**：

1. **确定角色标签**：按双层分类规则确定文件角色（`Entry`/`Service`/`Api` 等）。
2. **理解语义**：分析代码的功能，而不仅仅是结构。追踪函数调用，理解控制流。
3. **提取详细信息**：
   - 公共接口（导出的函数、类、类型、常量）
   - 内部逻辑和控制流（函数如何组合、主要执行路径）
   - 数据流和状态管理（数据从哪里进入、转换、退出模块）
   - 错误处理模式（自定义错误类型、错误传播、恢复策略）
   - 使用的设计模式（工厂、观察者、策略、中间件链等）
4. **识别关系**：模块依赖（导入）、调用图、共享类型和跨模块数据流。
5. 参考 `references/prompts.md` 获取分析提示词模板：
   - 代码语义分析 → 使用"代码深度分析"模板
   - 准备生成模块文档时 → 使用"模块文档"模板
   - 生成 `index.md`/`getting-started.md` 时 → 直接参考 `references/templates.md` 对应模板
6. 为每个模块输出结构化分析结果，供第 5 步和第 8 步使用。

**技巧**：从模块的入口文件或桶文件（如 `index.ts`、`__init__.py`）开始了解公共接口，然后读取实现文件了解内部逻辑。对于大文件，先关注导出的符号（`important_lines`），再根据需要读取上下文。

### 第 5 步：依赖关系综合

> 此步骤在深度阅读源码之后执行。它将孤立的文件分析转化为连贯的依赖图，供 `architecture.md` 和各模块文档的依赖章节使用。

**输入选择（三阶段漏斗）**：

1. **按重要性排序** — 从 `high_priority_files`（`importance_score >= 0.6`）开始，再扩展到 `core_files`（`>= 0.5`）。
2. **阈值过滤** — 仅处理 `importance_score >= 0.6` 的文件进行关系分析，过滤低价值工具文件噪音。
3. **数量截断** — 最多处理 150 个文件，每个文件最多展示前 20 个依赖项（防止超大型项目的 Token 溢出）。

**依赖提取（静态层）**：

从第 4 步的语义分析结果中，提取每个文件已识别的 `import`/`use`/`require` 声明，构建有向依赖边：

| 依赖类型 | 语义含义 | 典型静态证据 |
|---------|---------|------------|
| `Import` | 模块/文件级导入 | `import`、`use`、`require` 语句 |
| `FunctionCall` | 运行时调用依赖 | 跨模块函数调用 |
| `Inheritance` | 类型层次关系 | `extends`、`implements`、子类模式 |
| `Composition` | Has-a 结构包含 | 字段引用、持有类型 |
| `DataFlow` | 组件间的数据传递 | API 载荷、共享状态、消息传递 |
| `Module` | 模糊依赖（兜底） | 当具体类型不明确时使用 |

**AI 综合分析**：

在静态提取的基础上，参考 `references/prompts.md` 中的"依赖关系分析"模板，综合推断：
- **核心模块间的依赖** → 生成有向依赖边列表
- **关键数据流** → 标记 `DataFlow` 类型的边
- **架构分层** → 将模块按层次归组（展示层 → 业务层 → 数据层 → 基础设施层）
- **潜在的循环依赖** → 以警告形式标记

**输出**：一份结构化的 `RelationshipSummary`，包含：
- `core_dependencies`：有向依赖边列表（from、to、type、importance 1-5）
- `architecture_layers`：模块分层分组
- `key_insights`：架构观察与循环依赖警告

此输出直接用于：
- `architecture.md`（第 6 步）的"模块依赖图"章节（Mermaid `flowchart LR`）
- `doc-map.md`（第 7 步）的"依赖矩阵"章节
- 各模块 `modules/<name>.md`（第 8 步）的"依赖关系"章节

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

读取 `cache/structure.json` 中的模块列表（`modules` 字段），结合第 6 步概览文档中的架构分层，直接生成 `wiki/menu.json`， 参考如下（不可简单照搬）：

```json
{
  "title": "项目名称",
  "version": "1.0",
  "generated_at": "2026-04-20T10:00:00Z",
  "planned": true,
  "menu": [
    {"title": "概览", "items": [
      {"title": "首页", "path": "index.md"},
      {"title": "快速开始", "path": "getting-started.md"},
      {"title": "架构文档", "path": "architecture.md"}
    ]},
    {"title": "核心", "items": [
      {"title": "core", "items": [
        {"title": "模块文档", "path": "modules/core.md", "planned": true},
        {"title": "API 参考", "path": "api/core.md", "planned": true}
      ]}
    ]},
    {"title": "功能", "items": [
      {"title": "auth", "items": [
        {"title": "模块文档", "path": "modules/auth.md", "planned": true},
        {"title": "API 参考", "path": "api/auth.md", "planned": true}
      ]}
    ]},
    {"title": "更多", "items": [
      {"title": "文档地图", "path": "doc-map.md", "planned": true}
    ]}
  ]
}
```

**AI 生成菜单时的规则**：

1. **分组依据架构分层**：参考第 5 步输出的 `architecture_layers`，将模块按架构层次（核心层、业务层、数据层、基础设施层）分组，而非简单地放在一个"模块"组里。每组的 `title` 应体现层次含义（如"核心"、"服务层"、"数据访问"、"基础设施"）。
2. **组内按重要性排序**：同组内模块按 `importance_score` 降序排列。
3. **每个模块条目预设路径**：`modules/<name>.md` + `api/<name>.md`，标记 `"planned": true` 表示文件尚未生成。
4. **跳过不生成文档的模块**：如果 `config.yaml` 中有排除规则或模块类型为 `test`/`config` 且无代码文件，不放入菜单。
5. **`"planned": true` 标记**：顶部 `planned: true` 表示这是规划阶段菜单，步骤 8 完成后由脚本校验并移除此标记。

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

#### 7.2：生成 doc-map.md

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
|------|---------|---------|
| `modules/<name>.md` | `references/templates.md` → 模块 | 模块职责、核心接口、设计模式、依赖关系、代码示例 |
| `api/<name>.md` | `references/templates.md` → API 参考 | 函数签名、类型定义、参数说明、返回值、使用示例 |

**模块生成顺序**：按第 2 步分析结果的 `importance_score` 降序排列，高优先级模块优先处理。

**增量更新**：仅重新生成第 3 步检测到有变更的模块文档（含反向依赖传播的模块）。未变更模块的现有文档保持不变。

#### 每个 subagent 的输入上下文

无论使用 subagent 并行还是主 Agent 串行，每个模块的生成任务都接收以下统一上下文：

| 上下文 | 来源 | 用途 |
|--------|------|------|
| 项目上下文摘要 | 第 6 步产出 | 理解项目定位和技术栈 |
| 该模块的导航位置 | `menu.json` | 生成面包屑和前后导航链接 |
| 该模块的源码分析数据 | 第 4 步深度阅读结果 | 生成接口文档和代码示例 |
| 该模块的依赖关系 | 第 5 步输出 | 生成依赖关系章节 |
| 配置要求 | `config.yaml` | 语言、图表开关、源码链接等 |

#### 并行策略（subagent 可用时）

当运行环境支持 subagent 时，按模块分派 subagent 并行生成详细文档：

- **并行粒度**：每个 subagent 负责一个模块的 `modules/<name>.md` + `api/<name>.md`（同一模块的文档必须一起生成，保证交叉引用一致性）。
- **批次控制**：同批次内启动的 subagent 数量不超过 3 个，避免并发过高导致输出质量下降。
- **批次调度**：按模块优先级排序，每批从队列头部取 3 个无依赖关系的模块分派 subagent。同批次内所有 subagent 完成后，再启动下一批。
- **进度追踪**：每个 subagent 的状态记录在 `cache/progress.json` 的 `phases.details.modules` 中。

```json
{
  "phases": {
    "details": {
      "status": "in_progress",
      "modules": {
        "core": {"status": "completed", "agent": "main"},
        "auth": {"status": "in_progress", "agent": "subagent-1"},
        "utils": {"status": "in_progress", "agent": "subagent-2"},
        "db": {"status": "pending"}
      }
    }
  }
}
```

`agent` 字段：`"main"` 表示主 Agent 生成，`"subagent-N"` 表示第 N 个 subagent 生成。

#### 串行降级（subagent 不可用时）

当运行环境不支持 subagent（如无 Agent 工具权限、上下文过小、或 subagent 启动失败）时，自动降级为主 Agent 串行处理：

- **降级触发条件**：subagent 启动失败、subagent 输出质量不达标（生成的文档缺少源码追溯或章节数不足）、或运行环境不提供 subagent 能力。
- **串行策略**：恢复原有的批次处理机制，每批 1-2 个模块，主 Agent 按优先级顺序依次处理。
- **批次间保存进度**：每批完成后更新 `cache/progress.json`，确保中断后可从断点恢复。
- **无需用户干预**：降级是自动的、静默的，用户无需配置。

> **注意**：即使降级为串行，新的 8 步流程仍然优于原来的 7 步流程——因为概览文档和导航菜单在详细文档之前就已生成，详细文档可以引用精确的导航位置和架构上下文。

#### 失败重试（带自动降级）

无论并行还是串行，失败模块的处理策略一致：

1. 将失败模块在 `cache/progress.json` 中的状态标记为 `failed`，记录 `error` 字段。
2. 继续处理下一个模块，不中断流程。
3. 所有模块处理完毕后，扫描 `failed` 状态的模块，进行一轮重试（最多重试 1 次）。
4. **重试时自动降级读取深度**：
   - 将该模块所有文件的读取深度降低一档（深度分析 → 标准分析 → 快速浏览）
   - 生成简版文档：跳过条件章节，仅保留概述 + 公开接口 + 1 个基础示例
5. 重试仍失败的模块记录到 `meta.json` 的 `failed_modules` 字段。

#### 保存

- 将所有 wiki 文件写入 `.deepwiki/wiki/`。
- 更新 `meta.json` 的时间戳和每个模块的元数据。

#### 8.3：菜单校验（reconcile）

所有详细文档生成完毕后，从**技能目录**运行：

```bash
python scripts/generate_menu.py <项目目录绝对路径>/.deepwiki/wiki [项目名称] --reconcile
```

`--reconcile` 模式会：
1. 读取已有的 `menu.json`（步骤 7 生成的规划菜单）
2. 扫描 `wiki/` 目录下的实际文件
3. **校验并修正**：
   - 用实际文件的 H1 标题替换预设的模块名称
   - 将 `"planned": true` 标记移除（文档已实际生成）
   - 移除规划中存在但实际未生成文档的模块条目
   - 补充实际生成但规划中遗漏的文件（如插件产出的额外文档）
4. 输出校验报告：新增/移除/修改的条目数量

```bash
# 基本校验（仅当有差异时输出）
python scripts/generate_menu.py /path/to/.deepwiki/wiki "项目名称" --reconcile

# 详细输出
python scripts/generate_menu.py /path/to/.deepwiki/wiki "项目名称" --reconcile --verbose
```

应用 `after_generate` 插件钩子。更新 `cache/progress.json` 的 `phases.details.status` 为 `completed`。

## 大型项目处理

对于模块超过 10 个的项目，使用渐进式批次处理以确保完整覆盖和一致的质量。**全部自动执行，不需要用户确认。**

### 模块优先级排序

生成前对模块进行排序，高优先级模块优先处理：

| 优先级 | 类别 | 示例 | 原因 |
|-------|------|------|------|
| 1（最高） | `core` | 入口点、框架代码、被大量依赖 | 理解其余部分的基础 |
| 2 | `api` | 公共接口、客户端库、SDK | 外部消费者交互的对象 |
| 3 | `module` | 功能模块、业务逻辑 | 项目的主要功能 |
| 4 | `utility` | 工具、共享代码、通用类型 | 支撑基础设施 |
| 5 | `config` | 配置、常量、环境设置 | 需要的上下文但非核心逻辑 |
| 6（最低） | `test` | 测试基础设施、夹具、测试工具 | 理解测试是次要的 |

### 自动批次处理（第 8 步详细展开）

1. **subagent 并行（首选）**：每批最多 3 个无依赖关系的模块，各由一个 subagent 独立生成。同批次全部完成后启动下一批。
2. **串行降级（备选）**：subagent 不可用时，每批 1-2 个模块，主 Agent 依次处理。
3. **进度保存**：每批完成后更新 `cache/progress.json`：
   ```json
   {
     "last_updated": "2026-04-20T10:00:00Z",
     "phases": {
       "overview": {"status": "completed"},
       "menu": {"status": "completed"},
       "details": {
         "status": "in_progress",
         "mode": "subagent",
         "modules": {
           "core": {"status": "completed", "agent": "subagent-1"},
           "utils": {"status": "completed", "agent": "subagent-1"},
           "api": {"status": "completed", "agent": "subagent-2"},
           "auth": {"status": "in_progress", "agent": "subagent-3"},
           "db": {"status": "pending"}
         }
       }
     }
   }
   ```
   每个模块的状态值：`pending` → `in_progress` → `completed` / `failed`。`mode` 字段标记当前批次模式：`"subagent"` 或 `"serial"`。
   阶段级 `status` 汇总所有子项状态：全部 `completed` 时为 `completed`，存在 `in_progress` 时为 `in_progress`，存在 `failed` 且无 `in_progress` 时为 `failed`。
4. **自动继续**下一批，不暂停，直到所有模块都有文档。
5. **失败重试（带自动降级）**：全部模块处理完毕后，扫描 `failed` 状态的模块，进行一轮重试。重试时**自动降级读取深度**以提高成功率：
   - 将失败模块的文件读取深度降低一档（深度分析 → 标准分析 → 快速浏览）
   - 生成简版文档：跳过条件章节，仅保留概述 + 公开接口 + 1 个基础示例
   - 重试仍失败的模块记录到 `meta.json` 的 `failed_modules` 字段，并在总结报告中说明原因
6. **全部完成后**输出总结报告：已生成文档总数、质量检查结果、遇到的问题、使用模式（subagent/serial）。
7. **断点续传**：如果因上下文限制或错误中断，下次运行时自动读取 `cache/progress.json`，跳过已完成模块，从中断处继续。

## 知识库导出

生成的输出是自带嵌入式 Mermaid 图表的 Markdown 格式，可直接上传到知识库平台：

当目标平台不支持 Mermaid 图表时，在每个图表块下方附带纯文本描述作为备选，确保信息不丢失。

备选模式示例：

````markdown
```mermaid
flowchart LR
  A[Client] --> B[API Server]
  B --> C[Database]
```

<!-- 备选说明：Client 发送请求到 API Server，API Server 查询 Database。 -->
````

## 质量检查

从**技能目录**运行 `python scripts/check_quality.py` 验证生成的文档质量（需传入项目的 `.deepwiki` 目录绝对路径）：

```bash
# 切换到技能目录（$SKILL_DIR 为本 SKILL.md 所在目录）
cd $SKILL_DIR

# 基本检查
python scripts/check_quality.py /path/to/project/.deepwiki

# 详细报告
python scripts/check_quality.py /path/to/project/.deepwiki --verbose

# 导出 JSON 报告
python scripts/check_quality.py /path/to/project/.deepwiki --json report.json
```

检查项目：
- 每个文档的最低行数
- 每个模块文档的最低章节数
- Mermaid 图表是否存在
- 代码示例是否存在
- 源码追溯（Section sources 是否存在）
- 交叉链接是否存在

> **质量等级说明**：`check_quality.py` 基于行数、章节数、图表和示例综合评分得出 `basic/standard/professional` 三级，与插件内部的 API 文档质量评级相互独立，可能出现不同结果属正常情况。

> **性能提示**：`code-complexity` 和 `repo-analytics` 插件会遍历所有源文件，增加分析时间。对于小型项目，可在 `plugins/_registry.yaml` 中设置 `enabled: false` 按需关闭。

## 降级策略

当信息不足或遇到特殊情况时，**不要跳过文档生成**，而要按以下策略降级处理，确保流水线始终能产出可用输出：

| 情况 | 降级行为 | 说明 |
|------|---------|------|
| 文件超过 `max_file_size` | 生成"概述 + 入口点清单"占位文档 | 记录文件路径、大小、已识别的导出符号，标注"内容过大，需手动补充" |
| 文件接口信息不足（无导出/无函数） | 生成"概述 + 文件结构"简版文档 | 2-3 段描述文件职责，附文件大小和复杂度信息，跳过接口表格 |
| Mermaid 图表语法复杂难以生成 | 退化为表格形式的依赖说明 | 用表格替代 `flowchart` 图，在末尾注明"图表因复杂度降级为表格" |
| 源码链接无法确定行号 | 仅链接到文件，不指定行号 | 使用 `file:///path/to/file.ts` 而非 `#L42` 形式 |
| 模块依赖关系无法推断 | 仅记录静态导入，不推断语义 | 列出文件头部的 import 语句，标注"语义依赖关系待分析" |
| 文档生成中途中断（大型项目） | 保存已完成部分，记录断点 | 写入 `cache/progress.json`，下次运行自动从断点继续 |
| subagent 启动失败或输出质量不达标 | 降级为主 Agent 串行处理 | 自动切换到串行模式，进度文件记录 `mode: "serial"` |

> **核心原则（参考 deepwiki-rs 的韧性设计）**：降级不是失败，而是保证流水线不崩溃的安全网。一个有占位内容的 `basic` 级文档，远比完全缺失的文档更有价值，因为它可以通过 `升级 <模块> 文档` 命令随时升级。

## 增量更新命令

用户可触发特定的更新操作：

| 命令 | 操作 |
|------|------|
| `生成 wiki` / `创建文档` | 自动完整生成 -- 分析所有模块并生成完整文档 |
| `更新 wiki` / `重建 wiki` | 重新分析并重新生成所有文档 |
| `检查 wiki 质量` | 运行质量检查并显示报告 |
| `升级 <模块> 文档` | 重新生成特定模块的文档 |

> 所有命令均执行完整的 8 步工作流；区别在于第 3 步变更检测的范围：
> "生成/创建" = 首次生成，checksums 为空，等效全量处理所有模块；"更新/重建" = checksums 存在，仅处理变更模块（含反向依赖传播）。

## 配置

初始化时，`scripts/init_wiki.py` 会将 `assets/config.yaml` 作为模板写入项目的 `.deepwiki/config.yaml`。

> **完整配置格式与所有可用选项请参阅 [`assets/config.yaml`](assets/config.yaml)**，该文件是配置的权威来源。

主要配置项说明：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `generation.language` | `zh` | 文档语言：`zh` / `en` / `both` |
| `generation.include_diagrams` | `true` | 是否生成 Mermaid 图表 |
| `generation.include_examples` | `true` | 是否包含代码示例 |
| `generation.link_to_source` | `true` | 是否添加 `file:///` 源码链接 |
| `generation.max_file_size` | `100000` | 跳过超过此大小（字节）的文件 |
| `exclude` | 见 `assets/config.yaml` | 排除目录/文件列表，已预设所有支持语言的依赖目录，可在末尾追加项目特有规则 |

## 脚本参考

> **注意**：所有脚本均位于 **DeepWiki 技能目录**（本 SKILL.md 所在目录）的 `scripts/` 子目录下，需从技能目录运行，项目路径作为参数传入。

| 脚本 | 用途 |
|------|------|
| `scripts/init_wiki.py <项目路径>` | 初始化 .deepwiki 目录 |
| `scripts/analyze_project.py <项目路径>` | 分析项目结构和技术栈 |
| `scripts/detect_changes.py <项目路径>` | 检测文件变更，用于增量更新（含反向依赖传播） |
| `scripts/extract_docs.py <文件路径>` | 从源码提取文档注释 |
| `scripts/check_quality.py <.deepwiki路径>` | 检查文档质量（含源码链接有效性验证） |
| `scripts/generate_menu.py <wiki目录路径> [项目名称]` | 生成层级化导航菜单 menu.json（支持 `--reconcile` 校验模式） |
| `scripts/plugin_manager.py` | 管理插件 |

使用示例（请将 `$SKILL_DIR` 替换为本 SKILL.md 所在的实际目录）：

```bash
# 切换到技能目录
cd $SKILL_DIR

# 初始化新 wiki（$PROJECT_DIR 为目标项目的绝对路径）
python scripts/init_wiki.py $PROJECT_DIR

# 分析项目结构
python scripts/analyze_project.py $PROJECT_DIR

# 检测文件变更
python scripts/detect_changes.py $PROJECT_DIR

# 提取源码注释
python scripts/extract_docs.py /path/to/src/utils.ts

# 检查文档质量
python scripts/check_quality.py $PROJECT_DIR/.deepwiki

# 生成导航菜单
python scripts/generate_menu.py $PROJECT_DIR/.deepwiki/wiki "项目名称"

# Reconcile 模式：步骤 8 完成后校验并修正菜单
python scripts/generate_menu.py $PROJECT_DIR/.deepwiki/wiki "项目名称" --reconcile --verbose

# 列出已安装插件
python scripts/plugin_manager.py list
```

## 参考资料

`references/` 目录下提供了详细的模板和提示词：

- `references/prompts.md` -- AI 提示词模板（代码分析、模块文档、架构文档、API 参考、首页、文档地图）
- `references/templates.md` -- Wiki 页面模板，含 Mermaid 图表（首页、架构、模块、API 参考、快速开始、文档地图）
- `references/plugin-template.md` -- 插件格式规范（PLUGIN.md 结构、钩子定义、注册表格式）
