from scripts.wiki.mermaid import extract_mermaid_blocks, fix_mermaid_text, process_mermaid


def test_fix_mermaid_quotes_flowchart_labels():
    fixed, fixes = fix_mermaid_text("flowchart TD\n  A[数据处理] -->|error handler| B[Done]\n")

    assert fixes >= 2
    assert 'A["数据处理"]' in fixed
    assert '-->|"error handler"|' in fixed


def test_process_mermaid_repairs_markdown_file(tmp_path):
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)
    page = wiki / "overview.md"
    page.write_text("# Overview\n\n```mermaid\nflowchart TD\n  A[数据处理]\n```\n", encoding="utf-8")

    report = process_mermaid(tmp_path, dry_run=False, validate=False)

    assert report["files_checked"] == 1
    assert report["fixes"] >= 1
    assert 'A["数据处理"]' in page.read_text(encoding="utf-8")


def test_extract_mermaid_blocks():
    blocks = extract_mermaid_blocks("```mermaid\nflowchart TD\n  A-->B\n```\n")

    assert blocks[0]["diagram_type"] == "flowchart"
    assert blocks[0]["text"].startswith("flowchart TD")
