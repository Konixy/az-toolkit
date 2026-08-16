# SPDX-License-Identifier: MPL-2.0
"""Reinserting a drive must not restart the player.

These drive the real `stems_prepare` of the on-device module.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_API = ROOT / "mod/lib/module-api.sh"
STEMS_MODULE = ROOT / "mod/modules/stems/1.30/module.sh"

HARNESS = r"""
say() { echo "$@" >> "$SESSION_LOG"; }
PATCH_TABLE=""
PATCH_OFFSETS=""
PREPARE_HOOKS=""
AFTER_LAUNCH_HOOKS=""
POST_LAUNCH_HOOKS=""
REPORT_HOOKS=""
RBP_READY_FILES=""
RBP_DIAGNOSTIC_FILES=""
RUNTIME_PRELOAD_ENTRIES=""
LOADED_MODULES=""
CURRENT_MODULE=""
CURRENT_NAMESPACE=""
MODULE_LOAD_FAILED=0
NEED_RBP_RESTART=0
RESTART_REQUESTED_BY=""
RUNNING_HOOK=""
. "$MODULE_API"

rbp_environment_value()
{
    [ "$1" = AZ_STEMS_DIR ] || return 1
    printf '%s' "$RUNNING_STEMS_DIR"
}

. "$STEMS_MODULE"
STEMS_LINK=$FIXED_PATH
run_hooks "$PREPARE_HOOKS"
echo "restart=$NEED_RBP_RESTART" >> "$SESSION_LOG"
echo "published=$AZ_STEMS_DIR" >> "$SESSION_LOG"
echo "requested-by:$RESTART_REQUESTED_BY" >> "$SESSION_LOG"
"""


class Deck:
    def __init__(self, root: Path):
        self.root = root
        self.fixed_path = root / "tmp/az-stems"
        self.fixed_path.parent.mkdir(parents=True, exist_ok=True)
        self.running = ""

    def mount(self, device: str, sidecars: int = 2) -> Path:
        usb = self.root / "media/usb1" / device
        stems = usb / "AZ_STEMS"
        stems.mkdir(parents=True, exist_ok=True)
        for index in range(sidecars):
            (stems / f"Artist - {index}.rx3stem").write_bytes(b"x" * 128)
        return usb

    def insert(self, device: str, **kwargs) -> dict:
        usb = self.mount(device, **kwargs)
        log = self.root / "session.txt"
        log.write_text("")
        result = subprocess.run(
            ["sh", "-s"],
            input=HARNESS,
            text=True,
            capture_output=True,
            check=False,
            env={
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                "MODULE_API": str(MODULE_API),
                "STEMS_MODULE": str(STEMS_MODULE),
                "SESSION_LOG": str(log),
                "FIXED_PATH": str(self.fixed_path),
                "USB": str(usb),
                "RUNNING_STEMS_DIR": self.running,
            },
        )
        assert result.returncode == 0, result.stderr
        lines = log.read_text().splitlines()
        state = {
            "restart": next(l for l in lines if l.startswith("restart=")).split("=", 1)[1],
            "published": next(
                l for l in lines if l.startswith("published=")
            ).split("=", 1)[1],
            "lines": lines,
        }
        if state["restart"] == "1":
            self.running = state["published"]
        return state


class ReinsertionTests(unittest.TestCase):
    def test_stems_prepare_does_not_restart_rbp_on_1_30(self):
        with tempfile.TemporaryDirectory() as directory:
            deck = Deck(Path(directory))
            first = deck.insert("sda2")
            self.assertEqual(first["restart"], "0", first["lines"])
            second = deck.insert("sdb2")
            self.assertEqual(second["restart"], "0", second["lines"])
            self.assertEqual(second["published"], first["published"])
            self.assertEqual(
                deck.fixed_path.resolve(),
                (Path(directory) / "media/usb1/sdb2/AZ_STEMS").resolve(),
            )

    def test_the_published_path_never_names_the_mount_point(self):
        with tempfile.TemporaryDirectory() as directory:
            deck = Deck(Path(directory))
            state = deck.insert("sda2")
            self.assertEqual(state["published"], str(deck.fixed_path))
            self.assertNotIn("sda2", state["published"])

    def test_a_fixed_path_that_cannot_be_published_falls_back_to_the_mount(self):
        with tempfile.TemporaryDirectory() as directory:
            deck = Deck(Path(directory))
            deck.fixed_path.mkdir(parents=True)
            state = deck.insert("sda2")
            self.assertEqual(
                state["published"], str(Path(directory) / "media/usb1/sda2/AZ_STEMS")
            )
            self.assertTrue(
                any("falling back to the mount path" in line for line in state["lines"]),
                state["lines"],
            )

    def test_the_sidecar_count_still_reads_the_drive_itself(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Deck(Path(directory)).insert("sda2", sidecars=4)
            self.assertTrue(
                any("4 sidecar(s)" in line for line in state["lines"]), state["lines"]
            )


if __name__ == "__main__":
    unittest.main()
