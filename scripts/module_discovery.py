"""Compatibility wrapper for :mod:`scripts.analysis.module_discovery`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.analysis.module_discovery import *  # noqa: F401,F403
