#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.postprocess`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.postprocess import *  # noqa: F401,F403


if __name__ == "__main__":
    from scripts.postprocess import main

    main()
