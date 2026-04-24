"""Tests for scripts/scanner.py"""

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scanner import scan_files, scan_directories, compute_file_stats, find_documentation
from common import GitignoreCache


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

        gitignore_cache = GitignoreCache()
        files = scan_files(tmp_path, gitignore_cache=gitignore_cache)
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

        gitignore_cache = GitignoreCache()
        files = scan_files(tmp_path, gitignore_cache=gitignore_cache)
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

        # Create a gitignore cache and ensure it's loaded for this project
        from common import GitignoreCache, should_ignore_path, IGNORE_DIRS
        gitignore_cache = GitignoreCache()
        gitignore_cache.ensure_loaded(tmp_path)

        files = scan_files(tmp_path, gitignore_cache=gitignore_cache)
        paths = [f["path"] for f in files]
        assert not any("build/" in p for p in paths)
        # .log files have empty content so scan_files might not even include them,
        # but if they do, they should be excluded by gitignore
        assert not any(p == "debug.log" for p in paths)
        # src/main.py should still be present
        assert any("src/main.py" in p for p in paths)


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

        dirs = scan_directories(tmp_path)
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

        dirs = scan_directories(tmp_path)
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
        stats = compute_file_stats(files)
        assert stats["file_types"] == {".py": 2, ".ts": 1}
        # .md should not appear (not code)

    def test_size_distribution(self, tmp_path):
        files = [
            {"extension": ".py", "is_code": True, "size": 500},       # tiny
            {"extension": ".py", "is_code": True, "size": 5000},      # small
            {"extension": ".py", "is_code": True, "size": 20000},     # medium
            {"extension": ".py", "is_code": True, "size": 60000},     # large
        ]
        stats = compute_file_stats(files)
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
        stats = compute_file_stats(files)
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

        found = find_documentation(tmp_path)
        assert "README.md" in found
        assert "CHANGELOG.md" in found
        # docs/*.md glob returns paths relative to root, with forward slashes
        assert any("guide.md" in f for f in found)

    def test_no_docs(self, tmp_path):
        (tmp_path / "main.py").write_text("pass\n", encoding="utf-8")
        found = find_documentation(tmp_path)
        assert found == []
