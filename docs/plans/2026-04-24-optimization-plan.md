# DeepWiki Skill 优化实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 按 优化1→3→2→4→5→6→7→8 顺序对 deepwiki-skill 的 references/ 规范文档实施 8 项结构性优化

**Architecture:** 纯文档改造，不涉及脚本逻辑变更；所有变更限于 references/ 和 SKILL.md；新增两份规范文档（file-role-classification.md、analysis-output-spec.md）

**Tech Stack:** Markdown 文档编辑；涉及文件：SKILL.md、references/system-reference.md、references/workflow/extract-docs.md、references/workflow/generate-skeleton.md、references/rules/codepurpose-detection.md、references/rules/quality-standards.md、references/rules/menu-archetypes.md、references/generation/getting-started-page.md；新增：references/rules/file-role-classification.md、references/rules/analysis-output-spec.md

---
<!-- Tasks below -->

---

## Task 1：优化1 — 统一步骤编号，废弃双轨引用体系

> **问题**：`system-reference.md` 和各 workflow 文档混用"第N步"数字编号与工具名引用，导致 AI 执行时步骤定位困惑。
>
> **目标**：全局统一使用工具名引用，废弃"第N步/步骤N"数字引用；在 `system-reference.md` 的脚本表格中增加"工作流工具名"列，建立一一映射作为唯一索引。

**Files:**
- Modify: `references/system-reference.md`
- Modify: `references/workflow/generate-skeleton.md`
- Modify: `references/workflow/generate-module-docs.md`

**Step 1：修改 `system-reference.md` — 脚本列表增加"工作流工具名"列**

找到 `### 脚本列表` 下的2列表格，替换为3列版本：

```markdown
| 脚本 | 工作流工具名 | 用途 |
|------|------------|------|
| `scripts/init_wiki.py <项目路径>` | `init-wiki` | 初始化 .deepwiki 目录 |
| `scripts/analyze_project.py <项目路径>` | `analyze-project` | 分析项目结构和技术栈（同时生成 `cache/project-digest.md`） |
| `scripts/extract_structure.py <项目路径>` | `extract-structure` | 提取调用图、代码模式、关键时序和导入关系 |
| `scripts/generate_architecture_skeleton.py <项目路径>` | `generate-skeleton` | 从确定性缓存文件提取精简摘要，输出 `cache/architecture-skeleton-input.json` |
| `scripts/detect_changes.py <项目路径>` | `detect-changes` | 检测文件变更，用于增量更新（含反向依赖传播） |
| `scripts/extract_docs.py <文件路径>` | `extract-docs`（预提取子步骤） | 从源码提取文档注释 |
| `scripts/check_analysis_quality.py <项目路径>` | `check-analysis-quality` | 检查 `module-analysis.json` 是否满足最低质量标准 |
| `scripts/check_quality.py <.deepwiki路径>` | `generate-module-docs`（收尾质检） | 检查文档质量（含源码链接有效性验证） |
| `scripts/generate_menu.py <wiki目录路径> [项目名称]` | `generate-menu` | 生成层级化导航菜单 menu.json |
| `scripts/fix_mermaid.py <.deepwiki路径>` | `generate-module-docs`（Mermaid 修复子步骤） | 修复 Mermaid 图表语法错误 |
```

**Step 2：修改 `system-reference.md` — 输出目录结构表删除"第N步"注释**

将 `## 输出目录结构` 表格中含"第N步"字样的描述替换为工具名：
- `cache/architecture-skeleton-input.json` 行："第 3.5 步脚本" → "`generate-skeleton` 脚本段"
- `cache/architecture-skeleton.json` 行："第 3.5 步 AI" → "`generate-skeleton` AI段"
- `cache/module-analysis.json` 行："第 5 步" → "`extract-docs`"
- `wiki/overview.md` 行："（第 7 步生成）" → "（`generate-overview` 生成）"
- `wiki/doc-map.md` 行："（第 7 步基于 menu.json 生成）" → "（`generate-menu` 生成）"

**Step 3：修改 `generate-skeleton.md` — 警告信息中的 `[Step 3.5]` 改为工具名**

找到（约第 199 行）：

```
⚠️ [Step 3.5] 架构骨架生成失败，后续步骤将以无全局上下文模式运行
```

替换为：

```
⚠️ [generate-skeleton] 架构骨架生成失败，后续步骤将以无全局上下文模式运行
```

