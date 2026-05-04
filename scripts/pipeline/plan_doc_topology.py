#!/usr/bin/env python3
"""文档拓扑规划脚本

读取结构缓存并生成最小可用的文档拓扑与编译计划：
- .deepwiki/cache/doc-topology.json
- .deepwiki/cache/generation-plan.json
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from scripts.core.common import (
    CACHE_SCHEMA_VERSION,
    cache_dir,
    cache_path,
    extract_file_source_ranges,
    validate_cache_version,
)


def _load_cache(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data and not validate_cache_version(data):
        stored = data.get("cache_schema_version", "?")
        raise ValueError(
            f"cache schema version mismatch for {path.name}: "
            f"expected {CACHE_SCHEMA_VERSION}, got {stored}. "
            f"Run init-wiki --force to regenerate."
        )
    return data


def _slug(value: str) -> str:
    """Create a stable, readable file stem for generated wiki paths."""
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", value.strip())
    slug = re.sub(r"-+", "-", slug).strip("-_")
    return slug or "topic"


def _detect_monorepo_prefix(module_path: str) -> Tuple[str, str]:
    """Detect monorepo package structure from module path.

    Returns (package_name, slug_stem) where:
    - package_name: the monorepo package directory (e.g., "coding-agent")
    - slug_stem: a meaningful slug for the page file (e.g., "core-tools")

    Skips common convention dirs (src/, lib/) when building slug.
    Handles: packages/*, apps/*, libs/*, modules/*, services/*
    """
    parts = Path(module_path).parts
    monorepo_dirs = {"packages", "apps", "libs", "modules", "services"}

    for i, part in enumerate(parts):
        if part.lower() in monorepo_dirs and i + 1 < len(parts):
            package_name = parts[i + 1]
            # 只跳过紧邻 package 后的首个 src/lib 约定目录
            remaining = list(parts[i + 2:])
            if remaining and remaining[0].lower() in {"src", "lib"}:
                remaining = remaining[1:]
            slug_stem = _slug("-".join(remaining)) if remaining else _slug(package_name)
            return package_name, slug_stem

    return "", ""


def _module_analysis_map(module_analysis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    modules = module_analysis.get("modules", {}) if isinstance(module_analysis, dict) else {}
    if isinstance(modules, dict):
        return {str(name): data for name, data in modules.items() if isinstance(data, dict)}
    if isinstance(modules, list):
        result: Dict[str, Dict[str, Any]] = {}
        for item in modules:
            if not isinstance(item, dict):
                continue
            key = item.get("name") or Path(item.get("module_path", "")).name
            if key:
                result[str(key)] = item
        return result
    return {}


def _page_bucket(module_name: str, module_path: str, analysis: Dict[str, Any]) -> Tuple[str, str, str]:
    """Return (page_type, group_key, path_prefix) for a source module."""
    purpose = analysis.get("code_purpose", "")
    infrastructure_purposes = {"Dao", "Model", "Config", "Database", "Util", "Widget", "Other"}
    page_type = "internal" if purpose in infrastructure_purposes else "capability"

    package_name, _ = _detect_monorepo_prefix(module_path or module_name)
    prefix = f"deep-dive/{package_name}" if package_name else "deep-dive"

    return page_type, prefix, prefix


def _module_title(module_name: str, analysis: Dict[str, Any]) -> str:
    semantic_group = str(analysis.get("semantic_group", "")).strip()
    if semantic_group and semantic_group.lower() not in {"unknown", "other"}:
        return semantic_group
    # Fall back to a human-readable label derived from the module name:
    # take the last path segment, replace separators with spaces, title-case.
    stem = Path(module_name.rstrip("/\\")).name or module_name
    return stem.replace("-", " ").replace("_", " ").title()


def _source_files_for_module(
    analysis: Dict[str, Any], structure_module: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Extract source-file ranges used by module documentation generation."""
    source_files: List[Dict[str, Any]] = []
    for file_data in analysis.get("files", []):
        if not isinstance(file_data, dict) or not file_data.get("path"):
            continue
        ranges = extract_file_source_ranges(file_data, include_reason=True)
        source_files.append({
            "path": file_data["path"],
            "summary": file_data.get("summary", ""),
            "ranges": ranges,
        })
    if source_files:
        return source_files

    for core_file in structure_module.get("core_files", []):
        if isinstance(core_file, str):
            source_files.append({"path": core_file, "summary": "", "ranges": []})
        elif isinstance(core_file, dict) and core_file.get("path"):
            source_files.append({
                "path": core_file["path"],
                "summary": core_file.get("summary", ""),
                "ranges": [],
            })
    return source_files


def _build_pages(structure: Dict[str, Any], module_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    analysis_by_module = _module_analysis_map(module_analysis)
    pages: List[Dict[str, Any]] = [
        {
            "id": "overview",
            "type": "overview",
            "title": "项目概览",
            "output_path": "wiki/overview.md",
            "source_modules": [],
            "depends_on": ["structure.json", "code-structure.json"],
        },
        {
            "id": "getting-started",
            "type": "guide",
            "title": "快速开始",
            "output_path": "wiki/getting-started.md",
            "source_modules": [],
            "depends_on": ["structure.json"],
        },
        {
            "id": "doc-map",
            "type": "map",
            "title": "文档地图",
            "output_path": "wiki/doc-map.md",
            "source_modules": [],
            "depends_on": ["doc-topology.json", "generation-plan.json"],
        },
        {
            "id": "concept:architecture",
            "type": "concept",
            "title": "架构与设计视角",
            "output_path": "wiki/concepts/architecture.md",
            "source_modules": [],
            "depends_on": ["structure.json", "code-structure.json", "architecture-skeleton.json"],
        },
        {
            "id": "concept:development-guide",
            "type": "concept",
            "title": "继续开发指南",
            "output_path": "wiki/concepts/development-guide.md",
            "source_modules": [],
            "depends_on": ["module-analysis.json", "evidence-index.json"],
        },
        {
            "id": "reference:api-surface",
            "type": "reference",
            "title": "接口与配置索引",
            "output_path": "wiki/reference/api-surface.md",
            "source_modules": [],
            "depends_on": ["module-analysis.json"],
        },
    ]

    for module in structure.get("modules", []):
        module_name = module.get("name")
        module_path = module.get("path", module_name or "")
        if not module_name:
            continue
        analysis = analysis_by_module.get(module_path, analysis_by_module.get(module_name, {}))
        page_type, _, prefix = _page_bucket(module_name, module_path, analysis)
        title = _module_title(module_name, analysis)
        package_name, monorepo_slug = _detect_monorepo_prefix(module_path)
        page_id = f"deep-dive:{package_name}/{module_name}" if package_name else f"deep-dive:{module_name}"
        page_slug = monorepo_slug if monorepo_slug else _slug(module_name)
        pages.append({
            "id": page_id,
            "type": page_type,
            "title": title,
            "output_path": f"wiki/{prefix}/{page_slug}.md",
            "source_modules": [module_path],
            "source_files": _source_files_for_module(analysis, module),
            "depends_on": ["module-analysis.json", "code-structure.json"],
            "source_view": "top-down + bottom-up + feynman",
            "package_group": package_name or None,
        })
    return pages


def plan_doc_topology(project_root: Path) -> Dict[str, Any]:
    """从缓存构建文档拓扑与编译计划。"""
    root = Path(project_root)
    structure = _load_cache(cache_path(root, "structure.json"))
    code_structure = _load_cache(cache_path(root, "code-structure.json"))
    module_analysis = _load_cache(cache_path(root, "module-analysis.json"))

    if not structure:
        raise FileNotFoundError(f"structure.json not found: {cache_path(root, 'structure.json')}")

    pages = _build_pages(structure, module_analysis)
    generated_at = datetime.now(timezone.utc).isoformat()

    # Build nested sub-groupings for deep-dive by package directory
    deep_dive_pages = [
        (page["id"], page.get("title", page["id"]), page.get("package_group"))
        for page in pages
        if page["type"] in {"capability", "internal"}
    ]
    package_groups: Dict[str, List[str]] = {}
    for page_id, title, pkg in deep_dive_pages:
        key = pkg if pkg else title
        package_groups.setdefault(key, []).append(page_id)
    # Use nested dict when any sub-group has multiple pages
    _has_multi = any(len(v) > 1 for v in package_groups.values())
    deep_dive_grouping: Any = (
        dict(package_groups) if _has_multi
        else [pid for pid, _, _ in deep_dive_pages]
    )

    doc_topology = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "generated_at": generated_at,
        "project_name": structure.get("project_name", root.name),
        "pages": pages,
        "reading_order": [page["id"] for page in pages],
        "groupings": {
            "overview": ["overview", "getting-started", "doc-map"],
            "concepts": [page["id"] for page in pages if page["type"] == "concept"],
            "deep-dive": deep_dive_grouping,
            "reference": [page["id"] for page in pages if page["type"] == "reference"],
        },
        "sources": {
            "structure": "structure.json",
            "code_structure": "code-structure.json" if code_structure else None,
        },
    }

    generation_plan = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "generated_at": generated_at,
        "project_name": structure.get("project_name", root.name),
        "recompile_all": True,
        "pages": [
            {
                "page_id": page["id"],
                "output_path": page["output_path"],
                "inputs": page["depends_on"],
                "affected_modules": page["source_modules"],
                "source_files": page.get("source_files", []),
                "action": "create",
            }
            for page in pages
        ],
    }

    out_dir = cache_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_path(root, "doc-topology.json"), "w", encoding="utf-8") as f:
        json.dump(doc_topology, f, ensure_ascii=False, indent=2)
    with open(cache_path(root, "generation-plan.json"), "w", encoding="utf-8") as f:
        json.dump(generation_plan, f, ensure_ascii=False, indent=2)

    return {
        "doc_topology": doc_topology,
        "generation_plan": generation_plan,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Usage: python -m scripts.pipeline.plan_doc_topology <project_dir>")
        sys.exit(0)
    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.getcwd())
    result = plan_doc_topology(project_path)
    print(
        f"Planned {len(result['doc_topology']['pages'])} pages for "
        f"{result['doc_topology']['project_name']}"
    )
