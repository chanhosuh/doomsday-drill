# Development Notes

User-facing setup lives in the [README](../README.md) and [setup guide](setup.md).
This document records implementation details and possible future work.

## Layout

| File | Responsibility |
| --- | --- |
| `doomsday_drill/core.py` | Date selection, answer checking, mnemonics, and worked calculations |
| `doomsday_drill/stats.py` | Local persistence, streaks, and adaptive weights |
| `doomsday_drill/main.py` | One question-and-feedback workflow |
| `doomsday_drill/ui_mac.py` | Native AppKit interface through PyObjC |
| `doomsday_drill/watcher.py` | Login, session activation, and screen-unlock handling |
| `doomsday_drill/config.py` | Reference-link configuration |
| `launchd/` and `scripts/` | Portable LaunchAgent template and local installation |

## Checks

From the repository root, with dependencies installed:

```bash
.venv/bin/python -m compileall -q doomsday_drill tests
.venv/bin/python -m unittest discover -s tests
```

GitHub Actions runs the suite on macOS with Python 3.12, exercising AppKit imports
as well as the platform-independent calculation logic. A local GUI check remains
useful for window layout and macOS-version differences.

## Documentation Screenshots

```bash
.venv/bin/python scripts/capture-screenshots.py
```

This briefly opens the real app windows and captures the prompt, expanded hint,
and worked answer into `docs/images/`. It uses August 19, 1973, one of Conway's
examples, and synthetic statistics. Stats loading and saving are replaced in
that process only, so personal practice data is neither read nor written.
The screenshot process uses light appearance without changing system settings.

Review the images before committing. They should contain only the app's own
windows and sample data, with readable labels and no clipped explanation text.

## Stats and Adaptation

The stats file tracks total and correct attempts, current and best streaks,
recent attempts, missed months, offsets from anchors, centuries, years of the
century, and exact years. Recent attempt history is bounded.

When misses exist, the sampler usually targets one weak bucket. Correct answers
decay the matching weights so old weak spots stop dominating. After a wrong
answer, the user's selected mistake stage reinforces only the relevant buckets;
`Not sure` reinforces all relevant dimensions. Year-only questions offer only
century and year mistake stages.

About one in four prompts asks for a year's Doomsday directly. Repeated exposure
to missed years supports memorization. Feedback summarizes up to three current
adaptive priorities. Skipped prompts do not change stats.

Stats are written atomically. Malformed JSON is moved aside as
`stats.corrupt-*.json`, and a fresh history is started. See the
[setup guide](setup.md#saved-data-and-removal) for storage and log locations.

## Possible Future Work

Ideas, not a promised release schedule:

- A daily throttle for repeated unlocks.
- A terminal practice loop for longer sessions.
- Hard mode and configurable date ranges. The current default is 1900-2100.
- A fuller practice window if the one-question flow grows beyond a small popup.

Keep operating-system integration separate from the date logic. Prefer native
controls and a small dependency footprint as the UI evolves.
