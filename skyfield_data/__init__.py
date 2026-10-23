"""Local compatibility shim for skyfield-data.

``skyfield_data.get_skyfield_data_path()`` is what ``divination/_ephem.py`` hands to
skyfield's ``Loader``.  Resolution order:

1. the repository root, when a vendored ``de421.bsp`` is present (local dev, tests);
2. ``$SKYFIELD_PATH``, the directory baked into the runtime image at build time;
3. skyfield's own download cache (``~/.skyfield``), which downloads on first use.

``de421.bsp`` is gitignored (16.8MB binary), so a fresh clone has none of these
until something fetches it — the fallbacks keep that a first-run download instead
of a crash.
"""
from __future__ import annotations

import os
from pathlib import Path

EPHEMERIS_FILENAME = "de421.bsp"


def get_skyfield_data_path() -> str:
    root = Path(__file__).resolve().parents[1]
    if (root / EPHEMERIS_FILENAME).exists():
        return str(root)

    configured = os.environ.get("SKYFIELD_PATH")
    if configured and Path(configured).exists():
        return str(configured)

    return str(Path.home() / ".skyfield")
