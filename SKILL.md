---
name: deepwiki
description: >-
  Use when user requests "生成 wiki"、"创建文档"、"创建项目文档"、"更新 wiki"、"重建 wiki"、
  "检查 wiki 质量"、"升级文档".
  Also use when a project needs automated documentation generation from source code.
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
- `cache/progress.json` -- 大型项目的批次处理状态
- `wiki/index.md` -- 项目首页，含概述、徽章、导航、快速开始
- `wiki/architecture.md` -- 系统架构图、技术栈、模块依赖
- `wiki/getting-started.md` -- 前置条件、安装、第一个示例
- `wiki/doc-map.md` -- 文档关系图、阅读路径、依赖矩阵
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

## 5 步工作流

### 第 1 步：初始化

- 检查 `.deepwiki/` 是否存在。
  - **不存在**：运行 `scripts/init_wiki.py` 创建目录结构（`config.yaml`、`cache/`、`wiki/`）。
  - **已存在**：读取 `config.yaml` 和 `cache/structure.json` 获取增量更新上下文。检查 `meta.json` 的版本兼容性。
- 从 `plugins/_registry.yaml` 加载已启用的插件，读取每个插件的 `PLUGIN.md`，注册钩子。
- 应用 `on_init` 钩子指引。

### 第 2 步：分析

- 运行 `scripts/analyze_project.py` 检测：
  - **技术栈**：从清单文件（package.json、go.mod、Cargo.toml 等）检测语言、框架和库
  - **模块**：目录结构、逻辑分组、入口点
  - **入口文件**：`src/index.ts`、`main.py`、`cmd/`、`lib/` 等
  - **现有文档**：`README.md`、`CHANGELOG.md`、内联文档注释、已有的 wiki 文件
- 应用 `after_analyze` 插件钩子（纯文本指引）优化分析结果。
- 将分析结果保存到 `cache/structure.json`。
- **扁平结构项目**：`analyze_project.py` 会自动跳过 `scripts/`、`plugins/`、`docs/`、`tests/` 等非业务目录。如仍有误识别，可在 `.deepwiki/config.yaml` 的 `exclude` 中手动补充。

### 第 3 步：深度阅读源码

**首先读取 `cache/structure.json`**，获取第 2 步分析结果中的核心数据：

- **`core_files`**：所有 `importance_score >= 0.5` 的文件列表（已按评分降序排列）。这些是最值得分析的源文件。
- **`high_priority_files`**：所有 `importance_score >= 0.6` 的文件列表，用于关系分析和深度分析的精确过滤。
- **`modules`**：每个模块的 `importance_score`、`core_files` 列表和 `core_files_count`。
- **`file_types`**：扩展名 → 文件数，用于构建项目概览。
- **`directories`**：目录结构和重要性评分，用于理解项目布局。

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
6. 为每个模块输出结构化分析结果，供第 3.5 步和第 5 步使用。

**技巧**：从模块的入口文件或桶文件（如 `index.ts`、`__init__.py`）开始了解公共接口，然后读取实现文件了解内部逻辑。对于大文件，先关注导出的符号（`important_lines`），再根据需要读取上下文。

### 第 3.5 步：依赖关系综合

> 此步骤在深度阅读源码之后、变更检测之前执行。它将孤立的文件分析转化为连贯的依赖图，供 `architecture.md` 和各模块文档的依赖章节使用。

**输入选择（三阶段漏斗）**：

1. **按重要性排序** — 从 `high_priority_files`（`importance_score >= 0.6`）开始，再扩展到 `core_files`（`>= 0.5`）。
2. **阈值过滤** — 仅处理 `importance_score >= 0.6` 的文件进行关系分析，过滤低价值工具文件噪音。
3. **数量截断** — 最多处理 150 个文件，每个文件最多展示前 20 个依赖项（防止超大型项目的 Token 溢出）。

**依赖提取（静态层）**：

从第 3 步的语义分析结果中，提取每个文件已识别的 `import`/`use`/`require` 声明，构建有向依赖边：

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
- `architecture.md` 的"模块依赖图"章节（Mermaid `flowchart LR`）
- 各模块 `modules/<name>.md` 的"依赖关系"章节

### 第 4 步：变更检测

- 运行 `scripts/detect_changes.py` 对比当前文件校验和与 `cache/checksums.json`。
- 文件分类：
  - **新增文件** -> 排入完整文档生成队列
  - **修改文件** -> 排入文档更新队列
  - **删除文件** -> 将现有文档标记为废弃
