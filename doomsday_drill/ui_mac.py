from __future__ import annotations

from .config import REFERENCE_URL
from .core import parse_weekday_answer


MISTAKE_STAGE_OPTIONS = (
    ("Not sure", "unsure"),
    ("Century anchor", "century"),
    ("Year calculation", "year"),
    ("Month anchor", "month_anchor"),
    ("Counting from anchor", "offset"),
)


def _activate_app():
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    app.activateIgnoringOtherApps_(True)
    return app


def ask_weekday(
    prompt: str,
    hint: str = "",
    reference_url: str = REFERENCE_URL,
) -> str | None:
    _activate_app()
    controller = _PromptController.alloc().initWithPrompt_hint_referenceUrl_(
        prompt,
        hint,
        reference_url,
    )
    return controller.run()


def _label(text: str, font_size: float, selectable: bool = False):
    from AppKit import NSFont, NSLineBreakByWordWrapping, NSTextField

    field = NSTextField.alloc().initWithFrame_(((0.0, 0.0), (0.0, 0.0)))
    field.setStringValue_(text)
    field.setBezeled_(False)
    field.setDrawsBackground_(False)
    field.setEditable_(False)
    field.setSelectable_(selectable)
    field.setFont_(NSFont.systemFontOfSize_(font_size))

    cell = field.cell()
    cell.setWraps_(True)
    cell.setScrollable_(False)
    cell.setLineBreakMode_(NSLineBreakByWordWrapping)

    return field


def _error_label():
    from AppKit import NSColor

    field = _label("", 11.0)
    field.setTextColor_(NSColor.systemRedColor())
    return field


def _set_frame(view, x: float, y: float, width: float, height: float) -> None:
    from AppKit import NSMakeRect

    view.setFrame_(NSMakeRect(x, y, width, height))


def _set_window_content_size(window, width: float, height: float) -> None:
    from AppKit import NSMakeSize

    window.setContentSize_(NSMakeSize(width, height))


def _make_button(title: str, action: str):
    from AppKit import NSBezelStyleRounded, NSButton

    button = NSButton.alloc().initWithFrame_(((0.0, 0.0), (0.0, 0.0)))
    button.setTitle_(title)
    button.setBezelStyle_(NSBezelStyleRounded)
    button.setTarget_(None)
    button.setAction_(action)
    return button


def _open_url(url: str) -> None:
    from AppKit import NSWorkspace
    from Foundation import NSURL

    ns_url = NSURL.URLWithString_(url)
    if ns_url is not None:
        NSWorkspace.sharedWorkspace().openURL_(ns_url)


def _make_window(width: float, height: float):
    from AppKit import (
        NSBackingStoreBuffered,
        NSMakeRect,
        NSWindow,
        NSWindowStyleMaskClosable,
        NSWindowStyleMaskTitled,
    )

    _activate_app()
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(0.0, 0.0, width, height),
        NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
        NSBackingStoreBuffered,
        False,
    )
    window.setTitle_("Doomsday Drill")
    window.setReleasedWhenClosed_(False)
    return window


def _target_action_button(title: str, target, action: str):
    button = _make_button(title, action)
    button.setTarget_(target)
    return button


def _disclosure_button(target):
    from AppKit import NSBezelStyleDisclosure, NSButton, NSButtonTypeOnOff

    button = NSButton.alloc().initWithFrame_(((0.0, 0.0), (0.0, 0.0)))
    button.setTitle_("Conway-style hint")
    button.setButtonType_(NSButtonTypeOnOff)
    button.setBezelStyle_(NSBezelStyleDisclosure)
    button.setTarget_(target)
    button.setAction_("toggleHint:")
    return button


def _text_entry():
    from AppKit import NSTextField

    field = NSTextField.alloc().initWithFrame_(((0.0, 0.0), (0.0, 0.0)))
    field.setPlaceholderString_("Weekday")
    return field


def _is_on(control) -> bool:
    from AppKit import NSControlStateValueOn

    return control.state() == NSControlStateValueOn


