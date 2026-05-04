"""Compatibility wrapper for :mod:`scripts.core.importance_scoring`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.core.importance_scoring import *  # noqa: F401,F403
