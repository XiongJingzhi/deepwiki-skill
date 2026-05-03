#!/usr/bin/env python3
"""DeepWiki 文档后处理工具

合并 Mermaid 语法修复、文档质量检查、跨模块一致性检查。
支持子命令模式：python postprocess.py <command> [options]

用法:
    python scripts/postprocess.py mermaid <.deepwiki路径>
    python scripts/postprocess.py quality <.deepwiki路径>
    python scripts/postprocess.py consistency <.deepwiki路径>
"""

import os
import sys
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description="DeepWiki 文档后处理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # mermaid subcommand
    p_mermaid = subparsers.add_parser("mermaid", help="修复 Mermaid 图表语法")
    p_mermaid.add_argument("wiki_dir", help=".deepwiki 目录路径")
    p_mermaid.add_argument("--dry-run", action="store_true", help="仅报告不修改")
    p_mermaid.add_argument("--json", metavar="FILE", help="输出修复报告为 JSON")
    p_mermaid.add_argument("-v", "--verbose", action="store_true")

    # quality subcommand
    p_quality = subparsers.add_parser("quality", help="检查文档质量")
    p_quality.add_argument("wiki_dir", help=".deepwiki 目录路径")
    p_quality.add_argument("--verbose", "-v", action="store_true")
    p_quality.add_argument("--json", metavar="FILE", help="输出报告为 JSON")

    # consistency subcommand
    p_consistency = subparsers.add_parser("consistency", help="跨模块一致性检查")
    p_consistency.add_argument("wiki_dir", help=".deepwiki 目录路径")
    p_consistency.add_argument("--json", metavar="FILE", help="输出报告为 JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Locate scripts directory (same directory as this file)
    scripts_dir = os.path.dirname(os.path.abspath(__file__))

    if args.command == "mermaid":
        script = os.path.join(scripts_dir, "wiki", "fix_mermaid.py")
        cmd = [sys.executable, script, args.wiki_dir]
        if args.dry_run:
            cmd.append("--dry-run")
        if args.json:
            cmd.extend(["--json", args.json])
        if args.verbose:
            cmd.append("-v")

    elif args.command == "quality":
        script = os.path.join(scripts_dir, "quality", "check_doc_quality.py")
        cmd = [sys.executable, script, args.wiki_dir]
        if args.verbose:
            cmd.append("--verbose")
        if args.json:
            cmd.extend(["--json", args.json])

    elif args.command == "consistency":
        script = os.path.join(scripts_dir, "quality", "check_cross_module_consistency.py")
        cmd = [sys.executable, script, args.wiki_dir]
        if args.json:
            cmd.extend(["--json", args.json])

    else:
        parser.print_help()
        sys.exit(1)

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
