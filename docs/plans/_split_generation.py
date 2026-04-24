#!/usr/bin/env python
"""Task 5: Split prompts.md + templates.md into generation/ files."""
import pathlib, re

ROOT = pathlib.Path(__file__).parent.parent.parent
REF  = ROOT / "references"
GEN  = REF / "generation"
RULES = REF / "rules"

# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def read(path):
    return path.read_text(encoding="utf-8")

def extract_sections(text, *heading_prefixes):
    """Return the combined text of all ## sections whose title starts with
    any of the given prefixes (case-insensitive). Stops at the next ## heading
    not in the set."""
    result = []
    lines = text.split("\n")
    capturing = False
    buf = []
    for line in lines:
        if line.startswith("## "):
            if capturing:
                result.append("\n".join(buf).rstrip())
                buf = []
                capturing = False
            if any(line[3:].startswith(p) for p in heading_prefixes):
                capturing = True
                buf = [line]
        elif capturing:
            buf.append(line)
    if capturing and buf:
        result.append("\n".join(buf).rstrip())
    return "\n\n".join(result)

def extract_from(text, start_prefix, end_prefix=None):
    """Return text from the first '## <start_prefix>' up to (not including)
    the first '## <end_prefix>' or end of file."""
    lines = text.split("\n")
    started = False
    result = []
    for line in lines:
        if not started:
            if line.startswith("## ") and line[3:].startswith(start_prefix):
                started = True
                result.append(line)
        else:
            if end_prefix and line.startswith("## ") and line[3:].startswith(end_prefix):
                break
            result.append(line)
    return "\n".join(result).rstrip()

def write_gen(fname, header_tool, header_rules, body):
    """Write a generation/ file with standard frontmatter."""
    content = f"""# {fname.replace("-page.md", "").replace("-", " ").title()} 生成指南

> **适用工具：** `{header_tool}`
> **关联规则：** `../rules/quality-standards.md`、`../rules/components.md`

---

{body.strip()}
"""
    (GEN / fname).write_text(content, encoding="utf-8")
    print(f"  created: generation/{fname}")

# ─────────────────────────────────────────────────────────────────────
# Load source files
# ─────────────────────────────────────────────────────────────────────
prompts   = read(REF / "prompts.md")
templates = read(REF / "templates.md")

# ─────────────────────────────────────────────────────────────────────
# overview-page.md
#   prompts: "架构文档" section (L215+) through "API 文档"
#   templates: "概览文档骨架" section (L65+)
# ─────────────────────────────────────────────────────────────────────
p_overview = extract_from(prompts,   "架构文档",       "API 文档")
t_overview = extract_from(templates, "概览文档骨架",   "模块文档骨架")

write_gen(
    "overview-page.md",
    "generate-overview",
    "quality-standards、components",
    "## 生成指导\n\n" + p_overview + "\n\n---\n\n## 页面骨架\n\n" + t_overview,
)

# ─────────────────────────────────────────────────────────────────────
# module-page.md
#   prompts: "代码深度分析" + "模块文档" + "依赖关系分析" sections
#   templates: "模块文档骨架" section
# ─────────────────────────────────────────────────────────────────────
p_module = (
    extract_from(prompts, "代码深度分析", "模块文档") + "\n\n"
    + extract_from(prompts, "模块文档",      "架构文档") + "\n\n"
    + extract_from(prompts, "依赖关系分析",  "首页与快速开始")
)
t_module = extract_from(templates, "模块文档骨架", "API 文档骨架")

write_gen(
    "module-page.md",
    "generate-module-docs",
    "quality-standards、components、codepurpose-detection",
    "## 生成指导\n\n" + p_module + "\n\n---\n\n## 页面骨架\n\n" + t_module,
)

# ─────────────────────────────────────────────────────────────────────
# api-page.md
#   prompts: "API 文档" section
#   templates: "API 文档骨架" section
# ─────────────────────────────────────────────────────────────────────
p_api = extract_from(prompts,   "API 文档",    "依赖关系分析")
t_api = extract_from(templates, "API 文档骨架","快速开始骨架")

write_gen(
    "api-page.md",
    "generate-module-docs",
    "quality-standards、components",
    "## 生成指导\n\n" + p_api + "\n\n---\n\n## 页面骨架\n\n" + t_api,
)

# ─────────────────────────────────────────────────────────────────────
# getting-started-page.md
#   prompts: "首页与快速开始" section
#   templates: "快速开始骨架" section
# ─────────────────────────────────────────────────────────────────────
p_gs = extract_from(prompts,   "首页与快速开始", "架构文档")   # 首页段在文末
# 首页段在 prompts 末尾，用不同方式提取
p_gs_lines = prompts.split("\n")
p_gs_buf = []
in_sec = False
for line in p_gs_lines:
    if line.startswith("## 首页与快速开始"):
        in_sec = True
        p_gs_buf = [line]
    elif in_sec:
        p_gs_buf.append(line)
p_gs = "\n".join(p_gs_buf).rstrip()

t_gs = extract_from(templates, "快速开始骨架", "文档地图骨架")

write_gen(
    "getting-started-page.md",
    "generate-overview",
    "quality-standards",
    "## 生成指导\n\n" + p_gs + "\n\n---\n\n## 页面骨架\n\n" + t_gs,
)

# ─────────────────────────────────────────────────────────────────────
# docmap-page.md
#   templates: "文档地图骨架" + "menu.json 模板" sections
#   (no corresponding prompts section)
# ─────────────────────────────────────────────────────────────────────
t_docmap   = extract_from(templates, "文档地图骨架", "menu.json 模板")
t_menujson = extract_from(templates, "menu.json 模板", "源码追溯要求")

write_gen(
    "docmap-page.md",
    "generate-menu",
    "menu-archetypes",
    "## 页面骨架（文档地图）\n\n" + t_docmap
    + "\n\n---\n\n## menu.json 模板\n\n" + t_menujson,
)

# ─────────────────────────────────────────────────────────────────────
# Append extra sections to rules/
# ─────────────────────────────────────────────────────────────────────

# 1. prompts.md "组件选择流程" → rules/components.md (append)
comp_section = extract_from(prompts, "组件选择流程", "代码深度分析")
comp_file = RULES / "components.md"
existing = comp_file.read_text(encoding="utf-8")
if "组件选择流程" not in existing:
    comp_file.write_text(existing.rstrip() + "\n\n---\n\n" + comp_section + "\n", encoding="utf-8")
    print("  appended: rules/components.md ← 组件选择流程")

# 2. templates.md "模板设计原则" → rules/quality-standards.md (append)
design_section = extract_from(templates, "模板设计原则", "概览文档骨架")
qs_file = RULES / "quality-standards.md"
existing_qs = qs_file.read_text(encoding="utf-8")
if "模板设计原则" not in existing_qs:
    qs_file.write_text(existing_qs.rstrip() + "\n\n---\n\n" + design_section + "\n", encoding="utf-8")
    print("  appended: rules/quality-standards.md ← 模板设计原则")

print("\nAll generation/ files created.")

