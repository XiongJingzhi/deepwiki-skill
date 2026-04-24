#!/usr/bin/env python
"""Task 3: Re-write I/O contract tables and replace step references in workflow files."""
import pathlib

WF = pathlib.Path(__file__).parent.parent.parent / "references" / "workflow"

BT = "`"  # backtick — avoid shell substitution when this file is run via python

def bt(s):
    return BT + s + BT

def bts(*args):
    return "、".join(bt(a) for a in args)

# =====================================================================
# CONTRACT TABLE TEXT per file  (keyed by filename)
# Each value is the markdown block to insert right after the first heading
# =====================================================================
CONTRACTS = {
    "init-wiki.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | {bt("python scripts/init_wiki.py <项目路径> [--force]")} |
| **输入** | 项目目录 |
| **输出** | {bt(".deepwiki/config.yaml")}、{bt(".deepwiki/meta.json")} |
| **前置** | 无 |
| **后置** | {bt("analyze-project")} |

""",
    "analyze-project.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | {bt("python scripts/analyze_project.py <项目路径>")} |
| **输入** | 项目源代码目录 |
| **输出** | {bt("cache/structure.json")}、{bt("cache/project-digest.md")} |
| **前置** | {bt("init-wiki")} |
| **后置** | {bt("extract-structure")} |

""",
    "extract-structure.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | {bt("python scripts/extract_structure.py <项目路径>")} |
| **输入** | {bt("cache/structure.json")} |
| **输出** | {bt("cache/code-structure.json")}、{bt("cache/import-relations.json")} |
| **前置** | {bt("analyze-project")} |
| **后置** | {bt("generate-skeleton")}、{bt("detect-changes")} |

""",
    "generate-skeleton.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | {bt("python scripts/generate_architecture_skeleton.py <项目路径>")}（脚本段）+ AI 生成（AI 段） |
| **输入** | {bt("cache/structure.json")}、{bt("cache/code-structure.json")}、{bt("cache/import-relations.json")} |
| **输出** | {bt("cache/architecture-skeleton.json")} |
| **前置** | {bt("extract-structure")} |
| **后置** | {bt("extract-docs")}（注入全局上下文） |
| **失败策略** | 跳过骨架注入，后续工具以无全局上下文模式运行 |

""",
    "detect-changes.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | {bt("python scripts/detect_changes.py <项目路径>")} |
| **输入** | {bt("cache/checksums.json")}（上次保存值，可为空）、项目源文件 |
| **输出** | {bt("cache/checksums.json")}（更新）、变更模块列表（stdout） |
| **前置** | {bt("extract-structure")} |
| **后置** | {bt("extract-docs")} |

""",
    "parallel-analysis.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | 无（调度策略文档，由 AI 执行） |
| **输入** | {bt("cache/structure.json")}（模块列表+重要性评分） |
| **输出** | {bt("cache/module-analysis.json")}（增量写入） |
| **前置** | {bt("detect-changes")} |
| **后置** | {bt("check-analysis-quality")} |

""",
    "extract-docs.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | {bt("python scripts/extract_docs.py <文件绝对路径>")}（预提取注释，逐文件） |
| **输入** | {bt("cache/structure.json")}、{bt("cache/code-structure.json")}、{bt("cache/architecture-skeleton.json")}（可选） |
| **输出** | {bt("cache/module-analysis.json")} |
| **前置** | {bt("detect-changes")}，可选 {bt("generate-skeleton")} |
| **后置** | {bt("check-analysis-quality")}；并行策略见 {bt("parallel-analysis.md")} |

""",
    "check-analysis-quality.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | {bt("python scripts/check_analysis_quality.py <项目路径> [--verbose] [--json FILE]")} |
| **输入** | {bt("cache/module-analysis.json")} |
| **输出** | 质量报告（stdout），退出码（0/1/2） |
| **前置** | {bt("extract-docs")} |
| **后置** | exit=0 → {bt("synthesize-deps")}；exit=1 → 增量补充后重跑本工具；exit=2 → 重跑 {bt("extract-docs")} |

""",
    "synthesize-deps.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | 无（AI 执行） |
| **输入** | {bt("cache/module-analysis.json")}、{bt("cache/import-relations.json")}、{bt("cache/architecture-skeleton.json")}（可选） |
| **输出** | RelationshipSummary（AI 上下文，供后续工具使用） |
| **前置** | {bt("check-analysis-quality")}（exit=0） |
| **后置** | {bt("generate-overview")} |

""",
    "generate-overview.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | 无（AI 执行） |
| **输入** | RelationshipSummary（来自 {bt("synthesize-deps")}）、{bt("cache/architecture-skeleton.json")}（可选） |
| **输出** | {bt("wiki/overview.md")}、{bt("wiki/getting-started.md")} |
| **前置** | {bt("synthesize-deps")} |
| **后置** | {bt("generate-menu")} |
| **生成规则** | 见 {bt("../generation/overview-page.md")}、{bt("../generation/getting-started-page.md")} |

""",
    "generate-menu.md": f"""
## 契約

| 項 | 值 |
|----|-----|
| **脚本** | {bt("python scripts/generate_menu.py <wiki目录> [项目名] [--reconcile]")} |
| **输入** | {bt("cache/structure.json")}、{bt("cache/module-analysis.json")}、{bt("cache/architecture-skeleton.json")}（可选） |
| **输出** | {bt("wiki/menu.json")}、{bt("wiki/doc-map.md")} |
| **前置** | {bt("generate-overview")} |
| **后置** | {bt("generate-module-docs")} |
| **生成规则** | 见 {bt("../generation/docmap-page.md")}、{bt("../rules/menu-archetypes.md")} |

""",
    "generate-module-docs.md": f"""
## 契約

| 項 | 値 |
|----|-----|
| **脚本** | {bt("python scripts/generate_menu.py ... --reconcile")}、{bt("fix_mermaid.py")}、{bt("check_quality.py")} |
| **输入** | {bt("cache/module-analysis.json")}、{bt("wiki/menu.json")}、RelationshipSummary |
| **输出** | {bt("wiki/modules/*.md")}、{bt("wiki/api/*.md")}、{bt("wiki/menu.json")}（校验后） |
| **前置** | {bt("generate-menu")} |
| **后置** | 完成 |
| **生成规则** | 见 {bt("../generation/module-page.md")}、{bt("../generation/api-page.md")} |

""",
}

