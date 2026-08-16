# SPDX-License-Identifier: MPL-2.0
import unittest
from importlib import import_module


PATCH_32_BARS = "tools.rx3_patcher.beatjump_32bars"
PATCH_NO_QUANTIZE = "tools.rx3_patcher.beatjump_no_quantize"
PATCH_HOTCUE = "tools.rx3_patcher.instant_hotcue"


def load_patch_table(name):
    return import_module(name).PATCHES


class BeatJumpPatchTests(unittest.TestCase):
    def test_az_1_30_patch_tables_are_empty(self):
        self.assertEqual(load_patch_table(PATCH_32_BARS), [])
        self.assertEqual(load_patch_table(PATCH_NO_QUANTIZE), [])
        self.assertEqual(load_patch_table(PATCH_HOTCUE), [])


if __name__ == "__main__":
    unittest.main()
