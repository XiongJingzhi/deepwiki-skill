"""Context Budget 计算"""

from pathlib import Path
from typing import Dict, List, Any

from common import CODE_EXTENSIONS

# 语言感知 token 估算比率（字符数 / 比率 ≈ token 数）
# 值越大表示该语言每 token 对应的字符数越多（越 "verbose"）
_LANGUAGE_TOKEN_RATIOS = {
    '.py': 4, '.pyi': 4,
    '.js': 5, '.jsx': 5, '.ts': 5, '.tsx': 5, '.mjs': 5, '.cjs': 5,
    '.go': 4,
    '.rs': 5,
    '.java': 4, '.kt': 4, '.scala': 4,
    '.rb': 4, '.php': 5,
    '.cs': 4, '.fs': 5,
    '.vue': 4, '.svelte': 4, '.astro': 5,
    '.c': 4, '.cpp': 4, '.h': 5, '.hpp': 5,
}


def estimate_token_cost(file_path: Path) -> int:
    """
    估算单个文件的 token 消耗。

    根据文件扩展名使用语言特定的比率，默认 4（通用近似值）。
    """
    try:
        size = file_path.stat().st_size
        ratio = _LANGUAGE_TOKEN_RATIOS.get(file_path.suffix.lower(), 4)
        return max(size // ratio, 100)
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

    预算根据项目代码总 token 量动态计算（按项目规模自适应上下限）：
    - 小项目 (<100K tokens): [50K, 200K]
    - 中项目 (<1M tokens):   [150K, 400K]
    - 大项目 (>=1M tokens):  [300K, 600K]
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
    # 预算上下限按项目规模自适应
    if total_code_tokens < 100_000:
        floor, ceiling = 50_000, 200_000
    elif total_code_tokens < 1_000_000:
        floor, ceiling = 150_000, 400_000
    else:
        floor, ceiling = 300_000, 600_000
    total_budget = max(floor, min(ceiling, int(total_code_tokens * analysis_ratio)))
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