def _stop_modal() -> None:
    from AppKit import NSApplication

    NSApplication.sharedApplication().stopModal()


def _run_modal(window) -> None:
    from AppKit import NSApplication

    NSApplication.sharedApplication().runModalForWindow_(window)


def _return_key() -> str:
    return "\r"


def _escape_key() -> str:
    return "\033"


def _empty_sender():
    return None


def _close_window(window) -> None:
    window.close()


def _order_out(window) -> None:
    window.orderOut_(_empty_sender())


def _show_window(window) -> None:
    window.center()
    window.makeKeyAndOrderFront_(_empty_sender())


def _set_default_button(window, button) -> None:
    window.setDefaultButtonCell_(button.cell())


def _set_first_responder(window, view) -> None:
    window.makeFirstResponder_(view)


def _string_value(field) -> str:
    return str(field.stringValue())


def _set_string_value(field, value: str) -> None:
    field.setStringValue_(value)


def _content_view(window):
    return window.contentView()


def _add_subview(parent, child) -> None:
    parent.addSubview_(child)


def _hide(view, is_hidden: bool) -> None:
    view.setHidden_(is_hidden)


def _set_key_equivalent(button, value: str) -> None:
    button.setKeyEquivalent_(value)


def _set_delegate(window, delegate) -> None:
    window.setDelegate_(delegate)


def _set_title(control, title: str) -> None:
    control.setTitle_(title)


class _PromptControllerBase:
    WIDTH = 440.0
    COLLAPSED_HEIGHT = 204.0
    EXPANDED_HEIGHT = 418.0
    MARGIN = 20.0
    PROMPT_HEIGHT = 38.0
    ENTRY_HEIGHT = 24.0
    ERROR_HEIGHT = 18.0
    DISCLOSURE_HEIGHT = 24.0
    HINT_HEIGHT = 200.0
    BUTTON_WIDTH = 82.0
    REFERENCE_BUTTON_WIDTH = 104.0
    BUTTON_HEIGHT = 32.0

    def _build(self) -> None:
        self.window = _make_window(self.WIDTH, self.COLLAPSED_HEIGHT)
        _set_delegate(self.window, self)

        content = _content_view(self.window)
        self.prompt_field = _label(self.prompt, 14.0)
        self.answer_field = _text_entry()
        self.answer_field.setDelegate_(self)
        self.error_field = _error_label()
        self.disclosure = _disclosure_button(self)
        self.hint_field = _label(self.hint, 12.0, selectable=True)
        self.reference_button = _target_action_button("Reference", self, "reference:")
        self.skip_button = _target_action_button("Skip", self, "skip:")
        self.check_button = _target_action_button("Check", self, "check:")

        _set_key_equivalent(self.skip_button, _escape_key())
        _set_key_equivalent(self.check_button, _return_key())
        _set_default_button(self.window, self.check_button)

        for view in (
            self.prompt_field,
            self.answer_field,
            self.error_field,
            self.disclosure,
            self.hint_field,
            self.reference_button,
            self.skip_button,
            self.check_button,
        ):
            _add_subview(content, view)

        self._layout()

    def _layout(self) -> None:
        expanded = _is_on(self.disclosure)
        height = self.EXPANDED_HEIGHT if expanded else self.COLLAPSED_HEIGHT
        width = self.WIDTH - (self.MARGIN * 2)
        _set_window_content_size(self.window, self.WIDTH, height)

        y = height - self.MARGIN - self.PROMPT_HEIGHT
        _set_frame(self.prompt_field, self.MARGIN, y, width, self.PROMPT_HEIGHT)

        y -= 34.0
        _set_frame(self.answer_field, self.MARGIN, y, width, self.ENTRY_HEIGHT)

        y -= 22.0
        _set_frame(self.error_field, self.MARGIN, y, width, self.ERROR_HEIGHT)

        y -= 30.0
        _set_frame(self.disclosure, self.MARGIN, y, width, self.DISCLOSURE_HEIGHT)

        if expanded:
            _hide(self.hint_field, False)
            y -= self.HINT_HEIGHT + 4.0
            _set_frame(
                self.hint_field,
                self.MARGIN + 18.0,
                y,
                width - 18.0,
                self.HINT_HEIGHT,
            )
        else:
            _hide(self.hint_field, True)

        button_y = 20.0
        _set_frame(
            self.reference_button,
            self.MARGIN,
            button_y,
            self.REFERENCE_BUTTON_WIDTH,
            self.BUTTON_HEIGHT,
        )

        check_x = self.WIDTH - self.MARGIN - self.BUTTON_WIDTH
        skip_x = check_x - self.BUTTON_WIDTH - 8.0
        _set_frame(
            self.skip_button,
            skip_x,
            button_y,
            self.BUTTON_WIDTH,
            self.BUTTON_HEIGHT,
        )
        _set_frame(
            self.check_button,
            check_x,
            button_y,
            self.BUTTON_WIDTH,
            self.BUTTON_HEIGHT,
        )

    def run(self) -> str | None:
        _activate_app()
        _show_window(self.window)
        _set_first_responder(self.window, self.answer_field)
        _run_modal(self.window)
        _close_window(self.window)
        return self.answer

    def _finish(self, answer: str | None) -> None:
        if self.finished:
            return
        self.answer = answer
        self.finished = True
        _order_out(self.window)
        _stop_modal()