**Step 4：修改 `generate-module-docs.md` — 删除章节标题的数字后缀**

将以下5处标题去掉括号内的数字编号：

```
## 模块文档统一上下文（9.1）  →  ## 模块文档统一上下文
## 保存与 meta.json 更新（9.2）  →  ## 保存与 meta.json 更新
## 菜单校验（9.3）  →  ## 菜单校验
## Mermaid 语法修复（9.4）  →  ## Mermaid 语法修复
## 文档质量检查（9.5）  →  ## 文档质量检查
```

**Step 5：验证 — 搜索残留步骤编号**

```bash
grep -rn "第.*步\|Step [0-9]\." references/workflow/ references/system-reference.md
```

预期：只有 `generate-skeleton.md` 内部的 `### 第一步`、`### 第二步`、`### 第三步`（工具内部操作步骤，属于合理保留）。

**Step 6：Commit**

```bash
git add references/system-reference.md references/workflow/generate-skeleton.md references/workflow/generate-module-docs.md
git commit -m "docs(opt1): 统一步骤引用为工具名，废弃双轨数字编号体系"
```

---

## Task 2：优化3 — 修复 semantic_group 鸡蛋问题，引入单向数据流修正

> **问题**：`generate-skeleton`（前置）的 `module_groups` 作为约束传递给 `extract-docs`（后置），但骨架准确性本身依赖分析结果，形成先有鸡还是先有蛋的矛盾，导致 `semantic_group` 系统性偏移。
>
> **目标**：① 明确 `module_groups` 为"初始建议"非硬约束；② `extract-docs` 允许输出 `semantic_group_override: true` 标记；③ `generate-menu` 以 override 优先，并回写修正到骨架文件；④ `schemas/module-analysis-schema.json` 增加 `semantic_group_override` 字段。

**Files:**
- Modify: `references/workflow/generate-skeleton.md`
- Modify: `references/workflow/extract-docs.md`
- Modify: `references/workflow/generate-menu.md`
- Modify: `schemas/module-analysis-schema.json`

**Step 1：修改 `generate-skeleton.md` — 注入模板声明改为"建议"而非约束**

找到 `### 在extract-docs中注入骨架摘要` 小节，将 prompt 模板中的：

```
模块分组（请保持你的 semantic_group 与以下分组一致）：
```

替换为：

```
模块分组（以下分组为初始建议，非硬约束。若源码实际职责与建议不符，可输出 semantic_group_override: true 并使用更准确的命名）：
```

**Step 2：修改 `extract-docs.md` — 字段表格增加 override 规则，semantic_group 命名指南末尾新增冲突处理小节**

在 `### 每个模块必须写入的字段` 表格的 `semantic_group` 行描述末尾追加：

> 若分析结果与骨架建议分组不符，可同时写入 `semantic_group_override: true`，表明此命名来自深度分析；`generate-menu` 优先采用带 override 标记的命名。

在 `semantic_group 命名指南` 的"多模块同组示例"之后追加新小节：

```markdown
### 与骨架建议冲突时的处理

| 情形 | 操作 |
|------|------|
| 骨架建议名与源码职责吻合 | 直接使用，不写 `semantic_group_override` |
| 骨架建议过于宽泛，源码有更精确语义 | 使用精确命名，写 `semantic_group_override: true` |
| 骨架将两个明显独立职责归为一组 | 各自独立命名，各自写 `semantic_group_override: true` |
| 骨架 `reason` 字段含"import"（来自精确 import 数据） | 倾向保留骨架建议，慎用 override |
```

**Step 3：修改 `generate-menu.md` — 层2之前新增 override 前置检查，末尾追加骨架回写说明**

在 `#### 层2 决策矩阵` 标题之前插入：

```markdown
#### 前置检查：semantic_group_override 优先读取

在执行层2算法之前，扫描 `module-analysis.json` 中所有含 `semantic_group_override: true` 的条目：
- 这些模块的 `semantic_group` 来自深度源码分析，置信度视同 `high`
- 层2中这些模块的语义标注不再与骨架建议对比，直接作为分组命名依据
- 所有 override 模块命名确认后，**回写修正**到 `cache/architecture-skeleton.json` 对应的 `module_groups[].name`
```

在 `#### 层2 决策矩阵` 之后追加骨架回写说明：

