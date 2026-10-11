"""Test data taken from the live API: a match to bet on and a known balance."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from betting_qa.api.client import BettingApiClient
from betting_qa.api.models import Match, Selection

MAX_STAKE = Decimal("100")


def pick_upcoming_match(matches: list[Match]) -> Match:
    """Soonest upcoming match whose three prices are all different.

    Different prices on purpose: if the app mixed up home, draw and away,
    a match with equal odds would not show it.
    """
    today = date.today()
    upcoming = [m for m in matches if m.kickoff_date > today and len(set(m.odds.values())) == 3]
    if not upcoming:
        raise LookupError("No upcoming match with three different prices in the catalogue.")
    return min(upcoming, key=lambda m: m.kickoff_date)


def spend_balance_down_to(client: BettingApiClient, match: Match, target: Decimal) -> Decimal:
    """Reset the balance, then place valid bets until `target` is left.

    The API has no way to set a balance directly, so this is the only route.
    """
    client.reset_balance().raise_for_status()
    balance = client.get_balance()
    while balance > target:
        stake = min(MAX_STAKE, balance - target)
        client.place_bet(match.id, Selection.HOME, stake).raise_for_status()
        balance = client.get_balance()
    assert balance == target, f"Could not set the balance to {target}, the API reports {balance}"
    return balance
