#!/bin/sh
# SPDX-License-Identifier: MPL-2.0
# Publish the sidecar directory. No performance core exists for AZ 1.30 yet,
# so this cannot mix stems into rbp; it only records what the stick carries.

module_begin stems stems

STEMS_DIR="$USB/AZ_STEMS"
STEMS_LINK=/tmp/az-stems
STEMS_READY=0

stems_prepare()
{
    count=0
    for candidate in "$STEMS_DIR"/*.rx3stem; do
        [ -f "$candidate" ] || continue
        count=$((count+1))
    done

    published=$STEMS_DIR
    if [ ! -e "$STEMS_LINK" ] || [ -L "$STEMS_LINK" ]; then
        rm -f "$STEMS_LINK"
        ln -s "$STEMS_DIR" "$STEMS_LINK" 2>/dev/null && published=$STEMS_LINK
    fi
    [ "$published" = "$STEMS_LINK" ] || \
        say "Stems: $STEMS_LINK cannot be published, falling back to the mount path"

    export AZ_STEMS_DIR="$published"
    STEMS_READY=1
    say "Stems prepared: $count sidecar(s) at $STEMS_DIR"
    say "On-device stem mixing is not mapped for AZ 1.30; rbp was not modified"
}

stems_after_launch()
{
    [ "$STEMS_READY" = "1" ] || return 0
    say "AZ_STEMS is published at ${AZ_STEMS_DIR:-unset}"
    say "pad takeover and PCM mixing wait on a mapped performance core"
}

register_prepare_hook stems_prepare
register_after_launch_hook stems_after_launch
