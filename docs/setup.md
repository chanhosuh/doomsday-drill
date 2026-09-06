# Setup and Troubleshooting

For installation and a first drill, start with the [README](../README.md#running-locally).
Run the commands below from the repository directory unless stated otherwise.

## Login and Screen Unlock

```bash
./scripts/install-launch-agent.sh
```

The installer resolves the repository's absolute path and writes
`~/Library/LaunchAgents/local.doomsday-drill.plist`. The plist in the repository
is a template; the generated file is specific to your Mac and stays outside Git.
Keep the repository and its `.venv` at that location while the service is enabled.
If you move the repository or change the template, run the installer again.

Installation starts the watcher and presents a drill immediately. After that, the
watcher stays resident and presents a drill after login and each unlock. Duplicate
notifications are suppressed, and only one automatic drill runs at a time.

The watcher observes AppKit session activation and the distributed notification
`com.apple.screenIsUnlocked`. The latter name is undocumented by Apple, so unlock
detection may need adjustment on future macOS versions. Neither mechanism is part
of the authentication process.

## Check the Service

```bash
launchctl print gui/$(id -u)/local.doomsday-drill
```

Look for `state = running`. To restart the watcher and request a drill:

```bash
launchctl kickstart -k gui/$(id -u)/local.doomsday-drill
```

View output and errors:

```bash
tail -n 50 /tmp/local.doomsday-drill.out.log
tail -n 50 /tmp/local.doomsday-drill.err.log
```

If automatic drills do not appear, try `.venv/bin/python -m doomsday_drill` first.
If that fails, check your Python version and install `requirements.txt` in the
virtual environment. If it works, check the service and logs above, then rerun
the installer if the repository or Python path has changed.

## Choose a Reference Link

The **Reference** button opens [Conway's article](references.md) by default.
Override it for a manual drill with:

```bash
DOOMSDAY_REFERENCE_URL="https://en.wikipedia.org/wiki/Doomsday_rule" \
  .venv/bin/python -m doomsday_drill
```

For automatic drills, add this dictionary to the installed
`~/Library/LaunchAgents/local.doomsday-drill.plist`:

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>DOOMSDAY_REFERENCE_URL</key>
  <string>https://en.wikipedia.org/wiki/Doomsday_rule</string>
</dict>
```

A `file:///absolute/path/to/reference.pdf` URL also works for a local copy.
Use a complete URL; shell shortcuts such as `~` and `$HOME` do not expand in a
plist. Keep personal file URLs in the installed plist, outside the repository.

Reload that installed file to apply the change:

```bash
launchctl bootout gui/$(id -u)/local.doomsday-drill
launchctl bootstrap gui/$(id -u) "$HOME/Library/LaunchAgents/local.doomsday-drill.plist"
```

Running the installer regenerates the installed plist from the template and
overwrites local customizations. Use the reload commands above after editing the
installed file.

## Saved Data and Removal

Disable automatic launches and remove the generated LaunchAgent:

```bash
./scripts/uninstall-launch-agent.sh
```

The repository, virtual environment, statistics, and logs remain. None of them
can trigger automatic launches once the LaunchAgent has been removed.

| Location | Contents |
| --- | --- |
| `~/Library/Application Support/Doomsday Drill/stats.json` | Attempt history, accuracy, streaks, and adaptive practice weights |
| `~/Library/Application Support/Doomsday Drill/stats.corrupt-*.json` | Backups of malformed stats, if any |
| `/tmp/local.doomsday-drill.out.log` | Watcher output |
| `/tmp/local.doomsday-drill.err.log` | Watcher errors |

These files are optional to remove. Deleting the Application Support directory
resets your practice history. The logs may include local paths in error messages;
review them before sharing a bug report.

Stats are saved locally, and skipped prompts are not recorded. A drill itself
does not require a network connection; opening an online reference uses your
browser. [Development notes](development.md#stats-and-adaptation) describe how
the adaptive selection works.
