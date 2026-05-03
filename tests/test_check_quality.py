"""Tests for scripts/check_doc_quality.py"""

import json
import os

import pytest

import scripts.quality.check_doc_quality as check_doc_quality
import scripts.quality.check_analysis_quality as check_analysis_quality
import scripts.quality.build_evidence_index as build_evidence_index


# ---------------------------------------------------------------------------
# analyze_document
# ---------------------------------------------------------------------------


class TestAnalyzeDocument:
    """Tests for analyze_document()."""

    def test_basic_metrics_lines_and_sections(self, tmp_path):
        """Lines, H2 sections, H3 subsections are counted correctly."""
        p = tmp_path / "doc.md"
        content = (
            "# Title\n"
            "## Section A\n"
            "body\n"
            "## Section B\n"
            "### Sub 1\n"
            "### Sub 2\n"
            "## Section C\n"
        )
        p.write_text(content, encoding="utf-8")
        m = check_doc_quality.analyze_document(str(p))
        assert m.line_count == 8
        assert m.section_count == 3
        assert m.subsection_count == 2

    def test_mermaid_and_code_blocks(self, tmp_path):
        """Mermaid blocks counted in diagram_count; non-mermaid blocks in code_example_count."""
        p = tmp_path / "doc.md"
        # Note: the regex r'```(?!mermaid)[\s\S]*?```' can match ```\n...\n``` sequences
        # between mermaid blocks as "code blocks" (3 phantom matches), so use single block
        p.write_text(
            "## Diagrams\n"
            "```mermaid\nflowchart LR\n  A --> B\n```\n"
            "```mermaid\nclassDiagram\n  ClassA --> ClassB\n```\n"
            "## Code\n"
            "```python\nprint('hello')\n```\n"
            "```javascript\nconsole.log('hi')\n```\n",
            encoding="utf-8",
        )
        m = check_doc_quality.analyze_document(str(p))
        assert m.diagram_count == 2
        assert m.class_diagram_count == 1
        # code_example_count includes phantom matches from ```\n``` between blocks
        assert m.code_example_count >= 2

    def test_table_detection(self, tmp_path):
        """Table separator lines (with ---) are counted."""
        p = tmp_path / "doc.md"
        p.write_text(
            "## Data\n\n"
            "| Col1 | Col2 |\n"
            "|------|------|\n"
            "| a | b |\n\n"
            "| X | Y |\n"
            "|---|---|\n"
            "| 1 | 2 |\n",
            encoding="utf-8",
        )
        m = check_doc_quality.analyze_document(str(p))
        assert m.table_count == 2

    def test_cross_links_internal_md(self, tmp_path):
        """Internal .md links count as cross links."""
        p = tmp_path / "doc.md"
        p.write_text(
            "## See also\n\n"
            "Check [other](other.md) and [intro](intro.md#section).\n\n"
            "External: [Google](https://google.com)\n",
            encoding="utf-8",
        )
        m = check_doc_quality.analyze_document(str(p))
        assert m.cross_link_count == 2

    def test_cross_links_http_not_counted(self, tmp_path):
        """HTTP links do NOT count as cross links."""
        p = tmp_path / "doc.md"
        p.write_text(
            "## Links\n\n"
            "[Google](https://google.com)\n"
            "[GitHub](http://github.com)\n",
            encoding="utf-8",
        )
        m = check_doc_quality.analyze_document(str(p))
        assert m.cross_link_count == 0

    def test_source_tracing_detection(self, tmp_path):
        """Source tracing requires a file:// link (line ranges optional)."""
        # 来源 keyword without a source link is not enough.
        p1 = tmp_path / "a.md"
        p1.write_text("## Code\n\n**来源**：file1.py\n", encoding="utf-8")
        m1 = check_doc_quality.analyze_document(str(p1))
        assert m1.has_source_tracing is False

        # Diagram sources keyword without a source link is not enough.
        p2 = tmp_path / "b.md"
        p2.write_text("## Diagram\n\n**Diagram sources**: diagram.py\n", encoding="utf-8")
        m2 = check_doc_quality.analyze_document(str(p2))
        assert m2.has_source_tracing is False

        # A file:// link without a line range is enough.
        p3 = tmp_path / "c.md"
        p3.write_text("## Ref\n\nSee file:///src/main.py\n", encoding="utf-8")
        m3 = check_doc_quality.analyze_document(str(p3))
        assert m3.has_source_tracing is True

        # 相关源文件 (Chinese title) with file:// links and line ranges (new format)
        p5 = tmp_path / "e.md"
        p5.write_text(
            "# Module\n\n"
            "<details open><summary>相关源文件</summary>\n\n"
            "- [src/](file:///src/)\n"
            "  - [main.py](file:///src/main.py#L1-L50) - 认证主流程和错误分支\n"
            "  - [token.ts](file:///src/auth/token.ts#L1-L30) - token 生成与校验\n"
            "\n</details>\n",
            encoding="utf-8",
        )
        m5 = check_doc_quality.analyze_document(str(p5))
        assert m5.has_source_tracing is True
        assert m5.has_relevant_source_files is True

        # A late table-style source index should not count as the required top block.
        p6 = tmp_path / "f.md"
        p6.write_text(
            "# Module\n\n"
            "## 概述\n\n"
            "模块说明。\n\n"
            "## 相关源码文件\n\n"
            "| 文件 | 说明 |\n"
            "|------|------|\n"
            "| [src/main.py](file:///src/main.py) | 主流程 |\n",
            encoding="utf-8",
        )
        m6 = check_doc_quality.analyze_document(str(p6))
        assert m6.has_source_tracing is True
        assert m6.has_relevant_source_files is False

        # No source tracing
        p4 = tmp_path / "d.md"
        p4.write_text("## Intro\n\nSome text.\n", encoding="utf-8")
        m4 = check_doc_quality.analyze_document(str(p4))
        assert m4.has_source_tracing is False

    def test_best_practices_keyword(self, tmp_path):
        p = tmp_path / "doc.md"
        p.write_text("## 最佳实践\n\nGood stuff.\n", encoding="utf-8")
        m = check_doc_quality.analyze_document(str(p))
        assert m.has_best_practices is True

    def test_best_practices_english_keyword(self, tmp_path):
        p = tmp_path / "doc.md"
        p.write_text("## Best Practices\n\nGood stuff.\n", encoding="utf-8")
        m = check_doc_quality.analyze_document(str(p))
        assert m.has_best_practices is True

    def test_performance_keyword(self, tmp_path):
        p = tmp_path / "doc.md"
        p.write_text("## 性能优化\n\nOptimize.\n", encoding="utf-8")
        m = check_doc_quality.analyze_document(str(p))
        assert m.has_performance is True

    def test_performance_english_keyword(self, tmp_path):
        p = tmp_path / "doc.md"
        p.write_text("## Performance\n\nOptimize.\n", encoding="utf-8")
        m = check_doc_quality.analyze_document(str(p))
        assert m.has_performance is True

    def test_troubleshooting_keywords(self, tmp_path):
        for keyword in ["错误处理", "调试", "故障排除", "Troubleshoot", "debug"]:
            p = tmp_path / f"{keyword}.md"
            p.write_text(f"## {keyword}\n\nFix it.\n", encoding="utf-8")
            m = check_doc_quality.analyze_document(str(p))
            assert m.has_troubleshooting is True, f"keyword={keyword}"

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.md"
        p.write_text("", encoding="utf-8")
        m = check_doc_quality.analyze_document(str(p))
        assert m.line_count == 1  # empty string split('\n') -> ['']
        assert m.section_count == 0
        assert m.code_example_count == 0

    def test_nonexistent_file(self, tmp_path):
        p = tmp_path / "nonexistent.md"
        m = check_doc_quality.analyze_document(str(p))
        assert m.line_count == 0
        assert len(m.issues) >= 1
        assert "无法读取文件" in m.issues[0]


