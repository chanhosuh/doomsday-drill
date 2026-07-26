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
    odd_plus_eleven_hint,
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
        self.assertIn("Worked route:", message)
        self.assertIn("Year doomsday: Tuesday + 4 = Saturday.", message)

    def test_conway_hint_gives_scaffold_without_final_weekday(self):
        hint = conway_hint(date(2026, 7, 4))
        self.assertIn("Conway year method: 26 is 2 dozen plus 2 extra years", hint)
        self.assertIn("The year shift is 2 + 2 + 0 = 4, or 4 mod 7", hint)
        self.assertIn("Fong-Walters Odd + 11 alternative", hint)
        self.assertIn("It is even, so halve it: 13", hint)
        self.assertIn("13 is odd, so add 11: 24", hint)
        self.assertIn("Negate modulo 7: -24 gives a year shift of 4", hint)
        self.assertIn("7-11 pair: 7/11", hint)
        self.assertIn("7 days before", hint)
        self.assertIn("an exact number of weeks, so the weekday is unchanged", hint)
        self.assertIn("Sansday, Oneday, Twosday", hint)
        self.assertNotIn("Saturday", hint)

    def test_feedback_explains_2044_year_calculation(self):
        message = feedback_message(check_answer("Monday", date(2044, 8, 12)))
        self.assertIn("Nope. It was Friday.", message)
        self.assertIn("Century anchor: 2000s -> Tuesday", message)
        self.assertIn("Conway year method: 44 = 3 dozen + 8 extra years", message)
        self.assertIn("3 + 8 + 2 = 13, which is 6 mod 7", message)
        self.assertIn("Fong-Walters Odd + 11 check", message)
        self.assertIn("It is even, so halve it: 22", message)
        self.assertIn("22 is even, so leave it unchanged", message)
        self.assertIn("Negate modulo 7: -22 gives a year shift of 6", message)
        self.assertIn("Year doomsday: Tuesday + 6 = Monday.", message)
        self.assertIn("Use the even-month double date: 8/8 is a doomsday.", message)
        self.assertIn("August 12, 2044 is 4 days after August 8, 2044", message)
        self.assertIn("Monday -> Tuesday -> Wednesday -> Thursday -> Friday", message)

    def test_odd_plus_eleven_explains_both_odd_steps(self):
        hint = odd_plus_eleven_hint(57)
        self.assertIn("57 is odd, so add 11: 68", hint)
        self.assertIn("Halve it: 34", hint)
        self.assertIn("34 is even, so leave it unchanged", hint)
        self.assertIn("Negate modulo 7: -34 gives a year shift of 1", hint)


if __name__ == "__main__":
    unittest.main()
