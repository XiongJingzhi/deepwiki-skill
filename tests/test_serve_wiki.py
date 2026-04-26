"""Tests for serve_wiki.py"""

import json
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from threading import Thread
from http.server import HTTPServer

import pytest

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import serve_wiki
from serve_wiki import WikiHandler, resolve_wiki_dir


@pytest.fixture
def wiki_project(tmp_path):
    """Create a fake project with .deepwiki/wiki/ structure and menu.json."""
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)

    (wiki / "overview.md").write_text(
        "# Project Overview\n\nThis is the overview page.\n\n## Features\n\n- Feature A\n- Feature B\n",
        encoding="utf-8",
    )
    (wiki / "getting-started.md").write_text(
        "# Getting Started\n\n## Prerequisites\n\nInstall Python 3.9+.\n",
        encoding="utf-8",
    )
    concepts = wiki / "concepts"
    concepts.mkdir()
    (concepts / "architecture.md").write_text(
        "# Architecture\n\n## System Design\n\n```mermaid\ngraph TD\n    A[Client] --> B[Server]\n    B --> C[Database]\n```\n",
        encoding="utf-8",
    )
    (concepts / "models.md").write_text("# Models\n\nData models.\n", encoding="utf-8")

    menu = {
        "title": "TestProject",
        "version": "1.0",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "menu": [
            {
                "title": "Overview",
                "items": [
                    {"title": "Project Overview", "path": "overview.md"},
                    {"title": "Getting Started", "path": "getting-started.md"},
                ],
            },
            {
                "title": "Concepts",
                "items": [
                    {"title": "Architecture", "path": "concepts/architecture.md"},
                    {"title": "Models", "path": "concepts/models.md"},
                ],
            },
        ],
    }
    (wiki / "menu.json").write_text(json.dumps(menu), encoding="utf-8")
    return tmp_path


def _start_server(project_path, port=0):
    """Start server on OS-assigned port, return (server, actual_port)."""
    serve_wiki.project_root = Path(project_path).resolve()
    serve_wiki.wiki_dir = serve_wiki.resolve_wiki_dir(str(project_path))
    server = HTTPServer(("127.0.0.1", port), WikiHandler)
    t = Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    return server, server.server_address[1]


def _fetch(url):
    return urllib.request.urlopen(url)


class TestResolveWikiDir:
    def test_valid_path(self, wiki_project):
        result = resolve_wiki_dir(str(wiki_project))
        assert result == wiki_project / ".deepwiki" / "wiki"

    def test_missing_wiki(self, tmp_path):
        with pytest.raises(SystemExit):
            resolve_wiki_dir(str(tmp_path))


