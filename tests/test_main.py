import unittest
from datetime import date
from unittest.mock import patch

from doomsday_drill.core import DrillQuestion
from doomsday_drill.main import run
from doomsday_drill.stats import empty_stats


class MainTests(unittest.TestCase):
    @patch("doomsday_drill.main.show_message")
    @patch("doomsday_drill.main.save_stats")
    @patch("doomsday_drill.main.record_attempt")
    @patch("doomsday_drill.main.ask_weekday", return_value="notaday")
    @patch("doomsday_drill.main.make_question")
    @patch("doomsday_drill.main.load_stats", return_value={})
    def test_invalid_answer_is_not_recorded(
        self,
        load_stats,
        make_question,
        ask_weekday,
        record_attempt,
        save_stats,
        show_message,
    ):
        self.assertEqual(run(), 0)
        record_attempt.assert_not_called()
        save_stats.assert_not_called()
        show_message.assert_not_called()

    @patch("doomsday_drill.main.save_stats")
    @patch("doomsday_drill.main.show_message", return_value="year")
    @patch("doomsday_drill.main.ask_weekday", return_value="Sunday")
    @patch("doomsday_drill.main.load_stats", side_effect=empty_stats)
    def test_wrong_answer_records_reported_mistake_stage(
        self,
        load_stats,
        ask_weekday,
        show_message,
        save_stats,
    ):
        question = DrillQuestion(
            target=date(2026, 7, 4),
            prompt="What day?",
            correct_weekday="Saturday",
            hint="Hint",
        )

        with patch("doomsday_drill.main.make_question", return_value=question):
            self.assertEqual(run(), 0)

        saved_stats = save_stats.call_args.args[0]
        self.assertEqual(saved_stats["misses_by_year_mod_100"], {"26": 1})
        self.assertEqual(saved_stats["misses_by_month"], {})
        self.assertEqual(saved_stats["recent_attempts"][0]["mistake_stage"], "year")
        self.assertTrue(show_message.call_args.kwargs["collect_mistake_stage"])


if __name__ == "__main__":
    unittest.main()
