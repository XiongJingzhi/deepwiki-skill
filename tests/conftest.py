"""Shared fixtures for deepwiki-skill tests."""

import sys
import json
from pathlib import Path

# Add scripts/ to sys.path so tests can import scripts directly
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
import common


@pytest.fixture(autouse=True)
def reset_gitignore_cache():
    """Reset GitignoreCache singleton between tests.

    GitignoreCache uses a class-level singleton pattern, so we reset
    the class itself rather than module-level attributes.
    """
    from common import GitignoreCache
    if GitignoreCache._instance is not None:
        GitignoreCache._instance.reset()

    yield


@pytest.fixture
def fake_project(tmp_path):
    """Create a minimal fake project with src/, package.json."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "index.ts").write_text("export const app = {};", encoding="utf-8")
    (src / "main.ts").write_text("import { app } from './index';\napp.start();", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "fake-project", "dependencies": {"react": "^18.0.0"}}),
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Fake Project\n\nA test project.", encoding="utf-8")
    return tmp_path


@pytest.fixture
def fake_python_project(tmp_path):
    """Create a minimal fake Python project."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "__init__.py").write_text("", encoding="utf-8")
    (src / "main.py").write_text(
        '"""Main module."""\n\ndef main():\n    print("hello")\n', encoding="utf-8"
    )
    (src / "utils.py").write_text(
        '"""Utility functions."""\n\ndef helper():\n    pass\n', encoding="utf-8"
    )
    (tmp_path / "main.py").write_text(
        '"""Entry point."""\n\ndef run():\n    pass\n', encoding="utf-8"
    )
    (tmp_path / "requirements.txt").write_text("flask>=2.0\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fake-py"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("# Fake Py Project", encoding="utf-8")
    return tmp_path


@pytest.fixture
def fake_wiki(tmp_path):
    """Create a .deepwiki directory with wiki structure."""
    deepwiki = tmp_path / ".deepwiki"
    cache = deepwiki / "cache"
    wiki = deepwiki / "wiki"
    modules = wiki / "modules"
    api = wiki / "api"

    for d in [cache, wiki, modules, api]:
        d.mkdir(parents=True)

    # config.yaml
    (deepwiki / "config.yaml").write_text(
        "generation:\n  language: zh\nexclude:\n  - .git\n  - node_modules\n",
        encoding="utf-8",
    )

    # meta.json
    (deepwiki / "meta.json").write_text(
        json.dumps({"version": "2.0.0", "modules": {}}), encoding="utf-8"
    )

    # structure.json
    (cache / "structure.json").write_text(
        json.dumps(
            {
                "project_name": "test",
                "modules": [
                    {"name": "core", "path": "src/core", "importance_score": 0.7},
                    {"name": "utils", "path": "src/utils", "importance_score": 0.3},
                ],
            }
        ),
        encoding="utf-8",
    )

    # checksums.json
    (cache / "checksums.json").write_text(json.dumps({}), encoding="utf-8")

    # progress.json
    (cache / "progress.json").write_text(
        json.dumps({"last_updated": None, "phases": {}}), encoding="utf-8"
    )

    # Sample wiki files
    (wiki / "index.md").write_text("# Test Project\n\nOverview.", encoding="utf-8")
    (wiki / "architecture.md").write_text("# Architecture\n\nSystem design.", encoding="utf-8")
    (modules / "core.md").write_text("# Core Module\n\nCore functionality.", encoding="utf-8")

    return tmp_path


@pytest.fixture
def write_file():
    """Helper to write content to a file path."""

    def _write(path, content):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    return _write
