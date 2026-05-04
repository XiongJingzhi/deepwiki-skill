"""Compatibility wrapper for :mod:`scripts.analysis.context_budget`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.analysis.context_budget import *  # noqa: F401,F403
