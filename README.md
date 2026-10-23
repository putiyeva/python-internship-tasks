# Python Programming & AI: Internship Tasks

Solutions to four tasks from the Python Programming & AI internship assignment. Every task is a standalone folder with its own code, tests and README.

**Author:** Nermin Putiyeva

| Task | Level | Folder | Highlights |
|---|---|---|---|
| Task 1: CLI Expense Tracker | Level 1 | [`task1-expense-tracker`](task1-expense-tracker) | JSON persistence, input validation, monthly summary (bonus) |
| Task 2: Student Grade Processor | Level 1 | [`task2-student-grade-processor`](task2-student-grade-processor) | Importable module, custom exception, type hints (bonus) |
| Task 3: Automated File Organizer | Level 2 | [`task3-file-organizer`](task3-file-organizer) | Never overwrites files, dry-run, logging (bonus) |
| Task 4: OOP Inventory System | Level 2 | [`task4-oop-inventory`](task4-oop-inventory) | Inheritance, `@property`, `__str__`, pytest (bonus) |

## Requirements

- Python 3.8 or newer
- No third-party packages are needed to run the programs
- `pytest` is needed only to run the tests: `pip install -r requirements-dev.txt`

## Running a task

Each task runs from inside its own folder:

```bash
cd task2-student-grade-processor
python main.py
pytest
```

See the README in each folder for details and example output.

## Tests

Run the tests of one task by going into its folder and running `pytest`. Each task has its own test suite (Task 1: 12 tests, Task 2: 14, Task 3: 14, Task 4: 48).
