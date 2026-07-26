from __future__ import annotations

import calendar
import random
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date


WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

SUNDAY_ZERO_WEEKDAY_NAMES = (
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
)

ANSWER_ALIASES = {
    "mon": "Monday",
    "monday": "Monday",
    "tue": "Tuesday",
    "tues": "Tuesday",
    "tuesday": "Tuesday",
    "wed": "Wednesday",
    "wednesday": "Wednesday",
    "thu": "Thursday",
    "thur": "Thursday",
    "thurs": "Thursday",
    "thursday": "Thursday",
    "fri": "Friday",
    "friday": "Friday",
    "sat": "Saturday",
    "saturday": "Saturday",
    "sun": "Sunday",
    "sunday": "Sunday",
}

DOOMSDAY_ANCHORS_COMMON = (
    (1, 3),
    (2, 28),
    (3, 14),
    (4, 4),
    (5, 9),
    (6, 6),
    (7, 11),
    (8, 8),
    (9, 5),
    (10, 10),
    (11, 7),
    (12, 12),
)

DOOMSDAY_ANCHORS_LEAP = (
    (1, 4),
    (2, 29),
    (3, 14),
    (4, 4),
    (5, 9),
    (6, 6),
    (7, 11),
    (8, 8),
    (9, 5),
    (10, 10),
    (11, 7),
    (12, 12),
)

ADAPTIVE_PROBABILITY = 0.7
ADAPTIVE_BUCKETS = (
    "misses_by_month",
    "misses_by_offset",
    "misses_by_century",
    "misses_by_year",
    "misses_by_year_mod_100",
)
YEAR_DOOMSDAY_PROBABILITY = 0.25
QUESTION_KINDS = ("date", "year_doomsday")
QUESTION_MODES = (*QUESTION_KINDS, "mixed")


@dataclass(frozen=True)
class DrillQuestion:
    target: date
    prompt: str
    correct_weekday: str
    hint: str
    question_kind: str = "date"


@dataclass(frozen=True)
class AnswerResult:
    target: date
    guess: str
    correct_weekday: str
    is_correct: bool
    question_kind: str = "date"


@dataclass(frozen=True)
class DoomsdayReference:
    year: int
    doomsday_weekday: str
    nearest_anchor: date
    offset_days: int


@dataclass(frozen=True)
class YearCalculation:
    year: int
    century_start: int
    year_of_century: int
    century_anchor_index: int
    century_anchor_weekday: str
    dozens: int
    remainder: int
    fours: int
    dozen_shift_raw: int
    dozen_shift: int
    odd_plus_eleven_steps: tuple[int, ...]
    odd_plus_eleven_total: int
    odd_plus_eleven_shift: int
    doomsday_index: int
    doomsday_weekday: str


