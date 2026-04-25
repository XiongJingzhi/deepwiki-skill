"""Tests for scripts/project_detection.py"""

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from project_detection import (
    detect_project_types,
    detect_package_manager,
    detect_monorepo_tools,
    detect_project_languages,
    find_entry_points,
)


# =====================================================================
# 2. detect_project_types
# =====================================================================


class TestDetectProjectTypes:
    def test_nodejs(self, tmp_path):
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        types = detect_project_types(tmp_path)
        assert "nodejs" in types

    def test_python(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask>=2.0\n", encoding="utf-8")
        types = detect_project_types(tmp_path)
        assert "python" in types

    def test_go(self, tmp_path):
        (tmp_path / "go.mod").write_text("module example\n", encoding="utf-8")
        types = detect_project_types(tmp_path)
        assert "go" in types

    def test_rust(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text("[package]\nname='test'\n", encoding="utf-8")
        types = detect_project_types(tmp_path)
        assert "rust" in types

    def test_java(self, tmp_path):
        (tmp_path / "pom.xml").write_text("<project></project>", encoding="utf-8")
        types = detect_project_types(tmp_path)
        assert "java" in types

    def test_empty_dir(self, tmp_path):
        types = detect_project_types(tmp_path)
        assert types == []

    def test_fastapi_does_not_match_fastapi_utils(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["fastapi-utils>=0.2"]\n',
            encoding="utf-8",
        )
        types = detect_project_types(tmp_path)
        assert "python" in types
        assert "fastapi" not in types

    def test_fastapi_dependency_matches_exact_name(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["fastapi>=0.100"]\n',
            encoding="utf-8",
        )
        assert "fastapi" in detect_project_types(tmp_path)

    def test_node_react_does_not_match_react_native(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react-native-web": "^0.19"}}\n',
            encoding="utf-8",
        )
        types = detect_project_types(tmp_path)
        assert "react" not in types

    def test_node_react_matches_exact_name(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^18.2", "react-dom": "^18.2"}}\n',
            encoding="utf-8",
        )
        assert "react" in detect_project_types(tmp_path)

    def test_rust_tokio_does_not_match_tokio_stream(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text(
            '[dependencies]\ntokio-stream = "0.1"\n',
            encoding="utf-8",
        )
        types = detect_project_types(tmp_path)
        assert "tokio" not in types

    def test_rust_axum_matches_exact_name(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text(
            '[dependencies]\naxum = "0.7"\n',
            encoding="utf-8",
        )
        assert "axum" in detect_project_types(tmp_path)

    def test_go_gin_does_not_match_gin_contrib(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            "module app\n\ngo 1.21\n\nrequire github.com/gin-contrib/cors v1.5\n",
            encoding="utf-8",
        )
        types = detect_project_types(tmp_path)
        assert "gin" not in types

    def test_go_gin_matches_exact_name(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            "module app\n\ngo 1.21\n\nrequire github.com/gin-gonic/gin v1.9\n",
            encoding="utf-8",
        )
        assert "gin" in detect_project_types(tmp_path)


# =====================================================================
# 3. detect_package_manager
# =====================================================================


class TestDetectPackageManager:
    def test_npm(self, tmp_path):
        (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
        managers = detect_package_manager(tmp_path)
        assert "npm" in managers

    def test_pnpm(self, tmp_path):
        (tmp_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
        managers = detect_package_manager(tmp_path)
        assert "pnpm" in managers

    def test_none(self, tmp_path):
        managers = detect_package_manager(tmp_path)
        assert managers == []


# =====================================================================
# 4. detect_monorepo_tools
# =====================================================================


class TestDetectMonorepoTools:
    def test_pnpm_workspace(self, tmp_path):
        (tmp_path / "pnpm-workspace.yaml").write_text("", encoding="utf-8")
        tools = detect_monorepo_tools(tmp_path)
        assert "monorepo" in tools
        assert "pnpm-workspaces" in tools

    def test_lerna(self, tmp_path):
        (tmp_path / "lerna.json").write_text("{}", encoding="utf-8")
        tools = detect_monorepo_tools(tmp_path)
        assert "monorepo" in tools
        assert "lerna" in tools

    def test_npm_workspaces_in_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text(
            json.dumps({"workspaces": ["packages/*"]}), encoding="utf-8"
        )
        tools = detect_monorepo_tools(tmp_path)
        assert "monorepo" in tools
        assert "npm-workspaces" in tools

    def test_turborepo(self, tmp_path):
        (tmp_path / "turbo.json").write_text("{}", encoding="utf-8")
        tools = detect_monorepo_tools(tmp_path)
        assert "monorepo" in tools
        assert "turborepo" in tools


# =====================================================================
# 5. find_entry_points
# =====================================================================


class TestFindEntryPoints:
    def test_typescript_entry_points(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text("", encoding="utf-8")
        (src / "main.ts").write_text("", encoding="utf-8")
        entries = find_entry_points(tmp_path, ["nodejs"])
        assert "src/index.ts" in entries
        assert "src/main.ts" in entries

    def test_python_entry_points(self, tmp_path):
        (tmp_path / "main.py").write_text("", encoding="utf-8")
        (tmp_path / "app.py").write_text("", encoding="utf-8")
        entries = find_entry_points(tmp_path, ["python"])
        assert "main.py" in entries
        assert "app.py" in entries

    def test_no_entry_points(self, tmp_path):
        entries = find_entry_points(tmp_path, [])
        assert entries == []


# =====================================================================
# 7. detect_project_languages
# =====================================================================


class TestDetectProjectLanguages:
    def test_single_language(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (tmp_path / "utils.py").write_text("pass\n", encoding="utf-8")
        langs = detect_project_languages(tmp_path)
        assert len(langs) >= 1
        assert langs[0] == "Python"

    def test_mixed_sorted_by_count(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        for i in range(5):
            (src / f"f{i}.py").write_text("pass\n", encoding="utf-8")
        for i in range(2):
            (src / f"g{i}.ts").write_text("export {};\n", encoding="utf-8")
        langs = detect_project_languages(tmp_path)
        assert "Python" in langs
        assert "TypeScript" in langs
        # Python has more files, should be first
        assert langs.index("Python") < langs.index("TypeScript")

    def test_empty(self, tmp_path):
        langs = detect_project_languages(tmp_path)
        assert langs == []
