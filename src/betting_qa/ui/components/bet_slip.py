"""The bet slip: review the selection, enter a stake, submit."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By

from betting_qa.ui.base import UiObject
from betting_qa.utils.money import parse_money


class BetSlip(UiObject):
    SELECTION_CARD = (By.CSS_SELECTOR, "#bet-slip .betSelectionCard")
    SELECTION_FIXTURE = (By.CSS_SELECTOR, "#bet-slip .betSelectionTeams")
    SELECTION_MARKET = (By.CSS_SELECTOR, "#bet-slip .betSelectionMarket")
    SELECTION_ODDS = (By.CSS_SELECTOR, "#bet-slip .betSelectionOdds")
    STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    STAKE_WARNING = (By.CSS_SELECTOR, "#bet-slip .stakeWarning")
    TOTAL_STAKE = (By.ID, "bet-slip-total-stake")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    PLACE_BET = (By.ID, "bet-slip-place-bet")

    def has_selection(self) -> bool:
        return self.is_present(self.SELECTION_CARD)

    @property
    def fixture(self) -> str:
        """Match shown in the slip, e.g. 'Monaco vs Lyon'."""
        return self.text_of(self.SELECTION_FIXTURE)

    @property
    def market(self) -> str:
        """Market and outcome shown in the slip, e.g. 'Match Winner: Home'."""
        return self.text_of(self.SELECTION_MARKET)

    @property
    def odds(self) -> Decimal:
        return Decimal(self.text_of(self.SELECTION_ODDS).split(":")[-1].strip())

    @property
    def total_stake(self) -> Decimal:
        return parse_money(self.text_of(self.TOTAL_STAKE))

    @property
    def potential_payout(self) -> Decimal:
        return parse_money(self.text_of(self.POTENTIAL_PAYOUT))

    @property
    def validation_message(self) -> str | None:
        """Text of the stake warning, or ``None`` when the stake is valid."""
        warnings = self.driver.find_elements(*self.STAKE_WARNING)
        return warnings[0].text.splitlines()[-1].strip() if warnings else None

    def enter_stake(self, stake: Decimal | str) -> None:
        field = self.visible(self.STAKE_INPUT)
        field.clear()
        field.send_keys(str(stake))

    def can_place_bet(self) -> bool:
        return self.visible(self.PLACE_BET).is_enabled()

    def submit(self) -> None:
        self.click(self.PLACE_BET)
