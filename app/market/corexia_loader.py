"""
COREXIA module loader.

Loads matrix_scanner modules without clobbering the local app package.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Tuple

from app.config import COREXIA_PATH

_COREXIA_APP = None
_COREXIA_REGIME = None


def _load_module(module_name: str, module_path: Path):
    if not module_path.exists():
        raise FileNotFoundError(f"Missing COREXIA module: {module_path}")

    if str(COREXIA_PATH) not in sys.path:
        sys.path.append(str(COREXIA_PATH))

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_corexia_modules() -> Tuple[object, object]:
    """
    Load COREXIA app.py and regime_archive.py as isolated modules.
    """
    global _COREXIA_APP, _COREXIA_REGIME

    if _COREXIA_APP and _COREXIA_REGIME:
        return _COREXIA_APP, _COREXIA_REGIME

    corexia_app_path = COREXIA_PATH / "app.py"
    corexia_regime_path = COREXIA_PATH / "regime_archive.py"

    _COREXIA_APP = _load_module("corexia_app", corexia_app_path)
    _COREXIA_REGIME = _load_module("corexia_regime", corexia_regime_path)

    return _COREXIA_APP, _COREXIA_REGIME
