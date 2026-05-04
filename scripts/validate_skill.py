#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.quality.validate_skill`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quality.validate_skill import *  # noqa: F401,F403


if __name__ == "__main__":
    from scripts.quality.validate_skill import main

    raise SystemExit(main())
