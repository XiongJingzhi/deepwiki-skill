#!/usr/bin/env python3
"""跨模块文档一致性检查。

检查维度：
a) 模块 A 的 dependency_hints 引用了模块 B 的接口 → 模块 B 的文档是否记录了该接口
b) 模块间依赖方向是否和 menu.json 的分组结构一致

用法:
    python check_cross_module_consistency.py <项目路径>  [--json <报告文件>]
"""

import json
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple


def load_json(path: Path) -> dict:
    """安全加载 JSON 文件，不存在则返回空字典。"""
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"警告: 无法读取 {path}: {e}", file=sys.stderr)
        return {}


def load_module_analysis(wiki_dir: Path) -> Dict:
    """加载 module-analysis.json。"""
    path = wiki_dir / "cache" / "module-analysis.json"
    if not path.exists():
        return {}
    data = load_json(path)
    if isinstance(data, dict):
        return data
    return {}


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


def check_interface_coverage(wiki_dir: Path, module_analysis: Dict) -> List[Dict]:
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

            # 查找目标模块的文档文件。新结构中每个模块只对应一个学习页面，
            # API、核心逻辑和风险说明都并入同一页。
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
    sections = menu.get("menu", [])

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
        interface_issues = check_interface_coverage(wiki_path, module_analysis)
        all_issues.extend(interface_issues)

        # 检查 2: 依赖方向 vs menu 分组一致性
        dep_issues = check_dependency_menu_alignment(wiki_path, module_analysis, menu)
        all_issues.extend(dep_issues)

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
