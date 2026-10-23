"""Product classes: a base ``Product`` and a ``PerishableProduct`` with expiry tracking."""

import math
from datetime import date, datetime
from typing import List, Optional

from .errors import ExpiredProductError, InsufficientStockError


def _validate_amount(amount: int) -> int:
    """Check that ``amount`` is a positive whole number of units."""
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("amount must be an integer")
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    return amount


def _validate_non_negative_int(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if value < 0:
        raise ValueError(f"{label} cannot be negative")
    return value


class Product:
    """A product kept in stock.

    ``quantity``, ``price`` and ``low_stock_threshold`` are properties so that
    invalid values (negative stock, negative price, wrong types) can never be
    stored, no matter how they are assigned. ``sku`` is read-only because it
    identifies the product.
    """

    def __init__(
        self,
        sku: str,
        name: str,
        price: float,
        quantity: int = 0,
        low_stock_threshold: int = 5,
    ) -> None:
        if not isinstance(sku, str) or not sku.strip():
            raise ValueError("sku must be a non-empty string")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        self._sku = sku.strip()
        self.name = name.strip()
        self.price = price
        self.quantity = quantity
        self.low_stock_threshold = low_stock_threshold

    # ----- controlled attributes -----

    @property
    def sku(self) -> str:
        """Unique identifier (read-only)."""
        return self._sku

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("price must be a number")
        if not math.isfinite(value):
            raise ValueError("price must be a finite number")
        if value < 0:
            raise ValueError("price cannot be negative")
        self._price = round(float(value), 2)

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        self._quantity = _validate_non_negative_int(value, "quantity")

    @property
    def low_stock_threshold(self) -> int:
        return self._low_stock_threshold

    @low_stock_threshold.setter
    def low_stock_threshold(self, value: int) -> None:
        self._low_stock_threshold = _validate_non_negative_int(value, "low_stock_threshold")

    # ----- derived values -----

    @property
    def total_value(self) -> float:
        return round(self._price * self._quantity, 2)

    @property
    def is_low_stock(self) -> bool:
        """True when stock is at or below the threshold (includes out of stock)."""
        return self._quantity <= self._low_stock_threshold

    # ----- operations -----

    def add_stock(self, amount: int) -> int:
        """Add ``amount`` units and return the new quantity."""
        self.quantity = self._quantity + _validate_amount(amount)
        return self._quantity

    def remove_stock(self, amount: int) -> int:
        """Remove ``amount`` units and return the new quantity.

        Raises ``InsufficientStockError`` (and changes nothing) if there are
        not enough units.
        """
        amount = _validate_amount(amount)
        if amount > self._quantity:
            raise InsufficientStockError(
                f"cannot remove {amount} of '{self.name}': only {self._quantity} in stock"
            )
        self.quantity = self._quantity - amount
        return self._quantity

    def alerts(self, today: Optional[date] = None) -> List[str]:
        """Warnings that need attention. ``today`` is used by subclasses."""
        if self._quantity == 0:
            return [f"OUT OF STOCK: {self.name} ({self.sku})"]
        if self.is_low_stock:
            return [
                f"LOW STOCK: {self.name} ({self.sku}) has {self._quantity} left "
                f"(threshold {self._low_stock_threshold})"
            ]
        return []

    def status(self, today: Optional[date] = None) -> str:
        """Short status label for reports."""
        if self._quantity == 0:
            return "OUT"
        return "LOW" if self.is_low_stock else "OK"

    def __str__(self) -> str:
        return (
            f"[{self.sku}] {self.name} | qty: {self._quantity} | "
            f"price: {self._price:.2f} | value: {self.total_value:.2f}"
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(sku={self.sku!r}, name={self.name!r}, "
            f"price={self._price}, quantity={self._quantity})"
        )


class PerishableProduct(Product):
    """A product that expires.

    Adds behavior the base class does not have:

    * expiry tracking (days left, expired, expiring soon)
    * expired stock **cannot be sold**; it can only be discarded
    * extra alerts and report status for expired / expiring items
    """

    def __init__(
        self,
        sku: str,
        name: str,
        price: float,
        expiry_date: date,
        quantity: int = 0,
        low_stock_threshold: int = 5,
        expiry_warning_days: int = 3,
    ) -> None:
        super().__init__(sku, name, price, quantity, low_stock_threshold)
        if isinstance(expiry_date, datetime) or not isinstance(expiry_date, date):
            raise TypeError("expiry_date must be a datetime.date")
        self.expiry_date = expiry_date
        self.expiry_warning_days = _validate_non_negative_int(
            expiry_warning_days, "expiry_warning_days"
        )

    # ----- expiry tracking -----

    def days_until_expiry(self, today: Optional[date] = None) -> int:
        """Days left (0 = expires today, negative = already expired)."""
        return (self.expiry_date - (today or date.today())).days

    def is_expired(self, today: Optional[date] = None) -> bool:
        return self.days_until_expiry(today) < 0

    def is_expiring_soon(self, today: Optional[date] = None) -> bool:
        return 0 <= self.days_until_expiry(today) <= self.expiry_warning_days

    # ----- overridden behavior -----

    def remove_stock(self, amount: int, today: Optional[date] = None) -> int:
        """Sell units. Refuses to sell expired stock."""
        if self.is_expired(today):
            raise ExpiredProductError(
                f"'{self.name}' expired on {self.expiry_date.isoformat()} and cannot be sold; "
                "use discard_expired() instead"
            )
        return super().remove_stock(amount)

    def discard_expired(self, today: Optional[date] = None) -> int:
        """Throw away all stock if expired. Returns the number of units discarded."""
        if not self.is_expired(today):
            return 0
        discarded = self._quantity
        self.quantity = 0
        return discarded

    def alerts(self, today: Optional[date] = None) -> List[str]:
        messages: List[str] = []
        if self._quantity > 0:
            days = self.days_until_expiry(today)
            if days < 0:
                messages.append(
                    f"EXPIRED: {self.name} ({self.sku}) expired {-days} day(s) ago, "
                    f"{self._quantity} unit(s) must be discarded"
                )
            elif days <= self.expiry_warning_days:
                messages.append(
                    f"EXPIRING SOON: {self.name} ({self.sku}) expires in {days} day(s), "
                    f"{self._quantity} unit(s) left"
                )
        messages.extend(super().alerts(today))
        return messages

    def status(self, today: Optional[date] = None) -> str:
        if self._quantity > 0:
            if self.is_expired(today):
                return "EXPIRED"
            if self.is_expiring_soon(today):
                return f"EXPIRES {self.days_until_expiry(today)}d"
        return super().status(today)

    def __str__(self) -> str:
        days = self.days_until_expiry()
        when = "EXPIRED" if days < 0 else f"{days} day(s) left"
        return f"{super().__str__()} | expires: {self.expiry_date.isoformat()} ({when})"
