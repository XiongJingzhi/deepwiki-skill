#!/usr/bin/env python3
"""项目结构分析脚本 — 扫描项目目录，识别项目类型、模块结构和文档位置。"""
import logging
import os, json
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

from scripts.core.common import (GitignoreCache, CACHE_SCHEMA_VERSION, validate_cache_version,
                    cache_dir, cache_path, state_dir, state_path)
from scripts.analysis.project_detection import (detect_project_types, find_entry_points,
                                detect_project_languages)
from scripts.core.importance_scoring import normalize_path_scores
from scripts.analysis.module_discovery import discover_modules, _update_module_scores
from scripts.analysis.scanner import scan_files
from scripts.analysis.extract_structure import detect_archetype


def analyze_project(project_root: str, save_to_cache: bool = True) -> Dict[str, Any]:
    """完整分析项目结构。返回含文件元数据、重要性评分、核心文件识别的字典。"""
    root = Path(project_root)
    root_resolved = root.resolve()

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
    _update_module_scores(modules, all_files)
    modules.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
    # ────────────────────────────────────────────────────────────────────

    # 核心文件: importance_score >= 0.5
    core_files = [f for f in all_files if f['is_core']]

    # 高优先级文件: importance_score >= 0.6（用于关系分析和深度分析的精确过滤）
    high_priority_files = [f for f in all_files if f.get('is_high_priority')]

    result = {
        'cache_schema_version': CACHE_SCHEMA_VERSION,
        'project_root': str(root_resolved),
        'project_name': root_resolved.name,
        'languages': languages,
        'archetype': archetype,
        'entry_points': entry_points,
        'modules': modules,
        'core_files': core_files,
        'high_priority_files': high_priority_files,
    }

    # 保存到缓存
    if save_to_cache:
        struct_cache_path = cache_path(root, 'structure.json')
        cache_dir(root).mkdir(parents=True, exist_ok=True)
        with open(struct_cache_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # 保存文件 hash 到 state/，供 detect_changes 复用（避免二次全量扫描）
        file_hashes = {}
        for f in all_files:
            if f.get('hash'):
                file_hashes[f['path']] = f['hash']
        hash_cache_path = state_path(root, 'file-hashes.json')
        state_dir(root).mkdir(parents=True, exist_ok=True)
        with open(hash_cache_path, 'w', encoding='utf-8') as f:
            json.dump({
                'cache_schema_version': CACHE_SCHEMA_VERSION,
                'hashes': file_hashes,
            }, f, ensure_ascii=False, indent=2)

    return result


def print_analysis(result: Dict[str, Any]):
    """打印分析结果"""
    print(f"项目: {result['project_name']}")
    if result.get('languages'):
        print(f"语言: {', '.join(result['languages'])}")
    print(f"原型: {result.get('archetype', '未知')}")

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


if __name__ == '__main__':
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    result = analyze_project(project_path, save_to_cache=True)
    print_analysis(result)
