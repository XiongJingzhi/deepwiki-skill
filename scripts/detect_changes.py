#!/usr/bin/env python3
"""
变更检测脚本
对比文件校验和，检测项目变更以支持增量更新
"""

import os
import json
import hashlib
import fnmatch
import yaml
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime, timezone

from common import (
    IGNORE_DIRS as DEFAULT_EXCLUDES,
    CODE_EXTENSIONS, DOC_EXTENSIONS,
    GitignoreCache, should_ignore_path,
    CACHE_SCHEMA_VERSION,
)

# 模块级 gitignore 缓存实例
_gitignore_cache = GitignoreCache()


def load_config_excludes(project_root: Path) -> Set[str]:
    """从 .deepwiki/config.yaml 读取 exclude 规则，合并到排除集合"""
    config_path = project_root / ".deepwiki" / "config.yaml"
    if not config_path.exists():
        return set()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        excludes = set()
        for pattern in config.get("exclude", []):
            pattern = str(pattern).strip()
            if pattern:
                if any(c in pattern for c in ('*', '?', '[')):
                    _gitignore_cache.globs.add(pattern.lstrip('*'))
                else:
                    excludes.add(pattern)
        return excludes
    except Exception:
        return set()


def _ensure_gitignore_loaded(root_path: Path):
    """加载 .gitignore（仅首次调用时执行）。"""
    _gitignore_cache.ensure_loaded(root_path)


def calculate_file_hash(file_path: str) -> str:
    """计算文件的 SHA256 哈希值"""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]  # 只取前16位
    except Exception:
        return ""


def should_include_file(file_path: Path, excludes: Set[str], config_excludes: Set[str] = None) -> bool:
    """判断文件是否应该被包含（硬编码规则 + config.yaml 排除 + .gitignore）"""
    all_excludes = excludes | (config_excludes or set())

    # 检查是否在排除目录中
    for part in file_path.parts:
        if part in all_excludes:
            return False
        # 检查 glob 模式
        for pattern in all_excludes:
            if '*' in pattern and fnmatch.fnmatch(file_path.name, pattern):
                return False

    # 检查 .gitignore 规则
    if _gitignore_cache.dirs and any(part in _gitignore_cache.dirs for part in file_path.parts):
        return False
    if _gitignore_cache.globs and any(fnmatch.fnmatch(file_path.name, p) for p in _gitignore_cache.globs):
        return False

    # 只包含代码和文档文件
    return file_path.suffix in CODE_EXTENSIONS or file_path.suffix in DOC_EXTENSIONS


def scan_project_files(project_root: str, excludes: Set[str] = None, config_excludes: Set[str] = None) -> Dict[str, str]:
    """
    扫描项目文件并计算校验和

    Args:
        project_root: 项目根目录
        excludes: 硬编码排除规则
        config_excludes: 从 config.yaml 读取的排除规则

    Returns:
        {相对路径: 校验和}
    """
    if excludes is None:
        excludes = DEFAULT_EXCLUDES

    root = Path(project_root)
    checksums = {}

    for file_path in root.rglob('*'):
        if file_path.is_file() and should_include_file(file_path, excludes, config_excludes):
            rel_path = str(file_path.relative_to(root))
            checksums[rel_path] = calculate_file_hash(str(file_path))

    return checksums


def load_cached_checksums(wiki_dir: str) -> Dict[str, Dict[str, str]]:
    """加载缓存的校验和，版本不匹配时返回空 dict 触发全量扫描。"""
    cache_path = Path(wiki_dir) / "cache" / "checksums.json"
    if cache_path.exists():
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 版本校验
        if data.get("cache_schema_version") is not None:
            if data["cache_schema_version"] != CACHE_SCHEMA_VERSION:
                return {}
            return data.get("checksums", {})
        # 遗留格式（无版本字段）：直接返回整个 dict
        return data
    return {}


