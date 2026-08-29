# Troubleshooting

Symptoms, in the order you are likely to hit them. Each heading is linkable.

## macOS says the application is damaged

It is unsigned, and macOS refuses unsigned applications that carry a download
marker. Clear the marker on the unpacked `.app`, wherever you actually put it,
not on the `.zip`:

```sh
xattr -rc "/path/to/XDJ-AZ Toolkit.app"
```

Control-click then Open used to be enough. Recent macOS releases no longer offer
that path for an unsigned application.

On Windows the equivalent is a SmartScreen dialog: choose **More info**, then
**Run anyway**.

## Nothing happens when I insert the drive

Check four things, in this order:

1. the file is named exactly `autoexec.bin`, lower case, no second extension;
2. it sits at the root of the drive, not in a folder;
3. it was built for firmware `1.30`, and the AZ is running `1.30`;
4. the AZ still consumes Pioneer’s USB `autoexec.bin` path.

The published AZ GPL overlay has no `decrypt_autoexec.sh`. On firmware `1.30`
the measured result is that the player ignores the file: no `AZ_RUNTIME/`
folder, stock behaviour. See [the hardware probe](az-hardware-probe.md). That
is not a brick. Do not flash a `.UPD` to force it.

If the AZ does not see the drive at all, it is formatted as something other
than FAT32 or exFAT, or it was unplugged without ejecting.

A key file that is empty, or that holds something other than the key on its
first line, produces an `autoexec.bin` the player decrypts to garbage and
silently ignores. There is no error on the device.

## The interface does not come back

Remove the drive and power cycle. The AZ returns to stock, because nothing was
written to internal storage.

To find out why, keep **Session logging** ticked (it is on by default on this
port), reproduce, and read `AZ_RUNTIME/session.txt` from the drive on your
computer.

## There is no session log on the drive

Either logging was unticked in the builder, or the AZ never ran `autoexec.sh`.
A missing folder with logging still selected is the “USB path absent” case
above.

When logging *is* on and the script ran: **eject the drive from the AZ, never
pull it out**. The player keeps the log file open for as long as it plays, so
yanking it mid-write can corrupt the stick.

## The session log says STOP or FAILED

Delete `autoexec.bin` from the drive before using the AZ again.

`STOP:` means a precondition failed and nothing was modified. Common lines on
this port:

| Line | Meaning |
|---|---|
| `STOP: effective root is not RAM-backed` | Refusing a persistent write. Probe output may still be in the log. |
| `STOP: /root/pdj is a separate mount` | Same idea. |
| `STOP: rbp is 64-bit` | An ARM32 patch table was refused. |
| `STOP: unsupported rbp SHA-1` | Writes were requested but no hash is registered for 1.30. |

A default build registers zero guarded words, so the SHA-1 check is skipped and
the log should say `no guarded words: rbp will not be rewritten`.

`FAILED:` means something went wrong during a write and the previous state was
restored. Attach the full `session.txt` when reporting the problem. Redact
nothing about mounts and hashes; never attach a `.key` or a `.UPD`.

## Slip Loop pads 7 and 8 still create loops

Expected on firmware `1.30`. On-device stem mixing is not mapped. Unprepared
tracks would keep stock Slip Loop even after a future hook.

## Instant Hot Cue still waits for the grid

Expected on firmware `1.30`. The module is selected by default but registers no
bytes until a probe log maps the site. Playing decks are supposed to keep stock
quantize even after that.

## A prepared track has no stem controls

On 1.30, no prepared track has stem controls yet. When a hook exists: the
sidecar and the audio file must share exactly the same name before the
extension. Rekordbox cuts a filename to 44 characters on export; Stem Studio
applies the same cut.

Check also that `AZ_STEMS` sits at the root of the drive.

## The instrumental still has the vocal in it

Not applicable until on-device mixing exists. Host-side sidecars still need a
current toolkit so encoder delay is measured; see the RX3 notes in older
changelogs if you are generating files for a future hook.

## Stem Studio reports a missing runtime

Use **Install** in Advanced options, Runtime tab. Or point `RX3_SEPARATOR` and
`RX3_FFMPEG` at your own installation of audio-separator and FFmpeg.

## Runtime installation refuses to start

No Python between 3.10 and 3.13 was found on your computer. Install one from
[python.org](https://www.python.org/downloads/) and retry.

## Every track fails

If separation itself completes and then every track fails, the managed
environment is incomplete. Use **Install** again. If the failure mentions
`No such file or directory: 'ffmpeg'`, reinstall the runtime or put FFmpeg on
`PATH`.

## Separation fails partway with an FFmpeg filter error

The FFmpeg on your `PATH` is missing a filter the pipeline needs. Install the
separation runtime. If you set `RX3_FFMPEG` yourself, that override is used as
given.

## The GPU is idle during separation

The runtime was installed for a different accelerator. Select **Reinstall**.
On an Intel Mac this is expected: audio-separator gates its Metal path on an
ARM processor.

## The waveform still shows the full track

Expected. The waveform is precomputed from the file.
