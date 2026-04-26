"""Tests for scripts/init_wiki.py"""

import json
import pytest
from pathlib import Path

import init_wiki


class TestGetDefaultConfig:
    def test_returns_string(self):
        result = init_wiki.get_default_config()
        assert isinstance(result, str)

    def test_contains_generation(self):
        config = init_wiki.get_default_config()
        assert "generation:" in config

    def test_contains_exclude(self):
        config = init_wiki.get_default_config()
        assert "exclude:" in config

    def test_contains_language(self):
        config = init_wiki.get_default_config()
        assert "language:" in config


class TestGetDefaultMeta:
    def test_returns_dict(self):
        result = init_wiki.get_default_meta()
        assert isinstance(result, dict)

    def test_version(self):
        meta = init_wiki.get_default_meta()
        assert meta["version"] == "2.1.0"

    def test_last_updated_is_none(self):
        meta = init_wiki.get_default_meta()
        assert meta["last_updated"] is None

    def test_modules_is_empty_dict(self):
        meta = init_wiki.get_default_meta()
        assert meta["modules"] == {}

    def test_has_required_keys(self):
        meta = init_wiki.get_default_meta()
        expected_keys = {"version", "generated_at", "last_updated", "modules"}
        assert expected_keys == set(meta.keys())


class TestGetDefaultModuleMeta:
    def test_returns_dict(self):
        result = init_wiki.get_default_module_meta()
        assert isinstance(result, dict)

    def test_quality_level_is_none(self):
        meta = init_wiki.get_default_module_meta()
        assert meta["quality_level"] is None

    def test_has_required_keys(self):
        meta = init_wiki.get_default_module_meta()
        expected_keys = {"quality_level", "section_count", "word_count", "diagram_count", "last_updated"}
        assert expected_keys == set(meta.keys())


class TestInitDeepWiki:
    def test_creates_deepwiki_directory(self, tmp_path):
        result = init_wiki.init_deep_wiki(str(tmp_path))
        assert (tmp_path / ".deepwiki").is_dir()

    def test_creates_cache_directory(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        assert (tmp_path / ".deepwiki" / "cache").is_dir()

    def test_creates_wiki_directory(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        assert (tmp_path / ".deepwiki" / "wiki").is_dir()

    def test_creates_concepts_directory(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        assert (tmp_path / ".deepwiki" / "wiki" / "concepts").is_dir()

    def test_creates_deep_dive_directory(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        assert (tmp_path / ".deepwiki" / "wiki" / "deep-dive").is_dir()

    def test_creates_reference_directory(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        assert (tmp_path / ".deepwiki" / "wiki" / "reference").is_dir()

    def test_creates_assets_directory(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        assert (tmp_path / ".deepwiki" / "wiki" / "assets").is_dir()

    def test_creates_config_yaml(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        config_path = tmp_path / ".deepwiki" / "config.yaml"
        assert config_path.is_file()
        content = config_path.read_text(encoding="utf-8")
        assert "generation:" in content
        assert "language:" in content

    def test_creates_meta_json(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        meta_path = tmp_path / ".deepwiki" / "meta.json"
        assert meta_path.is_file()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["version"] == "2.1.0"
        assert "modules" in meta

    def test_creates_checksums_json(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        path = tmp_path / ".deepwiki" / "cache" / "checksums.json"
        assert path.is_file()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_creates_structure_json(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        path = tmp_path / ".deepwiki" / "cache" / "structure.json"
        assert path.is_file()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "project_name" in data
        assert "modules" in data

    def test_creates_progress_json(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        path = tmp_path / ".deepwiki" / "cache" / "progress.json"
        assert path.is_file()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "phases" in data

    def test_creates_gitignore(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        gitignore_path = tmp_path / ".deepwiki" / ".gitignore"
        assert gitignore_path.is_file()
        content = gitignore_path.read_text(encoding="utf-8")
        assert "cache/" in content
        assert "*.bak" in content

    def test_refuses_without_force(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        result = init_wiki.init_deep_wiki(str(tmp_path), force=False)
        assert result["success"] is False
        assert "force=True" in result["message"]

    def test_force_reinitializes(self, tmp_path):
        init_wiki.init_deep_wiki(str(tmp_path))
        result = init_wiki.init_deep_wiki(str(tmp_path), force=True)
        assert result["success"] is True
        # Config should be backed up
        backup_path = tmp_path / ".deepwiki" / "config.yaml.bak"
        assert backup_path.is_file()

    def test_returns_result_structure(self, tmp_path):
        result = init_wiki.init_deep_wiki(str(tmp_path))
        assert "success" in result
        assert "created" in result
        assert "skipped" in result
        assert "message" in result

    def test_created_list_not_empty(self, tmp_path):
        result = init_wiki.init_deep_wiki(str(tmp_path))
        assert len(result["created"]) > 0

    def test_success_message(self, tmp_path):
        result = init_wiki.init_deep_wiki(str(tmp_path))
        assert result["success"] is True
        assert "成功初始化" in result["message"]


def test_progress_json_has_analysis_phase(tmp_path):
    """初始化后 progress.json 应包含 analysis 阶段（第4步并行追踪）"""
    import json
    init_wiki.init_deep_wiki(str(tmp_path))
    progress_path = tmp_path / ".deepwiki" / "cache" / "progress.json"
    assert progress_path.exists()
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert "phases" in progress
    assert "analysis" in progress["phases"], \
        "progress.json 应包含 analysis 阶段"
    assert progress["phases"]["analysis"]["status"] == "pending"
    assert progress["phases"]["analysis"].get("modules") == {}


def test_progress_json_overview_documents(tmp_path):
    """progress.json 的 overview.documents 应包含 overview.md 而非 index.md/architecture.md"""
    import json
    init_wiki.init_deep_wiki(str(tmp_path))
    progress_path = tmp_path / ".deepwiki" / "cache" / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    docs = progress["phases"]["overview"]["documents"]
    assert "overview.md" in docs, "overview.md 应在 overview.documents 中"
    assert "index.md" not in docs, "index.md 不应再出现在 overview.documents 中"
    assert "architecture.md" not in docs, "architecture.md 不应再出现在 overview.documents 中"
