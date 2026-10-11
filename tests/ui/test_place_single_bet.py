"""E2E UI test: the core journey of the product, placing a single bet."""

from __future__ import annotations

from decimal import Decimal

import pytest

from betting_qa.api.client import BettingApiClient
from betting_qa.api.models import Match, Selection
from betting_qa.ui.pages.betting_page import BettingPage
from betting_qa.utils.money import expected_payout
from betting_qa.utils.soft_assert import SoftAssert

pytestmark = pytest.mark.ui

STAKE = Decimal("10.00")
SELECTION = Selection.HOME


def test_user_places_single_bet_and_receipt_matches_bet_slip(
    betting_page: BettingPage, api_client: BettingApiClient, upcoming_match: Match
) -> None:
    """Select odds, enter a stake, place the bet; slip, receipt and balance must agree.

    Why this test was chosen for automation:
      * It is the one journey every customer takes and the reason the feature exists.
        If it breaks, nothing else about the product matters, so it has to be checked
        on every build.
      * It is the only place where the pieces are verified together: match list ->
        bet slip -> POST /api/place-bet -> receipt -> balance. The test asserts
        consistency across them (what the user was shown before placing equals what
        the receipt confirms equals what the backend recorded), which a unit or API
        test cannot see.
      * The values involved are money. A wrong payout or balance on screen is a
        customer dispute even when the backend is right, and it is tedious and
        error-prone to re-check by eye on every release.
      * It is stable to automate: one deterministic path, element ids for locators,
        test data read from the API at run time rather than hard-coded.

    Design notes:
      * Expected values come from the API (match, odds, balance), not from the screen,
        so the UI is never compared with itself.
      * A 10.00 stake keeps stake x odds exact to the cent, so the test does not depend
        on the (unspecified) payout rounding rule.
      * Checks are soft: one run reports every inconsistency in the journey.
      * Not covered here: the "selection" line of the receipt required by spec 2.4.
        The receipt currently has no such element to locate; it is reported as a
        defect in docs/EXECUTION_REPORT.md.
    """
    odds = upcoming_match.odds[SELECTION]
    payout = expected_payout(STAKE, odds)
    balance_before = api_client.get_balance()
    balance_after_bet = balance_before - STAKE

    assert betting_page.header_balance_eventually(balance_before) == balance_before, (
        "Before betting, the header must show the balance held by the backend."
    )

    betting_page.select_odds(upcoming_match, SELECTION)
    slip = betting_page.bet_slip
    slip.enter_stake(STAKE)

    with SoftAssert() as check:
        check.equal(slip.fixture, upcoming_match.fixture, "bet slip match")
        check.is_true(SELECTION.label in slip.market, f"bet slip outcome shows {SELECTION.label}")
        check.equal(slip.odds, odds, "bet slip odds")
        check.equal(slip.total_stake, STAKE, "bet slip total stake")
        check.equal(slip.potential_payout, payout, "bet slip potential payout")
        check.is_true(slip.can_place_bet(), "Place Bet is enabled for a valid stake")

    receipt_modal = betting_page.place_bet()
    receipt = receipt_modal.read()
    receipt_modal.close()

    with SoftAssert() as check:
        check.is_true(receipt.bet_id, "receipt shows a bet id")
        check.equal(receipt.fixture, upcoming_match.fixture, "receipt match (home team first)")
        check.equal(receipt.stake, STAKE, "receipt stake")
        check.equal(receipt.odds, odds, "receipt odds")
        check.equal(receipt.potential_payout, payout, "receipt potential payout")
        check.is_true(receipt.placed_at, "receipt shows a placement timestamp")
        check.is_true(not slip.has_selection(), "bet slip is empty after closing the receipt")
        check.equal(api_client.get_balance(), balance_after_bet, "backend balance after the bet")
        check.equal(
            betting_page.header_balance_eventually(balance_after_bet),
            balance_after_bet,
            "header balance after the bet",
        )