```markdown
#### 骨架回写（菜单生成后执行）

`menu.json` 生成完毕后，将 override 修正结果写回：
1. 读取 `cache/architecture-skeleton.json`
2. 对每个 `semantic_group_override: true` 的模块，找到骨架中包含该模块的 `module_groups` 条目
3. 将 `name` 更新为 override 后的 `semantic_group`（不改 `modules` 和 `role`）
4. 写回文件

**目的**：确保骨架作为 `generate-overview` 和 `generate-module-docs` 共享上下文时，反映深度分析修正后的分组命名，消除骨架与文档内容的不一致。
```

**Step 4：修改 `schemas/module-analysis-schema.json` — 新增 `semantic_group_override` 字段**

在 `semantic_group_confidence` 字段定义的同层级下方插入：

```json
"semantic_group_override": {
  "type": "boolean",
  "description": "true 表示此 semantic_group 来自深度源码分析，与 generate-skeleton 骨架建议不一致；generate-menu 优先采用此命名并回写修正到骨架文件。",
  "default": false
}
```

**Step 5：验证三文件逻辑闭环**

```bash
grep -rn "semantic_group_override" references/ schemas/
```

预期：在 `generate-skeleton.md`、`extract-docs.md`、`generate-menu.md`、`schemas/module-analysis-schema.json` 共4处出现。

**Step 6：Commit**

```bash
git add references/workflow/generate-skeleton.md references/workflow/extract-docs.md references/workflow/generate-menu.md schemas/module-analysis-schema.json
git commit -m "docs(opt3): 修复 semantic_group 鸡蛋问题，引入 override 标记与骨架回写机制"
```

---

## Task 3：优化2 — 拆分 extract-docs 职责，新建两份独立规范文档

> **问题**：`extract-docs.md` 同时承担文件角色分类、读取深度决策、语义分析流程、分析结果持久化规范、semantic_group 命名指南等5+职责，AI 注意力分散。
>
> **目标**：将文件角色分类规则迁移到 `file-role-classification.md`，将输出规范迁移到 `analysis-output-spec.md`；`extract-docs.md` 保留核心决策逻辑并改为引用；更新 `SKILL.md` 工具索引表。

**Files:**
- Create: `references/rules/file-role-classification.md`
- Create: `references/rules/analysis-output-spec.md`
- Modify: `references/workflow/extract-docs.md`
- Modify: `SKILL.md`

**Step 1：创建 `references/rules/file-role-classification.md`**

新建文件，将 `extract-docs.md` 中 `## 文件角色分类（双层分类）` 整节（含第一层/第二层规则）原文迁移过来，添加文件头：

```markdown
# 文件角色分类规则

> 本文件定义文件的双层角色分类规则（CodePurpose 检测的文件级应用），是 `extract-docs` 分析阶段的前置分类步骤。
>
> **关联文档**：[`codepurpose-detection.md`](codepurpose-detection.md)（模块级 CodePurpose 检测信号）、[`../workflow/extract-docs.md`](../workflow/extract-docs.md)（分析执行流程）

---

[此处完整迁移 extract-docs.md 中"文件角色分类（双层分类）"的全部内容，保持原格式不变]
```

**Step 2：创建 `references/rules/analysis-output-spec.md`**

新建文件，将 `extract-docs.md` 中以下三节原文迁移：
1. `## 分析结果持久化`（含写入时机、路径、必须字段表格、降级处理）
2. `### semantic_group 命名指南`（含命名步骤、对比表、多模块同组示例）
3. Task 2（优化3）中新增的"与骨架建议冲突时的处理"小节

文件头：

```markdown
# 分析结果输出规范（module-analysis.json）

> 本文件定义 `extract-docs` 阶段向 `cache/module-analysis.json` 写入的完整规范：写入时机、必须字段、semantic_group 命名规则及骨架冲突处理。
>
> **关联 Schema**：[`../../schemas/module-analysis-schema.json`](../../schemas/module-analysis-schema.json)
>
> **关联文档**：[`../workflow/extract-docs.md`](../workflow/extract-docs.md)（分析执行流程）

---

[此处完整迁移以上三节内容]
```

**Step 3：修改 `extract-docs.md` — 删除已迁移内容，改为引用**

将 `## 文件角色分类（双层分类）` 整节替换为：

```markdown
## 文件角色分类

> 完整分类规则见 [`../rules/file-role-classification.md`](../rules/file-role-classification.md)。
>
> **执行要点**：在读取每个文件之前先完成分类，角色标签用于生成文档时的针对性描述。
```

