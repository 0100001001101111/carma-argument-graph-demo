#!/usr/bin/env python3
"""Run the demo without installing the package."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from aletheia_argument_graph.cli import main  # noqa: E402

raise SystemExit(main())
