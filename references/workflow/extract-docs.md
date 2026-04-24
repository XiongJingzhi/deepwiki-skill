# 文件分析指南


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/extract_docs.py <文件绝对路径>`（预提取注释，逐文件） |
| **输入** | `cache/structure.json`、`cache/code-structure.json`、`cache/architecture-skeleton.json`（可选） |
| **输出** | `cache/module-analysis.json` |
| **前置** | `detect-changes`，可选 `generate-skeleton` |
| **后置** | `check-analysis-quality`；并行策略见 `parallel-analysis.md` |

## 文件角色分类（双层分类）

在读取每个文件之前，先按以下两层规则确定文件的角色标签，角色标签将用于生成文档时的针对性描述。

### 第一层：路径/文件名模式快速分类（优先，无需读文件内容）

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
| `Command` | 路径含 `/commands/`、`/cli/`、`/cmd/`、文件名含 `command`、`cli` | `commands/deploy.ts` |
| `Test` | 文件名含 `.test.`、`.spec.`、路径含 `/__tests__/` | `user.test.ts` |
| `Other` | 以上规则均不匹配时的兜底分类 | `misc/helpers.ts` |

### 第二层：语义推断（仅在第一层无法确定时使用）

当路径规则无法确定角色时，读取文件内容的前 1,000 字符，根据以下信号推断：

- 含大量 HTTP 路由注册（`app.get`、`router.post`、`@GetMapping`）→ `Api`
- 含数据库查询（`SELECT`、`.query(`、`ORM.find`）→ `Dao`
- 含 UI 渲染逻辑（`render(`、`return <`、`template:`）→ `Widget` 或 `Page`
- 含配置常量（大量 `const CONFIG_`、`env.`）→ `Config`

---

## 分档读取深度

根据 `complexity_score` 和 `important_lines_count` 决定每个文件的分析深度，避免在低价值文件上浪费 Token：

| complexity_score | important_lines_count | 分析深度 | 操作 |
|-----------------|----------------------|---------|------|
| > 50 | 任意 | **深度分析** | 读取全文，追踪函数调用，提取完整接口表 |
| 20–50 | ≥ 10 | **标准分析** | 读取前 8,000 字节 + 所有重要代码行，提取主要接口 |
| 20–50 | < 10 | **快速浏览** | 读取前 3,000 字节，仅提取导出声明 |
| < 20 | 任意 | **快速浏览** | 读取前 2,000 字节，记录模块职责即可 |

> **重要行优先保留**：当文件需要截断时，优先保留含 `export`、`def`、`fn`、`class`、`import`、`interface`、`@decorator` 的行（即 `important_lines_count` 统计的行类型）。

---

## 读取优先级顺序

按以下优先级读取源文件：

1. **入口文件优先**：先读取 `entry_points` 中的文件，理解项目启动流程。
2. **高优先级文件优先**：从 `high_priority_files` 列表（`importance_score >= 0.6`）按评分降序进行深度分析。
3. **核心文件次之**：从 `core_files` 列表中按 `importance_score` 降序读取，应用分档深度策略。
4. **模块内读取顺序**：对每个模块，先读其 `core_files` 中的文件，再读其他文件。

**技巧**：从模块的入口文件或桶文件（如 `index.ts`、`__init__.py`）开始了解公共接口，然后读取实现文件了解内部逻辑。对于大文件，先关注导出的符号（`important_lines`），再根据需要读取上下文。

---

## 读取 structure.json（analyze-project 产出）



首先读取 `cache/structure.json`，获取以下核心字段：

| 字段 | 用途 |
|------|------|
| `core_files` | 所有 `importance_score >= 0.5` 的文件列表（按评分降序），是最值得分析的源文件 |
| `high_priority_files` | 所有 `importance_score >= 0.6` 的文件列表，用于关系分析和深度分析的精确过滤 |
| `modules` | 每个模块的 `importance_score`、`core_files` 列表和 `core_files_count` |
| `file_types` | 扩展名 → 文件数，用于构建项目概览 |
| `directories` | 目录结构和重要性评分，用于理解项目布局 |

## 读取 code-structure.json（extract-structure 产出）并应用

同时读取 `cache/code-structure.json`，作为语义分析锚点：

| 字段 | 如何应用 |
|------|---------|
| `archetype` | 决定分析侧重点：`spa-frontend`（组件树/状态流）/ `web-service`（请求链路/鉴权）/ `fullstack-framework`（SSR/API Routes）/ `cli-tool`（命令树/配置加载）/ `sdk-library`（公开 API 契约/扩展点）/ `ml-project`（数据管道/训练循环）/ `agent-project`（Agent 调度链路/工具注册/记忆管理） |
| `call_graph` | 每个函数的 `calls` 列表作为锚点，AI 只需补充语义（Why），而非重新推断结构（What） |
| `patterns` | 对检测到模式的文件优先深度分析（如 `middleware_chain` → 重点分析各中间件职责与错误传递；`react_component` → 重点分析 Props/状态/生命周期） |
| `key_sequences` | 验证或修正时序参与者顺序，补充每步业务语义；直接用于生成 `sequenceDiagram` |

## 读取 architecture-skeleton.json（generate-skeleton产出）并注入全局上下文

若 `cache/architecture-skeleton.json` 存在（generate-skeleton 成功生成），在每个 subagent/批次的分析 prompt 中注入以下摘要（约 1K tokens）：

```
## 全局架构上下文（来自generate-skeleton骨架）

项目类型：{{ skeleton.project_nature }}
架构风格：{{ skeleton.architecture_style }}

模块分组（请保持你分析的 semantic_group 与以下分组一致）：
- {{ group.name }}：{{ group.modules }}（{{ group.role }}）
  ...

当前模块所属分组：{{ current_module_group_name }}
```

**作用**：使每个批次的分析具备全局视野，确保跨批次的 `semantic_group` 命名和依赖方向一致。

**降级处理**：若 `architecture-skeleton.json` 不存在，跳过注入，以无全局上下文模式运行（不影响流程）。

## 图表类型选择

根据 `archetype` 和 `patterns` 选择合适的 Mermaid 图表类型：

| 场景 | 推荐图表 |
|------|---------|
| 请求处理链 / 鉴权流程 / 时序 | `sequenceDiagram` |
| 组件树 / 中间件堆叠 / 命令树 | `flowchart TB` |
| 状态机 / 组件生命周期 | `stateDiagram-v2` |
| 类继承 / 插件接口 | `classDiagram` |
| 数据模型关系 | `erDiagram` |

## 变更筛选（基于detect-changes结果）

根据detect-changes结果，筛选待处理文件：

- **首次生成**（无变更记录）：处理所有模块的核心文件。
- **增量更新**：仅处理变更文件所属模块的核心文件。对于被其他变更模块依赖的模块（反向依赖），也应纳入处理范围。

## 插件缓存优先

若 `.deepwiki/cache/api-analysis.json` 存在（由 `api-doc-enhancer` 插件在 `after_analyze` 阶段生成），优先读取其 `exports` 字段作为接口提取的基础，再进行语义补充，避免重复分析。

## 预提取文档注释

对每个待处理的核心文件，从**技能目录**运行以下命令预提取结构化注释（函数签名、参数、返回值、类定义）：

```bash
python scripts/extract_docs.py <文件绝对路径>
```

将提取结果作为语义分析的起点注入 `{{ EXTRACTED_DOCS }}` 变量，减少重复提取工作。若文件无文档注释则跳过。

## 语义分析流程

对每个文件进行语义分析时，按以下步骤执行：

1. 按双层分类规则确定文件角色（`Entry`/`Service`/`Api`/`Dao` 等）
2. 理解语义：追踪函数调用、控制流、数据流、错误处理和设计模式
3. 提取公共接口、内部逻辑和模块依赖
4. 参考 `../generation/module-page.md` 获取分析提示词模板（代码深度分析 / 模块文档 / 依赖分析）
5. 为每个模块输出结构化分析结果，供 synthesize-deps 和 generate-module-docs 使用

---

## 分析结果持久化

> **强制要求**：完成每个模块的语义分析后，必须立即将结构化结果写入 `cache/module-analysis.json`。不要等全部模块完成后再统一写入——中途中断将导致已分析数据全量丢失。

### 写入时机

每个模块分析完毕后**立即写入**，采用**增量追加模式**：

1. 若 `module-analysis.json` 已存在，读取其内容
2. 更新（或新增）对应模块 key 的条目
3. 写回文件

增量更新时（步骤 4 已确定变更模块列表），只覆盖变更模块的条目，未变更模块的历史分析数据保留不动。

### 写入路径

```
<项目目录>/.deepwiki/cache/module-analysis.json
```

### 每个模块必须写入的字段

| 字段 | 说明 |
|------|------|
| `module_path` | 模块相对路径（如 `src/auth`） |
| `code_purpose` | 模块整体 CodePurpose（取该模块主要文件的角色） |
| `analysis_depth` | 本次分析的最高深度（`deep` / `standard` / `quick`） |
| `module_summary` | 1-2 句描述模块职责和架构角色 |
| `selected_components` | 已选定的文档组件列表（generate-module-docs直接使用，无需重新决策） |
| `dependency_hints.imports` | 本模块依赖的其他模块名列表 |
| `dependency_hints.imported_by` | 依赖本模块的其他模块名列表（可从 import-relations.json 推断） |
| `files[].path` | 文件相对路径 |
| `files[].code_purpose` | 文件级 CodePurpose |
| `files[].complexity_score` | 来自 structure.json 的复杂度评分 |
| `files[].summary` | 文件职责一句话概述 |
| `files[].public_interfaces` | 导出接口列表（名称、类型、签名、行号、描述） |
| `files[].key_insights` | 2-5 条设计意图说明（解释 WHY，非 WHAT） |
| `files[].confidence` | 分析置信度（`high` / `medium` / `low`） |
| `semantic_group` | AI 对该模块的语义主题标注（**自由文字**，如"认证与鉴权"、"消息路由"、"Data Persistence"）——依据代码实际内容命名，不受 CodePurpose 枚举约束；命名面向读者理解，非文件路径 |
| `semantic_group_confidence` | 语义分组置信度：`high`=模块有清晰的语义边界 / `low`=职责混杂或 AI 不确定；步骤 8 分组时对 `low` 的条目降低权重，优先以依赖数据为准 |

### semantic_group 命名指南

命名应面向**读者理解**，而非代码路径或 CodePurpose 枚举：

| ✅ 好的命名 | ❌ 不好的命名 | 原因 |
|------------|--------------|------|
| `认证与鉴权` | `Service` | 不使用 CodePurpose 枚举 |
| `消息路由` | `src/router` | 不使用文件路径 |
| `Data Persistence` | `Dao + Model` | 语义聚合，非技术层 |
| `Agent 调度引擎` | `agent.py` | 面向概念，非文件名 |
| `配置与启动` | `Config` | 读者视角（"启动时做什么"）比技术层（"Config 类"）更清晰 |

**命名步骤：**
1. 看模块的主要文件名 + 目录名，提取业务关键词
2. 问：**"这个模块帮用户/系统做什么事？"**（回答就是 semantic_group 名称）
3. 同一功能域的多个模块应使用**相同或相近的 semantic_group 名称**（为 step8 的聚合提供信号）
4. 职责混杂或不确定时，设置 `semantic_group_confidence: "low"`

**多模块同组示例：**
- `src/auth`、`src/token`、`src/session` → 都标注 `semantic_group: "认证与鉴权"`
- `src/order`、`src/payment`、`src/cart` → 都标注 `semantic_group: "交易流程"`

> 完整字段格式见 [`schemas/module-analysis-schema.json`](../schemas/module-analysis-schema.json)。

### 降级处理

写入操作失败时（权限问题、磁盘满等），**记录警告并继续分析**，不中断流程。警告格式：

```
⚠️ [extract-docs] 写入 module-analysis.json 失败（模块：<name>）：<错误信息>
   synthesize-deps 和 generate-module-docs 将降级为从上下文窗口读取分析结果。
```