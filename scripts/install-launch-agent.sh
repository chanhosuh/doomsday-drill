#!/bin/sh

set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python_path="$project_dir/.venv/bin/python"
template="$project_dir/launchd/local.doomsday-drill.plist"
agents_dir="$HOME/Library/LaunchAgents"
plist="$agents_dir/local.doomsday-drill.plist"
domain="gui/$(id -u)"

if [ ! -x "$python_path" ]; then
  echo "Missing $python_path; complete the virtual-environment setup first." >&2
  exit 1
fi

mkdir -p "$agents_dir"
temporary_plist=$(mktemp "$agents_dir/.local.doomsday-drill.XXXXXX")
trap 'rm -f "$temporary_plist"' EXIT HUP INT TERM

cp "$template" "$temporary_plist"
plutil -replace Program -string "$python_path" "$temporary_plist"
plutil -replace WorkingDirectory -string "$project_dir" "$temporary_plist"
plutil -lint "$temporary_plist" >/dev/null

# Reload the service when updating an existing installation.
launchctl bootout "$domain/local.doomsday-drill" 2>/dev/null || true
launchctl bootout "$domain" "$plist" 2>/dev/null || true

mv "$temporary_plist" "$plist"
trap - EXIT HUP INT TERM

launchctl bootstrap "$domain" "$plist"
echo "Installed and started $plist"
