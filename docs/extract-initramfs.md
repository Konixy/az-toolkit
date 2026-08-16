# Pioneer sources and the USB key

The desktop app encrypts `autoexec.bin` with Pioneer’s historical USB
cryptoloop layout (AES-256-CBC per 512-byte sector). It needs the matching
key file to do that.

> **This project does not distribute that key, and never will.**

## What Pioneer publishes

GPL/LGPL sources for the XDJ-AZ are on Pioneer’s
[open source distribution page](https://www.pioneerdj.com/en/support/open-source-code-distribution/gnu-open-source-license/),
currently **XDJ-AZ version 1.04** (31 October 2024):

```text
XDJ-AZ.tar.gz.00
XDJ-AZ.tar.gz.01
XDJ-AZ.tar.gz.02
XDJ-AZ.tar.gz.03
XDJ-AZ.tar.gz.04
XDJ-AZ.tar.gz.05
```

Each listed file is a ZIP around one split part. Reassemble the tarball, then
extract it. That tree is Buildroot / Linux for **RK3399** (`RK_ARCH=arm64`),
with an overlay named along the lines of `fs-overlay-atc`.

The published overlay does **not** contain:

- `decrypt_autoexec.sh`
- `aes256.key`
- an `autoexec` helper under `/root/pdj` or `/usr/local/pdj`

USB media is mounted through ordinary udev / `device-mount.sh` paths such as
`/media/usb/...`. Whether the proprietary player still decrypts `autoexec.bin`
is not answered by the GPL tree. A first toolkit stick with **probe** and
**logging** is how you find out. If the file is ignored, the unit stays stock.

## Official firmware updates

AlphaTheta’s `.UPD` for the AZ (trailer model `XDJ-XZN`, version `1.30` on the
image this port targets) is **LUKS1 AES-XTS-plain64**, not the RX3 cryptoloop
container.

This toolkit:

- can *describe* a LUKS header (`python3 tools/rx3_firmware/firmware_image.py verify FILE.UPD`);
- will **not** brute-force a passphrase;
- will **not** flash a `.UPD`;
- will **not** write eMMC.

`encrypt` in that same tool still produces an RX3-style cryptoloop update
image. That is the wrong shape for an AZ update. Do not put it on the player.

## What the key file is

If the AZ USB path exists, it is the same 32-byte effective key the RX3 used
for cryptoloop: first line of the file, at most 31 bytes, then a NUL, matching
historical `xstrncpy(dst, src, 32)`.

A key from another Pioneer product may or may not match. A mismatch decrypts to
garbage and the player **silently ignores** the file. That is safe. Do not dump
the live player, do not copy keys into issues, and do not commit a `.key`.

## Extracting the published tarball

On macOS or Linux, after downloading the six ZIPs:

```sh
mkdir az-source && cd az-source
# extract each ZIP with 7-Zip (they may use Deflate64)
7zz x ../xdj-aztargz00.zip
# …repeat for 01–05…

cat XDJ-AZ.tar.gz.00 XDJ-AZ.tar.gz.01 XDJ-AZ.tar.gz.02 \
    XDJ-AZ.tar.gz.03 XDJ-AZ.tar.gz.04 XDJ-AZ.tar.gz.05 > XDJ-AZ.tar.gz
tar -tf XDJ-AZ.tar.gz | head
```

Inspect the overlay for `aes256.key` and `decrypt_autoexec.sh` if you want to
confirm they are absent. Building the GPL rootfs is optional and does not, by
itself, produce a USB key on this product.

Getting the key — and deciding whether you may use it where you live — remains
the step this repository will not do for you.
