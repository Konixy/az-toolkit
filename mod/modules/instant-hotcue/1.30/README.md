# Instant Hot Cue (stopped deck)

On a stock Pioneer player, firing a Hot Cue while the deck is stopped often
waits for the beat grid (or the Quantize window) before audio starts. This
module is meant to skip that wait **only when the track is not already
playing**. Live playback, loops, Beat Jump and global Quantize stay stock.

## Why it does nothing on firmware 1.30 yet

The RX3 equivalent (Beat Jump without grid reservation) is one ARM32 word: a
conditional branch to `startPlayQuantizeForJump()` is replaced with `nop`.
The XDJ-AZ player binary is a different architecture (RK3399 aarch64) and
that word is not at the RX3 offset. Registering the RX3 bytes would be a
random write.

This module therefore registers **no** `register_patch` calls until a probe
session from a real AZ names:

1. the `rbp` SHA-1
2. the Hot Cue quantize branch (stock word, patched word, 8-byte prologue)

Those three facts have to be added together. A hash without offsets, or
offsets without a hash, is refused by the orchestrator.

## Intended patch (once mapped)

Same shape as `beatjump-no-quantize` on the RX3: one guarded 32-bit (or
64-bit) instruction that selects the direct start path when the deck is
stopped. Playing decks must keep the stock branch.

Offline counterpart: `tools/rx3_patcher/instant_hotcue.py`. Its table and
`module.sh` are compared by `tests/test_module_consistency.py`.
