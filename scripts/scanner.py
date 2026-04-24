"""文件与目录扫描 -- 从 analyze_project.py 提取。

负责扫描项目文件/目录，计算元数据、重要性评分、复杂度和重要行数。
支持可选的 parse_cache 和 gitignore_cache 参数以复用已有解析结果。
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

from common import IGNORE_DIRS, IGNORE_FILES, CODE_EXTENSIONS, HASH_TRUNCATE_LENGTH, should_ignore_path
from importance_scoring import calculate_file_importance
from code_metrics import estimate_complexity, count_important_lines, compute_complexity_and_important_lines


def scan_files(root_path: Path, gitignore_cache=None, parse_cache=None,
               archetype: str = None, import_degrees: Dict[str, int] = None) -> List[Dict[str, Any]]:
    """
    扫描所有非忽略文件，计算元数据和重要性评分

    Args:
        root_path: 项目根目录
        gitignore_cache: GitignoreCache 实例（可选）
        parse_cache: {rel_path: cached_entry} 字典（可选），
                     来自 parse-results.json，用于复用 AST 解析结果
        archetype: 项目原型标签（可选），传递给 calculate_file_importance 用于动态权重
        import_degrees: {rel_path: in_degree_count} 字典（可选），
                        每个文件被 import 的次数，用于 importance 评分

    返回文件列表，按重要性评分降序排列。
    包含所有文件类型（不仅是代码文件），用于全面的 project view。
    """
    if import_degrees is None:
        import_degrees = {}
    files = []
    for f in root_path.rglob('*'):
        if not f.is_file():
            continue
        if gitignore_cache is not None and should_ignore_path(f, gitignore_cache, IGNORE_DIRS):
            continue
        if f.name in IGNORE_FILES:
            continue
        # 排除二进制文件
        ext = f.suffix.lower()
        if ext in {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
                   '.woff', '.woff2', '.ttf', '.eot', '.otf',
                   '.zip', '.tar', '.gz', '.rar', '.7z',
                   '.exe', '.dll', '.so', '.dylib', '.bin',
                   '.wasm', '.mp4', '.mp3', '.pdf', '.doc', '.docx'}:
            continue

        try:
            size = f.stat().st_size
        except OSError:
            size = 0

        # 计算文件 SHA256 hash（截断），供 detect_changes 复用，避免二次遍历
        file_hash = ""
        try:
            sha256 = hashlib.sha256()
            with open(f, 'rb') as fh:
                for chunk in iter(lambda: fh.read(8192), b''):
                    sha256.update(chunk)
            file_hash = sha256.hexdigest()[:HASH_TRUNCATE_LENGTH]
        except (OSError, IOError):
            pass

        rel_path = str(f.relative_to(root_path)).replace('\\', '/')
        is_code = ext in CODE_EXTENSIONS

        # 获取分数明细（用于后续归一化）
        file_import_degree = import_degrees.get(rel_path, 0)
        breakdown = calculate_file_importance(
            f, root_path, size, return_breakdown=True,
            archetype=archetype, import_degree=file_import_degree
        )
        importance = breakdown['total']

        if is_code:
            if parse_cache and rel_path in parse_cache:
                cached = parse_cache[rel_path]
                complexity = cached.get("complexity_score", 0)
                important_lines = cached.get("important_lines_count", 0)
            else:
                complexity, important_lines = compute_complexity_and_important_lines(f)
        else:
            complexity = 0
            important_lines = 0

        files.append({
            'path': rel_path,
            'name': f.name,
            'size': size,
            'hash': file_hash,
            'extension': ext,
            'is_code': is_code,
            'importance_score': round(importance, 2),
            'complexity_score': complexity,
            'important_lines_count': important_lines,
            'is_core': importance >= 0.5,
            # 高优先级档位：score >= 0.6，用于关系分析和深度分析阶段的精确过滤
            # 参考 deepwiki-rs：关系分析阶段仅处理 importance_score >= 0.6 的文件
            'is_high_priority': importance >= 0.6,
            # 原始分数（用于模块内归一化）
            'raw_path_score': breakdown['path_score'],
            'raw_identity_score': breakdown['identity_score'],
            'raw_lang_score': breakdown['lang_score'],
            'raw_size_score': breakdown['size_score'],
            'raw_import_degree_score': breakdown.get('import_degree_score', 0.0),
        })

    # 按重要性评分降序
    files.sort(key=lambda x: x['importance_score'], reverse=True)
    return files


def scan_directories(root_path: Path, gitignore_cache=None) -> List[Dict[str, Any]]:
    """
    扫描目录结构，计算目录重要性评分

    Args:
        root_path: 项目根目录
        gitignore_cache: GitignoreCache 实例（可选）

    因子:
    - 核心源码 (+0.4): 名称为 src 或 lib
    - 核心模块 (+0.3): 名称包含 core 或 main
    - 文件丰富 (+0.2): 包含超过 5 个代码文件
    - 深层嵌套 (+0.1): 包含超过 2 个子目录
    """
    directories = []
    for dir_path in root_path.rglob('*'):
        if not dir_path.is_dir():
            continue
        if gitignore_cache is not None and should_ignore_path(dir_path, gitignore_cache, IGNORE_DIRS):
            continue

        rel_path = str(dir_path.relative_to(root_path)).replace('\\', '/')
        name = dir_path.name

        try:
            code_file_count = sum(
                1 for f in dir_path.iterdir()
                if f.is_file() and f.suffix in CODE_EXTENSIONS
            )
            subdir_count = sum(
                1 for d in dir_path.iterdir()
                if d.is_dir() and d.name not in IGNORE_DIRS and not d.name.startswith('.')
            )
        except PermissionError:
            continue

        # 目录重要性评分
        score = 0.0
        if name in ('src', 'lib', 'pkg', 'cmd', 'internal'):
            score += 0.4
        if any(k in name.lower() for k in ('core', 'main', 'engine', 'kernel')):
            score += 0.3
        if code_file_count > 5:
            score += 0.2
        elif code_file_count > 0:
            score += 0.1
        if subdir_count > 2:
            score += 0.1

        directories.append({
            'path': rel_path,
            'name': name,
            'file_count': code_file_count,
            'subdirectory_count': subdir_count,
            'importance_score': round(min(score, 1.0), 2),
        })

    # 按重要性降序
    directories.sort(key=lambda x: x['importance_score'], reverse=True)
    return directories


def compute_file_stats(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算文件类型分布和大小分布统计"""
    # 文件类型分布（仅代码文件）
    file_types: Dict[str, int] = {}
    for f in files:
        if f['is_code']:
            ext = f['extension']
            file_types[ext] = file_types.get(ext, 0) + 1

    # 按数量降序排列
    file_types = dict(sorted(file_types.items(), key=lambda x: x[1], reverse=True))

    # 大小分布
    size_distribution = {'tiny': 0, 'small': 0, 'medium': 0, 'large': 0}
    for f in files:
        size = f['size']
        if size < 1024:         # < 1KB
            size_distribution['tiny'] += 1
        elif size < 10240:      # 1KB - 10KB
            size_distribution['small'] += 1
        elif size < 51200:      # 10KB - 50KB
            size_distribution['medium'] += 1
        else:                   # > 50KB
            size_distribution['large'] += 1

    return {
        'file_types': file_types,
        'size_distribution': size_distribution,
    }


def find_documentation(root_path: Path) -> List[str]:
    """发现现有文档"""
    doc_patterns = [
        'README.md', 'README.*.md', 'readme.md',
        'CHANGELOG.md', 'HISTORY.md', 'changelog.md',
        'CONTRIBUTING.md', 'ARCHITECTURE.md', 'DESIGN.md',
        'API.md', 'SECURITY.md', 'LICENSE', 'LICENSE.md',
        'docs/*.md', 'documentation/*.md'
    ]

    docs = []
    for pattern in doc_patterns:
        if '*' in pattern:
            docs.extend(str(p.relative_to(root_path)) for p in root_path.glob(pattern))
        elif (root_path / pattern).exists():
            docs.append(pattern)

    return docs