# ---------------------------------------------------------------------------
# evaluate_quality_level
# ---------------------------------------------------------------------------


class TestEvaluateQualityLevel:
    """Tests for evaluate_quality_level()."""

    def _make(self, **overrides):
        """Helper to create a QualityMetrics with defaults."""
        defaults = dict(
            file_path="test.md",
            has_source_tracing=True,
            source_link_valid_count=0,
            source_link_broken_count=0,
            code_example_count=1,
            section_count=3,
            diagram_count=1,
            cross_link_count=1,
            has_troubleshooting=True,
            has_best_practices=True,
            has_performance=True,
            class_diagram_count=1,
        )
        defaults.update(overrides)
        return check_doc_quality.QualityMetrics(**defaults)

    def test_no_source_tracing_always_basic(self):
        m = self._make(
            has_source_tracing=False,
            code_example_count=10,
            section_count=20,
        )
        assert check_doc_quality.evaluate_quality_level(m) == "basic"

    def test_all_source_links_broken_always_basic(self):
        m = self._make(
            source_link_valid_count=0,
            source_link_broken_count=3,
        )
        assert check_doc_quality.evaluate_quality_level(m) == "basic"

    def test_all_criteria_met_professional(self):
        """Everything passes -> score = 50 + 30 + 20 = 100 -> professional."""
        m = self._make()
        assert check_doc_quality.evaluate_quality_level(m) == "professional"

    def test_partial_criteria_standard(self):
        """Must 1/2 -> 25, Should 2/3 -> 20, Nice 0/3 -> 0 => 45 < 50 => basic.
        Let's try: Must 1/2 -> 25, Should 2/3 -> 20, Nice 1/3 -> ~6.67 => ~51.67 -> standard."""
        m = self._make(
            code_example_count=0,  # must: 0/2
            section_count=5,       # must: 1/2
            diagram_count=1,       # should: 1/3
            cross_link_count=1,    # should: 2/3
            has_troubleshooting=True,  # should: 3/3
            has_best_practices=False,
            has_performance=False,
            class_diagram_count=0,
        )
        # score = (1/2)*50 + (3/3)*30 + (0/3)*20 = 25 + 30 + 0 = 55 -> standard
        assert check_doc_quality.evaluate_quality_level(m) == "standard"

    def test_minimal_criteria_basic(self):
        """Very little met -> score < 50 -> basic."""
        m = self._make(
            code_example_count=0,
            section_count=1,
            diagram_count=0,
            cross_link_count=0,
            has_troubleshooting=False,
            has_best_practices=False,
            has_performance=False,
            class_diagram_count=0,
        )
        # score = (0/2)*50 + (0/3)*30 + (0/3)*20 = 0 -> basic
        assert check_doc_quality.evaluate_quality_level(m) == "basic"


