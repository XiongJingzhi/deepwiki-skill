"""Tests for scripts/detect_changes.py"""

import json
from pathlib import Path
import common
import detect_changes


# ---------------------------------------------------------------------------
# calculate_file_hash
# ---------------------------------------------------------------------------

class TestCalculateFileHash:
    """Tests for calculate_file_hash()."""

    def test_deterministic(self, tmp_path):
        """Same file content always produces the same hash."""
        f = tmp_path / "a.py"
        f.write_text("print('hello')", encoding="utf-8")
        h1 = detect_changes.calculate_file_hash(str(f))
        h2 = detect_changes.calculate_file_hash(str(f))
        assert h1 == h2

    def test_different_files_different_hashes(self, tmp_path):
        """Different file contents produce different hashes."""
        f1 = tmp_path / "a.py"
        f1.write_text("aaa", encoding="utf-8")
        f2 = tmp_path / "b.py"
        f2.write_text("bbb", encoding="utf-8")
        assert detect_changes.calculate_file_hash(str(f1)) != detect_changes.calculate_file_hash(str(f2))

    def test_nonexistent_file_returns_empty(self, tmp_path):
        """Non-existent file path returns empty string."""
        result = detect_changes.calculate_file_hash(str(tmp_path / "nope.py"))
        assert result == ""

    def test_result_is_16_hex_chars(self, tmp_path):
        """Hash result uses the shared truncation length."""
        f = tmp_path / "a.py"
        f.write_text("x", encoding="utf-8")
        h = detect_changes.calculate_file_hash(str(f))
        assert len(h) == common.HASH_TRUNCATE_LENGTH
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# should_include_file
# ---------------------------------------------------------------------------

class TestShouldIncludeFile:
    """Tests for should_include_file()."""

    def test_python_code_file_included(self):
        """A .py file is a code file and should be included."""
        p = Path("src") / "main.py"
        assert detect_changes.should_include_file(p, set()) is True

    def test_markdown_doc_file_included(self):
        """A .md file is a doc file and should be included."""
        p = Path("docs") / "readme.md"
        assert detect_changes.should_include_file(p, set()) is True

    def test_node_modules_excluded(self):
        """Files under node_modules are excluded by DEFAULT_EXCLUDES."""
        p = Path("node_modules") / "pkg" / "index.js"
        assert detect_changes.should_include_file(p, detect_changes.DEFAULT_EXCLUDES) is False

    def test_config_excludes(self):
        """config_excludes are merged into the exclusion set."""
        p = Path("src") / "main.py"
        assert detect_changes.should_include_file(p, set(), config_excludes={"src"}) is False

    def test_gitignore_cache_uses_common_ignore_logic(self):
        """should_include_file delegates ignore decisions to common.should_ignore_path."""
        cache = common.GitignoreCache()
        cache.dirs = {"generated"}
        cache.globs = {"*.tmp"}

        assert detect_changes.should_include_file(
            Path("generated") / "main.py", set(), gitignore_cache=cache
        ) is False
        assert detect_changes.should_include_file(
            Path("src") / "scratch.tmp", set(), gitignore_cache=cache
        ) is False

    def test_csv_not_included(self):
        """.csv is neither a code nor a doc extension, so excluded."""
        p = Path("data") / "report.csv"
        assert detect_changes.should_include_file(p, set()) is False

    def test_log_not_included(self):
        """.log is not a recognized extension, so excluded."""
        p = Path("app.log")
        assert detect_changes.should_include_file(p, set()) is False


# ---------------------------------------------------------------------------
# scan_project_files
# ---------------------------------------------------------------------------

