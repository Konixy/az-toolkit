# Beat Jump ±32, XDJ-AZ firmware 1.30

Fail-closed. The RX3 patch rewrites twelve ARM32 words at firmware 1.19
offsets. The AZ player is aarch64 and those offsets are not valid. This
module registers no guarded words until a probe log supplies a matching
`rbp` SHA-1 and verified stock/patched values.

`tools/rx3_patcher/beatjump_32bars.py` stays empty for the same reason.
`tests/test_module_consistency.py` requires the two tables to agree.