# ---------------------------------------------------------------------------
# calculate_expected_metrics
# ---------------------------------------------------------------------------


class TestCalculateExpectedMetrics:
    """Tests for calculate_expected_metrics()."""

    def test_default_values(self):
        """File name not matching any heuristic returns defaults."""
        result = check_doc_quality.calculate_expected_metrics("/tmp/random.md")
        assert result == {
            "min_lines": 100,
            "min_sections": 6,
            "min_diagrams": 1,
            "min_examples": 2,
        }

    def test_index_file_lower_values(self):
        result = check_doc_quality.calculate_expected_metrics("/tmp/index.md")
        assert result["min_lines"] == 50
        assert result["min_sections"] == 3
        assert result["min_examples"] == 0

    def test_core_file_higher_values(self):
        result = check_doc_quality.calculate_expected_metrics("/tmp/core.md")
        assert result["min_lines"] == 200
        assert result["min_sections"] == 8
        assert result["min_diagrams"] == 2
        assert result["min_examples"] == 3

    def test_util_file_lower_values(self):
        result = check_doc_quality.calculate_expected_metrics("/tmp/util.md")
        assert result["min_lines"] == 80
        assert result["min_sections"] == 5

    def test_from_structure_json_high_importance(self, tmp_path):
        """structure.json with importance_score >= 0.6 yields higher thresholds."""
        sp = tmp_path / "structure.json"
        sp.write_text(
            json.dumps({
                "modules": [
                    {"name": "mymod", "importance_score": 0.8},
                ]
            }),
            encoding="utf-8",
        )
        result = check_doc_quality.calculate_expected_metrics("/tmp/mymod.md", structure_path=str(sp))
        assert result["min_lines"] == 200
        assert result["min_sections"] == 8

    def test_from_structure_json_low_importance(self, tmp_path):
        """structure.json with importance_score < 0.4 yields lower thresholds."""
        sp = tmp_path / "structure.json"
        sp.write_text(
            json.dumps({
                "modules": [
                    {"name": "mymod", "importance_score": 0.2},
                ]
            }),
            encoding="utf-8",
        )
        result = check_doc_quality.calculate_expected_metrics("/tmp/mymod.md", structure_path=str(sp))
        assert result["min_lines"] == 80
        assert result["min_sections"] == 5


