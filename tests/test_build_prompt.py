"""Tests for subagent prompt generation."""

import json

from scripts.subagent.build_prompt import _build_extract_docs_vars


def test_extract_docs_prompt_uses_module_groups_from_skeleton(tmp_path):
    """extract-docs prompts should consume architecture-skeleton.module_groups."""
    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    (cache / "architecture-skeleton.json").write_text(
        json.dumps(
            {
                "project_nature": "Python CLI tool",
                "architecture_style": "layered",
                "module_groups": [
                    {
                        "name": "runtime",
                        "modules": ["src/app"],
                        "role": "启动和调度",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    variables = _build_extract_docs_vars(tmp_path, "src/app")

    assert "runtime" in variables["GROUPS_BLOCK"]
    assert "src/app" in variables["GROUPS_BLOCK"]
    assert variables["CURRENT_MODULE_GROUP_NAME"] == "runtime"
