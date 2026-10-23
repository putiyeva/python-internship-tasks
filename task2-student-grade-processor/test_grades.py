import pytest

from grades import (
    InvalidScoreError,
    calculate_average,
    highest_score,
    lowest_score,
    pass_fail,
    process_student,
    process_students,
    validate_score,
)


def test_average():
    assert calculate_average([80, 90, 100]) == 90.0


def test_highest_lowest():
    assert highest_score([10, 50, 99]) == 99.0
    assert lowest_score([10, 50, 99]) == 10.0


def test_pass_fail():
    assert pass_fail(50) == "PASS"
    assert pass_fail(49.99) == "FAIL"


@pytest.mark.parametrize("bad", [-1, 100.1, 101, "80", None, True, float("nan")])
def test_invalid_scores_raise(bad):
    with pytest.raises(InvalidScoreError):
        validate_score(bad)


def test_empty_list_raises():
    with pytest.raises(InvalidScoreError):
        calculate_average([])


def test_custom_exception_is_value_error():
    assert issubclass(InvalidScoreError, ValueError)


def test_process_student_record():
    result = process_student("Aysel", [60, 70])
    assert result["average"] == 65.0
    assert result["status"] == "PASS"


def test_process_students_skips_invalid_and_reports():
    results, errors = process_students(
        [
            {"name": "A", "scores": [80, 90]},
            {"name": "B", "scores": [80, -1]},
        ]
    )
    assert [r["name"] for r in results] == ["A"]
    assert errors[0][0] == "B"
