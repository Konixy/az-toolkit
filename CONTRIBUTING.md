# Contributing

Contributions are limited to original source code, tests, and XDJ-AZ
interoperability documentation.

By submitting a contribution you agree to license it under the Mozilla Public
License 2.0. Submit only material you created or have sufficient rights to
license under those terms.

## What must never be submitted

Firmware, manufacturer code, manufacturer binaries or GUI assets, credentials,
encryption keys, dumps, mounted images, copyrighted audio, extracted proprietary
assets, and generated artifacts.

Do not submit RX3 `rbp` SHA-1 values, ARM32 trampolines, or firmware 1.19
offsets as if they applied to the AZ. They do not.

`.gitignore` prevents the common accidents. It does not remove material already
in Git history. Run `make preflight`, review `git status`, and inspect the
staged diff before every public push.

Tagged GitHub Releases are the only exception for compiled artifacts: CI attaches
the desktop applications. Firmware, manufacturer code, keys, credentials,
generated `autoexec.bin` files, and ARM32 hooks are never release assets.

## Repository layout

Everything under `mod/` executes on the AZ, as root, if Pioneer’s USB
maintenance path still runs `autoexec.bin`. Everything above it runs on your
computer.

| Path | Contents |
|---|---|
| `mod/autoexec.sh` | On-device orchestrator: indexed module loading, validation, guarded writes, rollback, logging |
| `mod/lib/module-api.sh` | Registration contract shared by every on-device module |
| `mod/<firmware>/compatibility.sh` | Accepted `rbp` SHA-1 values for that firmware (empty on 1.30) |
| `mod/modules/<id>/<firmware>/` | One directory per module, named after its manifest `id`, versioned by firmware |
| `apps/rx3-toolbox/` | The Tkinter application: modules tab and stems tab |
| `tools/rx3_runtime/` | Build engine and its CLI |
| `tools/rx3_patcher/` | Offline counterparts to the on-device byte patches (empty tables on 1.30) |
| `tools/rx3_firmware/` | USB cryptoloop codec, LUKS header inspect, ISO 9660 authoring |
| `tools/rx3_stems/` | Rekordbox parsing, provisioning, separation, sidecar encoding |
| `scripts/` | Release packaging and the publication preflight |
| `tests/` | Unit tests |

Directory names still say `rx3_*` because this is a fork. Behaviour is AZ.

Neither GUI tab holds build or separation logic. Both drive `tools/`.

## Building from source

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

CI runs on Python 3.12. Clang is not required: firmware 1.30 has no mapped
aarch64 hook, and `make hook` records that skip instead of compiling the RX3
ARM32 core.

Run the interface from the repository:

```sh
make app
```

Build `autoexec.bin` from the terminal. Without `MODULES`, the manifest defaults
are used (`probe`, `logging`, `instant-hotcue`):

```sh
make autoexec KEY=/absolute/path/to/aes256.key FIRMWARE=1.30
```

## Before submitting

```sh
make test
make preflight
```

`make test` runs the module regression guards and the unit tests.
`make preflight` inspects every publishable tracked or untracked file.

## Hardware acceptance

Static tests do not cover the device. Until a mapped SHA-1 exists, the only
honest hardware claim is:

1. power the AZ on with the stick out;
2. insert a default (probe + logging) stick;
3. either `AZ_RUNTIME/session.txt` appears and ends with `=== complete ===`
   and `no guarded words: rbp will not be rewritten`, or nothing happens and
   the unit stays stock;
4. eject (do not yank);
5. power cycle without the stick and confirm stock behaviour.

Do not claim Instant Hot Cue, Beat Jump or stems mixing work on hardware until
the corresponding guarded words are registered and this sequence is expanded.

A useful probe log includes `uname`, ELF class of `rbp`, its SHA-1, and whether
`decrypt_autoexec.sh` / `aes256.key` are present. Redact keys.

## Adding a module

Each module lives in `mod/modules/<id>/<firmware>/`, where `<id>` is the
`id` its `manifest.json` declares, and provides a valid `manifest.json`. The
GUI, the CLI and the release packager must keep discovering the same manifest
rather than maintaining separate feature lists. The schema is in
[docs/reference.md](docs/reference.md#module-manifests).

Nothing else needs editing to add a module: `make test` picks up a
`test_regressions.py` placed beside the manifest.

A module that also ships an offline patcher puts it in `tools/rx3_patcher/`,
not under `mod/` — everything under `mod/` executes on the deck. The
patcher declares `MODULE_ID` so `tests/test_module_consistency.py` can prove
its table and the module's `register_patch` calls agree.

`register_patch` and `register_rbp_sha1` must be added together, and never with
RX3 words. An empty table is the correct 1.30 state.

Dependencies belong in `requires`; feature code must never probe for a sibling
module to create an implicit dependency. The build rejects missing modules,
cycles and conflicts, then writes the resolved order to `modules/index`.

Every `module.sh` starts with `module_begin <id> <namespace>`. Its lifecycle
function names must start with that namespace. Sourcing a module may register
contracts only; device mutation belongs in a registered lifecycle hook.

## Supporting another firmware build

Similar-looking addresses are not evidence. A submission adding support for
another AZ firmware build must identify:

- the exact target hash;
- the byte guards;
- the offsets;
- the static validation method;
- the result on hardware.

Every guarded word must have a stock value and a patched value, and the
orchestrator must be able to tell them apart. ELF class must match the table
(aarch64 is not ARM32).

## Security

Do not open an issue containing an encryption key, firmware image, dump,
credential, or personal data. Treat an exposed key as compromised; deleting it
from a commit does not remove it from Git history. See
[SECURITY.md](SECURITY.md).
