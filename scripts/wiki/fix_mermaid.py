#!/usr/bin/env python3
"""
Mermaid 语法修复脚本（兼容入口）

已重构：实际逻辑迁移至 scripts/wiki/mermaid/ 包
  - extractor.py   : 提取块 + 简单修复
  - fixers.py      : 各类图表正则修复函数
  - validator.py   : mmdc 语法校验（不可用时降级）
  - repairer.py    : AI 修复 Prompt + 错误报告管理
  - orchestrator.py: 整体流程编排

本文件保留 Mermaid CLI 接口，供 scripts.wiki.postprocess 调用。

用法:
    python scripts/wiki/fix_mermaid.py <项目目录>/.deepwiki
    python scripts/wiki/fix_mermaid.py <项目目录>/.deepwiki --dry-run
    python scripts/wiki/fix_mermaid.py <项目目录>/.deepwiki --validate
    python scripts/wiki/fix_mermaid.py <项目目录>/.deepwiki --apply-fix <block_id> --content <text>
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# 兼容直接运行与包导入两种场景
try:
    from .mermaid.orchestrator import run_regex_pass, run_validate_pass, run_apply_fix
    from .mermaid.extractor import extract_mermaid_blocks, extract_and_fix_file
    from .mermaid.fixers import (
        fix_mermaid_block, fix_flowchart, fix_class_diagram,
        fix_sequence_diagram, fix_duplicate_node_ids, _needs_quoting, _quote,
    )
except ImportError:
    _pkg_root = Path(__file__).parent.parent
    if str(_pkg_root) not in sys.path:
        sys.path.insert(0, str(_pkg_root))
    from wiki.mermaid.orchestrator import run_regex_pass, run_validate_pass, run_apply_fix
    from wiki.mermaid.extractor import extract_mermaid_blocks, extract_and_fix_file
    from wiki.mermaid.fixers import (
        fix_mermaid_block, fix_flowchart, fix_class_diagram,
        fix_sequence_diagram, fix_duplicate_node_ids, _needs_quoting, _quote,
    )


# -- 兼容旧接口（供外部直接 import） --

def fix_mermaid_in_file(file_path, dry_run=False):
    return extract_and_fix_file(Path(file_path), dry_run=dry_run)


def fix_all_mermaid(wiki_dir, dry_run=False):
    return run_regex_pass(wiki_dir, dry_run=dry_run)


# -- CLI 入口 --

def main():
    parser = argparse.ArgumentParser(description="DeepWiki Mermaid 语法修复工具")
    parser.add_argument("wiki_path", help="Wiki 目录路径 (.deepwiki)")
    parser.add_argument("--dry-run", action="store_true", help="仅报告问题，不修改文件")
    parser.add_argument("--json", metavar="FILE", help="将结果保存为 JSON")
    parser.add_argument("--validate", action="store_true",
                        help="阶段 2：运行 mmdc 校验，生成 state/mermaid-errors.json")
    parser.add_argument("--apply-fix", metavar="BLOCK_ID",
                        help="阶段 2：将 AI 修复结果写回（需同时提供 --content）")
    parser.add_argument("--content", metavar="TEXT",
                        help="配合 --apply-fix 使用：修复后的 mermaid 文本")

    args = parser.parse_args()

    if args.apply_fix:
        if not args.content:
            print("错误：--apply-fix 必须配合 --content 使用", file=sys.stderr)
            return 1
        ok = run_apply_fix(args.apply_fix, args.content, args.wiki_path)
        if ok:
            print(f"[APPLIED] {args.apply_fix}")
            return 0
        else:
            print(f"[FAILED] {args.apply_fix}: 未找到对应块或文件", file=sys.stderr)
            return 1

    if args.validate:
        summary = run_validate_pass(args.wiki_path)
        print(f"Mermaid 校验: {summary['total_blocks']} 块, "
              f"{summary['failed']} 失败, {summary['skipped']} 跳过(mmdc不可用)")
        if summary["report_path"]:
            print(f"  错误报告: {summary['report_path']}")
            return 1
        return 0

    results = run_regex_pass(args.wiki_path, dry_run=args.dry_run)
    total_files = len(results)
    total_blocks = sum(r.get("blocks_fixed", 0) for r in results)
    total_fixes = sum(r.get("total_fixes", 0) for r in results)

    print(f"Mermaid 修复: {total_fixes} 处修复 ({total_blocks} 个图表块, {total_files} 个文件)")
    for r in results:
        if r.get("total_fixes", 0) > 0:
            mode = "DRY-RUN" if args.dry_run else "FIXED"
            print(f"  [{mode}] {r['file']}: {r['total_fixes']} fixes in {r['blocks_fixed']} blocks")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({
                "check_time": datetime.now(timezone.utc).isoformat(),
                "total_fixes": total_fixes,
                "files_affected": [r for r in results if r.get("total_fixes", 0) > 0],
            }, f, indent=2, ensure_ascii=False)

    if args.dry_run and total_fixes > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