将 `## 分析结果持久化` 整节（含 semantic_group 命名指南）替换为：

```markdown
## 分析结果持久化

> 完整输出规范（必须字段、写入时机、semantic_group 命名规则、骨架冲突处理）见 [`../rules/analysis-output-spec.md`](../rules/analysis-output-spec.md)。

**核心约束（此处重申）**：
- 完成每个模块分析后**立即写入** `cache/module-analysis.json`，采用增量追加模式
- 不要等全部模块完成后统一写入——中途中断将导致已分析数据全量丢失
```

**Step 4：修改 `SKILL.md` — 工具索引表末尾追加两份规范文档**

在 `## 工具索引` 的表格最后一行之后追加：

```markdown
| `file-role-classification`（规则） | [references/rules/file-role-classification.md](references/rules/file-role-classification.md) |
| `analysis-output-spec`（规范） | [references/rules/analysis-output-spec.md](references/rules/analysis-output-spec.md) |
```

**Step 5：验证内容完整性**

```bash
# 确认新文件已创建
ls references/rules/

# 确认 extract-docs.md 中对两份新文件的引用格式正确
grep -n "file-role-classification\|analysis-output-spec" references/workflow/extract-docs.md

# 确认 SKILL.md 索引已更新
grep -n "file-role-classification\|analysis-output-spec" SKILL.md
```

**Step 6：Commit**

```bash
git add references/rules/file-role-classification.md references/rules/analysis-output-spec.md references/workflow/extract-docs.md SKILL.md
git commit -m "docs(opt2): 拆分 extract-docs 职责，新增 file-role-classification 和 analysis-output-spec 规范文档"
```

---

## Task 4：优化4 — 重建质量评分标准，对齐忠实性和可理解性目标

> **问题**：当前评分以"代码示例(25%)"为必须项，对 Config/Model 等无示例价值的模块会产生填充内容；"3个H2章节"也对简单模块产生空壳，违背 P1忠实性和 P2可理解性。
>
> **目标**：用5个与工程目标对齐的质量维度替代当前评分；将"代码示例"降为条件必须项；章节数要求改为动态参考值。

**Files:**
- Modify: `references/rules/quality-standards.md`

**Step 1：替换 `### 评分公式` 小节**

找到 `### 评分公式` 及下方表格，全部替换为：

```markdown
### 评分公式

加权评分：忠实性 30% + 可理解性 25% + 结构完整性 20% + 视觉辅助 15% + 可导航性 10%

| 维度 | 检查项 | 权重 |
|------|--------|------|
| **忠实性** | 所有章节有 Section sources 链接且链接有效 | 30% |
| **可理解性** | `key_insights` 非空且 ≥ 2 条（解释 WHY，非 WHAT） | 25% |
| **结构完整性** | 章节数 ≥ 模块重要性对应的动态最低值（见下方动态期望值表） | 20% |
| **视觉辅助** | Mermaid 图表数量 ≥ 与模块复杂度匹配的期望值 | 15% |
| **可导航性** | 含交叉链接 + nav-links 组件 | 10% |

> **代码示例是条件必须项**：`CodePurpose in [Api, Util, Widget, Dao, Service, Command]` 时，缺少代码示例扣 15 分（等同于视觉辅助维度全失）。`CodePurpose in [Config, Model, Database, Test, Other]` 时代码示例为可选项，缺失不影响评分。
```

**Step 2：更新 `### 硬门槛` 小节**

找到 `### 硬门槛`，删除"代码示例是必须项"的隐含表述，替换为：

```markdown
### 硬门槛

- **源码追溯是强制要求**。缺少时，无论其他指标如何，质量等级上限为 `basic`。
- **源码链接全部失效时**，同样降级为 `basic`。
- **`key_insights` 全部为空时**（模块分析深度不足），质量等级上限为 `standard`。
```

**Step 3：更新 `### 动态期望值` 表格**

将当前4列表格替换为5列版本（新增"最低 key_insights 数"列，同时调低章节数期望值）：

```markdown
| 模块重要性 | 最低行数 | 最低章节 | 最低图表 | 最低 key_insights |
|-----------|---------|---------|---------|-----------------|
| 高（>= 0.6） | 200 | 6 | 2 | 3 |
| 中（0.4-0.6） | 120 | 4 | 1 | 2 |
| 低（< 0.4） | 60 | 3 | 1 | 1 |
```

