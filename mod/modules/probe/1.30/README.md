# Safe inventory

Read-only. It records architecture, mounts, the player binary and its SHA-1,
and whether Pioneer’s USB maintenance tools are present. It does not write
`rbp`, does not preload a library, and does not restart the player.

Keep it selected until a session log from the actual XDJ-AZ exists. Binary
patches for firmware 1.30 are refused until that SHA-1 is registered with
verified offsets.
