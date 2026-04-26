# 分析结果输出规范（module-analysis.json）

> 本文件定义 `extract-docs` 阶段向 `cache/module-analysis.json` 写入的完整规范：写入时机、必须字段、semantic_group 命名规则及骨架冲突处理。
>
> **关联 Schema**：[`../../schemas/module-analysis-schema.json`](../../schemas/module-analysis-schema.json)
>
> **关联文档**：[`../workflow/extract-docs.md`](../workflow/extract-docs.md)（分析执行流程）

---

## 写入时机

> **强制要求**：完成每个模块的语义分析后，必须立即将结构化结果写入 `cache/module-analysis.json`。不要等全部模块完成后再统一写入——中途中断将导致已分析数据全量丢失。

每个模块分析完毕后**立即写入**，采用**增量追加模式**：

1. 若 `module-analysis.json` 已存在，读取其内容
2. 更新（或新增）对应模块 key 的条目
3. 写回文件

增量更新时（步骤 4 已确定变更模块列表），只覆盖变更模块的条目，未变更模块的历史分析数据保留不动。

### 写入路径

```
<项目目录>/.deepwiki/cache/module-analysis.json
```

---

## 每个模块必须写入的字段

| 字段 | 说明 |
|------|------|
| `module_path` | 模块相对路径（如 `src/auth`） |
| `code_purpose` | 模块整体 CodePurpose（取该模块主要文件的角色） |
| `analysis_depth` | 本次分析的最高深度（`deep` / `standard` / `quick`） |
| `module_summary` | 1-2 句描述模块职责和架构角色 |
| `selected_components` | 已选定的文档组件列表（generate-module-docs直接使用，无需重新决策） |
| `dependency_hints.imports` | 本模块依赖的其他模块名列表 |
| `dependency_hints.imported_by` | 依赖本模块的其他模块名列表（可从 code-structure.json 的 `import_relations` 字段推断） |
| `files[].path` | 文件相对路径 |
| `files[].code_purpose` | 文件级 CodePurpose |
| `files[].complexity_score` | 来自 structure.json 的复杂度评分 |
| `files[].summary` | 文件职责一句话概述 |
| `files[].public_interfaces` | 导出接口列表（名称、类型、签名、行号、描述） |
| `files[].key_insights` | 2-5 条设计意图说明（解释 WHY，非 WHAT） |
| `files[].confidence` | 分析置信度（`high` / `medium` / `low`） |
| `semantic_group` | AI 对该模块的语义主题标注（**自由文字**，如"认证与鉴权"、"消息路由"、"Data Persistence"）——依据代码实际内容命名，不受 CodePurpose 枚举约束；命名面向读者理解，非文件路径。若与骨架建议分组不符，可同时写入 `semantic_group_override: true`，表明此命名来自深度分析；`generate-menu` 优先采用带 override 标记的命名 |
| `semantic_group_confidence` | 语义分组置信度：`high`=模块有清晰的语义边界 / `low`=职责混杂或 AI 不确定；步骤 8 分组时对 `low` 的条目降低权重，优先以依赖数据为准 |

---

## semantic_group 命名指南

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

---

## 与骨架建议冲突时的处理

| 情形 | 操作 |
|------|------|
| 骨架建议名与源码职责吻合 | 直接使用，不写 `semantic_group_override` |
| 骨架建议过于宽泛，源码有更精确语义 | 使用精确命名，写 `semantic_group_override: true` |
| 骨架将两个明显独立职责归为一组 | 各自独立命名，各自写 `semantic_group_override: true` |
| 骨架 `reason` 字段含"import"（来自精确 import 数据） | 倾向保留骨架建议，慎用 override |

> 完整字段格式见 [`../../schemas/module-analysis-schema.json`](../../schemas/module-analysis-schema.json)。

---

## 降级处理

写入操作失败时（权限问题、磁盘满等），**记录警告并继续分析**，不中断流程。警告格式：

```
⚠️ [extract-docs] 写入 module-analysis.json 失败（模块：<name>）：<错误信息>
   validate-analysis 将无法通过；依赖综合规则和 generate-module-docs 只能降级为从上下文窗口读取分析结果。
```

---

## `doc-topology.json` 输出规范

> `doc-topology.json` 是 Documentation Planning Layer 的主契约，描述“页面应该如何组织”，而不是“源码目录长什么样”。

### 写入路径

```
<项目目录>/.deepwiki/cache/doc-topology.json
```

### 最小字段

| 字段 | 说明 |
|------|------|
| `pages` | 页面列表，每项至少包含 `id`、`type`、`title` |
| `pages[].source_modules` | 该页面覆盖的源码模块或主题集合 |
| `pages[].output_path` | 目标文档路径（如 `wiki/overview.md`） |
| `pages[].depends_on` | 上游页面或缓存依赖 |
| `reading_order` | 推荐阅读顺序 |
| `groupings` | 页面分组，如 `overview` / `concepts` / `capabilities` / `internals` / `reference` |

### 字段语义

- `pages` 代表文档知识树中的节点，而不是磁盘上已存在的文件
- `source_modules` 可为空数组，仅用于纯导航或索引页
- `depends_on` 允许引用缓存文件 id 或其他页面 id
- `groupings` 用于 `generate-menu` 构造稳定菜单结构

### 降级策略

- 若 `doc-topology.json` 不存在，`generate-menu` 和文档生成可退回骨架分组 + 磁盘扫描
- 若内容不完整，至少保留 overview / getting-started / doc-map / concepts / capabilities 或 internals 的基础页面集合

---

## `generation-plan.json` 输出规范

> `generation-plan.json` 描述“本轮具体要编译什么”，它比 `doc-topology.json` 更贴近一次实际执行。

### 写入路径

```
<项目目录>/.deepwiki/cache/generation-plan.json
```

### 最小字段

| 字段 | 说明 |
|------|------|
| `pages` | 本轮待生成或待更新页面列表 |
| `pages[].page_id` | 对应 `doc-topology.json` 中的页面 id |
| `pages[].inputs` | 该页面依赖的缓存文件集合 |
| `pages[].affected_modules` | 该页面依赖的模块集合 |
| `pages[].action` | `create` / `update` / `skip` |
| `recompile_all` | 是否需要全量重编译 |

### 字段语义

- `inputs` 用于帮助增量流程判断页面是否需要重算
- `affected_modules` 是模块到页面的映射桥
- `action` 是编译建议，不代表最终文件系统状态

### 降级策略

- 若 `generation-plan.json` 缺失，默认退回全量编译
- 若仅部分页面缺失计划项，未命中的页面按 `create` 处理

---

## `evidence-index.json` 输出规范

> `evidence-index.json` 把“文档中的关键结论”与“源码中的可验证事实”关联起来，是后续质量门控的基础。

### 写入路径

```
<项目目录>/.deepwiki/cache/evidence-index.json
```

### 最小字段

| 字段 | 说明 |
|------|------|
| `claims` | 关键结论列表 |
| `claims[].claim_id` | 结论唯一标识 |
| `claims[].page_id` | 该结论所属页面 |
| `claims[].claim_text` | 结论摘要 |
| `claims[].evidence` | 源码证据列表 |
| `claims[].confidence` | `high` / `medium` / `low` |

### 字段语义

- `evidence` 可引用文件路径、行号范围、调用图节点、导入关系或入口链路
- `confidence` 用于文档质量检查时的错误等级区分

### 降级策略

- 若证据索引缺失，质量检查应至少给出 warning，而不是静默跳过
- 若只有部分页面建立索引，只对已索引页面执行严格校验
