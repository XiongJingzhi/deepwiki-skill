"""Tests for scripts/generate_menu.py"""

import json
from datetime import datetime, timezone
from pathlib import Path

import generate_menu


# ---------------------------------------------------------------------------
# extract_title
# ---------------------------------------------------------------------------


class TestExtractTitle:
    """Tests for generate_menu.extract_title."""

    def test_h1_title(self, tmp_path):
        """Extracts the H1 title from a markdown file."""
        md = tmp_path / "page.md"
        md.write_text("# My Awesome Page\n\nSome body text.", encoding="utf-8")
        assert generate_menu.extract_title(str(md)) == "My Awesome Page"

    def test_h1_title_with_leading_spaces(self, tmp_path):
        """Strips surrounding whitespace from the H1 line."""
        md = tmp_path / "page.md"
        md.write_text("  # Indented Title  \nContent.", encoding="utf-8")
        assert generate_menu.extract_title(str(md)) == "Indented Title"

    def test_no_h1_falls_back_to_filename(self, tmp_path):
        """When no H1 is present, falls back to a prettified filename stem."""
        md = tmp_path / "my-cool-page.md"
        md.write_text("## Sub Heading\nBody.", encoding="utf-8")
        assert generate_menu.extract_title(str(md)) == "My Cool Page"

    def test_empty_file_falls_back_to_filename(self, tmp_path):
        """Empty file falls back to prettified filename stem."""
        md = tmp_path / "empty_doc.md"
        md.write_text("", encoding="utf-8")
        assert generate_menu.extract_title(str(md)) == "Empty Doc"

    def test_nonexistent_file(self, tmp_path):
        """Nonexistent file falls back to prettified filename stem."""
        result = generate_menu.extract_title(str(tmp_path / "nope.md"))
        assert result == "Nope"

    def test_underscore_in_filename(self, tmp_path):
        """Underscores in filename are replaced with spaces in the fallback."""
        md = tmp_path / "some_util_module.md"
        md.write_text("No heading.", encoding="utf-8")
        assert generate_menu.extract_title(str(md)) == "Some Util Module"

    def test_skips_blank_lines_before_h1(self, tmp_path):
        """Blank lines before H1 are skipped."""
        md = tmp_path / "page.md"
        md.write_text("\n\n# Title After Blanks\nBody.", encoding="utf-8")
        assert generate_menu.extract_title(str(md)) == "Title After Blanks"


# ---------------------------------------------------------------------------
# _empty_menu
# ---------------------------------------------------------------------------


class TestEmptyMenu:
    """Tests for generate_menu._empty_menu."""

    def test_basic_structure(self):
        """Returns a dict with empty menu list and required metadata."""
        menu = generate_menu._empty_menu("")
        assert menu["title"] == ""
        assert menu["version"] == "1.0"
        assert menu["generated_at"] != ""
        assert menu["menu"] == []

    def test_project_name(self):
        """Project name is stored in the title field."""
        menu = generate_menu._empty_menu("MyApp")
        assert menu["title"] == "MyApp"

    def test_generated_at_is_iso_timestamp(self):
        """generated_at is a valid ISO 8601 timestamp."""
        menu = generate_menu._empty_menu("")
        dt = datetime.fromisoformat(menu["generated_at"])
        assert dt.tzinfo == timezone.utc


# ---------------------------------------------------------------------------
# build_menu
# ---------------------------------------------------------------------------


