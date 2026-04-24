# DeepWiki Skill Source Intelligence Design

**Status:** Implemented baseline

**Date:** 2026-04-24

**Scope:** `SKILL.md`, `references/`, `scripts/`, `.deepwiki/cache/*`

## Implementation Summary

本设计已在 `feature/source-intelligence` 分支完成第一轮基线落地。

已完成的关键闭环：

- 新增并文档化 `doc-topology.json`、`generation-plan.json`、`evidence-index.json` 缓存契约
- 将模块发现结果明确为候选模块，并保留发现依据
- 扩展代码结构事实，覆盖注册点、状态访问、配置入口与跨模块桥接
- 新增 `plan-doc-topology` 文档拓扑规划阶段
- 将菜单生成切换为优先消费文档拓扑
- 强化模块分析质量门禁，要求模块角色、上下游、风险点与扩展点
- 新增 evidence-aware 文档验证
- 将增量更新扩展为页面感知
- 补齐本地 CLI 与依赖自检入口

## Context

当前项目已经具备一条清晰但不完全闭环的流水线：

- 前半段用脚本做确定性分析，产出 `structure.json`、`code-structure.json`、`file-hashes.json`
- 后半段由 skill 工作流和 agent 提示词负责语义综合、页面组织、文档生成

这个结构解决了“从零开始分析源码”的问题，但还没有完全解决“稳定地产出类似 DeepWiki 的高质量文档”。

当前瓶颈不是 Markdown 模板数量，而是中间表示不够强：

- 模块边界仍然偏目录启发式
- 全局系统模型没有独立的数据契约
- 文档树规划主要由 prompt 临场决定
- 质量检查偏字段完整性，不足以验证内容是否真正基于源码证据

## Goal

把当前项目从“文档生成型 skill”升级为“源码认知编译型 skill”。

具体来说：

- 让脚本更多负责提取稳定事实和可复用中间表示
- 让 agent 更多负责归纳、表达、解释，而不是决定全部结构
- 让文档生成流程从“直接写页面”改成“先生成文档拓扑和证据索引，再编译页面”
- 让增量更新作用于“认知模型和页面计划”，而不只是模块名

## Non-Goals

- 不把项目改造成独立 SaaS 或服务端产品
- 不在这一轮引入数据库、Web UI 或远程任务调度
- 不追求一次性重写全部脚本
- 不要求所有文档正文都改为纯确定性生成

## Design Principles

### 1. Facts First

先提取事实，再做解释。

- `structure.json`、`code-structure.json` 只放可验证事实或低推断摘要
- 推断性的语义归纳放到 `module-analysis.json`
- 文档正文中的关键结论必须可回溯到缓存中的事实

### 2. Separate Source Topology From Doc Topology

源码结构不等于文档结构。

- 一个源码模块可以拆成多个文档主题
- 多个源码模块也可以合并为一个问题域页面
- 页面树应服务“30 秒看轮廓、3 分钟看主路径、15 分钟开始改”

### 3. Compile, Don’t Improvise

生成文档前，先生成计划。

- 先生成 `doc-topology.json`
- 再生成 `generation-plan.json`
- 最后编译页面和菜单

这样可以减少不同 agent、不同上下文下的随机漂移。

### 4. Verification Over Formatting

质量检查重点从“字段齐不齐”升级到“结论是否有证据、页面之间是否一致、主路径是否可追溯”。

## Target Architecture

建议将项目重组为四层。

### 1. Discovery Layer

负责项目发现：

- 项目类型
- 主要语言
- 入口文件
- 模块候选
- 核心文件
- 现有文档

映射到当前实现：

- `scripts/analyze_project.py`
- `scripts/module_discovery.py`
- `scripts/scanner.py`

### 2. Source Intelligence Layer

负责源码事实提取：

- 调用图
- import 图
- 关键时序
- 模式检测
- 注册点和配置入口
- 状态源和跨模块桥接点

映射到当前实现：

- `scripts/extract_structure.py`
- `scripts/import_relations.py`
- `scripts/extract_doc_comments.py`

### 3. Documentation Planning Layer

这是新增的关键层，负责把源码理解映射成文档结构：

- 文档主题划分
- 页面粒度
- 阅读顺序
- 页面依赖关系
- 页面证据集合

新增契约：

- `doc-topology.json`
- `evidence-index.json`
- `generation-plan.json`

### 4. Doc Compile Layer

负责输出文档和验证：

- overview/getting-started/doc-map/module/api 页面生成
- menu 生成
- 跨页面一致性检查
- Mermaid 修复
- 增量重编译

映射到当前实现：

- `scripts/generate_menu.py`
- `scripts/finalize.py`
- `scripts/check_doc_quality.py`
- `scripts/check_cross_module_consistency.py`

## Data Contracts

### Keep: `structure.json`

继续作为项目发现层契约，职责保持不变：

- 项目名
- 项目类型
- 语言
- 入口点
- 模块候选
- 核心文件 / 高优先级文件
- 文件统计

建议新增字段：

- `module_candidates`
- `runtime_roots`
- `state_roots`
- `registration_files`

### Expand: `code-structure.json`

在现有字段基础上继续扩充：

- `call_graph`
- `import_relations`
- `patterns`
- `key_sequences`
- `entry_points`

建议新增：

- `registration_points`
- `state_access_paths`
- `config_entry_points`
- `cross_module_bridges`

### Upgrade: `module-analysis.json`

从“松散分析结果”升级成“模块认知模型”。

每个模块至少应包含：

- `module_path`
- `module_summary`
- `module_role`
- `upstream_inputs`
- `downstream_outputs`
- `key_interfaces`
- `state_sources`
- `extension_points`
- `risk_points`
- `semantic_group`
- `selected_components`
- `files`

