import unittest

from doomsday_drill.watcher import DrillTrigger


class MutableClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class WatcherTests(unittest.TestCase):
    def test_trigger_suppresses_duplicate_notifications(self):
        clock = MutableClock()
        calls = []
        trigger = DrillTrigger(lambda: calls.append("drill"), clock=clock)

        self.assertTrue(trigger.trigger())
        clock.now = 1.0
        self.assertFalse(trigger.trigger())
        clock.now = 5.0
        self.assertTrue(trigger.trigger())
        self.assertEqual(calls, ["drill", "drill"])

    def test_trigger_ignores_reentrant_notification(self):
        nested_results = []
        trigger = None

        def drill():
            nested_results.append(trigger.trigger())

        trigger = DrillTrigger(drill)
        self.assertTrue(trigger.trigger())
        self.assertEqual(nested_results, [False])

    def test_trigger_recovers_after_drill_error(self):
        clock = MutableClock()

        def failing_drill():
            raise RuntimeError("failed")

        trigger = DrillTrigger(failing_drill, clock=clock)
        with self.assertRaises(RuntimeError):
            trigger.trigger()

        clock.now = 5.0
        with self.assertRaises(RuntimeError):
            trigger.trigger()


if __name__ == "__main__":
    unittest.main()
