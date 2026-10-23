"""CLI Expense Tracker with persistent JSON storage.

Entries are kept in memory as a list of dictionaries and saved to a local
JSON file so they survive between runs.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DATA_FILE = Path(__file__).with_name("expenses.json")
DATE_FORMAT = "%Y-%m-%d"

Expense = Dict[str, object]


# ---------- storage ----------

def load_expenses(path: Path = DATA_FILE) -> List[Expense]:
    """Load expenses from ``path``. Return an empty list if missing or corrupt."""
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        print(f"Warning: could not read {path.name}, starting with an empty list.")
        return []
    return data if isinstance(data, list) else []


def save_expenses(expenses: List[Expense], path: Path = DATA_FILE) -> None:
    """Write expenses to ``path`` as pretty JSON."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(expenses, f, indent=2, ensure_ascii=False)


# ---------- validation / parsing ----------

def parse_amount(text: str) -> float:
    """Convert text to a positive amount or raise ``ValueError``."""
    try:
        amount = float(text.replace(",", "."))
    except ValueError:
        raise ValueError("Amount must be a number.") from None
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return round(amount, 2)


def parse_date(text: str) -> str:
    """Return a normalised YYYY-MM-DD date. Empty input means today."""
    text = text.strip()
    if not text:
        return datetime.now().strftime(DATE_FORMAT)
    try:
        return datetime.strptime(text, DATE_FORMAT).strftime(DATE_FORMAT)
    except ValueError:
        raise ValueError("Date must look like YYYY-MM-DD.") from None


def parse_category(text: str) -> str:
    category = text.strip().lower()
    if not category:
        raise ValueError("Category cannot be empty.")
    return category


# ---------- operations ----------

def add_expense(
    expenses: List[Expense], amount: float, category: str, date: str
) -> Expense:
    entry: Expense = {"amount": amount, "category": category, "date": date}
    expenses.append(entry)
    return entry


def monthly_summary(expenses: List[Expense], month: str) -> Dict[str, Dict[str, float]]:
    """Aggregate expenses of ``month`` (``YYYY-MM``) per category.

    Returns ``{category: {"total": ..., "average": ..., "count": ...}}``.
    """
    buckets: Dict[str, List[float]] = defaultdict(list)
    for e in expenses:
        if str(e["date"]).startswith(month):
            buckets[str(e["category"])].append(float(e["amount"]))  # type: ignore[arg-type]
    return {
        cat: {
            "total": round(sum(values), 2),
            "average": round(sum(values) / len(values), 2),
            "count": len(values),
        }
        for cat, values in buckets.items()
    }


def format_summary(month: str, summary: Dict[str, Dict[str, float]]) -> str:
    if not summary:
        return f"No expenses found for {month}."
    lines = [
        f"Monthly summary for {month}",
        f"{'Category':<15}{'Count':>7}{'Total':>12}{'Average':>12}",
        "-" * 46,
    ]
    grand_total = 0.0
    for cat in sorted(summary):
        s = summary[cat]
        grand_total += s["total"]
        lines.append(f"{cat:<15}{int(s['count']):>7}{s['total']:>12.2f}{s['average']:>12.2f}")
    lines.append("-" * 46)
    lines.append(f"{'TOTAL':<15}{'':>7}{grand_total:>12.2f}")
    return "\n".join(lines)


def format_expense_list(expenses: List[Expense]) -> str:
    if not expenses:
        return "No expenses recorded yet."
    lines = [f"{'#':<4}{'Date':<12}{'Category':<15}{'Amount':>10}", "-" * 41]
    for i, e in enumerate(sorted(expenses, key=lambda x: str(x["date"])), start=1):
        lines.append(f"{i:<4}{e['date']:<12}{e['category']:<15}{float(e['amount']):>10.2f}")  # type: ignore[arg-type]
    return "\n".join(lines)


# ---------- CLI ----------

def prompt(label: str, parser) -> str:
    """Keep asking until ``parser`` accepts the input."""
    while True:
        try:
            return parser(input(label))
        except ValueError as exc:
            print(f"  ! {exc}")


def handle_add(expenses: List[Expense]) -> None:
    amount = prompt("Amount: ", parse_amount)
    category = prompt("Category (food, transport, ...): ", parse_category)
    date = prompt("Date YYYY-MM-DD (empty = today): ", parse_date)
    add_expense(expenses, amount, category, date)
    save_expenses(expenses)
    print(f"Saved: {amount:.2f} on {category} ({date})")


def handle_summary(expenses: List[Expense]) -> None:
    default = datetime.now().strftime("%Y-%m")
    month = input(f"Month YYYY-MM (empty = {default}): ").strip() or default
    print()
    print(format_summary(month, monthly_summary(expenses, month)))


MENU = """
=== Expense Tracker ===
1. Add expense
2. List expenses
3. Monthly summary
4. Quit
"""


def main(argv: Optional[List[str]] = None) -> None:
    expenses = load_expenses()
    print(f"Loaded {len(expenses)} saved expense(s).")
    while True:
        print(MENU)
        choice = input("Choose 1-4: ").strip()
        if choice == "1":
            handle_add(expenses)
        elif choice == "2":
            print()
            print(format_expense_list(expenses))
        elif choice == "3":
            handle_summary(expenses)
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Please enter 1, 2, 3 or 4.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
