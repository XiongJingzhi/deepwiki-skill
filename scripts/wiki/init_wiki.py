"""Initialize a clean DeepWiki workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG = """generation:
  language: zh
  mode: agentic
"""


def init_wiki(project_path: str | Path, force: bool = False) -> Dict[str, Any]:
    root = Path(project_path)
    deepwiki = root / ".deepwiki"
    if deepwiki.exists() and not force:
        return {
            "success": True,
            "path": str(deepwiki),
            "message": ".deepwiki already exists",
        }

    (deepwiki / "cache" / "page-context").mkdir(parents=True, exist_ok=True)
    (deepwiki / "state").mkdir(parents=True, exist_ok=True)
    (deepwiki / "wiki").mkdir(parents=True, exist_ok=True)

    config_path = deepwiki / "config.yaml"
    if force or not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")

    return {
        "success": True,
        "path": str(deepwiki),
        "message": "initialized .deepwiki",
    }