def random_date(
    start_year: int = 1900,
    end_year: int = 2100,
    rng: random.Random | None = None,
) -> date:
    if start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year")

    rng = rng or random
    year = rng.randint(start_year, end_year)
    month = rng.randint(1, 12)
    day = rng.randint(1, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def adaptive_random_date(
    stats: Mapping[str, object],
    start_year: int = 1900,
    end_year: int = 2100,
    rng: random.Random | None = None,
) -> date:
    rng = rng or random
    available = [
        bucket
        for bucket in ADAPTIVE_BUCKETS
        if _weighted_items(stats.get(bucket))
    ]

    if not available or rng.random() > ADAPTIVE_PROBABILITY:
        return random_date(start_year=start_year, end_year=end_year, rng=rng)

    bucket = rng.choice(available)
    wanted = _weighted_choice(_weighted_items(stats.get(bucket)), rng)

    for _ in range(500):
        candidate = random_date(start_year=start_year, end_year=end_year, rng=rng)
        if _candidate_matches_bucket(candidate, bucket, wanted):
            return candidate

    return random_date(start_year=start_year, end_year=end_year, rng=rng)


def make_question(
    start_year: int = 1900,
    end_year: int = 2100,
    rng: random.Random | None = None,
    stats: Mapping[str, object] | None = None,
    mode: str = "date",
) -> DrillQuestion:
    if mode not in QUESTION_MODES:
        raise ValueError(f"unknown question mode: {mode}")

    rng = rng or random
    question_kind = mode
    if mode == "mixed":
        question_kind = (
            "year_doomsday"
            if rng.random() < YEAR_DOOMSDAY_PROBABILITY
            else "date"
        )

    target = (
        adaptive_random_date(
            stats=stats,
            start_year=start_year,
            end_year=end_year,
            rng=rng,
        )
        if stats
        else random_date(start_year=start_year, end_year=end_year, rng=rng)
    )

    if question_kind == "year_doomsday":
        target = date(target.year, 4, 4)
        return DrillQuestion(
            target=target,
            prompt=f"On which weekday does Doomsday fall in {target.year}?",
            correct_weekday=doomsday_weekday_name(target.year),
            hint=year_doomsday_hint(target.year),
            question_kind=question_kind,
        )

    return DrillQuestion(
        target=target,
        prompt=f"On which weekday does {format_date(target)} fall?",
        correct_weekday=weekday_name(target),
        hint=conway_hint(target),
        question_kind=question_kind,
    )


def format_date(value: date) -> str:
    return f"{calendar.month_name[value.month]} {value.day}, {value.year}"


def weekday_name(value: date) -> str:
    return WEEKDAY_NAMES[value.weekday()]


def normalize_answer(answer: str) -> str:
    return "".join(char for char in answer.lower() if char.isalpha())


def parse_weekday_answer(answer: str) -> str | None:
    return ANSWER_ALIASES.get(normalize_answer(answer))


def check_answer(
    answer: str,
    target: date,
    question_kind: str = "date",
) -> AnswerResult:
    if question_kind not in QUESTION_KINDS:
        raise ValueError(f"unknown question kind: {question_kind}")

    correct_weekday = weekday_name(target)
    parsed = parse_weekday_answer(answer)
    return AnswerResult(
        target=target,
        guess=answer,
        correct_weekday=correct_weekday,
        is_correct=parsed == correct_weekday,
        question_kind=question_kind,
    )


def century_anchor_sunday_zero(year: int) -> int:
    century = year // 100
    return (5 * (century % 4) + 2) % 7


def weekday_name_sunday_zero(index: int) -> str:
    return SUNDAY_ZERO_WEEKDAY_NAMES[index % 7]


def weekday_number_name(index: int) -> str:
    names = (
        "Sansday",
        "Oneday",
        "Twosday",
        "Treblesday",
        "Foursday",
        "Fiveday",
        "Six-a-day",
    )
    return names[index % 7]


def doomsday_weekday_sunday_zero(year: int) -> int:
    year_of_century = year % 100
    return (
        century_anchor_sunday_zero(year)
        + year_of_century
        + year_of_century // 4
    ) % 7


def doomsday_weekday_name(year: int) -> str:
    return SUNDAY_ZERO_WEEKDAY_NAMES[doomsday_weekday_sunday_zero(year)]


def year_calculation(year: int) -> YearCalculation:
    century_start = (year // 100) * 100
    year_of_century = year % 100
    century_anchor = century_anchor_sunday_zero(year)
    dozens = year_of_century // 12
    remainder = year_of_century % 12
    fours = remainder // 4
    dozen_shift_raw = dozens + remainder + fours
    dozen_shift = dozen_shift_raw % 7
    odd_steps, odd_total, odd_shift = odd_plus_eleven_calculation(year_of_century)
    doomsday_index = (century_anchor + dozen_shift) % 7

    return YearCalculation(
        year=year,
        century_start=century_start,
        year_of_century=year_of_century,
        century_anchor_index=century_anchor,
        century_anchor_weekday=weekday_name_sunday_zero(century_anchor),
        dozens=dozens,
        remainder=remainder,
        fours=fours,
        dozen_shift_raw=dozen_shift_raw,
        dozen_shift=dozen_shift,
        odd_plus_eleven_steps=odd_steps,
        odd_plus_eleven_total=odd_total,
        odd_plus_eleven_shift=odd_shift,
        doomsday_index=doomsday_index,
        doomsday_weekday=weekday_name_sunday_zero(doomsday_index),
    )


def nearest_doomsday_anchor(target: date) -> date:
    anchors = (
        DOOMSDAY_ANCHORS_LEAP
        if calendar.isleap(target.year)
        else DOOMSDAY_ANCHORS_COMMON
    )
    candidates = [date(target.year, month, day) for month, day in anchors]
    return min(candidates, key=lambda candidate: abs(candidate - target))


def doomsday_reference(target: date) -> DoomsdayReference:
    anchor = nearest_doomsday_anchor(target)
    return DoomsdayReference(
        year=target.year,
        doomsday_weekday=doomsday_weekday_name(target.year),
        nearest_anchor=anchor,
        offset_days=(target - anchor).days,
    )


def conway_hint(target: date) -> str:
    reference = doomsday_reference(target)
    calculation = year_calculation(target.year)

    if reference.offset_days == 0:
        offset = "The target date is itself a doomsday anchor."
    else:
        direction = "after" if reference.offset_days > 0 else "before"
        steps = abs(reference.offset_days) % 7
        plural = "" if abs(reference.offset_days) == 1 else "s"
        if steps == 0:
            offset = (
                f"The target is {abs(reference.offset_days)} days {direction} "
                f"{format_date(reference.nearest_anchor)}: an exact number of "
                "weeks, so the weekday is unchanged."
            )
        else:
            step_plural = "" if steps == 1 else "s"
            offset = (
                f"The target is {abs(reference.offset_days)} day{plural} {direction} "
                f"{format_date(reference.nearest_anchor)}, so move {steps} "
                f"weekday step{step_plural} modulo 7."
            )

    return (
        "Conway route:\n"
        f"{_year_hint(calculation)}\n"
        "Add the year shift to the century anchor, reducing by sevens.\n"
        f"{anchor_mnemonic(reference.nearest_anchor)}\n"
        f"{offset}\n"
        "For weekday numbers, use Conway's verbal names: Sansday, Oneday, "
        "Twosday, Treblesday, Foursday, Fiveday, Six-a-day."
    )


def year_doomsday_hint(year: int) -> str:
    calculation = year_calculation(year)
    return (
        "Year-doomsday route:\n"
        f"{_year_hint(calculation)}\n"
        "Add the year shift to the century anchor, reducing by sevens."
    )


def _year_hint(calculation: YearCalculation) -> str:
    return (
        f"Century anchor: {_century_span(calculation)} -> "
        f"{calculation.century_anchor_weekday} "
        f"({weekday_number_name(calculation.century_anchor_index)}).\n"
        f"Conway year method: {calculation.year_of_century:02d} is "
        f"{calculation.dozens} dozen plus "
        f"{_count(calculation.remainder, 'extra year')}; add "
        f"{_count(calculation.fours, 'complete group')} of four in the remainder. "
        f"The year shift is {calculation.dozens} + {calculation.remainder} + "
        f"{calculation.fours} = {calculation.dozen_shift_raw}, or "
        f"{calculation.dozen_shift} mod 7.\n"
        f"{odd_plus_eleven_hint(calculation.year_of_century)}"
    )


def odd_plus_eleven_hint(year_of_century: int) -> str:
    return (
        "Fong-Walters Odd + 11 alternative: "
        f"{odd_plus_eleven_explanation(year_of_century)}"
    )


def odd_plus_eleven_explanation(year_of_century: int) -> str:
    value = year_of_century
    sentences = [f"Start with {value:02d}."]

    if value % 2:
        next_value = value + 11
        sentences.append(f"{value} is odd, so add 11: {next_value}.")
        value = next_value
        value //= 2
        sentences.append(f"Halve it: {value}.")
    else:
        value //= 2
        sentences.append(f"It is even, so halve it: {value}.")

    if value % 2:
        next_value = value + 11
        sentences.append(f"{value} is odd, so add 11: {next_value}.")
        value = next_value
    else:
        sentences.append(f"{value} is even, so leave it unchanged.")

    shift = (-value) % 7
    sentences.append(f"Negate modulo 7: -{value} gives a year shift of {shift}.")
    return " ".join(sentences)


def odd_plus_eleven_calculation(year_of_century: int) -> tuple[tuple[int, ...], int, int]:
    total = year_of_century
    steps = [total]

    if total % 2:
        total += 11
        steps.append(total)

    total //= 2
    steps.append(total)

    if total % 2:
        total += 11
        steps.append(total)

    shift = (-total) % 7
    return tuple(steps), total, shift


def anchor_mnemonic(anchor: date) -> str:
    if anchor.month == 1:
        return (
            f"Use January {anchor.day}: the 3rd in three years out of four, "
            "the 4th in the leap year."
        )
    if anchor.month == 2:
        return "Use the last day of February as a doomsday."
    if anchor.month == 3:
        return "Use March 0 or Pi Day, March 14, as a doomsday."
    if anchor.month in (4, 6, 8, 10, 12):
        return (
            f"Use the even-month double date: "
            f"{anchor.month}/{anchor.day} is a doomsday."
        )
    if anchor.month in (5, 9):
        return (
            f"Use the 9-to-5 pair: {anchor.month}/{anchor.day} "
            "is a doomsday."
        )
    if anchor.month in (7, 11):
        return (
            f"Use the 7-11 pair: {anchor.month}/{anchor.day} "
            "is a doomsday."
        )
    raise ValueError(f"unexpected doomsday anchor month: {anchor.month}")


def feedback_message(result: AnswerResult) -> str:
    status = (
        f"Correct: {result.correct_weekday}."
        if result.is_correct
        else f"Not quite. The answer is {result.correct_weekday}."
    )
    worked = (
        worked_year_solution(result.target.year)
        if result.question_kind == "year_doomsday"
        else worked_solution(result.target)
    )

    return f"{status}\n\n{worked}"


def worked_solution(target: date) -> str:
    reference = doomsday_reference(target)
    calculation = year_calculation(target.year)

    if reference.offset_days == 0:
        offset = (
            f"{format_date(target)} is itself a doomsday anchor, so it is "
            f"{reference.doomsday_weekday}."
        )
    elif reference.offset_days > 0:
        steps = reference.offset_days % 7
        offset = (
            f"{format_date(target)} is {_count(reference.offset_days, 'day')} after "
            f"{format_date(reference.nearest_anchor)}. Count forward "
            f"{steps}: {weekday_walk(calculation.doomsday_index, steps)}."
        )
    else:
        steps = abs(reference.offset_days) % 7
        offset = (
            f"{format_date(target)} is "
            f"{_count(abs(reference.offset_days), 'day')} before "
            f"{format_date(reference.nearest_anchor)}. Count back "
            f"{steps}: {weekday_walk(calculation.doomsday_index, -steps)}."
        )

    return (
        "Worked route:\n"
        f"{_worked_year_calculation(calculation)}\n"
        f"{anchor_mnemonic(reference.nearest_anchor)}\n"
        f"{offset}"
    )


def worked_year_solution(year: int) -> str:
    return (
        "Worked year-doomsday route:\n"
        f"{_worked_year_calculation(year_calculation(year))}"
    )


def _worked_year_calculation(calculation: YearCalculation) -> str:
    return (
        f"Century anchor: {_century_span(calculation)} -> "
        f"{calculation.century_anchor_weekday} "
        f"({weekday_number_name(calculation.century_anchor_index)}).\n"
        f"Conway year method: {calculation.year_of_century:02d} = "
        f"{calculation.dozens} dozen + "
        f"{_count(calculation.remainder, 'extra year')}; then add "
        f"{_count(calculation.fours, 'complete group')} of four. "
        f"{calculation.dozens} + {calculation.remainder} + "
        f"{calculation.fours} = {calculation.dozen_shift_raw}, "
        f"which is {calculation.dozen_shift} mod 7.\n"
        f"Fong-Walters Odd + 11 check: "
        f"{odd_plus_eleven_explanation(calculation.year_of_century)}\n"
        f"Year doomsday: {calculation.century_anchor_weekday} + "
        f"{calculation.dozen_shift} = {calculation.doomsday_weekday}."
    )


def weekday_walk(start_index: int, steps: int) -> str:
    if steps == 0:
        return weekday_name_sunday_zero(start_index)

    direction = 1 if steps > 0 else -1
    names = [weekday_name_sunday_zero(start_index)]
    for step in range(1, abs(steps) + 1):
        names.append(weekday_name_sunday_zero(start_index + (direction * step)))

    return " -> ".join(names)


def _count(value: int, noun: str) -> str:
    suffix = "" if value == 1 else "s"
    return f"{value} {noun}{suffix}"


def _century_span(calculation: YearCalculation) -> str:
    return f"{calculation.century_start}-{calculation.century_start + 99}"


def _weighted_items(value: object) -> list[tuple[int, int]]:
    if not isinstance(value, Mapping):
        return []

    items = []
    for key, weight in value.items():
        try:
            parsed_key = int(key)
            parsed_weight = int(weight)
        except (TypeError, ValueError):
            continue

        if parsed_weight > 0:
            items.append((parsed_key, parsed_weight))

    return items


def _weighted_choice(items: list[tuple[int, int]], rng: random.Random) -> int:
    total = sum(weight for _, weight in items)
    pick = rng.randint(1, total)
    running = 0

    for value, weight in items:
        running += weight
        if pick <= running:
            return value

    return items[-1][0]


def _candidate_matches_bucket(candidate: date, bucket: str, wanted: int) -> bool:
    if bucket == "misses_by_month":
        return candidate.month == wanted
    if bucket == "misses_by_offset":
        return doomsday_reference(candidate).offset_days == wanted
    if bucket == "misses_by_century":
        return (candidate.year // 100) * 100 == wanted
    if bucket == "misses_by_year":
        return candidate.year == wanted
    if bucket == "misses_by_year_mod_100":
        return candidate.year % 100 == wanted
    return False