class TestWikiHandler:
    def test_ignores_menu_without_latest_menu_array(self, wiki_project):
        menu_path = wiki_project / ".deepwiki" / "wiki" / "menu.json"
        menu_path.write_text(
            json.dumps(
                {
                    "title": "InvalidProject",
                    "items": [
                        {"title": "项目概览", "path": "overview.md"},
                    ],
                }
            ),
            encoding="utf-8",
        )

        server, port = _start_server(wiki_project)
        try:
            resp = _fetch(f"http://127.0.0.1:{port}/api/menu")
            data = json.loads(resp.read().decode("utf-8"))
            assert data["title"] == "InvalidProject"
            assert data["menu"] == []
        finally:
            server.shutdown()

    def test_serves_html(self, wiki_project):
        server, port = _start_server(wiki_project)
        try:
            resp = _fetch(f"http://127.0.0.1:{port}/")
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert "<!DOCTYPE html>" in body
            assert "marked" in body
            assert "mermaid" in body
            assert "highlightCodeBlocks" in body
            assert "hljs.highlightElement" in body
            assert "linkifyPlainSourceReferences" in body
            assert "setupSourceLinks" in body
            assert 'parent.closest("a, code, pre, script, style")' in body
            assert "openSourcePanel" in body
            assert "source-panel" in body
            assert "source-backdrop" in body
            assert 'id="source-backdrop" onclick="closeSourcePanel()"' in body
            assert "backdrop.classList.add(\"open\")" in body
            assert "backdrop.classList.remove(\"open\")" in body
            assert "function parseHashPath" in body
            assert 'hash.startsWith("#/") ? hash.slice(2)' in body
            assert "top: var(--header-height)" in body
            assert "bottom: 0" in body
            assert ".source-code-table .source-line-number" in body
            assert ".source-code-table .source-line-code" in body
            assert "padding: 0 24px 0 12px" in body
            assert "padding: 0 16px 0 0" in body
            assert "--source-width: 40vw" in body
            assert ".source-panel.expanded" in body
            assert "width: 100vw" in body
            assert "toggleSourcePanelSize" in body
            assert "source-panel-expand" in body
            assert "position: fixed" in body
            assert "top: 0" in body
            assert 'if (url.host)' in body
            assert 'decodeURIComponent(url.host)' in body
            assert "source-link" in body
            assert "source-line-range" in body
        finally:
            server.shutdown()

    def test_html_includes_mermaid_viewer_controls(self, wiki_project):
        server, port = _start_server(wiki_project)
        try:
            resp = _fetch(f"http://127.0.0.1:{port}/")
            body = resp.read().decode("utf-8")
            assert "mermaid-toolbar" in body
            assert "openMermaidModal" in body
            assert "copyMermaidSource" in body
            assert "zoomMermaidModal" in body
            assert "resetMermaidZoom" in body
            assert "mermaid-zoom-value" in body
            assert "Mermaid 图表预览" in body
            assert "复制图片" in body
            assert "copyMermaidImageFromModal" in body
            assert "svgToPngBlob" in body
            assert "ClipboardItem" in body
            assert 'new ClipboardItem({ "image/png": svgToPngBlob(svg) })' in body
            assert '"image/png"' in body
            assert "cursor: grab" in body
            assert "cursor: grabbing" in body
            assert "startMermaidDrag" in body
            assert "moveMermaidDrag" in body
            assert "pointerdown" in body
            assert "translate(${mermaidPanX}px, ${mermaidPanY}px) scale(${mermaidZoom})" in body
        finally:
            server.shutdown()

    def test_serves_menu(self, wiki_project):
        server, port = _start_server(wiki_project)
        try:
            resp = _fetch(f"http://127.0.0.1:{port}/api/menu")
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            assert data["title"] == "TestProject"
            assert len(data["menu"]) == 2
        finally:
            server.shutdown()

    def test_serves_page(self, wiki_project):
        server, port = _start_server(wiki_project)
        try:
            resp = _fetch(f"http://127.0.0.1:{port}/api/page/overview.md")
            body = resp.read().decode("utf-8")
            assert "Project Overview" in body
        finally:
            server.shutdown()

    def test_serves_source_file_with_highlighted_range(self, wiki_project):
        source = wiki_project / "src" / "app.py"
        source.parent.mkdir()
        source.write_text("def main():\n    return 42\n\nmain()\n", encoding="utf-8")

        server, port = _start_server(wiki_project)
        try:
            url = (
                f"http://127.0.0.1:{port}/api/source?"
                + urllib.parse.urlencode(
                    {"path": str(source), "start": "1", "end": "2"}
                )
            )
            resp = _fetch(url)
            data = json.loads(resp.read().decode("utf-8"))
            assert resp.status == 200
            assert data["relative_path"] == "src/app.py"
            assert data["language"] == "python"
            assert data["lines"][0]["highlight"] is True
            assert data["lines"][1]["highlight"] is True
            assert data["lines"][2]["highlight"] is False
        finally:
            server.shutdown()

    def test_serves_project_relative_source_path_with_leading_slash(self, wiki_project):
        source = wiki_project / "app" / "main.py"
        source.parent.mkdir(exist_ok=True)
        source.write_text("value = 1\n", encoding="utf-8")

        server, port = _start_server(wiki_project)
        try:
            url = (
                f"http://127.0.0.1:{port}/api/source?"
                + urllib.parse.urlencode({"path": "/app/main.py", "start": "1"})
            )
            resp = _fetch(url)
            data = json.loads(resp.read().decode("utf-8"))
            assert resp.status == 200
            assert data["relative_path"] == "app/main.py"
            assert data["lines"][0]["highlight"] is True
        finally:
            server.shutdown()

    def test_source_endpoint_blocks_path_traversal(self, wiki_project, tmp_path):
        outside = tmp_path.parent / "outside.py"
        outside.write_text("secret = True\n", encoding="utf-8")

        server, port = _start_server(wiki_project)
        try:
            url = (
                f"http://127.0.0.1:{port}/api/source?"
                + urllib.parse.urlencode({"path": str(outside)})
            )
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                _fetch(url)
            assert exc_info.value.code == 403
        finally:
            server.shutdown()

    def test_serves_nested_page(self, wiki_project):
        server, port = _start_server(wiki_project)
        try:
            resp = _fetch(f"http://127.0.0.1:{port}/api/page/concepts/architecture.md")
            body = resp.read().decode("utf-8")
            assert "mermaid" in body
        finally:
            server.shutdown()

    def test_404_missing_page(self, wiki_project):
        server, port = _start_server(wiki_project)
        try:
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                _fetch(f"http://127.0.0.1:{port}/api/page/nonexistent.md")
            assert exc_info.value.code == 404
        finally:
            server.shutdown()

    def test_403_path_traversal(self, wiki_project):
        server, port = _start_server(wiki_project)
        try:
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                _fetch(f"http://127.0.0.1:{port}/api/page/../../etc/passwd")
            assert exc_info.value.code in (403, 404)
        finally:
            server.shutdown()

    def test_missing_menu_returns_default(self, wiki_project):
        (wiki_project / ".deepwiki" / "wiki" / "menu.json").unlink()
        server, port = _start_server(wiki_project)
        try:
            resp = _fetch(f"http://127.0.0.1:{port}/api/menu")
            data = json.loads(resp.read().decode("utf-8"))
            assert data["title"] == "Wiki"
            assert data["menu"] == []
        finally:
            server.shutdown()
