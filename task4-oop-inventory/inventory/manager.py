"""The ``Inventory`` class: a collection of products with reporting."""

from datetime import date
from typing import Dict, Iterator, List, Optional

from .errors import DuplicateProductError, ProductNotFoundError
from .products import Product


class Inventory:
    """Stores products by SKU and provides stock operations and reports."""

    def __init__(self) -> None:
        self._products: Dict[str, Product] = {}

    # ----- collection behavior -----

    def add_product(self, product: Product) -> None:
        if product.sku in self._products:
            raise DuplicateProductError(f"a product with SKU '{product.sku}' already exists")
        self._products[product.sku] = product

    def get_product(self, sku: str) -> Product:
        try:
            return self._products[sku]
        except KeyError:
            raise ProductNotFoundError(f"no product with SKU '{sku}'") from None

    def __len__(self) -> int:
        return len(self._products)

    def __contains__(self, sku: object) -> bool:
        return sku in self._products

    def __iter__(self) -> Iterator[Product]:
        """Iterate products sorted by SKU."""
        for sku in sorted(self._products):
            yield self._products[sku]

    # ----- stock operations -----

    def add_stock(self, sku: str, amount: int) -> int:
        """Add units to a product and return its new quantity."""
        return self.get_product(sku).add_stock(amount)

    def remove_stock(self, sku: str, amount: int) -> int:
        """Remove (sell) units from a product and return its new quantity."""
        return self.get_product(sku).remove_stock(amount)

    # ----- alerts and totals -----

    def low_stock_products(self) -> List[Product]:
        return [p for p in self if p.is_low_stock]

    def get_alerts(self, today: Optional[date] = None) -> List[str]:
        alerts: List[str] = []
        for product in self:
            alerts.extend(product.alerts(today))
        return alerts

    @property
    def total_units(self) -> int:
        return sum(p.quantity for p in self)

    @property
    def total_value(self) -> float:
        return round(sum(p.total_value for p in self), 2)

    # ----- report -----

    def report(self, today: Optional[date] = None) -> str:
        """Return a formatted, human-readable inventory report."""
        today = today or date.today()
        sku_w = max([len("SKU")] + [len(p.sku) for p in self]) + 2
        name_w = max([len("Name")] + [len(p.name) for p in self]) + 2

        header = (
            f"{'SKU':<{sku_w}}{'Name':<{name_w}}{'Qty':>6}"
            f"{'Price':>10}{'Value':>12}  {'Status':<14}"
        )
        rule = "-" * len(header)
        lines = [f"INVENTORY REPORT - {today.isoformat()}", rule, header, rule]

        for p in self:
            lines.append(
                f"{p.sku:<{sku_w}}{p.name:<{name_w}}{p.quantity:>6}"
                f"{p.price:>10.2f}{p.total_value:>12.2f}  {p.status(today):<14}"
            )

        lines.append(rule)
        lines.append(
            f"{len(self)} product(s), {self.total_units} unit(s), "
            f"total value {self.total_value:.2f}"
        )

        alerts = self.get_alerts(today)
        lines.append("")
        if alerts:
            lines.append("ALERTS")
            lines.extend(f"  ! {message}" for message in alerts)
        else:
            lines.append("No alerts.")
        return "\n".join(lines)
