# generate-skeleton：全局架构骨架生成

> 本文档描述工作流generate-skeleton的完整规则：在模块深度分析（extract-docs）之前，先生成轻量的全局架构骨架，为后续所有 AI 步骤提供一致的全局视角。


## 契約

| 項 | 值 |
|----|-----|
| **脚本** | `python scripts/generate_architecture_skeleton.py <项目路径>`（脚本段）+ AI 生成（AI 段） |
| **输入** | `cache/structure.json`、`cache/code-structure.json`、`cache/import-relations.json` |
| **输出** | `cache/architecture-skeleton.json` |
| **前置** | `extract-structure` |
| **后置** | `extract-docs`（注入全局上下文） |
| **失败策略** | 跳过骨架注入，后续工具以无全局上下文模式运行 |

## 目标与收益

### 为什么需要全局骨架？

extract-docs的深度分析采用 batch-3 策略（每批 3 个模块），每个 batch 的 subagent 只看到自己分配的模块，没有全局视角。这会导致：

- `dependency_hints.imports` 和 `semantic_group` 的跨模块一致性下降
- 不同 batch 分析同一依赖方向时可能得出相互矛盾的结论
- synthesize-deps、generate-overview、generate-menu 生成的文档缺乏统一的架构叙述

全局骨架以约 **17K tokens 的一次性成本**，换取后续所有步骤的一致性提升和 token 节省（预计净节省 15-20%）。

### 下游收益

| 步骤 | 骨架带来的收益 |
|------|--------------|
| extract-docs | 每个 subagent 注入骨架摘要（~1K tokens），使模块分析具备全局视野 |
| synthesize-deps | 从"从零推断"变为"验证修正"，AI 工作量减少约 50% |
| generate-overview | 直接复用骨架内容，减少 30-40% 的 AI token 消耗 |
| generate-menu | `module_groups` 已由骨架完成，三层分组的第一层无需重新推断 |

---

## 执行流程

### 第一步：运行数据提取脚本

从技能目录运行以下脚本，提取精简摘要，输出 `cache/architecture-skeleton-input.json`：

```bash
python scripts/generate_architecture_skeleton.py <项目目录绝对路径>
```

**脚本输入**（全部来自确定性脚本，零 AI 成本）：
- `cache/structure.json` — 模块列表、重要性排名、技术栈
- `cache/code-structure.json` — archetype、patterns 摘要、key_sequences 参与者
- `cache/import-relations.json` — 跨模块导入关系摘要

**脚本输出**：`cache/architecture-skeleton-input.json`（约 5-15K tokens）

### 第二步：AI 生成全局架构骨架

读取 `cache/architecture-skeleton-input.json`，使用以下提示词生成骨架：

```
你是一位架构师。根据以下项目分析数据，生成一份精简的全局架构骨架。

输入数据：
{{ SKELETON_INPUT_JSON }}

输出格式：严格遵循以下 JSON Schema，不要添加任何 Markdown 包装：

{
  "project_nature": "项目性质的一句话描述（含技术栈）",
  "architecture_style": "架构风格描述（如：分层架构、微服务、MVC等）",
  "module_groups": [
    {
      "name": "领域/层次名称（面向读者，如'用户管理域'）",
      "modules": ["模块名1", "模块名2"],
      "role": "该组在架构中的角色（1句话）",
      "reason": "为什么这些模块归为一组（基于导入关系或语义）"
    }
  ],
  "cross_domain_dependencies": [
    {
      "from": "源域名",
      "to": "目标域名",
      "type": "依赖类型（如：user_id 引用、HTTP 调用等）"
    }
  ],
  "key_data_flows": [
    "关键数据流描述（1句话，如：用户请求 → API网关 → 认证中间件 → 业务处理 → 数据库）"
  ],
  "architecture_layers": [
    {
      "layer": "层名称（如：展示层、业务层、数据层、基础设施层）",
      "modules": ["属于此层的模块名"]
    }
  ]
}

要求：
1. module_groups 中的每个模块名必须来自输入数据的模块列表
2. cross_domain_dependencies 基于 cross_module_imports 推断，方向必须正确（A imports B → A 依赖 B）
3. key_data_flows 最多 3 条，选择最重要的数据路径
4. 输出必须是合法 JSON，不含注释
```