class TestScanProjectFiles:
    """Tests for scan_project_files()."""

    def test_basic_scan_returns_dict(self, fake_python_project):
        """Scan returns a dict mapping relative paths to hashes."""
        result = detect_changes.scan_project_files(str(fake_python_project))
        assert isinstance(result, dict)
        # At least the Python source files and README.md should appear
        assert len(result) > 0

    def test_scan_keys_are_relative_paths(self, fake_python_project):
        """All keys in the returned dict are relative to project root."""
        result = detect_changes.scan_project_files(str(fake_python_project))
        for key in result:
            assert Path(key).is_absolute() is False

    def test_scan_excludes_git(self, fake_python_project):
        """Files under .git/ are never included."""
        git_file = fake_python_project / ".git" / "config"
        git_file.parent.mkdir(parents=True, exist_ok=True)
        git_file.write_text("[core]\nrepositoryformatversion = 0\n", encoding="utf-8")
        result = detect_changes.scan_project_files(str(fake_python_project))
        assert ".git/config" not in result

    def test_scan_with_custom_excludes(self, fake_python_project):
        """Custom excludes are honored."""
        result = detect_changes.scan_project_files(
            str(fake_python_project), excludes={"src"}
        )
        for key in result:
            assert not key.startswith("src")


# ---------------------------------------------------------------------------
# load_cached_checksums / save_checksums
# ---------------------------------------------------------------------------

class TestLoadCachedChecksums:
    """Tests for load_cached_checksums()."""

    def test_no_file_returns_empty(self, tmp_path):
        """Missing checksums file returns empty dict."""
        result = detect_changes.load_cached_checksums(str(tmp_path))
        assert result == {}

    def test_existing_file_returns_correct_data(self, tmp_path):
        """Existing checksums.json is parsed and returned."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        data = {"src/a.py": {"hash": "abc123", "doc": "", "updated_at": "2025-01-01T00:00:00"}}
        (cache_dir / "checksums.json").write_text(json.dumps(data), encoding="utf-8")
        result = detect_changes.load_cached_checksums(str(tmp_path))
        assert result == data


class TestSaveChecksums:
    """Tests for save_checksums()."""

    def test_creates_directory_if_needed(self, tmp_path):
        """save_checksums creates the cache/ directory automatically."""
        data = {"src/a.py": {"hash": "abc", "doc": "", "updated_at": "now"}}
        detect_changes.save_checksums(str(tmp_path), data)
        cache_file = tmp_path / "cache" / "checksums.json"
        assert cache_file.exists()
        loaded = json.loads(cache_file.read_text(encoding="utf-8"))
        assert loaded["checksums"] == data

    def test_overwrites_existing(self, tmp_path):
        """Calling save_checksums twice replaces the content."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        detect_changes.save_checksums(str(tmp_path), {"f1": {"hash": "1"}})
        detect_changes.save_checksums(str(tmp_path), {"f2": {"hash": "2"}})
        loaded = json.loads((cache_dir / "checksums.json").read_text(encoding="utf-8"))
        checksums = loaded.get("checksums", loaded)
        assert "f1" not in checksums
        assert "f2" in checksums


# ---------------------------------------------------------------------------
# detect_changes
# ---------------------------------------------------------------------------

