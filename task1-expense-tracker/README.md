# Task 1: CLI Expense Tracker with Persistent Storage

A command-line expense tracker. You enter an amount, a category and a date; entries are stored in a list of dictionaries during the session and saved to a local JSON file, so your data is still there next time you run it.

## Features

- Add expenses (amount, category, date) with input validation and re-prompting
- Data kept in memory as `list[dict]`, persisted to `expenses.json`
- Data reloaded automatically on startup (missing or corrupt file is handled safely)
- List all expenses sorted by date
- **Bonus:** monthly summary report with total, average and count per category (f-string formatted table)
- Unit tests with `pytest`

## Project structure

```
task1-expense-tracker/
├── expense_tracker.py       # application
├── test_expense_tracker.py  # pytest tests
├── expenses.json            # created automatically on first save
└── README.md
```

## Usage

```bash
python expense_tracker.py
```

```
=== Expense Tracker ===
1. Add expense
2. List expenses
3. Monthly summary
4. Quit
```

Example monthly summary:

```
Monthly summary for 2026-03
Category        Count       Total     Average
----------------------------------------------
food                2       30.00       15.00
transport           1        5.00        5.00
----------------------------------------------
TOTAL                       35.00
```

Stored data format (`expenses.json`):

```json
[
  {"amount": 10.0, "category": "food", "date": "2026-03-01"}
]
```

## Run tests

```bash
pip install pytest
pytest
```

## Concepts covered

Variables and data types, lists and dictionaries, file I/O with `json`, basic CLI design, f-strings and aggregation.
