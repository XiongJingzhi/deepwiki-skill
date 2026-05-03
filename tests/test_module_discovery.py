"""Tests for scripts/module_discovery.py"""

from pathlib import Path

import pytest

import sys

from scripts.analysis.module_discovery import discover_modules, categorize_module
from scripts.core.importance_scoring import calculate_file_importance
from scripts.core.common import CODE_EXTENSIONS


# =====================================================================
# 6. categorize_module
# =====================================================================


class TestCategorizeModule:
    def test_ui(self):
        for name in ["components", "views", "pages", "screens"]:
            assert categorize_module(name) == "ui"

    def test_api(self):
        for name in ["api", "service", "handler", "middleware", "controller", "router"]:
            assert categorize_module(name) == "api"

    def test_data(self):
        for name in ["migration", "entity", "model", "schema", "repository", "dao"]:
            assert categorize_module(name) == "data"

    def test_utility(self):
        for name in ["utils", "helper", "common", "shared"]:
            assert categorize_module(name) == "utility"

    def test_core(self):
        for name in ["core", "lib", "engine", "kernel"]:
            assert categorize_module(name) == "core"

    def test_config(self):
        for name in ["config", "setting"]:
            assert categorize_module(name) == "config"

    def test_test(self):
        for name in ["test", "spec", "__tests__", "__mocks__"]:
            assert categorize_module(name) == "test"

    def test_module(self):
        assert categorize_module("myfeature") == "module"


# =====================================================================
# 12. discover_modules
# =====================================================================


