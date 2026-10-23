# Task 4: Object-Oriented Inventory Management System

A class-based inventory system built around a base `Product` class and a `PerishableProduct` subclass that adds real, distinct behavior: expiry tracking.

## Design

| Class | Responsibility |
|---|---|
| `Product` | SKU, name, price, quantity, low-stock threshold. Add/remove stock, low-stock detection, alerts, `__str__` |
| `PerishableProduct(Product)` | Adds an expiry date and behavior the base class does not have (see below) |
| `Inventory` | Holds products by SKU, runs stock operations, collects alerts, builds the formatted report |
| `errors.py` | Custom exceptions: `InsufficientStockError`, `ExpiredProductError`, `ProductNotFoundError`, `DuplicateProductError` |

### Where `@property` is used (and why)

- `quantity`: must be a whole number and can never be negative, even when assigned directly (`product.quantity = -5` raises `ValueError`)
- `price`: must be a finite, non-negative number
- `low_stock_threshold`: must be a non-negative whole number
- `sku`: read-only, because it identifies the product
- `total_value`, `is_low_stock`: computed values

### What `PerishableProduct` adds

- Expiry tracking: `days_until_expiry()`, `is_expired()`, `is_expiring_soon()` (configurable warning window)
- Expired stock **cannot be sold**: `remove_stock()` raises `ExpiredProductError`; it can only be removed with `discard_expired()`
- Extra alerts (`EXPIRED`, `EXPIRING SOON`) that combine with the inherited low-stock alerts
- Its own report status (`EXPIRED`, `EXPIRES 2d`) and an expiry date in `__str__`

## Core operations

- Add stock: `inventory.add_stock("P-100", 10)`
- Remove stock: `inventory.remove_stock("P-100", 5)` (raises `InsufficientStockError` if there is not enough; nothing changes)
- Low-inventory alerts: `inventory.low_stock_products()` and `inventory.get_alerts()`
- Formatted report: `print(inventory.report())`

## Project structure

```
task4-oop-inventory/
├── inventory/
│   ├── __init__.py
│   ├── errors.py       # custom exceptions
│   ├── products.py     # Product, PerishableProduct
│   └── manager.py      # Inventory
├── tests/
│   ├── test_products.py
│   └── test_inventory.py
├── main.py             # demo
├── pytest.ini
└── README.md
```

## Usage

```bash
python main.py
```

Example report:

```
INVENTORY REPORT - 2026-10-24
------------------------------------------------------------------------
SKU    Name                    Qty     Price       Value  Status
------------------------------------------------------------------------
F-100  Milk 1L                  30      1.20       36.00  EXPIRES 2d
F-200  Yogurt                   12      0.90       10.80  EXPIRED
F-300  Cheese                   20      7.50      150.00  OK
P-100  USB-C Cable              40      4.99      199.60  OK
P-200  Wireless Mouse            8     15.50      124.00  LOW
P-300  Mechanical Keyboard       0     59.00        0.00  OUT
------------------------------------------------------------------------
6 product(s), 110 unit(s), total value 520.40

ALERTS
  ! EXPIRING SOON: Milk 1L (F-100) expires in 2 day(s), 30 unit(s) left
  ! EXPIRED: Yogurt (F-200) expired 1 day(s) ago, 12 unit(s) must be discarded
  ! LOW STOCK: Wireless Mouse (P-200) has 8 left (threshold 10)
  ! OUT OF STOCK: Mechanical Keyboard (P-300)
```

`print(product)` output (`__str__`):

```
[P-100] USB-C Cable | qty: 35 | price: 4.99 | value: 174.65
[F-100] Milk 1L | qty: 30 | price: 1.20 | value: 36.00 | expires: 2026-10-26 (2 day(s) left)
```

## Run tests

```bash
pip install pytest
pytest
```

48 tests cover validation, stock operations, the low-stock boundary, expiry logic (including the edge days), selling/discarding expired stock, alerts and the report. Dates are passed in explicitly so the tests never depend on today's date.

## Concepts covered

Object-oriented programming, inheritance and method overriding, properties and validation, custom exceptions, project structure, unit testing.