class TestDetectChanges:
    """Tests for detect_changes()."""

    def _setup_deepwiki_cache(self, project_root):
        """Create the .deepwiki/cache/ directory required by detect_changes."""
        cache_dir = project_root / ".deepwiki" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def test_first_run_all_added(self, fake_python_project):
        """First run has no cache, so every file is 'added'."""
        self._setup_deepwiki_cache(fake_python_project)
        result = detect_changes.detect_changes(str(fake_python_project))
        assert result["has_changes"] is True
        assert len(result["added"]) > 0
        assert result["modified"] == []
        assert result["deleted"] == []

    def test_second_run_no_changes(self, fake_python_project):
        """Second run finds no changes because cache was saved on first run."""
        self._setup_deepwiki_cache(fake_python_project)
        detect_changes.detect_changes(str(fake_python_project))
        result = detect_changes.detect_changes(str(fake_python_project))
        assert result["has_changes"] is False
        assert result["added"] == []
        assert result["modified"] == []
        assert result["deleted"] == []
        assert "无变更" in result["summary"]

    def test_modified_file_detected(self, fake_python_project):
        """Modifying a file after first run triggers 'modified' detection."""
        self._setup_deepwiki_cache(fake_python_project)
        detect_changes.detect_changes(str(fake_python_project))

        # Modify a file
        main_py = fake_python_project / "main.py"
        main_py.write_text("# modified\n" + main_py.read_text(encoding="utf-8"), encoding="utf-8")

        result = detect_changes.detect_changes(str(fake_python_project))
        assert result["has_changes"] is True
        assert "main.py" in result["modified"]

    def test_deleted_file_detected(self, fake_python_project):
        """Deleting a file after first run triggers 'deleted' detection."""
        self._setup_deepwiki_cache(fake_python_project)
        detect_changes.detect_changes(str(fake_python_project))

        # Delete a file
        utils_py = fake_python_project / "src" / "utils.py"
        utils_py.unlink()

        result = detect_changes.detect_changes(str(fake_python_project))
        assert result["has_changes"] is True
        # The deleted file should appear as a relative path in the deleted list
        deleted_paths = [p.replace("\\", "/") for p in result["deleted"]]
        assert any("utils.py" in p for p in deleted_paths)

    def test_new_file_detected(self, fake_python_project):
        """Adding a new file after first run triggers 'added' detection."""
        self._setup_deepwiki_cache(fake_python_project)
        detect_changes.detect_changes(str(fake_python_project))

        # Add a new file
        (fake_python_project / "src" / "new_module.py").write_text(
            "# new module\n", encoding="utf-8"
        )

        result = detect_changes.detect_changes(str(fake_python_project))
        assert result["has_changes"] is True
        added_paths = [p.replace("\\", "/") for p in result["added"]]
        assert any("new_module.py" in p for p in added_paths)

    def test_summary_format_added(self, fake_python_project):
        """Summary string for added files contains '+N'."""
        self._setup_deepwiki_cache(fake_python_project)
        result = detect_changes.detect_changes(str(fake_python_project))
        # The fake_python_project has multiple files, so added count could be any positive number
        assert "+" in result["summary"]
        assert "新增" in result["summary"]

    def test_summary_format_modified(self, fake_python_project):
        """Summary string for modified files contains '~N'."""
        self._setup_deepwiki_cache(fake_python_project)
        detect_changes.detect_changes(str(fake_python_project))

        # Modify two files
        (fake_python_project / "main.py").write_text("# changed\n", encoding="utf-8")
        (fake_python_project / "src" / "main.py").write_text("# changed\n", encoding="utf-8")

        result = detect_changes.detect_changes(str(fake_python_project))
        assert "~" in result["summary"]

    def test_affected_modules_with_structure_json(self, fake_python_project):
        """When structure.json exists and files change, affected_modules is populated."""
        cache_dir = self._setup_deepwiki_cache(fake_python_project)

        # Write a structure.json that maps modules to source directories
        structure = {
            "project_root": str(fake_python_project),
            "modules": [
                {"name": "core", "path": "src", "core_files": ["src/main.py", "src/utils.py"]},
            ],
        }
        (cache_dir / "structure.json").write_text(json.dumps(structure), encoding="utf-8")

        # First run to seed cache
        detect_changes.detect_changes(str(fake_python_project))

        # Modify a file under src/
        (fake_python_project / "src" / "main.py").write_text("# changed\n", encoding="utf-8")

        result = detect_changes.detect_changes(str(fake_python_project))
        assert result["has_changes"] is True
        assert "affected_modules" in result
        assert "core" in result["affected_modules"]

    def test_affected_pages_from_generation_plan(self, fake_python_project):
        """Changed modules are mapped to affected pages using generation-plan.json."""
        cache_dir = self._setup_deepwiki_cache(fake_python_project)
        structure = {
            "project_root": str(fake_python_project),
            "modules": [
                {"name": "core", "path": "src", "core_files": ["src/main.py"]},
            ],
        }
        generation_plan = {
            "recompile_all": False,
            "pages": [
                {
                    "page_id": "module:core",
                    "affected_modules": ["src"],
                    "output_path": "wiki/modules/core.md",
                },
                {
                    "page_id": "overview",
                    "affected_modules": [],
                    "output_path": "wiki/overview.md",
                },
            ],
        }
        (cache_dir / "structure.json").write_text(json.dumps(structure), encoding="utf-8")
        (cache_dir / "generation-plan.json").write_text(
            json.dumps(generation_plan), encoding="utf-8"
        )

        detect_changes.detect_changes(str(fake_python_project))
        (fake_python_project / "src" / "main.py").write_text("# changed\n", encoding="utf-8")

        result = detect_changes.detect_changes(str(fake_python_project))
        assert result["affected_pages"] == ["module:core"]
        assert result["recompile_all"] is False


