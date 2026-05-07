"""Final Markdown quality checks for agentic DeepWiki output."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


MERMAID_RE = re.compile(r"```mermaid\s*\n[\s\S]*?```", re.MULTILINE)
SOURCE_LINK_RE = re.compile(r"file:///[^)\s#]+(?:#L\d+(?:-L?\d+)?)?")
SOURCE_LINK_WITH_LINES_RE = re.compile(r"file:///[^)\s#]+#L\d+(?:-L?\d+)?")
TOP_SOURCE_RE = re.compile(
    r"\A\s*#\s+[^\n]+\n+(?:[ \t]*\n)*<details\s+open[^>]*>\s*(?:\n\s*)?<summary>\s*(?:Relevant source files|相关源文件)\s*</summary>",
    re.IGNORECASE,
)


def _resolve_wiki_dir(project_path: str | Path) -> Path:
    root = Path(project_path)
    if root.name == "wiki":
        return root
    deepwiki_wiki = root / ".deepwiki" / "wiki"
    if deepwiki_wiki.exists():
        return deepwiki_wiki
    if (root / "wiki").exists():
        return root / "wiki"
    return root


def _has_mermaid_preface(content: str, match: re.Match[str]) -> bool:
    before = content[: match.start()].rstrip()
    if not before:
        return False
    previous_block = before.split("\n\n")[-1].strip()
    if not previous_block or previous_block.startswith("#") or previous_block.startswith("```"):
        return False
    return bool(re.search(r"diagram|图|流程|关系|展示|shows?|illustrates?", previous_block, re.IGNORECASE))


def analyze_document(path: Path) -> Dict[str, Any]:
    content = path.read_text(encoding="utf-8", errors="replace")
    issues: List[str] = []
    warnings: List[str] = []
    h2_count = len(re.findall(r"^##\s+", content, re.MULTILINE))
    mermaid_blocks = list(MERMAID_RE.finditer(content))
    source_links = SOURCE_LINK_RE.findall(content)
    source_links_with_lines = SOURCE_LINK_WITH_LINES_RE.findall(content)

    if not re.search(r"\A\s*#\s+", content):
        issues.append("Document must start with an H1 title.")
    if not TOP_SOURCE_RE.search(content):
        issues.append("H1 must be followed by an open Relevant source files/相关源文件 block.")
    if h2_count < 1:
        warnings.append("Document should include at least one H2 section.")
    if not source_links:
        issues.append("Document must include file:/// source tracing links.")
    if len(source_links_with_lines) != len(source_links):
        issues.append("All file:/// source links must include #L line ranges.")
    for block in mermaid_blocks:
        if not _has_mermaid_preface(content, block):
            issues.append("Every Mermaid diagram must have a short explanatory paragraph before it.")
            break
    if not mermaid_blocks and "|" not in content:
        warnings.append("Document should include a Mermaid diagram or a structured table.")

    score = 100 - len(issues) * 30 - len(warnings) * 10
    quality_level = "professional" if score >= 85 else "standard" if score >= 60 else "basic"
    return {
        "file_path": str(path),
        "line_count": len(content.splitlines()),
        "section_count": h2_count,
        "diagram_count": len(mermaid_blocks),
        "source_link_count": len(source_links),
        "source_link_with_lines_count": len(source_links_with_lines),
        "quality_level": quality_level,
        "issues": issues,
        "warnings": warnings,
    }


def check_doc_quality(project_path: str | Path) -> Dict[str, Any]:
    wiki_dir = _resolve_wiki_dir(project_path)
    docs = [analyze_document(path) for path in sorted(wiki_dir.rglob("*.md")) if path.name != "doc-map.md"]
    issues = [issue for doc in docs for issue in doc["issues"]]
    return {
        "ok": not issues,
        "wiki_path": str(wiki_dir),
        "total_docs": len(docs),
        "docs": docs,
        "summary_issues": issues,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check DeepWiki Markdown quality")
    parser.add_argument("project_path")
    args = parser.parse_args(argv)
    report = check_doc_quality(args.project_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
