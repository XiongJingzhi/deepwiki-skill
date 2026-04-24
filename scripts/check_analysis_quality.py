#!/usr/bin/env python3
"""
Step 4.5 分析质量门控脚本

检查 module-analysis.json 中每个模块是否满足最低质量标准。
零 AI 成本，纯脚本实现。

用法：
  python scripts/check_analysis_quality.py <项目目录绝对路径>
  python scripts/check_analysis_quality.py <项目目录绝对路径> --verbose
  python scripts/check_analysis_quality.py <项目目录绝对路径> --json report.json

退出码：
  0 — 全部通过
  1 — 存在质量问题（打印缺失字段列表，供后续补充分析）
  2 — module-analysis.json 不存在或格式错误
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from common import cache_path


# ── 质量门控最低标准 ────────────────────────────────────────────────────────

# 模块级必需字段（缺失时为该模块标记为不通过）
MODULE_REQUIRED_FIELDS = [
    "module_path",
    "module_summary",
    "semantic_group",
    "selected_components",
]

# DeepWiki 级源码认知字段。缺失这些字段时，后续文档拓扑和证据校验
# 会退回到目录/命名推断，因此作为门控错误处理。
MODULE_COGNITIVE_FIELDS = [
    "module_role",
    "upstream_inputs",
    "downstream_outputs",
    "risk_points",
    "extension_points",
]

# 模块级推荐字段（缺失时仅警告，不导致失败）
MODULE_RECOMMENDED_FIELDS = [
    "code_purpose",
    "analysis_depth",
    "dependency_hints",
]

# 文件级必需字段（缺失时为该文件标记为不通过）
FILE_REQUIRED_FIELDS = [
    "path",
    "summary",
]

# 文件级推荐字段（至少一个文件必须具备，才算模块通过）
FILE_RECOMMENDED_FIELDS = [
    "public_interfaces",
    "key_insights",
]


def check_module_quality(mod_name: str, data: dict) -> Tuple[List[str], List[str]]:
    """
    检查单个模块的质量。

    Returns:
        (errors, warnings)
        errors:   导致门控失败的问题列表
        warnings: 建议补充但不强制的问题列表
    """
    errors: List[str] = []
    warnings: List[str] = []

    # ── 模块级必需字段 ──────────────────────────────────────────────────────
    for field in MODULE_REQUIRED_FIELDS:
        value = data.get(field)
        if not value:
            errors.append(f"缺少必需字段: {field}")

    # ── DeepWiki 认知结构字段 ───────────────────────────────────────────────
    for field in MODULE_COGNITIVE_FIELDS:
        value = data.get(field)
        if not value:
            errors.append(f"缺少认知结构字段: {field}")
        elif field != "module_role" and not isinstance(value, list):
            errors.append(f"{field} 必须是列表")
        elif isinstance(value, list) and len(value) == 0:
            errors.append(f"{field} 不能为空列表")

    # selected_components 需要是非空列表
    sc = data.get("selected_components")
    if sc is not None and (not isinstance(sc, list) or len(sc) == 0):
        errors.append("selected_components 不能为空列表")

    # ── 模块级推荐字段 ──────────────────────────────────────────────────────
    for field in MODULE_RECOMMENDED_FIELDS:
        if not data.get(field):
            warnings.append(f"建议补充字段: {field}")

    # dependency_hints 结构校验
    dep_hints = data.get("dependency_hints")
    if dep_hints is not None:
        if not isinstance(dep_hints, dict):
            errors.append("dependency_hints 必须是对象类型")
        else:
            if "imports" not in dep_hints and "imported_by" not in dep_hints:
                warnings.append("dependency_hints 缺少 imports 和 imported_by 子字段")

    # ── 文件级检查 ──────────────────────────────────────────────────────────
    files = data.get("files", [])
    if not files:
        warnings.append("files 数组为空，建议补充文件级分析")
    else:
        any_has_interfaces = False
        any_has_insights = False

        for i, f in enumerate(files):
            if not isinstance(f, dict):
                errors.append(f"files[{i}] 不是对象类型")
                continue

            # 文件级必需字段
            for field in FILE_REQUIRED_FIELDS:
                if not f.get(field):
                    errors.append(f"files[{i}] 缺少必需字段: {field}")

            # 统计推荐字段
            interfaces = f.get("public_interfaces")
            if isinstance(interfaces, list) and len(interfaces) > 0:
                any_has_interfaces = True

            insights = f.get("key_insights")
            if isinstance(insights, list) and len(insights) > 0:
                any_has_insights = True

        # 至少一个文件应有接口信息和设计洞察（排除纯配置/工具模块）
        code_purpose = data.get("code_purpose", "")
        is_utility_like = code_purpose in ("Config", "Test", "Util")

        if not any_has_interfaces and not is_utility_like:
            warnings.append("所有文件均缺少 public_interfaces，建议补充接口信息")
        if not any_has_insights and not is_utility_like:
            warnings.append("所有文件均缺少 key_insights，建议补充设计意图说明")

    return errors, warnings


def check_analysis_quality(
    module_analysis: dict,
    verbose: bool = False,
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], List[str]]:
    """
    检查整个 module-analysis.json 的质量。

    Args:
        module_analysis: 已解析的 module-analysis.json 内容
        verbose:         是否输出详细信息

    Returns:
        (all_errors, all_warnings, failed_modules)
        all_errors:     {mod_name: [error_msg, ...]}
        all_warnings:   {mod_name: [warning_msg, ...]}
        failed_modules: 有 errors 的模块名列表
    """
    all_errors: Dict[str, List[str]] = {}
    all_warnings: Dict[str, List[str]] = {}

    for mod_name, data in module_analysis.items():
        if not isinstance(data, dict):
            all_errors[mod_name] = [f"模块条目不是对象类型（实际类型：{type(data).__name__}）"]
            continue

        errors, warnings = check_module_quality(mod_name, data)
        if errors:
            all_errors[mod_name] = errors
        if warnings:
            all_warnings[mod_name] = warnings

    failed_modules = list(all_errors.keys())
    return all_errors, all_warnings, failed_modules


def load_module_analysis(project_path: Path) -> Optional[dict]:
    """加载 module-analysis.json，失败返回 None。"""
    analysis_path = cache_path(project_path, "module-analysis.json")
    if not analysis_path.exists():
        print(f"❌ module-analysis.json 不存在: {analysis_path}", file=sys.stderr)
        return None
    try:
        with open(analysis_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ module-analysis.json JSON 解析失败: {e}", file=sys.stderr)
        return None


def print_report(
    all_errors: Dict[str, List[str]],
    all_warnings: Dict[str, List[str]],
    failed_modules: List[str],
    verbose: bool,
    total_modules: int,
) -> None:
    """打印质量报告到 stdout。"""
    passed = total_modules - len(failed_modules)
    print(f"\n📊 分析质量门控报告")
    print(f"   模块总数：{total_modules}  通过：{passed}  需补充：{len(failed_modules)}")

    if failed_modules:
        print(f"\n❌ 需要补充分析的模块（{len(failed_modules)} 个）：")
        for mod in failed_modules:
            print(f"\n  📁 {mod}")
            for err in all_errors[mod]:
                print(f"     • [ERROR] {err}")
            if verbose and mod in all_warnings:
                for w in all_warnings[mod]:
                    print(f"     ⚠ [WARN]  {w}")
    else:
        print("\n✅ 所有模块均通过最低质量标准")

    if verbose and all_warnings:
        non_failed_with_warnings = {
            k: v for k, v in all_warnings.items() if k not in all_errors
        }
        if non_failed_with_warnings:
            print(f"\n⚠  建议补充的模块（{len(non_failed_with_warnings)} 个，不影响门控）：")
            for mod, warns in non_failed_with_warnings.items():
                print(f"\n  📁 {mod}")
                for w in warns:
                    print(f"     • {w}")


def main() -> int:
    import argparse

    # 确保 Windows 控制台支持 UTF-8 输出
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Step 4.5：检查 module-analysis.json 是否满足最低质量标准"
    )
    parser.add_argument("project_path", help="项目根目录绝对路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示警告信息")
    parser.add_argument("--json", metavar="FILE", dest="json_out", help="将报告输出为 JSON 文件")
    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.is_dir():
        print(f"❌ 项目目录不存在: {project_path}", file=sys.stderr)
        return 2

    module_analysis = load_module_analysis(project_path)
    if module_analysis is None:
        return 2

    if not isinstance(module_analysis, dict):
        print("❌ module-analysis.json 根节点必须是对象", file=sys.stderr)
        return 2

    total_modules = len(module_analysis)
    if total_modules == 0:
        print("⚠  module-analysis.json 为空，跳过质量检查")
        return 0

    all_errors, all_warnings, failed_modules = check_analysis_quality(
        module_analysis, verbose=args.verbose
    )

    print_report(all_errors, all_warnings, failed_modules, args.verbose, total_modules)

    # 可选：输出 JSON 报告
    if args.json_out:
        report = {
            "total_modules": total_modules,
            "passed": total_modules - len(failed_modules),
            "failed_count": len(failed_modules),
            "failed_modules": failed_modules,
            "errors": all_errors,
            "warnings": all_warnings,
        }
        out_path = Path(args.json_out)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 报告已写入: {out_path}")

    # 打印补充建议
    if failed_modules:
        print("\n💡 补充建议：")
        print("   对以上模块重新执行第 5 步深度阅读，仅补充缺失字段，不需要全量重做。")
        print(f"   失败模块列表：{', '.join(failed_modules)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
