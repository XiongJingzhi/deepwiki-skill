#!/usr/bin/env python3
"""跨模块文档一致性检查。

检查维度：
a) 模块 A 的 dependency_hints 引用了模块 B 的接口 → 模块 B 的文档是否记录了该接口
b) 模块间依赖方向是否和 menu.json 的分组结构一致
c) menu.json 中所有 path 条目指向实际存在的 .md 文件
d) wiki 内部相对链接（.md）指向实际存在的页面

用法:
    python check_cross_module_consistency.py <项目路径>  [--json <报告文件>]
"""

import json
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from scripts.core.common import load_json, load_module_analysis as _load_module_analysis


def load_module_analysis(wiki_dir: Path) -> Dict:
    """加载 module-analysis.json。wiki_dir 可能是 .deepwiki 目录或项目根目录。"""
    # common.load_module_analysis 期望项目根目录
    if wiki_dir.name == ".deepwiki":
        project_root = wiki_dir.parent
    else:
        project_root = wiki_dir
    data = _load_module_analysis(project_root)
    return data if data else {}


def load_menu(wiki_dir: Path) -> Dict:
    """加载 menu.json。"""
    path = wiki_dir / "wiki" / "menu.json"
    return load_json(path)


def extract_documented_interfaces(module_doc_path: Path) -> Set[str]:
    """从模块文档中提取已记录的接口名称。

    简单实现：搜索 markdown 中行内代码引用的函数/类名。
    """
    if not module_doc_path.exists():
        return set()

    try:
        content = module_doc_path.read_text(encoding='utf-8')
    except OSError:
        return set()

    documented = set()

    # 匹配行内代码引用的函数/类名：`function_name(`、`ClassName`、`name.property`
    for match in re.finditer(r'`([A-Za-z_][A-Za-z0-9_]*)[\(\.<]?', content):
        name = match.group(1)
        # 过滤常见非接口词（语言关键字、标记词等）
        if name.lower() in (
            'python', 'javascript', 'typescript', 'java', 'go', 'rust', 'kotlin',
            'true', 'false', 'null', 'undefined', 'none',
            'string', 'number', 'boolean', 'object', 'array', 'void', 'any', 'never',
            'int', 'float', 'str', 'bool', 'list', 'dict', 'set', 'tuple', 'map',
            'todo', 'fixme', 'note', 'warning', 'error', 'hint', 'tip', 'important',
            'http', 'https', 'www', 'com', 'org', 'io',
        ):
            continue
        documented.add(name)

    return documented


def _build_module_doc_map(wiki_dir: Path) -> Dict[str, Path]:
    """从 generation-plan.json 构建 module_path -> 实际 wiki 文档路径的映射。"""
    cache_dir = wiki_dir / "cache"
    plan_path = cache_dir / "generation-plan.json"
    doc_map: Dict[str, Path] = {}
    if plan_path.exists():
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            for page in plan.get("pages", []):
                for mod in page.get("affected_modules", []):
                    output = page.get("output_path", "")
                    if output.startswith("wiki/"):
                        output = output[5:]
                    doc_map[mod] = wiki_dir / "wiki" / output
        except (json.JSONDecodeError, OSError):
            pass
    return doc_map


