# The AZ mod

What the modules do, how the runtime is applied, and how to read what it left
behind. For a first run, follow the [Quick Start](../README.md#quick-start)
instead.

This is a port of the RX3 USB runtime. The XDJ-AZ is RK3399 aarch64 with
firmware `1.30`. RX3 ARM32 offsets, SHA-1 values and `librx3_core.so` are not
used. A build with no guarded words never touches `rbp`.

## The modules

| Module | Id | What changes | Needs | On by default |
|---|---|---|---|:--:|
| Safe inventory | `probe` | Read-only log of architecture, mounts, player binary, SHA-1. No writes. | — | yes |
| Instant Hot Cue | `instant-hotcue` | When mapped: a Hot Cue on a **stopped** deck starts at once. Playing decks stay stock. Empty table on 1.30. | — | yes |
| Session logging | `logging` | Writes `AZ_RUNTIME/session.txt`. Eject the stick, never yank it. | — | yes |
| Beat Jump ±32 | `beatjump-32bars` | Empty table on 1.30. Cannot write `rbp` yet. | `decoder-sleep` | no |
| Immediate Beat Jump | `beatjump-no-quantize` | Empty table on 1.30. Cannot write `rbp` yet. | `decoder-sleep` | no |
| Faster decoder polling | `decoder-sleep` | UDP `bufsleep` on decks 0–3 if port 20000 exists. No `rbp` write. | — | no |
| Stems (sidecar prep) | `stems` | Publishes `AZ_STEMS`. No pad mixing until a mapped core exists. | — | no |
| Diagnostic Telnet | `telnet` | BusyBox telnetd. Unencrypted. Isolated link only. | — | no |

There is no `keyshift` module and no performance `core`. Key shift is stock on
the AZ. On-device stem mixing needs a future aarch64 hook; it is not the RX3
ARM32 object.

The **Needs** column is enforced. Ticking either Beat Jump module also ticks
*Faster decoder polling*.

Telnet is unencrypted and, on Pioneer all-in-ones, is typically reachable only
through the rear computer USB port (APIPA `169.254.x.y`). Use it on an isolated
link, or leave it off.

## What actually happens on insertion

On the RX3, udev ran `decrypt_autoexec.sh`, which decrypted `autoexec.bin` and
executed `autoexec.sh` as root. The published AZ overlay does not contain that
helper. If the proprietary player still honours the file, the same ISO is
mounted and the same orchestrator runs. If it does not, the stick is an ordinary
Rekordbox export.

```text
AZ powered on
USB insertion
  (if Pioneer’s USB maintenance path exists)
    decrypt autoexec.bin
    run ./autoexec.sh <usb-mount> as root
  (otherwise)
    stock media mount, nothing else
```

`mod/autoexec.sh` holds the shared lifecycle: discovery, RAM-root validation,
guarded writes, process restart, rollback and logging. Each module owns its own
adapter. Adding or removing one requires no change to the orchestrator.

Nothing is flashed. When writes are enabled, they patch the copy of `rbp` held
in the RAM root. Power cycling discards it.

## Applying it

1. Make sure the drive is disconnected.
2. Power the AZ on and wait until the interface is fully loaded.
3. Insert the drive.
4. Leave the controls alone.
5. Eject the drive from the player when logging is on.

A default 1.30 image registers zero guarded words, so `rbp` is not restarted.
The log says `no guarded words: rbp will not be rewritten`.

## Reading the session log

With **Session logging** selected (the default on this port), every run writes
`AZ_RUNTIME/session.txt` to the drive.

| Line | Meaning |
|---|---|
| `=== complete ===` | The run finished. Last line of a good run. |
| `no guarded words: rbp will not be rewritten` | Expected on 1.30 until a hash is registered. |
| `STOP: effective root is not RAM-backed` | Persistent root; nothing was written. Probe report still ran. |
| `STOP: rbp is 64-bit` | A leftover ARM32 table was refused. |
| `STOP: unsupported rbp SHA-1` | Writes were requested but the hash is not registered. |
| `FAILED: ...` | Something went wrong during a write; previous bytes restored. |

On `STOP:` or `FAILED:`, delete `autoexec.bin` from the drive before using the
AZ again, then see [Troubleshooting](troubleshooting.md#the-session-log-says-stop-or-failed).

## Before it touches anything

The orchestrator verifies all of the following. A default 1.30 image stops after
step 2 because there are no guarded words:

1. the effective root mount is `tmpfs`, `ramfs` or `rootfs`;
2. `/root/pdj` is not a separate mount;
3. if any module registered a word: `rbp` is 32-bit ELF (aarch64 is refused until
   an aarch64 table exists), the SHA-1 is registered, and every word holds stock
   or already-patched bytes;
4. `rbp` is stopped before its backing file is written;
5. every write is read back and compared;
6. the replacement process stays alive, or the previous bytes and preload state
   are restored.

Stopping the process first is not optional: writing the backing file while its
executable pages are mapped can kill it with `SIGBUS`.

## Removing it

1. Stop playback and power off.
2. Remove the drive.
3. Power on without it, and confirm stock behaviour.
4. Delete `autoexec.bin` from the drive if it should stop applying on insertion.

## Safety

- Firmware `1.30` only.
- Never copy RX3 offsets, trampolines or SHA-1 values into `mod/1.30/`.
- Never flash a `.UPD` with this toolkit. AZ updates are LUKS.
- Keep a second, unmodified Rekordbox drive available.
- Start the AZ completely before inserting the runtime drive.
- Eject rather than yank when session logging is on.
- Read `AZ_RUNTIME/session.txt` before reporting a problem.
- Telnet traffic is unencrypted. Isolated links only.
