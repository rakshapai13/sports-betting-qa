"""Money is handled as Decimal rounded to cents, never as float."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_money(value: Decimal | float | str) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def parse_money(text: str) -> Decimal:
    """Pull the amount out of UI text: 'Balance: €120.00' -> 120.00, '€-0.01' -> -0.01."""
    amount = re.search(r"-?\d+(\.\d+)?", text)
    if amount is None:
        raise ValueError(f"No amount found in {text!r}")
    return to_money(amount.group())


def expected_payout(stake: Decimal, odds: Decimal) -> Decimal:
    return to_money(stake * odds)
