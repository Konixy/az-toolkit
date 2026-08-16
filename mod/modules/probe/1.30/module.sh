#!/bin/sh
# SPDX-License-Identifier: MPL-2.0
# Read-only inventory. No guarded words, no preload, no process restart.

module_begin probe probe

probe_say_file()
{
    label=$1
    path=$2
    if [ -r "$path" ]; then
        say "$label: $path"
        sed 's/^/  /' "$path" >> "$LOG" 2>/dev/null
    else
        say "$label: missing ($path)"
    fi
}

probe_say_cmd()
{
    label=$1
    shift
    say "--- $label ---"
    "$@" >> "$LOG" 2>&1 || say "  (command failed)"
}

probe_report()
{
    say ""
    say "=== AZ inventory (read-only) ==="
    say "date: $(date -u 2>/dev/null || date 2>/dev/null)"
    say "uid: $(id -u)  gid: $(id -g)"
    probe_say_cmd "uname" uname -a
    probe_say_file "firmware rev smdj2" /tmp/smdj2.rev
    probe_say_file "firmware rev smdj" /tmp/smdj.rev
    probe_say_file "os-release" /etc/os-release
    probe_say_file "cpuinfo (head)" /proc/cpuinfo
    if [ "$LOGGING" = "1" ] && [ -r /proc/cpuinfo ]; then
        # Keep the log finite; the rest of cpuinfo is per-core repetition.
        sed -n '1,40p' /proc/cpuinfo >> "$LOG" 2>/dev/null
    fi

    say "--- candidate player binaries ---"
    for candidate in \
        /root/pdj/rbp \
        /home/root/pdj/rbp \
        /opt/pdj/rbp \
        /usr/local/pdj/rbp \
        /usr/bin/rbp \
        /usr/bin/xplayer \
        /home/root/rbp
    do
        if [ -e "$candidate" ]; then
            say "found $candidate"
            ls -l "$candidate" >> "$LOG" 2>/dev/null
            sha1sum "$candidate" >> "$LOG" 2>/dev/null
            # ELF class: 01=32-bit, 02=64-bit. ARM32 trampolines must never
            # be applied to a 64-bit rbp, and the reverse is equally unsafe.
            hexdump -C -n 20 "$candidate" >> "$LOG" 2>/dev/null || \
                od -An -tx1 -N 20 "$candidate" >> "$LOG" 2>/dev/null
        fi
    done

    say "--- processes of interest ---"
    for process in /proc/[0-9]*; do
        comm=$(cat "$process/comm" 2>/dev/null) || continue
        case "$comm" in
            rbp|xplayer|pdj*|rekord*|XDJ*|xdj*|player*)
                say "pid ${process#/proc/} comm=$comm exe=$(readlink "$process/exe" 2>/dev/null)"
                ;;
        esac
    done

    say "--- Pioneer maintenance clues ---"
    for path in \
        /root/pdj/decrypt_autoexec.sh \
        /usr/local/pdj/decrypt_autoexec.sh \
        /usr/local/pdj/aes256.key \
        /root/pdj/aes256.key \
        /usr/sbin/dropbear \
        /bin/busybox
    do
        [ -e "$path" ] && say "present $path" || say "absent  $path"
    done

    say "--- usb / media ---"
    say "USB argument: ${USB:-unset}"
    ls -la /media  >> "$LOG" 2>/dev/null || true
    ls -la /mnt    >> "$LOG" 2>/dev/null || true
    ls -la /proc/udev_usb* >> "$LOG" 2>/dev/null || true

    say "--- listening sockets (head) ---"
    sed -n '1,30p' /proc/net/tcp >> "$LOG" 2>/dev/null || true
    sed -n '1,20p' /proc/net/udp >> "$LOG" 2>/dev/null || true

    say "inventory complete: rbp was not modified"
}

register_report_hook probe_report
