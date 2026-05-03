"""page_context: Extract generation context for a given wiki page.

Usage (CLI):
    python page_context.py <project_path> <wiki_rel_path>

Example:
    python page_context.py /my/project wiki/deep-dive/graph.md

Returns JSON with:
- page_path           : requested wiki-relative path (normalized)
- menu_entry          : matching entry in menu.json {title, path, section, group, planned}
- module_key          : key in module-analysis.json (null if not matched)
- module_summary      : one-sentence module description
- module_role         : module role in the system
- core_files          : list of core source file paths
- key_insights        : merged key_insights across files (up to 10)
- dependency_hints    : {imports, imported_by}
- selected_components : component list already decided by extract-docs
- risk_points         : known risk points
- extension_points    : extension points
- code_purpose        : module CodePurpose tag
- semantic_group      : semantic theme label
- analysis_depth      : analysis depth (deep/standard/quick)
- current_line_count  : current .md line count (0 if not yet generated)
- errors              : list of warnings/errors (missing cache, unmatched path, etc.)
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_json(path: Path) -> Any:
    """Load JSON; return None on missing file or parse error."""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _normalize_path(p: str) -> str:
    """Normalize to forward slash and strip optional leading "wiki/"."""
    p = p.replace("\\", "/").replace("\\\\", "/")
    if p.startswith("wiki/"):
        p = p[len("wiki/"):]
    return p


def _iter_menu_leaves(menu_data: dict):
    """Yield (section_title, group_title, entry) for every leaf node."""
    for section in menu_data.get("items", []):
        section_title = section.get("title", "")
        for item in section.get("items", []):
            sub_items = item.get("items", [])
            if sub_items:
                for sub in sub_items:
                    if "path" in sub:
                        yield section_title, item.get("title", ""), sub
            else:
                if "path" in item:
                    yield section_title, "", item


def _find_menu_entry(menu_data: dict, wiki_rel_path: str) -> Optional[Dict]:
    """Return menu leaf entry matching wiki_rel_path."""
    needle = _normalize_path(wiki_rel_path)
    for section_title, group_title, entry in _iter_menu_leaves(menu_data):
        if _normalize_path(entry.get("path", "")) == needle:
            return {
                "title": entry.get("title", ""),
                "path": entry.get("path", ""),
                "section": section_title,
                "group": group_title,
                "planned": entry.get("planned", False),
            }
    return None


def _stem_of(wiki_rel_path: str) -> str:
    return Path(wiki_rel_path).stem.replace("-", "_").lower()


def _find_module_key(module_analysis: dict, wiki_rel_path: str) -> Optional[str]:
    """Match wiki path to a module key using three strategies.

    1. Exact match on module_data["doc_path"] (if the field exists).
    2. Stem of wiki path matches last segment of module_path.
    3. Module key itself matches stem.
    """
    needle_norm = _normalize_path(wiki_rel_path)
    needle_stem = _stem_of(wiki_rel_path)

    modules: Dict[str, Any] = module_analysis.get("modules", module_analysis)
    if not isinstance(modules, dict):
        return None

    # Pass 1: exact doc_path
    for key, data in modules.items():
        if not isinstance(data, dict):
            continue
        doc_path = _normalize_path(data.get("doc_path", ""))
        if doc_path and doc_path == needle_norm:
            return key

    # Pass 2: module_path stem
    for key, data in modules.items():
        if not isinstance(data, dict):
            continue
        mod_path = data.get("module_path", key)
        mod_stem = Path(mod_path).name.replace("-", "_").lower()
        if mod_stem == needle_stem:
            return key

    # Pass 3: key stem
    for key in modules:
        if key.replace("-", "_").lower() == needle_stem:
            return key

    return None


def _extract_module_context(module_data: dict) -> Dict:
    """Pull relevant fields from a module-analysis entry."""
    from scripts.core.common import extract_file_source_ranges

    all_insights: List[str] = []
    core_files: List[str] = []
    source_ranges: List[dict] = []
    for f in module_data.get("files", []):
        path = f.get("path", "")
        if path:
            core_files.append(path)
            ranges = extract_file_source_ranges(f)
            if ranges:
                source_ranges.append({"path": path, "ranges": ranges})
        for insight in f.get("key_insights", []):
            if insight and insight not in all_insights:
                all_insights.append(insight)

    return {
        "module_summary": module_data.get("module_summary", ""),
        "module_role": module_data.get("module_role", ""),
        "core_files": core_files[:20],
        "source_ranges": source_ranges[:20],
        "key_insights": all_insights[:10],
        "dependency_hints": module_data.get("dependency_hints", {}),
        "selected_components": module_data.get("selected_components", []),
        "risk_points": module_data.get("risk_points", []),
        "extension_points": module_data.get("extension_points", []),
        "code_purpose": module_data.get("code_purpose", ""),
        "semantic_group": module_data.get("semantic_group", ""),
        "analysis_depth": module_data.get("analysis_depth", ""),
    }


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def get_page_context(project_path: Path, wiki_rel_path: str) -> Dict:
    """Return generation context for the given wiki page.

    Args:
        project_path: project root (parent of .deepwiki/)
        wiki_rel_path: relative path under wiki/ e.g. "deep-dive/graph.md"
                       or "wiki/deep-dive/graph.md" — both accepted.
    """
    errors: List[str] = []
    deepwiki = project_path / ".deepwiki"
    wiki_dir = deepwiki / "wiki"
    cache_dir = deepwiki / "cache"

    wiki_rel_clean = _normalize_path(wiki_rel_path)

    # 1. Resolve .md file
    md_abs = wiki_dir / wiki_rel_clean
    current_line_count = _count_lines(md_abs)
    if not md_abs.exists():
        errors.append(f"Page not yet generated: {md_abs}")

    # 2. menu.json
    menu_data = _load_json(wiki_dir / "menu.json")
    menu_entry = None
    if menu_data is None:
        errors.append("menu.json not found or invalid in wiki/")
    else:
        menu_entry = _find_menu_entry(menu_data, wiki_rel_clean)
        if menu_entry is None:
            errors.append(f"Path \"{wiki_rel_clean}\" not found in menu.json")

    # 3. module-analysis.json
    module_analysis = _load_json(cache_dir / "module-analysis.json")
    module_key = None
    module_ctx: Dict = {}
    if module_analysis is None:
        errors.append("module-analysis.json not found in cache/")
    else:
        module_key = _find_module_key(module_analysis, wiki_rel_clean)
        if module_key is None:
            errors.append(
                f"Could not match \"{wiki_rel_clean}\" to any module key in "
                "module-analysis.json — context will be incomplete"
            )
        else:
            modules = module_analysis.get("modules", module_analysis)
            module_data = modules.get(module_key, {})
            module_ctx = _extract_module_context(module_data)

    return {
        "page_path": wiki_rel_clean,
        "menu_entry": menu_entry,
        "module_key": module_key,
        **module_ctx,
        "current_line_count": current_line_count,
        "errors": errors,
    }


def print_context(ctx: Dict) -> None:
    print(json.dumps(ctx, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: page_context.py <project_path> <wiki_rel_path>", file=sys.stderr)
        raise SystemExit(1)
    result = get_page_context(Path(sys.argv[1]), sys.argv[2])
    print_context(result)
    raise SystemExit(1 if result["errors"] else 0)
