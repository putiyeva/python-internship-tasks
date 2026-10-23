"""Reusable grade-processing functions.

This module is meant to be imported (see ``main.py``) rather than run directly.
All public functions validate their input and raise ``InvalidScoreError`` when
a score is outside the allowed range.
"""

from typing import Dict, List, Tuple

MIN_SCORE: float = 0.0
MAX_SCORE: float = 100.0
PASS_THRESHOLD: float = 50.0


class InvalidScoreError(ValueError):
    """Raised when a score is not a number or is outside 0-100."""

    def __init__(self, score: object, reason: str = "") -> None:
        self.score = score
        message = f"Invalid score {score!r}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


def validate_score(score: float) -> float:
    """Return ``score`` if it is a valid number in [0, 100], else raise.

    Booleans are rejected on purpose, since ``True`` would otherwise pass as 1.
    """
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise InvalidScoreError(score, "must be a number")
    if score != score:  # NaN check
        raise InvalidScoreError(score, "must not be NaN")
    if score < MIN_SCORE:
        raise InvalidScoreError(score, "cannot be negative")
    if score > MAX_SCORE:
        raise InvalidScoreError(score, f"cannot be above {MAX_SCORE:g}")
    return float(score)


def validate_scores(scores: List[float]) -> List[float]:
    """Validate a whole list of scores and return them as floats."""
    if not scores:
        raise InvalidScoreError(scores, "score list is empty")
    return [validate_score(s) for s in scores]


def calculate_average(scores: List[float]) -> float:
    """Return the average of ``scores`` rounded to 2 decimals."""
    valid = validate_scores(scores)
    return round(sum(valid) / len(valid), 2)


def highest_score(scores: List[float]) -> float:
    """Return the highest score."""
    return max(validate_scores(scores))


def lowest_score(scores: List[float]) -> float:
    """Return the lowest score."""
    return min(validate_scores(scores))


def pass_fail(average: float, threshold: float = PASS_THRESHOLD) -> str:
    """Return ``"PASS"`` if ``average`` meets the threshold, else ``"FAIL"``."""
    validate_score(average)
    return "PASS" if average >= threshold else "FAIL"


def process_student(name: str, scores: List[float]) -> Dict[str, object]:
    """Build a result record for a single student."""
    avg = calculate_average(scores)
    return {
        "name": name,
        "average": avg,
        "highest": highest_score(scores),
        "lowest": lowest_score(scores),
        "status": pass_fail(avg),
    }


def process_students(
    records: List[Dict[str, object]],
) -> Tuple[List[Dict[str, object]], List[Tuple[str, str]]]:
    """Process many student records.

    Each record looks like ``{"name": "Aysel", "scores": [80, 90]}``.
    Students with invalid scores do not stop the run; they are collected
    in the second return value as ``(name, error message)`` pairs.
    """
    results: List[Dict[str, object]] = []
    errors: List[Tuple[str, str]] = []
    for record in records:
        name = str(record.get("name", "<unknown>"))
        try:
            results.append(process_student(name, record.get("scores", [])))  # type: ignore[arg-type]
        except InvalidScoreError as exc:
            errors.append((name, str(exc)))
    return results, errors
