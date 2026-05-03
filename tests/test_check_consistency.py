"""Tests for check_cross_module_consistency — 链接导航检查"""

import json
from pathlib import Path

import pytest

from scripts.quality.check_cross_module_consistency import (
    check_menu_paths,
    check_wiki_links,
    _collect_wiki_files,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_menu(wiki_path: Path, menu_data: dict) -> Path:
    menu_path = wiki_path / "menu.json"
    menu_path.write_text(json.dumps(menu_data, ensure_ascii=False), encoding="utf-8")
    return menu_path


def _write_md(wiki_path: Path, rel: str, content: str = "") -> Path:
    p = wiki_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# _collect_wiki_files
# ---------------------------------------------------------------------------


class TestCollectWikiFiles:
    def test_basic(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md")
        _write_md(wiki, "deep-dive/auth.md")
        files = _collect_wiki_files(wiki)
        assert "overview.md" in files
        assert "deep-dive/auth.md" in files

    def test_nonexistent_dir(self, tmp_path):
        assert _collect_wiki_files(tmp_path / "nope") == set()


# ---------------------------------------------------------------------------
# check_menu_paths
# ---------------------------------------------------------------------------


class TestCheckMenuPaths:
    def test_valid_paths_no_issues(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md")
        _write_md(wiki, "getting-started.md")
        _write_md(wiki, "deep-dive/auth.md")

        menu = {
            "items": [
                {
                    "title": "概览",
                    "items": [
                        {"title": "Overview", "path": "overview.md"},
                        {"title": "Getting Started", "path": "getting-started.md"},
                    ],
                },
                {
                    "title": "深入理解",
                    "items": [
                        {"title": "Auth", "path": "deep-dive/auth.md"},
                    ],
                },
            ],
        }
        _write_menu(wiki, menu)

        issues = check_menu_paths(tmp_path, menu)
        assert issues == []

    def test_missing_file(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md")
        # deep-dive/auth.md does NOT exist

        menu = {
            "items": [
                {
                    "title": "概览",
                    "items": [
                        {"title": "Overview", "path": "overview.md"},
                    ],
                },
                {
                    "title": "深入理解",
                    "items": [
                        {"title": "Auth", "path": "deep-dive/auth.md"},
                    ],
                },
            ],
        }
        _write_menu(wiki, menu)

        issues = check_menu_paths(tmp_path, menu)
        assert len(issues) == 1
        assert issues[0]["type"] == "menu_missing_file"
        assert issues[0]["path"] == "deep-dive/auth.md"
        assert issues[0]["severity"] == "error"
        assert "不存在" in issues[0]["message"]

    def test_nested_groups(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "deep-dive/engine/scheduler.md")
        # executor.md does NOT exist

        menu = {
            "items": [
                {
                    "title": "深入理解",
                    "items": [
                        {
                            "title": "核心引擎",
                            "items": [
                                {"title": "调度器", "path": "deep-dive/engine/scheduler.md"},
                                {"title": "执行器", "path": "deep-dive/engine/executor.md"},
                            ],
                        },
                    ],
                },
            ],
        }
        _write_menu(wiki, menu)

        issues = check_menu_paths(tmp_path, menu)
        assert len(issues) == 1
        assert issues[0]["path"] == "deep-dive/engine/executor.md"

    def test_empty_menu(self, tmp_path):
        issues = check_menu_paths(tmp_path, {"items": []})
        assert issues == []

    def test_no_menu(self, tmp_path):
        issues = check_menu_paths(tmp_path, {})
        assert issues == []

    def test_group_node_without_path(self, tmp_path):
        """分组节点（有 items 子项，无 path）不应被报告为缺失文件。"""
        wiki = tmp_path / "wiki"
        _write_md(wiki, "deep-dive/a.md")

        menu = {
            "items": [
                {
                    "title": "分组",
                    "items": [
                        {"title": "A", "path": "deep-dive/a.md"},
                    ],
                },
            ],
        }
        _write_menu(wiki, menu)

        issues = check_menu_paths(tmp_path, menu)
        assert issues == []


# ---------------------------------------------------------------------------
# check_wiki_links
# ---------------------------------------------------------------------------


class TestCheckWikiLinks:
    def test_valid_links_no_issues(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md", "See [Getting Started](getting-started.md).")
        _write_md(wiki, "getting-started.md", "Back to [Overview](overview.md).")

        issues = check_wiki_links(tmp_path)
        assert issues == []

    def test_broken_relative_link(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md", "See [Missing](deep-dive/nonexistent.md).")

        issues = check_wiki_links(tmp_path)
        assert len(issues) == 1
        assert issues[0]["type"] == "broken_link"
        assert issues[0]["target"] == "deep-dive/nonexistent.md"
        assert issues[0]["severity"] == "error"

    def test_cross_directory_link(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md", "See [Auth](deep-dive/auth.md).")
        _write_md(wiki, "deep-dive/auth.md",
                   "Back to [Overview](../overview.md).")

        issues = check_wiki_links(tmp_path)
        assert issues == []

    def test_broken_cross_directory_link(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "deep-dive/auth.md",
                   "See [Missing](../concepts/missing.md).")
        # concepts/missing.md does NOT exist

        issues = check_wiki_links(tmp_path)
        assert len(issues) == 1
        assert issues[0]["type"] == "broken_link"

    def test_ignores_absolute_urls(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md",
                   "See [GitHub](https://github.com/foo) and [file](file:///src/a.py).")

        issues = check_wiki_links(tmp_path)
        assert issues == []

    def test_ignores_pure_anchor_links(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md", "Jump to [section](#api-overview).")

        issues = check_wiki_links(tmp_path)
        assert issues == []

    def test_link_with_anchor_to_existing_file(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md",
                   "See [Getting Started](getting-started.md#prerequisites).")
        _write_md(wiki, "getting-started.md", "")

        issues = check_wiki_links(tmp_path)
        assert issues == []

    def test_link_with_anchor_to_missing_file(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md",
                   "See [Missing](missing.md#section).")

        issues = check_wiki_links(tmp_path)
        assert len(issues) == 1
        assert issues[0]["type"] == "broken_link"

    def test_multiple_broken_links(self, tmp_path):
        wiki = tmp_path / "wiki"
        _write_md(wiki, "overview.md",
                   "[A](a.md) and [B](b.md)")

        issues = check_wiki_links(tmp_path)
        assert len(issues) == 2

    def test_no_wiki_dir(self, tmp_path):
        issues = check_wiki_links(tmp_path)
        assert issues == []
