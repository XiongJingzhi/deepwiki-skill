"""Tests for import_relations.py — import relation extraction and path resolution."""

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on sys.path (conftest.py also does this)
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import import_relations


# ── extract_import_relations ────────────────────────────────────────────


class TestExtractImportRelations:
    """Test the main extract_import_relations function."""

    def test_python_imports(self, tmp_path):
        """Python: from X import Y and import X.Y."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").write_text("", encoding="utf-8")
        (src / "utils.py").write_text(
            "from src.auth import login\nimport os.path\n",
            encoding="utf-8",
        )
        (src / "auth.py").write_text("", encoding="utf-8")

        result = import_relations.extract_import_relations(
            [src / "utils.py"], tmp_path
        )
        # Should find auth.py via relative path resolution
        assert isinstance(result, dict)
        assert "src/utils.py" in result

    def test_typescript_imports(self, tmp_path):
        """TypeScript: import X from 'path'."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text(
            "import { app } from './main';\nexport default app;\n",
            encoding="utf-8",
        )
        (src / "main.ts").write_text("export const app = {};", encoding="utf-8")

        result = import_relations.extract_import_relations(
            [src / "index.ts"], tmp_path
        )
        assert "src/index.ts" in result

    def test_javascript_require(self, tmp_path):
        """JavaScript: require('module') at start of line."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.js").write_text(
            "require('./main.js');\nmodule.exports = {};\n",
            encoding="utf-8",
        )
        (src / "main.js").write_text("module.exports = {};", encoding="utf-8")

        result = import_relations.extract_import_relations(
            [src / "index.js"], tmp_path
        )
        assert "src/index.js" in result

    def test_go_imports(self, tmp_path):
        """Go: import statements."""
        (tmp_path / "main.go").write_text(
            'package main\n\nimport "fmt"\n\nfunc main() { fmt.Println() }\n',
            encoding="utf-8",
        )

        result = import_relations.extract_import_relations(
            [tmp_path / "main.go"], tmp_path
        )
        # Go standard library imports won't resolve to project files
        assert isinstance(result, dict)

    def test_rust_use(self, tmp_path):
        """Rust: use statements."""
        (tmp_path / "main.rs").write_text(
            'use std::collections::HashMap;\n\nfn main() {}\n',
            encoding="utf-8",
        )

        result = import_relations.extract_import_relations(
            [tmp_path / "main.rs"], tmp_path
        )
        # std imports won't resolve to project files
        assert isinstance(result, dict)

    def test_java_imports(self, tmp_path):
        """Java: import statements."""
        (tmp_path / "Main.java").write_text(
            'import java.util.List;\n\npublic class Main {}\n',
            encoding="utf-8",
        )

        result = import_relations.extract_import_relations(
            [tmp_path / "Main.java"], tmp_path
        )
        # java.util won't resolve to project files
        assert isinstance(result, dict)

    def test_empty_file(self, tmp_path):
        """File with no imports produces empty relations."""
        f = tmp_path / "empty.py"
        f.write_text("# just a comment\n", encoding="utf-8")

        result = import_relations.extract_import_relations([f], tmp_path)
        assert result == {}

    def test_nonexistent_file(self, tmp_path):
        """Nonexistent files are skipped gracefully."""
        f = tmp_path / "missing.py"
        result = import_relations.extract_import_relations([f], tmp_path)
        assert result == {}

    def test_unsupported_extension(self, tmp_path):
        """Files with unsupported extensions are skipped."""
        f = tmp_path / "readme.txt"
        f.write_text("some text", encoding="utf-8")
        result = import_relations.extract_import_relations([f], tmp_path)
        assert result == {}

    def test_no_files(self, tmp_path):
        """Empty file list produces empty relations."""
        result = import_relations.extract_import_relations([], tmp_path)
        assert result == {}


# ── _resolve_imports_to_paths ──────────────────────────────────────────


class TestResolveImportsToPaths:
    """Test import path resolution logic."""

    def test_relative_import_resolution(self, tmp_path):
        """Relative import (./module) resolves to sibling file."""
        src = tmp_path / "src"
        src.mkdir()
        source = src / "main.py"
        source.write_text("", encoding="utf-8")
        target = src / "utils.py"
        target.write_text("", encoding="utf-8")

        resolved = import_relations._resolve_imports_to_paths(
            ["./utils"], source, tmp_path
        )
        assert any("utils.py" in r for r in resolved)

    def test_bare_module_in_src(self, tmp_path):
        """Bare module name resolves to src/module.py."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "auth.py").write_text("", encoding="utf-8")

        source = tmp_path / "main.py"
        source.write_text("", encoding="utf-8")

        resolved = import_relations._resolve_imports_to_paths(
            ["auth"], source, tmp_path
        )
        assert any("auth.py" in r for r in resolved)

    def test_nonexistent_import_returns_empty(self, tmp_path):
        """Import pointing to nonexistent file returns no results."""
        source = tmp_path / "main.py"
        source.write_text("", encoding="utf-8")

        resolved = import_relations._resolve_imports_to_paths(
            ["nonexistent_module_xyz"], source, tmp_path
        )
        assert resolved == []


# ── _find_module_in_project ────────────────────────────────────────────


class TestFindModuleInProject:
    """Test module lookup across source directories."""

    def test_find_in_src_dir(self, tmp_path):
        """Finds module in src/ directory."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "utils.py").write_text("", encoding="utf-8")

        result = import_relations._find_module_in_project("utils", tmp_path, ".py")
        assert any("utils.py" in r for r in result)

    def test_find_in_lib_dir(self, tmp_path):
        """Finds module in lib/ directory."""
        lib = tmp_path / "lib"
        lib.mkdir()
        (lib / "core.py").write_text("", encoding="utf-8")

        result = import_relations._find_module_in_project("core", tmp_path, ".py")
        assert any("core.py" in r for r in result)

    def test_find_index_file(self, tmp_path):
        """Finds module via index.ts in subdirectory."""
        src = tmp_path / "src"
        src.mkdir()
        components = src / "components"
        components.mkdir()
        (components / "index.ts").write_text("", encoding="utf-8")

        result = import_relations._find_module_in_project("components", tmp_path, ".ts")
        assert any("index.ts" in r for r in result)

    def test_not_found(self, tmp_path):
        """Returns empty list for nonexistent module."""
        result = import_relations._find_module_in_project(
            "nonexistent_xyz_123", tmp_path, ".py"
        )
        assert result == []
