#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.quality.check_analysis_quality`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quality.check_analysis_quality import *  # noqa: F401,F403


if __name__ == "__main__":
    from scripts.quality.check_analysis_quality import main

    raise SystemExit(main())
