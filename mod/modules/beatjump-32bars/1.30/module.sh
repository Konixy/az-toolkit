#!/bin/sh
# SPDX-License-Identifier: MPL-2.0
# Beat Jump +/-32. No AZ 1.30 offsets are mapped; registering RX3 words
# would rewrite the wrong instructions in an aarch64 rbp.

module_begin beatjump-32bars beatjump_32bars

beatjump_32bars_report()
{
    say "Beat Jump +/-32: no verified rbp offsets for AZ 1.30; nothing written."
}

register_report_hook beatjump_32bars_report
