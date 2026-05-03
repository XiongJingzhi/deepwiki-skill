# module-analysis.json 输出规范

> **适用步骤：** `extract-docs`（写入）、`validate-analysis`（读取校验）
> 规划层规范（doc-topology / generation-plan / evidence-index）见 [`planning-output-spec.md`](planning-output-spec.md)。
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

增量更新时（detect-changes 已确定变更模块列表），只覆盖变更模块的条目，未变更模块的历史分析数据保留不动。

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
| **认知结构字段** | **以下 5 个字段为必填，质量门控会检查** |
| `module_role` | 模块在系统中的角色定位（面向读者的角色描述，如"负责用户认证决策"、"协调订单处理流程"） |
| `upstream_inputs` | 该模块的输入来源列表（外部模块、运行时事件、文件、请求、数据源等） |
| `downstream_outputs` | 该模块的输出目标列表（输出、副作用、调用、文档、状态变更等） |
| `risk_points` | 已知风险点列表（脆弱假设、边界条件、维护注意事项等） |
| `extension_points` | 扩展点列表（未来可扩展或修改行为的稳定位置） |
| `selected_components` | 已选定的文档组件列表（generate-module-docs直接使用，无需重新决策） |
| `dependency_hints.imports` | 本模块依赖的其他模块名列表 |
| `dependency_hints.imported_by` | 依赖本模块的其他模块名列表（可从 code-structure.json 的 `import_relations` 字段推断） |
| `files[].path` | 文件相对路径 |
| `files[].code_purpose` | 文件级 CodePurpose |
| `files[].complexity_score` | 来自 structure.json 的复杂度评分 |
| `files[].summary` | 文件职责一句话概述 |
| `files[].public_interfaces` | 导出接口列表（名称、类型、签名、起止行号、描述） |
| `files[].core_source_ranges` | 本文件适合文档讲解的核心源码范围，供 `相关源文件` 和核心逻辑源码片段引用 |
| `files[].key_insights` | 2-5 条设计意图说明（解释 WHY，非 WHAT） |
| `files[].confidence` | 分析置信度（`high` / `medium` / `low`） |
| `semantic_group` | AI 对该模块的语义主题标注（**自由文字**，如"认证与鉴权"、"消息路由"、"Data Persistence"）——依据代码实际内容命名，不受 CodePurpose 枚举约束；命名面向读者理解，非文件路径。若与骨架建议分组不符，使用更精确的命名 |

---

## 源码范围规范

`extract-docs` 写入的源码范围必须使用 1-based 行号：

```json
{
  "files": [
    {
      "path": "src/auth/service.ts",
      "public_interfaces": [
        {
          "name": "login",
          "type": "function",
          "line": 24,
          "end_line": 88,
          "description": "认证主流程"
        }
      ],
      "core_source_ranges": [
        {
          "label": "认证主流程",
          "start_line": 24,
          "end_line": 88,
          "reason": "覆盖参数校验、token 生成和错误处理"
        }
      ]
    }
  ]
}
```

规则：

- `line` / `start_line` 和 `end_line` 都是闭区间，供内部定位使用，不需要在生成链接中体现行范围。
- `相关源文件` 优先使用 `core_source_ranges`，其次使用 `public_interfaces.line/end_line`。
- 若仅有起始行，允许生成单行链接 `file:///path#L24`，但核心逻辑真实源码片段应尽量提供范围。

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
4. **参考 [`menu-archetypes.md`](menu-archetypes.md)** 的"常见语义主题"——该文档按项目原型提供了语义分组灵感，`semantic_group` 命名应与之对齐以便 `generate-menu` 复用

### 标题简洁化规则

模块文档 H1 标题和 `semantic_group` 命名必须简洁明了，只保留核心含义：

| ❌ 禁止的标题模式 | ✅ 正确示例 |
|-----------------|-----------|
| XXX 深入理解 | 认证与鉴权 |
| XXX 基础介绍 | 配置管理 |
| XXX 全面解析 | 消息路由 |
| XXX 核心原理解析 | 缓存策略 |
| XXX 实战指南 | 数据库访问层 |

**原则**：标题应直接反映模块功能（"做什么"），不添加评价性修饰词（深入、全面、基础）或体裁修饰词（指南、解析、理解）。

**多模块同组示例：**
- `src/auth`、`src/token`、`src/session` → 都标注 `semantic_group: "认证与鉴权"`
- `src/order`、`src/payment`、`src/cart` → 都标注 `semantic_group: "交易流程"`

---

## 与骨架建议冲突时的处理

### Mono-repo workspace 包

对于 `archetype == monorepo` 的项目，每个 workspace 包内拆分出的子模块应独立分析：

- `module_role` 需注明跨包视角的职责（如"为其他包提供 XXX 能力"）
- `dependency_hints.imports` 和 `imported_by` 必须包含跨包依赖
- `semantic_group` 命名应面向功能域，避免仅使用包名作为分组依据

---

| 情形 | 操作 |
|------|------|
| 骨架建议名与源码职责吻合 | 直接使用 |
| 骨架建议过于宽泛，源码有更精确语义 | 使用精确命名 |
| 骨架将两个明显独立职责归为一组 | 各自独立命名 |
| 骨架 `reason` 字段含"import"（来自精确 import 数据） | 倾向保留骨架建议 |

> 完整字段格式见 [`../../schemas/module-analysis-schema.json`](../../schemas/module-analysis-schema.json)。

---

## 降级处理

写入操作失败时（权限问题、磁盘满等），**记录警告并继续分析**，不中断流程。警告格式：

```
⚠️ [extract-docs] 写入 module-analysis.json 失败（模块：<name>）：<错误信息>
   validate-analysis 将无法通过；依赖综合规则和 generate-module-docs 只能降级为从上下文窗口读取分析结果。
```

---
