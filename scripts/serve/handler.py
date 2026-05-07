"""HTTP 请求处理器：路由分发、内容响应。"""

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from scripts.serve.html_template import HTML_TEMPLATE
from scripts.serve.source_utils import _resolve_source_path, _language_for_path

# Module-level state set by server.py before serving
wiki_dir: Path = Path(".")
project_root: Path = Path(".")


def _load_menu(wiki_dir_: Path) -> dict:
    menu_path = wiki_dir_ / "menu.json"
    if menu_path.is_file():
        with open(menu_path, "r", encoding="utf-8") as f:
            menu = json.load(f)
            if isinstance(menu, dict) and isinstance(menu.get("items"), list):
                return menu
            return {"title": menu.get("title", "Wiki") if isinstance(menu, dict) else "Wiki", "items": []}
    return {"title": "Wiki", "items": []}


# Directories / files to skip when building directory trees
_TREE_IGNORE = {
    ".git", ".deepwiki", "__pycache__", "node_modules", ".venv", "venv",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
    ".DS_Store", "Thumbs.db",
}


def _build_dir_tree(directory: Path, root: Path, _depth: int = 0) -> list:
    """Recursively build a JSON-serialisable directory tree (max depth 5).

    Each node:
      { "name": str, "type": "dir"|"file", "path": str (relative to root),
        "children": [...] }   # only for "dir" nodes
    """
    if _depth > 5:
        return []
    entries = []
    try:
        children = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return []
    for child in children:
        if child.name in _TREE_IGNORE or child.name.startswith("."):
            continue
        rel = child.relative_to(root).as_posix()
        if child.is_dir():
            entries.append({
                "name": child.name,
                "type": "dir",
                "path": rel,
                "children": _build_dir_tree(child, root, _depth + 1),
            })
        else:
            entries.append({"name": child.name, "type": "file", "path": rel})
    return entries


class WikiHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path in ("/", ""):
            self._serve_html()
        elif path == "/api/menu":
            self._serve_menu()
        elif path.startswith("/api/page/"):
            self._serve_page(path[len("/api/page/"):])
        elif path == "/api/source":
            self._serve_source(urllib.parse.parse_qs(parsed_url.query))
        else:
            self.send_error(404)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text, status=200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_html(self):
        self._send_html(HTML_TEMPLATE)

    def _serve_menu(self):
        menu = _load_menu(wiki_dir)
        self._send_json(menu)

    def _serve_page(self, encoded_path: str):
        page_path = urllib.parse.unquote(encoded_path)
        file_path = (wiki_dir / page_path).resolve()

        if not file_path.is_relative_to(wiki_dir.resolve()):
            self.send_error(403, "Forbidden")
            return
        if not file_path.is_file():
            self._send_json({"error": "not found"}, 404)
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            self._send_text(content)
        except OSError:
            self.send_error(500)

    def _serve_source(self, query):
        raw_path = query.get("path", [""])[0]
        if not raw_path:
            self._send_json({"error": "missing path"}, 400)
            return

        root = project_root.resolve()
        file_path = _resolve_source_path(raw_path, root)

        if not file_path.is_relative_to(root):
            self.send_error(403, "Forbidden")
            return

        # --- Directory: return tree ---
        if file_path.is_dir():
            self._send_json(
                {
                    "type": "directory",
                    "path": str(file_path),
                    "relative_path": file_path.relative_to(root).as_posix(),
                    "tree": _build_dir_tree(file_path, root),
                }
            )
            return

        if not file_path.is_file():
            self._send_json({"error": "source not found"}, 404)
            return
        if file_path.stat().st_size > 1_000_000:
            self._send_json({"error": "source file is too large to preview"}, 413)
            return

        try:
            start = int(query.get("start", ["0"])[0] or 0)
            end = int(query.get("end", [str(start)])[0] or start)
        except ValueError:
            self._send_json({"error": "invalid line range"}, 400)
            return

        if start < 0 or end < 0 or (start and end and end < start):
            self._send_json({"error": "invalid line range"}, 400)
            return

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            self.send_error(500)
            return

        lines = content.splitlines()
        payload_lines = []
        highlight_start = start or 0
        highlight_end = end or start or 0
        for index, text in enumerate(lines, start=1):
            payload_lines.append(
                {
                    "number": index,
                    "text": text,
                    "highlight": bool(
                        highlight_start and highlight_start <= index <= highlight_end
                    ),
                }
            )

        self._send_json(
            {
                "type": "file",
                "path": str(file_path),
                "relative_path": file_path.relative_to(root).as_posix(),
                "start_line": start or None,
                "end_line": end or None,
                "language": _language_for_path(file_path),
                "lines": payload_lines,
            }
        )
