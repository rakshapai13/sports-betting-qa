"""The single page of the application: match list, bet slip and outcome modals."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from betting_qa.api.models import Match, Selection
from betting_qa.config import Settings
from betting_qa.ui.base import Locator, UiObject
from betting_qa.ui.components.bet_receipt import BetReceiptModal
from betting_qa.ui.components.bet_slip import BetSlip
from betting_qa.utils.money import parse_money


class BetNotPlacedError(AssertionError):
    """The application answered a placement attempt with its error modal."""


class BettingPage(UiObject):
    HEADER_BALANCE = (By.ID, "header-balance")
    MATCH_CARDS = (By.CSS_SELECTOR, "#match-list .matchCard")
    ERROR_MODAL = (By.ID, "modal-error")
    ERROR_MESSAGE = (By.ID, "modal-error-message")

    def __init__(self, driver: WebDriver, settings: Settings) -> None:
        super().__init__(driver, settings.ui_timeout)
        self._settings = settings
        self.bet_slip = BetSlip(driver, settings.ui_timeout)
        self.receipt = BetReceiptModal(driver, settings.ui_timeout)

    @staticmethod
    def odds_button(match: Match, selection: Selection) -> Locator:
        return (By.ID, f"odds-{match.id}-{selection.key}")

    def open(self) -> BettingPage:
        self.driver.get(self._settings.app_url)
        self.wait_until(EC.presence_of_element_located(self.MATCH_CARDS))
        return self

    @property
    def header_balance(self) -> Decimal:
        return parse_money(self.text_of(self.HEADER_BALANCE))

    def header_balance_eventually(self, expected: Decimal) -> Decimal:
        """Header balance once it shows ``expected``, or whatever it shows at timeout."""
        return self.eventually(lambda: self.header_balance, expected)

    def select_odds(self, match: Match, selection: Selection) -> None:
        self.click(self.odds_button(match, selection))
        self.visible(BetSlip.SELECTION_CARD)

    def place_bet(self) -> BetReceiptModal:
        """Submit the bet slip and wait for the single final outcome.

        Returns the receipt modal on success. Raises ``BetNotPlacedError`` carrying the
        error-modal text if the application reports a failure instead.
        """
        self.bet_slip.submit()
        self.wait_until(
            EC.any_of(
                EC.visibility_of_element_located(BetReceiptModal.ROOT),
                EC.visibility_of_element_located(self.ERROR_MODAL),
            ),
            timeout=self._settings.bet_outcome_timeout,
        )
        if self.is_present(self.ERROR_MODAL):
            raise BetNotPlacedError(
                f"Bet placement ended in the error modal: {self.text_of(self.ERROR_MESSAGE)}"
            )
        return self.receipt
