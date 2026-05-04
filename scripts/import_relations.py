"""Compatibility wrapper for :mod:`scripts.analysis.import_relations`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.analysis.import_relations import *  # noqa: F401,F403
