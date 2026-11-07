#!/usr/bin/env bash
# SDRbox / rackio touch mapping.
# Tested interactively on Linux Mint (2026-11-07).
# IMPORTANT: ID_PATH identifies physical USB PORTS, not the screens themselves.
# Update if touch USB cables are moved.
export DISPLAY="${DISPLAY:-:0}"

xinput list --short |
grep 'wch.cn TouchScreen' |
grep -o 'id=[0-9]*' |
cut -d= -f2 |
while read -r id; do
    node=$(xinput list-props "$id" |
        sed -n 's/.*Device Node.*"\(.*\)"/\1/p')

    [ -z "$node" ] && continue

    path=$(udevadm info -q property -n "$node" |
        sed -n 's/^ID_PATH=//p')

    case "$path" in
        *usb-0:7:1.0|*usb-0:7:1.2)
            # Upper 1U display: disable both touch and mouse-emulation interfaces.
            xinput disable "$id"
            ;;
        *usb-0:6:1.0)
            # Lower 2U touchscreen: enable and map to physical display.
            xinput enable "$id"
            xinput map-to-output "$id" HDMI-2
            ;;
    esac
done
