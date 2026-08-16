#!/bin/sh
# SPDX-License-Identifier: MPL-2.0
# Supported rbp identities for XDJ-AZ firmware 1.30.
#
# Empty on purpose. Pioneer did not publish the AZ player binary, and the RX3
# SHA-1 values must never be reused here: a match would let RX3 offsets land
# in the wrong image. Binary patches stay disabled until a session log from
# this unit names a hash and that hash is registered together with verified
# stock/patched words.

module_begin compatibility compatibility
