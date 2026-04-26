#!/usr/bin/env python3
"""项目结构分析脚本 — 扫描项目目录，识别项目类型、模块结构和文档位置。"""
import logging
import os, json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from common import (GitignoreCache, CACHE_SCHEMA_VERSION, validate_cache_version,
                    cache_dir, cache_path)
from project_detection import (detect_project_types, find_entry_points,
                                detect_project_languages)
from importance_scoring import normalize_path_scores
from context_budget import compute_context_budget
from module_discovery import discover_modules
from scanner import (scan_files, scan_directories, compute_file_stats,
                     find_documentation)
from extract_structure import detect_archetype


def analyze_project(project_root: str, save_to_cache: bool = True) -> Dict[str, Any]:
    """完整分析项目结构。返回含文件元数据、重要性评分、核心文件识别的字典。"""
    root = Path(project_root)

    # 加载 .gitignore 规则
    _gitignore_cache = GitignoreCache.get(root)

    # 检测项目类型
    project_types = detect_project_types(root)

    # 检测项目主要语言
    languages = detect_project_languages(root)

    # 发现入口文件
    entry_points = find_entry_points(root, project_types)

    # Try loading parse cache (extract-structure may have populated it)
    _parse_cache_data = None
    pc_path = cache_path(root, 'parse-results.json')
    if pc_path.exists():
        try:
            pc_data = json.loads(pc_path.read_text('utf-8'))
            if validate_cache_version(pc_data):
                _parse_cache_data = pc_data.get('files', {})
        except Exception:
            logger.warning("Failed to load parse-results.json, skipping parse cache")

    # 检测 archetype（直接扫描 manifest 文件，而非从缓存读取旧值）
    archetype = detect_archetype(root)

    # 尝试从 code-structure.json 读取 import_degrees（如已存在）
    import_degrees: Dict[str, int] = {}
    cs_path = cache_path(root, 'code-structure.json')
    if cs_path.exists():
        try:
            cs_data = json.loads(cs_path.read_text('utf-8'))
            # 优先使用 code-structure.json 中已计算的 import_degrees
            precomputed = cs_data.get('import_degrees')
            if precomputed:
                import_degrees = precomputed
        except Exception:
            logger.warning("Failed to load code-structure.json, skipping import degrees")

    # 扫描所有文件（含重要性评分和复杂度估算，archetype + import_degree 感知）
    all_files = scan_files(root, gitignore_cache=_gitignore_cache,
                           parse_cache=_parse_cache_data,
                           archetype=archetype,
                           import_degrees=import_degrees)

    # 发现模块（传入文件数据用于计算模块重要性）
    modules = discover_modules(root, all_files=all_files)

    # 模块内归一化 path_score，重新计算重要性评分（archetype 感知权重）
    all_files = normalize_path_scores(all_files, modules, archetype=archetype)

    # 重新排序（归一化后分数可能变化）
    all_files.sort(key=lambda x: x['importance_score'], reverse=True)

    # ── 归一化后重算模块重要性 ──────────────────────────────────────────
    # normalize_path_scores 修改了文件的 importance_score，
    # 必须重新计算模块的平均分、core_files 列表和 core_files_count，
    # 否则模块排名将基于归一化前的文件分数，导致高估。
    for mod in modules:
        mod_prefix = mod['path'].rstrip('/') + '/'
        mod_files = [f for f in all_files
                     if f['path'].startswith(mod_prefix) or f['path'] == mod['path']]
        if mod_files:
            avg_score = sum(f['importance_score'] for f in mod_files) / len(mod_files)
            mod['importance_score'] = round(avg_score, 2)
            mod['core_files'] = [f['path'] for f in mod_files if f['is_core']][:20]
            mod['core_files_count'] = len([f for f in mod_files if f['is_core']])
    # 按归一化后的重要性重排模块
    modules.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
    # ────────────────────────────────────────────────────────────────────

    # 核心文件: importance_score >= 0.5
    core_files = [f for f in all_files if f['is_core']]

    # 高优先级文件: importance_score >= 0.6（用于关系分析和深度分析的精确过滤）
    high_priority_files = [f for f in all_files if f.get('is_high_priority')]

    # 发现文档
    docs = find_documentation(root)

    # 扫描目录
    directories = scan_directories(root, gitignore_cache=_gitignore_cache)

    # 文件统计
    file_stats = compute_file_stats(all_files)

    code_file_count = sum(1 for f in all_files if f['is_code'])

    result = {
        'cache_schema_version': CACHE_SCHEMA_VERSION,
        'project_root': str(root.resolve()),
        'project_name': root.name,
        'project_type': project_types,
        'languages': languages,
        'archetype': archetype,
        'entry_points': entry_points,
        'modules': modules,
        'core_files': core_files,
        'high_priority_files': high_priority_files,
        'directories': directories,
        'file_types': file_stats['file_types'],
        'size_distribution': file_stats['size_distribution'],
        'docs_found': docs,
        'stats': {
            'total_files': len(all_files),
            'code_files': code_file_count,
            'core_files_count': len(core_files),
            'high_priority_files_count': len(high_priority_files),
            'total_modules': len(modules),
            'total_directories': len(directories),
            'total_docs': len(docs),
        },
        'context_budget': compute_context_budget(all_files, root),
        'analyzed_at': datetime.now(timezone.utc).isoformat()
    }

    # 保存到缓存
    if save_to_cache:
        struct_cache_path = cache_path(root, 'structure.json')
        cache_dir(root).mkdir(parents=True, exist_ok=True)
        with open(struct_cache_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # 保存文件 hash 到 cache，供 detect_changes 复用（避免二次全量扫描）
        file_hashes = {}
        for f in all_files:
            if f.get('hash'):
                file_hashes[f['path']] = f['hash']
        hash_cache_path = cache_path(root, 'file-hashes.json')
        hash_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(hash_cache_path, 'w', encoding='utf-8') as f:
            json.dump({
                'cache_schema_version': CACHE_SCHEMA_VERSION,
                'hashes': file_hashes,
            }, f, ensure_ascii=False, indent=2)

    return result


def print_analysis(result: Dict[str, Any]):
    """打印分析结果"""
    stats = result['stats']
    print(f"项目: {result['project_name']}")
    print(f"技术栈: {', '.join(result['project_type']) or '未知'}")
    if result.get('languages'):
        print(f"语言: {', '.join(result['languages'])}")
    print(f"统计: {stats['code_files']} 个代码文件, "
          f"{stats['core_files_count']} 个核心文件, "
          f"{stats['high_priority_files_count']} 个高优先级文件, "
          f"{stats['total_modules']} 个模块, "
          f"{stats['total_files']} 个总文件")

    if result['entry_points']:
        print(f"\n入口文件:")
        for entry in result['entry_points']:
            print(f"  - {entry}")

    if result['modules']:
        print(f"\n模块 (按重要性排序):")
        for module in result['modules'][:10]:
            score = module.get('importance_score', 0)
            core = module.get('core_files_count', 0)
            print(f"  - {module['name']} ({module['files']} 文件, "
                  f"重要性: {score}, 核心文件: {core})")

    if result.get('high_priority_files'):
        print(f"\n高优先级文件 (importance >= 0.6, 用于关系分析):")
        for f in result['high_priority_files'][:10]:
            print(f"  - {f['path']} (评分: {f['importance_score']}, "
                  f"复杂度: {f['complexity_score']}, 重要行: {f['important_lines_count']})")
        if len(result['high_priority_files']) > 10:
            print(f"  ... 共 {len(result['high_priority_files'])} 个高优先级文件")

    if result.get('core_files'):
        print(f"\n核心文件 (importance >= 0.5):")
        for f in result['core_files'][:15]:
            print(f"  - {f['path']} (评分: {f['importance_score']}, "
                  f"复杂度: {f['complexity_score']}, 重要行: {f['important_lines_count']})")
        if len(result['core_files']) > 15:
            print(f"  ... 共 {len(result['core_files'])} 个核心文件")

    if result['docs_found']:
        print(f"\n现有文档:")
        for doc in result['docs_found']:
            print(f"  - {doc}")

    if result.get('file_types'):
        print(f"\n文件类型分布:")
        for ext, count in list(result['file_types'].items())[:8]:
            print(f"  - {ext}: {count}")


if __name__ == '__main__':
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    result = analyze_project(project_path, save_to_cache=True)
    print_analysis(result)
