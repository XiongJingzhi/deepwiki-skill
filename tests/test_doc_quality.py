from scripts.quality.doc_quality import check_doc_quality


GOOD_DOC = """# Runtime
<details open>
<summary>Relevant source files</summary>

- src/
  - [app.py](file:///src/app.py#L1-L3) `L1-L3` - runtime entry

</details>

## Overview

This page explains why the runtime exists and how it works.

The diagram below shows the runtime flow from request to output.

```mermaid
flowchart TD
  A["Request"] --> B["Runtime"]
```

**Source:** [app.py](file:///src/app.py#L1-L3)
"""


def test_doc_quality_accepts_document_with_source_and_diagram(tmp_path):
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "runtime.md").write_text(GOOD_DOC, encoding="utf-8")

    report = check_doc_quality(tmp_path)

    assert report["ok"] is True
    assert report["docs"][0]["quality_level"] in {"standard", "professional"}


def test_doc_quality_rejects_missing_top_source_block(tmp_path):
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "runtime.md").write_text("# Runtime\n\n## Overview\n\nNo sources.\n", encoding="utf-8")

    report = check_doc_quality(tmp_path)

    assert report["ok"] is False
    assert any("Relevant source files" in issue for issue in report["docs"][0]["issues"])


def test_doc_quality_rejects_mermaid_without_preface(tmp_path):
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)
    doc = GOOD_DOC.replace("The diagram below shows the runtime flow from request to output.\n\n", "")
    (wiki / "runtime.md").write_text(doc, encoding="utf-8")

    report = check_doc_quality(tmp_path)

    assert report["ok"] is False
    assert any("Mermaid" in issue for issue in report["docs"][0]["issues"])
