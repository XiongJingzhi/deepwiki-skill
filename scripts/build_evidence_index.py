#!/usr/bin/env python3
"""构建 DeepWiki 证据索引。

该脚本从 module-analysis.json 中抽取基础 claim，并把 claim 映射到源码文件证据。
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from common import CACHE_SCHEMA_VERSION, cache_dir, cache_path, validate_cache_version


def _load_module_analysis(project_root: Path) -> Dict[str, Any]:
    path = cache_path(project_root, "module-analysis.json")
    if not path.exists():
        raise FileNotFoundError(f"module-analysis.json not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not validate_cache_version(data):
        raise ValueError("module-analysis.json schema version mismatch")
    return data.get("modules", {})


def _evidence_for_module(module: Dict[str, Any]) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    for file_data in module.get("files", []):
        path = file_data.get("path") if isinstance(file_data, dict) else None
        if path:
            ranges: List[Dict[str, Any]] = []
            for source_range in file_data.get("core_source_ranges", []):
                if not isinstance(source_range, dict):
                    continue
                start = source_range.get("start_line")
                end = source_range.get("end_line", start)
                if start:
                    ranges.append({
                        "start_line": start,
                        "end_line": end,
                        "label": source_range.get("label") or source_range.get("name") or "core source",
                    })
            for interface in file_data.get("public_interfaces", []):
                if not isinstance(interface, dict):
                    continue
                start = interface.get("line")
                end = interface.get("end_line", start)
                if start:
                    ranges.append({
                        "start_line": start,
                        "end_line": end,
                        "label": interface.get("name") or "public interface",
                    })

            item = {
                "type": "file",
                "path": path,
                "source": "module-analysis",
            }
            if ranges:
                item["ranges"] = ranges
            evidence.append(item)
    return evidence


def _page_prefix_for_module(module: Dict[str, Any]) -> str:
    return "deep-dive"


def build_evidence_index(project_root: Path) -> Dict[str, Any]:
    """Build and write cache/evidence-index.json."""
    root = Path(project_root)
    modules = _load_module_analysis(root)
    generated_at = datetime.now(timezone.utc).isoformat()

    claims: List[Dict[str, Any]] = []
    for mod_name, module in modules.items():
        if not isinstance(module, dict):
            continue
        evidence = _evidence_for_module(module)
        for field in ("module_summary", "module_role"):
            text = module.get(field)
            if not text:
                continue
            page_prefix = _page_prefix_for_module(module)
            claims.append({
                "claim_id": f"{page_prefix}:{mod_name}:{field}",
                "page_id": f"{page_prefix}:{mod_name}",
                "claim_text": text,
                "evidence": evidence,
                "confidence": "high" if evidence else "low",
            })

    result = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "generated_at": generated_at,
        "claims": claims,
    }

    cache_dir(root).mkdir(parents=True, exist_ok=True)
    with open(cache_path(root, "evidence-index.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    import sys

    project_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.getcwd())
    result = build_evidence_index(project_path)
    print(f"Built evidence index with {len(result['claims'])} claims")
