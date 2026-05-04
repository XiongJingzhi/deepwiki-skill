"""Tests for subagent prompt generation."""

import json
from pathlib import Path

import pytest

from scripts.subagent import build_prompt
from scripts.subagent.build_prompt import (
    _build_extract_docs_vars,
    _build_generate_docs_vars,
    _build_quality_fix_vars,
    _build_snippets_hint,
    _source_link,
)


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
    context_path = cache / "modules" / "src_app" / "context.json"
    context_path.parent.mkdir(parents=True)
    context_path.write_text("{}", encoding="utf-8")

    variables = _build_extract_docs_vars(tmp_path, "src/app")

    assert "runtime" in variables["GROUPS_BLOCK"]
    assert "src/app" in variables["GROUPS_BLOCK"]
    assert variables["CURRENT_MODULE_GROUP_NAME"] == "runtime"
    assert variables["MODULE_PATH"] == "src/app"
    assert variables["MODULE_CONTEXT_PATH"].endswith(
        ".deepwiki/cache/modules/src_app/context.json"
    )
    assert variables["MODULE_ANALYSIS_PART_PATH"].endswith(
        ".deepwiki/cache/module-analysis.src_app.json"
    )


def test_extract_docs_prompt_requires_module_path():
    """extract-docs prompts are per-module and should not be built generically."""
    with pytest.raises(ValueError, match="module path"):
        _build_extract_docs_vars(Path("/tmp"), None)


def test_extract_docs_prompt_requires_prepared_context(tmp_path):
    """extract-docs should fail before dispatch if module context is missing."""
    with pytest.raises(ValueError, match="context\\.json"):
        _build_extract_docs_vars(tmp_path, "src/app")


