# Immediate Beat Jump, XDJ-AZ firmware 1.30

Fail-closed. The RX3 patch is one ARM32 NOP at `0x0A9DD4`. That address is
not valid on the AZ player. No guarded word is registered until a probe
session maps it.

`tools/rx3_patcher/beatjump_no_quantize.py` is empty for the same firmware.
