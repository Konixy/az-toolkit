#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Remove Beat Jump grid reservation without changing global Quantize.

Empty on XDJ-AZ firmware 1.30: no rbp offsets have been verified.
"""

from tools.rx3_patcher.patchlib import run

MODULE_ID = "beatjump-no-quantize"

PATCHES = []


if __name__ == "__main__":
    raise SystemExit(run(__doc__.splitlines()[0], PATCHES))