def check_interface_coverage(wiki_dir: Path, module_analysis: Dict,
                             doc_map: Optional[Dict[str, Path]] = None) -> List[Dict]:
    """检查：模块 A 引用模块 B 的接口 → B 的文档是否记录了该接口。

    遍历每个模块的 dependency_hints.imports，对其中引用的外部接口，
    检查目标模块的文档是否包含该接口的说明。

    Returns:
        问题列表：[{"type": "missing_interface", "source_module": ..., ...}]
    """
    issues = []

    # 筛选有效模块条目
    module_map = {
        mod_path: mod_data
        for mod_path, mod_data in module_analysis.items()
        if isinstance(mod_data, dict) and "module_summary" in mod_data
    }

    for mod_path, mod_data in module_map.items():
        hints = mod_data.get("dependency_hints", {})
        if not isinstance(hints, dict):
            continue
        imports = hints.get("imports", [])
        if not isinstance(imports, list):
            continue

        for imp in imports:
            if not isinstance(imp, dict):
                continue
            target_module = imp.get("module", "")
            interfaces = imp.get("interfaces", [])
            if not target_module or not interfaces:
                continue

            # 查找目标模块的文档文件。优先使用 generation-plan 中的实际路径，
            # 回退到 flat deep-dive 路径。
            if doc_map:
                target_doc = doc_map.get(target_module)
            else:
                target_doc = None
            if target_doc is None:
                target_mod_name = Path(target_module).name
                target_doc = wiki_dir / "wiki" / "deep-dive" / f"{target_mod_name}.md"

            if target_doc.exists():
                documented = extract_documented_interfaces(target_doc)
                for iface in interfaces:
                    if iface not in documented:
                        issues.append({
                            "type": "missing_interface",
                            "source_module": mod_path,
                            "target_module": target_module,
                            "interface": iface,
                            "severity": "warning",
                            "message": (
                                f"`{mod_path}` 引用 `{target_module}` 的接口 "
                                f"`{iface}`，但目标模块文档中未找到该接口的记录"
                            ),
                        })
            else:
                # 目标模块完全没有文档，不归入此项（由其他质量检查覆盖）
                pass

    return issues


def check_dependency_menu_alignment(
    wiki_dir: Path, module_analysis: Dict, menu: Dict
) -> List[Dict]:
    """检查：模块间依赖方向是否和 menu 分组一致。

    同一分组内的模块应有较强依赖关系；不同分组间应避免双向依赖。
    若两个分组之间存在双向依赖，可能表明分组不合理。

    Returns:
        问题列表：[{"type": "bidirectional_cross_section", ...}]
    """
    issues = []

    if not menu:
        return issues

    # 从 menu.json 提取分组结构
    sections = menu.get("items", [])

    # 构建模块 → 分组映射
    module_to_section: Dict[str, str] = {}
    section_names: Set[str] = set()

    def extract_modules_from_section(section: Dict, parent_name: str = "") -> None:
        """递归提取菜单节中的模块 → 分组映射。"""
        name = section.get("title", section.get("name", parent_name))
        section_names.add(name)
        items = section.get("items", section.get("children", []))
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, dict):
                # 子节 → 递归；叶子 → 映射模块
                if item.get("items") or item.get("children"):
                    extract_modules_from_section(item, name)
                else:
                    module_id = item.get("id", item.get("link", ""))
                    if module_id:
                        module_to_section[module_id] = name

    if isinstance(sections, list):
        for section in sections:
            if isinstance(section, dict):
                extract_modules_from_section(section)

    if not module_to_section:
        return issues

    # 收集跨分组依赖
    cross_section_deps: List[Tuple[str, str]] = []
    for mod_path, mod_data in module_analysis.items():
        if not isinstance(mod_data, dict):
            continue
        hints = mod_data.get("dependency_hints", {})
        if not isinstance(hints, dict):
            continue
        imports = hints.get("imports", [])
        if not isinstance(imports, list):
            continue

        source_section = module_to_section.get(mod_path)
        if not source_section:
            continue

        for imp in imports:
            if not isinstance(imp, dict):
                continue
            target = imp.get("module", "")
            target_section = module_to_section.get(target)
            if target_section and target_section != source_section:
                cross_section_deps.append((source_section, target_section))

    # 检测双向跨分组依赖
    dep_pairs: Set[Tuple[str, str]] = set()
    reported_pairs: Set[Tuple[str, str]] = set()

    for src, tgt in cross_section_deps:
        pair = tuple(sorted([src, tgt]))
        if pair in reported_pairs:
            continue
        if pair in dep_pairs:
            # 第二次看到该分组对 → 双向依赖
            issues.append({
                "type": "bidirectional_cross_section",
                "section_a": pair[0],
                "section_b": pair[1],
                "severity": "info",
                "message": (
                    f"分组 `{pair[0]}` 和 `{pair[1]}` 之间存在双向依赖，"
                    f"考虑是否应合并为同一分组"
                ),
            })
            reported_pairs.add(pair)
        else:
            dep_pairs.add(pair)

    return issues


# ── 链接导航检查 ──────────────────────────────────────────────────────

