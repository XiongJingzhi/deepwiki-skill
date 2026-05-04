#!/usr/bin/env python3
"""
公共模块 - 提取 analyze_project.py 和 detect_changes.py 的共享逻辑。
使用 GitignoreCache 类替代模块级全局变量，避免跨项目状态泄漏。
"""

import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

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


# 已知的包管理器清单文件名（按语言分组）
MANIFEST_FILES = (
    "package.json", "requirements.txt", "pyproject.toml",
    "go.mod", "Cargo.toml", "pom.xml", "Gemfile",
)


def has_manifest(project_path: Path) -> bool:
    """检查项目目录下是否存在任何已知的包管理器清单文件。"""
    return any((project_path / m).exists() for m in MANIFEST_FILES)


def manifest_has_dependency(project_path: Path, names: Set[str]) -> bool:
    """Return True when a manifest contains any dependency name as a token.

    The boundary avoids false positives such as matching ``vue`` inside
    ``vuepress`` while still allowing package paths like ``github.com/gin-gonic``.
    """
    manifests = [project_path / m for m in MANIFEST_FILES]
    for manifest in manifests:
        if not manifest.exists():
            continue
        try:
            text = manifest.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        for name in names:
            escaped = re.escape(name.lower())
            pattern = re.compile(r'(?<![.\w-])' + escaped + r'(?![.\w-])')
            if pattern.search(text):
                return True
    return False


def validate_cache_version(data: dict, expected: int = None) -> bool:
    """检查缓存 dict 是否具有预期的 schema 版本。"""
    if expected is None:
        expected = CACHE_SCHEMA_VERSION
    version = data.get("cache_schema_version")
    if version is None:
        return False
    return version == expected


# ── 缓存路径工具函数 ────────────────────────────────────────────────────

def cache_dir(root: Path) -> Path:
    """返回 .deepwiki/cache/ 目录路径。"""
    return root / ".deepwiki" / "cache"


def cache_path(root: Path, name: str) -> Path:
    """返回 .deepwiki/cache/{name} 文件路径。"""
    return cache_dir(root) / name


def state_dir(root: Path) -> Path:
    """返回 .deepwiki/state/ 目录路径（流程状态，脚本专用）。"""
    return root / ".deepwiki" / "state"


def state_path(root: Path, name: str) -> Path:
    """返回 .deepwiki/state/{name} 文件路径。"""
    return state_dir(root) / name


def load_json(path: Path) -> dict:
    """安全加载 JSON 文件，文件不存在或解析失败时返回空字典。"""
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"警告: 无法读取 {path}: {e}", file=sys.stderr)
        return {}


# ── 共享工具函数 ──────────────────────────────────────────────────────────

def infer_code_purpose(file_path: str) -> str:
    """Layer 1 路径规则推断 CodePurpose。"""
    p = file_path.lower()
    if any(x in p for x in ["main.", "index.", "app."]):
        return "Entry"
    if "agent" in p:
        return "Agent"
    if any(x in p for x in ["/pages/", "/views/", "/screens/"]):
        return "Page"
    if any(x in p for x in ["/components/", "/widgets/", "/ui/"]):
        return "Widget"
    if "service" in p:
        return "Service"
    if any(x in p for x in ["/api/", "/endpoint/", "/controller/"]):
        return "Api"
    if any(x in p for x in ["/dao/", "/repository/", "/persistence/"]):
        return "Dao"
    if any(x in p for x in ["/models/", "/entities/", "/data/"]):
        return "Model"
    if any(x in p for x in ["/config/", ".toml", ".yaml", ".env"]):
        return "Config"
    if any(x in p for x in ["/utils/", "/helpers/"]):
        return "Util"
    if any(x in p for x in ["/commands/", "/cli/", "/cmd/"]):
        return "Command"
    if any(x in p for x in [".test.", ".spec.", "/__tests__/"]):
        return "Test"
    if any(x in p for x in ["/db/", "/database/", "/migrations/", ".sql", ".prisma"]):
        return "Database"
    return "Other"


def get_module_files(module_info: dict) -> list:
    """从 module_info 提取文件列表（兼容 files / core_files 字段）。

    files 字段可能是文件列表或整数计数。
    """
    files = module_info.get("files")
    if isinstance(files, int):
        return module_info.get("core_files", [])
    return files if isinstance(files, list) else module_info.get("core_files", [])


def calculate_file_hash(file_path: str) -> str:
    """计算文件的 SHA256 哈希值（截断到 HASH_TRUNCATE_LENGTH 位）。"""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()[:HASH_TRUNCATE_LENGTH]
    except Exception:
        return ""


class UnionFind:
    """并查集（Union-Find）数据结构，带路径压缩。"""

    def __init__(self, elements):
        self.parent = {e: e for e in elements}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

    def groups(self):
        """返回分组列表：[[elements], ...]"""
        from collections import defaultdict
        groups = defaultdict(list)
        for e in self.parent:
            groups[self.find(e)].append(e)
        return list(groups.values())