### 第三步：保存骨架文件

将 AI 输出的 JSON 保存为 `cache/architecture-skeleton.json`：

- 若 AI 输出包含 Markdown 代码块（\`\`\`json）则去除包装后保存
- 验证 JSON 合法性（`json.loads` 不报错）
- 验证包含 `project_nature`、`architecture_style`、`module_groups` 三个必需字段

---

## 输出格式：architecture-skeleton.json

```json
{
  "project_nature": "前后端分离的 Web 应用，前端 React SPA + 后端 FastAPI 微服务",
  "architecture_style": "分层架构（展示层 → API 网关 → 业务层 → 数据层）",
  "module_groups": [
    {
      "name": "用户管理域",
      "modules": ["auth", "user", "session"],
      "role": "负责身份认证与用户数据管理",
      "reason": "auth/user/session 之间有强双向 import，共同依赖 database 模块"
    },
    {
      "name": "订单交易域",
      "modules": ["order", "payment", "cart"],
      "role": "处理电商核心交易流程",
      "reason": "order → payment 和 order → cart 的单向依赖链"
    }
  ],
  "cross_domain_dependencies": [
    {"from": "订单交易域", "to": "用户管理域", "type": "user_id 引用"}
  ],
  "key_data_flows": [
    "用户请求 → API 网关 → Auth 中间件 → 业务处理器 → 数据库",
    "前端状态变更 → API 调用 → 后端处理 → WebSocket 推送"
  ],
  "architecture_layers": [
    {"layer": "展示层", "modules": ["frontend", "pages"]},
    {"layer": "业务层", "modules": ["auth", "order", "payment"]},
    {"layer": "数据层", "modules": ["database", "cache"]}
  ]
}
```

---

## 骨架在后续步骤中的使用

### 在extract-docs中注入骨架摘要

每个 subagent 的 prompt 中注入以下摘要（约 1K tokens）：

```
## 全局架构上下文

项目类型：{{ skeleton.project_nature }}
架构风格：{{ skeleton.architecture_style }}

模块分组（以下分组来自全局骨架，请保持你的 semantic_group 与之一致）：
{% for group in skeleton.module_groups %}
- {{ group.name }}：{{ group.modules | join(", ") }}（{{ group.role }}）
{% endfor %}

关键数据流：
{% for flow in skeleton.key_data_flows %}
- {{ flow }}
{% endfor %}

当前你正在分析的模块属于：{{ current_module_group }}
```

### 在synthesize-deps中复用骨架

- 骨架的 `cross_domain_dependencies` 作为验证基线：AI 综合出的依赖边必须与骨架方向一致
- `architecture_layers` 作为分层分组的初始结构，AI 只需补充细节
- 不需要从零推断整体架构，只需验证和修正

### 在generate-overview中复用骨架

- `overview.md` 的"系统架构"章节直接从骨架的 `architecture_style` 和 `architecture_layers` 生成
- `module_groups` 直接用于模块列表章节的分组展示

### 在generate-menu中复用骨架

- `module_groups` 作为菜单分组的第一层，AI 只需决定每组内的排序和二级分组
- 无需重新推断模块归属

---

## 失败降级

若 Step 3.5 因任何原因失败（AI 输出格式错误、骨架文件缺失等）：

- **不中断后续步骤**，直接跳过骨架注入，extract-docs以无全局上下文模式运行
- 记录警告：`⚠️ [Step 3.5] 架构骨架生成失败，后续步骤将以无全局上下文模式运行`
- 在 `cache/progress.json` 中记录 `phases.skeleton.status: "failed"`

---

## Token 成本估算

| 操作 | 估算 token |
|------|-----------|
| 脚本提取（零 AI） | 0 |
| AI 读取 skeleton-input.json | ~10-15K |
| AI 生成 architecture-skeleton.json | ~2-3K |
| 总计（一次性） | ~17K |
| 每批 Step 5 注入骨架摘要 | +1K/batch |
| 净节省（20 模块项目） | ~50-80K |