**Step 4：在 `## 模板设计原则` 之前新增"评分与工程目标的对应关系"说明**

```markdown
## 评分维度与工程目标的对应关系

| 评分维度 | 对应工程目标 | 设计原因 |
|---------|------------|---------|
| 忠实性（源码追溯） | P1：文档必须与源码对应，无幻觉 | 让读者能直接验证文档内容 |
| 可理解性（key_insights WHY） | P2：读者能快速建立心智模型 | 理解"为什么"比"是什么"更有价值 |
| 结构完整性（章节数动态） | P2：人工阅读可读性高 | 动态要求，避免简单模块堆砌空壳章节 |
| 视觉辅助（图表） | P2：可读性辅助 | Mermaid 图表帮助读者快速理解结构 |
| 可导航性（链接） | P2：文档网络连贯性 | 交叉链接让读者能在文档网络中导航 |
```

**Step 5：Commit**

```bash
git add references/rules/quality-standards.md
git commit -m "docs(opt4): 重建质量评分标准，对齐忠实性和可理解性目标，代码示例降为条件必须项"
```

---

## Task 5：优化5 — 新增 monorepo archetype 及对应分析策略

> **问题**：当前 archetype 列表缺少 `monorepo`，50+包的大型仓库没有专门分析策略；`synthesize-deps` 的150文件截断在 monorepo 下会导致依赖图不完整。
>
> **目标**：在 `extract-structure.md`、`extract-docs.md`、`menu-archetypes.md`、`synthesize-deps.md` 四处增加 monorepo 支持。

**Files:**
- Modify: `references/workflow/extract-structure.md`
- Modify: `references/workflow/extract-docs.md`
- Modify: `references/workflow/synthesize-deps.md`
- Modify: `references/rules/menu-archetypes.md`

**Step 1：修改 `extract-structure.md` — archetype 枚举增加 monorepo，并追加检测逻辑说明**

在 `archetype` 字段枚举值末尾（`generic` 之前）追加 `monorepo`：

```
`spa-frontend` / `web-service` / `cli-tool` / `sdk-library` / `ml-project` / `agent-project` / `fullstack-framework` / `monorepo` / `generic`
```

在 `archetype` 行的"后续用途"描述末尾追加：
```
`monorepo`（包间依赖关系/共享模块/各子包独立入口/跨包调用链）
```

在文档末尾追加新节：

```markdown
## Monorepo 检测逻辑

当 `analyze-project` 在 `structure.json` 中检测到 `is_monorepo: true` 时，`extract-structure` 自动将 archetype 设为 `monorepo`，并调整分析单位：

| 普通项目 | Monorepo |
|---------|---------|
| 以目录模块为分析单位 | 以 package（子包）为分析单位 |
| `core_files` 覆盖全仓库 | `core_files` 优先覆盖各 package 的入口文件 |
| `import_relations` 为全仓库文件图 | `import_relations` 额外标注跨包引用（`cross_package: true`） |
```

**Step 2：修改 `extract-docs.md` — archetype 分析侧重点增加 monorepo**

找到 `| archetype | 决定分析侧重点：...` 的描述行，在已有 archetype 列表末尾追加：

```
`monorepo`（包间依赖关系/共享包/各子包独立入口/跨包调用链）
```

**Step 3：修改 `synthesize-deps.md` — 增加 monorepo 截断策略**

找到 `## 输入选择（三阶段漏斗）` 的"数量截断"条目，在其后追加：

```markdown
**Monorepo 特殊截断策略**：当 archetype == `monorepo` 时：
- 以 package 为单位截断：每个 package 最多取 30 个高优先级文件（`importance_score >= 0.5`）
- 跨包 import 关系（`cross_package: true`）全量保留，不截断
- 优先保留各 package 的入口文件和对外公开的 API 文件
- 若 package 总数 > 20，对低重要性 package（`importance_score < 0.3`）整体跳过，仅记录其对外接口声明
```

**Step 4：修改 `menu-archetypes.md` — 在 `## generic` 之前插入 monorepo 原型**