class TestDiscoverModules:
    def test_discovered_modules_marked_as_candidates(self, fake_project):
        """Discovered modules should carry candidate metadata for later refinement."""
        modules = discover_modules(fake_project)
        assert modules
        for mod in modules:
            assert mod["is_candidate"] is True
            assert mod["discovery_basis"].split(":")[0] in {"directory", "workspace", "fallback-root"}
            assert isinstance(mod["refined_by"], list)

    def test_src_subdirs_discovered(self, tmp_path):
        """src/auth/login.py + src/api/routes.py -> 2 modules"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "auth" / "login.py").parent.mkdir(parents=True, exist_ok=True)
        (src / "auth" / "login.py").write_text("pass\n", encoding="utf-8")
        (src / "api" / "routes.py").parent.mkdir(parents=True, exist_ok=True)
        (src / "api" / "routes.py").write_text("pass\n", encoding="utf-8")

        modules = discover_modules(tmp_path)
        names = {m["name"] for m in modules}
        assert "auth" in names
        assert "api" in names

    def test_application_container_splits_internal_modules_and_dependency_module(self, tmp_path):
        """app/ with entry + internal packages should not collapse into one directory module."""
        (tmp_path / "app" / "main.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "main.py").write_text("from app.modules.graph import workflow\n", encoding="utf-8")
        (tmp_path / "app" / "modules" / "graph" / "workflow.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "modules" / "graph" / "workflow.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "app" / "modules" / "skills" / "base.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "modules" / "skills" / "base.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "app" / "api" / "routes.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "api" / "routes.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "pycommon" / "base_app.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "pycommon" / "base_app.py").write_text("pass\n", encoding="utf-8")

        modules = discover_modules(tmp_path)
        by_path = {m["path"]: m for m in modules}

        assert "app" not in by_path
        assert "app/main.py" in by_path
        assert "app/modules" not in by_path
        assert "app/modules/graph" in by_path
        assert "app/modules/skills" in by_path
        assert "app/api" in by_path
        assert "pycommon" in by_path
        assert all(len(Path(path).parts) <= 3 for path in by_path)
        assert by_path["app/main.py"]["type"] == "core"
        assert by_path["app/main.py"]["discovery_basis"] == "fallback-root:entry"
        assert by_path["app/modules/graph"]["discovery_basis"] == "fallback-root:internal-module"
        assert by_path["app/modules/graph"]["refined_by"] == [
            "application-container",
            "submodule-split",
        ]
        assert by_path["pycommon"]["discovery_basis"] == "fallback-root:dependency-module"

    def test_split_respects_max_depth(self, tmp_path):
        """Submodule splitting should not exceed MAX_MODULE_PATH_DEPTH (8)."""
        (tmp_path / "app" / "main.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "main.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "app" / "modules" / "graph" / "nodes" / "intent.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "modules" / "graph" / "nodes" / "intent.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "app" / "modules" / "graph" / "edges" / "route.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "modules" / "graph" / "edges" / "route.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "app" / "modules" / "skills" / "base.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "modules" / "skills" / "base.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "app" / "api" / "routes.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "api" / "routes.py").write_text("pass\n", encoding="utf-8")

        modules = discover_modules(tmp_path)
        paths = {m["path"] for m in modules}

        # depth=8 allows splitting into graph/nodes and graph/edges
        assert "app/modules/graph/nodes" in paths
        assert "app/modules/graph/edges" in paths
        assert all(len(Path(path).parts) <= 8 for path in paths)

    def test_flat_structure(self, tmp_path):
        """Flat structure with auth/, api/ at root (no src/)"""
        (tmp_path / "auth" / "handler.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "auth" / "handler.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "api" / "router.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "api" / "router.py").write_text("pass\n", encoding="utf-8")

        modules = discover_modules(tmp_path)
        names = {m["name"] for m in modules}
        assert "auth" in names
        assert "api" in names

    def test_flat_skips_tools_dir(self, tmp_path):
        """tools/ dir should be skipped in flat structure (FLAT_ROOT_SKIP)"""
        (tmp_path / "auth" / "main.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "auth" / "main.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "tools" / "script.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "tools" / "script.py").write_text("pass\n", encoding="utf-8")

        modules = discover_modules(tmp_path)
        names = {m["name"] for m in modules}
        assert "auth" in names
        assert "tools" not in names

    def test_empty_code_dir_not_discovered(self, tmp_path):
        """An empty src/ dir (no code files) should not produce modules"""
        (tmp_path / "src").mkdir()
        modules = discover_modules(tmp_path)
        assert modules == []

    def test_all_files_adds_importance_score(self, tmp_path):
        """With all_files param, modules should have importance_score"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "core" / "engine.py").parent.mkdir(parents=True, exist_ok=True)
        (src / "core" / "engine.py").write_text("x" * 2000, encoding="utf-8")
        (src / "utils" / "helper.py").parent.mkdir(parents=True, exist_ok=True)
        (src / "utils" / "helper.py").write_text("pass\n", encoding="utf-8")

        # Build all_files list matching scan_files output format
        all_files = []
        for f in (src / "core").rglob("*"):
            if f.is_file() and f.suffix in CODE_EXTENSIONS:
                size = f.stat().st_size
                imp = calculate_file_importance(f, tmp_path, size)
                all_files.append({
                    "path": str(f.relative_to(tmp_path)).replace("\\", "/"),
                    "importance_score": round(imp, 2),
                    "is_core": imp >= 0.5,
                })
        for f in (src / "utils").rglob("*"):
            if f.is_file() and f.suffix in CODE_EXTENSIONS:
                size = f.stat().st_size
                imp = calculate_file_importance(f, tmp_path, size)
                all_files.append({
                    "path": str(f.relative_to(tmp_path)).replace("\\", "/"),
                    "importance_score": round(imp, 2),
                    "is_core": imp >= 0.5,
                })

        modules = discover_modules(tmp_path, all_files=all_files)
        for mod in modules:
            assert "importance_score" in mod

    def test_modules_sorted_by_importance(self, tmp_path):
        """Modules should be sorted by importance descending"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "core" / "main.py").parent.mkdir(parents=True, exist_ok=True)
        (src / "core" / "main.py").write_text("x" * 2000, encoding="utf-8")
        (src / "docs" / "helper.py").parent.mkdir(parents=True, exist_ok=True)
        (src / "docs" / "helper.py").write_text("pass\n", encoding="utf-8")

        modules = discover_modules(tmp_path)
        if len(modules) > 1:
            scores = [m.get("importance_score", 0) for m in modules]
            assert scores == sorted(scores, reverse=True)
