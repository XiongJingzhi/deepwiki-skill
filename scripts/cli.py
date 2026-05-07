#!/usr/bin/env python3
"""DeepWiki agentic helper CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from scripts.pipeline.prepare_inventory import prepare_inventory
from scripts.pipeline.validate_page_plan import validate_page_plan
from scripts.wiki.init_wiki import init_wiki


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
    if args.command == "self-check":
        print("DeepWiki skill self-check passed.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
