from scripts.pipeline.validate_page_plan import validate_page_plan


def valid_plan():
    return {
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
                "purpose": "Explain runtime flow.",
                "source_targets": ["src/app.py"],
                "depends_on": ["overview"],
                "status": "planned",
            },
        ],
        "generation_order": ["overview", "runtime"],
    }


def test_valid_page_plan_passes():
    result = validate_page_plan(valid_plan())

    assert result == {"ok": True, "errors": []}


def test_duplicate_page_id_fails():
    plan = valid_plan()
    plan["pages"][1]["page_id"] = "overview"

    result = validate_page_plan(plan)

    assert result["ok"] is False
    assert any("duplicate page_id" in error for error in result["errors"])


def test_duplicate_output_path_fails():
    plan = valid_plan()
    plan["pages"][1]["output_path"] = "overview.md"

    result = validate_page_plan(plan)

    assert result["ok"] is False
    assert any("duplicate output_path" in error for error in result["errors"])


def test_generation_order_missing_page_fails():
    plan = valid_plan()
    plan["generation_order"] = ["overview"]

    result = validate_page_plan(plan)

    assert result["ok"] is False
    assert any("generation_order" in error for error in result["errors"])


def test_unsafe_output_path_fails():
    for output_path in ("/tmp/page.md", "../page.md", "page.txt"):
        plan = valid_plan()
        plan["pages"][0]["output_path"] = output_path

        result = validate_page_plan(plan)

        assert result["ok"] is False
        assert any("output_path" in error for error in result["errors"])
