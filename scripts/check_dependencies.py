#!/usr/bin/env python3
"""检查 DeepWiki skill 运行依赖。"""

from typing import Dict, List


REQUIRED_IMPORTS = [
    "tree_sitter",
    "tree_sitter_python",
    "tree_sitter_javascript",
    "tree_sitter_typescript",
    "tree_sitter_go",
    "tree_sitter_rust",
    "tree_sitter_java",
    "tree_sitter_kotlin",
    "yaml",
]


def check_dependencies() -> Dict[str, List[str] | bool]:
    missing: List[str] = []
    available: List[str] = []
    for module_name in REQUIRED_IMPORTS:
        try:
            __import__(module_name)
            available.append(module_name)
        except Exception:
            missing.append(module_name)
    return {
        "ok": not missing,
        "available": available,
        "missing": missing,
    }


def main() -> int:
    result = check_dependencies()
    if result["ok"]:
        print("All DeepWiki runtime dependencies are available.")
        return 0

    print("Missing DeepWiki runtime dependencies:")
    for module_name in result["missing"]:
        print(f"  - {module_name}")
    print("\nInstall with: python3 -m pip install -e '.[dev]'")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
