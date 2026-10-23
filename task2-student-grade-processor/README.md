# Task 2: Student Grade Processor

Modular Python functions that calculate the average, highest and lowest score, and pass/fail status for a list of student records, with strict input validation.

## Features

- Separate importable module (`grades.py`) and a demo runner (`main.py`)
- Input validation: rejects negative scores, scores above 100, non-numbers, `NaN`, booleans and empty lists
- Custom exception class `InvalidScoreError` (a subclass of `ValueError`)
- Type hints on all function signatures
- PEP 8 style
- One bad student record does not crash the whole run; it is reported at the end
- Unit tests with `pytest`

## Project structure

```
task2-student-grade-processor/
├── grades.py        # reusable functions + custom exception
├── main.py          # demo and interactive mode
├── test_grades.py   # pytest tests
└── README.md
```

## Usage

```bash
python main.py
```

Example output:

```
Name           Avg    High     Low   Status
-------------------------------------------
Aysel        86.25    92.0    78.0     PASS
Murad        48.75    60.0    38.0     FAIL
Leyla        97.67   100.0    95.0     PASS

Skipped (invalid input):
  - Tural: Invalid score -5: cannot be negative
  - Nigar: Invalid score 105: cannot be above 100
```

Use it as a module:

```python
from grades import calculate_average, InvalidScoreError

try:
    print(calculate_average([80, 90, 101]))
except InvalidScoreError as e:
    print(e)
```

## Run tests

```bash
pip install pytest
pytest
```

## Concepts covered

Functions and parameters, modules and imports, PEP 8, input validation, custom exceptions, type hints.
