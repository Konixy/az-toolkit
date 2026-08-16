<h1 align="center">
  XDJ-AZ Toolkit
</h1>

<p align="center">
  <b>A fail-closed USB runtime for the XDJ-AZ, plus stem preparation on your computer.</b><br>
  No flashing. No firmware surgery. Pull the USB stick out and your player is stock again.
</p>

<p align="center">
  <a href="../../releases"><img alt="Release" src="https://img.shields.io/github/v/release/Konixy/az-toolkit?style=flat-square&color=ff5c00"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square"></a>
  <img alt="Firmware" src="https://img.shields.io/badge/XDJ--AZ%20firmware-1.30-black?style=flat-square">
  <img alt="Platforms" src="https://img.shields.io/badge/macOS%20%7C%20Windows%20%7C%20Linux-lightgrey?style=flat-square">
</p>

<p align="center">
  <a href="#what-you-get">What you get</a> •
  <a href="#quick-start">Quick start</a> •
  <a href="#playing-with-it">Playing with it</a> •
  <a href="#back-to-stock">Back to stock</a> •
  <a href="#roadmap">Roadmap</a> •
  <a href="#faq">FAQ</a> •
  <a href="#documentation">Docs</a>
</p>

---

## What you get

This is a port of [Tratosca’s XDJ-RX3 Toolkit](https://github.com/Tratosca/rx3-toolkit) to the **XDJ-AZ**. The AZ is a different machine (RK3399 aarch64, firmware `1.30`). RX3 ARM32 offsets, hashes and the performance core are **not** shipped. Until a session log from a real AZ names a player-binary hash and verified patch words, the USB runtime **does not rewrite `rbp`**.

### 🔍 Safe inventory (on by default)

The first stick is a probe. If Pioneer’s USB maintenance path still runs `autoexec.bin` on the AZ, you get `AZ_RUNTIME/session.txt` with architecture, mounts, the player binary and its SHA-1. If that path does not exist, the stick is ignored and the unit stays stock.

### ⏭️ Instant Hot Cue (on by default, inactive until mapped)

When a track is **not already playing**, triggering a Hot Cue should start at that cue immediately instead of waiting for the beat grid. Playing decks, loops, Beat Jump and global Quantize stay stock.

On firmware `1.30` the module registers **no** binary patch. Selecting it cannot write the player until a probe log maps the site.

### 🎤 Stem files on the computer

Prepare vocal sidecars on your laptop as before. They land in `AZ_STEMS/` as `.rx3stem` files. On-device pad mixing is **not** mapped on the AZ yet, so Slip Loop stays stock until a future hook exists.

### 🎹 Key shift

Not included. The AZ already ships key shift.

### ⏭️ 32-beat Beat Jump (optional, inactive)

The RX3 modules for ±32 Beat Jump and immediate jumps are present as empty, fail-closed adapters. They cannot write `rbp` until offsets are mapped. They stay **off** by default.

### 🔌 Lives on the USB stick, not in the player

Everything runs from the stick and disappears when the power goes off. Nothing is written to the player’s internal memory. This toolkit **never flashes a `.UPD`**.

**Power off → pull the stick → power on → stock AZ.**

---

## What you need

| | |
| --- | --- |
| 🎛️ **Player** | Pioneer DJ / AlphaTheta XDJ-AZ, firmware `1.30` only |
| 💻 **Computer** | macOS (Intel or Apple Silicon), Windows x64, or Linux x64 |
| 💾 **USB stick** | A normal Rekordbox export, FAT32 or exFAT |
| 🔑 **A key file** | Not distributed here — [see below](#4-the-key-file) |
| 📀 **Disk space** | ~1.5 GB, only if you want to prepare stems |

About **20 minutes** to set everything up. After that, stems take from a few
seconds to a few minutes per track. A GPU (NVIDIA, AMD, or Apple Silicon) makes
that dramatically faster.

---

## Before you start

**Read this bit.** It is short.

- **Nothing is flashed.** The toolkit does not write to the player’s internal
  storage and will not install an official or unofficial `.UPD`. If the AZ still
  runs Pioneer’s USB `autoexec.bin` path, the script runs in RAM. If it does not,
  inserting the stick does nothing.
- **Fail-closed.** Firmware `1.30` ships with an empty SHA-1 list and empty
  patch tables. A 64-bit `rbp` with a leftover ARM32 table is refused. A
  persistent (non-RAM) root is refused. Unknown hashes refuse any write.
- **It can still crash** once binary patches exist. Modified software on a live
  machine is modified software on a live machine. **Test at home. Keep a clean
  Rekordbox stick in the bag.**
- **Do not copy RX3 patches onto the AZ.** Different SoC, different ABI,
  different `rbp`.
- **Warranty.** Running unofficial software on consumer hardware may affect what
  the manufacturer is willing to do for you. Nothing here is permanent, but that
  is not a promise about anyone’s warranty decisions.
- **Liability.** This is an educational and experimental project.
- **Music.** Separation happens on your computer, on your files.
- **Affiliation.** Not affiliated with, endorsed by, or connected to Pioneer DJ
  or AlphaTheta. Product names identify compatible gear and nothing more.

---

## Quick start

Do these in order. For your first go, use a spare USB stick.

### 1. Check your firmware

Remove every USB stick, power the AZ on, hold **MENU (UTILITY)** for a second,
scroll to the bottom.

```text
VERSION No. 1.30
```

Anything else and you should stop here — the toolkit is built against this exact
version and will not apply binary patches to another one. AlphaTheta documents
updating [in its support article](https://support.alphatheta.com/en-us/articles/37072403941145).

Power the AZ back off.

### 2. Download the app

Grab the build for your computer from the [**Releases page**](../../releases) and
unpack it wherever you keep applications.

<details>
<summary><b>macOS says the app is damaged / Windows shows a warning</b></summary>

The app is not code-signed yet, which means your computer suspects it could be malicious.

**macOS** — clear the quarantine flag your browser put on the download. Open the Terminal application, type `xattr -rc` then drag the app into the window to fill in the path:

```sh
xattr -rc "/Applications/XDJ-AZ Toolkit.app"
```

`No such file or directory` means the path is wrong: it must point at the
unpacked `.app` itself, not the `.zip` and not the folder around it.

**Windows** — SmartScreen will complain. Choose **More info → Run anyway**.

**Linux** — unpack and run; you may need to mark the file executable first.

</details>

### 3. Prepare your stems *(optional)*

Skip this until on-device mixing exists, unless you want the files ready.

1. In Rekordbox, make a playlist with the tracks you want stems for.
2. Export your Rekordbox collection **as XML**.
3. Open the app, go to the **Stems preparation** tab, and hit **Set up… → Install**.
   You need an internet connection, ~1.5 GB free, and Python 3.10–3.13.
4. Select your XML, your playlist, and a destination (the Rekordbox USB stick is fine).
5. Pick a quality and start it.

Each track produces a `.rx3stem` file in an `AZ_STEMS` folder:

```text
Your USB stick
├── Contents    ← this holds your exported Rekordbox audio files
├── PIONEER
└── AZ_STEMS    ← the new one
```

Keep the laptop plugged in and awake. See [Troubleshooting](docs/troubleshooting.md#every-track-fails).

### 4. The key file

The file we will make needs to be encrypted for the player to load it, so the app needs the matching key to
build it.

> [!CAUTION]
> **This project does not distribute that key, and never will.**

Pioneer publishes GPL/LGPL sources for the XDJ-AZ (`XDJ-AZ.tar.gz.00` … `.05`) on its
[open source distribution page](https://www.pioneerdj.com/en/support/open-source-code-distribution/gnu-open-source-license/).
The published overlay does **not** contain `aes256.key` or `decrypt_autoexec.sh`. Getting a USB-maintenance key — and deciding whether you may use it where you live — is the one step nobody can do for you.

Step-by-step: [**Pioneer sources and the USB key**](docs/extract-initramfs.md).

### 5. Build the file for your stick

In the **Modules installation** tab: pick firmware `1.30`, leave the defaults
(**Safe inventory**, **Session logging**, **Instant Hot Cue**) ticked, pick your
key file, pick the **root of your Rekordbox stick** as the destination, then
**Build for your AZ**.

Eject the stick properly. It should now look like:

```text
USB stick/
├── autoexec.bin      ← the runtime, this is the whole on-device thing
├── AZ_STEMS/         ← only if you prepared stems
├── Contents/
└── PIONEER/
```

### 6. Put it on the player

**Order matters.**

1. Power the AZ on with the stick **out**.
2. Wait until the interface is fully loaded and responsive.
3. *Now* insert the stick.

Do not pull the stick, do not cut power, and do not mash the controls while it
thinks. If logging is on, **eject** the stick later — never yank it.

<details>
<summary><b>Did it work?</b></summary>

If Pioneer’s USB path ran the image, the stick now contains `AZ_RUNTIME/session.txt`. Its last line should read:

```text
=== complete ===
```

The log should also say `no guarded words: rbp will not be rewritten`. That is
the expected first run, not a failure.

**Nothing happened, no `AZ_RUNTIME` folder?** The AZ may not consume
`autoexec.bin`. The unit stayed stock. Keep the log-less stick; do not try to
flash firmware to “make it work”.

**Interface did not come back?** Pull the stick and power cycle — unplug the
mains lead if you have to. The AZ boots stock.

**Log says `STOP:` or `FAILED:`?** Delete `autoexec.bin` from the stick, then see
[Troubleshooting](docs/troubleshooting.md#the-session-log-says-stop-or-failed).

</details>

---

## Playing with it

On the first mapped-less build, playback is stock. That is intentional.

Once Instant Hot Cue is mapped from a probe log: load a track, leave it
**stopped**, hit a Hot Cue. Audio should start at that cue without waiting for
the grid. Start the track with Play first, then hit a Hot Cue — quantize stays
stock.

Stem pads and ±32 Beat Jump stay stock until those modules have verified
offsets. A prepared `AZ_STEMS` folder does no harm in the meantime.

---

## Back to stock

1. Stop playback.
2. Power off.
3. Pull the stick.
4. Power on.

Done. Nothing to uninstall, nothing to restore, nothing to reflash.

Leaving the stick in re-applies the runtime at the next power-on *if* the AZ
loads `autoexec.bin`. To turn it back into an ordinary Rekordbox stick for good,
delete `autoexec.bin` — your music and your stems can stay.

---

## FAQ

<details>
<summary><b>How does it work?</b></summary><br>

On the RX3, Pioneer’s Linux userland looks at every USB stick for an
`autoexec.bin`, decrypts it, and runs the script inside as root. That is the
manufacturer’s maintenance mechanism. This toolkit still builds that image.

The published XDJ-AZ GPL overlay does not include that decrypt helper. Whether
the proprietary player still honours the file is what the first probe stick is
for. If it does not, you get stock behaviour and an ordinary Rekordbox stick.

When the script does run, it may patch the live copy of `rbp` (the player
application) in RAM. Power off and the RAM forgets it. Firmware `1.30` registers
no patch words, so the first image only inventories the unit.

Details: [The AZ mod](docs/mod-rx3.md).
</details>

<details>
<summary><b>Does this flash custom firmware?</b></summary><br>

No. Official AZ `.UPD` files are LUKS-encrypted and this toolkit will not
decrypt or flash them. The USB runtime, when it runs at all, lives in memory.
</details>

<details>
<summary><b>Can it brick my AZ?</b></summary><br>

The project does not write to the player’s permanent storage, which removes the
usual reason custom firmware bricks things. That is not a mathematical proof that
nothing can ever go wrong. Unofficial software, own risk. Do not flash anything
to “force” the mod on.
</details>

<details>
<summary><b>Can it crash?</b></summary><br>

A probe-only image should not restart `rbp`. Once binary patches exist, yes —
test at home first.
</details>

<details>
<summary><b>Why is key shift missing?</b></summary><br>

The AZ already has it. The RX3 module and its ARM32 hook are not portable and
were removed rather than applied blindly.
</details>

<details>
<summary><b>Why only firmware 1.30?</b></summary><br>

Binary patches are tied to exact bytes. A firmware update moves that code.
`1.30` is the version this port targets, and it still refuses to write until a
hash from *your* unit is registered with verified words.
</details>

<details>
<summary><b>Can I update my firmware while this is installed?</b></summary><br>

There is nothing installed. Pull the stick and the unit is stock. After a
firmware change, do not assume the toolkit still works. **Update with a clean
boot, without the mod USB.**
</details>

---

## Roadmap

What is being worked on next. No dates, no promises.

| | What it would give you | Status |
| --- | --- | :--: |
| **Probe log from hardware** | A real `rbp` SHA-1 and ELF class from an AZ 1.30 | 🚧 Waiting on a first stick |
| **Instant Hot Cue** | Skip grid wait when the deck is stopped | 🚧 Module shipped, offsets not mapped |
| **±32 Beat Jump** | Pads 7/8 as ±32 | 💡 Planned after a mapped hash |
| **On-device stem pads** | Slip Loop vocal / instrumental on the AZ | 💡 Planned; sidecars already generate |
| **CPU and memory monitoring** | Headroom so heavier features stay safe | 💡 Planned |

Want one of these sooner? Or something else? Say so in an issue, or build it yourself (see
[Contributing](#contributing)).

---

## Documentation

| | |
| --- | --- |
| [Pioneer sources and the USB key](docs/extract-initramfs.md) | Published GPL overlay, LUKS updates, why the key is not in the tarball |
| [The AZ mod](docs/mod-rx3.md) | Architecture, modules, applying and removing, session logs |
| [Vocal stems](docs/stem-studio.md) | Models, presets, accelerators, tuning |
| [Troubleshooting](docs/troubleshooting.md) | Symptoms, errors, fixes |
| [Reference](docs/reference.md) | File formats, commands, hardware findings |
| [Contributing](CONTRIBUTING.md) | Build from source, run the tests, write a module |
| [Changelog](CHANGELOG.md) | What changed |

---

## Contributing

Pull requests welcome — probe logs from firmware `1.30` (redact keys), mapped
offsets with stock/patched words, UI work, faster separation, or better docs.
Start with [CONTRIBUTING.md](CONTRIBUTING.md).

**Reporting a bug?** Include your firmware version, your OS, the toolkit version,
the contents of `AZ_RUNTIME/session.txt`, and the steps to reproduce. For stem
problems, add the model, the quality preset, your CPU/GPU, and whether it affects
one track or all of them.

Please do **not** attach encryption keys, manufacturer firmware or binaries, or
copyrighted music.

---

## License

[Mozilla Public License 2.0](LICENSE). Changes to MPL-covered files stay under
the MPL; separate files may be combined into a larger work under other terms, as
the licence permits. Third-party components are listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Keys, firmware, manufacturer binaries and copyrighted music are not in this
repository and are never release assets.

Pioneer DJ, AlphaTheta, Rekordbox and XDJ-AZ are trademarks of their respective
owners, used here descriptively only.

---

## Acknowledgements

The open-source software running inside the player, the GPL/LGPL sources Pioneer
published, [Tratosca’s RX3 toolkit](https://github.com/Tratosca/rx3-toolkit) this
fork starts from, the reverse-engineering community, the people who build the
audio-separation models — and everyone who has ever looked at a perfectly
functional DJ player and asked:

> *"Yes, but what else can it do?"*