def _make_prompt_controller_class():
    import objc
    from Foundation import NSObject

    class PromptController(NSObject, _PromptControllerBase):
        def initWithPrompt_hint_referenceUrl_(
            self,
            prompt: str,
            hint: str,
            reference_url: str,
        ):
            self = objc.super(PromptController, self).init()
            if self is None:
                return None
            self.prompt = prompt
            self.hint = hint
            self.reference_url = reference_url
            self.answer = None
            self.finished = False
            self._build()
            return self

        def toggleHint_(self, sender):
            _set_title(
                self.disclosure,
                "Hide Conway-style hint" if _is_on(self.disclosure) else "Conway-style hint",
            )
            self._layout()
            self.window.center()

        def check_(self, sender):
            answer = _string_value(self.answer_field)
            if parse_weekday_answer(answer) is None:
                _set_string_value(
                    self.error_field,
                    "Enter a weekday name or abbreviation.",
                )
                _set_first_responder(self.window, self.answer_field)
                return

            self._finish(answer)

        def controlTextDidChange_(self, notification):
            _set_string_value(self.error_field, "")

        def reference_(self, sender):
            _open_url(self.reference_url)

        def skip_(self, sender):
            self._finish(None)

        def windowWillClose_(self, notification):
            if not self.finished:
                self._finish(None)

    return PromptController


_PromptController = _make_prompt_controller_class()


def show_message(
    message: str,
    collect_mistake_stage: bool = False,
    mistake_stage_keys: tuple[str, ...] | None = None,
) -> str | None:
    from AppKit import NSAlert, NSMakeRect, NSPopUpButton

    _activate_app()

    alert = NSAlert.alloc().init()
    alert.setMessageText_("Doomsday Drill")
    if collect_mistake_stage:
        message += "\n\nWhich step caused trouble?"
    alert.setInformativeText_(message)

    stage_popup = None
    stage_options = MISTAKE_STAGE_OPTIONS
    if collect_mistake_stage:
        if mistake_stage_keys is not None:
            allowed = set(mistake_stage_keys)
            stage_options = tuple(
                option
                for option in MISTAKE_STAGE_OPTIONS
                if option[1] == "unsure" or option[1] in allowed
            )
        stage_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(0.0, 0.0, 240.0, 26.0),
            False,
        )
        stage_popup.addItemsWithTitles_([label for label, _ in stage_options])
        stage_popup.setAccessibilityLabel_("Mistake stage")
        alert.setAccessoryView_(stage_popup)

    alert.addButtonWithTitle_("OK")
    alert.runModal()

    if stage_popup is None:
        return None

    return stage_options[stage_popup.indexOfSelectedItem()][1]
