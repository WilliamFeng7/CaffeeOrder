"""Money helpers - single place where the "cents are integers" rule lives.

Every persisted amount in this system is an integer number of cents (分). Floats
must not appear in the path between "price in the DB" and "balance change", and
conversion to yuan happens only at the display layer.
"""

from __future__ import annotations


def line_total(unit_price_cents: int, quantity: int) -> int:
    """Total cents for one order line. Integer math only."""
    return int(unit_price_cents) * int(quantity)


def order_total(lines: list[tuple[int, int]]) -> int:
    """
    Sum `(unit_price_cents, quantity)` pairs into a cents total.

    Kept as a helper so the pricing rule has one owner instead of a `+=`
    sprinkled through whichever router happens to be creating an order.
    """
    return sum(line_total(price, qty) for price, qty in lines)
