from datetime import date, datetime

import pytest

from inventory import (
    ExpiredProductError,
    InsufficientStockError,
    PerishableProduct,
    Product,
)

TODAY = date(2026, 3, 10)


def make_product(**overrides) -> Product:
    values = dict(sku="P1", name="Pen", price=2.5, quantity=10, low_stock_threshold=3)
    values.update(overrides)
    return Product(**values)


def make_perishable(days_left: int, **overrides) -> PerishableProduct:
    expiry = date.fromordinal(TODAY.toordinal() + days_left)
    values = dict(sku="F1", name="Milk", price=1.0, expiry_date=expiry,
                  quantity=10, low_stock_threshold=3)
    values.update(overrides)
    return PerishableProduct(**values)


# ---------- Product: validation through properties ----------

def test_negative_quantity_rejected_in_constructor_and_setter():
    with pytest.raises(ValueError):
        make_product(quantity=-1)
    product = make_product()
    with pytest.raises(ValueError):
        product.quantity = -5
    assert product.quantity == 10  # unchanged after the failed assignment


@pytest.mark.parametrize("bad", [2.5, "3", None, True])
def test_quantity_must_be_a_whole_number(bad):
    with pytest.raises(TypeError):
        make_product().__setattr__("quantity", bad)


@pytest.mark.parametrize("bad", [-0.01, float("inf"), float("nan")])
def test_invalid_price_values(bad):
    with pytest.raises(ValueError):
        make_product(price=bad)


def test_price_must_be_a_number():
    with pytest.raises(TypeError):
        make_product(price="cheap")


def test_sku_is_read_only():
    with pytest.raises(AttributeError):
        make_product().sku = "NEW"


@pytest.mark.parametrize("field", ["sku", "name"])
def test_empty_identity_fields_rejected(field):
    with pytest.raises(ValueError):
        make_product(**{field: "  "})


# ---------- Product: operations ----------

def test_add_stock():
    product = make_product()
    assert product.add_stock(5) == 15
    assert product.quantity == 15


def test_remove_stock():
    product = make_product()
    assert product.remove_stock(4) == 6


def test_remove_more_than_available_changes_nothing():
    product = make_product()
    with pytest.raises(InsufficientStockError):
        product.remove_stock(11)
    assert product.quantity == 10


def test_can_remove_exactly_all_stock():
    product = make_product()
    assert product.remove_stock(10) == 0


@pytest.mark.parametrize("bad", [0, -3])
def test_amount_must_be_positive(bad):
    product = make_product()
    with pytest.raises(ValueError):
        product.add_stock(bad)
    with pytest.raises(ValueError):
        product.remove_stock(bad)


@pytest.mark.parametrize("bad", [1.5, "2", True])
def test_amount_must_be_integer(bad):
    with pytest.raises(TypeError):
        make_product().add_stock(bad)


# ---------- Product: alerts ----------

def test_low_stock_boundary_is_inclusive():
    assert make_product(quantity=4).is_low_stock is False
    assert make_product(quantity=3).is_low_stock is True
    assert make_product(quantity=0).is_low_stock is True


def test_alert_messages_and_status():
    assert make_product(quantity=50).alerts() == []
    assert make_product(quantity=50).status() == "OK"

    low = make_product(quantity=2)
    assert low.status() == "LOW"
    assert low.alerts()[0].startswith("LOW STOCK")

    out = make_product(quantity=0)
    assert out.status() == "OUT"
    assert out.alerts()[0].startswith("OUT OF STOCK")


def test_total_value():
    assert make_product(price=2.5, quantity=4).total_value == 10.0


def test_str_and_repr():
    product = make_product()
    text = str(product)
    assert "[P1]" in text and "Pen" in text and "qty: 10" in text and "25.00" in text
    assert "Product(sku='P1'" in repr(product)


# ---------- PerishableProduct ----------

def test_perishable_is_a_product():
    item = make_perishable(5)
    assert isinstance(item, Product)
    assert item.add_stock(1) == 11  # inherited behavior still works


def test_days_until_expiry_and_flags():
    assert make_perishable(5).days_until_expiry(TODAY) == 5
    assert make_perishable(0).days_until_expiry(TODAY) == 0
    assert make_perishable(-2).days_until_expiry(TODAY) == -2

    assert make_perishable(0).is_expired(TODAY) is False   # expires today = still valid
    assert make_perishable(-1).is_expired(TODAY) is True

    assert make_perishable(3).is_expiring_soon(TODAY) is True    # boundary
    assert make_perishable(4).is_expiring_soon(TODAY) is False
    assert make_perishable(-1).is_expiring_soon(TODAY) is False  # expired, not "soon"


def test_expiry_date_must_be_a_date():
    with pytest.raises(TypeError):
        make_perishable(5, expiry_date="2026-03-15")
    with pytest.raises(TypeError):
        make_perishable(5, expiry_date=datetime(2026, 3, 15, 12, 0))


def test_cannot_sell_expired_stock():
    item = make_perishable(-1)
    with pytest.raises(ExpiredProductError):
        item.remove_stock(1, today=TODAY)
    assert item.quantity == 10


def test_can_sell_unexpired_stock():
    assert make_perishable(2).remove_stock(4, today=TODAY) == 6


def test_discard_expired():
    expired = make_perishable(-1, quantity=7)
    assert expired.discard_expired(TODAY) == 7
    assert expired.quantity == 0

    fresh = make_perishable(5, quantity=7)
    assert fresh.discard_expired(TODAY) == 0
    assert fresh.quantity == 7


def test_perishable_alerts_and_status():
    expired = make_perishable(-2, quantity=10)
    assert expired.status(TODAY) == "EXPIRED"
    assert expired.alerts(TODAY)[0].startswith("EXPIRED")
    assert "2 day(s) ago" in expired.alerts(TODAY)[0]

    soon = make_perishable(2, quantity=10)
    assert soon.status(TODAY) == "EXPIRES 2d"
    assert soon.alerts(TODAY)[0].startswith("EXPIRING SOON")

    fresh = make_perishable(20, quantity=10)
    assert fresh.status(TODAY) == "OK"
    assert fresh.alerts(TODAY) == []


def test_perishable_combines_expiry_and_low_stock_alerts():
    item = make_perishable(1, quantity=2)  # expiring soon AND low stock
    kinds = [a.split(":")[0] for a in item.alerts(TODAY)]
    assert kinds == ["EXPIRING SOON", "LOW STOCK"]


def test_no_expiry_alert_when_nothing_in_stock():
    item = make_perishable(-5, quantity=0)
    assert [a.split(":")[0] for a in item.alerts(TODAY)] == ["OUT OF STOCK"]
    assert item.status(TODAY) == "OUT"


def test_perishable_str_includes_expiry():
    text = str(make_perishable(5))
    assert "expires:" in text and "[F1]" in text
