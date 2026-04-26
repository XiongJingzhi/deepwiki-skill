#!/usr/bin/env python3
"""
导航菜单生成脚本

两种模式：
  默认模式：扫描 wiki/ 目录下所有 .md 文件，生成层级化 menu.json。
  --reconcile 模式：读取已有 menu.json，与实际文件校验并修正。

分组策略（默认模式）：
  - 有 cache_dir 时，数据驱动分组：
    1. doc-topology.json 的 concepts/capabilities/internals/reference 知识树
    2. 磁盘扫描 concepts/、capabilities/、internals/、reference/ 目录
  - 无 cache_dir 时，按新知识目录扫描
"""

import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from common import CACHE_SCHEMA_VERSION

# 多语言标签映射
_LABELS = {
    'zh': {'overview': '概览', 'concepts': '理解项目', 'capabilities': '能力导览',
           'internals': '内部实现', 'reference': '参考资料',
           'more': '更多', 'other': '其他',
           'subdirs': {
               'guides': '指南',
               'guide': '指南',
               'tutorials': '教程',
               'tutorial': '教程',
               'examples': '示例',
               'example': '示例',
               'reference': '参考资料',
               'references': '参考资料',
               'concepts': '理解项目',
               'capabilities': '能力导览',
               'internals': '内部实现',
               'docs': '文档',
               'decisions': '设计决策',
               'adr': '架构决策',
               'contributing': '贡献指南',
               'changelog': '更新日志',
           }},
    'en': {'overview': 'Overview', 'concepts': 'Understand', 'capabilities': 'Capabilities',
           'internals': 'Internals', 'reference': 'Reference',
           'more': 'More', 'other': 'Other', 'subdirs': {}},
}

_KNOWLEDGE_DIRS = ('concepts', 'capabilities', 'internals', 'reference')


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
    group_label_map = {
        'overview': L['overview'],
        'concepts': L['concepts'],
        'capabilities': L['capabilities'],
        'internals': L['internals'],
        'reference': L['reference'],
        'more': L['more'],
    }
    for raw_group_title, page_ids in groupings.items():
        if not isinstance(page_ids, list):
            continue
        section_title = group_label_map.get(raw_group_title, raw_group_title)
        direct_items: List[Dict[str, str]] = []

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

            direct_items.append({
                'title': page.get('title') or Path(path).stem,
                'path': path,
            })

        if direct_items:
            menu.append({'title': section_title, 'items': direct_items})

    if not menu:
        return None
    return _envelope(menu, project_name)


def _build_directory_section(wiki_path: Path, dirname: str, L: dict) -> Optional[Dict[str, Any]]:
    """Build a flat section from a first-class knowledge directory."""
    target_dir = wiki_path / dirname
    if not target_dir.exists():
        return None

    items: List[Dict[str, str]] = []
    for md_file in sorted(target_dir.glob('*.md')):
        if md_file.name in ('index.md', '_index.md'):
            continue
        title = extract_title(str(md_file))
        display_title = title if title != md_file.stem.title() else md_file.stem
        items.append({
            'title': display_title,
            'path': f'{dirname}/{md_file.name}',
        })
    if not items:
        return None
    return {'title': L.get(dirname, dirname), 'items': items}


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

    known_dirs = {'assets', 'modules', 'api', *_KNOWLEDGE_DIRS}
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
            subdir_title = L.get('subdirs', {}).get(subdir.name, subdir.name)
            subdir_items.append({'title': subdir_title, 'items': subdir_docs})

    if other_top or subdir_items:
        more_items: List[Dict[str, Any]] = []
        if other_top:
            more_items.append({'title': L.get('other', '其他'), 'items': other_top})
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
      wiki/concepts/*.md
      wiki/capabilities/*.md
      wiki/internals/*.md
      wiki/reference/*.md
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

    # ---------- 一等知识目录 ----------
    for dirname in _KNOWLEDGE_DIRS:
        section = _build_directory_section(wiki_path, dirname, L)
        if section:
            menu.append(section)

    # ---------- 更多分区 ----------
    more = _build_more_section(wiki_path, L)
    if more:
        menu.append(more)

    return _envelope(menu, project_name)


def reconcile_menu(wiki_dir: str, project_name: str = '',
                   verbose: bool = False,
                   cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """Reconcile menu.json against the new knowledge-oriented wiki layout."""
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

    L = _labels(wiki_dir)

    def reconcile_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        updated_items: List[Dict[str, Any]] = []
        for item in items:
            item = dict(item)
            if item.get('planned'):
                item.pop('planned', None)
                changes['planned_removed'] += 1

            if item.get('items'):
                nested = reconcile_items(item.get('items', []))
                if nested:
                    item['items'] = nested
                    updated_items.append(item)
                elif verbose:
                    print(f"  移除空分组: {item.get('title', '')}")
                continue

            item_path = item.get('path', '')
            full_path = wiki_path / item_path
            if not item_path or not full_path.exists():
                changes['missing_removed'] += 1
                if verbose:
                    print(f"  移除缺失: {item_path}")
                continue

            actual_title = extract_title(str(full_path))
            display_title = actual_title if actual_title != full_path.stem.title() else full_path.stem
            if item.get('title') != display_title:
                changes['titles_updated'] += 1
                if verbose:
                    print(f"  标题更新: {item.get('title', '')} -> {display_title}")
                item['title'] = display_title
            updated_items.append(item)
        return updated_items

    updated_menu: List[Dict[str, Any]] = []
    for group in menu_data.get('menu', []):
        items = reconcile_items(group.get('items', []))
        if items:
            updated_menu.append({**group, 'items': items})

    known_paths = {
        item.get('path', '')
        for group in updated_menu
        for item in group.get('items', [])
        if item.get('path')
    }

    for dirname in _KNOWLEDGE_DIRS:
        section = _build_directory_section(wiki_path, dirname, L)
        if not section:
            continue
        missing_items = [
            item for item in section['items']
            if item.get('path') not in known_paths
        ]
        if not missing_items:
            continue
        existing = next((g for g in updated_menu if g.get('title') == section['title']), None)
        if existing:
            existing.setdefault('items', []).extend(missing_items)
        else:
            updated_menu.append({'title': section['title'], 'items': missing_items})
        changes['added'] += len(missing_items)
        if verbose:
            for item in missing_items:
                print(f"  新增遗漏: {item['path']}")

    final_menu = [g for g in updated_menu if g.get('items')]
    menu_data['menu'] = final_menu
    menu_data['reconciled'] = True
    menu_data['reconciled_at'] = datetime.now(timezone.utc).isoformat()
    menu_data['titles_updated'] = changes['titles_updated']
    menu_data['planned_removed'] = changes['planned_removed']
    menu_data['missing_removed'] = changes['missing_removed']
    menu_data['added'] = changes['added']
    menu_data.pop('planned', None)

    semantic_group_hints: Dict[str, List[Dict[str, str]]] = {}
    if cache_dir:
        analysis_path = Path(cache_dir) / 'module-analysis.json'
        analysis_data = _load_json(analysis_path, {})
        modules = analysis_data.get('modules', {}) if isinstance(analysis_data, dict) else {}
        if isinstance(modules, dict):
            for mod_name, mod_data in modules.items():
                if not isinstance(mod_data, dict):
                    continue
                sg = mod_data.get('semantic_group')
                if not sg:
                    continue
                conf = mod_data.get('semantic_group_confidence', 'high')
                semantic_group_hints.setdefault(sg, []).append({
                    'module': mod_name,
                    'confidence': conf,
                })
    menu_data['semantic_group_hints'] = semantic_group_hints
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