- 此步骤实现增量更新，仅重新生成变更的模块，为大型项目节省时间。

### 第 5 步：生成与保存

应用 `before_generate` 钩子，然后生成以下文档类型：

#### 文档格式

参考 `references/templates.md` 中的模板生成各类文档：
`index.md`、`architecture.md`、`modules/<name>.md`、`api/<name>.md`、`getting-started.md`、`doc-map.md`。


#### 保存

- 将所有 wiki 文件写入 `.deepwiki/wiki/`。
- 更新 `cache/checksums.json` 为当前文件校验和。
- 更新 `meta.json` 的时间戳和每个模块的元数据。
- 应用 `after_generate` 插件钩子。

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

### 自动批次处理

1. **自动逐批处理所有模块**，每批 1-2 个模块，以保持每个文档的深度和质量。
2. **每批处理后将进度保存到 `cache/progress.json`**：
   ```json
   {
     "total_modules": 25,
     "completed_modules": ["core", "utils", "api"],
     "pending_modules": ["auth", "db"],
     "current_batch": 2,
     "last_updated": "2026-04-20T10:00:00Z"
   }
   ```
3. **自动继续**下一批，不暂停，直到所有模块都有文档。
4. **全部完成后**输出总结报告：已生成文档总数、质量检查结果、遇到的问题。
5. **断点续传**：如果因上下文限制或错误中断，下次运行时自动读取 `cache/progress.json`，跳过已完成模块，从中断处继续。

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

运行 `scripts/check_quality.py` 验证生成的文档质量：

```bash
# 基本检查
python scripts/check_quality.py /path/to/.deepwiki

# 详细报告
python scripts/check_quality.py /path/to/.deepwiki --verbose

# 导出 JSON 报告
python scripts/check_quality.py /path/to/.deepwiki --json report.json
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

> **核心原则（参考 deepwiki-rs 的韧性设计）**：降级不是失败，而是保证流水线不崩溃的安全网。一个有占位内容的 `basic` 级文档，远比完全缺失的文档更有价值，因为它可以通过 `升级 <模块> 文档` 命令随时升级。

## 增量更新命令

用户可触发特定的更新操作：

| 命令 | 操作 |
|------|------|
| `生成 wiki` / `创建文档` | 自动完整生成 -- 分析所有模块并生成完整文档 |
| `更新 wiki` / `重建 wiki` | 重新分析并重新生成所有文档 |
| `检查 wiki 质量` | 运行质量检查并显示报告 |
| `升级 <模块> 文档` | 重新生成特定模块的文档 |

> 所有命令均执行完整的 5 步工作流；区别在于第 4 步变更检测的范围：
> "生成/创建" = 全量处理所有模块；"更新/重建" = 仅处理变更模块。

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

| 脚本 | 用途 |
|------|------|
| `scripts/init_wiki.py <path>` | 初始化 .deepwiki 目录 |
| `scripts/analyze_project.py <path>` | 分析项目结构和技术栈 |
| `scripts/detect_changes.py <path>` | 检测文件变更，用于增量更新 |
| `scripts/extract_docs.py <file>` | 从源码提取文档注释 |
| `scripts/generate_diagram.py <wiki_dir>` | 生成 Mermaid 图表 |
| `scripts/generate_toc.py <wiki_dir>` | 生成目录 |
| `scripts/check_quality.py <wiki_dir>` | 检查文档质量 |
| `scripts/plugin_manager.py` | 管理插件 |

使用示例：

```bash
# 初始化新 wiki
python scripts/init_wiki.py /path/to/project

# 分析项目结构
python scripts/analyze_project.py /path/to/project

# 检测文件变更
python scripts/detect_changes.py /path/to/project

# 提取源码注释
python scripts/extract_docs.py /path/to/src/utils.ts

# 生成 Mermaid 图表
python scripts/generate_diagram.py /path/to/.deepwiki

# 生成目录
python scripts/generate_toc.py /path/to/.deepwiki

# 检查文档质量
python scripts/check_quality.py /path/to/.deepwiki

# 列出已安装插件
python scripts/plugin_manager.py list
```

## 参考资料

`references/` 目录下提供了详细的模板和提示词：

- `references/prompts.md` -- AI 提示词模板（代码分析、模块文档、架构文档、API 参考、首页、文档地图）
- `references/templates.md` -- Wiki 页面模板，含 Mermaid 图表（首页、架构、模块、API 参考、快速开始、文档地图）
- `references/plugin-template.md` -- 插件格式规范（PLUGIN.md 结构、钩子定义、注册表格式）
