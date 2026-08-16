#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Skip Hot Cue grid reservation on a stopped deck.

Empty on XDJ-AZ firmware 1.30: no rbp offsets have been verified. The
on-device module registers the same empty table, and
`tests/test_module_consistency.py` requires the two to stay in agreement.
"""

from tools.rx3_patcher.patchlib import run

MODULE_ID = "instant-hotcue"

# (offset, stock_hex, patched_hex, label) — filled only with a mapped SHA-1.
PATCHES = []


if __name__ == "__main__":
    raise SystemExit(run(__doc__.splitlines()[0], PATCHES))
