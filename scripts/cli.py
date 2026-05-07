#!/usr/bin/env python3
"""DeepWiki agentic helper CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from scripts.pipeline.prepare_inventory import prepare_inventory
from scripts.pipeline.page_context import build_page_context
from scripts.pipeline.validate_page_plan import validate_page_plan
from scripts.quality.doc_quality import check_doc_quality
from scripts.quality.validate_skill import validate_skill
from scripts.serve.server import serve_wiki
from scripts.wiki.finalize import finalize_wiki
from scripts.wiki.generate_menu import generate_menu
from scripts.wiki.init_wiki import init_wiki
from scripts.wiki.mermaid import process_mermaid


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="DeepWiki agentic helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    p_init = subparsers.add_parser("init", help="Initialize .deepwiki")
    p_init.add_argument("project_path")
    p_init.add_argument("--force", action="store_true")
    p_inventory = subparsers.add_parser(
        "prepare-inventory",
        help="Prepare lightweight project inventory",
    )
    p_inventory.add_argument("project_path")
    p_validate_plan = subparsers.add_parser(
        "validate-page-plan",
        help="Validate .deepwiki/cache/page-plan.json",
    )
    p_validate_plan.add_argument("project_path")
    p_page_context = subparsers.add_parser(
        "page-context",
        help="Build context for one planned page",
    )
    p_page_context.add_argument("project_path")
    p_page_context.add_argument("page_id")
    p_page_context.add_argument("--max-excerpt-chars", type=int, default=12000)
    p_generate_menu = subparsers.add_parser("generate-menu", help="Generate menu.json and doc-map.md")
    p_generate_menu.add_argument("project_path")
    p_generate_menu.add_argument("--project-name")
    p_mermaid = subparsers.add_parser("mermaid", help="Repair and optionally validate Mermaid diagrams")
    p_mermaid.add_argument("project_path")
    p_mermaid.add_argument("--dry-run", action="store_true")
    p_mermaid.add_argument("--validate", action="store_true")
    p_quality = subparsers.add_parser("quality", help="Check generated Markdown quality")
    p_quality.add_argument("project_path")
    p_finalize = subparsers.add_parser("finalize", help="Run final wiki checks")
    p_finalize.add_argument("project_path")
    p_serve = subparsers.add_parser("serve", help="Serve generated wiki")
    p_serve.add_argument("project_path")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8742)
    subparsers.add_parser("self-check", help="Validate the clean skill package")

    args = parser.parse_args(argv)
    if args.command == "init":
        result = init_wiki(Path(args.project_path), force=args.force)
        print(result["message"])
        return 0 if result["success"] else 1
    if args.command == "prepare-inventory":
        result = prepare_inventory(Path(args.project_path), save_to_cache=True)
        print(f"Prepared inventory with {result['stats']['total_files']} files")
        return 0
    if args.command == "validate-page-plan":
        path = Path(args.project_path) / ".deepwiki" / "cache" / "page-plan.json"
        import json

        result = validate_page_plan(json.loads(path.read_text(encoding="utf-8")))
        if result["ok"]:
            print("Page plan is valid.")
            return 0
        print("Page plan is invalid:")
        for error in result["errors"]:
            print(f"  - {error}")
        return 1
    if args.command == "page-context":
        context = build_page_context(
            Path(args.project_path),
            args.page_id,
            max_excerpt_chars=args.max_excerpt_chars,
            save_to_cache=True,
        )
        safe_id = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in context["page_id"]).strip("_") or "page"
        print(Path(args.project_path) / ".deepwiki" / "cache" / "page-context" / f"{safe_id}.json")
        return 0
    if args.command == "generate-menu":
        generate_menu(Path(args.project_path), project_name=args.project_name)
        print("Generated menu.json and doc-map.md")
        return 0
    if args.command == "mermaid":
        import json

        report = process_mermaid(Path(args.project_path), dry_run=args.dry_run, validate=args.validate)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report["validation_errors"] else 0
    if args.command == "quality":
        import json

        report = check_doc_quality(Path(args.project_path))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1
    if args.command == "finalize":
        return finalize_wiki(Path(args.project_path))
    if args.command == "serve":
        serve_wiki(Path(args.project_path), host=args.host, port=args.port)
        return 0
    if args.command == "self-check":
        result = validate_skill(Path("."))
        if result["ok"]:
            print("DeepWiki skill self-check passed.")
            return 0
        print("DeepWiki skill self-check failed:")
        for error in result["errors"]:
            print(f"  - {error}")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
