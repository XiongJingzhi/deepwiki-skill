"""Generate menu.json and doc-map.md from the agentic page plan."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


TYPE_LABELS = {
    "overview": "Overview",
    "getting-started": "Getting Started",
    "concept": "Concepts",
    "deep-dive": "Deep Dive",
    "reference": "Reference",
    "doc-map": "Doc Map",
    "custom": "More",
}


def _load_plan(project_path: Path) -> Dict[str, Any]:
    return json.loads((project_path / ".deepwiki" / "cache" / "page-plan.json").read_text(encoding="utf-8"))


def _page_map(plan: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        page["page_id"]: page
        for page in plan.get("pages", [])
        if page.get("page_id") and page.get("output_path")
    }


def _item(page: Dict[str, Any]) -> Dict[str, str]:
    return {"title": page.get("title") or page["page_id"], "path": page["output_path"]}


def _items_from_seed(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    pages = _page_map(plan)
    menu: List[Dict[str, Any]] = []
    for section in plan.get("menu_seed", []):
        items = [
            _item(pages[page_id])
            for page_id in section.get("page_ids", [])
            if page_id in pages
        ]
        if items:
            menu.append({"title": section.get("title", "Pages"), "items": items})
    return menu


def _items_by_type(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for page in plan.get("pages", []):
        grouped.setdefault(page.get("page_type", "custom"), []).append(_item(page))
    menu = []
    for page_type, items in grouped.items():
        menu.append({"title": TYPE_LABELS.get(page_type, page_type.title()), "items": items})
    return menu


def _write_doc_map(wiki_dir: Path, menu: Dict[str, Any]) -> None:
    lines = [f"# {menu['title']} Documentation Map", ""]
    for section in menu["items"]:
        lines.append(f"## {section['title']}")
        lines.append("")
        for item in section["items"]:
            lines.append(f"- [{item['title']}]({item['path']})")
        lines.append("")
    (wiki_dir / "doc-map.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def generate_menu(project_path: str | Path, project_name: Optional[str] = None, reconcile: bool = False) -> Dict[str, Any]:
    root = Path(project_path)
    wiki_dir = root / ".deepwiki" / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    plan = _load_plan(root)
    items = _items_from_seed(plan) or _items_by_type(plan)
    menu = {
        "title": project_name or root.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }
    (wiki_dir / "menu.json").write_text(json.dumps(menu, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_doc_map(wiki_dir, menu)
    return menu


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate DeepWiki menu")
    parser.add_argument("project_path")
    parser.add_argument("--project-name")
    parser.add_argument("--reconcile", action="store_true")
    args = parser.parse_args(argv)
    generate_menu(Path(args.project_path), project_name=args.project_name, reconcile=args.reconcile)
    print("Generated menu.json and doc-map.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
