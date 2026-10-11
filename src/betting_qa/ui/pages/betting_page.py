"""The application's single page: match list, bet slip and the result modals."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from betting_qa.api.models import Match, Selection
from betting_qa.config import Settings
from betting_qa.ui.base import UiObject
from betting_qa.ui.components.bet_receipt import BetReceiptModal
from betting_qa.ui.components.bet_slip import BetSlip
from betting_qa.utils.money import parse_money


class BettingPage(UiObject):
    HEADER_BALANCE = (By.ID, "header-balance")
    MATCH_CARD = (By.CSS_SELECTOR, "#match-list .matchCard")
    ERROR_MODAL = (By.ID, "modal-error")
    ERROR_MESSAGE = (By.ID, "modal-error-message")

    def __init__(self, driver: WebDriver, settings: Settings) -> None:
        super().__init__(driver, settings.ui_timeout)
        self.settings = settings
        self.bet_slip = BetSlip(driver, settings.ui_timeout)
        self.receipt = BetReceiptModal(driver, settings.ui_timeout)

    def open(self) -> BettingPage:
        self.driver.get(self.settings.app_url)
        self.wait_until(EC.presence_of_element_located(self.MATCH_CARD))
        return self

    @property
    def header_balance(self) -> Decimal:
        return parse_money(self.text_of(self.HEADER_BALANCE))

    def header_balance_eventually(self, expected: Decimal) -> Decimal:
        """The header balance once it shows `expected`, or whatever it shows at timeout."""
        return self.eventually(lambda: self.header_balance, expected)

    def select_odds(self, match: Match, selection: Selection) -> None:
        self.click((By.ID, f"odds-{match.id}-{selection.key}"))
        self.visible(BetSlip.SELECTION_CARD)

    def place_bet(self) -> BetReceiptModal:
        """Submit the slip and wait for the receipt. Fails if the error modal shows up instead."""
        self.bet_slip.submit()
        self.wait_until(
            EC.any_of(
                EC.visibility_of_element_located(BetReceiptModal.ROOT),
                EC.visibility_of_element_located(self.ERROR_MODAL),
            ),
            timeout=self.settings.bet_timeout,
        )
        if self.is_present(self.ERROR_MODAL):
            raise AssertionError(f"Bet was not placed: {self.text_of(self.ERROR_MESSAGE)}")
        return self.receipt