# =====================================================================
# REPLACEMENTS per file  (applied after contract insertion)
# Order matters: more specific patterns first
# =====================================================================
REPLACEMENTS = {
    "generate-skeleton.md": [
        ("第 5 步（深度分析）", "extract-docs"),
        ("第 6 步（依赖综合）", "synthesize-deps"),
        ("第 7 步（概览文档）", "generate-overview"),
        ("第 8 步（菜单生成）", "generate-menu"),
        ("第 3.5 步", "generate-skeleton"),
        ("第 5 步", "extract-docs"),
        ("第 6 步", "synthesize-deps"),
        ("第 7 步", "generate-overview"),
        ("第 8 步", "generate-menu"),
    ],
    "parallel-analysis.md": [
        ("第 4 步语义分析", "extract-docs 语义分析"),
        ("第 5 步语义分析", "extract-docs 语义分析"),
        ("第 6 步依赖综合", "synthesize-deps"),
        ("第 5 步依赖综合", "synthesize-deps"),
        ("references/step5-source-analysis.md", "workflow/extract-docs.md"),
        ("step5-source-analysis.md", "extract-docs.md"),
        ("第 4 步", "extract-docs"),
        ("第 5 步", "extract-docs"),
        ("第 6 步", "synthesize-deps"),
    ],
    "extract-docs.md": [
        ("本文档定义第 5 步", "本文档定义 extract-docs"),
        ("[Step 5]", "[extract-docs]"),
        ("第 3.5 步成功生成", "generate-skeleton 成功生成"),
        ("第 3.5 步", "generate-skeleton"),
        ("第 4 步变更检测", "detect-changes"),
        ("供第 6 步和第 9 步使用", "供 synthesize-deps 和 generate-module-docs 使用"),
        ("步骤 6 和步骤 9 将降级", "synthesize-deps 和 generate-module-docs 将降级"),
        ("第 4 步", "detect-changes"),
        ("第 5 步", "extract-docs"),
        ("第 6 步", "synthesize-deps"),
        ("第 9 步", "generate-module-docs"),
    ],
    "check-analysis-quality.md": [
        ("第 5 步（深度分析）完成后", "extract-docs 完成后"),
        ("第 5 步（深度分析）", "extract-docs"),
        ("第 6 步（依赖综合）开始前", "synthesize-deps 开始前"),
        ("第 6 步（依赖综合）", "synthesize-deps"),
        ("第 9.5 步（文档质量检查）", "generate-module-docs 质量检查阶段"),
        ("第 9.5 步", "generate-module-docs 收尾质检"),
        ("重新运行第 5 步", "重新运行 extract-docs"),
        ("回到第 5 步重做", "回到 extract-docs 重做"),
        ("第 5 步之后", "extract-docs 之后"),
        ("第 5 步", "extract-docs"),
        ("第 6 步", "synthesize-deps"),
        # 修复标题中的步骤编号
        ("第 4.5 步：分析质量门控", "分析质量门控"),
        ("工作流第 4.5 步的完整规则：", "分析质量门控的完整规则："),
    ],
    "synthesize-deps.md": [
        ("第 3.5 步生成", "generate-skeleton 生成"),
        ("第 3.5 步", "generate-skeleton"),
        ("第 7、8、9 步", "generate-overview、generate-menu、generate-module-docs"),
        ("第 5 步", "extract-docs"),
        ("第 6 步", "synthesize-deps"),
        ("第 7 步", "generate-overview"),
        ("第 8 步", "generate-menu"),
        ("第 9 步", "generate-module-docs"),
        # 修复标题
        ("本文件描述工作流第 6 步的完整规则", "本文件描述 synthesize-deps 的完整规则"),
    ],
    "generate-overview.md": [
        ("第 3.5 步生成", "generate-skeleton 生成"),
        ("第 3.5 步", "generate-skeleton"),
        ("第 2-6 步的分析结果", "init-wiki 到 synthesize-deps 的分析结果"),
        ("references/templates.md", "../generation/overview-page.md"),
        ("第 7 步", "generate-overview"),
        ("第 9 步", "generate-module-docs"),
        # 修复标题
        ("工作流第七步", "generate-overview"),
        ("第七步", "generate-overview"),
    ],
    "generate-menu.md": [
        ("第 5 步已提炼", "extract-docs 已提炼"),
        ("步骤 5 的分析结果", "extract-docs 的分析结果"),
        ("references/menu-archetypes.md", "../rules/menu-archetypes.md"),
        ("references/templates.md", "../generation/docmap-page.md"),
        ("第 5 步", "extract-docs"),
        ("第 8 步", "generate-menu"),
        # 修复标题
        ("工作流第八步", "generate-menu"),
        ("第八步", "generate-menu"),
    ],
    "generate-module-docs.md": [
        ("第 5 步写入", "extract-docs 写入"),
        ("references/templates.md", "../generation/module-page.md"),
        ("references/system-reference.md", "../system-reference.md"),
        ("第 5 步", "extract-docs"),
        ("第 6 步", "synthesize-deps"),
        ("第 9 步执行策略", "generate-module-docs 执行策略"),
        ("第 9 步", "generate-module-docs"),
        # 修复标题
        ("工作流第 9 步", "generate-module-docs"),
        ("工作流第九步", "generate-module-docs"),
        ("第九步", "generate-module-docs"),
    ],
    "init-wiki.md": [
        ("第 1 步：初始化", "init-wiki：初始化"),
        ("工作流第一步", "init-wiki"),
        ("第 1 步", "init-wiki"),
        ("第一步", "init-wiki"),
    ],
    "analyze-project.md": [
        ("第 2 步：分析项目结构", "analyze-project：分析项目结构"),
        ("工作流第二步", "analyze-project"),
        ("第 2 步", "analyze-project"),
        ("第二步", "analyze-project"),
    ],
    "extract-structure.md": [
        ("第 3 步：提取代码结构", "extract-structure：提取代码结构"),
        ("工作流第三步", "extract-structure"),
        ("第 3 步", "extract-structure"),
        ("第三步", "extract-structure"),
    ],
    "detect-changes.md": [
        ("本文档对应工作流第 4 步", "本文档对应 detect-changes"),
        ("第 4 步", "detect-changes"),
        ("第四步", "detect-changes"),
    ],
}

