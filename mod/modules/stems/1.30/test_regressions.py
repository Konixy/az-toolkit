#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Static guards for the AZ 1.30 stems module."""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parent
MODULE = (ROOT / "module.sh").read_text()
MANIFEST = json.loads((ROOT / "manifest.json").read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


require(
    "register_prepare_hook stems_prepare" in MODULE
    and "register_after_launch_hook stems_after_launch" in MODULE
    and "export AZ_STEMS_DIR" in MODULE,
    "stem lifecycle logic must remain owned by the stems module",
)
require(
    MANIFEST["requires"] == [] and MANIFEST["conflicts"] == [],
    "1.30 stems must not pull a performance core that is not mapped",
)
require(
    "register_patch" not in MODULE,
    "stems must not write rbp until a mapped core exists",
)
require(
    "librx3" not in MODULE and "librx" not in MODULE,
    "the stems module must not install a shared object of its own",
)
require(
    'STEMS_DIR="$USB/AZ_STEMS"' in MODULE,
    "sidecars live in AZ_STEMS on the stick",
)

print("Stems regression guards: OK")
