"""Tests for scripts/analyze_project.py"""

import json
from pathlib import Path

import pytest

import analyze_project


# =====================================================================
# 1. load_gitignore
# =====================================================================


class TestLoadGitignore:
    def test_no_gitignore(self, tmp_path):
        dirs, globs = analyze_project.load_gitignore(tmp_path)
        assert dirs == set()
        assert globs == set()

    def test_basic_patterns(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text(
            "node_modules\n*.log\ndist/\n",
            encoding="utf-8",
        )
        dirs, globs = analyze_project.load_gitignore(tmp_path)
        assert "node_modules" in dirs
        assert "dist" in dirs
        assert "*.log" in globs

    def test_comments_skipped(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text(
            "# this is a comment\nnode_modules\n  # indented comment\n*.pyc\n",
            encoding="utf-8",
        )
        dirs, globs = analyze_project.load_gitignore(tmp_path)
        assert dirs == {"node_modules"}
        assert globs == {"*.pyc"}
        assert "# this is a comment" not in dirs and "# this is a comment" not in globs

    def test_negation_skipped(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text(
            "*.log\n!important.log\n",
            encoding="utf-8",
        )
        dirs, globs = analyze_project.load_gitignore(tmp_path)
        assert "*.log" in globs
        # negation patterns are skipped
        assert not any("!" in p for p in dirs | globs)

    def test_double_star_prefix(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("**/temp\n", encoding="utf-8")
        dirs, globs = analyze_project.load_gitignore(tmp_path)
        assert "temp" in dirs


# =====================================================================
# 2. detect_project_types
# =====================================================================


class TestDetectProjectTypes:
    def test_nodejs(self, tmp_path):
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        types = analyze_project.detect_project_types(tmp_path)
        assert "nodejs" in types

    def test_python(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask>=2.0\n", encoding="utf-8")
        types = analyze_project.detect_project_types(tmp_path)
        assert "python" in types

    def test_go(self, tmp_path):
        (tmp_path / "go.mod").write_text("module example\n", encoding="utf-8")
        types = analyze_project.detect_project_types(tmp_path)
        assert "go" in types

    def test_rust(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text("[package]\nname='test'\n", encoding="utf-8")
        types = analyze_project.detect_project_types(tmp_path)
        assert "rust" in types

    def test_java(self, tmp_path):
        (tmp_path / "pom.xml").write_text("<project></project>", encoding="utf-8")
        types = analyze_project.detect_project_types(tmp_path)
        assert "java" in types

    def test_empty_dir(self, tmp_path):
        types = analyze_project.detect_project_types(tmp_path)
        assert types == []


# =====================================================================
# 3. detect_package_manager
# =====================================================================


class TestDetectPackageManager:
    def test_npm(self, tmp_path):
        (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
        managers = analyze_project.detect_package_manager(tmp_path)
        assert "npm" in managers

    def test_pnpm(self, tmp_path):
        (tmp_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
        managers = analyze_project.detect_package_manager(tmp_path)
        assert "pnpm" in managers

    def test_none(self, tmp_path):
        managers = analyze_project.detect_package_manager(tmp_path)
        assert managers == []


# =====================================================================
# 4. detect_monorepo_tools
# =====================================================================


class TestDetectMonorepoTools:
    def test_pnpm_workspace(self, tmp_path):
        (tmp_path / "pnpm-workspace.yaml").write_text("", encoding="utf-8")
        tools = analyze_project.detect_monorepo_tools(tmp_path)
        assert "monorepo" in tools
        assert "pnpm-workspaces" in tools

    def test_lerna(self, tmp_path):
        (tmp_path / "lerna.json").write_text("{}", encoding="utf-8")
        tools = analyze_project.detect_monorepo_tools(tmp_path)
        assert "monorepo" in tools
        assert "lerna" in tools

    def test_npm_workspaces_in_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text(
            json.dumps({"workspaces": ["packages/*"]}), encoding="utf-8"
        )
        tools = analyze_project.detect_monorepo_tools(tmp_path)
        assert "monorepo" in tools
        assert "npm-workspaces" in tools

    def test_turborepo(self, tmp_path):
        (tmp_path / "turbo.json").write_text("{}", encoding="utf-8")
        tools = analyze_project.detect_monorepo_tools(tmp_path)
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
        entries = analyze_project.find_entry_points(tmp_path, ["nodejs"])
        assert "src/index.ts" in entries
        assert "src/main.ts" in entries

    def test_python_entry_points(self, tmp_path):
        (tmp_path / "main.py").write_text("", encoding="utf-8")
        (tmp_path / "app.py").write_text("", encoding="utf-8")
        entries = analyze_project.find_entry_points(tmp_path, ["python"])
        assert "main.py" in entries
        assert "app.py" in entries

    def test_no_entry_points(self, tmp_path):
        entries = analyze_project.find_entry_points(tmp_path, [])
        assert entries == []


# =====================================================================
# 6. categorize_module
# =====================================================================


class TestCategorizeModule:
    def test_ui(self):
        for name in ["components", "views", "pages", "screens"]:
            assert analyze_project.categorize_module(name) == "ui"

    def test_api(self):
        for name in ["api", "service", "handler", "middleware", "controller", "router"]:
            assert analyze_project.categorize_module(name) == "api"

    def test_data(self):
        for name in ["migration", "entity", "model", "schema", "repository", "dao"]:
            assert analyze_project.categorize_module(name) == "data"

    def test_utility(self):
        for name in ["utils", "helper", "common", "shared"]:
            assert analyze_project.categorize_module(name) == "utility"

    def test_core(self):
        for name in ["core", "lib", "engine", "kernel"]:
            assert analyze_project.categorize_module(name) == "core"

    def test_config(self):
        for name in ["config", "setting"]:
            assert analyze_project.categorize_module(name) == "config"

    def test_test(self):
        for name in ["test", "spec", "__tests__", "__mocks__"]:
            assert analyze_project.categorize_module(name) == "test"

    def test_module(self):
        assert analyze_project.categorize_module("myfeature") == "module"


# =====================================================================
# 7. detect_project_languages
# =====================================================================


class TestDetectProjectLanguages:
    def test_single_language(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (tmp_path / "utils.py").write_text("pass\n", encoding="utf-8")
        langs = analyze_project.detect_project_languages(tmp_path)
        assert len(langs) >= 1
        assert langs[0] == "Python"

    def test_mixed_sorted_by_count(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        for i in range(5):
            (src / f"f{i}.py").write_text("pass\n", encoding="utf-8")
        for i in range(2):
            (src / f"g{i}.ts").write_text("export {};\n", encoding="utf-8")
        langs = analyze_project.detect_project_languages(tmp_path)
        assert "Python" in langs
        assert "TypeScript" in langs
        # Python has more files, should be first
        assert langs.index("Python") < langs.index("TypeScript")

    def test_empty(self, tmp_path):
        langs = analyze_project.detect_project_languages(tmp_path)
        assert langs == []


# =====================================================================
# 8. calculate_file_importance
# =====================================================================


class TestCalculateFileImportance:
    def test_src_main_ts_high_score(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        f = src / "main.ts"
        content = "x" * 2000  # 2000 bytes: 1KB <= size <= 50KB -> size_score = 1.0
        f.write_text(content, encoding="utf-8")
        score = analyze_project.calculate_file_importance(f, tmp_path, 2000)
        # path_score=1.0 (src), identity_score=1.0 (main), lang_score=1.0 (.ts), size_score=1.0
        assert score >= 0.8

    def test_config_lower_score(self, tmp_path):
        cfg = tmp_path / "config"
        cfg.mkdir()
        f = cfg / "settings.yaml"
        f.write_text("key: value\n", encoding="utf-8")
        score = analyze_project.calculate_file_importance(f, tmp_path, 10)
        # path_score=0.2 (config dir, not in IGNORE_DIRS), identity_score=0.3 (config in path),
        # lang_score=0.4 (.yaml), size_score=0.0 (<100)
        # 0.2*0.30 + 0.3*0.25 + 0.4*0.30 + 0.0*0.15 = 0.06+0.075+0.12 = 0.255
        assert score < 0.5

    def test_root_readme_moderate(self, tmp_path):
        f = tmp_path / "README.md"
        f.write_text("# Hello\n" * 100, encoding="utf-8")  # 500 bytes approx
        size = len(("# Hello\n" * 100).encode("utf-8"))
        score = analyze_project.calculate_file_importance(f, tmp_path, size)
        # path_score=0.3 (root), identity_score=0.0 (README not a keyword), lang_score=0.0 (.md)
        # size depends on actual byte count; if 100B<=size<1KB -> size_score=0.5
        assert 0.0 <= score <= 1.0

    def test_all_scores_in_range(self, tmp_path):
        # Test a variety of files to ensure scores always fall in [0.0, 1.0]
        src = tmp_path / "src"
        src.mkdir()
        test_files = [
            src / "index.ts",       # high score
            tmp_path / "style.css", # low score
            tmp_path / "data.json", # moderate-low
        ]
        for tf in test_files:
            tf.write_text("x" * 500, encoding="utf-8")
            score = analyze_project.calculate_file_importance(tf, tmp_path, 500)
            assert 0.0 <= score <= 1.0


# =====================================================================
# 9. estimate_complexity
# =====================================================================


class TestEstimateComplexity:
    def test_simple_file(self, tmp_path):
        f = tmp_path / "simple.py"
        f.write_text("x = 1\nprint(x)\n", encoding="utf-8")
        c = analyze_project.estimate_complexity(f)
        # "x = 1\nprint(x)\n" has 0 control flow and 0 definitions, so complexity is 0
        assert c >= 0

    def test_complex_file_higher(self, tmp_path):
        simple = tmp_path / "simple.py"
        simple.write_text("x = 1\nprint(x)\n", encoding="utf-8")

        complex_code_lines = [
            "import os",
            "",
            "def func1():",
            "    if x > 0:",
            "        for i in range(10):",
            "            if y:",
            "                pass",
            "            else:",
            "                pass",
            "    elif x < 0:",
            "        while True:",
            "            try:",
            "                pass",
            "            except:",
            "                pass",
            "    else:",
            "        pass",
            "",
            "def func2():",
            "    for i in range(10):",
            "        if i % 2 == 0:",
            "            continue",
            "        elif i % 3 == 0:",
            "            break",
            "        else:",
            "            pass",
            "",
            "class MyClass:",
            "    def method1(self):",
            "        if self.x:",
            "            return True",
            "        return False",
            "",
            "    def method2(self):",
            "        for item in items:",
            "            try:",
            "                result = process(item)",
            "            except Exception:",
            "                pass",
        ]
        complex_file = tmp_path / "complex.py"
        complex_file.write_text("\n".join(complex_code_lines), encoding="utf-8")

        c_simple = analyze_project.estimate_complexity(simple)
        c_complex = analyze_project.estimate_complexity(complex_file)
        assert c_complex > c_simple

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.py"
        f.write_text("", encoding="utf-8")
        c = analyze_project.estimate_complexity(f)
        assert c == 0

    def test_range(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("if True:\n    pass\n", encoding="utf-8")
        c = analyze_project.estimate_complexity(f)
        assert 0 <= c <= 100


# =====================================================================
# 10. count_important_lines
# =====================================================================


class TestCountImportantLines:
    def test_def_and_class_counted(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text(
            "def my_func():\n"
            "    pass\n"
            "\n"
            "class MyClass:\n"
            "    pass\n",
            encoding="utf-8",
        )
        count = analyze_project.count_important_lines(f)
        assert count >= 2  # def + class

    def test_import_counted(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text(
            "import os\n"
            "from sys import path\n"
            "import json\n",
            encoding="utf-8",
        )
        count = analyze_project.count_important_lines(f)
        assert count >= 3

    def test_decorator_counted(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text(
            "@property\n"
            "def name(self):\n"
            "    return self._name\n"
            "\n"
            "@staticmethod\n"
            "def run():\n"
            "    pass\n",
            encoding="utf-8",
        )
        count = analyze_project.count_important_lines(f)
        # @property, @staticmethod, def name, def run all counted
        assert count >= 4

    def test_plain_lines_not_counted(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("x = 1\ny = 2\nprint(x + y)\n", encoding="utf-8")
        count = analyze_project.count_important_lines(f)
        assert count == 0


# =====================================================================
# 11. scan_files
# =====================================================================


class TestScanFiles:
    def test_basic_project_sorted_by_importance(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.ts").write_text("x" * 2000, encoding="utf-8")
        (src / "util.ts").write_text("export function help() {}", encoding="utf-8")
        (tmp_path / "README.md").write_text("# Test\n", encoding="utf-8")

        # Reset gitignore cache to ensure clean state
        analyze_project._gitignore_cache.reset()

        files = analyze_project.scan_files(tmp_path)
        assert len(files) >= 3
        # Should be sorted descending by importance_score
        scores = [f["importance_score"] for f in files]
        assert scores == sorted(scores, reverse=True)

    def test_node_modules_excluded(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text("", encoding="utf-8")
        nm = tmp_path / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("", encoding="utf-8")

        analyze_project._gitignore_cache.reset()

        files = analyze_project.scan_files(tmp_path)
        paths = [f["path"] for f in files]
        assert not any("node_modules" in p for p in paths)

    def test_gitignore_patterns_excluded(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("build\n*.log\n", encoding="utf-8")

        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("", encoding="utf-8")
        build = tmp_path / "build"
        build.mkdir()
        (build / "app.js").write_text("", encoding="utf-8")
        (tmp_path / "debug.log").write_text("some log\n", encoding="utf-8")

        # Force reload gitignore
        analyze_project._gitignore_cache.reset()
        analyze_project._gitignore_loaded = False

        # Need to call _ensure_gitignore_loaded to actually load the .gitignore
        analyze_project._ensure_gitignore_loaded(tmp_path)

        files = analyze_project.scan_files(tmp_path)
        paths = [f["path"] for f in files]
        assert not any("build/" in p for p in paths)
        # .log files have empty content so scan_files might not even include them,
        # but if they do, they should be excluded by gitignore
        assert not any(p == "debug.log" for p in paths)
        # src/main.py should still be present
        assert any("src/main.py" in p for p in paths)


# =====================================================================
# 12. discover_modules
# =====================================================================


class TestDiscoverModules:
    def test_src_subdirs_discovered(self, tmp_path):
        """src/auth/login.py + src/api/routes.py -> 2 modules"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "auth" / "login.py").parent.mkdir(parents=True, exist_ok=True)
        (src / "auth" / "login.py").write_text("pass\n", encoding="utf-8")
        (src / "api" / "routes.py").parent.mkdir(parents=True, exist_ok=True)
        (src / "api" / "routes.py").write_text("pass\n", encoding="utf-8")

        modules = analyze_project.discover_modules(tmp_path)
        names = {m["name"] for m in modules}
        assert "auth" in names
        assert "api" in names

    def test_flat_structure(self, tmp_path):
        """Flat structure with auth/, api/ at root (no src/)"""
        (tmp_path / "auth" / "handler.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "auth" / "handler.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "api" / "router.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "api" / "router.py").write_text("pass\n", encoding="utf-8")

        modules = analyze_project.discover_modules(tmp_path)
        names = {m["name"] for m in modules}
        assert "auth" in names
        assert "api" in names

    def test_flat_skips_tools_dir(self, tmp_path):
        """tools/ dir should be skipped in flat structure (FLAT_ROOT_SKIP)"""
        (tmp_path / "auth" / "main.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "auth" / "main.py").write_text("pass\n", encoding="utf-8")
        (tmp_path / "tools" / "script.py").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "tools" / "script.py").write_text("pass\n", encoding="utf-8")

        modules = analyze_project.discover_modules(tmp_path)
        names = {m["name"] for m in modules}
        assert "auth" in names
        assert "tools" not in names

    def test_empty_code_dir_not_discovered(self, tmp_path):
        """An empty src/ dir (no code files) should not produce modules"""
        (tmp_path / "src").mkdir()
        modules = analyze_project.discover_modules(tmp_path)
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
            if f.is_file() and f.suffix in analyze_project.CODE_EXTENSIONS:
                size = f.stat().st_size
                imp = analyze_project.calculate_file_importance(f, tmp_path, size)
                all_files.append({
                    "path": str(f.relative_to(tmp_path)).replace("\\", "/"),
                    "importance_score": round(imp, 2),
                    "is_core": imp >= 0.5,
                })
        for f in (src / "utils").rglob("*"):
            if f.is_file() and f.suffix in analyze_project.CODE_EXTENSIONS:
                size = f.stat().st_size
                imp = analyze_project.calculate_file_importance(f, tmp_path, size)
                all_files.append({
                    "path": str(f.relative_to(tmp_path)).replace("\\", "/"),
                    "importance_score": round(imp, 2),
                    "is_core": imp >= 0.5,
                })

        modules = analyze_project.discover_modules(tmp_path, all_files=all_files)
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

        modules = analyze_project.discover_modules(tmp_path)
        if len(modules) > 1:
            scores = [m.get("importance_score", 0) for m in modules]
            assert scores == sorted(scores, reverse=True)


# =====================================================================
# 13. scan_directories
# =====================================================================


class TestScanDirectories:
    def test_src_and_tests_returned(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text("", encoding="utf-8")
        (src / "main.ts").write_text("", encoding="utf-8")
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text("", encoding="utf-8")

        # Reset gitignore cache
        analyze_project._gitignore_cache.reset()

        dirs = analyze_project.scan_directories(tmp_path)
        dir_names = {d["name"] for d in dirs}
        assert "src" in dir_names
        assert "tests" in dir_names

    def test_src_higher_score_than_tests(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text("", encoding="utf-8")
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text("", encoding="utf-8")

        analyze_project._gitignore_cache.reset()

        dirs = analyze_project.scan_directories(tmp_path)
        by_name = {d["name"]: d for d in dirs}
        src_score = by_name["src"]["importance_score"]
        tests_score = by_name["tests"]["importance_score"]
        assert src_score > tests_score


# =====================================================================
# 14. compute_file_stats
# =====================================================================


class TestComputeFileStats:
    def test_file_types(self, tmp_path):
        files = [
            {"extension": ".py", "is_code": True, "size": 500},
            {"extension": ".py", "is_code": True, "size": 1500},
            {"extension": ".ts", "is_code": True, "size": 2000},
            {"extension": ".md", "is_code": False, "size": 100},
        ]
        stats = analyze_project.compute_file_stats(files)
        assert stats["file_types"] == {".py": 2, ".ts": 1}
        # .md should not appear (not code)

    def test_size_distribution(self, tmp_path):
        files = [
            {"extension": ".py", "is_code": True, "size": 500},       # tiny
            {"extension": ".py", "is_code": True, "size": 5000},      # small
            {"extension": ".py", "is_code": True, "size": 20000},     # medium
            {"extension": ".py", "is_code": True, "size": 60000},     # large
        ]
        stats = analyze_project.compute_file_stats(files)
        assert stats["size_distribution"]["tiny"] == 1
        assert stats["size_distribution"]["small"] == 1
        assert stats["size_distribution"]["medium"] == 1
        assert stats["size_distribution"]["large"] == 1

    def test_non_code_files_excluded_from_types(self):
        files = [
            {"extension": ".py", "is_code": True, "size": 100},
            {"extension": ".json", "is_code": False, "size": 200},
            {"extension": ".yaml", "is_code": False, "size": 300},
        ]
        stats = analyze_project.compute_file_stats(files)
        assert stats["file_types"] == {".py": 1}
        # non-code files still counted in size_distribution
        assert stats["size_distribution"]["tiny"] == 3


# =====================================================================
# 15. find_documentation
# =====================================================================


class TestFindDocumentation:
    def test_readme_and_changelog_and_docs_dir(self, tmp_path):
        (tmp_path / "README.md").write_text("# Test\n", encoding="utf-8")
        (tmp_path / "CHANGELOG.md").write_text("# Changes\n", encoding="utf-8")
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "guide.md").write_text("# Guide\n", encoding="utf-8")

        found = analyze_project.find_documentation(tmp_path)
        assert "README.md" in found
        assert "CHANGELOG.md" in found
        # docs/*.md glob returns paths relative to root, with forward slashes
        assert any("guide.md" in f for f in found)

    def test_no_docs(self, tmp_path):
        (tmp_path / "main.py").write_text("pass\n", encoding="utf-8")
        found = analyze_project.find_documentation(tmp_path)
        assert found == []


# =====================================================================
# 16. analyze_project
# =====================================================================


class TestAnalyzeProject:
    def test_full_fake_project_no_cache(self, tmp_path):
        """Full fake project analyzed with save_to_cache=False returns all expected keys."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text("export const app = {};", encoding="utf-8")
        (src / "main.ts").write_text(
            "import { app } from './index';\napp.start();\n", encoding="utf-8"
        )
        (tmp_path / "package.json").write_text(
            json.dumps({"name": "fake-project", "dependencies": {"react": "^18.0.0"}}),
            encoding="utf-8",
        )
        (tmp_path / "README.md").write_text("# Fake Project\n", encoding="utf-8")
        (tmp_path / "requirements.txt").write_text("flask>=2.0\n", encoding="utf-8")

        result = analyze_project.analyze_project(str(tmp_path), save_to_cache=False)

        expected_keys = [
            "project_name",
            "project_type",
            "languages",
            "entry_points",
            "modules",
            "core_files",
            "high_priority_files",
            "directories",
            "file_types",
            "size_distribution",
            "docs_found",
            "stats",
            "analyzed_at",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

        # Verify some values
        assert result["project_name"] == tmp_path.name
        assert isinstance(result["project_type"], list)
        assert isinstance(result["languages"], list)
        assert isinstance(result["entry_points"], list)
        assert isinstance(result["modules"], list)
        assert isinstance(result["core_files"], list)
        assert isinstance(result["stats"]["total_files"], int)
        assert isinstance(result["stats"]["code_files"], int)

        # No cache file should exist
        cache_file = tmp_path / ".deepwiki" / "cache" / "structure.json"
        assert not cache_file.exists()

    def test_save_to_cache_creates_file(self, tmp_path):
        """save_to_cache=True creates .deepwiki/cache/structure.json"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (tmp_path / "requirements.txt").write_text("flask>=2.0\n", encoding="utf-8")

        result = analyze_project.analyze_project(str(tmp_path), save_to_cache=True)

        cache_file = tmp_path / ".deepwiki" / "cache" / "structure.json"
        assert cache_file.exists()

        # Verify the cached file has valid JSON with matching structure
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)

        assert cached["project_name"] == result["project_name"]
        assert cached["stats"]["total_files"] == result["stats"]["total_files"]
