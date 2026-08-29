#!/bin/sh

set -eu

agents_dir="$HOME/Library/LaunchAgents"
plist="$agents_dir/local.doomsday-drill.plist"
domain="gui/$(id -u)"

launchctl bootout "$domain/local.doomsday-drill" 2>/dev/null || true
launchctl bootout "$domain" "$plist" 2>/dev/null || true
rm -f "$plist"

echo "Automatic login and unlock drills are disabled. Saved stats were kept."
