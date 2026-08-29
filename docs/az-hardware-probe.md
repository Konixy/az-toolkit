# XDJ-AZ 1.30 hardware probe

What a real XDJ-AZ on firmware `1.30` actually exposes, measured on hardware on
2026-08-29. This is the result the fail-closed runtime was built for: the USB
stick test, the GPL overlay scan, and a network probe over the rear USB-B
computer port.

**Outcome: no software-only code-execution path was found.** The toolkit stays
probe-ready in case a legitimate path appears in a future firmware.

## USB storage execution: absent

A FAT32 stick carrying a correctly encrypted `autoexec.bin` (RX3 cryptoloop
key, extracted from Pioneer's published XDJ-RX3 GPL tree) was inserted into a
powered-on AZ 1.30:

- No `AZ_RUNTIME/` folder was created. The player never ran the script.
- The AZ treated the stick as ordinary media: it wrote its own
  `PIONEER/log/<uuid>-alog_0.bin` / `alog_1.bin` (small opaque media logs) and
  nothing else.
- Black-box names tried at the stick root, one stick at a time, all ignored:
  `autoexec.sh` (plain script), `update.sh`, `pioneer_update.sh`,
  `djm_update.sh`, and a dummy `XDJAZv999.UPD` (not a real update image).

The published XDJ-AZ 1.04 GPL overlay explains why. The only USB hook in
`fs-overlay-atc` is a udev rule that starts a mount service:

```text
98-local.rules
  ACTION=="add", DEVTYPE=="partition" → systemctl start device-mount@%k.service
  ACTION=="add", DEVTYPE=="disk"      → systemctl start device-mount@%k.service
```

`device-mount.sh` mounts the partition at `/media/usb/sdX` and writes a status
line to `/proc/udev_usbN`. There is no `autoexec`, `decrypt_autoexec`,
`aes256.key`, or `pdj` path anywhere in the GPL tree. If an execution hook
exists, it lives inside the proprietary `rbp` binary, which is not published.

## Network surface (rear USB-B computer port)

Connecting the AZ's rear USB-B port to a computer brings up an Ethernet gadget
interface with APIPA addressing:

| Property | Observed value |
|---|---|
| Hostname | `rk3399.local` (matches `BR2_TARGET_GENERIC_HOSTNAME` in the GPL defconfig) |
| IPv4 | `169.254.7.67` (link-local) |
| mDNS | Avahi live; advertises `_ssh._tcp` and `_sftp-ssh._tcp` on port 22 |
| TCP 22, 23, 53, 80, 443, 8080 | Connection refused |
| TCP sweep 1–1024 | Nothing open |
| TCP high ports | Only **12523** open — PRO DJ LINK DBServer, the documented track-metadata protocol |

The SSH advertisement is a Buildroot artifact: Avahi ships static service files
that announce SSH whether or not the daemon runs. Dropbear is compiled into the
firmware (`BR2_PACKAGE_DROPBEAR=y`, an ECDSA host key ships in the overlay, the
defconfig sets a blank root password and `DROPBEAR_ARGS=-B`) but the daemon is
**not running** in the shipped 1.30 build.

Port 12523 is the documented PRO DJ LINK metadata channel (UDP 50000–50004 plus
TCP 12523). It answers track-metadata queries; it is not a shell and this
project does not fuzz it.

## Firmware update path

Official `XDJAZv130.UPD` images are LUKS1 AES-XTS-plain64 with a model trailer
`XDJ-XZN`. This toolkit can describe that header
(`tools/rx3_firmware/firmware_image.py verify`) and will not decrypt the volume
or flash an update. Do not put a hand-built `.UPD` on the player.

## What remains

Only hardware paths are left, and they are out of scope for this project:

- the RK3399 debug UART on the main board (typically 1,500,000 baud 8N1, 3.3 V),
  which may offer a console given the blank root password in the defconfig;
- MaskRom USB boot, forced by shorting the eMMC clock line — a recovery mode
  that can also rewrite flash.

Both require opening the unit. Neither is needed to keep using the toolkit's
computer-side stem preparation.

## If a future firmware changes this

Re-run the probe stick first (defaults: probe + logging + Instant Hot Cue). A
run that works creates `AZ_RUNTIME/session.txt` ending with `=== complete ===`
and `no guarded words: rbp will not be rewritten`. Only that log justifies
registering a SHA-1 and guarded words, and both must land in the same change.
