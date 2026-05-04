"""Compatibility wrapper for :mod:`scripts.pipeline.page_context`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.pipeline.page_context import *  # noqa: F401,F403
