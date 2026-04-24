"""Tests for DeepWiki skill package validation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_validate_skill_reports_current_package_ready():
    """The repository should expose a deterministic skill integrity check."""
    from validate_skill import validate_skill

    result = validate_skill(Path(__file__).parent.parent)

    assert result["ok"]
    assert result["errors"] == []
    assert "SKILL.md" in result["checked"]
    assert "agents/openai.yaml" in result["checked"]
    assert "scripts/cli.py" in result["checked"]


def test_cli_self_check_command_runs():
    """Unified CLI should expose the package self-check."""
    import cli

    assert cli.main(["self-check", str(Path(__file__).parent.parent)]) == 0