```markdown
## monorepo（多包仓库类）

**常见语义主题：**
- 入门与工作区配置（Getting Started / Workspace Setup）
- 共享基础设施（Shared / Common / Core packages）
- 各业务域 package（按功能域聚合）
- 工具链与脚本（Tooling & Scripts）
- 扩展与插件（Extensions & Plugins）

**粒度建议：** 以 package 为文档单元；共享 package 单独成区且排在前面；业务 package 按功能域聚合而非逐个列出；工具链和 CI 相关归入"基础设施"区

**特殊处理：**
- `overview.md` 需包含"工作区结构"章节，展示 package 间依赖拓扑图（Mermaid flowchart）
- 各 package 文档通过 `nav-links` 指向共享依赖的文档
- package 版本独立发布时，文档首部标注版本号

**反模式：**
- ❌ 把每个 package 都展开为顶层区块——packages 数量多时应按功能域聚合
- ❌ 把共享工具 package 和业务 package 混在同一区块——共享包是基础设施，应独立成区
- ❌ 按目录层级（`packages/a`、`packages/b`）直接翻译为菜单——应按语义功能分组

---
```

**Step 5：验证 monorepo 在4个文件中均有出现**

```bash
grep -rn "monorepo" references/workflow/extract-structure.md references/workflow/extract-docs.md references/workflow/synthesize-deps.md references/rules/menu-archetypes.md
```

**Step 6：Commit**

```bash
git add references/workflow/extract-structure.md references/workflow/extract-docs.md references/workflow/synthesize-deps.md references/rules/menu-archetypes.md
git commit -m "docs(opt5): 新增 monorepo archetype，含分析策略、截断规则和菜单分组指南"
```

---

## Task 6：优化6 — getting-started.md 增加 archetype 感知差异化模板

> **问题**：`getting-started-page.md` 使用统一的"安装→示例→FAQ"模板，无法区分 SDK/Agent/全栈框架/CLI 等项目类型的快速开始侧重点。
>
> **目标**：新增"Archetype 感知章节差异"表格，骨架模板中"基本用法"章节增加条件注释，与 `menu-archetypes.md` 的分组思路对称。

**Files:**
- Modify: `references/generation/getting-started-page.md`

**Step 1：在 `## 页面骨架` 之前插入 Archetype 感知差异表**

```markdown
## Archetype 感知：差异化章节模板

根据 `cache/code-structure.json` 中的 `archetype` 字段，差异化"基本用法"章节的内容侧重和额外必需章节：

| Archetype | "基本用法"章节重点 | 额外必需章节 |
|-----------|----------------|------------|
| `sdk-library` | install → import → 调用核心 API → 查看输出 | **集成指南**（如何添加到已有项目、框架兼容性） |
| `agent-project` | 配置 LLM provider → 创建 Agent → 发送首条消息 | **配置说明**（API Key、工具注册、记忆后端） |
| `fullstack-framework` | scaffolding → 创建第一个路由 → 启动开发服务器 | **项目结构说明**（约定目录和命名规范） |
| `cli-tool` | 安装 → 运行 `--help` → 执行核心命令 | **配置文件说明**（配置文件位置和基本选项） |
| `ml-project` | 数据准备 → 训练 → 推理最小示例 | **环境依赖说明**（CUDA版本、数据集格式） |
| `spa-frontend` | clone → install → `npm run dev` → 访问首页 | **环境变量说明**（API 地址、认证配置） |
| `web-service` | 启动服务 → 调用第一个端点 → 查看响应 | **数据库初始化**（migrate 命令和初始数据） |
| `monorepo` | clone → install → 运行某个 package | **工作区命令速查**（如何只构建/测试某个 package） |
| `generic` | 使用通用模板（与现有骨架相同） | 无额外要求 |
```

**Step 2：修改骨架中 `## 基本用法` 章节，增加 archetype 条件注释**

找到骨架中的：

```markdown
## 基本用法

[code-example 组件：最小可运行示例]
```

替换为：

```markdown
## 基本用法

<!-- archetype 感知：根据上方"Archetype 感知章节差异"表格选择对应模板 -->
[code-example 组件：最小可运行示例（内容依 archetype 差异化）]

<!-- 条件章节：根据 archetype 生成对应的额外必需章节（见上方表格的"额外必需章节"列） -->
[对应 archetype 的额外必需章节（generic 时跳过）]
```

**Step 3：Commit**

```bash
git add references/generation/getting-started-page.md
git commit -m "docs(opt6): getting-started 增加 archetype 感知差异表，覆盖8种项目类型"
```

---

## Task 7：优化7 — 文件角色分类增加编程语言特定信号

