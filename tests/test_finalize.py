import json

from scripts.wiki.finalize import finalize_wiki


def write_plan(project_path):
    cache = project_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    plan = {
        "pages": [
            {
                "page_id": "overview",
                "title": "Overview",
                "output_path": "overview.md",
                "page_type": "overview",
                "status": "planned",
            }
        ],
        "menu_seed": [{"title": "Start", "page_ids": ["overview"]}],
    }
    (cache / "page-plan.json").write_text(json.dumps(plan), encoding="utf-8")


def test_finalize_fails_when_planned_page_missing(tmp_path):
    write_plan(tmp_path)
    (tmp_path / ".deepwiki" / "wiki").mkdir(parents=True)

    assert finalize_wiki(tmp_path) == 1


def test_finalize_passes_when_pages_exist(tmp_path):
    write_plan(tmp_path)
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "overview.md").write_text("# Overview\n\nSee [source](../../README.md).\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Source\n", encoding="utf-8")

    assert finalize_wiki(tmp_path) == 0


def test_finalize_reports_broken_local_markdown_links(tmp_path):
    write_plan(tmp_path)
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "overview.md").write_text("# Overview\n\nSee [missing](missing.md).\n", encoding="utf-8")

    assert finalize_wiki(tmp_path) == 1
