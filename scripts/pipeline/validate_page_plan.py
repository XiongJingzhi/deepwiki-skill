"""Validate an agentic DeepWiki page plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


REQUIRED_PAGE_FIELDS = {
    "page_id",
    "title",
    "output_path",
    "page_type",
    "purpose",
    "source_targets",
    "depends_on",
    "status",
}


def _duplicates(values: List[str]) -> List[str]:
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _safe_markdown_path(path: str) -> bool:
    candidate = Path(path)
    return not candidate.is_absolute() and ".." not in candidate.parts and candidate.suffix == ".md"


def validate_page_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    pages = plan.get("pages", [])
    if not isinstance(pages, list):
        return {"ok": False, "errors": ["pages must be a list"]}

    page_ids: List[str] = []
    output_paths: List[str] = []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            errors.append(f"pages[{index}] must be an object")
            continue

        missing = sorted(REQUIRED_PAGE_FIELDS - set(page))
        if missing:
            errors.append(f"pages[{index}] missing fields: {', '.join(missing)}")

        page_id = page.get("page_id")
        if isinstance(page_id, str) and page_id:
            page_ids.append(page_id)
        else:
            errors.append(f"pages[{index}] page_id must be non-empty")

        output_path = page.get("output_path")
        if isinstance(output_path, str) and output_path:
            output_paths.append(output_path)
            if not _safe_markdown_path(output_path):
                errors.append(f"pages[{index}] output_path is unsafe or not markdown: {output_path}")
        else:
            errors.append(f"pages[{index}] output_path must be non-empty")

        if not page.get("source_targets"):
            errors.append(f"pages[{index}] source_targets must be non-empty")

    for page_id in _duplicates(page_ids):
        errors.append(f"duplicate page_id: {page_id}")
    for output_path in _duplicates(output_paths):
        errors.append(f"duplicate output_path: {output_path}")

    generation_order = plan.get("generation_order", [])
    if not isinstance(generation_order, list):
        errors.append("generation_order must be a list")
    else:
        known = set(page_ids)
        ordered = set(generation_order)
        missing_from_order = sorted(known - ordered)
        unknown_in_order = sorted(ordered - known)
        if missing_from_order:
            errors.append(f"generation_order missing pages: {', '.join(missing_from_order)}")
        if unknown_in_order:
            errors.append(f"generation_order references unknown pages: {', '.join(unknown_in_order)}")

    return {"ok": not errors, "errors": errors}


def _page_plan_path(project_path: Path) -> Path:
    return project_path / ".deepwiki" / "cache" / "page-plan.json"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate DeepWiki page plan")
    parser.add_argument("project_path")
    args = parser.parse_args(argv)

    path = _page_plan_path(Path(args.project_path))
    plan = json.loads(path.read_text(encoding="utf-8"))
    result = validate_page_plan(plan)
    if result["ok"]:
        print("Page plan is valid.")
        return 0
    print("Page plan is invalid:")
    for error in result["errors"]:
        print(f"  - {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
