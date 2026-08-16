# Decoder polling interval, XDJ-AZ firmware 1.30

Not a binary patch. After the player is up, the module sends `bufsleep`
to UDP port 20000 for decks 0–3, the same debug console the RX3 used.

Off by default: we have not seen that console on an AZ yet. If the port is
closed, `apply.sh` logs the miss and leaves the player alone.
