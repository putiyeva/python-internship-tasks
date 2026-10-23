"""Demo of the inventory system."""

from datetime import date, timedelta

from inventory import (
    ExpiredProductError,
    InsufficientStockError,
    Inventory,
    PerishableProduct,
    Product,
)


def build_inventory() -> Inventory:
    today = date.today()
    inv = Inventory()
    inv.add_product(Product("P-100", "USB-C Cable", 4.99, quantity=40, low_stock_threshold=10))
    inv.add_product(Product("P-200", "Wireless Mouse", 15.50, quantity=8, low_stock_threshold=10))
    inv.add_product(Product("P-300", "Mechanical Keyboard", 59.00, quantity=0, low_stock_threshold=3))
    inv.add_product(
        PerishableProduct("F-100", "Milk 1L", 1.20, today + timedelta(days=2),
                          quantity=30, low_stock_threshold=10)
    )
    inv.add_product(
        PerishableProduct("F-200", "Yogurt", 0.90, today - timedelta(days=1),
                          quantity=12, low_stock_threshold=5)
    )
    inv.add_product(
        PerishableProduct("F-300", "Cheese", 7.50, today + timedelta(days=30),
                          quantity=20, low_stock_threshold=5)
    )
    return inv


def main() -> None:
    inv = build_inventory()

    print(inv.report())

    print("\n--- Operations ---")
    print("Sold 5 cables, left:", inv.remove_stock("P-100", 5))
    print("Restocked mice, now:", inv.add_stock("P-200", 20))

    try:
        inv.remove_stock("P-200", 100)
    except InsufficientStockError as exc:
        print("Error:", exc)

    try:
        inv.remove_stock("F-200", 1)
    except ExpiredProductError as exc:
        print("Error:", exc)

    yogurt = inv.get_product("F-200")
    print("Discarded expired yogurt units:", yogurt.discard_expired())

    try:
        inv.get_product("P-100").quantity = -5  # blocked by the property setter
    except ValueError as exc:
        print("Error:", exc)

    print("\n--- Product details (__str__) ---")
    print(inv.get_product("P-100"))
    print(inv.get_product("F-100"))

    print("\n--- Low stock products ---")
    for product in inv.low_stock_products():
        print(" ", product.name, f"({product.quantity} left)")

    print()
    print(inv.report())


if __name__ == "__main__":
    main()
