"""API test: a bet may never cost more than the user has."""

from __future__ import annotations

from decimal import Decimal

import pytest

from betting_qa.api.client import BettingApiClient
from betting_qa.api.data_setup import spend_balance_down_to
from betting_qa.api.models import Match, Selection

pytestmark = pytest.mark.api

ONE_CENT = Decimal("0.01")


def test_stake_above_available_balance_is_rejected(
    api_client: BettingApiClient, upcoming_match: Match
) -> None:
    """A stake one cent above the balance is rejected and the balance is untouched.

    Why this test was chosen for automation:
      * Risk: "stake must not exceed available balance" (spec 4.1) is the rule that
        protects real money. If the API lets it through, a user can bet money they
        do not have and the account goes negative. Nothing else in the feature has a
        higher cost of failure.
      * Layer: the UI check alone is not a control. It can be bypassed by calling the
        API directly, and it validates against a balance that may be out of date, so
        the server must enforce the rule itself. That makes the API the right place
        to pin it down.
      * Design: it is a boundary test. The balance is brought below the 100.00 stake
        cap first, so the only rule the request can break is the balance rule, and
        the stake is exactly one cent over, the smallest violation that exists.
      * Cost: no browser, runs in seconds, deterministic. Suitable for every commit.

    The assertions cover the response and, more importantly, the persisted state: a
    correct error message would be worthless if the stake were still deducted.
    """
    balance = spend_balance_down_to(api_client, upcoming_match, target=Decimal("20.00"))
    stake = balance + ONE_CENT

    response = api_client.place_bet(upcoming_match.id, Selection.HOME, stake)
    balance_after = api_client.get_balance()

    assert response.status_code == 422, (
        f"A stake of {stake} against a balance of {balance} must be rejected as a "
        f"validation error, but the API answered {response.status_code}: {response.text}"
    )
    assert response.json().get("error") == "insufficient_balance", (
        f"Expected the 'insufficient_balance' error code, got: {response.text}"
    )
    assert balance_after == balance, (
        f"A rejected bet must not change the balance: it was {balance} and is now {balance_after}."
    )
