#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.quality.build_evidence_index`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


if __name__ == "__main__":
    import runpy

    runpy.run_module("scripts.quality.build_evidence_index", run_name="__main__")
else:
    from scripts.quality.build_evidence_index import *  # noqa: F401,F403
