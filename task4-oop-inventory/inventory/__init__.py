"""Object-oriented inventory management system."""

from .errors import (
    DuplicateProductError,
    ExpiredProductError,
    InsufficientStockError,
    InventoryError,
    ProductNotFoundError,
)
from .manager import Inventory
from .products import PerishableProduct, Product

__all__ = [
    "Inventory",
    "Product",
    "PerishableProduct",
    "InventoryError",
    "InsufficientStockError",
    "ExpiredProductError",
    "ProductNotFoundError",
    "DuplicateProductError",
]
