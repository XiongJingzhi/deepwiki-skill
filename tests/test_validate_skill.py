"""Tests for DeepWiki skill package validation."""

import subprocess
import sys
from pathlib import Path



def _write_minimal_skill(root: Path, cli_text: str) -> None:
    """Create just enough files for validate_skill to focus on CLI behavior."""
    (root / "agents").mkdir()
    (root / "scripts").mkdir()
    (root / "references" / "rules").mkdir(parents=True)
    (root / "references" / "workflow").mkdir(parents=True)

    (root / "SKILL.md").write_text(
        "---\nname: deepwiki\ndescription: test skill\n---\n# DeepWiki\n",
        encoding="utf-8",
    )
    (root / "agents" / "openai.yaml").write_text(
        "interface:\n"
        '  display_name: "DeepWiki"\n'
        '  default_prompt: "Use $deepwiki to generate docs."\n',
        encoding="utf-8",
    )
    for rel_path in [
        "README.md",
        "scripts/check_dependencies.py",
        "scripts/validate_skill.py",
        "references/system-reference.md",
        "references/rules/codepurpose-detection.md",
        "references/workflow/validate-analysis.md",
        "references/workflow/build-evidence-index.md",
    ]:
        (root / rel_path).write_text("placeholder\n", encoding="utf-8")
    (root / "scripts" / "cli.py").write_text(cli_text, encoding="utf-8")


def test_validate_skill_reports_current_package_ready():
    """The repository should expose a deterministic skill integrity check."""
    from scripts.quality.validate_skill import validate_skill

    result = validate_skill(Path(__file__).parent.parent)

    assert result["ok"]
    assert result["errors"] == []
    assert "SKILL.md" in result["checked"]
    assert "scripts/cli.py" in result["checked"]
    assert "agents/openai.yaml" in result["checked"]


def test_cli_self_check_command_runs():
    """Unified CLI should expose the package self-check."""
    from scripts import cli

    assert cli.main(["self-check", str(Path(__file__).parent.parent)]) == 0


def test_legacy_script_wrappers_run_from_skill_root():
    """Old documented script paths should still work when run directly."""
    root = Path(__file__).parent.parent

    for script, args in [
        ("scripts/check_dependencies.py", []),
        ("scripts/validate_skill.py", [str(root)]),
    ]:
        result = subprocess.run(
            [sys.executable, script, *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr


def test_validate_skill_checks_cli_help_not_just_source_text(tmp_path):
    """CLI validation should verify commands exposed by argparse help."""
    from scripts.quality.validate_skill import validate_skill

    command_names = (
        "init analyze extract-structure detect-changes plan-doc-topology "
        "validate-analysis build-evidence-index quality finalize serve self-check"
    )
    _write_minimal_skill(
        tmp_path,
        f"""#!/usr/bin/env python3
# These names in comments should not satisfy validation: {command_names}
import argparse

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")
subparsers.add_parser("init")
parser.parse_args()
""",
    )

    result = validate_skill(tmp_path)

    assert not result["ok"]
    assert any("CLI help is missing command" in error for error in result["errors"])


def test_validate_skill_reports_broken_entrypoint_markdown_links(tmp_path):
    """Entrypoint docs should not point future agents at missing files."""
    from scripts.quality.validate_skill import validate_skill

    commands = [
        "init",
        "analyze",
        "extract-structure",
        "detect-changes",
        "plan-doc-topology",
        "validate-analysis",
        "build-evidence-index",
        "quality",
        "finalize",
        "serve",
        "self-check",
    ]
    parser_lines = "\n".join(f'subparsers.add_parser("{command}")' for command in commands)
    _write_minimal_skill(
        tmp_path,
        f"""#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")
{parser_lines}
parser.parse_args()
""",
    )
    (tmp_path / "SKILL.md").write_text(
        "---\nname: deepwiki\ndescription: test skill\n---\n"
        "# DeepWiki\n[Broken](references/workflow/missing.md)\n",
        encoding="utf-8",
    )

    result = validate_skill(tmp_path)

    assert not result["ok"]
    assert any("Broken markdown link" in error for error in result["errors"])

    result = validate_skill(tmp_path)

    assert not result["ok"]
    assert any("Broken markdown link" in error for error in result["errors"])


def test_validate_skill_requires_openai_metadata(tmp_path):
    """Skill validation should catch missing agent-facing metadata."""
    from scripts.quality.validate_skill import validate_skill

    commands = [
        "init",
        "analyze",
        "extract-structure",
        "detect-changes",
        "plan-doc-topology",
        "validate-analysis",
        "build-evidence-index",
        "quality",
        "finalize",
        "serve",
        "self-check",
    ]
    parser_lines = "\n".join(f'subparsers.add_parser("{command}")' for command in commands)
    _write_minimal_skill(
        tmp_path,
        f"""#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")
{parser_lines}
parser.parse_args()
""",
    )
    (tmp_path / "agents" / "openai.yaml").unlink()

    result = validate_skill(tmp_path)

    assert not result["ok"]
    assert "agents/openai.yaml" in result["checked"]
    assert any("Missing required file: agents/openai.yaml" == error for error in result["errors"])
