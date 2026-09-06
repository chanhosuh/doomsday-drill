import unittest
from unittest.mock import patch

from AppKit import NSApplication, NSControlStateValueOff, NSControlStateValueOn

from doomsday_drill.ui_mac import (
    _PromptController,
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

    def test_hint_expands_to_fit_and_collapses_without_moving_buttons(self):
        app = NSApplication.sharedApplication()
        with patch("doomsday_drill.ui_mac._activate_app", return_value=app):
            controller = _PromptController.alloc().initWithPrompt_hint_referenceUrl_(
                "On which weekday does August 19, 1973 fall?",
                "A short hint.",
                "https://example.org/reference",
            )
        try:
            collapsed_height = controller.window.contentView().frame().size.height
            button_frame = controller.reference_button.frame()
            self.assertEqual(controller.disclosure.title(), "")
            self.assertEqual(controller.hint_label.stringValue(), "Conway-style hint")

            controller.disclosure.setState_(NSControlStateValueOn)
            controller.toggleHint_(None)
            short_height = controller.window.contentView().frame().size.height
            controller.hint_field.setStringValue_("A line of explanation.\n" * 24)
            controller._layout()
            long_height = controller.window.contentView().frame().size.height
            self.assertGreater(long_height, short_height + 200)
            hint_frame = controller.hint_field.frame()
            self.assertGreater(
                hint_frame.origin.y, button_frame.origin.y + button_frame.size.height
            )
            self.assertLess(
                hint_frame.origin.y + hint_frame.size.height,
                controller.hint_label.frame().origin.y,
            )
            self.assertEqual(controller.reference_button.frame(), button_frame)

            controller.disclosure.setState_(NSControlStateValueOff)
            controller.toggleHint_(None)
            self.assertTrue(controller.hint_field.isHidden())
            self.assertEqual(
                controller.window.contentView().frame().size.height, collapsed_height
            )
        finally:
            controller.finished = True
            controller.window.close()


if __name__ == "__main__":
    unittest.main()
