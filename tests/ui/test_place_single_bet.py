from decimal import Decimal

import pytest

from betting_qa.api.models import Selection
from betting_qa.utils.money import expected_payout
from betting_qa.utils.soft_assert import SoftAssert

pytestmark = pytest.mark.ui

STAKE = Decimal("10.00")
SELECTION = Selection.HOME


def test_user_places_single_bet_and_receipt_matches_bet_slip(
    betting_page, api_client, upcoming_match
):
    """Pick odds, enter a stake, place the bet. Slip, receipt and balance must agree.

    Why this test: it is the main journey of the product and the only test that
    checks the whole chain in one go: match list -> bet slip -> place-bet call ->
    receipt -> balance. All the values are money, and re-checking them by eye on
    every release is slow and easy to get wrong.

    Expected values come from the API, not from the page, so the UI is never
    compared with itself. The stake is 10.00 so that stake x odds is exact and
    the test does not depend on the payout rounding rule. Checks are soft, so
    one run reports every mismatch.

    The "selection" line that spec 2.4 requires on the receipt is not checked:
    the receipt has no such element yet (BUG-11 in the execution report).
    """
    odds = upcoming_match.odds[SELECTION]
    payout = expected_payout(STAKE, odds)
    balance_before = api_client.get_balance()
    balance_after = balance_before - STAKE

    assert betting_page.header_balance_eventually(balance_before) == balance_before

    betting_page.select_odds(upcoming_match, SELECTION)
    slip = betting_page.bet_slip
    slip.enter_stake(STAKE)

    with SoftAssert() as check:
        check.equal(slip.fixture, upcoming_match.fixture, "bet slip match")
        check.is_true(SELECTION.label in slip.market, f"bet slip outcome is {SELECTION.label}")
        check.equal(slip.odds, odds, "bet slip odds")
        check.equal(slip.total_stake, STAKE, "bet slip total stake")
        check.equal(slip.potential_payout, payout, "bet slip potential payout")
        check.is_true(slip.can_place_bet(), "Place Bet is enabled")

    receipt_modal = betting_page.place_bet()
    receipt = receipt_modal.read()
    receipt_modal.close()

    with SoftAssert() as check:
        check.is_true(receipt.bet_id, "receipt has a bet id")
        check.equal(receipt.fixture, upcoming_match.fixture, "receipt match (home team first)")
        check.equal(receipt.stake, STAKE, "receipt stake")
        check.equal(receipt.odds, odds, "receipt odds")
        check.equal(receipt.potential_payout, payout, "receipt potential payout")
        check.is_true(receipt.placed_at, "receipt has a timestamp")
        check.is_true(not slip.has_selection(), "bet slip is empty after closing the receipt")
        check.equal(api_client.get_balance(), balance_after, "API balance after the bet")
        check.equal(
            betting_page.header_balance_eventually(balance_after),
            balance_after,
            "header balance after the bet",
        )
