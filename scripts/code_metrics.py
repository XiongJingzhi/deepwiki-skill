"""Compatibility wrapper for :mod:`scripts.core.code_metrics`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.core.code_metrics import *  # noqa: F401,F403
