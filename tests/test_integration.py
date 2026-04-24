"""Integration test: deterministic pipeline on a small Python project.

Tests the init → analyze → extract_structure → detect_changes pipeline
without AI involvement (steps 1-3, 2.5).
"""

import json
import sys
from pathlib import Path

# Ensure scripts/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest


class TestPipelineIntegration:
    """Smoke tests for the full deterministic pipeline."""

    def test_init_creates_directory(self, fake_python_project):
        """Step 1: init_deep_wiki creates .deepwiki/ structure."""
        from init_wiki import init_deep_wiki

        result = init_deep_wiki(str(fake_python_project))
        assert result["success"]
        assert (fake_python_project / ".deepwiki").exists()
        assert (fake_python_project / ".deepwiki" / "cache").exists()
        assert (fake_python_project / ".deepwiki" / "wiki").exists()
        assert (fake_python_project / ".deepwiki" / "config.yaml").exists()
        assert (fake_python_project / ".deepwiki" / "meta.json").exists()

    def test_analyze_detects_project(self, fake_python_project):
        """Step 2: analyze_project detects Python project with modules."""
        from analyze_project import analyze_project

        result = analyze_project(str(fake_python_project), save_to_cache=True)
        assert result["project_name"] == fake_python_project.name
        assert "python" in result["project_type"]
        assert result["languages"]
        assert result["stats"]["code_files"] >= 2
        assert (fake_python_project / ".deepwiki" / "cache" / "structure.json").exists()

    def test_extract_structure(self, fake_python_project):
        """Step 2.5: extract_structure produces code-structure.json."""
        from analyze_project import analyze_project
        from extract_structure import run_extract_structure

        # Requires structure.json to exist first
        analyze_project(str(fake_python_project), save_to_cache=True)
        result = run_extract_structure(fake_python_project)
        assert "archetype" in result
        assert "call_graph" in result
        assert "patterns" in result
        assert (fake_python_project / ".deepwiki" / "cache" / "code-structure.json").exists()

    def test_detect_changes_first_run(self, fake_python_project):
        """Step 3: detect_changes identifies all files as new on first run."""
        from detect_changes import detect_changes

        result = detect_changes(str(fake_python_project))
        assert result["has_changes"]
        assert len(result["added"]) > 0
        assert len(result["modified"]) == 0
        assert len(result["deleted"]) == 0

    def test_detect_changes_no_changes(self, fake_python_project):
        """Step 3: detect_changes finds no changes on second run."""
        from detect_changes import detect_changes

        # First run to save checksums
        detect_changes(str(fake_python_project))
        # Second run should show no changes
        result = detect_changes(str(fake_python_project))
        assert not result["has_changes"]
        assert len(result["added"]) == 0

    def test_full_pipeline(self, fake_python_project):
        """End-to-end: run all deterministic steps in sequence."""
        from init_wiki import init_deep_wiki
        from analyze_project import analyze_project
        from extract_structure import run_extract_structure

        # Step 1
        init_deep_wiki(str(fake_python_project))
        assert (fake_python_project / ".deepwiki").exists()

        # Step 2
        result = analyze_project(str(fake_python_project))
        assert result["project_name"] == fake_python_project.name

        # Step 2.5
        result = run_extract_structure(fake_python_project)
        assert "archetype" in result

        # Verify cache files exist
        cache = fake_python_project / ".deepwiki" / "cache"
        assert (cache / "structure.json").exists()
        assert (cache / "code-structure.json").exists()
        # import-relations data is now embedded in code-structure.json (no separate file)
        assert "import_relations" in json.loads((cache / "code-structure.json").read_text())
        assert (cache / "checksums.json").exists()
        assert (cache / "progress.json").exists()

    def test_cli_smoke_flow(self, fake_python_project):
        """Unified CLI wraps deterministic workflow commands."""
        import cli

        assert cli.main(["init", str(fake_python_project)]) == 0
        assert cli.main(["analyze", str(fake_python_project)]) == 0
        assert cli.main(["extract-structure", str(fake_python_project)]) == 0
        assert cli.main(["detect-changes", str(fake_python_project)]) == 0
        assert cli.main(["plan-doc-topology", str(fake_python_project)]) == 0

        from common import CACHE_SCHEMA_VERSION

        module_analysis = {
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "modules": {
                "app": {
                    "module_summary": "Application entry module",
                    "module_role": "Coordinates startup",
                    "files": [{"path": "app.py"}],
                }
            },
        }
        (fake_python_project / ".deepwiki" / "cache" / "module-analysis.json").write_text(
            json.dumps(module_analysis),
            encoding="utf-8",
        )
        assert cli.main(["build-evidence-index", str(fake_python_project)]) == 0
        assert cli.main(["quality", str(fake_python_project / ".deepwiki")]) == 0

        cache = fake_python_project / ".deepwiki" / "cache"
        assert (cache / "doc-topology.json").exists()
        assert (cache / "generation-plan.json").exists()
        assert (cache / "evidence-index.json").exists()

    def test_dependency_self_check_module(self):
        """Dependency self-check exposes a programmatic status."""
        import check_dependencies

        result = check_dependencies.check_dependencies()
        assert "ok" in result
        assert "missing" in result