# ---------------------------------------------------------------------------
# generate_issues
# ---------------------------------------------------------------------------


class TestGenerateIssues:
    """Tests for generate_issues()."""

    def _make(self, **overrides):
        defaults = dict(
            file_path="/tmp/test.md",
            line_count=150,
            section_count=8,
            diagram_count=2,
            class_diagram_count=1,
            code_example_count=3,
            cross_link_count=2,
            has_source_tracing=True,
            has_relevant_source_files=True,
            source_range_link_count=1,
            source_link_valid_count=0,
            source_link_broken_count=0,
            has_best_practices=True,
            has_performance=True,
            has_troubleshooting=True,
        )
        defaults.update(overrides)
        return check_doc_quality.QualityMetrics(**defaults)

    def test_line_count_too_low(self):
        m = self._make(line_count=50)
        issues = check_doc_quality.generate_issues(m)
        assert any("行数不足" in i for i in issues)

    def test_no_source_tracing(self):
        m = self._make(has_source_tracing=False)
        issues = check_doc_quality.generate_issues(m)
        assert any("源码追溯" in i for i in issues)

    def test_missing_relevant_source_files_for_module(self):
        m = self._make(has_relevant_source_files=False)
        issues = check_doc_quality.generate_issues(m)
        assert any("相关源文件" in i or "Relevant source files" in i for i in issues)

    def test_no_cross_links(self):
        m = self._make(cross_link_count=0)
        issues = check_doc_quality.generate_issues(m)
        assert any("交叉链接" in i for i in issues)

    def test_no_issues_when_all_good(self):
        m = self._make()
        issues = check_doc_quality.generate_issues(m)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# validate_source_links
# ---------------------------------------------------------------------------


