#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.wiki.init_wiki`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.wiki.init_wiki import *  # noqa: F401,F403


if __name__ == "__main__":
    from scripts.wiki.init_wiki import main

    raise SystemExit(main())
