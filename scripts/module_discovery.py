"""模块发现与分类 -- 从 analyze_project.py 提取。

负责扫描项目目录结构，发现业务模块，基于文件重要性计算模块优先级。
支持基于 import 连通分量的模块边界修正分析。
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

from common import IGNORE_DIRS, CODE_EXTENSIONS
from importance_scoring import calculate_file_importance


def _read_workspace_packages(root_path: Path) -> List[str]:
    """读取 monorepo workspace 配置，返回包目录名列表。"""
    packages = []

    # pnpm-workspace.yaml
    pnpm_ws = root_path / "pnpm-workspace.yaml"
    if pnpm_ws.exists():
        try:
            import yaml
            with open(pnpm_ws, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            for pattern in data.get("packages", []):
                if '/*' in pattern:
                    base = pattern.replace('/*', '').strip()
                    if base and (root_path / base).is_dir():
                        packages.append(base)
        except Exception:
            pass

    # package.json workspaces
    pkg = root_path / "package.json"
    if pkg.exists():
        try:
            with open(pkg, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ws = data.get("workspaces", [])
            if isinstance(ws, list):
                for pattern in ws:
                    if '/*' in pattern:
                        base = pattern.replace('/*', '').strip()
                        if base and (root_path / base).is_dir():
                            packages.append(base)
            elif isinstance(ws, dict):
                # npm workspaces as { "packages": [...] }
                for pattern in ws.get("packages", []):
                    if '/*' in pattern:
                        base = pattern.replace('/*', '').strip()
                        if base and (root_path / base).is_dir():
                            packages.append(base)
        except Exception:
            pass

    return packages


def discover_modules(root_path: Path, exclude_dirs: Set[str] = None,
                    all_files: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """发现项目模块，基于文件重要性计算模块优先级

    扫描策略（两阶段）：
    1. 优先扫描 src/lib/packages/apps/modules 等标准源码目录下的直接子目录。
       此阶段不使用 FLAT_ROOT_SKIP，确保 src/config/、src/models/ 等合法业务模块不被误跳过。
    2. 若第一阶段未发现模块（扁平结构项目），则回退到根目录一级扫描。
       此阶段使用 FLAT_ROOT_SKIP 过滤纯工具/文档目录，避免误识别为业务模块。

    重要：FLAT_ROOT_SKIP 只控制「根目录的哪些一级目录不被识别为模块」，
    不影响已选中模块内部的文件计数（防止模块内 config/ 子目录的文件被漏计）。
    """
    if exclude_dirs is None:
        exclude_dirs = IGNORE_DIRS

    # 扁平结构回退时，用于过滤根目录一级非业务目录的集合。
    # 注意：仅用于判断"某个根目录下的一级目录是否应被识别为业务模块"，
    #       不用于过滤模块内部的文件路径。
    FLAT_ROOT_SKIP = {
        'scripts', 'script', 'tools', 'tool',
        'plugins', 'plugin', 'extensions', 'extension',
        'references', 'reference', 'docs', 'doc', 'documentation',
        'assets', 'asset', 'static', 'public',
        'tests', 'test', '__tests__', 'spec', 'specs',
        'examples', 'example', 'samples', 'sample',
        'fixtures', 'mocks', 'stubs',
        'config', 'configs', 'configuration',
        '.github', '.vscode', '.idea',
    }

    modules = []
    src_dirs = ['src', 'lib', 'packages', 'apps', 'modules']

    # ── 阶段 0：读取 monorepo workspace 配置 ─────────────────────────────────
    workspace_dirs = _read_workspace_packages(root_path)
    if workspace_dirs:
        src_dirs = list(set(workspace_dirs + src_dirs))

    # ── 阶段一：扫描标准源码目录下的子目录 ──────────────────────────────────
    # 此阶段只用 exclude_dirs（技术排除目录），不使用 FLAT_ROOT_SKIP，
    # 确保 src/config/、src/models/ 等合法业务模块不被误跳过。
    for src_dir in src_dirs:
        src_path = root_path / src_dir
        if not src_path.exists():
            continue

        for item in src_path.iterdir():
            if item.is_dir() and item.name not in exclude_dirs:
                file_count = sum(
                    1 for f in item.rglob('*')
                    if f.is_file()
                    and f.suffix in CODE_EXTENSIONS
                    and not any(p in f.parts for p in exclude_dirs)
                )
                if file_count > 0:
                    modules.append({
                        'name': item.name,
                        'path': str(item.relative_to(root_path)).replace('\\', '/'),
                        'files': file_count,
                        'type': categorize_module(item.name),
                    })

    # ── 阶段二：扁平结构回退——扫描根目录一级子目录 ──────────────────────────
    # 仅在阶段一未发现任何模块时触发。
    # FLAT_ROOT_SKIP 只用于入口判断（决定该目录是否作为模块），
    # 统计文件数时仍只排除 exclude_dirs，避免模块内同名子目录文件被漏计。
    if not modules:
        root_skip = exclude_dirs | FLAT_ROOT_SKIP
        for item in root_path.iterdir():
            if (item.is_dir()
                    and item.name not in root_skip
                    and not item.name.startswith('.')):
                file_count = sum(
                    1 for f in item.rglob('*')
                    if f.is_file()
                    and f.suffix in CODE_EXTENSIONS
                    and not any(p in f.parts for p in exclude_dirs)  # 只排除技术目录
                )
                if file_count > 0:
                    modules.append({
                        'name': item.name,
                        'path': item.name,
                        'files': file_count,
                        'type': categorize_module(item.name),
                    })

    # 计算模块重要性: 基于模块内文件的平均重要性
    if all_files:
        for mod in modules:
            mod_prefix = mod['path'] + '/'
            mod_files = [f for f in all_files
                        if f['path'].startswith(mod_prefix) or f['path'] == mod['path']]
            if mod_files:
                avg_score = sum(f['importance_score'] for f in mod_files) / len(mod_files)
                core_count = sum(1 for f in mod_files if f['is_core'])
                mod['importance_score'] = round(avg_score, 2)
                mod['core_files_count'] = core_count
                mod['core_files'] = [f['path'] for f in mod_files if f['is_core']][:20]
            else:
                mod['importance_score'] = 0.0
                mod['core_files_count'] = 0
                mod['core_files'] = []

    # 按重要性降序排列
    modules.sort(key=lambda x: x.get('importance_score', 0), reverse=True)

    return modules


def categorize_module(name: str) -> str:
    """根据名称分类模块"""
    name_lower = name.lower()

    if any(k in name_lower for k in ['component', 'ui', 'view', 'page', 'screen']):
        return 'ui'
    elif any(k in name_lower for k in ['api', 'service', 'handler', 'middleware', 'controller', 'router']):
        return 'api'
    elif any(k in name_lower for k in ['migration', 'entity', 'model', 'schema', 'repository', 'dao']):
        return 'data'
    elif any(k in name_lower for k in ['util', 'helper', 'common', 'shared']):
        return 'utility'
    elif any(k in name_lower for k in ['core', 'lib', 'engine', 'kernel']):
        return 'core'
    elif any(k in name_lower for k in ['config', 'setting']):
        return 'config'
    elif any(k in name_lower for k in ['test', 'spec', '__tests__', '__mocks__']):
        return 'test'
    else:
        return 'module'


# ── import 连通分量分析 ────────────────────────────────────────────────────────

# 默认阈值常量
_MERGE_DENSITY_THRESHOLD = 0.5   # 跨模块 import 密度阈值，超过此值且双向引用则建议合并
_SPLIT_COMPONENT_RATIO = 0.5     # 模块内最大连通分量占比阈值，低于此值则建议拆分


def _build_file_to_module_map(
    modules: List[Dict], project_root: Path
) -> Dict[str, str]:
    """构建文件路径 → 模块名的映射。

    根据模块 path 前缀匹配：文件路径以模块 path + '/' 开头，则归属该模块。

    Args:
        modules: discover_modules 的输出列表
        project_root: 项目根目录

    Returns:
        {文件相对路径（正斜杠）: 模块名}
    """
    file_to_module: Dict[str, str] = {}
    for mod in modules:
        mod_path = mod['path']
        prefix = mod_path + '/'
        # 扫描模块目录下的代码文件
        mod_dir = project_root / mod_path
        if not mod_dir.exists():
            continue
        for f in mod_dir.rglob('*'):
            if f.is_file() and f.suffix in CODE_EXTENSIONS:
                rel = str(f.relative_to(project_root)).replace('\\', '/')
                if rel.startswith(prefix):
                    file_to_module[rel] = mod['name']
    return file_to_module


def _build_module_adjacency(
    file_to_module: Dict[str, str],
    import_relations: Dict[str, List[str]],
) -> Dict[str, Dict[str, int]]:
    """将文件级 import 关系聚合为模块级邻接图。

    Args:
        file_to_module: 文件 → 模块映射
        import_relations: {文件路径: [被导入文件路径]}

    Returns:
        {模块A: {模块B: import次数, ...}, ...}
    """
    adjacency: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for src_file, targets in import_relations.items():
        src_mod = file_to_module.get(src_file)
        if not src_mod:
            continue
        for tgt_file in targets:
            tgt_mod = file_to_module.get(tgt_file)
            if tgt_mod and tgt_mod != src_mod:
                adjacency[src_mod][tgt_mod] += 1
    return dict(adjacency)


def _compute_cross_density(
    mod_a: str, mod_b: str,
    adjacency: Dict[str, Dict[str, int]],
    file_to_module: Dict[str, str],
) -> float:
    """计算两个模块之间的跨模块 import 密度。

    密度 = (A→B + B→A 的 import 次数) / (A 的文件数 + B 的文件数)

    Args:
        mod_a, mod_b: 模块名
        adjacency: 模块邻接图
        file_to_module: 文件 → 模块映射

    Returns:
        密度值
    """
    count_ab = adjacency.get(mod_a, {}).get(mod_b, 0)
    count_ba = adjacency.get(mod_b, {}).get(mod_a, 0)
    cross_imports = count_ab + count_ba

    files_a = sum(1 for m in file_to_module.values() if m == mod_a)
    files_b = sum(1 for m in file_to_module.values() if m == mod_b)
    total_files = files_a + files_b

    if total_files == 0:
        return 0.0
    return cross_imports / total_files


def _compute_internal_components(
    mod_name: str,
    file_to_module: Dict[str, str],
    import_relations: Dict[str, List[str]],
) -> List[Set[str]]:
    """计算模块内部的 import 连通分量（仅限模块内文件之间的连接）。

    使用并查集（Union-Find）算法计算连通分量。

    Args:
        mod_name: 模块名
        file_to_module: 文件 → 模块映射
        import_relations: {文件路径: [被导入文件路径]}

    Returns:
        连通分量列表，每个分量是该模块内文件路径的集合
    """
    # 收集该模块的所有文件
    mod_files = {f for f, m in file_to_module.items() if m == mod_name}
    if not mod_files:
        return []

    # 并查集实现
    parent: Dict[str, str] = {f: f for f in mod_files}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # 路径压缩
            x = parent[x]
        return x

    def union(x: str, y: str) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    # 遍历该模块文件的 import 关系，仅处理模块内部的连接
    for src_file, targets in import_relations.items():
        if src_file not in mod_files:
            continue
        for tgt_file in targets:
            if tgt_file in mod_files:
                union(src_file, tgt_file)

    # 提取连通分量
    components: Dict[str, Set[str]] = defaultdict(set)
    for f in mod_files:
        components[find(f)].add(f)

    return list(components.values())


def refine_modules(
    modules: List[Dict],
    import_relations: Dict[str, List[str]],
    project_root: Path,
    merge_density_threshold: float = _MERGE_DENSITY_THRESHOLD,
    split_component_ratio: float = _SPLIT_COMPONENT_RATIO,
) -> List[Dict]:
    """基于 import 连通分量修正模块边界。

    策略：
    1. 将 import_relations 聚合到模块级别
    2. 计算跨模块 import 密度
    3. 高密度跨模块 import → 建议合并
    4. 模块内不连通子分量 → 建议拆分

    不实际合并/拆分模块，只在 refine_notes 中给出建议，保持接口稳定。

    Args:
        modules: discover_modules 的输出
        import_relations: {file_path: [imported_file_paths]}
        project_root: 项目根目录
        merge_density_threshold: 跨模块 import 密度阈值，默认 0.5
        split_component_ratio: 模块内最大连通分量占比阈值，默认 0.5

    Returns:
        修正后的模块列表（新增 refine_notes 字段）
    """
    # 深拷贝以避免修改原始数据
    refined = [dict(mod) for mod in modules]

    if not modules or not import_relations:
        return refined

    # 步骤 1：构建文件 → 模块映射
    file_to_module = _build_file_to_module_map(modules, project_root)

    # 步骤 2：聚合为模块级邻接图
    adjacency = _build_module_adjacency(file_to_module, import_relations)

    # 步骤 3：跨模块 import 密度分析 → 检测合并建议
    seen_pairs: Set[Tuple[str, str]] = set()
    merge_suggestions: Dict[str, List[str]] = defaultdict(list)

    for mod_a in adjacency:
        for mod_b in adjacency[mod_a]:
            pair = tuple(sorted([mod_a, mod_b]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            density = _compute_cross_density(mod_a, mod_b, adjacency, file_to_module)

            # 密度超过阈值且双向都有 import → 建议合并
            count_ab = adjacency.get(mod_a, {}).get(mod_b, 0)
            count_ba = adjacency.get(mod_b, {}).get(mod_a, 0)
            if density > merge_density_threshold and count_ab > 0 and count_ba > 0:
                merge_suggestions[mod_a].append(
                    f"建议与 [{mod_b}] 合并：跨模块 import 密度 {density:.2f} "
                    f"(A→B={count_ab}, B→A={count_ba})"
                )
                merge_suggestions[mod_b].append(
                    f"建议与 [{mod_a}] 合并：跨模块 import 密度 {density:.2f} "
                    f"(B→A={count_ba}, A→B={count_ab})"
                )

    # 步骤 4：模块内连通分量分析 → 检测拆分建议
    for mod in refined:
        mod_name = mod['name']
        notes = []

        # 添加合并建议（如果有）
        if mod_name in merge_suggestions:
            notes.extend(merge_suggestions[mod_name])

        # 分析模块内连通分量
        components = _compute_internal_components(mod_name, file_to_module, import_relations)
        if components:
            total_files = sum(len(c) for c in components)
            largest = max(len(c) for c in components)
            if total_files > 0 and largest < total_files * split_component_ratio:
                num_components = len(components)
                notes.append(
                    f"建议拆分：模块内存在 {num_components} 个不连通分量，"
                    f"最大分量占 {largest}/{total_files} ({largest/total_files:.0%})，"
                    f"低于阈值 {split_component_ratio:.0%}"
                )

        if notes:
            mod['refine_notes'] = '; '.join(notes)

    return refined


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python module_discovery.py refine <project_path>")
        sys.exit(1)

    action = sys.argv[1]
    project_path = Path(sys.argv[2])

    if action == "refine":
        # 读取 structure.json 和 code-structure.json
        structure_path = project_path / ".deepwiki" / "cache" / "structure.json"
        code_structure_path = project_path / ".deepwiki" / "cache" / "code-structure.json"

        with open(structure_path, 'r', encoding='utf-8') as f:
            structure = json.load(f)
        with open(code_structure_path, 'r', encoding='utf-8') as f:
            code_structure = json.load(f)

        modules = structure.get("modules", [])
        import_relations = code_structure.get("import_relations", {})

        refined = refine_modules(modules, import_relations, project_path)

        # 输出建议
        has_notes = [m for m in refined if m.get("refine_notes")]
        if has_notes:
            print("模块边界修正建议：")
            for m in has_notes:
                print(f"  [{m['name']}] {m['refine_notes']}")
        else:
            print("模块边界合理，无需修正。")
    else:
        print(f"未知操作: {action}")
        sys.exit(1)
