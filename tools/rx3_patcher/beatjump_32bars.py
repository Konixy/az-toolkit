#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Beat Jump ±32 offline patcher.

Empty on XDJ-AZ firmware 1.30: no rbp offsets have been verified. The
on-device module registers the same empty table.
"""

from tools.rx3_patcher.patchlib import run

MODULE_ID = "beatjump-32bars"

PATCHES = []


if __name__ == "__main__":
    raise SystemExit(run(__doc__.splitlines()[0], PATCHES))
