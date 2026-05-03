"""
build_prompt.py - 从模板生成 subagent 系统提示词

用法:
    python scripts/subagent/build_prompt.py <agent_type> --project <project_dir> [options]

    agent_type:
        extract-docs           [--module <module_path>]
        generate-module-docs   --page <page_id>
        quality-fix

输出:
    默认输出到 stdout。
    加 --output <path> 写入文件。
    加 --cache 写入 cache/prompts/<type>_<id>.md。
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict

# 模板目录：相对于本脚本的上上级 references/subagents/
TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "references" / "subagents"

# {{ VAR }} 模式
_TEMPLATE_VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def _load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _load_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


# ---------------------------------------------------------------------------
# 各 agent 类型的变量构建器
# ---------------------------------------------------------------------------

def _build_extract_docs_vars(project_dir: Path, module_path: str | None) -> Dict[str, str]:
    cache_dir = project_dir / ".deepwiki" / "cache"
    skeleton = _load_json(cache_dir / "architecture-skeleton.json")

    # 模块分组列表
    groups = skeleton.get("module_groups") or skeleton.get("groups", [])
    groups_lines = []
    for g in groups:
        name = g.get("name", "")
        modules = ", ".join(g.get("modules", []))
        role = g.get("role") or g.get("dominant_purpose", "")
        groups_lines.append(f"- {name}：{modules}（{role}）")
    groups_block = "\n".join(groups_lines) if groups_lines else "（骨架未生成分组信息）"

    # 当前模块所属分组
    current_group = ""
    if module_path:
        for g in groups:
            if module_path in g.get("modules", []):
                current_group = g.get("name", "")
                break

    return {
        "SKELETON_PROJECT_NATURE": skeleton.get("project_nature", "未检测"),
        "SKELETON_ARCHITECTURE_STYLE": skeleton.get("architecture_style", "未检测"),
        "GROUPS_BLOCK": groups_block,
        "CURRENT_MODULE_GROUP_NAME": current_group or "未分配",
    }


def _build_source_files_block(project_dir: Path, page: dict) -> str:
    """从 generation-plan.json 的 source_files 生成格式化的源码文件清单。"""
    source_files = page.get("source_files", [])
    if not source_files:
        return "（未找到源码文件清单，请从 module-analysis.json 推导）"

    lines = []
    project_abs = str(project_dir).replace("\\", "/")
    for sf in source_files:
        rel_path = sf.get("path", "")
        abs_path = f"{project_abs}/{rel_path}"
        ranges = sf.get("ranges", [])
        if ranges:
            for r in ranges:
                start = r.get("start_line", 1)
                end = r.get("end_line", start)
                label = r.get("label", "")
                desc = f" — {label}" if label else ""
                lines.append(f"- [{rel_path}](file:///{abs_path}#L{start}-L{end}){desc}")
        else:
            lines.append(f"- [{rel_path}](file:///{abs_path})")
    return "\n".join(lines)


def _build_module_analysis_block(module_data: dict) -> str:
    """格式化模块分析数据为可读文本。"""
    if not module_data:
        return "（模块分析数据缺失）"

    parts = []
    for key in ("module_summary", "module_role", "semantic_group", "code_purpose", "analysis_depth"):
        val = module_data.get(key, "")
        if val:
            parts.append(f"**{key}**: {val}")

    key_insights = module_data.get("key_insights", [])
    if key_insights:
        parts.append("\n**key_insights**:")
        for ki in key_insights[:10]:
            parts.append(f"  - {ki}")

    # 文件级数据
    files = module_data.get("files", [])
    if files:
        parts.append("\n**核心文件**:")
        for f in files[:10]:
            path = f.get("path", "")
            summary = f.get("summary", "")
            parts.append(f"  - `{path}`: {summary}")
            pis = f.get("public_interfaces", [])
            for pi in pis[:5]:
                if isinstance(pi, dict):
                    name = pi.get("name", "")
                    start = pi.get("line", "")
                    end = pi.get("end_line", "")
                    if name:
                        loc = f"L{start}-L{end}" if start and end else ""
                        parts.append(f"    - `{name}` {loc}")

    return "\n".join(parts)


def _build_snippets_hint(cache_dir: Path, page_id: str) -> str:
    """检查 snippets 文件是否存在，返回提示信息。"""
    snippet_path = cache_dir / "snippets" / f"{page_id}.json"
    if snippet_path.exists():
        return f"已预提取源码片段：`{snippet_path}`（优先读取此文件获取源码内容）"
    return "（无预提取 snippets，请直接读取源码文件）"


def _build_generate_docs_vars(project_dir: Path, page_id: str) -> Dict[str, str]:
    cache_dir = project_dir / ".deepwiki" / "cache"
    plan = _load_json(cache_dir / "generation-plan.json")
    analysis = _load_json(cache_dir / "module-analysis.json")

    # 在 plan 中查找页面
    page = {}
    for p in plan.get("pages", []):
        if p.get("id") == page_id or p.get("page_id") == page_id:
            page = p
            break

    source_modules = page.get("source_modules", page.get("affected_modules", []))
    module_path = source_modules[0] if source_modules else ""

    # 从 analysis 中获取模块数据
    modules = analysis.get("modules", {})
    module_data = modules.get(module_path, modules.get(module_path.replace("/", "\\"), {}))

    selected = module_data.get("selected_components", [])
    components_str = ", ".join(selected) if selected else "（从 module-analysis.json 的 selected_components 读取）"

    # 加载精简 P0 规范
    compiled_spec_path = TEMPLATE_DIR / "_compiled_p0_rules.md"
    compiled_spec = _load_text(compiled_spec_path)

    # 构建源码文件清单
    source_files_block = _build_source_files_block(project_dir, page)

    # 构建模块分析数据
    module_analysis_block = _build_module_analysis_block(module_data)

    # snippets 提示
    snippets_hint = _build_snippets_hint(cache_dir, page_id)

    return {
        "MODULE_NAME": module_data.get("semantic_group") or page.get("title", ""),
        "MODULE_PATH": module_path,
        "CODE_PURPOSE": module_data.get("code_purpose", ""),
        "SELECTED_COMPONENTS": components_str,
        "COMPILED_SPEC": compiled_spec,
        "SOURCE_FILES_BLOCK": source_files_block,
        "MODULE_ANALYSIS_BLOCK": module_analysis_block,
        "SNIPPETS_HINT": snippets_hint,
    }


def _build_quality_fix_vars(project_dir: Path) -> Dict[str, str]:
    # quality-fix 模板当前无变量，保留扩展点
    return {}


BUILDERS = {
    "extract-docs": _build_extract_docs_vars,
    "generate-module-docs": _build_generate_docs_vars,
    "quality-fix": _build_quality_fix_vars,
}


# ---------------------------------------------------------------------------
# 模板渲染
# ---------------------------------------------------------------------------

def render_template(agent_type: str, variables: Dict[str, str]) -> str:
    template_path = TEMPLATE_DIR / f"{agent_type}.md"
    if not template_path.exists():
        raise FileNotFoundError(f"模板不存在：{template_path}")

    content = template_path.read_text(encoding="utf-8")

    # 替换 {{ VAR }} 为实际值
    def _replacer(m):
        var_name = m.group(1)
        if var_name in variables:
            return variables[var_name]
        return m.group(0)  # 未识别的变量保持原样

    content = _TEMPLATE_VAR_RE.sub(_replacer, content)
    return content


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="从模板生成 subagent 系统提示词")
    parser.add_argument("agent_type", choices=BUILDERS.keys(), help="subagent 类型")
    parser.add_argument("--project", required=True, type=Path, help="项目目录")
    parser.add_argument("--module", help="模块路径（extract-docs 使用）")
    parser.add_argument("--page", help="页面 ID（generate-module-docs 使用）")
    parser.add_argument("--output", "-o", type=Path, help="输出文件路径")
    parser.add_argument("--cache", action="store_true", help="输出到 cache/prompts/ 目录")

    args = parser.parse_args()
    project_dir = args.project.resolve()

    # 构建变量
    if args.agent_type == "extract-docs":
        variables = BUILDERS[args.agent_type](project_dir, args.module)
    elif args.agent_type == "generate-module-docs":
        if not args.page:
            parser.error("generate-module-docs 需要 --page 参数")
        variables = BUILDERS[args.agent_type](project_dir, args.page)
    else:
        variables = BUILDERS[args.agent_type](project_dir)

    # 渲染
    result = render_template(args.agent_type, variables)

    # 输出
    if args.cache:
        cache_dir = project_dir / ".deepwiki" / "cache" / "prompts"
        cache_dir.mkdir(parents=True, exist_ok=True)
        safe_id = (args.page or args.module or args.agent_type).replace(":", "_").replace("/", "_").replace("\\", "_")
        out_path = cache_dir / f"{args.agent_type}_{safe_id}.md"
        out_path.write_text(result, encoding="utf-8")
        print(str(out_path))
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
        print(str(args.output))
    else:
        sys.stdout.write(result)


if __name__ == "__main__":
    main()
