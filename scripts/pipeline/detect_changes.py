#!/usr/bin/env python3
"""
变更检测脚本
对比文件校验和，检测项目变更以支持增量更新
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

from scripts.core.common import (
    IGNORE_DIRS as DEFAULT_EXCLUDES,
    CODE_EXTENSIONS, DOC_EXTENSIONS,
    GitignoreCache, should_ignore_path,
    CACHE_SCHEMA_VERSION, HASH_TRUNCATE_LENGTH, validate_cache_version,
    cache_path, state_path, calculate_file_hash,
)


def _load_precomputed_hashes(project_path: Path):
    """从 analyze-project 阶段保存的 file-hashes.json 读取预计算 hash。

    当 file-hashes.json 存在且版本匹配时，直接返回预计算的 {rel_path: hash} dict，
    避免 detect_changes 再次全量遍历项目文件计算 hash。
    """
    hash_cache = state_path(project_path, "file-hashes.json")
    if hash_cache.exists():
        try:
            with open(hash_cache, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if validate_cache_version(data):
                return data.get("hashes", {})
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def load_config_excludes(project_root: Path, gitignore_cache: GitignoreCache = None) -> Set[str]:
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
                    if gitignore_cache:
                        gitignore_cache.globs.add(pattern.lstrip('*'))
                else:
                    excludes.add(pattern)
        return excludes
    except Exception:
        return set()


def should_include_file(file_path: Path, excludes: Set[str],
                        config_excludes: Set[str] = None,
                        gitignore_cache: GitignoreCache = None) -> bool:
    """判断文件是否应该被包含（硬编码规则 + config.yaml 排除 + .gitignore）"""
    all_excludes = excludes | (config_excludes or set())

    if gitignore_cache:
        if should_ignore_path(file_path, gitignore_cache, all_excludes):
            return False
    elif any(part in all_excludes for part in file_path.parts):
        return False

    # 只包含代码和文档文件
    return file_path.suffix in CODE_EXTENSIONS or file_path.suffix in DOC_EXTENSIONS


def scan_project_files(project_root: str, excludes: Set[str] = None,
                       config_excludes: Set[str] = None,
                       gitignore_cache: GitignoreCache = None) -> Dict[str, str]:
    """
    扫描项目文件并计算校验和

    Args:
        project_root: 项目根目录
        excludes: 硬编码排除规则
        config_excludes: 从 config.yaml 读取的排除规则
        gitignore_cache: GitignoreCache 实例

    Returns:
        {相对路径: 校验和}
    """
    if excludes is None:
        excludes = DEFAULT_EXCLUDES

    root = Path(project_root)
    checksums = {}

    for file_path in root.rglob('*'):
        if file_path.is_file() and should_include_file(file_path, excludes, config_excludes, gitignore_cache):
            rel_path = str(file_path.relative_to(root))
            checksums[rel_path] = calculate_file_hash(str(file_path))

    return checksums


def load_cached_checksums(wiki_dir: str) -> Dict[str, Dict[str, str]]:
    """加载缓存的校验和，版本不匹配时返回空 dict 触发全量扫描。"""
    checksums_path = Path(wiki_dir) / "state" / "checksums.json"
    if checksums_path.exists():
        with open(checksums_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if data["cache_schema_version"] != CACHE_SCHEMA_VERSION:
            return {}
        return data.get("checksums", {})
    return {}


def save_checksums(wiki_dir: str, checksums: Dict[str, Dict[str, str]]):
    """保存校验和到 state/（含版本号）"""
    checksums_path = Path(wiki_dir) / "state" / "checksums.json"
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "checksums": checksums,
    }
    with open(checksums_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _extract_import_paths_heuristic(file_rel_path: str, source: bytes) -> List[str]:
    """用 tree-sitter 从文件中提取 import 路径，用于启发式反向依赖检测。

    比 regex 更准确：不会匹配字符串或注释中的伪 import。
    """
    from scripts.core.parsers import get_lang_for_ext
    from scripts.analysis.import_relations import _extract_imports_from_source

    ext = Path(file_rel_path).suffix.lower()
    lang_name = get_lang_for_ext(ext)
    if not lang_name:
        return []

    try:
        return _extract_imports_from_source(source, lang_name)
    except Exception:
        return []


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

    # 缓存已读取的文件内容
    file_cache: Dict[str, bytes] = {}

    for mod in modules:
        mod_name = mod['name']
        if mod_name in changed_modules:
            continue

        core_files = mod.get('core_files', [])[:10]  # 限制扫描文件数
        for file_rel_path in core_files:
            if file_rel_path in file_cache:
                source = file_cache[file_rel_path]
            else:
                try:
                    project_root = str(structure.get('project_root', '.')) \
                        if structure.get('project_root') else '.'
                    full_path = os.path.join(project_root, file_rel_path)
                    with open(full_path, 'rb') as f:
                        source = f.read()
                    file_cache[file_rel_path] = source
                except Exception:
                    continue

            # 用 tree-sitter 提取 import 路径
            import_paths = _extract_import_paths_heuristic(file_rel_path, source)
            for import_path in import_paths:
                # 将 Python 点路径（core.index）规范化为斜线路径（core/index）
                # 以便与 changed_prefix（如 "core/"）进行前缀匹配
                normalized = import_path.replace(".", "/")
                if not normalized.endswith("/"):
                    normalized += "/"
                for changed_prefix in changed_paths:
                    if (normalized.startswith(changed_prefix)
                            or changed_prefix.startswith(normalized)
                            or import_path.startswith(changed_prefix)
                            or changed_prefix.startswith(import_path)):
                        affected_modules.add(mod_name)
                        break
                if mod_name in affected_modules:
                    break
            if mod_name in affected_modules:
                break

    return affected_modules


def _load_generation_plan(root: Path) -> Dict[str, Any]:
    plan_path = cache_path(root, "generation-plan.json")
    if not plan_path.exists():
        return {}
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _affected_pages_from_plan(
    generation_plan: Dict[str, Any],
    affected_modules: Set[str],
    has_changes: bool,
) -> Tuple[List[str], bool]:
    if not has_changes or not generation_plan:
        return [], False

    pages = generation_plan.get("pages", [])
    recompile_all = bool(generation_plan.get("recompile_all"))
    if recompile_all:
        return sorted(
            page.get("page_id")
            for page in pages
            if isinstance(page, dict) and page.get("page_id")
        ), True

    affected_pages: Set[str] = set()
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_id = page.get("page_id")
        page_modules = set(page.get("affected_modules", []))
        if page_id and page_modules & affected_modules:
            affected_pages.add(page_id)
    return sorted(affected_pages), False


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
    _gitignore_cache = GitignoreCache.get(root)

    # 加载 config.yaml 排除规则（与 analyze_project.py 保持一致）
    config_excludes = load_config_excludes(root, gitignore_cache=_gitignore_cache)

    # 获取当前文件校验和（优先使用 scanner 阶段预计算的 hash）
    precomputed = _load_precomputed_hashes(root)
    if precomputed is not None:
        current_checksums = precomputed
    else:
        current_checksums = scan_project_files(project_root, excludes, config_excludes,
                                               gitignore_cache=_gitignore_cache)
    
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
    affected_module_keys: Set[str] = set()

    # 尝试从 structure.json 加载模块信息
    structure_path = cache_path(root, "structure.json")
    structure = None
    if structure_path.exists():
        try:
            with open(structure_path, 'r', encoding='utf-8') as f:
                structure = json.load(f)
        except Exception:
            pass

    if structure:
        modules = structure.get('modules', [])
        module_lookup: Dict[str, Dict[str, str]] = {}
        for mod in modules:
            if mod.get('name'):
                module_lookup[mod['name']] = mod
        # 构建模块名 -> 文件路径前缀的映射
        for mod in modules:
            mod_path = mod.get('path', '').replace('\\', '/')
            mod_prefix = mod_path + '/' if not mod_path.endswith('/') else mod_path
            for changed_file in changed_files:
                cf = changed_file.replace('\\', '/')
                if cf.startswith(mod_prefix) or cf == mod_path:
                    affected_modules.add(mod['name'])
                    affected_module_keys.add(mod['name'])
                    if mod_path:
                        affected_module_keys.add(mod_path)
                    break

        # 反向依赖传播
        reverse_affected = propagate_reverse_dependencies(affected_modules, structure)
        for mod_name in reverse_affected:
            affected_module_keys.add(mod_name)
            mod = module_lookup.get(mod_name, {})
            mod_path = mod.get('path', '').replace('\\', '/')
            if mod_path:
                affected_module_keys.add(mod_path)

    all_affected_modules = affected_modules | reverse_affected
    generation_plan = _load_generation_plan(root)
    affected_pages, recompile_all = _affected_pages_from_plan(
        generation_plan, affected_module_keys or all_affected_modules, has_changes
    )

    result = {
        "added": sorted(added),
        "modified": sorted(modified),
        "deleted": sorted(deleted),
        "unchanged": sorted(unchanged),
        "has_changes": has_changes,
        "summary": ", ".join(summary_parts),
        "current_checksums": current_checksums,
        "affected_pages": affected_pages,
        "recompile_all": recompile_all,
    }

    # 添加模块级变更信息
    if affected_modules or reverse_affected:
        result["affected_modules"] = sorted(affected_modules)
        result["reverse_affected_modules"] = sorted(reverse_affected)
        if reverse_affected:
            summary_parts.append(f"⇠{len(reverse_affected)} 反向传播")
            result["summary"] = ", ".join(summary_parts)
            result["all_affected_modules"] = sorted(all_affected_modules)

    return result


def update_checksums_cache(project_root: str, current_checksums: Dict[str, str]):
    """
    更新校验和缓存

    Args:
        project_root: 项目根目录
        current_checksums: 当前文件校验和
    """
    wiki_dir = Path(project_root) / ".deepwiki"

    cache_data = {}
    for file_path, file_hash in current_checksums.items():
        cache_data[file_path] = {
            "hash": file_hash,
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

    affected_pages = changes.get("affected_pages", [])
    if affected_pages:
        print(f"\n📄 需重编译页面: {', '.join(affected_pages)}")
    if changes.get("recompile_all"):
        print("📄 generation-plan 要求全量页面重编译")


if __name__ == '__main__':
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    changes = detect_changes(project_path)
    print_changes(changes)
