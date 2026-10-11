"""Money helpers.

All amounts are handled as ``Decimal`` rounded to cents. Comparing floats would let
one-cent defects slip through (or raise false alarms), and one cent is exactly the
size of defect a betting product has to care about.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
_AMOUNT = re.compile(r"-?\d+(?:\.\d+)?")


def to_money(value: Decimal | float | int | str) -> Decimal:
    """Convert any numeric value to a ``Decimal`` rounded half-up to cents."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def parse_money(text: str) -> Decimal:
    """Extract the amount from UI text such as ``'Balance: €120.00'`` or ``'€-0.01'``."""
    cleaned = text.replace(",", "").replace("−", "-")
    found = _AMOUNT.search(cleaned)
    if found is None:
        raise ValueError(f"No monetary amount found in {text!r}")
    return to_money(found.group())


def expected_payout(stake: Decimal, odds: Decimal) -> Decimal:
    """Potential payout as defined by the feature spec: stake x decimal odds."""
    return to_money(stake * odds)
