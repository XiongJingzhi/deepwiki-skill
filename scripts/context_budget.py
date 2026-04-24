"""Context Budget 计算"""

from pathlib import Path
from typing import Dict, List, Any

from common import CODE_EXTENSIONS


def estimate_token_cost(file_path: Path) -> int:
    """
    估算单个文件的 token 消耗。

    简化模型：字符数 / 4（经验值，适合大多数语言）
    """
    try:
        size = file_path.stat().st_size
        base_tokens = size // 4
        return max(base_tokens, 100)
    except Exception:
        return 200


def compute_context_budget(all_files: List[Dict[str, Any]],
                           project_root: Path) -> Dict[str, Any]:
    """
    计算 Context Budget 分配方案（动态计算，基于项目实际代码量）。

    三阶段漏斗：
    1. 快速扫描：所有核心文件，仅元数据
    2. 重点深入：Budget 允许范围内的高优先级文件
    3. 按需补读：生成阶段发现缺口时回读

    预算根据项目代码总 token 量动态计算：
    - 总预算 = max(80K, min(500K, total_tokens * 0.3))
    - 生成预留 = 总预算 * 1/3
    """
    # 估算项目代码总 token 量
    total_code_tokens = 0
    code_files = [f for f in all_files
                  if f.get("path", "").split(".")[-1].lower() in
                  {e.lstrip(".") for e in CODE_EXTENSIONS}]
    for f in code_files:
        fpath = project_root / f["path"]
        if fpath.exists():
            total_code_tokens += estimate_token_cost(fpath)

    # 动态计算预算
    analysis_ratio = 0.3
    total_budget = max(80000, min(500000, int(total_code_tokens * analysis_ratio)))
    reserved_ratio = 0.33
    reserved_for_generation = int(total_budget * reserved_ratio)
    available_for_analysis = total_budget - reserved_for_generation

    # 估算每个文件的 token 消耗
    file_costs = {}
    for f in all_files:
        fpath = project_root / f['path']
        if fpath.exists():
            file_costs[f['path']] = estimate_token_cost(fpath)
        else:
            file_costs[f['path']] = 200

    sorted_files = sorted(all_files, key=lambda x: x['importance_score'], reverse=True)

    # 阶段 1：快速扫描
    quick_scan_files = [f for f in sorted_files if f['is_core']]
    quick_scan_cost = sum(file_costs.get(f['path'], 200) // 10 for f in quick_scan_files)

    # 阶段 2：重点深入
    remaining_budget = available_for_analysis - quick_scan_cost
    deep_analysis_files = []
    deep_analysis_cost = 0

    high_priority = [f for f in sorted_files if f.get('is_high_priority') and f not in quick_scan_files]
    for f in high_priority:
        cost = file_costs.get(f['path'], 200)
        if deep_analysis_cost + cost <= remaining_budget:
            deep_analysis_files.append(f['path'])
            deep_analysis_cost += cost
        else:
            break

    return {
        'total_budget': total_budget,
        'reserved_for_generation': reserved_for_generation,
        'available_for_analysis': available_for_analysis,
        'quick_scan': {
            'file_count': len(quick_scan_files),
            'estimated_cost': quick_scan_cost,
        },
        'deep_analysis': {
            'file_count': len(deep_analysis_files),
            'estimated_cost': deep_analysis_cost,
            'files': deep_analysis_files[:20],
        },
        'remaining_budget': remaining_budget - deep_analysis_cost,
        'estimated_file_costs': {k: v for k, v in list(file_costs.items())[:50]},
    }
