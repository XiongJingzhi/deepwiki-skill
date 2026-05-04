"""Tests for packaging metadata used by agent runtime helpers."""

import tomllib
from pathlib import Path


def _pyproject() -> dict:
    return tomllib.loads((Path(__file__).parent.parent / "pyproject.toml").read_text())


def test_pyproject_installs_scripts_package():
    """Editable installs should make the helper modules importable outside the repo."""
    data = _pyproject()

    package_find = data["tool"]["setuptools"]["packages"]["find"]

    assert "scripts*" in package_find["include"]


def test_pyproject_exposes_deepwiki_console_script():
    """Agents should have one stable command entrypoint after pip install -e ."""
    data = _pyproject()

    assert data["project"]["scripts"]["deepwiki"] == "scripts.cli:main"
