"""Tests for tree-sitter parser manager."""

import sys
from pathlib import Path



def test_get_lang_for_ext_is_case_insensitive():
    from scripts.core import parsers

    manager = parsers.ParserManager()

    assert manager.get_lang_for_ext(".PY") == "python"
    assert manager.get_lang_for_ext(".tsx") == "tsx"
    assert manager.get_lang_for_ext(".unknown") is None


def test_parser_and_query_are_cached():
    from scripts.core import parsers

    manager = parsers.ParserManager()

    assert manager.get_parser("python") is manager.get_parser("python")
    assert manager.get_query("python", "func_class") is manager.get_query(
        "python", "func_class"
    )


def test_parse_file_returns_tree_and_source_for_python(tmp_path):
    from scripts.core import parsers

    source_path = tmp_path / "app.py"
    source_path.write_text("def main():\n    return 42\n", encoding="utf-8")

    parsed = parsers.ParserManager().parse_file(source_path)

    assert parsed is not None
    tree, source = parsed
    assert tree.root_node.type == "module"
    assert b"def main" in source

