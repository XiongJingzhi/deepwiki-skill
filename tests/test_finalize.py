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
    (wiki / "overview.md").write_text(
        "# Overview\n"
        "<details open>\n"
        "<summary>Relevant source files</summary>\n\n"
        "- [README.md](file:///README.md#L1-L1) `L1-L1` - source\n\n"
        "</details>\n\n"
        "## Overview\n\n"
        "See [source](../../README.md).\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Source\n", encoding="utf-8")

    assert finalize_wiki(tmp_path) == 0


def test_finalize_reports_broken_local_markdown_links(tmp_path):
    write_plan(tmp_path)
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "overview.md").write_text("# Overview\n\nSee [missing](missing.md).\n", encoding="utf-8")

    assert finalize_wiki(tmp_path) == 1


def test_finalize_runs_doc_quality(tmp_path):
    write_plan(tmp_path)
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "overview.md").write_text("# Overview\n\nNo source tracing.\n", encoding="utf-8")

    assert finalize_wiki(tmp_path) == 1


def test_finalize_repairs_mermaid(tmp_path):
    write_plan(tmp_path)
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)
    (tmp_path / "README.md").write_text("# Source\n", encoding="utf-8")
    (wiki / "overview.md").write_text(
        "# Overview\n"
        "<details open>\n"
        "<summary>Relevant source files</summary>\n\n"
        "- [README.md](file:///README.md#L1-L1) `L1-L1` - source\n\n"
        "</details>\n\n"
        "## Overview\n\n"
        "The diagram below shows the runtime flow.\n\n"
        "```mermaid\nflowchart TD\n  A[数据处理]\n```\n",
        encoding="utf-8",
    )

    assert finalize_wiki(tmp_path) == 0
    assert 'A["数据处理"]' in (wiki / "overview.md").read_text(encoding="utf-8")