def test_generate_module_docs_prompt_includes_page_and_output_path(tmp_path):
    """generate-module-docs prompts should tell subagents where to write."""
    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    (cache / "generation-plan.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": "deep-dive:auth",
                        "output_path": "wiki/deep-dive/auth.md",
                        "affected_modules": ["src/auth"],
                        "source_files": [{"path": "src/auth/service.py", "ranges": []}],
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
                    "src/auth": {
                        "semantic_group": "认证",
                        "code_purpose": "Service",
                        "selected_components": ["source_index"],
                        "files": [{"path": "src/auth/service.py", "summary": "认证服务"}],
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    variables = _build_generate_docs_vars(tmp_path, "deep-dive:auth")

    assert variables["PAGE_ID"] == "deep-dive:auth"
    assert variables["OUTPUT_PATH"] == "wiki/deep-dive/auth.md"
    assert variables["OUTPUT_ABS_PATH"].endswith(".deepwiki/wiki/deep-dive/auth.md")


def test_generate_module_docs_prompt_uses_safe_snippet_filename(tmp_path):
    """Prompt generation should find snippets written by extract_source_snippets."""
    cache = tmp_path / ".deepwiki" / "cache"
    snippets = cache / "snippets"
    snippets.mkdir(parents=True)
    safe_path = snippets / "deep-dive_pkg_auth.json"
    safe_path.write_text('{"snippets": []}', encoding="utf-8")

    hint = _build_snippets_hint(cache, "deep-dive:pkg/auth")

    assert str(safe_path) in hint
    assert "已预提取" in hint


def test_source_link_uses_standard_file_uri_for_absolute_paths(tmp_path):
    """file:// links should be valid URIs, including paths with spaces."""
    project = tmp_path / "project with space"
    source = project / "src" / "main.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('hello')\n", encoding="utf-8")

    link = _source_link(project, "src/main.py", 1, 1)

    assert link.startswith("file:///")
    assert " " not in link
    assert "%20" in link
    assert "////" not in link.replace("file:///", "", 1)


def test_generate_module_docs_prompt_requires_planned_page(tmp_path):
    """Unknown pages should fail before a subagent guesses an output path."""
    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    (cache / "generation-plan.json").write_text(
        json.dumps({"pages": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="page_id"):
        _build_generate_docs_vars(tmp_path, "deep-dive:missing")


def test_generate_module_docs_prompt_rejects_non_module_page(tmp_path):
    """Overview/concept pages need their own workflow, not module-docs prompts."""
    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    (cache / "generation-plan.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": "overview",
                        "output_path": "wiki/overview.md",
                        "affected_modules": [],
                        "source_files": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="no affected modules"):
        _build_generate_docs_vars(tmp_path, "overview")


def test_cli_rejects_extract_docs_prompt_without_module(tmp_path, capsys):
    """The CLI should fail early before producing an ambiguous extract-docs prompt."""
    with pytest.raises(SystemExit) as exc:
        build_prompt.main(["extract-docs", "--project", str(tmp_path)])

    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert "--module" in captured.err


def test_cache_prompt_records_manifest_entry(tmp_path, capsys):
    """Cached prompts should become explicit dispatch artifacts."""
    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    (cache / "generation-plan.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": "deep-dive:auth",
                        "output_path": "wiki/deep-dive/auth.md",
                        "affected_modules": ["src/auth"],
                        "source_files": [{"path": "src/auth/service.py", "ranges": []}],
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
                    "src/auth": {
                        "semantic_group": "认证",
                        "code_purpose": "Service",
                        "selected_components": ["source_index"],
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    build_prompt.main(
        [
            "generate-module-docs",
            "--project",
            str(tmp_path),
            "--page",
            "deep-dive:auth",
            "--cache",
        ]
    )
    prompt_path = Path(capsys.readouterr().out.strip())
    manifest = json.loads((cache / "prompts" / "manifest.json").read_text(encoding="utf-8"))

    entry = manifest["prompts"]["generate-module-docs"]["deep-dive:auth"]
    assert prompt_path == tmp_path / entry["prompt_path"]
    assert entry["agent_type"] == "generate-module-docs"
    assert entry["id"] == "deep-dive:auth"
    assert entry["safe_id"] == "deep-dive_auth"
    assert entry["source"] == "scripts/subagent/build_prompt.py"


def test_cache_prompt_manifest_records_extract_docs_and_quality_fix(tmp_path, capsys):
    """All subagent prompt types should be visible to the dispatcher."""
    context_path = tmp_path / ".deepwiki" / "cache" / "modules" / "src_app" / "context.json"
    context_path.parent.mkdir(parents=True)
    context_path.write_text("{}", encoding="utf-8")

    build_prompt.main(
        [
            "extract-docs",
            "--project",
            str(tmp_path),
            "--module",
            "src/app",
            "--cache",
        ]
    )
    build_prompt.main(
        [
            "quality-fix",
            "--project",
            str(tmp_path),
            "--page",
            "deep-dive/auth.md",
            "--cache",
        ]
    )
    capsys.readouterr()

    manifest = json.loads(
        (tmp_path / ".deepwiki" / "cache" / "prompts" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )

    extract_entry = manifest["prompts"]["extract-docs"]["src/app"]
    quality_entry = manifest["prompts"]["quality-fix"]["deep-dive/auth.md"]
    assert extract_entry["safe_id"] == "src_app"
    assert extract_entry["prompt_path"].endswith("extract-docs_src_app.md")
    assert quality_entry["safe_id"] == "deep-dive_auth_md"
    assert quality_entry["prompt_path"].endswith("quality-fix_deep-dive_auth_md.md")


def test_quality_fix_prompt_can_target_one_page(tmp_path):
    """quality-fix prompts should carry a single target page when provided."""
    variables = _build_quality_fix_vars(tmp_path, "deep-dive/auth.md")

    assert variables["TARGET_WIKI_PATH"] == "deep-dive/auth.md"
    assert "page-context" in variables["PAGE_CONTEXT_COMMAND"]
    assert "deep-dive/auth.md" in variables["PAGE_CONTEXT_COMMAND"]
    assert variables["QUALITY_COMMAND"].endswith("/.deepwiki --verbose")
