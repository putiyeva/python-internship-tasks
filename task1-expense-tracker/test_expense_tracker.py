import pytest

import expense_tracker as et


def test_parse_amount_valid():
    assert et.parse_amount("12.5") == 12.5
    assert et.parse_amount("3,75") == 3.75


@pytest.mark.parametrize("bad", ["abc", "0", "-4", ""])
def test_parse_amount_invalid(bad):
    with pytest.raises(ValueError):
        et.parse_amount(bad)


def test_parse_date():
    assert et.parse_date("2026-03-05") == "2026-03-05"
    with pytest.raises(ValueError):
        et.parse_date("05/03/2026")


def test_empty_date_means_today():
    assert len(et.parse_date("")) == 10


def test_save_and_reload(tmp_path):
    path = tmp_path / "data.json"
    expenses = []
    et.add_expense(expenses, 10.0, "food", "2026-03-01")
    et.save_expenses(expenses, path)
    assert et.load_expenses(path) == expenses


def test_load_missing_file(tmp_path):
    assert et.load_expenses(tmp_path / "nope.json") == []


def test_load_corrupt_file(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert et.load_expenses(path) == []


def test_monthly_summary_sum_and_average():
    expenses = []
    et.add_expense(expenses, 10, "food", "2026-03-01")
    et.add_expense(expenses, 20, "food", "2026-03-15")
    et.add_expense(expenses, 5, "transport", "2026-03-02")
    et.add_expense(expenses, 99, "food", "2026-04-01")  # other month
    summary = et.monthly_summary(expenses, "2026-03")
    assert summary["food"] == {"total": 30.0, "average": 15.0, "count": 2}
    assert summary["transport"]["total"] == 5.0
    assert "2026-04" not in str(summary)


def test_format_summary_empty():
    assert "No expenses" in et.format_summary("2026-03", {})
