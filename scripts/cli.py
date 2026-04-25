#!/usr/bin/env python3
"""统一封装 DeepWiki skill 的本地工具入口。"""

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from analyze_project import analyze_project
from build_evidence_index import build_evidence_index
from check_analysis_quality import (
    check_analysis_quality,
    load_module_analysis,
    print_report,
)
from check_doc_quality import check_wiki_quality
from detect_changes import detect_changes, print_changes
from extract_structure import run_extract_structure
from init_wiki import init_deep_wiki
from plan_doc_topology import plan_doc_topology
from validate_skill import validate_skill


def _deepwiki_path(path: str) -> Path:
    target = Path(path)
    return target if target.name == ".deepwiki" else target / ".deepwiki"


def _module_map(module_analysis: Dict[str, Any]) -> Dict[str, Any]:
    modules = module_analysis.get("modules")
    return modules if isinstance(modules, dict) else module_analysis


def validate_analysis(project_path: Path, verbose: bool = False) -> int:
    """Run the analysis quality gate and build the evidence index on success."""
    module_analysis = load_module_analysis(project_path)
    if module_analysis is None:
        return 2
    if not isinstance(module_analysis, dict):
        print("module-analysis.json root must be an object")
        return 2

    modules = _module_map(module_analysis)
    if not modules:
        print("module-analysis.json is empty; skipping analysis validation")
        return 0

    all_errors, all_warnings, failed_modules = check_analysis_quality(
        modules, verbose=verbose
    )
    print_report(all_errors, all_warnings, failed_modules, verbose, len(modules))
    if failed_modules:
        return 1

    result = build_evidence_index(project_path)
    print(f"Built evidence index with {len(result['claims'])} claims")
    return 0


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

    p_detect = subparsers.add_parser("detect-changes", help="Detect changed source files")
    p_detect.add_argument("project_path")

    p_plan = subparsers.add_parser("plan-doc-topology", help="Plan document topology")
    p_plan.add_argument("project_path")

    p_validate = subparsers.add_parser(
        "validate-analysis",
        help="Validate analysis and build evidence index",
    )
    p_validate.add_argument("project_path")
    p_validate.add_argument("--verbose", "-v", action="store_true")

    p_evidence = subparsers.add_parser("build-evidence-index", help="Build source evidence index")
    p_evidence.add_argument("project_path")

    p_quality = subparsers.add_parser("quality", help="Check generated wiki quality")
    p_quality.add_argument("path")

    p_self_check = subparsers.add_parser("self-check", help="Validate skill package")
    p_self_check.add_argument("skill_dir", nargs="?", default=str(Path(__file__).parent.parent))

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

    if args.command == "detect-changes":
        print_changes(detect_changes(args.project_path))
        return 0

    if args.command == "plan-doc-topology":
        plan_doc_topology(Path(args.project_path))
        return 0

    if args.command == "validate-analysis":
        return validate_analysis(Path(args.project_path), verbose=args.verbose)

    if args.command == "build-evidence-index":
        result = build_evidence_index(Path(args.project_path))
        print(f"Built evidence index with {len(result['claims'])} claims")
        return 0

    if args.command == "quality":
        check_wiki_quality(str(_deepwiki_path(args.path)))
        return 0

    if args.command == "self-check":
        result = validate_skill(Path(args.skill_dir))
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
