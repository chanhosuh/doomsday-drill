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
    "misses_by_year_mod_100",
)


@dataclass(frozen=True)
class DrillQuestion:
    target: date
    prompt: str
    correct_weekday: str
    hint: str


@dataclass(frozen=True)
class AnswerResult:
    target: date
    guess: str
    correct_weekday: str
    is_correct: bool


@dataclass(frozen=True)
class DoomsdayReference:
    year: int
    doomsday_weekday: str
    nearest_anchor: date
    offset_days: int


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
) -> DrillQuestion:
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
    return DrillQuestion(
        target=target,
        prompt=f"What day of the week was {format_date(target)}?",
        correct_weekday=weekday_name(target),
        hint=conway_hint(target),
    )


def format_date(value: date) -> str:
    return f"{calendar.month_name[value.month]} {value.day}, {value.year}"


def weekday_name(value: date) -> str:
    return WEEKDAY_NAMES[value.weekday()]


def normalize_answer(answer: str) -> str:
    return "".join(char for char in answer.lower() if char.isalpha())


def parse_weekday_answer(answer: str) -> str | None:
    return ANSWER_ALIASES.get(normalize_answer(answer))


def check_answer(answer: str, target: date) -> AnswerResult:
    correct_weekday = weekday_name(target)
    parsed = parse_weekday_answer(answer)
    return AnswerResult(
        target=target,
        guess=answer,
        correct_weekday=correct_weekday,
        is_correct=parsed == correct_weekday,
    )


def century_anchor_sunday_zero(year: int) -> int:
    century = year // 100
    return (5 * (century % 4) + 2) % 7


def doomsday_weekday_sunday_zero(year: int) -> int:
    year_of_century = year % 100
    return (
        century_anchor_sunday_zero(year)
        + year_of_century
        + year_of_century // 4
    ) % 7


def doomsday_weekday_name(year: int) -> str:
    return SUNDAY_ZERO_WEEKDAY_NAMES[doomsday_weekday_sunday_zero(year)]


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
    year_of_century = target.year % 100
    century_start = (target.year // 100) * 100
    dozens = year_of_century // 12
    remainder = year_of_century % 12
    fours = remainder // 4

    if reference.offset_days == 0:
        offset = "The target date is itself a doomsday anchor."
    else:
        direction = "after" if reference.offset_days > 0 else "before"
        steps = abs(reference.offset_days) % 7
        plural = "" if abs(reference.offset_days) == 1 else "s"
        step_plural = "" if steps == 1 else "s"
        offset = (
            f"The target is {abs(reference.offset_days)} day{plural} {direction} "
            f"{format_date(reference.nearest_anchor)}, so move {steps} "
            f"weekday step{step_plural} modulo 7."
        )

    return (
        "Conway route:\n"
        f"For {year_of_century:02d}, count {dozens} dozen(s), "
        f"{remainder} extra year(s), and {fours} four(s) in the extra years.\n"
        f"{odd_plus_eleven_hint(year_of_century)}\n"
        f"Add those to the {century_start}s century anchor, reducing by sevens.\n"
        f"{anchor_mnemonic(reference.nearest_anchor)}\n"
        f"{offset}\n"
        "For weekday numbers, use Conway's verbal names: Sansday, Oneday, "
        "Twosday, Treblesday, Foursday, Fiveday, Six-a-day."
    )


def odd_plus_eleven_hint(year_of_century: int) -> str:
    total = year_of_century
    steps = [f"{total:02d}"]

    if total % 2:
        total += 11
        steps.append(str(total))

    total //= 2
    steps.append(str(total))

    if total % 2:
        total += 11
        steps.append(str(total))

    return (
        f"Odd + 11 shortcut: {' -> '.join(steps)}; "
        f"use 7 - ({total} mod 7) as the shift."
    )


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
        else f"Nope. It was {result.correct_weekday}."
    )
    reference = doomsday_reference(result.target)

    if reference.offset_days == 0:
        offset = "The target date is itself a doomsday anchor."
    elif reference.offset_days > 0:
        offset = (
            f"The target date is {reference.offset_days} day(s) after "
            f"{format_date(reference.nearest_anchor)}."
        )
    else:
        offset = (
            f"The target date is {abs(reference.offset_days)} day(s) before "
            f"{format_date(reference.nearest_anchor)}."
        )

    return (
        f"{status}\n\n"
        f"For {reference.year}, doomsday is {reference.doomsday_weekday}.\n"
        f"{offset}"
    )


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
    if bucket == "misses_by_year_mod_100":
        return candidate.year % 100 == wanted
    return False
