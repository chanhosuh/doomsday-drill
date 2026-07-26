from __future__ import annotations

from .core import check_answer, feedback_message, make_question, parse_weekday_answer
from .stats import load_stats, record_attempt, save_stats, stats_summary
from .ui_mac import ask_weekday, show_message


def run() -> int:
    stats = load_stats()
    question = make_question(stats=stats)
    answer = ask_weekday(question.prompt, question.hint)

    if answer is None:
        return 0

    if parse_weekday_answer(answer) is None:
        return 0

    result = check_answer(answer, question.target)
    if result.is_correct:
        stats = record_attempt(stats, result)
        save_stats(stats)
        show_message(f"{feedback_message(result)}\n\n{stats_summary(stats)}")
        return 0

    preview_stats = record_attempt(stats, result, mistake_stage="unsure")
    mistake_stage = show_message(
        f"{feedback_message(result)}\n\n{stats_summary(preview_stats)}",
        collect_mistake_stage=True,
    )
    stats = record_attempt(stats, result, mistake_stage=mistake_stage)
    save_stats(stats)
    return 0
