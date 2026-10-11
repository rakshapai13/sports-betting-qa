"""The receipt modal shown after a bet is accepted."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from selenium.webdriver.common.by import By

from betting_qa.ui.base import UiObject
from betting_qa.utils.money import parse_money


@dataclass(frozen=True)
class Receipt:
    bet_id: str
    fixture: str
    stake: Decimal
    odds: Decimal
    potential_payout: Decimal
    placed_at: str


class BetReceiptModal(UiObject):
    ROOT = (By.ID, "modal-success")
    BET_ID = (By.ID, "modal-success-bet-id")
    FIXTURE = (By.ID, "modal-success-match")
    STAKE = (By.ID, "modal-success-stake")
    ODDS = (By.ID, "modal-success-odds")
    PAYOUT = (By.ID, "modal-success-payout")
    PLACED_AT = (By.ID, "modal-success-placed-at")
    CLOSE = (By.ID, "modal-success-close")

    def read(self) -> Receipt:
        """Copy the values out so they can still be checked after the modal is closed."""
        return Receipt(
            bet_id=self.text_of(self.BET_ID),
            fixture=self.text_of(self.FIXTURE),
            stake=parse_money(self.text_of(self.STAKE)),
            odds=Decimal(self.text_of(self.ODDS)),
            potential_payout=parse_money(self.text_of(self.PAYOUT)),
            placed_at=self.text_of(self.PLACED_AT),
        )

    def close(self) -> None:
        self.click(self.CLOSE)
        self.wait_gone(self.ROOT)
