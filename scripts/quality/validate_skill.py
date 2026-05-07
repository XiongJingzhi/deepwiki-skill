"""Validate the clean DeepWiki skill package."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Union


REQUIRED_FILES = [
    "SKILL.md",
    "pyproject.toml",
    "scripts/cli.py",
    "schemas/project-inventory-schema.json",
    "schemas/semantic-analysis-schema.json",
    "schemas/page-plan-schema.json",
    "schemas/page-context-schema.json",
    "references/system-reference.md",
    "references/workflow/init-wiki.md",
    "references/workflow/prepare-inventory.md",
    "references/workflow/agentic-analysis.md",
    "references/workflow/plan-pages.md",
    "references/workflow/generate-menu.md",
    "references/workflow/generate-pages.md",
    "references/workflow/finalize-wiki.md",
]


def validate_skill(skill_dir: Union[str, Path]) -> Dict[str, object]:
    root = Path(skill_dir)
    errors: List[str] = []
    for rel_path in REQUIRED_FILES:
        if not (root / rel_path).exists():
            errors.append(f"missing required file: {rel_path}")

    skill_path = root / "SKILL.md"
    if skill_path.exists():
        text = skill_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            errors.append("SKILL.md missing YAML frontmatter")
        if "name: deepwiki" not in text:
            errors.append("SKILL.md missing name: deepwiki")
        if "description:" not in text:
            errors.append("SKILL.md missing description")

    forbidden_dependency_phrases = [
        "requires structure.json",
        "input: structure.json",
        "reads structure.json",
        "requires module-analysis.json",
        "input: module-analysis.json",
        "reads module-analysis.json",
        "requires generation-plan.json",
        "input: generation-plan.json",
        "reads generation-plan.json",
    ]
    for rel_path in ["SKILL.md", "references/system-reference.md"]:
        path = root / rel_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in forbidden_dependency_phrases:
            if phrase in text:
                errors.append(f"{rel_path} declares legacy dependency: {phrase}")

    return {"ok": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DeepWiki skill package")
    parser.add_argument("skill_dir", nargs="?", default=".")
    args = parser.parse_args()
    result = validate_skill(Path(args.skill_dir))
    if result["ok"]:
        print("DeepWiki skill self-check passed.")
        return 0
    print("DeepWiki skill self-check failed:")
    for error in result["errors"]:
        print(f"  - {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
