"""Tests for shared module-analysis merge helpers."""

import json

from scripts.core.common import CACHE_SCHEMA_VERSION, merge_module_analysis_parts


def test_merge_module_analysis_parts_returns_module_analysis_envelope(tmp_path):
    """Subagent part files should merge into the schema validate-analysis reads."""
    part_a = tmp_path / "module-analysis.auth.json"
    part_b = tmp_path / "module-analysis.api.json"
    part_a.write_text(json.dumps({"auth": {"module_summary": "Auth"}}), encoding="utf-8")
    part_b.write_text(json.dumps({"api": {"module_summary": "API"}}), encoding="utf-8")

    merged = merge_module_analysis_parts(tmp_path, [part_a, part_b])

    assert merged["cache_schema_version"] == CACHE_SCHEMA_VERSION
    assert set(merged["modules"]) == {"auth", "api"}
