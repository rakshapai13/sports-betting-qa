"""The bet slip panel on the right."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By

from betting_qa.ui.base import UiObject
from betting_qa.utils.money import parse_money


class BetSlip(UiObject):
    SELECTION_CARD = (By.CSS_SELECTOR, "#bet-slip .betSelectionCard")
    FIXTURE = (By.CSS_SELECTOR, "#bet-slip .betSelectionTeams")
    MARKET = (By.CSS_SELECTOR, "#bet-slip .betSelectionMarket")
    ODDS = (By.CSS_SELECTOR, "#bet-slip .betSelectionOdds")
    STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    TOTAL_STAKE = (By.ID, "bet-slip-total-stake")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    PLACE_BET = (By.ID, "bet-slip-place-bet")

    def has_selection(self) -> bool:
        return self.is_present(self.SELECTION_CARD)

    @property
    def fixture(self) -> str:
        return self.text_of(self.FIXTURE)

    @property
    def market(self) -> str:
        """For example 'Match Winner: Home'."""
        return self.text_of(self.MARKET)

    @property
    def odds(self) -> Decimal:
        # shown as "Odds: 2.15"
        return Decimal(self.text_of(self.ODDS).split(":")[1].strip())

    @property
    def total_stake(self) -> Decimal:
        return parse_money(self.text_of(self.TOTAL_STAKE))

    @property
    def potential_payout(self) -> Decimal:
        return parse_money(self.text_of(self.POTENTIAL_PAYOUT))

    def enter_stake(self, stake: Decimal) -> None:
        field = self.visible(self.STAKE_INPUT)
        field.clear()
        field.send_keys(str(stake))

    def can_place_bet(self) -> bool:
        return self.visible(self.PLACE_BET).is_enabled()

    def submit(self) -> None:
        self.click(self.PLACE_BET)
