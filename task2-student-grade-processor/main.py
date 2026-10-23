"""Demo runner for the grade processor."""

from grades import InvalidScoreError, process_students, validate_score

STUDENTS = [
    {"name": "Aysel", "scores": [85, 92, 78, 90]},
    {"name": "Murad", "scores": [45, 52, 38, 60]},
    {"name": "Leyla", "scores": [100, 95, 98]},
    {"name": "Tural", "scores": [70, -5, 80]},      # invalid: negative
    {"name": "Nigar", "scores": [88, 105, 91]},     # invalid: above 100
]


def print_report(results, errors) -> None:
    print(f"{'Name':<10}{'Avg':>8}{'High':>8}{'Low':>8}{'Status':>9}")
    print("-" * 43)
    for r in results:
        print(
            f"{r['name']:<10}{r['average']:>8.2f}{r['highest']:>8.1f}"
            f"{r['lowest']:>8.1f}{r['status']:>9}"
        )
    if errors:
        print("\nSkipped (invalid input):")
        for name, message in errors:
            print(f"  - {name}: {message}")


def interactive_mode() -> None:
    """Let the user type scores and re-ask on invalid input."""
    name = input("Student name: ").strip() or "Student"
    scores = []
    print("Enter scores one by one (empty line to finish).")
    while True:
        raw = input("Score: ").strip()
        if not raw:
            break
        try:
            scores.append(validate_score(float(raw)))
        except ValueError as exc:  # covers InvalidScoreError and float() errors
            print(f"  Try again -> {exc}")
    if not scores:
        print("No scores entered.")
        return
    results, errors = process_students([{"name": name, "scores": scores}])
    print_report(results, errors)


def main() -> None:
    print("=== Sample data ===")
    results, errors = process_students(STUDENTS)
    print_report(results, errors)

    answer = input("\nTry interactive mode? (y/n): ").strip().lower()
    if answer == "y":
        interactive_mode()


if __name__ == "__main__":
    main()