# ---------------------------------------------------------------------------
# update_checksums_cache
# ---------------------------------------------------------------------------

class TestUpdateChecksumsCache:
    """Tests for update_checksums_cache()."""

    def test_saves_checksums(self, tmp_path):
        """Checksums are written to .deepwiki/cache/checksums.json."""
        cache_dir = tmp_path / ".deepwiki" / "cache"
        cache_dir.mkdir(parents=True)
        current = {"src/a.py": "abcd1234efgh5678"}
        detect_changes.update_checksums_cache(str(tmp_path), current)

        loaded = json.loads((cache_dir / "checksums.json").read_text(encoding="utf-8"))
        checksums = loaded.get("checksums", loaded)
        assert "src/a.py" in checksums
        assert checksums["src/a.py"]["hash"] == "abcd1234efgh5678"

    def test_doc_mapping_saved(self, tmp_path):
        """doc_mapping entries are stored in cache entries."""
        cache_dir = tmp_path / ".deepwiki" / "cache"
        cache_dir.mkdir(parents=True)
        current = {"src/a.py": "abcd1234efgh5678"}
        doc_mapping = {"src/a.py": "wiki/modules/a.md"}
        detect_changes.update_checksums_cache(str(tmp_path), current, doc_mapping)

        loaded = json.loads((cache_dir / "checksums.json").read_text(encoding="utf-8"))
        checksums = loaded.get("checksums", loaded)
        assert checksums["src/a.py"]["doc"] == "wiki/modules/a.md"

    def test_creates_directory(self, tmp_path):
        """Cache directory is created if it does not exist."""
        current = {"src/a.py": "abcd1234efgh5678"}
        detect_changes.update_checksums_cache(str(tmp_path), current)
        assert (tmp_path / ".deepwiki" / "cache" / "checksums.json").exists()

    def test_entry_has_updated_at_field(self, tmp_path):
        """Each cache entry includes an updated_at ISO timestamp."""
        cache_dir = tmp_path / ".deepwiki" / "cache"
        cache_dir.mkdir(parents=True)
        current = {"src/a.py": "abcd1234efgh5678"}
        detect_changes.update_checksums_cache(str(tmp_path), current)

        loaded = json.loads((cache_dir / "checksums.json").read_text(encoding="utf-8"))
        checksums = loaded.get("checksums", loaded)
        assert "updated_at" in checksums["src/a.py"]


# ---------------------------------------------------------------------------
# propagate_reverse_dependencies
# ---------------------------------------------------------------------------

class TestPropagateReverseDependencies:
    """Tests for propagate_reverse_dependencies()."""

    def test_empty_changed_modules(self):
        """Empty changed_modules set returns empty set."""
        result = detect_changes.propagate_reverse_dependencies(set(), {"modules": []})
        assert result == set()

    def test_empty_structure(self):
        """Empty or None structure returns empty set."""
        assert detect_changes.propagate_reverse_dependencies({"core"}, {}) == set()
        assert detect_changes.propagate_reverse_dependencies({"core"}, None) == set()

    def test_no_modules_in_structure(self):
        """Structure with no modules list returns empty set."""
        assert detect_changes.propagate_reverse_dependencies({"core"}, {"modules": []}) == set()

    def test_propagation_detected(self, tmp_path):
        """When module B imports module A and A changes, B is affected."""
        # Create actual files so propagate_reverse_dependencies can read them
        mod_a_dir = tmp_path / "core"
        mod_a_dir.mkdir()
        (mod_a_dir / "index.py").write_text("def func_a(): pass\n", encoding="utf-8")

        mod_b_dir = tmp_path / "utils"
        mod_b_dir.mkdir()
        (mod_b_dir / "helper.py").write_text(
            "import core.index\n", encoding="utf-8"
        )

        structure = {
            "project_root": str(tmp_path),
            "modules": [
                {
                    "name": "core",
                    "path": "core",
                    "core_files": ["core/index.py"],
                },
                {
                    "name": "utils",
                    "path": "utils",
                    "core_files": ["utils/helper.py"],
                },
            ],
        }

        # Note: propagate_reverse_dependencies reads files from disk.
        # We pass the actual file paths so the function can find them.
        structure["project_root"] = str(tmp_path)

        result = detect_changes.propagate_reverse_dependencies({"core"}, structure)
        assert "utils" in result


