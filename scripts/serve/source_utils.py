"""源代码文件工具函数：路径解析与语言识别。"""

import urllib.parse
from pathlib import Path


def _resolve_source_path(raw_path: str, root: Path) -> Path:
    """Resolve a source file/directory path from various formats to an absolute Path.

    Supported input formats:
    - Absolute path:           /home/user/project/src/main.py  or  C:/project/src/main.py
    - Relative path:           src/main.py  or  ./src/main.py
    - file:// URI (POSIX):     file:///home/user/project/src/main.py
    - file:// URI (Windows):   file:///C:/project/src/main.py
    - URL-encoded file:// URI: file:///C:/path%20with%20spaces/main.py
    - Leading-slash POSIX:     /app/main.py  (treated project-relative on Windows)

    Returns the resolved absolute Path (may not exist; callers emit 404 if so).
    Directories are returned as-is so callers can serve a directory tree.
    """
    path_str = raw_path.strip()

    # Strip file:// URI scheme: file:///  file://  file:/
    if path_str.lower().startswith("file://"):
        path_str = urllib.parse.unquote(path_str[len("file://"):])
        # Windows paths after scheme removal look like /C:/... – remove leading /
        if path_str.startswith("/") and len(path_str) > 2 and path_str[2] == ":":
            path_str = path_str[1:]
    else:
        path_str = urllib.parse.unquote(path_str)

    # Expand ~ if present
    if path_str.startswith("~"):
        path_str = str(Path(path_str).expanduser())

    candidate = Path(path_str)

    if candidate.is_absolute():
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
        # Fall back to project-relative (handles drive-letter casing / symlink mismatches)
        fallback = (root / path_str.lstrip("/\\")).resolve()
        if fallback.exists():
            return fallback
        return resolved  # callers will emit 404

    # Relative path – resolve against project root
    resolved = (root / candidate).resolve()
    if resolved.exists():
        return resolved
    # Strip accidental leading slashes (POSIX paths on Windows)
    stripped = (root / path_str.lstrip("/\\")).resolve()
    if stripped.exists():
        return stripped
    return resolved  # callers will emit 404


def _language_for_path(path: Path) -> str:
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".sh": "bash",
        ".css": "css",
        ".html": "xml",
        ".xml": "xml",
    }
    return mapping.get(path.suffix.lower(), "")