> **问题**：`file-role-classification.md`（Task 3 新建）的第二层语义推断仅有4条通用规则，对 Go/Rust/Java/Kotlin 等不遵循惯例目录命名的项目检测效果差。
>
> **目标**：在第二层末尾增加语言特定信号表，同时在 `codepurpose-detection.md` 中增加指向说明。

**Files:**
- Modify: `references/rules/file-role-classification.md`（Task 3 新建）
- Modify: `references/rules/codepurpose-detection.md`

**Step 1：修改 `file-role-classification.md` — 第二层末尾追加语言特定信号表**

在"第二层：语义推断"的4条通用规则之后，追加：

```markdown
### 语言特定信号（通用规则无法判断时适用）

| 语言 | 代码信号 | 推断角色 |
|------|---------|---------|
| **Go** | 含 `http.HandleFunc`、`gin.GET`、`echo.GET`、`mux.Handle` | `Api` |
| **Go** | 含 `sql.Query`、`db.Exec`、`gorm.Find`、`sqlx.Get` | `Dao` |
| **Go** | 含 `func main()` 且在 `main` package | `Entry` |
| **Rust** | 含 `#[tokio::main]` 或 `fn main()` | `Entry` |
| **Rust** | 含 `impl Trait`（Trait 为外部接口名） | `Service` |
| **Rust** | 含 `axum::Router`、`actix_web::HttpServer` | `Api` |
| **Java/Kotlin** | 含 `@RestController`、`@Controller` 注解 | `Api` |
| **Java/Kotlin** | 含 `@Repository`、`@Mapper` 注解 | `Dao` |
| **Java/Kotlin** | 含 `@Service`、`@Component`（无 `@Controller`） | `Service` |
| **Java/Kotlin** | 含 `@Entity`、`@Table` 注解 | `Model` |
| **Java/Kotlin** | 含 `@SpringBootApplication`、`fun main(` | `Entry` |
| **Python** | 含 `@app.route`、`@router.get`、`@router.post` | `Api` |
| **Python** | 继承 `BaseModel`（Pydantic）、`SQLModel` | `Model` |
| **Python** | 含 `if __name__ == "__main__"` 且调用核心业务函数 | `Entry` |
| **Python** | 含 `@pytest.fixture` 或函数名以 `test_` 开头 | `Test` |

> **应用顺序**：第一层路径规则 → 第二层通用语义规则 → 本语言特定信号表。只有前两步都无法确定时才查此表。
```

**Step 2：修改 `codepurpose-detection.md` — 检测信号表后追加引用说明**

在 `## CodePurpose 检测信号` 表格之后追加：

```markdown
> **语言特定信号扩展**：当上表的路径/文件名模式无法匹配时，参见 [`file-role-classification.md`](file-role-classification.md) 第二层语义推断的"语言特定信号"表格，适用于 Go / Rust / Java / Kotlin / Python 的框架注解和语法特征检测。
```

**Step 3：Commit**

```bash
git add references/rules/file-role-classification.md references/rules/codepurpose-detection.md
git commit -m "docs(opt7): 文件角色分类增加 Go/Rust/Java/Kotlin/Python 语言特定检测信号"
```

---

## Task 8：优化8 — 增量更新加入语义变更类型感知

> **问题**：`detect-changes` 仅做文件哈希比对，注释修改也会触发整个模块的全量重分析，浪费 Token。
>
> **目标**：在 `detect-changes.md` 中扩展变更分类为3种语义类型（`api-change` / `impl-change` / `doc-only-change`）；在 `extract-docs.md` 的变更筛选章节引用新类型，实现最小重分析范围。

**Files:**
- Modify: `references/workflow/detect-changes.md`
- Modify: `references/workflow/extract-docs.md`

**Step 1：修改 `detect-changes.md` — 替换 `## 文件分类` 表格**

将当前3行表格（新增/修改/删除）全部替换为：

```markdown
| 分类 | 判断依据 | 处理方式 |
|------|---------|---------|
| **新增文件** | 文件不在 `checksums.json` 中 | 排入完整文档生成队列 |
| **删除文件** | 文件在 `checksums.json` 中但已不存在 | 将现有文档标记为废弃 |
| **修改文件（api-change）** | 哈希变更 + 含 `export`/`pub`/`public` 的声明行发生变化 | 完整重分析队列 + 触发反向依赖传播 |
| **修改文件（impl-change）** | 哈希变更 + 公开接口行未变 + 非注释行有变化 | 定向重分析队列：仅更新 `key_insights` |
| **修改文件（doc-only-change）** | 哈希变更 + 仅注释/文档字符串行变化 | 轻量更新队列：仅更新文件 `summary` |

> **变更类型判断是尽力而为（best-effort）**：脚本通过对比前后版本的"重要行"（含 `export`/`def`/`fn`/`class`/`public` 的行）是否变化来区分 `api-change` 与 `impl-change`。无法判断时退化为 `api-change`（保守策略，确保不遗漏重要变更）。
```

