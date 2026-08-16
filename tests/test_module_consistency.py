# SPDX-License-Identifier: MPL-2.0
"""Cross-checks for facts that are stated twice in two different languages.

Each duplication below is deliberate: the device applies patches from shell at
boot, while the offline patcher rewrites a file on a workstation. Nothing in
the build makes the two copies agree, so these tests do.

Modules are located through their manifest rather than by path, so moving a
module directory does not silently disable a guard.
"""

import re
import sys
import unittest
from importlib import import_module
from pathlib import Path

REPOSITORY = Path(__file__).parents[1]
PATCHER_PACKAGE = REPOSITORY / "tools/rx3_patcher"
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(REPOSITORY / "tools"))

from rx3_runtime.build import discover_patches  # noqa: E402
from rx3_stems import sidecar  # noqa: E402


REGISTER_PATCH = re.compile(
    r"^register_patch\s+(\d+)\s+'([^']*)'\s+'([^']*)'\s+(\S+)",
    re.MULTILINE,
)
OCTAL_BYTE = re.compile(r"\\([0-7]{1,3})")


def shell_bytes(literal):
    """Decode the octal escapes `register_patch` hands to printf."""
    decoded = OCTAL_BYTE.sub(lambda match: chr(int(match.group(1), 8)), literal)
    return decoded.encode("latin-1")


def modules_by_id():
    return {patch.patch_id: patch for patch in discover_patches()}


class OfflinePatcherTests(unittest.TestCase):
    """The offline patchers and `module.sh` must rewrite the same words."""

    def test_offline_tables_match_the_device_registrations(self):
        definitions = modules_by_id()
        checked = 0
        for patcher in sorted(PATCHER_PACKAGE.glob("*.py")):
            if patcher.name.startswith("_") or patcher.name == "patchlib.py":
                continue
            imported = import_module(f"tools.rx3_patcher.{patcher.stem}")
            patch_id = imported.MODULE_ID

            self.assertIn(
                patch_id, definitions,
                f"{patcher.name}: MODULE_ID {patch_id!r} matches no manifest",
            )
            definition = definitions[patch_id]
            offline = {
                offset: (bytes.fromhex(stock), bytes.fromhex(patched))
                for offset, stock, patched, _label in imported.PATCHES
            }

            module_script = definition.directory / "module.sh"
            device = {
                int(offset): (shell_bytes(stock), shell_bytes(patched))
                for offset, stock, patched, _label in REGISTER_PATCH.findall(
                    module_script.read_text(encoding="utf-8")
                )
            }

            with self.subTest(module=patch_id):
                self.assertEqual(
                    sorted(offline), sorted(device),
                    f"{patch_id}: patch.py and module.sh disagree on which "
                    f"offsets are patched",
                )
                for offset in sorted(offline):
                    self.assertEqual(
                        offline[offset], device[offset],
                        f"{patch_id}: offset {offset} (0x{offset:X}) has "
                        f"different stock/patched words in patch.py and module.sh",
                    )
                for stock, patched in offline.values():
                    self.assertEqual(len(stock), 4)
                    self.assertEqual(len(patched), 4)
                    self.assertNotEqual(stock, patched)
            checked += 1

        self.assertTrue(checked, "no offline patcher was found to cross-check")


class SidecarHeaderTests(unittest.TestCase):
    """Host-side `.rx3stem` layout. No AZ performance core parses this yet."""

    def test_header_layout_is_stable(self):
        self.assertEqual(sidecar.HEADER.format, "<8sIIIIQ32s")
        self.assertEqual(sidecar.HEADER.size, 64)
        self.assertEqual(sidecar.MAGIC, b"RX3STM1\0")
        self.assertIn("stems", modules_by_id())
        stems = modules_by_id()["stems"]
        self.assertEqual(stems.firmware, "1.30")
        self.assertFalse((stems.directory / "rx3_stems_decl.h").exists())


if __name__ == "__main__":
    unittest.main()