### Add: `doc-topology.json`

负责描述文档知识树，而不是源码树。

建议结构：

- 页面列表
- 页面类型
- 每页覆盖的模块或主题
- 依赖页面
- 推荐阅读顺序
- 页面是否属于 overview/runtime/state/api/operations

### Add: `evidence-index.json`

负责把关键结论映射回源码证据。

建议结构：

- `claim_id`
- `page_id`
- `claim_text`
- `evidence`
- `confidence`

证据可指向：

- 文件路径
- 行号范围
- 调用图节点
- import 关系
- 入口链路

### Add: `generation-plan.json`

负责指导本轮实际编译。

建议字段：

- 要生成的页面
- 每页依赖的缓存文件
- 每页依赖的模块
- 页面是否受变更影响
- 可跳过页面

## Key Workflow Changes

### Change 1: Reframe Module Discovery

当前模块发现以目录为主，这对多数项目足够快，但对 deepwiki 风格文档还不够稳。

改造方向：

- 保留目录发现，作为 `module_candidates`
- 再基于 import 连通性修正
- 再基于入口可达性修正
- 再基于状态访问和注册关系修正

最终得到：

- 源码模块
- 文档模块

这两者允许不完全一致。

### Change 2: Add `plan-doc-topology`

在 `extract-docs` 之前增加拓扑规划阶段。

输入：

- `structure.json`
- `code-structure.json`
- `module-analysis.json` 的基础分析结果
- `architecture-skeleton.json`

输出：

- `doc-topology.json`
- `generation-plan.json`

这一步决定：

- 文档树长什么样
- 哪些模块要合并讲
- 哪些页面要强调运行时主路径
- 哪些页面要强调状态与扩展点

### Change 3: Make Menu Follow Topology

`generate_menu.py` 不应只在页面生成后“扫描目录拼菜单”。

它应优先读取：

- `doc-topology.json`
- `generation-plan.json`

再把磁盘上的实际页面作为校验对象，而不是主事实来源。

### Change 4: Promote Evidence-Based Validation

质量门控应分两层：

- 分析门控：检查 `module-analysis.json` 是否满足最低认知结构
- 文档门控：检查页面中的主结论是否有来源、页面之间是否冲突、主路径是否与入口链路一致

### Change 5: Incremental Updates Become Plan-Aware

增量更新不应只回答“哪些模块变了”，还应回答：

- 哪些缓存失效
- 哪些页面依赖这些缓存
- 哪些页面必须重编译
- 哪些页面可以保留

这要求 `detect_changes` 能和 `generation-plan.json` 对接。

## Skill-Specific Changes

因为这是一个 skill，不是独立应用，所以优化重点是“降低 agent 的认知负担”。

### `SKILL.md`

应从“大而全说明书”转向“调度入口 + 决策索引”：

- 按用户意图选择全量/增量/质量检查模式
- 明确每个步骤依赖的缓存契约
- 将复杂规则下沉到 `references/workflow/` 和 `references/rules/`

### `references/workflow/`

每个 workflow 文档应回答三件事：

- 输入是什么
- 输出契约是什么
- 失败时如何降级

### `references/rules/`

集中承载：

- 模块命名规则
- 页面粒度规则
- 证据引用规则
- 文档质量规则

## Minimal Engineering Work

为了保持 skill 可用性，需要补最小必要工程化：

- 单一 CLI 入口，用于本地自测与 smoke test
- 依赖检查脚本，优先检查 tree-sitter 相关依赖
- 更明确的错误信息，而不是在测试收集阶段直接失败
- 一组面向 fake project 的端到端 smoke tests

这部分是支撑 skill 的稳定性，不是要把项目改造成重型产品。

## Phased Rollout

### Phase 1: Contract Hardening

- 收紧 `structure.json`
- 扩展 `code-structure.json`
- 升级 `module-analysis.json`
- 引入 `doc-topology.json`

### Phase 2: Planning Before Writing

- 新增 `plan-doc-topology`
- 让 `generate-menu` 基于 topology
- 让 overview 和 module 页面基于 generation plan

### Phase 3: Evidence Validation

- 新增 `evidence-index.json`
- 升级分析质量门控
- 新增跨页面证据一致性检查

### Phase 4: Skill Stabilization

- 新增统一 CLI
- 新增依赖自检
- 补 smoke tests
- 优化失败恢复和错误提示

## Risks

### Risk 1: Contract Explosion

缓存文件变多后，理解门槛也会上升。

缓解：

- 每个缓存文件只承担单一职责
- 在 `references/system-reference.md` 中维护统一索引

### Risk 2: Prompt and Contract Divergence

如果 workflow 文档没及时跟上契约演进，agent 会重新退回“自由发挥”。

缓解：

- 优先改 contract 和 workflow，再改正文模板

### Risk 3: Over-Engineering

如果过早追求完全自动化，skill 会丧失轻量优势。

缓解：

- 保留 agent 的高层解释权
- 只把稳定、重复、易验证的部分脚本化

## Success Criteria

优化完成后，项目应满足：

- 同一仓库在不同 agent 会话中生成的页面树基本一致
- overview 的主路径可以回溯到 entry point 和 key sequence
- 模块文档的主要结论能回溯到源码证据
- 菜单结构不再主要依赖磁盘扫描结果
- 增量更新能明确回答“哪些页面要重编译”
- 在缺依赖时给出清晰报错和修复路径

## Recommendation

采用“中间表示强化型”为主、“最小工程化”为辅的路线。

原因很简单：

- 这最符合 skill 的轻量定位
- 这直接打在当前最核心的质量瓶颈上
- 这能最大化复用现有脚本，而不是推倒重来
