import unittest
from unittest.mock import patch

from doomsday_drill.main import run


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


if __name__ == "__main__":
    unittest.main()