def save_checksums(wiki_dir: str, checksums: Dict[str, Dict[str, str]]):
    """保存校验和到缓存（含版本号）"""
    cache_path = Path(wiki_dir) / "cache" / "checksums.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "checksums": checksums,
    }
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def propagate_reverse_dependencies(changed_modules: Set[str],
                                   structure: Dict[str, Any]) -> Set[str]:
    """
    反向依赖传播：当模块 A 变更时，将所有依赖 A 的模块也加入更新队列。

    使用 structure.json 中的模块文件列表和导入关系推断依赖方向。
    由于没有精确的依赖图，采用启发式方法：
    1. 从 structure.json 读取每个模块的 core_files 列表
    2. 扫描这些文件中的 import/use/require 语句
    3. 如果模块 B 的文件导入了模块 A 的文件，则 B 依赖 A

    Returns:
        需要更新（因反向依赖传播而新增）的模块名集合
    """
    if not changed_modules or not structure:
        return set()

    modules = structure.get('modules', [])
    if not modules:
        return set()

    # 构建模块名 -> 文件路径前缀的映射
    module_files: Dict[str, List[str]] = {}
    for mod in modules:
        mod_path = mod.get('path', '')
        # 标准化路径前缀（统一使用 / 分隔）
        prefix = mod_path.replace('\\', '/')
        if not prefix.endswith('/'):
            prefix += '/'
        module_files[mod['name']] = [prefix]

    # 构建变更模块的文件路径集合（用于匹配被导入的路径）
    changed_paths: Set[str] = set()
    for mod_name in changed_modules:
        if mod_name in module_files:
            changed_paths.update(module_files[mod_name])

    # 反向依赖：查找哪些模块导入了变更模块的文件
    affected_modules: Set[str] = set()
    import_patterns = [
        re.compile(r'''(?:from|import)\s+['"]([^'"]+)['"]'''),   # Python quoted: from "X" import Y
        re.compile(r'''(?:from|import)\s+([\w.]+)'''),           # Python bare: from X import Y, import X.Y
        re.compile(r'''(?:import|require)\s*\(?['"]([^'"]+)['"]'''),  # JS/TS
        re.compile(r'''use\s+['"]([^'"]+)['"]'''),                 # Rust
    ]

    # 缓存已读取的文件内容
    file_cache: Dict[str, str] = {}

    for mod in modules:
        mod_name = mod['name']
        if mod_name in changed_modules:
            continue

        core_files = mod.get('core_files', [])[:10]  # 限制扫描文件数
        for file_rel_path in core_files:
            if file_rel_path in file_cache:
                content = file_cache[file_rel_path]
            else:
                try:
                    # 从项目根目录读取文件
                    project_root = str(structure.get('project_root', '.')) \
                        if structure.get('project_root') else '.'
                    full_path = os.path.join(project_root, file_rel_path)
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    file_cache[file_rel_path] = content
                except Exception:
                    continue

            # 检查是否导入了任何变更模块的文件
            for pattern in import_patterns:
                for match in pattern.finditer(content):
                    import_path = match.group(1).replace('\\', '/').replace('.', '/')
                    for changed_prefix in changed_paths:
                        if import_path.startswith(changed_prefix) or changed_prefix.startswith(import_path):
                            affected_modules.add(mod_name)
                            break
                    if mod_name in affected_modules:
                        break
                if mod_name in affected_modules:
                    break
            if mod_name in affected_modules:
                break

    return affected_modules


