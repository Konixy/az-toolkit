# Reference

Commands, formats and platform findings. Written for a contributor.
Nothing here is needed to use the applications.

RX3 1.19 ARM32 addresses are not listed here. They must never be applied to an
XDJ-AZ `rbp`.

## Commands

Nothing in this repository is pip-installable. There is no packaging metadata
and no console script. Every entry point is invoked as a path.

### Make targets

| Target | Effect |
|---|---|
| `make help` | Print the target list. The default goal. |
| `make hook` | No-op on 1.30: records that no mapped AZ hook exists. Does not compile ARM32. |
| `make autoexec KEY=<path>` | Build `autoexec.bin`. `KEY` is required and must exist. |
| `make app` | Run XDJ-AZ Toolkit from source. |
| `make test` | Run the runtime regression guards, then the unit tests. |
| `make preflight` | Inspect every publishable tracked or untracked file. |
| `make clean` | Remove `build/` and nothing else. |

Variables: `PYTHON` defaults to `python3`, `BUILD_DIR` to `build`, `FIRMWARE` to
`1.30`, `MODULES` to empty, which means the manifest defaults.

```sh
make autoexec KEY=/absolute/path/to/aes256.key FIRMWARE=1.30
```

```sh
make autoexec KEY=/absolute/path/to/aes256.key FIRMWARE=1.30 \
  MODULES="probe logging instant-hotcue"
```

The RX3 `make emulate*` targets are not wired. See [emulator.md](emulator.md)
for historical RX3 1.19 notes only.

### Runtime build CLI

```sh
python3 tools/rx3_runtime/cli.py list --firmware 1.30
```

```sh
python3 tools/rx3_runtime/cli.py build --firmware 1.30 \
  --patch probe --patch logging --patch instant-hotcue \
  --key /path/to/aes256.key --output build
```

`--firmware` defaults to `1.30`. `--patch` repeats, and when it is omitted every
module whose manifest sets `default: true` is selected. `--key` and `--output`
are required. `--prebuilt-hook` is optional; 1.30 modules do not ship an ARM hook.

### Firmware image codec

```sh
python3 tools/rx3_firmware/firmware_image.py verify XDJAZv130.UPD
```

`verify` without `--key` prints the trailer and, if the payload starts with
LUKS magic, the cipher/mode/hash. It does not open the LUKS volume.

```sh
python3 tools/rx3_firmware/firmware_image.py verify-autoexec \
  build/autoexec.bin --key /path/to/aes256.key
```

`decrypt-autoexec IN OUT --key K` and `autoexec DIR OUT --key K` complete the
USB-image set. `encrypt` still writes an RX3-style cryptoloop `.UPD`. That is
the wrong shape for an AZ update. Do not flash it.

### Sidecar encoder

```sh
python3 tools/rx3_stems/make_sidecar.py vocals.wav "Artist - Title.rx3stem" \
  --match-full "Artist - Title.mp3" --separator-normalization 1.0
```

`--format` accepts `s16`, the default, or `f32`. `--match-full` validates trim
and padding against the full 44.1 kHz track.

### Offline patchers

Empty on 1.30. They refuse to rewrite a host copy of `rbp` until `PATCHES` is
filled together with `register_rbp_sha1` and matching `register_patch` calls.

```sh
python3 -m tools.rx3_patcher.instant_hotcue rbp --check
```

### Release plumbing

```sh
python3 scripts/package_release.py "dist/XDJ-AZ Toolkit" out.zip --include LICENSE
```

```sh
python3 scripts/smoke_desktop_app.py "dist/XDJ-AZ Toolkit"
```

```sh
python3 scripts/check_macos_bundle.py "dist/XDJ-AZ Toolkit.app"
```

```sh
./scripts/preflight.sh
```

`smoke_desktop_app.py` runs the packaged binary with `--self-test` under a
120-second timeout. `preflight.sh` rejects disallowed extensions, files over
2097152 bytes, and matches against its secret patterns.

### On-device

