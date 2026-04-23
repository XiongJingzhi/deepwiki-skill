#!/usr/bin/env python3
"""
Import 关系提取模块
基于正则提取文件级 import 关系，作为依赖验证的可信基线。
"""

import re
from pathlib import Path
from typing import Dict, List


# 各语言的 import 正则模式
_IMPORT_PATTERNS = {
    '.py': [
        re.compile(r'^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', re.MULTILINE),
    ],
    '.ts': [
        re.compile(r'^\s*import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', re.MULTILINE),
        re.compile(r'^\s*import\s+[\'"]([^\'"]+)[\'"]', re.MULTILINE),
    ],
    '.js': [
        re.compile(r'^\s*(?:import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]|require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\))', re.MULTILINE),
    ],
    '.go': [
        re.compile(r'^\s*import\s+(?:\([\s\S]*?\)|[\'"]([^\'"]+)[\'"])', re.MULTILINE),
    ],
    '.rs': [
        re.compile(r'^\s*use\s+([\w:]+)', re.MULTILINE),
    ],
    '.java': [
        re.compile(r'^\s*import\s+([\w.]+);', re.MULTILINE),
    ],
    '.kt': [
        re.compile(r'^\s*import\s+([\w.]+)', re.MULTILINE),
    ],
}


def extract_import_relations(files: List[Path], project_root: Path) -> Dict[str, List[str]]:
    """
    基于正则提取文件级 import 关系（作为依赖验证的可信基线）。
    
    Args:
        files: 待分析的文件列表
        project_root: 项目根目录
        
    Returns:
        {文件相对路径: [导入的目标模块/文件路径列表]}
    """
    relations = {}
    
    for fpath in files:
        if not fpath.exists():
            continue
            
        ext = fpath.suffix.lower()
        if ext not in _IMPORT_PATTERNS:
            continue
            
        try:
            content = fpath.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
            
        imports = []
        for pattern in _IMPORT_PATTERNS[ext]:
            for match in pattern.finditer(content):
                for group in match.groups():
                    if group:
                        imports.append(group)
                        break
                        
        if imports:
            rel_path = str(fpath.relative_to(project_root)).replace('\\', '/')
            resolved = _resolve_imports_to_paths(imports, fpath, project_root)
            relations[rel_path] = resolved
            
    return relations


def _resolve_imports_to_paths(imports: List[str], source_file: Path, project_root: Path) -> List[str]:
    """将 import 语句中的模块名解析为项目内的相对文件路径。"""
    resolved = []
    source_dir = source_file.parent
    source_ext = source_file.suffix
    
    for imp in imports:
        if '/' not in imp and '.' not in imp and not imp.startswith('.'):
            candidates = _find_module_in_project(imp, project_root, source_ext)
            resolved.extend(candidates)
        elif imp.startswith('.'):
            target_dir = source_dir if imp == '.' else source_dir / imp.replace('.', '/').lstrip('/')
            target_file = target_dir.with_suffix(source_ext) if target_dir.suffix == '' else target_dir
            if target_file.exists():
                resolved.append(str(target_file.relative_to(project_root)).replace('\\', '/'))
        elif '/' in imp:
            base_path = project_root / imp
            for ext in ['', '.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rs']:
                candidate = base_path.with_suffix(ext) if ext else base_path
                if candidate.exists() and candidate.is_file():
                    resolved.append(str(candidate.relative_to(project_root)).replace('\\', '/'))
                    break
                    
    return list(set(resolved))


def _find_module_in_project(module_name: str, project_root: Path, source_ext: str) -> List[str]:
    """在项目中查找模块名对应的文件路径。"""
    candidates = []
    src_dirs = ['src', 'lib', 'pkg', 'app', 'internal']
    
    for src_dir in src_dirs:
        src_path = project_root / src_dir
        if not src_path.exists():
            continue
            
        for ext in [source_ext, '.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rs']:
            candidate = src_path / f"{module_name}{ext}"
            if candidate.exists():
                candidates.append(str(candidate.relative_to(project_root)).replace('\\', '/'))
                break
                
        index_files = ['index.ts', 'index.tsx', 'index.js', 'index.jsx', '__init__.py', 'mod.rs', 'lib.go']
        for idx_file in index_files:
            candidate = src_path / module_name / idx_file
            if candidate.exists():
                candidates.append(str(candidate.relative_to(project_root)).replace('\\', '/'))
                break
                
    return candidates
