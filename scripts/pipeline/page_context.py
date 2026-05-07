"""Build per-page context for the agentic generation stage."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def _safe_page_id(page_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", page_id).strip("_") or "page"


def _load_plan(project_path: Path) -> Dict[str, Any]:
    path = project_path / ".deepwiki" / "cache" / "page-plan.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _find_page(plan: Dict[str, Any], page_id: str) -> Dict[str, Any]:
    for page in plan.get("pages", []):
        if page.get("page_id") == page_id:
            return page
    raise ValueError(f"page_id not found in page-plan.json: {page_id}")


def _related_pages(plan: Dict[str, Any], page_id: str, page: Dict[str, Any]) -> List[str]:
    related = set(page.get("depends_on", []))
    for candidate in plan.get("pages", []):
        if page_id in candidate.get("depends_on", []):
            related.add(candidate.get("page_id"))
    related.discard(None)
    related.discard(page_id)
    return sorted(related)


def _excerpt(path: Path, max_excerpt_chars: int) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    clipped = text[:max_excerpt_chars]
    end_line = max(1, clipped.count("\n") + 1)
    return {
        "text": clipped,
        "start_line": 1,
        "end_line": end_line,
    }


def build_page_context(
    project_path: str | Path,
    page_id: str,
    max_excerpt_chars: int = 12000,
    save_to_cache: bool = False,
) -> Dict[str, Any]:
    root = Path(project_path)
    plan = _load_plan(root)
    page = _find_page(plan, page_id)
    constraints: List[str] = ["Do not invent APIs, call chains, or runtime behavior."]
    source_files: List[Dict[str, str]] = []
    source_excerpts: List[Dict[str, Any]] = []

    for target in page.get("source_targets", []):
        source_files.append({"path": target, "reason": "listed in page source_targets"})
        source_path = root / target
        if not source_path.exists() or not source_path.is_file():
            constraints.append(f"Source target not readable: {target}")
            continue
        try:
            excerpt = _excerpt(source_path, max_excerpt_chars)
        except OSError:
            constraints.append(f"Source target not readable: {target}")
            continue
        source_excerpts.append({"path": target, **excerpt})

    context = {
        "page_id": page_id,
        "objective": page.get("purpose", ""),
        "source_files": source_files,
        "source_excerpts": source_excerpts,
        "related_pages": _related_pages(plan, page_id, page),
        "claims_to_cover": [page.get("purpose", "")] if page.get("purpose") else [],
        "must_link_symbols": [],
        "constraints": constraints,
    }

    if save_to_cache:
        output_dir = root / ".deepwiki" / "cache" / "page-context"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{_safe_page_id(page_id)}.json"
        output_path.write_text(
            json.dumps(context, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return context


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build DeepWiki page context")
    parser.add_argument("project_path")
    parser.add_argument("page_id")
    parser.add_argument("--max-excerpt-chars", type=int, default=12000)
    args = parser.parse_args(argv)

    context = build_page_context(
        Path(args.project_path),
        args.page_id,
        max_excerpt_chars=args.max_excerpt_chars,
        save_to_cache=True,
    )
    output_path = Path(args.project_path) / ".deepwiki" / "cache" / "page-context" / f"{_safe_page_id(context['page_id'])}.json"
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
