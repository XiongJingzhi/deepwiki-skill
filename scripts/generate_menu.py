#!/usr/bin/env python3
"""
导航菜单生成脚本

两种模式：
  默认模式：扫描 wiki/ 目录下所有 .md 文件，生成层级化 menu.json。
  --reconcile 模式：读取已有 menu.json，与实际文件校验并修正。

分组策略（默认模式）：
  - 有 cache_dir 时，数据驱动分组：
    1. architecture-skeleton.json 的 module_groups（骨架分组）
    2. module-analysis.json 的 semantic_group（语义标注）
    3. 纯依赖聚类（import_relations Union-Find）
    4. 平铺回退（单 "模块" 分区）
  - 无 cache_dir 时，平铺回退（保持向后兼容）
"""

import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from common import CACHE_SCHEMA_VERSION

# 多语言标签映射
_LABELS = {
    'zh': {'overview': '概览', 'modules': '模块', 'more': '更多',
           'module_doc': '模块文档', 'api_ref': 'API 参考'},
    'en': {'overview': 'Overview', 'modules': 'Modules', 'more': 'More',
           'module_doc': 'Module Doc', 'api_ref': 'API Reference'},
}


def _labels(wiki_dir: str) -> Dict[str, str]:
    """根据 config.yaml 的 language 设置返回标签字典。"""
    config_path = Path(wiki_dir).parent / 'config.yaml'
    lang = 'zh'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
            lang = cfg.get('generation', {}).get('language', 'zh')
            if lang not in _LABELS:
                lang = 'zh' if lang == 'both' else 'en'
        except Exception:
            pass
    return _LABELS.get(lang, _LABELS['zh'])


