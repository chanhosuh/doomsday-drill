import unittest

from doomsday_drill.ui_mac import (
    mistake_stage_options,
    weekday_validation_message,
)


class MacUiTests(unittest.TestCase):
    def test_weekday_validation_accepts_aliases(self):
        self.assertIsNone(weekday_validation_message("tues."))
        self.assertIsNotNone(weekday_validation_message(""))
        self.assertEqual(
            weekday_validation_message("notaday"),
            "Enter a weekday name or abbreviation.",
        )

    def test_mistake_stage_options_can_be_limited_for_year_questions(self):
        self.assertEqual(
            mistake_stage_options(("century", "year")),
            (
                ("Not sure", "unsure"),
                ("Century anchor", "century"),
                ("Year calculation", "year"),
            ),
        )

    def test_default_mistake_stage_options_include_all_stages(self):
        self.assertEqual(len(mistake_stage_options()), 5)

    def test_unknown_mistake_stage_options_are_not_displayed(self):
        self.assertEqual(
            mistake_stage_options(("unexpected",)),
            (("Not sure", "unsure"),),
        )


if __name__ == "__main__":
    unittest.main()