# =====================================================================
# PROCESS each file
# =====================================================================
for fname, contract in CONTRACTS.items():
    fpath = WF / fname
    if not fpath.exists():
        print(f"  SKIP (not found): {fname}")
        continue

    text = fpath.read_text(encoding="utf-8")

    # --- Step 1: Remove old (broken) contract table if present, then re-insert ---
    # The previous run inserted a table but backticks were stripped by bash.
    # Strategy: remove everything between "## 契約\n" and the next "## " heading,
    # then re-insert the correct contract block.
    import re
    # Remove existing broken contract block
    text = re.sub(
        r'\n## 契[約约]\n.*?(?=\n## |\Z)',
        '',
        text,
        flags=re.DOTALL
    )

    # --- Step 2: Insert contract block after the first heading (# ...) ---
    lines = text.split("\n")
    # Find end of opening block (title + description lines)
    insert_idx = 1
    for i in range(1, min(10, len(lines))):
        if lines[i].startswith("#") or (lines[i].strip() and not lines[i].startswith(">")):
            insert_idx = i
            break
        insert_idx = i + 1

    new_lines = lines[:insert_idx] + [contract.strip(), ""] + lines[insert_idx:]
    text = "\n".join(new_lines)

    # --- Step 3: Apply text replacements ---
    for old, new in REPLACEMENTS.get(fname, []):
        text = text.replace(old, new)

    fpath.write_text(text, encoding="utf-8")
    print(f"  OK: {fname}")

print("\nAll workflow files processed.")

