"""Import integration modules without Home Assistant installed.

The package ``__init__`` imports Home Assistant, so a bare package object
pointing at the integration folder is registered first. Modules that only
use the standard library (api, const, helpers, robot) can then be imported
normally, including their relative imports.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
import types

PACKAGE = "ezviz_vacuum_under_test"
PACKAGE_DIR = Path(__file__).parents[1] / "custom_components" / "ezviz_vacuum"


def load(module: str) -> types.ModuleType:
    """Import ``module`` from the integration package."""
    if PACKAGE not in sys.modules:
        package = types.ModuleType(PACKAGE)
        package.__path__ = [str(PACKAGE_DIR)]
        sys.modules[PACKAGE] = package
    return importlib.import_module(f"{PACKAGE}.{module}")