def build_file_to_module_map(
    modules,
    project_root: Optional[Path] = None,
    scan_fs: bool = False,
) -> dict:
    """构建 {文件路径: 模块标识} 映射。

    Args:
        modules: 两种格式之一：
            - dict: {模块路径: {"files": [...], ...}}
            - list: [{"path": ..., "name": ..., ...}]
        project_root: 项目根目录（scan_fs=True 时必需）
        scan_fs: 为 True 时扫描文件系统获取完整代码文件列表；
                 为 False 时从 modules 的 files/core_files 字段取

    Returns:
        {文件路径: 模块路径或模块名}
    """
    file_to_module: dict = {}

    if isinstance(modules, list) and scan_fs and project_root is not None:
        # 列表模式 + 文件系统扫描（refine_modules 使用）
        for mod in modules:
            mod_path = mod['path']
            prefix = mod_path + '/'
            mod_dir = project_root / mod_path
            if not mod_dir.exists():
                continue
            for f in mod_dir.rglob('*'):
                if f.is_file() and f.suffix in CODE_EXTENSIONS:
                    rel = str(f.relative_to(project_root)).replace('\\', '/')
                    if rel.startswith(prefix):
                        file_to_module[rel] = mod['name']
    elif isinstance(modules, list):
        # 列表模式，从每个模块的 files/core_files 字段取
        for mod in modules:
            mod_path = mod.get('path', mod.get('name', ''))
            mod_name = mod.get('name', mod_path)
            for f in get_module_files(mod):
                file_to_module[f] = mod_name
    elif isinstance(modules, dict):
        # dict 模式，从 files/core_files 字段取
        for mod_path, mod_info in modules.items():
            for f in get_module_files(mod_info):
                file_to_module[f] = mod_path
    else:
        raise ValueError(
            f"unsupported modules type: {type(modules).__name__}; "
            "expected dict or list"
        )

    return file_to_module


def load_module_analysis(project_path: Path, validate_version: bool = False) -> Optional[dict]:
    """加载 module-analysis.json。

    Args:
        project_path: 项目根目录
        validate_version: 为 True 时校验 cache_schema_version

    Returns:
        解析后的完整 dict，失败时返回 None。
    """
    analysis_path = cache_path(project_path, "module-analysis.json")
    if not analysis_path.exists():
        print(f"module-analysis.json 不存在: {analysis_path}", file=sys.stderr)
        return None
    try:
        with open(analysis_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"module-analysis.json JSON 解析失败: {e}", file=sys.stderr)
        return None
    if validate_version and not validate_cache_version(data):
        print("module-analysis.json schema version mismatch", file=sys.stderr)
        return None
    return data


def extract_file_source_ranges(
    file_data: dict,
    include_reason: bool = False,
) -> list:
    """从单个文件分析条目中提取 source-range 列表。

    同时处理 core_source_ranges 和 public_interfaces 两类来源。

    Args:
        file_data:      module-analysis.json 中单个文件条目（dict）
        include_reason: 为 True 时在每条 range 里附加 reason 字段
                        （plan_doc_topology 需要；build_evidence_index 不需要）

    Returns:
        [{"start_line": int, "end_line": int, "label": str, ?"reason": str}, ...]
    """
    ranges: list = []

    for source_range in file_data.get("core_source_ranges", []):
        if not isinstance(source_range, dict):
            continue
        start = source_range.get("start_line")
        end = source_range.get("end_line", start)
        if not start:
            continue
        entry: dict = {
            "start_line": start,
            "end_line": end,
            "label": source_range.get("label") or source_range.get("name") or "core source",
        }
        if include_reason:
            entry["reason"] = (
                source_range.get("reason") or source_range.get("summary") or "core source range"
            )
        ranges.append(entry)

    for interface in file_data.get("public_interfaces", []):
        if not isinstance(interface, dict):
            continue
        start = interface.get("line")
        end = interface.get("end_line", start)
        if not start:
            continue
        entry = {
            "start_line": start,
            "end_line": end,
            "label": interface.get("name") or "public interface",
        }
        if include_reason:
            entry["reason"] = "public interface"
        ranges.append(entry)

    return ranges


def merge_module_analysis_parts(cache_dir: Path, part_files: list, full_replace: bool = False) -> dict:
    """合并各个 subagent 写入的独立临时文件为 module-analysis.json。

    每个 part 文件格式为 {"<module_path>": { ... analysis data ... }}。
    合并策略：默认从已有 module-analysis.json 加载 modules，再用 part 覆盖。
    全量重建时可传 full_replace=True，从空集合开始。

    Args:
        cache_dir: .deepwiki/cache 目录
        part_files: 临时文件路径列表（Path 对象）
        full_replace: True 时忽略已有 module-analysis.json

    Returns:
        合并后的完整 module-analysis 数据 dict
    """
    modules: dict = {}
    analysis_path = Path(cache_dir) / "module-analysis.json"
    if not full_replace and analysis_path.exists():
        try:
            existing = json.loads(analysis_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict) and isinstance(existing.get("modules"), dict):
                modules.update(existing["modules"])
        except (json.JSONDecodeError, OSError):
            pass
    for part_path in part_files:
        if not part_path.exists():
            continue
        try:
            part = json.loads(part_path.read_text(encoding="utf-8"))
            if isinstance(part, dict):
                if isinstance(part.get("modules"), dict):
                    modules.update(part["modules"])
                else:
                    modules.update(part)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "modules": modules,
    }
