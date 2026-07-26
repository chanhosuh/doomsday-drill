# Doomsday Drill

A small macOS login drill for practicing Conway's Doomsday Algorithm.

The project keeps the critical date and answer-checking logic in plain Python. The macOS-specific popup code is isolated in `doomsday_drill/ui_mac.py` and uses PyObjC/AppKit.

## Setup

From the repo root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run one drill manually:

```bash
.venv/bin/python -m doomsday_drill
```

Run tests:

```bash
.venv/bin/python -m unittest discover -s tests
```

The same suite runs on `macos-latest` in GitHub Actions so the PyObjC/AppKit
import path is checked as well as the platform-independent calculation logic.

## Stats And Adaptation

Submitted answers are recorded in:

```text
~/Library/Application Support/Doomsday Drill/stats.json
```

The stats file tracks total attempts, correct attempts, current streak, best
streak, recent attempts, missed months, missed offsets from the nearest
doomsday anchor, missed centuries, and missed year-of-century values.

Future prompts are adaptive. When there is miss history, the sampler usually
biases toward one missed bucket, such as a month or an offset from a nearby
anchor. Correct answers decay the matching miss buckets, so old weak spots stop
dominating once they improve.

After a wrong answer, the result popup asks which step caused trouble. Choosing
the century anchor, year calculation, month anchor, or counting step reinforces
only that part of future practice. `Not sure` reinforces all four dimensions.

The login drill mixes complete-date questions with dedicated year-doomsday
questions; about one question in four asks directly for a year's doomsday.
Missed exact years are included in adaptive selection so repeated exposure can
turn calculated year doomsdays into memorized ones.

The result summary shows the current adaptive focus in plain language, with up
to three priorities drawn from the strongest remaining miss buckets.

Skipped prompts are not recorded.

Stats updates are written atomically, so an interrupted write does not damage the
previous file. If malformed JSON is found, it is moved aside as a timestamped
`stats.corrupt-*.json` file and the drill starts with fresh stats.

## Reference Link

The prompt includes a `Reference` button. By default it opens:

```text
https://en.wikipedia.org/wiki/Doomsday_rule
```

The original Conway article citation is:

```text
John Horton Conway, "Tomorrow is the Day After Doomsday,"
Eureka 36, pp. 28-31, October 1973.
```

The drill also teaches the later Odd + 11 shortcut as an alternative way to
calculate the year shift. It was introduced by Chamberlain Fong and Michael K.
Walters in [Methods for Accelerating Conway's Doomsday Algorithm (part
2)](https://arxiv.org/abs/1010.0765).

I have not found a clearly authorized public PDF to bundle with this repo. To
use a different source URL temporarily, set `DOOMSDAY_REFERENCE_URL` before
running the app. For launchd, add it under an `EnvironmentVariables` key in the
plist:

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>DOOMSDAY_REFERENCE_URL</key>
  <string>file:///Users/example/path/to/reference.pdf</string>
</dict>
```

## Login And Unlock LaunchAgent

The included LaunchAgent starts a lightweight watcher after your graphical user
session starts. It runs one drill at login and another after each screen unlock.
It does not hook into macOS authentication, does not run on the lock screen, and
does not block login or unlock.

The watcher listens for the system's `com.apple.screenIsUnlocked` distributed
notification and also observes AppKit's session-activation notification. Apple
documents the notification mechanisms but not the screen-unlock notification
name, so that exact hook may need adjustment on a future macOS release.

First complete the setup above so `.venv/bin/python` exists and PyObjC is
installed.

Enable it:

```bash
mkdir -p ~/Library/LaunchAgents
ln -sf /Users/example/git/doomsday-drill/launchd/com.example.doomsday-drill.plist \
  ~/Library/LaunchAgents/com.example.doomsday-drill.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.doomsday-drill.plist
```

Run it once immediately to test:

```bash
launchctl kickstart -k gui/$(id -u)/com.example.doomsday-drill
```

After that, the watcher remains resident in your graphical session and presents
the drill after login and each unlock. Duplicate notifications are suppressed,
and a second drill is not opened while one is already active.

Check whether launchd knows about it:

```bash
launchctl print gui/$(id -u)/com.example.doomsday-drill
```

View logs:

```bash
tail -n 50 /tmp/com.example.doomsday-drill.out.log
tail -n 50 /tmp/com.example.doomsday-drill.err.log
```

Disable it cleanly:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.example.doomsday-drill.plist
```

Remove the LaunchAgent symlink:

```bash
rm ~/Library/LaunchAgents/com.example.doomsday-drill.plist
```

If you edit the plist after it has already been loaded, unload and load it again:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.example.doomsday-drill.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.doomsday-drill.plist
```

## Extensions

Already implemented:

- After answering, the drill shows the correct weekday.
- The feedback includes the year's doomsday weekday.
- The feedback includes the nearest doomsday anchor date and the offset from it.
- The prompt includes a disclosure hint with Conway-style mnemonics and the Odd + 11 shortcut.
- Stats persist in `~/Library/Application Support/Doomsday Drill/stats.json`.
- The result popup shows accuracy and streaks.
- Future dates bias toward missed months, offsets, centuries, and year-of-century values.
- The drill includes adaptive year-doomsday questions for direct memorization.
- The prompt includes a configurable reference link.

Good next extensions:

- Add a "hard mode" that asks only for the weekday and does not show the anchor hint afterward.
- Add date range settings, for example 1800-2200, 1900-2100, current century, or future dates only.
- Add a daily throttle so repeated logins on the same day do not keep showing the prompt.
- Add a CLI practice loop for drilling many dates from Terminal.
- Replace the one-shot alert with a small SwiftUI wrapper if this grows beyond a simple popup.

Recommended build order:

1. Add daily throttle.
2. Add a CLI practice mode.
3. Add hard mode and date-range settings.
4. Revisit the UI only if the popup starts feeling too cramped.
