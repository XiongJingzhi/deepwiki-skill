#!/usr/bin/env python
# Helper: overwrite the restructure plan with updated design decisions
import pathlib

OUT = pathlib.Path(__file__).parent / "2026-04-24-skill-restructure.md"

CONTENT = """\
# DeepWiki SKILL.md 重构计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构 SKILL.md 和 references/ 目录，使工作流用 digraph 表达，workflow 文件按工具名原子化，去除步骤编号依赖，AI 生成辅助资料按类型归目录。

**Architecture:** SKILL.md 极度精简为"入口 + 路由 + digraph 流程图"；workflow 文件按脚本/工具名命名，开头声明 I/O 契约，内容里用工具名替代步骤编号；prompts/templates 按页面类型拆分到 `references/generation/`；辅助规则归入 `references/rules/`。

**Tech Stack:** Markdown, DOT digraph (文本格式), Python (断链验证)

---

## 设计决策

### workflow 文件命名规范

按**脚本/工具名**命名（方案 C），不含步骤编号：

| 原文件 | 新文件名 |
|--------|---------|
| `step1-init.md` | `init-wiki.md` |
| `step2-analyze.md` | `analyze-project.md` |
| `step3-extract-structure.md` | `extract-structure.md` |
| `step3.5-architecture-skeleton.md` | `generate-skeleton.md` |
| `step4-change-detection.md` | `detect-changes.md` |
| `step4-parallel-strategy.md` | `parallel-analysis.md` |
| `step4.5-analysis-quality-gate.md` | `check-analysis-quality.md` |
| `step5-source-analysis.md` | `extract-docs.md` |
| `step6-dependency-synthesis.md` | `synthesize-deps.md` |
| `step7-overview.md` | `generate-overview.md` |
| `step8-menu-and-docmap.md` | `generate-menu.md` |
| `step9-execution-strategy.md` | `generate-module-docs.md` |

### workflow 文件内容规范

每个文件**开头必须有 I/O 契约表**，内容里用工具名替代"第 N 步"：

```markdown
## 契约

| 项 | 值 |
|----|-----|
| **脚本** | `python scripts/xxx.py <项目路径>` |
| **输入** | `cache/structure.json`（由 `analyze-project` 生成） |
| **输出** | `cache/code-structure.json` |
| **前置** | `analyze-project` 完成 |
| **后置** | `generate-skeleton`、`detect-changes` |
```

内容中旧写法 → 新写法：
- ❌ `"供第 6 步和第 9 步使用"` → ✅ `"供 synthesize-deps 和 generate-module-docs 使用"`
- ❌ `"在第 4 步变更检测之后"` → ✅ `"在 detect-changes 完成后"`
- ❌ `"本文档对应工作流第 5 步"` → ✅ `"本文档定义 extract-docs 的执行规则"`

---

## 目标结构

```
references/
├── workflow/
│   ├── init-wiki.md
│   ├── analyze-project.md
│   ├── extract-structure.md
│   ├── generate-skeleton.md
│   ├── detect-changes.md
│   ├── parallel-analysis.md
│   ├── extract-docs.md
│   ├── check-analysis-quality.md
│   ├── synthesize-deps.md
│   ├── generate-overview.md
│   ├── generate-menu.md
│   └── generate-module-docs.md
├── generation/
│   ├── overview-page.md
│   ├── module-page.md
│   ├── api-page.md
│   ├── getting-started-page.md
│   └── docmap-page.md
├── rules/
│   ├── components.md
│   ├── codepurpose-detection.md
│   ├── quality-standards.md
│   └── menu-archetypes.md
├── system-reference.md
└── plugin.md
```

SKILL.md 精简后（目标 < 110 行）：
- frontmatter
- 运行模式（路由表）
- 工作流（digraph，节点=工具名）
- 工具索引表（工具名 → workflow/ 链接）
- 不适用场景
- 输出结构

---

## 变更映射表

| 原文件 | 操作 | 目标路径 |
|--------|------|---------|
| `references/step1-init.md` | **重命名+改内容** | `references/workflow/init-wiki.md` |
| `references/step2-analyze.md` | **重命名+改内容** | `references/workflow/analyze-project.md` |
| `references/step3-extract-structure.md` | **重命名+改内容** | `references/workflow/extract-structure.md` |
| `references/step3.5-architecture-skeleton.md` | **重命名+改内容** | `references/workflow/generate-skeleton.md` |
| `references/step4-change-detection.md` | **重命名+改内容** | `references/workflow/detect-changes.md` |
| `references/step4-parallel-strategy.md` | **重命名+改内容** | `references/workflow/parallel-analysis.md` |
| `references/step4.5-analysis-quality-gate.md` | **重命名+改内容** | `references/workflow/check-analysis-quality.md` |
| `references/step5-source-analysis.md` | **重命名+改内容** | `references/workflow/extract-docs.md` |
| `references/step6-dependency-synthesis.md` | **重命名+改内容** | `references/workflow/synthesize-deps.md` |
| `references/step7-overview.md` | **重命名+改内容** | `references/workflow/generate-overview.md` |
| `references/step8-menu-and-docmap.md` | **重命名+改内容** | `references/workflow/generate-menu.md` |
| `references/step9-execution-strategy.md` | **重命名+改内容** | `references/workflow/generate-module-docs.md` |
| `references/components.md` | **移动** | `references/rules/components.md` |
| `references/codepurpose-detection.md` | **移动** | `references/rules/codepurpose-detection.md` |
| `references/quality-standards.md` | **移动** | `references/rules/quality-standards.md` |
| `references/menu-archetypes.md` | **移动** | `references/rules/menu-archetypes.md` |
| `references/prompts.md` (架构文档章节) | **拆出** | `references/generation/overview-page.md` |
| `references/prompts.md` (模块+代码分析+依赖章节) | **拆出** | `references/generation/module-page.md` |
| `references/prompts.md` (API文档章节) | **拆出** | `references/generation/api-page.md` |
| `references/prompts.md` (首页与快速开始章节) | **拆出** | `references/generation/getting-started-page.md` |
| `references/prompts.md` (组件选择流程章节) | **合并到** | `references/rules/components.md` 末尾 |
| `references/templates.md` (概览骨架) | **合并到** | `references/generation/overview-page.md` |
| `references/templates.md` (模块骨架) | **合并到** | `references/generation/module-page.md` |
| `references/templates.md` (API骨架) | **合并到** | `references/generation/api-page.md` |
| `references/templates.md` (快速开始骨架) | **合并到** | `references/generation/getting-started-page.md` |
| `references/templates.md` (文档地图+menu.json) | **拆出** | `references/generation/docmap-page.md` |
| `references/templates.md` (模板设计原则) | **合并到** | `references/rules/quality-standards.md` 末尾 |
| `references/prompts.md` | **删除** | — |
| `references/templates.md` | **删除** | — |
| `SKILL.md` 工作流章节 | **替换为 digraph** | `SKILL.md` |

---

## Task 1：建立新目录结构

**Step 1: 创建三个新子目录**

```bash
cd /e/Python/deepwiki-skill && mkdir -p references/workflow references/generation references/rules
```

**Step 2: 验证**

```bash
ls references/
```
Expected: 看到 `workflow/`、`generation/`、`rules/`

---

## Task 2：迁移并重命名 workflow/ 文件

**Step 1: 批量移动并重命名**

```bash
cd /e/Python/deepwiki-skill/references
mv step1-init.md                    workflow/init-wiki.md
mv step2-analyze.md                 workflow/analyze-project.md
mv step3-extract-structure.md       workflow/extract-structure.md
mv "step3.5-architecture-skeleton.md" workflow/generate-skeleton.md
mv step4-change-detection.md        workflow/detect-changes.md
mv step4-parallel-strategy.md       workflow/parallel-analysis.md
mv "step4.5-analysis-quality-gate.md" workflow/check-analysis-quality.md
mv step5-source-analysis.md         workflow/extract-docs.md
mv step6-dependency-synthesis.md    workflow/synthesize-deps.md
mv step7-overview.md                workflow/generate-overview.md
mv step8-menu-and-docmap.md         workflow/generate-menu.md
mv step9-execution-strategy.md      workflow/generate-module-docs.md
```

**Step 2: 验证**

```bash
ls references/workflow/
```
Expected: 12 个文件，全部无 `step` 前缀

---

## Task 3：为 workflow 文件添加 I/O 契约表 + 替换步骤编号

每个文件：1) 在标题后插入契约表；2) 全文用工具名替换"第 N 步"。

### 3.1 init-wiki.md
- 脚本: `python scripts/init_wiki.py <项目路径> [--force]`
- 输入: 项目目录
- 输出: `.deepwiki/config.yaml`、`.deepwiki/meta.json`
- 前置: 无 / 后置: `analyze-project`

### 3.2 analyze-project.md
- 脚本: `python scripts/analyze_project.py <项目路径>`
- 输入: 项目源代码目录
- 输出: `cache/structure.json`、`cache/project-digest.md`
- 前置: `init-wiki` / 后置: `extract-structure`

### 3.3 extract-structure.md
- 脚本: `python scripts/extract_structure.py <项目路径>`
- 输入: `cache/structure.json`
- 输出: `cache/code-structure.json`、`cache/import-relations.json`
- 前置: `analyze-project` / 后置: `generate-skeleton`、`detect-changes`

### 3.4 generate-skeleton.md
- 脚本: `python scripts/generate_architecture_skeleton.py <项目路径>` + AI
- 输入: `cache/structure.json`、`cache/code-structure.json`、`cache/import-relations.json`
- 输出: `cache/architecture-skeleton.json`
- 前置: `extract-structure` / 后置: `extract-docs`（注入全局上下文）
- 失败策略: 跳过骨架注入，后续工具以无全局上下文模式运行
- 文内替换: 第 5 步→extract-docs, 第 6 步→synthesize-deps, 第 7 步→generate-overview, 第 8 步→generate-menu

### 3.5 detect-changes.md
- 脚本: `python scripts/detect_changes.py <项目路径>`
- 输入: `cache/checksums.json`（可为空）、项目源文件
- 输出: `cache/checksums.json`（更新）、变更模块列表
- 前置: `extract-structure` / 后置: `extract-docs`

### 3.6 parallel-analysis.md
- 脚本: 无（调度策略文档，AI 执行）
- 输入: `cache/structure.json`（模块列表+重要性评分）
- 输出: `cache/module-analysis.json`（增量写入）
- 前置: `detect-changes` / 后置: `check-analysis-quality`
- 文内替换: 第 4/5/6 步语义分析→extract-docs 语义分析，依赖综合→synthesize-deps，
  `references/step5-source-analysis.md`→`workflow/extract-docs.md`

### 3.7 extract-docs.md
- 脚本: `python scripts/extract_docs.py <文件绝对路径>`（逐文件）
- 输入: `cache/structure.json`、`cache/code-structure.json`、`cache/architecture-skeleton.json`（可选）
- 输出: `cache/module-analysis.json`
- 前置: `detect-changes`，可选 `generate-skeleton`
- 后置: `check-analysis-quality`；并行策略见 `parallel-analysis.md`
- 文内替换: 第 5 步→extract-docs, 第 3.5 步→generate-skeleton, 第 4 步变更检测→detect-changes,
  第 6/9 步→synthesize-deps/generate-module-docs, [Step 5]→[extract-docs]

### 3.8 check-analysis-quality.md
- 脚本: `python scripts/check_analysis_quality.py <项目路径>`
- 输入: `cache/module-analysis.json`
- 输出: 质量报告（stdout），退出码 0/1/2
- 前置: `extract-docs`
- 后置: exit=0→synthesize-deps; exit=1→增量补充后重跑; exit=2→重跑 extract-docs
- 文内替换: 第 5/6 步→extract-docs/synthesize-deps, 第 9.5 步→generate-module-docs 质量检查阶段

### 3.9 synthesize-deps.md
- 脚本: 无（AI 执行）
- 输入: `cache/module-analysis.json`、`cache/import-relations.json`、`cache/architecture-skeleton.json`（可选）
- 输出: RelationshipSummary（AI 上下文）
- 前置: `check-analysis-quality`（exit=0） / 后置: `generate-overview`
- 文内替换: 第 5 步→extract-docs, 第 3.5 步→generate-skeleton, 第 7/8/9 步→generate-overview/generate-menu/generate-module-docs

### 3.10 generate-overview.md
- 脚本: 无（AI 执行）
- 输入: RelationshipSummary、`cache/architecture-skeleton.json`（可选）
- 输出: `wiki/overview.md`、`wiki/getting-started.md`
- 前置: `synthesize-deps` / 后置: `generate-menu`
- 生成规则: 见 `../generation/overview-page.md`、`../generation/getting-started-page.md`
- 文内替换: 第 3.5 步→generate-skeleton, 第 9 步→generate-module-docs,
  `references/templates.md`→`../generation/overview-page.md`

### 3.11 generate-menu.md
- 脚本: `python scripts/generate_menu.py <wiki目录>`
- 输入: `cache/structure.json`、`cache/module-analysis.json`
- 输出: `wiki/menu.json`、`wiki/doc-map.md`
- 前置: `generate-overview` / 后置: `generate-module-docs`
- 生成规则: 见 `../generation/docmap-page.md`、`../rules/menu-archetypes.md`
- 文内替换: 第 5 步→extract-docs, `references/menu-archetypes.md`→`../rules/menu-archetypes.md`,
  `references/templates.md`→`../generation/docmap-page.md`

### 3.12 generate-module-docs.md
- 脚本: `generate_menu.py --reconcile`、`fix_mermaid.py`、`check_quality.py`
- 输入: `cache/module-analysis.json`、`wiki/menu.json`、RelationshipSummary
- 输出: `wiki/modules/*.md`、`wiki/api/*.md`
- 前置: `generate-menu` / 后置: 完成
- 生成规则: 见 `../generation/module-page.md`、`../generation/api-page.md`
- 文内替换: 第 5/6 步→extract-docs/synthesize-deps,
  `references/templates.md`→`../generation/module-page.md`,
  `references/system-reference.md`→`../system-reference.md`

---

## Task 4：迁移 rules/ 辅助规则文件

**Step 1: 批量移动**

```bash
cd /e/Python/deepwiki-skill/references
mv components.md rules/
mv codepurpose-detection.md rules/
mv quality-standards.md rules/
mv menu-archetypes.md rules/
```

**Step 2: 验证**

```bash
ls references/rules/
```
Expected: 4 个文件

---

## Task 5：拆分 prompts.md + templates.md → generation/

**Step 1: 查章节行号**

```bash
grep -n "^## " references/prompts.md
grep -n "^## " references/templates.md
```

**Step 2: 创建 generation/ 的 5 个文件**

每个文件结构：
```markdown
# <页面> 生成指南
> 适用工具：`<工具名>`
> 关联规则：`../rules/quality-standards.md`、`../rules/components.md`
---
## 生成指导
<从 prompts.md 对应章节提取>
---
## 页面骨架
<从 templates.md 对应章节提取>
```

文件对应关系：
- `overview-page.md`：prompts.md「架构文档」+ templates.md「概览文档骨架」
- `module-page.md`：prompts.md「代码深度分析+模块文档+依赖关系分析」+ templates.md「模块文档骨架」
- `api-page.md`：prompts.md「API 文档」+ templates.md「API 文档骨架」
- `getting-started-page.md`：prompts.md「首页与快速开始」+ templates.md「快速开始骨架」
- `docmap-page.md`：templates.md「文档地图骨架+menu.json 模板」

**Step 3: prompts.md「组件选择流程」追加到 rules/components.md 末尾**

**Step 4: templates.md「模板设计原则」追加到 rules/quality-standards.md 末尾**

**Step 5: 删除原始文件**

```bash
rm references/prompts.md references/templates.md
```

**Step 6: 验证**

```bash
ls references/generation/
```
Expected: 5 个文件

---

## Task 6：重写 SKILL.md（精简 + digraph，节点用工具名）

新 SKILL.md 工作流 digraph（节点全用工具名，无步骤编号）：

```dot
digraph deepwiki {
    rankdir=TB;
    start    [label="用户意图",              shape=doublecircle];
    done     [label="完成",                 shape=doublecircle];
    init     [label="init-wiki",            shape=box];
    analyze  [label="analyze-project",      shape=box];
    extract  [label="extract-structure",    shape=box];
    skeleton [label="generate-skeleton",    shape=box];
    detect   [label="detect-changes",       shape=box];
    docs     [label="extract-docs",         shape=box];
    gate     [label="check-analysis-quality", shape=box, style=filled, fillcolor=lightyellow];
    synth    [label="synthesize-deps",      shape=box];
    overview [label="generate-overview",    shape=box];
    menu     [label="generate-menu",        shape=box];
    modules  [label="generate-module-docs", shape=box];
    pass     [label="exit=0?",             shape=diamond];
    fix      [label="增量补充分析",          shape=box];

    start    -> init      [label="全量/增量"];
    init     -> analyze;
    analyze  -> extract;
    extract  -> skeleton;
    skeleton -> detect;
    detect   -> docs;
    docs     -> gate;
    gate     -> pass;
    pass     -> synth    [label="yes"];
    pass     -> fix      [label="no"];
    fix      -> gate;
    synth    -> overview;
    overview -> menu;
    menu     -> modules;
    modules  -> done;
    start    -> modules  [label="仅质量检查", style=dashed];
    start    -> docs     [label="定向重生成", style=dashed];
}
```

工具索引表（工具名 → `references/workflow/<name>.md`）放在 digraph 之后。

**Step 1: edit_file 全量替换 SKILL.md**

**Step 2: 验证行数**

```bash
wc -l SKILL.md
```
Expected: < 110

---

## Task 7：修复所有内部引用 + 断链验证

**Step 1: 查找残留旧引用**

```bash
cd /e/Python/deepwiki-skill
grep -rn "references/step\\|references/components\\|references/prompts\\|references/templates\\|references/quality-standards\\|references/codepurpose\\|references/menu-archetypes\\|第 [0-9]" \\
  references/workflow/ references/generation/ references/rules/ SKILL.md
```

**Step 2: 修复 workflow 文件内残留步骤编号**

**Step 3: 更新 system-reference.md**
将对 `step*.md` 的引用更新为 `workflow/*.md`，更新目录树。

**Step 4: 断链验证**

```bash
cd /e/Python/deepwiki-skill && python -c "
import re, pathlib, sys
errors = []
for md in pathlib.Path('.').rglob('*.md'):
    if any(p in str(md) for p in ['.git', 'docs/plans']): continue
    text = md.read_text(encoding='utf-8', errors='replace')
    for m in re.finditer(r'\[.*?\]\(([^)#]+\.md)[^)]*\)', text):
        target = (md.parent / m.group(1)).resolve()
        if not target.exists():
            errors.append(str(md) + ': ' + m.group(1))
for e in errors: print(e)
sys.exit(1 if errors else 0)
"
```
Expected: 无输出，exit 0

---

## 完成标准

- [ ] `references/workflow/` 含 12 个文件，全部无 `step` 前缀，每个文件开头有 I/O 契约表
- [ ] `references/workflow/` 内无"第 N 步"表述，用工具名替代
- [ ] `references/generation/` 含 5 个 page 文件
- [ ] `references/rules/` 含 4 个规则文件
- [ ] `references/` 根目录只剩 `system-reference.md` 和 `plugin.md`
- [ ] `SKILL.md` < 110 行，含 digraph 工作流（节点为工具名）和工具索引表
- [ ] 断链验证脚本 exit 0
- [ ] `references/prompts.md` 和 `references/templates.md` 已删除
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(CONTENT)
print(f"Written {OUT}, lines={CONTENT.count(chr(10))}")

