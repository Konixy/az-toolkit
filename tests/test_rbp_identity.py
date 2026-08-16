# SPDX-License-Identifier: MPL-2.0
"""AZ 1.30 must not ship rbp writes until a mapped SHA-1 exists."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools.rx3_runtime.build import discover_patches


ROOT = Path(__file__).parents[1]
REGISTER_PATCH = re.compile(r"^register_patch\s+", re.MULTILINE)


class AzIdentityTests(unittest.TestCase):
    def test_no_module_registers_a_binary_patch_on_1_30(self):
        for patch in discover_patches(ROOT, "1.30"):
            module = (patch.directory / "module.sh").read_text(encoding="utf-8")
            self.assertIsNone(
                REGISTER_PATCH.search(module),
                f"{patch.patch_id} still registers a guarded word",
            )

    def test_compatibility_registers_no_rbp_hash(self):
        text = (ROOT / "mod/1.30/compatibility.sh").read_text(encoding="utf-8")
        self.assertNotIn("register_rbp_sha1", text)

    def test_rx3_firmware_keyshift_and_core_are_gone(self):
        self.assertFalse((ROOT / "mod/1.19").exists())
        self.assertFalse((ROOT / "mod/modules/keyshift").exists())
        self.assertFalse((ROOT / "mod/modules/core").exists())
        patches = discover_patches(ROOT)
        self.assertEqual({patch.firmware for patch in patches}, {"1.30"})
        identifiers = {patch.patch_id for patch in patches}
        self.assertNotIn("keyshift", identifiers)
        self.assertNotIn("core", identifiers)
        self.assertIn("probe", identifiers)
        self.assertIn("instant-hotcue", identifiers)

    def test_autoexec_skips_identity_when_there_are_no_guarded_words(self):
        text = (ROOT / "mod/autoexec.sh").read_text(encoding="utf-8")
        self.assertIn('if [ "$PATCH_COUNT" = "0" ]; then', text)
        self.assertIn("no guarded words: rbp will not be rewritten", text)
        self.assertIn("STOP: effective root is not RAM-backed", text)
        self.assertIn("STOP: unsupported rbp SHA-1", text)
        self.assertIn("rbp ELF class:", text)
        self.assertIn("AZ_RUNTIME", text)
        self.assertNotIn("RX3_RUNTIME", text)


if __name__ == "__main__":
    unittest.main()
