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
    if data.get("cache_schema_version") is not None and not validate_cache_version(data):
        raise ValueError("module-analysis.json schema version mismatch")
    modules = data.get("modules", data)
    return modules if isinstance(modules, dict) else {}


def _evidence_for_module(module: Dict[str, Any]) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    for file_data in module.get("files", []):
        path = file_data.get("path") if isinstance(file_data, dict) else None
        if path:
            evidence.append({
                "type": "file",
                "path": path,
                "source": "module-analysis",
            })
    return evidence


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
            claims.append({
                "claim_id": f"module:{mod_name}:{field}",
                "page_id": f"module:{mod_name}",
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
