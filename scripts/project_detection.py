"""Compatibility wrapper for :mod:`scripts.analysis.project_detection`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.analysis.project_detection import *  # noqa: F401,F403
