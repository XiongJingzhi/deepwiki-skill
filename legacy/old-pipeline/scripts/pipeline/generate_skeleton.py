"""
generate_skeleton.py
为 generate-skeleton 工作流生成骨架的确定性字段，
减少 AI 需要处理的工作量（从 ~17K tokens 降至 ~4K tokens）。

AI 只需补充：
  - project_nature: 一句话描述项目性质和技术栈
  - key_data_flows: 2-3 条关键数据流描述

用法:
    python scripts/generate_skeleton.py <project_dir>

输出:
    cache/architecture-skeleton-draft.json（供 AI 补充后保存为 architecture-skeleton.json）
"""
import json
from pathlib import Path
from collections import defaultdict

from scripts.core.common import infer_code_purpose, get_module_files, UnionFind, build_file_to_module_map


_LAYER_MAP = {
    "Entry": "展示层/入口层",
    "Page": "展示层/入口层",
    "Widget": "展示层/入口层",
    "Api": "接口层",
    "Command": "接口层",
    "Service": "业务层",
    "Agent": "业务层",
    "Dao": "数据层",
    "Database": "数据层",
    "Model": "数据层",
    "Config": "基础设施层",
    "Util": "基础设施层",
    "Other": "其他",
    "Test": None,
}


def _module_primary_purpose(files: list) -> str:
    purposes = [infer_code_purpose(f) for f in files]
    priority = ["Entry", "Agent", "Api", "Command", "Service", "Dao", "Database", "Model", "Config", "Util", "Test", "Other"]
    for p in priority:
        if p in purposes:
            return p
    return "Other"


def _build_skeleton_input_summary(structure: dict, code_structure: dict) -> dict:
    """
    构建骨架生成所需的精简输入摘要（约 3-5K tokens），
    替代直接注入全量 code-structure.json（可达 100-200K tokens）。
    只保留模块级 import 关系和 archetype，去除函数级 call_graph。
    """
    modules_raw = structure.get("modules", {})
    # 兼容 modules 为 list 或 dict 格式
    if isinstance(modules_raw, list):
        modules = {m.get("path", m.get("name", "")): m for m in modules_raw}
    else:
        modules = modules_raw
    import_relations = code_structure.get("import_relations", {})
    archetype = code_structure.get("archetype", "unknown")

    file_to_module = build_file_to_module_map(modules)

    module_imports: dict = defaultdict(set)
    for file, imports in import_relations.items():
        src_mod = file_to_module.get(file)
        if not src_mod:
            continue
        if isinstance(imports, dict):
            imports = imports.get("imports", [])
        for imp in imports:
            if isinstance(imp, dict):
                tgt_path = imp.get("module", "")
            else:
                tgt_path = imp
            tgt_mod = file_to_module.get(tgt_path)
            if tgt_mod and tgt_mod != src_mod:
                module_imports[src_mod].add(tgt_mod)

    modules_summary = []
    for mod_path, mod_info in modules.items():
        files = get_module_files(mod_info)
        purpose = _module_primary_purpose(files)
        modules_summary.append({
            "name": mod_path,
            "purpose": purpose,
            "importance": mod_info.get("importance_score", 0),
            "imports": sorted(module_imports.get(mod_path, [])),
        })

    return {
        "archetype": archetype,
        "project_name": structure.get("project_name", ""),
        "tech_stack": structure.get("tech_stack", {}),
        "modules": modules_summary,
    }


def _build_module_dep_graph(modules: dict, import_relations: dict) -> dict:
    file_to_module = build_file_to_module_map(modules)

    dep_graph: dict = defaultdict(set)
    for file, data in import_relations.items():
        src_module = file_to_module.get(file)
        if not src_module:
            continue
        imports = data.get("imports", []) if isinstance(data, dict) else data
        for imp in imports:
            target_file = imp.get("module", "") if isinstance(imp, dict) else str(imp)
            tgt_module = file_to_module.get(target_file)
            if tgt_module and tgt_module != src_module:
                dep_graph[src_module].add(tgt_module)

    return dict(dep_graph)


def _cluster_modules(dep_graph: dict, all_modules: list) -> list:
    """
    Union-Find 将有依赖关系的模块聚为候选组。
    dep_weight(A,B) >= 1 即合并（有依赖即合并，后续可按阈值调整）。
    """
    uf = UnionFind(all_modules)

    for src, targets in dep_graph.items():
        for tgt in targets:
            if tgt in uf.parent:
                uf.union(src, tgt)

    return uf.groups()


