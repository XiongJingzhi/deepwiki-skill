"""Tests for page_context.py."""

import json

from scripts.pipeline.page_context import get_page_context


def test_page_context_prefers_generation_plan_output_mapping(tmp_path):
    """Wiki paths should map through generation-plan output_path before stem guessing."""
    deepwiki = tmp_path / ".deepwiki"
    cache = deepwiki / "cache"
    wiki = deepwiki / "wiki"
    cache.mkdir(parents=True)
    (wiki / "deep-dive").mkdir(parents=True)
    (wiki / "deep-dive" / "login-flow.md").write_text("# Login\n", encoding="utf-8")
    (wiki / "menu.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "title": "深入理解",
                        "items": [
                            {
                                "title": "登录流程",
                                "path": "deep-dive/login-flow.md",
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (cache / "generation-plan.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": "deep-dive:auth-service",
                        "output_path": "wiki/deep-dive/login-flow.md",
                        "affected_modules": ["src/auth/service"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (cache / "module-analysis.json").write_text(
        json.dumps(
            {
                "modules": {
                    "src/auth/service": {
                        "module_summary": "Auth service",
                        "module_role": "Handles login",
                        "semantic_group": "认证",
                        "files": [
                            {
                                "path": "src/auth/service.py",
                                "summary": "Login service",
                                "key_insights": ["Owns login flow"],
                            }
                        ],
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    ctx = get_page_context(tmp_path, "deep-dive/login-flow.md")

    assert ctx["module_key"] == "src/auth/service"
    assert ctx["module_summary"] == "Auth service"
    assert not any("Could not match" in error for error in ctx["errors"])