**Step 2：在 `detect-changes.md` 末尾追加"输出字段扩展"说明**

```markdown
## 输出字段扩展

脚本在变更列表中为每个修改文件附带 `change_type` 字段：

```json
{
  "affected_modules": ["auth", "api"],
  "reverse_affected_modules": ["core"],
  "changed_files": [
    {"path": "src/auth/service.py", "change_type": "api-change"},
    {"path": "src/auth/utils.py", "change_type": "impl-change"},
    {"path": "docs/auth.md", "change_type": "doc-only-change"}
  ]
}
```

`extract-docs` 根据 `change_type` 决定每个文件的最小重分析深度（见 `extract-docs.md` → 变更筛选章节）。
```

**Step 3：修改 `extract-docs.md` — 变更筛选章节替换为引用变更类型的版本**

找到 `## 变更筛选（基于detect-changes结果）` 整节，替换为：

```markdown
## 变更筛选（基于detect-changes结果）

根据 `detect-changes` 结果筛选待处理文件，并按 `change_type` 决定最小重分析深度：

- **首次生成**（无变更记录）：处理所有模块的核心文件，执行完整分析。

- **增量更新**：

  | change_type | 重分析范围 | 反向依赖传播 |
  |------------|-----------|------------|
  | `api-change` | 完整重分析：更新 `public_interfaces`、`key_insights`、`summary` | ✅ 触发 |
  | `impl-change` | 定向重分析：仅重读实现部分，更新 `key_insights` | ❌ 不触发 |
  | `doc-only-change` | 轻量更新：重跑 `extract_docs.py`，更新 `summary` | ❌ 不触发 |
  | 新增文件 | 完整分析（视同新模块） | 按所属模块处理 |
  | 删除文件 | 标记废弃，删除 `module-analysis.json` 中对应 `files[]` 条目 | ✅ 触发 |

  > **降级**：若 `changed_files` 中无 `change_type` 字段（旧版脚本输出），统一视为 `api-change`（向后兼容）。
```

**Step 4：Commit**

```bash
git add references/workflow/detect-changes.md references/workflow/extract-docs.md
git commit -m "docs(opt8): 增量更新增加语义变更类型感知，区分 api-change/impl-change/doc-only-change"
```

---

## Task 9：最终验证

**Step 1：验证所有 8 项优化的核心改动已落地**

```bash
# 优化1：废弃数字编号（仅 generate-skeleton 内部步骤名合理保留）
grep -rn "Step [0-9]\.\|第.*步[^骤]" references/workflow/ | grep -v "generate-skeleton.md"

# 优化3：semantic_group_override 在4处出现
grep -rn "semantic_group_override" references/ schemas/

# 优化2：两份新规范文件存在
ls references/rules/file-role-classification.md references/rules/analysis-output-spec.md

# 优化4：key_insights 出现在质量标准评分和硬门槛中
grep -n "key_insights" references/rules/quality-standards.md

# 优化5：monorepo 在4个文件中出现
grep -rn "monorepo" references/workflow/extract-structure.md references/workflow/synthesize-deps.md references/rules/menu-archetypes.md

# 优化6：getting-started 含 archetype 差异表
grep -n "sdk-library\|agent-project\|archetype" references/generation/getting-started-page.md

# 优化7：语言特定信号表已加入 file-role-classification.md
grep -n "RestController\|gin.GET\|tokio::main" references/rules/file-role-classification.md

# 优化8：api-change/impl-change/doc-only-change 在两个文件中均出现
grep -rn "api-change\|impl-change\|doc-only-change" references/workflow/
```

**Step 2：验证 SKILL.md 工具索引完整**

```bash
grep -n "file-role-classification\|analysis-output-spec" SKILL.md
```

**Step 3：最终整体状态确认**

```bash
git log --oneline -10
git status
```

预期：`git status` 显示 working tree clean（所有变更已 commit）。

---

