from __future__ import annotations

import time
import traceback
from collections.abc import Callable

from .main import run as run_drill


SCREEN_UNLOCK_NOTIFICATION = "com.apple.screenIsUnlocked"
TRIGGER_COOLDOWN_SECONDS = 5.0


class DrillTrigger:
    def __init__(
        self,
        drill: Callable[[], object],
        clock: Callable[[], float] = time.monotonic,
        cooldown_seconds: float = TRIGGER_COOLDOWN_SECONDS,
    ) -> None:
        self._drill = drill
        self._clock = clock
        self._cooldown_seconds = cooldown_seconds
        self._active = False
        self._last_finished_at: float | None = None

    def trigger(self) -> bool:
        now = self._clock()
        if self._active:
            return False
        if (
            self._last_finished_at is not None
            and now - self._last_finished_at < self._cooldown_seconds
        ):
            return False

        self._active = True
        try:
            self._drill()
        finally:
            self._active = False
            self._last_finished_at = self._clock()
        return True


def _run_drill_safely() -> None:
    try:
        run_drill()
    except Exception:
        traceback.print_exc()


def _make_unlock_observer_class():
    import objc
    from Foundation import NSObject

    class UnlockObserver(NSObject):
        def initWithTrigger_(self, trigger: DrillTrigger):
            self = objc.super(UnlockObserver, self).init()
            if self is None:
                return None
            self.trigger = trigger
            return self

        def screenUnlocked_(self, notification):
            self.trigger.trigger()

        def sessionBecameActive_(self, notification):
            self.trigger.trigger()

    return UnlockObserver


def run() -> int:
    from AppKit import NSWorkspace, NSWorkspaceSessionDidBecomeActiveNotification
    from Foundation import (
        NSDistributedNotificationCenter,
        NSNotificationSuspensionBehaviorDeliverImmediately,
        NSRunLoop,
    )

    trigger = DrillTrigger(_run_drill_safely)
    observer_class = _make_unlock_observer_class()
    observer = observer_class.alloc().initWithTrigger_(trigger)

    distributed_center = NSDistributedNotificationCenter.defaultCenter()
    distributed_center.addObserver_selector_name_object_suspensionBehavior_(
        observer,
        "screenUnlocked:",
        SCREEN_UNLOCK_NOTIFICATION,
        None,
        NSNotificationSuspensionBehaviorDeliverImmediately,
    )

    workspace_center = NSWorkspace.sharedWorkspace().notificationCenter()
    workspace_center.addObserver_selector_name_object_(
        observer,
        "sessionBecameActive:",
        NSWorkspaceSessionDidBecomeActiveNotification,
        None,
    )

    trigger.trigger()
    NSRunLoop.currentRunLoop().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