def extract_title(file_path: str) -> str:
    """从 Markdown 文件的第一行 H1 标题提取标题，无标题时用文件名。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('# '):
                    return stripped[2:].strip()
    except Exception:
        pass
    return Path(file_path).stem.replace('-', ' ').replace('_', ' ').title()


# =====================================================================
# 辅助函数：JSON / 数据加载
# =====================================================================


def _load_json(path: Path, default=None):
    """安全加载 JSON 文件，读取失败时返回 default。"""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return default


def _extract_semantic_groups(analysis: dict) -> Dict[str, str]:
    """从 module-analysis.json 提取 {module_name: semantic_group} 映射。

    兼容两种格式：
    - 字典格式 {"modules": {"auth": {"semantic_group": "...", ...}, ...}}
    - 数组格式 {"modules": [{"name": "auth", "semantic_group": "...", ...}, ...]}
    """
    groups: Dict[str, str] = {}
    if not analysis:
        return groups
    if isinstance(analysis, dict):
        modules = analysis.get('modules', {})
        if isinstance(modules, dict):
            for mod_name, mod_data in modules.items():
                if isinstance(mod_data, dict):
                    sg = mod_data.get('semantic_group')
                    if sg:
                        groups[mod_name] = sg
        elif isinstance(modules, list):
            for item in modules:
                mod_name = item.get('module_path', item.get('name', ''))
                sg = item.get('semantic_group')
                if sg:
                    groups[mod_name] = sg
    return groups


def _load_import_relations(cache_dir: str) -> Dict[str, List[str]]:
    """从 code-structure.json 加载 import_relations。"""
    cs_path = Path(cache_dir) / 'code-structure.json'
    cs = _load_json(cs_path)
    if not cs:
        return {}
    return cs.get('import_relations', {})


# =====================================================================
# 辅助函数：模块文件收集与映射
# =====================================================================


def _collect_module_files(wiki_path: Path) -> List[Path]:
    """收集 wiki/modules/*.md 文件（跳过 index.md / _index.md）。"""
    modules_dir = wiki_path / 'modules'
    if not modules_dir.exists():
        return []
    return sorted([
        f for f in modules_dir.glob('*.md')
        if f.name not in ('index.md', '_index.md')
    ])


def _map_module_names_to_files(module_files: List[Path], wiki_path: Path) -> Dict[str, Dict]:
    """将模块文件映射为 {module_stem: {"file": Path, "title": str, "has_api": bool}}。"""
    api_dir = wiki_path / 'api'
    mapping: Dict[str, Dict] = {}
    for md_file in module_files:
        title = extract_title(str(md_file))
        module_name = md_file.stem
        if title and title != module_name.title():
            display = title
        else:
            display = module_name
        mapping[module_name] = {
            'file': md_file,
            'title': display,
            'has_api': (api_dir / md_file.name).exists(),
        }
    return mapping


# =====================================================================
# 辅助函数：菜单项构造
# =====================================================================


def _make_module_item(module_name: str, file_info: dict, L: dict) -> Dict:
    """创建一个模块菜单项（含子项：模块文档 + 可选 API 文档）。"""
    md_file = file_info['file']
    title = file_info['title']
    children: List[Dict[str, str]] = [
        {'title': L['module_doc'], 'path': f'modules/{md_file.name}'},
    ]
    if file_info.get('has_api'):
        children.append({'title': L['api_ref'], 'path': f'api/{md_file.name}'})
    return {'title': title, 'items': children}


def _envelope(menu: list, project_name: str) -> Dict[str, Any]:
    """构建菜单数据外层包。"""
    return {
        'cache_schema_version': CACHE_SCHEMA_VERSION,
        'title': project_name or '',
        'version': '1.0',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'menu': menu,
    }


# =====================================================================
# 辅助函数：菜单分区构建
# =====================================================================


def _build_overview_section(wiki_path: Path, L: dict) -> Optional[Dict]:
    """构建概览分区（overview.md / getting-started.md / doc-map.md）。"""
    overview_items: List[Dict[str, str]] = []
    for filename in ('overview.md', 'getting-started.md', 'doc-map.md'):
        target = wiki_path / filename
        if target.exists():
            title = extract_title(str(target))
            overview_items.append({
                'title': title if title else target.stem,
                'path': filename,
            })
    if overview_items:
        return {'title': L['overview'], 'items': overview_items}
    return None


def _build_menu_from_topology(
    topology: dict, project_name: str, L: dict,
) -> Optional[Dict[str, Any]]:
    """优先根据 doc-topology.json 组装菜单。

    这里允许页面尚未实际生成，适合在编译前阶段先产出稳定导航结构。
    """
    pages = topology.get('pages')
    groupings = topology.get('groupings')
    if not isinstance(pages, list) or not isinstance(groupings, dict):
        return None

    page_map = {
        page.get('id'): page
        for page in pages
        if isinstance(page, dict) and page.get('id') and page.get('output_path')
    }
    if not page_map:
        return None

    menu: List[Dict[str, Any]] = []
    for raw_group_title, page_ids in groupings.items():
        if not isinstance(page_ids, list):
            continue
        section_title = L['overview'] if raw_group_title == 'overview' else raw_group_title
        direct_items: List[Dict[str, str]] = []
        module_items: Dict[str, Dict[str, Any]] = {}

        for page_id in page_ids:
            page = page_map.get(page_id)
            if not page:
                continue

            path = page.get('output_path', '')
            if path.startswith('wiki/'):
                path = path[5:]
            page_type = page.get('type')

            if page_type in {'overview', 'guide', 'map'}:
                direct_items.append({
                    'title': page.get('title') or Path(path).stem,
                    'path': path,
                })
                continue

            if page_type not in {'module', 'api'}:
                direct_items.append({
                    'title': page.get('title') or Path(path).stem,
                    'path': path,
                })
                continue

            module_name = Path(path).stem
            item = module_items.setdefault(module_name, {
                'title': module_name,
                'items': [],
            })
            if page_type == 'module':
                item['title'] = page.get('title') or module_name
                item['items'].append({'title': L['module_doc'], 'path': path})
            else:
                item['items'].append({'title': L['api_ref'], 'path': path})

        if module_items:
            menu.append({'title': section_title, 'items': list(module_items.values())})
        elif direct_items:
            menu.append({'title': section_title, 'items': direct_items})

    if not menu:
        return None
    return _envelope(menu, project_name)


def _group_modules_flat(wiki_path: Path, L: dict) -> List[Dict]:
    """无分析数据时的平铺回退（保持原有行为：单 "模块" 分区）。

    用于 cache_dir 为 None 时的向后兼容路径。
    """
    module_files = _collect_module_files(wiki_path)
    if not module_files:
        return []

    name_to_files = _map_module_names_to_files(module_files, wiki_path)
    module_items = [
        _make_module_item(name, info, L)
        for name, info in name_to_files.items()
    ]
    return [{'title': L['modules'], 'items': module_items}]


def _group_modules(wiki_path: Path, cache_dir: str, L: dict,
                   analysis: dict = None) -> List[Dict]:
    """数据驱动的模块分组。

    优先级：
    1. architecture-skeleton.json 的 module_groups（骨架分组）
    2. module-analysis.json 的 semantic_group（语义标注）
    3. 纯依赖聚类（import_relations Union-Find）
    4. 平铺回退

    Args:
        analysis: 预加载的 module-analysis.json 数据，避免重复读取
    """
    module_files = _collect_module_files(wiki_path)
    if not module_files:
        return []

    name_to_files = _map_module_names_to_files(module_files, wiki_path)
    cache_path = Path(cache_dir)

    # --- 策略 1: skeleton module_groups ---
    skeleton = _load_json(cache_path / 'architecture-skeleton.json')
    if skeleton:
        module_groups = skeleton.get('module_groups')
        if module_groups and isinstance(module_groups, list) and len(module_groups) > 0:
            sections = _apply_skeleton_groups(module_groups, name_to_files, L)
            if sections:
                # 将未被 skeleton 覆盖的模块追加到末尾的"其他模块"分区
                covered = set()
                for group in module_groups:
                    covered.update(group.get('modules', []))
                remaining = {
                    name: info for name, info in name_to_files.items()
                    if name not in covered
                }
                if remaining:
                    fallback = _cluster_by_semantic_group_or_flat(
                        remaining, cache_dir, L, analysis=analysis,
                    )
                    sections.extend(fallback)
                return sections

    # --- 策略 2: semantic_group ---
    if analysis is None:
        analysis = _load_json(cache_path / 'module-analysis.json')
    semantic_map = _extract_semantic_groups(analysis)
    if semantic_map:
        # 筛选在 semantic_map 中有标注的模块
        annotated = {
            name: info for name, info in name_to_files.items()
            if name in semantic_map
        }
        unannotated = {
            name: info for name, info in name_to_files.items()
            if name not in semantic_map
        }

        sections = _cluster_by_semantic_group(semantic_map, annotated, L)
        if sections:
            # 将无标注的模块追加到末尾
            if unannotated:
                fallback = _cluster_by_semantic_group_or_flat(
                    unannotated, cache_dir, L, analysis=analysis,
                )
                sections.extend(fallback)
            return sections

    # --- 策略 3: 依赖聚类（Union-Find） ---
    import_relations = _load_import_relations(cache_dir)
    if import_relations:
        sections = _cluster_by_import_relations(
            import_relations, name_to_files, wiki_path, L,
        )
        if sections:
            return sections

    # --- 策略 4: 平铺回退 ---
    return _group_modules_flat(wiki_path, L)


def _apply_skeleton_groups(module_groups: list, name_to_files: dict, L: dict) -> List[Dict]:
    """使用 skeleton module_groups 分组。"""
    sections: List[Dict] = []
    for group in module_groups:
        group_name = group.get('name', '')
        modules = group.get('modules', [])
        items = []
        for mod_name in modules:
            if mod_name in name_to_files:
                items.append(_make_module_item(mod_name, name_to_files[mod_name], L))
        if items:
            sections.append({'title': group_name, 'items': items})
    return sections


def _cluster_by_semantic_group(
    semantic_map: Dict[str, str], name_to_files: dict, L: dict,
) -> List[Dict]:
    """按 semantic_group 聚合模块。组名直接用 semantic_group 值。"""
    sg_to_modules: Dict[str, List[str]] = defaultdict(list)
    for mod_name, sg in semantic_map.items():
        if mod_name in name_to_files:
            sg_to_modules[sg].append(mod_name)

    sections: List[Dict] = []
    for sg_name in sorted(sg_to_modules.keys()):
        mod_names = sorted(sg_to_modules[sg_name])
        items = [_make_module_item(name, name_to_files[name], L) for name in mod_names]
        sections.append({'title': sg_name, 'items': items})
    return sections


def _cluster_by_import_relations(
    import_relations: Dict[str, List[str]],
    name_to_files: dict,
    wiki_path: Path,
    L: dict,
) -> List[Dict]:
    """基于 import_relations 的 Union-Find 依赖聚类。

    将文件路径归一化为模块名（与 modules/*.md 的 stem 对应），
    然后通过导入关系做连通分量聚类。

    注意：此处的 Union-Find 专注于「导航分组」，与
    module_discovery.py:refine_modules 的 Union-Find（专注于「模块边界修正」）
    目的不同但算法相似。两者共享 import_relations 数据源。
    """
    # Union-Find 实现
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])  # 路径压缩
            x = parent[x]
        return x

    def union(a: str, b: str):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # 将文件路径映射到模块名
    file_to_module: Dict[str, str] = {}
    for mod_name in name_to_files:
        file_to_module[mod_name] = mod_name
        # 也尝试匹配 src/xxx.py -> xxx 这样的常见路径
        for fpath in import_relations:
            fname = Path(fpath).stem
            if fname == mod_name:
                file_to_module[fpath] = mod_name

    # 构建连通分量
    for fpath, imports in import_relations.items():
        src_mod = None
        for mod_name in name_to_files:
            if Path(fpath).stem == mod_name:
                src_mod = mod_name
                break
        if not src_mod:
            continue
        for imp in imports:
            imp_mod = None
            for mod_name in name_to_files:
                if Path(imp).stem == mod_name:
                    imp_mod = mod_name
                    break
            if imp_mod:
                union(src_mod, imp_mod)

    # 按连通分量分组
    clusters: Dict[str, List[str]] = defaultdict(list)
    for mod_name in name_to_files:
        root = find(mod_name)
        clusters[root].append(mod_name)

    # 只保留多于 1 个模块的聚类作为有意义分组，其余合并为 "模块"
    sections: List[Dict] = []
    multi_clusters = []
    single_modules = []
    for root in sorted(clusters.keys()):
        mods = sorted(clusters[root])
        if len(mods) > 1:
            multi_clusters.append(mods)
        else:
            single_modules.extend(mods)

    for mods in multi_clusters:
        items = [_make_module_item(name, name_to_files[name], L) for name in mods]
        sections.append({'title': L['modules'], 'items': items})

    if single_modules:
        items = [_make_module_item(name, name_to_files[name], L) for name in single_modules]
        sections.append({'title': L['modules'], 'items': items})

    return sections


def _cluster_by_semantic_group_or_flat(
    name_to_files: dict, cache_dir: str, L: dict,
    analysis: dict = None,
) -> List[Dict]:
    """对一组模块先尝试 semantic_group 分组，无数据则平铺。"""
    if analysis is None:
        analysis = _load_json(Path(cache_dir) / 'module-analysis.json')
    semantic_map = _extract_semantic_groups(analysis)
    if semantic_map:
        filtered = {
            name: info for name, info in name_to_files.items()
            if name in semantic_map
        }
        if filtered:
            return _cluster_by_semantic_group(semantic_map, filtered, L)
    # 平铺回退
    items = [_make_module_item(name, info, L) for name, info in name_to_files.items()]
    return [{'title': L['modules'], 'items': items}] if items else []


def _build_more_section(wiki_path: Path, L: dict) -> Optional[Dict]:
    """构建"更多"分区（其他顶层文件 + 自定义子目录）。"""
    known_top_files = {'overview.md', 'getting-started.md', 'doc-map.md'}
    other_top: List[Dict[str, str]] = []
    for md_file in sorted(wiki_path.glob('*.md')):
        if md_file.name not in known_top_files:
            title = extract_title(str(md_file))
            other_top.append({
                'title': title if title != md_file.stem.title() else md_file.stem,
                'path': md_file.name,
            })

    known_dirs = {'modules', 'api', 'assets'}
    subdir_items: List[Dict[str, Any]] = []
    for subdir in sorted(wiki_path.iterdir()):
        if not subdir.is_dir() or subdir.name.startswith('.') or subdir.name.startswith('_'):
            continue
        if subdir.name in known_dirs:
            continue
        subdir_docs: List[Dict[str, str]] = []
        for md_file in sorted(subdir.glob('*.md')):
            title = extract_title(str(md_file))
            subdir_docs.append({
                'title': title if title != md_file.stem.title() else md_file.stem,
                'path': f'{subdir.name}/{md_file.name}',
            })
        if subdir_docs:
            subdir_items.append({'title': subdir.name, 'items': subdir_docs})

    if other_top or subdir_items:
        more_items: List[Dict[str, Any]] = []
        if other_top:
            more_items.append({'title': '其他', 'items': other_top})
        more_items.extend(subdir_items)
        return {'title': L['more'], 'items': more_items}
    return None


# =====================================================================
# 主函数
# =====================================================================


def build_menu(wiki_dir: str, project_name: str = '', cache_dir: str = None) -> Dict[str, Any]:
    """
    从 wiki 目录结构生成层级化导航菜单（默认模式）。

    目录布局:
      wiki/overview.md, wiki/getting-started.md, wiki/doc-map.md
      wiki/modules/*.md
      wiki/api/*.md
      wiki/changelog.md, wiki/其他顶层文件.md
      wiki/subdir/ (自定义子目录)

    Args:
        wiki_dir: Wiki 目录路径
        project_name: 项目名称
        cache_dir: 可选，.deepwiki/cache 目录路径。若提供，使用数据驱动分组。

    Returns:
        menu.json 的完整数据结构
    """
    wiki_path = Path(wiki_dir)
    if not wiki_path.exists():
        return _empty_menu(project_name)

    L = _labels(wiki_dir)
    if cache_dir:
        topology = _load_json(Path(cache_dir) / 'doc-topology.json')
        topology_menu = _build_menu_from_topology(topology, project_name, L) if topology else None
        if topology_menu:
            return topology_menu

    menu: List[Dict[str, Any]] = []

    # ---------- 概览分区 ----------
    overview = _build_overview_section(wiki_path, L)
    if overview:
        menu.append(overview)

    # ---------- 模块分组（数据驱动 / 平铺回退） ----------
    if cache_dir:
        analysis = _load_json(Path(cache_dir) / 'module-analysis.json')
        groups = _group_modules(wiki_path, cache_dir, L, analysis=analysis)
    else:
        groups = _group_modules_flat(wiki_path, L)
    menu.extend(groups)

    # ---------- 更多分区 ----------
    more = _build_more_section(wiki_path, L)
    if more:
        menu.append(more)

    return _envelope(menu, project_name)


def reconcile_menu(wiki_dir: str, project_name: str = '',
                   verbose: bool = False,
                   cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Reconcile 模式：读取已有 menu.json，与实际文件校验并修正。

    修正内容：
    - 用实际 H1 标题替换预设的模块名称
    - 移除 planned: true 标记（文档已实际生成）
    - 移除规划中存在但实际未生成的条目
    - 补充实际生成但规划中遗漏的文件（数据驱动分组）

    Args:
        wiki_dir: Wiki 目录路径
        project_name: 项目名称
        verbose: 是否显示详细变更信息
        cache_dir: 可选，.deepwiki/cache 目录路径。若提供，读取
                   module-analysis.json 并输出 semantic_group_hints，
                   同时在补充遗漏模块时使用语义分组。

    Returns:
        修正后的 menu.json 数据（含 semantic_group_hints 字段）
    """
    wiki_path = Path(wiki_dir)
    menu_path = wiki_path / 'menu.json'

    if not menu_path.exists():
        # 无已有菜单，退回普通生成模式
        if verbose:
            print("未找到 menu.json，使用普通生成模式")
        return build_menu(wiki_dir, project_name, cache_dir=cache_dir)

    try:
        with open(menu_path, 'r', encoding='utf-8') as f:
            menu_data = json.load(f)
    except UnicodeDecodeError:
        with open(menu_path, 'r', encoding='utf-8-sig') as f:
            menu_data = json.load(f)

    changes = {
        'titles_updated': 0,
        'planned_removed': 0,
        'missing_removed': 0,
        'added': 0,
    }

    menu = menu_data.get('menu', [])
    wiki_path_str = str(wiki_path)

    # ---- 修正已有条目 ----
    updated_menu: List[Dict[str, Any]] = []
    for group in menu:
        items = group.get('items', [])
        updated_items: List[Dict[str, Any]] = []
        for item in items:
            # 处理嵌套（模块组内有子项）
            children = item.get('items', [])
            if children:
                updated_children: List[Dict[str, Any]] = []
                for child in children:
                    child_path = child.get('path', '')
                    full_path = wiki_path / child_path

                    if not full_path.exists():
                        # 规划的文件未生成，跳过
                        changes['planned_removed'] += 1
                        if verbose:
                            print(f"  移除未生成: {child_path}")
                        continue

                    # 移除 planned 标记
                    if child.get('planned'):
                        child.pop('planned', None)

                    # 用实际 H1 标题更新模块名称（仅更新父级 item 的 title）
                    actual_title = extract_title(str(full_path))
                    if actual_title and actual_title != full_path.stem.title():
                        if verbose:
                            old_title = item.get('title', '')
                            if old_title != actual_title:
                                print(f"  标题更新: [{group['title']}] {old_title} -> {actual_title}")

                    updated_children.append(child)

                # 用第一个子文件的 H1 标题更新模块显示名称
                if updated_children:
                    first_child = updated_children[0]
                    first_path = wiki_path / first_child.get('path', '')
                    if first_path.exists():
                        module_name = first_path.stem
                        actual_title = extract_title(str(first_path))
                        display_title = actual_title if actual_title != module_name.title() else module_name
                        old_title = item.get('title', '')
                        if old_title != display_title and old_title:
                            changes['titles_updated'] += 1
                            if verbose:
                                print(f"  标题更新: {old_title} -> {display_title}")
                        item = {**item, 'title': display_title}
                    item = {**item, 'items': updated_children}
                    updated_items.append(item)
            else:
                # 顶层条目（无子项）
                item_path = item.get('path', '')
                full_path = wiki_path / item_path

                if not full_path.exists():
                    changes['missing_removed'] += 1
                    if verbose:
                        print(f"  移除缺失: {item_path}")
                    continue

                item = {**item, 'items': []}
                updated_items.append(item)

        updated_menu.append({**group, 'items': updated_items})

    # ---- 补充遗漏的文件 ----
    known_paths = set()
    for group in updated_menu:
        for item in group.get('items', []):
            for child in item.get('items', []):
                known_paths.add(child.get('path', ''))
            known_paths.add(item.get('path', ''))

    # 查找遗漏的模块文件
    modules_dir = wiki_path / 'modules'
    api_dir = wiki_path / 'api'

    if modules_dir.exists():
        existing_modules: Dict[str, Tuple[str, str]] = {}
        for f in modules_dir.glob('*.md'):
            if f.name in ('_index.md', 'index.md'):
                continue
            module_key = f'modules/{f.name}'
            if module_key not in known_paths:
                existing_modules[f.stem] = (f.name, extract_title(str(f)))

        for api_dir_child in [api_dir] if api_dir.exists() else []:
            for f in api_dir_child.glob('*.md'):
                module_key = f'api/{f.name}'
                if module_key not in known_paths:
                    # 检查对应的模块文档是否也在遗漏中
                    continue

        L = _labels(wiki_dir)

        if existing_modules:
            if cache_dir:
                # 数据驱动分组：读取 semantic_group，将遗漏模块归入对应分区
                analysis_path = Path(cache_dir) / 'module-analysis.json'
                analysis = _load_json(analysis_path)
                semantic_map = _extract_semantic_groups(analysis)

                # 按语义分组聚合
                sg_to_modules: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)
                ungrouped: List[Tuple[str, str, str]] = []

                for stem, (filename, title) in sorted(existing_modules.items()):
                    sg = semantic_map.get(stem)
                    if sg:
                        sg_to_modules[sg].append((stem, filename, title))
                    else:
                        ungrouped.append((stem, filename, title))

                # 按语义分组插入
                insert_idx = 1 if len(updated_menu) > 1 else len(updated_menu)
                for sg_name in sorted(sg_to_modules.keys()):
                    items = []
                    for stem, filename, title in sg_to_modules[sg_name]:
                        display_title = title if title != stem.title() else stem
                        children = [{'title': L['module_doc'], 'path': f'modules/{filename}'}]
                        if (api_dir / filename).exists():
                            children.append({'title': L['api_ref'], 'path': f'api/{filename}'})
                        items.append({'title': display_title, 'items': children})
                        changes['added'] += 1
                        if verbose:
                            print(f"  新增遗漏: modules/{filename} -> [{sg_name}]")
                    if items:
                        updated_menu.insert(insert_idx, {'title': sg_name, 'items': items})
                        insert_idx += 1

                # 无语义标注的模块归入默认"模块"组
                if ungrouped:
                    extra_module_items = []
                    for stem, filename, title in ungrouped:
                        display_title = title if title != stem.title() else stem
                        children = [{'title': L['module_doc'], 'path': f'modules/{filename}'}]
                        if (api_dir / filename).exists():
                            children.append({'title': L['api_ref'], 'path': f'api/{filename}'})
                        extra_module_items.append({
                            'title': display_title,
                            'items': children,
                        })
                        changes['added'] += 1
                        if verbose:
                            print(f"  新增遗漏: modules/{filename}")
                    if extra_module_items:
                        updated_menu.insert(insert_idx, {'title': L['modules'], 'items': extra_module_items})
            else:
                # 原有逻辑：统一归入"模块"组
                extra_module_items = []
                for stem, (filename, title) in sorted(existing_modules.items()):
                    display_title = title if title != stem.title() else stem
                    api_path = f'api/{filename}'
                    children = [{'title': L['module_doc'], 'path': f'modules/{filename}'}]
                    if (api_dir / filename).exists():
                        children.append({'title': L['api_ref'], 'path': api_path})
                    extra_module_items.append({
                        'title': display_title,
                        'items': children,
                    })
                    changes['added'] += 1
                    if verbose:
                        print(f"  新增遗漏: modules/{filename}")

                if extra_module_items:
                    # 插入到第一个分组之后（概览组之后），或追加
                    insert_idx = 1 if len(updated_menu) > 1 else len(updated_menu)
                    updated_menu.insert(insert_idx, {'title': L['modules'], 'items': extra_module_items})

    # ---- 移除空的分组 ----
    final_menu = [g for g in updated_menu if g.get('items')]

    menu_data['menu'] = final_menu
    menu_data['reconciled'] = True
    menu_data['reconciled_at'] = datetime.now(timezone.utc).isoformat()
    menu_data.pop('planned', None)

    # ── 读取 semantic_group 建议（来自 module-analysis.json）──────────────
    semantic_group_hints: Dict[str, List[Dict[str, str]]] = {}
    if cache_dir:
        analysis_path = Path(cache_dir) / 'module-analysis.json'
        if analysis_path.exists():
            try:
                analysis_data = json.loads(analysis_path.read_text(encoding='utf-8'))
                for mod_name, mod_data in analysis_data.get('modules', {}).items():
                    sg = mod_data.get('semantic_group')
                    conf = mod_data.get('semantic_group_confidence', 'high')
                    if sg:
                        if sg not in semantic_group_hints:
                            semantic_group_hints[sg] = []
                        semantic_group_hints[sg].append(
                            {'module': mod_name, 'confidence': conf}
                        )
            except (json.JSONDecodeError, OSError):
                pass  # 静默降级，不中断 reconcile 流程
    menu_data['semantic_group_hints'] = semantic_group_hints
    if verbose and semantic_group_hints:
        print("\n语义分组建议（来自 module-analysis.json）:")
        for group, mods in semantic_group_hints.items():
            mod_names = ', '.join(m['module'] for m in mods)
            print(f"  [{group}]: {mod_names}")
    # ────────────────────────────────────────────────────────────────────

    return menu_data


def _empty_menu(project_name: str) -> Dict[str, Any]:
    return {
        'cache_schema_version': CACHE_SCHEMA_VERSION,
        'title': project_name or '',
        'version': '1.0',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'menu': [],
    }


def save_menu(wiki_dir: str, menu_data: Dict[str, Any]) -> str:
    """将 menu.json 写入 wiki 目录，返回写入路径。"""
    output_path = Path(wiki_dir) / 'menu.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(menu_data, f, indent=2, ensure_ascii=False)
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="DeepWiki 导航菜单生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认模式：扫描已有文件生成菜单
  python generate_menu.py /path/to/.deepwiki/wiki "项目名称"

  # Reconcile 模式：校验并修正已有菜单
  python generate_menu.py /path/to/.deepwiki/wiki "项目名称" --reconcile
        """
    )
    parser.add_argument(
        "wiki_dir",
        help="Wiki 目录路径"
    )
    parser.add_argument(
        "project_name",
        nargs="?",
        default="",
        help="项目名称（可选，默认使用 wiki 目录的父目录名）"
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Reconcile 模式：校验已有 menu.json 与实际文件的一致性"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细变更信息"
    )

    args = parser.parse_args()

    wiki_dir = args.wiki_dir
    project_name = args.project_name

    if args.reconcile:
        # 自动推断 cache_dir：wiki_dir 的父目录下的 cache/
        inferred_cache = Path(wiki_dir).parent / 'cache'
        cache_dir = str(inferred_cache) if inferred_cache.exists() else None
        menu_data = reconcile_menu(wiki_dir, project_name, verbose=args.verbose,
                                   cache_dir=cache_dir)
        output = save_menu(wiki_dir, menu_data)
        total = sum([
            menu_data.get('titles_updated', 0),
            menu_data.get('planned_removed', 0),
            menu_data.get('missing_removed', 0),
            menu_data.get('added', 0),
        ])
        mode_label = "Reconcile"
        print(f"[{mode_label}] 修正完成: {total} 处变更 -> {output}")
        if args.verbose:
            print(f"  - 标题更新: {menu_data.get('titles_updated', 0)}")
            print(f"  - 规划条目移除: {menu_data.get('planned_removed', 0)}")
            print(f"  - 缺失条目移除: {menu_data.get('missing_removed', 0)}")
            print(f"  - 新增遗漏条目: {menu_data.get('added', 0)}")
    else:
        # 自动推断 cache_dir：wiki_dir 的父目录下的 cache/
        inferred_cache = Path(wiki_dir).parent / 'cache'
        cache_dir = str(inferred_cache) if inferred_cache.exists() else None
        menu_data = build_menu(wiki_dir, project_name, cache_dir=cache_dir)
        output = save_menu(wiki_dir, menu_data)
        print(f"菜单已生成: {output}")


if __name__ == '__main__':
    main()
