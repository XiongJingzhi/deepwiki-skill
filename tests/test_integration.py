import json

from scripts.pipeline.prepare_inventory import prepare_inventory
from scripts.pipeline.validate_page_plan import validate_page_plan
from scripts.wiki.finalize import finalize_wiki
from scripts.wiki.generate_menu import generate_menu
from scripts.wiki.init_wiki import init_wiki


def test_agentic_smoke_flow(tmp_path):
    (tmp_path / "README.md").write_text("# Sample\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")

    assert init_wiki(tmp_path)["success"] is True
    inventory = prepare_inventory(tmp_path, save_to_cache=True)
    assert inventory["stats"]["total_files"] == 2

    cache = tmp_path / ".deepwiki" / "cache"
    (cache / "semantic-analysis.json").write_text(
        json.dumps(
            {
                "cache_schema_version": 1,
                "generated_at": "2026-05-08T00:00:00+00:00",
                "project_purpose": "Sample project.",
                "architecture_model": {"summary": "Single runtime module."},
                "runtime_flows": [],
                "concepts": [],
                "modules": [],
                "cross_cutting_concerns": [],
                "risks": [],
                "extension_points": [],
                "source_evidence": [{"path": "README.md", "reason": "fixture"}],
                "confidence": "high",
                "open_questions": [],
            }
        ),
        encoding="utf-8",
    )
    plan = {
        "pages": [
            {
                "page_id": "overview",
                "title": "Overview",
                "output_path": "overview.md",
                "page_type": "overview",
                "purpose": "Introduce the sample.",
                "source_targets": ["README.md"],
                "depends_on": [],
                "status": "planned",
            }
        ],
        "generation_order": ["overview"],
        "menu_seed": [{"title": "Start", "page_ids": ["overview"]}],
    }
    (cache / "page-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    assert validate_page_plan(plan)["ok"] is True

    wiki = tmp_path / ".deepwiki" / "wiki"
    (wiki / "overview.md").write_text(
        "# Overview\n"
        "<details open>\n"
        "<summary>Relevant source files</summary>\n\n"
        "- [README.md](file:///README.md#L1-L1) `L1-L1` - project introduction\n\n"
        "</details>\n\n"
        "## Overview\n\n"
        "See [source](../../README.md).\n",
        encoding="utf-8",
    )
    generate_menu(tmp_path, "Sample")

    assert finalize_wiki(tmp_path) == 0
