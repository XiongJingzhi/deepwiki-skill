"""Prepare a lightweight project inventory for the agentic workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


CACHE_SCHEMA_VERSION = 1

LANG_BY_EXT = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
}
CONFIG_KINDS = {
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "package.json": "node",
    "pnpm-lock.yaml": "node",
    "yarn.lock": "node",
    "package-lock.json": "node",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pom.xml": "java",
    "build.gradle": "java",
    "vite.config.ts": "frontend",
    "next.config.js": "frontend",
}
DOC_EXTENSIONS = {".md", ".mdx", ".rst"}
BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".mp4",
    ".mp3",
    ".woff",
    ".woff2",
}
IGNORE_DIRS = {
    ".git",
    ".deepwiki",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
}
IGNORE_FILES = {".DS_Store"}
GENERATED_MARKERS = ("/dist/", "/build/", ".min.js", ".lock")
TEST_MARKERS = ("/test/", "/tests/", "_test.", ".test.", ".spec.", "test_")
ENTRY_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "cli.py",
    "index.js",
    "index.ts",
    "main.go",
    "main.rs",
}


def _rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _is_ignored(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    if any(part in IGNORE_DIRS for part in rel_parts):
        return True
    return path.name in IGNORE_FILES


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]


def _is_test(rel_path: str) -> bool:
    normalized = f"/{rel_path}"
    return any(marker in normalized for marker in TEST_MARKERS)


def _is_generated(rel_path: str) -> bool:
    normalized = f"/{rel_path}"
    return any(marker in normalized for marker in GENERATED_MARKERS)


def _category(path: Path, rel_path: str) -> str:
    if _is_test(rel_path):
        return "test"
    if path.name in CONFIG_KINDS:
        return "config"
    if path.suffix.lower() in DOC_EXTENSIONS:
        return "doc"
    if path.suffix.lower() in LANG_BY_EXT:
        return "code"
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return "asset"
    if path.suffix.lower() in {".json", ".yaml", ".yml", ".toml", ".csv"}:
        return "data"
    return "other"


def _package_managers(files: Iterable[Dict[str, Any]]) -> List[str]:
    names = {item["name"] for item in files}
    managers = []
    if {"pyproject.toml", "requirements.txt"} & names:
        managers.append("pip")
    if {"package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json"} & names:
        managers.append("npm")
    if "go.mod" in names:
        managers.append("go")
    if "Cargo.toml" in names:
        managers.append("cargo")
    if {"pom.xml", "build.gradle"} & names:
        managers.append("java")
    return managers


def _frameworks(files: Iterable[Dict[str, Any]]) -> List[str]:
    paths = {item["path"] for item in files}
    names = {item["name"] for item in files}
    frameworks = []
    if "next.config.js" in names:
        frameworks.append("nextjs")
    if "vite.config.ts" in names or "vite.config.js" in names:
        frameworks.append("vite")
    if "manage.py" in names:
        frameworks.append("django")
    if any(path.startswith("app/") for path in paths) and "package.json" in names:
        frameworks.append("frontend-app")
    return frameworks


def _top_level(root: Path) -> Dict[str, List[str]]:
    dirs: List[str] = []
    files: List[str] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if _is_ignored(child, root):
            continue
        if child.is_dir():
            dirs.append(child.name)
        elif child.is_file():
            files.append(child.name)
    return {"top_level_dirs": dirs, "top_level_files": files}


def _max_depth(paths: Iterable[str]) -> int:
    depth = 0
    for path in paths:
        depth = max(depth, len(Path(path).parts))
    return depth


def prepare_inventory(project_path: str | Path, save_to_cache: bool = False) -> Dict[str, Any]:
    root = Path(project_path).resolve()
    file_entries: List[Dict[str, Any]] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if _is_ignored(path, root):
            continue
        if path.suffix.lower() in BINARY_EXTENSIONS:
            continue

        rel_path = _rel(path, root)
        ext = path.suffix.lower()
        category = _category(path, rel_path)
        entry = {
            "path": rel_path,
            "name": path.name,
            "extension": ext,
            "size": path.stat().st_size,
            "hash": _hash_file(path),
            "category": category,
            "language": LANG_BY_EXT.get(ext),
            "is_test": category == "test",
            "is_config": category == "config",
            "is_doc": category == "doc",
            "is_generated": _is_generated(rel_path),
        }
        file_entries.append(entry)

    languages = sorted({entry["language"] for entry in file_entries if entry["language"]})
    top_level = _top_level(root)
    stats = {
        "total_files": len(file_entries),
        "code_files": sum(1 for entry in file_entries if entry["category"] == "code"),
        "test_files": sum(1 for entry in file_entries if entry["is_test"]),
        "config_files": sum(1 for entry in file_entries if entry["is_config"]),
        "doc_files": sum(1 for entry in file_entries if entry["is_doc"]),
        "generated_files": sum(1 for entry in file_entries if entry["is_generated"]),
    }
    inventory = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_name": root.name,
        "root_path": str(root),
        "languages": languages,
        "frameworks": _frameworks(file_entries),
        "package_managers": _package_managers(file_entries),
        "entry_candidates": [
            {"path": entry["path"], "reason": "main-like filename"}
            for entry in file_entries
            if entry["name"] in ENTRY_NAMES
        ],
        "important_configs": [
            {"path": entry["path"], "kind": CONFIG_KINDS[entry["name"]]}
            for entry in file_entries
            if entry["name"] in CONFIG_KINDS
        ],
        "docs_found": [entry["path"] for entry in file_entries if entry["is_doc"]],
        "ignore_rules": {
            "default_ignored_dirs": sorted(IGNORE_DIRS),
            "default_ignored_files": sorted(IGNORE_FILES),
            "gitignore_used": (root / ".gitignore").exists(),
        },
        "tree_summary": {
            "max_depth": _max_depth(entry["path"] for entry in file_entries),
            **top_level,
        },
        "stats": stats,
        "files": file_entries,
    }

    if save_to_cache:
        cache_dir = root / ".deepwiki" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "project-inventory.json").write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return inventory


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare DeepWiki project inventory")
    parser.add_argument("project_path")
    args = parser.parse_args(argv)
    result = prepare_inventory(Path(args.project_path), save_to_cache=True)
    print(f"Prepared inventory with {result['stats']['total_files']} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
