#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.analysis.extract_structure`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


if __name__ == "__main__":
    import runpy

    runpy.run_module("scripts.analysis.extract_structure", run_name="__main__")
else:
    from scripts.analysis.extract_structure import *  # noqa: F401,F403
