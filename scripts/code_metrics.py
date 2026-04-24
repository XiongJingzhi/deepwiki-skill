#!/usr/bin/env python3
"""
代码复杂度与重要行统计模块。

从 analyze_project.py 提取的纯函数，
供 analyze_project.py 和 parse_cache.py 共用。
"""

import re
from pathlib import Path


def compute_complexity_score(cf_count: int, def_count: int, loc: int) -> int:
    """Pure function: compute a 0-100 complexity score.

    Args:
        cf_count: number of control-flow nodes (if/for/while/try ...)
        def_count: number of definition nodes (function/class ...)
        loc: non-empty, non-comment lines of code
    """
    return min(int((cf_count * 2 + def_count) * 100 / max(loc, 1)), 100)


def estimate_complexity(file_path: Path) -> int:
    """
    估算代码复杂度（基于 tree-sitter AST 节点统计）

    统计控制流节点（if/for/while/try 等）和定义节点（function/class 等），
    归一化到 0-100 的范围，用于判断文件分析深度。
    """
    try:
        source = file_path.read_bytes()
    except Exception:
        return 0

    if not source.strip():
        return 0

    from parsers import get_lang_for_ext, get_manager

    ext = file_path.suffix.lower()
    lang_name = get_lang_for_ext(ext)
    if not lang_name:
        return 0

    try:
        mgr = get_manager()
        parser = mgr.get_parser(lang_name)
        tree = parser.parse(source)
        root = tree.root_node

        if root.has_error and root.child_count == 0:
            return 0

        caps = mgr.run_query(lang_name, "complexity", root)
        cf_count = len(caps.get("cf", []))
        def_count = len(caps.get("def", []))

        # 统计有效代码行（排除空行和纯注释行）
        lines = source.split(b"\n")
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith((b"#", b"//", b"/*", b"*"))]
        loc = len(non_empty_lines)

        return compute_complexity_score(cf_count, def_count, loc)
    except Exception:
        return 0


def count_important_lines(file_path: Path) -> int:
    """
    统计文件中"重要代码行"数量（基于 tree-sitter AST）。

    重要代码行是指含有接口定义、导出声明、导入声明等对文档生成高价值的行。
    使用 AST 节点统计而非 regex，避免字符串/注释中的误匹配。
    """
    try:
        source = file_path.read_bytes()
    except Exception:
        return 0

    if not source.strip():
        return 0

    from parsers import get_lang_for_ext, get_manager

    ext = file_path.suffix.lower()
    lang_name = get_lang_for_ext(ext)
    if not lang_name:
        # 无 tree-sitter 支持的语言，回退到行数统计
        try:
            lines = source.split(b"\n")
            return len([l for l in lines if l.strip()])
        except Exception:
            return 0

    try:
        mgr = get_manager()
        parser = mgr.get_parser(lang_name)
        tree = parser.parse(source)
        root = tree.root_node

        if root.has_error and root.child_count == 0:
            return 0

        caps = mgr.run_query(lang_name, "important", root)
        # 统计所有重要节点的行号（去重，一行只计一次）
        important_lines: set = set()
        for category in ("imp", "exp", "decl"):
            for node in caps.get(category, []):
                important_lines.add(node.start_point[0])

        # 加上 TODO/FIXME 等标记（regex 仍适合行级扫描）
        for i, line in enumerate(source.split(b"\n")):
            line_str = line.decode("utf-8", errors="replace")
            if re.search(r'(?:TODO|FIXME|HACK|NOTE|WARN|XXX)\s*[:\(]', line_str):
                important_lines.add(i)

        return len(important_lines)
    except Exception:
        return 0
