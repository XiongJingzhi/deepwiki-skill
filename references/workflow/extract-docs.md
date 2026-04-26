# 文件分析指南


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/extract_doc_comments.py <文件绝对路径>`（预提取注释，逐文件） |
| **输入** | `cache/structure.json`、`cache/code-structure.json`、`cache/architecture-skeleton.json`（可选） |
| **输出** | `cache/module-analysis.json` |
| **前置** | `detect-changes`，可选 `generate-skeleton` |
| **后置** | `validate-analysis`；并行策略见 `parallel-analysis.md` |

## 文件角色分类

> 完整分类规则见 [`../rules/codepurpose-detection.md`](../rules/codepurpose-detection.md)；组件触发规则见 [`../rules/components-guide.md`](../rules/components-guide.md)。
>
> **执行要点**：在读取每个文件之前先完成分类，角色标签用于生成文档时的针对性描述。

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
| `archetype` | 决定分析侧重点：`spa-frontend`（组件树/状态流）/ `web-service`（请求链路/鉴权）/ `fullstack-framework`（SSR/API Routes）/ `cli-tool`（命令树/配置加载）/ `sdk-library`（公开 API 契约/扩展点）/ `ml-project`（数据管道/训练循环）/ `agent-project`（Agent 调度链路/工具注册/记忆管理）/ `monorepo`（包间依赖关系/共享包/各子包独立入口/跨包调用链） |
| `call_graph` | 每个函数的 `calls` 列表作为锚点，AI 只需补充语义（Why），而非重新推断结构（What） |
| `patterns` | 对检测到模式的文件优先深度分析（如 `middleware_chain` → 重点分析各中间件职责与错误传递；`react_component` → 重点分析 Props/状态/生命周期） |
| `key_sequences` | 验证或修正时序参与者顺序，补充每步业务语义；直接用于生成 `sequenceDiagram` |

## 读取 architecture-skeleton.json（generate-skeleton产出）并注入全局上下文

若 `cache/architecture-skeleton.json` 存在（generate-skeleton 成功生成），在每个 subagent/批次的分析 prompt 中注入以下摘要（约 1K tokens）：

```
## 全局架构上下文（来自generate-skeleton骨架）

项目类型：{{ skeleton.project_nature }}
架构风格：{{ skeleton.architecture_style }}

模块分组（以下分组为初始建议，非硬约束。若源码实际职责与建议不符，可输出 semantic_group_override: true 并使用更准确的命名）：
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

根据 `detect-changes` 结果筛选待处理文件，并按 `change_type` 决定最小重分析深度：

- **首次生成**（无变更记录）：处理所有模块的核心文件，执行完整分析。

- **增量更新**：

  | change_type | 重分析范围 | 反向依赖传播 |
  |------------|-----------|------------|
  | `new` | 完整分析（视同新模块） | 按所属模块处理 |
  | `deleted` | 标记废弃，删除 `module-analysis.json` 中对应 `files[]` 条目 | ✅ 触发 |
  | `api-change` | 完整重分析：更新 `public_interfaces`、`key_insights`、`summary` | ✅ 触发 |
  | `impl-change` | 定向重分析：仅重读实现部分，更新 `key_insights` | ❌ 不触发 |
  | `doc-only-change` | 轻量更新：重跑 `extract_doc_comments.py`，更新 `summary` | ❌ 不触发 |

## 预提取文档注释

对每个待处理的核心文件，从**技能目录**运行以下命令预提取结构化注释（函数签名、参数、返回值、类定义）：

```bash
python scripts/extract_doc_comments.py <文件绝对路径>
```

将提取结果作为语义分析的起点注入 `{{ EXTRACTED_DOCS }}` 变量，减少重复提取工作。若文件无文档注释则跳过。

## 语义分析流程

> **多 agent 拆分提示**：本步骤可以按模块拆成多个 subagent 并行处理。每个 subagent 领取一个模块或一个批次内的少量模块，读取共享的 `structure.json`、`code-structure.json`、`architecture-skeleton.json`，只负责输出自己模块的分析结果。不要让多个 subagent 同时改写同一个模块条目；写入 `module-analysis.json` 时必须采用增量追加/合并方式。具体批次规则见 [`parallel-analysis.md`](parallel-analysis.md)。

对每个文件进行语义分析时，按以下步骤执行：

1. 按双层分类规则确定文件角色（`Entry`/`Service`/`Api`/`Dao` 等）
2. 理解语义：追踪函数调用、控制流、数据流、错误处理和设计模式
3. 提取公共接口、内部逻辑和模块依赖；公共接口必须包含 `line/end_line`，核心逻辑必须写入 `core_source_ranges`
4. 参考 `../generation/module-page.md` 获取分析提示词模板（代码深度分析 / 模块文档 / 依赖分析）
5. 为每个模块输出结构化分析结果，供 `validate-analysis`、依赖综合规则和 `generate-module-docs` 使用

---

## 分析结果持久化

> 完整输出规范（必须字段、写入时机、semantic_group 命名规则、骨架冲突处理）见 [`../rules/analysis-output-spec.md`](../rules/analysis-output-spec.md)。

**核心约束（此处重申）**：
- 完成每个模块分析后**立即写入** `cache/module-analysis.json`，采用增量追加模式
- `public_interfaces[].line/end_line` 与 `core_source_ranges[].start_line/end_line` 使用 1-based 闭区间，供 `Relevant source files` 和核心逻辑源码片段生成 `file:///path#Lx-Ly` 链接
- 不要等全部模块完成后统一写入——中途中断将导致已分析数据全量丢失