```sh
/mnt/iso/modules/decoder-sleep/apply.sh 100000 /tmp/az-decoder-sleep.log
```

The interval defaults to `100000` nanoseconds. The script needs `/bin/bash`,
requires a positive integer interval, waits up to 20 seconds for UDP port 20000,
and applies `bufsleep` on decks 0–3. Failure is logged and does not stop the
main runtime.

## Environment variables

| Variable | Read by | Effect |
|---|---|---|
| `RX3_SEPARATOR` | Stem Studio | Path to an `audio-separator` to use instead of `PATH` or the managed environment |
| `RX3_FFMPEG` | Stem Studio | Path to an `ffmpeg`. Used as given; a missing filter is reported, not worked around |
| `RX3_STEM_STUDIO_HOME` | Stem Studio | Overrides the managed runtime and model cache location |
| `RX3_PREBUILT_HOOK` | `rx3_toolbox.spec` | Optional path to a compiled hook. Ignored when unset; 1.30 does not need one |
| `AZ_STEMS_DIR` | on-device stems module | Published sidecar directory (symlink `/tmp/az-stems` when possible) |
| `DECODER_SLEEP_NS` | on-device decoder module | Overrides the polling interval, default `100000` |

## Build prerequisites

| Component | Version | Notes |
|---|---|---|
| Python | `3.12` in CI | No `requires-python` and no runtime guard exist |
| `cryptography` | `50.0.0` | Pinned in `requirements.txt` |
| `pycdlib` | `1.14.0` | Pinned. Imported lazily, with an `mkisofs` subprocess fallback |
| `pyinstaller` | `6.21.0` | Pinned in `requirements-release.txt` |
| FFmpeg | any complete build | Must carry `aformat`, `apad`, `aresample`, `astats`, `atrim`, `volume` |

The separation runtime needs a Python interpreter between 3.10 and 3.13 on the
host to seed its environment.

CI runs the source job on `ubuntu-24.04`, and application jobs on
`ubuntu-24.04`, `windows-2025`, `macos-latest` and `macos-15-intel`.

## Hardware and vendor platform

Findings from Pioneer’s published XDJ-AZ 1.04 GPL tree and from inspecting an
official `XDJAZv130.UPD` trailer. Proprietary `rbp` is not in this repository.

| Component | Observed value |
|---|---|
| SoC | Rockchip RK3399 |
| CPU | aarch64 (ARM64) |
| Device tree | `rk3399-atc-board-V03` |
| Overlay | `fs-overlay-atc` |
| Init | systemd, Buildroot |
| USB media | `/media/usb/...` via `device-mount.sh`, `/proc/udev_usbN` |
| USB autoexec helper | **not** in the published overlay |
| Main application | expected name `rbp`; path confirmed by the probe module at runtime |

The RX3 was i.MX6, ARM32 EABI5, SysV init, cryptoloop `.UPD`. Those facts do not
transfer. Compiling `--target=arm-linux-gnueabi` for this player is refused.

### Firmware image format

Two on-disk shapes exist.

**USB `autoexec.bin`** (what this toolkit writes): encrypted raw ISO 9660 volume
`UsbAuto`, no model trailer, no CRC. AES-256-CBC per 512-byte sector. IV is the
sector index as 32-bit little-endian, then 12 zero bytes. Effective key is first
31 bytes of the first line plus a NUL (`xstrncpy(..., 32)`).

**AZ `.UPD`**: LUKS1 (`LUKS\xba\xbe`), AES-XTS-plain64, SHA-256, then a 16-byte
trailer. Observed trailer model `XDJ-XZN`, version `1.30`. This toolkit will
describe the header and will not open or flash the volume.

**RX3 `.UPD`** (historical): same trailer layout with model `XDJ-RX3` and
cryptoloop payload. `encrypt` in `firmware_image.py` still produces that shape.

Rock Ridge extensions are required so `autoexec.sh` keeps its executable bit,
and the USB image size must stay aligned to 512 bytes.

## Beat Jump, Instant Hot Cue, stems mixing

