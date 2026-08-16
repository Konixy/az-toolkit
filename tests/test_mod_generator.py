# SPDX-License-Identifier: MPL-2.0
import importlib.util
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.rx3_runtime.build import build_runtime, discover_patches, resolve_patches


REPOSITORY = Path(__file__).parents[1]
FIRMWARE = "1.30"


def load_firmware_codec():
    path = REPOSITORY / "tools/rx3_firmware/firmware_image.py"
    spec = importlib.util.spec_from_file_location("firmware_image_builder_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModGeneratorTests(unittest.TestCase):
    def test_manifests_are_versioned_and_unique(self):
        patches = discover_patches(REPOSITORY, FIRMWARE)
        self.assertEqual(
            [patch.patch_id for patch in patches],
            [
                "probe",
                "decoder-sleep",
                "beatjump-32bars",
                "beatjump-no-quantize",
                "instant-hotcue",
                "stems",
                "telnet",
                "logging",
            ],
        )
        self.assertTrue(all(patch.directory.name == patch.firmware for patch in patches))
        self.assertTrue(next(patch for patch in patches if patch.patch_id == "probe").default)
        self.assertTrue(next(patch for patch in patches if patch.patch_id == "logging").default)
        self.assertFalse(next(patch for patch in patches if patch.patch_id == "telnet").default)
        self.assertFalse(next(patch for patch in patches if patch.patch_id == "decoder-sleep").default)
        instant = next(patch for patch in patches if patch.patch_id == "instant-hotcue")
        self.assertTrue(instant.default)
        self.assertEqual(instant.requires, ())
        for identifier in ("beatjump-32bars", "beatjump-no-quantize"):
            self.assertEqual(
                next(patch for patch in patches if patch.patch_id == identifier).requires,
                ("decoder-sleep",),
            )
        self.assertEqual(
            next(patch for patch in patches if patch.patch_id == "stems").requires,
            (),
        )

    def test_dependency_resolution_is_explicit_and_stable(self):
        patches = discover_patches(REPOSITORY, FIRMWARE)
        self.assertEqual(
            [patch.patch_id for patch in resolve_patches(patches, ["stems", "probe"])],
            ["probe", "stems"],
        )
        self.assertEqual(
            [patch.patch_id for patch in resolve_patches(patches, ["decoder-sleep"])],
            ["decoder-sleep"],
        )

    def test_dependency_cycles_and_conflicts_are_rejected(self):
        definitions = discover_patches(REPOSITORY, FIRMWARE)
        probe = next(patch for patch in definitions if patch.patch_id == "probe")
        stems = next(patch for patch in definitions if patch.patch_id == "stems")
        cycle = [
            replace(probe, requires=("stems",)),
            replace(stems, requires=("probe",)),
        ]
        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            resolve_patches(cycle, ["probe"])

        left = replace(probe, patch_id="left", selectable=True, conflicts=("right",))
        right = replace(probe, patch_id="right", selectable=True)
        with self.assertRaisesRegex(ValueError, "incompatible modules"):
            resolve_patches([left, right], ["left", "right"])

    def test_builds_selected_modules_without_external_iso_tool(self):
        codec = load_firmware_codec()
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            key = directory / "aes256.key"
            key.write_bytes(b"0123456789012345678901234567890\n")
            result = build_runtime(
                FIRMWARE,
                ["probe"],
                key,
                directory,
                root=REPOSITORY,
            )
            self.assertEqual(result.output, directory / "autoexec.bin")
            plain = codec.read_autoexec(result.output, key)
            self.assertEqual(codec.autoexec_iso_metadata(plain), "UsbAuto")
            self.assertEqual(result.patches, ("probe",))

    def test_build_does_not_add_unrelated_features(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            key = directory / "aes256.key"
            key.write_bytes(b"0123456789012345678901234567890\n")
            result = build_runtime(
                FIRMWARE, ["instant-hotcue"], key, directory, root=REPOSITORY
            )
            self.assertEqual(result.patches, ("instant-hotcue",))
            plain = load_firmware_codec().read_autoexec(result.output, key)

            self.assertIn(b"compatibility\ninstant-hotcue\n", plain)
            self.assertNotIn(b"\nstems\n", plain)

    def test_the_module_index_is_written_with_unix_line_endings(self):
        builder = (REPOSITORY / "tools/rx3_runtime/build.py").read_text()
        self.assertRegex(
            builder, r'modules / "index"\)\.write_text\((?s:.*?)newline=""'
        )

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            key = directory / "aes256.key"
            key.write_bytes(b"0123456789012345678901234567890\n")
            result = build_runtime(
                FIRMWARE, ["instant-hotcue"], key, directory, root=REPOSITORY
            )
            plain = load_firmware_codec().read_autoexec(result.output, key)
            self.assertNotIn(b"compatibility\r", plain)

    def test_the_session_log_ships_only_when_its_module_is_selected(self):
        codec = load_firmware_codec()
        autoexec = (REPOSITORY / "mod/autoexec.sh").read_text()
        self.assertIn("[ -d /mnt/iso/modules/logging ]", autoexec)

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            key = directory / "aes256.key"
            key.write_bytes(b"0123456789012345678901234567890\n")

            quiet = build_runtime(
                FIRMWARE, ["probe"], key, directory, root=REPOSITORY
            )
            self.assertNotIn("logging", quiet.patches)
            index = codec.read_autoexec(quiet.output, key)
            self.assertNotIn(b"\nlogging\n", index)

            verbose = build_runtime(
                FIRMWARE, ["probe", "logging"], key, directory, root=REPOSITORY
            )
            self.assertIn("logging", verbose.patches)
            index = codec.read_autoexec(verbose.output, key)
            self.assertIn(b"\nlogging\n", index)

    def test_the_logging_module_warns_about_pulling_the_drive_out(self):
        patch = next(
            item for item in discover_patches(REPOSITORY, FIRMWARE)
            if item.patch_id == "logging"
        )
        self.assertTrue(patch.default)
        self.assertTrue(patch.selectable)
        self.assertIn("EJECT", patch.description)
        self.assertIn("NEVER PULL IT OUT", patch.description)

    def test_rejects_unknown_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            key = directory / "aes256.key"
            key.write_bytes(b"key\n")
            with self.assertRaisesRegex(ValueError, "unknown patch"):
                build_runtime(FIRMWARE, ["not-a-patch"], key, directory, root=REPOSITORY)

    def test_default_build_is_probe_logging_and_inert_hotcue(self):
        codec = load_firmware_codec()
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            key = directory / "aes256.key"
            key.write_bytes(b"0123456789012345678901234567890\n")
            defaults = [
                patch.patch_id
                for patch in discover_patches(REPOSITORY, FIRMWARE)
                if patch.selectable and patch.default
            ]
            result = build_runtime(
                FIRMWARE, defaults, key, directory, root=REPOSITORY
            )
            self.assertEqual(result.patches, ("probe", "instant-hotcue", "logging"))
            plain = codec.read_autoexec(result.output, key)
            self.assertIn(b"compatibility\nprobe\ninstant-hotcue\nlogging\n", plain)

    def test_no_internal_modules_are_selectable_directly(self):
        internals = [patch.patch_id for patch in discover_patches(REPOSITORY, FIRMWARE) if not patch.selectable]
        self.assertEqual(internals, [])


if __name__ == "__main__":
    unittest.main()
