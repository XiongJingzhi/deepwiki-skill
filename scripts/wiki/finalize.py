"""Finalize and validate an agentic DeepWiki output."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from scripts.wiki.generate_menu import generate_menu


MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def _load_plan(project_path: Path) -> Dict[str, Any]:
    path = project_path / ".deepwiki" / "cache" / "page-plan.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _is_external_link(target: str) -> bool:
    parsed = urlparse(target)
    return parsed.scheme in {"http", "https", "mailto"}


def _link_target_exists(project_path: Path, page_path: Path, target: str) -> bool:
    if _is_external_link(target) or target.startswith("#"):
        return True
    clean_target = target.split("#", 1)[0]
    if not clean_target:
        return True
    candidate = (page_path.parent / clean_target).resolve()
    if candidate.exists():
        return True
    return (project_path / clean_target).resolve().exists()


def _check_links(project_path: Path, wiki_dir: Path, pages: List[Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    for page in pages:
        if page.get("status") == "skipped":
            continue
        page_path = wiki_dir / page["output_path"]
        if not page_path.exists():
            continue
        text = page_path.read_text(encoding="utf-8", errors="replace")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if not _link_target_exists(project_path, page_path, target):
                errors.append(f"broken link in {page['output_path']}: {target}")
    return errors


def finalize_wiki(project_path: str | Path) -> int:
    root = Path(project_path)
    wiki_dir = root / ".deepwiki" / "wiki"
    errors: List[str] = []
    try:
        plan = _load_plan(root)
    except FileNotFoundError:
        print("Finalize failed: missing .deepwiki/cache/page-plan.json")
        return 1

    pages = plan.get("pages", [])
    for page in pages:
        if page.get("status") == "skipped":
            continue
        output_path = page.get("output_path")
        if not output_path or not (wiki_dir / output_path).exists():
            errors.append(f"missing planned page: {output_path or page.get('page_id')}")

    errors.extend(_check_links(root, wiki_dir, pages))

    try:
        generate_menu(root)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        errors.append(f"menu generation failed: {exc}")

    if errors:
        print("Finalize failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Finalize completed successfully.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Finalize DeepWiki output")
    parser.add_argument("project_path")
    args = parser.parse_args(argv)
    return finalize_wiki(Path(args.project_path))


if __name__ == "__main__":
    raise SystemExit(main())