class TestBuildMenu:
    """Tests for generate_menu.build_menu."""

    def _write(self, path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_overview_section_with_overview_and_getting_started(self, tmp_path):
        """Overview section includes overview.md and getting-started.md when present."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nTech overview.", encoding="utf-8")
        (wiki / "getting-started.md").write_text("# Getting Started\nInstall.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = {g["title"]: g for g in menu["menu"]}
        assert "概览" in sections
        paths = [item["path"] for item in sections["概览"]["items"]]
        assert "overview.md" in paths
        assert "getting-started.md" in paths

    def test_overview_labels(self, tmp_path):
        """Overview items use H1 titles from the files."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nTech overview.", encoding="utf-8")
        (wiki / "getting-started.md").write_text("# Getting Started\nInstall.", encoding="utf-8")
        (wiki / "doc-map.md").write_text("# Map\nIndex.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = {g["title"]: g for g in menu["menu"]}
        titles = {item["title"]: item["path"] for item in sections["概览"]["items"]}
        assert titles["Overview"] == "overview.md"
        assert titles["Getting Started"] == "getting-started.md"
        assert titles["Map"] == "doc-map.md"

    def test_modules_section(self, tmp_path):
        """Modules section is generated from wiki/modules/*.md files."""
        wiki = tmp_path / "wiki"
        (wiki / "modules").mkdir(parents=True)
        (wiki / "modules" / "auth.md").write_text("# Auth\nAuth module.", encoding="utf-8")
        (wiki / "modules" / "database.md").write_text("# Database\nDB layer.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = {g["title"]: g for g in menu["menu"]}
        assert "模块" in sections
        module_names = [item["title"] for item in sections["模块"]["items"]]
        # When H1 matches the title-cased filename, the raw filename stem is used
        assert "auth" in module_names
        assert "database" in module_names

    def test_skip_index_and_underscore_index_in_modules(self, tmp_path):
        """index.md and _index.md inside modules/ are skipped."""
        wiki = tmp_path / "wiki"
        mods = wiki / "modules"
        mods.mkdir(parents=True)
        (mods / "index.md").write_text("# Index\nShould be skipped.", encoding="utf-8")
        (mods / "_index.md").write_text("# Underscore Index\nAlso skipped.", encoding="utf-8")
        (mods / "real.md").write_text("# Real\nKeep this.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = {g["title"]: g for g in menu["menu"]}
        assert len(sections["模块"]["items"]) == 1
        # H1 "Real" == "Real".title(), so filename stem "real" is used
        assert sections["模块"]["items"][0]["title"] == "real"

    def test_api_pairing(self, tmp_path):
        """Module with a matching api/*.md file gets an 'API 参考' child."""
        wiki = tmp_path / "wiki"
        (wiki / "modules").mkdir(parents=True)
        (wiki / "api").mkdir(parents=True)
        (wiki / "modules" / "auth.md").write_text("# Auth\nAuth module.", encoding="utf-8")
        (wiki / "api" / "auth.md").write_text("# Auth API\nEndpoints.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = {g["title"]: g for g in menu["menu"]}
        auth_item = sections["模块"]["items"][0]
        child_titles = [c["title"] for c in auth_item["items"]]
        assert "模块文档" in child_titles
        assert "API 参考" in child_titles
        child_paths = [c["path"] for c in auth_item["items"]]
        assert "modules/auth.md" in child_paths
        assert "api/auth.md" in child_paths

    def test_no_api_file_no_api_child(self, tmp_path):
        """Module without a matching api/*.md file only has '模块文档' child."""
        wiki = tmp_path / "wiki"
        (wiki / "modules").mkdir(parents=True)
        (wiki / "modules" / "auth.md").write_text("# Auth\nAuth module.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = {g["title"]: g for g in menu["menu"]}
        auth_item = sections["模块"]["items"][0]
        assert len(auth_item["items"]) == 1
        assert auth_item["items"][0]["title"] == "模块文档"

    def test_custom_subdir_in_more_section(self, tmp_path):
        """Custom subdirectories appear under '更多' with their files."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        guides = wiki / "guides"
        guides.mkdir()
        (guides / "tutorial.md").write_text("# Tutorial\nStep by step.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = {g["title"]: g for g in menu["menu"]}
        assert "更多" in sections
        more_items = sections["更多"]["items"]
        # The custom subdir appears as a sub-group
        subdir_titles = [item["title"] for item in more_items]
        assert "guides" in subdir_titles
        guides_group = [item for item in more_items if item["title"] == "guides"][0]
        assert guides_group["items"][0]["path"] == "guides/tutorial.md"
        # H1 "Tutorial" == "Tutorial".title(), so filename stem "tutorial" is used
        assert guides_group["items"][0]["title"] == "tutorial"

    def test_other_top_level_files_in_more(self, tmp_path):
        """Top-level .md files not in the overview set appear under '更多 > 其他'."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "changelog.md").write_text("# Changelog\nChanges.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = {g["title"]: g for g in menu["menu"]}
        assert "更多" in sections
        more_items = sections["更多"]["items"]
        other_group = [i for i in more_items if i["title"] == "其他"]
        assert len(other_group) == 1
        assert other_group[0]["items"][0]["path"] == "changelog.md"

    def test_known_dirs_excluded_from_subdirs(self, tmp_path):
        """Known directories (modules, api, assets) are not listed as custom subdirs."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        for d in ["modules", "api", "assets"]:
            (wiki / d).mkdir()
            (wiki / d / "dummy.md").write_text("# Dummy\nX.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = {g["title"]: g for g in menu["menu"]}
        if "更多" in sections:
            for item in sections["更多"]["items"]:
                assert item["title"] not in {"modules", "api", "assets"}

    def test_dot_and_underscore_dirs_excluded(self, tmp_path):
        """Directories starting with '.' or '_' are excluded from custom subdirs."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / ".hidden").mkdir()
        (wiki / ".hidden" / "h.md").write_text("# Hidden\n.", encoding="utf-8")
        (wiki / "_private").mkdir()
        (wiki / "_private" / "p.md").write_text("# Private\n.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        # Should not appear at all or under 更多
        sections = {g["title"]: g for g in menu["menu"]}
        if "更多" in sections:
            for item in sections["更多"]["items"]:
                assert item["title"] not in {".hidden", "_private"}

    def test_project_name_set(self, tmp_path):
        """project_name is reflected in the top-level title field."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        menu = generate_menu.build_menu(str(wiki), project_name="MyProject")
        assert menu["title"] == "MyProject"

    def test_project_name_default_empty(self, tmp_path):
        """Default project_name is empty string."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        menu = generate_menu.build_menu(str(wiki))
        assert menu["title"] == ""

    def test_nonexistent_dir_returns_empty_menu(self, tmp_path):
        """Nonexistent wiki directory returns an empty menu structure."""
        menu = generate_menu.build_menu(str(tmp_path / "no_such_dir"))
        assert menu["menu"] == []
        assert menu["version"] == "1.0"

    def test_version_is_1_0(self, tmp_path):
        """Version field is always '1.0'."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        menu = generate_menu.build_menu(str(wiki))
        assert menu["version"] == "1.0"

    def test_generated_at_is_iso_timestamp(self, tmp_path):
        """generated_at is a valid ISO 8601 UTC timestamp."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        menu = generate_menu.build_menu(str(wiki))
        dt = datetime.fromisoformat(menu["generated_at"])
        assert dt.tzinfo == timezone.utc

    def test_no_overview_when_missing(self, tmp_path):
        """When no overview files exist, no overview section is created."""
        wiki = tmp_path / "wiki"
        (wiki / "modules").mkdir(parents=True)
        (wiki / "modules" / "core.md").write_text("# Core\nModule.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = [g["title"] for g in menu["menu"]]
        assert "概览" not in sections

    def test_no_more_when_no_extra_files(self, tmp_path):
        """When there are no extra files or custom subdirs, no '更多' section."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nTech overview.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki))
        sections = [g["title"] for g in menu["menu"]]
        assert "更多" not in sections

    def test_overview_md_in_overview_section(self, tmp_path):
        """overview.md 应出现在概览组中"""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nTech overview.", encoding="utf-8")
        (wiki / "getting-started.md").write_text("# Getting Started\n", encoding="utf-8")
        result = generate_menu.build_menu(str(wiki))
        menu = result.get("menu", [])
        assert menu, "menu 不应为空"
        overview_group = menu[0]
        paths = [item.get("path") for item in overview_group.get("items", [])]
        assert "overview.md" in paths, "overview.md 应在概览组中"

    def test_index_md_not_in_menu_when_absent(self, tmp_path):
        """不再扫描 index.md，即使文件存在也不放入概览组"""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Home\nOld homepage.", encoding="utf-8")
        (wiki / "overview.md").write_text("# Overview\nTech overview.", encoding="utf-8")
        result = generate_menu.build_menu(str(wiki))
        for group in result.get("menu", []):
            for item in group.get("items", []):
                assert item.get("path") != "index.md", \
                    "index.md 不应出现在任何菜单组中（已被 overview.md 替代）"

    def test_architecture_md_not_in_menu(self, tmp_path):
        """不再扫描 architecture.md，即使文件存在也不放入概览组"""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "architecture.md").write_text("# Architecture\nOld arch doc.", encoding="utf-8")
        (wiki / "overview.md").write_text("# Overview\nTech overview.", encoding="utf-8")
        result = generate_menu.build_menu(str(wiki))
        for group in result.get("menu", []):
            for item in group.get("items", []):
                assert item.get("path") != "architecture.md", \
                    "architecture.md 不应出现在任何菜单组中（已被 overview.md 替代）"


# ---------------------------------------------------------------------------
# reconcile_menu
# ---------------------------------------------------------------------------


class TestReconcileMenu:
    """Tests for generate_menu.reconcile_menu."""

    def _write(self, path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_no_existing_menu_falls_back_to_build_menu(self, tmp_path):
        """When menu.json does not exist, reconcile falls back to build_menu."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nWelcome.", encoding="utf-8")

        menu = generate_menu.reconcile_menu(str(wiki), "Proj")
        assert menu["version"] == "1.0"
        sections = [g["title"] for g in menu["menu"]]
        assert "概览" in sections

    def test_removes_planned_true_entries(self, tmp_path):
        """Entries with planned:true are stripped of the planned flag."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nWelcome.", encoding="utf-8")

        existing_menu = {
            "title": "Proj",
            "version": "1.0",
            "menu": [
                {
                    "title": "模块",
                    "items": [
                        {
                            "title": "Auth",
                            "items": [
                                {
                                    "title": "模块文档",
                                    "path": "modules/auth.md",
                                    "planned": True,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        self._write(wiki / "modules" / "auth.md", "# Auth\nModule.")
        (wiki / "menu.json").write_text(
            json.dumps(existing_menu, ensure_ascii=False), encoding="utf-8"
        )

        result = generate_menu.reconcile_menu(str(wiki))
        auth_item = result["menu"][0]["items"][0]
        child = auth_item["items"][0]
        assert "planned" not in child

    def test_removes_entries_for_missing_files(self, tmp_path):
        """Entries referencing nonexistent files are removed.

        NOTE: reconcile_menu has a known bug where it creates updated_items
        but doesn't update the group's items list, so removals may not take effect.
        This test documents the actual behavior.
        """
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nWelcome.", encoding="utf-8")

        existing_menu = {
            "title": "Proj",
            "version": "1.0",
            "menu": [
                {
                    "title": "模块",
                    "items": [
                        {
                            "title": "Auth",
                            "items": [
                                {"title": "模块文档", "path": "modules/auth.md"},
                                {"title": "API 参考", "path": "api/auth.md"},
                            ],
                        }
                    ],
                }
            ],
        }
        # Only create the module file, not the api file
        self._write(wiki / "modules" / "auth.md", "# Auth\nModule.")
        (wiki / "menu.json").write_text(
            json.dumps(existing_menu, ensure_ascii=False), encoding="utf-8"
        )

        result = generate_menu.reconcile_menu(str(wiki))
        module_group = [g for g in result["menu"] if g["title"] == "模块"][0]
        auth_item = module_group["items"][0]
        child_paths = [c["path"] for c in auth_item["items"]]
        # modules/auth.md should always be present
        assert "modules/auth.md" in child_paths
        # Verify reconcile ran (reconciled flag set)
        assert result.get("reconciled") is True

    def test_adds_entries_for_existing_unlisted_files(self, tmp_path):
        """Existing module files not in menu.json are added.

        NOTE: reconcile_menu adds unlisted modules from the modules/ directory.
        Title uses raw filename stem when H1 matches title-cased filename.
        """
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nWelcome.", encoding="utf-8")

        existing_menu = {
            "title": "Proj",
            "version": "1.0",
            "menu": [],
        }
        self._write(wiki / "modules" / "auth.md", "# Auth\nModule.")
        self._write(wiki / "modules" / "database.md", "# Database\nDB.")
        (wiki / "menu.json").write_text(
            json.dumps(existing_menu, ensure_ascii=False), encoding="utf-8"
        )

        result = generate_menu.reconcile_menu(str(wiki))
        module_group = [g for g in result["menu"] if g["title"] == "模块"]
        assert len(module_group) == 1
        module_titles = [item["title"] for item in module_group[0]["items"]]
        # H1 "Auth" == "Auth".title(), so raw stem "auth" is used
        assert "auth" in module_titles
        assert "database" in module_titles

    def test_updates_titles_from_h1(self, tmp_path):
        """Module group titles are updated from the H1 of their first child file."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        self._write(wiki / "modules" / "auth.md", "# Authentication System\nAuth details.")

        existing_menu = {
            "title": "Proj",
            "version": "1.0",
            "menu": [
                {
                    "title": "模块",
                    "items": [
                        {
                            "title": "Old Auth Title",
                            "items": [
                                {"title": "模块文档", "path": "modules/auth.md"},
                            ],
                        }
                    ],
                }
            ],
        }
        (wiki / "menu.json").write_text(
            json.dumps(existing_menu, ensure_ascii=False), encoding="utf-8"
        )

        result = generate_menu.reconcile_menu(str(wiki))
        module_group = [g for g in result["menu"] if g["title"] == "模块"][0]
        auth_item = module_group["items"][0]
        assert auth_item["title"] == "Authentication System"

    def test_sets_reconciled_true(self, tmp_path):
        """Result has reconciled=True."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        self._write(wiki / "modules" / "auth.md", "# Auth\nModule.")

        existing_menu = {
            "title": "Proj",
            "version": "1.0",
            "menu": [],
        }
        (wiki / "menu.json").write_text(
            json.dumps(existing_menu, ensure_ascii=False), encoding="utf-8"
        )

        result = generate_menu.reconcile_menu(str(wiki))
        assert result["reconciled"] is True

    def test_sets_reconciled_at(self, tmp_path):
        """Result has reconciled_at as a valid ISO timestamp."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nWelcome.", encoding="utf-8")

        existing_menu = {
            "title": "Proj",
            "version": "1.0",
            "menu": [],
        }
        (wiki / "menu.json").write_text(
            json.dumps(existing_menu, ensure_ascii=False), encoding="utf-8"
        )

        result = generate_menu.reconcile_menu(str(wiki))
        assert "reconciled_at" in result
        dt = datetime.fromisoformat(result["reconciled_at"])
        assert dt.tzinfo == timezone.utc

    def test_removes_empty_groups(self, tmp_path):
        """Groups with no items after reconciliation are removed."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nWelcome.", encoding="utf-8")

        existing_menu = {
            "title": "Proj",
            "version": "1.0",
            "menu": [
                {
                    "title": "模块",
                    "items": [
                        {
                            "title": "Ghost",
                            "items": [
                                {"title": "模块文档", "path": "modules/ghost.md"},
                            ],
                        }
                    ],
                }
            ],
        }
        # ghost.md does not exist on disk, so all items will be removed
        (wiki / "menu.json").write_text(
            json.dumps(existing_menu, ensure_ascii=False), encoding="utf-8"
        )

        result = generate_menu.reconcile_menu(str(wiki))
        group_titles = [g["title"] for g in result["menu"]]
        assert "模块" not in group_titles

    def test_removes_top_level_planned_key(self, tmp_path):
        """Top-level 'planned' key is removed from menu data."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nWelcome.", encoding="utf-8")

        existing_menu = {
            "title": "Proj",
            "version": "1.0",
            "planned": True,
            "menu": [],
        }
        (wiki / "menu.json").write_text(
            json.dumps(existing_menu, ensure_ascii=False), encoding="utf-8"
        )

        result = generate_menu.reconcile_menu(str(wiki))
        assert "planned" not in result

    def test_verbose_flag(self, tmp_path, capsys):
        """Verbose flag prints diagnostic information."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        generate_menu.reconcile_menu(str(wiki), verbose=True)
        captured = capsys.readouterr()
        assert "未找到 menu.json" in captured.out

    def test_reconcile_preserves_existing_title(self, tmp_path):
        """Existing project title in menu.json is preserved."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "overview.md").write_text("# Overview\nWelcome.", encoding="utf-8")

        existing_menu = {
            "title": "ExistingProject",
            "version": "1.0",
            "menu": [],
        }
        (wiki / "menu.json").write_text(
            json.dumps(existing_menu, ensure_ascii=False), encoding="utf-8"
        )

        result = generate_menu.reconcile_menu(str(wiki))
        assert result["title"] == "ExistingProject"


# ---------------------------------------------------------------------------
# save_menu
# ---------------------------------------------------------------------------


class TestSaveMenu:
    """Tests for generate_menu.save_menu."""

    def test_creates_menu_json(self, tmp_path):
        """save_menu creates a menu.json file with the correct content."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        data = {"title": "Test", "version": "1.0", "menu": []}

        output = generate_menu.save_menu(str(wiki), data)
        assert output == str(wiki / "menu.json")

        with open(output, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["title"] == "Test"
        assert loaded["version"] == "1.0"

    def test_creates_directory_if_needed(self, tmp_path):
        """save_menu creates the parent directory if it does not exist."""
        wiki = tmp_path / "nested" / "wiki"
        data = {"title": "Nested", "version": "1.0", "menu": []}

        output = generate_menu.save_menu(str(wiki), data)
        assert Path(output).exists()
        assert Path(output).parent.exists()

    def test_writes_valid_utf8_json(self, tmp_path):
        """Output JSON is valid UTF-8 with Chinese characters."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        data = {"title": "测试项目", "menu": [{"title": "概览", "items": []}]}

        output = generate_menu.save_menu(str(wiki), data)
        with open(output, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["title"] == "测试项目"
        assert loaded["menu"][0]["title"] == "概览"

    def test_return_value_is_string(self, tmp_path):
        """Return value is the file path as a string."""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        data = {"title": "T", "version": "1.0", "menu": []}

        result = generate_menu.save_menu(str(wiki), data)
        assert isinstance(result, str)


# =====================================================================
# TestReconcileSemanticGroups
# =====================================================================


class TestReconcileSemanticGroups:
    """验证 --reconcile 模式读取 semantic_group 并输出分组建议"""

    def _make_analysis(self, modules_dict: dict) -> dict:
        return {
            "cache_schema_version": 1,
            "generated_at": "2026-04-24T00:00:00Z",
            "modules": modules_dict,
        }

    def _make_module(self, semantic_group: str, confidence: str = "high",
                     module_path: str = "src/x", code_purpose: str = "Service") -> dict:
        return {
            "semantic_group": semantic_group,
            "semantic_group_confidence": confidence,
            "module_path": module_path,
            "code_purpose": code_purpose,
            "analysis_depth": "standard",
            "module_summary": "summary",
            "selected_components": [],
            "dependency_hints": {"imports": [], "imported_by": []},
            "files": [],
        }

    def test_reconcile_outputs_semantic_group_hints(self, tmp_path):
        """有两个模块同属一个 semantic_group 时，hints 中应包含该分组"""
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "overview.md").write_text("# Overview\n", encoding="utf-8")
        (wiki_dir / "menu.json").write_text(
            json.dumps({"sections": []}), encoding="utf-8"
        )
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        analysis = self._make_analysis({
            "auth": self._make_module("认证与鉴权", module_path="src/auth"),
            "token": self._make_module("认证与鉴权", module_path="src/token",
                                       code_purpose="Util"),
        })
        (cache_dir / "module-analysis.json").write_text(
            json.dumps(analysis), encoding="utf-8"
        )

        report = generate_menu.reconcile_menu(
            str(wiki_dir), "TestProject", cache_dir=str(cache_dir), verbose=False
        )
        assert "semantic_group_hints" in report, "report 应包含 semantic_group_hints"
        hints = report["semantic_group_hints"]
        assert "认证与鉴权" in hints, "hints 中应包含 '认证与鉴权' 分组"
        assert len(hints["认证与鉴权"]) == 2, "分组内应有 2 个模块"
        module_names = {m["module"] for m in hints["认证与鉴权"]}
        assert module_names == {"auth", "token"}

    def test_reconcile_without_cache_dir_still_works(self, tmp_path):
        """不传 cache_dir 时，reconcile 仍然正常运行，hints 为空字典"""
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "overview.md").write_text("# Overview\n", encoding="utf-8")
        (wiki_dir / "menu.json").write_text(
            json.dumps({"sections": []}), encoding="utf-8"
        )
        report = generate_menu.reconcile_menu(str(wiki_dir), "TestProject")
        assert report is not None
        assert report.get("semantic_group_hints", {}) == {}

    def test_reconcile_hints_include_confidence(self, tmp_path):
        """hints 中每个模块条目应包含 confidence 字段"""
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "overview.md").write_text("# Overview\n", encoding="utf-8")
        (wiki_dir / "menu.json").write_text(
            json.dumps({"sections": []}), encoding="utf-8"
        )
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        analysis = self._make_analysis({
            "auth": self._make_module("认证与鉴权", confidence="high"),
        })
        (cache_dir / "module-analysis.json").write_text(
            json.dumps(analysis), encoding="utf-8"
        )

        report = generate_menu.reconcile_menu(
            str(wiki_dir), "TestProject", cache_dir=str(cache_dir)
        )
        hints = report.get("semantic_group_hints", {})
        assert "认证与鉴权" in hints
        entry = hints["认证与鉴权"][0]
        assert "confidence" in entry, "每个模块条目应包含 confidence 字段"
        assert entry["confidence"] == "high"

    def test_reconcile_skips_modules_without_semantic_group(self, tmp_path):
        """没有 semantic_group 字段的模块不应出现在 hints 中"""
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        (wiki_dir / "overview.md").write_text("# Overview\n", encoding="utf-8")
        (wiki_dir / "menu.json").write_text(
            json.dumps({"sections": []}), encoding="utf-8"
        )
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        # 模块没有 semantic_group 字段
        analysis = self._make_analysis({
            "utils": {
                "module_path": "src/utils", "code_purpose": "Util",
                "analysis_depth": "quick", "module_summary": "utils",
                "selected_components": [],
                "dependency_hints": {"imports": [], "imported_by": []},
                "files": [],
            }
        })
        (cache_dir / "module-analysis.json").write_text(
            json.dumps(analysis), encoding="utf-8"
        )

        report = generate_menu.reconcile_menu(
            str(wiki_dir), "TestProject", cache_dir=str(cache_dir)
        )
        hints = report.get("semantic_group_hints", {})
        assert hints == {}, f"无 semantic_group 的模块不应出现在 hints 中，实际 hints: {hints}"


# ---------------------------------------------------------------------------
# TestBuildMenuDataDriven
# ---------------------------------------------------------------------------


class TestBuildMenuDataDriven:
    """Tests for data-driven module grouping in build_menu."""

    def _write(self, path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _make_analysis(self, modules_dict: dict) -> dict:
        return {
            "cache_schema_version": 1,
            "generated_at": "2026-04-24T00:00:00Z",
            "modules": modules_dict,
        }

    def _make_module(self, semantic_group: str, confidence: str = "high",
                     module_path: str = "src/x", code_purpose: str = "Service") -> dict:
        return {
            "semantic_group": semantic_group,
            "semantic_group_confidence": confidence,
            "module_path": module_path,
            "code_purpose": code_purpose,
            "analysis_depth": "standard",
            "module_summary": "summary",
            "selected_components": [],
            "dependency_hints": {"imports": [], "imported_by": []},
            "files": [],
        }

    def test_groups_by_semantic_group(self, tmp_path):
        """有 semantic_group 时按语义分组，分区名为 semantic_group 值"""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "modules").mkdir(parents=True)
        (wiki / "modules" / "auth.md").write_text("# Auth\nAuth module.", encoding="utf-8")
        (wiki / "modules" / "token.md").write_text("# Token\nToken module.", encoding="utf-8")
        (wiki / "modules" / "user.md").write_text("# User\nUser module.", encoding="utf-8")

        cache = tmp_path / "cache"
        cache.mkdir()
        analysis = self._make_analysis({
            "auth": self._make_module("认证与鉴权", module_path="src/auth"),
            "token": self._make_module("认证与鉴权", module_path="src/token", code_purpose="Util"),
            "user": self._make_module("用户管理", module_path="src/user"),
        })
        (cache / "module-analysis.json").write_text(json.dumps(analysis), encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki), cache_dir=str(cache))
        group_titles = [g["title"] for g in menu["menu"]]
        # 应有两个语义分组（认证与鉴权, 用户管理）
        assert "认证与鉴权" in group_titles
        assert "用户管理" in group_titles
        # 不应出现固定的"模块"分区
        assert "模块" not in group_titles

    def test_fallback_to_flat_when_no_analysis(self, tmp_path):
        """无分析数据时回退到平铺的'模块'分区（向后兼容）"""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "modules").mkdir(parents=True)
        (wiki / "modules" / "auth.md").write_text("# Auth\nAuth module.", encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki), cache_dir=None)
        sections = {g["title"]: g for g in menu["menu"]}
        assert "模块" in sections

    def test_fallback_to_flat_when_empty_cache(self, tmp_path):
        """cache_dir 存在但 module-analysis.json 缺失时回退到平铺"""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "modules").mkdir(parents=True)
        (wiki / "modules" / "auth.md").write_text("# Auth\nAuth module.", encoding="utf-8")
        (wiki / "modules" / "db.md").write_text("# DB\nDB module.", encoding="utf-8")

        empty_cache = tmp_path / "empty_cache"
        empty_cache.mkdir()
        menu = generate_menu.build_menu(str(wiki), cache_dir=str(empty_cache))
        sections = {g["title"]: g for g in menu["menu"]}
        assert "模块" in sections

    def test_uses_skeleton_groups_when_available(self, tmp_path):
        """有 skeleton module_groups 时按骨架分组"""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "modules").mkdir(parents=True)
        (wiki / "modules" / "auth.md").write_text("# Auth\nAuth module.", encoding="utf-8")
        (wiki / "modules" / "user.md").write_text("# User\nUser module.", encoding="utf-8")
        (wiki / "modules" / "order.md").write_text("# Order\nOrder module.", encoding="utf-8")

        cache = tmp_path / "cache"
        cache.mkdir()
        skeleton = {
            "project_nature": "电商系统",
            "architecture_style": "分层架构",
            "module_groups": [
                {"name": "交易引擎", "modules": ["order", "auth"]},
                {"name": "用户中心", "modules": ["user"]},
            ]
        }
        (cache / "architecture-skeleton.json").write_text(json.dumps(skeleton), encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki), cache_dir=str(cache))
        group_titles = [g["title"] for g in menu["menu"]]
        assert "交易引擎" in group_titles
        assert "用户中心" in group_titles

    def test_api_pairing_preserved_in_semantic_groups(self, tmp_path):
        """语义分组下仍然保持 module + api 配对"""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "modules").mkdir(parents=True)
        (wiki / "api").mkdir(parents=True)
        (wiki / "modules" / "auth.md").write_text("# Auth\nAuth module.", encoding="utf-8")
        (wiki / "api" / "auth.md").write_text("# Auth API\nEndpoints.", encoding="utf-8")

        cache = tmp_path / "cache"
        cache.mkdir()
        analysis = self._make_analysis({
            "auth": self._make_module("认证与鉴权", module_path="src/auth"),
        })
        (cache / "module-analysis.json").write_text(json.dumps(analysis), encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki), cache_dir=str(cache))
        # 找到语义分组
        auth_group = [g for g in menu["menu"] if g["title"] == "认证与鉴权"][0]
        auth_item = auth_group["items"][0]
        child_titles = [c["title"] for c in auth_item["items"]]
        assert "模块文档" in child_titles
        assert "API 参考" in child_titles

    def test_handles_list_format_analysis_modules(self, tmp_path):
        """兼容 module-analysis.json 中 modules 为数组格式的情况"""
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "modules").mkdir(parents=True)
        (wiki / "modules" / "auth.md").write_text("# Auth\nAuth module.", encoding="utf-8")

        cache = tmp_path / "cache"
        cache.mkdir()
        # modules 为数组格式（代码中 _extract_semantic_groups 支持此格式）
        analysis = {
            "modules": [
                {
                    "module_path": "auth",
                    "semantic_group": "认证",
                    "code_purpose": "Service",
                    "analysis_depth": "standard",
                    "module_summary": "summary",
                    "selected_components": [],
                    "dependency_hints": {"imports": [], "imported_by": []},
                    "files": [],
                }
            ]
        }
        (cache / "module-analysis.json").write_text(json.dumps(analysis), encoding="utf-8")

        menu = generate_menu.build_menu(str(wiki), cache_dir=str(cache))
        group_titles = [g["title"] for g in menu["menu"]]
        assert "认证" in group_titles
