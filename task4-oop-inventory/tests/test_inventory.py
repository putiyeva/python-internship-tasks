from datetime import date

import pytest

from inventory import (
    DuplicateProductError,
    ExpiredProductError,
    InsufficientStockError,
    Inventory,
    PerishableProduct,
    Product,
    ProductNotFoundError,
)

TODAY = date(2026, 3, 10)


@pytest.fixture
def inv() -> Inventory:
    inventory = Inventory()
    inventory.add_product(Product("P-2", "Mouse", 15.5, quantity=8, low_stock_threshold=10))
    inventory.add_product(Product("P-1", "Cable", 5.0, quantity=40, low_stock_threshold=10))
    inventory.add_product(
        PerishableProduct("F-1", "Milk", 1.0, date(2026, 3, 12), quantity=30, low_stock_threshold=10)
    )
    inventory.add_product(
        PerishableProduct("F-2", "Yogurt", 2.0, date(2026, 3, 1), quantity=5, low_stock_threshold=2)
    )
    return inventory


def test_add_and_get_product(inv):
    assert len(inv) == 4
    assert "P-1" in inv
    assert inv.get_product("P-1").name == "Cable"


def test_duplicate_sku_rejected(inv):
    with pytest.raises(DuplicateProductError):
        inv.add_product(Product("P-1", "Another", 1.0))
    assert len(inv) == 4


def test_unknown_sku(inv):
    with pytest.raises(ProductNotFoundError):
        inv.get_product("NOPE")
    with pytest.raises(ProductNotFoundError):
        inv.add_stock("NOPE", 1)


def test_iteration_is_sorted_by_sku(inv):
    assert [p.sku for p in inv] == ["F-1", "F-2", "P-1", "P-2"]


def test_add_and_remove_stock_by_sku(inv):
    assert inv.add_stock("P-1", 10) == 50
    assert inv.remove_stock("P-1", 20) == 30


def test_remove_too_much(inv):
    with pytest.raises(InsufficientStockError):
        inv.remove_stock("P-2", 9)
    assert inv.get_product("P-2").quantity == 8


def test_expired_product_cannot_be_sold_through_inventory(inv):
    with pytest.raises(ExpiredProductError):
        inv.remove_stock("F-2", 1)


def test_low_stock_products(inv):
    assert [p.sku for p in inv.low_stock_products()] == ["P-2"]
    inv.remove_stock("P-1", 35)  # 5 left <= threshold 10
    assert [p.sku for p in inv.low_stock_products()] == ["P-1", "P-2"]


def test_alerts_from_all_product_types(inv):
    alerts = inv.get_alerts(TODAY)
    joined = "\n".join(alerts)
    assert "EXPIRING SOON: Milk" in joined
    assert "EXPIRED: Yogurt" in joined
    assert "LOW STOCK: Mouse" in joined
    assert len(alerts) == 3


def test_totals(inv):
    assert inv.total_units == 8 + 40 + 30 + 5
    assert inv.total_value == round(8 * 15.5 + 40 * 5.0 + 30 * 1.0 + 5 * 2.0, 2)


def test_report_content(inv):
    report = inv.report(TODAY)
    assert "INVENTORY REPORT - 2026-03-10" in report
    for sku in ("P-1", "P-2", "F-1", "F-2"):
        assert sku in report
    assert "EXPIRED" in report
    assert "EXPIRES 2d" in report
    assert "LOW" in report
    assert "4 product(s), 83 unit(s)" in report
    assert "ALERTS" in report


def test_report_without_alerts():
    inventory = Inventory()
    inventory.add_product(Product("A", "Thing", 1.0, quantity=100, low_stock_threshold=5))
    assert "No alerts." in inventory.report(TODAY)


def test_empty_inventory_report():
    report = Inventory().report(TODAY)
    assert "0 product(s), 0 unit(s)" in report
