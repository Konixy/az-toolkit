#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Inspect, decrypt, encrypt, and build Pioneer/AlphaTheta firmware images.

Two on-disk shapes exist:

RX3-style cryptoloop (historical USB autoexec.bin, and RX3 .UPD files):

    cat /usr/local/pdj/aes256.key | losetup -e aes -p 0 DEVICE IMAGE

    [encrypted payload, aligned to 512 bytes]
    [model and version field, 12 bytes]
    [CRC32 of encrypted payload, little-endian, 4 bytes]

    AES-256-CBC per 512-byte sector. IV is the sector index as a 32-bit
    little-endian integer followed by 12 zero bytes.

XDJ-AZ .UPD files (firmware 1.04+): LUKS1 AES-XTS-plain64, SHA-256, then the
same 16-byte model/version/CRC32 trailer. The observed model id is `XDJ-XZN`.
This module can describe that header. It does not brute-force the LUKS
passphrase, and the toolkit never flashes a .UPD.
"""

import argparse
import io
import pathlib
import struct
import subprocess
import sys
import tempfile
import zlib

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SECTOR = 512
TRAILER = 16
MODEL = b"XDJ-XZN"
LUKS_MAGIC = b"LUKS\xba\xbe"
ISO_BLOCK = 2048
ISO_PADDING_BLOCKS = 150


def load_key(path):
    """Reproduce xgetpass followed by xstrncpy(dst, src, 32).

    Only the first line is used. xstrncpy copies at most 31 bytes and writes a
    terminating NUL byte, yielding the effective 32-byte AES key.
    """
    lines = pathlib.Path(path).read_bytes().splitlines()
    if not lines:
        raise ValueError("key file is empty")
    return lines[0][:31].ljust(32, b"\0")


def crypt(body, key, decrypt):
    """Apply AES-256-CBC independently to each 512-byte sector."""
    if len(body) % SECTOR:
        raise ValueError(f"payload is not aligned to {SECTOR} bytes")
    algorithm = algorithms.AES(key)
    output = bytearray(len(body))
    for sector, offset in enumerate(range(0, len(body), SECTOR)):
        iv = struct.pack("<I", sector & 0xFFFFFFFF) + bytes(12)
        cipher = Cipher(algorithm, modes.CBC(iv))
        operation = cipher.decryptor() if decrypt else cipher.encryptor()
        block = body[offset:offset + SECTOR]
        output[offset:offset + SECTOR] = operation.update(block) + operation.finalize()
    return bytes(output)


def split(blob):
    """Return payload, model, version, stored CRC32, and calculated CRC32."""
    if len(blob) < TRAILER:
        raise ValueError("update image is shorter than its trailer")
    body, trailer = blob[:-TRAILER], blob[-TRAILER:]
    model = trailer[:7]
    version = trailer[7:12].rstrip(b"\0").decode("ascii", "replace")
    stored = struct.unpack("<I", trailer[12:])[0]
    actual = zlib.crc32(body) & 0xFFFFFFFF
    return body, model, version, stored, actual


def build(payload, version, model=MODEL):
    """Append the model/version field and encrypted-payload CRC32."""
    if not isinstance(model, bytes):
        model = model.encode("ascii")
    if len(model) != 7:
        raise ValueError(f"model must be 7 bytes, got {model!r}")
    encoded_version = version.encode("ascii")
    trailer = model + encoded_version.ljust(5, b"\0")
    if len(trailer) != 12:
        raise ValueError(f"version is too long: {version!r}")
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    return payload + trailer + struct.pack("<I", crc)


def luks_info(blob):
    """Return a LUKS1 summary from an update image, or None if it is not LUKS."""
    if len(blob) < TRAILER + 208:
        return None
    body = blob[:-TRAILER]
    if body[:6] != LUKS_MAGIC:
        return None
    version = struct.unpack(">H", body[6:8])[0]
    cipher = body[8:40].split(b"\0", 1)[0].decode("ascii", "replace")
    mode = body[40:72].split(b"\0", 1)[0].decode("ascii", "replace")
    hash_spec = body[72:104].split(b"\0", 1)[0].decode("ascii", "replace")
    payload_offset = struct.unpack(">I", body[104:108])[0]
    uuid = body[168:208].split(b"\0", 1)[0].decode("ascii", "replace")
    active_slots = 0
    for index in range(8):
        slot_active = struct.unpack(">I", body[208 + index * 48:212 + index * 48])[0]
        if slot_active == 0x00AC71F3:
            active_slots += 1
    return {
        "version": version,
        "cipher": cipher,
        "mode": mode,
        "hash": hash_spec,
        "payload_offset": payload_offset,
        "uuid": uuid,
        "active_slots": active_slots,
    }


def cmd_verify(args):
    blob = pathlib.Path(args.file).read_bytes()
    body, model, version, stored, actual = split(blob)
    print(f"Model          : {model.decode('ascii', 'replace')}")
    print(f"Version        : {version}")
    print(f"Payload        : {len(body):,} bytes ({len(body) // SECTOR} sectors)")
    print(f"Stored CRC32   : 0x{stored:08X}")
    print(f"Calculated CRC : 0x{actual:08X} -> {'OK' if stored == actual else 'FAILED'}")
    info = luks_info(blob)
    if info:
        print(
            f"LUKS           : version {info['version']} "
            f"{info['cipher']}-{info['mode']} {info['hash']}, "
            f"{info['active_slots']} keyslot(s), uuid {info['uuid']}"
        )
        print("Note           : AZ update images are LUKS; this tool will not flash them.")
        return 0 if stored == actual else 1
    if not args.key:
        return 0 if stored == actual else 1

    iv = struct.pack("<I", 64) + bytes(12)
    decryptor = Cipher(algorithms.AES(load_key(args.key)), modes.CBC(iv)).decryptor()
    pvd = decryptor.update(body[64 * SECTOR:65 * SECTOR]) + decryptor.finalize()
    valid = pvd[1:6] == b"CD001"
    suffix = ""
    if valid:
        volume = pvd[40:72].decode("ascii", "replace").rstrip(" \0")
        suffix = f"; volume {volume!r}"
    print(f"ISO 9660 at crypto sector 64: {'YES' if valid else 'NO'}{suffix}")
    return 0 if valid else 1


def cmd_decrypt(args):
    body, model, version, stored, actual = split(pathlib.Path(args.input).read_bytes())
    if stored != actual:
        raise ValueError(f"CRC mismatch: stored 0x{stored:08X}, calculated 0x{actual:08X}")
    plain = crypt(body, load_key(args.key), True)
    pathlib.Path(args.output).write_bytes(plain)
    print(
        f"{args.output}: {len(plain):,} bytes "
        f"(model {model.decode('ascii', 'replace')}, version {version})"
    )
    if plain[64 * SECTOR + 1:64 * SECTOR + 6] != b"CD001":
        print("WARNING: ISO signature is missing; the supplied key is likely incorrect")


def read_autoexec(path, key_path):
    """Decrypt a raw autoexec image without an update trailer."""
    body = pathlib.Path(path).read_bytes()
    if not body or len(body) % SECTOR:
        raise ValueError(f"autoexec image is not aligned to {SECTOR} bytes")
    return crypt(body, load_key(key_path), True)


def autoexec_iso_metadata(plain):
    """Return the ISO volume name from crypto sector 64."""
    pvd_offset = 64 * SECTOR
    pvd = plain[pvd_offset:pvd_offset + 2048]
    if len(pvd) != 2048 or pvd[1:6] != b"CD001":
        raise ValueError("ISO 9660 signature is missing; key or image is incorrect")
    return pvd[40:72].decode("ascii", "replace").rstrip(" \0")


def cmd_verify_autoexec(args):
    plain = read_autoexec(args.file, args.key)
    volume = autoexec_iso_metadata(plain)
    print(f"Autoexec       : {len(plain):,} bytes ({len(plain) // SECTOR} sectors)")
    print(f"ISO 9660       : OK, volume {volume!r}")


def cmd_decrypt_autoexec(args):
    plain = read_autoexec(args.input, args.key)
    volume = autoexec_iso_metadata(plain)
    pathlib.Path(args.output).write_bytes(plain)
    print(f"{args.output}: {len(plain):,} bytes, ISO 9660 volume {volume!r}")


def build_autoexec_iso(source):
    """Build a portable Rock Ridge ISO from a runtime staging directory.

    pycdlib is used by the desktop builder on every supported host OS. The
    mkisofs fallback keeps the developer CLI compatible with older setups.
    """
    source = pathlib.Path(source)
    if not (source / "autoexec.sh").is_file():
        raise ValueError(f"{source}/autoexec.sh is missing")

    try:
        import pycdlib
    except ImportError:
        with tempfile.TemporaryDirectory(prefix="rx3-autoexec-") as directory:
            iso_path = pathlib.Path(directory) / "autoexec.iso"
            subprocess.run(
                ["mkisofs", "-quiet", "-R", "-V", "UsbAuto", "-o", str(iso_path), str(source)],
                check=True,
            )
            return iso_path.read_bytes()

    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, vol_ident="UsbAuto", rock_ridge="1.09")
    iso_directories = {pathlib.Path(): ""}
    directory_number = 0
    file_number = 0

    for path in sorted((item for item in source.rglob("*") if item.is_dir())):
        relative = path.relative_to(source)
        parent_iso = iso_directories[relative.parent]
        directory_number += 1
        iso_path = f"{parent_iso}/D{directory_number:07d}"
        iso.add_directory(
            iso_path=iso_path,
            rr_name=relative.name,
            file_mode=0o40555,
        )
        iso_directories[relative] = iso_path

    for path in sorted((item for item in source.rglob("*") if item.is_file())):
        relative = path.relative_to(source)
        parent_iso = iso_directories[relative.parent]
        file_number += 1
        iso_path = f"{parent_iso}/F{file_number:07d};1"
        mode = 0o100755 if path.suffix == ".sh" else 0o100644
        iso.add_file(
            str(path),
            iso_path=iso_path,
            rr_name=relative.name,
            file_mode=mode,
        )

    output = io.BytesIO()
    iso.write_fp(output)
    iso.close()
    image = bytearray(output.getvalue())
    image.extend(bytes(ISO_PADDING_BLOCKS * ISO_BLOCK))

    # Match the padded images produced by mkisofs. Some ISO readers inspect
    # sectors beyond the logical filesystem before accepting a loop image.
    volume_blocks = len(image) // ISO_BLOCK
    pvd = 16 * ISO_BLOCK
    struct.pack_into("<I", image, pvd + 80, volume_blocks)
    struct.pack_into(">I", image, pvd + 84, volume_blocks)
    return bytes(image)


def write_autoexec(source, output, key_path):
    """Build, encrypt, and write a raw autoexec image."""
    source = pathlib.Path(source)
    plain = build_autoexec_iso(source)

    if len(plain) % SECTOR:
        plain += b"\0" * (SECTOR - len(plain) % SECTOR)

    pathlib.Path(output).write_bytes(crypt(plain, load_key(key_path), False))
    return len(plain)


def cmd_autoexec(args):
    """Build an encrypted Rock Ridge ISO without an update trailer."""
    size = write_autoexec(args.dir, args.output, args.key)
    print(f"{args.output}: {size:,} bytes ({size // SECTOR} sectors)")


def cmd_encrypt(args):
    plain = pathlib.Path(args.input).read_bytes()
    if len(plain) % SECTOR:
        padding = SECTOR - (len(plain) % SECTOR)
        plain += b"\0" * padding
        print(f"Added {padding} bytes to align the payload", file=sys.stderr)
    update = build(crypt(plain, load_key(args.key), False), args.version)
    pathlib.Path(args.output).write_bytes(update)
    crc = struct.unpack("<I", update[-4:])[0]
    print(f"{args.output}: {len(update):,} bytes; trailer {update[-16:-4]!r}; CRC32 0x{crc:08X}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    command = commands.add_parser("decrypt")
    command.add_argument("input")
    command.add_argument("output")
    command.add_argument("--key", required=True)
    command.set_defaults(function=cmd_decrypt)

    command = commands.add_parser("encrypt")
    command.add_argument("input")
    command.add_argument("output")
    command.add_argument("--key", required=True)
    command.add_argument("--version", required=True)
    command.set_defaults(function=cmd_encrypt)

    command = commands.add_parser("verify")
    command.add_argument("file")
    command.add_argument("--key")
    command.set_defaults(function=cmd_verify)

    command = commands.add_parser("verify-autoexec", help="verify a raw autoexec image")
    command.add_argument("file")
    command.add_argument("--key", required=True)
    command.set_defaults(function=cmd_verify_autoexec)

    command = commands.add_parser("decrypt-autoexec", help="decrypt a raw autoexec image")
    command.add_argument("input")
    command.add_argument("output")
    command.add_argument("--key", required=True)
    command.set_defaults(function=cmd_decrypt_autoexec)

    command = commands.add_parser("autoexec", help="build autoexec.bin from a directory")
    command.add_argument("dir")
    command.add_argument("output")
    command.add_argument("--key", required=True)
    command.set_defaults(function=cmd_autoexec)

    args = parser.parse_args()
    try:
        return args.function(args) or 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
