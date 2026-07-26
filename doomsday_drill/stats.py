from __future__ import annotations

import calendar
import json
import os
import sys
import tempfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from .core import AnswerResult, doomsday_reference, format_date


APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "Doomsday Drill"
DEFAULT_STATS_PATH = APP_SUPPORT_DIR / "stats.json"
MAX_RECENT_ATTEMPTS = 200
STATS_VERSION = 3
MISTAKE_STAGE_BUCKETS = {
    "century": ("misses_by_century",),
    "year": ("misses_by_year", "misses_by_year_mod_100"),
    "month_anchor": ("misses_by_month",),
    "offset": ("misses_by_offset",),
}


def empty_stats() -> dict[str, Any]:
    return {
        "version": STATS_VERSION,
        "total_attempts": 0,
        "correct_attempts": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "last_attempt_at": None,
        "misses_by_month": {},
        "misses_by_offset": {},
        "misses_by_century": {},
        "misses_by_year": {},
        "misses_by_year_mod_100": {},
        "recent_attempts": [],
    }


def load_stats(path: Path = DEFAULT_STATS_PATH) -> dict[str, Any]:
    if not path.exists():
        return empty_stats()

    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except json.JSONDecodeError:
        backup_path = _quarantine_corrupt_stats(path)
        if backup_path is not None:
            print(
                f"Doomsday Drill: moved corrupt stats to {backup_path}",
                file=sys.stderr,
            )
        return empty_stats()
    except OSError:
        return empty_stats()

    return normalize_stats(loaded)


