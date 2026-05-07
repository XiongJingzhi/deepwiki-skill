# 规划层输出规范（doc-topology / generation-plan / evidence-index）

> **适用步骤：** `plan-doc-topology`（写 doc-topology.json、generation-plan.json）、`build-evidence-index`（写 evidence-index.json）
> `module-analysis.json` 规范见 [`module-analysis-spec.md`](module-analysis-spec.md)。

---

## `doc-topology.json` 输出规范

> `doc-topology.json` 是 Documentation Planning Layer 的主契约，描述"页面应该如何组织"，而不是"源码目录长什么样"。

### 写入路径

```
<项目目录>/.deepwiki/cache/doc-topology.json
```

### 最小字段

| 字段 | 说明 |
|------|------|
| `pages` | 页面列表，每项至少包含 `id`、`type`、`title` |
| `pages[].source_modules` | 该页面覆盖的源码模块或主题集合 |
| `pages[].source_files` | 该页面最相关源码文件，供 `相关源文件` 和源码片段直接使用 |
| `pages[].output_path` | 目标文档路径（如 `wiki/overview.md`） |
| `pages[].depends_on` | 上游页面或缓存依赖 |
| `reading_order` | 推荐阅读顺序 |
| `groupings` | 页面分组，如 `overview` / `concepts` / `deep-dive` / `reference` |

### 字段语义

- `pages` 代表文档知识树中的节点，而不是磁盘上已存在的文件
- `source_modules` 可为空数组，仅用于纯导航或索引页
- `source_files[].ranges` 应来自 `core_source_ranges` 或 `public_interfaces.line/end_line`，用于生成 `file:///path#Lx-Ly` 链接
- `depends_on` 允许引用缓存文件 id 或其他页面 id
- `groupings` 用于 `generate-menu` 构造稳定菜单结构

### module_path → page_id 映射

`module-analysis-spec.md` 定义的 `module_path`（如 `src/auth`）与本文档的 `page_id` 通过以下规则映射：

- **默认映射**：`page_id` = 模块 slug（`module_path` 的最后一段目录名，小写连字符化）。例如 `src/auth/service` → `auth-service`。
- **一对多**：一个 `module_path` 可对应多个 `page_id`（例如 API 文档和核心逻辑文档分离）。
- **多对一**：多个 `module_path` 可合并到一个 `page_id`（通过 `doc-topology.json` 的 `source_modules` 数组关联）。
- **查询关系**：`generation-plan.json` 的 `affected_modules` 是完整的 module_path 列表，可通过它与 `module-analysis.json` 的条目 key 对应。

### 降级策略

- 若 `doc-topology.json` 不存在，`generate-menu` 和文档生成可退回骨架分组 + 磁盘扫描
- 若内容不完整，至少保留 overview / getting-started / doc-map / concepts / deep-dive 的基础页面集合

---

## `generation-plan.json` 输出规范

> `generation-plan.json` 描述"本轮具体要编译什么"，它比 `doc-topology.json` 更贴近一次实际执行。

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
| `pages[].source_files` | 本轮生成该页面必须使用的相关源码文件清单 |
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

## `cache/snippets/<safe_page_id>.json` 输出规范

> 由 `extract_source_snippets.py` 生成，为 `generate-module-docs` subagent 提供预提取的源码片段，避免读取整文件。

### 写入路径

```
<项目目录>/.deepwiki/cache/snippets/<safe_page_id>.json
```

### 最小字段

| 字段 | 说明 |
|------|------|
| `page_id` | 对应 `generation-plan.json` 中的页面 id |
| `snippets` | 源码片段列表 |
| `snippets[].path` | 源码文件相对路径 |
| `snippets[].lines` | 行号范围字符串（如 `"19-93"`） |
| `snippets[].content` | 行号范围 + 两侧各 5 行上下文的实际源码内容 |
| `snippets[].label` | 来源标签（对应 `core_source_ranges` 的 label） |

### 字段语义

- 每个 snippet 包含 `ranges` 中定义的行号范围，加上下文各 5 行
- 单个 snippet 内容上限 30000 字符，超出时截断并标注
- `page_id` 中 `:`、`/`、`\` 替换为 `_` 作为文件名（如 `deep-dive_pkg_auth.json`）
- 仅 `generation-plan.json` 中有 `source_files` 且 `ranges` 非空的页面才生成 snippets

### 降级策略

- 若 snippets 文件不存在，subagent 回退到自行读取源码文件（按 ranges 或整文件）
- 若源码文件不存在（如已删除），跳过该 snippet

---

## `evidence-index.json` 输出规范

> `evidence-index.json` 把"文档中的关键结论"与"源码中的可验证事实"关联起来，是后续质量门控的基础。

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
