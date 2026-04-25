#!/usr/bin/env python3
"""
公共模块 - 提取 analyze_project.py 和 detect_changes.py 的共享逻辑。
使用 GitignoreCache 类替代模块级全局变量，避免跨项目状态泄漏。
"""

import fnmatch
import re
from pathlib import Path
from typing import Optional, Set, Tuple

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

# 缓存 schema 版本号 —— 任一缓存文件格式变更时递增此值
CACHE_SCHEMA_VERSION = 2

# ── 分析参数常量 ──────────────────────────────────────────────────────────
HASH_TRUNCATE_LENGTH = 16          # SHA256 hash 截断长度（位）
MAX_CALLS_PER_FUNCTION = 20        # 每个函数最多追踪的被调用函数数
MAX_BFS_DEPTH = 6                  # 调用图 BFS 最大遍历深度


class GitignoreCache:
    """Per-root gitignore cache，避免模块级全局变量泄漏。"""

    _instance: Optional['GitignoreCache'] = None
    _loaded_root: Optional[str] = None

    def __init__(self):
        self.dirs: Set[str] = set()
        self.globs: Set[str] = set()
        self._loaded = False

    @classmethod
    def get(cls, root_path):
        """获取或创建 GitignoreCache 单例，自动加载指定根目录的规则。"""
        if cls._instance is None or cls._loaded_root != str(root_path):
            cls._instance = cls()
            cls._instance.ensure_loaded(root_path)
            cls._loaded_root = str(root_path)
        return cls._instance

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
        GitignoreCache._instance = None
        GitignoreCache._loaded_root = None


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


def manifest_has_dependency(project_path: Path, names: Set[str]) -> bool:
    """Return True when a manifest contains any dependency name as a token.

    The boundary avoids false positives such as matching ``vue`` inside
    ``vuepress`` while still allowing package paths like ``github.com/gin-gonic``.
    """
    manifests = [
        project_path / "package.json",
        project_path / "requirements.txt",
        project_path / "pyproject.toml",
        project_path / "go.mod",
        project_path / "Cargo.toml",
    ]
    for manifest in manifests:
        if not manifest.exists():
            continue
        try:
            text = manifest.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        for name in names:
            escaped = re.escape(name.lower())
            pattern = re.compile(r'(?<![.\w-])' + escaped + r'(?![.\w])')
            if pattern.search(text):
                return True
    return False


def validate_cache_version(data: dict, expected: int = None) -> bool:
    """检查缓存 dict 是否具有预期的 schema 版本。

    Returns True if version matches or no version field exists (legacy).
    Returns False if version exists and does not match.
    """
    if expected is None:
        expected = CACHE_SCHEMA_VERSION
    version = data.get("cache_schema_version")
    if version is None:
        return True  # 遗留缓存，无版本字段
    return version == expected


# ── 缓存路径工具函数 ────────────────────────────────────────────────────

def cache_dir(root: Path) -> Path:
    """返回 .deepwiki/cache/ 目录路径。"""
    return root / ".deepwiki" / "cache"


def cache_path(root: Path, name: str) -> Path:
    """返回 .deepwiki/cache/{name} 文件路径。"""
    return cache_dir(root) / name
