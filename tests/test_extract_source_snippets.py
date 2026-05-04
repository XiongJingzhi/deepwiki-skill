"""Tests for source snippet cache generation."""

import json

from scripts.pipeline.extract_source_snippets import extract_all_snippets


def test_extract_all_snippets_removes_orphan_snippet_files(tmp_path):
    """Snippet files for pages no longer in generation-plan should be deleted."""
    cache = tmp_path / ".deepwiki" / "cache"
    snippets = cache / "snippets"
    snippets.mkdir(parents=True)
    (snippets / "deep-dive_old.json").write_text("{}", encoding="utf-8")
    (tmp_path / "src.py").write_text("line1\nline2\n", encoding="utf-8")
    (cache / "generation-plan.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": "deep-dive:new",
                        "source_files": [
                            {
                                "path": "src.py",
                                "ranges": [{"start_line": 1, "end_line": 1}],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    extract_all_snippets(tmp_path)

    assert not (snippets / "deep-dive_old.json").exists()
    assert (snippets / "deep-dive_new.json").exists()


def test_extract_all_snippets_uses_prompt_safe_id_for_dotted_page_ids(tmp_path):
    """Snippet and prompt builders should agree on safe page IDs."""
    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    source = tmp_path / "src" / "auth.py"
    source.parent.mkdir()
    source.write_text("def login():\n    return True\n", encoding="utf-8")
    (cache / "generation-plan.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": "deep-dive:auth.v2",
                        "source_files": [
                            {"path": "src/auth.py", "ranges": [{"start_line": 1, "end_line": 2}]}
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    extract_all_snippets(tmp_path)

    assert (cache / "snippets" / "deep-dive_auth_v2.json").exists()


def test_extract_all_snippets_removes_stale_page_file_when_ranges_empty(tmp_path):
    """If a current page no longer yields snippets, its old snippet file is removed."""
    cache = tmp_path / ".deepwiki" / "cache"
    snippets = cache / "snippets"
    snippets.mkdir(parents=True)
    stale = snippets / "deep-dive_auth.json"
    stale.write_text('{"snippets": [{"path": "old.py"}]}', encoding="utf-8")
    (cache / "generation-plan.json").write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "page_id": "deep-dive:auth",
                        "source_files": [{"path": "src.py", "ranges": []}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = extract_all_snippets(tmp_path)

    assert result == {}
    assert not stale.exists()
