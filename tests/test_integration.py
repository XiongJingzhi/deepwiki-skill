"""Integration test: deterministic pipeline on a small Python project.

Tests the init → analyze → extract_structure → detect_changes pipeline
without AI involvement (steps 1-3, 2.5).
"""

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


class TestPipelineIntegration:
    """Smoke tests for the full deterministic pipeline."""

    def test_init_creates_directory(self, fake_python_project):
        """init_deep_wiki creates .deepwiki/ structure."""
        from scripts.wiki.init_wiki import init_deep_wiki

        result = init_deep_wiki(str(fake_python_project))
        assert result["success"]
        assert (fake_python_project / ".deepwiki").exists()
        assert (fake_python_project / ".deepwiki" / "cache").exists()
        assert (fake_python_project / ".deepwiki" / "wiki").exists()
        assert (fake_python_project / ".deepwiki" / "config.yaml").exists()
        assert (fake_python_project / ".deepwiki" / "meta.json").exists()

    def test_analyze_detects_project(self, fake_python_project):
        """analyze_project detects Python project with modules."""
        from scripts.analysis.analyze_project import analyze_project

        result = analyze_project(str(fake_python_project), save_to_cache=True)
        assert result["project_name"] == fake_python_project.name
        assert result["languages"]
        assert (fake_python_project / ".deepwiki" / "cache" / "structure.json").exists()

    def test_extract_structure(self, fake_python_project):
        """extract_structure produces code-structure.json."""
        from scripts.analysis.analyze_project import analyze_project
        from scripts.analysis.extract_structure import run_extract_structure

        # Requires structure.json to exist first
        analyze_project(str(fake_python_project), save_to_cache=True)
        result = run_extract_structure(fake_python_project)
        assert "archetype" in result
        assert "call_graph" in result
        assert (fake_python_project / ".deepwiki" / "cache" / "code-structure.json").exists()

    def test_detect_changes_first_run(self, fake_python_project):
        """detect_changes identifies all files as new on first run."""
        from scripts.pipeline.detect_changes import detect_changes

        result = detect_changes(str(fake_python_project))
        assert result["has_changes"]
        assert len(result["added"]) > 0
        assert len(result["modified"]) == 0
        assert len(result["deleted"]) == 0

    def test_detect_changes_no_changes(self, fake_python_project):
        """detect_changes finds no changes on second run."""
        from scripts.pipeline.detect_changes import detect_changes

        # First run to save checksums
        detect_changes(str(fake_python_project))
        # Second run should show no changes
        result = detect_changes(str(fake_python_project))
        assert not result["has_changes"]
        assert len(result["added"]) == 0

    def test_full_pipeline(self, fake_python_project):
        """End-to-end: run all deterministic steps in sequence."""
        from scripts.wiki.init_wiki import init_deep_wiki
        from scripts.analysis.analyze_project import analyze_project
        from scripts.analysis.extract_structure import run_extract_structure

        init_deep_wiki(str(fake_python_project))
        assert (fake_python_project / ".deepwiki").exists()

        result = analyze_project(str(fake_python_project))
        assert result["project_name"] == fake_python_project.name

        # extract-structure
        result = run_extract_structure(fake_python_project)
        assert "archetype" in result

        # Verify cache files exist
        cache = fake_python_project / ".deepwiki" / "cache"
        state = fake_python_project / ".deepwiki" / "state"
        assert (cache / "structure.json").exists()
        assert (cache / "code-structure.json").exists()
        # import-relations data is now embedded in code-structure.json (no separate file)
        assert "import_relations" in json.loads((cache / "code-structure.json").read_text())
        assert (state / "checksums.json").exists()
        assert (state / "progress.json").exists()

    def test_cli_smoke_flow(self, fake_python_project):
        """Unified CLI wraps deterministic workflow commands."""
        from scripts import cli

        assert cli.main(["init", str(fake_python_project)]) == 0
        assert cli.main(["analyze", str(fake_python_project)]) == 0
        assert cli.main(["extract-structure", str(fake_python_project)]) == 0
        assert cli.main(["detect-changes", str(fake_python_project)]) == 0
        assert cli.main(["plan-doc-topology", str(fake_python_project)]) == 0

        from scripts.core.common import CACHE_SCHEMA_VERSION

        module_analysis = {
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "modules": {
                "app": {
                    "module_path": "app.py",
                    "module_summary": "Application entry module",
                    "semantic_group": "Application",
                    "selected_components": ["overview"],
                    "module_role": "Coordinates startup",
                    "upstream_inputs": ["CLI arguments"],
                    "downstream_outputs": ["Application result"],
                    "risk_points": ["Startup configuration"],
                    "extension_points": ["Add subcommands"],
                    "code_purpose": "Entry",
                    "analysis_depth": "standard",
                    "dependency_hints": {"imports": [], "imported_by": []},
                    "files": [
                        {
                            "path": "app.py",
                            "summary": "Application entrypoint",
                            "public_interfaces": [{"name": "main"}],
                            "key_insights": ["Owns process startup"],
                        }
                    ],
                }
            },
        }
        (fake_python_project / ".deepwiki" / "cache" / "module-analysis.json").write_text(
            json.dumps(module_analysis),
            encoding="utf-8",
        )
        assert cli.main(["validate-analysis", str(fake_python_project)]) == 0
        assert cli.main(["quality", str(fake_python_project / ".deepwiki")]) == 0

        cache = fake_python_project / ".deepwiki" / "cache"
        assert (cache / "doc-topology.json").exists()
        assert (cache / "generation-plan.json").exists()
        assert (cache / "evidence-index.json").exists()

    def test_dependency_self_check_module(self):
        """Dependency self-check exposes a programmatic status."""
        import scripts.quality.check_dependencies as check_dependencies

        result = check_dependencies.check_dependencies()
        assert "ok" in result
        assert "missing" in result

    def test_validate_analysis_stops_before_evidence_when_quality_fails(self, fake_python_project):
        """validate-analysis should not build evidence for failed module analysis."""
        from scripts import cli
        from scripts.core.common import CACHE_SCHEMA_VERSION

        cache = fake_python_project / ".deepwiki" / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "module-analysis.json").write_text(
            json.dumps(
                {
                    "cache_schema_version": CACHE_SCHEMA_VERSION,
                    "modules": {
                        "app": {
                            "module_summary": "Missing required cognitive fields.",
                            "files": [{"path": "app.py", "summary": "Entry"}],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        assert cli.main(["validate-analysis", str(fake_python_project)]) == 1
        assert not (cache / "evidence-index.json").exists()

    def test_validate_analysis_cmd_invalidates_relationship_summary(self, fake_python_project):
        """cli.py validate-analysis 执行后应删除 relationship-summary.json"""
        import subprocess
        from scripts.core.common import CACHE_SCHEMA_VERSION
        from scripts.wiki.init_wiki import init_deep_wiki

        init_deep_wiki(str(fake_python_project))
        cache = fake_python_project / ".deepwiki" / "cache"

        # 预置合法的 module-analysis.json（空模块列表 → 通过门控）
        (cache / "module-analysis.json").write_text(
            json.dumps({"cache_schema_version": CACHE_SCHEMA_VERSION, "modules": {}}),
            encoding="utf-8",
        )

        # 预置旧的 relationship-summary.json
        rel_summary = cache / "relationship-summary.json"
        rel_summary.write_text(json.dumps({"stale": True}), encoding="utf-8")

        # 运行 cli validate-analysis
        result = subprocess.run(
            [sys.executable, "scripts/cli.py", "validate-analysis", str(fake_python_project)],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True,
        )

        # 进入 validate-analysis 即失效缓存（无论是否有模块数据）
        assert not rel_summary.exists(), (
            f"validate-analysis 后 relationship-summary.json 应被删除\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
