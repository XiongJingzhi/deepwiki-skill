#!/usr/bin/env python3
"""
导航菜单生成脚本

两种模式：
  默认模式：扫描 wiki/ 目录下所有 .md 文件，生成层级化 menu.json。
  --reconcile 模式：读取已有 menu.json，与实际文件校验并修正。
"""

import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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


def build_menu(wiki_dir: str, project_name: str = '') -> Dict[str, Any]:
    """
    从 wiki 目录结构生成层级化导航菜单（默认模式）。

    目录布局:
      wiki/index.md, wiki/architecture.md, wiki/getting-started.md, wiki/doc-map.md
      wiki/modules/*.md
      wiki/api/*.md
      wiki/changelog.md, wiki/其他顶层文件.md
      wiki/subdir/ (自定义子目录)

    Returns:
        menu.json 的完整数据结构
    """
    wiki_path = Path(wiki_dir)
    if not wiki_path.exists():
        return _empty_menu(project_name)

    L = _labels(wiki_dir)
    menu: List[Dict[str, Any]] = []

    # ---------- 顶层根文件（index.md 等概览类文档） ----------
    overview_items: List[Dict[str, str]] = []
    for filename in ('index.md', 'getting-started.md', 'architecture.md', 'doc-map.md'):
        target = wiki_path / filename
        if target.exists():
            title = extract_title(str(target))
            overview_items.append({
                'title': title if title else target.stem,
                'path': filename,
            })

    if overview_items:
        menu.append({'title': L['overview'], 'items': overview_items})

    # ---------- 模块文档 + API 文档（按模块名配对） ----------
    modules_dir = wiki_path / 'modules'
    api_dir = wiki_path / 'api'

    module_items: List[Dict[str, Any]] = []
    module_md_files: List[Path] = []

    if modules_dir.exists():
        for f in sorted(modules_dir.glob('*.md')):
            if f.name in ('_index.md', 'index.md'):
                continue
            module_md_files.append(f)

    for md_file in module_md_files:
        module_name = md_file.stem
        title = extract_title(str(md_file))

        children: List[Dict[str, str]] = [
            {'title': L['module_doc'], 'path': f'modules/{md_file.name}'},
        ]

        # 查找对应的 API 文档
        api_file = api_dir / md_file.name if api_dir.exists() else None
        if api_file and api_file.exists():
            children.append({
                'title': L['api_ref'],
                'path': f'api/{api_file.name}',
            })

        module_items.append({
            'title': title if title != module_name.title() else module_name,
            'items': children,
        })

    if module_items:
        menu.append({'title': L['modules'], 'items': module_items})

    # ---------- 其他顶层 .md 文件（changelog 等） ----------
    known_top_files = {'index.md', 'getting-started.md', 'architecture.md', 'doc-map.md'}
    other_top: List[Dict[str, str]] = []
    for md_file in sorted(wiki_path.glob('*.md')):
        if md_file.name not in known_top_files:
            title = extract_title(str(md_file))
            other_top.append({
                'title': title if title != md_file.stem.title() else md_file.stem,
                'path': md_file.name,
            })

    # ---------- 自定义子目录 ----------
    known_dirs = {'modules', 'api', 'assets'}
    subdir_items: List[Dict[str, Any]] = []
    for subdir in sorted(wiki_path.iterdir()):
        if not subdir.is_dir() or subdir.name.startswith('.') or subdir.name.startswith('_'):
            continue
        if subdir.name in known_dirs:
            continue
        # 扫描子目录下的 .md 文件
        subdir_docs: List[Dict[str, str]] = []
        for md_file in sorted(subdir.glob('*.md')):
            title = extract_title(str(md_file))
            subdir_docs.append({
                'title': title if title != md_file.stem.title() else md_file.stem,
                'path': f'{subdir.name}/{md_file.name}',
            })
        if subdir_docs:
            subdir_items.append({
                'title': subdir.name,
                'items': subdir_docs,
            })

    # 将其他顶层文件和自定义子目录归入"更多"分组
    if other_top or subdir_items:
        more_items: List[Dict[str, Any]] = []
        if other_top:
            more_items.append({'title': '其他', 'items': other_top})
        more_items.extend(subdir_items)
        menu.append({'title': L['more'], 'items': more_items})

    return {
        'cache_schema_version': CACHE_SCHEMA_VERSION,
        'title': project_name or '',
        'version': '1.0',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'menu': menu,
    }


def reconcile_menu(wiki_dir: str, project_name: str = '',
                   verbose: bool = False,
                   cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Reconcile 模式：读取已有 menu.json，与实际文件校验并修正。

    修正内容：
    - 用实际 H1 标题替换预设的模块名称
    - 移除 planned: true 标记（文档已实际生成）
    - 移除规划中存在但实际未生成的条目
    - 补充实际生成但规划中遗漏的文件

    Args:
        wiki_dir: Wiki 目录路径
        project_name: 项目名称
        verbose: 是否显示详细变更信息
        cache_dir: 可选，.deepwiki/cache 目录路径。若提供，读取
                   module-analysis.json 并输出 semantic_group_hints。

    Returns:
        修正后的 menu.json 数据（含 semantic_group_hints 字段）
    """
    wiki_path = Path(wiki_dir)
    menu_path = wiki_path / 'menu.json'

    if not menu_path.exists():
        # 无已有菜单，退回普通生成模式
        if verbose:
            print("未找到 menu.json，使用普通生成模式")
        return build_menu(wiki_dir, project_name)

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

        # 将遗漏的模块归入"模块"组
        L = _labels(wiki_dir)
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
        menu_data = build_menu(wiki_dir, project_name)
        output = save_menu(wiki_dir, menu_data)
        print(f"菜单已生成: {output}")


if __name__ == '__main__':
    main()