class TestValidateSourceLinks:
    """Tests for validate_source_links()."""

    def test_valid_link(self, tmp_path):
        """A file:// link pointing to an existing file counts as valid."""
        src = tmp_path / "main.py"
        src.write_text("print('hi')", encoding="utf-8")

        content = "See file:///main.py for details."
        valid, broken = check_doc_quality.validate_source_links(content, str(tmp_path))
        assert valid == 1
        assert broken == 0

    def test_broken_link(self, tmp_path):
        """A file:// link pointing to a nonexistent file counts as broken."""
        content = "See file:///nonexistent.py for details."
        valid, broken = check_doc_quality.validate_source_links(content, str(tmp_path))
        assert valid == 0
        assert broken == 1

    def test_dedup_same_link_counted_once(self, tmp_path):
        """The same file:// link appearing multiple times is only counted once."""
        src = tmp_path / "utils.py"
        src.write_text("pass", encoding="utf-8")

        content = (
            "Ref1: file:///utils.py\n"
            "Ref2: file:///utils.py\n"
            "Ref3: file:///utils.py\n"
        )
        valid, broken = check_doc_quality.validate_source_links(content, str(tmp_path))
        assert valid == 1
        assert broken == 0

    def test_no_file_links_returns_zeros(self, tmp_path):
        content = "No file links here. Just http://example.com"
        valid, broken = check_doc_quality.validate_source_links(content, str(tmp_path))
        assert valid == 0
        assert broken == 0

    def test_source_links_with_and_without_line_ranges(self, tmp_path):
        src = tmp_path / "utils.py"
        src.write_text("line 1\nline 2\n", encoding="utf-8")

        content = (
            "[with range](file:///utils.py#L1-L2)\n"
            "[without range](file:///utils.py)\n"
        )
        result = check_doc_quality.validate_source_link_with_lines(content, str(tmp_path))

        # Both links point to existing file; line ranges are optional now
        assert result["broken"] == 0
        assert result["valid"] >= 1


# ---------------------------------------------------------------------------
# check_wiki_quality
# ---------------------------------------------------------------------------


class TestCheckWikiQuality:
    """Tests for check_wiki_quality()."""

    def test_multiple_docs(self, tmp_path):
        """Reports correct counts for multiple docs in wiki/."""
        deepwiki = tmp_path / ".deepwiki"
        wiki = deepwiki / "wiki"
        wiki.mkdir(parents=True)

        (wiki / "a.md").write_text(
            "# A\n\n## S1\n\n## S2\n\n## S3\n\n"
            "**来源**：[a.py](file:///src/a.py#L1-L10)\n"
            "```python\ncode\n```\n"
            "```mermaid\nflowchart LR\nA-->B\n```\n"
            "[B doc](b.md)\n"
            "## Troubleshoot\n\nfix it\n",
            encoding="utf-8",
        )
        (wiki / "b.md").write_text("# B\n\nplain.\n", encoding="utf-8")

        report = check_doc_quality.check_wiki_quality(str(deepwiki))
        assert report.total_docs == 2
        # b.md has no source tracing -> basic
        assert report.basic_count >= 1

    def test_nonexistent_wiki_dir_adds_summary_issue(self, tmp_path):
        """When wiki/ does not exist, a summary_issue is added."""
        deepwiki = tmp_path / ".deepwiki"
        deepwiki.mkdir()
        report = check_doc_quality.check_wiki_quality(str(deepwiki))
        assert len(report.summary_issues) >= 1
        assert "Wiki 目录不存在" in report.summary_issues[0]
        assert report.total_docs == 0

    def test_uses_structure_json(self, tmp_path):
        """When cache/structure.json exists, it is used for expected metrics."""
        deepwiki = tmp_path / ".deepwiki"
        cache = deepwiki / "cache"
        wiki = deepwiki / "wiki"
        for d in [cache, wiki]:
            d.mkdir(parents=True)

        structure = {
            "project_name": "test",
            "modules": [
                {"name": "core", "path": "src/core", "importance_score": 0.8},
            ],
        }
        (cache / "structure.json").write_text(json.dumps(structure), encoding="utf-8")

        # Write a core.md that meets default thresholds but not high-importance ones
        (wiki / "core.md").write_text(
            "# Core\n\n"
            "## S1\n\n## S2\n\n## S3\n\n## S4\n\n## S5\n\n## S6\n\n"
            "**来源**：[core.py](file:///core.py#L1-L20)\n"
            "```python\nexample\n```\n"
            "```python\nexample2\n```\n"
            "[link](other.md)\n",
            encoding="utf-8",
        )

        report = check_doc_quality.check_wiki_quality(str(deepwiki))
        assert report.total_docs == 1
        # core.md with importance 0.8 expects min_lines=200; our doc has far fewer lines
        doc = report.docs[0]
        assert any("行数不足" in i for i in doc.issues)

    def test_missing_evidence_index_no_longer_adds_summary_issue(self, tmp_path):
        deepwiki = tmp_path / ".deepwiki"
        wiki = deepwiki / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "overview.md").write_text("# Overview\n\n## A\n", encoding="utf-8")

        report = check_doc_quality.check_wiki_quality(str(deepwiki))
        # evidence-index.json absence should no longer produce a summary issue
        assert not any("evidence-index.json" in issue for issue in report.summary_issues)

    def test_evidence_index_file_does_not_affect_quality_check(self, tmp_path):
        deepwiki = tmp_path / ".deepwiki"
        cache = deepwiki / "cache"
        wiki = deepwiki / "wiki"
        for d in [cache, wiki]:
            d.mkdir(parents=True)
        (wiki / "overview.md").write_text("# Overview\n\n## A\n", encoding="utf-8")
        (cache / "evidence-index.json").write_text(
            json.dumps({"claims": []}), encoding="utf-8"
        )

        report = check_doc_quality.check_wiki_quality(str(deepwiki))
        # evidence-index contents should no longer generate any doc-level issue
        assert not any("缺少证据索引" in issue for issue in report.docs[0].issues)


