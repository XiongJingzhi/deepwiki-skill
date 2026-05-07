"""Minimal static server for generated DeepWiki pages."""

from __future__ import annotations

import argparse
import functools
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import List, Optional


def wiki_dir_for_project(project_path: str | Path) -> Path:
    wiki_dir = Path(project_path) / ".deepwiki" / "wiki"
    if not wiki_dir.is_dir():
        raise FileNotFoundError(f"wiki directory not found: {wiki_dir}")
    return wiki_dir


def find_available_port(host: str, start_port: int) -> int:
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                port += 1
                continue
            return port


def serve_wiki(project_path: str | Path, host: str = "127.0.0.1", port: int = 8742) -> str:
    wiki_dir = wiki_dir_for_project(project_path)
    selected_port = find_available_port(host, port)
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(wiki_dir))
    server = ThreadingHTTPServer((host, selected_port), handler)
    url = f"http://{host}:{selected_port}/"
    print(f"Serving DeepWiki at {url}")
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return url


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Serve DeepWiki static pages")
    parser.add_argument("project_path")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8742)
    args = parser.parse_args(argv)
    serve_wiki(Path(args.project_path), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
