"""Resolve the application's portable runtime-data folder in one place."""

from __future__ import annotations

import os
import json
from pathlib import Path
import sys


APP_FOLDER = "CivitaiArtistDiscovery"
LEGACY_APP_FOLDER = "CivitaiArtistHistory"
DATA_DIR_ENV = "CIVITAI_HISTORY_DATA_DIR"


def application_root() -> Path:
    """Return the folder containing the executable, or the source checkout."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def _base() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share")


def data_root() -> Path:
    """Use isolated 3.0 data; never migrate an installed application's data."""
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override)
    from .build_config import ENVIRONMENT
    return application_root() / ('data-music-discovery' if ENVIRONMENT == 'production' else 'data-music-development')
