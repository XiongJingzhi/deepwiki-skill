#!/usr/bin/env python3
"""文档拓扑规划脚本

读取结构缓存并生成最小可用的文档拓扑与编译计划：
- .deepwiki/cache/doc-topology.json
- .deepwiki/cache/generation-plan.json
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from common import CACHE_SCHEMA_VERSION, cache_dir, cache_path, validate_cache_version


def _load_cache(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data and not validate_cache_version(data):
        raise ValueError(f"cache schema version mismatch for {path.name}")
    return data


def _build_pages(structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    pages: List[Dict[str, Any]] = [
        {
            "id": "overview",
            "type": "overview",
            "title": "Overview",
            "output_path": "wiki/overview.md",
            "source_modules": [],
            "depends_on": ["structure.json", "code-structure.json"],
        },
        {
            "id": "getting-started",
            "type": "guide",
            "title": "Getting Started",
            "output_path": "wiki/getting-started.md",
            "source_modules": [],
            "depends_on": ["structure.json"],
        },
        {
            "id": "doc-map",
            "type": "map",
            "title": "Doc Map",
            "output_path": "wiki/doc-map.md",
            "source_modules": [],
            "depends_on": ["doc-topology.json", "generation-plan.json"],
        },
    ]

    for module in structure.get("modules", []):
        module_name = module.get("name")
        module_path = module.get("path", module_name or "")
        if not module_name:
            continue
        pages.append({
            "id": f"module:{module_name}",
            "type": "module",
            "title": module_name,
            "output_path": f"wiki/modules/{module_name}.md",
            "source_modules": [module_path],
            "depends_on": ["module-analysis.json", "code-structure.json"],
        })
        pages.append({
            "id": f"api:{module_name}",
            "type": "api",
            "title": f"{module_name} API",
            "output_path": f"wiki/api/{module_name}.md",
            "source_modules": [module_path],
            "depends_on": ["module-analysis.json"],
        })
    return pages


def plan_doc_topology(project_root: Path) -> Dict[str, Any]:
    """从缓存构建文档拓扑与编译计划。"""
    root = Path(project_root)
    structure = _load_cache(cache_path(root, "structure.json"))
    code_structure = _load_cache(cache_path(root, "code-structure.json"))

    if not structure:
        raise FileNotFoundError(f"structure.json not found: {cache_path(root, 'structure.json')}")

    pages = _build_pages(structure)
    generated_at = datetime.now(timezone.utc).isoformat()

    doc_topology = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "generated_at": generated_at,
        "project_name": structure.get("project_name", root.name),
        "pages": pages,
        "reading_order": [page["id"] for page in pages],
        "groupings": {
            "overview": ["overview", "getting-started", "doc-map"],
            "modules": [page["id"] for page in pages if page["type"] == "module"],
            "api": [page["id"] for page in pages if page["type"] == "api"],
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