def detect_changes(project_root: str, excludes: Set[str] = None,
                    dry_run: bool = False) -> Dict[str, Any]:
    """
    检测项目变更
    
    Returns:
        {
            "added": [新增的文件列表],
            "modified": [修改的文件列表],
            "deleted": [删除的文件列表],
            "unchanged": [未变更的文件列表],
            "has_changes": bool,
            "summary": 变更摘要字符串
        }
    """
    root = Path(project_root)
    wiki_dir = root / ".deepwiki"

    # 加载 .gitignore 规则
    _ensure_gitignore_loaded(root)

    # 加载 config.yaml 排除规则（与 analyze_project.py 保持一致）
    config_excludes = load_config_excludes(root)

    # 获取当前文件校验和
    current_checksums = scan_project_files(project_root, excludes, config_excludes)
    
    # 加载缓存的校验和
    cached = load_cached_checksums(str(wiki_dir))
    cached_checksums = {k: v.get('hash', '') for k, v in cached.items()}
    
    current_files = set(current_checksums.keys())
    cached_files = set(cached_checksums.keys())
    
    # 分类变更
    added = list(current_files - cached_files)
    deleted = list(cached_files - current_files)
    
    modified = []
    unchanged = []
    
    for file_path in current_files & cached_files:
        if current_checksums[file_path] != cached_checksums[file_path]:
            modified.append(file_path)
        else:
            unchanged.append(file_path)
    
    has_changes = bool(added or modified or deleted)
    
    summary_parts = []
    if added:
        summary_parts.append(f"+{len(added)} 新增")
    if modified:
        summary_parts.append(f"~{len(modified)} 修改")
    if deleted:
        summary_parts.append(f"-{len(deleted)} 删除")
    if not summary_parts:
        summary_parts.append("无变更")
    
    # 自动保存当前校验和到缓存，使下次检测能正确识别变更
    if not dry_run:
        update_checksums_cache(project_root, current_checksums)

    # ---- 反向依赖传播 ----
    # 将文件级变更映射到模块级，然后传播给依赖这些模块的其他模块
    changed_files = set(added + modified + deleted)
    affected_modules: Set[str] = set()
    reverse_affected: Set[str] = set()

    # 尝试从 structure.json 加载模块信息
    structure_path = root / ".deepwiki" / "cache" / "structure.json"
    structure = None
    if structure_path.exists():
        try:
            with open(structure_path, 'r', encoding='utf-8') as f:
                structure = json.load(f)
        except Exception:
            pass

    if structure:
        modules = structure.get('modules', [])
        # 构建模块名 -> 文件路径前缀的映射
        for mod in modules:
            mod_path = mod.get('path', '').replace('\\', '/')
            mod_prefix = mod_path + '/' if not mod_path.endswith('/') else mod_path
            for changed_file in changed_files:
                cf = changed_file.replace('\\', '/')
                if cf.startswith(mod_prefix) or cf == mod_path:
                    affected_modules.add(mod['name'])
                    break

        # 反向依赖传播
        reverse_affected = propagate_reverse_dependencies(affected_modules, structure)

    result = {
        "added": sorted(added),
        "modified": sorted(modified),
        "deleted": sorted(deleted),
        "unchanged": sorted(unchanged),
        "has_changes": has_changes,
        "summary": ", ".join(summary_parts),
        "current_checksums": current_checksums,
    }

    # 添加模块级变更信息
    if affected_modules or reverse_affected:
        result["affected_modules"] = sorted(affected_modules)
        result["reverse_affected_modules"] = sorted(reverse_affected)
        all_affected = affected_modules | reverse_affected
        if reverse_affected:
            summary_parts.append(f"⇠{len(reverse_affected)} 反向传播")
            result["summary"] = ", ".join(summary_parts)
            result["all_affected_modules"] = sorted(all_affected)

    return result


def update_checksums_cache(project_root: str, current_checksums: Dict[str, str], 
                           doc_mapping: Dict[str, str] = None):
    """
    更新校验和缓存
    
    Args:
        project_root: 项目根目录
        current_checksums: 当前文件校验和
        doc_mapping: 文件到文档的映射 {源文件: 生成的文档路径}
    """
    wiki_dir = Path(project_root) / ".deepwiki"
    
    if doc_mapping is None:
        doc_mapping = {}
    
    cache_data = {}
    for file_path, file_hash in current_checksums.items():
        cache_data[file_path] = {
            "hash": file_hash,
            "doc": doc_mapping.get(file_path, ""),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    save_checksums(str(wiki_dir), cache_data)


def print_changes(changes: Dict[str, Any]):
    """打印变更信息"""
    print(f"变更检测结果: {changes['summary']}")
    print()

    if changes["added"]:
        print("📁 新增文件:")
        for f in changes["added"][:10]:
            print(f"  + {f}")
        if len(changes["added"]) > 10:
            print(f"  ... 还有 {len(changes['added']) - 10} 个文件")

    if changes["modified"]:
        print("\n📝 修改的文件:")
        for f in changes["modified"][:10]:
            print(f"  ~ {f}")
        if len(changes["modified"]) > 10:
            print(f"  ... 还有 {len(changes['modified']) - 10} 个文件")

    if changes["deleted"]:
        print("\n🗑️ 删除的文件:")
        for f in changes["deleted"][:10]:
            print(f"  - {f}")
        if len(changes["deleted"]) > 10:
            print(f"  ... 还有 {len(changes['deleted']) - 10} 个文件")

    # 模块级变更信息
    affected_modules = changes.get("affected_modules", [])
    if affected_modules:
        print(f"\n📦 受影响的模块: {', '.join(affected_modules)}")

    reverse_modules = changes.get("reverse_affected_modules", [])
    if reverse_modules:
        print(f"⇠ 反向依赖传播（需联动的模块）: {', '.join(reverse_modules)}")


if __name__ == '__main__':
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    changes = detect_changes(project_path)
    print_changes(changes)
