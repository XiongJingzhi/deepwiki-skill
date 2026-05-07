import json

from scripts.pipeline.page_context import build_page_context


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
                "purpose": "Introduce the project.",
                "source_targets": ["README.md"],
                "depends_on": [],
                "status": "planned",
            },
            {
                "page_id": "runtime",
                "title": "Runtime",
                "output_path": "deep-dive/runtime.md",
                "page_type": "deep-dive",
                "purpose": "Explain runtime.",
                "source_targets": ["src/app.py"],
                "depends_on": ["overview"],
                "status": "planned",
            },
        ],
        "generation_order": ["overview", "runtime"],
    }
    (cache / "page-plan.json").write_text(json.dumps(plan), encoding="utf-8")


def test_build_page_context_reads_sources_and_writes_cache(tmp_path):
    write_plan(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "README.md").write_text("# Sample\n\nProject intro\n", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")

    context = build_page_context(tmp_path, "runtime", max_excerpt_chars=12, save_to_cache=True)

    assert context["page_id"] == "runtime"
    assert context["objective"] == "Explain runtime."
    assert context["source_files"] == [{"path": "src/app.py", "reason": "listed in page source_targets"}]
    assert context["source_excerpts"][0]["path"] == "src/app.py"
    assert len(context["source_excerpts"][0]["text"]) <= 12
    assert set(context["related_pages"]) == {"overview"}

    output = tmp_path / ".deepwiki" / "cache" / "page-context" / "runtime.json"
    assert output.exists()


def test_build_page_context_includes_reverse_dependencies(tmp_path):
    write_plan(tmp_path)
    (tmp_path / "README.md").write_text("# Sample\n", encoding="utf-8")

    context = build_page_context(tmp_path, "overview")

    assert "runtime" in context["related_pages"]
