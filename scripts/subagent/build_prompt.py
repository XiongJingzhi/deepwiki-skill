"""
build_prompt.py - 从模板生成 subagent 系统提示词

用法:
    python scripts/subagent/build_prompt.py <agent_type> --project <project_dir> [options]

    agent_type:
        extract-docs           [--module <module_path>]
        generate-module-docs   --page <page_id>
        quality-fix             [--page <wiki_path>]

输出:
    默认输出到 stdout。
    加 --output <path> 写入文件。
    加 --cache 写入 cache/prompts/<type>_<safe_id>.md，并更新 manifest.json。
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
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


def _module_slug(module_path: str) -> str:
    return module_path.replace("/", "_").replace("\\", "_").strip("_") or "module"


def _safe_page_id(page_id: str) -> str:
    return (
        page_id.replace(":", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(".", "_")
    )


def _update_prompt_manifest(
    project_dir: Path,
    agent_type: str,
    prompt_id: str,
    safe_id: str,
    prompt_path: Path,
) -> None:
    """Record cached prompt files as explicit subagent dispatch artifacts."""
    prompts_dir = project_dir / ".deepwiki" / "cache" / "prompts"
    manifest_path = prompts_dir / "manifest.json"
    if manifest_path.exists():
        manifest = _load_json(manifest_path)
    else:
        manifest = {}

    manifest.setdefault("version", 1)
    manifest.setdefault("generated_at", "")
    manifest.setdefault("prompts", {})
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()

    by_type = manifest["prompts"].setdefault(agent_type, {})
    by_type[prompt_id] = {
        "agent_type": agent_type,
        "id": prompt_id,
        "safe_id": safe_id,
        "prompt_path": str(prompt_path.relative_to(project_dir)),
        "source": "scripts/subagent/build_prompt.py",
        "generated_at": manifest["generated_at"],
    }

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _source_link(project_dir: Path, rel_path: str, start: int | None = None, end: int | None = None) -> str:
    uri = (project_dir / rel_path).resolve().as_uri()
    if start:
        line_end = end or start
        return f"{uri}#L{start}-L{line_end}"
    return uri


# ---------------------------------------------------------------------------
# 各 agent 类型的变量构建器
# ---------------------------------------------------------------------------

def _build_extract_docs_vars(project_dir: Path, module_path: str | None) -> Dict[str, str]:
    if not module_path:
        raise ValueError("extract-docs requires a module path")
    cache_dir = project_dir / ".deepwiki" / "cache"
    skeleton = _load_json(cache_dir / "architecture-skeleton.json")
    module_slug = _module_slug(module_path)
    context_path = cache_dir / "modules" / module_slug / "context.json"
    part_path = cache_dir / f"module-analysis.{module_slug}.json"
    if not context_path.exists():
        raise ValueError(
            "extract-docs context.json missing; run "
            f"prepare_module_context.py before dispatch: {context_path}"
        )

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
        "MODULE_PATH": module_path,
        "MODULE_SLUG": module_slug,
        "MODULE_CONTEXT_PATH": str(context_path),
        "MODULE_ANALYSIS_PART_PATH": str(part_path),
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
    for sf in source_files:
        rel_path = sf.get("path", "")
        ranges = sf.get("ranges", [])
        if ranges:
            for r in ranges:
                start = r.get("start_line", 1)
                end = r.get("end_line", start)
                label = r.get("label", "")
                desc = f" — {label}" if label else ""
                lines.append(f"- [{rel_path}]({_source_link(project_dir, rel_path, start, end)}){desc}")
        else:
            lines.append(f"- [{rel_path}]({_source_link(project_dir, rel_path)})")
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
    snippet_path = cache_dir / "snippets" / f"{_safe_page_id(page_id)}.json"
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
    if not page:
        raise ValueError(f"page_id not found in generation-plan.json: {page_id}")
    output_path = page.get("output_path", "")
    if not output_path:
        raise ValueError(f"page_id has no output_path in generation-plan.json: {page_id}")
    if output_path.startswith("wiki/"):
        output_abs_path = project_dir / ".deepwiki" / output_path
        wiki_rel_path = output_path[len("wiki/"):]
    elif output_path:
        output_abs_path = project_dir / ".deepwiki" / "wiki" / output_path
        wiki_rel_path = output_path
    else:
        output_abs_path = project_dir / ".deepwiki" / "wiki" / f"{page_id.replace(':', '_')}.md"
        wiki_rel_path = ""

    source_modules = page.get("source_modules", page.get("affected_modules", []))
    if not source_modules:
        raise ValueError(f"page_id has no affected modules for generate-module-docs: {page_id}")
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
        "PAGE_ID": page_id,
        "OUTPUT_PATH": output_path,
        "OUTPUT_ABS_PATH": str(output_abs_path),
        "WIKI_REL_PATH": wiki_rel_path,
        "MODULE_NAME": module_data.get("semantic_group") or page.get("title", ""),
        "MODULE_PATH": module_path,
        "CODE_PURPOSE": module_data.get("code_purpose", ""),
        "SELECTED_COMPONENTS": components_str,
        "COMPILED_SPEC": compiled_spec,
        "SOURCE_FILES_BLOCK": source_files_block,
        "MODULE_ANALYSIS_BLOCK": module_analysis_block,
        "SNIPPETS_HINT": snippets_hint,
    }


def _build_quality_fix_vars(project_dir: Path, wiki_path: str | None = None) -> Dict[str, str]:
    target = wiki_path or "由质量报告中的 Basic 文档决定"
    return {
        "TARGET_WIKI_PATH": target,
        "PAGE_CONTEXT_COMMAND": (
            f"deepwiki page-context {project_dir} {wiki_path}"
            if wiki_path
            else "按质量报告中的目标页面逐个运行 deepwiki page-context <项目路径> <wiki_path>"
        ),
        "QUALITY_COMMAND": f"python scripts/postprocess.py quality {project_dir}/.deepwiki --verbose",
    }


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

def main(argv=None):
    parser = argparse.ArgumentParser(description="从模板生成 subagent 系统提示词")
    parser.add_argument("agent_type", choices=BUILDERS.keys(), help="subagent 类型")
    parser.add_argument("--project", required=True, type=Path, help="项目目录")
    parser.add_argument("--module", help="模块路径（extract-docs 使用）")
    parser.add_argument("--page", help="页面 ID（generate-module-docs）或 wiki 路径（quality-fix）")
    parser.add_argument("--output", "-o", type=Path, help="输出文件路径")
    parser.add_argument("--cache", action="store_true", help="输出到 cache/prompts/ 目录")

    args = parser.parse_args(argv)
    project_dir = args.project.resolve()

    # 构建变量
    if args.agent_type == "extract-docs":
        if not args.module:
            parser.error("extract-docs 需要 --module 参数")
        variables = BUILDERS[args.agent_type](project_dir, args.module)
    elif args.agent_type == "generate-module-docs":
        if not args.page:
            parser.error("generate-module-docs 需要 --page 参数")
        variables = BUILDERS[args.agent_type](project_dir, args.page)
    elif args.agent_type == "quality-fix":
        variables = BUILDERS[args.agent_type](project_dir, args.page)
    else:
        variables = BUILDERS[args.agent_type](project_dir)

    # 渲染
    result = render_template(args.agent_type, variables)

    # 输出
    if args.cache:
        cache_dir = project_dir / ".deepwiki" / "cache" / "prompts"
        cache_dir.mkdir(parents=True, exist_ok=True)
        prompt_id = args.page or args.module or args.agent_type
        safe_id = _safe_page_id(prompt_id)
        out_path = cache_dir / f"{args.agent_type}_{safe_id}.md"
        out_path.write_text(result, encoding="utf-8")
        _update_prompt_manifest(project_dir, args.agent_type, prompt_id, safe_id, out_path)
        print(str(out_path))
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
        print(str(args.output))
    else:
        sys.stdout.write(result)


if __name__ == "__main__":
    main()
