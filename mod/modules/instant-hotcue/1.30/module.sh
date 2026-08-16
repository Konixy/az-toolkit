#!/bin/sh
# SPDX-License-Identifier: MPL-2.0
# Instant Hot Cue on a stopped deck. Firmware 1.30 has no mapped rbp offsets
# yet, so this module registers no guarded words. Copying the RX3 Beat Jump
# NOP here would write an ARM32 instruction into an aarch64 image.

module_begin instant-hotcue instant_hotcue

instant_hotcue_report()
{
    say "Instant Hot Cue: no verified rbp offsets for AZ 1.30; nothing written."
    say "Intended behaviour once mapped: a Hot Cue on a stopped deck skips"
    say "grid quantize and starts at the cue. A playing deck is left stock."
}

register_report_hook instant_hotcue_report
