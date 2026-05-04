"""Compatibility wrapper for :mod:`scripts.analysis.scanner`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.analysis.scanner import *  # noqa: F401,F403