# 匹配 Markdown 相对链接: [text](relative/path.md) 或 [text](relative/path.md#anchor)
_MD_LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+\.md(?:#[^)]*)?)\)')


def _collect_wiki_files(wiki_path: Path) -> Set[str]:
    """收集 wiki/ 目录下所有 .md 文件的相对路径（正斜杠）。"""
    files: Set[str] = set()
    if not wiki_path.exists():
        return files
    for f in wiki_path.rglob("*.md"):
        rel = f.relative_to(wiki_path).as_posix()
        files.add(rel)
    return files


def check_menu_paths(wiki_dir: Path, menu: Dict) -> List[Dict]:
    """检查 menu.json 中所有 path 条目是否指向实际存在的 .md 文件。

    Returns:
        问题列表：[{"type": "menu_missing_file", "path": ..., "title": ..., ...}]
    """
    issues: List[Dict] = []
    if not menu:
        return issues

    wiki_path = wiki_dir / "wiki"
    wiki_files = _collect_wiki_files(wiki_path)

    def walk_items(items: list, section_title: str = "") -> None:
        for item in items:
            if not isinstance(item, dict):
                continue
            path = item.get("path", "")
            if not path:
                # 有子项的分组节点，递归
                sub = item.get("items", [])
                if sub:
                    walk_items(sub, item.get("title", section_title))
                continue
            if path not in wiki_files:
                issues.append({
                    "type": "menu_missing_file",
                    "path": path,
                    "title": item.get("title", ""),
                    "section": section_title,
                    "severity": "error",
                    "message": (
                        f"menu.json「{section_title}」分组中 "
                        f"`{item.get('title', path)}` 指向 `{path}`，"
                        f"但该文件不存在于 wiki/ 目录"
                    ),
                })

    sections = menu.get("items", [])
    if isinstance(sections, list):
        for section in sections:
            if isinstance(section, dict):
                walk_items(
                    section.get("items", []),
                    section.get("title", ""),
                )

    return issues


def check_wiki_links(wiki_dir: Path, menu: Optional[Dict] = None) -> List[Dict]:
    """检查 wiki 内所有 .md 文件中的相对链接是否指向实际存在的页面。

    同时检查链接目标是否出现在 menu.json 中（warn 级别）。

    Returns:
        问题列表：[{"type": "broken_link", ...}, {"type": "unlisted_link", ...}]
    """
    issues: List[Dict] = []

    wiki_path = wiki_dir / "wiki"
    if not wiki_path.exists():
        return issues

    wiki_files = _collect_wiki_files(wiki_path)

    # 收集 menu.json 中注册的所有路径
    menu_paths: Set[str] = set()
    if menu:
        def collect_menu_paths(items: list) -> None:
            for item in items:
                if not isinstance(item, dict):
                    continue
                p = item.get("path", "")
                if p:
                    menu_paths.add(p)
                collect_menu_paths(item.get("items", []))
        collect_menu_paths(menu.get("items", []))

    for md_file in sorted(wiki_path.rglob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        source_rel = md_file.relative_to(wiki_path).as_posix()

        for match in _MD_LINK_RE.finditer(content):
            link_text = match.group(1)
            link_target = match.group(2)

            # 分离锚点
            base_path = link_target.split("#")[0]

            # 跳过绝对 URL、file:// 链接、纯锚点
            if not base_path or base_path.startswith(("http://", "https://", "file://", "/")):
                continue

            # 解析相对路径：相对于当前文件所在目录
            current_dir = md_file.parent.relative_to(wiki_path)
            if str(current_dir) == ".":
                resolved = base_path
            else:
                resolved = Path(current_dir) / base_path
            # 规范化 ../ 等（纯字符串操作，不触及文件系统）
            try:
                resolved = resolved.as_posix()
            except AttributeError:
                resolved = str(resolved).replace("\\", "/")
            parts = Path(resolved).parts
            normalized: list = []
            for part in parts:
                if part == "..":
                    if normalized:
                        normalized.pop()
                elif part != ".":
                    normalized.append(part)
            resolved = "/".join(normalized) if normalized else ""

            if resolved not in wiki_files:
                issues.append({
                    "type": "broken_link",
                    "source": source_rel,
                    "link_text": link_text,
                    "target": link_target,
                    "severity": "error",
                    "message": (
                        f"`{source_rel}` 中链接 `{link_text}` → `{link_target}`，"
                        f"目标文件不存在（解析为 `{resolved}`）"
                    ),
                })
            elif resolved in menu_paths:
                # 链接有效且在 menu 中，无需报告
                pass

    # 检查: wiki 中存在但未列入 menu.json 的文件
    if menu_paths:
        # 顶层文件（overview.md 等）由 menu 的概览分区单独管理，不计入
        top_level_handled = {
            'overview.md', 'getting-started.md', 'doc-map.md',
            'index.md', '_index.md',
        }
        unlisted = wiki_files - menu_paths - top_level_handled
        for unlisted_path in sorted(unlisted):
            issues.append({
                "type": "unlisted_wiki_file",
                "path": unlisted_path,
                "severity": "warning",
                "message": f"Wiki file not listed in menu: {unlisted_path}",
            })

    return issues


def check_cross_module_consistency(wiki_dir: str) -> Dict:
    """主入口：执行所有跨模块一致性检查。

    Args:
        wiki_dir: .deepwiki 目录路径（或项目根路径，会自动查找 .deepwiki）

    Returns:
        {"issues": [...], "warnings": [...], "infos": [...], "errors": [...], "passed": bool}
    """
    wiki_path = Path(wiki_dir)

    # 自动定位 .deepwiki 目录
    if not (wiki_path / "cache").exists():
        candidate = wiki_path / ".deepwiki"
        if candidate.exists():
            wiki_path = candidate
        else:
            return {
                "issues": [],
                "errors": [],
                "warnings": [],
                "infos": [],
                "passed": True,
            }

    module_analysis = load_module_analysis(wiki_path)
    menu = load_menu(wiki_path)

    all_issues: List[Dict] = []

    # 检查 1: 接口覆盖率 — 模块 A 引用模块 B 的接口 → B 的文档是否记录
    if module_analysis:
        doc_map = _build_module_doc_map(wiki_path)
        interface_issues = check_interface_coverage(wiki_path, module_analysis, doc_map)
        all_issues.extend(interface_issues)

        # 检查 2: 依赖方向 vs menu 分组一致性
        dep_issues = check_dependency_menu_alignment(wiki_path, module_analysis, menu)
        all_issues.extend(dep_issues)

    # 检查 3: menu.json 路径有效性
    menu_path_issues = check_menu_paths(wiki_path, menu)
    all_issues.extend(menu_path_issues)

    # 检查 4: wiki 内部相对链接有效性
    link_issues = check_wiki_links(wiki_path, menu)
    all_issues.extend(link_issues)

    # 按严重级别分类
    errors = [i for i in all_issues if i.get("severity") == "error"]
    warnings = [i for i in all_issues if i.get("severity") == "warning"]
    infos = [i for i in all_issues if i.get("severity") == "info"]

    return {
        "issues": all_issues,
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "passed": len(errors) == 0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="DeepWiki 跨模块文档一致性检查",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python check_cross_module_consistency.py /path/to/project
  python check_cross_module_consistency.py /path/to/project/.deepwiki
  python check_cross_module_consistency.py . --json report.json
        """,
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="项目路径或 .deepwiki 目录路径（默认: 当前目录）",
    )
    parser.add_argument(
        "--json",
        metavar="FILE",
        help="将检查结果保存为 JSON 文件",
    )

    args = parser.parse_args()

    result = check_cross_module_consistency(args.project_path)

    # 输出结果
    if result["passed"]:
        print("跨模块一致性检查通过")
    else:
        print(f"跨模块一致性检查失败: {len(result['errors'])} 个错误")

    if result["warnings"]:
        print(f"\n{len(result['warnings'])} 个警告:")
        for w in result["warnings"]:
            print(f"  [警告] {w['message']}")

    if result["infos"]:
        print(f"\n{len(result['infos'])} 个建议:")
        for i in result["infos"]:
            print(f"  [建议] {i['message']}")

    if not result["issues"]:
        print("  （未发现跨模块一致性问题）")

    # 保存 JSON 报告
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n报告已保存到: {args.json}")

    sys.exit(1 if not result["passed"] else 0)


if __name__ == "__main__":
    main()
