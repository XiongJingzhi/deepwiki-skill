"""DeepWiki 本地预览服务器入口。"""

import argparse
import sys
from http.server import HTTPServer
from pathlib import Path

import scripts.serve.handler as _handler


def resolve_wiki_dir(project_path: str) -> Path:
    """解析并验证 .deepwiki/wiki 目录路径，不存在则退出。"""
    target = Path(project_path).resolve()
    wiki = target / ".deepwiki" / "wiki"
    if not wiki.is_dir():
        print(f"Error: wiki directory not found at {wiki}", file=sys.stderr)
        sys.exit(1)
    return wiki


def serve_wiki(project_path: str, port: int = 8742, host: str = "127.0.0.1"):
    """启动本地 wiki 预览服务器。"""
    _handler.project_root = Path(project_path).resolve()
    _handler.wiki_dir = resolve_wiki_dir(project_path)
    menu = _handler._load_menu(_handler.wiki_dir)

    server = HTTPServer((host, port), _handler.WikiHandler)
    url = f"http://{host}:{port}"
    print(f"DeepWiki server running at {url}")
    print(f"  Project: {menu.get('title', _handler.wiki_dir.parent.parent.name)}")
    print(f"  Wiki:    {_handler.wiki_dir}")
    print(f"  Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Start DeepWiki documentation server")
    parser.add_argument("project_path", help="Path to project with .deepwiki/ directory")
    parser.add_argument("--port", type=int, default=8742, help="Server port (default: 8742)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    args = parser.parse_args()
    serve_wiki(args.project_path, args.port, args.host)


if __name__ == "__main__":
    main()
