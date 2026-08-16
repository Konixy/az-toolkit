# XDJ-AZ Toolkit

One Tkinter desktop application with a tab for each half of preparing an AZ USB
drive.

| File | Contents |
| --- | --- |
| `main.py` | The window, the two tabs, and the `--self-test` entry point CI smoke-tests. |
| `mod_generator.py` | **Modules installation** tab: selects firmware-specific modules and writes `autoexec.bin`. |
| `stem_studio.py` | **Stems preparation** tab: generates `.rx3stem` vocal sidecars from a Rekordbox playlist. |
| `theme.py` | Appearance detection, the named ttk styles both tabs use, and the shared path-row widget. |

Neither tab holds engine logic. The modules tab uses `tools.rx3_runtime.build`;
the stems tab uses `tools/rx3_stems/`.

Run from source:

```sh
make app
# or
python3 apps/rx3-toolbox/main.py
```

Firmware `1.30` has no mapped ARM hook. `RX3_PREBUILT_HOOK` is optional; the
PyInstaller spec embeds a hook only when that file exists.

## Appearance

`theme.py` decides light or dark from the colour Tk is actually painting rather
than from an operating-system query, and registers `Muted.TLabel` and
`Warning.TLabel` for secondary text. Nothing may hard-code a foreground colour:
a fixed grey is unreadable in whichever appearance it was not chosen for. Only
classic Tk widgets, which ttk styles do not reach, are recoloured by hand — the
log pane is the one case.

## Quality presets

The stems tab offers **Fast**, **High quality**, and **Custom**. The first two
are defined in `tools/rx3_stems/separation.py` as one or more `Variant`s — a
model candidate list plus the tuning that model wants — and a preset always
names exactly one configuration. Editing anything in Advanced options switches
the setting to Custom rather than leaving a preset name on a configuration it no
longer describes.

A preset has a second variant when the trade-off it names cannot be expressed
the same way everywhere. Separation runs under two inference runtimes, and
`Acceleration.accelerates_torch` / `accelerates_onnx` in `provisioning.py`
record which of them each build actually gets its work done on the GPU with.
Where PyTorch is accelerated and ONNX Runtime is not, `Acceleration.prefers_torch`
is true and `apply_preset` takes the Torch variant.

Those two flags are the place to state such a fact, and they are answers to
measurements rather than to capability queries. If you change one of these
flags, say what you measured and on what.

Neither preset predicts how long it will take. Speed depends on the model, the
device and the machine's load, so `tools/rx3_stems/estimate.py` measures it per
run.

The per-user data directory still uses the Stem Studio names
(`RX3 Stem Studio` / `rx3-stem-studio`) so an environment installed by the RX3
app is reused rather than downloaded again.

User documentation is in [README.md](../../README.md),
[docs/mod-rx3.md](../../docs/mod-rx3.md), and
[docs/stem-studio.md](../../docs/stem-studio.md). Build and packaging details
are in [CONTRIBUTING.md](../../CONTRIBUTING.md).
