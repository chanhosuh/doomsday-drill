import random
import unittest
from datetime import date

from doomsday_drill.core import (
    check_answer,
    conway_hint,
    doomsday_weekday_name,
    feedback_message,
    make_question,
    nearest_doomsday_anchor,
    parse_weekday_answer,
    weekday_name,
)


class CoreTests(unittest.TestCase):
    def test_weekday_name_uses_gregorian_calendar(self):
        self.assertEqual(weekday_name(date(2026, 7, 4)), "Saturday")
        self.assertEqual(weekday_name(date(2000, 1, 1)), "Saturday")

    def test_parse_weekday_answer_accepts_common_forms(self):
        self.assertEqual(parse_weekday_answer("Tue"), "Tuesday")
        self.assertEqual(parse_weekday_answer("tues."), "Tuesday")
        self.assertEqual(parse_weekday_answer(" THURSDAY "), "Thursday")
        self.assertIsNone(parse_weekday_answer("notaday"))

    def test_check_answer(self):
        target = date(2026, 7, 4)
        self.assertTrue(check_answer("sat", target).is_correct)
        self.assertFalse(check_answer("sun", target).is_correct)

    def test_doomsday_weekday_matches_known_anchor_dates(self):
        for year in (1900, 1999, 2000, 2026, 2100):
            self.assertEqual(
                doomsday_weekday_name(year),
                weekday_name(date(year, 4, 4)),
            )

    def test_nearest_doomsday_anchor_uses_leap_year_january_anchor(self):
        self.assertEqual(nearest_doomsday_anchor(date(2024, 1, 5)), date(2024, 1, 4))
        self.assertEqual(nearest_doomsday_anchor(date(2026, 1, 5)), date(2026, 1, 3))

    def test_make_question_can_use_seeded_rng(self):
        question = make_question(rng=random.Random(7))
        self.assertIn(str(question.target.year), question.prompt)
        self.assertEqual(question.correct_weekday, weekday_name(question.target))
        self.assertIn("Conway route:", question.hint)

    def test_feedback_includes_doomsday_reference(self):
        message = feedback_message(check_answer("sat", date(2026, 7, 4)))
        self.assertIn("Correct: Saturday.", message)
        self.assertIn("For 2026, doomsday is Saturday.", message)

    def test_conway_hint_gives_scaffold_without_final_weekday(self):
        hint = conway_hint(date(2026, 7, 4))
        self.assertIn("For 26, count 2 dozen(s), 2 extra year(s)", hint)
        self.assertIn("Odd + 11 shortcut: 26 -> 13 -> 24", hint)
        self.assertIn("7-11 pair: 7/11", hint)
        self.assertIn("7 days before", hint)
        self.assertIn("Sansday, Oneday, Twosday", hint)
        self.assertNotIn("Saturday", hint)


if __name__ == "__main__":
    unittest.main()
