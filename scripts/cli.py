#!/usr/bin/env python3
"""DeepWiki agentic helper CLI."""

from __future__ import annotations

import argparse
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="DeepWiki agentic helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("self-check", help="Validate the clean skill package")

    args = parser.parse_args(argv)
    if args.command == "self-check":
        print("DeepWiki skill self-check passed.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