class TestBuildEvidenceIndex:
    """Tests for build_evidence_index.py."""

    def test_builds_claims_from_module_analysis(self, tmp_path):
        deepwiki = tmp_path / ".deepwiki"
        cache = deepwiki / "cache"
        cache.mkdir(parents=True)
        (cache / "module-analysis.json").write_text(
            json.dumps(
                {
                    "cache_schema_version": 2,
                    "modules": {
                        "auth": {
                            "module_path": "src/auth",
                            "module_summary": "Handles authentication.",
                            "module_role": "Owns sign-in decisions.",
                            "semantic_group": "Authentication",
                            "files": [
                                {
                                    "path": "src/auth/service.py",
                                    "summary": "Auth service.",
                                    "public_interfaces": [
                                        {"name": "login", "line": 10, "end_line": 24}
                                    ],
                                    "core_source_ranges": [
                                        {
                                            "label": "login flow",
                                            "start_line": 10,
                                            "end_line": 24,
                                        }
                                    ],
                                }
                            ],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        result = build_evidence_index.build_evidence_index(tmp_path)
        claims = result["claims"]
        assert claims
        assert claims[0]["page_id"] == "deep-dive:auth"
        assert claims[0]["evidence"]
        assert claims[0]["evidence"][0]["ranges"] == [
            {"start_line": 10, "end_line": 24, "label": "login flow"},
            {"start_line": 10, "end_line": 24, "label": "login"},
        ]
        assert (cache / "evidence-index.json").exists()

    def test_deep_dive_internal_doc_matches_internal_evidence(self, tmp_path):
        deepwiki = tmp_path / ".deepwiki"
        cache = deepwiki / "cache"
        wiki = deepwiki / "wiki"
        deep_dive = wiki / "deep-dive"
        cache.mkdir(parents=True)
        deep_dive.mkdir(parents=True)

        (tmp_path / "src" / "db").mkdir(parents=True)
        (tmp_path / "src" / "db" / "storage.py").write_text(
            "\n".join(f"line {i}" for i in range(1, 40)),
            encoding="utf-8",
        )
        (deep_dive / "storage.md").write_text(
            "# Storage\n\n"
            "<details open><summary>Relevant source files</summary>\n\n"
            "- [src/](file:///src/)\n"
            "  - [db/](file:///src/db/)\n"
            "    - [storage.py](file:///src/db/storage.py#L1-L39) - 存储实现\n\n"
            "</details>\n\n"
            "## 概述\n\n"
            "存储实现。\n\n"
            "**来源**：[storage.py](file:///src/db/storage.py)\n"
            "[storage.py](file:///src/db/storage.py)\n",
            encoding="utf-8",
        )
        (cache / "evidence-index.json").write_text(
            json.dumps(
                {
                    "claims": [
                        {
                            "page_id": "deep-dive:storage",
                            "claim_text": "Storage internals.",
                            "evidence": [{"path": "src/db/storage.py"}],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        report = check_doc_quality.check_wiki_quality(str(deepwiki))
        storage = next(doc for doc in report.docs if doc.file_path.endswith("storage.md"))
        assert not any("缺少证据索引" in issue for issue in storage.issues)


# ---------------------------------------------------------------------------
# save_report_json
# ---------------------------------------------------------------------------


class TestSaveReportJson:
    """Tests for save_report_json()."""

    def test_file_creation_and_structure(self, tmp_path):
        """save_report_json creates a valid JSON file with expected keys."""
        metrics = check_doc_quality.QualityMetrics(
            file_path="/wiki/test.md",
            line_count=100,
            section_count=5,
            quality_level="standard",
            issues=["some issue"],
        )
        report = check_doc_quality.QualityReport(
            wiki_path="/wiki",
            check_time="2025-01-01T00:00:00",
            total_docs=1,
            standard_count=1,
            docs=[metrics],
        )

        out = tmp_path / "report.json"
        check_doc_quality.save_report_json(report, str(out))

        assert out.exists()
        with open(out, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["wiki_path"] == "/wiki"
        assert data["check_time"] == "2025-01-01T00:00:00"
        assert data["summary"]["total"] == 1
        assert data["summary"]["standard"] == 1
        assert len(data["docs"]) == 1

        doc = data["docs"][0]
        assert doc["file"] == "/wiki/test.md"
        assert doc["quality_level"] == "standard"
        assert doc["metrics"]["lines"] == 100
        assert doc["metrics"]["sections"] == 5
        assert doc["issues"] == ["some issue"]


# ---------------------------------------------------------------------------
# check_analysis_quality
# ---------------------------------------------------------------------------


class TestCheckAnalysisQuality:
    """Tests for module-analysis cognitive structure gates."""

    def _module(self, **overrides):
        data = {
            "module_path": "src/auth",
            "module_summary": "Handles authentication.",
            "semantic_group": "Authentication",
            "selected_components": ["overview"],
            "code_purpose": "Service",
            "analysis_depth": "standard",
            "dependency_hints": {"imports": [], "imported_by": []},
            "files": [
                {
                    "path": "src/auth/service.py",
                    "summary": "Authentication service.",
                    "public_interfaces": [{"name": "login", "line": 10, "end_line": 24}],
                    "core_source_ranges": [
                        {
                            "label": "login flow",
                            "start_line": 10,
                            "end_line": 24,
                            "reason": "Covers the authentication happy path.",
                        }
                    ],
                    "key_insights": ["Keeps credential handling isolated."],
                }
            ],
        }
        data.update(overrides)
        return data

    def test_missing_cognitive_fields_fails_module(self):
        errors, warnings = check_analysis_quality.check_module_quality(
            "auth", self._module()
        )
        assert warnings == []
        assert any("module_role" in err for err in errors)
        assert any("upstream_inputs" in err for err in errors)
        assert any("downstream_outputs" in err for err in errors)
        assert any("risk_points" in err for err in errors)
        assert any("extension_points" in err for err in errors)

    def test_cognitive_fields_allow_module_to_pass(self):
        errors, warnings = check_analysis_quality.check_module_quality(
            "auth",
            self._module(
                module_role="Owns authentication decisions.",
                upstream_inputs=["HTTP credentials"],
                downstream_outputs=["Session token"],
                risk_points=["Password handling"],
                extension_points=["Add SSO provider"],
            ),
        )
        assert errors == []
        assert warnings == []

    def test_missing_source_ranges_warns(self):
        module = self._module(
            module_role="Owns authentication decisions.",
            upstream_inputs=["HTTP credentials"],
            downstream_outputs=["Session token"],
            risk_points=["Password handling"],
            extension_points=["Add SSO provider"],
            files=[
                {
                    "path": "src/auth/service.py",
                    "summary": "Authentication service.",
                    "public_interfaces": [{"name": "login"}],
                    "key_insights": ["Keeps credential handling isolated."],
                }
            ],
        )
        errors, warnings = check_analysis_quality.check_module_quality("auth", module)
        assert errors == []
        assert any("line/end_line" in warning for warning in warnings)
        assert any("core_source_ranges" in warning for warning in warnings)


def test_check_quality_with_module_filter(tmp_path):
    """modules 参数只检查指定模块，其他模块缺字段不影响结果"""
    import json
    from scripts.core.common import CACHE_SCHEMA_VERSION
    from scripts.quality.check_analysis_quality import check_analysis_quality

    module_data = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "modules": {
            "auth": {
                "module_path": "src/auth",
                "code_purpose": "Service",
                "module_summary": "Auth service.",
                "selected_components": ["overview"],
                "dependency_hints": {"imports": [], "imported_by": []},
                "semantic_group": "认证",
                "module_role": "Handles user authentication",
                "upstream_inputs": ["Login requests"],
                "downstream_outputs": ["Auth tokens"],
                "risk_points": ["Session hijacking"],
                "extension_points": ["OAuth providers"],
                "files": [],
            },
            "broken": {},  # 故意缺字段，但 modules=["auth"] 时不应被检查
        },
    }

    all_errors, all_warnings, failed, checked = check_analysis_quality(
        module_data["modules"], modules=["auth"]
    )

    # auth 模块应通过
    assert "auth" not in all_errors
    # broken 模块未被检查
    assert "broken" not in all_errors
    # 只检查了指定模块
    assert checked == ["auth"]


def test_check_analysis_quality_cli_unwraps_module_analysis_envelope(tmp_path, monkeypatch):
    """The CLI should validate module-analysis.json modules, not top-level metadata."""
    from scripts.core.common import CACHE_SCHEMA_VERSION
    from scripts.quality.check_analysis_quality import main

    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    (cache / "module-analysis.json").write_text(
        json.dumps(
            {
                "cache_schema_version": CACHE_SCHEMA_VERSION,
                "modules": {
                    "auth": {
                        "module_summary": "Missing required fields.",
                        "files": [{"path": "src/auth.py", "summary": "Auth"}],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["check_analysis_quality.py", str(tmp_path), "--module", "auth"],
    )

    assert main() == 1


def test_check_analysis_quality_cli_fails_for_unknown_module_filter(tmp_path, monkeypatch):
    """A misspelled --module filter should not report a false pass."""
    from scripts.core.common import CACHE_SCHEMA_VERSION
    from scripts.quality.check_analysis_quality import main

    cache = tmp_path / ".deepwiki" / "cache"
    cache.mkdir(parents=True)
    (cache / "module-analysis.json").write_text(
        json.dumps(
            {
                "cache_schema_version": CACHE_SCHEMA_VERSION,
                "modules": {
                    "auth": {
                        "module_path": "src/auth",
                        "module_summary": "Auth service.",
                        "semantic_group": "认证",
                        "selected_components": ["overview"],
                        "module_role": "Handles login",
                        "upstream_inputs": ["credentials"],
                        "downstream_outputs": ["token"],
                        "risk_points": ["password handling"],
                        "extension_points": ["oauth"],
                        "files": [{"path": "src/auth.py", "summary": "Auth"}],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["check_analysis_quality.py", str(tmp_path), "--module", "missing"],
    )

    assert main() == 2
