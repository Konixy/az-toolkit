#!/bin/sh
# SPDX-License-Identifier: MPL-2.0
# Direct Beat Jump path. No AZ 1.30 offsets are mapped.

module_begin beatjump-no-quantize beatjump_no_quantize

beatjump_no_quantize_report()
{
    say "Immediate Beat Jump: no verified rbp offsets for AZ 1.30; nothing written."
}

register_report_hook beatjump_no_quantize_report
