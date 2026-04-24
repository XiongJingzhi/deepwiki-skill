#!/usr/bin/env python3
"""
Import 关系提取模块
基于 tree-sitter AST 提取文件级 import 关系，作为依赖验证的可信基线。
"""

from pathlib import Path
from typing import Dict, List, Optional

from parsers import get_manager, get_lang_for_ext, get_parser_for_ext


def _extract_imports_from_source(source: bytes, lang_name: str) -> List[str]:
    """用 tree-sitter 从源码中提取 import 路径字符串。"""
    mgr = get_manager()
    parser = mgr.get_parser(lang_name)
    tree = parser.parse(source)
    root = tree.root_node

    if root.has_error or root.child_count == 0:
        return []

    try:
        captures = mgr.run_query(lang_name, "import", root)
    except (ValueError, Exception):
        return []

    imports: List[str] = []
    seen: set = set()

    # import.path — 大多数语言的模块路径（含 JS/TS 引号字符串、Go 包路径、Rust 路径等）
    for node in captures.get("import.path", []):
        raw = node.text.decode("utf-8", errors="replace")
        # 清理引号包裹的路径
        text = raw.strip('"').strip("'")
        if not text:
            continue
        # Rust 的 use 声明可能是 self::mod 或 crate::mod 形式
        if lang_name == "rust":
            text = text.replace("self::", "").replace("super::", "").replace("crate::", "")
        if text and text not in seen:
            seen.add(text)
            imports.append(text)

    # import.module — Python from X import 中的模块名
    for node in captures.get("import.module", []):
        text = node.text.decode("utf-8", errors="replace")
        if text and text not in seen:
            seen.add(text)
            imports.append(text)

    return imports


def extract_import_relations(files: List[Path], project_root: Path) -> Dict[str, List[str]]:
    """
    基于 tree-sitter AST 提取文件级 import 关系（作为依赖验证的可信基线）。

    Args:
        files: 待分析的文件列表
        project_root: 项目根目录

    Returns:
        {文件相对路径: [导入的目标模块/文件路径列表]}
    """
    relations: Dict[str, List[str]] = {}

    for fpath in files:
        if not fpath.exists():
            continue

        lang_name = get_lang_for_ext(fpath.suffix.lower())
        if not lang_name:
            continue

        try:
            source = fpath.read_bytes()
            if not source.strip():
                continue
        except Exception:
            continue

        try:
            imports = _extract_imports_from_source(source, lang_name)
        except Exception:
            continue

        if imports:
            rel_path = str(fpath.relative_to(project_root)).replace("\\", "/")
            resolved = _resolve_imports_to_paths(imports, fpath, project_root)
            relations[rel_path] = resolved

    return relations


def _resolve_imports_to_paths(imports: List[str], source_file: Path, project_root: Path) -> List[str]:
    """将 import 语句中的模块名解析为项目内的相对文件路径。"""
    resolved: List[str] = []
    source_dir = source_file.parent
    source_ext = source_file.suffix

    for imp in imports:
        if "/" not in imp and "." not in imp and not imp.startswith("."):
            candidates = _find_module_in_project(imp, project_root, source_ext)
            resolved.extend(candidates)
        elif imp.startswith("."):
            target_dir = source_dir if imp == "." else source_dir / imp.replace(".", "/").lstrip("/")
            target_file = target_dir.with_suffix(source_ext) if target_dir.suffix == "" else target_dir
            if target_file.exists():
                resolved.append(str(target_file.relative_to(project_root)).replace("\\", "/"))
        elif "/" in imp:
            base_path = project_root / imp
            for ext in ["", ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"]:
                candidate = base_path.with_suffix(ext) if ext else base_path
                if candidate.exists() and candidate.is_file():
                    resolved.append(str(candidate.relative_to(project_root)).replace("\\", "/"))
                    break

    return list(set(resolved))


def _find_module_in_project(module_name: str, project_root: Path, source_ext: str) -> List[str]:
    """在项目中查找模块名对应的文件路径。"""
    candidates: List[str] = []
    src_dirs = [
        "src", "lib", "pkg", "app", "internal",
        # Java convention
        "src/main/java", "src/main/kotlin", "src/main/scala",
        # Go convention
        "cmd",
    ]

    for src_dir in src_dirs:
        src_path = project_root / src_dir
        if not src_path.exists():
            continue

        for ext in [source_ext, ".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"]:
            candidate = src_path / f"{module_name}{ext}"
            if candidate.exists():
                candidates.append(str(candidate.relative_to(project_root)).replace("\\", "/"))
                break

        index_files = ["index.ts", "index.tsx", "index.js", "index.jsx", "__init__.py", "mod.rs", "lib.go"]
        for idx_file in index_files:
            candidate = src_path / module_name / idx_file
            if candidate.exists():
                candidates.append(str(candidate.relative_to(project_root)).replace("\\", "/"))
                break

    return candidates
