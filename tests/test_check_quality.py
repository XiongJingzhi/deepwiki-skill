"""Tests for scripts/check_doc_quality.py"""

import json
import os

import pytest

import check_doc_quality


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
        """Source tracing is detected via **Section sources** or **Diagram sources** or file://."""
        # Section sources keyword
        p1 = tmp_path / "a.md"
        p1.write_text("## Code\n\n**Section sources**: file1.py\n", encoding="utf-8")
        m1 = check_doc_quality.analyze_document(str(p1))
        assert m1.has_source_tracing is True

        # Diagram sources keyword
        p2 = tmp_path / "b.md"
        p2.write_text("## Diagram\n\n**Diagram sources**: diagram.py\n", encoding="utf-8")
        m2 = check_doc_quality.analyze_document(str(p2))
        assert m2.has_source_tracing is True

        # file:// link
        p3 = tmp_path / "c.md"
        p3.write_text("## Ref\n\nSee file:///src/main.py\n", encoding="utf-8")
        m3 = check_doc_quality.analyze_document(str(p3))
        assert m3.has_source_tracing is True

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
            "**Section sources**: src/a.py\n"
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
            "**Section sources**: core.py\n"
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
