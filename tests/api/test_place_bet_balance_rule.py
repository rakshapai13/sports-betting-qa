from decimal import Decimal

import pytest

from betting_qa.api.data_setup import spend_balance_down_to
from betting_qa.api.models import Selection

pytestmark = pytest.mark.api


def test_stake_above_available_balance_is_rejected(api_client, upcoming_match):
    """A bet of one cent more than the balance must be refused and cost nothing.

    Why this test: "stake must not exceed available balance" is the rule that
    protects real money, and the API is the only place that can really enforce it.
    The UI check can be bypassed, and it works off a balance that may be stale.
    It needs no browser and runs in a few seconds, so it can run on every commit.

    The balance is first brought down to 20.00, below the 100.00 stake cap,
    so the balance rule is the only reason the request could be rejected.
    """
    balance = spend_balance_down_to(api_client, upcoming_match, target=Decimal("20.00"))
    stake = balance + Decimal("0.01")

    response = api_client.place_bet(upcoming_match.id, Selection.HOME, stake)
    balance_after = api_client.get_balance()

    assert response.status_code == 422, (
        f"Stake {stake} with balance {balance} should be rejected, "
        f"got {response.status_code}: {response.text}"
    )
    assert response.json()["error"] == "insufficient_balance"
    assert balance_after == balance, "a rejected bet must not change the balance"
