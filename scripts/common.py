#!/usr/bin/env python3
"""
公共模块 - 提取 analyze_project.py 和 detect_changes.py 的共享逻辑。
使用 GitignoreCache 类替代模块级全局变量，避免跨项目状态泄漏。
"""

import fnmatch
from pathlib import Path
from typing import Set, Tuple

# 默认排除目录
IGNORE_DIRS = {
    'node_modules', '.git', 'dist', 'build', '__pycache__',
    '.next', '.nuxt', 'coverage', '.nyc_output', 'vendor',
    'venv', '.venv', 'env', '.env', 'eggs', '.eggs',
    '.tox', '.cache', '.pytest_cache', '.mypy_cache',
    '.deepwiki', '.agent'
}

# 默认排除文件
IGNORE_FILES = {
    '.DS_Store', 'Thumbs.db', '.gitignore', '.gitattributes',
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'poetry.lock', 'Pipfile.lock', 'composer.lock'
}

# 支持的代码文件扩展名
CODE_EXTENSIONS = {
    '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs',
    '.py', '.pyi',
    '.go', '.rs', '.java', '.kt', '.scala',
    '.rb', '.php', '.cs', '.fs',
    '.vue', '.svelte', '.astro'
}

# 文档扩展名
DOC_EXTENSIONS = {'.md', '.mdx', '.rst', '.txt'}


class GitignoreCache:
    """Per-root gitignore cache，避免模块级全局变量泄漏。"""

    def __init__(self):
        self.dirs: Set[str] = set()
        self.globs: Set[str] = set()
        self._loaded = False

    def ensure_loaded(self, root_path: Path):
        """加载 .gitignore（仅首次调用时执行）。"""
        if not self._loaded:
            self.dirs, self.globs = load_gitignore(root_path)
            self._loaded = True

    def reset(self):
        """重置缓存（测试用）。"""
        self.dirs = set()
        self.globs = set()
        self._loaded = False


def load_gitignore(root_path: Path) -> Tuple[Set[str], Set[str]]:
    """
    解析项目根目录的 .gitignore 文件。

    Returns:
        (dir_patterns, glob_patterns)
        - dir_patterns: 纯名称匹配（如 node_modules、.env）
        - glob_patterns: 通配符模式（如 *.log、*.pyc）
    """
    gitignore_path = root_path / '.gitignore'
    if not gitignore_path.exists():
        return set(), set()

    dir_patterns: Set[str] = set()
    glob_patterns: Set[str] = set()

    try:
        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.rstrip('\n\r')
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                # 移除行内注释
                if ' #' in stripped:
                    stripped = stripped[:stripped.index(' #')].strip()
                # 跳过取反规则
                if stripped.startswith('!'):
                    continue
                # 处理 **/ 前缀（匹配任意深度）
                if stripped.startswith('**/'):
                    stripped = stripped[3:]
                # 处理 /** 后缀（匹配目录及所有内容）
                elif stripped.endswith('/**'):
                    stripped = stripped[:-3]
                # 移除末尾 /（目录标记）
                stripped = stripped.rstrip('/')
                if not stripped:
                    continue

                if any(c in stripped for c in ('*', '?', '[')):
                    glob_patterns.add(stripped)
                else:
                    dir_patterns.add(stripped)
    except Exception:
        pass

    return dir_patterns, glob_patterns


def should_ignore_path(path: Path, cache: GitignoreCache,
                       extra_excludes: Set[str] = None) -> bool:
    """检查路径是否应被忽略。"""
    if extra_excludes and any(part in extra_excludes for part in path.parts):
        return True
    if cache.dirs and any(part in cache.dirs for part in path.parts):
        return True
    if cache.globs and any(fnmatch.fnmatch(path.name, p) for p in cache.globs):
        return True
    return False