def _build_architecture_layers(modules: dict) -> list:
    layers: dict = defaultdict(list)
    for mod_path, mod_info in modules.items():
        files = get_module_files(mod_info)
        purpose = _module_primary_purpose(files)
        layer = _LAYER_MAP.get(purpose)
        if layer:
            layers[layer].append(mod_path)

    layer_order = ["展示层/入口层", "接口层", "业务层", "数据层", "基础设施层", "其他"]
    return [
        {"layer": layer, "modules": sorted(layers[layer])}
        for layer in layer_order
        if layer in layers
    ]


def _build_cross_domain_deps(module_groups: list, dep_graph: dict) -> list:
    mod_to_group: dict = {}
    for group in module_groups:
        for mod in group["modules"]:
            mod_to_group[mod] = group["name"]

    cross_deps: set = set()
    for src, targets in dep_graph.items():
        src_grp = mod_to_group.get(src)
        for tgt in targets:
            tgt_grp = mod_to_group.get(tgt)
            if src_grp and tgt_grp and src_grp != tgt_grp:
                cross_deps.add((src_grp, tgt_grp))

    return [
        {"from": src_grp, "to": tgt_grp, "direction": "depends-on"}
        for src_grp, tgt_grp in sorted(cross_deps)
    ]


def generate_skeleton_structure(project_dir) -> dict:
    """
    生成骨架的确定性字段。

    Args:
        project_dir: 项目根目录（包含 .deepwiki/ 子目录）

    Returns:
        包含 module_groups / architecture_layers / cross_domain_dependencies /
        project_nature（空）/ key_data_flows（空）的字典
    """
    project_dir = Path(project_dir)
    cache_dir = project_dir / ".deepwiki" / "cache"

    structure_path = cache_dir / "structure.json"
    code_structure_path = cache_dir / "code-structure.json"

    if not structure_path.exists() or not code_structure_path.exists():
        raise FileNotFoundError(f"缺少必要输入文件：{structure_path} 或 {code_structure_path}")

    structure = json.loads(structure_path.read_text(encoding="utf-8"))
    code_structure = json.loads(code_structure_path.read_text(encoding="utf-8"))

    modules_raw = structure.get("modules", {})
    # 兼容 modules 为 list 或 dict 格式
    if isinstance(modules_raw, list):
        modules = {m.get("path", m.get("name", "")): m for m in modules_raw}
    else:
        modules = modules_raw
    import_relations: dict = code_structure.get("import_relations", {})

    all_module_list = list(modules.keys())
    dep_graph = _build_module_dep_graph(modules, import_relations)
    raw_clusters = _cluster_modules(dep_graph, all_module_list)

    module_groups = []
    for i, cluster in enumerate(raw_clusters):
        # 用集群中主要模块的 purpose 命名组
        purposes = [_module_primary_purpose(get_module_files(modules[m])) for m in cluster]
        dominant = max(set(purposes), key=purposes.count)
        module_groups.append({
            "name": f"group_{i+1}_{dominant.lower()}",
            "modules": sorted(cluster),
            "dominant_purpose": dominant,
        })

    architecture_layers = _build_architecture_layers(modules)
    cross_domain_dependencies = _build_cross_domain_deps(module_groups, dep_graph)

    summary = _build_skeleton_input_summary(structure, code_structure)

    return {
        "module_groups": module_groups,
        "architecture_layers": architecture_layers,
        "cross_domain_dependencies": cross_domain_dependencies,
        "project_nature": "",
        "key_data_flows": [],
        "_input_summary": summary,
    }


def main():
    import sys
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python -m scripts.pipeline.generate_skeleton <project_dir>")
        sys.exit(0 if len(sys.argv) >= 2 else 1)
    result = generate_skeleton_structure(Path(sys.argv[1]))
    out_path = Path(sys.argv[1]) / ".deepwiki" / "cache" / "architecture-skeleton.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"骨架已写入 {out_path}")
    print(f"  module_groups: {len(result['module_groups'])} 组")
    print(f"  architecture_layers: {len(result['architecture_layers'])} 层")
    print("  请 AI 补充 project_nature 和 key_data_flows 字段后覆写保存。")


if __name__ == "__main__":
    main()
