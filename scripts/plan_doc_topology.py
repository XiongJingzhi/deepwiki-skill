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

from common import CACHE_SCHEMA_VERSION, cache_dir, cache_path, validate_cache_version


def _load_cache(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data and not validate_cache_version(data):
        raise ValueError(f"cache schema version mismatch for {path.name}")
    return data


def _slug(value: str) -> str:
    """Create a stable, readable file stem for generated wiki paths."""
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", value.strip())
    slug = re.sub(r"-+", "-", slug).strip("-_")
    return slug or "topic"


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


def _page_bucket(module_name: str, analysis: Dict[str, Any]) -> Tuple[str, str, str]:
    """Return (page_type, group_key, path_prefix) for a source module."""
    purpose = analysis.get("code_purpose", "")
    infrastructure_purposes = {"Dao", "Model", "Config", "Database", "Util", "Widget", "Other"}
    if purpose in infrastructure_purposes:
        return "internal", "deep-dive", "deep-dive"
    return "capability", "deep-dive", "deep-dive"


def _module_title(module_name: str, analysis: Dict[str, Any]) -> str:
    semantic_group = str(analysis.get("semantic_group", "")).strip()
    if semantic_group and semantic_group.lower() not in {"unknown", "other"}:
        return semantic_group
    return module_name


def _source_files_for_module(
    analysis: Dict[str, Any], structure_module: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Extract source-file ranges used by module documentation generation."""
    source_files: List[Dict[str, Any]] = []
    for file_data in analysis.get("files", []):
        if not isinstance(file_data, dict) or not file_data.get("path"):
            continue

        ranges: List[Dict[str, Any]] = []
        for source_range in file_data.get("core_source_ranges", []):
            if not isinstance(source_range, dict):
                continue
            start = source_range.get("start_line")
            end = source_range.get("end_line", start)
            if not start:
                continue
            ranges.append({
                "start_line": start,
                "end_line": end,
                "label": source_range.get("label") or source_range.get("name") or "core source",
                "reason": source_range.get("reason") or source_range.get("summary") or "core source range",
            })

        for interface in file_data.get("public_interfaces", []):
            if not isinstance(interface, dict):
                continue
            start = interface.get("line")
            end = interface.get("end_line", start)
            if not start:
                continue
            ranges.append({
                "start_line": start,
                "end_line": end,
                "label": interface.get("name") or "public interface",
                "reason": "public interface",
            })

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
        analysis = analysis_by_module.get(module_name, {})
        page_type, _, prefix = _page_bucket(module_name, analysis)
        title = _module_title(module_name, analysis)
        page_id = f"deep-dive:{module_name}"
        pages.append({
            "id": page_id,
            "type": page_type,
            "title": title,
            "output_path": f"wiki/{prefix}/{_slug(module_name)}.md",
            "source_modules": [module_path],
            "source_files": _source_files_for_module(analysis, module),
            "depends_on": ["module-analysis.json", "code-structure.json"],
            "source_view": "top-down + bottom-up + feynman",
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

    doc_topology = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "generated_at": generated_at,
        "project_name": structure.get("project_name", root.name),
        "pages": pages,
        "reading_order": [page["id"] for page in pages],
        "groupings": {
            "overview": ["overview", "getting-started", "doc-map"],
            "concepts": [page["id"] for page in pages if page["type"] == "concept"],
            "deep-dive": [
                page["id"]
                for page in pages
                if page["type"] in {"capability", "internal"}
            ],
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

    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.getcwd())
    result = plan_doc_topology(project_path)
    print(
        f"Planned {len(result['doc_topology']['pages'])} pages for "
        f"{result['doc_topology']['project_name']}"
    )