# ---------------------------------------------------------------------------
# load_config_excludes
# ---------------------------------------------------------------------------

class TestLoadConfigExcludes:
    """Tests for load_config_excludes()."""

    def test_no_config_returns_empty(self, tmp_path):
        """Missing config.yaml returns empty set."""
        result = detect_changes.load_config_excludes(tmp_path)
        assert result == set()

    def test_with_exclude_list(self, tmp_path):
        """config.yaml with exclude list returns the correct set."""
        deepwiki = tmp_path / ".deepwiki"
        deepwiki.mkdir()
        (deepwiki / "config.yaml").write_text(
            "exclude:\n  - build\n  - temp\n  - logs\n", encoding="utf-8"
        )
        result = detect_changes.load_config_excludes(tmp_path)
        assert result == {"build", "temp", "logs"}

    def test_empty_exclude_list(self, tmp_path):
        """config.yaml with empty exclude list returns empty set."""
        deepwiki = tmp_path / ".deepwiki"
        deepwiki.mkdir()
        (deepwiki / "config.yaml").write_text(
            "exclude: []\n", encoding="utf-8"
        )
        result = detect_changes.load_config_excludes(tmp_path)
        assert result == set()

    def test_malformed_config_returns_empty(self, tmp_path):
        """Malformed YAML returns empty set (graceful fallback)."""
        deepwiki = tmp_path / ".deepwiki"
        deepwiki.mkdir()
        (deepwiki / "config.yaml").write_text(
            "not: valid: yaml: [", encoding="utf-8"
        )
        result = detect_changes.load_config_excludes(tmp_path)
        assert result == set()


# =========================================================================
# 新增测试：缓存版本控制
# =========================================================================

class TestCacheVersioningDetectChanges:
    """Tests for checksums.json version handling."""

    def test_stale_checksums_triggers_full_scan(self, tmp_path):
        """Old version checksums should be treated as empty (force full scan)."""
        deepwiki = tmp_path / ".deepwiki"
        cache_dir = deepwiki / "cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "checksums.json").write_text(json.dumps({
            "cache_schema_version": 0,
            "checksums": {"old_file.txt": {"hash": "abc123"}},
        }))

        cached = detect_changes.load_cached_checksums(str(deepwiki))
        assert cached == {}

    def test_saved_checksums_include_version(self, tmp_path):
        """Saved checksums should have cache_schema_version field."""
        deepwiki = tmp_path / ".deepwiki"
        cache_dir = deepwiki / "cache"
        cache_dir.mkdir(parents=True)
        detect_changes.save_checksums(str(deepwiki), {"test.py": {"hash": "abc"}})

        data = json.loads((cache_dir / "checksums.json").read_text())
        assert data.get("cache_schema_version") == common.CACHE_SCHEMA_VERSION
        assert "checksums" in data

    def test_load_saved_checksums_roundtrip(self, tmp_path):
        """Checksums saved then loaded should be consistent."""
        deepwiki = tmp_path / ".deepwiki"
        cache_dir = deepwiki / "cache"
        cache_dir.mkdir(parents=True)
        original = {"file1.py": {"hash": "aaa"}, "file2.py": {"hash": "bbb"}}
        detect_changes.save_checksums(str(deepwiki), original)

        loaded = detect_changes.load_cached_checksums(str(deepwiki))
        assert loaded == original

    def test_legacy_checksums_still_readable(self, tmp_path):
        """Checksums without version field (legacy format) should still load."""
        deepwiki = tmp_path / ".deepwiki"
        cache_dir = deepwiki / "cache"
        cache_dir.mkdir(parents=True)
        # Legacy format: no version field, data is directly the checksum dict
        legacy_data = {"file1.py": {"hash": "aaa"}, "file2.py": {"hash": "bbb"}}
        (cache_dir / "checksums.json").write_text(json.dumps(legacy_data))

        loaded = detect_changes.load_cached_checksums(str(deepwiki))
        # Should return the legacy data as-is (backward compatible)
        assert loaded == legacy_data
