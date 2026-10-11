"""Test-data helpers built on the public API.

The API offers no "set balance" endpoint and no fixed test fixtures, so tests derive
their data from the live system: a match is chosen from the catalogue at run time and
a specific balance is reached by resetting and then placing ordinary, valid bets.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from betting_qa.api.client import BettingApiClient
from betting_qa.api.models import Match, Selection

MIN_STAKE = Decimal("1.00")
MAX_STAKE = Decimal("100.00")


def pick_upcoming_match(matches: list[Match], today: date | None = None) -> Match:
    """Return the next upcoming match whose three prices are all different.

    Distinct prices matter: if the application mixed up HOME/DRAW/AWAY, a match with
    equal prices would hide the mistake.
    """
    today = today or date.today()
    candidates = sorted(
        (m for m in matches if m.is_upcoming(today) and len(set(m.odds.values())) == 3),
        key=lambda m: m.kickoff_date,
    )
    if not candidates:
        raise LookupError("The match catalogue contains no upcoming match with distinct odds.")
    return candidates[0]


def spend_balance_down_to(client: BettingApiClient, match: Match, target: Decimal) -> Decimal:
    """Reset the balance, then place valid bets until exactly ``target`` remains.

    Returns the balance read back from the API, so callers never rely on arithmetic.
    """
    client.reset_balance().raise_for_status()
    balance = client.get_balance()
    if balance < target:
        raise ValueError(f"Cannot reach a balance of {target}: the reset balance is {balance}.")

    while balance > target:
        remaining = balance - target
        stake = min(MAX_STAKE, remaining)
        # Never leave a remainder smaller than the minimum stake: it could not be spent.
        if Decimal("0") < remaining - stake < MIN_STAKE:
            stake -= MIN_STAKE
        client.place_bet(match.id, Selection.HOME, stake).raise_for_status()
        balance = client.get_balance()

    if balance != target:
        raise RuntimeError(f"Set-up expected a balance of {target} but the API reports {balance}.")
    return balance
