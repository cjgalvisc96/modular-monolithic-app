"""Architecture boundary tests — runs import-linter contracts from pyproject.toml.

Asserts layer direction (domain ← application ← infrastructure), bounded-context
isolation, domain framework-purity, and the presentation→infrastructure ban.
"""

from __future__ import annotations

import subprocess
import sys

import pytest


def test_import_linter_contracts_pass():
    result = subprocess.run(
        [sys.executable, "-m", "importlinter.cli", "lint"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail("import-linter contracts failed:\n" + result.stdout + "\n" + result.stderr)