Firmware `1.30` registers **no** guarded words. Offline patchers ship `PATCHES
= []`. `tests/test_module_consistency.py` requires those tables to stay in
agreement with `module.sh`.

Fill `register_rbp_sha1`, `register_patch` and the matching Python table in the
same change, from a probe log of *this* unit. Instant Hot Cue is one guarded
instruction that must select the direct start path only when the deck is
stopped.

Decoder sleep is not a binary patch. If UDP port 20000 is open it sends
`bufsleep N 100000` for `N` in `0 1 2 3`.

## Sidecar format

A 64-byte little-endian header followed by interleaved stereo vocal PCM. The
on-device mixer is not mapped on 1.30; the host encoder still writes this
container so a future hook can consume it.

| Offset | Size | Field |
|---:|---:|---|
| `0x00` | 8 | magic `RX3STM1\0` |
| `0x08` | 4 | sample rate, `44100` |
| `0x0c` | 4 | channel count, `2` |
| `0x10` | 4 | sample format: `1` float32, `2` int16 |
| `0x14` | 4 | header size, `64` |
| `0x18` | 8 | frame count |
| `0x20` | 32 | reserved, zero-filled |
| `0x40` | variable | interleaved stereo vocal PCM |

Sidecars live in `AZ_STEMS/<basename>.rx3stem`. Rekordbox truncates a filename
to the first 44 characters of its stem on export; Stem Studio uses the same
cut (`export_stem` in `tools/rx3_stems/rekordbox.py`).

Gain and encoder-delay handling are unchanged from the RX3 host pipeline:
normalization is pinned to 1.0, padding is measured with
`-flags2 +skip_manual`, and the instrumental on a future hook is full mix minus
vocal.

### Stem Studio internals

| Path | Contents |
|---|---|
| `tools/rx3_stems/rekordbox.py` | Rekordbox XML export parser |
| `tools/rx3_stems/provisioning.py` | runtime detection, acceleration profiles, environment provisioning |
| `tools/rx3_stems/separation.py` | model catalogue, tunable options, stored settings |
| `tools/rx3_stems/job.py` | separation and sidecar generation pipeline |
| `tools/rx3_stems/sidecar.py` | `.rx3stem` encoder |
| `tools/rx3_stems/make_sidecar.py` | encoder command-line front end |

audio-separator and FFmpeg are invoked as subprocesses.

## Module manifests

Each runtime feature lives under a firmware version directory and provides a
`manifest.json`. The GUI, the CLI and the release packager all discover the same
manifest rather than maintaining separate feature lists.

| Field | Meaning |
|---|---|
| `id` | Stable lowercase module identifier. |
| `firmware` | Exact compatible firmware revision; it must match the directory. |
| `runtime_directory` | Single safe directory name written into the ISO. |
| `namespace` | Unique POSIX-shell prefix for every lifecycle callback. |
| `default` | Selected by default when the module is user-selectable. |
| `selectable` | `false` for an internal service; direct selection is rejected. Defaults to `true`. |
| `order` | Stable load order; dependencies must have a lower order. |
| `requires` | Transitive module dependencies. |
| `conflicts` | Modules that cannot appear in the same runtime. |
| `files` | Source-to-runtime file mappings and executable bits. |
| `build_files` | Module-owned headers or other compile-time-only sources. |
| `arm_hook` | Optional hook source and ELF target. Unused on 1.30. |

The build resolves dependencies, rejects cycles/conflicts and writes the exact
device load order to `modules/index`. `BuildResult` reports this effective
selection.

### Example

```json
{
  "id": "probe",
  "name": "Safe inventory (required first run)",
  "description": "Writes what the stick can see and changes nothing.",
  "firmware": "1.30",
  "default": true,
  "order": 1,
  "runtime_directory": "probe",
  "namespace": "probe",
  "requires": [],
  "conflicts": [],
  "files": [
    {"source": "module.sh", "target": "module.sh", "executable": false}
  ]
}
```

The directory name must equal the `firmware` field, and ids, runtime directories
and shell namespaces must be unique for that firmware.
