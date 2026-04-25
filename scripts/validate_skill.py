#!/usr/bin/env python3
"""Validate that this directory is a usable DeepWiki skill package."""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml


REQUIRED_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "README.md",
    "scripts/cli.py",
    "scripts/check_dependencies.py",
    "scripts/validate_skill.py",
    "references/system-reference.md",
    "references/rules/file-role-classification.md",
    "references/workflow/build-evidence-index.md",
]

REQUIRED_CLI_COMMANDS = [
    "init",
    "analyze",
    "extract-structure",
    "detect-changes",
    "plan-doc-topology",
    "build-evidence-index",
    "quality",
    "self-check",
]

ENTRYPOINT_MARKDOWN_FILES = [
    "SKILL.md",
    "README.md",
]


def _frontmatter(text: str) -> Dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data: Dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def _local_markdown_links(text: str) -> List[str]:
    """Extract local markdown links that should resolve inside the skill package."""
    links: List[str] = []
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = match.group(1).strip()
        if (
            not target
            or target.startswith("#")
            or "://" in target
            or target.startswith("mailto:")
            or "{" in target
        ):
            continue
        links.append(target.split("#", 1)[0])
    return links


def validate_skill(skill_dir: Path) -> Dict[str, Any]:
    """Return deterministic validation results for a DeepWiki skill directory."""
    root = Path(skill_dir)
    errors: List[str] = []
    checked: List[str] = []

    for rel_path in REQUIRED_FILES:
        path = root / rel_path
        checked.append(rel_path)
        if not path.exists():
            errors.append(f"Missing required file: {rel_path}")

    skill_path = root / "SKILL.md"
    if skill_path.exists():
        meta = _frontmatter(skill_path.read_text(encoding="utf-8"))
        if meta.get("name") != "deepwiki":
            errors.append("SKILL.md frontmatter must include name: deepwiki")
        if not meta.get("description"):
            errors.append("SKILL.md frontmatter must include description")

    openai_path = root / "agents" / "openai.yaml"
    if openai_path.exists():
        data = yaml.safe_load(openai_path.read_text(encoding="utf-8")) or {}
        interface = data.get("interface", {})
        if not interface.get("display_name"):
            errors.append("agents/openai.yaml must include interface.display_name")
        default_prompt = interface.get("default_prompt", "")
        if "$deepwiki" not in default_prompt:
            errors.append("agents/openai.yaml default_prompt must mention $deepwiki")

    for rel_path in ENTRYPOINT_MARKDOWN_FILES:
        doc_path = root / rel_path
        if not doc_path.exists():
            continue
        for link in _local_markdown_links(doc_path.read_text(encoding="utf-8")):
            target = (doc_path.parent / link).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                errors.append(f"Markdown link escapes skill package: {rel_path} -> {link}")
                continue
            if not target.exists():
                errors.append(f"Broken markdown link: {rel_path} -> {link}")

    cli_path = root / "scripts" / "cli.py"
    if cli_path.exists():
        help_result = subprocess.run(
            [sys.executable, str(cli_path), "--help"],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
        if help_result.returncode != 0:
            errors.append("CLI help command failed")
        help_text = f"{help_result.stdout}\n{help_result.stderr}"
        for command in REQUIRED_CLI_COMMANDS:
            if command not in help_text:
                errors.append(f"CLI help is missing command: {command}")

    if (root / ".git").exists():
        git_result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
        if git_result.returncode == 0:
            tracked_noise = [
                path for path in git_result.stdout.splitlines()
                if "__pycache__" in path or ".pytest_cache" in path or "egg-info" in path
            ]
            if tracked_noise:
                errors.append("Generated artifacts are tracked by Git")

    return {
        "ok": not errors,
        "errors": errors,
        "checked": checked,
    }


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
