#!/usr/bin/env python3
"""统一封装 DeepWiki skill 的本地工具入口。"""

import argparse
from pathlib import Path
from typing import List, Optional

from analyze_project import analyze_project
from check_doc_quality import check_wiki_quality
from extract_structure import run_extract_structure
from init_wiki import init_deep_wiki
from plan_doc_topology import plan_doc_topology


def _deepwiki_path(path: str) -> Path:
    target = Path(path)
    return target if target.name == ".deepwiki" else target / ".deepwiki"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="DeepWiki skill helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_init = subparsers.add_parser("init", help="Initialize .deepwiki")
    p_init.add_argument("project_path")
    p_init.add_argument("--force", action="store_true")

    p_analyze = subparsers.add_parser("analyze", help="Analyze project structure")
    p_analyze.add_argument("project_path")

    p_extract = subparsers.add_parser("extract-structure", help="Extract code structure")
    p_extract.add_argument("project_path")

    p_plan = subparsers.add_parser("plan-doc-topology", help="Plan document topology")
    p_plan.add_argument("project_path")

    p_quality = subparsers.add_parser("quality", help="Check generated wiki quality")
    p_quality.add_argument("path")

    args = parser.parse_args(argv)

    if args.command == "init":
        result = init_deep_wiki(args.project_path, force=args.force)
        if not result.get("success"):
            print(result.get("message", "init failed"))
            return 1
        return 0

    if args.command == "analyze":
        analyze_project(args.project_path, save_to_cache=True)
        return 0

    if args.command == "extract-structure":
        run_extract_structure(Path(args.project_path))
        return 0

    if args.command == "plan-doc-topology":
        plan_doc_topology(Path(args.project_path))
        return 0

    if args.command == "quality":
        check_wiki_quality(str(_deepwiki_path(args.path)))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
