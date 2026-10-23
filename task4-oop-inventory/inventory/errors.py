"""Custom exceptions for the inventory system."""


class InventoryError(Exception):
    """Base class for all inventory-related errors."""


class InsufficientStockError(InventoryError):
    """Raised when trying to remove more units than are in stock."""


class ExpiredProductError(InventoryError):
    """Raised when trying to sell a perishable product that has expired."""


class ProductNotFoundError(InventoryError):
    """Raised when a SKU is not in the inventory."""


class DuplicateProductError(InventoryError):
    """Raised when adding a product whose SKU already exists."""
