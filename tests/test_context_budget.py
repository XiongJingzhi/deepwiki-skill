"""Tests for context budget calculations."""

import sys
from pathlib import Path



def test_estimate_token_cost_uses_language_ratio(tmp_path):
    from scripts.analysis import context_budget

    py_file = tmp_path / "small.py"
    py_file.write_text("x" * 800, encoding="utf-8")

    assert context_budget.estimate_token_cost(py_file) == 200


def test_compute_context_budget_reserves_generation_and_prioritizes_files(tmp_path):
    from scripts.analysis import context_budget

    src = tmp_path / "src"
    src.mkdir()
    (src / "core.py").write_text("x" * 2000, encoding="utf-8")
    (src / "feature.py").write_text("x" * 1600, encoding="utf-8")
    (src / "notes.md").write_text("x" * 4000, encoding="utf-8")

    files = [
        {
            "path": "src/core.py",
            "importance_score": 0.9,
            "is_core": True,
            "is_high_priority": True,
        },
        {
            "path": "src/feature.py",
            "importance_score": 0.8,
            "is_core": False,
            "is_high_priority": True,
        },
        {
            "path": "src/notes.md",
            "importance_score": 1.0,
            "is_core": False,
            "is_high_priority": True,
        },
    ]

    budget = context_budget.compute_context_budget(files, tmp_path)

    assert budget["total_budget"] == 50_000
    assert budget["reserved_for_generation"] == 16_500
    assert budget["available_for_analysis"] == 33_500
    assert budget["quick_scan"]["file_count"] == 1
    assert budget["deep_analysis"]["files"] == ["src/notes.md", "src/feature.py"]
