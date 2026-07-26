import random
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from doomsday_drill.core import adaptive_random_date, check_answer
from doomsday_drill.stats import (
    empty_stats,
    load_stats,
    record_attempt,
    save_stats,
    stats_summary,
)


class StatsTests(unittest.TestCase):
    def test_record_attempt_tracks_streaks_and_miss_buckets(self):
        stats = empty_stats()
        timestamp = datetime(2026, 7, 4, 9, 30, tzinfo=timezone.utc)

        stats = record_attempt(
            stats,
            check_answer("Sunday", date(2026, 7, 4)),
            attempted_at=timestamp,
        )

        self.assertEqual(stats["total_attempts"], 1)
        self.assertEqual(stats["correct_attempts"], 0)
        self.assertEqual(stats["current_streak"], 0)
        self.assertEqual(stats["misses_by_month"], {"7": 1})
        self.assertEqual(stats["misses_by_century"], {"2000": 1})
        self.assertEqual(stats["misses_by_year_mod_100"], {"26": 1})
        self.assertEqual(stats["recent_attempts"][0]["date"], "2026-07-04")
        self.assertEqual(stats["recent_attempts"][0]["mistake_stage"], "unsure")

        stats = record_attempt(
            stats,
            check_answer("Saturday", date(2026, 7, 4)),
            attempted_at=timestamp,
        )

        self.assertEqual(stats["total_attempts"], 2)
        self.assertEqual(stats["correct_attempts"], 1)
        self.assertEqual(stats["current_streak"], 1)
        self.assertEqual(stats["longest_streak"], 1)
        self.assertEqual(stats["misses_by_month"], {})
        self.assertEqual(stats["misses_by_century"], {})

    def test_reported_mistake_only_reinforces_that_stage(self):
        stats = record_attempt(
            empty_stats(),
            check_answer("Sunday", date(2026, 7, 4)),
            mistake_stage="year",
        )

        self.assertEqual(stats["misses_by_year_mod_100"], {"26": 1})
        self.assertEqual(stats["misses_by_month"], {})
        self.assertEqual(stats["misses_by_offset"], {})
        self.assertEqual(stats["misses_by_century"], {})
        self.assertEqual(stats["recent_attempts"][0]["mistake_stage"], "year")

    def test_unknown_mistake_stage_uses_all_buckets(self):
        stats = record_attempt(
            empty_stats(),
            check_answer("Sunday", date(2026, 7, 4)),
            mistake_stage="unexpected",
        )

        self.assertEqual(stats["misses_by_month"], {"7": 1})
        self.assertEqual(stats["misses_by_offset"], {"-7": 1})
        self.assertEqual(stats["misses_by_century"], {"2000": 1})
        self.assertEqual(stats["misses_by_year_mod_100"], {"26": 1})
        self.assertEqual(stats["recent_attempts"][0]["mistake_stage"], "unsure")

    def test_stats_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.json"
            stats = record_attempt(
                empty_stats(),
                check_answer("Saturday", date(2026, 7, 4)),
                attempted_at=datetime(2026, 7, 4, 9, 30, tzinfo=timezone.utc),
            )

            save_stats(stats, path=path)
            loaded = load_stats(path=path)

        self.assertEqual(loaded["total_attempts"], 1)
        self.assertEqual(loaded["correct_attempts"], 1)
        self.assertEqual(loaded["current_streak"], 1)

    def test_failed_save_preserves_existing_stats(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.json"
            path.write_text('{"total_attempts": 7}\n', encoding="utf-8")

            with patch("doomsday_drill.stats.json.dump", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    save_stats(empty_stats(), path=path)

            self.assertEqual(
                path.read_text(encoding="utf-8"),
                '{"total_attempts": 7}\n',
            )
            self.assertEqual(list(path.parent.glob(".stats.json.*.tmp")), [])

    def test_load_quarantines_malformed_stats(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.json"
            path.write_text('{"total_attempts":', encoding="utf-8")

            with patch("doomsday_drill.stats.sys.stderr"):
                loaded = load_stats(path=path)

            backups = list(path.parent.glob("stats.corrupt-*.json"))
            self.assertEqual(loaded, empty_stats())
            self.assertFalse(path.exists())
            self.assertEqual(len(backups), 1)
            self.assertEqual(
                backups[0].read_text(encoding="utf-8"),
                '{"total_attempts":',
            )

    def test_stats_summary(self):
        stats = record_attempt(
            empty_stats(),
            check_answer("Saturday", date(2026, 7, 4)),
            attempted_at=datetime(2026, 7, 4, 9, 30, tzinfo=timezone.utc),
        )

        self.assertIn("1/1 correct (100%)", stats_summary(stats))
        self.assertIn("Current streak: 1", stats_summary(stats))

    def test_adaptive_random_date_biases_toward_missed_month(self):
        stats = empty_stats()
        stats["misses_by_month"] = {"2": 25}

        target = adaptive_random_date(stats, rng=random.Random(1))

        self.assertEqual(target.month, 2)


if __name__ == "__main__":
    unittest.main()
