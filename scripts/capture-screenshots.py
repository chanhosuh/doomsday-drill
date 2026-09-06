"""Capture the real AppKit workflow using a fixed question and in-memory stats."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from AppKit import (
    NSAppearance,
    NSAppearanceNameAqua,
    NSApplication,
    NSBitmapImageFileTypePNG,
    NSModalPanelRunLoopMode,
)
from Foundation import NSRunLoop, NSTimer

from doomsday_drill import main
from doomsday_drill.core import DrillQuestion, conway_hint, format_date, weekday_name
from doomsday_drill.stats import empty_stats


def capture(window, path: Path) -> None:
    view = window.contentView().superview()
    view.layoutSubtreeIfNeeded()
    window.displayIfNeeded()
    bitmap = view.bitmapImageRepForCachingDisplayInRect_(view.bounds())
    view.cacheDisplayInRect_toBitmapImageRep_(view.bounds(), bitmap)
    data = bitmap.representationUsingType_properties_(NSBitmapImageFileTypePNG, {})
    if not data.writeToFile_atomically_(str(path), True):
        raise RuntimeError(f"Could not write {path}")
    print(f"Captured {path.name}: {bitmap.pixelsWide()} x {bitmap.pixelsHigh()}")


def run() -> None:
    output = ROOT / "docs" / "images"
    output.mkdir(parents=True, exist_ok=True)
    target = date(1973, 8, 19)
    question = DrillQuestion(
        target=target,
        prompt=f"On which weekday does {format_date(target)} fall?",
        correct_weekday=weekday_name(target),
        hint=conway_hint(target),
        question_kind="date",
    )
    stats = empty_stats()
    stats.update(total_attempts=11, correct_attempts=9, current_streak=3, longest_streak=4)
    app = NSApplication.sharedApplication()
    app.setAppearance_(NSAppearance.appearanceNamed_(NSAppearanceNameAqua))
    phase = 0
    failures = []

    def advance(timer):
        nonlocal phase
        try:
            window = app.keyWindow()
            if window is None:
                raise RuntimeError("The drill did not open a window")
            if phase == 0:
                capture(window, output / "prompt.png")
                controller = window.delegate()
                controller.disclosure.performClick_(None)
            elif phase == 1:
                capture(window, output / "hint.png")
                controller = window.delegate()
                controller.answer_field.setStringValue_("Sunday")
                controller.check_button.performClick_(None)
            else:
                capture(window, output / "feedback.png")
                timer.invalidate()
                app.stopModal()
                window.orderOut_(None)
            phase += 1
        except Exception as error:
            failures.append(error)
            timer.invalidate()
            app.abortModal()

    timer = NSTimer.timerWithTimeInterval_repeats_block_(1.0, True, advance)
    NSRunLoop.currentRunLoop().addTimer_forMode_(timer, NSModalPanelRunLoopMode)
    try:
        with (
            patch.object(main, "make_question", return_value=question),
            patch.object(main, "load_stats", return_value=stats),
            patch.object(main, "save_stats"),
        ):
            main.run()
    finally:
        timer.invalidate()
        for window in app.windows():
            window.orderOut_(None)
    if failures:
        raise failures[0]
    if phase != 3:
        raise RuntimeError("Capture interrupted before all three screenshots were written")


if __name__ == "__main__":
    run()