def save_stats(stats: dict[str, Any], path: Path = DEFAULT_STATS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            json.dump(normalize_stats(stats), handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        temp_path.replace(path)
    except BaseException:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def normalize_stats(value: object) -> dict[str, Any]:
    stats = empty_stats()
    if not isinstance(value, dict):
        return stats

    for key in (
        "total_attempts",
        "correct_attempts",
        "current_streak",
        "longest_streak",
    ):
        stats[key] = _safe_int(value.get(key), stats[key])

    stats["last_attempt_at"] = (
        value.get("last_attempt_at")
        if isinstance(value.get("last_attempt_at"), str)
        else None
    )

    for key in (
        "misses_by_month",
        "misses_by_offset",
        "misses_by_century",
        "misses_by_year",
        "misses_by_year_mod_100",
    ):
        stats[key] = _normalize_counter(value.get(key))

    recent_attempts = value.get("recent_attempts")
    if isinstance(recent_attempts, list):
        stats["recent_attempts"] = [
            attempt for attempt in recent_attempts[-MAX_RECENT_ATTEMPTS:]
            if isinstance(attempt, dict)
        ]

    return stats


def record_attempt(
    stats: dict[str, Any],
    result: AnswerResult,
    attempted_at: datetime | None = None,
    mistake_stage: str | None = None,
) -> dict[str, Any]:
    attempted_at = attempted_at or datetime.now().astimezone()
    updated = normalize_stats(deepcopy(stats))

    updated["total_attempts"] += 1
    updated["last_attempt_at"] = attempted_at.isoformat(timespec="seconds")

    if result.is_correct:
        updated["correct_attempts"] += 1
        updated["current_streak"] += 1
        updated["longest_streak"] = max(
            updated["longest_streak"],
            updated["current_streak"],
        )
        _decay_miss_buckets(updated, result)
    else:
        updated["current_streak"] = 0
        mistake_stage = _normalize_mistake_stage(mistake_stage)
        _record_miss_buckets(updated, result, mistake_stage)

    updated["recent_attempts"].append(
        _attempt_record(result, attempted_at, mistake_stage)
    )
    updated["recent_attempts"] = updated["recent_attempts"][-MAX_RECENT_ATTEMPTS:]
    return updated


def stats_summary(stats: dict[str, Any]) -> str:
    normalized = normalize_stats(stats)
    total = normalized["total_attempts"]
    correct = normalized["correct_attempts"]
    accuracy = (correct / total * 100.0) if total else 0.0

    return (
        f"Stats: {correct}/{total} correct ({accuracy:.0f}%).\n"
        f"Current streak: {normalized['current_streak']}. "
        f"Best streak: {normalized['longest_streak']}.\n"
        f"Current focus: {_adaptive_focus_summary(normalized)}."
    )


def _adaptive_focus_summary(stats: dict[str, Any]) -> str:
    specs = (
        ("misses_by_year", 0),
        ("misses_by_year_mod_100", 1),
        ("misses_by_month", 2),
        ("misses_by_offset", 3),
        ("misses_by_century", 4),
    )
    candidates: list[tuple[int, int, str, int, str]] = []

    for bucket, priority in specs:
        counter = stats[bucket]
        if not counter:
            continue
        key, weight = sorted(
            counter.items(),
            key=lambda item: (-item[1], int(item[0])),
        )[0]
        value = int(key)
        candidates.append(
            (weight, priority, bucket, value, _focus_label(bucket, value))
        )

    candidates.sort(key=lambda candidate: (-candidate[0], candidate[1]))
    selected: list[tuple[int, int, str, int, str]] = []
    for candidate in candidates:
        if any(_focuses_overlap(candidate, existing) for existing in selected):
            continue
        selected.append(candidate)
        if len(selected) == 3:
            break

    if not selected:
        return "broad practice"
    return "; ".join(candidate[4] for candidate in selected)


def _focus_label(bucket: str, value: int) -> str:
    if bucket == "misses_by_year":
        return f"{value} year doomsday"
    if bucket == "misses_by_year_mod_100":
        return f"years ending in {value:02d}"
    if bucket == "misses_by_month":
        month = calendar.month_name[value] if 1 <= value <= 12 else f"month {value}"
        return f"{month} month anchor"
    if bucket == "misses_by_offset":
        if value == 0:
            return "dates on a doomsday anchor"
        direction = "after" if value > 0 else "before"
        return f"{_count(abs(value), 'day')} {direction} an anchor"
    if bucket == "misses_by_century":
        return f"{value}-{value + 99} century anchor"
    raise ValueError(f"unknown focus bucket: {bucket}")


def _focuses_overlap(
    first: tuple[int, int, str, int, str],
    second: tuple[int, int, str, int, str],
) -> bool:
    _, _, first_bucket, first_value, _ = first
    _, _, second_bucket, second_value, _ = second
    buckets = {first_bucket, second_bucket}

    if buckets == {"misses_by_year", "misses_by_year_mod_100"}:
        year = first_value if first_bucket == "misses_by_year" else second_value
        ending = (
            first_value
            if first_bucket == "misses_by_year_mod_100"
            else second_value
        )
        return year % 100 == ending

    if buckets == {"misses_by_year", "misses_by_century"}:
        year = first_value if first_bucket == "misses_by_year" else second_value
        century = (
            first_value if first_bucket == "misses_by_century" else second_value
        )
        return century <= year <= century + 99

    return False


def _count(value: int, noun: str) -> str:
    suffix = "" if value == 1 else "s"
    return f"{value} {noun}{suffix}"


def _record_miss_buckets(
    stats: dict[str, Any],
    result: AnswerResult,
    mistake_stage: str,
) -> None:
    reference = doomsday_reference(result.target)
    values = {
        "misses_by_month": result.target.month,
        "misses_by_offset": reference.offset_days,
        "misses_by_century": (result.target.year // 100) * 100,
        "misses_by_year": result.target.year,
        "misses_by_year_mod_100": result.target.year % 100,
    }
    selected_buckets = MISTAKE_STAGE_BUCKETS.get(mistake_stage)
    relevant_buckets = _relevant_buckets(result)

    for bucket, value in values.items():
        if bucket not in relevant_buckets:
            continue
        if selected_buckets is None or bucket in selected_buckets:
            _increment_counter(stats[bucket], value)


def _decay_miss_buckets(stats: dict[str, Any], result: AnswerResult) -> None:
    reference = doomsday_reference(result.target)
    values = {
        "misses_by_month": result.target.month,
        "misses_by_offset": reference.offset_days,
        "misses_by_century": (result.target.year // 100) * 100,
        "misses_by_year": result.target.year,
        "misses_by_year_mod_100": result.target.year % 100,
    }

    for bucket in _relevant_buckets(result):
        _decrement_counter(stats[bucket], values[bucket])


def _attempt_record(
    result: AnswerResult,
    attempted_at: datetime,
    mistake_stage: str | None,
) -> dict[str, Any]:
    reference = doomsday_reference(result.target)
    return {
        "attempted_at": attempted_at.isoformat(timespec="seconds"),
        "date": result.target.isoformat(),
        "display_date": format_date(result.target),
        "guess": result.guess,
        "correct_weekday": result.correct_weekday,
        "is_correct": result.is_correct,
        "question_kind": result.question_kind,
        "mistake_stage": mistake_stage if not result.is_correct else None,
        "month": result.target.month,
        "year": result.target.year,
        "century": (result.target.year // 100) * 100,
        "year_mod_100": result.target.year % 100,
        "nearest_anchor": reference.nearest_anchor.isoformat(),
        "offset_days": reference.offset_days,
    }


def _increment_counter(counter: dict[str, int], value: int) -> None:
    key = str(value)
    counter[key] = counter.get(key, 0) + 1


def _decrement_counter(counter: dict[str, int], value: int) -> None:
    key = str(value)
    if key not in counter:
        return

    next_value = counter[key] - 1
    if next_value > 0:
        counter[key] = next_value
    else:
        del counter[key]


def _normalize_counter(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}

    counter = {}
    for key, weight in value.items():
        try:
            parsed_key = str(int(key))
            parsed_weight = int(weight)
        except (TypeError, ValueError):
            continue

        if parsed_weight > 0:
            counter[parsed_key] = parsed_weight

    return counter


def _safe_int(value: object, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback

    return max(0, parsed)


def _normalize_mistake_stage(value: object) -> str:
    if isinstance(value, str) and value in MISTAKE_STAGE_BUCKETS:
        return value
    return "unsure"


def _relevant_buckets(result: AnswerResult) -> tuple[str, ...]:
    year_buckets = (
        "misses_by_century",
        "misses_by_year",
        "misses_by_year_mod_100",
    )
    if result.question_kind == "year_doomsday":
        return year_buckets
    return (*year_buckets, "misses_by_month", "misses_by_offset")


def _quarantine_corrupt_stats(path: Path) -> Path | None:
    timestamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%f%z")
    backup_path = path.with_name(f"{path.stem}.corrupt-{timestamp}{path.suffix}")

    try:
        path.replace(backup_path)
    except OSError:
        return None

    return backup_path
