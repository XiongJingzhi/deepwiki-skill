"""
Unified AST parse cache -- parse once, use everywhere.
Solves P0: eliminates repeated tree-sitter parsing across pipeline steps.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

from common import CACHE_SCHEMA_VERSION


class ParseCache:
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.cache_dir = project_path / ".deepwiki" / "cache"
        self._data = {}  # {rel_path: cache_entry}
        self._load()

    def _load(self):
        """Load existing parse-results.json if available."""
        path = self.cache_dir / "parse-results.json"
        if path.exists():
            try:
                data = json.loads(path.read_text('utf-8'))
                if data.get('cache_schema_version') == CACHE_SCHEMA_VERSION:
                    self._data = data.get('files', {})
            except Exception:
                pass

    def get(self, filepath: Path) -> Optional[dict]:
        """Get cached parse result for a file. Returns None if not cached or stale."""
        if not filepath.exists():
            return None
        try:
            mtime = filepath.stat().st_mtime
        except OSError:
            return None
        rel = str(filepath.relative_to(self.project_path)).replace('\\', '/')
        entry = self._data.get(rel)
        if entry and entry.get('mtime') == mtime:
            return entry
        return None

    def populate(self, filepaths):
        """Parse files and add to cache."""
        from parsers import get_lang_for_ext, get_manager
        from code_metrics import compute_complexity_score

        for fp in filepaths:
            rel = str(fp.relative_to(self.project_path)).replace('\\', '/')
            if self.get(fp):  # already cached and fresh
                continue

            ext = fp.suffix.lower()
            lang_name = get_lang_for_ext(ext)
            if not lang_name:
                continue

            try:
                source = fp.read_bytes()
                if not source.strip():
                    continue
                mtime = fp.stat().st_mtime
            except Exception:
                continue

            try:
                mgr = get_manager()
                parser = mgr.get_parser(lang_name)
                tree = parser.parse(source)
                root = tree.root_node
                if root.has_error and root.child_count == 0:
                    continue

                # Complexity
                caps = mgr.run_query(lang_name, "complexity", root)
                cf_count = len(caps.get("cf", []))
                def_count = len(caps.get("def", []))
                lines = source.split(b"\n")
                non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith((b"#", b"//", b"/*", b"*"))]
                loc = len(non_empty_lines)
                complexity_score = compute_complexity_score(cf_count, def_count, loc)

                # Important lines
                caps_imp = mgr.run_query(lang_name, "important", root)
                important_lines = sorted(set(
                    node.start_point[0]
                    for category in ("imp", "exp", "decl")
                    for node in caps_imp.get(category, [])
                ))
                # Add TODO/FIXME lines
                for i, line in enumerate(source.split(b"\n")):
                    line_str = line.decode("utf-8", errors="replace")
                    if re.search(r'(?:TODO|FIXME|HACK|NOTE|WARN|XXX)\s*[:\(]', line_str):
                        important_lines.append(i)
                important_lines = sorted(set(important_lines))

                self._data[rel] = {
                    "mtime": mtime,
                    "language": lang_name,
                    "complexity_cf_count": cf_count,
                    "complexity_def_count": def_count,
                    "complexity_score": complexity_score,
                    "loc": loc,
                    "important_lines": important_lines,
                    "important_lines_count": len(important_lines),
                }
            except Exception:
                continue

    def save(self):
        """Write cache to disk（merge 模式，保留磁盘上已有的非本次写入文件的数据）。"""
        import os
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / "parse-results.json"

        # 读取磁盘上已有的数据，进行合并
        existing_files = {}
        if path.exists():
            try:
                existing_data = json.loads(path.read_text('utf-8'))
                if existing_data.get('cache_schema_version') == CACHE_SCHEMA_VERSION:
                    existing_files = existing_data.get('files', {})
            except Exception:
                pass

        # 本次数据覆盖已有数据，不在本次范围内的文件保留
        merged_files = {**existing_files, **self._data}

        data = {
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "files": merged_files,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
